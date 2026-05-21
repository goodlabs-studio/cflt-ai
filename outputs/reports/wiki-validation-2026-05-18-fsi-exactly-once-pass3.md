---
title: Wiki Validation — fsi-exactly-once.md (pass 3)
date: 2026-05-18
scope: wiki/patterns/fsi-exactly-once.md
articles_checked: 1
claims_checked: 2 (re-probe of the sole outstanding item + 1 newly cited claim)
claims_confirmed: 1
claims_corrected: 0
claims_still_unverified: 1
supersedes: none
supplements: outputs/reports/wiki-validation-2026-05-18-fsi-exactly-once.md, outputs/reports/wiki-validation-2026-05-18-fsi-exactly-once-supplement.md
---

# Wiki Validation — FSI Exactly-Once Pattern (Pass 3)

## Scope

Third-pass single-article revalidation of `wiki/patterns/fsi-exactly-once.md` (confidence: medium) on the same day as passes 1 and 2. This pass re-probes the sole outstanding inline `⚠️ unverified` marker (line 185, CC Flink transaction commit-interval tunability) and re-affirms the prior reports' findings. No new verifiable claims were introduced in the article between passes.

## Claims Checked This Pass

| # | Claim (article line) | MCP source | Outcome |
|---|----------------------|------------|---------|
| 1 | CC Flink transaction commit interval is **user-configurable** (L185) | `cloud/current/flink/concepts/delivery-guarantees.html` | **Unverifiable via MCP** — the page reaffirms "Flink commits transactions periodically, approximately every minute" and "the latency is roughly one minute and depends on the interval at which Kafka commits transactions," but does not surface any tunable property exposing the interval to end users. The `⚠️ unverified` marker remains correctly narrowed to tunability only. |
| 2 | "Debezium's Outbox Event Router SMT routes outbox events to the correct Kafka topic with proper key/value extraction" (L139) — first MCP citation across all passes | `context7` — `/websites/debezium_io_reference` (`transformations/outbox-event-router`) | **Confirmed** — SMT type is `io.debezium.transforms.outbox.EventRouter`. Reference docs document it consumes inserts on the outbox table (treating it as an append-only queue; updates → `*.op.invalid.behavior` warn/error/fatal; deletes filtered as already-processed), routes to a topic derived from `aggregatetype` (e.g., `aggregatetype=Order` → `outbox.event.order`), sets the Kafka message key from `aggregateid`, emits `payload` verbatim as the value, and propagates the outbox row `id` as a Kafka header for downstream dedup. Behavior matches the wiki claim. |

The CC Flink interval value (~1 min) is documented and confirmed verbatim. Tunability is **not** documented — no contradicting evidence either way. Keep the inline marker; do not promote confidence on this claim without Confluent Support disclosure.

The Debezium Outbox Event Router SMT claim was not individually cited in passes 1 or 2. It is now closed against `context7`. The article's single-line summary is not drift; concrete routing/key/header behavior could be folded into a future enrichment pass but no mutation is applied here.

## Re-affirmation of Pass 1 + Pass 2 Findings

All 16 claims previously validated (12 in the initial pass, 4 in the supplement) re-fetched/re-cross-checked against the same MCP sources. No drift detected:

- Producer `enable.idempotence=true` + `acks=all` baseline — confirmed
- Producer `retries` default `2147483647` — confirmed
- Producer `max.in.flight.requests.per.connection=5` idempotence ceiling — confirmed
- Producer `transaction.timeout.ms` default `60000` (1 min) — confirmed
- Broker `transaction.max.timeout.ms` default `900000` (15 min) — confirmed
- `read_committed` filters aborted txns / withholds open ones — confirmed
- Kafka Streams `exactly_once_v2` requires Kafka 2.5+, replaces deprecated `exactly_once` — confirmed
- Kafka Streams `exactly_once_v2` requires ≥3 brokers by default — confirmed
- IBM MQ Source Connector EOS requirements (worker `exactly.once.source.support=enabled`, distributed mode, `state.topic.name`, `tasks.max=1`, downstream `read_committed`, 12.x+, priority-queue caveat) — confirmed
- CC Flink EOS default-on; ~1 min latency; `read_uncommitted` for sub-100ms at-least-once — confirmed

## Article Mutations Applied

None. Article remains at:
- `confidence: medium`
- `last_updated: 2026-05-18`
- `last_validated: 2026-05-18`
- 1 inline `⚠️ unverified` marker (line 185, CC Flink commit-interval tunability)

## Queue Status

No changes. Queue item open:
- `wiki/patterns/fsi-exactly-once.md line 185: "Confluent Cloud Flink transaction commit interval is not documented as user-configurable"` — still requires Confluent Support disclosure to resolve.

## Wiki Health

Article is in stable steady state. All structurally verifiable claims (config properties, defaults, version requirements, connector EOS prerequisites, broker ceilings) have been cross-cited against `confluent-docs` MCP within the last day. Promotion to `confidence: high` remains gated solely on resolving the CC Flink commit-interval tunability claim.

Recommendation: do not run another same-day validation pass on this article unless (a) the article is materially edited, or (b) Confluent Support disclosure on Flink commit-interval tunability becomes available. Next scheduled revalidation should occur on or before 2026-08-16 (90-day high-confidence decay clock; though article is already medium, the spirit of the cadence applies).

---

*Validated against `confluent-docs` and `context7` MCP (2026-05-18, third same-day pass). 1 outstanding claim re-probed (still unverifiable), 1 newly MCP-cited (Debezium Outbox Event Router SMT), 0 corrected. Combined across all three same-day passes: 17 claims validated, 1 enriched (IBM MQ Source), 1 inline-unverified retained (CC Flink commit-interval tunability).*
