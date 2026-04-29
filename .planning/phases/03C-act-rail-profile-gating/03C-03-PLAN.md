---
phase: 03C-act-rail-profile-gating
plan: 03
type: execute
wave: 3
depends_on: ["03C-02"]
files_modified:
  - tests/test_profile_gating.py
autonomous: true
requirements: [ACTG-01, ACTG-02, ACTG-03, ACTG-04]

must_haves:
  truths:
    - "Every tool forbidden by read-only profile is denied (full matrix)"
    - "Every break-glass-tier tool forbidden by engineer profile is denied"
    - "Every tool is permitted by break-glass profile"
    - "Unclassified tools are denied by all profiles"
    - "acme-bank engineer denies module/flink tools and permits role/cp_audit tools"
    - "Classification table contains >= 50 tools"
  artifacts:
    - path: "tests/test_profile_gating.py"
      provides: "Per-profile negative-space test suite with full tool x profile matrix"
      contains: "TestReadOnlyGating"
      min_lines: 80
  key_links:
    - from: "tests/test_profile_gating.py"
      to: "tools/apply_engine.py::check_tool_permitted"
      via: "import and parametrized assertions"
      pattern: "check_tool_permitted"
    - from: "tests/test_profile_gating.py"
      to: "tools/profiles/tool_classification.json"
      via: "JSON load for tool list parametrization"
      pattern: "tool_classification.json"
    - from: "tests/test_profile_gating.py::TestCustomerDifferential"
      to: "canon/customer/acme-bank/profiles/engineer.json"
      via: "load_profile with customer='acme-bank'"
      pattern: "acme-bank"
---

<objective>
Create the per-profile negative-space test suite that proves every forbidden tool fails closed across all profiles, verifies classification table coverage >= 50 tools, and demonstrates acme-bank differential gating.

Purpose: This is the verification layer for ACTG-02 (negative-space suites prove forbidden tools fail closed) and exercises ACTG-01 (coverage gate), ACTG-03 (break-glass logging), and ACTG-04 (customer differential). The full tool x profile matrix via pytest.mark.parametrize is the only way to prove 50+ tools x 3 profiles = 150+ combinations.
Output: tests/test_profile_gating.py with parametrized per-profile test classes
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/03C-act-rail-profile-gating/03C-CONTEXT.md
@.planning/phases/03C-act-rail-profile-gating/03C-RESEARCH.md
@.planning/phases/03C-act-rail-profile-gating/03C-01-SUMMARY.md
@.planning/phases/03C-act-rail-profile-gating/03C-02-SUMMARY.md

<interfaces>
<!-- Functions from apply_engine.py (after Plan 02 extensions) -->

From tools/apply_engine.py:
```python
PROFILE_TIER_ORDER = ["read-only", "engineer", "break-glass"]

def load_tool_classification() -> Dict:
    """Load tool_classification.json. Cached after first load."""

def check_tool_permitted(profile_name: str, tool_name: str, customer: Optional[str] = None) -> bool:
    """Check whether profile_name permits invoking tool_name via classification table.
    Returns False (fail-closed) if tool_name is not in classification table."""

def load_profile(profile_name: str, *, customer: Optional[str] = None) -> Dict:
    """Load a policy profile, with optional customer override."""
```

From tools/profiles/tool_classification.json:
```json
{
  "version": "1",
  "tools": { "<tool_name>": "<tier>", ... },
  "unclassified_policy": "deny"
}
```

Tier semantics:
- "read-only" tools: permitted by all three profiles
- "engineer" tools: permitted by engineer and break-glass; denied by read-only
- "break-glass" tools: permitted only by break-glass; denied by read-only and engineer
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create test_profile_gating.py with full parametrized negative-space suite</name>
  <files>
    tests/test_profile_gating.py
  </files>
  <read_first>
    tools/apply_engine.py,
    tools/profiles/tool_classification.json,
    canon/customer/acme-bank/profiles/engineer.json,
    tests/test_apply_engine.py
  </read_first>
  <action>
    Create `tests/test_profile_gating.py` following the RESEARCH.md Pattern 5 structure and mirroring the test class pattern from test_apply_engine.py.

    Structure:

    ```python
    """Per-profile negative-space test suite (ACTG-01, ACTG-02, ACTG-03, ACTG-04).

    Parametrized across every tool in tool_classification.json x every profile.
    Proves forbidden tools fail closed — not just "some", but ALL.
    """
    import json
    import sys
    from pathlib import Path

    import pytest

    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))

    from tools.apply_engine import (
        check_tool_permitted,
        load_profile,
        load_tool_classification,
    )

    # Load classification table for parametrization
    CLASSIFICATION = json.loads(
        (PROJECT_ROOT / "tools" / "profiles" / "tool_classification.json").read_text()
    )
    ALL_TOOLS = sorted(CLASSIFICATION["tools"].keys())

    # Partition tools by tier for targeted assertions
    READ_ONLY_TOOLS = [t for t, tier in CLASSIFICATION["tools"].items() if tier == "read-only"]
    ENGINEER_TOOLS = [t for t, tier in CLASSIFICATION["tools"].items() if tier == "engineer"]
    BREAK_GLASS_TOOLS = [t for t, tier in CLASSIFICATION["tools"].items() if tier == "break-glass"]

    # Tools that read-only should deny = engineer + break-glass tier tools
    READ_ONLY_FORBIDDEN = sorted(ENGINEER_TOOLS + BREAK_GLASS_TOOLS)
    # Tools that engineer should deny = break-glass tier tools only
    ENGINEER_FORBIDDEN = sorted(BREAK_GLASS_TOOLS)
    ```

    Test classes:

    1. **TestClassificationCoverage (ACTG-01):**
       - `test_classification_covers_minimum_tools`: `assert len(ALL_TOOLS) >= 50`
       - `test_all_tiers_have_tools`: each tier has at least 1 tool
       - `test_no_unknown_tiers`: every tier value in {"read-only", "engineer", "break-glass"}
       - `test_unclassified_policy_is_deny`: `CLASSIFICATION["unclassified_policy"] == "deny"`

    2. **TestReadOnlyGating (ACTG-02):**
       - `@pytest.mark.parametrize("tool_name", READ_ONLY_FORBIDDEN)` on `test_forbidden_tool_denied`: `assert not check_tool_permitted("read-only", tool_name)`
       - `@pytest.mark.parametrize("tool_name", READ_ONLY_TOOLS)` on `test_permitted_tool_allowed`: `assert check_tool_permitted("read-only", tool_name)`

    3. **TestEngineerGating (ACTG-02):**
       - `@pytest.mark.parametrize("tool_name", ENGINEER_FORBIDDEN)` on `test_break_glass_tool_denied`: `assert not check_tool_permitted("engineer", tool_name)`
       - `@pytest.mark.parametrize("tool_name", sorted(READ_ONLY_TOOLS + ENGINEER_TOOLS))` on `test_permitted_tool_allowed`: `assert check_tool_permitted("engineer", tool_name)`

    4. **TestBreakGlassGating (ACTG-02):**
       - `@pytest.mark.parametrize("tool_name", ALL_TOOLS)` on `test_all_tools_permitted`: `assert check_tool_permitted("break-glass", tool_name)`

    5. **TestUnclassifiedToolDenial (ACTG-01):**
       - `test_unclassified_denied_by_read_only`: `assert not check_tool_permitted("read-only", "nonexistent_tool_xyz")`
       - `test_unclassified_denied_by_engineer`: `assert not check_tool_permitted("engineer", "nonexistent_tool_xyz")`
       - `test_unclassified_denied_by_break_glass`: `assert not check_tool_permitted("break-glass", "nonexistent_tool_xyz")`

    6. **TestCustomerDifferential (ACTG-04):**
       - `test_base_engineer_permits_flink`: load base engineer profile, verify `"module/flink"` in `allowed_operations`
       - `test_acme_bank_engineer_denies_flink`: `load_profile("engineer", customer="acme-bank")` returns profile where `"module/flink"` NOT in `allowed_operations`
       - `test_acme_bank_engineer_permits_cp_audit`: `load_profile("engineer", customer="acme-bank")` returns profile where `"role/cp_audit"` in `allowed_operations`
       - `test_acme_bank_preserves_base_permissions`: acme-bank engineer still has `"module/topic"` in `allowed_operations`
       - `test_nonexistent_customer_falls_back_to_base`: `load_profile("engineer", customer="nonexistent")` returns base engineer (has `"module/flink"`)

    Ensure all tool name strings in parametrize decorators come from the classification table (loaded dynamically), NOT hardcoded. This makes tests self-updating if the classification table changes.
  </action>
  <verify>
    <automated>pytest tests/test_profile_gating.py -x -q && pytest tests/test_profile_gating.py --co -q 2>&1 | tail -1</automated>
  </verify>
  <acceptance_criteria>
    - `tests/test_profile_gating.py` exists
    - `grep "class TestClassificationCoverage" tests/test_profile_gating.py` finds the class
    - `grep "class TestReadOnlyGating" tests/test_profile_gating.py` finds the class
    - `grep "class TestEngineerGating" tests/test_profile_gating.py` finds the class
    - `grep "class TestBreakGlassGating" tests/test_profile_gating.py` finds the class
    - `grep "class TestUnclassifiedToolDenial" tests/test_profile_gating.py` finds the class
    - `grep "class TestCustomerDifferential" tests/test_profile_gating.py` finds the class
    - `grep "pytest.mark.parametrize" tests/test_profile_gating.py` appears at least 4 times
    - `grep "len(ALL_TOOLS) >= 50" tests/test_profile_gating.py` finds the ACTG-01 coverage gate
    - `grep "acme-bank" tests/test_profile_gating.py` finds the customer differential tests
    - `pytest tests/test_profile_gating.py -x -q` passes all tests
    - `pytest tests/test_profile_gating.py --co -q` shows >= 150 test items (50+ tools x 3 profiles worth of parametrized cases)
    - `pytest tests/ -x -q` passes full suite (no regressions)
  </acceptance_criteria>
  <done>Per-profile negative-space test suite with full tool x profile matrix passes. >= 150 parametrized test cases. Classification coverage gate at 50 tools. Customer differential verified for acme-bank.</done>
</task>

</tasks>

<verification>
- `pytest tests/test_profile_gating.py -x -q` — all tests pass
- `pytest tests/test_profile_gating.py --co -q 2>&1 | tail -1` — shows >= 150 test items
- `pytest tests/ -x -q` — full suite passes (no regressions across all test files)
</verification>

<success_criteria>
- 6 test classes covering ACTG-01 through ACTG-04
- Parametrized tests cover every tool x profile combination
- Unclassified tool denial tested for all 3 profiles
- Customer differential (acme-bank) verified: flink denied, cp_audit permitted
- Classification coverage gate: >= 50 tools
- Full test suite green
</success_criteria>

<output>
After completion, create `.planning/phases/03C-act-rail-profile-gating/03C-03-SUMMARY.md`
</output>
