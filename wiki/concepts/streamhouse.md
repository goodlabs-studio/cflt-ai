---
title: Streamhouse — Architecture, Purpose, and Confluent's Implementation
tags: [streamhouse, lightning-tables, real-time-context-engine, tableflow, confluent-cloud, flink, kafka, mcp, ai-agents, architecture, fsi]
sources: [https://developer.confluent.io/learn/streamhouse/, https://www.confluent.io/blog/aiven-confluent-redpanda-streamnative-and-ververica-form-streamhouse-working-group/, https://docs.confluent.io/cloud/current/lightning-tables/overview.md, https://docs.confluent.io/cloud/current/lightning-tables/query/overview.md, https://docs.confluent.io/cloud/current/lightning-tables/query/sql-reference.md, https://docs.confluent.io/cloud/current/lightning-tables/limitations.md, https://docs.confluent.io/cloud/current/ai/real-time-context-engine/overview.md]
related: [concepts/tableflow-iceberg-delta, patterns/cdc-to-tableflow-flink-decode, concepts/flink-confluent-cloud-setup, concepts/schema-registry-best-practices, patterns/fsi-l1-reference-architecture]
confidence: high
last_updated: 2026-11-04
last_validated: 2026-11-04
---

# Streamhouse — Architecture, Purpose, and Confluent's Implementation

## Summary

A **Streamhouse** is an architecture pattern, not a product. It is a real-time, production-native, decentralized data architecture that keeps the *current state of the business* continuously available to applications, analytics, and AI agents. The pattern has five stages: **capture → transport → transform → govern → serve**. The term was coined by Ververica. A vendor-neutral working group (Aiven, Confluent, Redpanda, StreamNative, Ververica) published a definition on 2026-09-15, and Confluent announced its own Streamhouse capabilities on 2026-11-04.

**Is it built on top of existing Confluent / Kafka? Yes.** Confluent's Streamhouse is the existing Confluent Cloud stack plus a new **Query** pillar:

- **Stream** — Kafka / Kora
- **Connect** — managed connectors / CDC
- **Process** — Flink
- **Govern** — Stream Governance
- **Query** (new) — groups Tableflow (existing), **Lightning Tables** (new), and the **Real-Time Context Engine** (an MCP interface over Lightning Tables).

Kafka topics remain the system of record. Every serving surface is a materialization of a topic.

## Detail

### Why it exists (the problem statement)

Lakehouses and warehouses were built for historical and reporting workloads. Confluent's argument is that when the operational systems, the lake, and the warehouse each hold a different view of "now", AI agents and applications act on stale or conflicting state.

Before Streamhouse, the usual fix was a separate sink for every consumer: a KV store or cache for apps, a warehouse for analytics, a vector DB for agents. Each sink has its own pipeline and its own governance gaps.

Streamhouse says: capture once, govern once near the source, then serve many shapes (stream, open table, low-latency query) from the same governed log. The working group frames Streamhouse as **complementary to the lakehouse, not a replacement**:

- **Lakehouse:** runs analysis over history.
- **Streamhouse:** runs the business as events happen.
- **Bridge:** the two exchange data through open table formats (Iceberg / Delta).

Confluent's own explainer is candid that the pattern is not new: "these architectures have been in use for years. What's new is the name." Treat Streamhouse as a vocabulary and positioning layer over the Kafka + Flink + Tableflow patterns this wiki already documents. The one genuinely new piece of product is Lightning Tables.

### The three defining attributes (working-group definition)

| Attribute | Meaning |
|---|---|
| Real-time | State stays current as events occur, not refreshed by periodic batch |
| Production-native | Built to production SLOs; governance and controls run in production, not on a separate copy |
| Decentralized | Meets data where it lives; no prerequisite to consolidate everything into one system |

The working group explicitly states that no single project or vendor portfolio *is* a Streamhouse by itself. It can be built from OSS, commercial products, or a mix. Redpanda, Pulsar, or Kinesis can fill the transport slot.

### Reference architecture — five stages

```text
 Operational systems (DBs, mainframe, SaaS, devices)
          │
   ┌──────▼──────┐   ┌────────────┐   ┌────────────┐   ┌──────────────────────────────┐
   │  CAPTURE    │──▶│ TRANSPORT  │──▶│ TRANSFORM  │──▶│           SERVE              │
   │ CDC/connect │   │ Kafka/Kora │   │ Flink /    │   │ • Streams (Kafka topics)     │
   │ (Debezium,  │   │ durable,   │   │ Kafka      │   │ • Open tables (Tableflow →   │
   │  managed    │   │ replayable │   │ Streams    │   │   Iceberg / Delta)           │
   │  connectors)│   │ log        │   │            │   │ • Low-latency query          │
   └─────────────┘   └────────────┘   └────────────┘   │   (Lightning Tables, RTCE)   │
   ════════════════════ GOVERN (spans all stages) ══════└──────────────────────────────┘
   Schema Registry / data contracts, quality rules,         │        │          │
   lineage, catalog, encryption, RBAC                     Apps   AI agents  Lakehouse/
                                                                            warehouse
```

| Stage | Role | Confluent Cloud component | Status |
|---|---|---|---|
| Capture | Pull changes from source systems as they happen | Managed connectors (150+), CDC; new hybrid connector management | Existing |
| Transport | Durable, replayable movement of events | Kafka on Kora engine | Existing |
| Transform | Filter, join, enrich, aggregate in flight | Confluent Cloud for Apache Flink; adds **batch execution** to bootstrap streaming jobs from existing data | Existing + enhancement |
| Govern | Schemas, contracts, quality, lineage, access control, applied once near the source | Stream Governance (SR, catalog, lineage, CSFLE/encryption, RBAC) | Existing |
| Serve / **Query** | Deliver state as streams, tables, or queries | Tableflow (analytics), **Lightning Tables** (apps), **Real-Time Context Engine** (agents via MCP) | Tableflow existing; LT + RTCE new |

### Lightning Tables — the new serving layer

This is the only truly new runtime component, so its constraints define what a Confluent Streamhouse can and cannot do today.

**What it is:** A fully managed, read-only materialization of a single Kafka topic, optimized for low-latency SQL lookups. You enable it per topic, so there are no consumers to write and no Flink jobs to manage. The docs state the table is updated **within 100 ms** of data arriving in the topic. Per Confluent's internal testing in the press release, query latency is 10–100 ms at 1,000+ QPS.

**Retention decoupling:** The Lightning Table persists independently of topic retention. A query can return rows that have already aged out of the topic. That matters for audit and retention reasoning; see the FSI notes.

**Ingestion mode is chosen automatically from `cleanup.policy`:**

| Topic `cleanup.policy` | Mode | Semantics |
|---|---|---|
| `delete` (default) | Append | Every record is queryable (event-log style) |
| includes `compact` | Upsert | Latest record per Kafka key, last-write-wins; a tombstone deletes the key, and a later record re-adds it |

The upsert-mode requirements are:
- a Kafka record key, which becomes the primary key;
- `compact` in `cleanup.policy`.

Key-schema changes are not supported.

**Eligibility:**
- Supported cluster types: Basic, Standard, Enterprise, and Dedicated, **on AWS only**.
- The topic must have a registered Avro, Protobuf, or JSON Schema.
- Topics using `INTERVAL`, `MULTISET`, `TIMESTAMP WITH TIME ZONE`, or `RAW` types cannot be enabled.

**Query surface (read-only, single table):**

| Supported | Not supported |
|---|---|
| Key lookups, `WHERE` filters (`= != < > <= >= IN NOT IN IS [NOT] NULL LIKE BETWEEN`), `AND`/`OR`, column selection, `ORDER BY`, `LIMIT` | Aggregates (`COUNT/SUM/AVG/MIN/MAX`), `GROUP BY`, **joins**, subqueries, set operators, DDL, DML |

```sql
-- Valid Lightning Table query: point/range read against one materialized topic
SELECT ORDERID, ITEMID, ORDERUNITS
FROM `orders`
WHERE ORDERUNITS > 5
ORDER BY ORDERTIME DESC
LIMIT 10;
```

Design consequence: **all joins and aggregations happen upstream in Flink.** Flink writes a pre-shaped, keyed, compacted topic, and the Lightning Table serves that. This is the same "decode/shape in Flink, then materialize" discipline as [CDC to Tableflow](../patterns/cdc-to-tableflow-flink-decode.md).

**Access interfaces:**

| Interface | Auth | Notes |
|---|---|---|
| HTTP API | Global API key | Large or long queries run asynchronously |
| MCP (via Real-Time Context Engine) | Global API key, CC sign-in, or OAuth | For AI agents |
| JDBC | Global API key | BI tools, Java apps |
| Confluent CLI | CC user sign-in | `confluent lightning query` |
| Cloud Console | CC user sign-in | Preview pane |

Over **private networking**, only API, MCP, and JDBC work through a private endpoint. Console and CLI queries do not.

**Lightning Table query vs Flink queries:**

| Query type | Runs | Use for |
|---|---|---|
| Lightning Table query | Once, sub-second | Point lookups and range scans from many concurrent apps/agents |
| Flink snapshot query | Once, then exits | Complex exploratory analysis over history |
| Flink streaming query | Continuously | Ongoing processing |

A Lightning Table query reads the materialized table, not the topic. It can therefore return different results from a Flink query on the same topic.

### Real-Time Context Engine

This is the **MCP server interface to Lightning Tables**, part of Confluent Intelligence. An agent connects via MCP, discovers enabled topics, inspects their schemas, and queries the latest state.

It is distinct from Confluent's *management* MCP servers (such as `mcp-confluent`). Those manage infrastructure; RTCE serves business data. Enabling a topic for RTCE simply means enabling a Lightning Table on that topic.

### Where Tableflow fits

Tableflow is unchanged by the announcement; it is now grouped under the Query pillar. It covers the analytical half of serving (Iceberg / Delta for lakehouses and warehouses), with minutes-level freshness. Lightning Tables cover the operational half (sub-second, high-concurrency lookups). The same governed topic can feed both. See [Tableflow](tableflow-iceberg-delta.md).

### Positioning notes

- **Not Confluent-exclusive as a term.** The name is free to use under Ververica's trademark commitment, and Redpanda, StreamNative, and Aiven are co-founders of the working group. Differentiate on implementation, not on the label. Confluent's edge is a managed serving layer (Lightning Tables + RTCE) plus Tableflow plus Stream Governance spanning all stages, with Flink in the same control plane. Vs. Redpanda and MSK, the canon competitive points still apply.
- **Analyst criticism (TechTarget, at launch):** the public definition is thin on reference implementations, and agent access still needs a dedicated governance/security layer.

### FSI considerations

- **Deployment scope.** Lightning Tables are **Confluent Cloud on AWS only**. There is no CP/CFK equivalent and no Azure/GCP support in the docs as of 2026-11-04. For on-prem or LinuxONE estates, a "Streamhouse" means Kafka + Flink + a self-managed serving store.
- **Auth posture.** API, JDBC, and MCP access use Global API keys (MCP also accepts OAuth). That falls short of the canon's "never username/password in FSI" stance for service-to-service access. Prefer OAuth where the interface allows it, scope access with RBAC, and route through private endpoints. Confirm with Confluent whether identity-pool / OAuth support extends to the API and JDBC paths (unverified).
- **Retention / right-to-erasure.** The Lightning Table outlives topic retention. A record deleted by `retention.ms` is *not* gone from serving. In upsert mode, only a tombstone removes a key. Erasure workflows must emit tombstones to compacted topics, and append-mode tables need a documented disable/re-enable story.
- **Regulatory reporting.** Lightning Tables are a read path. Exactly-once guarantees stop at the topic (EOS producers / Flink EOS writing it). Last-write-wins upsert gives you current state, not an audit history; keep the append-mode or Tableflow copy for the audit trail.
- **SLA tiers.** About 100 ms freshness plus 10–100 ms query latency fits the **<100 ms compliance** and **async** tiers. It does not fit the sub-ms market-data tier and is marginal for <10 ms risk. Keep risk lookups in-process or on Flink state.

### Open questions / unverified

- The underlying storage engine of Lightning Tables, and whether it is Kora-native or a separate store, is not documented.
- The exact ordering semantics behind "most recent record" in upsert mode are not stated; offset order is presumed.
- Region list, per-interface row limits (MCP limits are on a separate page), and pricing dimensions were not captured here. See `billing/dimensions/rtce` in the docs.

## Related

- [Tableflow — Kafka Topics as Iceberg and Delta Lake Tables](tableflow-iceberg-delta.md) — the analytical serve path inside the Query pillar
- [CDC to Tableflow — Flink Decode Pattern](../patterns/cdc-to-tableflow-flink-decode.md) — same "shape in Flink, then materialize" discipline Lightning Tables require
- [Flink on Confluent Cloud Setup](flink-confluent-cloud-setup.md) — the transform stage; where joins and aggregates must live
- [Schema Registry Best Practices](schema-registry-best-practices.md) — a registered schema is a hard prerequisite for Lightning Tables and Tableflow
- [FSI Reference Architecture — LinuxONE + Off-Platform Analytics](../patterns/fsi-l1-reference-architecture.md) — an existing Streamhouse-shaped topology under a different name
