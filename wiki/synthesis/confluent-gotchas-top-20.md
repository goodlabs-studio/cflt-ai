---
title: Top 20 Confluent Gotchas
tags: [kafka, gotchas, troubleshooting, fsi, synthesis, producers, consumers, connect, flink, kubernetes, security, networking]
sources: [outputs/reports/confluent-best-practices-quickstart.md]
related: [patterns/producer-config-fsi, patterns/consumer-config-fsi, patterns/connect-deployment-models, patterns/flink-runtime-models, concepts/cc-cluster-tiers, concepts/network-connectivity-by-tier, concepts/schema-registry-best-practices]
confidence: medium
last_updated: 2026-05-14
last_validated: 2026-05-14
---

# Top 20 Confluent Gotchas

## Summary

The compounding sharp edges across producers, consumers, schemas, Connect, Flink, K8s, security, and networking. These are the things that show up in audits, production incidents, and "my consumer randomly stops" tickets. Most have a deeper home elsewhere in the wiki — this article exists as a **fast scan-and-recognize index** for triage and code review, with one-line forward pointers.

## Detail

### Producers (1–2)

1. **`enable.idempotence=true` is the default since Kafka 3.0** — but it *implies* `acks=all`, `retries>0`, `max.in.flight≤5`. If you override `acks=1` you **silently lose** idempotence and ordering guarantees. Don't override acks down. → `patterns/producer-config-fsi.md`
2. **`UnknownProducerIdException` after low retention** — the producer's PID metadata aged out of the partition. Don't set topic retention shorter than your producer's idle period; upgrade brokers; the producer self-heals by re-initializing.

### Consumers (3–5)

3. **`auto.offset.reset` is a trap door, not a setting you'll often see fire.** It only triggers when there's *no* committed offset or the committed offset is *out of range* — which happens silently when `offsets.retention.minutes` (default 7 days) expires an idle group's offsets. Commit periodically even when idle, or pin the group.
4. **`enable.auto.commit=true` commits on `poll()` before you've processed** → at-most-once on crash. Never in a processing app. Manual commit *after* processing. → `patterns/consumer-config-fsi.md`
5. **`max.poll.interval.ms` exceeded = the broker ejects the consumer** → rebalance → the symptom looks like "my consumer randomly stops." Shrink `max.poll.records`, speed up processing, or `pause()`/`resume()`.

### Topics & clusters (6–7)

6. **More partitions are not free, and you can't remove them.** They slow rebalances, broker recovery, controller failover, and add produce-request overhead — and adding partitions to a *keyed* topic breaks `hash(key) % n` so per-key ordering is lost going forward. Size deliberately; don't "round up to be safe."
7. **On Confluent Cloud, RF (3), `min.insync.replicas` (2), and `unclean.leader.election` (false) are fixed.** Don't write runbooks or capacity plans that assume you can change them. → `concepts/cc-cluster-tiers.md`

### Schema Registry (8–10)

8. **Schema IDs are not portable across environments.** Dev ID 100 ≠ prod ID 100. Use Schema Linking or export/import; never hardcode schema IDs or assume they match. → `concepts/schema-registry-best-practices.md`
9. **`auto.register.schemas=true` in producers = governance bypass + a race** registering slightly-different "latest" schemas. Register in CI (fail the build on incompat); clients use `use.latest.version=true` or a pinned version.
10. **Compatibility direction matters.** Adding a field *without a default* breaks `BACKWARD`. Removing a field breaks `FORWARD`. Know which side (producers vs consumers) upgrades first and pick the mode accordingly; use `FULL` for widely-shared contracts. → `concepts/schema-evolution-strategies.md`

### Kafka Connect (11–13)

11. **Kafka Connect's `connect-offsets` / `connect-configs` / `connect-status` must be compacted, RF 3.** If `cleanup.policy` ever becomes `delete` (common after a botched migration), connectors **silently lose state** — they replay or forget. `config.storage.topic` must have exactly 1 partition. → `patterns/connect-deployment-models.md`
12. **`tasks.max` > partition count = idle tasks doing nothing.** Sink connector parallelism is hard-capped by topic partitions regardless of `tasks.max`. Set it to `min(partitions, target parallelism, worker capacity)`.
13. **Object-store sink "small files problem":** low `flush.size` / short `rotate.interval.ms` → millions of tiny S3/GCS objects → slow queries + huge API bills. Target ~128 MB–1 GB files — or use **Tableflow** and stop hand-rolling this.

### Flink (14–16)

14. **Unbounded regular joins and non-windowed aggregations keep state FOREVER without `sql.state-ttl` / `table.exec.state.ttl`.** This is the #1 surprise CFU/cost blow-up and OOM cause on CC Flink. Set a TTL on every non-windowed stateful operator; prefer interval/temporal/lookup joins. → `patterns/flink-runtime-models.md`
15. **Watermarks don't advance if a partition is idle** → windows never fire → output is silent. Set `table.exec.source.idle-timeout`. "My aggregation produces nothing" is almost always this or a too-tight watermark bound.
16. **`max_cfu` on a CC compute pool cannot be decreased after creation.** Size to realistic peak, not paranoid peak. Pool exhaustion → statements stuck `PENDING`.

### Kubernetes / CFK (17)

17. **CFK rolling upgrades stall by design while any partition is under-replicated** — the operator won't take down the next broker until URP=0. A "stuck" roll almost always means a lagging broker or a bad disk, not a CFK bug. Find the URP, fix it, the roll continues.

### Networking & security (18–20)

18. **`advertised.listeners` (CP) / broker-hostname DNS resolution (CC PrivateLink) is the #1 connectivity footgun.** Clients reach the bootstrap, then fail to reach the brokers it returns. Verify every client can *resolve and route to* every advertised address, per-AZ. Test from inside *and* outside the network. → `concepts/network-connectivity-by-tier.md`
19. **SASL/PLAIN without TLS ships credentials in cleartext.** In FSI: mTLS or SASL/OAUTHBEARER. If you must use SASL, it's SCRAM-over-TLS minimum — never PLAIN-over-plaintext. And API keys never go in git.
20. **Cross-AZ traffic is the silent cost driver** (`acks=all` replication + consumers fetching from leaders across AZs). Enable fetch-from-follower (`client.rack` + `broker.rack` + `RackAwareReplicaSelector`) — typically 30–50% off inter-AZ egress.

### Bonus

- **#21 — Freight clusters** trade ms-latency (latency lands in *seconds*, not ms) for substantially cheaper throughput vs. self-managed Kafka. Confirmed limitations (`cloud/current/clusters/cluster-types.md`, 2026-05-14): **no idempotent producer, no transactions, no EOS, no key-based compaction** — wrong tool for transactional/audit workloads. ⚠️ unverified — exact $/GB ratio vs. Standard/Enterprise is marketing-positioned ("~10× cheaper than self-managed Kafka") and not a Confluent docs-table number; cite the pricing calculator, not a fixed ratio. → `concepts/cc-cluster-tiers.md`

## Tips & workarounds

- **Always `--dry-run` before `--execute`** on `kafka-consumer-groups --reset-offsets`. Always.
- **`kcat`** for quick inspection: `kcat -b <broker> -t <topic> -C -o -1 -c1` peeks the last message; `-L` lists metadata.
- **`linger.ms=0` is not "low latency" under load** — small lingers (5–20 ms) cut request count and often *lower* p99.
- **For "exactly once into a database," prefer the outbox pattern + idempotent consumer** over Connect/Streams EOS gymnastics. See `patterns/fsi-exactly-once.md`.
- **Static membership (`group.instance.id`) + tuned `session.timeout.ms`** = deploy/restart a consumer without triggering a rebalance.
- **On CC, use the Metrics API + Stream Lineage** instead of rolling your own JMX scraping.
- **Test schema compatibility in CI** (`mvn schema-registry:test-compatibility`) before merge — never let production be the first compat check.
- **Flink enrichment: `LOOKUP JOIN` against an `upsert-kafka` / JDBC table** beats a regular join — bounded state.
- **`cleanup.policy=compact,delete`** for changelog topics that also need a time bound (compact for current state, delete for the floor).
- **DR endpoint flip:** put a service-discovery indirection (Consul / DNS) in front of `bootstrap.servers` so failover is one atomic change. See `patterns/dr-cluster-linking.md`, ADR-003.
- **`message.timestamp.type=LogAppendTime`** if you don't trust producers' clocks and your retention/windowing depends on timestamps — but know it overwrites the producer's CreateTime.

## Related

- [FSI Producer Configuration](../patterns/producer-config-fsi.md) — gotchas #1, #2
- [FSI Consumer Configuration](../patterns/consumer-config-fsi.md) — gotchas #3, #4, #5
- [Confluent Cloud Cluster Tiers](../concepts/cc-cluster-tiers.md) — gotcha #7, #21
- [Schema Registry Best Practices](../concepts/schema-registry-best-practices.md) — gotchas #8, #9
- [Schema Evolution Strategies](../concepts/schema-evolution-strategies.md) — gotcha #10
- [Kafka Connect Deployment Models](../patterns/connect-deployment-models.md) — gotchas #11, #12, #13
- [Flink Runtime Models](../patterns/flink-runtime-models.md) — gotchas #14, #15, #16
- [Network Connectivity by Tier](../concepts/network-connectivity-by-tier.md) — gotchas #18, #20
- [Consumer Group Rebalancing](../concepts/consumer-group-rebalancing.md) — gotcha #5 deeper context
- [FSI Exactly-Once Pattern](../patterns/fsi-exactly-once.md) — outbox/idempotent-consumer answer for "EOS into a DB"
