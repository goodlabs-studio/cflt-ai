# Review: Confluent Gateway — Protocol-Aware Kafka Proxy

**Date:** 2026-08-06
**Source files:** wiki/concepts/confluent-gateway.md
**Scope:** Confluent Gateway — architecture (Streaming Domains/Routes/Policies), both backend flavors (self-managed and Confluent Cloud), Client Switchover/DR mechanics, KCP migration, auth swapping/passthrough, centralized governance, licensing/support lifecycle, FSI considerations
**Claims extracted:** 40

## Summary

This is a re-review of an article that has been edited four times since its last full review (2026-08-05): renamed, merged with a since-deleted `confluent-cloud-gateway.md` companion article, and had its disambiguation section rewritten twice. Nearly every claim checked against `confluent-docs` (both the `private-cloud-gateway/` and the newly-relevant `cloud/current/cp-component/gateway/` doc trees) is confirmed, including the new "Backend flavor" section added this session. Two findings carry over unresolved from the prior review and are now sharper: the Core Capabilities auth-swap table still omits **mTLS** even though the article's own new CC-flavor example demonstrates an mTLS swap two sections later — an internal self-contradiction, not just a gap. And the "sub-minute DR RTO" framing in Use Case 2 doesn't map to any of the four canonical FSI SLA tiers, which is a real risk if this article gets used to justify Gateway-based DR for a risk- or compliance-tier workload. One new canon-compliance finding: the worked example for connecting to Confluent Cloud uses a static API-key/secret pair (`SASL_SSL`+`PLAIN`) as the primary path, which is structurally the "username/password" pattern FSI canon prohibits — the compliant OAuth alternative is mentioned only in prose, not shown as a worked example.

## Claim Validation

### Summary

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| confluent-gateway-1 | Self-managed, stateless, Kafka-protocol-aware proxy; rewrites Metadata, swaps auth, custom domain, re-targets clusters without client config change | — | `overview.html` (both trees) | — | — | Confirmed |
| confluent-gateway-2 | Ships as one product with two backend flavors differing only by image (`cpc-gateway` / `confluent-gateway-for-cloud`); no fully-managed CC SKU | `confluent-cloud-private-networking.md` (disambiguation, no overlap) | `co-gateway-overview.html`, `cloud/current/cp-component/gateway/overview.html` | — | — | Confirmed |
| confluent-gateway-3 | Current release 1.3.0 (July 2026) | — | `gateway-release-notes.html` | — | — | Confirmed |
| confluent-gateway-4 | Switchover requires a gateway restart identically for both backend flavors | `patterns/dr-application-routing.md` (aligned, re-checked this pass) | `gateway-migrate.html` + `cloud/current/cp-component/gateway/gateway-migrate.html` (fetched both trees, word-for-word identical) | — | — | **Confirmed in both trees** |
| confluent-gateway-5 | Docs direct against switchover for strict-ordering apps like Kafka Streams | — | `gateway-migrate.html` | kafka-streams-programming | Confirmed | Confirmed |
| confluent-gateway-6 | Distinct from Confluent Cloud Ingress PrivateLink Gateway (unrelated CC networking resource) | `confluent-cloud-private-networking.md` | — | — | — | Confirmed |

### Naming and disambiguation

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| confluent-gateway-7 | Confluent Gateway operates at Kafka protocol layer; PrivateLink Gateway at network layer | `confluent-cloud-private-networking.md` | `overview.html` | — | — | Confirmed |
| confluent-gateway-8 | `confluent_gateway` Terraform resource belongs to PrivateLink Gateway; Confluent Gateway has no native Terraform resource | `patterns/terraform-cicd-confluent-private-networking.md` (confirms `confluent_gateway`+`confluent_access_point` as the PrivateLink resource pair) | Absence across full doc tree (both flavors) | — | — | Confirmed |
| confluent-gateway-9 | "One gateway per environment per region" is the PrivateLink/PNI rule, unrelated to this product | `confluent-cloud-private-networking.md` | — | — | — | Confirmed |

### What protocol-aware buys you / Architecture / Broker identification

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| confluent-gateway-10 | TCP LB can't rewrite Metadata; DNS aliasing alone insufficient | `patterns/dr-application-routing.md` (identical framing) | `overview.html` | — | — | Confirmed |
| confluent-gateway-11 | Gateway swaps SASL mechanisms client-side vs. broker-side | — | `gateway-security.html` | — | — | Confirmed |
| confluent-gateway-12 | Streaming Domains: bootstrapServers[] (id+protocol://host:port), TLS material, optional nodeIdRanges | — | `gateway-deploy.html`, `co-gateway-deploy.html` | — | — | Confirmed (verbatim) |
| confluent-gateway-13 | Routes: name (≤30 chars, default `route-<index>`), endpoint, brokerIdentificationStrategy, streamingDomain ref, optional fence/security/logNetwork/logFrames | — | `co-gateway-deploy.html` | — | — | Confirmed (verbatim — this was Unverifiable in the prior review; the CFK CRD reference fetched since then confirms it) |
| confluent-gateway-14 | A cutover = repoint route at different streaming domain | — | `gateway-migrate.html` | — | — | Confirmed |
| confluent-gateway-15 | `port` (default): each broker own port, requires nodeIdRanges | — | `gateway-deploy.html` | — | — | Confirmed (verbatim) |
| confluent-gateway-16 | `host`: SNI-based, `pattern` with `$(nodeId)`, requires wildcard DNS | — | `gateway-deploy.html`, `gateway-custom-domains.html` | — | — | Confirmed |

### Core capabilities

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| confluent-gateway-17 | Network isolation: same-VPC/cross-VPC/external patterns | — | `gateway-custom-domains.html` | — | — | Confirmed (verbatim) |
| confluent-gateway-18 | Auth-swap pairs: SASL/SCRAM→SASL/PLAIN, OIDC→SASL, OAuth→OAuth (1.3.0), NONE | — | `gateway-security.html` | — | — | **Corrected — see below** |
| confluent-gateway-19 | Fencing: `fence.scope` ALL\|NONE, default `errorCode BROKER_NOT_AVAILABLE`; 1.3.0 reorders fencing before auth-swap | — | `gateway-deploy.html`, `gateway-release-notes.html` | — | — | Confirmed (verbatim) |
| confluent-gateway-20 | Centralized governance 1.3.0 EA/Docker-only; 4 policy types, Avro/JSON Schema/Protobuf, per-topic overrides | — | `gateway-release-notes.html`, `overview.html` | — | — | Confirmed (verbatim) |

**Corrections:**
- **Claim confluent-gateway-18**: The Core Capabilities table's auth-swap pairs list still omits **mTLS**, exactly as flagged in the 2026-08-05 review's Corrections (never remediated). This is now sharper than before: the article's own new "Backend flavor: connecting to a Confluent Cloud cluster" section (line 212 of the current file) shows a worked `clientAuth: mtls:` swap example — meaning the document now **demonstrates** mTLS swapping in one section while its own capability summary table two sections earlier still doesn't list it as supported. Fix: add mTLS to the "Supported pairs" sentence in Core Capabilities.

### Version history, support lifecycle, compatibility

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| confluent-gateway-21 | 1.1.0/1.2.0/1.3.0 feature sets and EOL/EOS dates | — | `gateway-release-notes.html`, `gateway-deploy-overview.html` (private-cloud-gateway tree) | — | — | Confirmed for the self-managed flavor; **Unverifiable for the Confluent Cloud flavor** — see Gaps |
| confluent-gateway-22 | Quarterly patch, 3yr support, 6-month patch window, max 2 patches/minor | — | `gateway-deploy-overview.html` | — | — | Confirmed (verbatim) |
| confluent-gateway-23 | Kafka Client 4.0, protocol 3.x/4.0, librdkafka 2.0.0–2.13.0, other clients untested | — | `gateway-deploy-overview.html` | — | — | Confirmed (verbatim) |
| confluent-gateway-24 | `CREATE_CLUSTER_LINKS`/`LIST_CLUSTER_LINKS` don't work through gateway | — | `gateway-deploy-overview.html` | — | — | Confirmed (verbatim) |

### Deployment, sizing, licensing (both flavors)

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| confluent-gateway-25 | Sizing: 2vCPU/4GB min, 4vCPU/8GB rec, 45MB/s per 1Gbps, 10GB disk | — | `gateway-deploy-overview.html` **and** `cloud/current/cp-component/gateway/overview.html` (identical numbers in both trees) | — | — | **Confirmed, identical across both flavors** |
| confluent-gateway-26 | Trial (no key, 4-route cap, community support) / Enterprise (key required, unlimited routes); key differs by image | — | `gateway-deploy-overview.html`, `co-gateway-deploy.html` (license-by-image table) | — | — | Confirmed (verbatim) |
| confluent-gateway-27 | CFK reuses existing CFK license; Docker requires Engine 20.10+/Compose v2 | — | `co-gateway-deploy.html`, `gateway-deploy-overview.html` | — | — | Confirmed (verbatim) |
| confluent-gateway-28 | No Terraform resource for either flavor; CFK CRD generically Terraform-able via `kubernetes_manifest`/`kubectl_manifest` | `patterns/terraform-cicd-confluent-private-networking.md` | Absence across both doc trees | — | — | Confirmed |
| confluent-gateway-29 | Admin port 9190: `/metrics`, `/livez`; default JVM metrics list | — | `gateway-deploy.html`, `co-gateway-deploy.html` | — | — | Confirmed (verbatim) |
| confluent-gateway-30 | HA: multiple replicas behind LB; failover connection-level | — | `co-gateway-troubleshoot.html` (`kubectl get svc/pods -l app=confluent-gateway`) | — | — | Confirmed |

### Backend flavor: connecting to a Confluent Cloud cluster (new section this session)

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| confluent-gateway-31 | Same CR/compose schema; swap image+license, point streaming domain at CC bootstrap | — | `co-gateway-deploy.html` (CC listed as a first-class `kafkaCluster` target) | — | — | Confirmed |
| confluent-gateway-32 | CC endpoints use publicly-trusted CA certs; no custom truststore needed by default | — | (not independently re-verified; general knowledge of CC's public-CA TLS posture, consistent with no truststore config shown in any CC example) | — | — | Unverifiable via MCP this session — plausible, not contradicted |
| confluent-gateway-33 | Auth swap targets: CC API key/secret (`SASL_SSL`+`PLAIN`) or CC OAuth/Identity Pools (`SASL_SSL`+`OAUTHBEARER`) | — | `gateway-security.html` | — | — | Confirmed |
| confluent-gateway-34 | Identity passthrough only valid for clients already on CC-compatible SASL (PLAIN/SCRAM/OAUTHBEARER) | — | `gateway-security.html` (passthrough explicitly unsupported for mTLS) | — | — | Confirmed |
| confluent-gateway-35 | Documented failure mode: OAUTHBEARER passthrough breaks after switchover (stale `lkc` extension); fix via `passthroughConfig` | — | `co-gateway-troubleshoot.html` | — | — | Confirmed (verbatim — dedicated troubleshooting entry) |
| confluent-gateway-36 | CC flavor's governance validates against CC Schema Registry specifically | — | `cloud/current/cp-component/gateway/overview.html` | — | — | Confirmed (verbatim) |

### Client Switchover mechanism

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| confluent-gateway-37 | Data replication out of scope for gateway; set up via Cluster Linking separately | `patterns/dr-cluster-linking.md` | `gateway-migrate.html` (both trees) | — | — | Confirmed |
| confluent-gateway-38 | Switchover requires gateway restart; documented procedure edit-then-restart | `patterns/dr-application-routing.md` (re-checked, still aligned) | `gateway-migrate.html` (both trees, verbatim) | — | — | Confirmed |
| confluent-gateway-39 | Switching breaks ordering/consistency; vendor excludes Kafka Streams | `patterns/dr-application-routing.md` | `gateway-migrate.html` | kafka-streams-programming | Confirmed | Confirmed |
| confluent-gateway-40 | Restart-impact table (consumer rebalance, producer duplication, transaction abort-on-source) | — | `gateway-migrate.html` (both trees — table wording near-identical) | — | — | Confirmed (verbatim) |

**Corrections:**
- No new corrections in this section. One unresolved wording nuance carried over from the prior review: `wiki/concepts/cluster-linking-topology.md` still describes CL's transaction handling as "transactional messages are replicated but cross-topic atomicity is not preserved," while this article says CL "does not support transactions on mirror topics at all" (line 288). Same substance, different emphasis — this was recommended for alignment in the 2026-08-05 review and still hasn't been applied. Not a correctness issue, just unfinished cross-document polish.

## Premise Challenge

| # | Premise | Assumption | Challenge | Severity |
|---|---------|------------|-----------|----------|
| 1 | "Sub-minute DR RTO" (Use Case 2) is a meaningful target for FSI workloads | Readers will correctly place "sub-minute" against the four canonical FSI SLA tiers | It doesn't map to any of them. Market data is sub-millisecond, risk is <10ms, compliance is <100ms — all orders of magnitude tighter than "sub-minute" (tens of seconds). Only "reconciliation" (async) is loose enough to plausibly fit. The article never states this, so a reader could wrongly cite Gateway DR as satisfying a risk- or compliance-tier SLA when it categorically cannot. | Critical |
| 2 | The Core Capabilities auth-swap table is a complete, self-consistent list | mTLS isn't listed as a swap pair there, and the rest of the document doesn't contradict that | The document's own new "Backend flavor" section shows a worked `clientAuth: mtls:` swap example. The article now contradicts itself internally, not just under-documents a real capability (as in the prior review). | Critical |
| 3 | Version history / support lifecycle (1.1.0–1.3.0 dates) applies identically to the Confluent Cloud flavor | The self-managed flavor's release-notes page is authoritative for both | Only the self-managed (`private-cloud-gateway/`) release-notes page was fetched. The Confluent Cloud flavor's own release-notes page (under `cloud/current/cp-component/gateway/`) was never independently checked for matching version cadence or EOL/EOS dates this session. Sizing and switchover mechanics were confirmed identical across both trees; the lifecycle table wasn't. | Moderate |
| 4 | "Vendor backing satisfied... meets the FSI vendor-contract rule" covers both flavors under one procurement relationship | One Confluent contract covers both license SKUs (CPC Enterprise and CC Gateway license) automatically | The document doesn't say whether these are one contract line or two from a vendor-management standpoint — worth confirming before an FSI procurement/legal review, since the two license types are enumerated as genuinely distinct SKUs. | Moderate |
| 5 | The passthrough-vs-swap guidance in "Backend flavor" fully conveys the mTLS restriction | Saying passthrough is "only valid if clients already speak a CC-compatible SASL mechanism" implicitly excludes mTLS | Technically correct (mTLS isn't SASL) but doesn't say outright that mTLS clients are unconditionally barred from passthrough — a reader could miss the exclusion rather than infer it. | Minor |

## Canon Compliance

| Area | Status | Notes |
|------|--------|-------|
| `security.auth_mechanism` (mTLS + RBAC; never username/password in FSI) | **Partial** | Client-side mTLS is supported and shown in the CC-flavor example (compliant). But that same example's **cluster-side** (gateway→CC) auth uses `SASL_SSL`+`PLAIN` with a static API key/secret — structurally the "username/password" pattern canon prohibits for FSI. The compliant alternative (`SASL_SSL`+`OAUTHBEARER` via CC OAuth/Identity Pools) is mentioned only in prose one paragraph later, not shown as a worked example. For an FSI-facing version of this article, the OAUTHBEARER variant should be the primary worked example, with API-key/PLAIN demoted to a non-FSI note. |
| Producer/consumer canon (`acks=all`, `enable_idempotence`, `isolation.level=read_committed`) | Compliant | Restart-impact mitigation table matches canon exactly (unchanged from prior review). |
| `schema_registry` (Avro/Protobuf, compatibility) | Compliant | Governance EA/Docker-only caveat still correctly flagged. |
| `cluster_linking` (preferred over MM2, explicit control) | Compliant | Unchanged from prior review. |
| `security.audit_log` | Compliant | `logFrames` risk correctly flagged; SIEM forwarding recommended. |
| `topic_design.naming_convention` | N/A | Gateway routing namespace is not Kafka topic naming. |

## Gaps

1. **Confluent Cloud flavor's own version/support-lifecycle page was not independently fetched.** The version history table's exact dates (EOL/EOS per release) were confirmed only against the self-managed flavor's release notes. Given the two flavors otherwise track in lockstep (identical sizing, identical switchover mechanics, confirmed this session), the lifecycle table is very likely also shared — but this wasn't independently checked. Recommend a follow-up MCP fetch of the `cloud/current/cp-component/gateway/` release-notes-equivalent page before treating the dates as flavor-agnostic in a customer-facing SLA conversation.
2. **CC endpoint TLS/truststore claim (confluent-gateway-32)** rests on general knowledge of Confluent Cloud's public-CA posture rather than a directly fetched confirmation for the Gateway product specifically.
3. **Cross-document wording nuance** between this article and `cluster-linking-topology.md` on CL transaction support (same substance, different phrasing) — flagged in the prior review, still unresolved, low priority.

## Recommendations

1. **Add mTLS to the Core Capabilities auth-swap row.** This is the second review to find this gap, and it's now a self-contradiction against the article's own worked example — highest-priority fix from this pass.
2. **Add an explicit SLA-tier caveat to Use Case 2.** One sentence stating that "sub-minute" does not satisfy the risk (<10ms) or compliance (<100ms) FSI tiers, and is realistically scoped to reconciliation-tier (async) workloads, would close a real misapplication risk.
3. **Swap the primary CC auth example to OAUTHBEARER, or add an explicit FSI callout on the PLAIN/API-key path.** As written, the only worked example for connecting to Confluent Cloud uses the non-compliant pattern for regulated environments.
4. **Fetch the Confluent Cloud flavor's release-notes-equivalent page** to confirm the version/support-lifecycle table is genuinely shared, not just assumed shared by extension from the sizing/switchover parity already confirmed.
5. Lower priority, carried from the 2026-08-05 review: align the Cluster Linking transaction-support wording between this article and `cluster-linking-topology.md`.

---
Canon stack: base + industry/fsi | Hash: 437a88b8eb364e19 | MANIFEST: unavailable (raw/repos/fsi-dsp/MANIFEST.yaml not present in this checkout) | Floor: claude-sonnet-5 | Generated: 2026-08-06T15:48:52Z
