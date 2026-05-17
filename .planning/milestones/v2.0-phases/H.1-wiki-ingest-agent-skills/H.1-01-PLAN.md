---
phase: H.1-wiki-ingest-agent-skills
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tools/vendor-sources.json
  - raw/_ingest.md
  - raw/vendor/confluent-agent-skills/91d1871e/
autonomous: true
requirements: [WIKI-06]
requirements_addressed: [WIKI-06]
must_haves:
  truths:
    - "Vendored snapshot of confluent-agent-skills@91d1871e exists on disk under raw/vendor/confluent-agent-skills/91d1871e/ and contains exactly the four skills' references/ + SKILL.md files (per D-01, D-02)"
    - "tools/vendor-sources.json exists with the schema from CONTEXT.md <specifics> and is forward-compatible with H.3b (kind: claude-plugin entry shape preserved)"
    - "raw/_ingest.md ## Pending section contains 19 new entries (10 parent articles + 9 trip-wires) pointing at vendored paths (per D-12)"
  artifacts:
    - path: "tools/vendor-sources.json"
      provides: "Vendor pin registry; single source of truth for SHA used by /wiki:validate drift check (D-09)"
      contains: "confluent-agent-skills key with commit field == 91d1871ef8c320be92bca955c8e42492a2778cb4"
    - path: "raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/topology-patterns.md"
      provides: "Sentinel file proving vendor copy succeeded; one of 26 ref files present"
    - path: "raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/SKILL.md"
      provides: "SKILL.md for KS skill — source for trip-wires #1, #2, #3"
    - path: "raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/SKILL.md"
      provides: "SKILL.md for CDC-Tableflow — source for trip-wires #1, #2, #3 about Tableflow"
    - path: "raw/vendor/confluent-agent-skills/91d1871e/skills/developing-kafka-python-client/SKILL.md"
      provides: "SKILL.md for python-client — source for WarpStream trip-wire #7"
    - path: "raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/SKILL.md"
      provides: "SKILL.md for SR skill — referenced by parent articles #9, #10"
    - path: "raw/_ingest.md"
      provides: "Ingest queue populated for H.1-02 and H.1-03 to consume; 19 new ## Pending entries (D-12)"
  key_links:
    - from: "tools/vendor-sources.json"
      to: "raw/vendor/confluent-agent-skills/91d1871e/"
      via: "vendor_path field"
      pattern: "vendor_path.*91d1871e"
    - from: "raw/_ingest.md"
      to: "raw/vendor/confluent-agent-skills/91d1871e/skills/*/references/*.md"
      via: "path: field in each pending entry"
      pattern: "path: raw/vendor/confluent-agent-skills/91d1871e"
---

<objective>
Lay the H.1 foundation: vendor the upstream content at pinned commit `91d1871ef8c320be92bca955c8e42492a2778cb4`, author the new `tools/vendor-sources.json` pin registry, and populate `raw/_ingest.md` with all 19 ingest queue entries (10 parent + 9 trip-wires). This plan is pure setup — no wiki articles authored, no MCP validation. The next two plans consume the artifacts produced here.

Purpose: Decouple vendor acquisition (mechanical, deterministic) from wiki authoring (judgment, validation). Mirrors the G.2c generator-as-single-source-of-truth pattern — once this plan ships, the SHA is the only knob; bumping it is a single-PR action.

Output: A vendored content tree, a JSON pin registry, and an ingest queue ready for /wiki:ingest to process.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md
@raw/_ingest.md
</context>

<interfaces>
<!-- The vendor-sources.json schema is locked verbatim in CONTEXT.md <specifics>. Reproduced here so the executor does not need to scavenge: -->

`tools/vendor-sources.json` shape:
```json
{
  "confluent-agent-skills": {
    "upstream": "https://github.com/confluentinc/agent-skills",
    "commit": "91d1871ef8c320be92bca955c8e42492a2778cb4",
    "ingested_at": "2026-05-16",
    "vendor_path": "raw/vendor/confluent-agent-skills/91d1871e/",
    "license": "Apache-2.0",
    "kind": "wiki-source"
  }
}
```

Note: H.3b will add a second top-level key `streaming-skills-plugin` with `kind: claude-plugin`. Schema must accommodate that without rework — keep `kind` as a free-form string field.

`raw/_ingest.md` pending entry format (existing convention, see raw/_ingest.md head):
```yaml
- path: <source path>
  source_url: <optional>
  added: YYYY-MM-DD
  notes: <ingest hints for /wiki:ingest>
```

The 10 parent articles + 9 trip-wires inventory is locked in CONTEXT.md D-05 tables. Each pending entry must reference the vendored path under `raw/vendor/confluent-agent-skills/91d1871e/` and include a `notes:` block telling /wiki:ingest the target wiki path and (for parents) whether this is a multi-file merge.
</interfaces>

<tasks>

<task type="auto">
  <name>Task 1: Clone confluent-agent-skills at pinned SHA and vendor the four skills' content</name>
  <files>raw/vendor/confluent-agent-skills/91d1871e/</files>
  <read_first>
    - .planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md (D-01, D-02, canonical_refs section — vendor mechanics locked)
    - .gitignore (verify raw/vendor/ is NOT ignored — D-decision recommendation in code_context says track in repo so `git log` shows SHA bumps; if ignored, that's a finding)
  </read_first>
  <action>
    Implements D-01 and D-02 (vendor at pinned SHA via shallow clone, not submodule).

    Steps:

    1. Create temp clone directory and clone `confluentinc/agent-skills` at exact SHA:
       ```bash
       TMPDIR=$(mktemp -d)
       git clone --depth=1 https://github.com/confluentinc/agent-skills.git "$TMPDIR/agent-skills"
       cd "$TMPDIR/agent-skills"
       # Convert shallow → full enough to checkout SHA; if --depth=1 doesn't have the SHA, fetch it explicitly:
       git fetch --depth=1 origin 91d1871ef8c320be92bca955c8e42492a2778cb4
       git checkout 91d1871ef8c320be92bca955c8e42492a2778cb4
       cd -
       ```
       If the SHA is not the HEAD of main and `--depth=1` won't reach it, fall back to a full clone, then checkout the SHA. The objective is: working tree at exactly `91d1871ef8c320be92bca955c8e42492a2778cb4`.

    2. Create the vendor directory tree under the cflt-ai repo:
       ```bash
       mkdir -p raw/vendor/confluent-agent-skills/91d1871e/skills
       ```

    3. Copy each of the four skills' `references/` directories AND `SKILL.md` files (per D-02 — references dirs + the four SKILL.md files, nothing else — no evals/, no scripts/, no project scaffolds):
       ```bash
       VPATH=raw/vendor/confluent-agent-skills/91d1871e/skills
       for skill in kafka-streams-programming developing-kafka-python-client kafka-schema-registry confluent-cloud-cdc-tableflow; do
         mkdir -p "$VPATH/$skill"
         cp -r "$TMPDIR/agent-skills/skills/$skill/references" "$VPATH/$skill/references"
         cp "$TMPDIR/agent-skills/skills/$skill/SKILL.md" "$VPATH/$skill/SKILL.md"
       done
       ```

    4. Drop a small `raw/vendor/confluent-agent-skills/91d1871e/PROVENANCE.md` capturing: upstream URL, commit SHA, ingested date (today: 2026-05-16), license (Apache-2.0), and the four skill names included. One-paragraph file, ≤15 lines. Body template:
       ```markdown
       # Vendored: confluent-agent-skills @ 91d1871e

       - **Upstream:** https://github.com/confluentinc/agent-skills
       - **Commit:** 91d1871ef8c320be92bca955c8e42492a2778cb4
       - **Ingested:** 2026-05-16
       - **License:** Apache-2.0
       - **Skills included:** kafka-streams-programming, developing-kafka-python-client, kafka-schema-registry, confluent-cloud-cdc-tableflow

       Each skill subdirectory contains the upstream `SKILL.md` and the entire `references/` tree. Other upstream artifacts (`evals/`, `scripts/`, project-scaffold templates) are intentionally omitted — see `.planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md` D-02 and <specifics> "Anti-references" for rationale.

       To re-ingest at a new SHA: bump `commit` in `tools/vendor-sources.json`, delete this vendor tree, re-clone at new SHA, re-run `/wiki:ingest` on affected articles, re-run `/wiki:validate`.
       ```

    5. Verify `.gitignore` does NOT exclude `raw/vendor/` (per code_context recommendation — track in repo so `git log` shows when SHA changed). If it does, that's an explicit finding to surface in the summary; do NOT modify .gitignore in this task without confirming the intent.

    6. Clean up temp clone: `rm -rf "$TMPDIR"`.

    Do NOT copy any of these (anti-references from CONTEXT.md <specifics>):
    - `evals/evals.json` files (H.2 will handle separately if needed)
    - Project-scaffold templates inside any skill's references/: `readme-template.md`, `terraform-templates.md`, `report-template.md`, `cli-commands.md`, `docker-compose.md`, `verification.md`, `build-templates.md`
    - But: the four `*-optimization.md` files (warpstream-optimization.md etc.) ARE in scope as source material for trip-wires #7, #8, #9 — leave them in place under references/.

    The wholesale `cp -r references` in step 3 will pull in those scaffold templates. After copying, prune them. **Use a single shell variable as source-of-truth for the scaffold-template list** so the prune action and the verify can't drift apart (Issue 3/8 fix):
    ```bash
    # Single source of truth for the scaffold-template predicate list.
    # Used by BOTH the prune action below AND the verify block at end of task.
    SCAFFOLDS='-name readme-template.md -o -name terraform-templates.md -o -name report-template.md -o -name cli-commands.md -o -name docker-compose.md -o -name verification.md -o -name build-templates.md'
    find "$VPATH" -type f \( $SCAFFOLDS \) -delete
    ```

    Note: the `\( ... \)` paren grouping is REQUIRED. Without it, `find` is left-associative and only the LAST `-name` predicate gets the implicit `-print` (or `-delete`) action — the other six are silently no-ops. This bit us in the original draft; the parens are load-bearing.
  </action>
  <verify>
    <automated>
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/SKILL.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/topology-patterns.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/debugging.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/production-hardening.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/schema-patterns.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/config-baseline.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/architecture.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/warpstream-optimization.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/SKILL.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/flink-sql-patterns.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/connector-configs.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/database-prerequisites.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/troubleshooting.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/SKILL.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/detection-patterns.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/code-migration.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/schema-inference.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/categorization.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/skills/developing-kafka-python-client/SKILL.md &amp;&amp;
      test -f raw/vendor/confluent-agent-skills/91d1871e/PROVENANCE.md &amp;&amp;
      SCAFFOLDS='-name readme-template.md -o -name terraform-templates.md -o -name report-template.md -o -name cli-commands.md -o -name docker-compose.md -o -name verification.md -o -name build-templates.md' &amp;&amp;
      ! find raw/vendor/confluent-agent-skills/91d1871e -type f \( $SCAFFOLDS \) | grep -q .
    </automated>
  </verify>
  <done>
    Every required reference file exists at its vendored path; all four SKILL.md files present; PROVENANCE.md present; project-scaffold templates pruned. The grouped `find` command (with `\( ... \)` parens — without parens, only the last `-name` predicate would be checked) returns no matches, confirming all seven scaffold-template filenames are absent.
  </done>
</task>

<task type="auto">
  <name>Task 2: Author tools/vendor-sources.json with the locked schema</name>
  <files>tools/vendor-sources.json</files>
  <read_first>
    - .planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md (<specifics> section — exact JSON shape is locked there)
    - .planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md (D-01 — pin registry contract)
    - .planning/ROADMAP.md (Phase H.3 section — H.3b will extend this file with streaming-skills-plugin entry; schema must accommodate)
  </read_first>
  <action>
    Implements D-01.

    Create `tools/vendor-sources.json` with this exact content (matches CONTEXT.md <specifics> schema; the H.3b comment-key is omitted because JSON has no comments — H.3b will add its real entry when promoted):

    ```json
    {
      "confluent-agent-skills": {
        "upstream": "https://github.com/confluentinc/agent-skills",
        "commit": "91d1871ef8c320be92bca955c8e42492a2778cb4",
        "ingested_at": "2026-05-16",
        "vendor_path": "raw/vendor/confluent-agent-skills/91d1871e/",
        "license": "Apache-2.0",
        "kind": "wiki-source"
      }
    }
    ```

    Schema constraints (so H.3b drops in cleanly):
    - Top level is an object keyed by vendor short-name (`confluent-agent-skills`, future `streaming-skills-plugin`).
    - Each entry has: `upstream` (HTTPS URL), `commit` (40-char SHA), `ingested_at` (YYYY-MM-DD), `vendor_path` (repo-relative), `license` (SPDX identifier), `kind` (free-form string; current values: `wiki-source` for H.1, `claude-plugin` reserved for H.3b).
    - `kind` is deliberately a string not an enum so future vendor kinds (e.g., `terraform-module`, `python-package`) don't require a schema migration.

    Format: 2-space indentation, no trailing comma, newline at EOF. Must be `json.loads()` parseable.
  </action>
  <verify>
    <automated>
      test -f tools/vendor-sources.json &amp;&amp;
      python3 -c "import json; d = json.load(open('tools/vendor-sources.json')); assert d['confluent-agent-skills']['commit'] == '91d1871ef8c320be92bca955c8e42492a2778cb4', 'SHA mismatch'; assert d['confluent-agent-skills']['kind'] == 'wiki-source', 'kind mismatch'; assert d['confluent-agent-skills']['vendor_path'] == 'raw/vendor/confluent-agent-skills/91d1871e/', 'vendor_path mismatch'; assert d['confluent-agent-skills']['license'] == 'Apache-2.0', 'license mismatch'; print('OK')"
    </automated>
  </verify>
  <done>
    `tools/vendor-sources.json` exists, is valid JSON, and contains the locked schema with SHA 91d1871ef8c320be92bca955c8e42492a2778cb4, kind=wiki-source, vendor_path matches the path Task 1 created.
  </done>
</task>

<task type="auto">
  <name>Task 3: Populate raw/_ingest.md ## Pending with 19 entries (10 parents + 9 trip-wires)</name>
  <files>raw/_ingest.md</files>
  <read_first>
    - raw/_ingest.md (current format — see existing Processed entries for the canonical entry shape)
    - .planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md (D-05 tables — locked inventory; D-12 — queue mechanics)
    - .claude/commands/wiki/ingest.md (Step 1 — what /wiki:ingest expects to find)
  </read_first>
  <action>
    Implements D-12. Append 19 new entries to the `## Pending` section of `raw/_ingest.md`. The two existing Pending entries (`kafka-best-practices.md`, `kafka-recommendations.md` from April) stay — append, do not replace.

    Add a header comment above the new block so future reviewers can find it:
    ```
    # === Phase H.1: confluent-agent-skills@91d1871e ingest queue ===
    ```

    Then add all 19 entries below it. Each entry MUST reference the vendored path under `raw/vendor/confluent-agent-skills/91d1871e/` (NOT the upstream URL) — /wiki:ingest reads the source file from disk.

    **D-02 / D-05 tension resolved (read once, applies to trip-wires #4, #5, #6):** CONTEXT.md D-05 Table 2 lists `evals.json` as a source for trip-wires #4, #5, #6. Per D-02, `evals/evals.json` files are NOT vendored (they are CI gates upstream, not knowledge content — see `<deferred>` in CONTEXT.md). For these three trip-wires, the queue entry's `path:` field points at the corresponding `SKILL.md` (the vendored sibling) and `source_url:` cites the evals.json filepath by reference (not by clickable link) so /wiki:ingest can mention the eval's existence in body prose without requiring the file on disk. This is the recorded resolution of the D-02/D-05 tension.

    **10 parent article entries (D-05 table 1).** For each, `notes:` tells /wiki:ingest:
    1. Target wiki path
    2. Article type (concept vs pattern)
    3. Frontmatter extension (`source:` + `upstream_path:` fields)
    4. Confidence handling: source attestation per D-07 — emit `confidence: high` justified by upstream provenance, NO full MCP re-validation pass on these (D-07 explicit split)
    5. For multi-file merges (#8, #9, #10), list all merge inputs

    ```yaml
    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/topology-patterns.md
      added: 2026-05-16
      notes: |
        Parent article #1 of 10 (H.1). Target: wiki/patterns/kafka-streams-topology-patterns.md (pattern template).
        Frontmatter: extend with `source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4`
        and `upstream_path: skills/kafka-streams-programming/references/topology-patterns.md`.
        Provenance footer per CONTEXT.md D-03 shape.
        Confidence: high via source attestation (D-07) — skip the full MCP re-validation gate; upstream evals
        gate at 90%+ before merge so source attestation suffices. /wiki:ingest Step 3d remains for cross-link
        accuracy but does not block confidence: high.
        related: cross-link to existing wiki articles where natural (e.g., concepts/exactly-once-semantics,
        patterns/dr-cluster-linking) plus the trip-wires this article seeds (#4, #5, #6).

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/debugging.md
      added: 2026-05-16
      notes: |
        Parent article #2. Target: wiki/concepts/kafka-streams-debugging.md (concept template).
        Extend frontmatter with source/upstream_path. confidence: high via source attestation (D-07).
        Seeds trip-wires #4 (uncaught-exception-handler-import), #5 (avro-schema-source-directory),
        #6 (schema-aware-console-producer). related: cross-link to those trip-wire articles via `related:`.

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/production-hardening.md
      added: 2026-05-16
      notes: |
        Parent article #3. Target: wiki/concepts/kafka-streams-production-hardening.md (concept).
        Extend frontmatter with source/upstream_path. confidence: high via source attestation.
        related: cross-link to concepts/exactly-once-semantics, patterns/producer-config-fsi,
        patterns/consumer-config-fsi.

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/schema-patterns.md
      added: 2026-05-16
      notes: |
        Parent article #4. Target: wiki/concepts/kafka-streams-schema-patterns.md (concept).
        Extend frontmatter. confidence: high via source attestation.
        related: concepts/schema-registry-best-practices, concepts/schema-evolution-strategies,
        patterns/schema-registry-shared-types.

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/config-baseline.md
      added: 2026-05-16
      notes: |
        Parent article #5. Target: wiki/concepts/kafka-streams-config-baseline.md (concept).
        Extend frontmatter. confidence: high via source attestation.
        related: patterns/producer-config-fsi, patterns/consumer-config-fsi.

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/architecture.md
      added: 2026-05-16
      notes: |
        Parent article #6. Target: wiki/concepts/kafka-streams-architecture.md (concept).
        Extend frontmatter. confidence: high via source attestation.
        related: concepts/fsi-data-streaming-platform, concepts/exactly-once-semantics,
        patterns/flink-runtime-models.

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/flink-sql-patterns.md
      added: 2026-05-16
      notes: |
        Parent article #7. Target: wiki/patterns/cdc-to-tableflow-flink-decode.md (pattern).
        Extend frontmatter (upstream_path: skills/confluent-cloud-cdc-tableflow/references/flink-sql-patterns.md).
        confidence: high via source attestation.
        Seeds trip-wires #1 (tableflow-changelog-mode-immutability), #2 (cdc-tableflow-flink-decode-required).
        related: concepts/exactly-once-semantics, concepts/flink-checkpointing,
        concepts/flink-confluent-cloud-setup, and the two trip-wire descendants.

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/connector-configs.md
      source_url: |
        Also merges:
          raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/database-prerequisites.md
          raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/troubleshooting.md
      added: 2026-05-16
      notes: |
        Parent article #8 — THREE-WAY MERGE into a single wiki/concepts/cdc-source-connector-setup.md.
        Section ordering (Claude's Discretion per CONTEXT.md): (1) Database prerequisites first, (2) Connector
        config recipes second, (3) Troubleshooting last as a triage table — mirrors operational reading order
        (pre-deploy → deploy → debug). Cite all three upstream_paths in frontmatter as a yaml list:
          upstream_path:
            - skills/confluent-cloud-cdc-tableflow/references/connector-configs.md
            - skills/confluent-cloud-cdc-tableflow/references/database-prerequisites.md
            - skills/confluent-cloud-cdc-tableflow/references/troubleshooting.md
        Provenance footer should list all three files. Seeds trip-wire #3 (oracle-xstream-source-limitations).
        confidence: high via source attestation. related: patterns/cdc-to-tableflow-flink-decode,
        patterns/connect-deployment-models.

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/detection-patterns.md
      source_url: |
        Also merges:
          raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/code-migration.md
      added: 2026-05-16
      notes: |
        Parent article #9 — TWO-WAY MERGE into wiki/patterns/schema-registry-adoption-playbook.md (pattern).
        Section ordering: (1) Detection patterns first (scan existing Kafka usage), (2) Code migration second
        (Terraform generation + producer/consumer migration). upstream_path is a yaml list of both files.
        Provenance footer lists both. confidence: high via source attestation.
        related: concepts/schema-registry-best-practices, concepts/schema-evolution-strategies,
        patterns/fsi-governance-automation.

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/schema-inference.md
      source_url: |
        Also merges:
          raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/categorization.md
      added: 2026-05-16
      notes: |
        Parent article #10 — TWO-WAY MERGE into wiki/concepts/schema-inference-and-pii-categorization.md (concept).
        Section ordering: (1) Schema inference (deriving Avro from data samples), (2) Categorization (PII
        tagging on inferred schemas). upstream_path lists both. Provenance footer lists both.
        confidence: high via source attestation.
        related: concepts/schema-registry-best-practices, concepts/fsi-compliance,
        patterns/schema-registry-shared-types.
    ```

    **9 trip-wire entries (D-05 table 2).** These DO get full /wiki:ingest MCP-validation per D-07. Each entry's `notes:` calls out:
    - Target wiki path (all in wiki/concepts/ except #2 in wiki/patterns/)
    - Article type (concept template, ≤500 words, single-fact-focused)
    - `confidence: high` after full MCP gate (NOT source attestation — that's parent-only)
    - For trip-wires #7, #8, #9 (WarpStream): the verbatim "FSI context" paragraph from CONTEXT.md <specifics> MUST appear in the article body
    - The parent article(s) to cross-link via `related:` (back-link from D-06)

    ```yaml
    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/SKILL.md
      added: 2026-05-16
      notes: |
        Trip-wire #1 (H.1). Target: wiki/concepts/tableflow-changelog-mode-immutability.md (concept, ≤500 words).
        Single-fact-focused: "Tableflow changelog mode is immutable after first materialization."
        FULL MCP-validation gate (D-07): query confluent-docs for Tableflow materialization semantics,
        especially `changelog` mode behavior on schema/topic changes. Set confidence: high only after the
        MCP gate passes. Extend frontmatter with source/upstream_path. related: patterns/cdc-to-tableflow-flink-decode
        (parent #7), patterns/cdc-tableflow-flink-decode-required (sibling trip-wire #2),
        concepts/oracle-xstream-source-limitations (sibling #3).

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/SKILL.md
      added: 2026-05-16
      notes: |
        Trip-wire #2 (H.1). Target: wiki/patterns/cdc-tableflow-flink-decode-required.md (pattern, ≤500 words).
        Single-fact-focused: "Don't enable Tableflow on a CDC source topic — tombstones break APPEND mode;
        decode via Flink first, sink to a clean topic, then enable Tableflow on the clean topic."
        FULL MCP-validation gate (D-07): confluent-docs for Tableflow APPEND vs CHANGELOG mode tombstone
        handling. Frontmatter source/upstream_path. related: patterns/cdc-to-tableflow-flink-decode (parent #7),
        concepts/tableflow-changelog-mode-immutability (sibling #1).

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/SKILL.md
      added: 2026-05-16
      notes: |
        Trip-wire #3 (H.1). Target: wiki/concepts/oracle-xstream-source-limitations.md (concept, ≤500 words).
        Single-fact-focused: "OracleXStreamSource doesn't support `after.state.only` — workaround is a
        Flink transform on the source topic before sinking to the target topic."
        FULL MCP-validation gate (D-07): confluent-docs for OracleXStreamSource connector config.
        Frontmatter source/upstream_path. related: wiki/concepts/cdc-source-connector-setup (parent #8 — where
        connector configs live).

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/SKILL.md
      source_url: also-cite: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/evals/evals.json
      added: 2026-05-16
      notes: |
        Trip-wire #4 (H.1). Target: wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md
        (concept, ≤500 words). Single-fact-focused: "In Kafka Streams 4.x, StreamsUncaughtExceptionHandler
        lives in `org.apache.kafka.streams.errors`, NOT as a nested class under `KafkaStreams`. Import path
        changed in the 4.x refactor."
        FULL MCP-validation gate (D-07): confluent-docs for KS 4.x package structure; context7 fallback for
        KIP references if applicable. Include a 3-line code snippet showing the correct import statement
        (Java). NOTE: the evals/evals.json file referenced in source_url is intentionally NOT vendored
        (excluded in Task 1 per D-02 — see also D-02/D-05 tension note above); cite its existence in the
        wiki body as upstream proof of the trip-wire's importance, but the citation path is the SKILL.md,
        not the evals.json. Frontmatter source/upstream_path.
        related: wiki/concepts/kafka-streams-debugging (parent #2),
        wiki/concepts/kafka-streams-production-hardening (parent #3).

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/SKILL.md
      source_url: also-cite: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/evals/evals.json
      added: 2026-05-16
      notes: |
        Trip-wire #5 (H.1). Target: wiki/concepts/avro-schema-source-directory.md (concept, ≤500 words).
        Single-fact-focused: "Avro schemas live in `src/main/avro/` (the Avro Maven plugin convention),
        NOT `src/main/resources/avro/`. Code generation breaks silently if put in resources/."
        FULL MCP-validation gate (D-07): context7 for Avro Maven Plugin canonical layout; confluent-docs
        fallback for Confluent Schema Registry Maven Plugin layout. Include a 4-line `pom.xml` snippet
        showing the plugin's expected source directory. Frontmatter source/upstream_path. evals.json source
        cited by path in body prose only (file not vendored per D-02 — see D-02/D-05 tension note above).
        related: wiki/concepts/kafka-streams-debugging (parent #2),
        wiki/concepts/kafka-streams-schema-patterns (parent #4).

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/SKILL.md
      source_url: also-cite: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/evals/evals.json
      added: 2026-05-16
      notes: |
        Trip-wire #6 (H.1). Target: wiki/concepts/schema-aware-console-producer-required.md (concept, ≤500 words).
        Single-fact-focused: "`kafka-console-producer` doesn't speak Schema Registry — using it against a
        SR-governed topic ships records WITHOUT the magic-byte+schema-id prefix and breaks all SR-aware
        consumers. Use `kafka-avro-console-producer` (or `kafka-protobuf-console-producer` / `kafka-json-schema-console-producer`)
        for verification on SR-governed topics."
        FULL MCP-validation gate (D-07): confluent-docs for `kafka-avro-console-producer` CLI usage and the
        wire format magic-byte. Include a 2-line CLI invocation example. Frontmatter source/upstream_path.
        evals.json source cited by path in body prose only (file not vendored per D-02 — see D-02/D-05
        tension note above).
        related: wiki/concepts/schema-registry-best-practices, wiki/concepts/kafka-streams-debugging (parent #2).

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/developing-kafka-python-client/SKILL.md
      source_url: also-cite: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/warpstream-optimization.md
      added: 2026-05-16
      notes: |
        Trip-wire #7 (H.1). Target: wiki/concepts/warpstream-schema-registry-format-constraint.md (concept, ≤500 words).
        Single-fact-focused: "WarpStream's built-in Schema Registry only supports Avro and Protobuf;
        `GET /schemas/types` returns `[\"AVRO\",\"PROTOBUF\"]` — no JSON Schema support."
        FULL MCP-validation gate (D-07): cannot validate via confluent-docs (WarpStream is not Confluent);
        rely on context7 search of WarpStream's docs OR mark verifiable claims with ⚠️ unverified inline
        and downgrade confidence to medium IF the majority of claims are unverifiable; otherwise keep high.
        MANDATORY: include the verbatim "FSI context" paragraph from CONTEXT.md <specifics> immediately
        after the trip-wire claim — this is non-negotiable per the vendor-backing rule (feedback memory).
        Frontmatter source/upstream_path (upstream_path is the SKILL.md path).
        related: wiki/concepts/schema-registry-best-practices,
        wiki/concepts/warpstream-config-overrides (sibling #8),
        wiki/concepts/exactly-once-v2-warpstream-throughput-cost (sibling #9).

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/warpstream-optimization.md
      added: 2026-05-16
      notes: |
        Trip-wire #8 (H.1). Target: wiki/concepts/warpstream-config-overrides.md (concept, ≤500 words).
        Single-fact-focused: "WarpStream does not honor `fetch.min.bytes` (silently ignored), and
        `replication.factor` is cosmetic (the WarpStream tier always replicates 3-way internally regardless
        of the value set on topic creation)."
        FULL MCP-validation gate (D-07): same caveat as #7 — context7 fallback, inline ⚠️ unverified where
        WarpStream docs are silent.
        MANDATORY: include the verbatim "FSI context" paragraph from CONTEXT.md <specifics>.
        Frontmatter source/upstream_path. related: wiki/concepts/warpstream-schema-registry-format-constraint
        (sibling #7), wiki/concepts/exactly-once-v2-warpstream-throughput-cost (sibling #9),
        wiki/concepts/kafka-streams-config-baseline (parent #5).

    - path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/warpstream-optimization.md
      added: 2026-05-16
      notes: |
        Trip-wire #9 (H.1). Target: wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md (concept, ≤500 words).
        Single-fact-focused: "Enabling `processing.guarantee=exactly_once_v2` in Kafka Streams turns on
        idempotent producers internally, which throttles in-flight request concurrency. On WarpStream's
        S3-backed storage tier this translates to a meaningful throughput hit; on classic Kafka the cost is
        present but smaller. Quantify before turning on for high-throughput WarpStream pipelines."
        FULL MCP-validation gate (D-07): confluent-docs for `processing.guarantee=exactly_once_v2`
        semantics and idempotent producer constraints (max.in.flight.requests.per.connection ≤5).
        context7 fallback for WarpStream-specific impact.
        MANDATORY: include the verbatim "FSI context" paragraph from CONTEXT.md <specifics>.
        Frontmatter source/upstream_path. related: wiki/concepts/exactly-once-semantics,
        wiki/concepts/warpstream-config-overrides (sibling #8),
        wiki/concepts/kafka-streams-production-hardening (parent #3).
    ```

    All 19 entries go under the existing `## Pending` heading, after the existing two April-2026 entries. Do NOT touch the existing entries. Do NOT modify the `## Processed` section.

    Verify the YAML in each `notes:` block doesn't accidentally include a `---` separator that would confuse downstream tooling.
  </action>
  <verify>
    <automated>
      test -f raw/_ingest.md &amp;&amp;
      grep -c "raw/vendor/confluent-agent-skills/91d1871e" raw/_ingest.md | awk '{ if ($1 &lt; 19) { print "FAIL: expected ≥19 vendor path refs, got " $1; exit 1 } else print "OK: " $1 " vendor refs" }' &amp;&amp;
      grep -q "Phase H.1: confluent-agent-skills@91d1871e ingest queue" raw/_ingest.md &amp;&amp;
      grep -c "Trip-wire #" raw/_ingest.md | awk '{ if ($1 &lt; 9) { print "FAIL: expected 9 trip-wires, got " $1; exit 1 } else print "OK: " $1 " trip-wires" }' &amp;&amp;
      grep -c "Parent article #" raw/_ingest.md | awk '{ if ($1 &lt; 10) { print "FAIL: expected 10 parents, got " $1; exit 1 } else print "OK: " $1 " parents" }' &amp;&amp;
      grep -q "kafka-best-practices.md" raw/_ingest.md &amp;&amp; echo "OK: existing April entries preserved"
    </automated>
  </verify>
  <done>
    `raw/_ingest.md` contains the H.1 header comment, 10 parent entries, 9 trip-wire entries (all referencing vendored paths), and preserves the two existing April-2026 Pending entries. Total of ≥19 references to `raw/vendor/confluent-agent-skills/91d1871e`.
  </done>
</task>

</tasks>

<verification>
After all three tasks pass:

1. `tools/vendor-sources.json` parses and contains the locked SHA.
2. The full reference tree exists under `raw/vendor/confluent-agent-skills/91d1871e/skills/{kafka-streams-programming,developing-kafka-python-client,kafka-schema-registry,confluent-cloud-cdc-tableflow}/` with all four `SKILL.md` files and the references/ subdirectories pruned of project-scaffold templates.
3. `raw/_ingest.md` has 19 new Pending entries — 10 parents + 9 trip-wires — each correctly pointing at vendored paths and annotated for downstream /wiki:ingest behavior (parent → source attestation, trip-wire → full MCP gate; WarpStream trip-wires call out the FSI-context paragraph as MANDATORY).
4. No wiki articles authored yet — H.1-02 and H.1-03 will do that, consuming the queue produced here.

Roll-up command:
```bash
test -f tools/vendor-sources.json &&
test -d raw/vendor/confluent-agent-skills/91d1871e/skills &&
test $(ls raw/vendor/confluent-agent-skills/91d1871e/skills | wc -l) -eq 4 &&
grep -c "raw/vendor/confluent-agent-skills/91d1871e" raw/_ingest.md
```
</verification>

<success_criteria>
- `tools/vendor-sources.json` exists, valid JSON, SHA=91d1871ef8c320be92bca955c8e42492a2778cb4, kind=wiki-source
- Vendor tree exists with the 4 skills × (SKILL.md + references/) layout; project-scaffold templates pruned
- `raw/_ingest.md` ## Pending has 19 new entries pointing at vendored paths
- Existing two April-2026 Pending entries preserved untouched
- WIKI-06 partial coverage: vendor + queue setup complete (article authoring happens in H.1-02 and H.1-03)
</success_criteria>

<output>
After completion, create `.planning/phases/H.1-wiki-ingest-agent-skills/H.1-01-SUMMARY.md` capturing:
- Vendor tree size (file count, byte count) and any deviations from CONTEXT.md D-05 file lists
- Any pruning surprises (project-scaffold templates discovered that weren't in the anti-references list)
- Final `tools/vendor-sources.json` content (verbatim)
- Final pending entry count (should be 21 = 19 new + 2 preserved)
- Any .gitignore findings
</output>
</content>
</invoke>