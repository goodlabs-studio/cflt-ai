---
title: Wiki Validation — Queues for Kafka (Share Groups)
date: 2026-06-09
scope: wiki/concepts/queues-for-kafka-share-groups.md
articles_checked: 1
claims_validated: 12
drift_found: 3
defaults_filled: 5
stubs_expandable: 0
---

# Wiki Validation — Queues for Kafka (Share Groups)

## Scope

Single-article validation of `wiki/concepts/queues-for-kafka-share-groups.md`
(`confidence: medium`), invoked specifically to resolve the `⚠️ unverified`
markers the article carried from authoring time — when the dedicated Confluent
share-groups docs were not yet resolvable via MCP. They now are.

- **Preload bundle:** none (single-article scope, Step 1.5 skipped)
- **Skills consulted:** none (`tools/skill_routing.py` returned no slug for the share-groups topic)
- **Skill-MCP conflicts:** 0

## Sources

Validated via `confluent-docs` MCP + targeted web search:
- `platform/current/clients/share-consumers.html` (Share Consumers for CP)
- `platform/current/installation/configuration/broker-configs.html` (broker config reference — authoritative defaults)
- `platform/current/installation/docker/operations/kafka-queues-docker.html` (enablement procedure)
- Apache Kafka 4.2.0 release announcement (Feb 2026); Confluent "Kafka Queue Semantics Now GA" blog

## Claims validated (12)

### Confirmed as stated (7)
| Claim | MCP finding |
|-------|-------------|
| `KafkaShareConsumer` is the share-group client | Confirmed (CP share-consumers page) |
| `share.acknowledgement.mode` — `implicit` (default) / `explicit` | Confirmed: type string, default `implicit`, valid `[implicit, explicit]` |
| `group.share.record.lock.duration.ms` (name) | Confirmed broker config |
| `group.share.delivery.count.limit` (name) | Confirmed broker config |
| `group.share.session.timeout.ms` / `group.share.heartbeat.interval.ms` (names) | Confirmed broker configs |
| `group.share.max.size` = max members in a share group | Confirmed (purpose exact) |
| Delivery-count → archive (poison terminus); per-record Accept/Release/Reject | Confirmed concept |
| `kafka-share-groups.sh` tooling | Confirmed (CP share-consumers page) |

### Defaults filled (were `⚠️ unverified`) (5)
| Property | Confirmed default | Valid range |
|----------|-------------------|-------------|
| `group.share.record.lock.duration.ms` | **30000 (30s)** | [1000, 3600000] |
| `group.share.delivery.count.limit` | **5** | [2, 10] |
| `group.share.session.timeout.ms` | **45000 (45s)** | — |
| `group.share.heartbeat.interval.ms` | **5000 (5s)** | — |
| `group.share.max.size` | **200** | [1, 1000] |

## Drift found (3)

1. **`group.share.enable` does not exist.** The article lists it as the broker
   "master switch." There is no such property in the CP broker-config reference.
   Share groups are gated by the **`share.version=1`** feature flag, enabled with
   `kafka-features.sh ... upgrade --feature share.version=1` (Kafka 4.1+). On 4.0
   Early Access the gate was `group.coordinator.rebalance.protocols=classic,consumer,share`
   + `unstable.api.versions.enable=true`. → **correct the config table row.**

2. **Maturity is stale.** Article says "Early Access / Preview in Apache Kafka
   4.0, with GA targeted for a later 4.x release." Actual timeline (as of
   2026-06): EA in 4.0 → **Preview in 4.1** → **production-ready / GA in Apache
   Kafka 4.2.0 (Feb 2026)**. KIP-932 is **GA on Confluent Cloud**; Confluent
   Platform support ships alongside the 4.2 release train. → **rewrite Maturity section.**

3. **Missing `RENEW` acknowledgement type.** Article enumerates Accept / Release
   / Reject. Kafka 4.2 GA added a fourth ack type, **RENEW** (extend the
   acquisition lock for longer processing). → **add to the "How delivery works" list.**

## Advisory (not auto-fixed)

- The article attributes durable state persistence to the "share-partition
  leader." Docs distinguish roles: the **share-partition leader** manages
  in-flight record locks (SPSO/SPEO); the **share coordinator** persists durable
  share-group state to the internal state topic (configured via
  `KAFKA_SHARE_COORDINATOR_STATE_TOPIC_*`). The literal topic name
  `__share_group_state` was not confirmed verbatim on the fetched pages — keep
  the article's hedged "commonly" phrasing or attribute persistence to the share
  coordinator. Low-severity nuance.

## Health assessment

The article was well-built and honestly flagged — every drift was already
behind an `⚠️ unverified` marker. With the 3 corrections + 5 defaults applied
and the unverified markers cleared, all verifiable claims are MCP-validated and
the article qualifies for **`confidence: high`**. The single change in posture is
that share groups are no longer "preview" — they are GA (CC) / shipping (CP),
which strengthens the FSI applicability framing rather than weakening it.

---

## Re-validation pass (independent re-check) — 2026-06-09

Second `/wiki:validate` invocation on the same article, same day. Independent
re-verification against `confluent-docs` MCP (no dedicated share-groups page is
indexed in the current `llms.txt`; the CP `consumer.md` page does not cover
KIP-932) with web-search fallback to the authoritative KIP-932 / Apache Kafka
4.2.0 sources. **Skills consulted:** none. **Skill-MCP conflicts:** 0.
**Preload bundle:** none (single-article). **Source-staleness:** 0 STALE/MISSING/AMBIGUOUS.

**Result: no new drift.** Every correction from the first pass independently re-confirmed:

| Claim | Independent finding |
|-------|---------------------|
| `RENEW` ack type added at 4.2 GA | Confirmed. `AcknowledgeType` enum is `0:Gap, 1:Accept, 2:Release, 3:Reject, 4:Renew`; RENEW landed via **KIP-1222** in 4.2. |
| GA in Apache Kafka 4.2.0 | Confirmed — release announced **2026-02-17**; KIP-932 production-ready. |
| EA 4.0 → Preview 4.1 → GA 4.2 | Confirmed against the KIP-932 EA/Preview release-notes pages + 4.2 announcement. |
| `share.version=1` enablement via `kafka-features.sh` | Confirmed. |
| `group.share.*` defaults (30000 / 5 / 45000 / 5000 / 200) + `share.acknowledgement.mode=implicit` | Consistent with KIP-932; no change. |

**New (non-drift) findings for the queue:**

1. **Expansion — native share-group lag metrics (4.2 GA).** The article's
   Monitoring bullet still carries the by-design `⚠️ unverified` on share-group
   *metric identities* and frames lag as not-applicable to share groups. Kafka
   4.2 GA shipped **comprehensive native share-group lag metrics**. The "lag does
   not describe a share group" framing is now too strong — native share-group
   lag metrics exist and are the right signal to resolve that marker against the
   observability mapping. → queued under *Articles to Expand*.

2. **Advisory (precision nuance, not drift).** `RENEW` is available only in
   **explicit** acknowledgement mode (KIP-1222: "…in share consumer explicit
   mode"). The article lists RENEW unconditionally under "How delivery works."
   A one-clause qualifier ("explicit ack mode") would make it exact. Low
   severity — offered as an optional refinement, not logged as drift.

Also observed in 4.2 but out of article scope: **KIP-1206 `ShareAcquireMode`**
(`batch_optimized` soft-limit vs `record_limit` strict enforcement of fetched
record counts). Not currently a wiki claim; noted for future expansion only.

**Posture unchanged:** article remains accurate at `confidence: high`. No
auto-fix required.
