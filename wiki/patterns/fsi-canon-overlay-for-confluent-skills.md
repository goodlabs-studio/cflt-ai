---
title: FSI Canon Overlay for Confluent Agent Skills
slug: fsi-canon-overlay-for-confluent-skills
category: pattern
confidence: high
last_validated: 2026-05-17
source: streaming-skills-plugin@1.0.0
source_commit: 91d1871ef8c320be92bca955c8e42492a2778cb4
tags: [fsi, overlay, upstream-skills, canon, kafka-streams, python-client, schema-registry, tableflow]
---

# FSI Canon Overlay for Confluent Agent Skills

> **Automated activation (v2.2+):** `/review` Step 4.0.5 and `/wiki:validate`
> Step 2e now call `tools/skill_routing.py` automatically when a claim or stub
> matches a skill's keywords. `activate_skill()` extracts the matching
> `## <skill-slug>` section below and returns the parsed override table to the
> calling skill spec, which folds the overrides into Canon Compliance checks.
> Manual read-then-apply is preserved for ad-hoc consultation but is no longer
> the only activation path.

When the four upstream skills shipped by the `streaming-skills-plugin@confluent-agent-skills` plugin activate inside cflt-ai — `kafka-streams-programming`, `developing-kafka-python-client`, `kafka-schema-registry`, `confluent-cloud-cdc-tableflow` — Claude reads this overlay and applies the FSI overrides below on top of the upstream defaults. Each section corresponds to one upstream skill, opens with a "when this skill activates" hook, and lays out a 5-column override table where every row traces back to the project's `CLAUDE.md` Confluent Canon (or an ADR / wiki article when the override goes beyond canon).

The overlay is the **operator/production** layer of the canon overlay stack: base (GoodLabs) → industry (FSI, this article) → customer (acme-bank, etc.) → engagement. The **developer-sandbox** layer is orthogonal and lands in Phase H.4 — when Claude is helping a developer scaffold a local-only test project, the dev-sandbox overlay relaxes some of the rows below; for any prod-tier or customer-facing work, FSI overrides win.

Provenance is at the bottom of the article. Every override table cites a section of `CLAUDE.md` so the reasoning is auditable.

## kafka-streams-programming

**When this skill activates:** developer asks for KStream/KTable topology design, requests a Build Mode scaffold, or hits a Debug Mode symptom (rebalancing loops, processing stalls, state-store issues, EOS transaction failures). Triggered by mentions of `KStream`, `KTable`, `TopologyTestDriver`, `StreamsBuilder`, `GlobalKTable`, joins/windows/aggregations, or any Kafka Streams runtime symptom.

| Override Key | Upstream Default | FSI Override | Rationale | Canon Source |
|---|---|---|---|---|
| `processing.guarantee` | Not set (at-least-once); `exactly_once_v2` is opt-in. WarpStream guidance: default to `at_least_once` | **`exactly_once_v2`** (required for any compliance-tier or reconciliation workload; required for regulatory reporting) | Duplicate/missing transactions constitute material misstatement under SOX 302/404; FSI cannot ship at-least-once for reportable financial events | `CLAUDE.md §FSI-Specific Overlay` ("Always call out exactly-once semantics implications for regulatory reporting") |
| `replication.factor` (internal topics) | `3` documented only under EOS resilience block; no general default | **`3` always** (broker + internal topics, not just under EOS) | Durable writes mandatory; matches broker-side canon | `CLAUDE.md §Cluster / Topic Design` ("Replication factor: 3 in production") |
| `min.insync.replicas` (broker side) | Not addressed by skill; broker default `1` | **`2`** | Two-replica ack floor required to survive single-broker loss without lost writes | `CLAUDE.md §Cluster / Topic Design` ("`min.insync.replicas = 2`") |
| `auto.register.schemas` | `true` in baseline (inline comment: "Set to false in production") | **`false`** unconditionally; schemas registered via CI/CD pipeline before app starts | Uncontrolled schema evolution is a Schema Registry Category C risk; FSI requires explicit, auditable registration | `CLAUDE.md §Schema Registry` ("Always use Avro or Protobuf in production") + the upstream `kafka-schema-registry` skill's Category C risk classification |
| `default.value.serde` | Set based on user's schema format (Avro / Protobuf / JSON Schema all listed equivalently) | **Avro or Protobuf only** (`SpecificAvroSerde` or `KafkaProtobufSerde`); **never** `KafkaJsonSchemaSerde` in production | JSON Schema lacks the strong typing and Schema Registry tooling maturity FSI compliance demands | `CLAUDE.md §Schema Registry` ("JSON Schema only for prototype/debug") |
| Topic naming | None enforced; topic names are user-provided strings | **`<domain>.<entity>.<event>`** (e.g., `payments.transaction.completed`) — enforced via Terraform module + Schema Registry subject naming | Cross-team discovery, prefix-based RBAC, and audit-trail readability all hinge on consistent naming | `CLAUDE.md §Cluster / Topic Design` ("Naming convention: `<domain>.<entity>.<event>`") |
| Partition count (output / DLQ topics) | None enforced; "pre-create before deploying to production" | **`6 × peak MB/s throughput`** starting point; tune for consumer parallelism + rebalance cost | Standardized capacity-planning rule keeps partition sprawl bounded and rebalance windows predictable | `CLAUDE.md §Cluster / Topic Design` ("Partition count: `6 × (peak MB/s throughput)` as a starting point") |
| Security (auth mechanism) | Side-by-side patterns (SASL_SSL+PLAIN, SCRAM, mTLS, OAUTHBEARER); CC env block defaults SASL_SSL+PLAIN | **mTLS + RBAC** in regulated environments; **never** username/password | FSI regulatory posture (PCI DSS, SOX, MAS TRM) requires certificate-based auth + service accounts; PLAIN/SCRAM are non-starters | `CLAUDE.md §Security` ("mTLS + RBAC in regulated environments; never username/password in FSI") |
| `num.standby.replicas` | `0` default outside EOS; `1` recommended under EOS resilience | **`1`** under EOS (matches upstream); **`1`** under at-least-once when stateful (override) | Standby replicas cut rebalance + state-restoration time, critical for FSI SLA tiers; cost is acceptable for the latency win | `CLAUDE.md §FSI-Specific Overlay` (SLA tier framing) + upstream EOS resilience block |
| WarpStream override path | Skill includes `references/warpstream-optimization.md` and overrides config for WarpStream targets | **Not applicable in FSI prod.** WarpStream lacks a Confluent contractual support relationship; do not deploy against FSI workloads. Treat WarpStream Streams targets as competitive context only | FSI vendor-backing rule: only vendor-contracted tooling for customer engagements | `CLAUDE.md §5. Competitive Context` (Redpanda framing applies identically to WarpStream) + FSI vendor-backing memory rule |

### Why this overlay

Kafka Streams is the closest upstream skill to FSI production reality because every default in the baseline has regulatory implications — schema discipline, EOS, replication, and durability are not optimizations in FSI, they are compliance requirements. The override surface here is intentionally large because the upstream baseline targets the broadest Kafka audience (dev, prototype, prod across AK/CP/CC/WarpStream); FSI narrows that to the prod-CC-with-regulatory-reporting subset.

## developing-kafka-python-client

**When this skill activates:** developer asks for Python producer/consumer scaffolding (greenfield or adding Kafka to an existing FastAPI/Flask/Django service), wants to migrate from raw JSON to schema-backed serialization, or hits a librdkafka config edge case. The skill enforces a HARD-GATE around mandatory questions (existing app vs. greenfield, target environment, producer/consumer/both) before generating any code — FSI overrides apply once the HARD-GATE is satisfied.

| Override Key | Upstream Default | FSI Override | Rationale | Canon Source |
|---|---|---|---|---|
| `acks` | librdkafka default (`-1`/`all`); not explicitly set in SKILL.md | **`acks=all`** (set explicitly; never rely on implicit defaults across librdkafka versions) | Durable writes mandatory; explicit override means future librdkafka default changes can't silently degrade durability | `CLAUDE.md §Producers` ("`acks=all` in production (never `acks=0` or `acks=1` for durable workloads)") |
| `enable.idempotence` | librdkafka default `true` since 2.x; WarpStream override path explicitly **disables** | **`true` always** (never disable, even for WarpStream — and WarpStream is out of scope for FSI prod regardless) | Idempotent producer prevents broker-level duplicates — Layer 1 of the FSI five-layer EOS pattern | `CLAUDE.md §Producers` ("`enable.idempotence=true` always") |
| `compression.type` | Not set; librdkafka default `none`; WarpStream guidance unspecified | **`lz4`** for throughput; **`zstd`** for storage-constrained clusters | Lz4 strikes the right CPU-vs-bandwidth ratio for typical FSI message sizes; never run uncompressed in prod | `CLAUDE.md §Producers` ("`compression.type=lz4` for throughput; `zstd` for storage-constrained clusters") |
| `auto.offset.reset` | Not set in SKILL.md; librdkafka default `latest` | **`earliest`** in new deployments; document deliberately if using `latest` | New deployments must not silently drop pre-existing messages; `latest` is a deliberate decision, not a default | `CLAUDE.md §Consumers` ("`auto.offset.reset=earliest` in new deployments; document deliberately if using `latest`") |
| `enable.auto.commit` | librdkafka default `true`; SKILL.md says "Consumers must `unsubscribe()` then `close()`" — implies graceful flow but does not override the auto-commit setting | **`false`** in any processing workload; commit explicitly after processing | Auto-commit can advance offsets before processing succeeds, causing silent data loss on failure | `CLAUDE.md §Consumers` ("Avoid `enable.auto.commit=true` in any processing workload; commit after processing") |
| `auto.register.schemas` | **`False`** (already aligned with FSI) | **`false`** (no change — confirms alignment); register schemas via dedicated `register_schema()` step before serializer creation | Aligns with canon already; documented here for explicit confirmation | `CLAUDE.md §Schema Registry` (registration discipline) + upstream Core Principle #2 |
| Schema format | **JSON Schema** by default; Avro only when targeting WarpStream's built-in SR | **Avro or Protobuf**; JSON Schema only for prototype/debug | FSI compliance posture demands strong typing and CSFLE compatibility — Avro/Protobuf are mandatory in prod | `CLAUDE.md §Schema Registry` ("Always use Avro or Protobuf in production; JSON Schema only for prototype/debug") |
| Authentication mechanism | `SASL_SSL` + `PLAIN` for CC; `PLAINTEXT` for local Docker; mixed for WarpStream | **mTLS + RBAC** (or `SASL_SSL` + `OAUTHBEARER` against CP MDS); **never** `PLAIN` against an FSI cluster | PLAIN passes credentials in cleartext over TLS — acceptable for prototype but not for FSI; service accounts per application required | `CLAUDE.md §Security` ("mTLS + RBAC in regulated environments; never username/password in FSI") + `CLAUDE.md §Security` ("Service accounts per application, not per team") |
| Message key for ordering | Always set message key for domain events (upstream Core Principle #7) | **Same as upstream** — set message key for any entity/event stream; only `key=None` if ordering explicitly does not matter | Aligns with canon; documented for explicit confirmation. Note: the WarpStream null-key sticky-partitioning exception in the upstream skill does not apply to FSI (WarpStream out of scope) | `CLAUDE.md §Cluster / Topic Design` (entity-keyed compaction) + `CLAUDE.md §FSI-Specific Overlay` (audit-trail / lineage requirement) |

### Why this overlay

The Python client skill is the most prescriptive upstream skill (it ships with a HARD-GATE confirmation flow), which means most of the discipline FSI needs is already there. The two genuinely large deltas are **schema format** (JSON Schema → Avro/Protobuf) and **authentication** (PLAIN → mTLS/OAUTHBEARER). Both originate from the upstream skill optimizing for developer onboarding ease; FSI's regulatory posture inverts the trade-off and prioritizes correctness + auditability over scaffold simplicity.

## kafka-schema-registry

**When this skill activates:** developer asks to scan a repo/folder for Kafka usage and audit Schema Registry posture, extract schemas from data models, tag PII fields, generate Terraform for schema registration, or build a migration plan with category-based rollout ordering. The skill produces three deliverables — `schema-report.md`, `schemas/` tree, and `terraform/` tree — and classifies every detected producer into one of six categories (A / A→Header / B / C / D / E).

| Override Key | Upstream Default | FSI Override | Rationale | Canon Source |
|---|---|---|---|---|
| Subject naming strategy | **TopicNameStrategy implicit** via `{topic}-value.{ext}` / `{topic}-key.{ext}` kebab-case file naming | **`TopicNameStrategy`** by default (confirms alignment); **`RecordNameStrategy`** for event-union patterns (multi-event topics) | Single-event topics use TopicNameStrategy for predictable subject-to-topic mapping; event-union topics need RecordNameStrategy to avoid subject collisions | `CLAUDE.md §Schema Registry` ("Subject naming strategy: `TopicNameStrategy` by default; `RecordNameStrategy` for event union patterns") |
| Compatibility mode (per subject) | Not set by the skill; Terraform templates register schemas without per-subject compatibility | **`BACKWARD`** default; **`FULL`** for shared consumer contracts (acme-bank shared-types library, cross-team event streams) | Default BACKWARD permits producer-led evolution; FULL is required when readers and writers evolve independently across teams | `CLAUDE.md §Schema Registry` ("Compatibility mode: `BACKWARD` default; escalate to `FULL` for shared consumer contracts") |
| Schema format | All three supported (Avro / JSON Schema / Protobuf); directory split into `schemas/{avro,json,proto}/` | **Avro or Protobuf only**; reject JSON Schema for any subject backing a production topic | JSON Schema in production is a Category D risk: weak typing, no CSFLE, no shared-types library support | `CLAUDE.md §Schema Registry` ("Always use Avro or Protobuf in production; JSON Schema only for prototype/debug") |
| `auto.register.schemas` | Detected as Category C risk; flagged but not eliminated by the skill | **`false`** mandatory; Category C producers must be migrated to explicit Terraform registration before any FSI deployment | Category C uncontrolled schema evolution is a regulatory exposure (schema-as-contract drift); aligns with the broader FSI Schema-Registry discipline | `CLAUDE.md §Schema Registry` (registration discipline) + upstream Phase 2 Risk Detection |
| PII tagging | `confluent:tags` with values `PII`, `PRIVATE`, `SENSITIVE`, `PHI` (upstream aligned) | **Same as upstream** — confirm alignment; also wire tags into CSFLE policy and audit-log pipelines (see `wiki/patterns/audit-log-siem-integration.md`) | Aligns with canon; documented to anchor the CSFLE + audit-log dependency chain | `CLAUDE.md §Schema Registry` (Avro/Protobuf supports `confluent:tags`) + `wiki/concepts/schema-inference-and-pii-categorization.md` |
| Migration rollout order | Per-category sequence (B → producer first; A→Header → consumer-verify → producer; C → Terraform-register → disable auto-register; E → consumer first) | **Same as upstream** — per-category sequence is canon-aligned; add C4E PR review gate before any Category C → A transition lands | Upstream rollout ordering is sound; FSI adds the human review gate to ensure C-class migrations don't silently regress downstream consumers | upstream `kafka-schema-registry/SKILL.md` Phase 4 (Categorization) + `wiki/patterns/fsi-governance-automation.md` (CI/CD enforcement + C4E override review) |

### Why this overlay

The schema-registry skill is the **most canon-aligned upstream skill** — its PII tagging vocabulary, per-category rollout, and TopicNameStrategy implicit default all match FSI canon out of the box. The overlay's job is to **harden the gaps** (explicit BACKWARD/FULL compatibility mode setting, hard-reject JSON Schema in prod, mandate Category C migration before deployment) rather than reinvent the workflow. This section is intentionally shorter than the others because most of the work is already done.

## confluent-cloud-cdc-tableflow

**When this skill activates:** developer asks to build a CDC pipeline (database → Iceberg/Delta) on Confluent Cloud using Debezium source connectors + Flink decode + Tableflow. Triggered by phrases like "CDC to Tableflow", "database to Iceberg", "stream database changes to data lake", or "schemaless topic to Tableflow". Does NOT trigger on generic CDC/Debezium requests without a Tableflow destination.

| Override Key | Upstream Default | FSI Override | Rationale | Canon Source |
|---|---|---|---|---|
| Schema format (connector output) | **`JSON_SR` default**; AVRO and PROTOBUF supported alternatives | **`AVRO`** default; PROTOBUF acceptable; never plain `JSON` (already enforced upstream) | Same Avro/Protobuf-in-prod canon as the other skills; `JSON_SR` is JSON Schema under the hood, which FSI rejects for prod | `CLAUDE.md §Schema Registry` ("Always use Avro or Protobuf in production") |
| Flink watermark strategy | Not set explicitly; Cloud Flink auto-discovers CDC tables and handles source-table properties automatically | **`BOUNDED_OUT_OF_ORDERNESS`** with a bounded delay; never unbounded — set explicitly on any custom Flink statement that introduces watermark logic beyond CDC auto-discovery | Unbounded watermarks stall windowed aggregations and produce non-deterministic results — incompatible with deterministic regulatory reporting | `CLAUDE.md §Flink SQL (Confluent Cloud)` ("Watermark strategy: `BOUNDED_OUT_OF_ORDERNESS` with a bounded delay; never unbounded") |
| `scan.startup.mode` | Not addressed by skill (CC Flink auto-managed; consume verification starts at latest offset) | **`scan.startup.mode = 'earliest-offset'`** on any custom Flink table that backs a Tableflow target (deterministic replay required) | Regulatory reporting + audit-trail reconstruction require deterministic replay from a known offset; latest-only consumption breaks lineage | `CLAUDE.md §Flink SQL (Confluent Cloud)` ("Always specify `scan.startup.mode = 'earliest-offset'` for deterministic replay") |
| Connector preference / Tableflow target topic | Flink decode → target topic with `'changelog.mode' = 'upsert'` → Tableflow (upstream Critical Architecture Rule #1 + #2) | **Same as upstream** — `UPSERT-KAFKA` semantics via `changelog.mode='upsert'` on the target topic is canon-aligned; confirm and enforce | Aligns with `UPSERT-KAFKA` connector preference for CDC/changelog output; immutability of Tableflow changelog mode makes "set correctly from the start" a hard requirement | `CLAUDE.md §Flink SQL (Confluent Cloud)` ("Prefer `UPSERT-KAFKA` connector for changelog/CDC-style output") + upstream Critical Architecture Rule #2 |
| Window aggregations (when CDC pipeline includes aggregation Flink statements) | Not addressed directly by skill (focused on decode pattern, not aggregations) | **Tumbling > sliding > session** for resource efficiency; choose tumbling unless the use case genuinely requires overlap (sliding) or activity-burst boundaries (session) | Resource efficiency directly translates to CFU cost and consumer-side latency; tumbling is the default unless overridden with rationale | `CLAUDE.md §Flink SQL (Confluent Cloud)` ("Window aggregations: tumbling > sliding > session for resource efficiency") |
| Schema Registry compatibility for CDC subjects | Upstream recommends `FULL_TRANSITIVE` override (default `BACKWARD` "can halt CDC connectors when database columns are dropped") | **`FULL_TRANSITIVE`** (matches upstream); for cross-team consumer contracts on the target topic also escalate to `FULL` per Schema-Registry section above | Upstream guidance is correct for CDC sources; FSI extends the same discipline to the Tableflow target subjects | upstream `confluent-cloud-cdc-tableflow/SKILL.md` Phase 1.3 + `CLAUDE.md §Schema Registry` |
| Tableflow target format | Iceberg (recommended) or Delta Lake | **Iceberg** preferred for new pipelines (broader downstream tooling, open governance); Delta Lake acceptable when the downstream consumer is Databricks-native | Iceberg's open table format + Confluent's Cluster Linking → Tableflow → Iceberg → Databricks pattern is the FSI canonical analytics flow (see `wiki/patterns/fsi-l1-reference-architecture.md`) | `wiki/patterns/fsi-l1-reference-architecture.md` (L1 + CC Tableflow → Databricks analytics path) |
| Tableflow storage type | Managed (recommended) or BYOB | **Managed** for non-regulated environments; **BYOB** with customer-controlled S3 + KMS for any compliance-tier workload (data residency, key management requirements) | Regulated FSI workloads frequently mandate customer-controlled keys and bucket policies; managed storage is acceptable only when the regulator permits it | `CLAUDE.md §Security` (audit log enabled on all production clusters) + customer-overlay considerations (acme-bank often requires BYOB) |

### Why this overlay

The CDC-Tableflow skill is the **most architecturally opinionated** upstream skill — it bakes in two Critical Architecture Rules (Flink decode required, changelog mode immutable) that FSI inherits wholesale. The overrides here are mostly about **format discipline** (Avro over JSON_SR), **deterministic replay** (`earliest-offset`), and **storage choice** (BYOB for compliance tiers). The Tableflow immutability rule (already in upstream + already covered by `wiki/concepts/tableflow-changelog-mode-immutability.md` trip-wire) means there is no second chance to fix mode after first materialization — getting `changelog.mode='upsert'` correct from the start is a one-shot operation, and FSI's bias toward Iceberg + earliest-offset replay reinforces this.

## How to use this overlay

When an upstream skill activates inside cflt-ai, Claude reads this article and applies the override rows for that skill's section. For any override key not listed in a section, the upstream default applies — silence means alignment. If the upstream skill produces output that conflicts with an FSI override row (e.g., scaffolds Python code with `enable.auto.commit=true` despite the override table), the overlay wins: Claude must edit the generated output to match the override row before presenting it, and log the conflict as a review note for the developer. The overlay does not modify the upstream skills themselves — they remain pinned at SHA `91d1871e` and are upgraded explicitly per the H.3b pin process.

---

**Provenance**
- `streaming-skills-plugin/kafka-streams-programming/SKILL.md` @ 91d1871e
- `streaming-skills-plugin/developing-kafka-python-client/SKILL.md` @ 91d1871e
- `streaming-skills-plugin/kafka-schema-registry/SKILL.md` @ 91d1871e
- `streaming-skills-plugin/confluent-cloud-cdc-tableflow/SKILL.md` @ 91d1871e

Vendor pin: `tools/vendor-sources.json` → `confluent-agent-skills` @ commit `91d1871ef8c320be92bca955c8e42492a2778cb4`. Plugin pin formalized in H.3b (`tools/vendor-plugins.json` + `.github/workflows/streaming-skills-drift.yml`).
