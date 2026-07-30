> Part of **Flink Center of Excellence — Managed Flink on Confluent Cloud** (self-contained series). Validated against Confluent documentation 2026-07-30.

# Part 1 — Overview

## What this is

This guide is the foundation for a Flink Center of Excellence / Center for Enablement (COE/C4E) built on **Managed Flink on Confluent Cloud (CC)** — the serverless Flink SQL / Table API offering. It is intentionally *not* about a specific use case: it establishes the environment, guardrails, and best practices so that when workloads arrive, the platform, security model, networking, and cost controls are already correct.

The single most important thing to internalize: **CC Flink is a governed subset of Apache Flink / Confluent Platform (CP) Flink SQL.** Several statements you would reach for on open-source (OSS) Flink or CP-Flink (managed by Confluent Manager for Apache Flink, "CMF") are unsupported or behave differently on CC — and one of them (`DROP TABLE`) deletes real Kafka data. See "Anticipated blockers" at the end of this part.

## Where CC Managed Flink sits

There are three ways to run Flink against Confluent. The one-line decision:

| Model | Surface | Who owns the engine | Choose it when |
|---|---|---|---|
| **CC Managed Flink** (this COE) | Flink **SQL + Table API** only | Confluent — serverless; no checkpoint / state-backend / parallelism knobs | New SQL/Table workloads on Confluent Cloud; zero engine ops |
| **CMF** (Confluent Manager for Apache Flink) on Kubernetes | **Full Flink** — SQL, Table *and* DataStream API, custom JARs | You — checkpointing, state backend, parallelism, HA | On CP/Kubernetes already; need DataStream/custom code |
| **Self-managed OSS Flink** | Full Flink | You + community support | Genuine open-source freedom / unsupported connectors |

The COE's scope is the first row. If a use case later needs the DataStream API, custom operators, or arbitrary JARs, that is a signal to escalate to CMF — **CC cannot do those.**

## The CC Flink mental model (what differs from OSS/CMF)

CC maps Confluent Cloud objects onto Flink concepts automatically. This is the biggest day-one adjustment for engineers coming from OSS/CMF:

- **Catalog = environment, database = cluster, table = Kafka topic.** Every topic in the cluster is already a queryable table, with its key/value schema mapped from Schema Registry. You rarely write `CREATE TABLE` — use it only to customize a schema, set a non-default serialization format, set changelog mode, or run `CREATE TABLE AS SELECT`. A topic with no registered schema is exposed as raw `BINARY` key/value.
- **Compute pools, sized in CFUs (Confluent Flink Units).** Statements run in a compute pool with a maximum-CFU ceiling. Autoscaling ("Autopilot") scales resources within that ceiling based on statement parallelism. Pools **scale down to zero** when no statement is running (no cost at rest).
- **`'connector' = 'confluent'`** — a single connector covers both append and upsert behavior. On OSS/CMF you would write `'kafka'` or `'upsert-kafka'`; that syntax does not apply on CC.
- **Default watermark strategy + `$rowtime` system column.** CC applies a default watermark (fixed out-of-orderness tolerance ~180 ms) to every table, based on the `$rowtime` column (the Kafka record timestamp). Override it with `ALTER TABLE` only when your out-of-orderness materially exceeds that (for example, batch-loaded historical data). CC is event-time by default.
- **Schema Registry: Avro, JSON Schema (JSON_SR), and Protobuf** are all supported natively (OSS Flink supports only Avro with Schema Registry). `INFORMATION_SCHEMA` exists on CC (it does not in OSS).
- **Configuration options are a remapped subset.** CC exposes only the necessary subset of Flink options, under `sql.*` names. Port OSS configs through this mapping — do not assume the OSS name works:

| Confluent Cloud | Apache Flink (OSS/CP) |
|---|---|
| `sql.state-ttl` | `table.exec.state.ttl` |
| `sql.tables.scan.startup.mode` | `scan.startup.mode` |
| `sql.tables.scan.idle-timeout` | `table.exec.source.idle-timeout` |
| `sql.local-time-zone` | `table.local-time-zone` |

## Environment setup best practices (do these before use cases land)

- **Compute pools per team/environment boundary**, not one shared pool — isolation and billing clarity. Pool exhaustion parks statements in `PENDING`. A default pool (up to 50 CFU) is auto-provisioned on first use; create dedicated pools to isolate production. Suggested starting ceilings: **5–10 dev / 10–20 staging / 20–50 prod.**
- **Service accounts per application, never per person.** Humans get RBAC role bindings; applications get service accounts and API keys. Production statements should run *as a service account* — see Part 3.
- **Naming and governance up front** — topic/table naming `<domain>.<entity>.<event>`; Schema Registry compatibility `BACKWARD` by default, Avro or Protobuf (JSON only for prototype). Carry the environment/team in pool and statement names for cost attribution.
- **Dead-letter handling on source tables** — CC Flink supports a managed DLQ via the source table property `error-handling.mode = 'log'` (with `error-handling.log.target = '<table>'`), which routes records CC cannot deserialize to a DLQ table instead of failing the statement. **Scope caveat:** it catches *source deserialization* errors only — not errors in user-defined functions, serialization, or windowed aggregations.
- **Networking decided before the first statement** — for FSI this is PrivateLink. The client→Flink control-plane path is private; Flink→Kafka traffic stays internal to Confluent Cloud. See Part 4.
- **Baseline defaults that apply to every statement:** bounded watermarks plus an idleness timeout; `sql.state-ttl` on every non-windowed stateful operator; the `confluent` connector for changelog output; tumbling windows preferred over sliding/session; `sql.tables.scan.startup.mode = earliest-offset` for deterministic replay.
- **Canonical topology:** `Producers → raw landing topic → Flink SQL (filter/transform) → output topic`. "Direct to Flink" does not exist on CC — Flink is compute over Kafka only. External data must enter via a connector or producer first.

## Anticipated blockers & FSI gotchas

Flag these now — several surface the moment engineers port OSS/CMF habits:

| Blocker | Why it bites | Mitigation |
|---|---|---|
| **`DROP TABLE` deletes the underlying Kafka topic + all data + Schema Registry subjects** (default `TopicNameStrategy`) | On OSS it is metadata-only. On CC it destroys regulated data in one statement — a genuine incident risk. | RBAC: withhold table-drop from developer roles; change-control any `DROP`. `RecordNameStrategy` / `TopicRecordNameStrategy` preserve subjects but still drop the topic. |
| **Unsupported statements:** `DELETE`, `UPDATE`, `TRUNCATE`, `ANALYZE`, `CALL`, `JAR`, `LOAD`/`UNLOAD`, and catalog/database `CREATE`/`DROP`/`ALTER` | Engineers assume full SQL DML/DDL. CC is append/stream-oriented; no row mutation. | Model as streams/changelogs. Escalate genuinely-needed cases to CMF. |
| **No DataStream API and no custom JARs on CC** | Custom operators / arbitrary Java are impossible on CC. | If a use case needs it → CMF, not CC. Decide the runtime per use case. |
| **No processing-time operations** (`PROCTIME()`, `TUMBLE_PROCTIME`, etc.) | Event-time only. Porting processing-time jobs fails. | Use event-time (`$rowtime`) — better for regulatory determinism anyway. |
| **Limited `ALTER TABLE`** — only change the watermark strategy, add a metadata column, or change a parameter value | Structural alters available on OSS are not on CC. | Evolve schemas through Schema Registry, not `ALTER TABLE`. |
| **Windowing only via Table-Valued-Function syntax** (`TUMBLE`/`HOP`/`SESSION`/`CUMULATE` as TVFs) | Legacy grouped-window syntax is rejected. | Write window TVFs from the start. |
| **State without TTL runs away; CFU cost follows state and throughput** | The #1 CC Flink cost surprise. | `sql.state-ttl` on every unbounded stateful operator (see Part 2). |
| **A Flink statement needs a principal** to run as | Terraform fails with `error creating Flink Statement: one of provider.flink principal id … must be set`. | Set the service-account principal on the provider or the resource (see Part 3). |
| **`SHOW CREATE TABLE` output is not a re-runnable script** | Re-running yields a Schema-Registry subject-mismatch error, easily misread as a schema-incompatibility problem. | Do not use it as a migration script. |

---
