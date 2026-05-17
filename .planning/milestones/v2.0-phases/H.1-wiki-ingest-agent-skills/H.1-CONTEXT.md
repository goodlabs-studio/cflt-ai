# Phase H.1: Wiki ingest from confluent-agent-skills references — Context

**Gathered:** 2026-05-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Compile ~10 peer-reviewed Confluent reference articles from `confluentinc/agent-skills/skills/*/references/` into our wiki under existing `wiki/concepts/` and `wiki/patterns/` namespaces, and lift ≥9 trip-wire facts (hard-won correctness notes embedded in the upstream references) into standalone `confidence: high` micro-articles. After H.1, our wiki has authoritative coverage of Kafka Streams topology/debugging/production-hardening, Schema Registry adoption playbook, CDC-to-Tableflow pipeline construction (Flink decode pattern), and the specific gotchas that would trip up an SA on a customer engagement. Source content is vendored at pinned commit SHA `91d1871ef8c320be92bca955c8e42492a2778cb4`; upgrade is an explicit PR.

Out of scope: `/dsp:scaffold` (H.3c), FSI canon overlay article (H.3a), developer-sandbox profile family (H.4), eval harness extension (H.2). This phase is content-only — no new skills, no profile changes, no CI gates beyond what `/wiki:validate` already provides.

</domain>

<decisions>
## Implementation Decisions

### Source acquisition
- **D-01:** Vendored copy at pinned commit SHA in `raw/vendor/confluent-agent-skills/<sha>/`. The pin is recorded in a new `tools/vendor-sources.json` file (e.g., `{"confluent-agent-skills": {"upstream": "https://github.com/confluentinc/agent-skills", "commit": "91d1871ef8c320be92bca955c8e42492a2778cb4"}}`). Upgrade workflow: bump SHA in vendor-sources.json → re-clone vendor directory at new SHA → re-run `/wiki:ingest` against affected articles → re-validate → commit as a single PR. Mirrors G.2c pattern.
- **D-02:** Vendor directory is **not** a submodule — just a shallow checkout copied in via the planner's task (e.g., `git clone --depth=1 https://github.com/confluentinc/agent-skills.git /tmp/...; cp -r skills/*/references raw/vendor/confluent-agent-skills/<sha>/`). Submodules add operational tax (`.gitmodules`, pointer commits, recursive clone) for negligible benefit here since we only read content.

### Wiki namespacing
- **D-03:** Ingested articles live alongside our own in **standard `wiki/concepts/` and `wiki/patterns/`** — no separate vendor namespace. Distinguished by two frontmatter fields:
  - `source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4`
  - `upstream_path: skills/<skill-name>/references/<file>.md`
  Plus a provenance footer at the bottom of each article:
  > `Source: confluentinc/agent-skills@91d1871e · skills/<skill>/references/<file>.md · Ingested 2026-05-16`
- **D-04:** No filename namespace prefix (`confluent.kafka-streams-debugging.md` is NOT how we name them). Names follow our existing convention: descriptive, lowercase-with-hyphens, scoped by topic (`kafka-streams-debugging.md`, `cdc-to-tableflow-flink-decode.md`).

### Trip-wire articles
- **D-05:** Each trip-wire fact gets its own short `confidence: high` article in `wiki/concepts/`. Target ≥9 trip-wires (exceeds the WIKI-07 minimum of 8). Articles are **citation-friendly** — short title, single section, exact fact stated upfront, full provenance to upstream source path + line number, plus cross-link back to the parent ingest article that elaborates context.
- **D-06:** Parent ingest articles cross-link to their trip-wire descendants via the `related:` frontmatter field, so navigation works in both directions. Parent articles do NOT inline-repeat the trip-wire claim — they cite the standalone article as the canonical source.

### MCP re-validation strategy
- **D-07:** Selective re-validation. The 9 trip-wire articles get **full MCP re-validation** via `/wiki:ingest` standard flow (`confluent-docs` for config/API, `context7` for patterns) — these are cited verbatim downstream so accuracy stakes are highest. The 10 parent articles get **source attestation** instead: `confidence: high` justified by `source: confluent-agent-skills@<sha>` provenance + the fact that upstream's evals gate at 90%+ before merge. Saves ~60% of ingest time without measurable correctness loss.
- **D-08:** `/wiki:validate` is the routine re-validation surface, same as for all other wiki articles. The existing 90-day `last_validated` decay rule applies — these articles drop from `confidence: high` → `medium` after 90 days unless re-validated.

### Drift detection
- **D-09:** Passive drift detection only. Frontmatter `source: confluent-agent-skills@<sha>` is the staleness signal. `/wiki:validate` is extended to compare the SHA against the current pin in `tools/vendor-sources.json` and emit a `drift` finding when stale. Surfaces in routine wiki health checks alongside the existing decay rule. No CI drift gate — content articles aren't a fail-PR concern the way classification keys are.
- **D-10:** Stretch (not blocking H.1 success criteria): periodic comparison against upstream main (`git ls-remote https://github.com/confluentinc/agent-skills HEAD`) to flag when a re-ingest would pick up new content. Implement as a sub-task of `/wiki:validate` if it fits naturally; defer otherwise.

### Article inventory (locked from CONTEXT.md to reduce planner research)

**10 parent articles to ingest** (from the 26 ref files in `confluentinc/agent-skills@91d1871e`, dropping project scaffolds like `readme-template.md`, `terraform-templates.md`, `cli-commands.md`, `docker-compose.md`, `verification.md`, `build-templates.md`, `report-template.md`):

| # | Upstream source | Target wiki article | Type |
|---|-----------------|---------------------|------|
| 1 | `kafka-streams-programming/references/topology-patterns.md` | `wiki/patterns/kafka-streams-topology-patterns.md` | pattern |
| 2 | `kafka-streams-programming/references/debugging.md` | `wiki/concepts/kafka-streams-debugging.md` | concept |
| 3 | `kafka-streams-programming/references/production-hardening.md` | `wiki/concepts/kafka-streams-production-hardening.md` | concept |
| 4 | `kafka-streams-programming/references/schema-patterns.md` | `wiki/concepts/kafka-streams-schema-patterns.md` | concept |
| 5 | `kafka-streams-programming/references/config-baseline.md` | `wiki/concepts/kafka-streams-config-baseline.md` | concept |
| 6 | `kafka-streams-programming/references/architecture.md` | `wiki/concepts/kafka-streams-architecture.md` | concept |
| 7 | `confluent-cloud-cdc-tableflow/references/flink-sql-patterns.md` | `wiki/patterns/cdc-to-tableflow-flink-decode.md` | pattern |
| 8 | `confluent-cloud-cdc-tableflow/references/{connector-configs,database-prerequisites,troubleshooting}.md` (merged) | `wiki/concepts/cdc-source-connector-setup.md` | concept |
| 9 | `kafka-schema-registry/references/{detection-patterns,code-migration}.md` (merged) | `wiki/patterns/schema-registry-adoption-playbook.md` | pattern |
| 10 | `kafka-schema-registry/references/{schema-inference,categorization}.md` (merged) | `wiki/concepts/schema-inference-and-pii-categorization.md` | concept |

**9 trip-wire micro-articles to author** (lifted from the parent ingests; each is `confidence: high`, ≤500 words, single-fact-focused):

| # | Trip-wire fact | Target wiki article | Source |
|---|---------------|---------------------|--------|
| 1 | Tableflow changelog mode is immutable after first materialization | `wiki/concepts/tableflow-changelog-mode-immutability.md` | cdc-tableflow/SKILL.md |
| 2 | Don't enable Tableflow on a CDC source topic — tombstones break APPEND mode | `wiki/patterns/cdc-tableflow-flink-decode-required.md` | cdc-tableflow/SKILL.md |
| 3 | OracleXStreamSource doesn't support `after.state.only` config | `wiki/concepts/oracle-xstream-source-limitations.md` | cdc-tableflow/SKILL.md |
| 4 | `StreamsUncaughtExceptionHandler` is in `org.apache.kafka.streams.errors`, NOT a nested class under `KafkaStreams` in KS 4.x | `wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md` | kafka-streams-programming/SKILL.md + evals.json |
| 5 | Avro schemas live in `src/main/avro/`, NOT `src/main/resources/avro/` | `wiki/concepts/avro-schema-source-directory.md` | kafka-streams-programming/evals.json |
| 6 | `kafka-console-producer` doesn't speak Schema Registry — use `kafka-avro-console-producer` (or equivalent schema-aware producer) for verification | `wiki/concepts/schema-aware-console-producer-required.md` | kafka-streams-programming/evals.json |
| 7 | WarpStream built-in Schema Registry only supports Avro and Protobuf; `GET /schemas/types` returns `["AVRO","PROTOBUF"]` — not JSON Schema | `wiki/concepts/warpstream-schema-registry-format-constraint.md` | python-client/SKILL.md + warpstream-optimization.md |
| 8 | WarpStream `fetch.min.bytes` is not supported; `replication.factor` is cosmetic (always 3) | `wiki/concepts/warpstream-config-overrides.md` | kafka-streams-programming/references/warpstream-optimization.md |
| 9 | `exactly_once_v2` enables idempotent producers internally → significant throughput cost on WarpStream (limited in-flight request concurrency) | `wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md` | kafka-streams-programming/references/warpstream-optimization.md |

### Tools and skill mechanics
- **D-11:** Use existing `/wiki:ingest` skill — extend its prompt only to accept the new `source:` and `upstream_path:` frontmatter fields, not rewriting the skill. The skill's existing MCP-validation gate continues to apply for trip-wire articles.
- **D-12:** `raw/_ingest.md` queue gets 19 new entries (10 parents + 9 trip-wires). Each entry references the vendored path under `raw/vendor/confluent-agent-skills/<sha>/`. After successful ingest, entries move from `## Pending` to `## Processed` per existing skill behavior.
- **D-13:** `wiki/_index.md` and `wiki/_graph.md` updates handled by `/wiki:ingest` as part of standard flow (Steps 4–5 of the skill).

### Claude's Discretion
- Exact wording of provenance footers (within the shape locked in D-03)
- How to merge the 3-into-1 (#8) and 2-into-1 (#9, #10) parent articles — section ordering, header levels, intro framing
- Trip-wire article opening sentence (the single-fact-stated-upfront line)
- Whether to include the WarpStream content with explicit "competitive context, not FSI guidance" framing in the article body (vendor-backing rule from feedback memory)
- Cross-link `related:` fields (planner will compute based on existing wiki graph)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source of upstream content
- `https://github.com/confluentinc/agent-skills/tree/91d1871e/skills` — pinned snapshot of the four skills (kafka-streams-programming, developing-kafka-python-client, kafka-schema-registry, confluent-cloud-cdc-tableflow), each with `SKILL.md`, `references/`, and `evals/evals.json`
- Planner: clone `--depth=1` at SHA `91d1871ef8c320be92bca955c8e42492a2778cb4`, copy `skills/*/references/` and the four `SKILL.md` files into `raw/vendor/confluent-agent-skills/91d1871e/` (truncate SHA to 8 chars in path for readability)

### cflt-ai wiki contract
- `wiki/_index.md` — master article index (37 entries currently); ingest must append per format `[Title](path/to/article.md) — one-line summary — #tag1 #tag2`
- `wiki/_graph.md` — backlink graph; every new article needs ≥1 inbound and ≥1 outbound link in format `source/article → target/article : relationship description`
- `wiki/concepts/schema-registry-best-practices.md` (existing) — exemplar frontmatter shape (`title, tags, sources, related, confidence, last_updated, last_validated`); H.1 articles extend with `source: confluent-agent-skills@<sha>` and `upstream_path: skills/<skill>/references/<file>.md`
- `wiki/patterns/aks-kafka-tuning.md` (existing) — pattern-template exemplar
- `.claude/commands/wiki/ingest.md` — the `/wiki:ingest` skill we're using (6 steps: queue → index → draft → MCP-validate → write → update graph); H.1 follows this verbatim
- `.claude/commands/wiki/references/article-format.md` — frontmatter schema and article templates (concept vs pattern)
- `.claude/commands/wiki/references/quality-standards.md` — MCP routing table (`confluent-docs` for config/API, `context7` for patterns)

### Prior phase context
- `.planning/phases/G.2c-tool-classification-rename/G.2c-CONTEXT.md` — established the pinning + CI-drift pattern we mirror here (D-01, D-09); also established generator-as-single-source-of-truth principle (the vendor SHA play here is the same shape)
- `.planning/PROJECT.md` — Core Value (canon overlay stack); v2.0 active milestone
- `.planning/REQUIREMENTS.md` — WIKI-06, WIKI-07, WIKI-08 success criteria (the locked specs H.1 must satisfy)

### Roadmap entry
- `.planning/ROADMAP.md` §"Phase H.1: Wiki ingest from confluent-agent-skills references" — full goal, depends_on, success criteria

### Memory / global rules
- `feedback_confluent_supported_connectors.md` — FSI vendor-backing rule: only vendor-contracted tooling for FSI customer engagements. WarpStream content (trip-wires 7, 8, 9 + the python-client warpstream-optimization.md material) must be framed as **competitive context for SA conversations**, not as FSI production guidance. Add an explicit note in each WarpStream article body.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`/wiki:ingest` skill** — handles the full content compilation flow (queue → draft → MCP-validate → write → index/graph). H.1 uses it verbatim; only extension is accepting `source:` and `upstream_path:` frontmatter fields, which are additive (won't break existing 37 articles).
- **`/wiki:validate` skill** — routine validation against MCP sources. H.1 phase verification runs this against every newly ingested article; success criterion #3 demands zero drift findings.
- **`tools/wiki-lint.py`** — applies the 90-day `last_validated` decay rule. Will pick up H.1 articles automatically.
- **`tools/wiki-stats.py`** — coverage tracking. Will pick up H.1 articles automatically.
- **`raw/_ingest.md`** — existing pending/processed queue format; H.1 adds 19 entries to `## Pending`.

### Established Patterns
- **Frontmatter convention** — `title, tags, sources, related, confidence, last_updated, last_validated`; locked across 37 existing articles. H.1 extends with two additive fields (`source` and `upstream_path`), no breaking change.
- **`confidence: high` standard** — must be MCP-validated OR have explicit source attestation per quality-standards.md. H.1 trip-wires use the former; H.1 parents use the latter.
- **Cross-linking via `related:`** — every article has ≥1 inbound + ≥1 outbound link in `_graph.md`. H.1 must compute these on ingest.
- **Topic naming** — descriptive, lowercase-with-hyphens, no vendor prefix. `wiki/concepts/kafka-streams-debugging.md` not `wiki/concepts/confluent.kafka-streams-debugging.md`.
- **Vendor sources file** — does NOT currently exist. `tools/vendor-sources.json` is new in H.1 (small JSON file: `{"<vendor-name>": {"upstream": "<URL>", "commit": "<SHA>"}}`). H.3b will reuse it for `streaming-skills-plugin` pin, so the schema must be general (not agent-skills-specific).

### Integration Points
- New content lives in existing `wiki/concepts/` and `wiki/patterns/` directories — no new wiki layout
- `wiki/_index.md` gets 19 new entries (10 parents + 9 trip-wires)
- `wiki/_graph.md` gets cross-links between parents and their trip-wire descendants, plus links to existing relevant articles
- `raw/_ingest.md` Pending queue gets 19 new entries
- `tools/vendor-sources.json` is a NEW file introduced by H.1; H.3b will extend it
- `raw/vendor/confluent-agent-skills/91d1871e/` is a NEW vendor directory (gitignored? — D-decision needed by planner; recommendation: track in repo so `git log` shows when SHA changed)

</code_context>

<specifics>
## Specific Ideas

**The four upstream skills (canon-aligned source):**

1. `kafka-streams-programming` — Architect/Build/Debug modes for KS apps. References cover topology, debugging, production-hardening, schema patterns, config baseline, architecture, WarpStream optimization.
2. `developing-kafka-python-client` — Scaffolds confluent-kafka-python projects. References cover multi-event guide, schema generation rules, WarpStream optimization.
3. `kafka-schema-registry` — Scans projects for Kafka usage, generates Terraform for SR registration. References cover detection patterns, code migration, schema inference, categorization (PII tagging).
4. `confluent-cloud-cdc-tableflow` — Sets up CDC→Iceberg/Delta pipelines via Debezium + Flink + Tableflow. References cover connector configs, database prerequisites, Flink SQL patterns, REST API, troubleshooting.

**Filename normalization rationale (D-04):**

Existing wiki uses `schema-evolution-strategies.md`, `schema-registry-best-practices.md`, `producer-config-fsi.md` — no vendor prefix. New articles follow same shape. Cross-linking and search work uniformly.

**The 9 trip-wires were chosen because each:**
- Is verbatim citable in `/review` claim extraction (REVW-01)
- Would cause a customer-visible failure if violated (compilation error, suspended pipeline, lost data, throughput tank)
- Is not in upstream Confluent canonical docs prominently enough that an SA would naturally encounter it via `confluent-docs` MCP

**WarpStream framing — concrete:**

The three WarpStream trip-wires (#7, #8, #9) must include this paragraph in the article body, immediately after the trip-wire claim:

> **FSI context:** WarpStream is not Confluent. FSI customer engagements require vendor-contracted tooling per the canon overlay stack — Confluent has a contractual support relationship; WarpStream does not. This article exists as **competitive context for SA conversations and customer comparison-shopping**, not as FSI production guidance. If a customer is evaluating WarpStream as a cost-reduction alternative, use this article to brief them on the limitations they'll inherit; do not deploy WarpStream against FSI workloads without explicit vendor-contract sign-off (which has not been observed at time of writing).

**Vendor-sources.json schema (forward-compatible with H.3b):**

```json
{
  "confluent-agent-skills": {
    "upstream": "https://github.com/confluentinc/agent-skills",
    "commit": "91d1871ef8c320be92bca955c8e42492a2778cb4",
    "ingested_at": "2026-05-16",
    "vendor_path": "raw/vendor/confluent-agent-skills/91d1871e/",
    "license": "Apache-2.0",
    "kind": "wiki-source"
  },
  "streaming-skills-plugin": {
    "// future H.3b entry": "...",
    "kind": "claude-plugin"
  }
}
```

**Anti-references (non-goals for H.1):**

- Don't extend the wiki frontmatter schema beyond the two additive fields (`source`, `upstream_path`) — that's a separate cleanup if it ever needs to happen
- Don't redesign `/wiki:ingest` skill — only add the new frontmatter field acceptance
- Don't add a CI gate for vendor drift — `/wiki:validate` is the routine surface; if a future incident requires hard blocking, that's a separate phase
- Don't ingest project-scaffold templates (`readme-template.md`, `terraform-templates.md`, `report-template.md`, `cli-commands.md`, `docker-compose.md`, `verification.md`, `build-templates.md`) — these are useful inside the upstream skills but not wiki canon
- Don't author overlay decisions in this phase — FSI canon overlay is H.3a's job
- Don't build `/dsp:scaffold` — that's H.3c

</specifics>

<deferred>
## Deferred Ideas

- **Active CI drift gate for vendor sources** — Considered and rejected for H.1 (content articles ≠ classification keys). If a future incident shows wiki drift causing real customer-engagement bugs, file as 999.x and promote into a follow-on phase.
- **Re-ingest automation when upstream releases** — D-10 stretch goal; if `/wiki:validate` doesn't naturally accommodate the upstream-main comparison, defer to a small follow-up rather than expanding H.1's scope.
- **Ingesting the upstream `evals/evals.json` files as wiki content** — Their evals are CI gates over there, not knowledge content. The trip-wire articles we author here distill the load-bearing facts from those evals; we don't need to ingest the evals JSON itself. (If H.2 needs them as fixtures, H.2 can fetch them separately.)
- **Vendoring other Confluent repos** (e.g., `confluentinc/tutorials`) — Same vendor-sources.json schema would accommodate, but scope-creep for H.1.
- **Frontmatter `vendor:` boolean shortcut** — Could add `vendor: true` as a quick discriminator instead of always parsing the `source` field. Not worth the schema change for one phase.

</deferred>

---

*Phase: H.1-wiki-ingest-agent-skills*
*Context gathered: 2026-05-16*
