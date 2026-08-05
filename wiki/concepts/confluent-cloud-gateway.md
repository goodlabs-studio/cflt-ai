---
title: Confluent Gateway — Protocol-Aware Kafka Proxy
tags: [kafka, gateway, proxy, dr, migration, networking, cfk, confluent-platform, governance, fsi]
sources:
  - https://docs.confluent.io/private-cloud-gateway/current/overview.html
  - https://docs.confluent.io/private-cloud-gateway/current/gateway-deploy-overview.html
  - https://docs.confluent.io/private-cloud-gateway/current/gateway-release-notes.html
  - https://docs.confluent.io/private-cloud-gateway/current/gateway-migrate.html
  - https://docs.confluent.io/private-cloud-gateway/current/gateway-custom-domains.html
  - https://docs.confluent.io/operator/current/gateway/co-gateway-deploy.html
  - https://www.confluent.io/blog/kafka-client-failover-poc-confluent-cloud-gateway/
  - https://www.confluent.io/blog/client-migration-kcp-gateway/
related: [concepts/private-networking, patterns/dr-cluster-linking, patterns/dr-mirrormaker2, patterns/dr-application-routing, concepts/cluster-linking-topology, concepts/network-connectivity-by-tier, concepts/schema-registry-best-practices]
confidence: high
last_updated: 2026-08-05
last_validated: 2026-08-05
---

# Confluent Gateway — Protocol-Aware Kafka Proxy

## Summary

**Confluent Gateway** is a self-managed, stateless, Kafka-protocol-aware proxy that sits between clients and one or more Kafka clusters. Because it speaks the Kafka wire protocol on both sides (not L4 TCP load balancing), it can rewrite `Metadata` responses in-band, swap authentication mechanisms, present a single custom domain to clients, and re-target traffic to a different cluster — **without changing client configuration**. The load-bearing use cases are **client migration** (move a client estate to Confluent Cloud without app redeploys), **DR switchover**, **secure external/partner access** to private brokers, and **centralized governance** (schema/contract enforcement at the proxy).

It ships as one product across two doc surfaces and **two images**: `confluentinc/cpc-gateway` (Confluent Private Cloud Gateway, for self-managed Kafka) and `confluentinc/confluent-gateway-for-cloud` (Confluent Cloud Gateway). Deployment is **Docker or Confluent for Kubernetes (CFK)** — there is no fully-managed Confluent Cloud SKU. Current release is **1.3.0** (July 2026).

**Two hard constraints to check before scoping any work:** (1) client switchover **requires a gateway restart** — it is not a hot route repoint; (2) the docs explicitly direct you **not** to use switchover for strict-ordering applications such as **Kafka Streams**.

**Do not confuse** this product with the **Confluent Cloud Ingress PrivateLink Gateway** (a CC networking resource) — see [Private Networking](private-networking.md).

## Detail

### Naming and disambiguation

The wiki filename `confluent-cloud-gateway.md` is historical; the canonical product name is **Confluent Gateway**.

| Product | What it is | Where it runs |
|---|---|---|
| **Confluent Gateway** (this article) | Kafka-protocol-aware proxy; rewrites metadata, swaps auth, re-targets clusters, enforces governance | Self-managed on CFK / Docker |
| **Confluent Cloud Ingress PrivateLink Gateway** | CC networking resource — terminates VPC private endpoints, multiplexes traffic to CC services | Confluent-managed inside CC |

The CC PrivateLink Gateway operates at the **network layer** (VPC endpoints, DNS). Confluent Gateway operates at the **Kafka protocol layer** — it parses `Metadata`, `Produce`, `Fetch`, `SaslHandshake`, and makes per-request routing decisions. They solve different problems and compose well (PrivateLink for private reach; Confluent Gateway for protocol-level routing).

There is also a third, unrelated use of the word: **"one gateway per environment per region"** is the PrivateLink/PNI access-point rule in CC networking. If someone says "one gateway" in a Terraform/networking context, they mean that — not this product. See [Private Networking](private-networking.md).

### What "protocol-aware" buys you

A TCP load balancer (HAProxy, NLB, Azure ILB) can spray Kafka connections across brokers but cannot:

- **Rewrite the `Metadata` response** so clients believe the brokers are `broker-0.kafka.fsifirm.com:9092` rather than the real cluster's advertised listeners. Clients use the names returned in metadata for **subsequent** produce/fetch connections, so DNS aliasing alone is insufficient — the names must be rewritten in-band. This is the core reason the product exists.
- **Swap SASL mechanisms** between client and broker — client authenticates to the gateway with SASL/SCRAM; the gateway re-authenticates to the cluster with CC API keys pulled from a secret store.
- **Re-target the same client-facing endpoint to a different physical cluster** — the basis of both migration and DR switchover.

### Architecture — three primitives

| Primitive | What it is |
|---|---|
| **Streaming Domains** | Logical representation of an upstream Kafka cluster: `kafkaCluster.bootstrapServers[]` (one per security-protocol listener, each with an `id` and `endpoint` in `protocol://host:port` form), TLS material, and optional `nodeIdRanges`. |
| **Routes** | The virtualized client-facing listeners. `name` (≤30 chars, defaults to `route-<index>`), `endpoint` (`host:port` the gateway listens on), `brokerIdentificationStrategy`, a `streamingDomain` reference (`name` + `bootstrapServerId`), plus optional `fence`, `security`, `logNetwork`, `logFrames`. |
| **Policies / Filters** | Governance enforced centrally: fencing, schema validation, encryption, data contracts. |

**A cutover is: repoint a route at a different streaming domain.** That single mechanism underlies migration, blue/green upgrades, and DR switchover alike.

### Broker identification — the design decision that matters

Chosen per route via `brokerIdentificationStrategy.type`:

- **`port`** (default) — each upstream broker gets its own port on the gateway (9092 → broker-0, 9093 → broker-1, …). Requires `nodeIdRanges` on every cluster attached to the route's streaming domain. Simple, no DNS work, but burns a port range and scales poorly across many clusters.
- **`host`** — SNI-based routing. The gateway derives a per-broker hostname from `pattern`, substituting `$(nodeId)` at runtime. Requires **wildcard DNS** and clients that present SNI. **This is the one you want** for custom domains and multi-cluster fronting.

```yaml
# CFK Gateway CR — host-strategy route with SNI-derived broker hostnames
kind: Gateway
spec:
  routes:
    - name: payments-prod                                    # <=30 chars
      endpoint: kafka.fsifirm.com:9092                       # what clients put in bootstrap.servers
      brokerIdentificationStrategy:
        type: host                                           # SNI routing; needs wildcard DNS
        pattern: broker-$(nodeId).kafka.fsifirm.com:9092     # $(nodeId) substituted at runtime
      streamingDomain:
        name: prod-us-east
        bootstrapServerId: SASL_SSL-1                        # must match a bootstrapServers[].id
      security:
        auth: passthrough
```

### Core capabilities

| Capability | Detail |
|---|---|
| **Custom domains** | Stable client-facing FQDN decoupled from cluster identity; gateway rewrites advertised listeners. |
| **Network isolation** | Brokers stay entirely private; the gateway is the only reachable endpoint. Three documented patterns: same-VPC (private hosted zone), cross-VPC (peering/TGW + shared zone), external (public hosted zone). |
| **Auth swapping** | Terminate one mechanism client-side, present another broker-side. Supported pairs include SASL/SCRAM→SASL/PLAIN (CC API keys), OIDC→SASL, OAuth→OAuth (1.3.0), and NONE. Credentials come from external secret stores: AWS Secrets Manager, HashiCorp Vault, Azure Key Vault, **CyberArk Conjur** (1.3.0). |
| **Fencing** | Route-level filter: `fence.scope: ALL\|NONE`, with configurable `errorCode` (default `BROKER_NOT_AVAILABLE`) and `errorMessage`. Quiesce traffic before a cutover, or blast-radius a rogue client. As of 1.3.0 the fencing filter runs **before** the auth-swap filter, so fenced clients get the error immediately. |
| **Centralized governance** | 1.3.0, **Early Access, Docker-only.** Four independent enforcement policy types for record keys and values — schema ID enforcement, deep schema validation, field-level encryption, and full payload encryption — across Avro, JSON Schema, and Protobuf, with per-topic overrides. |
| **Blue/green upgrades** | Route repoint between old and new cluster versions. |

> ⚠️ Governance enforcement is Early Access: Docker only, and the config schema (property names, enforcement levels, YAML structure) may change incompatibly before GA. Do not build FSI tooling against it yet.

### Version history and support lifecycle

| Version | Released | Contents | Std. End of Life | Std. End of Support |
|---|---|---|---|---|
| **1.0.0** | — | GA. Protocol routing, routes + streaming domains, auth swapping with credential storage, blue/green and DR switchover, partner access. | — | — |
| **1.1.0** | Nov 2025 | License management — Trial and Enterprise modes. | May 2026 | Nov 2028 |
| **1.2.0** | Mar 2026 | SASL/SCRAM, NONE auth, **fencing filter**, librdkafka 2.0.0–2.13.0 support. | Sep 2026 | Mar 2029 |
| **1.3.0** (current) | Jul 2026 | Centralized governance (EA, Docker-only), OAuth→OAuth swap, CyberArk Conjur, fencing filter ordering change, SCRAM→NONE bugfix. | Jan 2027 | Jul 2029 |

Support policy: quarterly patch cadence, **three years** of technical support from the `.0` date, but only a **six-month patch window** yielding at most two patches per minor (e.g. 1.1.1 and 1.1.2 — never 1.1.3). To get fixes after that window, upgrade the minor version. 1.0.0 does not appear in the published lifecycle table.

### Client and protocol compatibility — audit this first

- Built on **Kafka Client 4.0**; inherits the Kafka 4.0 client/broker forward-compatibility guarantees.
- **Kafka protocol 3.x and 4.0.** Other third-party clients on compatible protocol versions "should work" but are **not** extensively tested — you own validation.
- **librdkafka v2.0.0–v2.13.0** officially supported (this is what makes non-Java clients viable).
- **Proprietary vendor APIs are not supported.** Confluent Platform-specific APIs such as `CREATE_CLUSTER_LINKS` and `LIST_CLUSTER_LINKS` **do not work through the gateway**. This matters more than it first appears: Cluster Linking is the replication substrate underneath gateway DR, so CL administration must go direct to the cluster, not through the proxy.

For an FSI estate with long-lived legacy apps, protocol-version audit is the first gate — it can disqualify the gateway for exactly the ancient clients you most wanted to migrate without touching.

### Deployment, sizing, and licensing

Self-managed only. Stateless with respect to Kafka data — offsets, transactions, and consumer-group state all live in the upstream cluster.

**Published system requirements** (per gateway instance):

| Resource | Requirement |
|---|---|
| CPU / memory (minimum) | 2 vCPU, 4 GB RAM |
| CPU / memory (recommended) | 4 vCPU, 8 GB RAM |
| Network throughput | 45 MB/s sustained per 1 Gbps link |
| Storage | 10 GB disk |

> These are Confluent-published numbers and supersede the generic "1.5–2× broker CPU" proxy heuristic previously carried in this article and in [DR Application Routing](../patterns/dr-application-routing.md). Still load-test against your own p99 budget — the parse-and-re-encode hop is real.

**Licensing:** mode is selected automatically by whether a key is present. **Trial** (default, no key) caps you at **4 routes**, community/limited support, unlimited duration — PoC only. **Enterprise** requires a valid key and lifts the route cap. The key differs by image: a Confluent Private Cloud Enterprise license for `cpc-gateway`, a Confluent Cloud Gateway license for `confluent-gateway-for-cloud`.

**CFK deployment** uses a `kind: Gateway` custom resource — a plain `kubectl apply -f gateway.yaml`. Reuse an existing CFK license; no separate CFK license purchase is needed for the gateway. Requires Docker Engine 20.10+ / Compose v2 on the Docker path.

```yaml
# CFK Gateway CR — top-level shape
kind: Gateway
metadata:
  name: fsi-gateway
  namespace: confluent
spec:
  image:
    application: confluentinc/cpc-gateway:<version-tag>      # or confluent-gateway-for-cloud for CC
    init: confluentinc/confluent-init-container:3.3.0
  streamingDomains: []                                       # upstream Kafka clusters
  secretStores: []                                           # required for auth swapping
  routes: []                                                 # client-facing listeners
  admin:
    bindAddress: 0.0.0.0
    port: 9190                                               # /metrics (Prometheus) and /livez
    endpoints:
      metrics: true
    commonTags:
      region: us-east-1                                      # applied to every emitted metric
  podTemplate:
    envVars:
      - name: GATEWAY_LICENSES                               # Enterprise mode
        valueFrom:
          secretKeyRef:
            name: confluent-gateway-licenses                 # k8s secret, one key per line
            key: licenses.txt
```

**Observability:** admin endpoint on port **9190** — `/metrics` (Prometheus scrape target) and `/livez`. JVM metrics (`JvmGcMetrics`, `JvmMemoryMetrics`, `JvmThreadMetrics`, `ProcessorMetrics`, `UptimeMetrics`) are enabled by default; `commonTags` adds host/region labels. Wire into the CFK/on-prem Grafana tier alongside broker JMX (see [Observability Metrics Mapping](observability-metrics-mapping.md)).

**HA:** multiple replicas behind a TCP load balancer, or a multi-endpoint bootstrap list. Failover between replicas is connection-level.

### Client Switchover — the mechanism, and its real cost

Client Switchover is the documented feature behind both DR and migration. Data replication between source and destination is **out of scope for the gateway** — you set that up separately with [Cluster Linking](cluster-linking-topology.md).

Mechanically: define two streaming domains, point the route at the source, then change `streamingDomain.name` to the destination.

```yaml
streamingDomains:
  - name: prod-domain
    type: kafka
    kafkaCluster:
      name: kafka-prod
      bootstrapServers:
        - id: internal-sasl-ssl
          endpoint: "SASL_SSL://kafka-prod.fsifirm.internal:9093"
  - name: dr-domain
    type: kafka
    kafkaCluster:
      name: kafka-dr
      bootstrapServers:
        - id: internal-sasl-ssl
          endpoint: "SASL_SSL://kafka-dr.fsifirm.internal:9093"

routes:
  - name: switchover-route
    endpoint: "kafka.fsifirm.com:9092"
    streamingDomain:
      name: prod-domain          # change to dr-domain to cut over
      bootstrapServerId: internal-sasl-ssl
```

> ⚠️ **Switchover requires a gateway restart.** This corrects the earlier claim in this article that route changes take effect on the running process. The documented procedure is: edit the route, then **stop and restart** the gateway. Every RTO estimate and every client-impact analysis must budget a full gateway restart, not a hot reconfiguration.

**Documented hard limitation:** switching between clusters **breaks message ordering and end-to-end consistency**, because source and destination are separate Kafka clusters. Confluent explicitly says **do not use Client Switchover for applications requiring strict ordering, such as Kafka Streams applications.** This is now a vendor statement, not an inference.

**Restart-impact by client role, with mitigations:**

| Component | Impact during restart | Mitigation |
|---|---|---|
| **Consumer** | Group rebalance triggers if the restart exceeds `session.timeout.ms` (default 45s). Consumers may reprocess messages if offsets weren't committed before restart. | `isolation.level=read_committed` to avoid reading aborted transactions; tune `group.coordinator.rebalance.protocols` and `group.coordinator.session.timeout.ms`. |
| **Producer** | Duplication when the broker acks but the gateway dies before relaying the ack, causing producer retries. | `enable.idempotence=true` (canon default anyway), or make the app duplicate-tolerant. |
| **Transactions** | EOS holds *across the restart window*: in-flight transactions commit if the outage is shorter than `transaction.timeout.ms`, else abort. Any transaction left open on the source **aborts and cannot be committed on the target**. | The producer application must reset transaction state on failure and start a new transaction. |

Note the two distinct transaction caveats — they live at different layers and both apply:
1. **Gateway layer** (above): open transactions don't survive the cluster swap.
2. **Cluster Linking layer:** CL does not support transactions on mirror topics at all.

For regulatory reporting workloads, **do not represent gateway + Cluster Linking failover as exactly-once-preserving.** See [Exactly-Once Semantics](exactly-once-semantics.md).

### Use case 1 — client migration (KCP)

Confluent extended **KCP** in Q2 2026 to drive gateway-based client migration off MSK/self-managed Kafka:

1. Deploy the gateway with streaming domains for **both** source and destination clusters.
2. Plan **migration groups** — related topics plus the apps that touch them.
3. Onboard clients to the gateway bootstrap endpoints. This is the only client-side change, and it is one-time.
4. Cut over group by group with three KCP commands:
   - **`init`** — validates infra, Cluster Linking config, and consumer offset sync. No traffic change.
   - **`lag-check`** — live terminal dashboard on replication lag; wait for acceptable.
   - **`execute`** — pause traffic → promote mirror topics → switch routes → resume.

Producer blocking is seconds; consumers see effectively zero downtime because offsets are synced. Auth is handled by the swap layer — SCRAM client credentials translate to CC API keys from the secret store, so clients never learn they moved.

**Limitations:** a migration group cuts over all-at-once (no separate producer/consumer phasing); principal- and topic-level granularity is future work; **rollback exists only until topic promotion completes.**

### Use case 2 — DR switchover

Cluster Linking replicates active→passive; the gateway closes the client-side switchover gap that CL alone leaves as a manual client reconfiguration. Planned mode does a graceful close with CL reversal; unplanned mode promotes mirror topics immediately.

Confluent's 60-second-RTO POC is explicitly **not production software**. Read its caveats as a requirements list:

- **Schema Registry failover is unsupported.**
- **Consumer group state requires manual management.**
- **Cluster Linking does not support transactions on mirror topics** — a real problem for EOS workloads and dangerous on failback.
- POC scope was single-region, Dedicated clusters, public endpoints, **OAuth2 required** — because OAuth2 and Identity Pools are org-scoped in CC, the same client ID/secret works across clusters; with API keys you'd need per-cluster credentials.

**FSI read:** the gateway moves *connections*, not *state*. For stateless producer/consumer apps, gateway + CL is a sound sub-minute RTO story *if* you budget the restart. For Kafka Streams (changelog/repartition topics, RocksDB) or in-flight EOS transactions, it is not — and Confluent's own docs now say so directly. Pair with an explicit state-rebuild plan or budget the reset into your RTO.

### Use case 3 — secure external/partner access

Brokers stay private; the gateway is the only public surface, terminating mTLS and enforcing policy centrally. Combined with fencing and per-route auth swapping, this is a cleaner partner-access story than punching broker-level ACLs plus public endpoints.

### When to use Confluent Gateway

- **Migrating a large client estate** to Confluent Cloud where coordinating app redeploys is the actual blocker. This is the strongest case.
- **Sub-minute DR RTO on stateless workloads** with Cluster Linking already in place, and a restart budgeted into the RTO.
- **Auth bridging** — legacy mTLS/SCRAM client population against a modern OAUTHBEARER cluster, without a coordinated client rollout.
- **Partner/external access** to otherwise-private brokers.
- **Multi-tenant traffic control** where fencing a client at the proxy beats an ACL roll.

### When NOT to use Confluent Gateway

- **Strict-ordering or stateful apps — especially Kafka Streams.** Vendor-documented exclusion, not a judgment call.
- **CC-only greenfield** with native PrivateLink and Cluster Linking already working — you're adding an operational tier for limited gain.
- **Latency-critical paths** — parse + re-encode of every Kafka frame is a real p99 tail cost. Measure first.
- **Kafka 2.x clients in the estate** — hard incompatibility.
- **Anywhere you need Cluster Linking admin APIs through the same endpoint** — `CREATE_CLUSTER_LINKS`/`LIST_CLUSTER_LINKS` don't traverse the gateway.

### FSI considerations

- **Vendor backing satisfied.** Confluent Gateway is a Confluent-supported, licensed product with a published three-year support lifecycle — it meets the FSI vendor-contract rule. Envoy Kafka filters and custom Netty proxies do not.
- **Enterprise licensing is mandatory in production** — Trial's 4-route cap and community-only support disqualify it for regulated workloads. Budget the license.
- **mTLS termination at the gateway** with re-auth to the broker centralizes FSI client-cert lifecycle: the gateway holds broker-side credentials (Conjur/Vault), client certs rotate independently.
- **Secret store choice matters.** CyberArk Conjur support (1.3.0) is the one that usually clears FSI review; it pins you to ≥1.3.0.
- **Audit logging** — enable `logNetwork` and `logFrames` per route deliberately. `logFrames` logs Kafka protocol frames and is a **data-exposure risk** in regulated environments; leave it off outside of scoped troubleshooting. Forward gateway events to SIEM alongside broker audit logs (see [Audit Log SIEM Integration](../patterns/audit-log-siem-integration.md)).
- **Exactly-once:** see the two-layer transaction caveat above. Do not claim EOS preservation across a switchover for regulatory reporting.
- **Patch discipline:** the six-month patch window means an FSI change-freeze calendar can strand you on an unpatchable minor. Plan minor upgrades on a ≤6-month cadence.

## Related

- [Private Networking — PrivateLink Gateway, PNI, Peering, TGW](private-networking.md) — disambiguation: CC PrivateLink Gateway is a networking resource, and "one gateway per environment per region" is that rule, not this product
- [DR Application Routing](../patterns/dr-application-routing.md) — routing-pattern view of the gateway's DR use case
- [DR — Cluster Linking](../patterns/dr-cluster-linking.md) — the replication substrate; a prerequisite for switchover, and not administrable through the gateway
- [DR — MirrorMaker 2](../patterns/dr-mirrormaker2.md) — alternative replication backend for CFK/CP topologies
- [Cluster Linking Topology](cluster-linking-topology.md) — six CL topology patterns that determine which switchover model applies
- [Exactly-Once Semantics](exactly-once-semantics.md) — why switchover is not EOS-preserving
- [Network Connectivity by Cluster Tier](network-connectivity-by-tier.md) — where the gateway sits relative to CC tier networking
- [Observability Metrics Mapping](observability-metrics-mapping.md) — wiring the `:9190/metrics` endpoint into the CFK/on-prem Grafana tier
