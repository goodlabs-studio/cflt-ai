# Phase 3b: Act Rail — Apply - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the `/dsp:apply` skill that executes planned infrastructure changes through fsi-dsp artifacts with mandatory human confirmation, three policy profiles enforcing least-privilege (read-only, engineer, break-glass), and full provenance logging. Every apply creates a wiki incident entry. Structural correctness holds at >= 95%.

</domain>

<decisions>
## Implementation Decisions

### Human Confirmation & Bypass Prevention
- /dsp:apply uses AskUserQuestion with explicit "CONFIRM APPLY" option for human confirmation — consistent with Claude Code UX and checkpoint patterns
- Before confirmation, show full plan summary: artifact ID, arguments, gate results, target environment, active policy profile
- On rejection: log rejection to activity log with reason, return to prompt without executing — rejection is a valid audit event
- Bypass testing covers 3 vectors: (a) direct MCP tool call without confirmation step, (b) crafted prompt injection attempting to skip confirmation, (c) missing profile flag — covers realistic attack surface per ACTA-02

### Policy Profile Architecture
- Profile files live in `tools/profiles/read-only.json`, `engineer.json`, `break-glass.json` — colocated with act rail tooling
- Active profile selected via `--profile <name>` flag on /dsp:apply, defaults to `read-only` — explicit per-invocation, fail-safe default
- Three tiers: read-only (plan + inspect only), engineer (plan + apply standard modules), break-glass (all including destructive ops)
- Fail closed: profile loads at skill start; unrecognized tool/operation returns error + logs attempt — never silently degrades to permissive mode

### Activity Log, Provenance & Wiki Incidents
- Apply uses same `wiki/activity/YYYY-MM.md` log as plan — single audit trail, entries distinguished by `**Skill:** /dsp:apply`
- Apply entries add fields beyond plan: operator, profile, confirmation_status, execution_result, duration_seconds — full provenance schema per ACTA-04
- Wiki incident entry is a new article in `wiki/incidents/<slug>-<YYYY-MM-DD>.md` with frontmatter (artifact, operator, profile, outcome, canon hash) — each apply creates a trackable incident per ACTA-05
- Incident article structure: frontmatter + sections (What Changed, Why with link to plan, Gate Results, Provenance) — mirrors plan output with execution outcome

### Claude's Discretion
- Internal implementation details of profile enforcement logic
- Exact error messages for bypass attempts and profile violations
- Incident article frontmatter field names and values
- Test case selection for structural correctness validation

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/act_gates.py` — four-gate validation chain with `run_gate_chain()` orchestrator (from Phase 3a)
- `.claude/commands/dsp-plan.md` — /dsp:plan skill with 6-step structure, flag parsing, gate chain invocation (pattern to mirror for /dsp:apply)
- `canon/stack.py` — `resolve_stack()`, `active_layers()`, `provenance_footer()` for provenance
- `raw/repos/fsi-dsp/MANIFEST.yaml` — artifact registry for capability resolution
- `tools/check-canon-parity.py` — parity checker with CI workflow (from Phase 3a)
- `wiki/activity/2026-04.md` — existing activity log format to extend

### Established Patterns
- Skill files in `.claude/commands/` — flag parsing in Step 1, structured extraction, provenance footer
- Tools in `tools/` — Python CLI with argparse, importable functions for unit testing
- Golden harness in `tests/golden/` — case files with frontmatter, parametrized pytest runner
- Activity log emission to `wiki/activity/YYYY-MM.md` after every skill invocation
- Gate chain returns structured result dicts: `{gate, status, detail, evidence}`

### Integration Points
- `.claude/commands/dsp-apply.md` — new skill file (mirrors dsp-plan.md structure)
- `tools/profiles/` — new directory for policy profile JSON files
- `tools/apply_engine.py` — new module for apply execution logic with profile enforcement
- `wiki/incidents/` — new directory for incident articles
- `wiki/activity/YYYY-MM.md` — extend existing log format with apply-specific fields
- `tests/golden/act/` — extend with apply-specific test cases or `tests/golden/apply/`

</code_context>

<specifics>
## Specific Ideas

- /dsp:apply consumes a plan file produced by /dsp:plan — the plan is the input, not a raw natural language request
- The gate chain from Phase 3a runs again at apply time (not just plan time) to catch state drift between plan and apply
- Profile enforcement happens before gate chain — wrong profile blocks execution before any MCP calls
- Break-glass profile (Phase 3c concern for per-tool classification, but the file structure ships here)

</specifics>

<deferred>
## Deferred Ideas

- Per-tool classification of mcp-confluent tools into profiles — Phase 3c concern
- Negative-space test suites for forbidden tools per profile — Phase 3c concern
- Break-glass two-step confirmation with override logging — Phase 3c concern
- Customer fork with differential profile gating — Phase 3c concern

</deferred>
