---
title: FSI Reference Architecture — LinuxONE Operational Plane + Off-Platform Analytics
tags: [fsi linuxone reference-architecture confluent mongodb cockroachdb postgres redis neo4j databricks telum]
sources:
  - https://www.ibm.com/products/linuxone/ai-processor
  - https://www.cockroachlabs.com/docs/stable/install-cockroachdb-linux
  - https://www.mongodb.com/docs/manual/administration/production-notes/
  - https://neo4j.com/docs/operations-manual/current/installation/linux/
  - https://www.confluent.io/customers/ibm/
  - https://www.databricks.com/product/data-intelligence-platform
related: [concepts/fsi-data-streaming-platform, concepts/linuxone-kafka-integration, concepts/sla-tiers, concepts/fsi-compliance, patterns/linuxone-validation-suite, patterns/linuxone-kafka-tuning, patterns/linuxone-flink-validation-tuning, patterns/dr-cluster-linking, patterns/fsi-exactly-once]
confidence: medium
last_updated: 2026-05-05
last_validated: 2026-05-05
validated_via: [confluent-docs (cloud connectors index, versions-interoperability.html, postgresql cdc v1 EOL page), context7]
changelog:
  - 2026-05-04 (rev 2) — Replaced Debezium-direct CDC references with Confluent-supported connectors per Confluent Hub: MongoDB Connector for Apache Kafka, PostgreSQL CDC Source V2 (Debezium V1 EOL 2026-03-31), CockroachDB CDC Connector, Neo4j Connector for Confluent. Single-vendor support model under IBM Confluent Platform for Z/LinuxONE bundle.
  - 2026-05-05 (rev 3) — MCP-validated. Tableflow output confirmed as Iceberg AND Delta Lake (not Iceberg only). PostgreSQL CDC V1 EOL date verified at March 31, 2026. CockroachDB integration mechanism clarified (native changefeed; Hub entry exists but is self-managed only — not in CC fully-managed list).
---

# FSI Reference Architecture — LinuxONE Operational Plane + Off-Platform Analytics

## Summary

Reference architecture for FSI workloads that pins the **operational data plane** to IBM LinuxONE Emperor 5 — the L1-certified data stores (MongoDB, CockroachDB, PostgreSQL, Redis, Neo4j, Confluent Platform) plus Confluent Manager for Apache Flink — and routes the **analytical plane** off-platform to Databricks via Confluent Cluster Linking. Confluent is the universal nervous system: every state change in every operational store flows as an event onto Kafka, and every analytical workload reads from Kafka or its tiered-storage cold object copy. Telum II provides on-chip AI inference for sub-ms decisioning; Spyre (where present) covers larger model classes. DR is multi-frame Cluster Linking. Off-platform analytics never read directly from L1 stores — they consume the event stream.

> Why this shape: every store named is L1-certified, which means a single hardware footprint with FIPS 140-3, in-frame networking, and shared operational tooling. The analytical plane needs elastic compute and access to non-FSI data (market feeds, vendor enrichment), which Databricks delivers better than any on-frame option. Splitting at the operational/analytical boundary is the natural seam.

## Pattern

### 1. Topology

```
┌─────────────────────────  IBM LinuxONE Emperor 5 (frame 1)  ─────────────────────────┐
│                                                                                       │
│  ┌─ Operational Stores LPAR ─────────────────────────────────────────────────────┐    │
│  │ MongoDB  │  CockroachDB  │  PostgreSQL  │  Redis  │  Neo4j                     │    │
│  └──────────────────────────┬────────────────────────────────────────────────────┘    │
│                              │  CDC (Debezium / Cockroach changefeed / pg_logical)    │
│                              ▼                                                        │
│  ┌─ Confluent Platform LPAR ─────────────────────────────────────────────────────┐    │
│  │ Kafka brokers (KRaft)  │  Schema Registry  │  Connect (CDC, MQ, JDBC)          │    │
│  └────────┬────────────────────────────────────────┬─────────────────────────────┘    │
│           │ HiperSockets / SMC-D                   │                                  │
│           ▼                                         ▼                                  │
│  ┌─ Flink LPAR (CMF) ─────────┐         ┌─ z/OS LPAR ──────────────┐                  │
│  │ Stateful streams + UDFs    │         │ Mainframe apps via IBM MQ │                  │
│  │ Telum II NNPA inference    │         └──────────────────────────┘                  │
│  └────────────────────────────┘                                                       │
│           │                                                                            │
│           ▼  Kafka topics: scored events, alerts, decisions                            │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                          │  Cluster Linking over OSA-Express
                                          ▼
                            ┌─  Confluent Cloud (cross-region) ─┐
                            │  Mirror topics, governed          │
                            └─────────────┬─────────────────────┘
                                          │  Iceberg / Tableflow
                                          ▼
                            ┌─  Databricks (off-platform)  ────┐
                            │  Lakehouse, ML training, BI       │
                            └───────────────────────────────────┘
```

A second Emperor 5 in a paired data center mirrors the operational plane via store-native replication (Cockroach multi-region, Mongo replica set, etc.) and Confluent **Cluster Linking** for the event plane. RPO=0 for `compliance` tier is achieved via MRC on Confluent Platform.

### 2. Roles and Sizing

| Component | Role | L1 sizing (per frame) | Notes |
|-----------|------|------------------------|-------|
| **Confluent Platform** | Event nervous system | 6 brokers + 3 KRaft controllers | KRaft only (CP 8.0+); see [LinuxONE Kafka Tuning](linuxone-kafka-tuning.md) |
| **CMF (Flink)** | Stateful processing, AI inference | 4 TaskManagers, 16 slots each | Telum II UDFs for sub-ms decisioning |
| **MongoDB** | Document store for customer / account profiles | Replica set, 3 members in-frame, 2 cross-frame | WiredTiger; ensure `s390x` tarball |
| **CockroachDB** | OLTP for ledger / payments | 3-node cluster, locality-aware replication | Multi-region across the two frames; `survive=region` for `critical` tier |
| **PostgreSQL** | Transactional / analytical hybrid | 1 primary + 2 replicas per frame | Logical replication for CDC into Kafka |
| **Redis** | Hot cache, session, rate limiting | 3-master + 3-replica cluster | Redis Enterprise on s390x certified |
| **Neo4j** | Entity / fraud graph | 3-node causal cluster | Aura on L1 not GA; self-managed Enterprise |
| **IBM Cloud Object Storage** | Tiered storage target, model artifacts | Off-LPAR, on-frame | S3-compatible for Confluent Tiered Storage and Flink checkpoints |
| **Databricks** | Lakehouse, ML training, BI | Off-platform (AWS / Azure / GCP) | Receives Iceberg/Delta Lake topics via Tableflow / Confluent Cloud |

### 3. Data Flow Patterns

#### 3.1 Operational Write → Event Stream
Every operational store emits CDC into Kafka via a **Confluent-supported connector** — first-party connector from Confluent Hub or a partner-published connector that Confluent supports. Avoid Debezium-direct or community connectors here: the IBM Confluent Platform for Z and LinuxONE bundle gives single-vendor support across the broker + connector lifecycle, and FSI audit prefers a single throat to choke.

| Source | Connector (Confluent-supported) | Mechanism | Topic naming |
|--------|----------------------------------|-----------|--------------|
| MongoDB | **MongoDB CDC Source (Debezium)** (Confluent-managed in CC); **MongoDB Atlas Source/Sink** also fully-managed | MongoDB change streams | `cust.profile.changed.v1` |
| CockroachDB | **CockroachDB CDC Connector** on Confluent Hub (self-managed only — not in CC fully-managed catalog as of 2026-05). Underlying mechanism is Cockroach's native changefeed sinking directly to Kafka | Native CockroachDB changefeed → Kafka | `ledger.transaction.posted.v1` |
| PostgreSQL | **PostgreSQL CDC Source V2 (Debezium)** (Confluent-managed in CC). V1 reached EOL **2026-03-31** — migrate any V1 instances | Logical replication via `pgoutput` | `accounts.balance.updated.v1` |
| Redis | No source connector — cache is derived state, not source of truth. Use the **Redis Sink** to *materialize* into Redis, not the reverse | n/a | n/a |
| Neo4j | **Neo4j Sink** (Confluent-managed in CC) + **Neo4j Connector for Confluent and Apache Kafka** v5.1+ (by Neo4j; certified on Hub for source/CDC; CDC source requires Neo4j Enterprise / Aura with CDC enabled) | Neo4j CDC stream | `fraud.entity.linked.v1` |
| z/OS | **IBM MQ Source** (Confluent-managed in CC; also self-managed on Hub) — see [LinuxONE Kafka Integration](concepts/linuxone-kafka-integration.md) | MQ queue → Kafka topic | `mainframe.txn.recorded.v1` |

All topics governed per [SLA Tiers](concepts/sla-tiers.md): tier-driven defaults for partitions, retention, compatibility, RBAC, and DR.

> **Why not Debezium-direct?** Debezium is the OSS upstream that several Confluent connectors are built on (PostgreSQL CDC, SQL Server CDC, MySQL CDC). Running Debezium direct gives you the same engine without the Confluent support contract, certification, or governance hooks. In FSI on the IBM L1 bundle, that's the wrong trade — pick the Confluent-packaged variant on Confluent Hub.

#### 3.2 Real-Time Decisioning (the L1 differentiator)
Flink jobs co-resident on L1 consume events, enrich via lookup joins to PostgreSQL or Redis (over HiperSockets), and call **Telum II NNPA** for sub-ms inference. Decisions land back on Kafka:

- `kafka.fraud.alerts.v1` → ops console, downstream block actions
- `kafka.events.scored.v1` → audit trail, ML retraining feed

See [LinuxONE Flink Validation & Tuning § Telum II Sub-Millisecond Anomaly Detection](linuxone-flink-validation-tuning.md).

#### 3.3 Off-Platform Analytics (Databricks)
**Cluster Linking** replicates governed topics from the on-frame Confluent Platform cluster to a Confluent Cloud cluster co-located with the Databricks workspace:

1. CL mirrors selected topics (no `auto.create.mirror.topics.enable`; explicit topic-by-topic).
2. CC's **Tableflow** materializes those topics as **Apache Iceberg or Delta Lake** tables in the analytical bucket — Tableflow supports both open table formats per Confluent's product brief.
3. Databricks reads via Unity Catalog (Delta Lake native; Iceberg via Uniform / Iceberg-REST).

This means:
- **No direct connection** from Databricks to L1 operational stores (security boundary).
- **Schema continuity** — same Avro/Protobuf schemas govern Iceberg tables; schema evolution flows through.
- **Replay** — Databricks ML training reads from Iceberg/Delta Lake cold storage; live features read via Kafka client.
- **Cost split** — L1 carries the durable transactional & decisioning load; Databricks carries the elastic analytical load. Each is best-fit.

#### 3.4 Off-Platform Targets Beyond Databricks
Same Tableflow pattern fans out to additional analytical destinations without re-reading the source-of-truth stores:

| Target | Use |
|--------|-----|
| **Databricks** | Lakehouse, ML training, ad-hoc analytics |
| **Snowflake** | Reporting, BI, regulatory submissions |
| **AWS S3 + Athena** | Long-term archive, on-demand queries |
| **Splunk / Dynatrace / Datadog** | Observability ([Audit Log SIEM Integration](audit-log-siem-integration.md)) |

### 4. Governance & Security

- **Schema Registry** is the canonical contract; all CDC connectors register Avro/Protobuf schemas; `compatibility.level` per tier.
- **RBAC** — service accounts per app, never per team; topic prefixes derived from [Topic Naming](topic-naming.md). MDS/RBAC on the L1 cluster; Confluent Cloud RBAC on the analytical mirror.
- **mTLS + OAUTHBEARER** end-to-end; FIPS 140-3 via CEX8S on L1 and the BCFIPS provider in JVMs.
- **Audit log** — forwarded from CC to SIEM via the [Audit Log SIEM Integration](audit-log-siem-integration.md) pattern. On-frame audit goes to the same SIEM via Confluent Platform audit-log topic.
- **Data residency** — operational data physically stays on the customer's L1 frames; only mirrored topics leave the perimeter. Per-topic mirror policy = governance hook for residency rules (e.g., EU customer data: do not mirror).

### 5. SLA Tier Mapping

| Workload | Stores | Tier | DR Target |
|----------|--------|------|-----------|
| Real-time payments | CockroachDB + Confluent + Flink | `critical` | RPO < 5 min (Cluster Linking + Cockroach multi-region) |
| Fraud / AML decisioning | Neo4j + Redis + Confluent + Flink (NNPA) | `critical` | RPO < 5 min |
| Regulatory reporting | PostgreSQL + Confluent (Tiered Storage to COS) | `compliance` | RPO = 0 (MRC on CP) |
| Customer profile / CRM | MongoDB | `standard` | RPO < 2 hr |
| Audit trail | Confluent compacted topics + Iceberg/Delta Lake | `compliance` | RPO = 0; infinite retention |

### MCP Validation Notes

| Claim | Source | Result |
|-------|--------|--------|
| MongoDB CDC Source (Debezium) is Confluent-managed in CC | confluent-docs CC connectors index | Confirmed |
| PostgreSQL CDC Source V2 (Debezium) is Confluent-managed in CC | confluent-docs CC connectors index + V1 EOL page | Confirmed: V1 EOL 2026-03-31; "Confluent recommends migrating to PostgreSQL CDC Source V2 (Debezium)" |
| Neo4j Sink is Confluent-managed in CC | confluent-docs CC connectors index | Confirmed |
| IBM MQ Source is Confluent-managed in CC | confluent-docs CC connectors index | Confirmed |
| CockroachDB CDC Connector availability | confluent-docs CC connectors index | Corrected: NOT in CC fully-managed catalog. Hub self-managed entry exists (`confluent.io/hub/cockroachdb/cockroach-cdc`); native CockroachDB changefeed → Kafka is the canonical mechanism |
| Tableflow output formats | confluent-docs llms.txt + Tableflow overview | Corrected: "Apache Iceberg™ and Delta Lake" — not Iceberg only |
| Analytics & ML | Databricks (off-platform) | `best-effort` (analytical replica) | Re-derivable from CL + Iceberg |

### 6. Why This Shape Works for FSI

- **One frame, full FIPS 140-3 footprint** — operational data, encryption, decisioning, and DR are all inside the same hardware certification and audit boundary.
- **Sub-ms decisioning** — Telum II in-process inference is unmatched on x86 because the network hop alone breaks the budget.
- **Vendor positioning** — IBM acquired Confluent (2026); the L1 + CP combination is now first-party, with IBM's "Confluent Platform for Z and LinuxONE" bundle.
- **Off-platform elasticity for analytics** — Databricks elastic compute, lakehouse format, MLOps maturity, and access to vendor data make it the right analytical home; pinning it to L1 would waste both the platform's strengths and L1's silicon.
- **Replayable from one source of truth** — Kafka Tiered Storage to IBM COS is the long-term immutable log; everything downstream (Iceberg, Databricks, Snowflake) is reproducible.

### 7. Anti-Patterns

- **Direct Databricks-to-operational-store JDBC pulls.** Breaks the audit boundary, blows the residency story, hammers OLTP locks. Always go through the event stream.
- **Mirroring all topics by default.** Use explicit topic policy; default to *not* mirroring sensitive PII unless residency rules permit.
- **Running combined-mode KRaft (controller + broker on same node).** Forbidden in production validation; see [LinuxONE Validation Suite §3.7](linuxone-validation-suite.md).
- **Using Redis as a system of record.** Redis is hot cache and ephemeral state only — Cockroach or Postgres is the SoR.
- **Skipping in-frame networking.** If brokers and producers are on the same frame and traffic still leaves via OSA, tuning is wrong — see [LinuxONE Kafka Tuning §LinuxONE Overlay](linuxone-kafka-tuning.md).
- **Off-platform AI for sub-ms decisioning.** GPU microservices over 10 GbE p99 at 5–15 ms; that misses the FSI `critical`/`market_data` tier targets entirely.

## Related

- [FSI Data Streaming Platform](concepts/fsi-data-streaming-platform.md) — the platform layer that this architecture deploys onto
- [LinuxONE Kafka Integration](concepts/linuxone-kafka-integration.md) — the frame-level mainframe-bridge precedent
- [LinuxONE Validation Suite](linuxone-validation-suite.md) — how to prove this works
- [LinuxONE Kafka Tuning](linuxone-kafka-tuning.md) — operational tuning for the event plane
- [LinuxONE Flink Validation & Tuning](linuxone-flink-validation-tuning.md) — the AI decisioning layer
- [SLA Tiers](concepts/sla-tiers.md) — tier mapping driving every governance default
- [DR — Cluster Linking](dr-cluster-linking.md) — DR mechanism for the event plane
- [FSI Exactly-Once Pattern](fsi-exactly-once.md) — durability bar across the whole stack
- [Audit Log SIEM Integration](audit-log-siem-integration.md) — observability boundary
