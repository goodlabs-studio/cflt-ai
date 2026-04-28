---
title: FSI Governance Automation
tags: [kafka fsi terraform ansible ci-cd governance]
sources: [fsi-dsp://role/cp_topic, fsi-dsp://role/cp_schema, fsi-dsp://role/cp_rbac]
related: [concepts/fsi-data-streaming-platform, concepts/sla-tiers, concepts/fsi-compliance, concepts/schema-evolution-strategies, patterns/topic-naming]
confidence: high
last_updated: 2026-04-11
last_validated: 2026-04-28
---

# FSI Governance Automation

## Summary

Governance-as-code pattern where a single Terraform module call produces a fully governed Kafka topic (topic + Avro schema + RBAC + metadata tags + DR mirror), with SLA-tier-based defaults eliminating per-topic configuration decisions. Ansible roles provide equivalent governance for CP and CFK deployments. CI/CD enforces naming, compatibility, and override detection at PR time.

## Pattern

### Single-Module Topic Provisioning

One Terraform module call creates the complete resource stack for a governed topic:

```hcl
module "corebanking_account_txn" {
  source      = "../../modules/topic"
  domain      = "corebanking"
  application = "transactions"
  version     = "v1"
  entity      = "account-transaction"
  sla_tier    = "critical"           # Drives: partitions, retention, compatibility, DR thresholds
  owner       = "core-banking-team@company.com"
  schema_file = "../../schemas/corebanking/account-transaction.avsc"
  # ... producer/consumer service accounts for RBAC ...
}
```

The module assembles the topic name (`corebanking.transactions.v1.account-transaction`), selects compatibility mode from tier (FULL_TRANSITIVE for critical), sets partition count (12 for critical), configures retention, registers the schema, creates RBAC bindings, sets metadata tags (owner, PII, data-classification), and creates the DR mirror topic.

### SLA-Tier Defaults

Configuration derived from a single `sla_tier` input:

| Config | critical | standard | best-effort | compliance |
|--------|----------|----------|-------------|------------|
| Compatibility | FULL_TRANSITIVE | BACKWARD_TRANSITIVE | BACKWARD | FULL_TRANSITIVE |
| Partitions | 12 | 6 | 3 | 12 |
| Retention | 7d | 3d | 1d | infinite |
| min.insync.replicas | 2 | 2 | 1 | 2 |

Override variables exist for documented exceptions (`compatibility_override`, `partitions_override`, `retention_ms_override`), but CI detects and flags overrides for C4E review.

### Ansible Parity (CP/CFK)

Nine roles mirror Terraform governance for self-managed deployments:

- `cp_topic` — Topic CRUD via Admin REST v3 with SLA-tier governance (same tier→config mapping)
- `cp_schema` — Avro schema registration with two-pass compatibility safety
- `cp_rbac` — MDS RBAC binding lifecycle with LIST/DIFF/ADD/REMOVE reconciliation
- `cp_connect` — Connector lifecycle via idempotent PUT REST API
- `cp_observability` — JMX exporter, Prometheus, Grafana, SLA-tier alerts
- `cp_dr_mm2` / `cp_dr_mrc` — DR automation
- `cfk_operator` / `cfk_topic` — CFK Helm deployment and KafkaTopic CRD generation

Governance parity between Terraform and Ansible is CI-validated (`tests/ansible/test_governance_parity.py`).

### CI/CD Enforcement

- **Pre-check**: Validates topic naming regex, SLA tiers, schema compatibility, retention, and RBAC across Terraform, CFK YAML, and CPTopic formats
- **Schema validation**: Avro syntax + compatibility checks on every PR
- **Override detection**: Flags governance overrides (compatibility_override, etc.) for C4E review
- **Post-apply validation**: Verifies topic existence, schema registration, RBAC, and DR mirror status after deployment

### Metadata-Driven Cataloging

Schema metadata properties — owner, sla-tier, data-classification, domain, application, PII flag, PII fields — feed directly into data cataloging (Alation), compliance scanning, and cost allocation without external tooling dependencies.

## When to Use

- Standing up new Kafka topics in any FSI deployment model
- Enforcing consistent governance across multi-cloud, hybrid, and on-prem Confluent deployments
- Satisfying regulatory audit requirements for change management and access control
- Onboarding new teams to the Kafka platform with self-service topic provisioning

## Caveats

- Requires upfront agreement on domain boundaries and SLA tier classification
- Terraform and Ansible governance constants must stay in sync (CI parity tests mitigate this)
- Override mechanism exists for exceptions but introduces audit surface
- Module assumes Confluent-specific resources (provider, Schema Registry, RBAC model)

## Related

- [FSI Data Streaming Platform](concepts/fsi-data-streaming-platform.md) — platform overview
- [SLA Tiers](concepts/sla-tiers.md) — tier definitions driving all defaults
- [Topic Naming](patterns/topic-naming.md) — naming convention enforced by this pattern
- [Schema Evolution Strategies](concepts/schema-evolution-strategies.md) — compatibility modes
- [FSI Compliance](concepts/fsi-compliance.md) — audit trail for CI/CD
