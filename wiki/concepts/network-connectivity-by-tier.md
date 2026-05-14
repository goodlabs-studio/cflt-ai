---
title: Network Connectivity by Cluster Tier
tags: [networking, confluent-cloud, privatelink, peering, transit-gateway, advertised-listeners, fsi]
sources: [outputs/reports/confluent-best-practices-quickstart.md]
related: [concepts/cc-cluster-tiers, patterns/dr-cluster-linking, patterns/low-latency-kafka-azure, patterns/aks-kafka-tuning]
confidence: high
last_updated: 2026-05-14
last_validated: 2026-05-14
---

# Network Connectivity by Cluster Tier

## Summary

Confluent Cloud connectivity is determined by **cluster tier** — Basic/Standard get public only, Enterprise is **PrivateLink/PSC only**, Dedicated supports everything (public, PrivateLink, peering, AWS Transit Gateway). On Confluent Platform you own `advertised.listeners` end-to-end; it is the #1 connectivity footgun. This article captures the **mapping from tier to networking mode**, the cross-AZ cost surface (fetch-from-follower as the canonical save), and the FSI defaults (private-only for prod). For tier selection itself, see `concepts/cc-cluster-tiers.md`.

## Detail

### Confluent Cloud connectivity by cluster type

Validated against `confluent-docs` MCP (`networking/overview.md`, `connectors/bring-your-connector/custom-connector-fands.md`) on 2026-05-14.

| Option | Direction | CIDR overlap OK? | Cluster types | Notes |
|---|---|---|---|---|
| **Public internet** | n/a | n/a | Basic, Standard, Dedicated | TLS + IP allowlists. Fine for dev; generally not FSI prod. |
| **AWS PrivateLink / Azure Private Link / GCP Private Service Connect** | one-way (you → CC) | **Yes** (no overlap concerns) | Enterprise, Dedicated | The recommended private option. Per-AZ endpoints; **zonal DNS** records (`*.<region>.aws.private.confluent.cloud` etc.) — clients must resolve the zonal endpoints. |
| **AWS Private Network Interface (PNI)** | bidirectional (hub-spoke capable) | **Yes** (supports IP overlap) | Enterprise, Freight (AWS only) | Highest-throughput private option; customer-managed security groups. Required to take an Enterprise cluster above 10 eCKU on AWS (up to 32). |
| **VPC / VNet peering** | two-way | **No** (must be non-overlapping) | Dedicated only | More setup; route tables; only when you genuinely need CC → you. |
| **AWS Transit Gateway** | hub | non-overlapping | Dedicated only | Many-VPC hub-and-spoke. |

### Key constraints

- **Enterprise clusters** support PrivateLink/PSC across AWS/Azure/GCP and PNI on AWS — no VPC peering, no Transit Gateway. Enterprise on AWS PrivateLink is capped at 10 eCKU; PNI raises that to 32.
- **Freight clusters on AWS** use PNI only (no PrivateLink, no peering, no Transit Gateway).
- **Fully-managed connectors on a private cluster** need a way to reach *your* source — Confluent provides egress mechanisms (static egress IPs, PrivateLink to your endpoint depending on connector); plan this, it's a common surprise.
- **Custom Connectors** are supported on Dedicated and on Enterprise AWS clusters using **PrivateLink egress access points** (a dedicated, newly-provisioned serverless egress PrivateLink gateway is required). Custom Connectors are not supported on Freight, and require a public or PrivateLink-egress path — public static egress IPs are not supported for Custom Connectors.
- **Cluster Linking over private networking** — both link endpoints must be mutually reachable. CC↔CC is straightforward; **CC↔CP** needs the CP side reachable from CC (via DC connectivity or a public endpoint) — design the link path explicitly.

### Confluent Platform networking

- **`advertised.listeners` is the #1 footgun.** It must be the address clients *actually use* to reach each broker — not the bind address. Multiple listeners (internal / external / replication) on different ports; **SANs in broker certs must match every advertised name**; LB/Route SNI for external access.
- Firewall the right ports: 9092 (broker), 9093 (KRaft controller), 8081 (SR), 8083 (Connect), 8090 (MDS), 9021 (Control Center).
- High-bandwidth-delay links — raise `socket.send.buffer.bytes` / `socket.receive.buffer.bytes`; jumbo frames in the DC where supported. On LinuxONE: HiperSockets MTU, SMC-D/SMC-R cross-frame transport (see `patterns/linuxone-kafka-tuning.md`).
- DNS — bootstrap resolves to a load balancer; brokers then advertise their own hostnames — **clients must resolve those too**. Split-horizon DNS or a service-discovery layer (Consul, ADR-003) handles the DR endpoint flip cleanly.

### Latency & cost — the cross-AZ surface

- **Cross-AZ ≈ 1–2 ms** added per hop; `acks=all` waits for ISR which may span AZs — budget for it in latency-tier apps.
- **Cross-region replication is async, always** (Cluster Linking). RPO=0 across regions doesn't exist — design for it. See `patterns/dr-cluster-linking.md` (async CC↔CC) and `patterns/dr-multi-region-cluster.md` (within-region MRC RPO=0 on CP).
- **Fetch-from-follower** (`client.rack` + `broker.rack` + `RackAwareReplicaSelector`) keeps consumer fetch traffic in-AZ — typically **30–50% off inter-AZ egress**. Do this.
- **Cross-AZ traffic is the silent cost line** (replication + cross-AZ consumer fetch). **Freight clusters** trade latency for object-storage-backed writes that slash inter-AZ replication cost — use them for latency-tolerant firehoses.
- **Co-locate latency-critical clients** in the cluster's region (ideally AZ); keep connections warm; be ILB-aware. See `patterns/low-latency-kafka-azure.md` and `fsi-dsp:reference/*-low-latency-azure/`.

### FSI defaults

- **Private connectivity for prod.** PrivateLink/PSC on Enterprise (or Dedicated where peering/TGW is required).
- **No public endpoints** on FSI clusters except as deliberate documented exceptions.
- **Zonal DNS resolvable per-AZ** from every client subnet.
- **`client.rack` set on all consumers** — fetch-from-follower is a money-leaving-the-table item if it's not on.
- **DR endpoint indirection** (Consul / DNS) in front of `bootstrap.servers` so failover is one atomic change, not a config push to every client (`patterns/dr-cluster-linking.md`, ADR-003).

## Related

- [Confluent Cloud Cluster Tiers](cc-cluster-tiers.md) — tier matrix and decision rule; this article extends it on the networking axis
- [DR — Cluster Linking](../patterns/dr-cluster-linking.md) — Consul-based endpoint flip, CC↔CC over private networking
- [Low-Latency Kafka Clients on Azure](../patterns/low-latency-kafka-azure.md) — ILB-aware connection management, fetch-from-follower
- [AKS Kafka Tuning](../patterns/aks-kafka-tuning.md) — Azure VM/NIC tuning, advertised listeners on CFK
- [Top 20 Confluent Gotchas](../synthesis/confluent-gotchas-top-20.md) — #18 (`advertised.listeners` / PrivateLink zonal DNS), #20 (cross-AZ cost)
