---
title: OracleXStreamSource Doesn't Support after.state.only
tags: [trip-wire, cdc, oracle, confluent-cloud, confluent-agent-skills]
sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/SKILL.md]
related: [concepts/cdc-source-connector-setup, concepts/tableflow-changelog-mode-immutability, patterns/cdc-tableflow-flink-decode-required]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/confluent-cloud-cdc-tableflow/SKILL.md
---

# OracleXStreamSource Doesn't Support after.state.only

## Summary

The `OracleXStreamSource` connector does **not** support the `after.state.only` configuration option. Where the PostgreSQL, MySQL, and SQL Server Debezium V2 connectors expose `after.state.only=true` to strip the CDC envelope and emit only post-image records, `OracleXStreamSource` rejects this config. To emit only post-image state from Oracle XStream, apply a Flink transform on the source topic before sinking to the downstream topic. Validated against confluent-docs via /wiki:ingest Step 3d on 2026-05-16.

## Detail

XStream is Oracle's native logical replication API (not Debezium's LogMiner path), and Confluent's managed `OracleXStreamSource` connector wraps it directly. The wrapper does not implement `after.state.only` — passing the config either has no effect or rejects on connector validation depending on connector version.

**Failure mode:** an engineer copies a `after.state.only=true` config from a working PostgreSQL CDC connector to a new Oracle XStream pipeline. Either (a) the connector starts but emits full Debezium envelopes regardless (silently), confusing downstream Flink jobs that expected stripped post-image records, or (b) the connector fails validation with a "Unknown configuration" error and never starts.

### Correct pattern — strip the envelope in Flink

Don't try to bypass the decode step. The canonical CDC-to-Tableflow pipeline already includes a Flink decode layer (see `patterns/cdc-tableflow-flink-decode-required`); use it to project post-image columns explicitly:

```sql
INSERT INTO `target_customers`
SELECT `id`, `name`, `email`, `created_at`
FROM `oracle-cdc.HR.CUSTOMERS`;
-- Flink auto-decodes the XStream envelope; selecting columns yields post-image only.
```

### Other XStream limitations to brief the operator on

The same upstream skill flags these alongside the `after.state.only` constraint — call them out together in customer engagements to avoid surprise:

- Only supports non-CDB architecture on Amazon RDS for Oracle
- Does NOT support Oracle Autonomous Databases or Oracle Standby (Data Guard)
- Does NOT support Downstream Capture
- Requires a valid Confluent license for XStream Out
- Database prerequisites: `enable_goldengate_replication=TRUE`, `ARCHIVELOG` mode, supplemental logging, XStream admin user with `DBMS_XSTREAM_AUTH` privileges, XStream outbound server created via `DBMS_XSTREAM_ADM.CREATE_OUTBOUND`

Reference: [Oracle XStream CDC Source prereqs validation](https://docs.confluent.io/cloud/current/connectors/cc-oracle-xstream-cdc-source/prereqs-validation.html).

## Related

- Parent: `concepts/cdc-source-connector-setup` — full database-prereq + connector-config + troubleshooting matrix for all five supported CDC sources.
- Sibling trip-wire: `concepts/tableflow-changelog-mode-immutability` — why getting Flink decode right matters end-to-end.
- Sibling trip-wire: `patterns/cdc-tableflow-flink-decode-required` — the load-bearing pattern that obviates the need for `after.state.only` shortcuts.

---

*Source: confluentinc/agent-skills@91d1871e · skills/confluent-cloud-cdc-tableflow/SKILL.md · Ingested 2026-05-16 (full MCP-validation gate per D-07) · Apache-2.0*
