---
title: SLA Tiers
tags: [kafka fsi governance sla]
sources: [raw/repos/fsi-dsp/ansible/vars/sla_tiers.yml]
related: [concepts/fsi-data-streaming-platform, concepts/schema-evolution-strategies, concepts/fsi-compliance, patterns/fsi-governance-automation, patterns/dr-cluster-linking, patterns/dr-mirrormaker2, patterns/dr-multi-region-cluster]
confidence: high
last_updated: 2026-04-11
---

# SLA Tiers

## Summary

Four SLA tiers (critical, standard, best-effort, compliance) drive all governance defaults across the FSI Kafka Platform. A topic's tier determines its schema compatibility mode, partition count, retention, min.insync.replicas, DR RPO/RTO targets, and mirror lag alert thresholds. The tier is set once at topic creation and propagates through Terraform modules and Ansible roles, eliminating per-topic configuration decisions.

## Detail

### Tier Definitions

Source of truth: `ansible/vars/sla_tiers.yml` (CI-validated for parity with Terraform `modules/topic/main.tf`).

#### Governance Constants

| Property | critical | standard | best-effort | compliance |
|----------|----------|----------|-------------|------------|
| Compatibility | FULL_TRANSITIVE | BACKWARD_TRANSITIVE | BACKWARD | FULL_TRANSITIVE |
| Partitions | 12 | 6 | 3 | 12 |
| Retention (ms) | 604,800,000 (7d) | 259,200,000 (3d) | 86,400,000 (1d) | -1 (infinite) |
| min.insync.replicas | 2 | 2 | 1 | 2 |

Default tier: **standard** (if not specified).

#### DR Targets

| Tier | RPO Target | RTO Target | Priority |
|------|-----------|-----------|----------|
| critical | < 5 minutes | < 15 minutes | P1 — immediate |
| compliance | RPO = 0 | < 15 minutes | P1 — immediate |
| standard | < 2 hours | < 1 hour | P2 — business hours |
| best-effort | < 24 hours | < 4 hours | P3 — next business day |

During multi-topic outages, failover verification follows priority order: P1 (critical + compliance) first, then P2, then P3.

#### Mirror Lag Thresholds

Used by `fsi-dr.sh` pre-failover checks and Ansible `cp_dr_mm2` role:

| Tier | Warn (seconds) | Alert (seconds) |
|------|---------------|-----------------|
| critical | 30 | 60 |
| compliance | 10 | 30 |
| standard | 300 (5 min) | 900 (15 min) |
| best-effort | 3,600 (1 hr) | 14,400 (4 hr) |

If mirror lag exceeds a topic's alert threshold at failover time, the CLI warns about potential data loss and requires operator acknowledgment.

### Tier Selection Guide

- **critical** — Core banking transactions, fraud detection signals, real-time payments. Near-zero RPO, immediate failover, strictest schema compatibility.
- **compliance** — OFAC screening, AML alerts, CFT reporting. Zero data loss required for regulatory audit trails. Infinite retention. RPO=0 achieved via MRC on CP; near-zero via CL on CC with enhanced monitoring.
- **standard** — Internal events, batch feeds, non-latency-sensitive integrations. Moderate RPO/RTO, standard compatibility.
- **best-effort** — Logs, metrics, dev/test data, analytics feeds. Tolerates significant data loss and recovery time. Minimal ISR requirements.

### Parity Enforcement

Terraform and Ansible governance constants must stay in sync. CI validates parity via `tests/ansible/test_governance_parity.py`. The `sla_tiers.yml` file carries a header warning: "These values MUST stay in sync with Terraform."

Mirror lag thresholds are DR-specific and are not parity-tested with Terraform (Terraform does not manage MM2 mirror lag — CP/CFK only).

## Related

- [FSI Data Streaming Platform](concepts/fsi-data-streaming-platform.md) — platform overview
- [Schema Evolution Strategies](concepts/schema-evolution-strategies.md) — compatibility modes per tier
- [Governance Automation](patterns/fsi-governance-automation.md) — how tiers propagate through IaC
- [DR — Cluster Linking](patterns/dr-cluster-linking.md) — DR thresholds in action
- [DR — MirrorMaker 2](patterns/dr-mirrormaker2.md) — MM2 lag monitoring
- [DR — Multi-Region Cluster](patterns/dr-multi-region-cluster.md) — RPO=0 for compliance tier
- [ADR Index](synthesis/adr-index.md) — ADR-002 (compatibility by tier), ADR-008 (DR tier classification)
