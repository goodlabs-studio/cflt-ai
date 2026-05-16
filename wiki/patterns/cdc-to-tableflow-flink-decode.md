---
title: CDC to Tableflow — Flink Decode Pattern
tags: [tableflow, cdc, flink, confluent-cloud, iceberg, delta, confluent-agent-skills]
sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/flink-sql-patterns.md]
related: [concepts/exactly-once-semantics, concepts/flink-checkpointing, concepts/flink-confluent-cloud-setup, concepts/tableflow-changelog-mode-immutability, patterns/cdc-tableflow-flink-decode-required, concepts/cdc-source-connector-setup, concepts/schema-registry-best-practices]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/confluent-cloud-cdc-tableflow/references/flink-sql-patterns.md
---

# CDC to Tableflow — Flink Decode Pattern

## Summary

Canonical pipeline shape for streaming change-data-capture into a lakehouse via Confluent Cloud: Debezium source connector → Kafka raw CDC topic → Flink SQL decode (envelope strip + type conversion) → Kafka clean topic with `changelog.mode = upsert` → Tableflow on the clean topic → Iceberg/Delta. **Never enable Tableflow on the raw CDC topic** — tombstones break Tableflow's `APPEND` mode. The Flink decode layer is what makes the pipeline correct. Pairs with [CDC Source Connector Setup](../concepts/cdc-source-connector-setup.md) (pre-deploy and operational side) and surfaces the trip-wires that bite teams in production.

Sourced from `confluentinc/agent-skills@91d1871e` (Apache-2.0) — upstream maintains an eval gate at 90%+ pass before merge, so this article is `confidence: high` via source attestation rather than per-claim MCP re-validation. Trip-wire micro-articles in `wiki/concepts/` carry full MCP validation.

## Pattern

### Pipeline shape

```
Source DB ──Debezium CDC Source──▶ raw topic (CHANGELOG envelope)
                                    │
                                    ▼
                              Flink INSERT (decode + type-convert)
                                    │
                                    ▼
                                  clean topic (changelog.mode=upsert, with PRIMARY KEY)
                                    │
                                    ▼
                                  Tableflow → Iceberg/Delta
```

The clean topic is the **Tableflow handoff point**. Never enable Tableflow on the raw CDC topic — see [CDC Tableflow Flink Decode Required](cdc-tableflow-flink-decode-required.md) for the trip-wire.

### CDC source tables auto-discovered

CDC source tables are auto-discovered from Kafka topics with SR schemas — no manual `CREATE TABLE` for sources. Reference them with backtick-quoting: `` `postgres-cdc.public.customers` ``. All patterns work identically with `JSON_SR`, `AVRO`, and `PROTOBUF` formats. If a CDC table doesn't appear in `SHOW TABLES`, the connector may not have produced data yet — wait 2-5 minutes.

### Debezium type mappings

Debezium uses specific logical types that map to Flink types differently than you might expect:

| Debezium logical type | Flink column type | Conversion |
|---|---|---|
| `io.debezium.time.ZonedTimestamp` | `STRING` | None — already ISO 8601 string |
| `io.debezium.time.NanoTimestamp` | `BIGINT` | `TO_TIMESTAMP_LTZ(col / 1000000, 3)` |
| `io.debezium.time.MicroTimestamp` | `BIGINT` | `TO_TIMESTAMP_LTZ(col / 1000, 3)` |
| `io.debezium.time.Timestamp` | `BIGINT` | `TO_TIMESTAMP_LTZ(col, 3)` |
| `io.debezium.time.Date` | `INT` | Use as-is or convert |
| `io.debezium.time.MicroTime` | `BIGINT` | Use as-is or convert |
| `DECIMAL` / `NUMERIC` | `STRING` (with `decimal.handling.mode=string`) | Set connector config — without it, DECIMAL arrives as raw BYTES Flink cannot cast |
| `INTERVAL` (PG/Oracle) | `STRING` (with `interval.handling.mode=string`) | Set connector config for lossless ISO 8601 |
| Binary (`BYTEA`, `BLOB`) | `STRING` (with `binary.handling.mode=base64`) | Set connector config for JSON-safe encoding |

### Pattern 1 — Create target table (minimal WITH clause)

Target tables use a minimal WITH clause — no connector, format, bootstrap, or SR properties.

```sql
CREATE TABLE `target_customers` (
  `id` INT NOT NULL,
  `name` STRING,
  `email` STRING,
  `created_at` TIMESTAMP_LTZ(3),
  PRIMARY KEY (`id`) NOT ENFORCED
) WITH (
  'changelog.mode' = 'upsert'
);
```

Key points:

- Only `'changelog.mode' = 'upsert'` is needed in WITH for CDC pipelines.
- Do NOT add `'connector'`, `'value.format'`, `'properties.bootstrap.servers'`, or SR URL — these are not supported in CC Flink and will cause errors.
- Use `TIMESTAMP_LTZ(3)` (not `TIMESTAMP(3)`) for columns converted from Debezium MicroTimestamp/Timestamp.
- Define `PRIMARY KEY (...) NOT ENFORCED` to maintain upsert semantics.

### Pattern 2 — INSERT (CDC envelope decoded automatically)

CC Flink recognizes CDC changelog tables natively. You do NOT reference `after.*` fields or filter by `op` — Flink handles Debezium envelope decoding and CDC semantics (inserts, updates, deletes) automatically.

```sql
INSERT INTO `target_customers`
SELECT
  `id`,
  `name`,
  `email`,
  TO_TIMESTAMP_LTZ(`created_at` / 1000, 3)
FROM `postgres-cdc.public.customers`;
```

- Reference columns directly by name (`id`, not `after.id`).
- Flink automatically interprets the changelog stream — inserts, updates, deletes all handled.
- No `WHERE op IN ('c', 'u', 'r')` filter needed.

### Pattern 3 — Multi-table pipeline

For each captured table, create a target table (Pattern 1) and an INSERT (Pattern 2). **Each INSERT runs as a separate Flink statement** — they're independent continuous jobs.

```sql
INSERT INTO `target_customers`
SELECT `id`, `name`, `email`, TO_TIMESTAMP_LTZ(`created_at` / 1000, 3)
FROM `postgres-cdc.public.customers`;

INSERT INTO `target_orders`
SELECT `order_id`, `customer_id`, `amount`, TO_TIMESTAMP_LTZ(`order_date` / 1000, 3)
FROM `postgres-cdc.public.orders`;
```

### Pattern 4 — Filtering and transformation

```sql
-- Filter by column value
INSERT INTO `target_active_customers`
SELECT `id`, `name`, `email`, TO_TIMESTAMP_LTZ(`created_at` / 1000, 3)
FROM `postgres-cdc.public.customers`
WHERE `status` = 'active';

-- Add computed columns
INSERT INTO `target_customers_enriched`
SELECT
  `id`, `name`, `email`,
  TO_TIMESTAMP_LTZ(`created_at` / 1000, 3),
  CURRENT_TIMESTAMP AS `processed_at`,
  'flink-cdc-pipeline' AS `source_system`
FROM `postgres-cdc.public.customers`;

-- Join with reference data
INSERT INTO `target_orders_enriched`
SELECT o.`order_id`, o.`customer_id`, o.`region_id`, r.`region_name`, o.`amount`
FROM `postgres-cdc.public.orders` o
LEFT JOIN `dim_regions` r ON o.`region_id` = r.`region_id`;
```

### Pattern 5 — Schema evolution

When database schemas change:

```sql
-- 1. Stop the INSERT (via MCP: delete-flink-statements)
-- 2. Drop and recreate target with new columns
DROP TABLE `target_customers`;
CREATE TABLE `target_customers` (
  `id` INT NOT NULL,
  `name` STRING,
  `email` STRING,
  `phone` STRING,       -- new column
  `created_at` TIMESTAMP_LTZ(3),
  PRIMARY KEY (`id`) NOT ENFORCED
) WITH ('changelog.mode' = 'upsert');

-- 3. Recreate INSERT with the new column
INSERT INTO `target_customers`
SELECT `id`, `name`, `email`, `phone`, TO_TIMESTAMP_LTZ(`created_at` / 1000, 3)
FROM `postgres-cdc.public.customers`;
```

Tableflow caches the changelog mode at first materialization — see [Tableflow Changelog Mode Immutability](../concepts/tableflow-changelog-mode-immutability.md) for the immutability trip-wire and the full pipeline-reset procedure if you need to change it.

### Pattern 6 — Schemaless topics

If a topic has no schema in SR, Flink cannot auto-discover its structure. Preferred fix: register a schema in SR or use schema inference. If you need to work with the topic directly without a schema, use the raw BYTES approach:

```sql
ALTER TABLE `raw_topic` MODIFY (`key` STRING, `val` STRING);

INSERT INTO `target_customers`
SELECT
  JSON_VALUE(`val`, '$.id' RETURNING INT) AS `id`,
  JSON_VALUE(`val`, '$.name') AS `name`,
  JSON_VALUE(`val`, '$.email') AS `email`,
  TO_TIMESTAMP_LTZ(
    CAST(JSON_VALUE(`val`, '$.created_at') AS BIGINT) / 1000, 3
  ) AS `created_at`
FROM `raw_topic`;
```

More fragile than schema-based approaches (no type safety, no schema evolution), but useful for ad-hoc exploration.

### Pattern 7 — Multi-event topics

Multi-event topics (`RecordNameStrategy` / `TopicRecordNameStrategy`) can't be auto-discovered by Flink — split them by event type into typed target tables:

```sql
ALTER TABLE `shared_events` MODIFY (`key` STRING, `val` STRING);

-- Route orders to a typed target
INSERT INTO `target_orders`
SELECT
  JSON_VALUE(`val`, '$.order_id' RETURNING INT),
  JSON_VALUE(`val`, '$.customer_id' RETURNING INT),
  JSON_VALUE(`val`, '$.amount' RETURNING DOUBLE)
FROM `shared_events`
WHERE JSON_VALUE(`val`, '$.event_type') = 'order';

-- Route customers to a separate typed target
INSERT INTO `target_customers`
SELECT
  JSON_VALUE(`val`, '$.customer_id' RETURNING INT),
  JSON_VALUE(`val`, '$.name'),
  JSON_VALUE(`val`, '$.email')
FROM `shared_events`
WHERE JSON_VALUE(`val`, '$.event_type') = 'customer';
```

Each INSERT runs as a separate continuous Flink job. The target topics use `TopicNameStrategy` (the default for Flink-created topics), so each has a single schema and works normally with Tableflow.

**Long-term recommendation:** migrate to `TopicNameStrategy` with one topic per event type for anything that needs to flow into Tableflow.

### Statement management via MCP

Use `mcp__confluent__create-flink-statement` with:

| Parameter | Description |
|---|---|
| `statement` | The SQL text |
| `statementName` | Lowercase kebab-case (e.g., `cdc-create-target-customers`) |
| `environmentId` | The CC environment ID |
| `computePoolId` | The Flink compute pool ID |
| `catalogName` | Usually the environment display name |
| `databaseName` | The Kafka cluster display name |

Workflow:

1. `SHOW TABLES` → verify CDC source auto-discovered.
2. `CREATE TABLE` → target with upsert mode.
3. `INSERT INTO` → start continuous decode.
4. `read-flink-statement` → verify INSERT is running.

## When to Use

- Streaming database changes into an Iceberg/Delta lakehouse via Confluent Cloud.
- Need exactly-once or upsert semantics from CDC events for downstream analytics.
- Multi-table CDC pipelines where each table flows into its own Iceberg/Delta target.
- Schema-aware CDC pipelines (`JSON_SR`, `AVRO`, `PROTOBUF`) — not plain `JSON`.

## Caveats

- **Never enable Tableflow directly on the raw CDC source topic.** Tombstones (`tombstones.on.delete=true`) produce null Kafka records that suspend Tableflow in `APPEND` mode. See [CDC Tableflow Flink Decode Required](cdc-tableflow-flink-decode-required.md).
- **Changelog mode is immutable after first materialization.** Flipping APPEND ↔ UPSERT requires deleting Tableflow topic + Kafka topic + schemas, then recreating. See [Tableflow Changelog Mode Immutability](../concepts/tableflow-changelog-mode-immutability.md).
- **Do not use `'value.format'` / `'connector'` / SR-URL properties** in CC Flink `CREATE TABLE`. Cloud Flink handles format/connector automatically.
- **`TIMESTAMP(3)` is incompatible with `TO_TIMESTAMP_LTZ()`.** Use `TIMESTAMP_LTZ(3)` in target columns.
- **Connector-level data type issues** (DECIMAL garbled bytes, INTERVAL lossy values, binary breaking JSON, Oracle NUMBER structs, Oracle `after.state.only` unsupported) must be fixed at the connector, not in Flink SQL. See [CDC Source Connector Setup](../concepts/cdc-source-connector-setup.md) and [Oracle XStream Source Limitations](../concepts/oracle-xstream-source-limitations.md).
- **Subject name strategies:** `RecordNameStrategy` / `TopicRecordNameStrategy` break Flink auto-discovery and Tableflow. Use `TopicNameStrategy` (Debezium default).
- **Advisory warnings on INSERT** ("Primary key does not match upsert key", "Highly state-intensive operators without TTL") can be ignored — they don't prevent execution.

## Related

- [CDC Source Connector Setup](../concepts/cdc-source-connector-setup.md) — database prerequisites + connector configs + troubleshooting
- [Tableflow Changelog Mode Immutability](../concepts/tableflow-changelog-mode-immutability.md) — trip-wire on the cached changelog mode
- [CDC Tableflow Flink Decode Required](cdc-tableflow-flink-decode-required.md) — trip-wire on tombstone-breaks-APPEND
- [Oracle XStream Source Limitations](../concepts/oracle-xstream-source-limitations.md) — `after.state.only` unsupported
- [Exactly-Once Semantics](../concepts/exactly-once-semantics.md) — EOS across the pipeline
- [Flink Checkpointing](../concepts/flink-checkpointing.md) — checkpointing for the Flink decode step
- [Flink on Confluent Cloud — Setup, RBAC, Lifecycle, and Statement Evolution](../concepts/flink-confluent-cloud-setup.md) — CC Flink setup context
- [Schema Registry Best Practices](../concepts/schema-registry-best-practices.md) — TopicNameStrategy and SR operational surface

---

*Source: confluentinc/agent-skills@91d1871e · skills/confluent-cloud-cdc-tableflow/references/flink-sql-patterns.md · Ingested 2026-05-16 · Apache-2.0*
