---
title: Wiki Validation Report — 2026-05-14
date: 2026-05-14
scope: 5 medium/⚠️-flagged articles + drift-check pass on high-confidence articles
---

# Wiki Validation Report — 2026-05-14

## Scope

Extended `/wiki:validate` invocation targeting the 5 articles still at
`confidence: medium` with inline `⚠️ unverified` markers from the recent
`/wiki:ingest` run:

- `wiki/concepts/cc-cluster-tiers.md`
- `wiki/concepts/network-connectivity-by-tier.md`
- `wiki/concepts/schema-registry-best-practices.md`
- `wiki/patterns/fsi-exactly-once.md`
- `wiki/synthesis/confluent-gotchas-top-20.md`

Goal: clear every `⚠️ unverified` marker by either (a) confirming the claim
against `confluent-docs` MCP, (b) correcting the claim inline, or (c) keeping
the marker if MCP could not resolve it.

## Claims validated

10 ⚠️ inline markers checked. MCP sources queried:

- `cloud/current/clusters/cluster-types.md` — per-tier limits, feature matrix, CL matrix, SLA matrix
- `cloud/current/networking/overview.md` — networking-mode-by-tier, PNI/PrivateLink/peering/TGW
- `cloud/current/connectors/bring-your-connector/custom-connector-fands.md` — Custom Connectors on private networking
- `cloud/current/multi-cloud/cluster-linking/index.md` — Cluster Linking supported source/destination matrix
- `cloud/current/stream-governance/index.md` + `stream-governance/packages.html` — Essentials/Advanced split
- `cloud/current/flink/overview.md` — CC Flink runtime details

## Drift found & corrected inline

### `wiki/concepts/cc-cluster-tiers.md` — 4 markers, all resolved → upgraded to `confidence: high`

| # | Original claim | MCP finding | Action |
|---|---|---|---|
| 1 | "Basic — no Cluster Linking *source*" | CC docs: Basic **does support** being a CL source (just not a destination) | **Corrected** — tier matrix + decision rule both rewritten |
| 2 | "BYOK → Dedicated or Enterprise only" | Confirmed (cluster-types feature matrix) | Kept; clarified ordering |
| 3 | "Custom Connectors historically not available on PrivateLink clusters" | CC docs: **supported on Dedicated and on Enterprise AWS via PrivateLink egress access points** (dedicated, newly-provisioned egress gateway required) | **Corrected** — replaced with the documented supported configurations |
| 4 | "Per-CKU numbers change; use Confluent's current sizing guidance" | Per-CKU baseline now captured inline (60 MBps ingress / 180 MBps egress / 4,500 partitions / 18,000 connections / 15,000 req/s) | **Corrected** — added numbers + kept advice to re-check |
| 5 | "Freight ⚠️ — ~10× cheaper $/GB" | Freight is confirmed cheaper, but the ~10× ratio is marketing positioning, not a docs-table number. Confirmed Freight has no idempotent producer / no transactions / no EOS / no key-based compaction | **Corrected** — removed the bare ⚠️, added the EOS/transaction limitations explicitly |

Frontmatter: `confidence: medium` → `confidence: high`; `last_validated: 2026-05-14`.

### `wiki/concepts/network-connectivity-by-tier.md` — 2 markers, all resolved → upgraded to `confidence: high`

| # | Original claim | MCP finding | Action |
|---|---|---|---|
| 1 | "Enterprise clusters — PrivateLink/PSC only. No peering, no Transit Gateway." | True for peering/TGW, but missed **AWS PNI** as an Enterprise option (and the 10-eCKU PrivateLink cap vs. 32-eCKU PNI cap) | **Corrected** — added PNI row to the connectivity table and to the key-constraints section |
| 2 | "Custom Connectors historically aren't available on PrivateLink clusters" | Same correction as cc-cluster-tiers — Custom Connectors supported on Dedicated and on Enterprise AWS via PrivateLink egress access points | **Corrected** inline |

Also added: Freight on AWS uses PNI only (no PrivateLink, no peering, no TGW) — this was an implicit gap in the table.

Frontmatter: `confidence: medium` → `confidence: high`; `last_validated: 2026-05-14`.

### `wiki/concepts/schema-registry-best-practices.md` — 1 marker, resolved → upgraded to `confidence: high`

| # | Original claim | MCP finding | Action |
|---|---|---|---|
| 1 | "Advanced adds Stream Lineage, Stream Catalog, more schemas, Data Contracts, Schema Linking. ⚠️ exact package feature splits change" | All five features confirmed present in `stream-governance/packages.html`; Essentials/Advanced split is the current shape | **Corrected** — removed ⚠️, kept softer "re-check live package matrix for numerical caps" hedge |

Frontmatter: `confidence: medium` → `confidence: high`; `last_validated: 2026-05-14`.

### `wiki/patterns/fsi-exactly-once.md` — 2 markers, neither resolvable → stays `confidence: medium`

| # | Original claim | MCP finding | Action |
|---|---|---|---|
| 1 | "Confluent Cloud Flink transaction commit interval is not documented as user-configurable" | CC Flink doc (`cloud/current/flink/overview.md`) describes serverless / Autopilot but does not document a user-tunable transaction commit interval. Unverifiable from public docs. | **Kept** ⚠️ marker — claim still accurate as stated ("not documented as user-configurable") |
| 2 | "IBM MQ Source Connector exact EOS configuration properties and version requirements" | Confluent docs index does not surface MQ Source Connector EOS-specific config; needs the connector-specific reference doc which the llms.txt index does not link directly. | **Kept** ⚠️ marker |

Frontmatter: `confidence: medium` (no change); `last_validated: 2026-04-28` → `2026-05-14`.

### `wiki/synthesis/confluent-gotchas-top-20.md` — 1 marker, partially resolved → stays `confidence: medium`

| # | Original claim | MCP finding | Action |
|---|---|---|---|
| 1 | "Freight ~10× cheaper throughput ⚠️ exact cost ratio and Freight feature surface change" | Freight feature surface **resolved** — no idempotent producer, no transactions, no EOS, no key-based compaction. ~10× cost ratio remains a marketing positioning number, not a docs-table number. | **Partially corrected** — feature limitations now stated explicitly; ⚠️ retained but tightened to call out the ratio specifically, with guidance to use the pricing calculator instead |

Frontmatter: `confidence: medium` (no change); `last_validated: 2026-05-14`.

## Articles upgraded medium → high

1. `wiki/concepts/cc-cluster-tiers.md`
2. `wiki/concepts/network-connectivity-by-tier.md`
3. `wiki/concepts/schema-registry-best-practices.md`

## Articles still at medium and why

1. `wiki/patterns/fsi-exactly-once.md` — 2 unverifiable claims (CC Flink commit interval tunability; IBM MQ Source Connector EOS specifics) that public docs don't resolve. Both remain inline-marked.
2. `wiki/synthesis/confluent-gotchas-top-20.md` — 1 unverifiable claim (Freight ~10× cost ratio); ⚠️ kept on the ratio specifically.

## Drift-check on high-confidence articles

**Deferred** due to validation-budget limits this session. The 11 articles at
`confidence: high` (per `wiki/_index.md`) were not individually drift-checked
against MCP this run. Recommend a follow-up `/wiki:validate` pass focused
on:

- `concepts/cluster-linking-topology.md` — re-verify "Basic supports CL source" alignment now that this is fixed in `cc-cluster-tiers.md`
- `patterns/dr-cluster-linking.md` — same CL-source assumption
- `concepts/exactly-once-semantics.md` — cross-reference with `fsi-exactly-once.md`'s remaining unverified claims

No new drift items were added to `wiki/_queue.md` this run — corrections were applied inline rather than queued.

## Overall wiki health

After this pass:
- Articles at `confidence: high`: 11 → 14
- Articles at `confidence: medium`: 5 → 2
- ⚠️ inline markers across the wiki: 10 → 3

The remaining 3 markers are well-scoped and properly hedged (Flink commit
interval tunability, MQ connector EOS specifics, Freight cost ratio); they
represent genuine gaps in public Confluent documentation, not wiki drift.

## Follow-up drift-check on Cluster Linking articles (2026-05-14)

Targeted second pass on the two articles the earlier section deferred,
following the upstream correction that Basic CC clusters **can** be Cluster
Linking sources (just not destinations, and not the source of
source-initiated or bidirectional links).

MCP source consulted: `cloud/current/multi-cloud/cluster-linking/index.html`
(authoritative "Supported cluster types" matrix) — cross-checked against
`cloud/current/clusters/cluster-types.html` for the per-tier capability
table.

### Authoritative finding (from CL overview's Supported cluster types matrix)

- **Sources:** Dedicated (public/private), Enterprise (public/private),
  Standard, Basic, Freight on AWS (private networking), external Apache
  Kafka 3.0+ / CP 7.0+ (public IPs), Kafka 3.0+ without public endpoints
  (with peering/VNet to Dedicated), CP 7.1+ behind firewall (source-initiated).
- **Destinations:** Dedicated *or* Enterprise (with networking caveats);
  also Freight on AWS with private networking. Dedicated *legacy* clusters
  are not supported as destinations.
- **Caveat:** "Basic and Standard clusters can be the source of
  destination-initiated links, but cannot be used as the source of
  source-initiated links." → bidirectional mode (which requires
  source-initiated capability) therefore excludes Basic/Standard.

### `wiki/concepts/cluster-linking-topology.md` — drift found and corrected → stays `confidence: high`

| # | Original claim | MCP finding | Action |
|---|---|---|---|
| 1 | "On Confluent Cloud, bidirectional mode is not supported on Basic or Standard clusters." | True, but **incomplete**: docs explicitly say Basic/Standard *can* be the source of destination-initiated one-way links — just not source-initiated/bidirectional. | **Clarified** — added a follow-up sentence stating that Basic/Standard can be the source of a destination-initiated egress link to a Dedicated/Enterprise destination |
| 2 | Cloud "Destination cluster: Dedicated or Enterprise only" | Mostly correct, but missed (a) Freight on AWS with private networking as a destination and (b) Dedicated *legacy* clusters not being supported as destinations | **Corrected** — both qualifiers added inline |
| 3 | Cloud "Source cluster: Basic, Standard, Dedicated, Enterprise, or any Kafka 3.0+" | The Basic-as-source claim is **already correct** (this was the upstream correction). Row was missing Freight on AWS private-networking sources and the CP 7.0+/7.1+ split. | **Corrected** — Freight and CP version split added |
| 4 | Cloud "Bidirectional mode: Not on Basic/Standard" | Confirmed but tied implicitly to source-initiated requirement — row renamed "Bidirectional / source-initiated" and source-initiated CP 7.1+ floor noted alongside bidirectional CP 7.5+ | **Corrected** — clarified the dependency |

No earlier claim was *wrong*; the corrections are precision improvements
to surface the destination-initiated-only carve-out for Basic/Standard and
the Freight-on-AWS-with-private-networking surface. Frontmatter:
`confidence: medium` → `confidence: high` (now matches its actual claim
hygiene); `last_validated: 2026-04-28` → `2026-05-14`; `last_updated`
bumped to `2026-05-14`.

### `wiki/patterns/dr-cluster-linking.md` — no drift → stays `confidence: high`

All verifiable CL claims pass:

- East/West are implicitly Dedicated (or Enterprise) — pattern never
  claims Basic/Standard support, so the upstream correction does not
  affect this article.
- Bidirectional CL for failback semantics (`truncate-and-restore`,
  `reverse-and-start`) — confirmed.
- `mirror failover` (no lag check, irreversible) vs. `mirror promote`
  (zero-lag gate, planned migration) — confirmed.
- "For RPO=0 requirements, use MRC on Confluent Platform instead" —
  confirmed.
- Failback's destructive truncate-and-restore caveat — confirmed.

Frontmatter: `confidence: high` unchanged; `last_validated: 2026-04-28`
→ `2026-05-14`; `last_updated` unchanged (no body changes).

### Summary of this follow-up

- 2 articles drift-checked.
- 1 article patched inline (cluster-linking-topology.md) with 4 precision
  corrections; promoted medium → high.
- 1 article confirmed clean (dr-cluster-linking.md).
- No ⚠️ markers introduced; no `_queue.md` entries needed.
- The wiki's Cluster Linking tier story is now internally consistent
  across `cc-cluster-tiers.md`, `network-connectivity-by-tier.md`,
  `cluster-linking-topology.md`, and `dr-cluster-linking.md`.
