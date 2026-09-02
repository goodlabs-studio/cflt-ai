---
title: Confluent Cloud Certified Operator (CCAC) Exam Prep
tags: [certification, ccac, confluent-cloud, exam-prep, rbac, stream-governance]
sources: [https://www.confluent.io/certification/, https://training.confluent.io/learn/courses/1103/confluent-cloud-certified-operator, https://docs.confluent.io/cloud/current/security/access-control/rbac/predefined-rbac-roles.html]
related: [concepts/cc-cluster-tiers, concepts/confluent-cloud-cluster-sku-selection, concepts/network-connectivity-by-tier, concepts/confluent-cloud-private-networking, concepts/cluster-linking-topology, patterns/dr-cluster-linking, concepts/schema-registry-best-practices, concepts/schema-evolution-strategies, concepts/consumer-group-rebalancing, concepts/consumer-lag-monitoring, concepts/observability-metrics-mapping, concepts/flink-confluent-cloud-setup, concepts/ksqldb-observability]
confidence: medium
last_updated: 2026-08-18
last_validated: 2026-08-18
---

# Confluent Cloud Certified Operator (CCAC) Exam Prep

## Summary

CCAC is Confluent's official certification for operating Confluent Cloud (as distinct from CCDAK for developers and CCAAK for self-managed Kafka administrators). It's a 90-minute, ~60-question proctored exam (multiple-choice, matching, ordering) costing $150 and valid for 2 years. Domain weightings below are compiled from third-party prep vendors, not an official Confluent-published blueprint — **pull the current official exam guide from the training portal before treating these percentages as fixed.** This article exists to map exam domains to what's already validated in this wiki and flag the console/UI and terminology gaps the wiki doesn't cover.

## Detail

### Exam facts

| Attribute | Value |
|---|---|
| Format | 90 min, ~60 questions — multiple-choice, matching, list-ordering |
| Delivery | Remote proctored via Honorlock, Chrome required |
| Cost | $150 USD |
| Validity | 2 years |
| Prerequisites | None formal; Confluent recommends 6–12 months hands-on with Confluent Cloud |
| Registration | [training.confluent.io/learn/courses/1103](https://training.confluent.io/learn/courses/1103/confluent-cloud-certified-operator) |

### Domain breakdown (unofficial — confirm against the current exam guide)

| Domain | Weight | Wiki coverage |
|---|---|---|
| CC Core Concepts | 17% | `cc-cluster-tiers.md`, `confluent-cloud-cluster-sku-selection.md` |
| Kafka Operations | 17% | `consumer-group-rebalancing.md`, `consumer-lag-monitoring.md`, `producer-batching-config.md`, `exactly-once-semantics.md` |
| CC Static Operations (provisioning/config) | 14% | `confluent-cloud-private-networking.md`, `network-connectivity-by-tier.md` — RBAC role taxonomy is a gap (see below) |
| CC Dynamic Operations (scaling/monitoring/troubleshooting) | 16% | `observability-metrics-mapping.md`, `consumer-lag-monitoring.md` |
| CC Streaming Pipelines (Connect/ksqlDB/Flink) | 11% | `flink-confluent-cloud-setup.md`, `ksqldb-observability.md`, `kafka-connect-deployment-models.md`, `cdc-source-connector-setup.md` |
| CC Data Governance (Schema Registry/Stream Governance) | 13% | `schema-registry-best-practices.md`, `schema-evolution-strategies.md` — Stream Catalog/Lineage UI is a gap (see below) |
| CC Resilience (Cluster Linking/DR) | 11% | `cluster-linking-topology.md`, `dr-cluster-linking.md` |

### Gaps not covered elsewhere in this wiki

The wiki is architecture/CLI/Terraform-oriented; the exam tests Cloud Console navigation and exact platform terminology that don't show up in IaC-first documentation. Study these separately:

**RBAC predefined roles** (validated against `confluent-docs` 2026-08-18; corrected 2026-08-18 after two errors surfaced in downstream practice questions) — organization-scoped: `OrganizationAdmin`, and **`NetworkAdmin`** (provisions networks/network connections "for all environments in an organization" per Confluent's own role description — commonly mischaracterized as cluster-scoped; it is not, and it cannot see cluster resources like topics/consumer groups/connectors at all). Environment-scoped: `EnvironmentAdmin`. Cluster-scoped: `CloudClusterAdmin`, `Operator`, `ResourceOwner`, `DeveloperRead`, `DeveloperWrite`, `DeveloperManage`, `MetricsViewer`. Governance-scoped: `DataDiscovery`, `DataSteward`. Know which scope each role binds at (org / env / cluster) — the exam tests this distinction directly, and it's not documented anywhere else in this wiki. **Trip-wire:** `Sensitive` (along with `Public`, `Private`, `PII`) is a **Stream Catalog tag value** used to classify schema fields — it is not an RBAC role at all, despite reading like one alongside `DataDiscovery`/`DataSteward`.

**Stream Governance product surface** — Stream Catalog (business metadata, tags, search) and Stream Lineage (visual data-flow graph) are console features layered on top of Schema Registry. The wiki's `schema-inference-and-pii-categorization.md` covers `confluent:tags` at the schema level but not the Catalog/Lineage UI itself.

**Cloud Console click-paths** — creating a cluster, a fully-managed connector, and a ksqlDB application through the console UI (not `confluent` CLI or Terraform, which is how this wiki does everything). The exam assumes console fluency.

**Billing/usage limits as raw numbers** — the wiki's `cc-cluster-tiers.md` and `confluent-cloud-cluster-sku-selection.md` give decision rules and flag that exact CKU/eCKU numbers drift; the exam may quiz the current numbers directly. Re-verify current per-tier/per-CKU limits via `confluent-docs` MCP or the Cloud Console before the exam, not from this wiki's decision-tree framing.

### Suggested prep path

1. Pull the official exam guide from the training portal — confirm real domain weights before relying on the table above.
2. Spin up a CC trial org and walk the console for the four gap areas above (fastest ROI if your architecture fundamentals are already solid).
3. Review the wiki articles cross-referenced per domain above as refreshers.
4. Take Confluent's free on-demand courses for Cluster Linking, Schema Registry, and Stream Governance specifically — these map to the domains least covered by CLI/Terraform-oriented material.
5. Do a timed practice exam close to test day — the matching/ordering question formats trip people up more than the content itself.

## Related

- [Confluent Cloud Cluster Tiers](cc-cluster-tiers.md) — Core Concepts domain
- [Confluent Cloud Cluster SKU Selection](confluent-cloud-cluster-sku-selection.md) — Static Operations domain
- [Network Connectivity by Tier](network-connectivity-by-tier.md) — Static Operations domain
- [Cluster Linking Topology](cluster-linking-topology.md) — Resilience domain
- [DR — Cluster Linking](../patterns/dr-cluster-linking.md) — Resilience domain
- [Schema Registry Best Practices](schema-registry-best-practices.md) — Data Governance domain
- [Consumer Group Rebalancing](consumer-group-rebalancing.md) — Kafka Operations domain
- [Observability Metrics Mapping](observability-metrics-mapping.md) — Dynamic Operations domain
- [Flink on Confluent Cloud — Setup, RBAC, Lifecycle](flink-confluent-cloud-setup.md) — Streaming Pipelines domain
