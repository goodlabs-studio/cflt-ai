---
title: Tableflow Changelog Mode is Immutable After First Materialization
tags: [trip-wire, tableflow, changelog, confluent-cloud, confluent-agent-skills]
sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/SKILL.md]
related: [patterns/cdc-to-tableflow-flink-decode, patterns/cdc-tableflow-flink-decode-required, concepts/oracle-xstream-source-limitations]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/confluent-cloud-cdc-tableflow/SKILL.md
---

# Tableflow Changelog Mode is Immutable After First Materialization

## Summary

Once a Tableflow table has materialized in `APPEND` mode (the default) or `UPSERT` mode, the mode is **immutable**. You cannot switch a CHANGELOG-mode Tableflow table to APPEND mode (or vice versa) without recreating both the Tableflow topic AND the underlying Kafka topic from scratch. Validated against confluent-docs via /wiki:ingest Step 3d on 2026-05-16.

## Detail

Tableflow caches the changelog mode (`APPEND` or `UPSERT`) when it first materializes data. The S3 `table_path` is keyed by the Kafka topic name, so simply deleting and recreating the Tableflow topic reuses the same S3 path AND the cached mode state. Altering the Kafka topic's `changelog.mode` property after first materialization does not propagate.

Attempting to change the mode produces a runtime error:

> *"The changelog mode for this topic has been modified since table materialization began."*

Flip-flopping the mode further corrupts state with:

> *"Incompatible schema evolution detected."*

**Failure mode:** a customer wires up a CDC-to-Tableflow pipeline with the wrong `changelog.mode` (typically forgetting `'upsert'` on a CDC-decoded target table), Tableflow materializes a few records in APPEND, then suspends on the first DELETE tombstone. The natural remediation — flip the topic property to upsert — does not work, leaving the operator with a half-suspended pipeline and no in-place recovery path.

### Correct remediation (the only path)

1. Disable the Tableflow topic
2. Delete the underlying Kafka topic
3. Recreate the Kafka topic with `'changelog.mode' = 'upsert'` (or the intended mode) from the start
4. Re-enable Tableflow

### Correct Flink CREATE TABLE shape

```sql
CREATE TABLE `target_customers` (
  `id` INT NOT NULL,
  `name` STRING,
  `email` STRING,
  PRIMARY KEY (`id`) NOT ENFORCED
) WITH (
  'changelog.mode' = 'upsert'
);
```

Set `changelog.mode` **before** the first INSERT statement runs — once data lands in Tableflow, the mode is sealed.

## Related

- Parent: `patterns/cdc-to-tableflow-flink-decode` — the full Debezium → Flink → Tableflow pipeline pattern that depends on this constraint.
- Sibling trip-wire: `patterns/cdc-tableflow-flink-decode-required` — never enable Tableflow on a raw CDC topic (tombstones break APPEND immediately).
- Sibling trip-wire: `concepts/oracle-xstream-source-limitations` — XStream-specific reason this matters (no `after.state.only` shortcut).

---

*Source: confluentinc/agent-skills@91d1871e · skills/confluent-cloud-cdc-tableflow/SKILL.md · Ingested 2026-05-16 (full MCP-validation gate per D-07) · Apache-2.0*
