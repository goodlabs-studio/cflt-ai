# Phase 3c: Act Rail — Profile Gating - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Classify every mcp-confluent tool (50+) into profile tiers by explicit name. Per-profile negative-space test suites prove forbidden tools fail closed. Break-glass profile requires two-step confirmation (reason first, then confirm) with override reason logged. At least one customer fork (acme-bank) demonstrates differential profile gating relative to base.

</domain>

<decisions>
## Implementation Decisions

### Tool Classification Architecture
- Classification table lives in `tools/profiles/tool_classification.json` — single JSON file mapping every mcp-confluent tool name to its profile tier, loaded by apply_engine
- Tool list hardcoded from current mcp-confluent docs — explicit by-name per ACTG-01, no runtime introspection
- Fail-closed: unclassified tools denied by all profiles, logged as "unclassified_tool" — consistent with Phase 3b VALID_PROFILES fail-closed pattern
- Replace break-glass wildcard with explicit tool enumeration; engineer and read-only list allowed tools by name — satisfies ACTG-01 "by name, not regex"

### Break-Glass Two-Step Confirmation
- Step 1: "Provide override reason" (free-text) — forces deliberation before commit point
- Step 2: "CONFIRM BREAK-GLASS: <artifact> with reason: <reason>?" — shows artifact + reason for final confirmation
- Override reason logged to both activity log (override_reason field) AND incident article frontmatter — dual logging per ACTG-03
- No session timeout — each invocation requires its own two-step confirmation; session-level activation is a v2 concern

### Customer Fork & Differential Gating
- Customer overlay directory `canon/customer/<name>/profiles/` overrides base profiles — follows existing canon overlay composition pattern
- Demo customer: acme-bank (existing overlay in `canon/customer/acme-bank/`)
- Differential: acme-bank engineer profile removes "module/flink" (bank prohibits self-service Flink) and adds "role/cp_audit" (bank requires audit role management)
- `load_profile()` gains optional `customer` param; checks customer overlay first, falls back to base — consistent with canon/stack.py resolution

### Negative-Space Test Architecture
- Single parametrized test file `tests/test_profile_gating.py` with per-profile test classes (TestReadOnlyGating, TestEngineerGating, TestBreakGlassGating)
- Structural tests: `check_profile_permits(profile, tool_name)` assertions — unit-level enforcement, no MCP mocking needed
- Full matrix: every tool × every profile via parametrize — ACTG-02 says "forbidden tools fail closed", not "some"
- Customer differential test: load acme-bank engineer, verify "module/flink" denied AND "role/cp_audit" permitted

### Claude's Discretion
- Exact mcp-confluent tool names and tier assignments (based on current documentation)
- Classification JSON schema details (field names, tier values)
- Error message wording for unclassified tool denials
- Break-glass prompt exact wording and formatting

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/apply_engine.py` — load_profile(), check_profile_permits(), emit_activity_log_apply(), write_incident_article() from Phase 3b
- `tools/profiles/read-only.json`, `engineer.json`, `break-glass.json` — existing profile structure to extend
- `tools/act_gates.py` — gate chain with run_gate_chain() orchestrator
- `.claude/commands/dsp-apply.md` — 9-step skill file referencing apply_engine functions
- `canon/customer/acme-bank/overrides.yaml` — existing customer overlay pattern
- `tests/test_apply_engine.py` — 27 unit tests across 6 test classes for apply engine

### Established Patterns
- VALID_PROFILES explicit set in apply_engine.py — fail-closed on unknown names
- check_profile_permits() checks allowed_operations list: "*" permits all, empty denies all, exact match otherwise
- Canon overlay resolution: base → industry → customer → engagement (canon/stack.py)
- Golden harness parametrized testing pattern (tests/golden/)
- Activity log 11-field schema for /dsp:apply entries

### Integration Points
- `tools/profiles/tool_classification.json` — new file: tool-to-tier mapping
- `tools/apply_engine.py` — extend: customer overlay resolution, two-step break-glass, classification-based enforcement
- `tools/profiles/` — update: replace wildcard with enumerated tools in break-glass.json
- `canon/customer/acme-bank/profiles/` — new directory: customer profile overrides
- `tests/test_profile_gating.py` — new file: per-profile negative-space suites
- `.claude/commands/dsp-apply.md` — update: break-glass two-step confirmation in Step 6

</code_context>

<specifics>
## Specific Ideas

- The classification table is the single source of truth for which tools each profile can access
- check_profile_permits() evolves from simple list check to classification-table-aware lookup
- Break-glass two-step is an enhancement to the existing Step 6 confirmation in dsp-apply.md
- Customer fork follows the same overlay pattern as canon config (acme-bank already has overrides.yaml)

</specifics>

<deferred>
## Deferred Ideas

- Session-level break-glass activation (approve once, apply multiple tools in window) — v2 concern
- Runtime tool discovery via MCP introspection — current approach is explicit hardcoded classification
- Profile tier beyond three (e.g., "auditor" tier for compliance-only operations) — not in v1 scope
- Automatic profile recommendation based on artifact type — future intelligence layer

</deferred>
