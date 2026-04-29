---
phase: 03C-act-rail-profile-gating
verified: 2026-04-29T17:00:00Z
status: passed
score: 10/10 must-haves verified
re_verification: false
---

# Phase 03C: Act Rail Profile Gating Verification Report

**Phase Goal:** Every mcp-confluent tool is explicitly classified into a profile by name, per-profile negative-space suites prove forbidden tools fail closed, break-glass requires two-step confirmation, and a customer fork demonstrates differential gating

**Verified:** 2026-04-29T17:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every mcp-confluent tool (50+) appears in tool_classification.json by exact name | VERIFIED | 81 tools present, all literal names, no wildcards |
| 2 | No tool uses regex or wildcard — all entries are literal tool names | VERIFIED | All 81 values are one of three literal tier strings |
| 3 | break-glass.json no longer contains wildcard `*` — replaced with explicit list | VERIFIED | `allowed_operations: ["module/topic","module/flink","role/cp_schema","role/cp_rbac","role/cp_connect","script/fsi-dr","scenario/cc-aws"]` |
| 4 | acme-bank engineer profile removes module/flink and adds role/cp_audit relative to base | VERIFIED | `canon/customer/acme-bank/profiles/engineer.json` confirmed |
| 5 | check_tool_permitted() denies unclassified tools with fail-closed behavior | VERIFIED | `unclassified_policy: "deny"`, function returns False for unknown tools |
| 6 | check_tool_permitted() uses tier hierarchy: read-only < engineer < break-glass | VERIFIED | `PROFILE_TIER_ORDER` constant + index comparison in apply_engine.py |
| 7 | load_profile() accepts optional customer param and checks customer overlay first | VERIFIED | keyword-only `customer` param, overlay-first path resolution wired |
| 8 | dsp-apply.md Step 6 has two-step break-glass branch | VERIFIED | "Step 6 Break-Glass Extension" with Interaction 1 + Interaction 2 present |
| 9 | Per-profile negative-space suites prove forbidden tools fail closed | VERIFIED | 255 parametrized tests, 6 test classes, all pass |
| 10 | override_reason logged to both activity log and incident article frontmatter | VERIFIED | `emit_activity_log_apply` and `write_incident_article` both accept/write `override_reason` |

**Score:** 10/10 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tools/profiles/tool_classification.json` | Tool-to-tier classification for all mcp-confluent tools | VERIFIED | 81 tools, 3 tiers, `unclassified_policy: "deny"` |
| `tools/profiles/break-glass.json` | Explicit tool enumeration, no wildcard | VERIFIED | Wildcard replaced; 7 explicit artifact IDs |
| `canon/customer/acme-bank/profiles/engineer.json` | Acme-bank differential engineer profile | VERIFIED | module/flink absent, role/cp_audit present, complete profile doc |
| `canon/customer/acme-bank/adrs/adr-003.md` | ADR documenting Flink prohibition + audit role | VERIFIED | Status: Accepted, Decision references both module/flink and role/cp_audit |
| `tools/apply_engine.py` | Classification-aware tool check, customer overlay, dual override logging | VERIFIED | All 6 new/extended functions present and wired |
| `.claude/commands/dsp-apply.md` | Two-step break-glass confirmation in Step 6 | VERIFIED | "BREAK-GLASS CONFIRMATION REQUIRED", "CONFIRM BREAK-GLASS", Interaction 1 + 2 |
| `tests/test_profile_gating.py` | Per-profile negative-space test suite | VERIFIED | 6 test classes, 255 tests, >= 80 lines (192 lines) |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tools/apply_engine.py::check_tool_permitted` | `tools/profiles/tool_classification.json` | `load_tool_classification()` JSON load + tier lookup | WIRED | Line 68: `classification = load_tool_classification()` |
| `tools/apply_engine.py::load_profile` | `canon/customer/*/profiles/*.json` | customer overlay path resolution | WIRED | Lines 112-115: `customer_profile.exists()` guard + load |
| `.claude/commands/dsp-apply.md` | `tools/apply_engine.py::emit_activity_log_apply` | `override_reason` parameter in Step 8 | WIRED | Step 8 explicitly documents `override_reason` param |
| `.claude/commands/dsp-apply.md` | `tools/apply_engine.py::write_incident_article` | `override_reason` parameter in Step 9 | WIRED | Step 9 explicitly documents `override_reason` param |
| `tests/test_profile_gating.py` | `tools/apply_engine.py::check_tool_permitted` | import + parametrized assertions | WIRED | Line 15-19: explicit import; all test classes call function |
| `tests/test_profile_gating.py` | `tools/profiles/tool_classification.json` | JSON load for parametrize lists | WIRED | Lines 22-24: module-level load feeds ALL_TOOLS etc. |
| `tests/test_profile_gating.py::TestCustomerDifferential` | `canon/customer/acme-bank/profiles/engineer.json` | `load_profile(customer="acme-bank")` | WIRED | Lines 166-192: 5 tests exercise acme-bank overlay |

---

### Data-Flow Trace (Level 4)

Not applicable — this phase produces data files (JSON classification tables, profile overlays, ADR markdown) and enforcement logic (Python functions, test suite). No dynamic rendering components. Data flows through function calls, which are verified by the test suite.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| tool_classification.json has 50+ tools | `python3 -c "import json; d=json.load(open('tools/profiles/tool_classification.json')); print(len(d['tools']))"` | 81 | PASS |
| Unclassified policy is deny | `python3 -c "import json; d=json.load(open('tools/profiles/tool_classification.json')); print(d['unclassified_policy'])"` | deny | PASS |
| break-glass has no wildcard | `python3 -c "import json; d=json.load(open('tools/profiles/break-glass.json')); print('*' not in d['allowed_operations'])"` | True | PASS |
| acme-bank differential correct | `python3 -c "import json; d=json.load(open('canon/customer/acme-bank/profiles/engineer.json')); print('module/flink' not in d['allowed_operations'], 'role/cp_audit' in d['allowed_operations'])"` | True True | PASS |
| Full gating test suite | `pytest tests/test_profile_gating.py -x -q` | 255 passed | PASS |
| Apply engine test suite | `pytest tests/test_apply_engine.py -x -q` | 40 passed | PASS |

---

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|-------------|---------------|-------------|--------|----------|
| ACTG-01 | 03C-01, 03C-02, 03C-03 | Every mcp-confluent tool (50+) classified into a profile by name, not regex | SATISFIED | 81 tools in tool_classification.json; `unclassified_policy: deny`; TestClassificationCoverage + TestUnclassifiedToolDenial |
| ACTG-02 | 03C-03 | Per-profile negative-space test suite ensures forbidden tools fail closed | SATISFIED | TestReadOnlyGating (44 forbidden), TestEngineerGating (20 forbidden), TestBreakGlassGating (81 permitted) — 255 total parametrized tests |
| ACTG-03 | 03C-02, 03C-03 | Break-glass profile requires two-step confirmation with explicit override reason logged | SATISFIED | dsp-apply.md Step 6 Break-Glass Extension (Interaction 1 + 2); `override_reason` on both `emit_activity_log_apply` and `write_incident_article`; `break-glass-reason-rejected` / `break-glass-cancelled` results |
| ACTG-04 | 03C-01, 03C-02, 03C-03 | >= 1 customer fork demonstrates differential profile gating relative to base | SATISFIED | `canon/customer/acme-bank/profiles/engineer.json` (module/flink removed, role/cp_audit added); ADR-003 documents rationale; TestCustomerDifferential (5 tests) |

All 4 requirements satisfied. No orphaned requirements found — all ACTG IDs in REQUIREMENTS.md are Phase 3c scope and accounted for across plans 01, 02, and 03.

---

### Anti-Patterns Found

| File | Pattern | Severity | Assessment |
|------|---------|----------|------------|
| `tools/apply_engine.py` line 152 | `execution_result = "deferred-to-mcp-runtime"` | Info | Intentional stub — Step 7 execution stub is pre-existing, documented in SUMMARY.md as intentional. MCP execution wiring is out of scope for this phase. Does not block any phase 03C goal. |

No blockers. No warnings. The deferred-to-mcp-runtime stub is a named, intentional deferral to future phase work, not a gap in 03C goal achievement.

---

### Human Verification Required

None. All phase 03C must-haves are verifiable programmatically:
- JSON files are structurally verifiable
- Python functions are test-covered (295 tests across two test files, all passing)
- dsp-apply.md command workflow is text-verifiable (break-glass keywords present and correctly structured)
- No UI, no real-time behavior, no external service integration in scope

---

### Gaps Summary

No gaps. All 10 observable truths verified. All 7 artifacts exist and are substantive. All 7 key links confirmed wired. All 4 requirements (ACTG-01 through ACTG-04) satisfied with direct implementation evidence.

The phase goal is fully achieved:
- **Classification:** 81 mcp-confluent tools explicitly classified by exact name into three tiers
- **Negative-space suites:** 255 parametrized tests prove forbidden tools fail closed across all profiles
- **Break-glass two-step:** Interaction 1 (reason collection) + Interaction 2 (confirmed display) in dsp-apply.md; override_reason logged to both activity log and incident article frontmatter
- **Customer fork:** acme-bank engineer overlay demonstrates differential gating (module/flink removed, role/cp_audit added), documented by ADR-003

---

_Verified: 2026-04-29T17:00:00Z_
_Verifier: Claude (gsd-verifier)_
