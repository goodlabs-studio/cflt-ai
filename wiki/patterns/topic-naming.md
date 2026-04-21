---
title: Topic Naming Convention
tags: [kafka governance naming fsi]
sources: [raw/repos/fsi-dsp/ansible/vars/naming_rules.yml, raw/repos/fsi-dsp/docs/schema-guide.md]
related: [concepts/sla-tiers, concepts/schema-evolution-strategies, patterns/fsi-governance-automation, concepts/fsi-data-streaming-platform]
confidence: high
last_updated: 2026-04-11
---

# Topic Naming Convention

## Summary

Topics follow the pattern `{domain}.{application}.{version}.{entity}` with dot separators and strict regex validation per segment. The convention enables prefix-based RBAC (`corebanking.*`), dashboard auto-discovery by domain, deterministic Schema Registry subject naming (TopicNameStrategy), and versioned topic migration for breaking schema changes. Enforced in Terraform variable validation and CI pre-check across all IaC formats.

## Pattern

### Format

```
{domain}.{application}.{version}.{entity}
```

Example: `corebanking.transactions.v1.account-transaction`

### Segment Rules

Source of truth: `ansible/vars/naming_rules.yml` (CI-validated against Terraform `modules/topic/variables.tf`).

| Segment | Regex | Max Length | Example |
|---------|-------|-----------|---------|
| domain | `^[a-z][a-z0-9-]{1,30}$` | 31 chars | `corebanking` |
| application | `^[a-z][a-z0-9-]{1,30}$` | 31 chars | `transactions` |
| version | `^v[0-9]+$` | — | `v1` |
| entity | `^[a-z][a-z0-9-]{1,60}$` | 61 chars | `account-transaction` |

All segments: lowercase, start with a letter (except version which starts with `v`), alphanumeric with hyphens.

### Examples

| Topic | Domain | Application | Version | Entity |
|-------|--------|-------------|---------|--------|
| `corebanking.transactions.v1.account-transaction` | corebanking | transactions | v1 | account-transaction |
| `fraud.detection.v1.alert-signal` | fraud | detection | v1 | alert-signal |
| `compliance.screening.v1.match-result` | compliance | screening | v1 | match-result |
| `corebanking.transactions.v2.account-transaction` | corebanking | transactions | v2 | account-transaction |

### Why Dots

- Standard hierarchical separator in Kafka (used by Confluent for internal topics, metrics, consumer group IDs)
- Enables prefix-based RBAC: `DeveloperRead` on `corebanking.*` grants read to all corebanking topics
- Visually distinct from hyphens within segments — `corebanking.transactions.v1.account-transaction` is unambiguous
- Underscores (`_`) and dots are interchangeable in Kafka metric names, causing collisions. Consistent dot usage avoids the `metrics_period_problem` where `a.b` and `a_b` map to the same metric.

### Why Version in the Name

- Schema compatibility modes prevent incompatible changes to existing topics
- Breaking changes require a new versioned topic (`v2`) alongside `v1`
- Both versions coexist during migration (see breaking change runbook in [Schema Evolution](concepts/schema-evolution-strategies.md))
- The version segment makes dual-version operation explicit and discoverable

### Avro Namespace Convention

Avro namespaces follow: `org.fsi.{domain}.{application}.{version}`

The entity is the Avro record name (e.g., `AccountTransaction`), not part of the namespace. Matches Java package conventions.

### Enforcement

- **Terraform:** Inline `validation` blocks with regex in `modules/topic/variables.tf` — invalid names fail at plan time
- **CI:** C4E pre-check validates naming across Terraform, CFK YAML, and CPTopic formats
- **Ansible:** Naming rules in `ansible/vars/naming_rules.yml` with parity tests against Terraform

## When to Use

Always. Every topic on the FSI Kafka Platform must follow this convention. The Terraform module assembles the name from the four segments — teams provide individual segments, not the full name.

## Caveats

- Topic names are permanent. Renaming requires creating a new topic and migrating consumers.
- Domain boundaries must be agreed upfront. Renaming a domain means new topics.
- Long names (max ~125 chars total) are well within Kafka's 255-char limit but may affect dashboard column widths.
- Version segment adds visual complexity for teams that never do breaking changes, but costs nothing to include and prevents future pain.

## Related

- [Schema Evolution Strategies](concepts/schema-evolution-strategies.md) — versioned topic migration runbook
- [Governance Automation](patterns/fsi-governance-automation.md) — module that assembles and validates names
- [SLA Tiers](concepts/sla-tiers.md) — tier selection per topic
- [ADR Index](synthesis/adr-index.md) — ADR-007 (topic naming decision)
