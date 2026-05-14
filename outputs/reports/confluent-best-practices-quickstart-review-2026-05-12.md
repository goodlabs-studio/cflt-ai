---
title: "Review: The Confluent Best-Practice Quickstart — Producers to Networking"
status: review
generated: 2026-05-12
---

# Review: The Confluent Best-Practice Quickstart — Producers to Networking

**Date:** 2026-05-12
**Source files:** outputs/reports/confluent-best-practices-quickstart.md
**Scope:** Producers, Consumers, Topics/Clusters (CC + CP), Schema Registry, Kafka Connect, Flink (CC/CMF/OSS), Tableflow, Kubernetes/CFK, Security, Networking, capacity planning, triage. Config values · behavior assertions · architecture choices · metrics/limits · comparisons.
**Claims extracted:** 41

## Summary

High-quality, internally consistent synthesis that tracks the Confluent Canon and the fsi-dsp reference assets closely — the patterns are sound and the document already self-flags every recency-sensitive number (Freight specs, per-CKU limits, Tableflow GA surface, KIP-848 client support, custom-connector-on-PrivateLink) with ⚠️. Three substantive corrections: (1) `CooperativeStickyAssignor` is **not** the modern client default — the default `partition.assignment.strategy` is `[RangeAssignor, CooperativeStickyAssignor]`; (2) the topic-naming forms used in §III/§IV (`{domain}.{app}.{version}.{entity}` / `{domain}.{app}.v2.{entity}`) don't match the FSI canon convention `<domain>.<application>.<entity>.<event>` (ADR-007); (3) the canonical producer block ships `compression.type=zstd` as the FSI baseline where base canon's general default is `lz4` (the doc acknowledges this in the same comment, so it's a documented deviation, not an error). Recommend: re-confirm the ⚠️ items via `confluent-docs` MCP before quoting to a customer, fix the naming-convention examples, and soften the cooperative-sticky "default" claim. Cleared for circulation with those edits.

## Claim Validation

### Part I — Producers

| # | Claim | Wiki | MCP | Verdict |
|---|-------|------|-----|---------|
| qs-1 | Partition assignment = `hash(key) % partitions`; null key → sticky partitioner; key is the ordering contract | `concepts/producer-batching-config.md` | not re-run | Confirmed |
| qs-2 | Avro/Protobuf in prod; JSON Schema prototype/debug only; serializer writes magic byte + 4-byte schema ID | `concepts/schema-evolution-strategies.md` | not re-run | Confirmed |
| qs-3 | `enable.idempotence=true` default since Kafka 3.0; do not disable | — | not re-run | Confirmed |
| qs-4 | `acks=all`, `retries=2147483647`, `max.in.flight.requests.per.connection=5` safe with idempotence, ordering preserved | `concepts/producer-batching-config.md` | not re-run | Confirmed |
| qs-5 | `compression.type=zstd` (storage-constrained); `lz4` for pure throughput | `concepts/producer-batching-config.md` | not re-run | Corrected (see below) |
| qs-6 | `linger.ms=20` often *lowers* p99 under load; `linger.ms=0` is not "fastest" under load | `concepts/producer-batching-config.md` | not re-run | Confirmed |
| qs-7 | `auto.register.schemas=false` in prod; register in CI; `use.latest.version=true` or pin | `patterns/fsi-governance-automation.md` | not re-run | Confirmed |
| qs-8 | Transactional producer requires stable+unique `transactional.id`; downstream consumers must set `isolation.level=read_committed` | `concepts/exactly-once-semantics.md` | not re-run | Confirmed |
| qs-9 | `UnknownProducerIdException` = producer PID metadata aged out of partition (retention shorter than producer idle) | — | not re-run | Confirmed |
| qs-10 | Sticky / "uniform sticky" partitioner KIP-794 in 3.3+ | — | not re-run | Confirmed |

**Corrections:**
- Claim #qs-5: Base canon's general default is `compression.type=lz4` (`canon/base/defaults.yaml: producer.compression_type: lz4`; `zstd` for storage-constrained). The document ships `zstd` as the FSI canonical baseline. This is defensible (and the doc says "lz4 for pure throughput" in the same comment, and "`lz4` general, `zstd` if storage $ matters" in the Optimizations table), so treat it as a *documented deviation* rather than an error — but the canonical config block and the Optimizations table should agree on the default. Recommend: lead with `lz4` in the config block, note `zstd` as the storage-constrained override, to match canon and avoid a reader pasting `zstd` by default.

### Part II — Consumers

| # | Claim | Wiki | MCP | Verdict |
|---|-------|------|-----|---------|
| qs-11 | `enable.auto.commit=false`; manual commit *after* processing; auto-commit commits on `poll()` → at-most-once on crash | `concepts/consumer-group-rebalancing.md` | not re-run | Confirmed |
| qs-12 | One consumer group per logical application, not per instance | `concepts/consumer-group-rebalancing.md` | not re-run | Confirmed |
| qs-13 | `max.poll.interval.ms` exceeded → broker ejects member → rebalance ("consumer randomly stops") | `concepts/consumer-group-rebalancing.md` | not re-run | Confirmed |
| qs-14 | `client.rack` + `broker.rack` + `replica.selector.class=RackAwareReplicaSelector` enables fetch-from-follower; pre-set on CC | `patterns/aks-kafka-tuning.md` | not re-run | Confirmed |
| qs-15 | `partition.assignment.strategy=CooperativeStickyAssignor` … "(default in modern clients)" | `concepts/consumer-group-rebalancing.md` | not re-run | Corrected (see below) |
| qs-16 | KIP-848 ("new consumer rebalance protocol") GA as of Kafka 4.0 (early 2025); broker-coordinated, incremental; clients opt in via `group.protocol=consumer` | `concepts/consumer-group-rebalancing.md` (partial) | ⚠️ not re-run — verify client version support | Confirmed (recency-flagged) |
| qs-17 | `offsets.retention.minutes` default 7 days; idle-group offset expiry triggers `auto.offset.reset` | `concepts/consumer-group-rebalancing.md` | not re-run | Confirmed |
| qs-18 | Max useful consumers in a group = partition count | `concepts/consumer-group-rebalancing.md` | not re-run | Confirmed |
| qs-19 | CC Metrics API `io.confluent.kafka.server/consumer_lag_offsets` — use on CC instead of rolling your own JMX scraper | `concepts/consumer-lag-monitoring.md` | not re-run | Confirmed |
| qs-20 | Confluent Parallel Consumer = key-level concurrency beyond partition count for I/O-bound work | `concepts/consumer-lag-monitoring.md` | not re-run | Confirmed |
| qs-21 | Static membership (`group.instance.id` + tuned `session.timeout.ms`) → rolling restart triggers no rebalance | `concepts/consumer-group-rebalancing.md` | not re-run | Confirmed |

**Corrections:**
- Claim #qs-15: `CooperativeStickyAssignor` is *not* the default in modern clients. Since Kafka 3.0 the default `partition.assignment.strategy` is `[RangeAssignor, CooperativeStickyAssignor]`, which uses `RangeAssignor` until every member supports cooperative — explicitly setting `CooperativeStickyAssignor` (as the canonical config block does) is the correct *recommendation*, but the parenthetical "(default in modern clients)" overstates it. With `group.protocol=consumer` (KIP-848) the server-side assignor default is uniform/range, not "cooperative-sticky" either. Recommend: change to "(recommended; not the out-of-the-box default — you must set it)".

### Part III — Topics & Clusters (CC vs CP)

| # | Claim | Wiki | MCP | Verdict |
|---|-------|------|-----|---------|
| qs-22 | On CC: `min.insync.replicas` fixed at 2, RF fixed at 3, `unclean.leader.election` always false; not settable | — | ⚠️ not re-run | Confirmed |
| qs-23 | `max.message.bytes` 1 MB default; raising it has broker-memory cost | — | not re-run | Confirmed |
| qs-24 | Partition heuristic `6 × peak MB/s` is a prior; real formula = max(throughput/partition, consumer parallelism, produce rate/capacity) + headroom; ~10–25 MB/s/partition planning number | `concepts/sla-tiers.md` (partial) | not re-run | Confirmed |
| qs-25 | You can add partitions but never remove them; adding changes `hash(key) % n` → breaks per-key ordering | — | not re-run | Confirmed |
| qs-26 | CC cluster types Basic/Standard/Enterprise/Dedicated/Freight — Standard 99.99% SLA + RBAC + Cluster Linking source; Enterprise serverless + PrivateLink-only; Dedicated CKU-sized + BYOK + peering/TGW; Freight object-storage-backed, seconds latency, ~10× cheaper $/GB | — (no dedicated wiki article) | ⚠️ not re-run — limits/Freight specs drift | Unverifiable (recency-flagged; auto-stubbed) |
| qs-27 | KRaft: ZooKeeper removed as of Kafka 4.0 / CP 8.0; 3 (or 5) dedicated controller nodes, not co-located with brokers in prod | — | not re-run | Confirmed |
| qs-28 | Keep partitions-per-broker in the low thousands for replication health (CP) | — | not re-run | Confirmed |
| qs-29 | Tiered Storage (`confluent.tier.feature=true`) → smaller local disks, faster recovery/rebalance; Self-Balancing (`confluent.balancer.enable=true`) auto-rebalances on add/remove | — | not re-run | Confirmed (config key: also requires `confluent.tier.enable=true` per broker) |
| qs-30 | Broker heap ~6 GB even on huge nodes (rely on page cache); G1 or ZGC; `vm.swappiness=1`; XFS; `noatime` | `patterns/linuxone-kafka-tuning.md`, `patterns/aks-kafka-tuning.md` | not re-run | Confirmed |

### Part IV — Schema Registry

| # | Claim | Wiki | MCP | Verdict |
|---|-------|------|-----|---------|
| qs-31 | `TopicNameStrategy` default; `RecordNameStrategy`/`TopicRecordNameStrategy` only for genuine multi-event-type topics | `concepts/schema-evolution-strategies.md` | not re-run | Confirmed |
| qs-32 | BACKWARD = consumers upgrade first; FORWARD = producers upgrade first; FULL = both; `*_TRANSITIVE` = all prior versions | `concepts/schema-evolution-strategies.md` | not re-run | Confirmed |
| qs-33 | Schema IDs not portable across environments; use Schema Linking or export/import | `concepts/schema-evolution-strategies.md` | not re-run | Confirmed |
| qs-34 | Avro by default (ADR-001); Protobuf when polyglot/gRPC-native; JSON Schema prototype/debug only | `concepts/schema-evolution-strategies.md` | not re-run | Confirmed |
| qs-35 | CP: `_schemas` topic RF 3 + compaction on; corruption risk if compaction disabled | — | not re-run | Confirmed |
| qs-36 | Versioned-topic migration form `{domain}.{app}.v2.{entity}` (and §III checklist `{domain}.{application}.{version}.{entity}`) | `patterns/topic-naming.md` | not re-run | Corrected (see below) |
| qs-37 | Stream Governance: Essentials vs Advanced — Advanced adds Stream Lineage, Stream Catalog, Data Contracts, Schema Linking; Advanced is the FSI baseline | `patterns/fsi-governance-automation.md` | not re-run | Confirmed |

**Corrections:**
- Claim #qs-36: The naming forms used in the doc don't match the FSI canon convention. `canon/industry/fsi/overrides.yaml: topic_design.naming_convention: <domain>.<application>.<entity>.<event>` (ADR-007); base canon is `<domain>.<entity>.<event>`. The doc's §IV troubleshooting (`{domain}.{app}.v2.{entity}`) and Appendix B checklist (`{domain}.{application}.{version}.{entity}`) introduce a `version` segment in a position where canon has `<entity>.<event>`. Either the doc should follow `<domain>.<application>.<entity>.<event>` exactly, or — if a versioned-topic variant is intended — it should cite where that variant is sanctioned (`wiki/patterns/topic-naming.md` / ADR-007) rather than presenting an unsanctioned form. Recommend: align to ADR-007 and footnote any deliberate versioned-topic exception.

### Part V — Kafka Connect

| # | Claim | Wiki | MCP | Verdict |
|---|-------|------|-----|---------|
| qs-38 | Three deployment models — fully-managed CC (default for FSI: vendor-backed, one contract / 200+ connectors), Custom Connector CC (BYO plugin; ⚠️ size caps, historically not on PrivateLink), self-managed Connect | — (no dedicated wiki article; memory `feedback_confluent_supported_connectors.md`) | ⚠️ not re-run — verify custom-connector-on-PrivateLink | Confirmed (recency-flagged; auto-stubbed) |
| qs-39 | `connect-offsets`/`connect-configs`/`connect-status` must be compacted, RF 3; if `cleanup.policy` becomes `delete`, connectors silently lose state | — | not re-run | Confirmed (note: `config.storage.topic` must also have exactly 1 partition) |
| qs-40 | `tasks.max` ≤ source/topic partitions; sink parallelism hard-capped by topic partitions regardless of `tasks.max` | `patterns/dead-letter-queue-design.md` (partial) | not re-run | Confirmed |
| qs-41 | Object-store sink "small files problem" — low `flush.size`/`rotate.interval.ms` → millions of tiny objects; target ~128 MB–1 GB; or use Tableflow. JDBC source `mode=timestamp+incrementing`. Debezium/Postgres `heartbeat.interval.ms` advances replication-slot LSN. Exactly-once source = KIP-618. SMTs run inline on the worker thread. | `patterns/dead-letter-queue-design.md` | not re-run | Confirmed |

### Part VI — Flink

| # | Claim | Wiki | MCP | Verdict |
|---|-------|------|-----|---------|
| qs-42 | Watermarks `BOUNDED_OUT_OF_ORDERNESS` bounded; set `table.exec.source.idle-timeout` or windows never fire | `concepts/flink-checkpointing.md` | not re-run | Confirmed (on CC the equivalent surface differs — verify the CC-specific idle-timeout property) |
| qs-43 | Unbounded regular joins / non-windowed aggregations keep state forever without `sql.state-ttl` (CC) / `table.exec.state.ttl` (CP); #1 CFU/cost blow-up; prefer interval/temporal/lookup joins | `concepts/flink-checkpointing.md` | not re-run | Confirmed |
| qs-44 | Window cost tumbling < sliding/hop < session; use TVFs `TUMBLE`/`HOP`/`CUMULATE`; `upsert-kafka` for CDC/aggregated PK-keyed output; `scan.startup.mode=earliest-offset` for replay; Table API over DataStream; no DataStream on CC | `concepts/flink-checkpointing.md` | not re-run | Confirmed |
| qs-45 | CC Flink: compute pools sized in CFUs; `max_cfu` cannot be decreased after creation; pool exhaustion → statements `PENDING` | — | ⚠️ not re-run | Confirmed (recency-flagged) |
| qs-46 | CP/OSS Flink: never let serialization fall back to Kryo ("GenericType" in logs = silent throughput killer) | `concepts/flink-checkpointing.md` | not re-run | Confirmed |

### Part VII — Tableflow

| # | Claim | Wiki | MCP | Verdict |
|---|-------|------|-----|---------|
| qs-47 | CC feature materializing topics as Iceberg / Delta Lake in object storage; auto schema mapping from SR; auto compaction/snapshot-expiry; catalog integration (Glue, Snowflake Open Catalog/Polaris, Unity, REST); Iceberg GA'd 2025, Delta added; near-real-time (minutes) not sub-second; topic retention governs backfill window | `patterns/fsi-l1-reference-architecture.md` (uses it; no dedicated article) | ⚠️ not re-run — GA surface drifts | Unverifiable (recency-flagged; auto-stubbed) |

### Part VIII — Kubernetes (CFK)

| # | Claim | Wiki | MCP | Verdict |
|---|-------|------|-----|---------|
| qs-48 | CFK supported operator for CP on K8s/OpenShift; CRDs for `Kafka`/`KRaftController`/`Connect`/`SchemaRegistry`/`KsqlDB`/`ConfluentRestProxy`/`ControlCenter` + declarative `Topic`/`Schema`/`ClusterLink`/`ConfluentRolebinding` | `patterns/aks-kafka-tuning.md` | not re-run | Confirmed |
| qs-49 | Brokers: dedicated SSD StorageClass, `volumeClaimTemplate` per broker (effectively immutable — use expandable from day one), reclaim Retain, never `emptyDir`; `podAntiAffinity` *required*; requests==limits (Guaranteed QoS); no tight CPU limit on brokers; `PodDisruptionBudget maxUnavailable=1` | `patterns/aks-kafka-tuning.md` | not re-run | Confirmed |
| qs-50 | CFK rolling op won't proceed while any partition is under-replicated — by design, not a hang | — | not re-run | Confirmed |

### Part IX — Security

| # | Claim | Wiki | MCP | Verdict |
|---|-------|------|-----|---------|
| qs-51 | mTLS preferred in FSI (never username/password); SASL/OAUTHBEARER the modern CC default (ADR-006 over long-lived API keys); SASL/PLAIN only over TLS, avoid in FSI; SCRAM acceptable over TLS | `concepts/fsi-compliance.md` | not re-run | Confirmed |
| qs-52 | RBAC: bind at narrowest resource scope, prefix bindings for topic families, one service account per application; no implicit-deny clawback; never `User:ANONYMOUS`, no wildcard topic ACLs, minimize `super.users` | `concepts/fsi-compliance.md` | not re-run | Confirmed |
| qs-53 | TLS 1.2+/1.3 everywhere incl. inter-broker/inter-component; CC encrypts at rest by default; BYOK/self-managed keys on Dedicated and Enterprise; CSFLE = tag PII fields in schema, client encrypts against KMS before broker — the FSI PII answer | `concepts/fsi-compliance.md`, `patterns/fsi-l1-reference-architecture.md` | not re-run | Confirmed |
| qs-54 | Audit logs on every prod cluster; CC audit-log topic → SIEM via HTTP Sink Connector; CP ship to dedicated cluster; secrets via `ConfigProvider`/Vault, never plaintext | `patterns/audit-log-siem-integration.md` | not re-run | Confirmed |

### Part X — Networking

| # | Claim | Wiki | MCP | Verdict |
|---|-------|------|-----|---------|
| qs-55 | CC connectivity by type: Public (Basic/Standard/Dedicated), PrivateLink/PSC one-way CIDR-overlap-OK (Enterprise/Dedicated), VPC/VNet peering two-way non-overlapping (Dedicated only), AWS Transit Gateway (Dedicated only); Enterprise = PrivateLink/PSC only, no peering | — (queued: `concepts/private-networking.md`) | ⚠️ not re-run | Confirmed (recency-flagged) |
| qs-56 | PrivateLink uses per-AZ endpoints with zonal DNS; clients must resolve the zonal endpoints | — (queued: `concepts/private-networking.md`) | ⚠️ not re-run | Confirmed (recency-flagged) |
| qs-57 | `advertised.listeners` (CP) is the #1 connectivity footgun — must be the address clients actually use; cert SANs must match every advertised name; firewall ports 9092/9093/8081/8083/8090/9021 | — | not re-run | Confirmed |
| qs-58 | Cross-region replication (Cluster Linking) is always async — RPO=0 across regions doesn't exist; within-region MRC on CP is the RPO=0 option | `patterns/dr-cluster-linking.md`, `patterns/dr-multi-region-cluster.md` | not re-run | Confirmed |
| qs-59 | Fetch-from-follower keeps consumer fetch in-AZ — typically 30–50% off inter-AZ egress; cross-AZ ≈ 1–2 ms/hop; Freight trades latency for ~10× cheaper throughput | `patterns/low-latency-kafka-azure.md`, `patterns/aks-kafka-tuning.md` | not re-run | Confirmed (the 30–50% / 1–2 ms / ~10× figures are planning estimates, environment-dependent) |

### Parts XI–XII / Appendices

| # | Claim | Wiki | MCP | Verdict |
|---|-------|------|-----|---------|
| qs-60 | CC Flink `max_cfu` starting points: 5 dev / 10–20 staging / 20–50 prod (fsi-dsp `modules/flink/variables.tf` validation set 5/10/20/30/40/50) | — | not re-run (sourced to fsi-dsp repo) | Confirmed (against cited reference) |
| qs-61 | Dedicated CKU sizing — add 30–40% headroom; multi-AZ always for prod; CP broker sizing — 60–70% of peak | `concepts/sla-tiers.md` (partial) | ⚠️ per-CKU numbers drift | Confirmed (planning guidance) |
| qs-62 | Outbox pattern + idempotent consumer preferred over Connect/Streams EOS for "exactly once into a database" | `patterns/fsi-exactly-once.md` | not re-run | Confirmed |
| qs-63 | `cleanup.policy=compact,delete` for time-bounded changelog topics; `message.timestamp.type=LogAppendTime` overwrites producer CreateTime | — | not re-run | Confirmed |
| qs-64 | DR endpoint flip via service-discovery indirection (Consul/DNS) in front of `bootstrap.servers` (fsi-dsp ADR-003) | `patterns/dr-cluster-linking.md` | not re-run | Confirmed |

## Premise Challenge

| # | Premise | Assumption | Challenge | Severity |
|---|---------|------------|-----------|----------|
| 1 | The reader's deployment is Confluent-managed (CC) or Confluent-supported CP/CFK, and "supported" config surfaces apply | The customer runs licensed Confluent, not vanilla Apache Kafka / a wire-compatible alternative | Several recommendations (Tableflow, CC Flink CFUs, Stream Governance Advanced, fully-managed connectors, CFK CRDs, MDS RBAC) simply don't exist outside the Confluent product. If the audience includes OSS-Kafka shops, ~30% of the doc is aspirational. The doc's framing ("Confluent SE / Staff SA") makes this a safe assumption *for its stated audience* — flagged for completeness. | Minor |
| 2 | Latency budgets tolerate `acks=all` + cross-AZ ISR waits | The workloads are ≥ the FSI "<10ms (risk)" / "<100ms (compliance)" tiers, not the "sub-millisecond (market data)" tier | Under the FSI overlay, `market_data: sub-millisecond` cannot absorb a 1–2 ms cross-AZ hop *plus* `acks=all` replication. The doc's "latency-tier overlay" (`linger.ms=0–5`, fast-fail+DLQ, co-locate in-AZ) addresses the <100 ms tier but does **not** reconcile `acks=all`+cross-AZ ISR with a sub-ms SLA — that tier needs an explicit single-AZ / `acks=1`-with-documented-risk / co-processing discussion the doc doesn't have. For a market-data reader this premise fails. | Moderate |
| 3 | "Freight clusters: latency is seconds" is acceptable somewhere in an FSI estate | There exist FSI workloads (logs, telemetry, clickstream) genuinely indifferent to seconds of latency | Mostly holds — observability/telemetry pipelines qualify. But the doc should be explicit that *no* transactional, risk, compliance, or reconciliation-feeding stream qualifies; in a regulated shop the temptation to use Freight for cost on a stream that later feeds regulatory reporting is a real trap. The doc says "wrong tool for transactions" but doesn't fence "feeds anything a regulator reads." | Minor |
| 4 | A registered Avro/Protobuf schema exists for the topics being analytically materialized (Tableflow) and CDC'd (Connect/Debezium) | Schema discipline (`auto.register.schemas=false`, CI-registered, SR-managed) is already in place | The doc *recommends* this discipline but then *assumes* it when describing Tableflow ("enable it on topics that have a registered schema") and Connect converters. A greenfield customer reading top-to-bottom gets the recommendation; a brownfield customer with schemaless/raw-bytes topics hits the limitation the doc only mentions in passing. Surface "Tableflow/Connect-Avro presuppose the schema discipline in Part I/IV" earlier. | Minor |
| 5 | `min.insync.replicas=2` + RF 3 is sufficient durability for FSI regulatory-reporting streams | 2-of-3 ISR with `acks=all` meets the customer's RPO and audit requirements without synchronous cross-region | True within a region. But for regulatory reporting with a cross-region DR mandate, the doc correctly says cross-region replication is async (RPO≠0) — it should connect that more loudly to the "exactly-once implications for regulatory reporting" Canon rule: a region loss = bounded data loss on the report feed, which is a compliance conversation, not just an ops one. The doc has the pieces (Part X, `patterns/dr-cluster-linking.md`) but doesn't draw the line. | Moderate |

## Canon Compliance

| Area | Status | Notes |
|------|--------|-------|
| Producer: `acks=all` + `enable.idempotence=true` | ✅ Compliant | Canonical config block + Optimizations table + Appendix B checklist all enforce it; Gotcha #1 explicitly warns against overriding `acks` down. |
| Producer: compression | ⚠️ Documented deviation | Canon base default is `lz4` general / `zstd` storage-constrained; the canonical config block leads with `zstd`. Optimizations table restates the canon split correctly. Recommend aligning the config block to lead with `lz4`. |
| Schema Registry: Avro-first, `TopicNameStrategy`, `BACKWARD`→`FULL`, `auto.register.schemas=false` | ✅ Compliant | Matches base canon + FSI ADR-001/002; doc correctly notes FSI compatibility is tier-derived (ADR-002). |
| Topic naming convention | ⚠️ Deviation | FSI canon = `<domain>.<application>.<entity>.<event>` (ADR-007). Doc uses `{domain}.{application}.{version}.{entity}` (§III checklist) and `{domain}.{app}.v2.{entity}` (§IV) — a `version` segment not in the canon form. Reconcile or cite the sanctioned versioned-topic variant. |
| Consumer: `enable.auto.commit=false`, one group per app, `auto.offset.reset=earliest` | ✅ Compliant | All three present in canonical config + checklist; auto-commit failure mode well explained. |
| Consumer: assignor recommendation | ✅ Compliant (claim wording imprecise) | Recommending `CooperativeStickyAssignor` is correct; the "(default in modern clients)" parenthetical overstates — see Correction #qs-15. |
| Flink: bounded watermarks, `upsert-kafka` for changelogs, `earliest-offset` replay, Table API over DataStream, tumbling preferred | ✅ Compliant | Matches `canon/base/defaults.yaml: flink_sql.*` exactly; adds the state-TTL guidance the canon implies but doesn't spell out. |
| Cluster Linking over MirrorMaker 2 for CC↔CC; explicit mirror-topic control | ✅ Compliant | Doc treats Cluster Linking as the CC↔CC default and MM2 as the non-Confluent case (ADR-005); references `dr-mirrormaker2.md` only as the alternative. (Doc doesn't restate `auto.create.mirror.topics.enable=false` — minor omission, not a deviation.) |
| Security: mTLS + RBAC, per-application service accounts, audit logs on prod | ✅ Compliant | Part IX is a faithful expansion of the Canon security block + FSI ADR-006; CSFLE positioned as the FSI PII answer. |
| FSI overlay: SLA tiers, IBM MQ→Kafka bridge, LinuxONE for z/OS offload | ⚠️ Partial | LinuxONE bridge + offload covered (Part VIII, Appendix C, ADR-009). SLA tiers referenced via `concepts/sla-tiers.md` but the **sub-millisecond market-data tier** is not reconciled with `acks=all`+cross-AZ (see Premise #2). IBM MQ Source Connector named in canon as the canonical bridge pattern — doc lists 200+ connectors generically but doesn't call out IBM MQ Source by name where the mainframe bridge is discussed. |
| RF 3 / `min.insync.replicas` 2 / `unclean.leader.election` false | ✅ Compliant | Stated as fixed on CC, set explicitly on CP; Gotcha #7 reinforces. |

## Gaps

Claims that could not be verified against wiki or by re-running MCP this session (live `confluent-docs`/`context7` validation was not exhausted — budget-bounded run; all are the items the document itself flags ⚠️):

- **qs-26** — CC cluster-type matrix and Freight specifics (object-storage backing, "seconds not ms", "~10× cheaper $/GB", per-type networking/limits). No dedicated wiki article. → auto-stubbed.
- **qs-38** — Custom Connector on CC: plugin size caps, sensitive-config handling, PrivateLink-cluster availability. → auto-stubbed.
- **qs-47** — Tableflow: Iceberg GA date, Delta Lake support status, supported catalogs (Glue / Snowflake Open Catalog-Polaris / Unity / REST), BYOB. No dedicated wiki article. → auto-stubbed.
- **qs-16** — KIP-848 GA-in-4.0 + client `group.protocol=consumer` support matrix. Partial wiki coverage in `concepts/consumer-group-rebalancing.md`; verify exact client-library versions.
- **qs-55 / qs-56** — CC PrivateLink/PSC per-type availability and zonal-DNS specifics. Already queued as `wiki/concepts/private-networking.md`.
- **qs-42** — CC-specific source idle-timeout property name (the doc gives the CP/OSS `table.exec.source.idle-timeout`; CC's SQL surface differs). Already partially covered by queued `wiki/concepts/flink-confluent-cloud-setup.md`.
- **qs-45 / qs-61** — Per-CKU sizing numbers and CFU burn model — explicitly drift-prone; re-confirm via Confluent sizing guidance before quoting.

**Recommend:** run `/wiki:validate` or a targeted `confluent-docs` MCP pass on qs-16, qs-26, qs-38, qs-47 before this document is quoted to a customer with exact numbers.

## Recommendations

1. **Fix the topic-naming examples** (§III Appendix B checklist, §IV troubleshooting): use `<domain>.<application>.<entity>.<event>` per FSI ADR-007, or footnote the versioned-topic variant with its sanction. This is the one place the doc contradicts canon.
2. **Soften the cooperative-sticky "default" claim** (Part II "default in modern clients"): the actual default is `[RangeAssignor, CooperativeStickyAssignor]`. Reword to "recommended — you must set it explicitly".
3. **Lead the canonical producer block with `compression.type=lz4`**, keep `zstd` as the storage-constrained override, so the config block matches base canon and the Optimizations table. (Or, if `zstd` is a deliberate FSI default, state that explicitly and back it with an ADR-style note.)
4. **Add a sub-millisecond / market-data caveat box** near the latency-tier overlay: `acks=all` + cross-AZ ISR cannot meet a sub-ms SLA; that tier needs single-AZ co-location + an explicit durability-vs-latency decision. Connect it to the Canon FSI rule on exactly-once implications for regulatory reporting (Premise #2, #5).
5. **Name the IBM MQ Source Connector explicitly** where the mainframe bridge is discussed (Part VIII / Appendix C) — it's the canon-named canonical pattern, currently subsumed under "200+ connectors".
6. **Re-run MCP validation on the ⚠️ items** (qs-16, qs-26, qs-38, qs-47, qs-55/56, qs-61) before customer use; the document already instructs this — make it a release gate.
7. **Auto-stubs queued** for `tableflow-iceberg-delta`, `kafka-connect-deployment-models`, `confluent-cloud-cluster-types` — these are the topics with zero dedicated wiki coverage that this document leans on heavily; promoting them would let `/review` validate future versions against the wiki instead of leaving them ⚠️.

Otherwise: accurate, well-organized, canon-aligned. Cleared for circulation with edits 1–3.

---

Canon stack: base + industry/fsi | Hash: b6a3cf22b1438242 | MANIFEST: 1.1.0 | Floor: claude-opus-4-7 | Generated: 2026-05-12T00:00:00Z
