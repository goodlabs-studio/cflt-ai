---
phase: H.2-eval-harness-extension
plan: 02
type: execute
wave: 2
depends_on: [H.2-01]
files_modified:
  - tests/evals/wiki-ingest/evals.json
  - tests/evals/wiki-validate/evals.json
  - tests/evals/wiki-lint/evals.json
  - tests/evals/wiki-recommend/evals.json
autonomous: true
requirements: [EVAL-02, EVAL-03]
requirements_addressed: [EVAL-02, EVAL-03]

must_haves:
  truths:
    - "Each of /wiki:ingest, /wiki:validate, /wiki:lint, /wiki:recommend has an evals.json file with >= 10 cases"
    - "The 2 H.1 trip-wires assigned to /wiki:ingest per D-08 (avro-schema-source-directory, warpstream-config-overrides) are encoded as expectations[] strings verbatim from CONTEXT.md"
    - "All 40 new JSON cases use the upstream confluentinc/agent-skills schema verbatim per D-03"
    - "Every expectation string is grep-checkable per D-04 — no LLM-judgment assertions"
    - "After this plan + Plan 03 land, test_all_seven_new_skills_discovered passes (all 7 skills present in tests/evals/)"
  artifacts:
    - path: "tests/evals/wiki-ingest/evals.json"
      provides: "10 cases for /wiki:ingest skill, including the 2 H.1 trip-wires (avro-schema-source-directory + warpstream-config-overrides)"
      contains: "Avro schemas live in src/main/avro/"
    - path: "tests/evals/wiki-validate/evals.json"
      provides: "10 cases for /wiki:validate covering drift, decay, broken-link, orphan, schema-violation, source-attestation"
    - path: "tests/evals/wiki-lint/evals.json"
      provides: "10 cases for /wiki:lint covering broken-link, orphan, malformed, decay, drift, schema, exit-code, --fix flag"
    - path: "tests/evals/wiki-recommend/evals.json"
      provides: "10 cases for /wiki:recommend covering alias-dispatch, write-back, queue-stub, no-coverage"
  key_links:
    - from: "tests/evals/wiki-ingest/evals.json"
      to: "tests/evals/run_skill_evals.py"
      via: "load_json_cases() glob discovery — runner picks up evals.json from each subdir"
      pattern: "skill_name.*wiki:ingest"
    - from: "tests/evals/wiki-ingest/evals.json"
      to: "wiki/concepts/avro-schema-source-directory.md (H.1 trip-wire #5)"
      via: "expectation string referencing src/main/avro/ — keeps wiki + skill harness in lockstep per D-08"
      pattern: "src/main/avro/"
    - from: "tests/evals/wiki-ingest/evals.json"
      to: "wiki/concepts/warpstream-config-overrides.md (H.1 trip-wire #8)"
      via: "expectation string flagging unsupported fetch.min.bytes per D-08"
      pattern: "fetch.min.bytes"
---

<objective>
Author the 4 new evals.json files for the wiki-skill family — `/wiki:ingest`, `/wiki:validate`, `/wiki:lint`, `/wiki:recommend` — using the upstream confluentinc/agent-skills schema verbatim (D-03). Each file has ≥10 cases. The `/wiki:ingest` file additionally encodes the 2 trip-wires assigned to it per D-08 (avro-schema-source-directory, warpstream-config-overrides).

This plan addresses EVAL-02 for 4 of the 7 named skills (Plan 03 covers /review, /dsp:plan, /dsp:apply). It addresses EVAL-03 partially via the 2 trip-wires landing in /wiki:ingest (the other 7 trip-wires land via Plan 03).

Purpose: Close the EVAL-02 silent-drift gap for the four wiki-management skills. Source cases from real-world signals — `wiki/_queue.md` for coverage gaps, `raw/_ingest.md` Processed entries for happy paths, the H.1-03 wiki-lint TDD test suite for lint behaviors (per CONTEXT.md D-11).

Output: 4 new JSON files. No changes to runner, no changes to existing MD harnesses, no changes to `tools/apply_engine.py` or `.claude/commands/dsp-apply.md`.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/H.2-eval-harness-extension/H.2-CONTEXT.md
@.planning/phases/H.2-eval-harness-extension/H.2-01-PLAN.md
@.claude/commands/wiki/ingest.md
@.claude/commands/wiki/validate.md
@.claude/commands/wiki/lint.md
@.claude/commands/wiki/recommend.md
@wiki/_queue.md
@raw/_ingest.md
@wiki/concepts/avro-schema-source-directory.md
@wiki/concepts/warpstream-config-overrides.md

<interfaces>
<!-- Verbatim upstream schema from D-03 (CONTEXT.md). Each evals.json file MUST conform. -->
{
  "skill_name": "/wiki:ingest" | "/wiki:validate" | "/wiki:lint" | "/wiki:recommend",
  "evals": [
    {
      "id": 1,                          // integer, 1-indexed per file
      "prompt": "string — what the user asked /wiki:<verb> to do",
      "expected_output": "string — short description of the artifact or signal /wiki:<verb> should produce",
      "files": ["optional", "fixture", "paths"],
      "expectations": ["grep-checkable assertion 1", "grep-checkable assertion 2", "..."]
    }
  ]
}

<!-- D-08 verbatim trip-wire expectation strings (FOR /wiki:ingest — copy verbatim, do not paraphrase): -->
- "When ingesting an article that proposes Avro schemas under `src/main/resources/avro/`, MCP-validation flags this as incorrect and the article cites `src/main/avro/` instead"
- "When ingesting an article that proposes WarpStream `fetch.min.bytes` config, MCP-validation flags this as unsupported and the article documents the omission"
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Author tests/evals/wiki-ingest/evals.json (10 cases, including the 2 D-08 trip-wires verbatim)</name>
  <files>tests/evals/wiki-ingest/evals.json</files>
  <read_first>
    - tests/evals/wiki-ingest/evals.json (will not exist — confirm and create)
    - .planning/phases/H.2-eval-harness-extension/H.2-CONTEXT.md (D-03 schema lock, D-08 trip-wire verbatim strings)
    - tests/evals/fixtures/sample_evals.json (shape reference — but is fixture-only, not a content template)
    - .claude/commands/wiki/ingest.md (the skill being tested — to ground prompts in real behavior)
    - raw/_ingest.md (Processed section — real ingest history, source for happy-path prompts)
    - wiki/_queue.md (Stubs section — real coverage gaps, source for "I want to ingest X" prompts)
    - wiki/concepts/avro-schema-source-directory.md (the trip-wire #5 article — confirms the assertion direction)
    - wiki/concepts/warpstream-config-overrides.md (the trip-wire #8 article — confirms the assertion direction)
  </read_first>
  <behavior>
    - Test 1: File parses as valid JSON.
    - Test 2: Top-level keys are exactly `skill_name` and `evals` (no additions per D-03 verbatim lock).
    - Test 3: `skill_name == "/wiki:ingest"`.
    - Test 4: `len(evals) >= 10`.
    - Test 5: Every `evals[i]` has fields `id` (integer), `prompt` (non-empty string), `expected_output` (non-empty string), `expectations` (list of >= 1 non-empty strings). `files` is optional (per upstream schema).
    - Test 6: Case IDs are unique integers 1..N (1-indexed, dense).
    - Test 7: Exactly one case encodes the avro-source-directory trip-wire — its `expectations[]` contains the verbatim string `"When ingesting an article that proposes Avro schemas under `src/main/resources/avro/`, MCP-validation flags this as incorrect and the article cites `src/main/avro/` instead"`.
    - Test 8: Exactly one case encodes the WarpStream fetch.min.bytes trip-wire — its `expectations[]` contains the verbatim string `"When ingesting an article that proposes WarpStream `fetch.min.bytes` config, MCP-validation flags this as unsupported and the article documents the omission"`.
    - Test 9: At least one case references a real `raw/_ingest.md` Processed entry as a happy-path scenario.
    - Test 10: At least one case references a real `wiki/_queue.md` stub as a "fill the gap" scenario.
  </behavior>
  <action>
    Create `tests/evals/wiki-ingest/evals.json`. Use the verbatim upstream schema (D-03). Author 10 cases drawn from CONTEXT.md D-11 sources.

    **CRITICAL: the two trip-wire expectation strings from CONTEXT.md `<specifics>` D-08 must be COPIED VERBATIM into the relevant cases — do not paraphrase, do not adjust punctuation, do not change the backticks.** Verbatim trip-wire strings:

    1. (Trip-wire #5, Avro source dir):
       `"When ingesting an article that proposes Avro schemas under `src/main/resources/avro/`, MCP-validation flags this as incorrect and the article cites `src/main/avro/` instead"`

    2. (Trip-wire #8, WarpStream fetch.min.bytes):
       `"When ingesting an article that proposes WarpStream `fetch.min.bytes` config, MCP-validation flags this as unsupported and the article documents the omission"`

    JSON encoding note: backticks inside JSON strings are valid — write them verbatim. The whole expectation is a single JSON string (the outer `"` are the JSON quotes).

    Authored cases (concrete content, no paraphrasing — these are the prompts and expectations):

    ```json
    {
      "skill_name": "/wiki:ingest",
      "evals": [
        {
          "id": 1,
          "prompt": "Ingest the Kafka Streams topology-patterns reference at raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/topology-patterns.md into wiki/patterns/.",
          "expected_output": "A new wiki/patterns/kafka-streams-topology-patterns.md article with source: confluent-agent-skills@<sha> frontmatter and a provenance footer citing the upstream path.",
          "files": ["raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/topology-patterns.md"],
          "expectations": [
            "Output article frontmatter includes `source: confluent-agent-skills@91d1871e`",
            "Output article frontmatter includes `upstream_path: skills/kafka-streams-programming/references/topology-patterns.md`",
            "Output article includes a provenance footer line beginning with `Source: confluentinc/agent-skills@`",
            "Output article path is `wiki/patterns/kafka-streams-topology-patterns.md` (no vendor-prefix in filename per H.1 D-04)"
          ]
        },
        {
          "id": 2,
          "prompt": "Ingest a draft article that proposes placing Avro schemas under `src/main/resources/avro/`. Validate against upstream Confluent canon before writing.",
          "expected_output": "MCP-validation flags the path as incorrect and the resulting article cites `src/main/avro/` (Gradle and Maven Avro plugin default).",
          "files": [],
          "expectations": [
            "When ingesting an article that proposes Avro schemas under `src/main/resources/avro/`, MCP-validation flags this as incorrect and the article cites `src/main/avro/` instead",
            "Resulting article includes `src/main/avro/` as the canonical directory",
            "Resulting article does NOT cite `src/main/resources/avro/` as a recommendation"
          ]
        },
        {
          "id": 3,
          "prompt": "Ingest a draft article on WarpStream tuning that proposes setting `fetch.min.bytes=1024`. Validate against upstream Confluent canon and WarpStream documentation before writing.",
          "expected_output": "MCP-validation flags fetch.min.bytes as unsupported on WarpStream; the article documents the omission and notes WarpStream's BYOC architecture pre-empts client-side fetch batching.",
          "files": [],
          "expectations": [
            "When ingesting an article that proposes WarpStream `fetch.min.bytes` config, MCP-validation flags this as unsupported and the article documents the omission",
            "Resulting article notes that `replication.factor` on WarpStream is cosmetic (always 3)",
            "Resulting article includes the FSI-context paragraph framing WarpStream as competitive context, not FSI production guidance"
          ]
        },
        {
          "id": 4,
          "prompt": "Process the next pending entry in `raw/_ingest.md` — fill `wiki/concepts/flink-confluent-cloud-setup.md` from `wiki/_queue.md` Stubs.",
          "expected_output": "A new wiki/concepts/flink-confluent-cloud-setup.md article covering compute pool creation, catalog/database/table mapping, RBAC model, statement lifecycle, watermarks, statement evolution.",
          "files": ["wiki/_queue.md"],
          "expectations": [
            "Output article path is `wiki/concepts/flink-confluent-cloud-setup.md`",
            "Output article includes a section on compute pool creation",
            "Output article includes `catalog`, `database`, and `table` mapping concepts",
            "Output article references `RBAC` for dual control-plane + data-plane access",
            "`raw/_ingest.md` Pending section no longer contains the flink-confluent-cloud-setup entry",
            "`wiki/_index.md` contains a line referencing `flink-confluent-cloud-setup.md`"
          ]
        },
        {
          "id": 5,
          "prompt": "Ingest the schema-registry detection-patterns reference at raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/detection-patterns.md, merged with code-migration.md, into wiki/patterns/schema-registry-adoption-playbook.md.",
          "expected_output": "A merged wiki/patterns/schema-registry-adoption-playbook.md article with both reference sources cited in the provenance footer and both sources listed in `upstream_path` (or equivalent multi-source representation).",
          "files": [
            "raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/detection-patterns.md",
            "raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/code-migration.md"
          ],
          "expectations": [
            "Output article path is `wiki/patterns/schema-registry-adoption-playbook.md`",
            "Output article cites both upstream paths in provenance",
            "Output article header includes `detection` and `migration` as top-level sections",
            "Output article frontmatter includes `confidence: high` (source attestation per H.1 D-07)"
          ]
        },
        {
          "id": 6,
          "prompt": "Ingest a new pattern article without confluent-docs MCP available. Use context7 for architectural patterns and document the validation gap.",
          "expected_output": "Article ingests with `confidence: medium` (downgraded due to incomplete MCP validation) and a frontmatter note explaining the missing confluent-docs check.",
          "files": [],
          "expectations": [
            "Output article frontmatter includes `confidence: medium` or lower when confluent-docs MCP was unavailable",
            "Output article documents which MCP sources were used and which were skipped",
            "Article is NOT silently promoted to `confidence: high` without full MCP coverage"
          ]
        },
        {
          "id": 7,
          "prompt": "Ingest an article whose proposed `related:` frontmatter would create a 0-inbound entry in wiki/_graph.md. Detect and reject (or add the inbound automatically).",
          "expected_output": "Either /wiki:ingest fails closed with a graph-coverage error, OR it adds at least one inbound link in wiki/_graph.md before writing the article.",
          "files": ["wiki/_graph.md"],
          "expectations": [
            "Output article has >= 1 inbound link in wiki/_graph.md after ingest",
            "Output article has >= 1 outbound link in wiki/_graph.md after ingest",
            "Ingest never produces an orphan article (0 inbound)"
          ]
        },
        {
          "id": 8,
          "prompt": "Ingest two articles that both want to claim `wiki/concepts/kafka-streams-debugging.md` as a target path. Resolve the collision deterministically.",
          "expected_output": "The first ingest succeeds; the second fails closed with a name-collision error and suggests an alternate slug.",
          "files": [],
          "expectations": [
            "Second ingest exits non-zero or emits an explicit collision-detection message",
            "Second ingest does NOT silently overwrite the first article's content",
            "Suggested alternate slug does not contain a vendor-prefix per H.1 D-04 (e.g., `kafka-streams-debugging-v2.md` is OK; `confluent.kafka-streams-debugging.md` is NOT)"
          ]
        },
        {
          "id": 9,
          "prompt": "Ingest from a non-vendored URL (e.g., a Confluent blog post). Confirm the source-attestation path differs from vendored-tree ingest.",
          "expected_output": "Article frontmatter omits the `source: confluent-agent-skills@<sha>` field, uses `sources:` (plural list) with the URL, and sets `confidence: high` only if MCP validation completes.",
          "files": [],
          "expectations": [
            "Output article frontmatter does NOT include `source: confluent-agent-skills@`",
            "Output article frontmatter `sources:` list includes the URL",
            "Output article frontmatter does NOT include `upstream_path:` (that field is vendored-tree-only)"
          ]
        },
        {
          "id": 10,
          "prompt": "Ingest an article and update wiki/_index.md and wiki/_graph.md in the same operation. Verify both are touched.",
          "expected_output": "After /wiki:ingest completes, both wiki/_index.md and wiki/_graph.md have new lines referencing the new article.",
          "files": ["wiki/_index.md", "wiki/_graph.md"],
          "expectations": [
            "`wiki/_index.md` contains a new line referencing the article slug",
            "`wiki/_graph.md` contains at least one new edge involving the new article",
            "Both index and graph updates happen atomically (single commit message references both)"
          ]
        }
      ]
    }
    ```

    Encoding constraints (FROM H.1 BLOCKER LESSON):
    - Use comma-separated array syntax everywhere (`["a", "b", "c"]`) — NOT space-separated. JSON only accepts comma-separated; mimicking the H.1 YAML lesson here as an explicit check.
    - The trip-wire expectation strings contain backticks. JSON allows backticks inside strings — do not escape them, do not replace with single quotes.
    - The whole file must `python -c "import json; json.load(open('tests/evals/wiki-ingest/evals.json'))"` round-trip without error.

    File must end with a trailing newline (POSIX text-file convention; existing wiki tooling expects it).
  </action>
  <verify>
    <automated>test -f tests/evals/wiki-ingest/evals.json && python -c "import json; d=json.load(open('tests/evals/wiki-ingest/evals.json')); assert d['skill_name'] == '/wiki:ingest', d['skill_name']; assert len(d['evals']) >= 10, len(d['evals']); ids=[e['id'] for e in d['evals']]; assert ids == sorted(set(ids)) and len(ids) == len(set(ids)), 'duplicate or out-of-order ids'; print('OK', len(d['evals']))" && grep -c "src/main/avro/" tests/evals/wiki-ingest/evals.json && grep -c "fetch.min.bytes" tests/evals/wiki-ingest/evals.json && grep -c "When ingesting an article that proposes Avro schemas under" tests/evals/wiki-ingest/evals.json && grep -c "When ingesting an article that proposes WarpStream" tests/evals/wiki-ingest/evals.json</automated>
  </verify>
  <done>
    - `tests/evals/wiki-ingest/evals.json` exists and is valid JSON.
    - `skill_name == "/wiki:ingest"`, `len(evals) >= 10`, IDs are unique 1..N.
    - Trip-wire #5 verbatim string `"When ingesting an article that proposes Avro schemas under ... cites `src/main/avro/` instead"` appears exactly once in the file (`grep -c` returns 1).
    - Trip-wire #8 verbatim string `"When ingesting an article that proposes WarpStream `fetch.min.bytes` config ..."` appears exactly once.
    - Every `evals[i].expectations` is a non-empty list of non-empty strings.
    - File parses cleanly: `python -c "import json; json.load(open('tests/evals/wiki-ingest/evals.json'))"` exits 0.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Author tests/evals/{wiki-validate,wiki-lint,wiki-recommend}/evals.json (30 cases total, 10 each)</name>
  <files>tests/evals/wiki-validate/evals.json, tests/evals/wiki-lint/evals.json, tests/evals/wiki-recommend/evals.json</files>
  <read_first>
    - tests/evals/wiki-validate/evals.json, tests/evals/wiki-lint/evals.json, tests/evals/wiki-recommend/evals.json (will not exist — confirm and create)
    - .planning/phases/H.2-eval-harness-extension/H.2-CONTEXT.md (D-03 schema, D-11 case-authoring sources)
    - .claude/commands/wiki/validate.md (the validate skill — to ground expectations)
    - .claude/commands/wiki/lint.md (the lint skill — to ground expectations)
    - .claude/commands/wiki/recommend.md (the recommend skill — confirms it's an alias dispatch to /ask --mode reconsolidate per Phase 01-knowledge-skill decision)
    - tools/wiki-lint.py (the wiki-lint tool — for grounding lint-behavior cases)
    - tests/test_wiki_lint_drift.py, tests/test_wiki_decay.py, tests/test_wiki_citations.py, tests/test_wiki_tools.py (existing tests document expected behaviors)
    - wiki/_index.md, wiki/_graph.md (artifacts that validate/lint operate over)
    - raw/_ingest.md (Processed section — for recommend's queue-stub behavior)
  </read_first>
  <behavior>
    For each of the 3 files independently:
    - File parses as valid JSON.
    - Top-level keys exactly `skill_name` and `evals`.
    - `skill_name` matches the file's directory: `/wiki:validate`, `/wiki:lint`, `/wiki:recommend`.
    - `len(evals) >= 10`.
    - IDs are unique 1..10 (or 1..N).
    - Every case has `id` (int), `prompt`, `expected_output`, `expectations[]` (non-empty list of non-empty strings).
  </behavior>
  <action>
    Author three files. Per CONTEXT.md D-11, draw cases from:
    - `wiki/_queue.md` Stubs + `raw/_ingest.md` Processed for /wiki:validate and /wiki:recommend
    - `tools/wiki-lint.py` test suite (`tests/test_wiki_lint_drift.py`, `tests/test_wiki_decay.py`, `tests/test_wiki_citations.py`) for /wiki:lint

    Use the verbatim upstream schema (D-03). Backticks in JSON strings are valid — write them as-is.

    **`tests/evals/wiki-validate/evals.json` (10 cases covering: drift, decay, broken-link, orphan, schema-violation, source-attestation, vendor-drift, MCP-source-routing, decay-vs-validated, multi-finding):**

    ```json
    {
      "skill_name": "/wiki:validate",
      "evals": [
        {
          "id": 1,
          "prompt": "Validate wiki/concepts/schema-registry-best-practices.md against MCP sources. Report any drift findings.",
          "expected_output": "Zero drift findings — confluent-docs and context7 agree with article content.",
          "files": ["wiki/concepts/schema-registry-best-practices.md"],
          "expectations": [
            "Validation output includes `confluent-docs` as a queried MCP source",
            "Validation output includes `context7` as a queried MCP source",
            "Validation output includes `drift: 0` or equivalent zero-finding marker",
            "If `last_validated` < 90 days, `confidence: high` is preserved"
          ]
        },
        {
          "id": 2,
          "prompt": "Validate an article with `last_validated: 2025-01-01` (over 90 days stale). Trigger the decay rule.",
          "expected_output": "Article confidence drops from `high` to `medium` per the 90-day decay rule.",
          "files": [],
          "expectations": [
            "Output includes `decay` as a finding type",
            "Output proposes `confidence: medium` for the stale article",
            "Output does NOT silently rewrite the article — it surfaces the finding for human review"
          ]
        },
        {
          "id": 3,
          "prompt": "Validate an article that links to wiki/concepts/nonexistent-article.md. Detect broken-link.",
          "expected_output": "Validation flags the broken inbound or outbound link.",
          "files": [],
          "expectations": [
            "Output includes `broken-link` as a finding type",
            "Output names the missing target path",
            "Validation exit is non-zero if --strict is set; otherwise warning-only"
          ]
        },
        {
          "id": 4,
          "prompt": "Validate wiki/_graph.md to find orphans (articles with 0 inbound edges).",
          "expected_output": "Any orphan articles are reported with their paths.",
          "files": ["wiki/_graph.md"],
          "expectations": [
            "Output includes `orphan` as a finding type when 0-inbound articles exist",
            "Output names each orphan article path",
            "Articles with >= 1 inbound edge are NOT reported as orphans"
          ]
        },
        {
          "id": 5,
          "prompt": "Validate an article with malformed YAML frontmatter (e.g., space-separated tag array `tags: a b c`).",
          "expected_output": "Validation flags the malformed frontmatter (H.1 blocker lesson: only comma-separated arrays are valid YAML flow sequences).",
          "files": [],
          "expectations": [
            "Output includes `schema-violation` or `malformed-frontmatter` as a finding type",
            "Output references the comma-separated array requirement",
            "yaml.safe_load on the corrected frontmatter exits successfully"
          ]
        },
        {
          "id": 6,
          "prompt": "Validate vendored-source articles by comparing `source: confluent-agent-skills@<sha>` against the pin in tools/vendor-sources.json.",
          "expected_output": "Articles with stale SHA report `vendor-drift` (per H.1 D-09 passive detection).",
          "files": ["tools/vendor-sources.json"],
          "expectations": [
            "Output includes `vendor-drift` as a finding type when SHA is stale",
            "Vendor-drift findings are non-fatal (exit 0) per H.1 D-09 passive posture",
            "Output names the stale SHA and the current pin"
          ]
        },
        {
          "id": 7,
          "prompt": "Validate an article that cites WarpStream behavior. Confirm the FSI-context paragraph is present.",
          "expected_output": "Validation passes only if the article contains the canonical FSI-context paragraph framing WarpStream as competitive context.",
          "files": ["wiki/concepts/warpstream-schema-registry-format-constraint.md"],
          "expectations": [
            "Output checks for the phrase `competitive context for SA conversations` or equivalent FSI-framing",
            "Article without FSI-framing is flagged as `fsi-framing-missing`",
            "Article with FSI-framing passes this check"
          ]
        },
        {
          "id": 8,
          "prompt": "Validate the cdc-to-tableflow-flink-decode.md pattern article against confluent-docs MCP. Confirm the decode-pattern claim is current.",
          "expected_output": "confluent-docs returns content consistent with the article's claim that Tableflow on a CDC source topic requires a Flink decode step.",
          "files": ["wiki/patterns/cdc-to-tableflow-flink-decode.md"],
          "expectations": [
            "Output queries confluent-docs MCP",
            "Output confirms `Flink decode` is the documented mitigation",
            "Output confirms `Tableflow` on CDC source topic is documented as unsupported direct"
          ]
        },
        {
          "id": 9,
          "prompt": "Validate that every wiki article with `confidence: high` either has MCP-validated sources OR explicit source attestation (per H.1 D-07).",
          "expected_output": "Articles claiming `confidence: high` without either provenance signal are flagged.",
          "files": [],
          "expectations": [
            "Output includes `confidence-unjustified` as a finding type",
            "Articles with `source: confluent-agent-skills@<sha>` pass this check (source attestation)",
            "Articles with `sources: [...]` and recent `last_validated` pass this check (MCP attestation)",
            "Articles with neither are flagged"
          ]
        },
        {
          "id": 10,
          "prompt": "Validate the entire wiki/ tree in batch mode. Report total finding counts per type.",
          "expected_output": "Summary block listing finding counts: `drift: N1`, `decay: N2`, `broken-link: N3`, `orphan: N4`, `schema-violation: N5`, `vendor-drift: N6`, `confidence-unjustified: N7`.",
          "files": [],
          "expectations": [
            "Output includes a summary block with per-type counts",
            "Output is parseable line-by-line (one finding per line, or JSON output for --format=json)",
            "Exit code is 0 for warning-only findings (decay, vendor-drift); non-zero for hard violations (broken-link, schema-violation) when --strict is set"
          ]
        }
      ]
    }
    ```

    **`tests/evals/wiki-lint/evals.json` (10 cases covering: broken-link, orphan, malformed, decay, drift, schema, exit-code, --fix flag, citation, vendor-drift):**

    ```json
    {
      "skill_name": "/wiki:lint",
      "evals": [
        {
          "id": 1,
          "prompt": "Run wiki-lint on a clean wiki tree. Expect exit 0.",
          "expected_output": "wiki-lint exits 0 with no findings on a clean tree.",
          "files": [],
          "expectations": [
            "Exit code is 0 when no findings exist",
            "Output to stdout is empty or only a summary line `wiki-lint: 0 findings`",
            "Tool does NOT write to disk in default (non-fix) mode"
          ]
        },
        {
          "id": 2,
          "prompt": "Run wiki-lint on a wiki with a broken internal link. Detect and report.",
          "expected_output": "Exit non-zero; output names the broken link target.",
          "files": [],
          "expectations": [
            "Exit code is non-zero when broken-link findings exist",
            "Output names the source article and the broken target path",
            "Finding type is `broken-link`"
          ]
        },
        {
          "id": 3,
          "prompt": "Run wiki-lint --fix on an article with stale `last_validated` field. Expect the field to be apply_decay_fix-rewritten.",
          "expected_output": "Article frontmatter is updated to `confidence: medium` (decay applied); body is untouched.",
          "files": [],
          "expectations": [
            "Frontmatter field `confidence` changes from `high` to `medium`",
            "Body of the article is byte-identical pre/post --fix",
            "Per H.1 phase decision: apply_decay_fix is regex-scoped to frontmatter block only — never rewrites body text"
          ]
        },
        {
          "id": 4,
          "prompt": "Run wiki-lint --full on the entire tree. Expect a categorized finding list.",
          "expected_output": "Categorized output: broken-link, orphan, malformed, decay, drift, schema, citation-resolution, vendor-drift.",
          "files": [],
          "expectations": [
            "Output is grouped by finding type",
            "Each finding includes the source article path and a brief reason",
            "--full includes vendor-drift findings (H.1 D-09 extension)"
          ]
        },
        {
          "id": 5,
          "prompt": "Run wiki-lint on an article with malformed YAML frontmatter (space-separated tag list `tags: a b c`).",
          "expected_output": "Lint flags the malformed list as a schema violation; --fix can repair it.",
          "files": [],
          "expectations": [
            "Finding type is `schema-violation` or `malformed-frontmatter`",
            "--fix mode rewrites `tags: a b c` to `tags: [a, b, c]`",
            "yaml.safe_load on the corrected frontmatter exits successfully"
          ]
        },
        {
          "id": 6,
          "prompt": "Run wiki-lint on an article missing required frontmatter fields (`title`, `tags`, `sources`, `confidence`).",
          "expected_output": "Lint reports each missing field as a separate finding.",
          "files": [],
          "expectations": [
            "Each missing field produces a distinct finding line",
            "Finding type is `missing-field` or equivalent",
            "Exit code is non-zero"
          ]
        },
        {
          "id": 7,
          "prompt": "Run wiki-lint on a wiki where wiki/_graph.md has an orphan article (0 inbound edges).",
          "expected_output": "Lint reports the orphan with the article path.",
          "files": ["wiki/_graph.md"],
          "expectations": [
            "Finding type is `orphan`",
            "Output names the orphan article path",
            "Articles with >= 1 inbound edge are NOT flagged"
          ]
        },
        {
          "id": 8,
          "prompt": "Run wiki-lint on an article with `source: confluent-agent-skills@<stale-sha>` (SHA differs from tools/vendor-sources.json pin).",
          "expected_output": "Vendor-drift finding emitted; exit code is 0 (passive per H.1 D-09).",
          "files": ["tools/vendor-sources.json"],
          "expectations": [
            "Finding type is `vendor-drift` or `DRIFT`",
            "Exit code is 0 (passive vendor-drift per H.1 D-09)",
            "Output names the stale SHA and the current pin"
          ]
        },
        {
          "id": 9,
          "prompt": "Run wiki-lint with citation-resolution check on an article that references a non-existent fsi-dsp:// URI.",
          "expected_output": "Lint reports the unresolvable citation as a finding.",
          "files": [],
          "expectations": [
            "Finding type is `citation-unresolved` or `broken-citation`",
            "Output names the unresolvable URI",
            "Exit code is non-zero"
          ]
        },
        {
          "id": 10,
          "prompt": "Run wiki-lint --fix on a wiki where multiple findings exist. Expect deterministic ordering and idempotency.",
          "expected_output": "All fixable findings are applied in a stable order; running --fix again produces zero new changes.",
          "files": [],
          "expectations": [
            "First --fix run modifies one or more files",
            "Second --fix run produces zero new modifications (`git diff --quiet` exits 0)",
            "Findings are processed in a stable order (e.g., alphabetical by path)"
          ]
        }
      ]
    }
    ```

    **`tests/evals/wiki-recommend/evals.json` (10 cases covering: alias-dispatch, write-back, queue-stub, no-coverage, ambiguous-route, confidence-medium, ephemeral-mode, full-mode, multi-doc, retry-after-stub):**

    Per Phase 01-knowledge-skill decision (STATE.md), `/wiki:recommend` is a thin alias dispatching to `/ask --mode reconsolidate`. Cases test the alias dispatch + write-back behavior.

    ```json
    {
      "skill_name": "/wiki:recommend",
      "evals": [
        {
          "id": 1,
          "prompt": "Invoke /wiki:recommend with a question that has wiki coverage. Confirm the alias dispatches to /ask --mode reconsolidate.",
          "expected_output": "Output references /ask under the hood and writes back any newly discovered facts to wiki.",
          "files": [],
          "expectations": [
            "Output indicates /ask was invoked with `--mode reconsolidate`",
            "If new facts were discovered during answer, they are appended to the relevant wiki article",
            "If no new facts emerged, no wiki write occurs (write-back is conditional)"
          ]
        },
        {
          "id": 2,
          "prompt": "Invoke /wiki:recommend on a topic with zero wiki coverage. Confirm a queue stub is created in wiki/_queue.md.",
          "expected_output": "wiki/_queue.md grows by one Stubs entry referencing the missing topic.",
          "files": ["wiki/_queue.md"],
          "expectations": [
            "wiki/_queue.md `## Stubs to Create` section has one additional entry after the call",
            "The new entry follows the format `- [ ] wiki/concepts/<slug>.md — brief description`",
            "Auto-stub fires even in ephemeral mode (Phase 01 decision: coverage gaps are never lost)"
          ]
        },
        {
          "id": 3,
          "prompt": "Invoke /wiki:recommend on a question that has only `confidence: medium` wiki coverage. Confirm the answer flags the uncertainty.",
          "expected_output": "Response cites the medium-confidence article AND notes the confidence floor; suggests /wiki:validate as next step.",
          "files": [],
          "expectations": [
            "Response cites article path",
            "Response includes the phrase `confidence: medium` or equivalent uncertainty marker",
            "Response suggests `/wiki:validate` as a follow-up action"
          ]
        },
        {
          "id": 4,
          "prompt": "Invoke /wiki:recommend in ephemeral mode (no write-back). Confirm wiki is byte-identical post-call.",
          "expected_output": "wiki/ directory has zero modifications after the call (except auto-stub if coverage gap detected).",
          "files": [],
          "expectations": [
            "Wiki articles are byte-identical pre/post (no auto-write)",
            "wiki/_queue.md MAY grow (auto-stub fires per Phase 01 decision)",
            "wiki/_index.md and wiki/_graph.md are byte-identical"
          ]
        },
        {
          "id": 5,
          "prompt": "Invoke /wiki:recommend on a triage classifier route-failure case (ambiguous). Confirm graceful degradation.",
          "expected_output": "Response either picks a default route (deep) and proceeds, or refuses with a clear explanation.",
          "files": [],
          "expectations": [
            "Response does NOT crash with a stack trace",
            "Response either declares a route choice or refuses cleanly",
            "If refused, the reason is human-readable (e.g., `ambiguous query — please specify topic`)"
          ]
        },
        {
          "id": 6,
          "prompt": "Invoke /wiki:recommend --force-route deep on a question that triage would otherwise route to wiki-only.",
          "expected_output": "Deep route runs even though triage suggested wiki-only.",
          "files": [],
          "expectations": [
            "Response invokes the deep route per --force-route bypass",
            "Triage classifier is logged but its route choice is overridden",
            "Per Phase 01 decision: --force-route bypasses the classifier"
          ]
        },
        {
          "id": 7,
          "prompt": "Invoke /wiki:recommend on a multi-doc question (cites multiple wiki articles). Confirm provenance footers reference all cited articles.",
          "expected_output": "Response cites every wiki article used; output includes a `Provenance:` block listing them.",
          "files": [],
          "expectations": [
            "Output includes a Provenance section",
            "Every cited article appears in the Provenance block by path",
            "Citation order is stable (alphabetical or invocation-order, deterministic)"
          ]
        },
        {
          "id": 8,
          "prompt": "Invoke /wiki:recommend after the queue stub from a prior call has been filled. Confirm the queue entry is removed.",
          "expected_output": "wiki/_queue.md `## Stubs to Create` section loses the resolved entry; new entry may move to `## Resolved`.",
          "files": ["wiki/_queue.md"],
          "expectations": [
            "Stub entry is removed from `## Stubs to Create`",
            "Either the entry is fully deleted OR moved to a `## Resolved` section (implementation choice)",
            "The new wiki article is referenced in wiki/_index.md"
          ]
        },
        {
          "id": 9,
          "prompt": "Invoke /wiki:recommend on a question that crosses into the FSI overlay (e.g., `which auth mechanism should I use?`). Confirm canon overlay applies.",
          "expected_output": "Response cites both the upstream canon AND the FSI overlay; recommends mTLS per FSI canon.",
          "files": [],
          "expectations": [
            "Response cites the FSI canon overlay (`mTLS` for FSI, not just SASL/PLAIN)",
            "Response distinguishes between general canon and FSI-specific overlay",
            "Response does NOT recommend username/password auth for FSI workloads (per CLAUDE.md FSI overlay rule)"
          ]
        },
        {
          "id": 10,
          "prompt": "Invoke /wiki:recommend twice on the same query. Confirm deterministic output (modulo write-back side effects).",
          "expected_output": "The response content is identical or near-identical across two invocations on a frozen wiki state.",
          "files": [],
          "expectations": [
            "Two invocations on the same query produce the same cited articles",
            "Two invocations produce the same route choice (modulo classifier nondeterminism — acceptable variance documented if any)",
            "wiki/_queue.md auto-stub is idempotent — second invocation does not append a duplicate stub entry"
          ]
        }
      ]
    }
    ```

    Encoding constraints (same as Task 1):
    - Comma-separated JSON arrays only.
    - Backticks inside strings are literal — do not escape.
    - All files end with trailing newline.
    - All three files round-trip via `json.load()`.
  </action>
  <verify>
    <automated>for s in wiki-validate wiki-lint wiki-recommend; do test -f "tests/evals/$s/evals.json" || exit 1; python -c "import json; d=json.load(open(f'tests/evals/$s/evals.json')); assert d['skill_name'] == '/$s'.replace('wiki-', 'wiki:'), d['skill_name']; assert len(d['evals']) >= 10, len(d['evals']); ids=[e['id'] for e in d['evals']]; assert len(ids) == len(set(ids)), 'duplicate ids'; assert all(isinstance(e['id'], int) and e['prompt'] and e['expected_output'] and isinstance(e['expectations'], list) and e['expectations'] for e in d['evals']), 'malformed case'; print(f'{s}: OK', len(d['evals']))"; done</automated>
  </verify>
  <done>
    - All three files exist at `tests/evals/{wiki-validate,wiki-lint,wiki-recommend}/evals.json`.
    - Each parses as valid JSON.
    - Each has `skill_name` matching the directory (`/wiki:validate`, `/wiki:lint`, `/wiki:recommend`).
    - Each has `len(evals) >= 10` with unique integer IDs.
    - Every case has non-empty `prompt`, `expected_output`, and `expectations[]` (list of non-empty strings).
    - `python -m pytest tests/evals/run_skill_evals.py::test_threshold_per_skill -v` still PASSES (every new case structurally well-formed).
  </done>
</task>

</tasks>

<verification>
After both tasks complete:

1. **All 4 wiki-skill files exist:** `for s in wiki-ingest wiki-validate wiki-lint wiki-recommend; do test -f "tests/evals/$s/evals.json" || echo "MISSING $s"; done` produces no output.
2. **Each has >= 10 cases:** `for s in wiki-ingest wiki-validate wiki-lint wiki-recommend; do python -c "import json; print(s, len(json.load(open(f'tests/evals/$s/evals.json'))['evals']))" 2>/dev/null; done` — every line shows count >= 10.
3. **Trip-wires verbatim in /wiki:ingest:**
   - `grep -c "When ingesting an article that proposes Avro schemas under" tests/evals/wiki-ingest/evals.json` returns 1.
   - `grep -c "When ingesting an article that proposes WarpStream" tests/evals/wiki-ingest/evals.json` returns 1.
4. **Runner picks up new cases:** `python -m pytest tests/evals/run_skill_evals.py --collect-only -q 2>&1 | tail -3` — collected count grows by 40 vs Plan 01 baseline.
5. **Threshold gate still passes:** `python -m pytest tests/evals/run_skill_evals.py::test_threshold_per_skill -v` PASSES (every new case is structurally well-formed).
6. **Coverage gate progresses:** `python -m pytest tests/evals/run_skill_evals.py::test_all_seven_new_skills_discovered -v` — 4 wiki skills now present; STILL FAILS naming the 3 remaining skills `/review`, `/dsp:plan`, `/dsp:apply` (Plan 03 closes this).
7. **Existing harnesses unaffected:** `python -m pytest tests/golden/ -q --tb=no` PASSES.
8. **No changes to locked files:** `git diff --quiet tools/apply_engine.py .claude/commands/dsp-apply.md tests/golden/ask/` exits 0.
9. **JSON shape lesson (H.1):** all arrays are comma-separated; `grep -E ',\\s*"' tests/evals/wiki-*/evals.json | wc -l` is large (hundreds of array elements); `grep -E '" +"[a-zA-Z]' tests/evals/wiki-*/evals.json` returns nothing (no space-separated array values).
</verification>

<success_criteria>
- EVAL-02 satisfied for 4/7 named skills: /wiki:ingest, /wiki:validate, /wiki:lint, /wiki:recommend each have >= 10 cases.
- EVAL-03 partially satisfied: 2 trip-wires (avro-schema-source-directory, warpstream-config-overrides) encoded as verbatim expectation strings.
- D-03 upstream-schema verbatim: every file uses `{"skill_name": "...", "evals": [{"id": N, "prompt": "...", "expected_output": "...", "files": [...], "expectations": [...]}]}` exactly.
- D-04 structural-only: every expectation is a grep-checkable string; no LLM-judgment phrasing (e.g., no "subjectively assess" or "evaluate quality of").
- D-08 trip-wire distribution honored: exactly the 2 /wiki:ingest trip-wires land here; the other 7 are in Plan 03.
- H.1 array-format lesson honored: all arrays comma-separated.
- D-11 lock: `tools/apply_engine.py` + `.claude/commands/dsp-apply.md` byte-identical.
- Existing harnesses unaffected: `python -m pytest tests/golden/ -q` PASSES.
</success_criteria>

<output>
After completion, create `.planning/phases/H.2-eval-harness-extension/H.2-02-SUMMARY.md` documenting:
- Per-file case counts (target 10 each)
- The 2 trip-wire expectation strings landed in /wiki:ingest, with line numbers in the JSON file
- Real-world signals drawn on for each skill (which `wiki/_queue.md` stubs, which `raw/_ingest.md` Processed entries)
- Any cases that ended up structurally weak (e.g., expectations that were hard to make grep-checkable) and the chosen mitigation
</output>
