# Review: Confluent Gateway — Protocol-Aware Kafka Proxy

**Date:** 2026-08-05
**Source files:** wiki/concepts/confluent-cloud-gateway.md
**Scope:** Confluent Gateway (self-managed Kafka-protocol-aware proxy) — architecture, client switchover/DR, migration (KCP), auth swapping, centralized governance, licensing/support lifecycle, FSI considerations
**Claims extracted:** 42

## Summary

The article is technically strong and, on every claim checked directly against live `confluent-docs` (release notes, overview, migration, deploy, security, custom-domains, deploy-overview pages), matches the vendor documentation almost verbatim — including the corrected, non-obvious claim that Client Switchover requires a full gateway restart (confirmed word-for-word against `gateway-migrate.html`, including the restart-impact table). One real gap surfaced: the Core Capabilities auth-swap table omits **mTLS**, which live docs show is not just supported but *mandatory* (identity passthrough cannot be used for mTLS; swapping is required) — this directly undercuts the article's own FSI claim that "mTLS termination at the gateway" is a load-bearing capability. The more serious finding is external to this article: the sibling wiki article `patterns/dr-application-routing.md` was never updated after this article's 2026-08-05 restart-requirement correction, and it still asserts a 5–30s RTO with "no restart required" for the gateway path — a stale, contradicted claim that could mislead an FSI DR sizing conversation. Recommend patching that article as a follow-up.

## Claim Validation

### Summary

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| gw-1 | Self-managed, stateless, Kafka-protocol-aware proxy; rewrites Metadata, swaps auth, custom domain, re-targets clusters without client config change | related articles (dr-application-routing.md) | `overview.html` | — | — | Confirmed |
| gw-2 | Two images (cpc-gateway, confluent-gateway-for-cloud); Docker or CFK; no fully-managed CC SKU | — | `gateway-deploy.html`, `gateway-deploy-overview.html` | — | — | Confirmed |
| gw-3 | Current release 1.3.0 (July 2026) | — | `gateway-release-notes.html` | — | — | Confirmed |
| gw-4 | Switchover requires a gateway restart, not a hot repoint | — | `gateway-migrate.html` | — | — | **Confirmed (verbatim)** |
| gw-5 | Docs direct against switchover for strict-ordering apps (Kafka Streams) | — | `gateway-migrate.html` | kafka-streams-programming | Confirmed | Confirmed |

**Corrections:** none in this subsection.

### Naming and disambiguation

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| gw-6 | CC PrivateLink Gateway = network layer; Confluent Gateway = Kafka protocol layer (Metadata/Produce/Fetch/SaslHandshake) | `private-networking.md` (no overlap/bleed confirmed) | `overview.html` ("Unlike generic proxy solutions that operate at the network layer...") | — | — | Confirmed |
| gw-7 | "One gateway per environment per region" is a PrivateLink/PNI rule, unrelated to this product | `private-networking.md` | — | — | — | Confirmed (wiki-internal, consistent) |

**Corrections:** none.

### What protocol-aware buys you

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| gw-8 | TCP LB can't rewrite Metadata; clients use returned names for subsequent produce/fetch, so DNS aliasing alone is insufficient | `patterns/dr-application-routing.md` (identical framing) | `overview.html` | — | — | Confirmed |
| gw-9 | Gateway swaps SASL mechanisms (SASL/SCRAM client → CC API keys broker-side via secret store) | — | `gateway-security.html` | — | — | Confirmed |

### Architecture — three primitives

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| gw-10 | Streaming Domains: bootstrapServers[] (id + protocol://host:port), TLS material, optional nodeIdRanges | — | `gateway-deploy.html` | — | — | Confirmed (verbatim) |
| gw-11 | Routes: name (≤30 chars, default route-\<index\>), endpoint, brokerIdentificationStrategy, streamingDomain ref, optional fence/security/logNetwork/logFrames | — | `gateway-deploy.html` (name/endpoint/brokerIdentificationStrategy/streamingDomain/security/fence confirmed) | — | — | **Partially Unverifiable** — the ≤30-char name limit and `logNetwork`/`logFrames` fields did not appear in the Docker-path config reference fetched; likely real but scoped to a page not covered (CFK CRD reference) |
| gw-12 | A cutover = repoint a route at a different streaming domain; same mechanism for migration, blue/green, DR | — | `gateway-migrate.html`, `overview.html` | — | — | Confirmed |

**Corrections:**
- Claim gw-11: could not independently verify the 30-character route-name limit or `logNetwork`/`logFrames` route properties against the fetched `docs.confluent.io` pages (they weren't in the Docker Compose config reference). Not disputed — just outside the pages this session fetched. Flagging as a gap rather than an error.

### Broker identification

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| gw-13 | `port` (default): one port per broker, requires nodeIdRanges | — | `gateway-deploy.html` | — | — | Confirmed (verbatim) |
| gw-14 | `host`: SNI-based, `pattern` with `$(nodeId)`, requires wildcard DNS + SNI clients | — | `gateway-deploy.html`, `gateway-custom-domains.html` (wildcard A record example) | — | — | Confirmed |
| gw-15 | `host` recommended over `port` for custom domains / multi-cluster fronting | — | (docs are neutral on this recommendation; it's the article's own guidance) | — | — | Confirmed as reasonable engineering guidance, not a direct vendor claim |

### Core capabilities

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| gw-16 | Network isolation: same-VPC / cross-VPC / external patterns | — | `gateway-custom-domains.html` | — | — | Confirmed (verbatim: private hosted zone / peering+TGW+shared zone / public hosted zone) |
| gw-17 | Auth-swap pairs: SASL/SCRAM→SASL/PLAIN, OIDC→SASL, OAuth→OAuth (1.3.0), NONE | — | `gateway-security.html` | — | — | **Corrected** |
| gw-18 | Fencing: `fence.scope: ALL\|NONE`, default `errorCode: BROKER_NOT_AVAILABLE`; 1.3.0 reorders fencing before auth-swap | — | `gateway-deploy.html`, `gateway-release-notes.html` | — | — | Confirmed (verbatim, including default `NONE` scope and default error message) |
| gw-19 | Centralized governance (1.3.0 EA, Docker-only): 4 policy types, Avro/JSON Schema/Protobuf, per-topic overrides | — | `gateway-release-notes.html`, `overview.html` | — | — | Confirmed (verbatim) |

**Corrections:**
- **Claim gw-17**: The wiki's auth-swap pairs list is incomplete. Live docs (`gateway-security.html`) show client-side swap auth supports **SASL/PLAIN, SASL/SCRAM, SASL/OAUTHBEARER, mTLS, and NONE** — not just "SASL/SCRAM, OIDC, OAuth, NONE." Critically, **mTLS is omitted from the wiki's list entirely**, yet the docs state: *"Identity passthrough cannot be used for mTLS due to TLS termination at Confluent Gateway; currently, authentication swapping is mandatory for mTLS clients."* An explicit `mTLS → SASL/OAUTHBEARER` example is documented. This matters because the article's own FSI Considerations section (claim gw-39/mTLS-termination) leans on mTLS termination at the gateway as a headline FSI capability — the capability table one section earlier should list it as a supported swap pair, and currently doesn't. Recommend adding mTLS to the Core Capabilities auth-swapping row, plus noting that mTLS clients cannot use identity passthrough (swap is mandatory for them).
- Also worth noting for precision: the wiki's "OIDC→SASL" label is Confluent's own marketing-level shorthand (the actual client mechanism is `SASL/OAUTHBEARER` validating OIDC-issued tokens via JWKS) — this is a terminology simplification, not an error, and doesn't need a fix.

### Version history and support lifecycle

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| gw-20 | 1.1.0 (Nov 2025) / 1.2.0 (Mar 2026) / 1.3.0 (Jul 2026) feature sets and EOL/EOS dates | — | `gateway-release-notes.html`, `gateway-deploy-overview.html` | — | — | **Confirmed, exact date-for-date match** |
| gw-21 | Quarterly patch cadence, 3-year support, 6-month patch window, max 2 patches/minor (e.g. 1.1.1/1.1.2, never 1.1.3) | — | `gateway-deploy-overview.html` | — | — | Confirmed (verbatim, including the exact 1.1.1/1.1.2/no-1.1.3 example) |

### Client and protocol compatibility

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| gw-22 | Kafka Client 4.0 base, protocol 3.x/4.0, librdkafka 2.0.0–2.13.0, other clients untested | — | `gateway-deploy-overview.html` | kafka-schema-registry | Out-of-scope (spurious keyword match on "client"/"version"; not a schema-registry claim) | Confirmed (verbatim) |
| gw-23 | `CREATE_CLUSTER_LINKS`/`LIST_CLUSTER_LINKS` don't work through the gateway; CL admin must go direct | — | `gateway-deploy-overview.html` | — | — | Confirmed (verbatim) |

### Deployment, sizing, and licensing

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| gw-24 | Sizing: min 2vCPU/4GB, rec 4vCPU/8GB, 45MB/s per 1Gbps, 10GB disk | `patterns/dr-application-routing.md` **STILL has the superseded 1.5–2x-broker-CPU heuristic** | `gateway-deploy-overview.html` | — | — | Confirmed (verbatim); **wiki cross-doc drift found (see Gaps)** |
| gw-25 | Trial (no key, 4-route cap, community support, PoC) / Enterprise (key required, unlimited routes) | — | `gateway-deploy-overview.html`, `gateway-deploy.html` | — | — | Confirmed; the "key differs by image" sub-claim (CPC Enterprise vs. CC Gateway license) is plausible given the two-image architecture but wasn't independently confirmed on the pages fetched — Unverifiable (scope) |
| gw-26 | CFK: `kind: Gateway` CR, reuses existing CFK license; Docker: Engine 20.10+/Compose v2 | — | `gateway-deploy-overview.html` (Docker reqs confirmed) | — | — | Docker requirement Confirmed; "reuses CFK license" not found on fetched pages (likely on the `operator/current` CFK-specific tree, out of session scope) — Unverifiable (scope) |
| gw-27 | Admin port 9190, `/metrics`, `/livez`, default JVM metrics list | — | `gateway-deploy.html` | — | — | Confirmed (verbatim, exact metric class names) |
| gw-28 | HA: multiple replicas behind LB or multi-endpoint list; failover is connection-level | — | (not directly covered on fetched pages) | — | — | Unverifiable (scope) — plausible, consistent with a stateless proxy, not contradicted |

### Client Switchover

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| gw-29 | Data replication out of scope for gateway; set up via Cluster Linking separately | `patterns/dr-cluster-linking.md` | `gateway-migrate.html` | — | — | Confirmed |
| gw-30 | Documented procedure: edit route, then stop/restart gateway — not hot reconfig | `patterns/dr-application-routing.md` **contradicts this** (says "no restart required," RTO 5–30s) | `gateway-migrate.html` | — | — | **Confirmed, verbatim** against MCP. **Wiki-internal contradiction flagged — see Gaps.** |
| gw-31 | Breaks ordering/consistency across clusters; vendor says don't use for Kafka Streams | `patterns/dr-application-routing.md` (workload-class discriminator section, consistent) | `gateway-migrate.html` | kafka-streams-programming | Confirmed (FSI overlay mandates `exactly_once_v2` for Streams; switchover's ordering break is incompatible with that requirement) | Confirmed |
| gw-32 | Restart-impact table: consumer rebalance/session.timeout.ms, producer idempotence, transaction abort-on-source | — | `gateway-migrate.html` | — | — | **Confirmed, table matches verbatim** (component-by-component wording is near-identical to the live docs table) |
| gw-33 | Two distinct transaction caveats: gateway-layer (open txn doesn't survive swap) vs. CL-layer (no txn support on mirror topics at all) | `concepts/cluster-linking-topology.md` — "transactional atomicity is not preserved on the mirror side" (softer phrasing) | — | — | — | Confirmed, with a wiki phrasing nuance: `cluster-linking-topology.md` says atomicity "is not preserved," this article says CL "does not support transactions... at all." Same substance, worth aligning wording across the two articles for consistency. |

### Use case 1 — client migration (KCP)

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| gw-34 | KCP extended Q2 2026 for gateway-based migration off MSK/self-managed; init/lag-check/execute; seconds producer blocking, ~zero consumer downtime | — | Blog-sourced (`confluent.io/blog/client-migration-kcp-gateway/`) — **out of `confluent-docs` MCP domain scope, could not re-fetch** | — | — | Unverifiable via MCP this session (domain-restricted); trusts the article's own cited blog source |
| gw-35 | KCP limitations: all-at-once cutover, no principal/topic granularity yet, rollback only pre-promotion | — | same as above | — | — | Unverifiable via MCP this session (domain-restricted) |

### Use case 2 — DR switchover

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| gw-36 | Confluent's 60s-RTO POC explicitly not production software; POC scope single-region/Dedicated/public/OAuth2-required | — | Blog-sourced (`confluent.io/blog/kafka-client-failover-poc-confluent-cloud-gateway/`) — domain-restricted | — | — | Unverifiable via MCP this session (domain-restricted); trusts the article's own cited blog source |
| gw-37 | POC caveats: SR failover unsupported, consumer group state manual, CL doesn't support txn on mirror topics | `concepts/cluster-linking-topology.md` corroborates the CL-transaction point | same as above | — | — | Confirmed by wiki corroboration; blog-sourced portion unverifiable via MCP |
| gw-38 | OAuth2 required in POC because Identity Pools are org-scoped in CC (same client ID/secret cross-cluster) | — | same as above | — | — | Unverifiable via MCP this session (domain-restricted) |

### FSI considerations

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|----------------|---------|
| gw-39 | Vendor backing: 3-yr support lifecycle satisfies FSI vendor-contract rule; Envoy/Netty proxies don't | `patterns/dr-application-routing.md` (identical framing: "Confluent Gateway ✅; ORKA = GoodLabs contract") | `gateway-deploy-overview.html` (support lifecycle table) | — | — | Confirmed |
| gw-40 | Enterprise licensing mandatory in production for FSI; Trial 4-route cap disqualifies | — | `gateway-deploy-overview.html` | — | — | Confirmed |
| gw-41 | `logFrames` is a data-exposure risk; leave off outside scoped troubleshooting | — | (not directly covered on fetched pages; `logNetwork`/`logFrames` fields not found in Docker config reference — see gw-11) | — | — | Unverifiable (scope) — sound security guidance regardless |
| gw-42 | 6-month patch window means FSI change-freeze calendars can strand a deployment on an unpatchable minor | — | `gateway-deploy-overview.html` (patch-window mechanics confirmed; the FSI-change-freeze consequence is the article's own — sound — inference) | — | — | Confirmed |

## Premise Challenge

| # | Premise | Assumption | Challenge | Severity |
|---|---------|------------|-----------|----------|
| 1 | A gateway restart is a boundable, RTO-budgetable event | The restart duration is short and predictable enough to fold into a "sub-minute RTO" story | The article (and live docs) never publish a restart-time SLA or benchmark. Every RTO claim in "Use case 2" rests on an unstated number. Without it, "sound sub-minute RTO story if you budget the restart" can't actually be sized. | Critical |
| 2 | The Core Capabilities auth-swap table is a complete list of what mTLS-heavy FSI shops can do at the gateway | mTLS isn't a supported swap pair (only SASL/SCRAM→PLAIN, OIDC→SASL, OAuth→OAuth, NONE are listed) | MCP validation shows this is false — mTLS is supported and, per docs, *mandatory* to swap (no passthrough). The FSI section's "mTLS termination at the gateway" claim is real, but the article's own capability table doesn't support it. Internal inconsistency between two sections of the same document. | Critical (now resolved via this review — see Corrections gw-17) |
| 3 | An OAuth2-required DR posture (per the 60s-RTO POC) sits comfortably inside an FSI shop standardized on the canon default `mTLS + RBAC` | OAuth2-only auth in the POC doesn't need reconciling against the FSI security default | Base+FSI canon (`security.auth_mechanism: mTLS + RBAC`, ADR-006 "never username/password in FSI") doesn't explicitly bless OAuth2-as-primary. The article doesn't address whether an FSI shop needs mTLS-terminated auth-swap-to-OAuth2 (which the gateway supports, per gw-17's correction) to reconcile this, or whether native OAuth2 suffices under FSI review. | Moderate |
| 4 | Centralized governance (schema/encryption enforcement) is a meaningful FSI capability to plan around today | The feature is presented alongside CFK/production guidance as if broadly usable | It's Early Access and **Docker-only** — the one feature FSI would most want (governance enforcement) is currently unavailable on the CFK path the article elsewhere recommends for production. The article does flag this with a warning callout, but doesn't connect it explicitly to the FSI section's silence on governance. | Moderate |
| 5 | Canon's `6 × peak MB/s` partition-count formula applies unchanged behind a gateway-fronted topic | The parse-and-re-encode hop doesn't change effective per-partition throughput math | The sizing table gives *instance-level* gateway throughput (45MB/s per 1Gbps) but never ties it back to partition-count capacity planning for the topics behind it. Not wrong, just an unaddressed seam between gateway sizing and topic sizing. | Minor |

## Canon Compliance

| Area | Status | Notes |
|------|--------|-------|
| `security.auth_mechanism` (mTLS + RBAC) | **Partial** | The underlying product supports mTLS-terminated auth swapping (confirmed via MCP) so the *capability* complies with canon, but the article's own Core Capabilities table omits mTLS as a swap pair (gw-17 Correction) — a documentation gap, not a product gap. |
| `security.service_account_scope` (per-application) | Compliant | Confluent's own security best practices (fetched via MCP) explicitly recommend one Gateway-to-Broker SASL credential per client, matching canon; the article doesn't cite this specific guidance but doesn't contradict it either. |
| `security.audit_log` (all production clusters) | Compliant | Article correctly flags `logFrames` as a data-exposure risk and recommends SIEM forwarding. |
| `schema_registry.format` / `compatibility_mode` (Avro/Protobuf, tier-derived/FULL) | Compliant | Centralized governance's EA/Docker-only status is correctly flagged as not-yet-safe for FSI tooling — appropriately cautious, doesn't recommend bypassing native Schema Registry governance. |
| `cluster_linking.preferred_over` / `auto_create_mirror_topics` | Compliant (N/A for auto-create) | Article correctly treats CL as the replication substrate underneath gateway DR and correctly notes CL admin APIs don't traverse the gateway. |
| Producer canon (`acks=all`, `enable_idempotence`) | Compliant | Restart-impact mitigation table explicitly recommends `enable.idempotence=true` and `isolation.level=read_committed`, matching canon producer/consumer defaults exactly. |
| `topic_design.naming_convention` | N/A | Gateway routing/streaming-domain naming is a different namespace than Kafka topic naming; not addressed and not expected to be. |
| FSI `mainframe_integration`, LinuxONE keys | N/A | Out of scope for this product. |

## Gaps

1. **Cross-document drift (highest priority):** `patterns/dr-application-routing.md` was compiled alongside this article on 2026-05-18 and has not been updated to reflect this article's 2026-08-05 correction that switchover requires a gateway restart. It currently states an RTO floor of "5–30s (reconnect only)," "Application restart: Not required. This is the load-bearing benefit," and a decision-matrix row claiming "No" for application restart required — all now contradicted by the MCP-confirmed restart requirement. It also still carries the superseded "1.5–2× broker CPU" sizing heuristic that this article explicitly says it supersedes. **Recommend a follow-up `/wiki:validate` or manual patch pass on `dr-application-routing.md`.**
2. **KCP and 60-second-RTO POC claims (gw-34, 35, 36, 38)** are sourced from Confluent blog posts, which are outside the `confluent-docs` MCP's allowed domain (`docs.confluent.io` only). Could not independently re-verify this session; they rest on the article's own cited sources.
3. **Route-level fields not found in the fetched config reference:** the ≤30-character route-name limit and the `logNetwork`/`logFrames` route properties (gw-11, gw-41) weren't present in the Docker Compose config reference fetched. They may be documented on the CFK-specific (`operator/current`) tree, which wasn't fetched this session.
4. **No wiki article covers gateway observability wiring into Grafana** (the `:9190/metrics` endpoint), despite `observability-metrics-mapping.md` being linked in this article's "Related" section as if it did. Auto-stubbed to `wiki/_queue.md` (`gateway-observability-grafana-wiring`).
5. **No wiki article covers gateway-level centralized governance vs. native Schema Registry governance** — a genuinely new topic as of 1.3.0 EA. Auto-stubbed to `wiki/_queue.md` (`gateway-centralized-governance-vs-schema-registry`).

## Recommendations

1. **Fix `patterns/dr-application-routing.md`** to match this article's corrected restart requirement: update the RTO floor (no longer "5–30s, no restart"), the "Application restart required" decision-matrix cell (currently "No"), and the superseded CPU-sizing heuristic. This is the single highest-value fix from this review — an FSI DR sizing conversation using the current `dr-application-routing.md` would under-budget RTO.
2. **Add mTLS to the Core Capabilities auth-swapping row** in this article, and note that identity passthrough is unavailable for mTLS clients (swap is mandatory). This closes the internal gap between the capability table and the FSI section's mTLS-termination claim.
3. **Align the Cluster Linking transaction-support wording** between this article ("does not support transactions on mirror topics at all") and `cluster-linking-topology.md` ("cross-topic atomicity is not preserved") — same substance, different emphasis; pick one phrasing and cross-link.
4. **Publish a restart-duration figure or load-test methodology** for Client Switchover if one exists internally — without it, the "sub-minute DR RTO" framing in Use Case 2 can't actually be validated end-to-end (Premise Challenge #1).
5. Consider re-fetching the two cited Confluent blog posts (KCP migration, 60s-RTO POC) through a general web fetch (outside `confluent-docs` MCP's `docs.confluent.io` restriction) in a future validation pass, since they underpin several DR/migration claims that couldn't be re-verified this session.

---
Canon stack: base + industry/fsi | Hash: 437a88b8eb364e19 | MANIFEST: unavailable (raw/repos/fsi-dsp/MANIFEST.yaml not present in this checkout) | Floor: claude-sonnet-5 | Generated: 2026-08-05T20:51:24Z
