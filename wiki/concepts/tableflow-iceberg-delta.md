---
title: Tableflow — Kafka Topics as Iceberg and Delta Lake Tables
tags: [tableflow, iceberg, delta-lake, confluent-cloud, lakehouse, schema-registry, fsi]
sources: [outputs/reports/confluent-best-practices-quickstart.md]
related: [patterns/cdc-to-tableflow-flink-decode, concepts/tableflow-changelog-mode-immutability, patterns/cdc-tableflow-flink-decode-required, concepts/schema-registry-best-practices, patterns/fsi-l1-reference-architecture, concepts/network-connectivity-by-tier]
confidence: high
last_updated: 2026-05-18
last_validated: 2026-05-18
---

# Tableflow — Kafka Topics as Iceberg and Delta Lake Tables

## Summary

Tableflow is a Confluent Cloud feature that materializes Kafka topics as Apache Iceberg or Delta Lake tables in object storage, with automated schematization, type conversion, schema evolution, compaction, snapshot management, and catalog publishing. It replaces the hand-rolled "object-store sink connector → compaction job → small-file cleanup → catalog sync" pipeline with one switch on a topic. Iceberg and Delta Lake materializations are both generally available; the analytical surface is read-only and intentionally near-real-time (minutes, not sub-second). Tableflow stays on the analytical side of the operational/analytical seam — Kafka remains the system of record.

## Detail

### What Tableflow materializes

Tableflow continuously converts records on a Kafka topic into Parquet files and publishes them as either Iceberg or Delta Lake tables. Schema Registry is the source of truth for table schemas, so only SR-managed topics (Avro, Protobuf, or JSON Schema) are eligible — schemaless / raw-bytes topics are not supported.

| Format | Internal file format | Generally available | Storage model |
|---|---|---|---|
| Apache Iceberg | Parquet | Yes | Managed storage **or** BYOS |
| Delta Lake | Parquet | Yes | **BYOS only** (no Confluent-managed storage option) |

Tables surface as **read-only** — analytics engines (Snowflake, Databricks, BigQuery, Trino, Athena, Spark, DuckDB, Flink) read them directly without data duplication.

### Storage models — managed vs BYOS

- **Confluent-managed storage:** Confluent provisions and operates the object bucket for the Iceberg tables. Fastest to stand up; less control over residency and cost surface.
- **BYOS (Bring Your Own Storage):** the customer's S3 / ADLS bucket holds the Parquet + table metadata. Required for Delta Lake. Preferred for FSI because it keeps data inside the customer's account boundary, residency controls, and key-management posture.

> ⚠️ unverified — the quickstart that originally queued this article used the term "BYOB"; the current Confluent docs canonically refer to this as **BYOS (Bring Your Own Storage)**. Use BYOS.

The IAM role Tableflow assumes needs both bucket-write and catalog-write permissions in the target account. A common failure mode is granting bucket-write but not the catalog-side trust policy, which silently breaks table publication.

### Schema mapping and evolution

- Avro, Protobuf, and JSON Schema records are converted to the Iceberg/Delta type system automatically.
- Schema changes are governed by the topic's Schema Registry **compatibility mode** — Tableflow propagates compatible evolutions (additive `BACKWARD`-style changes) automatically.
- Incompatible changes surface as a failed mapping or a new column shape; the operational lever is to keep the topic's compatibility mode tight (`BACKWARD` for entity streams, `FULL` for shared contracts) so breaks fail at registration, not at materialization.
- See [Schema Registry Best Practices](schema-registry-best-practices.md) for compatibility-by-tier guidance.

### Catalog integration

Tableflow publishes table metadata to external catalogs so analytics engines can discover the tables without manual registration. Supported targets:

| Catalog | Engines that consume it |
|---|---|
| AWS Glue | Athena, EMR, Redshift Spectrum, downstream Spark |
| Databricks Unity Catalog | Databricks (Delta and Iceberg via UniForm) |
| Snowflake Open Catalog (Apache Polaris) | Snowflake, Spark, Trino, Flink |
| Apache Polaris | Any Polaris-aware engine |
| Built-in Iceberg REST Catalog (IRC) | Any engine that speaks Iceberg REST — no external catalog required |

For FSI deployments, the built-in IRC is the lowest-blast-radius starting point because it removes a third-party trust-policy surface; Glue or Unity get added later as the analytics consumers land.

### Table maintenance

Tableflow handles the operational burden that hand-rolled Iceberg/Delta pipelines normally accumulate:

- **Compaction** of the small Parquet files emitted by continuous streaming, on a managed cadence.
- **Snapshot retention** — Tableflow keeps a **minimum of 10 and maximum of 100 snapshots** automatically; no manual snapshot expiry job needed.
- **Metadata publishing** to the configured catalog on each commit.

This is the part that justifies Tableflow over a self-managed `S3 Sink Connector + Spark compaction job` stack: the "small files problem" goes away by default. See `synthesis/confluent-gotchas-top-20.md` (gotcha #13) for the failure mode this is preventing.

### Availability surface

| Surface | Tableflow availability |
|---|---|
| Confluent Cloud — AWS | Supported |
| Confluent Cloud — Azure | Supported |
| Confluent Cloud — **Google Cloud** | **Not available** |
| Confluent Platform (self-managed) | **Not available** — cloud-only |
| Confluent for Kubernetes (CFK) | Not available — cloud-only |

The Google Cloud and CP gaps are significant for FSI shops with multi-cloud or hybrid footprints — if the source topics live on CP or on CC-GCP, the canonical analytical bridge is **Cluster Linking → CC-AWS or CC-Azure → Tableflow**, which is the shape used in [FSI Reference Architecture — LinuxONE + Off-Platform Analytics](../patterns/fsi-l1-reference-architecture.md).

### Operational characteristics

- **Near-real-time, not sub-second.** Latency is measured in minutes — Tableflow is an analytical sink, not an operational read path. For low-latency consumption, read the Kafka topic directly.
- **Read-only tables.** Writes only come from the upstream topic. There is no Iceberg/Delta INSERT path back into Tableflow.
- **Backfill window = topic retention.** Tableflow reads the topic, not a separate history store. Only data still within the topic's retention materializes. For full history, either set infinite retention on the source topic or seed the table from a compaction-cleaned "current state" topic.
- **Partitioning.** Iceberg tables should be partitioned on a sensible low-cardinality column (date, region, tier) for query pruning. Tableflow honors partition hints; pick them at table-create time.

### CDC pairing

The dominant production use case is Change Data Capture into a lakehouse. Tableflow on the **raw** Debezium topic doesn't work — Debezium emits null-value tombstones on DELETE, and Tableflow's default APPEND mode suspends on the first tombstone. The canonical shape is:

```
Source DB ──Debezium──▶ raw CDC topic ──Flink decode──▶ clean topic (changelog.mode=upsert) ──Tableflow──▶ Iceberg / Delta
```

See:
- [CDC to Tableflow — Flink Decode Pattern](../patterns/cdc-to-tableflow-flink-decode.md) — the canonical pipeline.
- [Tableflow Changelog Mode Immutability](tableflow-changelog-mode-immutability.md) — the mode is sealed on first materialization; flipping APPEND ↔ UPSERT requires recreating both topics.
- [CDC Tableflow Flink Decode Required](../patterns/cdc-tableflow-flink-decode-required.md) — the trip-wire elaborated.

### Triage

| Symptom | Likely cause | First move |
|---|---|---|
| Table not updating | Source topic has no new data; schema not registered in SR; topic was deleted/recreated; IAM role lost bucket or catalog write | Check topic produce rate, SR subject, IAM trust policy and bucket policy |
| Schema-evolution surprise (new column / failed mapping) | Incompatible change slipped past SR compatibility mode | Tighten the topic's compatibility mode; the failed change should have failed at SR registration |
| Glue / Unity catalog errors | Tableflow IAM role missing catalog-write or trust policy | Re-check the integration's role; bucket-write alone is not enough |
| "Where's my history?" | Only data within the topic's current retention materializes | Set infinite retention or seed from a compacted current-state topic |
| Reader incompatibility | Engine doesn't support the Iceberg v2 / Delta reader features Tableflow emits | Confirm engine version against Iceberg / Delta reader matrix |
| Tableflow suspended on a CDC topic | Tableflow was enabled on the raw Debezium topic; tombstones broke APPEND | Move Tableflow to a clean topic produced by Flink decode (see [CDC to Tableflow](../patterns/cdc-to-tableflow-flink-decode.md)) |

## Related

- [CDC to Tableflow — Flink Decode Pattern](../patterns/cdc-to-tableflow-flink-decode.md) — canonical pipeline shape
- [Tableflow Changelog Mode Immutability](tableflow-changelog-mode-immutability.md) — mode is sealed on first materialization
- [CDC Tableflow Flink Decode Required](../patterns/cdc-tableflow-flink-decode-required.md) — trip-wire on never enabling Tableflow on raw CDC topics
- [Schema Registry Best Practices](schema-registry-best-practices.md) — compatibility-mode governance that drives Tableflow's schema-evolution behavior
- [FSI Reference Architecture — LinuxONE + Off-Platform Analytics](../patterns/fsi-l1-reference-architecture.md) — Cluster Linking → CC Tableflow → Databricks bridge for FSI workloads
- [Network Connectivity by Cluster Tier](network-connectivity-by-tier.md) — networking context for Tableflow when source CC clusters use PrivateLink

---

*Compiled directly from confluent-docs MCP (Tableflow overview, Iceberg + Delta Lake materialization pages, catalog integration overview, schema and storage concept pages) on 2026-05-18 via /wiki:ingest. All verifiable claims (formats, GA status, catalog targets, snapshot bounds, BYOS scope, GCP/CP exclusions, schemaless-topic exclusion, near-real-time latency, read-only surface) validated against the live docs. One inline ⚠️ unverified marker on the BYOB→BYOS terminology correction. confidence: high.*
