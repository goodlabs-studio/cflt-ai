---
title: DR — Cluster Linking
tags: [kafka confluent-cloud dr cluster-linking fsi]
sources: [fsi-dsp://adr/005, fsi-dsp://script/mirror-failover]
related: [patterns/dr-mirrormaker2, patterns/dr-multi-region-cluster, concepts/sla-tiers, concepts/cluster-linking-topology, concepts/fsi-data-streaming-platform]
confidence: high
last_updated: 2026-04-11
last_validated: 2026-05-14
---

# DR — Cluster Linking

## Summary

Active-passive DR pattern for Confluent Cloud deployments using bidirectional Cluster Linking between East (primary) and West (DR) clusters. A 6-step scripted failover promotes mirror topics, flips Consul service discovery, and resumes connectors. Failback reverses the process with truncate-and-restore to resync East, then reverse-and-start to restore the original direction. RPO is bounded by mirror lag (typically seconds); RTO is ~5-10 minutes dominated by Consul propagation and connector resume.

## Pattern

### Architecture

- **East (Primary):** Active production cluster, all producers and consumers resolve here via Consul DNS
- **West (DR):** Passive, receives mirror topics via bidirectional cluster link
- **Service Discovery:** Consul KV key `fsi/kafka/active-region` determines active region. Single KV update atomically flips Kafka, Schema Registry, and Oracle JDBC endpoints.
- **CLI:** `fsi-dr.sh` automates all procedures. Backend defaults to `cluster-linking`.

### Failover (6 Steps)

Execute when East is confirmed down, RTO clock is running, and on-call lead has approved:

1. **Pause Connectors** — Snapshot connector state, pause all RUNNING connectors via Connect REST API. Safe to abort — no system changes yet.
2. **Promote Mirror Topics** — `confluent kafka mirror failover` promotes all active mirrors on West. Topics become read-write. **Irreversible** — once promoted, topics are independent. Use `mirror failover` (emergency), never `mirror promote` (planned migration).
3. **Flip Consul** — Set `fsi/kafka/active-region = west`. All Consul-resolved endpoints redirect atomically.
4. **Verify DNS** — Confirm `dig +short kafka.fsi.internal` / `schema.fsi.internal` / `oracle.fsi.internal` resolve to West IPs. Retries with 3-second intervals for up to 30 seconds.
5. **Resume Connectors** — Resume only connectors that were RUNNING before Step 1 (from state snapshot). Intentionally-paused connectors stay paused.
6. **Validate** — Verify West cluster is serving traffic, no active mirrors remaining, connectors running.

### Failback (8 Steps)

Execute during a planned change window after East is recovered and stable:

1. **Verify East** — Confirm East cluster is reachable and healthy.
2. **Pause Connectors on West** — Same snapshot/pause pattern as failover.
3. **Truncate and Restore** (**DESTRUCTIVE**, confirmation gate) — Truncates East topic data and configures East topics as mirrors from West. If this fails partway, some East topics may be truncated — West still has all data and is still serving.
4. **Wait for Sync** — Poll mirror lag on East until all topics reach near-zero lag. Default timeout 300 seconds, configurable via `FSI_DR_SYNC_TIMEOUT`.
5. **Reverse and Start** (confirmation gate) — East becomes read-write (primary), West becomes mirrors again.
6. **Flip Consul to East** — Set `fsi/kafka/active-region = east`.
7. **Resume Connectors** — Resume previously-RUNNING connectors.
8. **Validate** — Verify East is serving traffic, Consul points to east.

### Pre-Flight

Always run `fsi-dr.sh failover --dry-run` before execution. Reports per-topic mirror lag with SLA-tier assessment. If any topic exceeds its tier's alert threshold, operator must acknowledge data loss risk.

### SLA-Tier Thresholds

| Tier | RPO | RTO | Lag Warn | Lag Alert |
|------|-----|-----|----------|-----------|
| critical | < 5 min | < 15 min | 30s | 60s |
| compliance | = 0 | < 15 min | 10s | 30s |
| standard | < 2 hours | < 1 hour | 5 min | 15 min |
| best-effort | < 24 hours | < 4 hours | 1 hour | 4 hours |

## When to Use

- Confluent Cloud deployments (CC on AWS/Azure/GCP)
- Active-passive DR with RPO targets measurable in seconds to minutes
- Environments using Consul for service discovery
- Organizations preferring managed Cluster Linking over self-managed MirrorMaker 2

## Caveats

- Mirror promotion is irreversible — once promoted, requires full failback procedure to restore East
- RPO > 0 (async replication). For RPO=0 requirements, use MRC on Confluent Platform instead.
- Consul is a hard dependency for atomic endpoint flip. If Consul is down, manual DNS updates are required.
- Failback involves a destructive truncate-and-restore step — always execute in a planned change window
- `mirror failover` vs. `mirror promote` have different semantics. DR events always use `failover`.

## Related

- [DR — MirrorMaker 2](patterns/dr-mirrormaker2.md) — alternative DR backend for CFK/CP
- [DR — Multi-Region Cluster](patterns/dr-multi-region-cluster.md) — RPO=0 alternative on CP
- [SLA Tiers](concepts/sla-tiers.md) — tier definitions driving RPO/RTO targets
- [Cluster Linking Topology](concepts/cluster-linking-topology.md) — cluster link architecture
- [ADR-005](synthesis/adr-index.md) — decision to use CL over MRC for CC deployments
- [ADR-003](synthesis/adr-index.md) — decision to use Consul for service discovery
