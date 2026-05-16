---
title: exactly_once_v2 on WarpStream — Throughput Cost from Idempotent-Producer Throttling
tags: [trip-wire, warpstream, competitive-context, exactly-once, eos, confluent-agent-skills]
sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/warpstream-optimization.md]
related: [concepts/exactly-once-semantics, concepts/warpstream-config-overrides, concepts/kafka-streams-production-hardening]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/kafka-streams-programming/references/warpstream-optimization.md
---

# exactly_once_v2 on WarpStream — Throughput Cost from Idempotent-Producer Throttling

## Summary

Setting `processing.guarantee=exactly_once_v2` in Kafka Streams enables idempotent producers internally, which caps `max.in.flight.requests.per.connection ≤ 5`. On classic Kafka this is a modest cost; on WarpStream's S3-backed storage tier the in-flight cap interacts with per-partition pull cadence to produce a meaningful throughput hit (WarpStream's docs flag idempotent and EOS producers as a known throughput tradeoff, and the Java client may see retriable `KAFKA_STORAGE_ERROR` errors due to frequent partition ownership shifts between agents). Quantify before enabling EOS on high-throughput WarpStream pipelines.

> **FSI context:** WarpStream is not Confluent. FSI customer engagements require vendor-contracted tooling per the canon overlay stack — Confluent has a contractual support relationship; WarpStream does not. This article exists as **competitive context for SA conversations and customer comparison-shopping**, not as FSI production guidance. If a customer is evaluating WarpStream as a cost-reduction alternative, use this article to brief them on the limitations they'll inherit; do not deploy WarpStream against FSI workloads without explicit vendor-contract sign-off (which has not been observed at time of writing).

## Detail

### The classic-Kafka half (confluent-docs verified)

`processing.guarantee=exactly_once_v2` in Kafka Streams turns on:

- Transactional producer (`transactional.id` set automatically per task)
- `enable.idempotence=true` (forced — incompatible with explicit `false`)

`enable.idempotence=true` requires `max.in.flight.requests.per.connection ≤ 5` (broker-side check), `acks=all`, and `retries > 0`. On classic Kafka, the in-flight cap costs ~5–15% throughput vs. `at_least_once` on most workloads — usually worth it for correctness.

> Validated via confluent-docs on 2026-05-16: `processing.guarantee=exactly_once_v2` semantics and the `enable.idempotence` constraint on `max.in.flight.requests.per.connection ≤ 5` are documented in the Kafka Streams developer guide and the producer configuration reference.

### The WarpStream-specific half

> ⚠️ unverified — context7 has limited published coverage of the exact throughput delta on WarpStream. The numbers below are from the vendored confluent-agent-skills@91d1871e WarpStream optimization reference (Confluent-maintained competitive guidance).

WarpStream's S3-backed storage tier introduces per-partition pull latency that classic Kafka does not have. When idempotent producers cap in-flight requests to 5, those 5 slots are occupied for longer (because each round-trip waits on an S3 read), and the producer throughput drops more than the 5–15% you'd see on classic Kafka. The same upstream reference also calls out:

- Java clients may see retriable `KAFKA_STORAGE_ERROR` errors with EOS enabled due to frequent partition ownership shifts between WarpStream agents
- WarpStream's general recommendation on high-throughput pipelines is to raise `max.in.flight.requests.per.connection` aggressively (1000 Java, 1000000 librdkafka) — exactly the knob that EOS forces back down to 5

### Benchmark recipe (quantify before deciding)

Run two parallel test pipelines on the customer's WarpStream cluster:

1. Pipeline A: synthetic 1 MB/s and 10 MB/s workloads with `processing.guarantee=at_least_once`
2. Pipeline B: same workloads with `processing.guarantee=exactly_once_v2`

Measure: producer record-send-rate, consumer lag at steady state, p99 end-to-end latency. The upstream reference suggests a 20–40% delta on WarpStream vs. ~5–15% on classic Kafka; numbers vary with object-storage backend and region. Treat any decision to enable EOS on WarpStream as data-driven, not default-driven.

### What this means for an SA briefing

If a customer cites WarpStream as a cost-reduction alternative AND has EOS requirements (FSI regulatory reporting is a common driver), the cost story may collapse: WarpStream's S3-storage savings can be eaten by the additional compute capacity needed to hit the same throughput under EOS. Quantify with a benchmark before letting them pivot.

## Related

- Foundation: `concepts/exactly-once-semantics` — idempotent producers, transactional producers, EOS v1/v2, Flink 2PC, Connect EOS (KIP-618).
- Parent: `concepts/kafka-streams-production-hardening` — EOS posture in production KS deployments.
- Sibling WarpStream trip-wire: `concepts/warpstream-config-overrides` — `fetch.min.bytes` ignored, `replication.factor` cosmetic.
- Sibling WarpStream trip-wire: `concepts/warpstream-schema-registry-format-constraint` — bundled SR limits.

---

*Source: confluentinc/agent-skills@91d1871e · skills/kafka-streams-programming/references/warpstream-optimization.md · Ingested 2026-05-16 (full MCP-validation gate per D-07) · Apache-2.0*
