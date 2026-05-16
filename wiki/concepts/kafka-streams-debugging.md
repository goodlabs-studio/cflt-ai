---
title: Kafka Streams Debugging
tags: [kafka-streams, debugging, troubleshooting, fsi, confluent-agent-skills]
sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/debugging.md]
related: [concepts/kafka-streams-production-hardening, concepts/kafka-streams-architecture, concepts/kafka-streams-4x-uncaught-exception-handler-import, concepts/avro-schema-source-directory, concepts/schema-aware-console-producer-required, synthesis/confluent-gotchas-top-20, concepts/consumer-group-rebalancing, concepts/exactly-once-semantics]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/kafka-streams-programming/references/debugging.md
---

# Kafka Streams Debugging

## Summary

Symptom-organised diagnostic guide for Kafka Streams (KS) applications: startup failures, processing stalls, rebalance storms, deserialization errors, state-store pathology, thread failures, memory issues, EOS/transaction failure modes, and Confluent Cloud-specific gotchas. Start from what the user sees, work backward to root cause. The most common P1 pattern in production is the rebalance loop driven by `max.poll.interval.ms` violations during state restoration — diagnose that first, then look elsewhere.

Sourced from `confluentinc/agent-skills@91d1871e` (Apache-2.0) — upstream maintains an eval gate at 90%+ pass before merge, so this article is `confidence: high` via source attestation rather than per-claim MCP re-validation. Trip-wire micro-articles in `wiki/concepts/` carry full MCP validation.

## Detail

### Startup failures

| Error | Likely cause | Fix |
|---|---|---|
| `UnsupportedVersionException` on startup | `group.protocol=streams` (KIP-1071) requires AK 4.2+/CP 8.2+. Broker is too old. | Remove `group.protocol=streams`. Upgrade broker when possible. |
| `TopologyException: Invalid topology` | Missing source topics, duplicate store names, or circular dependencies. | Audit `TopologyBuilder.build()`; verify all sources exist and store names unique. |
| `StreamsException: Could not find state directory` | `state.dir` is non-existent or non-writable. | Create directory; in containers, ensure mounted and writable. |
| Schema Registry connection timeout | Confluent SR serdes call SR during `configure()`. If SR is unreachable, the app hangs. | Verify SR URL reachable (`curl <SR_URL>/subjects`), check creds, version compatibility. |
| `ConfigException: Missing required config` | Missing `application.id`, `bootstrap.servers`, or default serdes when internal topics will be created. | Set the missing config explicitly. |

### Processing stalls

**App runs but produces no output:**

1. Check consumer lag — are input topics getting new records?
2. Is the app in `RUNNING` state? Check `/health/ready` or state-transition logs.
3. Look for `LogAndContinueExceptionHandler` messages — the app may be dropping all records.
4. Check filter predicates — excluded everything?
5. For stream-stream joins, records outside the join window are silently dropped.

**Stream-table join produces nulls:**

- Table not populated yet (compacted topic). Pre-populate, or use `leftJoin()` and handle nulls.
- Co-partitioning violation — same partition count and key strategy on both sides.
- Key mismatch — same type, same serialization on both sides.

### Rebalancing — the most common P1

The cascade: processing exceeds `max.poll.interval.ms` → consumer evicted → rebalance → state restoration → restoration exceeds poll timeout → evicted again → loop.

Diagnostic runbook:

1. **`max.poll.interval.ms` violation** — look for `Member consumer-<id> has exceeded max.poll.interval.ms`. Fix: increase `consumer.max.poll.interval.ms` (default 300000 = 5 min).
2. **State restoration as bottleneck** — look for `Restoration in progress for N partitions`. Restoration itself is exceeding poll timeout. See State Restoration Cascade below.
3. **Slow processing** — monitor `process-latency-max`, `punctuate-latency-max`. Culprits: blocking REST/DB calls, full state-store scans in punctuators, slow RocksDB.
4. **Instance instability** — K8s OOM kills, health-check failures. For stateful apps, **compute expected RocksDB off-heap memory** using the [Architecture](kafka-streams-architecture.md#memory) formula. Container OOMs from undersized memory requests are a frequent rebalance root cause.
5. **CPU throttling** — K8s CPU limits cause poll delays → rebalances. **Never set CPU limits on KS containers.**

Config-relationship rules that must all hold:

- `session.timeout.ms` ≤ `max.poll.interval.ms` (with cooperative protocol)
- `request.timeout.ms` ≥ `max.poll.interval.ms`
- For EOS: `transaction.timeout.ms` ≤ `max.poll.interval.ms`

**10-minute probing-rebalance loop:** `probing.rebalance.interval.ms` defaults to 600000 (10 min). Standbys never catching up → probing fires → nothing changes → same pattern repeats. Fix: increase `acceptable.recovery.lag`, or set `probing.rebalance.interval.ms` to 24 h if probing isn't needed.

**Broker failover causing simultaneous disconnect:** All consumers lose the coordinator on the failed broker; reconnection takes longer than `session.timeout.ms`, so everyone gets evicted. Fix: `session.timeout.ms ≥ 60000`, increase `reconnect.backoff.max.ms`, add `num.standby.replicas=1`.

**Stuck after partial shutdown:** Zombie members hold the group generation. Stop ALL instances → wait `session.timeout.ms` → restart incrementally. Always shut down with `streams.close(Duration.ofSeconds(30))` and `Runtime.getRuntime().addShutdownHook()`. In K8s, set `terminationGracePeriodSeconds ≥ close() timeout`.

### Deserialization errors

| Error | Cause | Fix |
|---|---|---|
| `Unknown magic byte!` | Record produced without Schema Registry (plain `kafka-console-producer`). SR serdes expect a 5-byte header (magic byte + schema ID). | Use schema-aware producer (`kafka-avro-console-producer`, etc.). See [Schema-aware console producer required](schema-aware-console-producer-required.md). |
| `ClassCastException: LinkedHashMap cannot be cast to MyPojo` | JSON Schema serde missing `json.value.type`. | Set `json.value.type=com.example.MyPojo` on the serde. |
| `Cannot construct instance of MyPojo (no Creators)` | JSON Schema POJO missing no-arg constructor. | Add `public MyPojo() {}`. |
| `DynamicMessage` instead of typed Protobuf | Protobuf serde missing `specific.protobuf.value.type`. | Set `specific.protobuf.value.type=com.example.proto.MyMessage`. |
| Schema incompatibility errors | Schema evolution broke compatibility. | Check SR compat settings; reset if needed. |

### State-store pathology

**State store growing without bound:** KTable or store accumulates unique keys without expiration. Set TTL via `Materialized.withRetention(Duration.ofDays(30))` or produce tombstones.

**State Restoration Cascade:** After restart, state stores rebuild from changelog topics. For large stores (tens to hundreds of GB), this takes minutes to hours. Restoration blocks poll → `max.poll.interval.ms` exceeded → evicted → another rebalance → cancels and restarts restoration. Death spiral.

Fix:

1. **Use persistent volumes (PVCs) in K8s.** Ephemeral storage forces full restoration on every restart.
2. Increase `consumer.max.poll.interval.ms` to at least 2× expected restoration time.
3. `restore.consumer.fetch.max.bytes=52428800` (50 MB) to speed up restoration.
4. `num.standby.replicas=1` for warm standby.
5. Tune `acceptable.recovery.lag`.

**Large State Store Pathology (100 GB+ per partition):** Full-scan operations (`store.all()`, `seekToFirst()`) in punctuators block the stream thread for minutes, causing `DisconnectException`, rebalances, cascading failures. Tombstone accumulation in delete-heavy workloads is the usual amplifier.

Diagnosis: thread dumps show the stream thread stuck in RocksDB `seekToFirst()` (RUNNABLE state); punctuator callbacks taking minutes; `live-sst-files-size` growing; `compaction-pending` staying high; `num-open-iterators` and `oldest-iterator-open-since-ms` suggest leaked iterators.

Fix: replace `store.all()` with `store.range(lastProcessedKey, null)`; switch to `CompactionStyle.UNIVERSAL` for delete-heavy workloads; increase background compaction threads.

### Thread failures

| Symptom | Cause | Fix |
|---|---|---|
| StreamThread dies and isn't replaced | No `UncaughtExceptionHandler` set — default is to shut down. | Add `MaxFailuresUncaughtExceptionHandler` (see [Production Hardening](kafka-streams-production-hardening.md)). |
| Thread replaced but same error repeats | Failing record retried after replacement. | Defensive null/validation checks; `ProcessingExceptionHandler` (KIP-1034) → DLQ; `LogAndContinueExceptionHandler` for deser errors. |
| `ProducerFencedException` | EOS transaction timeout, zombie instance, or transactional.id expired (CC, idle > 7 days). | Increase `transaction.timeout.ms`; stop old instances; new `application.id` or handle `InvalidPidMappingException`. |

The `StreamsUncaughtExceptionHandler` interface moved in Kafka Streams 4.x — it's in `org.apache.kafka.streams.errors`, not a nested class under `KafkaStreams`. See [Kafka Streams 4.x uncaught exception handler import](kafka-streams-4x-uncaught-exception-handler-import.md) for the exact import path.

### Memory issues

**OutOfMemoryError (JVM heap):** Reduce `statestore.cache.max.bytes` (on-heap, 10 MB/thread default), reduce `num.stream.threads`, or increase JVM heap (leave room for RocksDB).

**Container OOM killed (JVM heap is fine):** RocksDB off-heap exceeded container limit. Compute RocksDB memory via the [Architecture](kafka-streams-architecture.md#memory) formula; set `MaxRAMPercentage=75`; reduce RocksDB memory with `BoundedMemoryRocksDBConfig`.

**Memory keeps growing:** unbounded state store (add `.withRetention()`); unbounded suppression buffer (use `maxRecords(N).shutDownWhenFull()`); stateful lambdas retaining objects.

### EOS / transaction issues

**Transaction timeout cascade:** Processing or restoration > `transaction.timeout.ms` (10 s default). Broker logs show `Completed rollback of ongoing transaction for transactionalId ... due to timeout`. Producer fenced; rebalance triggers state restoration; cycle repeats.

Fix: increase `transaction.timeout.ms` (60 s starting point, some prod apps use 900 s); reduce `consumer.max.poll.records`; `consumer.max.poll.interval.ms ≥ transaction.timeout.ms`; `num.standby.replicas=1`.

**EOS error amplification (state wipe on unhandled exception):** EOS aborts the transaction, wipes local state, rebuilds from changelog. Each error = 40+ minutes of restoration for large stores.

**Emergency procedure:** immediately switch to `processing.guarantee=at_least_once` to stop the state-wipe loop → fix the bug → add `ProcessingExceptionHandler` (KIP-1034) for DLQ routing → re-enable EOS.

**`InvalidPidMappingException` (CC-specific):** Transactional ID-to-PID mappings expire after 7 days of inactivity on CC. Restart after 7+ days idle triggers this. Fix: restart, or use a new `application.id`. Preventive: ensure app runs at least weekly.

**`COORDINATOR_NOT_AVAILABLE` after broker failure:** `__transaction_state` partition leaders on the failed broker. Ensure `transaction.state.log.replication.factor=3` and at least 3 healthy brokers. Manual restart for stuck apps.

### Confluent Cloud gotchas

- **Topics must be pre-created.** CC always has `auto.create.topics.enable=false`. Internal topics (changelog, repartition) auto-create only if the service account has `CREATE` with prefix ACL matching `application.id`.
- **ACLs for Kafka Streams need more than a simple producer/consumer:** consumer-group `READ`, source `READ`, output `WRITE`, internal prefix-ACL `READ`/`WRITE`/`CREATE`, transactional-ID prefix `WRITE` (EOS), cluster `IDEMPOTENT_WRITE` (EOS). Missing any → `TopicAuthorizationException`, `GroupAuthorizationException`, or silent failure.
- **CKU throttling:** exceeding CKU produce/consume byte limits causes `TimeoutException` and potential rebalances. Monitor `received_bytes` / `sent_bytes`.
- **No broker logs.** All troubleshooting is client-side. Enable DEBUG for `org.apache.kafka.streams` and `org.apache.kafka.clients.consumer`.
- **Audit log growth from KS.** Frequent `DeleteRecords` on repartition topics → hundreds of records/sec at scale. Route audit log to exclude `kafka.DeleteRecords` on internal topics.

### Additional failure patterns

- **Cloud LB idle-connection drop** during long RocksDB ops (Azure/AWS/GCP, 4-30 min). Set OS-level TCP keepalive and `connections.max.idle.ms` < LB timeout.
- **Topology-change breaking state stores.** KS auto-generates internal topic/store names from topology structure. Changing it breaks compatibility. Prevention: `ensure.explicit.internal.resource.naming=true` and `Named.as()` on all operators.
- **Schema Registry throttling (HTTP 429).** Mass restart → all instances hit SR simultaneously. Enable client-side caching, stagger startup, pre-register in CI/CD, `auto.register.schemas=false` in prod.
- **SSL/TLS rotation breaks Streams.** Rolling restart after rotation; verify certs in truststore before rotation.
- **Post-upgrade breaking changes:** cooperative rebalancing default; `exactly_once` → `exactly_once_v2`; KIP-1071 (`group.protocol=streams`) requiring AK 4.2+/CP 8.2+; internal topic naming changes.

### Key metrics

Thread-level: `alive-stream-threads` (= `num.stream.threads`), `failed-stream-threads` (0), `process-rate`, `commit-rate`, `active-process-ratio` (> 0.5 — below means more time polling than processing).

State store: `put-latency-avg`, `get-latency-avg` (< 1 ms on local SSD), `suppression-buffer-size-avg`.

Expose via JMX for Prometheus/Grafana.

## Related

- [Kafka Streams Production Hardening](kafka-streams-production-hardening.md) — error handling, health checks, deployment sizing
- [Kafka Streams Architecture](kafka-streams-architecture.md) — threading model, RocksDB memory formula
- [Kafka Streams 4.x Uncaught Exception Handler Import](kafka-streams-4x-uncaught-exception-handler-import.md) — KS 4.x package layout
- [Avro Schema Source Directory](avro-schema-source-directory.md) — `src/main/avro/` plugin convention
- [Schema-Aware Console Producer Required](schema-aware-console-producer-required.md) — magic-byte verification path
- [Top 20 Confluent Gotchas](../synthesis/confluent-gotchas-top-20.md) — cross-pollination index
- [Consumer Group Rebalancing](consumer-group-rebalancing.md) — protocol generations, assignment strategies
- [Exactly-Once Semantics](exactly-once-semantics.md) — transactional foundations

---

*Source: confluentinc/agent-skills@91d1871e · skills/kafka-streams-programming/references/debugging.md · Ingested 2026-05-16 · Apache-2.0*
