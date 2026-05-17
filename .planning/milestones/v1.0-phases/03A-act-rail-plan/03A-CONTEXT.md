# Phase 3a: Act Rail — Plan - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a read-only `/dsp:plan` skill that selects and validates fsi-dsp artifacts through a four-gate validation chain (canon compliance, fsi-dsp coverage, confluent-docs schema, mcp-confluent state). The skill never generates inline Terraform or invokes write tools. Structural correctness >= 95% measured by a golden harness with >= 20 cases. Canon-to-fsi-dsp parity CI blocks drift in both repos.

</domain>

<decisions>
## Implementation Decisions

### Skill Interface & Output Contract
- `/dsp:plan` accepts natural language request strings (e.g., "create a topic for trade events with DR") — consistent with /ask and /review input patterns
- Flags: `--overlay <name>` (reuse from /review for customer overlay resolution), `--dry-run` (default true, plan-only mode), `--gate-bypass <gate>` (dev mode — skip specific named gates per ACT-03)
- Output: Markdown plan document with sections (Selected Artifact, Arguments, Gate Results, Canon Compliance, Provenance Footer) written to `outputs/plans/<slug>-plan-<YYYY-MM-DD>.md`
- Unresolvable requests: Return structured "no matching artifact" response with suggested alternatives from MANIFEST.yaml — never generate inline Terraform (per Out of Scope constraint). Unresolvable requests may suggest a PR proposal to fsi-dsp.

### Four-Gate Architecture
- Gates execute sequentially in fail-fast order: gate 1 (canon compliance) failure skips gates 2-4, saves MCP round-trips, gives clear "fix this first" guidance
- Dev-mode bypass via `--gate-bypass <gate-name>` flag, requiring explicit gate name (not blanket skip-all) — satisfies ACT-03 individual testability and bypassability
- Each gate returns structured result dict: `{gate: str, status: pass|fail|skipped, detail: str, evidence: list}` — composable pipeline, each gate independently unit-testable
- Gate pipeline lives in `tools/act_gates.py` module with one function per gate + `run_gate_chain()` orchestrator — consistent with existing tools/ convention (review-to-docx.py)

### Terraform MCP & Parity CI
- Wire `hashicorp/terraform-mcp-server` (official HashiCorp Terraform MCP) into `.mcp.json` — provides plan/validate/state reads without requiring local Terraform install
- Canon-fsi-dsp parity checked by `tools/check-canon-parity.py` reading MANIFEST.yaml capabilities vs. canon defaults.yaml keys — runs in GitHub Actions CI for both repos
- Parity failure triggers bidirectional: fsi-dsp adds capability not covered by canon defaults, OR canon adds config key with no matching fsi-dsp artifact
- Gate 4 (mcp-confluent state) calls mcp-confluent to verify target cluster/environment exists and is accessible — confirms plan is actionable, not theoretical

### Claude's Discretion
- Internal gate implementation details (error messages, evidence format, timeout handling)
- Golden harness case selection and negative-space coverage design
- CI workflow YAML structure and trigger patterns

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `canon/stack.py` — resolve_stack(), active_layers(), provenance_footer() for canon compliance checking and provenance
- `tools/review-to-docx.py` — established pattern for tools/ module with CLI interface, provenance, and unit tests
- `raw/repos/fsi-dsp/MANIFEST.yaml` — stable ID registry for all fsi-dsp capabilities (9 Ansible roles, 2 Terraform modules)
- `canon/base/defaults.yaml` — base canon config values for compliance checking
- `canon/industry/fsi/overrides.yaml` — FSI overlay with latency tiers
- `canon/customer/acme-bank/overrides.yaml` — customer overlay for differential testing

### Established Patterns
- Skill files in `.claude/commands/` (ask.md, review.md) — flag parsing in Step 1, structured extraction, provenance footer
- Tools in `tools/` — Python CLI with argparse, importable functions for unit testing
- Golden harness in `tests/golden/` — case files with frontmatter, parametrized pytest runner
- Activity log emission to `wiki/activity/YYYY-MM.md` after every skill invocation

### Integration Points
- `.mcp.json` — add hashicorp/terraform-mcp-server alongside existing MCP servers
- `.claude/commands/` — new `dsp-plan.md` skill file
- `tools/` — new `act_gates.py` and `check-canon-parity.py`
- `tests/golden/act/` — new golden harness directory
- `.github/workflows/` — new parity CI workflow
- `wiki/activity/` — activity log entry per /dsp:plan invocation

</code_context>

<specifics>
## Specific Ideas

- Four gates in order: (1) canon compliance — does the request align with active canon config, (2) fsi-dsp coverage — does MANIFEST.yaml have an artifact that matches, (3) confluent-docs schema — does the artifact's Terraform/Ansible schema validate against current Confluent docs, (4) mcp-confluent state — is the target cluster/environment reachable and in expected state
- Gate chain is the core abstraction — all downstream phases (3b: apply, 3c: profile gating) compose on top of it
- Parity CI is bidirectional: neither repo can drift without the other noticing

</specifics>

<deferred>
## Deferred Ideas

- Policy profiles (read-only, engineer, break-glass) — Phase 3b concern
- Human confirmation gate for apply — Phase 3b concern
- Per-tool classification of mcp-confluent tools — Phase 3c concern
- Negative-space test suites for forbidden tools — Phase 3c concern

</deferred>
