---
phase: G.2c-tool-classification-rename
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tools/regenerate_tool_classification.py
  - tests/test_regenerate_tool_classification.py
  - tests/fixtures/mcp_confluent_tool_name_sample.js
autonomous: true
requirements_addressed:
  - ACTG-01
must_haves:
  truths:
    - "Running `python tools/regenerate_tool_classification.py --check` exits 0 when committed JSON matches live registry"
    - "Running `python tools/regenerate_tool_classification.py --check` exits 1 and prints divergences when JSON drifts from live registry"
    - "Running `python tools/regenerate_tool_classification.py` (no flag) rewrites tools/profiles/tool_classification.json from the pinned mcp-confluent version"
    - "Generator applies the verb-prefix rule (D-05) and the explicit overrides for produce-message and consume-messages"
    - "Generator pins to the version stored in tool_classification.json `mcp_confluent_version` field; takes --version override only when the file is absent or being initialized"
  artifacts:
    - path: "tools/regenerate_tool_classification.py"
      provides: "Generator + checker for tool_classification.json"
      contains: "def parse_tool_name_js"
    - path: "tests/test_regenerate_tool_classification.py"
      provides: "Unit tests for the regex parser and verb-prefix classifier against a static fixture"
      contains: "def test_parse_tool_name_js_extracts_kebab_names"
    - path: "tests/fixtures/mcp_confluent_tool_name_sample.js"
      provides: "Static minimal sample of tool-name.js for offline parser testing"
      contains: "ToolName"
  key_links:
    - from: "tools/regenerate_tool_classification.py"
      to: "@confluentinc/mcp-confluent dist/confluent/tools/tool-name.js"
      via: "subprocess.run(['npm', 'install', ...]) into tempfile.TemporaryDirectory + regex parse"
      pattern: "ToolName\\[\\\"[A-Z_]+\\\"\\]\\s*=\\s*\\\"[a-z-]+\\\""
    - from: "tools/regenerate_tool_classification.py"
      to: "verb-prefix rule from D-05"
      via: "classify_tier(tool_name) function with explicit OVERRIDES dict"
      pattern: "OVERRIDES = \\{.*produce-message.*break-glass.*consume-messages.*break-glass.*\\}"
---

<objective>
Build `tools/regenerate_tool_classification.py` — a dual-mode generator/checker that is the single source of truth for keeping `tools/profiles/tool_classification.json` aligned with the pinned `@confluentinc/mcp-confluent` package. This script underpins both the big-bang rewrite in G.2c-02 and the CI drift gate in G.2c-03. Per D-01/D-02, it is fully self-contained: pins live in the JSON file itself, npm-install runs into a controlled temp prefix, no reliance on the per-machine `~/.npm/_npx/...` cache.

Purpose: Make `tool_classification.json` reproducible from a clean machine and machine-verifiable in CI. Per ACTG-01, every mcp-confluent tool must be classified by exact name — this script guarantees that property holds against the real registry.

Output: One Python tool (`tools/regenerate_tool_classification.py`), one pytest module exercising the parser + classifier in isolation, and one static fixture file capturing the shape of `tool-name.js` so tests run offline.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/G.2c-tool-classification-rename/G.2c-CONTEXT.md
@tools/profiles/tool_classification.json
@tools/apply_engine.py
@tools/check-canon-parity.py

<interfaces>
<!-- Existing runtime contract the generator must preserve. -->
<!-- From tools/apply_engine.py lines 49-55: -->

```python
def load_tool_classification() -> Dict:
    """Load tool_classification.json. Cached after first load."""
    global _tool_classification_cache
    if _tool_classification_cache is None:
        path = PROFILES_DIR / "tool_classification.json"
        _tool_classification_cache = json.loads(path.read_text())
    return _tool_classification_cache
```

The file MUST remain valid JSON with top-level `tools` (dict of name → tier string) and `unclassified_policy` ("deny"). Generator must preserve `version` ("1"), `description`, add `mcp_confluent_version` (pin), and add `tier_rule` (documents the verb-prefix rule for human reviewers).

Tier values are exactly: `"read-only"`, `"engineer"`, `"break-glass"` (see `PROFILE_TIER_ORDER` in apply_engine.py line 39).
</interfaces>
</context>

<tasks>

<task id="01" type="auto" tdd="true">
  <name>Task 1: Author static fixture + parser/classifier unit tests (RED)</name>
  <files>tests/fixtures/mcp_confluent_tool_name_sample.js, tests/test_regenerate_tool_classification.py</files>
  <read_first>
    - tools/profiles/tool_classification.json (current shape — preserve top-level fields)
    - tools/apply_engine.py (lines 32-81: load_tool_classification + check_tool_permitted + PROFILE_TIER_ORDER — runtime contract the JSON must keep satisfying)
    - .planning/phases/G.2c-tool-classification-rename/G.2c-CONTEXT.md (D-01, D-05, D-06; the <specifics> section for the 50-tool list and override rules)
    - tests/test_profile_gating.py lines 22-30 (existing pattern for loading classification from disk in tests)
    - tools/check-canon-parity.py (existing tools/ pattern for a CI-runnable checker script — pure stdlib, exits 0/1, prints to stderr)
  </read_first>
  <behavior>
    - parse_tool_name_js(content: str) -> set[str] extracts every kebab-case value from `ToolName["KEY"] = "kebab-name";` lines. Returns a set of kebab-case strings.
    - classify_tier(tool_name: str) -> str applies D-05 verb-prefix rule with overrides:
      - "list-topics" → "read-only" (list- prefix)
      - "read-environment" → "read-only" (read- prefix)
      - "get-topic-config" → "read-only" (get- prefix)
      - "search-topics-by-tag" → "read-only" (search- prefix)
      - "detect-flink-statement-issues" → "read-only" (detect- prefix)
      - "check-flink-statement-health" → "read-only" (check- prefix)
      - "describe-flink-table" → "read-only" (describe- prefix)
      - "query-metrics" → "read-only" (query- prefix)
      - "create-topics" → "engineer" (create- prefix)
      - "update-tableflow-topic" → "engineer" (update- prefix)
      - "alter-topic-config" → "engineer" (alter- prefix)
      - "add-tags-to-topic" → "engineer" (add- prefix)
      - "delete-topics" → "break-glass" (delete- prefix)
      - "remove-tag-from-entity" → "break-glass" (remove- prefix)
      - "produce-message" → "break-glass" (EXPLICIT OVERRIDE — verb-prefix would not match)
      - "consume-messages" → "break-glass" (EXPLICIT OVERRIDE — verb-prefix would not match)
      - Unknown verb prefix raises a ValueError so CI fails loudly when mcp-confluent adds a new shape (per D-06: regeneration aid, not runtime fallback).
    - build_classification(tool_names: set[str], mcp_confluent_version: str) -> dict produces the full JSON-ready dict with: version="1", description, mcp_confluent_version, tier_rule (a string documenting D-05), tools (sorted dict — flat alphabetical so the next bump PR has a clean diff per D-05 "Claude's Discretion"), unclassified_policy="deny".
    - diff_classification(committed: dict, expected: dict) -> tuple[list[str], list[str]] returns (missing_from_committed, extra_in_committed) for bidirectional drift detection per D-08.
  </behavior>
  <action>
    Step 1: Write `tests/fixtures/mcp_confluent_tool_name_sample.js` — a small, hand-crafted excerpt that mimics the real `dist/confluent/tools/tool-name.js` shape. Include at minimum these enum lines (covering every D-05 verb-prefix branch + both explicit overrides):

    ```javascript
    export var ToolName;
    (function (ToolName) {
        ToolName["LIST_TOPICS"] = "list-topics";
        ToolName["READ_ENVIRONMENT"] = "read-environment";
        ToolName["GET_TOPIC_CONFIG"] = "get-topic-config";
        ToolName["SEARCH_TOPICS_BY_TAG"] = "search-topics-by-tag";
        ToolName["DETECT_FLINK_STATEMENT_ISSUES"] = "detect-flink-statement-issues";
        ToolName["CHECK_FLINK_STATEMENT_HEALTH"] = "check-flink-statement-health";
        ToolName["DESCRIBE_FLINK_TABLE"] = "describe-flink-table";
        ToolName["QUERY_METRICS"] = "query-metrics";
        ToolName["CREATE_TOPICS"] = "create-topics";
        ToolName["UPDATE_TABLEFLOW_TOPIC"] = "update-tableflow-topic";
        ToolName["ALTER_TOPIC_CONFIG"] = "alter-topic-config";
        ToolName["ADD_TAGS_TO_TOPIC"] = "add-tags-to-topic";
        ToolName["DELETE_TOPICS"] = "delete-topics";
        ToolName["REMOVE_TAG_FROM_ENTITY"] = "remove-tag-from-entity";
        ToolName["PRODUCE_MESSAGE"] = "produce-message";
        ToolName["CONSUME_MESSAGES"] = "consume-messages";
    })(ToolName || (ToolName = {}));
    ```

    Step 2: Write `tests/test_regenerate_tool_classification.py` with these test classes:

    - `TestParseToolNameJs`:
      - `test_parse_extracts_all_kebab_names`: parser returns set of exactly the 16 kebab names above when fed the fixture.
      - `test_parse_ignores_non_toolname_lines`: parser ignores `(function ...)` lines, comments, blank lines.
      - `test_parse_handles_real_world_quoting`: parser handles both `ToolName["X"]` and `ToolName['X']` quote styles (be defensive — TypeScript compilers emit both).

    - `TestClassifyTier`:
      - `test_read_only_prefixes`: parametrized over the 8 read-only verbs (list, read, get, search, detect, check, describe, query) — each maps to "read-only".
      - `test_engineer_prefixes`: parametrized over (create, update, alter, add) — each maps to "engineer".
      - `test_break_glass_prefixes`: parametrized over (delete, remove) — each maps to "break-glass".
      - `test_produce_message_override`: classify_tier("produce-message") == "break-glass".
      - `test_consume_messages_override`: classify_tier("consume-messages") == "break-glass".
      - `test_unknown_verb_prefix_raises`: classify_tier("frobnicate-cluster") raises ValueError mentioning the tool name and the unknown prefix.

    - `TestBuildClassification`:
      - `test_top_level_fields_present`: result has keys `version`, `description`, `mcp_confluent_version`, `tier_rule`, `tools`, `unclassified_policy`.
      - `test_version_field_is_1`: result["version"] == "1" (file format version, unchanged from current).
      - `test_unclassified_policy_is_deny`: result["unclassified_policy"] == "deny".
      - `test_tools_sorted_alphabetically`: list(result["tools"].keys()) is sorted ascending.
      - `test_mcp_confluent_version_threaded_through`: build_classification(names, "1.3.0")["mcp_confluent_version"] == "1.3.0".
      - `test_every_input_tool_classified`: build_classification(parse(fixture), "1.3.0")["tools"] has exactly the 16 fixture tool names as keys.

    - `TestDiffClassification`:
      - `test_identical_returns_empty_diffs`: diff(d, d) returns ([], []).
      - `test_missing_from_committed_detected`: diff with one tool added to expected returns it in first element.
      - `test_extra_in_committed_detected`: diff with one tool removed from expected returns it in second element.
      - `test_bidirectional_drift_detected`: diff with both forms returns both populated lists.

    Tests are RED at this point — `tools/regenerate_tool_classification.py` does not yet exist. Running them must fail with `ModuleNotFoundError` or `ImportError`.

    Imports in the test file follow the existing tests/test_profile_gating.py pattern:
    ```python
    import sys
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))
    from tools.regenerate_tool_classification import (
        parse_tool_name_js,
        classify_tier,
        build_classification,
        diff_classification,
    )
    ```
  </action>
  <verify>
    <automated>pytest tests/test_regenerate_tool_classification.py -v 2>&1 | grep -E "(ImportError|ModuleNotFoundError|collection errors)" || (echo "Tests should be RED (ImportError) — they pass or fail for wrong reason"; exit 1)</automated>
  </verify>
  <acceptance_criteria>
    - `test -f tests/fixtures/mcp_confluent_tool_name_sample.js` exits 0
    - `test -f tests/test_regenerate_tool_classification.py` exits 0
    - `grep -c 'ToolName\["' tests/fixtures/mcp_confluent_tool_name_sample.js` returns 16
    - `grep -c '"produce-message"' tests/fixtures/mcp_confluent_tool_name_sample.js` returns 1
    - `grep -c '"consume-messages"' tests/fixtures/mcp_confluent_tool_name_sample.js` returns 1
    - `grep -E "from tools.regenerate_tool_classification import" tests/test_regenerate_tool_classification.py` returns a match
    - `pytest tests/test_regenerate_tool_classification.py -v 2>&1 | grep -E "ImportError|ModuleNotFoundError"` returns a match (tests fail RED because the module does not exist yet)
  </acceptance_criteria>
  <done>Static fixture exists with all D-05 verb branches + both overrides represented; test module exists with parametrized coverage of parser, classifier, builder, and diff functions; pytest run is RED with ImportError (proving the test suite is wired but the implementation is missing). Commit RED test scaffold: `test(G.2c-01): add failing tests for regenerate_tool_classification`.</done>
</task>

<task id="02" type="auto" tdd="true">
  <name>Task 2: Implement regenerate_tool_classification.py + GREEN the unit tests + self-check against real registry</name>
  <files>tools/regenerate_tool_classification.py</files>
  <read_first>
    - tests/test_regenerate_tool_classification.py (from Task 1 — the contract this script must satisfy)
    - tests/fixtures/mcp_confluent_tool_name_sample.js (test input)
    - tools/profiles/tool_classification.json (existing file the script will eventually overwrite — read for current top-level fields: version, description, unclassified_policy)
    - tools/check-canon-parity.py (existing tools/ script pattern: argparse, exit codes, print to stderr on drift)
    - tools/apply_engine.py lines 32-55 (the load_tool_classification contract — the JSON must keep working with this loader)
    - .planning/phases/G.2c-tool-classification-rename/G.2c-CONTEXT.md (D-01, D-02, D-05, D-06, D-07, D-08, D-09)
  </read_first>
  <behavior>
    All `TestParseToolNameJs`, `TestClassifyTier`, `TestBuildClassification`, `TestDiffClassification` tests from Task 1 pass GREEN. Additionally, the script must:
    - Provide a CLI: `python tools/regenerate_tool_classification.py [--check] [--version VERSION] [--dry-run]`
    - Default mode (no flags): npm-install pinned mcp-confluent into a temp prefix, parse, classify, write to `tools/profiles/tool_classification.json`. Exit 0.
    - `--check` mode: npm-install pinned version into temp prefix, parse, classify, compare against committed JSON, exit 0 if identical, exit 1 with stderr diff if drifted.
    - `--dry-run` mode: use the static fixture instead of npm-installing — runs parse + classify + build path against `tests/fixtures/mcp_confluent_tool_name_sample.js`, prints the resulting JSON to stdout, never touches disk. Exit 0. (This is the self-test that proves the parser/classifier chain works without network access.)
    - `--version` flag overrides the pin from the committed JSON file. If the committed JSON does not exist, --version is required.
    - Reads version from existing `tool_classification.json` `mcp_confluent_version` field. If field absent and --version not given, exit 1 with clear error.
  </behavior>
  <action>
    Step 1: Write `tools/regenerate_tool_classification.py` with this structure:

    NOTE on operating-mode scope: The `--dry-run` mode is planner-added under D-05 "Claude's Discretion" (exact shell/Python plumbing). It enables the unit-test gate to validate parsing against a static fixture without npm-installing. Locked-spec modes per CONTEXT.md D-01/D-07/D-08 are default-regenerate and `--check` only.

    NOTE on tier_rule field: D-05 specifies "comment block at the top of tool_classification.json"; JSON does not support comments, so the rule is stored as a top-level `tier_rule` string field. Semantic intent (human-readable rule visible when the file is opened) is preserved.

    ```python
    #!/usr/bin/env python3
    """
    Regenerate tools/profiles/tool_classification.json from the pinned
    @confluentinc/mcp-confluent package's dist/confluent/tools/tool-name.js.

    Modes:
      (default)     Regenerate the JSON file from the live registry.
      --check       Compare committed JSON against live registry; exit 1 on drift.
      --dry-run     Use the static fixture under tests/fixtures/ instead of npm-installing.
      --version X   Override the pinned mcp-confluent version (otherwise read from JSON).

    Requirements: ACTG-01 (every mcp-confluent tool classified by exact name).
    """
    import argparse
    import json
    import re
    import subprocess
    import sys
    import tempfile
    from pathlib import Path
    from typing import Dict, List, Set, Tuple

    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    JSON_PATH = PROJECT_ROOT / "tools" / "profiles" / "tool_classification.json"
    FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "mcp_confluent_tool_name_sample.js"

    # D-05 verb-prefix rule. Order matters: longest match wins is unnecessary because
    # prefixes are disjoint, but we keep tuples for clarity.
    READ_ONLY_PREFIXES = ("list-", "read-", "get-", "search-", "detect-", "check-", "describe-", "query-")
    ENGINEER_PREFIXES = ("create-", "update-", "alter-", "add-")
    BREAK_GLASS_PREFIXES = ("delete-", "remove-")

    # Explicit tier overrides for tools whose verb does not match any prefix
    # OR whose verb-prefix tier is wrong for FSI canon (data-plane safety).
    # See G.2c-CONTEXT.md D-05 "Exceptions".
    OVERRIDES: Dict[str, str] = {
        "produce-message": "break-glass",   # data-plane write; production guard
        "consume-messages": "break-glass",  # data-plane read; FSI PII consideration
    }

    TIER_RULE_DOC = (
        "Verb-prefix rule: list-/read-/get-/search-/detect-/check-/describe-/query- → read-only; "
        "create-/update-/alter-/add- → engineer; delete-/remove- → break-glass. "
        "Overrides: produce-message → break-glass; consume-messages → break-glass. "
        "Regenerate via `python tools/regenerate_tool_classification.py`."
    )

    TOOL_NAME_RE = re.compile(r"""ToolName\[\s*["']([A-Z_]+)["']\s*\]\s*=\s*["']([a-z][a-z0-9\-]*)["']""")


    def parse_tool_name_js(content: str) -> Set[str]:
        return {m.group(2) for m in TOOL_NAME_RE.finditer(content)}


    def classify_tier(tool_name: str) -> str:
        if tool_name in OVERRIDES:
            return OVERRIDES[tool_name]
        for p in READ_ONLY_PREFIXES:
            if tool_name.startswith(p):
                return "read-only"
        for p in ENGINEER_PREFIXES:
            if tool_name.startswith(p):
                return "engineer"
        for p in BREAK_GLASS_PREFIXES:
            if tool_name.startswith(p):
                return "break-glass"
        raise ValueError(
            f"Cannot classify tool {tool_name!r}: no known verb prefix "
            f"and no entry in OVERRIDES. Add an explicit override in "
            f"tools/regenerate_tool_classification.py OVERRIDES dict."
        )


    def build_classification(tool_names: Set[str], mcp_confluent_version: str) -> Dict:
        tools = {name: classify_tier(name) for name in sorted(tool_names)}
        return {
            "version": "1",
            "description": (
                "mcp-confluent tool-to-tier mapping. "
                "Tier hierarchy: read-only < engineer < break-glass. "
                "Unclassified tools denied by all profiles."
            ),
            "mcp_confluent_version": mcp_confluent_version,
            "tier_rule": TIER_RULE_DOC,
            "tools": tools,
            "unclassified_policy": "deny",
        }


    def diff_classification(committed: Dict, expected: Dict) -> Tuple[List[str], List[str]]:
        c_tools = set(committed.get("tools", {}).keys())
        e_tools = set(expected.get("tools", {}).keys())
        missing_from_committed = sorted(e_tools - c_tools)
        extra_in_committed = sorted(c_tools - e_tools)
        return missing_from_committed, extra_in_committed


    def _install_and_read(version: str) -> str:
        """npm-install pinned mcp-confluent into a temp prefix and return tool-name.js contents."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subprocess.run(
                ["npm", "install", "--prefix", str(tmp_path), "--no-save", "--silent",
                 f"@confluentinc/mcp-confluent@{version}"],
                check=True,
            )
            js = tmp_path / "node_modules" / "@confluentinc" / "mcp-confluent" / "dist" / "confluent" / "tools" / "tool-name.js"
            if not js.exists():
                raise FileNotFoundError(f"tool-name.js not found after npm install at {js}")
            return js.read_text()


    def _resolve_version(args_version: str | None) -> str:
        if args_version:
            return args_version
        if JSON_PATH.exists():
            data = json.loads(JSON_PATH.read_text())
            v = data.get("mcp_confluent_version")
            if v:
                return v
        raise SystemExit(
            "No --version provided and tool_classification.json has no "
            "mcp_confluent_version field. Pass --version on first run."
        )


    def main() -> int:
        ap = argparse.ArgumentParser(description=__doc__)
        ap.add_argument("--check", action="store_true", help="Compare against committed JSON; exit 1 on drift.")
        ap.add_argument("--dry-run", action="store_true", help="Use static fixture instead of npm install.")
        ap.add_argument("--version", help="Override pinned mcp-confluent version.")
        args = ap.parse_args()

        if args.dry_run:
            content = FIXTURE_PATH.read_text()
            version = args.version or "fixture"
        else:
            version = _resolve_version(args.version)
            content = _install_and_read(version)

        tool_names = parse_tool_name_js(content)
        if not tool_names:
            print("ERROR: parser extracted zero tool names — regex or input changed", file=sys.stderr)
            return 1

        expected = build_classification(tool_names, version)

        if args.dry_run:
            print(json.dumps(expected, indent=2))
            return 0

        if args.check:
            if not JSON_PATH.exists():
                print(f"ERROR: {JSON_PATH} does not exist; cannot --check.", file=sys.stderr)
                return 1
            committed = json.loads(JSON_PATH.read_text())
            missing, extra = diff_classification(committed, expected)
            if missing or extra:
                print("DRIFT detected between committed tool_classification.json and live registry:", file=sys.stderr)
                if missing:
                    print(f"  Missing from committed (add with tier): {missing}", file=sys.stderr)
                if extra:
                    print(f"  Extra in committed (remove or pin older mcp-confluent): {extra}", file=sys.stderr)
                return 1
            print("OK: tool_classification.json matches mcp-confluent registry.", file=sys.stderr)
            return 0

        JSON_PATH.write_text(json.dumps(expected, indent=2) + "\n")
        print(f"Wrote {JSON_PATH} with {len(expected['tools'])} classified tools (mcp-confluent {version}).", file=sys.stderr)
        return 0


    if __name__ == "__main__":
        sys.exit(main())
    ```

    Step 2: Run `pytest tests/test_regenerate_tool_classification.py -v` — all tests must pass GREEN. Fix any divergence between the implementation above and the test expectations (e.g., if the regex over-matches, tighten it; if classify_tier ordering matters, adjust).

    Step 3: Run `python tools/regenerate_tool_classification.py --dry-run` — verify it prints a JSON document with the 16 fixture tools classified correctly. Save the output for visual inspection.

    Step 4: DO NOT overwrite `tool_classification.json` in this task. Task G.2c-02 will run the generator against the live 1.3.0 registry to perform the big-bang rewrite. This task ends with the generator working but the JSON file unchanged.

    Step 5: Commit `feat(G.2c-01): implement regenerate_tool_classification generator + checker`.
  </action>
  <verify>
    <automated>pytest tests/test_regenerate_tool_classification.py -v && python tools/regenerate_tool_classification.py --dry-run | python -c "import json, sys; d = json.load(sys.stdin); assert d['tools']['produce-message'] == 'break-glass', 'override failed'; assert d['tools']['consume-messages'] == 'break-glass', 'override failed'; assert d['tools']['list-topics'] == 'read-only', 'verb rule failed'; assert d['tools']['create-topics'] == 'engineer', 'verb rule failed'; assert d['tools']['delete-topics'] == 'break-glass', 'verb rule failed'; assert d['unclassified_policy'] == 'deny', 'policy missing'; assert d['mcp_confluent_version'] == 'fixture', 'version not threaded'; print('OK')"</automated>
  </verify>
  <acceptance_criteria>
    - `test -f tools/regenerate_tool_classification.py` exits 0
    - `python tools/regenerate_tool_classification.py --help` exits 0 and lists `--check`, `--dry-run`, `--version` flags
    - `pytest tests/test_regenerate_tool_classification.py -v` exits 0
    - `python tools/regenerate_tool_classification.py --dry-run | python -c "import json, sys; d=json.load(sys.stdin); assert len(d['tools']) == 16"` exits 0
    - `python tools/regenerate_tool_classification.py --dry-run | grep -c '"break-glass"' ` returns at least 4 (delete-topics, remove-tag-from-entity, produce-message, consume-messages)
    - `grep -c '"produce-message": "break-glass"' OVERRIDES.dump 2>/dev/null || python tools/regenerate_tool_classification.py --dry-run | grep -c '"produce-message": "break-glass"'` returns 1
    - `grep "OVERRIDES" tools/regenerate_tool_classification.py | grep -c "produce-message"` returns at least 1
    - `grep "unclassified_policy" tools/regenerate_tool_classification.py | grep -c "deny"` returns at least 1
    - `tools/profiles/tool_classification.json` is UNCHANGED from before this task (verify with `git diff --quiet tools/profiles/tool_classification.json`; exit 0 means no changes)
  </acceptance_criteria>
  <done>Generator script committed and passing all unit tests; `--dry-run` against fixture produces a correct, sorted, fully-classified JSON document with proper top-level fields; `tool_classification.json` is untouched (rewrite happens in G.2c-02). Run produces zero failures and the script is ready for both G.2c-02 (regenerate) and G.2c-03 (CI gate via --check).</done>
</task>

</tasks>

<verification>
- `pytest tests/test_regenerate_tool_classification.py -v` exits 0
- `python tools/regenerate_tool_classification.py --dry-run` exits 0 and emits a JSON document with all 16 fixture tools classified per D-05
- `python tools/regenerate_tool_classification.py --help` exits 0
- `git diff --quiet tools/profiles/tool_classification.json` exits 0 (this plan does NOT overwrite the JSON; that is G.2c-02's job)
- `grep -c "produce-message" tools/regenerate_tool_classification.py` returns at least 1 (override is implemented)
- `grep -c "consume-messages" tools/regenerate_tool_classification.py` returns at least 1 (override is implemented)
- `grep "READ_ONLY_PREFIXES" tools/regenerate_tool_classification.py` finds the verb-prefix table
- No changes to `tools/apply_engine.py`, `tools/profiles/*.json`, or `tests/test_profile_gating.py` (this is a tool-only plan)
</verification>

<success_criteria>
1. `tools/regenerate_tool_classification.py` exists, is executable Python, and provides the three operating modes (default regenerate, `--check`, `--dry-run`).
2. The script encodes D-05's verb-prefix rule and both explicit overrides (produce-message, consume-messages) in code, not regex.
3. Unit tests in `tests/test_regenerate_tool_classification.py` cover the parser, classifier, builder, and diff functions and all pass against the static fixture without network access.
4. The generator is the single source of truth: G.2c-02 will invoke it without flags to overwrite the JSON; G.2c-03 will wire `--check` into CI.
5. `tools/profiles/tool_classification.json` is unmodified by this plan — keeping the diff in G.2c-02 small and reviewable.
</success_criteria>

<output>
After completion, create `.planning/phases/G.2c-tool-classification-rename/G.2c-01-SUMMARY.md` per the standard summary template.
</output>
</content>
</invoke>