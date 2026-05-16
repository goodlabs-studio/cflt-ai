---
phase: H.1-wiki-ingest-agent-skills
plan: 03
type: execute
wave: 3
depends_on: [H.1-02]
files_modified:
  - wiki/concepts/tableflow-changelog-mode-immutability.md
  - wiki/patterns/cdc-tableflow-flink-decode-required.md
  - wiki/concepts/oracle-xstream-source-limitations.md
  - wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md
  - wiki/concepts/avro-schema-source-directory.md
  - wiki/concepts/schema-aware-console-producer-required.md
  - wiki/concepts/warpstream-schema-registry-format-constraint.md
  - wiki/concepts/warpstream-config-overrides.md
  - wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md
  - wiki/_index.md
  - wiki/_graph.md
  - raw/_ingest.md
  - tools/wiki-lint.py
autonomous: true
requirements: [WIKI-07, WIKI-08]
requirements_addressed: [WIKI-07, WIKI-08]
must_haves:
  truths:
    - "9 trip-wire micro-articles exist at the locked paths from CONTEXT.md D-05 table 2, each ≤500 words, single-fact-focused, with `confidence: high` justified by FULL /wiki:ingest MCP-validation gate (D-07)"
    - "Trip-wires #7, #8, #9 (WarpStream) include the verbatim FSI-context paragraph from CONTEXT.md <specifics>"
    - "Every trip-wire cross-links back to its parent ingest article via `related:` (per D-06)"
    - "`wiki/_index.md` and `wiki/_graph.md` updated with all 9 trip-wires, closing the forward-reference warnings from H.1-02"
    - "raw/_ingest.md ## Pending no longer contains the 9 trip-wire entries (moved to ## Processed)"
    - "tools/wiki-lint.py extended to read `source: confluent-agent-skills@<sha>` from article frontmatter, compare against current pin in tools/vendor-sources.json, and emit a `drift` finding when stale (D-09)"
    - "python tools/wiki-lint.py exits 0 against the final wiki state — zero broken links, zero orphans, zero drift (current SHA matches pin), zero decay (all articles fresh)"
  artifacts:
    - path: "wiki/concepts/tableflow-changelog-mode-immutability.md"
      provides: "Trip-wire #1 — Tableflow CHANGELOG mode immutable after first materialization"
      contains: "confidence: high"
    - path: "wiki/patterns/cdc-tableflow-flink-decode-required.md"
      provides: "Trip-wire #2 — don't enable Tableflow directly on CDC source; tombstones break APPEND"
      contains: "confidence: high"
    - path: "wiki/concepts/oracle-xstream-source-limitations.md"
      provides: "Trip-wire #3 — OracleXStreamSource doesn't support after.state.only"
      contains: "confidence: high"
    - path: "wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md"
      provides: "Trip-wire #4 — KS 4.x StreamsUncaughtExceptionHandler import path change"
      contains: "org.apache.kafka.streams.errors"
    - path: "wiki/concepts/avro-schema-source-directory.md"
      provides: "Trip-wire #5 — Avro schemas in src/main/avro/ not src/main/resources/avro/"
      contains: "src/main/avro/"
    - path: "wiki/concepts/schema-aware-console-producer-required.md"
      provides: "Trip-wire #6 — kafka-console-producer doesn't speak SR; use kafka-avro-console-producer"
      contains: "kafka-avro-console-producer"
    - path: "wiki/concepts/warpstream-schema-registry-format-constraint.md"
      provides: "Trip-wire #7 — WarpStream SR only supports Avro and Protobuf"
      contains: "FSI context"
    - path: "wiki/concepts/warpstream-config-overrides.md"
      provides: "Trip-wire #8 — WarpStream fetch.min.bytes ignored; replication.factor cosmetic"
      contains: "FSI context"
    - path: "wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md"
      provides: "Trip-wire #9 — exactly_once_v2 throughput cost on WarpStream"
      contains: "FSI context"
    - path: "tools/wiki-lint.py"
      provides: "Drift detection extension per D-09 — reads source: from frontmatter, compares against tools/vendor-sources.json pin, emits drift finding when stale"
      contains: "vendor-sources.json"
  key_links:
    - from: "wiki/concepts/tableflow-changelog-mode-immutability.md"
      to: "patterns/cdc-to-tableflow-flink-decode"
      via: "related: frontmatter field (back-link to parent #7)"
      pattern: "related:.*cdc-to-tableflow-flink-decode"
    - from: "wiki/concepts/warpstream-schema-registry-format-constraint.md"
      to: "wiki/concepts/warpstream-config-overrides"
      via: "related: cross-link between sibling WarpStream trip-wires"
      pattern: "related:.*warpstream-config-overrides"
    - from: "tools/wiki-lint.py"
      to: "tools/vendor-sources.json"
      via: "drift check reads pin file"
      pattern: "vendor-sources.json"
    - from: "wiki/_graph.md"
      to: "concepts/tableflow-changelog-mode-immutability"
      via: "≥1 inbound + ≥1 outbound graph edge"
      pattern: "tableflow-changelog-mode-immutability"
---

<objective>
Author the 9 trip-wire micro-articles per CONTEXT.md D-05 table 2 with FULL `/wiki:ingest` MCP-validation (D-07: trip-wires get the rigorous half, not source attestation). Include the verbatim FSI-context paragraph in the three WarpStream articles per CONTEXT.md `<specifics>`. Update `wiki/_index.md` and `wiki/_graph.md` to register the 9 articles and close the forward-reference warnings from H.1-02. Move the 9 trip-wire entries from Pending to Processed. Extend `tools/wiki-lint.py` with vendor-source drift detection per D-09.

Purpose: Trip-wires are the load-bearing facts SAs cite in customer engagements via `/review` claim extraction (REVW-01). They are short, single-fact-focused, and MCP-validated against `confluent-docs` / `context7` so accuracy stakes are highest. After this plan, the wiki gains 9 citation-friendly micro-articles plus passive drift detection for the entire vendored content slice.

Output: 9 new wiki articles, updated index and graph, processed queue entries, extended wiki-lint.py. WIKI-07 (≥8 trip-wires) is fully satisfied; WIKI-08 (validate passes on every article, index + graph updated) is fully satisfied at the end of this plan (this plan is the sole owner of WIKI-08 closure per Issue 5 fix in H.1-02).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md
@.planning/phases/H.1-wiki-ingest-agent-skills/H.1-01-SUMMARY.md
@.planning/phases/H.1-wiki-ingest-agent-skills/H.1-02-SUMMARY.md
@.claude/commands/wiki/ingest.md
@.claude/commands/wiki/references/article-format.md
@.claude/commands/wiki/references/quality-standards.md
@tools/vendor-sources.json
@tools/wiki-lint.py
@wiki/_index.md
@wiki/_graph.md
@wiki/patterns/cdc-to-tableflow-flink-decode.md
@wiki/concepts/kafka-streams-debugging.md
@wiki/concepts/kafka-streams-production-hardening.md
@wiki/concepts/kafka-streams-config-baseline.md
@wiki/concepts/schema-registry-best-practices.md
@raw/_ingest.md
@raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/SKILL.md
@raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/SKILL.md
@raw/vendor/confluent-agent-skills/91d1871e/skills/developing-kafka-python-client/SKILL.md
@raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/warpstream-optimization.md
</context>

<interfaces>
<!-- Trip-wire frontmatter — same 9 fields as parents, with `tags:` always including `trip-wire` for discoverability -->
<!-- YAML rule (load-bearing — Issue 1 blocker fix): tag arrays MUST be comma-separated -->
<!--   GOOD: tags: [trip-wire, tableflow, changelog, confluent-cloud, confluent-agent-skills] -->
<!--   BAD:  tags: [trip-wire tableflow changelog confluent-cloud confluent-agent-skills]    -->
<!-- The exemplar `wiki/concepts/schema-registry-best-practices.md` line 3 is the canonical reference: -->
<!--   tags: [schema-registry, avro, protobuf, compatibility, governance, fsi, csfle] -->
<!-- YAML interprets [a b c] as a single scalar "a b c", NOT a 3-element list; downstream tag-based -->
<!-- filtering (wiki-lint, wiki-stats, /ask, /review) silently breaks. Task 4's verify grep-checks this. -->

```yaml
# ---
title: <Single-fact title (≤8 words)>
tags: [trip-wire, <topic-tag-1>, <topic-tag-2>, confluent-agent-skills]
sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/<skill>/<file>]
related: [<parent article path>, <sibling trip-wire paths if any>]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/<skill>/<file>
# ---
```

<!-- Trip-wire body structure (concept template, ≤500 words): -->

```markdown
# <Title>

## Summary

<Single-fact stated upfront in 1–2 sentences. This is the citation surface for /review claim extraction (REVW-01).>

<For WarpStream trip-wires #7, #8, #9 — verbatim FSI-context paragraph from CONTEXT.md <specifics> goes HERE, immediately after the trip-wire claim.>

## Detail

<2–4 paragraphs: why it matters, what failure looks like if violated, minimal code/CLI example proving the correct form. MCP-validated content.>

## Related

<Bulleted links to parent article and sibling trip-wires.>

# ---

*Source: confluentinc/agent-skills@91d1871e · skills/<skill>/<file> · Ingested 2026-05-16 · Apache-2.0*
```

<!-- MCP routing per D-07 + quality-standards.md MCP routing table: -->

| Trip-wire | Primary MCP | Fallback | Notes |
|-----------|-------------|----------|-------|
| #1 Tableflow CHANGELOG | `confluent-docs` | `context7` | Query Tableflow materialization semantics |
| #2 Tableflow tombstones | `confluent-docs` | `context7` | Query Tableflow APPEND vs CHANGELOG modes |
| #3 OracleXStream | `confluent-docs` | — | Query OracleXStreamSource config |
| #4 KS 4.x import | `confluent-docs` | `context7` | Query KS 4.x package structure / migration guide |
| #5 Avro src dir | `context7` | `confluent-docs` | Query Avro Maven Plugin convention |
| #6 Console producer | `confluent-docs` | — | Query kafka-avro-console-producer CLI |
| #7 WarpStream SR | `context7` | inline ⚠️ unverified | WarpStream not in confluent-docs |
| #8 WarpStream config | `context7` | inline ⚠️ unverified | WarpStream not in confluent-docs |
| #9 EOS v2 + WarpStream | `confluent-docs` (EOS part) + `context7` (WarpStream part) | inline ⚠️ unverified | Split coverage |

<!-- D-02 / D-05 tension resolved (read once, applies to trip-wires #4, #5, #6 throughout this plan): -->
<!-- CONTEXT.md D-05 Table 2 lists `evals.json` as a source for trip-wires #4, #5, #6. Per D-02, -->
<!-- `evals/evals.json` files are NOT vendored (they are CI gates upstream, not knowledge content — see -->
<!-- `<deferred>` in CONTEXT.md). For these three trip-wires, frontmatter `upstream_path:` cites the -->
<!-- corresponding `SKILL.md` (the vendored sibling), and the body prose mentions the evals.json filepath -->
<!-- by citation. This is the recorded resolution of the D-02/D-05 tension. -->

<!-- wiki-lint.py drift detection signature -->

The extension must add a function that:
1. Loads `tools/vendor-sources.json` (parse JSON)
2. For each wiki article with a `source:` frontmatter field matching `confluent-agent-skills@<sha>`, compare `<sha>` against `vendor-sources.json["confluent-agent-skills"]["commit"]`
3. Emit a `drift` finding when stale: `DRIFT: <article path>: source=<article-sha>, current pin=<json-sha>`
4. Run alongside existing decay check (D-09 — "surfaces in routine wiki health checks alongside the existing decay rule")
5. Match by prefix (8-char SHA in article frontmatter `91d1871` is OK to match the 40-char pin if the 40-char pin starts with that prefix — D-03 allows shortened SHAs in paths but the frontmatter `source:` field uses the full 40-char form per the CONTEXT.md schema)
</interfaces>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Extend tools/wiki-lint.py with vendor-source drift detection</name>
  <files>tools/wiki-lint.py, tests/test_wiki_lint_drift.py</files>
  <read_first>
    - tools/wiki-lint.py (current head — drift function will live alongside the existing decay check; see structure on lines 1–40)
    - tools/vendor-sources.json (the pin registry to read from — created by H.1-01)
    - .planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md (D-09 — drift detection scope)
    - wiki/concepts/schema-registry-best-practices.md (exemplar of a non-vendored article — drift check must skip these)
    - wiki/patterns/cdc-to-tableflow-flink-decode.md (exemplar of a vendored article post-H.1-02 — drift check must catch these)
  </read_first>
  <behavior>
    - Test 1: Article with `source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4` and vendor-sources.json pin matching the same SHA → no drift finding emitted.
    - Test 2: Article with `source: confluent-agent-skills@OLDSHA` and vendor-sources.json pin == `91d1871ef8c320be92bca955c8e42492a2778cb4` → drift finding emitted in the form `DRIFT: <path>: source=OLDSHA, pin=91d1871e...`.
    - Test 3: Article with no `source:` field (e.g., existing non-vendored article like schema-registry-best-practices.md) → no drift finding emitted (skip silently).
    - Test 4: `tools/vendor-sources.json` missing → drift check exits with a clear `MISSING vendor-sources.json` warning but doesn't crash the lint run.
    - Test 5: Article with malformed `source:` value (no `@` separator) → emit a `MALFORMED source field` finding, don't crash.
  </behavior>
  <action>
    Implements D-09 (passive drift detection extension to wiki-lint).

    1. **Read `tools/wiki-lint.py` first** to understand its current structure: `parse_frontmatter()` helper exists (line 27ff); decay check pattern is already in place via `DECAY_DAYS = 90`. Match the existing style — pure-Python stdlib + `yaml`, no new dependencies.

    2. **Write the test file first (RED phase):** Create `tests/test_wiki_lint_drift.py` with the 5 cases from `<behavior>` above. Use pytest. Mock the wiki tree by creating temp files in `tmp_path` fixtures, write fake frontmatter, point `CFLT_WIKI_ROOT` at the tmp dir. Pseudo-shape:

    ```python
    import json, os, subprocess, pytest
    from pathlib import Path

    SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "wiki-lint.py"

    def make_article(dir: Path, name: str, source_value: str | None):
        body = "---\ntitle: Test\nconfidence: high\nlast_updated: 2026-05-16\nlast_validated: 2026-05-16\n"
        if source_value is not None:
            body += f"source: {source_value}\n"
        body += "---\n\n# Test\n\nBody.\n"
        path = dir / "wiki" / "concepts" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
        return path

    def make_vendor_sources(dir: Path, commit: str | None):
        if commit is None:
            return  # skip creating
        data = {"confluent-agent-skills": {"upstream": "https://example/agent-skills", "commit": commit, "kind": "wiki-source"}}
        (dir / "tools").mkdir(exist_ok=True)
        (dir / "tools" / "vendor-sources.json").write_text(json.dumps(data))

    def run_lint(root: Path):
        env = os.environ.copy()
        env["CFLT_WIKI_ROOT"] = str(root)
        return subprocess.run(["python", str(SCRIPT)], env=env, capture_output=True, text=True)

    def test_drift_match_no_finding(tmp_path):
        make_article(tmp_path, "a.md", "confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4")
        make_vendor_sources(tmp_path, "91d1871ef8c320be92bca955c8e42492a2778cb4")
        result = run_lint(tmp_path)
        assert "DRIFT" not in result.stdout, result.stdout

    def test_drift_stale_sha_emits_finding(tmp_path):
        make_article(tmp_path, "a.md", "confluent-agent-skills@0123456789abcdef0123456789abcdef01234567")
        make_vendor_sources(tmp_path, "91d1871ef8c320be92bca955c8e42492a2778cb4")
        result = run_lint(tmp_path)
        assert "DRIFT" in result.stdout
        assert "0123456789abcdef" in result.stdout

    def test_no_source_field_skipped(tmp_path):
        make_article(tmp_path, "a.md", None)
        make_vendor_sources(tmp_path, "91d1871ef8c320be92bca955c8e42492a2778cb4")
        result = run_lint(tmp_path)
        assert "DRIFT" not in result.stdout

    def test_missing_vendor_sources_warns_not_crashes(tmp_path):
        make_article(tmp_path, "a.md", "confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4")
        make_vendor_sources(tmp_path, None)
        result = run_lint(tmp_path)
        assert result.returncode == 0 or "MISSING vendor-sources.json" in (result.stdout + result.stderr)

    def test_malformed_source_field_emits_finding(tmp_path):
        make_article(tmp_path, "a.md", "confluent-agent-skills-no-at-sign")
        make_vendor_sources(tmp_path, "91d1871ef8c320be92bca955c8e42492a2778cb4")
        result = run_lint(tmp_path)
        assert "MALFORMED" in result.stdout
    ```

    Run the test suite — expect failures (RED): `python -m pytest tests/test_wiki_lint_drift.py -x`.

    3. **Implement the drift check in `tools/wiki-lint.py` (GREEN phase):**

    Add (alongside existing functions):

    ```python
    def load_vendor_pins(repo_root: Path) -> dict | None:
        """Return parsed tools/vendor-sources.json or None if missing.

        Missing file is a soft condition — print warning to stderr, return None,
        callers skip the drift check. Matches D-09 'passive' posture: not a hard fail.
        """
        pin_path = repo_root / "tools" / "vendor-sources.json"
        if not pin_path.exists():
            print(f"WARNING: MISSING vendor-sources.json at {pin_path} — drift check skipped", file=sys.stderr)
            return None
        try:
            return json.loads(pin_path.read_text())
        except json.JSONDecodeError as exc:
            print(f"WARNING: MALFORMED vendor-sources.json: {exc} — drift check skipped", file=sys.stderr)
            return None


    def check_vendor_drift(article_path: Path, frontmatter: dict, vendor_pins: dict | None) -> list[str]:
        """Return list of drift findings for one article. Empty list = clean."""
        if vendor_pins is None:
            return []
        source = frontmatter.get("source")
        if not source:
            return []  # non-vendored article; skip
        if "@" not in source:
            return [f"MALFORMED source field in {article_path}: {source!r} (expected '<vendor>@<sha>')"]
        vendor, sha = source.split("@", 1)
        pin_entry = vendor_pins.get(vendor)
        if pin_entry is None:
            return [f"UNKNOWN VENDOR in {article_path}: {vendor!r} not in vendor-sources.json"]
        pinned_sha = pin_entry.get("commit", "")
        if sha != pinned_sha:
            return [f"DRIFT: {article_path}: source={sha[:12]}..., pin={pinned_sha[:12]}..."]
        return []
    ```

    Wire `check_vendor_drift` into the main wiki-lint loop alongside the existing decay/link/orphan checks. Findings collected and printed at the end, same format as existing findings. Exit code stays 0 for drift findings alone (passive — surfaces but doesn't fail). Only break links / missing frontmatter / true failures exit non-zero.

    Import `json` at top of file if not already imported.

    4. **Re-run tests (GREEN verified):** `python -m pytest tests/test_wiki_lint_drift.py -v` — all 5 must pass.

    5. **Run the full wiki-lint against the current wiki state** to confirm no spurious findings against the 10 parent articles H.1-02 created:

    ```bash
    python tools/wiki-lint.py
    ```

    Expected: zero DRIFT findings (all 10 parent articles have `source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4` matching the pin); zero UNKNOWN VENDOR; zero MALFORMED.

    If any spurious findings surface, the parent articles' `source:` frontmatter values are wrong — fix in H.1-02 first (out of scope for this task; flag as a blocker).
  </action>
  <verify>
    <automated>
      python -m pytest tests/test_wiki_lint_drift.py -v &amp;&amp;
      python tools/wiki-lint.py | grep -E "DRIFT|UNKNOWN VENDOR|MALFORMED" | grep -v "^$" &amp;&amp; { echo "FAIL: unexpected drift findings against current pin"; exit 1; } || echo "OK: no drift findings (current state matches pin)"
    </automated>
  </verify>
  <done>
    `tools/wiki-lint.py` has a working `check_vendor_drift` function; 5 pytest cases pass; full wiki-lint run against current wiki state produces zero drift findings (because the 10 parent articles' source-SHAs match the pin).
  </done>
</task>

<task type="auto">
  <name>Task 2: Author the 6 non-WarpStream trip-wires (#1–#6) with full MCP validation</name>
  <files>
    wiki/concepts/tableflow-changelog-mode-immutability.md,
    wiki/patterns/cdc-tableflow-flink-decode-required.md,
    wiki/concepts/oracle-xstream-source-limitations.md,
    wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md,
    wiki/concepts/avro-schema-source-directory.md,
    wiki/concepts/schema-aware-console-producer-required.md
  </files>
  <read_first>
    - .planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md (D-05 table 2 rows 1–6; D-07 trip-wire MCP gate)
    - .claude/commands/wiki/references/quality-standards.md (MCP routing table — line 18–28; mandatory MCP validation rules — line 8–17)
    - .claude/commands/wiki/ingest.md (Step 3d — MCP validation gate)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/SKILL.md (source for trip-wires #1, #2, #3)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/SKILL.md (source for trip-wires #4, #5, #6)
    - wiki/patterns/cdc-to-tableflow-flink-decode.md (parent for #1, #2; created in H.1-02)
    - wiki/concepts/cdc-source-connector-setup.md (parent for #3; created in H.1-02)
    - wiki/concepts/kafka-streams-debugging.md (parent for #4, #5, #6; created in H.1-02)
    - wiki/concepts/schema-registry-best-practices.md (canonical YAML tag-array exemplar at line 3 — `tags: [a, b, c]` comma-separated)
  </read_first>
  <action>
    Apply the /wiki:ingest 6-step flow with FULL Step 3d MCP validation for each trip-wire. These are the rigorous half per D-07.

    **YAML tag-array rule (Issue 1 blocker fix, applies to ALL frontmatter in this task):** every `tags:` array MUST be comma-separated — `tags: [trip-wire, tableflow, changelog, confluent-agent-skills]` NOT `tags: [trip-wire tableflow changelog confluent-agent-skills]`. The exemplar at `wiki/concepts/schema-registry-best-practices.md` line 3 is the canonical reference. YAML's flow-sequence `[...]` syntax requires commas; without them the array parses as one scalar string and downstream tag-keyed filtering (wiki-lint, wiki-stats, /ask, /review) silently breaks. Task 4's verify grep-checks every trip-wire article's tags parse as a YAML list.

    **D-02 / D-05 tension resolved (already noted in `<interfaces>` above — applies to trip-wires #4, #5, #6):** evals.json is NOT vendored per D-02; `upstream_path:` cites SKILL.md (the vendored sibling); the body prose mentions the evals.json filepath by citation only. This is the recorded resolution of the D-02/D-05 tension.

    **For each trip-wire, the structure is fixed** (≤500 words total body):

    1. Frontmatter (locked schema; trip-wires always tagged `trip-wire`; **all tag arrays comma-separated**)
    2. Title (the fact, restated)
    3. `## Summary` — 1–2 sentence single-fact statement (citation surface for REVW-01)
    4. `## Detail` — 2–4 paragraphs: why it matters, failure mode, minimal correct example
    5. `## Related` — back-link to parent + sibling trip-wires
    6. Provenance footer (italicized last paragraph)

    **MCP validation per trip-wire (D-07 + quality-standards.md routing table):** for every verifiable claim in `## Detail` (config names, version numbers, import paths, CLI flags, behavioral assertions), invoke the appropriate MCP tool and apply the three outcomes:
    - **Confirmed:** keep as-is
    - **Contradicted:** correct the claim in the body
    - **No MCP data:** inline `> ⚠️ unverified — <claim>` marker

    For these 6 (non-WarpStream) trip-wires, MCP data should be present for the majority of claims. Set `confidence: high` if so. Note in summary: "Validated against confluent-docs + context7 via /wiki:ingest Step 3d on 2026-05-16."

    ---

    **Trip-wire #1: `wiki/concepts/tableflow-changelog-mode-immutability.md`**

    Source: `skills/confluent-cloud-cdc-tableflow/SKILL.md`

    Frontmatter:
    ```yaml
    title: Tableflow Changelog Mode is Immutable After First Materialization
    tags: [trip-wire, tableflow, changelog, confluent-cloud, confluent-agent-skills]
    sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/SKILL.md]
    related: [patterns/cdc-to-tableflow-flink-decode, patterns/cdc-tableflow-flink-decode-required, concepts/oracle-xstream-source-limitations]
    confidence: high
    last_updated: 2026-05-16
    last_validated: 2026-05-16
    source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
    upstream_path: skills/confluent-cloud-cdc-tableflow/SKILL.md
    ```

    Summary opener: "Once a Tableflow table has materialized in CHANGELOG mode, the mode is **immutable**. You cannot switch a CHANGELOG-mode Tableflow table to APPEND mode (or vice versa) without recreating the table." MCP-validate via `confluent-docs` query on Tableflow materialization semantics.

    ---

    **Trip-wire #2: `wiki/patterns/cdc-tableflow-flink-decode-required.md`** (pattern template, single-fact pattern)

    Source: `skills/confluent-cloud-cdc-tableflow/SKILL.md`

    Frontmatter (tags include `pattern` since pattern template; all comma-separated):
    ```yaml
    title: Decode CDC With Flink Before Tableflow — Don't Sink Direct
    tags: [trip-wire, pattern, tableflow, cdc, flink, confluent-cloud, confluent-agent-skills]
    related: [patterns/cdc-to-tableflow-flink-decode, concepts/tableflow-changelog-mode-immutability, concepts/cdc-source-connector-setup]
    ```

    Summary opener: "Don't enable Tableflow on a CDC source topic. Debezium emits null-value tombstones for deletes, which break Tableflow APPEND mode (the default). Decode the CDC stream through Flink first, sink to a clean topic, then enable Tableflow on the clean topic."

    Pattern body sections: Pattern, When to Use, Caveats, Related. MCP-validate the Debezium tombstone behavior claim via `confluent-docs`. Provide a 4-line Flink SQL snippet showing the decode pattern.

    ---

    **Trip-wire #3: `wiki/concepts/oracle-xstream-source-limitations.md`**

    Source: `skills/confluent-cloud-cdc-tableflow/SKILL.md`

    Frontmatter (tags comma-separated):
    ```yaml
    tags: [trip-wire, cdc, oracle, confluent-cloud, confluent-agent-skills]
    ```

    Summary opener: "The `OracleXStreamSource` connector does not support the `after.state.only` configuration option. To emit only post-image state from XStream, apply a Flink transform on the source topic before sinking to the downstream topic."

    MCP-validate via `confluent-docs` query on `OracleXStreamSource` connector reference. If the doc explicitly lists supported configs and `after.state.only` is absent (or marked Postgres-only), claim is confirmed.

    `related:` includes `concepts/cdc-source-connector-setup` (parent #8).

    ---

    **Trip-wire #4: `wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md`**

    Source: `skills/kafka-streams-programming/SKILL.md` (also cite evals.json existence in body text, but `upstream_path` is the SKILL.md per D-02/D-05 tension resolution above)

    Frontmatter (tags comma-separated):
    ```yaml
    tags: [trip-wire, kafka-streams, java, error-handling, confluent-agent-skills]
    ```

    Summary opener: "In Kafka Streams 4.x, `StreamsUncaughtExceptionHandler` lives in the `org.apache.kafka.streams.errors` package. It is NOT a nested class under `KafkaStreams` (that was the 2.8–3.x shape). Code copy-pasted from older guides will fail to compile."

    Include a 3-line Java snippet:
    ```java
    import org.apache.kafka.streams.errors.StreamsUncaughtExceptionHandler;
    streams.setUncaughtExceptionHandler((StreamsUncaughtExceptionHandler) exception ->
        StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse.SHUTDOWN_CLIENT);
    ```

    MCP-validate via `confluent-docs` (Kafka Streams Javadoc / migration guide for 4.x). `related:` includes `concepts/kafka-streams-debugging` (parent #2), `concepts/kafka-streams-production-hardening` (parent #3).

    ---

    **Trip-wire #5: `wiki/concepts/avro-schema-source-directory.md`**

    Source: `skills/kafka-streams-programming/SKILL.md` (D-02/D-05 tension: evals.json cited by path in body only, not as upstream_path)

    Frontmatter (tags comma-separated):
    ```yaml
    tags: [trip-wire, avro, maven, schema-registry, confluent-agent-skills]
    ```

    Summary opener: "Avro schemas live in `src/main/avro/` — the Avro Maven Plugin's canonical source directory. NOT `src/main/resources/avro/`. Putting them in `resources/` silently skips code generation; you'll get a compile error trying to instantiate the generated classes (because they were never generated)."

    Include a 4-line `pom.xml` snippet showing the `avro-maven-plugin` config with explicit `<sourceDirectory>${project.basedir}/src/main/avro</sourceDirectory>`.

    MCP-validate via `context7` (Avro Maven Plugin canonical layout) with `confluent-docs` fallback. `related:` includes `concepts/kafka-streams-debugging` (parent #2), `concepts/kafka-streams-schema-patterns` (parent #4).

    ---

    **Trip-wire #6: `wiki/concepts/schema-aware-console-producer-required.md`**

    Source: `skills/kafka-streams-programming/SKILL.md` (D-02/D-05 tension: evals.json cited by path in body only)

    Frontmatter (tags comma-separated):
    ```yaml
    tags: [trip-wire, schema-registry, cli, kafka-tools, confluent-agent-skills]
    ```

    Summary opener: "`kafka-console-producer` does not speak Schema Registry. Using it against an SR-governed topic ships records without the 5-byte wire-format prefix (magic byte + 4-byte schema ID), breaking every SR-aware consumer. Use `kafka-avro-console-producer`, `kafka-protobuf-console-producer`, or `kafka-json-schema-console-producer` for verification on SR-governed topics."

    Include a 2-line CLI invocation example:
    ```bash
    kafka-avro-console-producer --bootstrap-server localhost:9092 --topic payments.transaction.events \
      --property schema.registry.url=http://localhost:8081 --property value.schema='{"type":"record",...}'
    ```

    MCP-validate via `confluent-docs` (CLI reference for `kafka-avro-console-producer`). `related:` includes `concepts/schema-registry-best-practices`, `concepts/kafka-streams-debugging` (parent #2).

    ---

    **All 6 articles:**
    - Body ≤500 words (count the prose; code blocks excluded from the limit)
    - All `tags:` arrays comma-separated (Issue 1 blocker fix)
    - Italicized provenance footer:
      ```markdown
      ---

      *Source: confluentinc/agent-skills@91d1871e · skills/<skill>/<file> · Ingested 2026-05-16 (full MCP-validation gate per D-07) · Apache-2.0*
      ```
    - Trip-wires #4, #5, #6 ALSO cite the upstream `evals/evals.json` in body prose as proof of importance (one sentence: "This trip-wire is encoded as an upstream eval assertion at `skills/kafka-streams-programming/evals/evals.json` — it would fail an upstream merge if violated.") — the evals.json file is intentionally not vendored (D-02), so the citation is path-only, not link.

    Do NOT update `_index.md`, `_graph.md`, or `raw/_ingest.md` in this task. Task 4 handles those.
  </action>
  <verify>
    <automated>
      test -f wiki/concepts/tableflow-changelog-mode-immutability.md &amp;&amp;
      test -f wiki/patterns/cdc-tableflow-flink-decode-required.md &amp;&amp;
      test -f wiki/concepts/oracle-xstream-source-limitations.md &amp;&amp;
      test -f wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md &amp;&amp;
      test -f wiki/concepts/avro-schema-source-directory.md &amp;&amp;
      test -f wiki/concepts/schema-aware-console-producer-required.md &amp;&amp;
      grep -l "trip-wire" wiki/concepts/tableflow-changelog-mode-immutability.md wiki/patterns/cdc-tableflow-flink-decode-required.md wiki/concepts/oracle-xstream-source-limitations.md wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md wiki/concepts/avro-schema-source-directory.md wiki/concepts/schema-aware-console-producer-required.md | wc -l | awk '$1 != 6 { print "FAIL"; exit 1 } { print "OK: 6 trip-wire tags" }' &amp;&amp;
      grep -l "confidence: high" wiki/concepts/tableflow-changelog-mode-immutability.md wiki/patterns/cdc-tableflow-flink-decode-required.md wiki/concepts/oracle-xstream-source-limitations.md wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md wiki/concepts/avro-schema-source-directory.md wiki/concepts/schema-aware-console-producer-required.md | wc -l | awk '$1 != 6 { print "FAIL"; exit 1 } { print "OK: 6 confidence:high" }' &amp;&amp;
      grep -l "source: confluent-agent-skills@91d1871" wiki/concepts/tableflow-changelog-mode-immutability.md wiki/patterns/cdc-tableflow-flink-decode-required.md wiki/concepts/oracle-xstream-source-limitations.md wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md wiki/concepts/avro-schema-source-directory.md wiki/concepts/schema-aware-console-producer-required.md | wc -l | awk '$1 != 6 { print "FAIL"; exit 1 } { print "OK: 6 source: fields" }' &amp;&amp;
      grep -q "org.apache.kafka.streams.errors" wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md &amp;&amp;
      grep -q "src/main/avro" wiki/concepts/avro-schema-source-directory.md &amp;&amp;
      grep -q "kafka-avro-console-producer" wiki/concepts/schema-aware-console-producer-required.md
    </automated>
  </verify>
  <done>
    All 6 non-WarpStream trip-wire articles exist with `trip-wire` tag, `confidence: high`, locked source frontmatter (comma-separated tags arrays), and the load-bearing factual content (import path, source dir, console-producer name) appearing in the body. MCP-validation gate run for each.
  </done>
</task>

<task type="auto">
  <name>Task 3: Author the 3 WarpStream trip-wires (#7, #8, #9) with verbatim FSI-context paragraph</name>
  <files>
    wiki/concepts/warpstream-schema-registry-format-constraint.md,
    wiki/concepts/warpstream-config-overrides.md,
    wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md
  </files>
  <read_first>
    - .planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md (D-05 table 2 rows 7–9; <specifics> "WarpStream framing — concrete" — the FSI-context paragraph is verbatim, not paraphrased; canonical_refs feedback memory reference)
    - .planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md (canonical_refs section: feedback_confluent_supported_connectors.md — vendor-backing rule)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/developing-kafka-python-client/SKILL.md (source for #7)
    - raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/warpstream-optimization.md (source for #8, #9; ALSO a secondary citation source for #7)
    - wiki/concepts/exactly-once-semantics.md (existing — natural cross-link for #9)
    - wiki/concepts/schema-registry-best-practices.md (existing — natural cross-link for #7; also canonical YAML tag-array exemplar at line 3)
  </read_first>
  <action>
    Same /wiki:ingest 6-step flow as Task 2, but with three additional constraints unique to WarpStream content:

    1. **MANDATORY FSI-context paragraph** — verbatim from CONTEXT.md `<specifics>` "WarpStream framing — concrete". Goes in the body, immediately after the trip-wire claim, BEFORE the `## Detail` section. The paragraph must appear character-for-character; do NOT paraphrase. Reproduced here for executor convenience:

       > **FSI context:** WarpStream is not Confluent. FSI customer engagements require vendor-contracted tooling per the canon overlay stack — Confluent has a contractual support relationship; WarpStream does not. This article exists as **competitive context for SA conversations and customer comparison-shopping**, not as FSI production guidance. If a customer is evaluating WarpStream as a cost-reduction alternative, use this article to brief them on the limitations they'll inherit; do not deploy WarpStream against FSI workloads without explicit vendor-contract sign-off (which has not been observed at time of writing).

       This paragraph must appear verbatim in ALL THREE WarpStream articles (#7, #8, #9). Place it in the Summary section directly after the single-fact claim line.

    2. **MCP-validation caveat:** WarpStream is not in `confluent-docs` (vendor-backing rule). Per the MCP routing table in `<interfaces>`:
       - For #7, #8: `context7` primary; inline `> ⚠️ unverified — <claim>` markers where context7 has no coverage. If majority of claims unverifiable, downgrade to `confidence: medium` per quality-standards.md rules. If majority verifiable via context7, keep `high`.
       - For #9: split coverage — the `exactly_once_v2` + idempotent-producer interaction part validates via `confluent-docs` (`processing.guarantee` / `max.in.flight.requests.per.connection` / `enable.idempotence`); the WarpStream-specific throughput-cost claim validates via `context7` or carries `⚠️ unverified`.

    3. **Tags:** every WarpStream article includes `warpstream`, `competitive-context`, `trip-wire`, `confluent-agent-skills` in `tags:` (comma-separated per Issue 1 blocker fix). The `competitive-context` tag is the discoverability signal that says "this is comparison material, not FSI guidance" — useful for `/ask` and `/review` to surface the framing without re-reading the body.

    ---

    **Trip-wire #7: `wiki/concepts/warpstream-schema-registry-format-constraint.md`**

    Source: PRIMARY `skills/developing-kafka-python-client/SKILL.md`; SECONDARY `skills/kafka-streams-programming/references/warpstream-optimization.md` (per Issue 6 fix — trip-wire #7's `sources:` must list BOTH vendored paths, not just the python-client SKILL.md)

    Frontmatter (Issue 6 fix — `sources:` is a YAML list of BOTH vendored paths):
    ```yaml
    title: WarpStream Schema Registry Supports Only Avro and Protobuf — No JSON Schema
    tags: [trip-wire, warpstream, competitive-context, schema-registry, confluent-agent-skills]
    sources:
      - raw/vendor/confluent-agent-skills/91d1871e/skills/developing-kafka-python-client/SKILL.md
      - raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/warpstream-optimization.md
    related: [concepts/schema-registry-best-practices, concepts/warpstream-config-overrides, concepts/exactly-once-v2-warpstream-throughput-cost]
    confidence: high
    last_updated: 2026-05-16
    last_validated: 2026-05-16
    source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
    upstream_path: skills/developing-kafka-python-client/SKILL.md
    ```

    Summary opener: "WarpStream's built-in Schema Registry only supports Avro and Protobuf. A `GET /schemas/types` request returns `[\"AVRO\",\"PROTOBUF\"]` — no JSON Schema support, despite JSON Schema being a first-class format in Confluent's Schema Registry."

    Then immediately: the verbatim FSI-context paragraph.

    Then `## Detail`: query example with curl, what fails if a client tries to register a JSON Schema subject (HTTP 415 or 422 response), and the workaround if JSON Schema is required (run an external Schema Registry pointed at WarpStream-stored `_schemas` topic — but this is operationally awkward and not the WarpStream-recommended path).

    Provenance footer must list BOTH source files separated by ` · `:
    ```markdown
    *Source: confluentinc/agent-skills@91d1871e · skills/developing-kafka-python-client/SKILL.md · skills/kafka-streams-programming/references/warpstream-optimization.md · Ingested 2026-05-16 (full MCP-validation gate per D-07) · Apache-2.0*
    ```

    ---

    **Trip-wire #8: `wiki/concepts/warpstream-config-overrides.md`**

    Source: `skills/kafka-streams-programming/references/warpstream-optimization.md`

    Frontmatter (tags comma-separated):
    ```yaml
    title: WarpStream Config Drift — fetch.min.bytes Ignored, replication.factor Cosmetic
    tags: [trip-wire, warpstream, competitive-context, configuration, confluent-agent-skills]
    sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/warpstream-optimization.md]
    related: [concepts/warpstream-schema-registry-format-constraint, concepts/exactly-once-v2-warpstream-throughput-cost, concepts/kafka-streams-config-baseline]
    ```
    + standard source/upstream_path/dates.

    Summary opener: "Two Kafka client/topic configs do NOT behave on WarpStream the way they do on classic Kafka: `fetch.min.bytes` is silently ignored (WarpStream batches based on its own S3-pull cadence, not consumer fetch hints); `replication.factor` is cosmetic — the WarpStream tier always replicates 3-way across S3-backed virtual brokers regardless of the value set at topic creation time."

    Then: verbatim FSI-context paragraph.

    Then `## Detail`: explain the implications — fetch latency tuning is no longer client-controllable (use WarpStream's region/cluster pull cadence settings instead); RF=1 on a WarpStream topic looks like a durability red flag but is actually fine (still 3-way replicated internally) — confusing in FSI compliance reviews, document the explanation.

    ---

    **Trip-wire #9: `wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md`**

    Source: `skills/kafka-streams-programming/references/warpstream-optimization.md`

    Frontmatter (tags comma-separated):
    ```yaml
    title: exactly_once_v2 on WarpStream — Throughput Cost from Idempotent-Producer Throttling
    tags: [trip-wire, warpstream, competitive-context, exactly-once, eos, confluent-agent-skills]
    sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/warpstream-optimization.md]
    related: [concepts/exactly-once-semantics, concepts/warpstream-config-overrides, concepts/kafka-streams-production-hardening]
    ```

    Summary opener: "Setting `processing.guarantee=exactly_once_v2` in Kafka Streams enables idempotent producers internally, which caps `max.in.flight.requests.per.connection ≤ 5` — on classic Kafka this is a modest cost, but on WarpStream's S3-backed storage tier the in-flight cap interacts with per-partition pull cadence to produce a meaningful throughput hit. Quantify before enabling EOS on high-throughput WarpStream pipelines."

    Then: verbatim FSI-context paragraph.

    Then `## Detail`: cite confluent-docs MCP confirmation of `max.in.flight.requests.per.connection ≤ 5` constraint under `enable.idempotence=true` (this is the classic-Kafka half — MCP-verifiable). Cite context7 / WarpStream docs for the throughput-cost claim (or inline `⚠️ unverified` if context7 doesn't cover). Suggest a benchmark recipe (produce a synthetic 1MB/s and 10MB/s workload with `processing.guarantee=at_least_once` and `=exactly_once_v2` on a WarpStream test cluster; compare consumer lag and produce rate; expect 20–40% throughput delta).

    ---

    **All 3 articles:**
    - Body ≤500 words including the FSI-context paragraph (the paragraph is ~110 words; leaves ~390 for prose — tight, kept by being terse)
    - All `tags:` arrays comma-separated (Issue 1 blocker fix)
    - Italicized provenance footer naming the upstream file(s) — trip-wire #7's footer lists BOTH source files per Issue 6 fix
    - The FSI-context paragraph is character-for-character verbatim; if minor punctuation changes appear in the executor's output, they fail the "verbatim" requirement and must be fixed

    Do NOT update `_index.md`, `_graph.md`, or `raw/_ingest.md` in this task.
  </action>
  <verify>
    <automated>
      test -f wiki/concepts/warpstream-schema-registry-format-constraint.md &amp;&amp;
      test -f wiki/concepts/warpstream-config-overrides.md &amp;&amp;
      test -f wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md &amp;&amp;
      for f in wiki/concepts/warpstream-schema-registry-format-constraint.md wiki/concepts/warpstream-config-overrides.md wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md; do
        grep -q "WarpStream is not Confluent" "$f" || { echo "FAIL: $f missing verbatim FSI-context opener"; exit 1; }
        grep -q "competitive context for SA conversations" "$f" || { echo "FAIL: $f missing verbatim FSI-context middle"; exit 1; }
        grep -q "vendor-contract sign-off" "$f" || { echo "FAIL: $f missing verbatim FSI-context closer"; exit 1; }
        grep -q "competitive-context" "$f" || { echo "FAIL: $f missing competitive-context tag"; exit 1; }
        grep -q "warpstream" "$f" || { echo "FAIL: $f missing warpstream tag"; exit 1; }
      done &amp;&amp;
      # Issue 6 fix verification: trip-wire #7's `sources:` lists BOTH vendored paths
      grep -q "skills/developing-kafka-python-client/SKILL.md" wiki/concepts/warpstream-schema-registry-format-constraint.md &amp;&amp;
      grep -q "skills/kafka-streams-programming/references/warpstream-optimization.md" wiki/concepts/warpstream-schema-registry-format-constraint.md &amp;&amp;
      echo "OK: all 3 WarpStream trip-wires include verbatim FSI-context + competitive-context tag; trip-wire #7 lists both sources"
    </automated>
  </verify>
  <done>
    All 3 WarpStream trip-wire articles exist with the verbatim FSI-context paragraph, the `competitive-context` tag, comma-separated tag arrays, and the locked frontmatter. Trip-wire #7's `sources:` lists both vendored paths (python-client SKILL.md + warpstream-optimization.md) per Issue 6 fix. MCP-validation applied with documented `⚠️ unverified` markers where context7 was silent.
  </done>
</task>

<task type="auto">
  <name>Task 4: Update _index.md and _graph.md for 9 trip-wires; assert tag-array YAML shape; move queue entries to Processed; final clean wiki-lint pass</name>
  <files>wiki/_index.md, wiki/_graph.md, raw/_ingest.md</files>
  <read_first>
    - wiki/_index.md (current state — H.1-02 already added 10 parents under Concepts/Patterns)
    - wiki/_graph.md (current state — H.1-02 already added the "## H.1 — confluent-agent-skills ingest" block; this task EXTENDS it with trip-wire edges, closing the forward-references)
    - raw/_ingest.md (current state — 9 trip-wires still in Pending, 10 parents already Processed)
    - .claude/commands/wiki/ingest.md (Steps 4, 5, 6, 7)
  </read_first>
  <action>
    Implements /wiki:ingest Steps 4, 5, 6, 7 for the 9 trip-wires; closes WIKI-08 (index + graph updated, validate passes — full ownership per Issue 5 fix).

    **Step 4 — wiki/_index.md:** Append the 9 trip-wires under the correct sections (8 concepts, 1 pattern). Insert in alphabetical order within each section to keep the index navigable. Use exact format:

    Under `## Concepts` (insert alphabetically):
    ```
    [Avro Schema Source Directory](concepts/avro-schema-source-directory.md) — Trip-wire: Avro schemas live in src/main/avro/ NOT src/main/resources/avro/; code generation breaks silently if misplaced — #trip-wire #avro #confluent-agent-skills
    [exactly_once_v2 on WarpStream — Throughput Cost](concepts/exactly-once-v2-warpstream-throughput-cost.md) — Trip-wire: EOS v2 enables idempotent producer throttling; meaningful throughput hit on WarpStream's S3-backed tier — #trip-wire #warpstream #competitive-context #exactly-once #confluent-agent-skills
    [Kafka Streams 4.x Uncaught Exception Handler Import](concepts/kafka-streams-4x-uncaught-exception-handler-import.md) — Trip-wire: StreamsUncaughtExceptionHandler is in org.apache.kafka.streams.errors in KS 4.x, no longer a nested class under KafkaStreams — #trip-wire #kafka-streams #confluent-agent-skills
    [Oracle XStream Source Limitations](concepts/oracle-xstream-source-limitations.md) — Trip-wire: OracleXStreamSource doesn't support after.state.only; workaround via Flink transform — #trip-wire #cdc #oracle #confluent-agent-skills
    [Schema-Aware Console Producer Required](concepts/schema-aware-console-producer-required.md) — Trip-wire: kafka-console-producer doesn't speak Schema Registry; use kafka-avro-console-producer for SR-governed topics — #trip-wire #schema-registry #cli #confluent-agent-skills
    [Tableflow Changelog Mode Immutability](concepts/tableflow-changelog-mode-immutability.md) — Trip-wire: Tableflow CHANGELOG mode is immutable after first materialization; cannot switch to APPEND without recreate — #trip-wire #tableflow #confluent-cloud #confluent-agent-skills
    [WarpStream Config Overrides](concepts/warpstream-config-overrides.md) — Trip-wire: WarpStream silently ignores fetch.min.bytes; replication.factor is cosmetic (always 3-way internally) — #trip-wire #warpstream #competitive-context #configuration #confluent-agent-skills
    [WarpStream Schema Registry Format Constraint](concepts/warpstream-schema-registry-format-constraint.md) — Trip-wire: WarpStream built-in SR only supports Avro and Protobuf; no JSON Schema — #trip-wire #warpstream #competitive-context #schema-registry #confluent-agent-skills
    ```

    Under `## Patterns` (insert alphabetically):
    ```
    [CDC-Tableflow — Flink Decode Required](patterns/cdc-tableflow-flink-decode-required.md) — Trip-wire pattern: Don't enable Tableflow on CDC source topics; tombstones break APPEND mode; decode through Flink to a clean topic first — #trip-wire #pattern #tableflow #cdc #flink #confluent-cloud #confluent-agent-skills
    ```

    Bump `last_updated:` in `_index.md` frontmatter to `2026-05-16`.

    **Step 5 — wiki/_graph.md:** Extend the existing `## H.1 — confluent-agent-skills ingest (2026-05-16)` block with the 9 trip-wire edges. Every trip-wire needs ≥1 inbound + ≥1 outbound. The inbound edges from parent articles were forward-declared in H.1-02 — they are already in the graph and now resolve correctly. Add the OUTBOUND edges from each trip-wire (back to its parent + to sibling trip-wires per `related:` field):

    Append under the existing H.1 block (after the parents' edges, before any trailing content):

    ```
    # Trip-wires — outbound (close forward-references from parents)
    # Trip-wire #1: tableflow-changelog-mode-immutability
    concepts/tableflow-changelog-mode-immutability → patterns/cdc-to-tableflow-flink-decode : parent ingest article (back-link per D-06)
    concepts/tableflow-changelog-mode-immutability → patterns/cdc-tableflow-flink-decode-required : sibling trip-wire (Tableflow + CDC)
    concepts/tableflow-changelog-mode-immutability → concepts/oracle-xstream-source-limitations : sibling trip-wire (CDC-Tableflow cluster)

    # Trip-wire #2: cdc-tableflow-flink-decode-required
    patterns/cdc-tableflow-flink-decode-required → patterns/cdc-to-tableflow-flink-decode : parent ingest article (back-link per D-06)
    patterns/cdc-tableflow-flink-decode-required → concepts/tableflow-changelog-mode-immutability : sibling trip-wire
    patterns/cdc-tableflow-flink-decode-required → concepts/cdc-source-connector-setup : parent for CDC connector configs

    # Trip-wire #3: oracle-xstream-source-limitations
    concepts/oracle-xstream-source-limitations → concepts/cdc-source-connector-setup : parent ingest article (back-link per D-06)
    concepts/oracle-xstream-source-limitations → concepts/tableflow-changelog-mode-immutability : sibling trip-wire (CDC-Tableflow cluster)

    # Trip-wire #4: kafka-streams-4x-uncaught-exception-handler-import
    concepts/kafka-streams-4x-uncaught-exception-handler-import → concepts/kafka-streams-debugging : parent ingest article (back-link per D-06)
    concepts/kafka-streams-4x-uncaught-exception-handler-import → concepts/kafka-streams-production-hardening : closely-related parent
    concepts/kafka-streams-4x-uncaught-exception-handler-import → concepts/avro-schema-source-directory : sibling KS-programming trip-wire
    concepts/kafka-streams-4x-uncaught-exception-handler-import → concepts/schema-aware-console-producer-required : sibling KS-programming trip-wire

    # Trip-wire #5: avro-schema-source-directory
    concepts/avro-schema-source-directory → concepts/kafka-streams-debugging : parent ingest article (back-link per D-06)
    concepts/avro-schema-source-directory → concepts/kafka-streams-schema-patterns : parent for schema-patterns context
    concepts/avro-schema-source-directory → concepts/kafka-streams-4x-uncaught-exception-handler-import : sibling KS-programming trip-wire

    # Trip-wire #6: schema-aware-console-producer-required
    concepts/schema-aware-console-producer-required → concepts/schema-registry-best-practices : SR operational surface
    concepts/schema-aware-console-producer-required → concepts/kafka-streams-debugging : parent ingest article (back-link per D-06)
    concepts/schema-aware-console-producer-required → concepts/kafka-streams-4x-uncaught-exception-handler-import : sibling KS-programming trip-wire

    # Trip-wire #7: warpstream-schema-registry-format-constraint
    concepts/warpstream-schema-registry-format-constraint → concepts/schema-registry-best-practices : SR operational surface
    concepts/warpstream-schema-registry-format-constraint → concepts/warpstream-config-overrides : sibling WarpStream trip-wire
    concepts/warpstream-schema-registry-format-constraint → concepts/exactly-once-v2-warpstream-throughput-cost : sibling WarpStream trip-wire

    # Trip-wire #8: warpstream-config-overrides
    concepts/warpstream-config-overrides → concepts/kafka-streams-config-baseline : parent ingest article (back-link per D-06)
    concepts/warpstream-config-overrides → concepts/warpstream-schema-registry-format-constraint : sibling WarpStream trip-wire
    concepts/warpstream-config-overrides → concepts/exactly-once-v2-warpstream-throughput-cost : sibling WarpStream trip-wire

    # Trip-wire #9: exactly-once-v2-warpstream-throughput-cost
    concepts/exactly-once-v2-warpstream-throughput-cost → concepts/exactly-once-semantics : EOS foundation
    concepts/exactly-once-v2-warpstream-throughput-cost → concepts/kafka-streams-production-hardening : parent ingest article (back-link per D-06)
    concepts/exactly-once-v2-warpstream-throughput-cost → concepts/warpstream-config-overrides : sibling WarpStream trip-wire
    concepts/exactly-once-v2-warpstream-throughput-cost → concepts/warpstream-schema-registry-format-constraint : sibling WarpStream trip-wire
    ```

    Bump `last_updated:` in `_graph.md` frontmatter to `2026-05-16`.

    Inbound edges from existing wiki articles to trip-wires are already in place from H.1-02 (the parent articles' outbound edges to trip-wires) — verify those resolve now that the trip-wire targets exist.

    **Step 6 — Move 9 trip-wire entries from Pending to Processed in `raw/_ingest.md`:** Same pattern as H.1-02 Task 4 (Processed entry with `compiled: 2026-05-16` and `wiki_articles:` list). After this task, `## Pending` should contain only the two original April-2026 entries (`kafka-best-practices.md`, `kafka-recommendations.md`).

    **Step 7a — Assert tag-array YAML parse (Issue 1 blocker fix):** every new trip-wire article's `tags:` MUST parse as a YAML list:

    ```bash
    python3 -c "
    import yaml, glob, sys
    tripwires = [
        'wiki/concepts/tableflow-changelog-mode-immutability.md',
        'wiki/patterns/cdc-tableflow-flink-decode-required.md',
        'wiki/concepts/oracle-xstream-source-limitations.md',
        'wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md',
        'wiki/concepts/avro-schema-source-directory.md',
        'wiki/concepts/schema-aware-console-producer-required.md',
        'wiki/concepts/warpstream-schema-registry-format-constraint.md',
        'wiki/concepts/warpstream-config-overrides.md',
        'wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md',
    ]
    fail = 0
    for path in tripwires:
        try:
            content = open(path).read()
        except FileNotFoundError:
            print(f'FAIL: {path} not found'); fail += 1; continue
        if '---' not in content:
            print(f'FAIL: {path} has no frontmatter'); fail += 1; continue
        try:
            fm = yaml.safe_load(content.split('---')[1])
        except yaml.YAMLError as exc:
            print(f'FAIL: {path}: YAML parse error: {exc}'); fail += 1; continue
        tags = fm.get('tags')
        if not isinstance(tags, list):
            print(f'FAIL: {path}: tags is not a YAML list (got {type(tags).__name__}: {tags!r}) — did you forget commas in [a, b, c]?'); fail += 1
            continue
        if 'trip-wire' not in tags:
            print(f'FAIL: {path}: trip-wire tag absent from tags list'); fail += 1
            continue
        if len(tags) < 3:
            print(f'FAIL: {path}: tags list too short ({len(tags)} entries; trip-wires need ≥3)'); fail += 1
            continue
    if fail:
        sys.exit(1)
    print('OK: all 9 trip-wire articles have YAML-list tag arrays containing trip-wire tag')
    "
    ```

    **Step 7b — Final clean wiki-lint pass (Issue 9 minor fix):** the original verify ran a bare `python tools/wiki-lint.py` with no explicit zero-findings assertion. Replace with an explicit zero-findings check that distinguishes intentional `⚠️ unverified` markers (allowed in WarpStream articles) from actual findings:

    ```bash
    python tools/wiki-lint.py > /tmp/h1-03-wl.out 2>&1
    rc=$?
    # Hard findings — none of these may appear after H.1-03 completes (WIKI-08 zero-drift criterion).
    if grep -qE 'BROKEN|ORPHAN|DRIFT|MALFORMED|UNKNOWN VENDOR|SCHEMA|STALE' /tmp/h1-03-wl.out; then
      cat /tmp/h1-03-wl.out
      echo "FAIL: wiki-lint findings present after H.1-03 — WIKI-08 zero-drift criterion not yet met"
      exit 1
    fi
    if [ $rc -ne 0 ]; then
      cat /tmp/h1-03-wl.out
      echo "FAIL: wiki-lint exit code $rc"
      exit $rc
    fi
    echo "OK: wiki-lint clean — WIKI-08 zero-drift criterion satisfied"
    ```

    Acceptable (NOT findings, kept):
    - `⚠️ unverified` body markers in WarpStream articles (Task 3) — these are inline annotations, not wiki-lint output.

    If wiki-lint exits non-zero or any hard finding (BROKEN/ORPHAN/DRIFT/MALFORMED/UNKNOWN VENDOR/SCHEMA/STALE) appears, surface the findings and fix at root rather than suppressing.
  </action>
  <verify>
    <automated>
      grep -c "concepts/tableflow-changelog-mode-immutability.md\|patterns/cdc-tableflow-flink-decode-required.md\|concepts/oracle-xstream-source-limitations.md\|concepts/kafka-streams-4x-uncaught-exception-handler-import.md\|concepts/avro-schema-source-directory.md\|concepts/schema-aware-console-producer-required.md\|concepts/warpstream-schema-registry-format-constraint.md\|concepts/warpstream-config-overrides.md\|concepts/exactly-once-v2-warpstream-throughput-cost.md" wiki/_index.md | awk '{ if ($1 &lt; 9) { print "FAIL: expected 9 trip-wire entries, got " $1; exit 1 } else print "OK: " $1 " trip-wire entries in _index.md" }' &amp;&amp;
      for art in concepts/tableflow-changelog-mode-immutability patterns/cdc-tableflow-flink-decode-required concepts/oracle-xstream-source-limitations concepts/kafka-streams-4x-uncaught-exception-handler-import concepts/avro-schema-source-directory concepts/schema-aware-console-producer-required concepts/warpstream-schema-registry-format-constraint concepts/warpstream-config-overrides concepts/exactly-once-v2-warpstream-throughput-cost; do
        outbound=$(grep -cE "^${art} →" wiki/_graph.md)
        inbound=$(grep -cE "→ ${art}( |$)" wiki/_graph.md)
        if [ "$outbound" -lt 1 ] || [ "$inbound" -lt 1 ]; then
          echo "FAIL: $art outbound=$outbound inbound=$inbound (need ≥1 each)"
          exit 1
        fi
      done &amp;&amp; echo "OK: all 9 trip-wires have ≥1 inbound + ≥1 outbound" &amp;&amp;
      awk '/^## Pending/{in_pending=1; in_proc=0} /^## Processed/{in_pending=0; in_proc=1} /Trip-wire #/{ if(in_pending) p++; if(in_proc) q++ } END{ if (p != 0) { print "FAIL: " p " trip-wires still in Pending"; exit 1 } if (q != 9) { print "FAIL: " q " trip-wires in Processed, expected 9"; exit 1 } print "OK: 0 trip-wires in Pending, 9 in Processed" }' raw/_ingest.md &amp;&amp;
      python3 -c "
import yaml, sys
tripwires = [
    'wiki/concepts/tableflow-changelog-mode-immutability.md',
    'wiki/patterns/cdc-tableflow-flink-decode-required.md',
    'wiki/concepts/oracle-xstream-source-limitations.md',
    'wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md',
    'wiki/concepts/avro-schema-source-directory.md',
    'wiki/concepts/schema-aware-console-producer-required.md',
    'wiki/concepts/warpstream-schema-registry-format-constraint.md',
    'wiki/concepts/warpstream-config-overrides.md',
    'wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md',
]
fail = 0
for path in tripwires:
    content = open(path).read()
    fm = yaml.safe_load(content.split('---')[1])
    tags = fm.get('tags')
    if not isinstance(tags, list):
        print(f'FAIL: {path}: tags not a YAML list (got {type(tags).__name__}: {tags!r}) — forgot commas?'); fail += 1
        continue
    if 'trip-wire' not in tags:
        print(f'FAIL: {path}: trip-wire tag absent'); fail += 1
if fail: sys.exit(1)
print('OK: all 9 trip-wire tag arrays parse as YAML lists with trip-wire tag')
" &amp;&amp;
      python tools/wiki-lint.py > /tmp/h1-03-wl.out 2>&amp;1; rc=$?;
      if grep -qE 'BROKEN|ORPHAN|DRIFT|MALFORMED|UNKNOWN VENDOR|SCHEMA|STALE' /tmp/h1-03-wl.out; then cat /tmp/h1-03-wl.out; echo "FAIL: wiki-lint findings present after H.1-03"; exit 1; fi;
      [ $rc -eq 0 ] || { cat /tmp/h1-03-wl.out; echo "FAIL: wiki-lint exit code $rc"; exit $rc; };
      echo "OK: wiki-lint clean — WIKI-08 zero-drift criterion satisfied"
    </automated>
  </verify>
  <done>
    `wiki/_index.md` has 9 new trip-wire entries (8 concepts + 1 pattern, alphabetized within section); `wiki/_graph.md` has ≥1 inbound + ≥1 outbound for each trip-wire; `raw/_ingest.md` shows 0 trip-wires in Pending, 9 in Processed; every trip-wire article's `tags:` parses as a YAML list with `trip-wire` tag present (Issue 1 fix); `python tools/wiki-lint.py` exits 0 with NO BROKEN/ORPHAN/DRIFT/MALFORMED/UNKNOWN VENDOR/SCHEMA/STALE findings (Issue 9 fix — explicit zero-findings assertion).
  </done>
</task>

</tasks>

<verification>
After all 4 tasks pass:

1. 9 trip-wire articles exist at locked paths with `trip-wire` tag, `confidence: high`, full MCP-validation per D-07, comma-separated `tags:` arrays.
2. WarpStream articles (#7, #8, #9) include verbatim FSI-context paragraph + `competitive-context` tag.
3. Trip-wire #7's `sources:` lists BOTH vendored paths (python-client SKILL.md + warpstream-optimization.md) per Issue 6 fix.
4. `wiki/_index.md` lists all 19 H.1 articles (10 parents + 9 trip-wires) under correct sections.
5. `wiki/_graph.md` has ≥1 inbound + ≥1 outbound per trip-wire; forward-references from H.1-02 now resolve.
6. `tools/wiki-lint.py` has working drift detection (5 pytest cases pass); full lint run exits 0 with NO hard findings (Issue 9 fix).
7. `raw/_ingest.md` ## Pending has only the two original April-2026 entries.

Roll-up:
```bash
test $(ls wiki/concepts/tableflow-changelog-mode-immutability.md wiki/patterns/cdc-tableflow-flink-decode-required.md wiki/concepts/oracle-xstream-source-limitations.md wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md wiki/concepts/avro-schema-source-directory.md wiki/concepts/schema-aware-console-producer-required.md wiki/concepts/warpstream-schema-registry-format-constraint.md wiki/concepts/warpstream-config-overrides.md wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md 2>/dev/null | wc -l) -eq 9 &&
grep -c "WarpStream is not Confluent" wiki/concepts/warpstream-*.md wiki/concepts/exactly-once-v2-warpstream-*.md | grep -c ":1" | awk '{ if ($1 == 3) print "OK: 3 WarpStream FSI-context paragraphs"; else { print "FAIL"; exit 1 } }' &&
python -m pytest tests/test_wiki_lint_drift.py -v &&
python tools/wiki-lint.py
```
</verification>

<success_criteria>
- 9 trip-wire articles exist at locked paths, each ≤500 words, with `trip-wire` tag, `confidence: high`, full MCP-validation gate run (D-07), comma-separated tag arrays (Issue 1 fix)
- WarpStream trip-wires (#7, #8, #9) contain verbatim FSI-context paragraph
- Trip-wire #7's `sources:` lists both vendored paths (Issue 6 fix)
- `wiki/_index.md` has all 9 trip-wire entries
- `wiki/_graph.md` has ≥1 inbound + ≥1 outbound for each trip-wire
- `tools/wiki-lint.py` drift detection works (5 pytest cases pass) and runs alongside existing decay check
- Full `python tools/wiki-lint.py` exits 0 — zero broken links, orphans, drift, decay, schema violations (Issue 9 fix — explicit zero-findings assertion)
- `raw/_ingest.md` ## Pending has 0 H.1 entries (all 19 moved to Processed across H.1-02 and H.1-03)
- WIKI-07 (≥8 trip-wires): SATISFIED (9 trip-wires)
- WIKI-08 (validate passes, index + graph updated): SATISFIED — full ownership (Issue 5 fix)
</success_criteria>

<output>
After completion, create `.planning/phases/H.1-wiki-ingest-agent-skills/H.1-03-SUMMARY.md` capturing:
- Final 9 trip-wire paths
- MCP-validation outcomes per trip-wire (claims confirmed, corrected, marked ⚠️ unverified)
- Any context7 gaps on WarpStream that forced inline ⚠️ unverified markers
- Final wiki-lint output (paste verbatim) — must show zero hard findings
- Total wiki article count before H.1 (37) and after (37 + 19 = 56)
- Drift-detection extension diff for `tools/wiki-lint.py` (lines added)
- Confirmation that every trip-wire's `tags:` parses as a YAML list (Issue 1 verification)
- Confirmation that trip-wire #7's `sources:` lists both vendored paths (Issue 6 verification)
- Any deviations from CONTEXT.md D-05 trip-wire targets (target ≥9 — should be exactly 9)
</output>
</content>
</invoke>