---
title: DR — Multi-Region Cluster
tags: [kafka confluent-platform dr mrc fsi]
sources: [fsi-dsp://adr/008, fsi-dsp://script/fsi-dr]
related: [patterns/dr-cluster-linking, patterns/dr-mirrormaker2, concepts/sla-tiers, concepts/fsi-data-streaming-platform]
confidence: high
last_updated: 2026-04-11
---

# DR — Multi-Region Cluster

## Summary

RPO=0 DR pattern using Confluent Platform's replica placement v2 with synchronous replication across two full data centers and an observer in a third. The 2.5-cluster architecture (2 East replicas + 2 West replicas + 1 observer) with `min.insync.replicas=3` forces cross-DC synchronous writes, guaranteeing zero data loss. Failover is often automatic via observer promotion when ISR drops below threshold. Available on Confluent Platform only (not Confluent Cloud).

## Pattern

### 2.5-Cluster Architecture

- **East DC (Primary):** 2 replicas per partition (full read/write)
- **West DC (DR):** 2 replicas per partition (full read/write)
- **Central DC (Observer):** 1 observer replica (async, auto-promotes on ISR loss)
- **Replication Factor:** 5 (2 + 2 + 1)
- **min.insync.replicas:** 3 (forces at least one replica in each full DC to acknowledge)

### Key Properties

| Property | Cluster Linking | MirrorMaker 2 | MRC |
|----------|----------------|---------------|-----|
| Mechanism | Mirror topics | Connector replication | Native replica placement |
| RPO | > 0 (async) | > 0 (async) | = 0 (sync) |
| Failover | Manual promotion | Pause connectors | Leader election (often automatic) |
| Failback | Reverse link | Reverse connectors | Leader election |
| Topic writable | After promotion | Always (separate topics) | Always (same topic, all DCs) |

### Failover

Triggered by East DC failure. Observer auto-promotes if `observerPromotionPolicy: under-min-isr`.

```bash
export FSI_DR_BACKEND=mrc
export FSI_MRC_BOOTSTRAP=kafka-west-1:9092   # Surviving DC

fsi-dr.sh failover --dry-run    # Preview
fsi-dr.sh failover              # Execute
fsi-dr.sh status                # Verify
```

Steps:
1. Pre-flight: verify surviving DC reachable, Consul available
2. Observer replicas auto-promoted into ISR (if not already)
3. Preferred leader election moves partition leadership to surviving DC
4. Consul KV updated to point clients at surviving DC
5. Connect and consumer groups resume on new leaders

### Failback

Triggered when East DC recovers and brokers rejoin ISR:

```bash
export FSI_DR_BACKEND=mrc
export FSI_MRC_BOOTSTRAP=kafka-east-1:9092   # Recovered DC

fsi-dr.sh status                # Verify primary healthy
fsi-dr.sh failback --dry-run    # Preview
fsi-dr.sh failback              # Rebalances leaders to primary
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FSI_DR_BACKEND` | `cluster-linking` | Set to `mrc` |
| `FSI_MRC_BOOTSTRAP` | `localhost:9092` | MRC cluster bootstrap |
| `FSI_MRC_EAST_RACK` | `us-east` | East DC rack ID |
| `FSI_MRC_WEST_RACK` | `us-west` | West DC rack ID |
| `FSI_MRC_OBSERVER_RACK` | `us-central` | Observer DC rack ID |
| `FSI_MRC_COMMAND_CONFIG` | (empty) | Auth config properties path |

## When to Use

- Compliance-tier topics requiring RPO=0 (OFAC screening, AML alerts, CFT reporting)
- Confluent Platform on RHEL deployments where MRC is available
- Regulatory environments where "near-zero" RPO is not sufficient — must be provably zero
- Use cases where automatic failover (no manual intervention) is required

## Caveats

- **CP only** — not available on Confluent Cloud. CC compliance topics use critical-tier CL with enhanced monitoring as a workaround.
- **Latency cost** — synchronous cross-DC replication adds produce latency (network round-trip between DCs). Not suitable for sub-millisecond latency requirements.
- **Infrastructure cost** — 5x replication factor across 3 DCs is significantly more expensive than 2-cluster CL.
- `observerPromotionPolicy` must be set at topic creation time with replica placement v2 JSON.
- Producers may see `NotEnoughReplicasException` during the failover window before observer promotes into ISR.

## Related

- [DR — Cluster Linking](patterns/dr-cluster-linking.md) — async DR for CC deployments
- [DR — MirrorMaker 2](patterns/dr-mirrormaker2.md) — async DR for CFK/CP
- [SLA Tiers](concepts/sla-tiers.md) — compliance tier drives RPO=0 requirement
- [ADR-005](synthesis/adr-index.md) — why CL is preferred over MRC for current CC deployments
- [ADR-008](synthesis/adr-index.md) — DR tier classification and backend selection
