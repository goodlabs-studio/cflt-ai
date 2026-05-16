---
title: CDC Source Connector Setup
tags: [cdc, connect, confluent-cloud, oracle, postgres, mysql, sqlserver, dynamodb, confluent-agent-skills]
sources:
  - raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/database-prerequisites.md
  - raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/connector-configs.md
  - raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/troubleshooting.md
related: [patterns/cdc-to-tableflow-flink-decode, patterns/connect-deployment-models, concepts/oracle-xstream-source-limitations, concepts/schema-registry-best-practices]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path:
  - skills/confluent-cloud-cdc-tableflow/references/database-prerequisites.md
  - skills/confluent-cloud-cdc-tableflow/references/connector-configs.md
  - skills/confluent-cloud-cdc-tableflow/references/troubleshooting.md
---

# CDC Source Connector Setup

## Summary

Operational reference for deploying Debezium CDC source connectors on Confluent Cloud — covering all five supported databases (PostgreSQL, MySQL, SQL Server, Oracle XStream, DynamoDB) in the order an operator actually needs them: database prerequisites first (what to set up before the connector can be deployed), then connector configuration recipes (the JSON templates you actually paste), then troubleshooting (the symptoms you'll hit when something is wrong). The merge order mirrors the operational reading order: pre-deploy → deploy → debug.

Sourced from `confluentinc/agent-skills@91d1871e` (Apache-2.0) — upstream maintains an eval gate at 90%+ pass before merge, so this article is `confidence: high` via source attestation rather than per-claim MCP re-validation. Trip-wire micro-articles in `wiki/concepts/` carry full MCP validation.

This article is one half of the CDC-to-Tableflow story. The operational counterpart is [CDC to Tableflow — Flink Decode Pattern](../patterns/cdc-to-tableflow-flink-decode.md), which covers the pipeline shape and Flink decode patterns. Read this when setting up the source; read that when designing the decode.

## Detail

### Section 1 — Database prerequisites

Each database requires specific configuration to support CDC. Get this right before deploying the connector.

#### PostgreSQL

Required configuration (`postgresql.conf`, restart required):

```
wal_level = logical
max_replication_slots = 4    # at least 1 per connector
max_wal_senders = 4          # at least 1 per connector
```

Required permissions and publication:

```sql
ALTER USER <connector_user> WITH REPLICATION;
GRANT CONNECT ON DATABASE <database> TO <connector_user>;
GRANT USAGE ON SCHEMA <schema> TO <connector_user>;
GRANT SELECT ON ALL TABLES IN SCHEMA <schema> TO <connector_user>;
ALTER DEFAULT PRIVILEGES IN SCHEMA <schema> GRANT SELECT ON TABLES TO <connector_user>;

CREATE PUBLICATION dbz_publication FOR TABLE table1, table2, table3;
```

Cloud-specific:

- **AWS RDS/Aurora:** set `rds.logical_replication = 1`, reboot, use master user or `rds_replication` role.
- **GCP Cloud SQL:** set `cloudsql.logical_decoding = on`, restart, grant `cloudsqlsuperuser`.
- **Azure DB for PostgreSQL:** set `wal_level = logical`, `max_replication_slots >= 4`, restart.

**Replication slot cleanup (critical):** Deleting a connector does NOT drop its replication slot. Orphaned slots hold WAL segments indefinitely; the DB eventually fills up and goes read-only.

```sql
-- List active slots
SELECT slot_name, active,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained_wal
FROM pg_replication_slots;

-- Drop orphaned slot (only when active = false)
SELECT pg_drop_replication_slot('debezium_slot');
```

Alert on `pg_wal_lsn_diff` growing beyond a threshold (e.g., 1 GB) for any inactive slot.

#### MySQL

Required configuration (`my.cnf`, restart required):

```
log_bin = mysql-bin
binlog_format = ROW
binlog_row_image = FULL
gtid_mode = ON                       # recommended
enforce_gtid_consistency = ON        # recommended
binlog_expire_logs_seconds = 604800  # 7 days minimum
```

Required permissions:

```sql
CREATE USER '<connector_user>'@'%' IDENTIFIED BY '<password>';
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO '<connector_user>'@'%';
GRANT LOCK TABLES ON <database>.* TO '<connector_user>'@'%';
GRANT SELECT ON <database>.* TO '<connector_user>'@'%';
FLUSH PRIVILEGES;
```

**`LOCK TABLES` on managed MySQL:** Managed services (RDS, Aurora, Cloud SQL, Azure) don't grant `SUPER`, so Debezium can't use `FLUSH TABLES WITH READ LOCK` and falls back to per-table `LOCK TABLES`. Without this grant, the connector fails during snapshot.

#### SQL Server

SQL Server Agent must be running for CDC to work.

```sql
USE <database_name>;
EXEC sys.sp_cdc_enable_db;

EXEC sys.sp_cdc_enable_table @source_schema = N'dbo',
                              @source_name = N'<table_name>',
                              @role_name = NULL,
                              @supports_net_changes = 1;

CREATE LOGIN <connector_user> WITH PASSWORD = '<password>';
CREATE USER <connector_user> FOR LOGIN <connector_user>;
GRANT SELECT ON SCHEMA :: dbo TO <connector_user>;
GRANT SELECT ON SCHEMA :: cdc TO <connector_user>;
GRANT VIEW DATABASE STATE TO <connector_user>;
EXEC sp_addrolemember N'db_datareader', N'<connector_user>';
```

On AWS RDS SQL Server, use `EXEC msdb.dbo.rds_cdc_enable_db '<database_name>'` instead of `sys.sp_cdc_enable_db`.

#### Oracle XStream

**Supported:** Self-managed Oracle 19c+, Amazon RDS for Oracle (non-CDB architecture only).
**NOT supported:** Autonomous Databases, Data Guard standby, downstream capture, CDB on RDS.
**Licensing:** Requires a valid Confluent license for Oracle XStream Out.

Seven steps:

1. **Enable GoldenGate replication** — `ALTER SYSTEM SET enable_goldengate_replication=TRUE SCOPE=BOTH;` (on RDS, set in DB parameter group and reboot).
2. **Enable ARCHIVELOG mode** — `ALTER DATABASE ARCHIVELOG;` (on RDS, enabled automatically when automated backups are turned on).
3. **Configure supplemental logging** — minimal (`ALTER DATABASE ADD SUPPLEMENTAL LOG DATA`) plus per-table ALL-columns (`ALTER TABLE ... ADD SUPPLEMENTAL LOG DATA (ALL) COLUMNS`).
4. **Create XStream admin user and grant privileges:**
   ```sql
   CREATE USER xstream_admin IDENTIFIED BY <password>;
   GRANT CREATE SESSION, SET CONTAINER TO xstream_admin;

   BEGIN
     DBMS_XSTREAM_AUTH.GRANT_ADMIN_PRIVILEGE(
       grantee => 'xstream_admin',
       privilege_type => 'CAPTURE',
       grant_select_privileges => TRUE
     );
   END;
   /
   ```
5. **Create XStream outbound server** (name must match the connector's `database.out.server.name`):
   ```sql
   BEGIN
     DBMS_XSTREAM_ADM.CREATE_OUTBOUND(
       server_name => 'dbz_outbound',
       table_names => '<SCHEMA>.<TABLE1>,<SCHEMA>.<TABLE2>',
       source_database => '<database_name>'
     );
   END;
   /
   ```
6. **Create connector user and grant permissions** — `CREATE SESSION`, `SET CONTAINER`, `SELECT ON V_$DATABASE`, `SELECT ON V_$INSTANCE`, `FLASHBACK ANY TABLE`, `SELECT_CATALOG_ROLE`, `EXECUTE_CATALOG_ROLE`, `SELECT ANY TABLE`, `LOCK ANY TABLE`. Then `DBMS_XSTREAM_ADM.ALTER_OUTBOUND(server_name=>'dbz_outbound', connect_user=>'<connector_user>')`.
7. **Verify complete setup** — check `enable_goldengate_replication=TRUE`, `LOG_MODE=ARCHIVELOG`, `SUPPLEMENTAL_LOG_DATA_MIN=YES`, outbound server `ATTACHED` or `ENABLED`.

The connector configuration ties to these prerequisites via `database.out.server.name` (Step 5), `database.processor.licenses` (the license count), and `database.user` (Step 6 user).

#### DynamoDB

Enable DynamoDB Streams on the table:

```bash
aws dynamodb update-table \
  --table-name <table-name> \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES
```

Use `NEW_AND_OLD_IMAGES` for full CDC.

**IAM permissions — critical:** the CDC phase requires write permissions for a KCL-style checkpointing table. Without `CreateTable`, `PutItem`, `GetItem`, `UpdateItem`, `DeleteItem`, snapshot works but CDC streaming silently fails (no real-time changes captured).

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DynamoDBReadAndCheckpointing",
      "Effect": "Allow",
      "Action": [
        "dynamodb:DescribeTable", "dynamodb:DescribeStream",
        "dynamodb:DescribeTimeToLive", "dynamodb:DescribeContinuousBackups",
        "dynamodb:DescribeLimits", "dynamodb:GetRecords",
        "dynamodb:GetShardIterator", "dynamodb:ListStreams",
        "dynamodb:ListTables", "dynamodb:ListGlobalTables",
        "dynamodb:ListTagsOfResource", "dynamodb:Scan",
        "dynamodb:CreateTable", "dynamodb:PutItem", "dynamodb:GetItem",
        "dynamodb:UpdateItem", "dynamodb:DeleteItem",
        "dynamodb:DeleteTable", "dynamodb:TagResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "TagAndCloudWatch",
      "Effect": "Allow",
      "Action": ["tag:GetResources", "cloudwatch:PutMetricData"],
      "Resource": "*"
    }
  ]
}
```

---

### Section 2 — Connector configuration recipes

After prerequisites are met, paste these JSON templates. All connectors share common settings; per-database specifics follow.

**Preferred deployment method:** Use `mcp__confluent__create-connector` with `connectorName`, `environmentId`, `clusterId`, `connectorConfig` (a flat map of string key-value pairs).

`kafka.api.key` / `kafka.api.secret` in the connector config must be scoped to the target Kafka cluster.

#### Common configuration elements

```json
{
  "connector.class": "<connector-class>",
  "name": "<connector-name>",
  "topic.prefix": "<topic-prefix>",

  "kafka.api.key": "<KAFKA_API_KEY>",
  "kafka.api.secret": "<KAFKA_API_SECRET>",

  "output.data.format": "JSON_SR",
  "output.key.format": "JSON_SR",

  "decimal.handling.mode": "string",
  "binary.handling.mode": "base64",

  "tasks.max": "1"
}
```

**REQUIRED: `topic.prefix`** — controls topic naming. All CDC V2 connectors require it. Topics are named `{topic.prefix}.{schema}.{table}`.

**Schema format options:**

- `JSON_SR` (recommended default) — JSON with Schema Registry. Human-readable payloads, easy to debug.
- `AVRO` — binary, 30-50% smaller than JSON_SR. Best for high-throughput production CDC.
- `PROTOBUF` — binary, strongly typed with nested message support. Good when downstream consumers are already on Protobuf.

| Criterion | JSON_SR | AVRO | PROTOBUF |
|---|---|---|---|
| Debug readability | Best — human-readable | Poor — binary | Poor — binary |
| Throughput / msg size | Largest payloads | ~30-50% smaller | ~30-50% smaller |
| Flink auto-discovery | Yes | Yes | Yes |
| Tableflow compatibility | Yes | Yes | Yes |
| Schema evolution | Supported via SR | Best via SR | Supported via SR |

All three use Schema Registry and work with Flink auto-discovery and Tableflow. The choice is payload size vs. debuggability.

**Important:** `output.data.format` and `output.key.format` must both use a SR-backed format. Plain `JSON` (no SR) means no schema is registered, breaking Flink auto-discovery and Tableflow.

Managed connectors take 2-5 minutes to provision. The connector shows `tasks: []` until provisioning completes — poll until tasks appear.

#### PostgreSQL CDC Source V2

**Connector class:** `PostgresCdcSourceV2`

```json
{
  "connector.class": "PostgresCdcSourceV2",
  "name": "cdc-pipeline-skill-postgres-connector",

  "kafka.api.key": "${file:/secrets.properties:KAFKA_API_KEY}",
  "kafka.api.secret": "${file:/secrets.properties:KAFKA_API_SECRET}",

  "database.hostname": "<postgres-host>",
  "database.port": "5432",
  "database.user": "<postgres-user>",
  "database.password": "<postgres-password>",
  "database.dbname": "<database-name>",
  "database.server.name": "<logical-server-name>",
  "topic.prefix": "<topic-prefix>",

  "table.include.list": "<schema>.<table1>,<schema>.<table2>",

  "plugin.name": "pgoutput",
  "publication.name": "dbz_publication",
  "slot.name": "debezium_slot",

  "output.data.format": "JSON_SR",
  "output.key.format": "JSON_SR",

  "snapshot.mode": "initial",
  "tombstones.on.delete": "true",

  "heartbeat.interval.ms": "30000",
  "heartbeat.action.query": "INSERT INTO heartbeat (ts) VALUES (NOW())",

  "decimal.handling.mode": "string",
  "binary.handling.mode": "base64",
  "interval.handling.mode": "string",
  "hstore.handling.mode": "map",

  "tasks.max": "1"
}
```

Topic pattern: `{topic.prefix}.{schema}.{table}` — e.g., `postgres-cdc.public.users`.

#### MySQL CDC Source V2

**Connector class:** `MySqlCdcSourceV2`

```json
{
  "connector.class": "MySqlCdcSourceV2",
  "name": "cdc-pipeline-skill-mysql-connector",

  "kafka.api.key": "${file:/secrets.properties:KAFKA_API_KEY}",
  "kafka.api.secret": "${file:/secrets.properties:KAFKA_API_SECRET}",

  "database.hostname": "<mysql-host>",
  "database.port": "3306",
  "database.user": "<mysql-user>",
  "database.password": "<mysql-password>",
  "database.server.id": "184054",
  "database.server.name": "<logical-server-name>",
  "topic.prefix": "<topic-prefix>",

  "database.include.list": "<database-name>",
  "table.include.list": "<database>.<table1>,<database>.<table2>",

  "output.data.format": "JSON_SR",
  "output.key.format": "JSON_SR",

  "snapshot.mode": "initial",
  "tombstones.on.delete": "true",
  "include.schema.changes": "false",
  "gtid.source.includes": ".*",

  "decimal.handling.mode": "string",
  "binary.handling.mode": "base64",

  "tasks.max": "1"
}
```

`table.include.list` format: `database.table` (not `schema.table`). Topic pattern: `{topic.prefix}.{database}.{table}`.

#### SQL Server CDC Source V2

**Connector class:** `SqlServerCdcSourceV2`

```json
{
  "connector.class": "SqlServerCdcSourceV2",
  "name": "cdc-pipeline-skill-sqlserver-connector",

  "kafka.api.key": "${file:/secrets.properties:KAFKA_API_KEY}",
  "kafka.api.secret": "${file:/secrets.properties:KAFKA_API_SECRET}",

  "database.hostname": "<sqlserver-host>",
  "database.port": "1433",
  "database.user": "<sqlserver-user>",
  "database.password": "<sqlserver-password>",
  "database.names": "<database-name>",
  "database.server.name": "<logical-server-name>",
  "topic.prefix": "<topic-prefix>",

  "table.include.list": "dbo.<table1>,dbo.<table2>",

  "output.data.format": "JSON_SR",
  "output.key.format": "JSON_SR",

  "snapshot.mode": "initial",
  "tombstones.on.delete": "true",
  "include.schema.changes": "false",

  "decimal.handling.mode": "string",
  "binary.handling.mode": "base64",

  "tasks.max": "1"
}
```

`table.include.list` format: `schema.table` (use `dbo` for the default schema).

#### Oracle XStream CDC Source

**Connector class:** `OracleXStreamSource`

```json
{
  "connector.class": "OracleXStreamSource",
  "name": "cdc-pipeline-skill-oracle-connector",

  "kafka.api.key": "${file:/secrets.properties:KAFKA_API_KEY}",
  "kafka.api.secret": "${file:/secrets.properties:KAFKA_API_SECRET}",

  "database.hostname": "<oracle-host>",
  "database.port": "1521",
  "database.user": "<oracle-user>",
  "database.password": "<oracle-password>",
  "database.dbname": "<service-name-or-sid>",
  "database.service.name": "<service-name-or-sid>",
  "database.server.name": "<logical-server-name>",
  "topic.prefix": "<topic-prefix>",

  "database.connection.adapter": "xstream",
  "database.out.server.name": "dbz_outbound",
  "database.processor.licenses": "1",

  "table.include.list": "<schema>.<table1>,<schema>.<table2>",

  "output.data.format": "JSON_SR",
  "output.key.format": "JSON_SR",

  "snapshot.mode": "initial",
  "tombstones.on.delete": "true",

  "decimal.handling.mode": "string",
  "binary.handling.mode": "base64",
  "interval.handling.mode": "string",

  "tasks.max": "1"
}
```

Oracle-specific:

- `database.service.name` **required.**
- `database.processor.licenses` **required.**
- `table.include.list` uses UPPERCASE: `SCHEMA.TABLE`.
- Oracle `NUMBER`/`FLOAT` without precision produces a `VariableScaleDecimal` struct — `decimal.handling.mode: string` fixes this.
- **`after.state.only` is NOT supported** by `OracleXStreamSource` — do not use this option. See [Oracle XStream Source Limitations](oracle-xstream-source-limitations.md) for the workaround pattern.

Topic pattern: `{topic.prefix}.{schema}.{table}` — e.g., `oracle-cdc.HR.EMPLOYEES`.

#### DynamoDB CDC Source

**Connector class:** `DynamoDbCdcSource`

```json
{
  "connector.class": "DynamoDbCdcSource",
  "name": "cdc-pipeline-skill-dynamodb-connector",

  "kafka.api.key": "${file:/secrets.properties:KAFKA_API_KEY}",
  "kafka.api.secret": "${file:/secrets.properties:KAFKA_API_SECRET}",

  "aws.access.key.id": "<aws-access-key>",
  "aws.secret.access.key": "<aws-secret-key>",

  "dynamodb.service.endpoint": "https://dynamodb.<aws-region>.amazonaws.com",
  "dynamodb.table.discovery.mode": "INCLUDELIST",
  "dynamodb.table.sync.mode": "SNAPSHOT_CDC",
  "dynamodb.table.includelist": "<table1>,<table2>",

  "output.data.format": "JSON_SR",

  "dynamodb.cdc.max.poll.records": "5000",
  "dynamodb.snapshot.max.poll.records": "1000",

  "tasks.max": "1"
}
```

Property names are `dynamodb.table.includelist` (one word), NOT `table.include.list` like the SQL connectors. A single DynamoDB table is processed by one task — `tasks.max` should equal the number of tables in `dynamodb.table.includelist`.

#### Configuration best practices

**Data type serialization** — always include these for interoperability:

| Setting | Default | Problem | Recommended |
|---|---|---|---|
| `decimal.handling.mode` | `precise` | DECIMAL serialized as raw bytes | `string` |
| `binary.handling.mode` | `bytes` | Breaks JSON serialization | `base64` |
| `interval.handling.mode` (PG/Oracle) | `numeric` | Microsecond approximation, lossy | `string` |
| `hstore.handling.mode` (PG) | `json` | HSTORE as JSON string | `map` |

Database quirks: MySQL `TINYINT(1)` → INT16 (not BOOLEAN); MySQL `BIGINT UNSIGNED` overflows at 2^63; SQL Server `DATETIMEOFFSET` → STRING; Oracle `NUMBER` (no precision) → `VariableScaleDecimal` struct (fixed by `decimal.handling.mode = string`).

**Secrets management:**

```json
{
  "database.password": "${file:/path/to/secrets.properties:DB_PASSWORD}",
  "kafka.api.key": "${file:/path/to/secrets.properties:KAFKA_API_KEY}"
}
```

**Snapshot modes:**

- `initial` — recommended for new connectors (snapshot then stream).
- `never` — no historical data, only new changes.
- `schema_only` — schema only, then stream changes. Use for pipeline validation on large tables.
- `always` — testing only, not production.

For large tables (100 M+ rows), validate end-to-end with `schema_only` first, then recreate with `initial`. The initial snapshot can lock the source DB, burst-produce to Kafka, and trigger SR rate limits.

**Subject name strategy:** Use `TopicNameStrategy` (Debezium default). `RecordNameStrategy` and `TopicRecordNameStrategy` break Flink auto-discovery and Tableflow.

---

### Section 3 — Troubleshooting (symptom → fix triage)

| Symptom | Likely cause | Fix |
|---|---|---|
| Connector creation fails with "topic.prefix is required" | Missing required field | Add `"topic.prefix": "<prefix>"` |
| `tasks: []` after 5+ min | Still provisioning OR failed | Poll `read-connector` every 30-60 s; investigate failures only after 5 min |
| Connector status `FAILED` immediately | DB connectivity / auth / wrong DB name / CDC not enabled / SR misconfigured / invalid config | See per-database verification queries below |
| **MySQL: "LOCK TABLES privilege required"** during snapshot | Managed MySQL (RDS/Aurora, Cloud SQL, Azure) restricts `SUPER` | `GRANT LOCK TABLES ON <database>.* TO '<connector_user>'@'%'`; recreate connector |
| Snapshot takes hours / unclear if pipeline is broken | Large tables (100 M+ rows) — normal | Check `read-connector` (tasks assigned?), `list-schemas` (schemas registered = producing?). For initial validation, use `snapshot.mode: schema_only`. |
| CDC connector broken after Kafka topic deletion | Connector lost its position (offsets, binlog LSN, etc.) | Delete connector entirely → recreate. **Never delete CDC source topics while connector is running.** |
| **DynamoDB: snapshot works, CDC silently fails** | IAM user missing checkpointing table write permissions | Update IAM policy to include `CreateTable`, `PutItem`, `GetItem`, `UpdateItem`, `DeleteItem`; delete + recreate connector |
| Connector runs but no messages | Initial snapshot still in progress; `table.include.list` filter excludes all (case sensitivity); `snapshot.mode = never` with no recent changes | Check `list-schemas(subjectPrefix)`; verify filter; check snapshot mode |
| **Orphaned PostgreSQL replication slot after delete** | Replication slot NOT auto-dropped on connector delete; holds WAL | `SELECT pg_drop_replication_slot('debezium_slot');` |
| Flink `CREATE TABLE` fails: "Unsupported format: avro-confluent" | Explicit format specs not supported in CC Flink | Remove all format/connector/bootstrap/SR properties; use only `'changelog.mode' = 'upsert'` |
| Flink INSERT type mismatch on timestamp | Debezium MicroTimestamp is BIGINT, not TIMESTAMP | Use `TIMESTAMP_LTZ(3)` in target; `TO_TIMESTAMP_LTZ(col / 1000, 3)` in INSERT |
| CDC source table not in `SHOW TABLES` | Connector hasn't produced data yet (still provisioning/snapshotting) | Verify tasks; verify schemas exist; wait 2-5 min; check `databaseName` matches cluster display name |
| Flink statement name invalid | Must be lowercase kebab-case `[a-z0-9]([-a-z0-9]*[a-z0-9])?`, max 100 chars | Rename |
| **Tableflow suspended: null value on APPEND topic** | CDC `tombstones.on.delete=true` produces nulls; Tableflow APPEND mode can't handle | **Never enable Tableflow on CDC source topic.** Use Flink decode → clean topic with `changelog.mode = upsert` → Tableflow. `after.state.only=true` and `record_failure_strategy: SKIP` do NOT work. See [CDC Tableflow Flink Decode Required](../patterns/cdc-tableflow-flink-decode-required.md). |
| **Tableflow error: changelog mode modified** | Mode is cached at first materialization; cannot change | Delete Tableflow topic + Kafka topic + schemas; recreate with `'changelog.mode' = 'upsert'` from creation. See [Tableflow Changelog Mode Immutability](tableflow-changelog-mode-immutability.md). |
| Tableflow incompatible schema evolution: nullable → non-nullable | Multiple changelog mode flips corrupted S3 state | Full pipeline reset — delete Tableflow topic, Kafka topic, schemas; recreate |
| Tableflow fails to activate | Wrong topic format (must be plain JSON_SR or Avro, not Debezium envelope); BYOB IAM permissions; cluster type | Decode envelope before writing to target; check Provider Integration / IAM; verify cluster tier supports Tableflow |
| Flink DEGRADED: "Schema ID N not found" after schema delete | Old messages reference deleted schema IDs | Clean reset in order: delete Flink statements → delete connector → delete source topics → hard-delete schemas → drop replication slot (PG) → recreate connector |
| **SR rejects new schema after column drop/type change** | Default compatibility `BACKWARD` rejects removed fields | Set `FULL_TRANSITIVE` for CDC subjects (or globally — affects non-CDC) |
| Topic has no schema, Flink can't auto-discover | Topic produced with plain `JSON` (no SR serializer) | Register a JSON schema in SR (partial schemas work); use schema inference; or use Flink raw BYTES |
| Multi-event topic, Flink can't auto-discover | `RecordNameStrategy` / `TopicRecordNameStrategy` instead of `TopicNameStrategy` | Split into typed target tables via Flink (see [CDC to Tableflow — Flink Decode Pattern](../patterns/cdc-to-tableflow-flink-decode.md) Pattern 7) |
| **DECIMAL columns appear as garbled bytes** | Default `decimal.handling.mode = precise` outputs raw bytes | `"decimal.handling.mode": "string"` on connector; recreate connector. Flink cannot CAST VARBINARY to DECIMAL — must be fixed at connector. |
| INTERVAL columns produce wrong values | Default `interval.handling.mode = numeric` is microsecond approximation | `"interval.handling.mode": "string"` for ISO 8601 |
| Binary columns produce garbled JSON | Default `binary.handling.mode = bytes` breaks JSON | `"binary.handling.mode": "base64"` |
| Oracle `NUMBER` without precision produces struct | Debezium serializes as `VariableScaleDecimal` | `"decimal.handling.mode": "string"` |

#### Verification queries (database-level)

PostgreSQL:

```sql
SHOW wal_level;                          -- must be 'logical'
SHOW max_replication_slots;              -- >= 1
SELECT * FROM pg_publication_tables WHERE pubname = 'dbz_publication';
SELECT slot_name, active,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained_wal
FROM pg_replication_slots;
```

MySQL:

```sql
SHOW VARIABLES LIKE 'log_bin';           -- must be ON
SHOW VARIABLES LIKE 'binlog_format';     -- must be ROW
SHOW VARIABLES LIKE 'gtid_mode';         -- should be ON
SHOW GRANTS FOR '<connector_user>'@'%';
```

SQL Server:

```sql
SELECT name, is_cdc_enabled FROM sys.databases;
SELECT name, is_tracked_by_cdc FROM sys.tables WHERE is_tracked_by_cdc = 1;
EXEC sys.sp_cdc_help_jobs;
```

Oracle:

```sql
SELECT VALUE FROM V$PARAMETER WHERE NAME = 'enable_goldengate_replication';   -- TRUE
SELECT LOG_MODE FROM V$DATABASE;                                                -- ARCHIVELOG
SELECT SUPPLEMENTAL_LOG_DATA_MIN, SUPPLEMENTAL_LOG_DATA_ALL FROM V$DATABASE;
SELECT SERVER_NAME, CONNECT_USER, STATUS FROM ALL_XSTREAM_OUTBOUND;
```

DynamoDB:

```bash
aws dynamodb describe-table --table-name <table-name> | jq '.Table.StreamSpecification'
```

## Related

- [CDC to Tableflow — Flink Decode Pattern](../patterns/cdc-to-tableflow-flink-decode.md) — operational counterpart pipeline shape
- [Oracle XStream Source Limitations](oracle-xstream-source-limitations.md) — trip-wire on `after.state.only`
- [Tableflow Changelog Mode Immutability](tableflow-changelog-mode-immutability.md) — trip-wire on cached changelog mode
- [CDC Tableflow Flink Decode Required](../patterns/cdc-tableflow-flink-decode-required.md) — trip-wire on tombstone-breaks-APPEND
- [Kafka Connect Deployment Models](../patterns/connect-deployment-models.md) — Connect deployment patterns
- [Schema Registry Best Practices](schema-registry-best-practices.md) — TopicNameStrategy and SR operational surface

---

*Source: confluentinc/agent-skills@91d1871e · skills/confluent-cloud-cdc-tableflow/references/{database-prerequisites,connector-configs,troubleshooting}.md · Ingested 2026-05-16 · Apache-2.0*
