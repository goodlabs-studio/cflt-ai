---
phase: H.1-wiki-ingest-agent-skills
plan: 02
type: execute
wave: 2
depends_on: [H.1-01]
files_modified:
  - wiki/patterns/kafka-streams-topology-patterns.md
  - wiki/concepts/kafka-streams-debugging.md
  - wiki/concepts/kafka-streams-production-hardening.md
  - wiki/concepts/kafka-streams-schema-patterns.md
  - wiki/concepts/kafka-streams-config-baseline.md
  - wiki/concepts/kafka-streams-architecture.md
  - wiki/patterns/cdc-to-tableflow-flink-decode.md
  - wiki/concepts/cdc-source-connector-setup.md
  - wiki/patterns/schema-registry-adoption-playbook.md
  - wiki/concepts/schema-inference-and-pii-categorization.md
  - wiki/_index.md
  - wiki/_graph.md
  - raw/_ingest.md
autonomous: true
requirements: [WIKI-06]
requirements_addressed: [WIKI-06]
must_haves:
  truths:
    - "10 parent ingest articles exist at the locked paths from CONTEXT.md D-05 table 1, each with extended frontmatter (`source`, `upstream_path`) and a provenance footer in the body"
    - "Every parent article has `confidence: high` justified by source attestation (D-07) — upstream provenance + the 90%+ upstream evals gate, NOT a full MCP re-validation pass"
    - "wiki/_index.md lists all 10 parent articles under correct Concepts/Patterns sections with the standard `[Title](path) — summary — #tags` format"
    - "wiki/_graph.md contains ≥20 new link entries (≥1 inbound + ≥1 outbound for each of the 10 parents); cross-links between merged-article siblings and into the existing 37-article graph"
    - "raw/_ingest.md ## Pending no longer contains the 10 parent entries (moved to ## Processed per Step 6 of /wiki:ingest)"
    - "python tools/wiki-lint.py reports ONLY the expected 9 forward-reference warnings to unauthored trip-wires (closed in H.1-03); zero regressions"
  artifacts:
    - path: "wiki/patterns/kafka-streams-topology-patterns.md"
      provides: "Parent article #1; pattern template; sourced from kafka-streams-programming/references/topology-patterns.md"
      contains: "source: confluent-agent-skills@91d1871"
    - path: "wiki/concepts/kafka-streams-debugging.md"
      provides: "Parent article #2; concept template; seeds trip-wires #4, #5, #6"
      contains: "source: confluent-agent-skills@91d1871"
    - path: "wiki/concepts/kafka-streams-production-hardening.md"
      provides: "Parent article #3"
      contains: "source: confluent-agent-skills@91d1871"
    - path: "wiki/concepts/kafka-streams-schema-patterns.md"
      provides: "Parent article #4"
      contains: "source: confluent-agent-skills@91d1871"
    - path: "wiki/concepts/kafka-streams-config-baseline.md"
      provides: "Parent article #5"
      contains: "source: confluent-agent-skills@91d1871"
    - path: "wiki/concepts/kafka-streams-architecture.md"
      provides: "Parent article #6"
      contains: "source: confluent-agent-skills@91d1871"
    - path: "wiki/patterns/cdc-to-tableflow-flink-decode.md"
      provides: "Parent article #7; pattern; seeds trip-wires #1 and #2"
      contains: "source: confluent-agent-skills@91d1871"
    - path: "wiki/concepts/cdc-source-connector-setup.md"
      provides: "Parent article #8; THREE-WAY merge of connector-configs + database-prerequisites + troubleshooting"
      contains: "skills/confluent-cloud-cdc-tableflow/references/connector-configs.md"
    - path: "wiki/patterns/schema-registry-adoption-playbook.md"
      provides: "Parent article #9; TWO-WAY merge of detection-patterns + code-migration"
      contains: "skills/kafka-schema-registry/references/detection-patterns.md"
    - path: "wiki/concepts/schema-inference-and-pii-categorization.md"
      provides: "Parent article #10; TWO-WAY merge of schema-inference + categorization"
      contains: "skills/kafka-schema-registry/references/schema-inference.md"
  key_links:
    - from: "wiki/_index.md"
      to: "wiki/concepts/kafka-streams-debugging.md"
      via: "Concepts section index entry"
      pattern: "kafka-streams-debugging"
    - from: "wiki/_graph.md"
      to: "wiki/patterns/cdc-to-tableflow-flink-decode.md"
      via: "≥1 inbound + ≥1 outbound graph edge"
      pattern: "cdc-to-tableflow-flink-decode"
    - from: "wiki/patterns/kafka-streams-topology-patterns.md"
      to: "concepts/exactly-once-semantics"
      via: "related: frontmatter field cross-linking to existing wiki article"
      pattern: "related:.*exactly-once-semantics"
    - from: "raw/_ingest.md"
      to: "## Processed"
      via: "10 parent entries moved from Pending to Processed with compiled date + wiki_articles list"
      pattern: "compiled: 2026-05-16"
---

<objective>
Ingest the 10 parent articles from `raw/vendor/confluent-agent-skills/91d1871e/skills/*/references/` into `wiki/concepts/` and `wiki/patterns/` following the `/wiki:ingest` 6-step flow, with `confidence: high` justified by source attestation (D-07) rather than full MCP re-validation. Updates `wiki/_index.md` and `wiki/_graph.md` for all 10 articles. Moves their 10 ingest queue entries from `## Pending` to `## Processed`.

Purpose: Establish the long-form parent articles that the 9 trip-wire micro-articles in H.1-03 will cite back into. These are the "context" articles — readers land on a trip-wire fact, follow `related:` back to the parent for the surrounding picture.

Output: 10 new wiki articles (4 patterns + 6 concepts when you count the merges), updated index and graph, processed queue entries. WIKI-06 (≥10 articles) is fully satisfied by the end of this plan. WIKI-08 (`_index.md` + `_graph.md` updated, zero drift) has only PARTIAL coverage here (index and graph updated, but forward-references to unauthored trip-wires still warn); H.1-03 fully satisfies WIKI-08 by authoring the trip-wires and running the final clean lint. WIKI-08 is therefore NOT listed in this plan's `requirements_addressed` — it lives only in H.1-03.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md
@.planning/phases/H.1-wiki-ingest-agent-skills/H.1-01-SUMMARY.md
@.claude/commands/wiki/ingest.md
@.claude/commands/wiki/references/article-format.md
@.claude/commands/wiki/references/quality-standards.md
@wiki/_index.md
@wiki/_graph.md
@wiki/concepts/schema-registry-best-practices.md
@wiki/patterns/aks-kafka-tuning.md
@raw/_ingest.md
@tools/vendor-sources.json
</context>

<interfaces>
<!-- Standard wiki frontmatter (existing 7 fields, locked) + 2 H.1-additive fields. -->

```yaml
# ---
title: <string>
tags: [<tag1>, <tag2>, ...]                   # COMMA-SEPARATED — see YAML rule below
sources: [<path>, ...]                        # vendor paths
related: [<wiki-relative-path>, ...]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/<skill>/references/<file>.md
# ---
```

**YAML rule (load-bearing — Issue 1 blocker fix):** Tag arrays MUST be comma-separated flow-sequence — `tags: [a, b, c]` NOT `tags: [a b c]` — matching the existing wiki convention (see `wiki/concepts/schema-registry-best-practices.md` line 3). YAML interprets `[a b c]` as a single scalar string `"a b c"`, NOT a 3-element list; downstream tag-based filtering (`tools/wiki-lint.py`, `tools/wiki-stats.py`, tag-keyed logic in `/ask` and `/review`, `_index.md` tag display) silently breaks. The verify in Task 4 grep-checks every new article's tags parse as a YAML list.

For merged-parent articles (#8, #9, #10), `upstream_path` is a YAML list:
```yaml
upstream_path:
  - skills/<skill>/references/<file1>.md
  - skills/<skill>/references/<file2>.md
  - skills/<skill>/references/<file3>.md
```

Provenance footer (last paragraph in body, per D-03):
```markdown
# ---

*Source: confluentinc/agent-skills@91d1871e · skills/<skill>/references/<file>.md · Ingested 2026-05-16 · Apache-2.0*
```

For merged articles, footer lists all merge inputs separated by ` · `.

`wiki/_index.md` line format (per existing convention, line 17 of _index.md):
```
[Title](path/to/article.md) — one-line summary — #tag1 #tag2
```

`wiki/_graph.md` line format (per existing convention, line 13 of _graph.md):
```
source/article → target/article : relationship description
```

`raw/_ingest.md` Processed entry format (per existing convention, line 33-57 of raw/_ingest.md):
```yaml
- path: <original path>
  source_url: <if present>
  notes: <original notes>
  compiled: 2026-05-16
  wiki_articles:
    - wiki/<path to article created>
```
</interfaces>

<tasks>

<task type="auto">
  <name>Task 1: Ingest the 6 Kafka Streams parent articles (parents #1–#6)</name>
  <files>
    wiki/patterns/kafka-streams-topology-patterns.md,
    wiki/concepts/kafka-streams-debugging.md,
    wiki/concepts/kafka-streams-production-hardening.md,
    wiki/concepts/kafka-streams-schema-patterns.md,
    wiki/concepts/kafka-streams-config-baseline.md,
    wiki/concepts/kafka-streams-architecture.md
  </files>
  <read_first>
    - .planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md (D-03, D-04, D-05 table 1, D-07 source-attestation policy)
    - .claude/commands/wiki/ingest.md (the 6-step skill flow — Steps 3a, 3c, 3e are in scope this task; Step 3d MCP gate is REPLACED by source attestation per D-07 for parents)
    - .claude/commands/wiki/references/article-format.md (concept vs pattern templates)
    - wiki/concepts/schema-registry-best-practices.md (exemplar concept frontmatter — H.1 articles extend this shape; note line 3 `tags: [a, b, c]` comma-separated convention)
    - wiki/patterns/aks-kafka-tuning.md (exemplar pattern frontmatter)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/topology-patterns.md (source for #1)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/debugging.md (source for #2)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/production-hardening.md (source for #3)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/schema-patterns.md (source for #4)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/config-baseline.md (source for #5)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/architecture.md (source for #6)
  </read_first>
  <action>
    Apply the /wiki:ingest flow with D-07 modification: skip Step 3d (MCP gate) for these parent articles; instead, set `confidence: high` and cite source attestation in the body. Process all 6 articles in this task because they share the same source skill (kafka-streams-programming) — single context load.

    **YAML tag-array rule (Issue 1 blocker fix):** Every `tags:` array in every article frontmatter MUST be comma-separated — `tags: [a, b, c]` not `tags: [a b c]`. This matches the existing wiki convention (see `wiki/concepts/schema-registry-best-practices.md` line 3); YAML interprets the space-separated form as a single scalar `"a b c"`, NOT a 3-element list, and downstream tag-based filtering silently breaks. Task 4's verify grep-checks every new article's tags parse as a YAML list.

    Per /wiki:ingest Step 3a: read each vendored source file (paths in <read_first> above).

    Per Step 3c: draft each article using the correct template (per D-05 table 1 column "Type"):

    | # | Vendored source | Target wiki path | Template |
    |---|----------------|------------------|----------|
    | 1 | skills/kafka-streams-programming/references/topology-patterns.md | wiki/patterns/kafka-streams-topology-patterns.md | pattern |
    | 2 | skills/kafka-streams-programming/references/debugging.md | wiki/concepts/kafka-streams-debugging.md | concept |
    | 3 | skills/kafka-streams-programming/references/production-hardening.md | wiki/concepts/kafka-streams-production-hardening.md | concept |
    | 4 | skills/kafka-streams-programming/references/schema-patterns.md | wiki/concepts/kafka-streams-schema-patterns.md | concept |
    | 5 | skills/kafka-streams-programming/references/config-baseline.md | wiki/concepts/kafka-streams-config-baseline.md | concept |
    | 6 | skills/kafka-streams-programming/references/architecture.md | wiki/concepts/kafka-streams-architecture.md | concept |

    For each article, the frontmatter MUST include (locked schema from CONTEXT.md D-03):

    ```yaml
    ---
    title: <Human-readable title>
    tags: [kafka-streams, <topic-specific-tag-1>, <topic-specific-tag-2>, confluent-agent-skills]   # COMMA-separated; see YAML rule above
    sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/<file>.md]
    related: [<2–5 wiki-relative paths, no .md extension required>]
    confidence: high                                # via source attestation per D-07
    last_updated: 2026-05-16
    last_validated: 2026-05-16                      # set to today; D-08 says 90-day decay applies
    source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
    upstream_path: skills/kafka-streams-programming/references/<file>.md
    ---
    ```

    Body: faithfully port the upstream content. Don't rewrite voice — these are peer-reviewed reference articles, preserve their structure. Drop any upstream-specific language that doesn't translate (e.g., references to other `references/` files inside the same skill — re-link them to the wiki articles being created in this same task where applicable, or remove if no wiki target exists yet). Apply our existing concept/pattern template structure: concept = Summary + Detail + Related; pattern = Summary + Pattern + When to Use + Caveats + Related.

    **Source attestation paragraph (D-07)**: in addition to the frontmatter `source:` field and provenance footer, add a brief inline note in the Summary section explaining the source attestation rationale. One sentence, e.g.:

    > Sourced from `confluentinc/agent-skills@91d1871e` (Apache-2.0) — upstream maintains an eval gate at 90%+ pass before merge, so this article is `confidence: high` via source attestation rather than per-claim MCP re-validation. The accompanying trip-wire articles in `wiki/concepts/` carry full MCP validation.

    **Provenance footer** (last paragraph of body, italicized):
    ```markdown
    ---

    *Source: confluentinc/agent-skills@91d1871e · skills/kafka-streams-programming/references/<file>.md · Ingested 2026-05-16 · Apache-2.0*
    ```

    **Cross-links via `related:`** — every article needs ≥1 outbound link. For these 6 KS articles, natural targets (existing wiki):
    - `concepts/exactly-once-semantics` (for #1 topology, #3 production-hardening)
    - `concepts/consumer-group-rebalancing` (for #3 production-hardening, #5 config-baseline)
    - `concepts/flink-checkpointing` (for #6 architecture, conceptual sibling)
    - `concepts/schema-registry-best-practices` (for #4 schema-patterns)
    - `concepts/schema-evolution-strategies` (for #4 schema-patterns)
    - `patterns/producer-config-fsi` (for #5 config-baseline)
    - `patterns/consumer-config-fsi` (for #5 config-baseline)
    - `patterns/fsi-exactly-once` (for #3 production-hardening)
    - `synthesis/confluent-gotchas-top-20` (for #2 debugging — natural cross-pollination)

    Plus forward-references to the trip-wire articles H.1-03 will create — these MUST be listed in `related:` even though the targets don't exist yet (H.1-03 creates them). Specifically:
    - #2 debugging → related: concepts/kafka-streams-4x-uncaught-exception-handler-import, concepts/avro-schema-source-directory, concepts/schema-aware-console-producer-required
    - #3 production-hardening → related: concepts/exactly-once-v2-warpstream-throughput-cost (the WarpStream-EOS trip-wire elaborates a production concern)
    - #5 config-baseline → related: concepts/warpstream-config-overrides

    **Expected wiki-lint forward-reference warnings after this plan completes** (Issue 7 fix — enumerated explicitly so Task 4 allowlist matches them; H.1-03 Task 4 closes them):

    The 9 trip-wire targets that parents' `related:` fields cite. Exactly 9 broken-link findings, one per:
    - concepts/tableflow-changelog-mode-immutability
    - patterns/cdc-tableflow-flink-decode-required
    - concepts/oracle-xstream-source-limitations
    - concepts/kafka-streams-4x-uncaught-exception-handler-import
    - concepts/avro-schema-source-directory
    - concepts/schema-aware-console-producer-required
    - concepts/warpstream-schema-registry-format-constraint
    - concepts/warpstream-config-overrides
    - concepts/exactly-once-v2-warpstream-throughput-cost

    Any OTHER broken-link finding from wiki-lint is a regression and MUST fail Task 4 verify.

    Forward-references will surface as `wiki-lint.py` warnings about missing targets until H.1-03 commits. That's acceptable — H.1-03 closes them.

    **Required tags for each article** (must appear in `tags:` array, COMMA-separated):
    - All 6: `kafka-streams`, `confluent-agent-skills` (the second tag is the discoverability hook for vendored content)
    - #1 topology-patterns: also `topology`, `dsl`, `processor-api`
    - #2 debugging: also `debugging`, `troubleshooting`
    - #3 production-hardening: also `production`, `resilience`, `fsi`
    - #4 schema-patterns: also `schema-registry`, `avro`
    - #5 config-baseline: also `configuration`, `tuning`
    - #6 architecture: also `architecture`, `topology`

    Per Step 3e: write each article to its target path.

    Do NOT update `_index.md`, `_graph.md`, or `raw/_ingest.md` in this task — Tasks 3/4 handle those after all 10 parents are written.
  </action>
  <verify>
    <automated>
      test -f wiki/patterns/kafka-streams-topology-patterns.md &amp;&amp;
      test -f wiki/concepts/kafka-streams-debugging.md &amp;&amp;
      test -f wiki/concepts/kafka-streams-production-hardening.md &amp;&amp;
      test -f wiki/concepts/kafka-streams-schema-patterns.md &amp;&amp;
      test -f wiki/concepts/kafka-streams-config-baseline.md &amp;&amp;
      test -f wiki/concepts/kafka-streams-architecture.md &amp;&amp;
      grep -c "source: confluent-agent-skills@91d1871" wiki/patterns/kafka-streams-topology-patterns.md wiki/concepts/kafka-streams-debugging.md wiki/concepts/kafka-streams-production-hardening.md wiki/concepts/kafka-streams-schema-patterns.md wiki/concepts/kafka-streams-config-baseline.md wiki/concepts/kafka-streams-architecture.md | awk -F: '$2 &lt; 1 { print "FAIL: " $1 " missing source frontmatter"; exit 1 } END { print "OK: all 6 have source: frontmatter" }' &amp;&amp;
      grep -c "confidence: high" wiki/patterns/kafka-streams-topology-patterns.md wiki/concepts/kafka-streams-debugging.md wiki/concepts/kafka-streams-production-hardening.md wiki/concepts/kafka-streams-schema-patterns.md wiki/concepts/kafka-streams-config-baseline.md wiki/concepts/kafka-streams-architecture.md | awk -F: '$2 &lt; 1 { print "FAIL: " $1 " missing confidence: high"; exit 1 } END { print "OK: all 6 confidence: high" }' &amp;&amp;
      grep -c "upstream_path: skills/kafka-streams-programming/references/" wiki/patterns/kafka-streams-topology-patterns.md wiki/concepts/kafka-streams-debugging.md wiki/concepts/kafka-streams-production-hardening.md wiki/concepts/kafka-streams-schema-patterns.md wiki/concepts/kafka-streams-config-baseline.md wiki/concepts/kafka-streams-architecture.md | awk -F: '$2 &lt; 1 { print "FAIL: " $1 " missing upstream_path"; exit 1 } END { print "OK: all 6 have upstream_path" }' &amp;&amp;
      grep -l "Source: confluentinc/agent-skills@91d1871e" wiki/patterns/kafka-streams-topology-patterns.md wiki/concepts/kafka-streams-debugging.md wiki/concepts/kafka-streams-production-hardening.md wiki/concepts/kafka-streams-schema-patterns.md wiki/concepts/kafka-streams-config-baseline.md wiki/concepts/kafka-streams-architecture.md | wc -l | awk '$1 != 6 { print "FAIL: provenance footer count " $1 " != 6"; exit 1 } { print "OK: 6 provenance footers" }'
    </automated>
  </verify>
  <done>
    All 6 Kafka Streams parent articles exist at locked paths, every one has `confidence: high`, `source: confluent-agent-skills@91d1871...`, `upstream_path: skills/kafka-streams-programming/...`, comma-separated `tags:` array, and an italicized provenance footer in the body. No MCP re-validation gate run (per D-07).
  </done>
</task>

<task type="auto">
  <name>Task 2: Ingest the 4 CDC-Tableflow + Schema Registry parent articles (parents #7–#10, includes 3-way and 2-way merges)</name>
  <files>
    wiki/patterns/cdc-to-tableflow-flink-decode.md,
    wiki/concepts/cdc-source-connector-setup.md,
    wiki/patterns/schema-registry-adoption-playbook.md,
    wiki/concepts/schema-inference-and-pii-categorization.md
  </files>
  <read_first>
    - .planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md (D-05 table 1 rows 7–10; Claude's Discretion item on merge ordering; D-07 source attestation)
    - .claude/commands/wiki/references/article-format.md (concept + pattern templates)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/flink-sql-patterns.md (source for #7)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/connector-configs.md (merge input #8)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/database-prerequisites.md (merge input #8)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/troubleshooting.md (merge input #8)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/detection-patterns.md (merge input #9)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/code-migration.md (merge input #9)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/schema-inference.md (merge input #10)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/categorization.md (merge input #10)
    - wiki/concepts/schema-registry-best-practices.md (exemplar — and the natural `related:` neighbor for #9 and #10; note line 3 `tags: [a, b, c]` comma-separated convention)
  </read_first>
  <action>
    Apply the same /wiki:ingest flow as Task 1, with these specifics for the merges.

    **Reminder of the YAML tag-array rule (Issue 1 blocker fix):** all `tags:` arrays MUST be comma-separated — `tags: [a, b, c]` not `tags: [a b c]`. The exemplar `wiki/concepts/schema-registry-best-practices.md` line 3 is the canonical reference. YAML's flow-sequence `[...]` syntax requires commas; without them the array parses as one scalar string. Task 4's verify grep-checks this.

    **Parent #7: cdc-to-tableflow-flink-decode.md (pattern)** — single-source article. Source: `flink-sql-patterns.md`.

    Frontmatter:
    ```yaml
    ---
    title: CDC to Tableflow — Flink Decode Pattern
    tags: [tableflow, cdc, flink, confluent-cloud, iceberg, delta, confluent-agent-skills]
    sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/flink-sql-patterns.md]
    related: [concepts/exactly-once-semantics, concepts/flink-checkpointing, concepts/flink-confluent-cloud-setup, concepts/tableflow-changelog-mode-immutability, patterns/cdc-tableflow-flink-decode-required, concepts/cdc-source-connector-setup]
    confidence: high
    last_updated: 2026-05-16
    last_validated: 2026-05-16
    source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
    upstream_path: skills/confluent-cloud-cdc-tableflow/references/flink-sql-patterns.md
    ---
    ```

    Body: pattern template. Cover the canonical pipeline shape (Debezium source → Kafka raw topic → Flink decode → Kafka clean topic → Tableflow). Surface the trip-wire facts inline-by-reference (don't restate them — `[See: Tableflow changelog mode is immutable](../concepts/tableflow-changelog-mode-immutability.md)` style cross-link). Provenance footer.

    **Parent #8: cdc-source-connector-setup.md (concept) — THREE-WAY MERGE.** Source files (per Claude's Discretion section ordering):

    1. **Section 1 — Database prerequisites** (from `database-prerequisites.md`): port/log mining setup for Oracle, Postgres WAL setup, MySQL binlog setup, supplemental logging requirements
    2. **Section 2 — Connector configuration recipes** (from `connector-configs.md`): per-connector config templates (OracleXStreamSource, PostgresCdcSource, MySqlCdcSource, etc.)
    3. **Section 3 — Troubleshooting** (from `troubleshooting.md`): symptom-to-fix triage table

    Rationale (record in body as a brief one-liner intro paragraph): mirrors operational reading order — pre-deploy → deploy → debug.

    Frontmatter `upstream_path` is a YAML list:
    ```yaml
    upstream_path:
      - skills/confluent-cloud-cdc-tableflow/references/connector-configs.md
      - skills/confluent-cloud-cdc-tableflow/references/database-prerequisites.md
      - skills/confluent-cloud-cdc-tableflow/references/troubleshooting.md
    ```

    Frontmatter `sources` is a YAML list of all three vendored paths. `tags:` MUST be comma-separated, e.g. `tags: [cdc, connect, confluent-cloud, oracle, postgres, mysql, confluent-agent-skills]`.

    Provenance footer lists all three upstream files separated by ` · `:
    ```markdown
    *Source: confluentinc/agent-skills@91d1871e · skills/confluent-cloud-cdc-tableflow/references/{connector-configs,database-prerequisites,troubleshooting}.md · Ingested 2026-05-16 · Apache-2.0*
    ```

    `related:` includes: `patterns/cdc-to-tableflow-flink-decode` (parent #7 — operational counterpart), `patterns/connect-deployment-models` (existing wiki — Connect deployment patterns), `concepts/oracle-xstream-source-limitations` (trip-wire #3 — H.1-03 will create).

    **Parent #9: schema-registry-adoption-playbook.md (pattern) — TWO-WAY MERGE.** Source files:

    1. **Section 1 — Detection patterns** (from `detection-patterns.md`): how to scan an existing codebase for Kafka usage and identify SR-missing surfaces
    2. **Section 2 — Code migration** (from `code-migration.md`): converting raw producers/consumers to SR-aware (Avro/Protobuf serdes), generating Terraform for subject registration

    Pattern template: Summary → Pattern (Detection + Migration as subsections) → When to Use → Caveats → Related.

    Frontmatter:
    ```yaml
    upstream_path:
      - skills/kafka-schema-registry/references/detection-patterns.md
      - skills/kafka-schema-registry/references/code-migration.md
    ```

    `tags:` comma-separated, e.g. `tags: [schema-registry, adoption, migration, terraform, confluent-agent-skills]`.

    `related:`: `concepts/schema-registry-best-practices`, `concepts/schema-evolution-strategies`, `patterns/fsi-governance-automation`, `patterns/schema-registry-shared-types`, `concepts/schema-inference-and-pii-categorization` (parent #10 — natural sibling).

    **Parent #10: schema-inference-and-pii-categorization.md (concept) — TWO-WAY MERGE.** Source files:

    1. **Section 1 — Schema inference** (from `schema-inference.md`): deriving Avro schemas from data samples (JSON → Avro, CSV → Avro)
    2. **Section 2 — Categorization (PII tagging)** (from `categorization.md`): tagging inferred schemas with PII metadata for CSFLE

    Concept template: Summary → Detail (Inference + Categorization as Detail subsections) → Related.

    Frontmatter:
    ```yaml
    upstream_path:
      - skills/kafka-schema-registry/references/schema-inference.md
      - skills/kafka-schema-registry/references/categorization.md
    ```

    `tags:` comma-separated, e.g. `tags: [schema-registry, pii, csfle, fsi, confluent-agent-skills]`.

    `related:`: `concepts/schema-registry-best-practices`, `concepts/fsi-compliance` (PII tagging connects to compliance), `patterns/schema-registry-shared-types`, `patterns/schema-registry-adoption-playbook` (parent #9 — natural sibling).

    For all 4 articles in this task:
    - Same source-attestation Summary paragraph as Task 1
    - Same provenance footer pattern (italicized last paragraph, list all merge inputs)
    - Same forward-references to trip-wire articles that H.1-03 will create
    - `confidence: high`, dates 2026-05-16
    - **All `tags:` arrays comma-separated** (Issue 1 blocker fix)

    Do NOT update `_index.md`, `_graph.md`, or `raw/_ingest.md` in this task — Tasks 3/4 handle.
  </action>
  <verify>
    <automated>
      test -f wiki/patterns/cdc-to-tableflow-flink-decode.md &amp;&amp;
      test -f wiki/concepts/cdc-source-connector-setup.md &amp;&amp;
      test -f wiki/patterns/schema-registry-adoption-playbook.md &amp;&amp;
      test -f wiki/concepts/schema-inference-and-pii-categorization.md &amp;&amp;
      grep -l "source: confluent-agent-skills@91d1871" wiki/patterns/cdc-to-tableflow-flink-decode.md wiki/concepts/cdc-source-connector-setup.md wiki/patterns/schema-registry-adoption-playbook.md wiki/concepts/schema-inference-and-pii-categorization.md | wc -l | awk '$1 != 4 { print "FAIL"; exit 1 } { print "OK: 4 source: fields" }' &amp;&amp;
      grep -q "skills/confluent-cloud-cdc-tableflow/references/connector-configs.md" wiki/concepts/cdc-source-connector-setup.md &amp;&amp;
      grep -q "skills/confluent-cloud-cdc-tableflow/references/database-prerequisites.md" wiki/concepts/cdc-source-connector-setup.md &amp;&amp;
      grep -q "skills/confluent-cloud-cdc-tableflow/references/troubleshooting.md" wiki/concepts/cdc-source-connector-setup.md &amp;&amp;
      grep -q "skills/kafka-schema-registry/references/detection-patterns.md" wiki/patterns/schema-registry-adoption-playbook.md &amp;&amp;
      grep -q "skills/kafka-schema-registry/references/code-migration.md" wiki/patterns/schema-registry-adoption-playbook.md &amp;&amp;
      grep -q "skills/kafka-schema-registry/references/schema-inference.md" wiki/concepts/schema-inference-and-pii-categorization.md &amp;&amp;
      grep -q "skills/kafka-schema-registry/references/categorization.md" wiki/concepts/schema-inference-and-pii-categorization.md &amp;&amp;
      grep -l "Source: confluentinc/agent-skills@91d1871e" wiki/patterns/cdc-to-tableflow-flink-decode.md wiki/concepts/cdc-source-connector-setup.md wiki/patterns/schema-registry-adoption-playbook.md wiki/concepts/schema-inference-and-pii-categorization.md | wc -l | awk '$1 != 4 { print "FAIL"; exit 1 } { print "OK: 4 provenance footers" }'
    </automated>
  </verify>
  <done>
    All 4 articles exist; merged-parent articles (#8, #9, #10) reference every merge-input upstream_path in their body provenance and frontmatter; all 4 have confidence: high, the source: frontmatter field, and comma-separated `tags:` arrays.
  </done>
</task>

<task type="auto">
  <name>Task 3: Update wiki/_index.md and wiki/_graph.md for all 10 parent articles</name>
  <files>wiki/_index.md, wiki/_graph.md</files>
  <read_first>
    - wiki/_index.md (current 37-article index — Concepts and Patterns sections; line format on line 17)
    - wiki/_graph.md (current backlink graph — format on line 13; see existing patterns/aks-kafka-tuning entries for outbound style)
    - .claude/commands/wiki/ingest.md (Steps 4 and 5)
    - .claude/commands/wiki/references/quality-standards.md (backlink requirements section)
  </read_first>
  <action>
    Implements /wiki:ingest Steps 4 and 5 for the 10 parents (Task 1 articles + Task 2 articles).

    **Step 4 — wiki/_index.md:** Append entries under the correct sections (Concepts or Patterns). Use this exact format (per line 17 of _index.md):

    ```
    [<Title>](<path>) — <one-line summary> — #tag1 #tag2
    ```

    Append the 3 patterns (under `## Patterns`):
    ```
    [Kafka Streams Topology Patterns](patterns/kafka-streams-topology-patterns.md) — Canonical KS DSL/Processor-API topology shapes with stateful operator and rebalance considerations — #kafka-streams #topology #dsl #confluent-agent-skills
    [CDC to Tableflow — Flink Decode Pattern](patterns/cdc-to-tableflow-flink-decode.md) — Debezium source → Kafka raw → Flink decode → clean topic → Tableflow; avoids tombstone-breaks-APPEND failure mode — #tableflow #cdc #flink #confluent-cloud #confluent-agent-skills
    [Schema Registry Adoption Playbook](patterns/schema-registry-adoption-playbook.md) — Detection patterns for SR-missing surfaces + code migration recipe (raw → Avro/Protobuf serdes) — #schema-registry #adoption #migration #confluent-agent-skills
    ```

    Append the 7 concepts (under `## Concepts`) — parents #2, #3, #4, #5, #6, #8, #10 are concepts:
    ```
    [Kafka Streams Debugging](concepts/kafka-streams-debugging.md) — Diagnostic workflow for KS apps: state-store corruption, repartition explosions, rebalance loops, exception-handler routing — #kafka-streams #debugging #troubleshooting #confluent-agent-skills
    [Kafka Streams Production Hardening](concepts/kafka-streams-production-hardening.md) — Production checklist for KS: EOS configuration, deployment topology, idempotence, dead-letter routing, monitoring — #kafka-streams #production #fsi #confluent-agent-skills
    [Kafka Streams Schema Patterns](concepts/kafka-streams-schema-patterns.md) — SR-aware serdes, Avro vs Protobuf decision, schema-evolution friendly state stores — #kafka-streams #schema-registry #avro #confluent-agent-skills
    [Kafka Streams Config Baseline](concepts/kafka-streams-config-baseline.md) — Recommended StreamsConfig values for production: parallelism, EOS, error handling, RocksDB tuning — #kafka-streams #configuration #tuning #confluent-agent-skills
    [Kafka Streams Architecture](concepts/kafka-streams-architecture.md) — Topology graph model, task partitioning, state store semantics, processor lifecycle — #kafka-streams #architecture #confluent-agent-skills
    [CDC Source Connector Setup](concepts/cdc-source-connector-setup.md) — Database prerequisites + connector configs + troubleshooting for Oracle XStream, Postgres CDC, MySQL CDC — #cdc #connect #confluent-cloud #confluent-agent-skills
    [Schema Inference and PII Categorization](concepts/schema-inference-and-pii-categorization.md) — Deriving Avro schemas from data samples + PII tagging for CSFLE — #schema-registry #pii #csfle #fsi #confluent-agent-skills
    ```

    Insert these in alphabetical order within each section to keep the index navigable. Bump `last_updated:` in the `_index.md` frontmatter to `2026-05-16`.

    **Step 5 — wiki/_graph.md:** Add backlinks for all 10 new articles. Every article needs ≥1 inbound + ≥1 outbound. Use the `source → target : relationship` format (see line 18 of _graph.md for the exact convention).

    Add the following backlink block at the end of the file under a comment header `## H.1 — confluent-agent-skills ingest (2026-05-16)`:

    ```
    ## H.1 — confluent-agent-skills ingest (2026-05-16)

    # Parent #1: kafka-streams-topology-patterns — outbound
    patterns/kafka-streams-topology-patterns → concepts/exactly-once-semantics : EOS implications for stateful topologies
    patterns/kafka-streams-topology-patterns → concepts/consumer-group-rebalancing : rebalance behavior under stateful operators
    patterns/kafka-streams-topology-patterns → concepts/kafka-streams-architecture : architecture context for topology choices
    patterns/kafka-streams-topology-patterns → concepts/kafka-streams-debugging : debugging stateful topologies

    # Parent #2: kafka-streams-debugging — outbound
    concepts/kafka-streams-debugging → concepts/kafka-streams-production-hardening : production diagnostics complement
    concepts/kafka-streams-debugging → concepts/kafka-streams-4x-uncaught-exception-handler-import : trip-wire on KS 4.x import
    concepts/kafka-streams-debugging → concepts/avro-schema-source-directory : trip-wire on Avro source dir
    concepts/kafka-streams-debugging → concepts/schema-aware-console-producer-required : trip-wire on console-producer verification
    concepts/kafka-streams-debugging → synthesis/confluent-gotchas-top-20 : cross-pollination with gotchas index

    # Parent #3: kafka-streams-production-hardening — outbound
    concepts/kafka-streams-production-hardening → concepts/exactly-once-semantics : EOS production posture
    concepts/kafka-streams-production-hardening → patterns/fsi-exactly-once : FSI five-layer EOS pattern
    concepts/kafka-streams-production-hardening → concepts/exactly-once-v2-warpstream-throughput-cost : trip-wire on EOS cost on WarpStream
    concepts/kafka-streams-production-hardening → concepts/kafka-streams-debugging : debugging counterpart
    concepts/kafka-streams-production-hardening → patterns/producer-config-fsi : producer-layer config baseline

    # Parent #4: kafka-streams-schema-patterns — outbound
    concepts/kafka-streams-schema-patterns → concepts/schema-registry-best-practices : SR operational surface
    concepts/kafka-streams-schema-patterns → concepts/schema-evolution-strategies : compatibility policy
    concepts/kafka-streams-schema-patterns → patterns/schema-registry-shared-types : shared-types library pattern
    concepts/kafka-streams-schema-patterns → concepts/avro-schema-source-directory : trip-wire on Avro source dir

    # Parent #5: kafka-streams-config-baseline — outbound
    concepts/kafka-streams-config-baseline → patterns/producer-config-fsi : producer baseline pairing
    concepts/kafka-streams-config-baseline → patterns/consumer-config-fsi : consumer baseline pairing
    concepts/kafka-streams-config-baseline → concepts/warpstream-config-overrides : trip-wire on WarpStream config drift
    concepts/kafka-streams-config-baseline → concepts/kafka-streams-architecture : architectural rationale for defaults

    # Parent #6: kafka-streams-architecture — outbound
    concepts/kafka-streams-architecture → concepts/exactly-once-semantics : EOS in stream processing
    concepts/kafka-streams-architecture → concepts/flink-checkpointing : alternative streaming runtime context
    concepts/kafka-streams-architecture → patterns/flink-runtime-models : Flink vs Kafka Streams runtime trade-offs
    concepts/kafka-streams-architecture → concepts/fsi-data-streaming-platform : platform context

    # Parent #7: cdc-to-tableflow-flink-decode — outbound
    patterns/cdc-to-tableflow-flink-decode → concepts/tableflow-changelog-mode-immutability : trip-wire on Tableflow immutability
    patterns/cdc-to-tableflow-flink-decode → patterns/cdc-tableflow-flink-decode-required : trip-wire elaborating decode requirement
    patterns/cdc-to-tableflow-flink-decode → concepts/cdc-source-connector-setup : pre-pipeline connector setup
    patterns/cdc-to-tableflow-flink-decode → concepts/flink-checkpointing : checkpointing for the Flink decode step
    patterns/cdc-to-tableflow-flink-decode → concepts/flink-confluent-cloud-setup : CC Flink setup context
    patterns/cdc-to-tableflow-flink-decode → concepts/exactly-once-semantics : EOS across the pipeline

    # Parent #8: cdc-source-connector-setup — outbound
    concepts/cdc-source-connector-setup → patterns/cdc-to-tableflow-flink-decode : operational counterpart pattern
    concepts/cdc-source-connector-setup → concepts/oracle-xstream-source-limitations : trip-wire on after.state.only
    concepts/cdc-source-connector-setup → patterns/connect-deployment-models : Connect deployment patterns

    # Parent #9: schema-registry-adoption-playbook — outbound
    patterns/schema-registry-adoption-playbook → concepts/schema-registry-best-practices : operational surface for SR
    patterns/schema-registry-adoption-playbook → concepts/schema-evolution-strategies : compatibility policy
    patterns/schema-registry-adoption-playbook → patterns/fsi-governance-automation : Terraform enforcement of registered subjects
    patterns/schema-registry-adoption-playbook → patterns/schema-registry-shared-types : shared-types library
    patterns/schema-registry-adoption-playbook → concepts/schema-inference-and-pii-categorization : inference + PII tagging sibling

    # Parent #10: schema-inference-and-pii-categorization — outbound
    concepts/schema-inference-and-pii-categorization → concepts/schema-registry-best-practices : SR operational surface
    concepts/schema-inference-and-pii-categorization → concepts/fsi-compliance : PII categorization connects to compliance
    concepts/schema-inference-and-pii-categorization → patterns/schema-registry-shared-types : shared types include PII-tagged fields
    concepts/schema-inference-and-pii-categorization → patterns/schema-registry-adoption-playbook : adoption playbook sibling

    # Inbound (existing wiki → new H.1 articles) — backfill so every new article has ≥1 inbound
    concepts/exactly-once-semantics → concepts/kafka-streams-production-hardening : EOS production application
    concepts/exactly-once-semantics → concepts/kafka-streams-architecture : EOS in stream processing
    concepts/schema-registry-best-practices → concepts/kafka-streams-schema-patterns : KS-specific schema patterns
    concepts/schema-registry-best-practices → patterns/schema-registry-adoption-playbook : adoption playbook for SR
    concepts/schema-registry-best-practices → concepts/schema-inference-and-pii-categorization : inference + PII categorization
    patterns/connect-deployment-models → concepts/cdc-source-connector-setup : CDC source connector deployment specifics
    concepts/flink-checkpointing → patterns/cdc-to-tableflow-flink-decode : checkpointing in the CDC decode pipeline
    patterns/producer-config-fsi → concepts/kafka-streams-config-baseline : KS-specific config baseline
    patterns/consumer-config-fsi → concepts/kafka-streams-config-baseline : KS-specific config baseline
    synthesis/confluent-gotchas-top-20 → concepts/kafka-streams-debugging : debugging-focused gotchas
    ```

    Bump `last_updated:` in `_graph.md` frontmatter to `2026-05-16`.

    **Verify each new article has ≥1 inbound + ≥1 outbound** by counting graph entries — every article path appears on at least one LHS (outbound) and at least one RHS (inbound) of `→`.
  </action>
  <verify>
    <automated>
      grep -c "patterns/kafka-streams-topology-patterns.md\|concepts/kafka-streams-debugging.md\|concepts/kafka-streams-production-hardening.md\|concepts/kafka-streams-schema-patterns.md\|concepts/kafka-streams-config-baseline.md\|concepts/kafka-streams-architecture.md\|patterns/cdc-to-tableflow-flink-decode.md\|concepts/cdc-source-connector-setup.md\|patterns/schema-registry-adoption-playbook.md\|concepts/schema-inference-and-pii-categorization.md" wiki/_index.md | awk '{ if ($1 &lt; 10) { print "FAIL: expected 10 _index.md entries, got " $1; exit 1 } else print "OK: " $1 " _index.md entries" }' &amp;&amp;
      grep -q "H.1 — confluent-agent-skills ingest" wiki/_graph.md &amp;&amp;
      for art in patterns/kafka-streams-topology-patterns concepts/kafka-streams-debugging concepts/kafka-streams-production-hardening concepts/kafka-streams-schema-patterns concepts/kafka-streams-config-baseline concepts/kafka-streams-architecture patterns/cdc-to-tableflow-flink-decode concepts/cdc-source-connector-setup patterns/schema-registry-adoption-playbook concepts/schema-inference-and-pii-categorization; do
        outbound=$(grep -cE "^${art} →" wiki/_graph.md)
        inbound=$(grep -cE "→ ${art}( |$)" wiki/_graph.md)
        if [ "$outbound" -lt 1 ] || [ "$inbound" -lt 1 ]; then
          echo "FAIL: $art outbound=$outbound inbound=$inbound (need ≥1 each)"
          exit 1
        fi
      done &amp;&amp; echo "OK: all 10 articles have ≥1 inbound and ≥1 outbound in _graph.md"
    </automated>
  </verify>
  <done>
    `_index.md` lists all 10 new parents under correct sections; `_graph.md` H.1 block contains both outbound and inbound edges for each of the 10 articles (≥1 inbound + ≥1 outbound proven by automated check).
  </done>
</task>

<task type="auto">
  <name>Task 4: Move 10 parent entries from raw/_ingest.md Pending to Processed; assert tag-array YAML shape; run scoped wiki-lint</name>
  <files>raw/_ingest.md</files>
  <read_first>
    - raw/_ingest.md (current state — H.1-01 added 19 Pending entries; the 10 parents are the first 10 of those 19)
    - .claude/commands/wiki/ingest.md (Step 6 — Processed entry shape; Step 7 — run wiki-lint)
  </read_first>
  <action>
    Implements /wiki:ingest Steps 6 and 7 for the parent articles.

    **Step 6 — Move 10 parent entries from `## Pending` to `## Processed`** in `raw/_ingest.md`. For each of the 10 parent entries (those whose `notes:` start with `Parent article #N`):

    1. Remove from `## Pending`
    2. Append to `## Processed` with these added fields:
       - `compiled: 2026-05-16`
       - `wiki_articles:` (YAML list) containing the wiki path(s) created

    Example processed entry shape (mirror existing entries in lines 30+ of raw/_ingest.md):

    ```yaml
    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/topology-patterns.md
      added: 2026-05-16
      notes: |
        Parent article #1 of 10 (H.1). Target: wiki/patterns/kafka-streams-topology-patterns.md (pattern template).
        [...preserve full original notes...]
      compiled: 2026-05-16
      wiki_articles:
        - wiki/patterns/kafka-streams-topology-patterns.md
    ```

    For the merged parents (#8, #9, #10), `wiki_articles:` is still a single-item list (one wiki file per parent, even though multiple upstream files merged in). The merge inputs are recorded in the article's frontmatter `upstream_path:` list and provenance footer — no need to duplicate here.

    Preserve the original `notes:` block verbatim under each entry — don't rewrite, just append the new fields.

    The 9 trip-wire entries STAY in `## Pending` — H.1-03 will process them.

    **Step 7a — Assert tag-array YAML parse (Issue 1 blocker fix):** every new article's `tags:` field MUST parse as a YAML list. If a `tags: [a b c]` slipped in instead of `tags: [a, b, c]`, this catches it before wiki-lint runs (because wiki-lint may not surface tag-shape issues directly):

    ```bash
    python3 -c "
    import yaml, glob, sys
    articles = (
        glob.glob('wiki/concepts/kafka-streams-*.md')
        + glob.glob('wiki/patterns/kafka-streams-*.md')
        + ['wiki/patterns/cdc-to-tableflow-flink-decode.md',
           'wiki/concepts/cdc-source-connector-setup.md',
           'wiki/patterns/schema-registry-adoption-playbook.md',
           'wiki/concepts/schema-inference-and-pii-categorization.md']
    )
    fail = 0
    for path in sorted(set(articles)):
        try:
            content = open(path).read()
        except FileNotFoundError:
            continue
        if '---' not in content:
            continue
        try:
            fm = yaml.safe_load(content.split('---')[1])
        except yaml.YAMLError as exc:
            print(f'FAIL: {path}: YAML parse error: {exc}'); fail += 1; continue
        tags = fm.get('tags')
        if not isinstance(tags, list):
            print(f'FAIL: {path}: tags is not a YAML list (got {type(tags).__name__}: {tags!r}) — did you forget commas in [a, b, c]?'); fail += 1
            continue
        if len(tags) < 2:
            print(f'FAIL: {path}: tags list too short ({len(tags)} entries)'); fail += 1
            continue
    if fail:
        sys.exit(1)
    print('OK: all new H.1-02 parent articles have YAML-list tag arrays')
    "
    ```

    **Step 7b — Scoped wiki-lint run (Issue 2 major fix):** the original verify ran `python tools/wiki-lint.py; echo "$?"` which swallows the exit code. Replace with an allowlist regex that filters the 9 EXPECTED forward-reference warnings (closed in H.1-03) and fails on anything else:

    ```bash
    python tools/wiki-lint.py > /tmp/h1-02-wl.out 2>&1
    rc=$?
    # The 9 trip-wire targets parents' `related:` fields cite forward to.
    # H.1-03 authors these; until then wiki-lint warns about them. Allowlist them; anything else is a regression.
    EXPECTED_FORWARD_REFS='tableflow-changelog-mode-immutability|cdc-tableflow-flink-decode-required|oracle-xstream-source-limitations|kafka-streams-4x-uncaught-exception-handler-import|avro-schema-source-directory|schema-aware-console-producer-required|warpstream-schema-registry-format-constraint|warpstream-config-overrides|exactly-once-v2-warpstream-throughput-cost'
    # Strip the expected forward-ref lines from output; anything matching BROKEN|ORPHAN|SCHEMA|MALFORMED|UNKNOWN VENDOR|DRIFT is a regression.
    if grep -vE "$EXPECTED_FORWARD_REFS" /tmp/h1-02-wl.out | grep -qE 'BROKEN|ORPHAN|SCHEMA|MALFORMED|UNKNOWN VENDOR|DRIFT'; then
      echo "FAIL: unexpected wiki-lint finding (not in expected forward-ref allowlist):"
      cat /tmp/h1-02-wl.out
      exit 1
    fi
    echo "OK: wiki-lint has only the expected 9 forward-ref warnings (closed in H.1-03 Task 4); exit code was $rc"
    ```

    If wiki-lint flags `last_validated` decay (none of these articles should — all set to 2026-05-16), that's a date-handling bug to fix.
  </action>
  <verify>
    <automated>
      grep -c "Parent article #" raw/_ingest.md | awk '{ print "Parent article # mentions in file: " $1 }' &amp;&amp;
      # The 10 parent entries should now appear ONLY in Processed (after the "## Processed" line) — count occurrences of "Parent article #" in each section
      awk '/^## Pending/{in_pending=1; in_proc=0} /^## Processed/{in_pending=0; in_proc=1} /Parent article #/{ if(in_pending) p++; if(in_proc) q++ } END{ if (p != 0) { print "FAIL: " p " parent entries still in Pending"; exit 1 } if (q != 10) { print "FAIL: " q " parent entries in Processed, expected 10"; exit 1 } print "OK: 0 parents in Pending, 10 parents in Processed" }' raw/_ingest.md &amp;&amp;
      awk '/^## Pending/{in_pending=1; in_proc=0} /^## Processed/{in_pending=0; in_proc=1} /Trip-wire #/{ if(in_pending) t++ } END{ if (t != 9) { print "FAIL: " t " trip-wires in Pending, expected 9 (unchanged from H.1-01)"; exit 1 } print "OK: 9 trip-wires still in Pending" }' raw/_ingest.md &amp;&amp;
      grep -c "compiled: 2026-05-16" raw/_ingest.md | awk '{ if ($1 &lt; 10) { print "FAIL: expected ≥10 compiled: 2026-05-16, got " $1; exit 1 } else print "OK: " $1 " compiled markers" }' &amp;&amp;
      python3 -c "
import yaml, glob, sys
articles = (
    glob.glob('wiki/concepts/kafka-streams-*.md')
    + glob.glob('wiki/patterns/kafka-streams-*.md')
    + ['wiki/patterns/cdc-to-tableflow-flink-decode.md',
       'wiki/concepts/cdc-source-connector-setup.md',
       'wiki/patterns/schema-registry-adoption-playbook.md',
       'wiki/concepts/schema-inference-and-pii-categorization.md']
)
fail = 0
for path in sorted(set(articles)):
    try:
        content = open(path).read()
    except FileNotFoundError:
        continue
    if '---' not in content:
        continue
    try:
        fm = yaml.safe_load(content.split('---')[1])
    except yaml.YAMLError as exc:
        print(f'FAIL: {path}: YAML parse error: {exc}'); fail += 1; continue
    tags = fm.get('tags')
    if not isinstance(tags, list):
        print(f'FAIL: {path}: tags is not a YAML list (got {type(tags).__name__}: {tags!r}) — did you forget commas?'); fail += 1
        continue
    if len(tags) &lt; 2:
        print(f'FAIL: {path}: tags list too short ({len(tags)} entries)'); fail += 1
if fail: sys.exit(1)
print('OK: all H.1-02 parent articles have YAML-list tag arrays')
" &amp;&amp;
      python tools/wiki-lint.py > /tmp/h1-02-wl.out 2>&amp;1; rc=$?;
      EXPECTED_FORWARD_REFS='tableflow-changelog-mode-immutability|cdc-tableflow-flink-decode-required|oracle-xstream-source-limitations|kafka-streams-4x-uncaught-exception-handler-import|avro-schema-source-directory|schema-aware-console-producer-required|warpstream-schema-registry-format-constraint|warpstream-config-overrides|exactly-once-v2-warpstream-throughput-cost';
      if grep -vE "$EXPECTED_FORWARD_REFS" /tmp/h1-02-wl.out | grep -qE 'BROKEN|ORPHAN|SCHEMA|MALFORMED|UNKNOWN VENDOR|DRIFT'; then echo "FAIL: unexpected wiki-lint finding:"; cat /tmp/h1-02-wl.out; exit 1; fi;
      echo "OK: wiki-lint shows only the 9 expected forward-ref warnings; exit code was $rc"
    </automated>
  </verify>
  <done>
    All 10 parent entries moved from Pending to Processed with `compiled: 2026-05-16` and `wiki_articles:` populated; 9 trip-wires remain in Pending; every new parent article's `tags:` parses as a YAML list (Issue 1 fix); wiki-lint produces ONLY the 9 expected forward-reference warnings (Issue 2 fix — non-zero exit no longer swallowed).
  </done>
</task>

</tasks>

<verification>
After all 4 tasks:

1. 10 new wiki articles exist with the locked frontmatter shape (comma-separated tag arrays) and provenance footer.
2. `wiki/_index.md` lists all 10 under correct sections.
3. `wiki/_graph.md` has ≥1 inbound + ≥1 outbound for each new article.
4. `raw/_ingest.md`: 10 parents in Processed; 9 trip-wires in Pending.
5. Every new article's `tags:` field parses as a YAML list (Issue 1 fix — verified by Task 4's pyyaml check).
6. `python tools/wiki-lint.py` produces ONLY the 9 expected forward-reference warnings to unauthored trip-wires (Issue 2 fix — allowlist regex filters them; anything else fails the verify).

**Partial WIKI-08 coverage (Issue 5 fix):** This plan updates `wiki/_index.md` and `wiki/_graph.md` (parts 2 and 3 of WIKI-08) but leaves the expected forward-reference warnings for the 9 trip-wires not yet authored (part 1 — `/wiki:validate` zero drift findings). H.1-03 closes part 1 by authoring the trip-wires and running the final clean lint pass. WIKI-08 is therefore NOT listed in this plan's `requirements_addressed` — it lives only in H.1-03's frontmatter to keep ownership of completion unambiguous.

Roll-up verification:
```bash
test $(ls wiki/patterns/kafka-streams-topology-patterns.md wiki/concepts/kafka-streams-debugging.md wiki/concepts/kafka-streams-production-hardening.md wiki/concepts/kafka-streams-schema-patterns.md wiki/concepts/kafka-streams-config-baseline.md wiki/concepts/kafka-streams-architecture.md wiki/patterns/cdc-to-tableflow-flink-decode.md wiki/concepts/cdc-source-connector-setup.md wiki/patterns/schema-registry-adoption-playbook.md wiki/concepts/schema-inference-and-pii-categorization.md 2>/dev/null | wc -l) -eq 10 &&
grep -c "source: confluent-agent-skills@91d1871" wiki/concepts/*.md wiki/patterns/*.md | grep -c ":1" | awk '{ if ($1 >= 10) print "OK: " $1 " articles with source: field"; else { print "FAIL"; exit 1 } }'
```
</verification>

<success_criteria>
- 10 parent articles exist at locked paths from CONTEXT.md D-05 table 1
- Every parent has `confidence: high` via source attestation, extended frontmatter (`source`, `upstream_path`), comma-separated `tags:` array, and italicized provenance footer
- Merged-parent articles (#8, #9, #10) list all merge-input upstream_paths in frontmatter and footer
- `wiki/_index.md` has all 10 entries in correct sections
- `wiki/_graph.md` has ≥1 inbound + ≥1 outbound per new article
- `raw/_ingest.md` shows 10 parents Processed, 9 trip-wires still Pending
- Every new parent article's `tags:` parses as a YAML list (verified by yaml.safe_load)
- `python tools/wiki-lint.py` produces ONLY the 9 expected forward-reference warnings; any other BROKEN/ORPHAN/SCHEMA/MALFORMED/UNKNOWN VENDOR/DRIFT finding fails Task 4
- WIKI-06 ≥10 articles: SATISFIED
- WIKI-08: NOT claimed here (Issue 5 fix — H.1-03 owns full WIKI-08 coverage)
</success_criteria>

<output>
After completion, create `.planning/phases/H.1-wiki-ingest-agent-skills/H.1-02-SUMMARY.md` capturing:
- Final 10 article paths (verbatim)
- Any merge-ordering decisions that deviated from the recommended "operational reading order" (pre-deploy → deploy → debug)
- Forward-reference warnings from wiki-lint (expected: exactly 9 — one per missing trip-wire; allowlist regex matched them)
- Total inbound + outbound edges added to `_graph.md`
- Any upstream content that didn't map cleanly to our concept/pattern templates (so H.1-03 doesn't repeat the friction)
- Confirmation that every parent article's `tags:` parses as a YAML list (Issue 1 verification)
</output>
</content>
</invoke>