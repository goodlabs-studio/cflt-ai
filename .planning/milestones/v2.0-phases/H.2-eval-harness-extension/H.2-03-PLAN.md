---
phase: H.2-eval-harness-extension
plan: 03
type: execute
wave: 2
depends_on: [H.2-01]
files_modified:
  - tests/evals/review/evals.json
  - tests/evals/dsp-plan/evals.json
  - tests/evals/dsp-apply/evals.json
autonomous: true
requirements: [EVAL-02, EVAL-03]
requirements_addressed: [EVAL-02, EVAL-03]

must_haves:
  truths:
    - "Each of /review, /dsp:plan, /dsp:apply has an evals.json file with >= 10 cases (thin wrappers referencing existing MD cases plus trip-wire expectations)"
    - "The 4 H.1 trip-wires assigned to /review per D-08 (Tableflow-on-CDC, EOS-WarpStream, schema-aware-producer, KS-4x-import) are encoded as expectations[] strings verbatim from CONTEXT.md"
    - "The 3 H.1 trip-wires assigned to /dsp:plan per D-08 (Tableflow-changelog-immutability, OracleXStream-after-state-only, WarpStream-SR-format) are encoded as expectations[] strings verbatim"
    - "Existing MD cases in tests/golden/{review,act}/cases/*.md are unchanged (D-01 hybrid lock)"
  artifacts:
    - path: "tests/evals/review/evals.json"
      provides: "16+ cases for /review — references the existing 16 MD cases by ID and adds 4 trip-wire expectations as standalone cases"
      contains: "Tableflow-on-CDC-source-topic"
    - path: "tests/evals/dsp-plan/evals.json"
      provides: "Thin-wrapper referencing the 22 existing /dsp:plan MD cases plus 3 trip-wire expectations"
      contains: "Tableflow changelog"
    - path: "tests/evals/dsp-apply/evals.json"
      provides: "Thin-wrapper referencing the 10 existing /dsp:apply MD cases"
  key_links:
    - from: "tests/evals/review/evals.json"
      to: "tests/golden/review/cases/*.md"
      via: "case_ref field — JSON case references existing MD case ID; merged by the runner via skill grouping"
      pattern: "case_ref.*[a-z-]+-[0-9]+"
    - from: "tests/evals/review/evals.json"
      to: "wiki/concepts/cdc-tableflow-flink-decode-required.md, wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md, wiki/concepts/schema-aware-console-producer-required.md, wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md"
      via: "Trip-wire expectation strings — keeps /review claim extraction in sync with H.1 trip-wire articles per D-08"
      pattern: "Flags .* as a violation"
    - from: "tests/evals/dsp-plan/evals.json"
      to: "wiki/concepts/tableflow-changelog-mode-immutability.md, wiki/concepts/oracle-xstream-source-limitations.md, wiki/concepts/warpstream-schema-registry-format-constraint.md"
      via: "Trip-wire expectation strings — keeps /dsp:plan gate violations in sync with H.1 trip-wire articles per D-08"
      pattern: "Refuses to plan"
---

<objective>
Author the 3 thin-wrapper evals.json files for `/review`, `/dsp:plan`, `/dsp:apply` using the verbatim upstream confluentinc/agent-skills schema (D-03). Each file references the existing markdown-per-case cases by ID (per CONTEXT.md D-01 hybrid lock) AND adds trip-wire expectations per D-08:

- `/review` evals: existing 16 MD cases via case_refs + 4 standalone trip-wire cases (Tableflow-on-CDC, EOS-WarpStream, schema-aware-producer, KS-4x-import)
- `/dsp:plan` evals: existing 22 MD cases via case_refs + 3 standalone trip-wire cases (Tableflow-changelog-immutability, OracleXStream-after-state-only, WarpStream-SR-format)
- `/dsp:apply` evals: existing 10 MD cases via case_refs (no trip-wires for /dsp:apply per D-08 distribution)

This plan addresses EVAL-02 for the remaining 3/7 named skills. It addresses EVAL-03 with the 7 trip-wires that didn't go into /wiki:ingest (Plan 02 handled the other 2). Combined with Plan 02, all 9 H.1 trip-wires are encoded — well above EVAL-03's "≥5 trip-wires" floor.

Output: 3 new JSON files. NO changes to existing MD harnesses (D-01 lock). NO changes to runtime files (D-11 lock).
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
@.claude/commands/review.md
@.claude/commands/dsp-plan.md
@.claude/commands/dsp-apply.md
@tests/golden/review/cases/
@tests/golden/act/cases/
@wiki/concepts/cdc-tableflow-flink-decode-required.md
@wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md
@wiki/concepts/schema-aware-console-producer-required.md
@wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md
@wiki/concepts/tableflow-changelog-mode-immutability.md
@wiki/concepts/oracle-xstream-source-limitations.md
@wiki/concepts/warpstream-schema-registry-format-constraint.md

<interfaces>
<!-- Verbatim upstream schema from D-03 (CONTEXT.md). Each evals.json file MUST conform. -->
<!-- Thin-wrapper extension: cases can reference existing MD cases via `case_ref` field. -->
<!-- The `case_ref` field is OPTIONAL (additive); upstream schema permits arbitrary fields per case (`files` is already optional in upstream). -->

{
  "skill_name": "/review" | "/dsp:plan" | "/dsp:apply",
  "evals": [
    {
      "id": 1,
      "prompt": "...",
      "expected_output": "...",
      "files": ["optional"],
      "expectations": ["..."],
      "case_ref": "optional — references an existing MD case by ID (e.g., 'apply-bypass-confirmation-029')"
    }
  ]
}

<!-- D-08 verbatim trip-wire expectation strings (FOR /review — copy verbatim, do not paraphrase): -->
1. "Flags Tableflow-on-CDC-source-topic claims as a violation — citing the Flink decode pattern as the required mitigation"
2. "Flags exactly-once-v2 on WarpStream claims as a throughput-cost violation — citing the 'EOS enables idempotent producers internally' fact"
3. "Flags kafka-console-producer usage in verification snippets as a Schema-Registry-incompatible tool — recommends kafka-avro-console-producer"
4. "Flags `StreamsUncaughtExceptionHandler` cited as a nested class under `KafkaStreams` — corrects to org.apache.kafka.streams.errors import (KS 4.x rename)"

<!-- D-08 verbatim trip-wire expectation strings (FOR /dsp:plan — copy verbatim, do not paraphrase): -->
5. "Refuses to plan a Tableflow changelog mode change on an already-materialized topic — directs to delete+recreate per immutability rule"
6. "Refuses to plan OracleXStreamSource with `after.state.only=true` — that config is not supported by Oracle XStream"
7. "Refuses to plan JSON Schema registration against WarpStream's built-in Schema Registry — accepts Avro or Protobuf only"

<!-- Existing MD case ID patterns (from tests/golden/{review,act}/cases/*.md) — used in case_ref fields: -->
- /review cases: filename stems like `review-cdc-blueprint-001.md`, `review-fsi-overlay-008.md`, etc. (16 total)
- /dsp:plan cases: filename stems like `plan-topic-fsi-001.md`, `plan-flink-002.md`, etc. (22 total — all act cases WITHOUT skill: /dsp:apply frontmatter)
- /dsp:apply cases: filename stems like `apply-topic-engineer-023.md`, `apply-bypass-confirmation-029.md`, etc. (10 total — all act cases WITH skill: /dsp:apply frontmatter)
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Author tests/evals/review/evals.json (thin wrapper: 16 existing MD case_refs + 4 trip-wire cases verbatim per D-08)</name>
  <files>tests/evals/review/evals.json</files>
  <read_first>
    - tests/evals/review/evals.json (will not exist — confirm and create)
    - .planning/phases/H.2-eval-harness-extension/H.2-CONTEXT.md (D-03 schema, D-08 /review trip-wires verbatim)
    - tests/evals/wiki-ingest/evals.json (sibling JSON exemplar from Plan 02 — confirms shape)
    - tests/golden/review/cases/ (16 existing MD cases — list filenames to populate case_ref fields)
    - wiki/concepts/cdc-tableflow-flink-decode-required.md (trip-wire #2 article — confirms assertion direction)
    - wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md (trip-wire #9 article)
    - wiki/concepts/schema-aware-console-producer-required.md (trip-wire #6 article)
    - wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md (trip-wire #4 article)
    - .claude/commands/review.md (the skill being tested — to ground trip-wire prompt phrasing)
  </read_first>
  <behavior>
    - Test 1: File parses as valid JSON.
    - Test 2: `skill_name == "/review"`.
    - Test 3: `len(evals) >= 10` (specifically: 16 case_refs + 4 trip-wires = 20 cases).
    - Test 4: At least 16 cases have a `case_ref` field referencing an existing MD case (e.g., `tests/golden/review/cases/review-cdc-blueprint-001.md` → case_ref `"review-cdc-blueprint-001"`).
    - Test 5: Every case_ref resolves to an actual file in tests/golden/review/cases/.
    - Test 6: Exactly 4 cases encode the trip-wire expectations (verbatim from D-08): each appears exactly once as an expectation string.
    - Test 7: All trip-wire expectation strings appear verbatim — bytewise — no paraphrasing.
  </behavior>
  <action>
    Enumerate existing /review MD cases first:
    ```bash
    ls tests/golden/review/cases/*.md | xargs -n1 basename | sed 's/\.md$//'
    ```
    This yields 16 stems. Use each as a case_ref value.

    Create `tests/evals/review/evals.json` with the verbatim upstream schema (D-03), extended with the additive `case_ref` field (D-03 schema-additive — extra fields per case are permitted in upstream; `files` is already an optional field).

    **CRITICAL: the four trip-wire expectation strings from CONTEXT.md `<specifics>` D-08 must be COPIED VERBATIM into the relevant trip-wire cases. Do not paraphrase, do not adjust punctuation, do not change the backticks.** Verbatim strings:

    1. (Trip-wire #2, Tableflow-on-CDC): `"Flags Tableflow-on-CDC-source-topic claims as a violation — citing the Flink decode pattern as the required mitigation"`
    2. (Trip-wire #9, EOS-WarpStream): `"Flags exactly-once-v2 on WarpStream claims as a throughput-cost violation — citing the 'EOS enables idempotent producers internally' fact"`
    3. (Trip-wire #6, schema-aware producer): `"Flags kafka-console-producer usage in verification snippets as a Schema-Registry-incompatible tool — recommends kafka-avro-console-producer"`
    4. (Trip-wire #4, KS 4.x import): ``"Flags `StreamsUncaughtExceptionHandler` cited as a nested class under `KafkaStreams` — corrects to org.apache.kafka.streams.errors import (KS 4.x rename)"``

    Note the em-dashes in strings 1 and 2 are U+2014 (—), not double-hyphen. Copy as Unicode. The single quotes in string 2 (around `'EOS enables idempotent producers internally'`) are ASCII single quotes, not curly.

    File content:

    ```json
    {
      "skill_name": "/review",
      "evals": [
        {
          "id": 1,
          "case_ref": "<stem-of-first-review-MD-case>",
          "prompt": "Review the fixture document referenced by the MD case. Apply premise-challenge then wiki cross-reference per the /review skill flow.",
          "expected_output": "A review report matching the MD case's required_report_sections / forbidden_content frontmatter.",
          "files": ["tests/golden/review/cases/<stem-of-first-review-MD-case>.md"],
          "expectations": [
            "Report includes the required_report_sections listed in the MD case frontmatter",
            "Report does NOT include any forbidden_content from the MD case frontmatter",
            "Report includes a YAML claim block before the verdict table (Phase 02-review-skill reproducibility anchor)"
          ]
        }
        // ... 15 more wrapper cases, ids 2..16, one per existing MD case ...
        ,
        {
          "id": 17,
          "prompt": "Review a customer architecture deck that proposes enabling Tableflow directly on a Debezium CDC source topic emitting tombstones.",
          "expected_output": "Report flags the Tableflow-on-CDC pattern as a violation and cites the Flink decode pattern as the required mitigation.",
          "files": [],
          "expectations": [
            "Flags Tableflow-on-CDC-source-topic claims as a violation — citing the Flink decode pattern as the required mitigation",
            "Report cites wiki/patterns/cdc-tableflow-flink-decode-required.md or equivalent canonical reference",
            "Report does NOT recommend enabling Tableflow directly on a CDC source topic"
          ]
        },
        {
          "id": 18,
          "prompt": "Review a runbook that enables exactly_once_v2 on a WarpStream cluster without flagging the throughput cost.",
          "expected_output": "Report flags exactly-once-v2 on WarpStream as a throughput-cost violation; cites the 'EOS enables idempotent producers internally' fact.",
          "files": [],
          "expectations": [
            "Flags exactly-once-v2 on WarpStream claims as a throughput-cost violation — citing the 'EOS enables idempotent producers internally' fact",
            "Report cites wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md or equivalent canonical reference",
            "Report flags this as the WarpStream-specific in-flight request concurrency limit"
          ]
        },
        {
          "id": 19,
          "prompt": "Review a verification snippet that uses kafka-console-producer to publish a message to a topic registered with Schema Registry.",
          "expected_output": "Report flags kafka-console-producer as Schema-Registry-incompatible; recommends kafka-avro-console-producer.",
          "files": [],
          "expectations": [
            "Flags kafka-console-producer usage in verification snippets as a Schema-Registry-incompatible tool — recommends kafka-avro-console-producer",
            "Report cites wiki/concepts/schema-aware-console-producer-required.md or equivalent canonical reference",
            "Report's verdict on the snippet is `Corrected` per REVW-01 verdict taxonomy"
          ]
        },
        {
          "id": 20,
          "prompt": "Review a Java code sample on Kafka Streams 4.x that imports StreamsUncaughtExceptionHandler as a nested class under KafkaStreams.",
          "expected_output": "Report flags the nested-class import as the KS 3.x pattern; corrects to org.apache.kafka.streams.errors.StreamsUncaughtExceptionHandler.",
          "files": [],
          "expectations": [
            "Flags `StreamsUncaughtExceptionHandler` cited as a nested class under `KafkaStreams` — corrects to org.apache.kafka.streams.errors import (KS 4.x rename)",
            "Report cites wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md or equivalent canonical reference",
            "Report's verdict is `Corrected`"
          ]
        }
      ]
    }
    ```

    Step-by-step authoring:

    1. Run `ls tests/golden/review/cases/*.md | xargs -n1 basename | sed 's/\.md$//' | sort` to enumerate the 16 existing review MD case stems.

    2. For each stem, emit one wrapper case (ids 1..16) with:
       - `case_ref` = the stem
       - `files` = `["tests/golden/review/cases/<stem>.md"]`
       - `prompt` = `"Review the fixture document referenced by the MD case. Apply premise-challenge then wiki cross-reference per the /review skill flow."`
       - `expected_output` and `expectations` = boilerplate referencing MD case frontmatter

    3. Append the 4 trip-wire cases (ids 17..20) with VERBATIM expectation strings.

    4. Validate trip-wire string presence with bytewise grep — see verify block.

    Encoding constraints (same as Plan 02):
    - Comma-separated JSON arrays only.
    - Backticks in strings are literal — do not escape.
    - Em-dash (U+2014) is literal in trip-wire strings 1, 2, 3, 4.
    - File ends with trailing newline.
  </action>
  <verify>
    <automated>test -f tests/evals/review/evals.json && python -c "import json; d=json.load(open('tests/evals/review/evals.json')); assert d['skill_name'] == '/review', d['skill_name']; assert len(d['evals']) >= 10, len(d['evals']); ids=[e['id'] for e in d['evals']]; assert len(ids) == len(set(ids)), 'dup ids'; refs=[e.get('case_ref') for e in d['evals'] if e.get('case_ref')]; assert len(refs) >= 16, f'expected >=16 case_refs, got {len(refs)}'; print('OK', len(d['evals']), 'cases,', len(refs), 'case_refs')" && grep -c "Flags Tableflow-on-CDC-source-topic claims as a violation" tests/evals/review/evals.json && grep -c "Flags exactly-once-v2 on WarpStream claims as a throughput-cost violation" tests/evals/review/evals.json && grep -c "Flags kafka-console-producer usage in verification snippets" tests/evals/review/evals.json && grep -c "Flags .StreamsUncaughtExceptionHandler. cited as a nested class under .KafkaStreams." tests/evals/review/evals.json && for ref in $(python -c "import json; d=json.load(open('tests/evals/review/evals.json')); print(' '.join(e['case_ref'] for e in d['evals'] if e.get('case_ref')))"); do test -f "tests/golden/review/cases/${ref}.md" || { echo "MISSING: $ref"; exit 1; }; done</automated>
  </verify>
  <done>
    - `tests/evals/review/evals.json` exists, valid JSON, `skill_name == "/review"`.
    - `len(evals) >= 10`; specifically expected 20 (16 case_refs + 4 trip-wires).
    - Each of the 4 trip-wire verbatim strings appears exactly once via grep:
      - "Flags Tableflow-on-CDC-source-topic claims as a violation" (count = 1)
      - "Flags exactly-once-v2 on WarpStream claims as a throughput-cost violation" (count = 1)
      - "Flags kafka-console-producer usage in verification snippets" (count = 1)
      - StreamsUncaughtExceptionHandler nested-class flag (count = 1; grep with `.` wildcard for backticks)
    - Every `case_ref` resolves to an existing file in `tests/golden/review/cases/`.
    - `python -m pytest tests/evals/run_skill_evals.py::test_threshold_per_skill -v` PASSES.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Author tests/evals/dsp-plan/evals.json (thin wrapper: 22 existing MD case_refs + 3 trip-wire cases verbatim per D-08)</name>
  <files>tests/evals/dsp-plan/evals.json</files>
  <read_first>
    - tests/evals/dsp-plan/evals.json (will not exist — confirm and create)
    - .planning/phases/H.2-eval-harness-extension/H.2-CONTEXT.md (D-03 schema, D-08 /dsp:plan trip-wires verbatim)
    - tests/evals/review/evals.json (sibling shape from Task 1)
    - tests/golden/act/cases/ (32 cases total — 22 /dsp:plan + 10 /dsp:apply; filter by absent `skill: /dsp:apply` frontmatter for plan cases)
    - .claude/commands/dsp-plan.md (the skill being tested)
    - wiki/concepts/tableflow-changelog-mode-immutability.md (trip-wire #1 article)
    - wiki/concepts/oracle-xstream-source-limitations.md (trip-wire #3 article)
    - wiki/concepts/warpstream-schema-registry-format-constraint.md (trip-wire #7 article)
  </read_first>
  <behavior>
    - Test 1: File parses as valid JSON.
    - Test 2: `skill_name == "/dsp:plan"`.
    - Test 3: `len(evals) >= 10` (specifically: 22 case_refs + 3 trip-wires = 25).
    - Test 4: At least 22 cases have a `case_ref` field referencing an existing /dsp:plan MD case.
    - Test 5: Every case_ref resolves to a file in tests/golden/act/cases/ AND that file does NOT have `skill: /dsp:apply` frontmatter (i.e., it's a plan case).
    - Test 6: The 3 D-08 trip-wire expectation strings appear verbatim, each exactly once.
  </behavior>
  <action>
    Enumerate existing /dsp:plan MD case stems:
    ```bash
    grep -L '^skill: /dsp:apply' tests/golden/act/cases/*.md | xargs -n1 basename | sed 's/\.md$//'
    ```
    This yields 22 stems. Use each as a case_ref.

    Create `tests/evals/dsp-plan/evals.json` in the same shape as Task 1.

    **VERBATIM trip-wire expectation strings (from CONTEXT.md D-08 specifics):**

    5. (Trip-wire #1, Tableflow changelog immutability): `"Refuses to plan a Tableflow changelog mode change on an already-materialized topic — directs to delete+recreate per immutability rule"`
    6. (Trip-wire #3, Oracle XStream after.state.only): ``"Refuses to plan OracleXStreamSource with `after.state.only=true` — that config is not supported by Oracle XStream"``
    7. (Trip-wire #7, WarpStream SR format): `"Refuses to plan JSON Schema registration against WarpStream's built-in Schema Registry — accepts Avro or Protobuf only"`

    File structure (abbreviated — actual file lists 22 wrappers + 3 trip-wires):

    ```json
    {
      "skill_name": "/dsp:plan",
      "evals": [
        {
          "id": 1,
          "case_ref": "<stem-of-first-plan-MD-case>",
          "prompt": "Plan the fsi-dsp artifact selection for the request in the referenced MD case. Apply the 4-gate chain (intent → tool-class → drift → canon).",
          "expected_output": "A plan output matching the MD case's expected_artifact / required_claims / forbidden_claims frontmatter.",
          "files": ["tests/golden/act/cases/<stem>.md"],
          "expectations": [
            "Plan output references the expected_artifact from the MD case",
            "Plan output's required_claims appear in the response",
            "Plan output's forbidden_claims do NOT appear (especially the standard `resource \"confluent_` no-inline-Terraform constraint per ACT-06)"
          ]
        }
        // ... 21 more wrapper cases, ids 2..22 ...
        ,
        {
          "id": 23,
          "prompt": "Plan a change to an existing Tableflow-enabled topic switching from CHANGELOG to APPEND mode after first materialization.",
          "expected_output": "Plan refuses — directs operator to delete+recreate per Tableflow changelog mode immutability rule.",
          "files": [],
          "expectations": [
            "Refuses to plan a Tableflow changelog mode change on an already-materialized topic — directs to delete+recreate per immutability rule",
            "Plan cites wiki/concepts/tableflow-changelog-mode-immutability.md or equivalent canonical reference",
            "Plan output uses `no matching artifact` per ACT-06 negative-space convention"
          ]
        },
        {
          "id": 24,
          "prompt": "Plan an OracleXStreamSource connector with `after.state.only=true` to reduce payload size.",
          "expected_output": "Plan refuses — Oracle XStream does not support after.state.only config.",
          "files": [],
          "expectations": [
            "Refuses to plan OracleXStreamSource with `after.state.only=true` — that config is not supported by Oracle XStream",
            "Plan cites wiki/concepts/oracle-xstream-source-limitations.md or equivalent canonical reference",
            "Plan output uses `no matching artifact` per ACT-06 negative-space convention"
          ]
        },
        {
          "id": 25,
          "prompt": "Plan a JSON Schema registration against a WarpStream cluster's built-in Schema Registry endpoint.",
          "expected_output": "Plan refuses — WarpStream's built-in Schema Registry supports only Avro and Protobuf.",
          "files": [],
          "expectations": [
            "Refuses to plan JSON Schema registration against WarpStream's built-in Schema Registry — accepts Avro or Protobuf only",
            "Plan cites wiki/concepts/warpstream-schema-registry-format-constraint.md or equivalent canonical reference",
            "Plan output includes the FSI-context note that WarpStream is competitive context, not FSI production",
            "Plan output uses `no matching artifact` per ACT-06 negative-space convention"
          ]
        }
      ]
    }
    ```

    Authoring steps:

    1. Run the grep above to list the 22 /dsp:plan MD case stems.
    2. Emit wrapper cases 1..22, one per stem.
    3. Append trip-wire cases 23..25 with verbatim D-08 strings.
    4. Validate trip-wire string presence via bytewise grep.

    Same encoding constraints as Task 1 (comma arrays, literal backticks, em-dashes, trailing newline).
  </action>
  <verify>
    <automated>test -f tests/evals/dsp-plan/evals.json && python -c "import json; d=json.load(open('tests/evals/dsp-plan/evals.json')); assert d['skill_name'] == '/dsp:plan', d['skill_name']; assert len(d['evals']) >= 10, len(d['evals']); ids=[e['id'] for e in d['evals']]; assert len(ids) == len(set(ids)), 'dup ids'; refs=[e.get('case_ref') for e in d['evals'] if e.get('case_ref')]; assert len(refs) >= 22, f'expected >=22 case_refs, got {len(refs)}'; print('OK', len(d['evals']), 'cases,', len(refs), 'case_refs')" && grep -c "Refuses to plan a Tableflow changelog mode change on an already-materialized topic" tests/evals/dsp-plan/evals.json && grep -c "Refuses to plan OracleXStreamSource with" tests/evals/dsp-plan/evals.json && grep -c "Refuses to plan JSON Schema registration against WarpStream" tests/evals/dsp-plan/evals.json && for ref in $(python -c "import json; d=json.load(open('tests/evals/dsp-plan/evals.json')); print(' '.join(e['case_ref'] for e in d['evals'] if e.get('case_ref')))"); do test -f "tests/golden/act/cases/${ref}.md" || { echo "MISSING: $ref"; exit 1; }; if grep -q '^skill: /dsp:apply' "tests/golden/act/cases/${ref}.md"; then echo "WRONG SKILL (should be plan): $ref"; exit 1; fi; done</automated>
  </verify>
  <done>
    - `tests/evals/dsp-plan/evals.json` exists, valid JSON, `skill_name == "/dsp:plan"`.
    - `len(evals) >= 10`; expected 25.
    - 22 case_refs resolve to existing files in tests/golden/act/cases/; none have `skill: /dsp:apply` (all are plan cases).
    - Each of the 3 D-08 trip-wire verbatim strings appears exactly once via grep.
    - `python -m pytest tests/evals/run_skill_evals.py::test_threshold_per_skill -v` PASSES.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Author tests/evals/dsp-apply/evals.json (thin wrapper: 10 existing MD case_refs; no trip-wires per D-08)</name>
  <files>tests/evals/dsp-apply/evals.json</files>
  <read_first>
    - tests/evals/dsp-apply/evals.json (will not exist — confirm and create)
    - .planning/phases/H.2-eval-harness-extension/H.2-CONTEXT.md (D-03 schema, D-08 confirms NO trip-wires for /dsp:apply)
    - tests/evals/dsp-plan/evals.json (sibling shape from Task 2)
    - tests/golden/act/cases/ (filter for files with `skill: /dsp:apply` frontmatter — 10 cases)
    - .claude/commands/dsp-apply.md (the skill being tested; D-11 byte-identical lock — do NOT modify)
  </read_first>
  <behavior>
    - Test 1: File parses as valid JSON.
    - Test 2: `skill_name == "/dsp:apply"`.
    - Test 3: `len(evals) >= 10` (specifically: 10 case_refs).
    - Test 4: At least 10 cases have a `case_ref` field referencing an existing /dsp:apply MD case.
    - Test 5: Every case_ref resolves to a file in tests/golden/act/cases/ AND that file HAS `skill: /dsp:apply` frontmatter.
    - Test 6: NO trip-wire expectation strings are encoded (per D-08 — /dsp:apply gets no trip-wires).
    - Test 7: `tools/apply_engine.py` and `.claude/commands/dsp-apply.md` are byte-identical pre/post (D-11 lock).
  </behavior>
  <action>
    Enumerate existing /dsp:apply MD case stems:
    ```bash
    grep -l '^skill: /dsp:apply' tests/golden/act/cases/*.md | xargs -n1 basename | sed 's/\.md$//'
    ```
    This yields 10 stems (verified by earlier discovery in this plan's authoring).

    Create `tests/evals/dsp-apply/evals.json` as a pure wrapper — NO trip-wires per D-08.

    Each wrapper case references one /dsp:apply MD case. Expectations are drawn from the MD case's frontmatter contract (profile, confirmation, expected_incident, required_claims, forbidden_claims).

    File structure:

    ```json
    {
      "skill_name": "/dsp:apply",
      "evals": [
        {
          "id": 1,
          "case_ref": "<stem-of-first-apply-MD-case>",
          "prompt": "Apply the fsi-dsp artifact referenced by the MD case under the specified profile.",
          "expected_output": "Apply output matching the MD case's expected_artifact / profile / confirmation / expected_incident frontmatter.",
          "files": ["tests/golden/act/cases/<stem>.md"],
          "expectations": [
            "Apply respects the profile gating from the MD case frontmatter (read-only fails closed; engineer permitted; break-glass requires explicit operator confirmation)",
            "Apply respects the confirmation requirement — `bypass_attempt` cases produce a refusal log entry per ACTA-02",
            "Apply records an incident entry under wiki/incidents/ only if the MD case's expected_incident is true",
            "Apply does NOT generate inline Terraform — `resource \"confluent_` MUST NOT appear in any output (ACT-06)"
          ]
        }
        // ... 9 more wrapper cases, ids 2..10 ...
      ]
    }
    ```

    Authoring steps:

    1. Run the grep above to enumerate the 10 /dsp:apply case stems.
    2. Emit wrapper cases 1..10, one per stem.
    3. NO trip-wire cases — confirmed by D-08 distribution.
    4. Validate via verify block.

    Encoding constraints same as Tasks 1-2.

    **D-11 lock self-check:** Before declaring done, confirm `git diff --quiet tools/apply_engine.py .claude/commands/dsp-apply.md` exits 0. This plan must NOT modify those files — eval harness is testing infrastructure only, not runtime.
  </action>
  <verify>
    <automated>test -f tests/evals/dsp-apply/evals.json && python -c "import json; d=json.load(open('tests/evals/dsp-apply/evals.json')); assert d['skill_name'] == '/dsp:apply', d['skill_name']; assert len(d['evals']) >= 10, len(d['evals']); ids=[e['id'] for e in d['evals']]; assert len(ids) == len(set(ids)), 'dup ids'; refs=[e.get('case_ref') for e in d['evals'] if e.get('case_ref')]; assert len(refs) >= 10, f'expected >=10 case_refs, got {len(refs)}'; print('OK', len(d['evals']), 'cases,', len(refs), 'case_refs')" && for ref in $(python -c "import json; d=json.load(open('tests/evals/dsp-apply/evals.json')); print(' '.join(e['case_ref'] for e in d['evals'] if e.get('case_ref')))"); do test -f "tests/golden/act/cases/${ref}.md" || { echo "MISSING: $ref"; exit 1; }; if ! grep -q '^skill: /dsp:apply' "tests/golden/act/cases/${ref}.md"; then echo "WRONG SKILL (should be apply): $ref"; exit 1; fi; done && git diff --quiet tools/apply_engine.py .claude/commands/dsp-apply.md && echo "D-11 lock: OK"</automated>
  </verify>
  <done>
    - `tests/evals/dsp-apply/evals.json` exists, valid JSON, `skill_name == "/dsp:apply"`.
    - `len(evals) >= 10`; expected 10.
    - 10 case_refs resolve to existing files in `tests/golden/act/cases/`; ALL have `skill: /dsp:apply` frontmatter.
    - File contains NO trip-wire expectation strings (D-08 distribution: /dsp:apply gets none).
    - `git diff --quiet tools/apply_engine.py .claude/commands/dsp-apply.md` exits 0 (D-11 lock).
    - `python -m pytest tests/evals/run_skill_evals.py::test_threshold_per_skill -v` PASSES.
  </done>
</task>

</tasks>

<verification>
After all three tasks complete:

1. **All 3 wrapper files exist:** `for s in review dsp-plan dsp-apply; do test -f "tests/evals/$s/evals.json" || echo "MISSING $s"; done` produces no output.
2. **Skill names correct:** `for s in review dsp-plan dsp-apply; do python -c "import json; d=json.load(open(f'tests/evals/$s/evals.json')); print(d['skill_name'])"; done` outputs `/review`, `/dsp:plan`, `/dsp:apply` respectively.
3. **Case counts meet floor:** every file has `len(evals) >= 10`.
4. **case_refs resolve:** every `case_ref` string maps to an existing file under `tests/golden/{review,act}/cases/`.
5. **Trip-wires verbatim:**
   - `/review` has exactly 4 trip-wire strings (Tableflow-on-CDC, EOS-WarpStream, kafka-console-producer, KS-4x StreamsUncaughtExceptionHandler).
   - `/dsp:plan` has exactly 3 trip-wire strings (Tableflow changelog mode, OracleXStream after.state.only, WarpStream JSON Schema).
   - `/dsp:apply` has 0 trip-wire strings (per D-08).
6. **Runner picks up new cases:** `python -m pytest tests/evals/run_skill_evals.py --collect-only -q 2>&1 | tail -3` — collected count grows by 20 + 25 + 10 = 55 vs Plan 02 baseline.
7. **Threshold gate passes:** `python -m pytest tests/evals/run_skill_evals.py::test_threshold_per_skill -v` PASSES.
8. **Coverage gate now CLOSES:** `python -m pytest tests/evals/run_skill_evals.py::test_all_seven_new_skills_discovered -v` PASSES (all 7 required skills now present after Plans 02 + 03 combined).
9. **Existing harnesses unaffected:** `python -m pytest tests/golden/ -q --tb=no` PASSES.
10. **No changes to locked files (D-11):** `git diff --quiet tools/apply_engine.py .claude/commands/dsp-apply.md tests/golden/` exits 0.
11. **Combined trip-wire count (Plan 02 + Plan 03):** 2 (wiki-ingest) + 4 (review) + 3 (dsp-plan) + 0 (dsp-apply) = 9. Well above EVAL-03's "≥5 trip-wires" floor.
12. **JSON shape lesson (H.1):** all arrays are comma-separated; `grep -E '" +"[a-zA-Z]' tests/evals/{review,dsp-plan,dsp-apply}/evals.json` returns nothing.
</verification>

<success_criteria>
- EVAL-02 satisfied for the remaining 3/7 named skills: /review, /dsp:plan, /dsp:apply each have >= 10 cases.
- EVAL-03 satisfied for the trip-wire half: 7 of 9 H.1 trip-wires encoded as verbatim expectations[] strings here (combined with Plan 02's 2 = all 9). CI half lands in Plan 04.
- D-01 hybrid lock honored: zero modifications to tests/golden/{review,act}/cases/*.md.
- D-03 upstream-schema verbatim: every file matches `{"skill_name", "evals": [{"id", "prompt", "expected_output", "files", "expectations", "case_ref"?}]}` shape.
- D-04 structural-only: every expectation is grep-checkable; no LLM-judgment phrasing.
- D-08 trip-wire distribution honored: exactly 4 in /review, 3 in /dsp:plan, 0 in /dsp:apply, 2 in /wiki:ingest (Plan 02).
- D-11 lock: `tools/apply_engine.py` + `.claude/commands/dsp-apply.md` byte-identical.
- After Plans 02 + 03 land together, the runner's `test_all_seven_new_skills_discovered` test transitions RED→GREEN.
</success_criteria>

<output>
After completion, create `.planning/phases/H.2-eval-harness-extension/H.2-03-SUMMARY.md` documenting:
- Per-file case counts (target: /review 20, /dsp:plan 25, /dsp:apply 10)
- The 7 trip-wire expectation strings landed here, with file + line numbers
- Confirmation that all case_refs resolve to existing MD cases with correct skill attribution
- Confirmation that D-11 lock held (git diff of tools/apply_engine.py and .claude/commands/dsp-apply.md is empty)
</output>
