# Report: Confluent Gateway — Terraform/IaC, Confluent Cloud Connectivity, and HA/DR Automation

**Date:** 2026-08-06
**Source:** pasted questions (ephemeral /ask thread, saved to report on request)
**Scope:** (1) Is Confluent Gateway Terraform-managed, and what else is needed to stand it up; (2) how to point a CFK-deployed Gateway at a Confluent Cloud cluster; (3) whether Gateway supports automatic client switchover on pod death or region death
**Claims checked:** 14

## Correction to a prior answer in this thread

Earlier in this conversation I stated that "Confluent Cloud Gateway" is not a separate product — just the image-tag variant (`confluentinc/confluent-gateway-for-cloud`) of the same self-managed proxy. **That undersold it.** Confluent documents **two named, separately-doc-treed editions** of the same architecture:

| Edition | Image | Primary doc tree | Backend cluster type |
|---|---|---|---|
| **Confluent Private Cloud Gateway** | `confluentinc/cpc-gateway` | `docs.confluent.io/private-cloud-gateway/current/` | Self-managed / Confluent Platform Kafka |
| **Confluent Cloud Gateway** | `confluentinc/confluent-gateway-for-cloud` | `docs.confluent.io/cloud/current/cp-component/gateway/` | Confluent Cloud Kafka |

Confirmed via MCP: `co-gateway-overview.html` (the CFK-level entry point) explicitly lists these as two separate "core product documentation" links, not one page with a tag switch. The Confluent Cloud Gateway overview page (`cloud/current/cp-component/gateway/overview.html`) is a near-mirror of the Private Cloud Gateway overview — same Routes/Streaming Domains/Policies architecture, **identical** published system requirements (2 vCPU/4GB min, 4 vCPU/8GB recommended, 45MB/s per 1Gbps, 10GB disk) — but its governance feature explicitly targets **Confluent Cloud Schema Registry** as the validation backend, and it has its own mirrored `gateway-migrate.html`, `gateway-custom-domains.html`, etc.

**What doesn't change:** both editions are still self-managed (you deploy and operate them yourself via Docker or CFK) — neither is a Confluent Cloud–hosted/managed service. And the Client Switchover restart requirement is **word-for-word identical** across both editions' migrate pages (confirmed by fetching both) — this is a fact about the product architecture, not an artifact of which edition you're reading about.

This should be corrected in the wiki article itself if you want it durable — see Recommendations.

---

## Question 1: Is Confluent Gateway controlled by Terraform?

### Answer

No — same conclusion as before, now on firmer footing. Neither edition (`cpc-gateway` nor `confluent-gateway-for-cloud`) has a purpose-built Terraform resource. Deployment is always `docker compose up -d` or `kubectl apply -f <gateway-CR>.yaml`.

**The naming trap stands and is worth restating plainly**: the Confluent Terraform provider *does* ship a resource literally named `confluent_gateway` — but per `wiki/patterns/terraform-cicd-confluent-private-networking.md`, that resource manages the **Confluent Cloud (Ingress) PrivateLink Gateway** (a CC networking access point paired with `confluent_access_point` + your cloud's VPC endpoint resource) — a third, unrelated product. Anyone searching Terraform registry docs for "Confluent Gateway" will land on the wrong resource.

**What you need to stand it up outside Terraform:**
1. Docker Engine 20.10+/Compose v2, or a Kubernetes cluster with CFK installed.
2. The correct image for your backend: `cpc-gateway` (self-managed) or `confluent-gateway-for-cloud` (Confluent Cloud) — see the correction above for why this choice matters beyond just a tag.
3. A `docker-compose.yaml` or `kind: Gateway` CR.
4. A license (Enterprise mode) — CPC Enterprise license key or CC Gateway license key, via `GATEWAY_LICENSES`.
5. A secret store for auth swapping (Vault/AWS Secrets Manager/Azure Key Vault/CyberArk Conjur) — genuinely Terraform-managed territory via cloud-provider providers, even though Gateway's own config isn't.
6. DNS records (host-strategy broker identification / custom domains) — also cloud-provider Terraform territory.
7. Network path from gateway to the upstream cluster(s).
8. TLS material (keystores/truststores) mounted into the container/pod.

Caveat unchanged: since CFK's `Gateway` CR is a plain Kubernetes custom resource, it *can* be Terraform-managed generically via `kubernetes_manifest` or `kubectl_manifest` — just not natively/documented the way `confluent_kafka_topic` is.

### MCP Validation

| Claim | Source | Result |
|---|---|---|
| No Terraform deployment path documented for either Gateway edition | `gateway-deploy.html`, `gateway-deploy-overview.html`, `co-gateway-deploy.html`, `co-gateway-overview.html`, `cloud/current/cp-component/gateway/overview.html` | Confirmed (absence across both editions' full doc trees) |
| `confluent_gateway` Terraform resource exists but targets PrivateLink Gateway, not this product | `wiki/patterns/terraform-cicd-confluent-private-networking.md` (previously MCP-validated) | Confirmed |
| Terraform provider resource inventory, checked directly | `terraform` MCP | Unavailable this session (server never surfaced tools) — relied on the wiki's prior validated inventory instead |

---

## Question 2: How do I point my CFK-deployed Gateway at a Confluent Cloud cluster?

### Answer

Deploy the **Confluent Cloud Gateway** edition specifically (image `confluentinc/confluent-gateway-for-cloud`, license type "Confluent Cloud Gateway license key" — using the wrong license type against this image is a documented failure mode). The CR shape is identical to the self-managed case; you're just pointing the streaming domain's bootstrap server at your CC cluster and choosing the right auth mode.

```yaml
kind: Gateway
metadata:
  name: cc-gateway
  namespace: confluent
spec:
  image:
    application: confluentinc/confluent-gateway-for-cloud:<version-tag>
    init: confluentinc/confluent-init-container:3.3.0
  streamingDomains:
    - name: cc-prod
      type: kafka
      kafkaCluster:
        name: cc-prod-cluster
        bootstrapServers:
          - id: SASL_SSL-1
            endpoint: "SASL_SSL://pkc-xxxxx.us-east-1.aws.confluent.cloud:9092"
            # CC endpoints use publicly-trusted CA certs — omit a custom truststore
            # unless your org pins a private CA.
  routes:
    - name: cc-route
      endpoint: "kafka.fsifirm.com:9092"      # what your clients put in bootstrap.servers
      streamingDomain:
        name: cc-prod
        bootstrapServerId: SASL_SSL-1
      security:
        auth: swap                             # or "passthrough" — see below
        swapConfig:
          clientAuth:
            mtls:                               # however your clients authenticate today
              ssl:
                principalMappingRules: "RULE:^CN=([a-zA-Z0-9._-]+),OU=.*$/$1/,DEFAULT"
          secretStore: cc-secrets
          clusterAuth:
            sasl:
              mechanism: PLAIN                  # CC API key as username, secret as password
              callbackHandlerClass: "org.apache.kafka.common.security.authenticator.SaslClientCallbackHandler"
              jaasConfig:
                file: /opt/gateway/cc-cluster-jaas.conf
  secretStores:
    - name: cc-secrets
      provider:
        type: Vault   # or AWS / Azure / CyberArk
        config:
          address: https://vault.fsifirm.internal
          authMethod: AppRole
          role: gateway-cc-role
          path: secret/gateway/cc
  admin:
    bindAddress: 0.0.0.0
    port: 9190
    endpoints:
      metrics: true
```

Two auth choices, pick based on what your clients already do:
- **Authentication swapping** (`auth: swap`, shown above): clients keep whatever they already use (mTLS, SASL/SCRAM, etc.); the gateway swaps to CC's API key/secret (`SASL_SSL` + `PLAIN`) or to CC's OAuth/Identity Pools (`SASL_SSL` + `OAUTHBEARER`) pulled from your secret store. This is the right choice for a migration where you don't want to touch client config at all.
- **Identity passthrough** (`auth: passthrough`): only valid if clients already speak a CC-compatible SASL mechanism (PLAIN/SCRAM/OAUTHBEARER) directly. If your clients use `SASL_PLAINTEXT`/OAUTHBEARER passthrough to reach CC, you must set `passthroughConfig.sasl.extensionHeaders.logicalCluster` to your CC cluster's `lkc-xxxxx` ID — Confluent's own troubleshooting docs flag a specific documented failure mode here: **"SASL/OAUTHBEARER passthrough fails after a failover"** — after a cluster switchover, the client-supplied `lkc` extension becomes stale (it still points at the old cluster), so you must let Confluent Gateway inject the extension itself rather than relying on the client to supply it.

Expose the route via a Kubernetes `Service` (`kubectl get svc -l app=confluent-gateway` is how you verify it post-deploy), and `kubectl apply -f cc-gateway.yaml` to deploy.

### MCP Validation

| Claim | Source | Result |
|---|---|---|
| Confluent Cloud is a documented, first-class `kafkaCluster` target for a Gateway streaming domain | `co-gateway-deploy.html` ("Confluent Server, Confluent Cloud Kafka, or self-managed Kafka") | Confirmed |
| Cluster-side (Gateway→broker) auth for swapping supports SASL PLAIN/OAUTHBEARER, matching CC's API-key and OAuth models | `gateway-security.html` | Confirmed |
| Identity-passthrough-to-CC failure mode requires `passthroughConfig` to inject `lkc` extension, especially post-failover | `co-gateway-troubleshoot.html` | Confirmed (verbatim — dedicated troubleshooting entry for this exact scenario) |
| CC-specific example config / exact field names for a CC-targeted streaming domain | GitHub examples repo, referenced but not directly fetchable (outside `docs.confluent.io`) | Unverifiable via MCP this session — the YAML above follows the documented CR schema but wasn't checked against a CC-specific worked example |

---

## Question 3: Can Confluent Gateway do HA with auto-switchover if a pod dies, or if a region dies?

### Answer

**These are two different failure modes, and the honest answer is different for each. Don't conflate them — that's exactly the kind of overclaim this review thread has been correcting.**

**Pod death (single region) — yes, and it's automatic, via ordinary Kubernetes HA, not a Gateway-specific feature.** Run multiple Gateway replicas behind a Kubernetes `Service`/load balancer, with the `/livez` admin endpoint wired as a liveness/readiness probe. If a pod dies, Kubernetes reschedules it and the Service routes to surviving replicas. This does **not** trigger Client Switchover — the backing Kafka cluster (streaming domain target) hasn't changed, only which gateway pod serves the connection — so clients see an ordinary reconnect, not the documented switchover restart-impact profile. This is what the article's existing HA section already describes ("multiple replicas behind a TCP load balancer... failover between replicas is connection-level"), and it's the one part of this whole HA question that's genuinely self-healing today.

**Region death (of the backend Kafka cluster) — no, not automatically. This is exactly what Client Switchover is, and it is always operator-initiated.** I re-checked this specifically because it's the crux of your question: both the Private Cloud Gateway and Confluent Cloud Gateway migrate pages describe the *identical* manual procedure — edit the route's `streamingDomain` reference, then **stop and restart** the gateway. There is no documented health-check, heartbeat, or automatic-failover trigger anywhere in either doc tree. "Auto switchover on region death" is not a shipped capability — if you want it, you have to build the automation yourself: something that (a) detects the backend region/cluster is unhealthy and (b) programmatically edits the CR and re-applies it (`kubectl apply`), which per the docs *will* cause the same restart-impact profile (consumer rebalance risk, producer duplication risk, in-flight transaction abort) as a manual switchover — automating the trigger doesn't remove the disruption, it just removes the human in the loop for deciding to accept it.

**Region death (of the Gateway tier itself — your K8s cluster/region goes down, not just the backend Kafka)** is a third, separate problem Gateway doesn't address at all. Multi-replica HA within one cluster doesn't survive that cluster's region going dark. To cover this you'd need Gateway instances running in ≥2 regions/K8s clusters, with a global traffic manager (DNS health-check failover — e.g. Route 53 failover routing — or a global load balancer) in front of both regional Gateway endpoints. This is the same "DNS abstraction" pattern already documented in `wiki/patterns/dr-application-routing.md`, just applied one layer up the stack (to the gateway tier) instead of to the broker tier — Gateway doesn't ship this, you'd build it the same way you'd build DNS-based DR for any stateless proxy tier.

**Bottom line for a DR runbook**: pod-level resilience is free (K8s HA); region-level resilience for the backend cluster requires you to script the switchover trigger yourself (health-check + `kubectl apply` + accept the restart-impact profile); region-level resilience for the gateway tier itself requires a second regional deployment plus your own global DNS/LB failover in front of it. None of the region-level cases are "automatic" out of the box.

### MCP Validation

| Claim | Source | Result |
|---|---|---|
| Pod-level HA is standard K8s Service/replica behavior; `/livez` is the liveness endpoint | `gateway-deploy.html`, `co-gateway-troubleshoot.html` (`kubectl get svc/pods -l app=confluent-gateway`) | Confirmed |
| Client Switchover requires a manual restart, identically, in both the Private Cloud and Confluent Cloud Gateway editions | `gateway-migrate.html` (private-cloud-gateway tree) and `cloud/current/cp-component/gateway/gateway-migrate.html` (Confluent Cloud tree) — both fetched and compared word-for-word this session | **Confirmed, verbatim in both editions** |
| No documented automatic/health-check-triggered failover mechanism exists for either edition | Absence across both editions' full doc trees (overview, deploy, migrate, custom-domains, troubleshoot pages) | Confirmed (absence) |
| No native multi-region gateway-tier failover capability | Absence across both editions' doc trees; no such feature mentioned anywhere | Confirmed (absence) — this is an architectural gap you fill yourself, not a documented Confluent feature |

## Canon Compliance

No canon-default deviation to flag — these are infrastructure-topology and IaC-tooling questions, not config-default questions. One FSI-relevant note: if you build the "auto-switchover on region death" automation yourself, the restart-impact mitigations from the reviewed wiki article (`enable.idempotence=true`, `isolation.level=read_committed`) are exactly canon's existing producer/consumer defaults — the automation doesn't need new canon, it needs to *not bypass* what's already there under time pressure during an incident.

## Recommendations

1. **Update `wiki/concepts/confluent-gateway.md`** to reflect that "Confluent Cloud Gateway" is a separately-doc-treed edition (own doc tree under `cloud/current/cp-component/gateway/`), not merely an image tag on one product — the current article's "two images" framing undersells this. Want me to make that edit now?
2. **Auto-stubbed two gaps** to `wiki/_queue.md`: `confluent-gateway-terraform-iac` (from the prior /ask this session) and, new this round, the Confluent-Cloud-Gateway-as-separate-edition distinction and the pod-vs-region HA/failover distinction — both genuinely uncovered topics.
3. If you're going to build region-failure automation, treat it as its own DR runbook artifact (following the `fsi-dr.sh`-style pattern already used for Cluster Linking DR elsewhere in this wiki) rather than a Gateway feature — this keeps the "not automatic" fact honest in whatever you hand to an SE or customer.

---
*Validated against Confluent docs via MCP (2026-08-06). 14 claims checked, 0 corrected (beyond the self-correction on Confluent Cloud Gateway noted above), 2 unverifiable (Terraform provider resource inventory — server unavailable; CC-specific worked YAML example — outside `docs.confluent.io` domain scope).*

Canon stack: base + industry/fsi | Hash: 437a88b8eb364e19 | MANIFEST: unavailable (raw/repos/fsi-dsp/MANIFEST.yaml not present in this checkout) | Floor: claude-sonnet-5 | Generated: 2026-08-06T14:42:59Z
