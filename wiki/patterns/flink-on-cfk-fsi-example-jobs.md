---
title: Flink-on-CFK FSI Example Jobs
tags: [flink, cmf, cfk, linuxone, fsi, s390x, mtls, avro-confluent, tumbling-window, temporal-join]
sources:
  - fsi-dsp://accelerator/confluent-on-linuxone
related:
  - patterns/flink-runtime-models
  - concepts/flink-checkpointing
  - concepts/linuxone-platform-foundations
  - patterns/linuxone-on-cfk-reference-architecture
  - concepts/s390x-custom-image-build-pipeline
  - patterns/auditor-readonly-rbac-payload-isolation
confidence: high
last_updated: 2026-05-23
last_validated: 2026-05-23
---

# Flink-on-CFK FSI Example Jobs

## Summary

Two canonical FSI Flink jobs that ship with the LinuxONE accelerator (layer 05):
a 1-minute tumbling-window transaction-volume aggregation, and an
account-transaction temporal stream-table enrichment join against a compacted
`customer-profile` lookup. Both run as `FlinkApplication` CRs against a
CMF-managed Flink compute environment, use mTLS to Kafka via cert-manager
Certificate CRs signed by the `confluent-ca-issuer` registered by layer 02,
read/write Avro-Confluent over an `https://` Schema Registry URL, and are
audited automatically by layer 01's `ConfluentServerAuthorizer` with **no
layer-04 change required**.

Source of truth: `fsi-dsp://accelerator/confluent-on-linuxone` (layer 05 —
`apply_sequence` `05-flink`) — DESIGN.md L176–200 (layer-05 detail) and
README.md L96–115 (layer-05 rationale + prerequisites).

## Layer 05 architecture

Layer 05 is a **resources-only** Kustomize Component (no `patches:` block).
Flink is a Kafka client — it adds new CRs rather than mutating existing CFK
CRs. The component contributes:

| CR | Purpose |
|----|---------|
| `FlinkEnvironment` | CMF-managed Flink compute context (s390x nodeAffinity, RocksDB state backend, Prometheus reporter port 9249, mTLS cert volume mount) |
| `CMFRestClass` | mTLS-secured CFK → CMF control channel (CFK submits, cancels, savepoints FlinkApplications via CMF REST) |
| `FlinkApplication` × 2 | Two example jobs (described below) |
| `ConfigMap` × 2 | SQL scripts mounted into each FlinkApplication |
| `ConfluentRolebinding` × 4 | `flink-developer` (group → FlinkEnvironmentAdmin); 3 `flink-job-runtime-*` (SA → DeveloperRead source / DeveloperWrite sink / DeveloperRead SR) |
| `Certificate` × 2 | `cmf-tls` and `flink-kafka-client-tls`, both `issuerRef: confluent-ca-issuer` (no new PKI) |
| `KafkaTopic` × 2 | Output topics — `flink.output.corebanking.txn-volume-1m`, `flink.output.fraud.enriched-transaction` |

Per-overlay sizing patches live in `overlays/{dev,prod}/kustomization.yaml`:

- **prod**: EXACTLY_ONCE semantics, `parallelism: 2`, `checkpointing.interval: 30000ms`
- **dev**: AT_LEAST_ONCE, `parallelism: 1`, `checkpointing.interval: 60000ms`

## Example job 1 — 1-minute transaction-volume tumbling window

FSI use case: real-time transaction-volume aggregation by domain, feeding
risk/compliance dashboards and alert thresholds.

```sql
CREATE TABLE account_transaction (
  transaction_id  STRING,
  account_number  STRING,
  amount          DECIMAL(15, 2),
  transaction_type STRING,
  `timestamp`     TIMESTAMP(3),
  WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '5' SECOND
) WITH (
  'connector'        = 'kafka',
  'topic'            = 'corebanking.transactions.v1.account-transaction',
  'value.format'     = 'avro-confluent',
  'value.avro-confluent.url' = 'https://schemaregistry.confluent.svc.cluster.local:8081',
  -- mTLS keystore + truststore on both Kafka client AND SR REST client
  'properties.security.protocol' = 'SSL',
  ...
);

CREATE TABLE txn_volume_1m (...) WITH ('connector' = 'kafka', ...);

INSERT INTO txn_volume_1m
SELECT window_start, window_end, COUNT(*), SUM(amount), AVG(amount), MIN(amount), MAX(amount)
FROM TABLE(TUMBLE(TABLE account_transaction, DESCRIPTOR(`timestamp`), INTERVAL '1' MINUTE))
GROUP BY window_start, window_end;
```

**WATERMARK** is `BOUNDED_OUT_OF_ORDERNESS` with a 5-second bound — never
unbounded, per the Confluent Canon Flink SQL rule. `scan.startup.mode =
'earliest-offset'` enables deterministic replay for regulatory recompute.

## Example job 2 — Account-transaction enrichment (temporal stream-table join)

FSI use case: enrich the real-time transaction stream with `customer-profile`
attributes (risk rating, KYC status, country code) for fraud detection. Uses
Flink SQL's `FOR SYSTEM_TIME AS OF` temporal join semantics against a compacted
lookup topic.

```sql
CREATE TABLE customer_profile (
  account_number STRING PRIMARY KEY NOT ENFORCED,
  risk_rating    STRING,
  kyc_status     STRING,
  country_code   STRING
) WITH ('connector' = 'kafka', 'topic' = 'corebanking.customers.v1.customer-profile', ...);

INSERT INTO enriched_transaction
SELECT
  txn.transaction_id, txn.account_number, txn.amount, txn.transaction_type, txn.`timestamp`,
  cust.risk_rating, cust.kyc_status, cust.country_code
FROM account_transaction AS txn
JOIN customer_profile
  FOR SYSTEM_TIME AS OF txn.`timestamp` AS cust
ON txn.account_number = cust.account_number;
```

**Temporal join requirements** (all three must hold):
1. `customer-profile` topic must have `cleanup.policy=compact` (compacted lookup table)
2. `customer-profile` schema must define a `PRIMARY KEY` field
3. JOIN ON clause must include the primary-key column

Memory sizing: the enrichment task carries larger state than pure aggregation
(customer-profile lookup cache) — `taskManager.resource.memory: 8192m` in the
sample CR, vs `4096m` for the tumbling-window job.

## mTLS — keystore AND truststore required

Both example FlinkApplications use **mutual TLS** (keystore + truststore), not
truststore-only, because layer 02 enables
`listeners.internal.authentication.type: mtls` on every broker. A truststore-only
client gets handshake-rejected.

The mTLS material is delivered via two cert-manager Certificate CRs both
referencing the existing `confluent-ca-issuer` ClusterIssuer (registered by
layer 02 — no new PKI):

- `cmf-tls` — CFK → CMF control channel
- `flink-kafka-client-tls` — Flink → Kafka data channel (mounted into the
  FlinkApplication pod at `/opt/certs/keystore.jks` + `/opt/certs/truststore.jks`)

Two subtle SQL points the SQL itself documents:

1. **The Kafka client SSL config is separate from the SR REST client SSL
   config.** The avro-confluent format uses its own `CachedSchemaRegistryClient`
   that does NOT inherit `properties.ssl.*` — you must set
   `value.avro-confluent.ssl.{keystore,truststore}.{location,password,type}`
   explicitly.
2. **JKS keystore type required** — both `properties.ssl.keystore.type = 'JKS'`
   and `value.avro-confluent.ssl.keystore.type = 'JKS'` on every WITH clause.

## RBAC bindings (4 total)

Layer 05 contributes its own RBAC, self-contained — no layer-01 change required
(the principles enforced are layer-01 patterns; the bindings are layer-05's
responsibility):

| Role | Principal | Resource |
|------|-----------|----------|
| `FlinkEnvironmentAdmin` | LDAP group `flink-developer` | FlinkEnvironment `fsi-flink-env` |
| `DeveloperRead` | SA `flink-job-runtime-source` | source topics (PREFIXED `corebanking.`) + consumer group |
| `DeveloperWrite` | SA `flink-job-runtime-sink` | sink topics (PREFIXED `flink.output.`) |
| `DeveloperRead` | SA `flink-job-runtime-sr` | SR subjects (PREFIXED) |

Note this is **service-account-per-runtime-concern**, not per-job. Three SAs
cover the read/write/SR access surface for all Flink jobs in the environment.

## Audit integration — no layer-04 change required

This is the load-bearing architectural property of layer 05: Flink's Kafka
access is audited **automatically** by the layer-04 audit pipeline.

The mechanism:
1. Flink mTLS handshake establishes the principal identity (`CN` from the cert)
2. Every topic access goes through layer-01's `ConfluentServerAuthorizer`
3. `ConfluentServerAuthorizer` emits an authz-decision event for every access
4. Layer 04's `confluent.security.event.router.config` routes the event to
   `confluent-audit-log-events`

So a Flink job reading `corebanking.transactions.v1.account-transaction`
produces an audit event in `confluent-audit-log-events` identifying the SA
(`flink-job-runtime-source`), the topic, the timestamp, and the decision (ALLOW).
The auditor (`patterns/auditor-readonly-rbac-payload-isolation`) can review the
audit topic and see every Flink access — without having permission to consume
the underlying business topic.

## Prerequisites

| Prereq | How it lands |
|--------|--------------|
| FKO (Flink Kubernetes Operator) | `ansible-playbook ansible/playbooks/flink_operators.yml` (RUNBOOK Step 1b) |
| CMF (Confluent Managed Flink) Helm operator | Same playbook (parallel install) |
| Custom s390x SQL-runner image (G-12) | `docker buildx --platform linux/s390x` — see `concepts/s390x-custom-image-build-pipeline` |
| Encrypted checkpoint storage (G-13) | OCP encrypted StorageClass OR S3-compatible with SSE-KMS |
| confluent-ca-issuer ClusterIssuer | Registered by layer 02 (must apply before layer 05) |
| layer 01 RBAC | ConfluentServerAuthorizer must be active for audit integration |

FKO + CMF are **Helm operators outside the Kustomize build** (KNOWN-GAPS G-10).
Applying `kustomize build overlays/prod` without them first produces
`no kind "FlinkApplication" is registered` from the API server. The playbook
provides a `--check` audit-only mode for compliance verification.

## Per-overlay sizing patches

```yaml
# overlays/prod/kustomization.yaml — example
patches:
  - patch: |-
      - op: replace
        path: /spec/job/parallelism
        value: 2
      - op: replace
        path: /spec/flinkConfiguration/execution.checkpointing.interval
        value: "30000"
    target:
      kind: FlinkApplication
      name: fsi-txn-volume-tumbling-window
```

Same component, different operational shape per environment — the audit-grade
reproducibility property of the accelerator (one buildable artifact per env)
holds.

## Confluent Canon alignment

- **Table API over DataStream API** (Canon §3): Flink SQL is Table API by default
- **Watermark `BOUNDED_OUT_OF_ORDERNESS`** (Canon §3): both jobs use `INTERVAL '5' SECOND`
- **`scan.startup.mode = 'earliest-offset'`** (Canon §3): explicit on every CREATE TABLE
- **Tumbling > sliding > session windows** (Canon §3): tumbling 1-minute used
- **mTLS + RBAC** (Canon §3 Security): mTLS via cert-manager, RBAC via ConfluentRolebinding

## Related

- `patterns/flink-runtime-models` — CMF as one of three Flink runtime options
- `concepts/flink-checkpointing` — checkpoint mechanics; G-13 encryption requirement
- `concepts/linuxone-platform-foundations` — s390x platform foundations under the runtime
- `patterns/linuxone-on-cfk-reference-architecture` — layer 05 in the 5-layer composition
- `concepts/s390x-custom-image-build-pipeline` — building the SQL-runner image
- `patterns/auditor-readonly-rbac-payload-isolation` — audit-trail consumer of Flink access events

## Provenance

- DESIGN.md L176–200 (layer 05 detail block — CMF compute env, FlinkApplications, mTLS, RBAC, audit integration)
- README.md L96–115 (layer 05 rationale + prerequisites)
- `layers/05-flink/applications/txn-volume-tumbling-window.yaml` (1-minute TPS job)
- `layers/05-flink/applications/account-transaction-enrichment.yaml` (temporal stream-table join)
- KNOWN-GAPS G-10 (FKO + CMF parallel Helm operators)
- KNOWN-GAPS G-12 (Custom s390x SQL-runner image)
- KNOWN-GAPS G-13 (Flink checkpoint state encryption)
