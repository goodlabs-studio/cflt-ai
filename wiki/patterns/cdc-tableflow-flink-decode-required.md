---
title: Decode CDC With Flink Before Tableflow — Don't Sink Direct
tags: [trip-wire, pattern, tableflow, cdc, flink, confluent-cloud, confluent-agent-skills]
sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/SKILL.md]
related: [patterns/cdc-to-tableflow-flink-decode, concepts/tableflow-changelog-mode-immutability, concepts/cdc-source-connector-setup]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/confluent-cloud-cdc-tableflow/SKILL.md
---

# Decode CDC With Flink Before Tableflow — Don't Sink Direct

## Pattern

Never enable Tableflow on a raw CDC source topic. Debezium connectors with `tombstones.on.delete=true` (the default) emit null-value Kafka records on DELETE operations, and Tableflow's default `APPEND` mode suspends on the first null record with:

> *"Tableflow will be suspended because we detected a Kafka record with a null value."*

The canonical pattern: **CDC Source Topic → Flink INSERT → clean topic (`'changelog.mode' = 'upsert'`) → Tableflow**. The Flink decode layer interprets Debezium CDC semantics natively, translating DELETEs into proper retract/tombstone messages that upsert-mode Tableflow handles correctly. Validated against confluent-docs via /wiki:ingest Step 3d on 2026-05-16.

## When to Use

Every Confluent Cloud CDC-to-Tableflow pipeline. There is no "lightweight" variant — sinking Tableflow directly onto the CDC source topic is always wrong.

This applies to all five supported managed Debezium connectors: PostgreSQL CDC Source V2, MySQL CDC Source V2, SQL Server CDC Source V2, Oracle XStream CDC Source, and DynamoDB CDC Source.

## Caveats

**Do NOT use `after.state.only=true` as a shortcut.** It strips the Debezium envelope (removing `op`, `before`, `after` wrappers), but the DELETE-emits-null-record behavior persists — Tableflow APPEND still suspends on the first tombstone. Additionally, `OracleXStreamSource` does not support `after.state.only` at all (see `concepts/oracle-xstream-source-limitations`).

**Mode is immutable after first materialize.** Get the target topic's `'changelog.mode' = 'upsert'` right BEFORE the first INSERT runs — once Tableflow has materialized, the mode is sealed (see `concepts/tableflow-changelog-mode-immutability`). Recovery requires deleting both topics and recreating.

### Minimal correct Flink SQL

```sql
-- Decoded target topic (upsert mode is non-negotiable)
CREATE TABLE `target_customers` (
  `id` INT NOT NULL,
  `name` STRING,
  `email` STRING,
  PRIMARY KEY (`id`) NOT ENFORCED
) WITH ('changelog.mode' = 'upsert');

-- Continuous INSERT — Flink auto-discovers the CDC source table
INSERT INTO `target_customers`
SELECT `id`, `name`, `email`
FROM `postgres-cdc.public.customers`;
```

Then enable Tableflow on `target_customers`, not on `postgres-cdc.public.customers`.

## Related

- Parent: `patterns/cdc-to-tableflow-flink-decode` — the full decode-pattern pipeline including database prerequisites and tableflow config.
- Sibling trip-wire: `concepts/tableflow-changelog-mode-immutability` — the immutability constraint that makes the upsert-mode choice load-bearing.
- Parent for connector configs: `concepts/cdc-source-connector-setup`.

---

*Source: confluentinc/agent-skills@91d1871e · skills/confluent-cloud-cdc-tableflow/SKILL.md · Ingested 2026-05-16 (full MCP-validation gate per D-07) · Apache-2.0*
