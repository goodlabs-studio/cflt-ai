---
phase: 03C-act-rail-profile-gating
plan: 02
type: execute
wave: 2
depends_on: ["03C-01"]
files_modified:
  - tools/apply_engine.py
  - .claude/commands/dsp-apply.md
autonomous: true
requirements: [ACTG-01, ACTG-03, ACTG-04]

must_haves:
  truths:
    - "check_tool_permitted() denies unclassified tools with fail-closed behavior"
    - "check_tool_permitted() uses tier hierarchy: read-only < engineer < break-glass"
    - "load_profile() accepts optional customer param and checks customer overlay first"
    - "emit_activity_log_apply() accepts and writes override_reason field"
    - "write_incident_article() accepts and writes override_reason to frontmatter"
    - "dsp-apply.md Step 6 has two-step break-glass branch"
  artifacts:
    - path: "tools/apply_engine.py"
      provides: "Classification-aware tool check, customer overlay loading, dual override logging"
      exports: ["check_tool_permitted", "load_tool_classification", "load_profile", "emit_activity_log_apply", "write_incident_article"]
    - path: ".claude/commands/dsp-apply.md"
      provides: "Two-step break-glass confirmation flow in Step 6"
      contains: "CONFIRM BREAK-GLASS"
  key_links:
    - from: "tools/apply_engine.py::check_tool_permitted"
      to: "tools/profiles/tool_classification.json"
      via: "JSON load and tier lookup"
      pattern: "tool_classification.json"
    - from: "tools/apply_engine.py::load_profile"
      to: "canon/customer/*/profiles/*.json"
      via: "customer overlay path resolution"
      pattern: "customer.*profiles"
    - from: ".claude/commands/dsp-apply.md"
      to: "tools/apply_engine.py::emit_activity_log_apply"
      via: "override_reason parameter in Step 8"
      pattern: "override_reason"
---

<objective>
Extend apply_engine.py with classification-table-aware tool checking, customer overlay profile loading, and dual override_reason logging. Update dsp-apply.md with the two-step break-glass confirmation flow.

Purpose: Wires the classification data (Plan 01) into enforcement logic. Per ACTG-01, unclassified tools must be denied. Per ACTG-03, break-glass requires two-step confirmation with override reason logged to both activity log and incident article. Per ACTG-04, load_profile() must support customer overlays.
Output: Extended apply_engine.py, updated dsp-apply.md
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

<interfaces>
<!-- Current apply_engine.py signatures that will be extended -->

From tools/apply_engine.py (current):
```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = PROJECT_ROOT / "tools" / "profiles"
VALID_PROFILES = {"read-only", "engineer", "break-glass"}

def load_profile(profile_name: str) -> Dict:
    """Load a policy profile by name from PROFILES_DIR."""

def check_profile_permits(profile: Dict, artifact_id: str) -> bool:
    """Check whether a policy profile permits a given artifact operation."""

def emit_activity_log_apply(
    overlay: str, plan_path: str, artifact_id: str, profile_name: str,
    confirmation_status: str, execution_result: str, duration_seconds: float,
    gate_results: List[Dict], operator: str,
) -> None:
    """Append a /dsp:apply entry to the overlay-scoped activity log."""

def write_incident_article(
    slug: str, artifact_id: str, operator: str, profile_name: str,
    outcome: str, canon_hash: str, plan_path: str, gate_results: List[Dict],
    execution_result: str,
) -> Path:
    """Write a wiki incident article for a /dsp:apply execution."""
```

From tools/profiles/tool_classification.json (created in Plan 01):
```json
{
  "version": "1",
  "description": "mcp-confluent tool-to-tier mapping...",
  "tools": { "confluent_kafka_topic_list": "read-only", ... },
  "unclassified_policy": "deny"
}
```

Tier hierarchy (from RESEARCH.md):
- "read-only" — permitted by read-only, engineer, and break-glass
- "engineer" — permitted by engineer and break-glass; denied by read-only
- "break-glass" — permitted only by break-glass; denied by read-only and engineer
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Extend apply_engine.py with tool classification, customer overlay, and dual override logging</name>
  <files>
    tools/apply_engine.py,
    tests/test_apply_engine.py
  </files>
  <read_first>
    tools/apply_engine.py,
    tests/test_apply_engine.py,
    tools/profiles/tool_classification.json,
    canon/customer/acme-bank/profiles/engineer.json
  </read_first>
  <behavior>
    - Test: load_tool_classification() returns dict with "tools" and "unclassified_policy" keys
    - Test: check_tool_permitted("read-only", "confluent_kafka_topic_list") returns True (read-only tool, read-only profile)
    - Test: check_tool_permitted("read-only", "confluent_kafka_topic_create") returns False (engineer tool, read-only profile)
    - Test: check_tool_permitted("engineer", "confluent_kafka_topic_create") returns True (engineer tool, engineer profile)
    - Test: check_tool_permitted("engineer", "confluent_cluster_delete") returns False (break-glass tool, engineer profile)
    - Test: check_tool_permitted("break-glass", "confluent_cluster_delete") returns True (break-glass tool, break-glass profile)
    - Test: check_tool_permitted("engineer", "nonexistent_tool_xyz") returns False (unclassified, fail-closed)
    - Test: load_profile("engineer", customer="acme-bank") returns profile WITHOUT module/flink
    - Test: load_profile("engineer", customer="acme-bank") returns profile WITH role/cp_audit
    - Test: load_profile("engineer", customer="nonexistent") falls back to base engineer (has module/flink)
    - Test: load_profile("engineer") without customer param still works (backward compat)
    - Test: emit_activity_log_apply with override_reason="P0 incident" includes "P0 incident" in log content
    - Test: write_incident_article with override_reason="DR failover" includes "override_reason: DR failover" in frontmatter
  </behavior>
  <action>
    Add the following to `tools/apply_engine.py`:

    1. **PROFILE_TIER_ORDER constant** (after VALID_PROFILES):
       ```python
       PROFILE_TIER_ORDER = ["read-only", "engineer", "break-glass"]
       ```

    2. **load_tool_classification() function** (new, in a new "Tool Classification" section):
       ```python
       _tool_classification_cache = None

       def load_tool_classification() -> Dict:
           """Load tool_classification.json. Cached after first load."""
           global _tool_classification_cache
           if _tool_classification_cache is None:
               path = PROFILES_DIR / "tool_classification.json"
               _tool_classification_cache = json.loads(path.read_text())
           return _tool_classification_cache
       ```

    3. **check_tool_permitted() function** (new, parallel to check_profile_permits):
       ```python
       def check_tool_permitted(profile_name: str, tool_name: str, customer: Optional[str] = None) -> bool:
           """Check whether profile_name permits invoking tool_name via classification table.

           Returns False (fail-closed) if tool_name is not in classification table.
           Uses tier hierarchy: read-only < engineer < break-glass.
           If customer is provided, loads customer overlay profile for tier comparison.

           Args:
               profile_name: One of VALID_PROFILES.
               tool_name: Exact mcp-confluent tool name.
               customer: Optional customer name for overlay resolution.

           Returns:
               True if permitted; False otherwise (fail-closed).
           """
           classification = load_tool_classification()
           tools = classification.get("tools", {})

           if tool_name not in tools:
               return False

           required_tier = tools[tool_name]
           profile_idx = PROFILE_TIER_ORDER.index(profile_name)
           required_idx = PROFILE_TIER_ORDER.index(required_tier)
           return profile_idx >= required_idx
       ```

    4. **Extend load_profile() signature** — add `customer` as keyword-only parameter with default None (per RESEARCH.md Pitfall 2, use `*, customer` or `customer: Optional[str] = None`). The customer param checks `canon/customer/<name>/profiles/<profile_name>.json` first, falls back to base:
       ```python
       def load_profile(profile_name: str, *, customer: Optional[str] = None) -> Dict:
       ```
       Add customer overlay resolution BEFORE the base fallback:
       ```python
       if customer:
           customer_profile = PROJECT_ROOT / "canon" / "customer" / customer / "profiles" / f"{profile_name}.json"
           if customer_profile.exists():
               return json.loads(customer_profile.read_text())
       ```
       Keep existing base fallback unchanged after the customer check.

    5. **Extend emit_activity_log_apply() signature** — add `override_reason: Optional[str] = None` parameter. When not None, add a line `f"**Override reason:** {override_reason}"` to the entry_lines list, after the "Canon stack" line.

    6. **Extend write_incident_article() signature** — add `override_reason: Optional[str] = None` parameter. When not None, add `f"override_reason: {override_reason}"` to frontmatter_lines (before the closing `"---"`), and add a line in the "## Why" section: `f"Override reason: {override_reason}"`.

    Then add tests to `tests/test_apply_engine.py` for the new functionality:
    - New import: `check_tool_permitted, load_tool_classification` in the import block
    - New test class `TestToolClassification` with the behavior tests listed above
    - New test class `TestCustomerOverlay` with customer param tests
    - New test class `TestOverrideReasonLogging` with dual-logging tests

    CRITICAL: All new parameters use `Optional[str] = None` (not `str | None`) per Python 3.9 compat rule.
    CRITICAL: `customer` parameter on `load_profile` must be keyword-only to avoid breaking existing positional callers (per RESEARCH.md Pitfall 2).
  </action>
  <verify>
    <automated>pytest tests/test_apply_engine.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `grep "PROFILE_TIER_ORDER" tools/apply_engine.py` finds the constant
    - `grep "def load_tool_classification" tools/apply_engine.py` finds the function
    - `grep "def check_tool_permitted" tools/apply_engine.py` finds the function
    - `grep "customer: Optional\[str\]" tools/apply_engine.py` finds customer param on load_profile
    - `grep "override_reason: Optional\[str\]" tools/apply_engine.py` finds param on both emit and write functions
    - `grep "override_reason:" tools/apply_engine.py` appears in both emit_activity_log_apply and write_incident_article
    - `grep "class TestToolClassification" tests/test_apply_engine.py` finds new test class
    - `grep "class TestCustomerOverlay" tests/test_apply_engine.py` finds new test class
    - `grep "class TestOverrideReasonLogging" tests/test_apply_engine.py` finds new test class
    - `pytest tests/test_apply_engine.py -x -q` passes ALL tests (existing 27 + new)
    - No `str | None` union syntax anywhere in apply_engine.py (Python 3.9 compat)
  </acceptance_criteria>
  <done>apply_engine.py extended with check_tool_permitted(), customer overlay on load_profile(), and override_reason on both logging functions. All tests pass including new and existing.</done>
</task>

<task type="auto">
  <name>Task 2: Update dsp-apply.md with two-step break-glass confirmation</name>
  <files>
    .claude/commands/dsp-apply.md
  </files>
  <read_first>
    .claude/commands/dsp-apply.md,
    .planning/phases/03C-act-rail-profile-gating/03C-RESEARCH.md
  </read_first>
  <action>
    Update `.claude/commands/dsp-apply.md` Step 6 to include the break-glass two-step confirmation branch per CONTEXT.md locked decision and RESEARCH.md Pattern 4.

    Add the following AFTER the existing Step 6 content (before Step 7), as a subsection:

    ```markdown
    ### Step 6 Break-Glass Extension (when --profile break-glass)

    If profile is "break-glass", execute this two-step sequence BEFORE the standard confirmation:

    **Interaction 1 -- Override reason (required):**
    Ask: "Break-glass profile selected. This bypasses standard engineer controls.
    Provide override reason (e.g., 'P0 incident: Flink pool exhausted, DR failover required'):"

    If the user provides an empty reason or declines:
    - Treat as CANCEL
    - Log to activity log: call `emit_activity_log_apply()` with `execution_result="break-glass-reason-rejected"`
    - Do NOT proceed.

    Store response as <override_reason>.

    **Interaction 2 -- Artifact + reason confirmation:**
    Display:
    ```
    === BREAK-GLASS CONFIRMATION REQUIRED ===
    Artifact:        <artifact_id>
    Profile:         break-glass
    Override Reason: <override_reason>
    Operator:        <operator_id>
    [gate results table from Step 4]
    ```

    Ask: "CONFIRM BREAK-GLASS: <artifact_id> with reason: <override_reason>?"
    Options: ["CONFIRM BREAK-GLASS", "CANCEL"]

    On CONFIRM BREAK-GLASS: proceed to Step 7 with override_reason captured for Steps 8 and 9.
    On CANCEL: log to activity log with `confirmation_status="rejected"`, `execution_result="break-glass-cancelled"`. Exit.

    **Dual logging requirement (ACTG-03):**
    - Step 8 (activity log): pass override_reason to `emit_activity_log_apply()` as `override_reason=<override_reason>`
    - Step 9 (incident article): pass override_reason to `write_incident_article()` as `override_reason=<override_reason>`
    ```

    Also update Step 7 comment to remove the "Phase 3c will classify" reference since this IS Phase 3c. Replace with:
    ```
    - MCP tool classification is enforced via `check_tool_permitted()` from `tools/apply_engine.py`
    - The tool_classification.json table determines which MCP tools the active profile can invoke
    ```

    Also update Step 8 to mention the optional override_reason parameter:
    Add after the operator line: `  - `override_reason`: from Step 6 break-glass flow (if break-glass profile; omit otherwise)`

    Also update Step 9 similarly:
    Add to the write_incident_article call list: `  - `override_reason`: from Step 6 break-glass flow (if break-glass profile; omit otherwise)`
  </action>
  <verify>
    <automated>grep -c "BREAK-GLASS CONFIRMATION REQUIRED" .claude/commands/dsp-apply.md | grep -q "1" && grep -c "override_reason" .claude/commands/dsp-apply.md | xargs test 3 -le && echo "OK: break-glass two-step and override_reason present"</automated>
  </verify>
  <acceptance_criteria>
    - `grep "BREAK-GLASS CONFIRMATION REQUIRED" .claude/commands/dsp-apply.md` finds the display block
    - `grep "CONFIRM BREAK-GLASS" .claude/commands/dsp-apply.md` finds the confirmation option
    - `grep "override_reason" .claude/commands/dsp-apply.md` appears at least 3 times (Step 6, Step 8, Step 9)
    - `grep "Interaction 1" .claude/commands/dsp-apply.md` finds the reason collection step
    - `grep "Interaction 2" .claude/commands/dsp-apply.md` finds the confirmation step
    - `grep "break-glass-reason-rejected" .claude/commands/dsp-apply.md` finds the empty-reason handling
    - `grep "check_tool_permitted" .claude/commands/dsp-apply.md` finds the Phase 3c tool classification reference
    - Step 7 no longer says "Phase 3c will classify"
  </acceptance_criteria>
  <done>dsp-apply.md has two-step break-glass flow with reason collection and dual logging. Step 7 updated to reference tool classification. Steps 8 and 9 reference override_reason parameter.</done>
</task>

</tasks>

<verification>
- `pytest tests/test_apply_engine.py -x -q` — all tests pass (existing + new)
- `grep "def check_tool_permitted" tools/apply_engine.py` — new function exists
- `grep "CONFIRM BREAK-GLASS" .claude/commands/dsp-apply.md` — two-step flow present
- `grep "override_reason" tools/apply_engine.py` — dual logging wired
</verification>

<success_criteria>
- check_tool_permitted() enforces tier hierarchy against classification table
- Unclassified tools fail closed (return False)
- load_profile() supports customer keyword param with overlay-first resolution
- emit_activity_log_apply() and write_incident_article() both accept and write override_reason
- dsp-apply.md Step 6 has complete two-step break-glass flow
- All existing tests still pass (backward compatible)
- All new tests pass
</success_criteria>

<output>
After completion, create `.planning/phases/03C-act-rail-profile-gating/03C-02-SUMMARY.md`
</output>
