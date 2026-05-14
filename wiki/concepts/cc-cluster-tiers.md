---
title: Confluent Cloud Cluster Tiers
tags: [kafka, confluent-cloud, cluster-types, basic, standard, enterprise, dedicated, freight, fsi]
sources: [outputs/reports/confluent-best-practices-quickstart.md]
related: [concepts/network-connectivity-by-tier, patterns/dr-cluster-linking, concepts/fsi-data-streaming-platform, concepts/sla-tiers]
confidence: high
last_updated: 2026-05-14
last_validated: 2026-05-14
---

# Confluent Cloud Cluster Tiers

## Summary

Confluent Cloud offers five cluster types — **Basic, Standard, Enterprise, Dedicated, Freight** — each with distinct networking modes, SLA, capacity model, and feature ceilings. This article captures the **decision rule** and the **fixed invariants** every FSI runbook needs (RF=3, `min.insync.replicas=2`, `unclean.leader.election.enable=false`). The specific per-cluster limits, per-CKU numbers, and Freight surface change frequently — those are flagged inline and should be confirmed against `confluent-docs` MCP or your Confluent SE before you quote them to a customer. The *tier mental model* is stable; the *numbers* drift.

## Detail

### Tier matrix

Verified against `confluent-docs` MCP (cluster-types.md) on 2026-05-14. Numbers below reflect current per-eCKU/CKU and aggregate limits; spot-check before quoting to a customer as Confluent re-tunes these periodically.

| Type | Use it when | Networking | Notable limits / features |
|---|---|---|---|
| **Basic** | Dev/test, demos | Public only | 99.5% SLA only, no RBAC inside the cluster, **can source a Cluster Link but cannot destination one**, no audit log, no mTLS. Never prod. |
| **Standard** | Smaller prod workloads | Public only | 99.9% or 99.99% SLA (99.99% requires 2 eCKU), RBAC, audit log, OAuth, Cluster Linking source, eCKU-elastic (max 10 eCKU). |
| **Enterprise** | Prod with elastic + private + zero capacity planning | Private only (PrivateLink / PSC / PNI on AWS) | Serverless/auto-scaling (max 32 eCKU on AWS PNI; 10 eCKU on AWS PrivateLink), 99.9% or 99.99% SLA, BYOK, mTLS, audit log, can source and destination Cluster Links. Strong default for new private prod workloads. |
| **Dedicated** | Need highest limits, single-tenant isolation, VPC peering / Transit Gateway, schema validation, ksqlDB, or Cluster Linking at scale | Public, PrivateLink/PSC, VPC peering, AWS Transit Gateway | Single-tenant, **CKU-sized** (manual capacity), BYOK, all networking modes, schema validation, ksqlDB. The "I need control on CC" option. |
| **Freight** | High-throughput firehose (logs, telemetry, clickstream) where ms-to-seconds latency is fine | Private (AWS PNI today) | Cheaper $/GB, **latency in seconds rather than milliseconds**. Does **not** support idempotent producers, transactions, or EOS — wrong choice for transactional / low-latency / audit-grade workloads. |

### Decision rule

1. **Standard** if it fits the ceilings (max 10 eCKU) and you don't need private networking.
2. **Enterprise** for most new private prod workloads (no capacity math, serverless, BYOK, mTLS on AWS, audit log).
3. **Dedicated** if you need VPC peering / AWS Transit Gateway, schema validation, ksqlDB, the highest limits, or single-tenant isolation.
4. **Freight** only for latency-tolerant firehoses (no transactions, no EOS).

See `concepts/network-connectivity-by-tier.md` for how networking maps to each tier; `patterns/dr-cluster-linking.md` for Cluster Linking topology and which tiers can source vs sink.

### Fixed invariants (CC, all types)

These are **not configurable** on Confluent Cloud — don't write runbooks or capacity plans that assume otherwise:

- `replication.factor=3`
- `min.insync.replicas=2`
- `unclean.leader.election.enable=false`

The hard part of CP (replication math, durability invariants, OS tuning) is the part CC does for you for free. The hard part of CC is that you *can't* override the things you used to tune. Plan around these as immutable.

### Capacity-planning skeleton

1. **Measure peak, not average** — peak ingress MB/s, peak produce req/s, peak partition count, peak connection count.
2. **Compute egress** ≈ ingress × (number of independent consumer groups) + internal replication. Fan-out is the multiplier people forget.
3. **Pick the type** using the decision rule above.
4. **Dedicated only — size CKUs** from current per-CKU limits + **30–40% headroom**. Per-CKU baseline (validated 2026-05-14): 60 MBps ingress, 180 MBps egress, 4,500 partitions, 18,000 connections, 15,000 req/s. Re-check Confluent's current sizing guidance before committing capacity. Multi-AZ always for prod.

### When the tier choice forces an FSI conversation

- **BYOK / customer-managed keys** → Enterprise or Dedicated only.
- **Cluster Linking source** → Basic, Standard, Enterprise, Dedicated all support being a *source*. Only Enterprise and Dedicated can be a *destination*. Freight can be neither.
- **VPC peering or AWS Transit Gateway** → Dedicated only. Enterprise on AWS supports PrivateLink and PNI; Azure/GCP Enterprise is PrivateLink/PSC only.
- **Custom Connectors on private networking** → supported on Dedicated and on Enterprise AWS via PrivateLink egress access points (dedicated, newly provisioned egress gateway required); not available on Freight, and not on Enterprise outside AWS-with-PrivateLink-egress.
- **Sub-ms market-data tier** → no CC tier meets a sub-ms SLA across AZs. This is a single-AZ co-location or self-managed conversation.

## Related

- [Network Connectivity by Tier](network-connectivity-by-tier.md) — public, PrivateLink/PSC, peering, Transit Gateway, mapped to tier
- [DR — Cluster Linking](../patterns/dr-cluster-linking.md) — which tiers can source CL; topology choices
- [FSI Data Streaming Platform](fsi-data-streaming-platform.md) — six deployment models including CC tier selection
- [SLA Tiers](sla-tiers.md) — FSI SLA tiers (governance defaults, not the same as CC cluster tiers — note the naming overlap)
- [Top 20 Confluent Gotchas](../synthesis/confluent-gotchas-top-20.md) — #7 (RF/min.insync/unclean leader fixed on CC)
