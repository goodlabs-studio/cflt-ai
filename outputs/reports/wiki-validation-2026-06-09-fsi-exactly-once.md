# Wiki Validation Report — fsi-exactly-once

**Date:** 2026-06-09
**Scope:** `wiki/patterns/fsi-exactly-once.md` (single article)
**Preload bundle:** none (single-article scope, under the 10-article threshold)

## Summary

| Metric | Count |
|--------|-------|
| Articles checked | 1 |
| Verifiable claims validated | 12 |
| Drift instances found | 0 |
| Stubs with expansion potential | 0 (article is `confidence: medium`, fully written) |
| Skill–MCP conflicts | 0 |
| Source-staleness (STALE-SOURCE-1) | 0 (article has `sources: []` — no `fsi-dsp://` URIs) |
| Missing/ambiguous sources | 0 |

**Skills consulted:** `kafka-streams-programming`

## Claims Validated

### Confirmed via `confluent-docs` (IBM MQ Source Connector overview)

The mainframe-bridge EOS section (lines 286–299) was checked against the live
[IBM MQ Source Connector for Confluent Platform](https://docs.confluent.io/kafka-connectors/ibmmq-source/current/overview.html)
overview. All six EOS preconditions confirmed verbatim:

1. `exactly.once.source.support=enabled` on all Connect workers — confirmed (KIP-618 worker setting)
2. Distributed mode required; standalone cannot provide EOS — confirmed
3. Connect worker principal requires exactly-once-source ACLs — confirmed
4. `state.topic.name` set at first create; changing it later reintroduces duplicates — confirmed
5. Single task only — EOS mode does not support `tasks.max > 1` / multiple receiver threads — confirmed
6. Downstream consumers set `isolation.level=read_committed` — confirmed

Also confirmed:
- Transactional producer used for Kafka writes (extends EOS from MQ boundary) — confirmed
- 11.x line does not support at-least-once and is no longer supported; 12.x+ required — confirmed
- Priority-queue caveat: MQ may deliver out of order, EOS cannot be guaranteed, connector may fail — confirmed verbatim

### Confirmed via `confluent-docs` (producer- and broker-config references)

Second pass (2026-06-09, later run) — config defaults re-fetched directly from the live
config references, closing the gap the earlier report flagged for promotion:

- `transaction.timeout.ms` producer default — **confirmed**: producer-configs reference reads
  "Default: 60000 (1 minute)"
- `transaction.max.timeout.ms` broker default — **confirmed**: broker-configs reference reads
  "Default: 900000 (15 minutes)"
- `enable.idempotence=true` requires `max.in.flight.requests.per.connection ≤ 5`, `retries>0`,
  `acks=all` — **confirmed** verbatim in the producer-configs idempotence note; article's
  `max.in.flight=5` is the maximum allowable value
- `processing.guarantee=exactly_once_v2` "requires Kafka 2.5+" — consistent with KIP-447
  (EOS v2 shipped in Apache Kafka 2.5). Not drift.

### Skill consultation (advisory)

`kafka-streams-programming` routed on the EOS / `exactly_once_v2` claims and was
activated. Its FSI overlay block independently sets `exactly_once_v2` as the
mandatory FSI default for any compliance-tier or reconciliation workload
(rationale: SOX 302/404 material misstatement). **Agrees with MCP** — no conflict
logged.

### Unverifiable (already marked inline)

- Confluent Cloud for Apache Flink transaction commit interval (~1 min) is not
  documented as user-configurable. Already carries an inline `⚠️ unverified`
  marker (line 185). Per quality-standards, a single unverifiable claim does not
  downgrade confidence.

## Health Assessment

Article is accurate and current. The high-risk, version-specific surface (IBM MQ
Source Connector EOS preconditions and 11.x→12.x support boundary) was
fact-checked directly against live `confluent-docs` and is correct in every
particular. `last_validated` bumped to 2026-06-09.

**Promotion to `high` now warranted.** The earlier run held at `medium` pending a
fresh config-reference fetch; that fetch is now done — `transaction.timeout.ms`
(60000) and `transaction.max.timeout.ms` (900000) are both confirmed directly from
`confluent-docs`. The only remaining unverifiable claim (CC Flink commit interval)
is correctly fenced with an inline `⚠️ unverified` marker, and per quality-standards
a single unverifiable claim does not downgrade confidence. All MCP-routable
verifiable claims (config defaults, version requirements, MQ connector EOS feature
availability) are confirmed with zero drift — the `confidence: high` bar in
`article-format.md` is met. **Recommend promoting `medium → high` and setting
`last_validated: 2026-06-09`.**

## Auto-fix

No drift found — nothing to fix.
