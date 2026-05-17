---
phase: G.2c-tool-classification-rename
plan: 02
type: execute
wave: 2
depends_on:
  - G.2c-01
files_modified:
  - tools/profiles/tool_classification.json
  - tests/test_apply_engine.py
autonomous: true
requirements_addressed:
  - ACTG-01
  - ACTG-02
  - ACTG-03
  - ACTG-04
must_haves:
  truths:
    - "tools/profiles/tool_classification.json contains exactly 50 kebab-case tool names that match the @confluentinc/mcp-confluent 1.3.0 dist/confluent/tools/tool-name.js registry"
    - "Every fictional snake_case entry (confluent_kafka_acl_*, confluent_peering_*, confluent_transit_gateway_*, etc.) has been removed"
    - "Every kebab-case tool is classified into exactly one of read-only / engineer / break-glass per D-05"
    - "produce-message and consume-messages are classified as break-glass (the two explicit overrides)"
    - "tool_classification.json has mcp_confluent_version: \"1.3.0\""
    - "tests/test_profile_gating.py (parametrized matrix) passes with the new keys with no manual edits required — matrix self-rebuilds from JSON"
    - "tests/test_apply_engine.py TestToolClassification suite passes with kebab-case tool names substituted in for the five hard-coded snake_case references at lines 441, 445, 449, 453, 457"
    - "tools/apply_engine.py is byte-identical to before the rename (verifying the key-opaque assumption holds)"
    - "ACTG-03 break-glass two-step flow is untouched — verified by .claude/commands/dsp-apply.md being byte-identical (the two-step confirmation logic lives in that slash command, not in pytest). git diff --quiet .claude/commands/dsp-apply.md exits 0."
    - "ACTG-04 customer differential gating remains intact — verified by tests/test_profile_gating.py TestCustomerDifferential passing unchanged"
  artifacts:
    - path: "tools/profiles/tool_classification.json"
      provides: "Live-registry-aligned classification table with 50 kebab-case keys + tier_rule documentation + mcp_confluent_version pin"
      contains: "list-topics"
    - path: "tests/test_apply_engine.py"
      provides: "Updated TestToolClassification assertions using kebab-case tool names"
      contains: "list-topics"
  key_links:
    - from: "tools/apply_engine.py:load_tool_classification"
      to: "tools/profiles/tool_classification.json"
      via: "json.loads(path.read_text()) — key-opaque, unchanged"
      pattern: "_tool_classification_cache = json.loads"
    - from: "tests/test_profile_gating.py"
      to: "tools/profiles/tool_classification.json"
      via: "CLASSIFICATION['tools'] parametrization at module load"
      pattern: "CLASSIFICATION\\['tools'\\]"
    - from: "tests/test_apply_engine.py TestToolClassification"
      to: "new kebab-case keys"
      via: "direct check_tool_permitted(profile, kebab-name) assertions"
      pattern: "check_tool_permitted\\(.*\"list-topics\""
---

<objective>
Execute the big-bang rename per D-03: regenerate `tools/profiles/tool_classification.json` from the live `@confluentinc/mcp-confluent@1.3.0` registry using the generator from G.2c-01, then update the five hard-coded snake_case tool-name references in `tests/test_apply_engine.py` to the kebab-case equivalents that survive. All other test suites (test_profile_gating.py, test_apply_executor.py) must pass unchanged — the parametrized matrix in test_profile_gating.py rebuilds itself from the JSON, and apply_engine.py is key-opaque per D-06.

Purpose: Replace the fictional snake_case table with the real 1.3.0 kebab-case table. This is the data half of G.2c — the engine half (CI gate) is G.2c-03. Together they close ACTG-01 against the actual mcp-confluent surface and verify ACTG-02/03/04 still hold.

Output: A rewritten `tool_classification.json` and a minimally-edited `tests/test_apply_engine.py`. No changes to `tools/apply_engine.py` or any profile JSON.
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
@.planning/phases/G.2c-tool-classification-rename/G.2c-01-PLAN.md
@tools/profiles/tool_classification.json
@tools/profiles/read-only.json
@tools/profiles/engineer.json
@tools/profiles/break-glass.json
@tools/apply_engine.py
@tests/test_profile_gating.py
@tests/test_apply_engine.py

<interfaces>
<!-- The runtime contract is unchanged. Only the keys flowing through change. -->
<!-- From tools/apply_engine.py: -->

```python
def check_tool_permitted(profile_name: str, tool_name: str, customer: Optional[str] = None) -> bool:
    classification = load_tool_classification()
    tools = classification.get("tools", {})
    if tool_name not in tools:
        return False
    required_tier = tools[tool_name]
    profile_idx = PROFILE_TIER_ORDER.index(profile_name)
    required_idx = PROFILE_TIER_ORDER.index(required_tier)
    return profile_idx >= required_idx
```

<!-- The five hard-coded snake_case references in tests/test_apply_engine.py (lines 439-457): -->

```python
def test_read_only_profile_permits_read_only_tool(self):
    assert check_tool_permitted("read-only", "confluent_kafka_topic_list") is True
def test_read_only_profile_denies_engineer_tool(self):
    assert check_tool_permitted("read-only", "confluent_kafka_topic_create") is False
def test_engineer_profile_permits_engineer_tool(self):
    assert check_tool_permitted("engineer", "confluent_kafka_topic_create") is True
def test_engineer_profile_denies_break_glass_tool(self):
    assert check_tool_permitted("engineer", "confluent_kafka_cluster_delete") is False
def test_break_glass_profile_permits_break_glass_tool(self):
    assert check_tool_permitted("break-glass", "confluent_kafka_cluster_delete") is True
```

<!-- Kebab-case equivalents that survive in the new 1.3.0 table: -->
<!-- confluent_kafka_topic_list   → list-topics            (read-only) -->
<!-- confluent_kafka_topic_create → create-topics          (engineer) -->
<!-- confluent_kafka_cluster_delete → delete-schema        (break-glass)  [Note: cluster_delete is fictional; substitute delete-schema to preserve cross-resource-family semantic — engineer denied a break-glass-tier delete on a non-topics resource, not just a different verb on topics] -->

<!-- Per G.2c-CONTEXT.md <specifics>, the full 50-tool 1.3.0 list (use VERBATIM): -->

Topics & data plane (7):
  list-topics, create-topics, delete-topics, produce-message, consume-messages, alter-topic-config, get-topic-config

Flink statements (8):
  list-flink-statements, create-flink-statement, read-flink-statement, delete-flink-statements,
  get-flink-statement-exceptions, check-flink-statement-health, detect-flink-statement-issues, get-flink-statement-profile

Flink catalog (5):
  list-flink-catalogs, list-flink-databases, list-flink-tables, describe-flink-table, get-flink-table-info

Connectors (4):
  list-connectors, read-connector, create-connector, delete-connector

Tags & search (7):
  search-topics-by-tag, search-topics-by-name, create-topic-tags, delete-tag, remove-tag-from-entity, add-tags-to-topic, list-tags

Clusters & environments (3):
  list-clusters, list-environments, read-environment

Schema Registry (2):
  list-schemas, delete-schema

Tableflow (11):
  create-tableflow-topic, list-tableflow-regions, list-tableflow-topics, read-tableflow-topic,
  update-tableflow-topic, delete-tableflow-topic, create-tableflow-catalog-integration,
  list-tableflow-catalog-integrations, read-tableflow-catalog-integration,
  update-tableflow-catalog-integration, delete-tableflow-catalog-integration

Billing & metrics (3):
  list-billing-costs, query-metrics, list-available-metrics

Total: 50 tools.
</interfaces>
</context>

<tasks>

<task id="01" type="auto">
  <name>Task 1: Regenerate tool_classification.json from live mcp-confluent@1.3.0 and verify parametrized test matrix self-rebuilds</name>
  <files>tools/profiles/tool_classification.json</files>
  <read_first>
    - tools/profiles/tool_classification.json (current snake_case state — about to be overwritten)
    - tools/regenerate_tool_classification.py (the generator from G.2c-01)
    - .planning/phases/G.2c-tool-classification-rename/G.2c-CONTEXT.md <specifics> section (the 50-tool kebab-case list, the fictional-deletion inventory, the verb-prefix tier rule with overrides for produce-message and consume-messages)
    - tools/apply_engine.py lines 32-81 (load_tool_classification + check_tool_permitted — must keep working post-rename)
    - tests/test_profile_gating.py lines 22-30 (parametrization source — matrix rebuilds from JSON automatically)
    - tools/profiles/read-only.json, engineer.json, break-glass.json (verify out-of-scope per CONTEXT.md `<domain>` — `allowed_operations` references artifacts like `module/topic`, NOT tool names)
  </read_first>
  <action>
    Step 1: Confirm the existing JSON has no `mcp_confluent_version` field yet — this is the first-run case. Inspect with: `python -c "import json; d=json.load(open('tools/profiles/tool_classification.json')); print('mcp_confluent_version' in d)"`. Expected: `False`.

    Step 2: Confirm `npm` is available on the local machine: `npm --version`. (Required for the generator's npm-install step.)

    Step 3: Run the generator with explicit version pin (first-run case):
    ```
    python tools/regenerate_tool_classification.py --version 1.3.0
    ```
    Expected behavior: npm-installs `@confluentinc/mcp-confluent@1.3.0` into a temp prefix, parses `dist/confluent/tools/tool-name.js`, classifies via the verb-prefix rule + overrides, writes `tools/profiles/tool_classification.json`. Prints a success line to stderr including the tool count (50).

    Step 4: Inspect the regenerated file:
    ```
    python -c "
    import json
    d = json.load(open('tools/profiles/tool_classification.json'))
    print('top-level keys:', sorted(d.keys()))
    print('mcp_confluent_version:', d['mcp_confluent_version'])
    print('unclassified_policy:', d['unclassified_policy'])
    print('tool count:', len(d['tools']))
    print('produce-message tier:', d['tools'].get('produce-message'))
    print('consume-messages tier:', d['tools'].get('consume-messages'))
    print('list-topics tier:', d['tools'].get('list-topics'))
    print('create-topics tier:', d['tools'].get('create-topics'))
    print('delete-topics tier:', d['tools'].get('delete-topics'))
    print('alter-topic-config tier:', d['tools'].get('alter-topic-config'))
    print('any snake_case keys?:', any('_' in k for k in d['tools']))
    "
    ```

    Expected output:
    ```
    top-level keys: ['description', 'mcp_confluent_version', 'tier_rule', 'tools', 'unclassified_policy', 'version']
    mcp_confluent_version: 1.3.0
    unclassified_policy: deny
    tool count: 50
    produce-message tier: break-glass
    consume-messages tier: break-glass
    list-topics tier: read-only
    create-topics tier: engineer
    delete-topics tier: break-glass
    alter-topic-config tier: engineer
    any snake_case keys?: False
    ```

    If the tool count is not exactly 50, the live registry has changed since CONTEXT.md was authored — STOP and report the divergence; do not proceed silently. The plan is pinned to 50 tools per CONTEXT.md `<specifics>`.

    Step 5: Run the existing parametrized gating test suite WITHOUT modifying it — it must self-rebuild from the new JSON keys:
    ```
    pytest tests/test_profile_gating.py -v
    ```
    Expected: every test in `TestClassificationCoverage`, `TestReadOnlyGating`, `TestEngineerGating`, `TestBreakGlassGating`, `TestUnclassifiedToolDenial`, and `TestCustomerDifferential` passes. The parametrized matrix now runs 50 tools × 3 profiles. If any assertion fails, debug — likely root cause is either (a) the file has unexpected tool count (live registry drift) or (b) `check_tool_permitted()` has a side dependency we didn't account for.

    Step 6: Confirm `tools/apply_engine.py` was not modified — the key-opaque assumption holds:
    ```
    git diff --quiet tools/apply_engine.py && echo "apply_engine.py unchanged ✓" || echo "FAIL: apply_engine.py modified"
    ```

    Step 7: Confirm none of the profile JSON files (`read-only.json`, `engineer.json`, `break-glass.json`) were modified:
    ```
    git diff --quiet tools/profiles/read-only.json tools/profiles/engineer.json tools/profiles/break-glass.json && echo "profile JSONs unchanged ✓"
    ```

    Step 8: Commit `feat(G.2c-02): regenerate tool_classification.json against mcp-confluent@1.3.0`.
  </action>
  <verify>
    <automated>pytest tests/test_profile_gating.py -v && python -c "import json; d=json.load(open('tools/profiles/tool_classification.json')); assert len(d['tools']) == 50, f'expected 50, got {len(d[\"tools\"])}'; assert d['mcp_confluent_version'] == '1.3.0'; assert d['unclassified_policy'] == 'deny'; assert d['tools']['produce-message'] == 'break-glass'; assert d['tools']['consume-messages'] == 'break-glass'; assert d['tools']['list-topics'] == 'read-only'; assert d['tools']['create-topics'] == 'engineer'; assert d['tools']['delete-topics'] == 'break-glass'; assert not any('_' in k for k in d['tools']), 'snake_case key found'; print('OK')"</automated>
  </verify>
  <acceptance_criteria>
    - `python -c "import json; d=json.load(open('tools/profiles/tool_classification.json')); print(len(d['tools']))"` prints `50`
    - `grep -c '"list-topics":' tools/profiles/tool_classification.json` returns 1
    - `grep -c '"create-topics":' tools/profiles/tool_classification.json` returns 1
    - `grep -c '"delete-topics":' tools/profiles/tool_classification.json` returns 1
    - `grep -c '"produce-message": "break-glass"' tools/profiles/tool_classification.json` returns 1
    - `grep -c '"consume-messages": "break-glass"' tools/profiles/tool_classification.json` returns 1
    - `grep -c '"alter-topic-config": "engineer"' tools/profiles/tool_classification.json` returns 1
    - `grep -c '"query-metrics": "read-only"' tools/profiles/tool_classification.json` returns 1
    - `grep '"confluent_kafka_acl_create":' tools/profiles/tool_classification.json` returns no matches
    - `grep '"confluent_kafka_topic_list":' tools/profiles/tool_classification.json` returns no matches
    - `grep '"confluent_peering_' tools/profiles/tool_classification.json` returns no matches
    - `grep '"confluent_transit_gateway_' tools/profiles/tool_classification.json` returns no matches
    - `grep '"confluent_rbac_role_binding_' tools/profiles/tool_classification.json` returns no matches
    - `grep '"confluent_service_account_' tools/profiles/tool_classification.json` returns no matches
    - `grep '"confluent_schema_exporter_' tools/profiles/tool_classification.json` returns no matches
    - `grep '"mcp_confluent_version": "1.3.0"' tools/profiles/tool_classification.json` returns a match
    - `grep '"unclassified_policy": "deny"' tools/profiles/tool_classification.json` returns a match
    - `grep '"tier_rule":' tools/profiles/tool_classification.json` returns a match
    - `pytest tests/test_profile_gating.py -v` exits 0
    - `git diff --quiet tools/apply_engine.py` exits 0 (file unchanged — key-opaque assumption holds)
    - `git diff --quiet tools/profiles/read-only.json tools/profiles/engineer.json tools/profiles/break-glass.json` exits 0
  </acceptance_criteria>
  <done>tool_classification.json is the live-registry-aligned source of truth (50 kebab-case tools, pinned to 1.3.0, sorted, with verb-prefix-rule documentation in tier_rule); parametrized profile-gating test matrix rebuilds itself and passes (50 × 3 = 150 parametrized assertions plus the static cases); apply_engine.py and all three profile JSONs are byte-identical to before this task; one commit recorded.</done>
</task>

<task id="02" type="auto">
  <name>Task 2: Rewrite five hard-coded snake_case tool names in tests/test_apply_engine.py and re-verify all apply-engine tests + break-glass two-step</name>
  <files>tests/test_apply_engine.py</files>
  <read_first>
    - tests/test_apply_engine.py (specifically lines 430-462 — the TestToolClassification class with hard-coded snake_case names)
    - tools/profiles/tool_classification.json (the regenerated kebab-case table from Task 1 — source of valid replacement names)
    - tools/apply_engine.py (verify check_tool_permitted contract is unchanged)
    - .claude/commands/dsp-apply.md (the actual location of the ACTG-03 break-glass two-step confirmation logic — must remain byte-identical)
    - .planning/phases/G.2c-tool-classification-rename/G.2c-CONTEXT.md (D-04: regenerate hard-coded test cases in the same PR)
  </read_first>
  <action>
    Step 1: Confirm the five hard-coded snake_case lines are still present at the expected positions (line numbers may have shifted slightly):
    ```
    grep -n 'check_tool_permitted("read-only", "confluent_' tests/test_apply_engine.py
    grep -n 'check_tool_permitted("engineer", "confluent_' tests/test_apply_engine.py
    grep -n 'check_tool_permitted("break-glass", "confluent_' tests/test_apply_engine.py
    ```
    Expected: 5 total matches (2 read-only, 2 engineer, 1 break-glass).

    Step 2: Apply the following exact replacements in `tests/test_apply_engine.py` using the Edit tool:

    Replacement A (line ~441):
    - Find: `assert check_tool_permitted("read-only", "confluent_kafka_topic_list") is True`
    - Replace: `assert check_tool_permitted("read-only", "list-topics") is True`

    Replacement B (line ~445):
    - Find: `assert check_tool_permitted("read-only", "confluent_kafka_topic_create") is False`
    - Replace: `assert check_tool_permitted("read-only", "create-topics") is False`

    Replacement C (line ~449):
    - Find: `assert check_tool_permitted("engineer", "confluent_kafka_topic_create") is True`
    - Replace: `assert check_tool_permitted("engineer", "create-topics") is True`

    Replacement D (line ~453):
    - Find: `assert check_tool_permitted("engineer", "confluent_kafka_cluster_delete") is False`
    - Replace: `assert check_tool_permitted("engineer", "delete-schema") is False`

    Replacement E (line ~457):
    - Find: `assert check_tool_permitted("break-glass", "confluent_kafka_cluster_delete") is True`
    - Replace: `assert check_tool_permitted("break-glass", "delete-schema") is True`

    Rationale (applies to D and E): Replacement D/E use `delete-schema` rather than `delete-topics` to preserve the original test's cross-resource-family semantic (engineer denied a break-glass-tier delete on schema resources, not just a different verb on topics). `confluent_kafka_cluster_delete` was fictional; the test's original intent was a cross-resource pairing — engineer-tier write on topics (Replacement C: `create-topics`) vs break-glass-tier delete on a *different* resource family. Substituting `delete-topics` would collapse both sides of the matrix onto the `*-topics` family and make future readers assume topics is the only family being tier-tested. `delete-schema` is present in the 1.3.0 registry, classified as break-glass per the D-05 verb-prefix rule, and lives in the Schema Registry resource family — preserving the cross-family intent.

    Step 3: Run the full apply-engine test suite:
    ```
    pytest tests/test_apply_engine.py -v
    ```
    Expected: every test passes, including:
    - `TestToolClassification` (the five updated lines above)
    - `TestCustomerOverlay` (ACTG-04 verification — must be unchanged)

    Note on ACTG-03: The break-glass two-step confirmation flow is implemented in `.claude/commands/dsp-apply.md`, not in pytest. Verify it is unchanged by this PR via `git diff --quiet .claude/commands/dsp-apply.md` (must exit 0).

    Step 4: Run the broader test suite to confirm no collateral damage:
    ```
    pytest tests/ -v 2>&1 | tail -30
    ```
    Expected: no test regressions. Pre-existing failures unrelated to this phase (if any) should remain at the same count.

    Step 5: Confirm only `tests/test_apply_engine.py` was modified in this task:
    ```
    git diff --name-only
    ```
    Expected output: `tests/test_apply_engine.py`. No other files.

    Step 6: Commit `test(G.2c-02): rewrite test_apply_engine TestToolClassification with kebab-case tool names`.
  </action>
  <verify>
    <automated>pytest tests/test_apply_engine.py -v && pytest tests/test_profile_gating.py -v && grep -c "check_tool_permitted.*confluent_kafka" tests/test_apply_engine.py | grep -q "^0$" && echo "no snake_case tool refs remain"</automated>
  </verify>
  <acceptance_criteria>
    - `grep -c 'check_tool_permitted("read-only", "list-topics")' tests/test_apply_engine.py` returns 1
    - `grep -c 'check_tool_permitted("read-only", "create-topics")' tests/test_apply_engine.py` returns 1
    - `grep -c 'check_tool_permitted("engineer", "create-topics")' tests/test_apply_engine.py` returns 1
    - `grep -c 'check_tool_permitted("engineer", "delete-schema")' tests/test_apply_engine.py` returns 1
    - `grep -c 'check_tool_permitted("break-glass", "delete-schema")' tests/test_apply_engine.py` returns 1
    - `grep "check_tool_permitted.*confluent_kafka_topic_list" tests/test_apply_engine.py` returns no matches
    - `grep "check_tool_permitted.*confluent_kafka_topic_create" tests/test_apply_engine.py` returns no matches
    - `grep "check_tool_permitted.*confluent_kafka_cluster_delete" tests/test_apply_engine.py` returns no matches
    - `pytest tests/test_apply_engine.py -v` exits 0
    - `git diff --quiet .claude/commands/dsp-apply.md` exits 0 (break-glass two-step source unchanged — ACTG-03 untouched)
    - `pytest tests/test_apply_engine.py::TestToolClassification::test_break_glass_profile_permits_break_glass_tool -v` exits 0 (break-glass-tier permit logic verified against renamed tools)
    - `pytest tests/test_profile_gating.py -v` exits 0 (verifies ACTG-02 + ACTG-04 untouched)
    - `pytest tests/test_profile_gating.py::TestCustomerDifferential -v` exits 0 (explicit ACTG-04 verification)
    - `git diff --quiet tools/apply_engine.py` exits 0
    - `git diff --quiet tools/profiles/read-only.json tools/profiles/engineer.json tools/profiles/break-glass.json` exits 0
  </acceptance_criteria>
  <done>Five snake_case tool-name strings replaced with their kebab-case equivalents in test_apply_engine.py; full apply-engine test suite passes; ACTG-03 break-glass two-step verified untouched via byte-identical .claude/commands/dsp-apply.md (the two-step logic lives in the slash command, not pytest); ACTG-04 customer differential gating verified unchanged via TestCustomerDifferential; no other files modified; one commit recorded.</done>
</task>

</tasks>

<verification>
- `python -c "import json; d=json.load(open('tools/profiles/tool_classification.json')); assert len(d['tools']) == 50 and d['mcp_confluent_version']=='1.3.0' and d['unclassified_policy']=='deny' and not any('_' in k for k in d['tools'])"` exits 0
- `pytest tests/test_profile_gating.py -v` exits 0 (ACTG-01, ACTG-02 confirmed by parametrized matrix self-rebuild over 50 tools × 3 profiles)
- `pytest tests/test_apply_engine.py -v` exits 0 (TestToolClassification updated; TestCustomerOverlay / ACTG-04 unchanged)
- ACTG-03 verified by `git diff --quiet .claude/commands/dsp-apply.md` (exit 0) AND `pytest tests/test_apply_engine.py::TestToolClassification::test_break_glass_profile_permits_break_glass_tool` (exit 0)
- `pytest tests/test_apply_executor.py -v` exits 0 (verifies G.1 executor still works; apply_engine.py is byte-identical so this is a smoke check, not a functional one)
- `git diff --quiet tools/apply_engine.py` exits 0 (key-opaque assumption preserved)
- `git diff --quiet tools/profiles/read-only.json tools/profiles/engineer.json tools/profiles/break-glass.json` exits 0 (profile files reference `allowed_operations` artifact IDs, not tool names, per CONTEXT.md `<domain>`)
- `git log --oneline G.2c-02 | wc -l` returns at least 2 (regenerate commit + test-update commit)
</verification>

<success_criteria>
1. `tool_classification.json` is fully aligned with the live `@confluentinc/mcp-confluent@1.3.0` registry: 50 kebab-case keys, version pinned, sorted, documented, no fictional entries.
2. ACTG-01 is now genuinely satisfied — the classification table maps onto the real tool surface, not a training-data hallucination.
3. ACTG-02 is verified by the test_profile_gating.py parametrized matrix automatically rebuilding from the new keys and passing 50×3 forbidden-tool assertions.
4. ACTG-03 verified untouched via byte-identical .claude/commands/dsp-apply.md (the two-step logic lives in the slash command, not pytest) plus the apply-engine break-glass-tier permit test.
5. ACTG-04 (customer differential gating) is verified untouched via TestCustomerDifferential passing unchanged.
6. `tools/apply_engine.py` is unchanged — proving the rename is purely a data fix and the runtime stays key-opaque per D-06.
7. The diff is small and reviewable: one JSON file rewrite, one test file with 5 string substitutions. No engine, no profile, no production-code changes.
</success_criteria>

<output>
After completion, create `.planning/phases/G.2c-tool-classification-rename/G.2c-02-SUMMARY.md` per the standard summary template.
</output>
</content>
</invoke>