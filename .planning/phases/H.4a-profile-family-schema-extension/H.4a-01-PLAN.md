---
phase: H.4a-profile-family-schema-extension
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tools/apply_engine.py
  - tools/profiles/read-only.json
  - tools/profiles/engineer.json
  - tools/profiles/break-glass.json
  - tests/test_profile_gating.py
  - tests/snapshots/h4a_operator_permits.json
  - tests/fixtures/profiles/test-dev-fixture.json
autonomous: true
requirements: [PROFAM-01, PROFAM-02]
requirements_addressed: [PROFAM-01]

must_haves:
  truths:
    - "`tools/profiles/read-only.json`, `engineer.json`, `break-glass.json` each contain literal `\"family\": \"operator\"` field, placed after `description` and before `allowed_operations`"
    - "`tools/apply_engine.py` defines `VALID_FAMILIES = {\"operator\", \"developer\"}` constant"
    - "`load_profile()` returns a dict whose `family` key is one of `\"operator\"` or `\"developer\"` after defaulting; absent `family` field defaults to `\"operator\"`; unknown family value raises ValueError"
    - "`load_profile()` validates per-family invariants: operator profiles MUST have `allowed_operations` list; developer profiles MUST have `tool_overrides` dict AND `skill_blocklist` list (may be empty)"
    - "`check_tool_permitted()` signature unchanged: `(profile_name, tool_name, customer=None)` — no call-site edits required anywhere in repo"
    - "`check_tool_permitted()` branches on family: operator → existing PROFILE_TIER_ORDER cascade (byte-identical to v1.0 Phase 3c); developer → reads `tool_overrides` map from profile JSON, permits if tool in map, denies otherwise"
    - "`tests/test_profile_gating.py` gains three new test groups: (1) family round-trip (3 functions); (2) operator-branch byte-compat via snapshot; (3) developer-branch dispatch via fixture"
    - "`tests/snapshots/h4a_operator_permits.json` exists and captures every (operator-profile × every-tool-in-classification) → permit decision; matches live behavior after the H.4a refactor"
    - "`tests/fixtures/profiles/test-dev-fixture.json` exists with the developer-family shape (family=developer, tool_overrides={produce-message: developer-sandbox}, skill_blocklist=[], no allowed_operations)"
    - "`pytest tests/test_profile_gating.py -v` exits 0 — all original tests pass + 5 new tests pass (3 family round-trip + 1 operator-snapshot + 1 developer-branch)"
    - "All other existing test suites (golden harnesses, eval harnesses, etc.) pass byte-identical to pre-H.4a baseline — no spillover regressions"
    - "Operator-profile load behavior is byte-identical: `load_profile('engineer')` returns the same dict as before EXCEPT for the new `family` key"
    - "No new third-party dependency added (no jsonschema, no pydantic — validation stays pure-Python per CONTEXT D-07)"
    - "No changes to `tools/profiles/tool_classification.json` (G.2c territory) or `tools/regenerate_tool_classification.py`"
    - "No changes to canon/ or scenario/ files (H.4b/H.4c territory)"
  artifacts:
    - path: "tools/apply_engine.py"
      provides: "VALID_FAMILIES constant + family-aware load_profile() + family-branched check_tool_permitted() + per-family invariant validation"
      contains:
        - "VALID_FAMILIES"
        - "operator"
        - "developer"
        - "tool_overrides"
        - "family"
    - path: "tools/profiles/read-only.json"
      provides: "Read-only operator profile with explicit family field"
      contains:
        - "\"family\": \"operator\""
        - "\"name\": \"read-only\""
    - path: "tools/profiles/engineer.json"
      provides: "Engineer operator profile with explicit family field"
      contains:
        - "\"family\": \"operator\""
        - "\"name\": \"engineer\""
    - path: "tools/profiles/break-glass.json"
      provides: "Break-glass operator profile with explicit family field"
      contains:
        - "\"family\": \"operator\""
        - "\"name\": \"break-glass\""
    - path: "tests/test_profile_gating.py"
      provides: "Family round-trip tests, operator-branch byte-compat snapshot test, developer-branch dispatch test"
      contains:
        - "test_load_profile_reads_family"
        - "test_load_profile_defaults_family_to_operator_when_absent"
        - "test_load_profile_rejects_unknown_family"
        - "test_check_tool_permitted_operator_branch_byte_identical"
        - "test_check_tool_permitted_developer_branch_reads_tool_overrides"
    - path: "tests/snapshots/h4a_operator_permits.json"
      provides: "Snapshot of all (operator-profile, tool) permit decisions for the regression-guard test"
      contains:
        - "read-only"
        - "engineer"
        - "break-glass"
    - path: "tests/fixtures/profiles/test-dev-fixture.json"
      provides: "Test-only developer profile for the developer-branch dispatch test"
      contains:
        - "\"family\": \"developer\""
        - "\"tool_overrides\""
        - "produce-message"
  key_links:
    - from: "tools/apply_engine.py:check_tool_permitted"
      to: "tools/profiles/*.json:family"
      via: "load_profile() reads family; check_tool_permitted() branches on it"
      pattern: "family"
    - from: "tests/test_profile_gating.py"
      to: "tests/snapshots/h4a_operator_permits.json"
      via: "test_check_tool_permitted_operator_branch_byte_identical loads snapshot and asserts current behavior matches"
      pattern: "h4a_operator_permits.json"
    - from: "tests/test_profile_gating.py"
      to: "tests/fixtures/profiles/test-dev-fixture.json"
      via: "test_check_tool_permitted_developer_branch_reads_tool_overrides loads the fixture and asserts dispatch behavior"
      pattern: "test-dev-fixture.json"
---

<objective>
Land the family-field schema extension + engine-branch groundwork so H.4b can author the first developer-family profile (sandbox.json) without further engine surgery. Zero behavior change for existing operator profiles — proven by an exhaustive snapshot test of every (profile, tool) → permit decision. Single PLAN.md, single wave, autonomous.

After this plan: PROFAM-01 is fully satisfied (family field added to every profile, branching wired, defaults documented, validation in place). PROFAM-02 is half satisfied (the developer-branch dispatch logic is proven by a test fixture; the negative-space proof that operator profiles CANNOT invoke developer-tier tools requires a real developer profile, which H.4b lands). The other 3 ROADMAP success criteria are met: criterion #1 (family field on every profile + load_profile parses + check_tool_permitted branches — verified by tests), #3 (JSON Schema validation — implemented in Python per CONTEXT D-07), #4 (all existing operator-profile tests still pass — verified by the snapshot + full pytest run).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/H.4a-profile-family-schema-extension/H.4a-CONTEXT.md
@.planning/phases/03C-act-rail-profile-gating/03C-CONTEXT.md
@tools/apply_engine.py
@tools/profiles/read-only.json
@tools/profiles/engineer.json
@tools/profiles/break-glass.json
@tools/profiles/tool_classification.json
@tests/test_profile_gating.py

<interfaces>
<!-- Operator profile shape (post-H.4a) -->
{
  "name": "engineer",
  "description": "...",
  "family": "operator",
  "allowed_operations": [...]
}

<!-- Developer profile shape (H.4b will author the first real one; H.4a fixture proves dispatch) -->
{
  "name": "test-dev-fixture",
  "description": "Test fixture — do not load in production",
  "family": "developer",
  "skill_blocklist": [],
  "tool_overrides": {"produce-message": "developer-sandbox"}
}

<!-- VALID_FAMILIES constant -->
VALID_FAMILIES = {"operator", "developer"}

<!-- load_profile() return shape — operator -->
{"name": "engineer", "description": "...", "family": "operator", "allowed_operations": [...]}

<!-- load_profile() return shape — developer -->
{"name": "test-dev-fixture", "description": "...", "family": "developer", "skill_blocklist": [], "tool_overrides": {...}}

<!-- check_tool_permitted() branch logic -->
def check_tool_permitted(profile_name, tool_name, customer=None):
    profile = load_profile(profile_name, customer=customer)
    family = profile["family"]  # always present after H.4a load
    if family == "operator":
        # Existing v1.0 Phase 3c logic — PROFILE_TIER_ORDER cascade
        classification = load_tool_classification()
        tools = classification.get("tools", {})
        if tool_name not in tools:
            return False
        required_tier = tools[tool_name]
        profile_idx = PROFILE_TIER_ORDER.index(profile_name)
        required_idx = PROFILE_TIER_ORDER.index(required_tier)
        return profile_idx >= required_idx
    elif family == "developer":
        overrides = profile.get("tool_overrides", {})
        return tool_name in overrides  # fail-closed: tools not in overrides are denied
    else:
        raise ValueError(f"Unknown profile family: {family!r}")
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add VALID_FAMILIES constant and family validation to tools/apply_engine.py, update load_profile() to parse family + apply back-compat default + validate per-family invariants</name>
  <files>
    - tools/apply_engine.py
  </files>
  <read_first>
    - tools/apply_engine.py (current — lines 1–125 cover VALID_PROFILES, PROFILE_TIER_ORDER, check_tool_permitted, load_profile)
    - .planning/phases/H.4a-profile-family-schema-extension/H.4a-CONTEXT.md (D-01 through D-08 — the validation contract)
  </read_first>
  <action>
    Edit `tools/apply_engine.py`. Make these targeted changes only — do NOT refactor unrelated code:

    1. Add new constant near `VALID_PROFILES` (around line 36–39):
       ```python
       VALID_FAMILIES = {"operator", "developer"}
       ```

    2. Add a module-level docstring or comment block near VALID_FAMILIES describing the family contract (D-08):
       ```python
       # Profile families (H.4a):
       #   - "operator" — tier cascade (read-only < engineer < break-glass) via PROFILE_TIER_ORDER.
       #                  Profile JSON MUST have "allowed_operations" list. Tool permission via
       #                  check_tool_permitted() consults tool_classification.json (G.2c).
       #   - "developer" — per-profile tool_overrides map. Profile JSON MUST have
       #                   "tool_overrides" dict AND "skill_blocklist" list (may be empty).
       #                   NO allowed_operations field (operator-only). Authored in H.4b.
       # Unknown family value → ValueError. Missing family field → defaults to "operator" for
       # back-compat with pre-H.4a external profiles; log the default-application.
       ```

    3. Modify `load_profile()` (current lines 88–124) to:
       - After loading `profile_data` from JSON (line 123), call a new private helper `_normalize_and_validate_profile(profile_data, profile_name)` that:
         a. If `family` key absent → inject `family: "operator"` and emit a one-line stderr note: `f"[apply_engine] profile {profile_name!r} missing 'family' field; defaulting to 'operator' (pre-H.4a shape)"`. Use `sys.stderr.write()` (no logging framework).
         b. If `family` key present but not in `VALID_FAMILIES` → raise ValueError with shape: `f"Profile {profile_name!r} has unknown family {profile_data['family']!r} — must be one of {sorted(VALID_FAMILIES)}"`.
         c. If `family == "operator"`: require `allowed_operations` key present and is a list. Raise ValueError otherwise: `f"Operator profile {profile_name!r} is missing required 'allowed_operations' list"`.
         d. If `family == "developer"`: require BOTH `tool_overrides` key present (dict) AND `skill_blocklist` key present (list, may be empty). Forbid `allowed_operations` key (operator-only). Raise ValueError on any violation with clear shape.
         e. Return the (possibly-mutated) profile_data dict.
       - Replace the final `return profile_data` (current line 124) with `return _normalize_and_validate_profile(profile_data, profile_name)`.
       - Apply the same normalization to the customer-overlay branch (current lines 116–119): `if customer_profile.exists(): return _normalize_and_validate_profile(json.loads(customer_profile.read_text()), profile_name)`.

    4. Define `_normalize_and_validate_profile()` as a module-level private function placed immediately before `load_profile()`. Include a one-line docstring.

    5. Add `import sys` to the imports at the top of the file if not already present.

    Do NOT yet modify `check_tool_permitted()` — Task 2 handles that. This task is a strict superset of the v1.0 load_profile() contract (every operator profile still loads identically, plus the new family field is now present in the returned dict).
  </action>
  <acceptance_criteria>
    - `grep -c "VALID_FAMILIES = " tools/apply_engine.py` returns exactly 1.
    - `grep -c "operator" tools/apply_engine.py` returns ≥ 3 (constant + docstring + branch handling).
    - `grep -c "developer" tools/apply_engine.py` returns ≥ 3 (constant + docstring + branch handling).
    - `grep -c "_normalize_and_validate_profile" tools/apply_engine.py` returns exactly 4 (1 def + 3 callsites: base path + customer overlay path + the rewritten final return).
    - `grep -c "import sys" tools/apply_engine.py` returns ≥ 1.
    - Python sanity: `python3 -c "from tools.apply_engine import load_profile, VALID_FAMILIES; assert VALID_FAMILIES == {'operator', 'developer'}; p = load_profile('engineer'); assert p['family'] == 'operator'"` exits 0 — works AFTER Task 2 commits the JSON updates, OR before if `load_profile('engineer')` is called on a temporarily-modified copy. (Honor task ordering — this acceptance check runs after Task 2.)
    - `pytest tests/test_profile_gating.py -v` does NOT fail any existing tests (run before Task 2 — should pass since load_profile() still returns dicts with everything previously expected, plus the new family key which existing tests don't assert against).
  </acceptance_criteria>
</task>

<task type="auto">
  <name>Task 2: Add family: "operator" field to read-only.json, engineer.json, break-glass.json (place after description, before allowed_operations)</name>
  <files>
    - tools/profiles/read-only.json
    - tools/profiles/engineer.json
    - tools/profiles/break-glass.json
  </files>
  <read_first>
    - tools/profiles/read-only.json
    - tools/profiles/engineer.json
    - tools/profiles/break-glass.json
    - .planning/phases/H.4a-profile-family-schema-extension/H.4a-CONTEXT.md (D-01 placement rule)
  </read_first>
  <action>
    Edit each of the three profile JSON files. Add the `family` field as a string with value `"operator"`. Placement: immediately after the `description` field and immediately before the `allowed_operations` field.

    **For tools/profiles/read-only.json** — current shape ends with `"allowed_operations": []`. Edit to:
    ```json
    {
      "name": "read-only",
      "description": "Plan and inspect only. No apply operations.",
      "family": "operator",
      "allowed_operations": []
    }
    ```

    **For tools/profiles/engineer.json** — current shape has the engineer entries. Edit to:
    ```json
    {
      "name": "engineer",
      "description": "Plan + apply standard non-destructive modules (topics, schemas, RBAC, Flink) and Confluent Cloud starter-kit scenarios that compose those modules with DR cluster-linking.",
      "family": "operator",
      "allowed_operations": [
        "module/topic",
        "module/flink",
        "role/cp_schema",
        "role/cp_rbac",
        "role/cp_connect",
        "scenario/cc-aws",
        "scenario/cc-azure",
        "scenario/cc-gcp"
      ]
    }
    ```

    **For tools/profiles/break-glass.json** — current shape has break-glass entries. Edit to:
    ```json
    {
      "name": "break-glass",
      "description": "All operations including destructive (DR failover, cluster reconfig, deletion).",
      "family": "operator",
      "allowed_operations": [
        "module/topic",
        "module/flink",
        "role/cp_schema",
        "role/cp_rbac",
        "role/cp_connect",
        "script/fsi-dr",
        "scenario/cc-aws",
        "scenario/cc-azure",
        "scenario/cc-gcp"
      ]
    }
    ```

    Preserve existing 2-space indentation. Do NOT modify `tool_classification.json` (different schema — that file is the G.2c tool tier mapping, not a profile).
  </action>
  <acceptance_criteria>
    - `python3 -c "import json; [print(p['name'], '→', p['family']) for p in [json.loads(open(f).read()) for f in ['tools/profiles/read-only.json', 'tools/profiles/engineer.json', 'tools/profiles/break-glass.json']]]"` prints `read-only → operator`, `engineer → operator`, `break-glass → operator`.
    - `grep -c '"family": "operator"' tools/profiles/read-only.json` returns 1.
    - `grep -c '"family": "operator"' tools/profiles/engineer.json` returns 1.
    - `grep -c '"family": "operator"' tools/profiles/break-glass.json` returns 1.
    - `python3 -c "import json; assert json.loads(open('tools/profiles/tool_classification.json').read()).get('family') is None, 'tool_classification.json should NOT have family field — it is not a profile'"` exits 0.
    - All three files still parse as valid JSON: `for f in tools/profiles/read-only.json tools/profiles/engineer.json tools/profiles/break-glass.json; do python3 -c "import json; json.load(open('$f'))"; done` — no exceptions.
    - `python3 -c "from tools.apply_engine import load_profile; p = load_profile('engineer'); assert p['family'] == 'operator'; assert 'allowed_operations' in p"` exits 0 (verifies Task 1 + Task 2 integrate correctly).
  </acceptance_criteria>
</task>

<task type="auto">
  <name>Task 3: Update check_tool_permitted() in tools/apply_engine.py to branch on family — operator path preserves existing logic byte-identical, developer path reads tool_overrides map from profile JSON</name>
  <files>
    - tools/apply_engine.py
  </files>
  <read_first>
    - tools/apply_engine.py (current check_tool_permitted at lines 58–81)
    - .planning/phases/H.4a-profile-family-schema-extension/H.4a-CONTEXT.md (D-04, D-05, D-06)
  </read_first>
  <action>
    Modify `check_tool_permitted()` (current lines 58–81). Keep the function signature byte-identical: `def check_tool_permitted(profile_name: str, tool_name: str, customer: Optional[str] = None) -> bool:`.

    Replace the function body with the family-branched logic:

    ```python
    def check_tool_permitted(profile_name: str, tool_name: str, customer: Optional[str] = None) -> bool:
        """Check whether profile_name permits invoking tool_name.

        Branches on profile family (H.4a):
          - operator family: uses tier hierarchy (read-only < engineer < break-glass) +
            tool_classification.json tier map. Identical to v1.0 Phase 3c behavior.
          - developer family: reads `tool_overrides` map from the profile JSON.
            Tool is permitted if present in the map; denied otherwise (fail-closed).

        Returns False (fail-closed) when:
          - tool_name is not in classification table (operator branch)
          - tool_name is not in tool_overrides map (developer branch)
          - profile_name is not in VALID_PROFILES (caller error — raises via load_profile)

        Args:
            profile_name: One of VALID_PROFILES.
            tool_name:    Exact mcp-confluent tool name.
            customer:     Optional customer overlay name (keyword-only — see load_profile).

        Returns:
            True if permitted; False otherwise (fail-closed).

        Raises:
            ValueError: If profile family is unknown (defensive — load_profile validates first).
        """
        profile = load_profile(profile_name, customer=customer)
        family = profile["family"]  # always present after H.4a load (defaulted or explicit)

        if family == "operator":
            # v1.0 Phase 3c branch — byte-identical to pre-H.4a behavior.
            classification = load_tool_classification()
            tools = classification.get("tools", {})

            if tool_name not in tools:
                return False

            required_tier = tools[tool_name]
            profile_idx = PROFILE_TIER_ORDER.index(profile_name)
            required_idx = PROFILE_TIER_ORDER.index(required_tier)
            return profile_idx >= required_idx

        elif family == "developer":
            # H.4a developer-branch — per-profile tool_overrides dispatch.
            # Tools listed in the map are permitted; anything else is denied (fail-closed).
            # The map's value-strings (developer-sandbox, developer-restricted, etc.) are
            # informational at H.4a; H.4b's developer-sandbox profile pins the value set.
            overrides = profile.get("tool_overrides", {})
            return tool_name in overrides

        else:
            # Defensive — load_profile validates family before we get here, but if a
            # third party calls load_profile with a malformed profile and the validation
            # is bypassed, raise rather than silently permit.
            raise ValueError(f"Unknown profile family {family!r} for profile {profile_name!r}")
    ```

    Notes:
    - The function now consults `load_profile()` once at the top. v1.0 callers passed `profile_name` and `tool_name` without ever loading the profile — H.4a needs the profile to know the family. The per-call overhead is one JSON read; acceptable for the small profile files.
    - `PROFILE_TIER_ORDER` only contains operator-family tier names (`read-only`, `engineer`, `break-glass`). If a developer profile somehow reaches the operator branch (it shouldn't), `PROFILE_TIER_ORDER.index(profile_name)` will raise ValueError — also fail-closed.
  </action>
  <acceptance_criteria>
    - `grep -c "family == \"operator\"" tools/apply_engine.py` returns ≥ 1.
    - `grep -c "family == \"developer\"" tools/apply_engine.py` returns ≥ 1.
    - `grep -c "tool_overrides" tools/apply_engine.py` returns ≥ 2 (docstring + map read).
    - `python3 -c "from tools.apply_engine import check_tool_permitted; assert check_tool_permitted('engineer', 'list-environments') == True; assert check_tool_permitted('read-only', 'delete-topics') == False"` exits 0 (operator branch byte-compat sanity).
    - The function signature is unchanged — `python3 -c "import inspect; from tools.apply_engine import check_tool_permitted; sig = inspect.signature(check_tool_permitted); assert list(sig.parameters.keys()) == ['profile_name', 'tool_name', 'customer'], f'unexpected signature: {sig}'"` exits 0.
    - `pytest tests/test_profile_gating.py -v` passes all existing tests (the operator branch is byte-identical).
  </acceptance_criteria>
</task>

<task type="auto">
  <name>Task 4: Create tests/fixtures/profiles/test-dev-fixture.json and tests/snapshots/h4a_operator_permits.json — add three new test groups to tests/test_profile_gating.py covering family round-trip, operator-snapshot byte-compat, and developer-branch dispatch</name>
  <files>
    - tests/fixtures/profiles/test-dev-fixture.json
    - tests/snapshots/h4a_operator_permits.json
    - tests/test_profile_gating.py
  </files>
  <read_first>
    - tests/test_profile_gating.py (existing test patterns — parametrize shape, fixture loading)
    - tools/apply_engine.py (post-Task 3 — check_tool_permitted contract)
    - tools/profiles/tool_classification.json (tool list for the snapshot)
    - .planning/phases/H.4a-profile-family-schema-extension/H.4a-CONTEXT.md (D-09 test surface)
  </read_first>
  <action>
    **Sub-task 4a — Create the fixture profile:**

    Create `tests/fixtures/profiles/test-dev-fixture.json`:
    ```json
    {
      "name": "test-dev-fixture",
      "description": "Test fixture — do not load in production. Used by tests/test_profile_gating.py to prove the developer-family branch dispatches against tool_overrides.",
      "family": "developer",
      "skill_blocklist": [],
      "tool_overrides": {
        "produce-message": "developer-sandbox",
        "consume-messages": "developer-sandbox",
        "create-topics": "developer-sandbox"
      }
    }
    ```

    **Sub-task 4b — Generate the operator-permits snapshot:**

    Run this one-liner to regenerate the snapshot from live behavior (it must match post-Task 3 reality):
    ```bash
    mkdir -p tests/snapshots
    python3 -c "
    import json
    from tools.apply_engine import check_tool_permitted, VALID_PROFILES, load_tool_classification
    tc = load_tool_classification()
    operator_profiles = ['read-only', 'engineer', 'break-glass']
    snapshot = {p: {t: check_tool_permitted(p, t) for t in sorted(tc['tools'])} for p in operator_profiles}
    print(json.dumps(snapshot, indent=2))
    " > tests/snapshots/h4a_operator_permits.json
    ```

    The resulting file is the baseline against which Test 4 asserts.

    **Sub-task 4c — Append three new test groups to tests/test_profile_gating.py:**

    Add these tests at the bottom of the file (do NOT modify any existing tests):

    ```python
    # ---------------------------------------------------------------------------
    # H.4a — Family field round-trip + branch dispatch tests
    # ---------------------------------------------------------------------------

    import json
    import pytest
    from pathlib import Path
    from tools.apply_engine import (
        load_profile,
        check_tool_permitted,
        VALID_FAMILIES,
        PROFILES_DIR,
    )

    FIXTURE_DIR = Path(__file__).parent / "fixtures" / "profiles"
    SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


    class TestFamilyRoundTrip:
        """H.4a D-09 test group 1 — family field round-trip through load_profile()."""

        def test_load_profile_reads_family_for_all_operator_profiles(self):
            """Every committed operator profile loads with family == 'operator'."""
            for name in ("read-only", "engineer", "break-glass"):
                p = load_profile(name)
                assert p["family"] == "operator", (
                    f"Profile {name!r} expected family=operator, got {p.get('family')!r}"
                )

        def test_load_profile_defaults_family_to_operator_when_absent(self, tmp_path, monkeypatch):
            """A profile JSON missing the family field defaults to operator (back-compat)."""
            legacy_profile = {
                "name": "engineer",  # name MUST be a VALID_PROFILES entry for load to proceed
                "description": "Pre-H.4a shape",
                "allowed_operations": []
            }
            tmp_profiles = tmp_path / "profiles"
            tmp_profiles.mkdir()
            (tmp_profiles / "engineer.json").write_text(json.dumps(legacy_profile))
            monkeypatch.setattr("tools.apply_engine.PROFILES_DIR", tmp_profiles)
            p = load_profile("engineer")
            assert p["family"] == "operator", (
                f"Absent family field should default to 'operator', got {p.get('family')!r}"
            )

        def test_load_profile_rejects_unknown_family(self, tmp_path, monkeypatch):
            """A profile with family not in VALID_FAMILIES raises ValueError."""
            bad_profile = {
                "name": "engineer",
                "description": "Bogus family value",
                "family": "platform",  # not in VALID_FAMILIES
                "allowed_operations": []
            }
            tmp_profiles = tmp_path / "profiles"
            tmp_profiles.mkdir()
            (tmp_profiles / "engineer.json").write_text(json.dumps(bad_profile))
            monkeypatch.setattr("tools.apply_engine.PROFILES_DIR", tmp_profiles)
            with pytest.raises(ValueError, match="unknown family"):
                load_profile("engineer")


    class TestOperatorBranchByteCompat:
        """H.4a D-09 test group 2 — operator-branch behavior byte-identical to pre-H.4a.

        The snapshot at tests/snapshots/h4a_operator_permits.json captures every
        (operator-profile × tool) permit decision after the H.4a refactor. Any future
        change that shifts the permit set will fail this test, forcing the snapshot
        to be regenerated in a separate visible-diff PR.

        Regenerate via the one-liner in tests/snapshots/h4a_operator_permits.json's
        sibling docstring (this docstring): see H.4a-01-PLAN.md Task 4 sub-task 4b.
        """

        def test_check_tool_permitted_operator_branch_byte_identical(self):
            snapshot_path = SNAPSHOT_DIR / "h4a_operator_permits.json"
            assert snapshot_path.exists(), (
                f"Snapshot missing — regenerate via the one-liner in H.4a-01-PLAN Task 4b"
            )
            snapshot = json.loads(snapshot_path.read_text())
            for profile_name, tool_decisions in snapshot.items():
                for tool_name, expected_permit in tool_decisions.items():
                    actual = check_tool_permitted(profile_name, tool_name)
                    assert actual == expected_permit, (
                        f"Permit drift: profile={profile_name!r} tool={tool_name!r} "
                        f"snapshot={expected_permit} live={actual}"
                    )


    class TestDeveloperBranchDispatch:
        """H.4a D-09 test group 3 — developer-branch dispatches against tool_overrides."""

        def test_check_tool_permitted_developer_branch_reads_tool_overrides(self, monkeypatch):
            """Developer profile permits only tools listed in tool_overrides; denies all others.

            Note: We monkeypatch PROFILES_DIR and add the dev fixture name to VALID_PROFILES
            for the duration of this test. Production code never sees test-dev-fixture.
            """
            from tools import apply_engine
            monkeypatch.setattr(apply_engine, "PROFILES_DIR", FIXTURE_DIR)
            monkeypatch.setattr(apply_engine, "VALID_PROFILES", apply_engine.VALID_PROFILES | {"test-dev-fixture"})
            # Permit: in tool_overrides
            assert check_tool_permitted("test-dev-fixture", "produce-message") is True
            assert check_tool_permitted("test-dev-fixture", "consume-messages") is True
            assert check_tool_permitted("test-dev-fixture", "create-topics") is True
            # Deny: NOT in tool_overrides (would be permitted at engineer-tier under operator branch)
            assert check_tool_permitted("test-dev-fixture", "list-environments") is False
            assert check_tool_permitted("test-dev-fixture", "describe-cluster") is False
            # Deny: unknown tool name (fail-closed)
            assert check_tool_permitted("test-dev-fixture", "totally-fake-tool-name-xyz") is False


    class TestPerFamilyInvariants:
        """H.4a D-07 — load_profile validates per-family invariants."""

        def test_operator_profile_missing_allowed_operations_raises(self, tmp_path, monkeypatch):
            bad_profile = {
                "name": "engineer",
                "description": "Operator missing required field",
                "family": "operator"
                # no allowed_operations
            }
            tmp_profiles = tmp_path / "profiles"
            tmp_profiles.mkdir()
            (tmp_profiles / "engineer.json").write_text(json.dumps(bad_profile))
            monkeypatch.setattr("tools.apply_engine.PROFILES_DIR", tmp_profiles)
            with pytest.raises(ValueError, match="allowed_operations"):
                load_profile("engineer")

        def test_developer_profile_missing_tool_overrides_raises(self, tmp_path, monkeypatch):
            from tools import apply_engine
            bad_profile = {
                "name": "test-dev-fixture",
                "description": "Developer missing required field",
                "family": "developer",
                "skill_blocklist": []
                # no tool_overrides
            }
            tmp_profiles = tmp_path / "profiles"
            tmp_profiles.mkdir()
            (tmp_profiles / "test-dev-fixture.json").write_text(json.dumps(bad_profile))
            monkeypatch.setattr(apply_engine, "PROFILES_DIR", tmp_profiles)
            monkeypatch.setattr(apply_engine, "VALID_PROFILES", apply_engine.VALID_PROFILES | {"test-dev-fixture"})
            with pytest.raises(ValueError, match="tool_overrides"):
                load_profile("test-dev-fixture")
    ```

    **Important imports note:** The existing `tests/test_profile_gating.py` may already import some of these names; add only what's missing. Read the existing imports first, then add `VALID_FAMILIES` and `PROFILES_DIR` to the import line if `from tools.apply_engine import ...` exists, or add a new import line below.
  </action>
  <acceptance_criteria>
    - `tests/fixtures/profiles/test-dev-fixture.json` exists and parses as valid JSON with `family == "developer"`.
    - `tests/snapshots/h4a_operator_permits.json` exists, parses as valid JSON, and contains keys `read-only`, `engineer`, `break-glass`.
    - `grep -c "class TestFamilyRoundTrip" tests/test_profile_gating.py` returns exactly 1.
    - `grep -c "class TestOperatorBranchByteCompat" tests/test_profile_gating.py` returns exactly 1.
    - `grep -c "class TestDeveloperBranchDispatch" tests/test_profile_gating.py` returns exactly 1.
    - `grep -c "class TestPerFamilyInvariants" tests/test_profile_gating.py` returns exactly 1.
    - `pytest tests/test_profile_gating.py -v` exits 0 — all existing tests pass + all new tests pass.
    - `pytest tests/test_profile_gating.py::TestFamilyRoundTrip -v` exits 0.
    - `pytest tests/test_profile_gating.py::TestOperatorBranchByteCompat -v` exits 0.
    - `pytest tests/test_profile_gating.py::TestDeveloperBranchDispatch -v` exits 0.
    - `pytest tests/test_profile_gating.py::TestPerFamilyInvariants -v` exits 0.
  </acceptance_criteria>
</task>

<task type="auto">
  <name>Task 5: Run full regression — pytest across all test suites; confirm no cross-suite breakage from the apply_engine.py refactor; write SUMMARY.md</name>
  <files>
    - .planning/phases/H.4a-profile-family-schema-extension/H.4a-01-SUMMARY.md
  </files>
  <read_first>
    - tools/apply_engine.py (post-Task 3 — the modified file)
    - tests/test_profile_gating.py (post-Task 4 — full test surface)
    - .planning/phases/H.4a-profile-family-schema-extension/H.4a-CONTEXT.md (validation gate criteria)
    - tests/ (top-level — enumerate all test files for regression run)
  </read_first>
  <action>
    Run the full test surface and confirm zero regressions. Cross-suite verification protects against the apply_engine refactor inadvertently affecting downstream consumers (eval harnesses, golden cases, etc.).

    Commands to run, in order:
    1. `pytest tests/test_profile_gating.py -v` — Confirms all family-related tests pass.
    2. `pytest tests/ -v --tb=short` — Full test suite. Capture exit code; any non-zero is a regression.
    3. `pytest tests/golden/ -v` — Golden harnesses (ask / review / act). Must pass byte-identical.
    4. `pytest tests/evals/run_skill_evals.py -v` — H.2 unified eval harness. Must pass.

    If any non-pytest-profile-gating suite fails, diagnose and decide:
    - **If the failure is caused by a real H.4a-introduced regression** (e.g., a test that loads a profile and asserts on dict shape — now finds a new family key): fix the test by updating its expected-shape, then re-run.
    - **If the failure is unrelated to H.4a** (e.g., a flaky test that already failed pre-H.4a): note it in SUMMARY.md as a pre-existing condition, don't fix in this plan.

    Write `.planning/phases/H.4a-profile-family-schema-extension/H.4a-01-SUMMARY.md`:

    ```markdown
    # H.4a-01 Summary

    **Plan:** H.4a-01 — Profile-family schema extension
    **Status:** Complete
    **Date:** 2026-05-17

    ## What landed
    - `VALID_FAMILIES = {"operator", "developer"}` constant in `tools/apply_engine.py`
    - `load_profile()` now reads `family` field, defaults to operator when absent, raises ValueError on unknown values, validates per-family invariants
    - `check_tool_permitted()` branches on family: operator → existing PROFILE_TIER_ORDER cascade (byte-identical); developer → `tool_overrides` map dispatch (fail-closed)
    - Three operator profile JSONs gain explicit `"family": "operator"` field
    - 4 new test classes: TestFamilyRoundTrip (3), TestOperatorBranchByteCompat (1, snapshot-based), TestDeveloperBranchDispatch (1, fixture-based), TestPerFamilyInvariants (2)
    - `tests/fixtures/profiles/test-dev-fixture.json` — first developer-family fixture (proves dispatch)
    - `tests/snapshots/h4a_operator_permits.json` — baseline snapshot of all (operator-profile × tool) permits for regression guard

    ## Requirements
    - PROFAM-01: ✓ Fully satisfied (family field + branching + defaults + validation + unit tests for both branches)
    - PROFAM-02: ⚪ Half satisfied — developer-branch dispatch proven via fixture; full negative-space proof (operator profiles cannot invoke developer-family tools and vice versa with REAL profiles) requires H.4b's developer-sandbox profile + H.4b's negative-space test matrix

    ## ROADMAP success criteria
    1. ✓ Every existing profile has family="operator"; absence defaults to operator in load_profile (verified by TestFamilyRoundTrip)
    2. ✓ check_tool_permitted branches on family — operator uses tier cascade, developer reads tool_overrides; both branches unit-tested
    3. ✓ JSON Schema for profiles validates family field and rejects unknown values (implemented in Python per CONTEXT D-07; verified by TestFamilyRoundTrip.test_load_profile_rejects_unknown_family)
    4. ✓ All existing operator-profile tests still pass — zero behavior change for operator family (verified by TestOperatorBranchByteCompat snapshot + full regression run)

    ## Regression results
    - `pytest tests/test_profile_gating.py`: [PASS/FAIL count]
    - `pytest tests/`: [PASS/FAIL count, total]
    - `pytest tests/golden/`: [PASS/FAIL count]
    - `pytest tests/evals/`: [PASS/FAIL count]

    ## Deferred to H.4b
    - First real developer-family profile (`tools/profiles/developer/sandbox.json`)
    - FSI dev canon overlay (`canon/industry/fsi/developer-sandbox/`)
    - Negative-space test matrix proving operator/developer family isolation with real profiles
    - Pinning the `tool_overrides` value-string enum (developer-sandbox, developer-restricted, …)
    - Activity-log family-field emission

    ## Self-Check: PASSED
    ```
  </action>
  <acceptance_criteria>
    - `.planning/phases/H.4a-profile-family-schema-extension/H.4a-01-SUMMARY.md` exists and contains `## Self-Check: PASSED`.
    - SUMMARY.md contains the literal strings `PROFAM-01`, `PROFAM-02`, `VALID_FAMILIES`, `tool_overrides`.
    - `pytest tests/ -v` returns exit code 0 (full suite passes). If any non-H.4a-related pre-existing failure, document it in SUMMARY.md under "Pre-existing test issues" — do not fix in this plan.
    - `git status` shows ONLY the 7 files in this plan's `files_modified` list plus `.planning/phases/H.4a-.../H.4a-01-SUMMARY.md` (and STATE.md / ROADMAP.md from gsd-tools commits). No `canon/` changes, no scenario/ changes, no .github/workflows/ changes.
  </acceptance_criteria>
</task>

</tasks>

<verification>
After all tasks complete, verify the phase exit gate:

1. **Family field on all profiles** — `for f in tools/profiles/{read-only,engineer,break-glass}.json; do grep -q '"family": "operator"' "$f" || (echo "MISSING: $f"; exit 1); done; echo "✓ family field present"`.
2. **VALID_FAMILIES constant** — `grep "VALID_FAMILIES = {" tools/apply_engine.py` returns the constant definition.
3. **Branch dispatch working** — Python sanity script: `python3 -c "from tools.apply_engine import check_tool_permitted; assert check_tool_permitted('engineer','list-environments') is True; assert check_tool_permitted('read-only','delete-topics') is False"` exits 0.
4. **Snapshot baseline present** — `tests/snapshots/h4a_operator_permits.json` exists and parses as JSON.
5. **All tests pass** — `pytest tests/test_profile_gating.py -v` returns 0; `pytest tests/ -v` returns 0.
6. **No spillover** — `git status` shows ONLY the 7 plan-modified files + SUMMARY + gsd-tools state files. No `canon/`, no scenario/, no .github/, no docs outside .planning/.

All 6 must pass before the phase is considered done. Any failure → re-route to gap closure.
</verification>
