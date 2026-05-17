# Phase 3C: Act Rail — Profile Gating - Research

**Researched:** 2026-04-29
**Domain:** Python policy enforcement, mcp-confluent tool classification, parametrized pytest, customer overlay composition
**Confidence:** HIGH

## Summary

Phase 3C closes the last open loop in the act rail: replacing the wildcard `"*"` in `break-glass.json` with explicit per-tool enumeration, building a classification table mapping every mcp-confluent tool to a profile tier, adding a two-step break-glass confirmation to `dsp-apply.md`, and wiring a customer overlay (acme-bank) that demonstrates differential profile gating. All four ACTG requirements have a direct code path in existing infrastructure — this is an extension, not a rewrite.

The classification table (`tools/profiles/tool_classification.json`) becomes the single source of truth. `check_profile_permits()` evolves from a list-membership check to a classification-table-aware lookup. Per-profile negative-space tests in `tests/test_profile_gating.py` verify forbidden tools fail closed across every profile and across the acme-bank customer overlay.

The scope is narrowly bounded: no new gates, no new profiles, no session-level activation. The v2 deferred items (session break-glass, runtime introspection, auditor tier) are explicitly out of scope.

**Primary recommendation:** Implement in three sequential waves — (1) classification table + profile JSON updates, (2) apply_engine.py and dsp-apply.md changes, (3) negative-space test suite. Each wave has a clear green/red signal before the next starts.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Tool Classification Architecture**
- Classification table lives in `tools/profiles/tool_classification.json` — single JSON file mapping every mcp-confluent tool name to its profile tier, loaded by apply_engine
- Tool list hardcoded from current mcp-confluent docs — explicit by-name per ACTG-01, no runtime introspection
- Fail-closed: unclassified tools denied by all profiles, logged as "unclassified_tool" — consistent with Phase 3b VALID_PROFILES fail-closed pattern
- Replace break-glass wildcard with explicit tool enumeration; engineer and read-only list allowed tools by name — satisfies ACTG-01 "by name, not regex"

**Break-Glass Two-Step Confirmation**
- Step 1: "Provide override reason" (free-text) — forces deliberation before commit point
- Step 2: "CONFIRM BREAK-GLASS: <artifact> with reason: <reason>?" — shows artifact + reason for final confirmation
- Override reason logged to both activity log (override_reason field) AND incident article frontmatter — dual logging per ACTG-03
- No session timeout — each invocation requires its own two-step confirmation; session-level activation is a v2 concern

**Customer Fork & Differential Gating**
- Customer overlay directory `canon/customer/<name>/profiles/` overrides base profiles — follows existing canon overlay composition pattern
- Demo customer: acme-bank (existing overlay in `canon/customer/acme-bank/`)
- Differential: acme-bank engineer profile removes "module/flink" (bank prohibits self-service Flink) and adds "role/cp_audit" (bank requires audit role management)
- `load_profile()` gains optional `customer` param; checks customer overlay first, falls back to base — consistent with canon/stack.py resolution

**Negative-Space Test Architecture**
- Single parametrized test file `tests/test_profile_gating.py` with per-profile test classes (TestReadOnlyGating, TestEngineerGating, TestBreakGlassGating)
- Structural tests: `check_profile_permits(profile, tool_name)` assertions — unit-level enforcement, no MCP mocking needed
- Full matrix: every tool × every profile via parametrize — ACTG-02 says "forbidden tools fail closed", not "some"
- Customer differential test: load acme-bank engineer, verify "module/flink" denied AND "role/cp_audit" permitted

### Claude's Discretion
- Exact mcp-confluent tool names and tier assignments (based on current documentation)
- Classification JSON schema details (field names, tier values)
- Error message wording for unclassified tool denials
- Break-glass prompt exact wording and formatting

### Deferred Ideas (OUT OF SCOPE)
- Session-level break-glass activation (approve once, apply multiple tools in window) — v2 concern
- Runtime tool discovery via MCP introspection — current approach is explicit hardcoded classification
- Profile tier beyond three (e.g., "auditor" tier for compliance-only operations) — not in v1 scope
- Automatic profile recommendation based on artifact type — future intelligence layer
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ACTG-01 | Every mcp-confluent tool (50+) classified into a profile by name, not regex | Classification table in `tool_classification.json`; profile JSONs updated with explicit tool lists |
| ACTG-02 | Per-profile negative-space test suite ensures forbidden tools fail closed | `tests/test_profile_gating.py` parametrized across every tool × every profile |
| ACTG-03 | Break-glass profile requires two-step confirmation with explicit override reason logged | Two-step flow in dsp-apply.md Step 6; `override_reason` field added to activity log and incident frontmatter |
| ACTG-04 | >= 1 customer fork demonstrates differential profile gating relative to base | `canon/customer/acme-bank/profiles/engineer.json` removes `module/flink`, adds `role/cp_audit`; differential test in test suite |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib: json | built-in | Load/parse classification table and profile files | Already used throughout tools/ |
| Python stdlib: pathlib | built-in | File resolution for profile and overlay directories | Established pattern in all tools/ modules |
| pytest | already installed | Parametrized negative-space test suite | Project test runner; 27 tests already passing in test_apply_engine.py |
| pytest.mark.parametrize | built-in to pytest | Full tool × profile matrix testing | Only viable way to prove every tool fails closed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typing (Dict, List, Optional) | stdlib | Type hints on new/extended functions | Python 3.9 compat — use `Optional[str]` not `str | None` |
| yaml | already installed | Customer overlay profile loading (if YAML format chosen) | If customer profiles use YAML; JSON also acceptable |

**Installation:** No new dependencies. All required libraries are already present.

**Python 3.9 compatibility rule (from STATE.md):** Use `Optional[List[str]]` not `X | Y` union syntax anywhere in tools/.

---

## Architecture Patterns

### Recommended Project Structure (Phase 3C additions)

```
tools/
├── profiles/
│   ├── tool_classification.json        # NEW: tool-name → tier map (50+ entries)
│   ├── read-only.json                  # UPDATE: add explicit allowed_tools list
│   ├── engineer.json                   # UPDATE: add explicit allowed_tools list
│   └── break-glass.json                # UPDATE: replace "*" with explicit tool names
├── apply_engine.py                     # UPDATE: customer param, classification lookup, dual override log

canon/customer/acme-bank/
├── profiles/                           # NEW directory
│   └── engineer.json                   # NEW: acme-bank engineer differential

tests/
└── test_profile_gating.py              # NEW: per-profile negative-space suite

.claude/commands/
└── dsp-apply.md                        # UPDATE: two-step break-glass in Step 6
```

### Pattern 1: Classification Table Schema

The `tool_classification.json` maps tool names to tier strings. Tier strings correspond to profile names. The apply_engine looks up the requested tool name and checks whether the active profile's tier permits it.

```json
{
  "version": "1",
  "tools": {
    "confluent_kafka_topic_create": "engineer",
    "confluent_kafka_topic_list":   "read-only",
    "confluent_flink_statement_create": "engineer",
    "confluent_cluster_delete":     "break-glass",
    "confluent_environment_delete": "break-glass"
  },
  "unclassified_policy": "deny"
}
```

**Tier semantics:**
- `"read-only"` — permitted by read-only, engineer, and break-glass
- `"engineer"` — permitted by engineer and break-glass; denied by read-only
- `"break-glass"` — permitted only by break-glass; denied by read-only and engineer

This is a tier hierarchy, not a flat list. A tool classified at tier `X` means "requires at least profile X to operate."

### Pattern 2: Updated `check_profile_permits()` — Classification-Aware

The existing `check_profile_permits(profile, artifact_id)` checks against `allowed_operations`. Phase 3C introduces a parallel check path for MCP tool names via the classification table.

```python
# Conceptual extension — exact names at Claude's discretion
PROFILE_TIER_ORDER = ["read-only", "engineer", "break-glass"]

def load_tool_classification() -> Dict:
    """Load tool_classification.json. Cached after first load."""
    path = PROFILES_DIR / "tool_classification.json"
    return json.loads(path.read_text())

def check_tool_permitted(profile_name: str, tool_name: str) -> bool:
    """Check whether profile_name permits invoking tool_name.

    Returns False (fail-closed) if tool_name is not in classification table.
    Logs 'unclassified_tool' event if tool not found.
    """
    classification = load_tool_classification()
    tools = classification.get("tools", {})

    if tool_name not in tools:
        # Fail-closed: unclassified tools are denied by all profiles
        return False

    required_tier = tools[tool_name]
    profile_idx = PROFILE_TIER_ORDER.index(profile_name)
    required_idx = PROFILE_TIER_ORDER.index(required_tier)
    return profile_idx >= required_idx
```

### Pattern 3: `load_profile()` with Customer Overlay

The customer param is optional — if provided, checks `canon/customer/<name>/profiles/<profile>.json` first, then falls back to base `tools/profiles/<profile>.json`.

```python
def load_profile(profile_name: str, customer: Optional[str] = None) -> Dict:
    """Load a policy profile, with optional customer override.

    Customer overlay path: canon/customer/<name>/profiles/<profile>.json
    Falls back to tools/profiles/<profile>.json if customer overlay absent.
    """
    if profile_name not in VALID_PROFILES:
        raise ValueError(
            f"Unknown profile: {profile_name!r} — must be one of {sorted(VALID_PROFILES)}"
        )

    # Check customer overlay first
    if customer:
        customer_profile = (
            PROJECT_ROOT / "canon" / "customer" / customer / "profiles" / f"{profile_name}.json"
        )
        if customer_profile.exists():
            return json.loads(customer_profile.read_text())

    # Fall back to base profile
    profile_path = PROFILES_DIR / f"{profile_name}.json"
    return json.loads(profile_path.read_text())
```

### Pattern 4: Break-Glass Two-Step in dsp-apply.md

The existing Step 6 (`## Step 6: Human confirmation`) gains a break-glass branch. When `--profile break-glass` is active, Step 6 executes TWO interactions before proceeding:

```
STEP 6 BREAK-GLASS BRANCH (when profile == "break-glass"):

Interaction 1 — Reason collection:
  Ask: "Break-glass profile selected. Provide override reason (required):"
  If user provides empty string or cancels: CANCEL — log bypass-attempt, exit
  Store reason as <override_reason>

Interaction 2 — Full confirmation:
  Display:
    === BREAK-GLASS CONFIRMATION REQUIRED ===
    Artifact:        <artifact_id>
    Profile:         break-glass
    Override Reason: <override_reason>
    Operator:        <operator_id>
    ...gate results...
  Ask: "CONFIRM BREAK-GLASS: <artifact_id> with reason: <override_reason>?"
  Options: ["CONFIRM BREAK-GLASS", "CANCEL"]

On CONFIRM: proceed to Step 7
  - Pass override_reason to emit_activity_log_apply() as override_reason field
  - Pass override_reason to write_incident_article() for frontmatter

On CANCEL: log rejected, exit
```

**Dual logging requirement (ACTG-03):** `override_reason` must appear in:
1. Activity log entry — new field alongside existing 11 fields
2. Incident article frontmatter — new key alongside existing 7 keys

### Pattern 5: Parametrized Negative-Space Test Architecture

```python
# tests/test_profile_gating.py — structural sketch

import pytest
from tools.apply_engine import load_profile, check_tool_permitted

# Load full tool list from classification table
import json
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLASSIFICATION = json.loads(
    (PROJECT_ROOT / "tools" / "profiles" / "tool_classification.json").read_text()
)
ALL_TOOLS = list(CLASSIFICATION["tools"].keys())

# Tools forbidden for read-only = all tools
ENGINEER_FORBIDDEN = [t for t, tier in CLASSIFICATION["tools"].items()
                      if tier == "break-glass"]
READ_ONLY_FORBIDDEN = ALL_TOOLS  # all tools require at least engineer

class TestReadOnlyGating:
    @pytest.mark.parametrize("tool_name", READ_ONLY_FORBIDDEN)
    def test_forbidden_tool_denied(self, tool_name):
        assert not check_tool_permitted("read-only", tool_name)

class TestEngineerGating:
    @pytest.mark.parametrize("tool_name", ENGINEER_FORBIDDEN)
    def test_break_glass_tool_denied(self, tool_name):
        assert not check_tool_permitted("engineer", tool_name)

class TestBreakGlassGating:
    @pytest.mark.parametrize("tool_name", ALL_TOOLS)
    def test_all_tools_permitted(self, tool_name):
        assert check_tool_permitted("break-glass", tool_name)

class TestCustomerDifferential:
    def test_acme_bank_engineer_denies_flink(self):
        profile = load_profile("engineer", customer="acme-bank")
        # module/flink removed from acme-bank engineer
        assert not check_tool_permitted("engineer", "confluent_flink_statement_create",
                                        customer="acme-bank")

    def test_acme_bank_engineer_permits_cp_audit(self):
        profile = load_profile("engineer", customer="acme-bank")
        # role/cp_audit added in acme-bank engineer
        assert check_tool_permitted("engineer", "confluent_rbac_role_binding_create",
                                    customer="acme-bank")
```

### Anti-Patterns to Avoid

- **Regex-based tool matching:** ACTG-01 requires "by name, not regex." No `re.match(r".*_delete$", tool)` patterns in profiles or classification table.
- **Wildcard retained in break-glass.json:** The `"*"` wildcard must be replaced with explicit tool names before Phase 3C is complete.
- **Silent fallthrough on unclassified tools:** An unclassified tool must be logged as `"unclassified_tool"` and denied — not silently passed or passed with a warning.
- **Customer profile without base fallback:** `load_profile()` must fall back to base if customer overlay file is absent — not raise FileNotFoundError.
- **Skipping break-glass two-step for "obvious" cases:** The two-step is unconditional when profile is break-glass. No shortcuts.
- **Python 3.10+ union syntax:** `str | None` not permitted — use `Optional[str]` per STATE.md constraint.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tool permission check | Custom regex or glob matching against tool names | Exact-match lookup against classification table | Regex creates false positives; explicit by-name is the ACTG-01 requirement |
| Profile tier comparison | Custom string comparison logic | `PROFILE_TIER_ORDER` index comparison | Deterministic, testable, avoids string ordering bugs |
| Customer override resolution | Custom file search logic | `canon/stack.py` pattern (`load_profile(name, customer=X)` with explicit path check) | Already battle-tested in Phase 3a/3b; same composition semantics |
| Test parametrization | Separate test function per tool | `@pytest.mark.parametrize("tool_name", ALL_TOOLS)` loaded from classification table | 50+ tools × 3 profiles = 150+ combinations; only parametrize scales |

---

## Common Pitfalls

### Pitfall 1: Classification Table Drift from Actual mcp-confluent Tools
**What goes wrong:** Tool classification table is authored once and never updated. Real mcp-confluent adds/renames tools; table becomes stale. Unclassified new tools silently fail closed — correct behavior, but new tooling silently unavailable.
**Why it happens:** No automated linkage between mcp-confluent capability list and classification table.
**How to avoid:** Add a test in `test_profile_gating.py` that verifies `ALL_TOOLS` count >= 50 (ACTG-01 threshold). Also: classification table version field enables future drift detection.
**Warning signs:** `check_tool_permitted()` logging "unclassified_tool" events for a tool that should work.

### Pitfall 2: `load_profile()` Signature Change Breaks Existing Tests
**What goes wrong:** Adding `customer: Optional[str] = None` to `load_profile()` is backward-compatible as a keyword-only addition, but any test that calls `load_profile("engineer", "acme-bank")` positionally may fail if parameter order changes.
**Why it happens:** Positional vs keyword argument mismatch when extending function signatures.
**How to avoid:** Add `customer` as keyword-only argument. All existing `load_profile(name)` calls continue to work. New calls use `load_profile(name, customer="acme-bank")`.
**Warning signs:** `TypeError` in existing `test_apply_engine.py` tests after signature change.

### Pitfall 3: `override_reason` Field Not Added to Both Log Destinations
**What goes wrong:** Override reason logged to activity log but not incident article frontmatter (or vice versa). ACTG-03 requires dual logging — missing either destination fails the requirement.
**Why it happens:** Two separate functions (`emit_activity_log_apply` and `write_incident_article`) must both be updated; easy to update one and miss the other.
**How to avoid:** Both functions gain `override_reason: Optional[str] = None` parameter simultaneously. Tests verify both destinations.
**Warning signs:** Incident article frontmatter has 7 keys but `override_reason` missing; or activity log missing field.

### Pitfall 4: acme-bank Profile Overlay Missing `name` Field
**What goes wrong:** `canon/customer/acme-bank/profiles/engineer.json` is authored as a partial override (only diff from base) — but `load_profile()` returns the whole dict, including `name`. If `name` field is missing from overlay, downstream code breaks.
**Why it happens:** Partial overlay vs. full profile file confusion. Canon config overlays are partial diffs; profile files are complete documents.
**How to avoid:** Customer profile files must be COMPLETE profile documents (same schema as base), not partial diffs. The `load_profile()` customer-override path loads the entire file, not merges it.
**Warning signs:** `profile["name"]` KeyError or missing `allowed_operations` key from acme-bank engineer profile.

### Pitfall 5: Parametrized Test Count Below ACTG-01 Threshold
**What goes wrong:** Test suite parametrizes against classification table, but table has fewer than 50 tools because not all mcp-confluent tools were enumerated during authoring.
**Why it happens:** mcp-confluent has 50+ tools; if table is authored by memory rather than docs, some are missed.
**How to avoid:** Include a dedicated test `test_classification_covers_minimum_tools()` asserting `len(ALL_TOOLS) >= 50`. This test fails RED immediately if classification was under-authored.
**Warning signs:** Test count on `TestBreakGlassGating` parametrize is fewer than 50 cases.

---

## Code Examples

### Classification Table — Partial Example (Claude's Discretion for Full List)

```json
{
  "version": "1",
  "description": "mcp-confluent tool-to-tier mapping. Tier hierarchy: read-only < engineer < break-glass.",
  "tools": {
    "confluent_kafka_topic_list":               "read-only",
    "confluent_kafka_topic_describe":            "read-only",
    "confluent_schema_registry_schema_list":     "read-only",
    "confluent_flink_statement_list":            "read-only",
    "confluent_kafka_topic_create":              "engineer",
    "confluent_kafka_topic_update":              "engineer",
    "confluent_schema_registry_schema_create":   "engineer",
    "confluent_flink_statement_create":          "engineer",
    "confluent_flink_statement_delete":          "engineer",
    "confluent_rbac_role_binding_create":        "engineer",
    "confluent_rbac_role_binding_delete":        "engineer",
    "confluent_connector_create":                "engineer",
    "confluent_kafka_topic_delete":              "break-glass",
    "confluent_environment_delete":              "break-glass",
    "confluent_cluster_delete":                  "break-glass",
    "confluent_cluster_link_create":             "break-glass",
    "confluent_cluster_link_delete":             "break-glass"
  },
  "unclassified_policy": "deny"
}
```

**Source:** Claude's Discretion — exact names from mcp-confluent documentation. Tool names follow `confluent_<resource>_<action>` convention. Full list must reach >= 50 entries (ACTG-01).

### acme-bank Customer Engineer Profile

```json
{
  "name": "engineer",
  "description": "Acme Bank engineer profile: Flink self-service prohibited, audit role management required.",
  "allowed_operations": ["module/topic", "role/cp_schema", "role/cp_rbac", "role/cp_connect", "role/cp_audit"],
  "customer_overrides": {
    "removed": ["module/flink"],
    "added": ["role/cp_audit"],
    "adr_ref": "canon/customer/acme-bank/adrs/adr-003.md"
  }
}
```

Note: `module/flink` is absent vs. base engineer; `role/cp_audit` is present. The `customer_overrides` metadata block is optional documentation — `load_profile()` uses `allowed_operations` only.

### Break-Glass Two-Step in dsp-apply.md (Step 6 Extension)

```markdown
## Step 6: Human confirmation -- MANDATORY

[existing content for standard profiles...]

### Step 6 Break-Glass Extension (when --profile break-glass)

If profile is "break-glass", execute this two-step sequence BEFORE the standard confirmation:

**Interaction 1 — Override reason (required):**
Ask: "Break-glass profile selected. This bypasses standard engineer controls.
Provide override reason (e.g., 'P0 incident: Flink pool exhausted, DR failover required'):"

If the user provides an empty reason or declines:
- Treat as CANCEL
- Log to activity log with execution_result="break-glass-reason-rejected"
- Do NOT proceed.

Store response as <override_reason>.

**Interaction 2 — Artifact + reason confirmation:**
Display:
  === BREAK-GLASS CONFIRMATION REQUIRED ===
  Artifact:        <artifact_id>
  Profile:         break-glass
  Override Reason: <override_reason>
  Operator:        <operator_id>
  [gate results table]

Ask: "CONFIRM BREAK-GLASS: <artifact_id> with reason: <override_reason>?"
Options: ["CONFIRM BREAK-GLASS", "CANCEL"]

On CONFIRM BREAK-GLASS: proceed to Step 7 with override_reason captured for Steps 8 and 9.
On CANCEL: log rejected, exit.

**Dual logging requirement:**
- Step 8 (activity log): pass override_reason to emit_activity_log_apply()
- Step 9 (incident article): pass override_reason to write_incident_article()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| break-glass wildcard `"*"` | Explicit per-tool enumeration | Phase 3C | Full tool inventory; unclassified tools now fail closed |
| `check_profile_permits()` artifact-only | Classification-table-aware tool check | Phase 3C | MCP tool names enforced, not just fsi-dsp artifact IDs |
| Single-step break-glass confirmation | Two-step with reason capture | Phase 3C | Forces deliberation; reason appears in both audit trails |
| No customer profile overlays | `canon/customer/<name>/profiles/` overlay | Phase 3C | Differential gating per customer without forking base profiles |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | apply_engine.py, test suite | Yes | system python3 | — |
| pytest | test_profile_gating.py | Yes | already installed | — |
| mcp-confluent MCP server | Tool name enumeration reference | Yes (registered in .mcp.json) | — | Tool list from docs |
| json (stdlib) | Classification table loading | Yes | built-in | — |

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (already installed) |
| Config file | pytest.ini or setup.cfg — existing project config |
| Quick run command | `pytest tests/test_profile_gating.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ACTG-01 | Every mcp-confluent tool classified by name | unit | `pytest tests/test_profile_gating.py::test_classification_covers_minimum_tools -x` | Wave 0 |
| ACTG-01 | Unclassified tool denied by all profiles | unit | `pytest tests/test_profile_gating.py::TestReadOnlyGating -x` | Wave 0 |
| ACTG-02 | Every break-glass-tier tool denied by engineer | unit | `pytest tests/test_profile_gating.py::TestEngineerGating -x` | Wave 0 |
| ACTG-02 | Every tool denied by read-only | unit | `pytest tests/test_profile_gating.py::TestReadOnlyGating -x` | Wave 0 |
| ACTG-03 | Break-glass activity log contains override_reason | unit | `pytest tests/test_profile_gating.py::TestBreakGlassGating -x` | Wave 0 |
| ACTG-03 | Break-glass incident article frontmatter contains override_reason | unit | `pytest tests/test_profile_gating.py::TestBreakGlassGating -x` | Wave 0 |
| ACTG-04 | acme-bank engineer denies module/flink | unit | `pytest tests/test_profile_gating.py::TestCustomerDifferential -x` | Wave 0 |
| ACTG-04 | acme-bank engineer permits role/cp_audit | unit | `pytest tests/test_profile_gating.py::TestCustomerDifferential -x` | Wave 0 |

Existing test coverage (test_apply_engine.py, 27 tests) must remain green after all changes.

### Sampling Rate
- **Per task commit:** `pytest tests/test_apply_engine.py tests/test_profile_gating.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_profile_gating.py` — covers ACTG-01, ACTG-02, ACTG-03, ACTG-04
- [ ] `tools/profiles/tool_classification.json` — must exist before test_profile_gating.py can parametrize

*(Existing test infrastructure: pytest, conftest.py, monkeypatch patterns all present in test_apply_engine.py — reuse directly)*

---

## Open Questions

1. **Exact mcp-confluent tool names (Claude's Discretion)**
   - What we know: mcp-confluent is registered in `.mcp.json`; tools follow `confluent_<resource>_<action>` naming convention based on Confluent Cloud API resources
   - What's unclear: Whether the server exposes a tool list endpoint that can be queried without executing a real operation, or whether names must be enumerated from documentation
   - Recommendation: Use mcp-confluent documentation to enumerate tool names explicitly (per locked decision: no runtime introspection). Target >= 50 entries. Add `test_classification_covers_minimum_tools()` as a count gate.

2. **`check_tool_permitted()` vs. extended `check_profile_permits()`**
   - What we know: `check_profile_permits(profile, artifact_id)` operates on fsi-dsp artifact IDs; the new classification check operates on mcp-confluent tool names — these are different namespaces
   - What's unclear: Whether to add a second function or overload the existing one with type detection
   - Recommendation: Add a parallel `check_tool_permitted(profile_name, tool_name, customer=None)` function. Keep `check_profile_permits()` for artifact-ID checks (backward compat). Document the two-namespace distinction in code comments.

3. **acme-bank ADR for profile overrides**
   - What we know: `canon/customer/acme-bank/adrs/` has adr-001.md and adr-002.md (compression and latency overrides). The pattern requires an ADR for every override.
   - What's unclear: Whether adr-003.md should be created as part of this phase or whether the customer profiles directory alone is sufficient
   - Recommendation: Create adr-003.md documenting the Flink prohibition and cp_audit addition. Consistent with CANST-03 ("every override is an ADR in the layer that introduces it").

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `tools/apply_engine.py` — current `load_profile()`, `check_profile_permits()`, `emit_activity_log_apply()`, `write_incident_article()` signatures
- Direct code inspection: `tools/profiles/break-glass.json`, `engineer.json`, `read-only.json` — current profile structure
- Direct code inspection: `canon/stack.py` — `resolve_stack()` overlay resolution pattern used as model for `load_profile(customer=X)`
- Direct code inspection: `tests/test_apply_engine.py` — 27 existing tests, monkeypatch pattern, test class structure to mirror
- Direct code inspection: `.claude/commands/dsp-apply.md` — 9-step structure, Step 6 current confirmation, Step 7 stub comment referencing Phase 3C
- Direct code inspection: `.planning/STATE.md` — all accumulated decisions including Python 3.9 compat rule

### Secondary (MEDIUM confidence)
- `.planning/phases/03C-act-rail-profile-gating/03C-CONTEXT.md` — locked decisions and architecture choices from /gsd:discuss-phase

### Tertiary (LOW confidence)
- mcp-confluent tool naming convention inferred from `confluent_<resource>_<action>` pattern — not verified against live server enumeration

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already present; no new dependencies
- Architecture patterns: HIGH — direct extension of verified Phase 3b code; patterns extracted from existing implementation
- Pitfalls: HIGH — derived from actual code paths and Phase 3b decisions in STATE.md
- Tool classification names: MEDIUM — convention inferred; full list at Claude's Discretion during implementation

**Research date:** 2026-04-29
**Valid until:** 2026-07-29 (stable Python project; 90-day window)
