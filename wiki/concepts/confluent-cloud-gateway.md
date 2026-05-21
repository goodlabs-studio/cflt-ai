---
title: Confluent Gateway — Protocol-Aware Kafka Proxy
tags: [kafka, gateway, proxy, dr, networking, cfk, confluent-platform, fsi]
sources: []
related: [concepts/private-networking, patterns/dr-cluster-linking, patterns/dr-mirrormaker2, concepts/cluster-linking-topology, concepts/network-connectivity-by-tier]
confidence: medium
last_updated: 2026-05-18
last_validated: 2026-05-18
---

# Confluent Gateway — Protocol-Aware Kafka Proxy

## Summary

**Confluent Gateway** is a self-managed, protocol-aware Kafka proxy that sits between Kafka clients and one or more clusters. It speaks the Kafka wire protocol natively (not L4 TCP load balancing), so it can rewrite `Metadata` responses, swap authentication mechanisms, present a single custom domain to clients, and redirect traffic to a different cluster — all without client reconfiguration or restart. The primary use cases are **traffic control** (rate limiting, blast-radius isolation, A/B routing), **DR switchover** (point the gateway at the DR cluster; clients keep their existing connections), **custom domains** (clients connect to a stable FQDN regardless of underlying cluster naming), and **auth swapping** (e.g., client uses mTLS, broker side uses SASL/OAUTHBEARER). It is deployed self-managed via **Confluent for Kubernetes (CFK)** or **Docker** — there is no fully-managed Confluent Cloud SKU as of this writing. **Do not confuse** this product with the **Confluent Cloud Ingress PrivateLink Gateway** (a networking resource for private connectivity into CC) — see [Private Networking](private-networking.md) for that. This article covers the protocol-proxy gateway product only.

## Detail

### Naming and disambiguation

The wiki filename `confluent-cloud-gateway.md` is historical; the canonical product name is **Confluent Gateway** (sometimes informally "CPC Gateway", reflecting its Confluent Platform Components lineage).

| Product | What it is | Where it runs |
|---|---|---|
| **Confluent Gateway** (this article) | Protocol-aware Kafka proxy; rewrites metadata, swaps auth, redirects traffic | Self-managed on CFK / Docker / bare metal |
| **Confluent Cloud Ingress PrivateLink Gateway** | CC networking resource — terminates VPC private endpoints, multiplexes traffic to CC services | Confluent-managed inside CC |

The CC PrivateLink Gateway operates at the network layer (VPC endpoints, DNS). Confluent Gateway operates at the **Kafka protocol layer** — it parses `Metadata`, `Produce`, `Fetch`, `SaslHandshake`, etc., and can make routing or rewriting decisions per-request. They solve different problems and are frequently used together (PrivateLink for private reach into a self-managed cluster fronted by Confluent Gateway, for example).

### What "protocol-aware" buys you

A TCP load balancer (HAProxy, Azure ILB, AWS NLB) can spray Kafka connections across brokers but cannot:

- Rewrite the `Metadata` response so clients believe they are talking to brokers `gateway-1.fsifirm.com:9092` etc. instead of the underlying cluster's `b-1.cluster-1.kafka.us-east-1.aws.confluent.cloud:9092`. Clients use the names in metadata for **subsequent** connections (produce/fetch), so DNS aliasing alone is insufficient — the names must be rewritten in-band.
- Swap SASL mechanisms between client and broker — e.g., client authenticates to the gateway with mTLS; the gateway re-authenticates to the cluster with SASL/OAUTHBEARER using a service-account credential.
- Re-target the same client connection to a different physical cluster without the client noticing — which is the basis of DR switchover without restart.

Confluent Gateway can do all three because it is a full Kafka protocol implementation on both sides.

### Core capabilities

| Capability | What it does | Typical use |
|---|---|---|
| **Custom domains** | Clients connect to a stable FQDN (e.g., `kafka.fsifirm.com:9092`); gateway rewrites `Metadata` advertised hostnames | Decouple client config from cluster identity; environment promotion (dev→prod) without client redeploy |
| **Auth swapping** | Terminate one mechanism on the client side; present a different one to the broker | Client uses mTLS while broker side is SASL/OAUTHBEARER; centralize credential management at the gateway |
| **Traffic control** | Rate-limit, throttle, or partition traffic by client identity / topic / API key | Multi-tenant cluster sharing; protect a tier-1 cluster from a rogue producer |
| **DR switchover** | Repoint the gateway at the DR cluster; clients see brief disconnect, then reconnect to the gateway and resume | RTO target measured in seconds without coordinated client restart |
| **Fencing / unfencing** | Block or unblock a particular client identity from producing or fetching | Operational blast-radius control; pre-failover quiescing |

> ⚠️ unverified — the exact set of capabilities included in **Confluent Gateway 1.1.0 GA** vs **CPC Gateway 1.2** (which the source notes adds fencing/unfencing) was not re-validated against current Confluent docs in this ingest. Treat the version-feature pairing as the source intent; reconfirm against the release notes for the customer-facing version before quoting.

### Deployment model

Confluent Gateway is **self-managed only** as of 2026-05. There is no fully-managed Confluent Cloud SKU.

- **Confluent for Kubernetes (CFK)**: gateway runs as a CRD-managed StatefulSet (similar to other CP components). CFK handles rolling updates, TLS cert rotation, and lifecycle.
- **Docker / bare metal**: container image plus a YAML/JSON config. Pair with a process supervisor (systemd) or container runtime.

The gateway is **stateless** in the routing-config sense — config changes (re-target a route, fence a client) take effect on the running process. It does **not** persist Kafka data; consumer offsets, transaction state, etc., remain in the underlying Kafka cluster.

For HA, run the gateway as **multiple replicas** behind a TCP load balancer (cloud LB, ILB, NLB) or with client-side bootstrap to all gateway pods. Failover between gateway replicas is connection-level; clients reconnect to the next replica via the bootstrap list.

> ⚠️ unverified — exact CFK CRD names (e.g., `ConfluentGateway`?) and Helm chart packaging were not validated against current CFK docs in this ingest. Reconfirm against the CFK release notes for the version in use.

### DR switchover — the load-bearing use case

The reason this product matters for FSI deployments is **DR client switchover without restart**. The conventional Cluster Linking DR pattern (see [DR — Cluster Linking](../patterns/dr-cluster-linking.md)) requires clients to be reconfigured to point at the DR cluster's bootstrap endpoints after a `mirror promote`. With Confluent Gateway:

1. Both prod and DR clusters are mirrored via Cluster Linking (offset-preserving).
2. Clients connect to `kafka.fsifirm.com:9092` — the gateway's address.
3. The gateway routes to prod.
4. On failover: operator runs `mirror promote` on the DR cluster, then updates the gateway route to point at DR.
5. Clients see a transient disconnect, reconnect to the gateway, and resume producing/consuming from the new cluster at the same offsets — **no client restart, no client config change**.

This is functionally equivalent to the ORKA-style proxy-pause-and-redirect pattern referenced in the DR validation reports (see `wiki/_queue.md` resolved items from 2026-05-15 and 2026-05-18). The discriminator is **workload class**:

- **Stateless consumers** (standard producer/consumer apps with simple offset management): switchover via gateway + CL is sound; Kafka delivery guarantees preserved end-to-end.
- **Stateful apps** (Kafka Streams with changelog/repartition topics, in-flight EOS transactions, RocksDB state): CL does **not** replicate the state surface. Confluent's own client-switchover guidance cautions against attributing stateful guarantee-preservation to any proxy-based DR mechanism without explicit handling. See `outputs/reports/wiki-validation-2026-05-18-orka-guarantees.md` for the full analysis.

### When to use Confluent Gateway

- **DR with sub-minute RTO requirement** and the cluster topology already uses Cluster Linking (or MM2) for data replication — gateway closes the client-side switchover gap.
- **Multi-cluster fronting** behind a single stable DNS name — common in regulated FSI environments where the cluster identity should not leak into client configs across environments.
- **Auth bridging** — client population on legacy mTLS, target cluster on modern OAUTHBEARER/SASL; gateway re-authenticates without forcing a coordinated client rollout.
- **Traffic control on shared multi-tenant clusters** — fencing a rogue producer at the gateway is cheaper than ACL rolls on the brokers.

### When NOT to use Confluent Gateway

- **Confluent Cloud-only deployments** with native PrivateLink Gateway and Cluster Linking already in place — the CC One-Click DR migration path (when applicable) handles the switchover problem without a separate proxy. Adding Confluent Gateway in front of CC adds an operational surface for limited additional value.
- **Stateful Kafka Streams DR** where the intent is to fail over without state loss — the gateway moves connections, it does not move state. Pair with an explicit state-rebuild strategy or accept the reset.
- **Pure latency-critical workloads** where the added proxy hop (parse + re-encode the Kafka frame) is part of the latency budget. Measure before deploying; the extra hop is non-trivial in the p99 tail.

### FSI considerations

- **Vendor backing required.** Confluent Gateway is a Confluent-supported product; using it satisfies the FSI vendor-contract rule (see `MEMORY.md`). Self-built protocol proxies (Envoy filters, custom Netty handlers) do not.
- **Audit logging** at the gateway is operationally useful — every connection establishment, auth swap, and routing decision is logged. Forward to SIEM via the same channel as broker audit logs (see [Audit Log SIEM Integration](../patterns/audit-log-siem-integration.md)).
- **mTLS termination at the gateway** with re-auth to the broker is a clean way to centralize FSI client-cert lifecycle. The gateway holds the broker-side credentials; client certs rotate independently.
- **Capacity sizing** is driven by the gateway's CPU cost per Kafka request (parse + re-encode is the dominant cost). Plan for 1.5–2× the broker count at peak throughput as a starting point; right-size from production metrics.

> ⚠️ unverified — specific sizing multiplier (1.5–2× broker CPU) is a general protocol-proxy heuristic, not a Confluent-published number for Confluent Gateway. Validate against load test before production sizing.

## Related

- [Private Networking — PrivateLink Gateway, PNI, Peering, TGW](private-networking.md) — disambiguation: CC PrivateLink Gateway is a networking resource, not a protocol proxy
- [DR — Cluster Linking](../patterns/dr-cluster-linking.md) — data-plane replication that pairs with Confluent Gateway for client-side switchover
- [DR — MirrorMaker 2](../patterns/dr-mirrormaker2.md) — alternative replication backend for CFK/CP topologies
- [Cluster Linking Topology](cluster-linking-topology.md) — six CL topology patterns that determine which switchover model applies
- [Network Connectivity by Cluster Tier](network-connectivity-by-tier.md) — where the gateway sits relative to CC tier networking
