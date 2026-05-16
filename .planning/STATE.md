---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: — Developer Persona + Quality Gates
status: Ready to execute
stopped_at: Completed H.1-02-PLAN.md (10 parent articles ingested via source attestation)
last_updated: "2026-05-16T16:07:46.389Z"
last_activity: 2026-05-16
progress:
  total_phases: 8
  completed_phases: 7
  total_plans: 27
  completed_plans: 26
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-16)

**Core value:** Canon overlay stack works — customers can fork and override safely
**Current focus:** Phase H.1 — Wiki ingest from confluent-agent-skills references

## Current Position

Milestone: v2.0
Phase: H.1 (Wiki ingest from confluent-agent-skills references) — EXECUTING
Plan: 3 of 3
Last activity: 2026-05-16

Progress: [░░░░░░░░░░] 0%

## v1.0 Reference

Shipped: 2026-05-16 — 9 phases, 26 plans, 44/44 requirements validated.
Archive: `.planning/milestones/v1.0-{ROADMAP,REQUIREMENTS,MILESTONE-AUDIT}.md`
Tag: `v1.0`

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 00-foundation P01 | 8 | 2 tasks | 6 files |
| Phase 00-foundation P02 | 8 | 2 tasks | 2 files |
| Phase 00-foundation P04 | 8 | 2 tasks | 3 files |
| Phase 00-foundation P03 | 172 | 2 tasks | 13 files |
| Phase 00-foundation P05 | 2 | 2 tasks | 14 files |
| Phase 00-foundation P06 | 10 | 3 tasks | 5 files |
| Phase 01-knowledge-skill P02 | 109 | 2 tasks | 3 files |
| Phase 01-knowledge-skill P01 | 3 | 2 tasks | 23 files |
| Phase 01-knowledge-skill P03 | 5 | 2 tasks | 36 files |
| Phase 02-review-skill P01 | 1 | 1 tasks | 1 files |
| Phase 02-review-skill P02 | 3 | 3 tasks | 6 files |
| Phase 02-review-skill P03 | 4 | 2 tasks | 27 files |
| Phase 03A-act-rail-plan P01 | 3 | 2 tasks | 3 files |
| Phase 03A-act-rail-plan P02 | 3 | 2 tasks | 5 files |
| Phase 03A-act-rail-plan P03 | 3 | 2 tasks | 24 files |
| Phase 03B-act-rail-apply P02 | 2 | 1 tasks | 1 files |
| Phase 03B-act-rail-apply P01 | 2 | 1 tasks | 5 files |
| Phase 03B-act-rail-apply P03 | 8 | 2 tasks | 11 files |
| Phase 03C-act-rail-profile-gating P01 | 8 | 2 tasks | 5 files |
| Phase 03C-act-rail-profile-gating P02 | 3 | 2 tasks | 3 files |
| Phase 03C-act-rail-profile-gating P03 | 31438793 | 1 tasks | 1 files |
| Phase G.2c P01 | 3 | 2 tasks | 3 files |
| Phase G.2c-tool-classification-rename P03 | 1 | 1 tasks | 1 files |
| Phase G.2c P02 | 4 | 2 tasks | 3 files |
| Phase H.1-wiki-ingest-agent-skills P01 | 4 | 3 tasks | 39 files |
| Phase H.1 P02 | 17 | 4 tasks | 13 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Canon overlay stack uses composition, not inheritance — customers override without forking
- Claude Code is the runtime host through Phase 3 (no custom server)
- fsi-dsp linked as submodule; MANIFEST.yaml is the stable contract between repos
- Phase exits are threshold-gated (golden harness), not date-driven
- [Phase 00-foundation]: pytest chosen as test runner for wiki tooling regression tests
- [Phase 00-foundation]: MANIFEST.yaml IDs embed type prefix to prevent cross-type collisions
- [Phase 00-foundation]: ADR-009 pre-registered as proposed in MANIFEST.yaml to unblock citation CI before authoring
- [Phase 00-foundation]: Activity log uses overlay-scoped fields (Overlay + Canon stack) for full audit context per WIKI-02
- [Phase 00-foundation]: ADR-009 status set to Accepted (not Proposed) — decision is already canonical in CLAUDE.md FSI overlay
- [Phase 00-foundation]: canon/stack.py uses Optional[List[str]] typing for Python 3.9 compatibility (not X|Y union syntax)
- [Phase 00-foundation]: Stack hash truncated to 16 hex chars from SHA-256 for compact provenance footers
- [Phase 00-foundation]: fsi-dsp:// URI scheme adopted as stable citation form — IDs survive fsi-dsp refactors per MANIFEST.yaml contract
- [Phase 00-foundation]: Citation test pattern: pytest classes with fixture-based wiki traversal for ongoing enforcement of citation hygiene
- [Phase 00-foundation]: fsi-dsp scripts committed inside submodule then parent pointer updated
- [Phase 00-foundation]: check-manifest-stability.py allows ID removal only on major version bump
- [Phase 01-knowledge-skill]: Triage classifier uses four routes (wiki-only/wiki+MCP/deep/refuse); --force-route bypasses classifier
- [Phase 01-knowledge-skill]: Mode flag governs write behavior only; MCP routing is route-driven via triage classifier
- [Phase 01-knowledge-skill]: Auto-stub fires on all modes including ephemeral — coverage gaps are never lost
- [Phase 01-knowledge-skill]: /wiki:recommend reduced to thin alias dispatching to /ask --mode reconsolidate
- [Phase 01-knowledge-skill]: last_validated field uses 2026-04-28 for all articles (Phase 0 review date); DECAY_DAYS=90 constant; check_decay falls back to last_updated if field absent
- [Phase 01-knowledge-skill]: apply_decay_fix scoped to front matter block via regex to prevent body text rewrites; --fix implies --full in wiki-lint.py
- [Phase 01-knowledge-skill]: 32 golden cases authored (exceeds 30 minimum) with TDD RED-GREEN discipline — test runner committed before cases
- [Phase 02-review-skill]: YAML claim block is mandatory before table rendering — reproducibility anchor for REVW-01 claim extraction determinism >= 95%
- [Phase 02-review-skill]: Multi-doc claim IDs use source-slug prefix (deck-1, runbook-2) to prevent ID collision on merge
- [Phase 02-review-skill]: Premise-challenge (Step 2.5) runs before wiki cross-reference so overlay conflicts inform validation pass
- [Phase 02-review-skill]: /review is always report mode — no ephemeral variant; every invocation writes a file and emits activity log
- [Phase 02-review-skill]: tools/__init__.py uses importlib to register review-to-docx.py as tools.review_to_docx — only clean solution for hyphenated module name without renaming the CLI entry point
- [Phase 02-review-skill]: Provenance footer implemented as final paragraph in body flow (not Word native footer frame) — simpler, visible in body text, matches review.md Step 6 report format
- [Phase 02-review-skill]: acme-bank overlay selects zstd and sub-100-microsecond as differentials — produce verdict changes on the most common review claims (compression recommendation, latency SLA adequacy)
- [Phase 02-review-skill]: Golden review harness mirrors ask harness exactly: load_case, ALL_CASES glob, parametrize, REQUIRED_FIELDS — consistent pattern across both skill harnesses
- [Phase 02-review-skill]: overlay=null in YAML front matter is explicit null value — load_case().get('overlay') returns None, not KeyError — consistent with optional field convention
- [Phase 03A-act-rail-plan]: Gate 2 prefers terraform-module over ansible-role when create/provision verb detected in request
- [Phase 03A-act-rail-plan]: Gates 3 and 4 are stubs returning pass — MCP connectivity required for real validation; unit tests verify structure only
- [Phase 03A-act-rail-plan]: Violation pattern matching uses explicit lowercase string patterns (not regex or NLP) for determinism
- [Phase 03A-act-rail-plan]: /dsp:plan Rules section enforces ACT-06 read-only: NEVER generate inline Terraform or invoke mcp-confluent write tools
- [Phase 03A-act-rail-plan]: MODULE_TO_CANON_KEY is explicit (not heuristic) — each new terraform-module requires a conscious canon key assignment; unknown modules produce blocking DRIFT-1 violations
- [Phase 03A-act-rail-plan]: Canon parity CI covers both repos via submodule pointer: raw/repos/fsi-dsp/** path catches fsi-dsp MANIFEST changes without duplicating the workflow in fsi-dsp
- [Phase 03A-act-rail-plan]: Golden act harness mirrors ask/review harness pattern exactly: load_case, ALL_CASES glob, parametrize, REQUIRED_FIELDS for consistency across all skill harnesses
- [Phase 03A-act-rail-plan]: REQUIRED_FIELDS for act cases: 8 fields (id, request, expected_artifact, floor_model, tags, required_claims, forbidden_claims, negative_space) capturing the act rail's unique concerns
- [Phase 03A-act-rail-plan]: Negative-space cases enforce ACT-06 at structural level: forbidden_claims must contain 'resource "confluent_' — catches core hand-rolled Terraform violation in every negative-space case
- [Phase 03B-act-rail-apply]: gate-bypass excluded from apply skill; unconditional gate re-run at apply time catches state drift
- [Phase 03B-act-rail-apply]: Step 7 stub emits deferred-to-mcp-runtime; real MCP execution wired in Phase 3c per-tool classification
- [Phase 03B-act-rail-apply]: Bypass refusal pattern covers 'apply immediately' / 'skip confirmation' / 'just do it' vectors with activity log entry per ACTA-02
- [Phase 03B-act-rail-apply]: VALID_PROFILES explicit set (not filesystem scan) — unknown names fail immediately, fail-closed enforcement before any gate chain runs
- [Phase 03B-act-rail-apply]: Wildcard '*' in break-glass allowed_operations covers Phase 3b scope; per-tool enumeration deferred to Phase 3c for mcp-confluent tool classification
- [Phase 03B-act-rail-apply]: Activity log uses 11-field schema for /dsp:apply entries matching ACTA-04: operator, profile, confirmation_status, execution_result, duration_seconds plus overlay, artifact, plan, gates, canon_stack, skill
- [Phase 03B-act-rail-apply]: Incident articles use YAML frontmatter (7 keys: artifact, operator, profile, outcome, canon_hash, plan_ref, timestamp) + 4 sections (What Changed, Why, Gate Results, Provenance)
- [Phase 03B-act-rail-apply]: Apply negative-space cases include 'no matching artifact' in required_claims for consistency with plan harness pattern
- [Phase 03B-act-rail-apply]: APPLY_CASES filtered from ALL_CASES by skill field — no separate glob, single source of truth
- [Phase 03B-act-rail-apply]: test_apply_case_has_valid_profile skips validation for negative-space cases to allow unknown profile rejection tests
- [Phase 03C-act-rail-profile-gating]: 81 mcp-confluent tools explicitly classified into three tiers by exact name; unclassified_policy=deny for fail-closed enforcement
- [Phase 03C-act-rail-profile-gating]: break-glass wildcard replaced with explicit artifact operation list; acme-bank engineer overlay is complete profile doc (not partial diff)
- [Phase 03C-act-rail-profile-gating]: check_tool_permitted() is parallel to check_profile_permits() — separate namespaces: MCP tool names vs fsi-dsp artifact IDs
- [Phase 03C-act-rail-profile-gating]: customer param on load_profile() is keyword-only per RESEARCH.md Pitfall 2 — existing positional callers unaffected
- [Phase 03C-act-rail-profile-gating]: override_reason Optional[str]=None — backward compatible; None means omit the field from log/frontmatter
- [Phase 03C-act-rail-profile-gating]: Tool lists loaded from classification JSON at module level so parametrize lists are self-updating when classification table grows
- [Phase G.2c]: regenerate_tool_classification.py is the single source of truth for tool_classification.json — JSON is downstream artifact of Python, never hand-edited
- [Phase G.2c]: D-05 verb-prefix rule encoded as Python tables (READ_ONLY_PREFIXES/ENGINEER_PREFIXES/BREAK_GLASS_PREFIXES) + OVERRIDES dict; classify_tier() raises ValueError on unknown shapes per D-06 so CI blocks bump PRs until human classifies new tools
- [Phase G.2c]: tier_rule stored as top-level JSON string field (JSON has no comments — workaround for D-05's 'comment block at the top' literal language; semantic intent preserved)
- [Phase G.2c]: tool_classification.json deliberately unchanged in plan 01 — big-bang rewrite is G.2c-02's job; keeps the rewrite diff small and reviewable separately from generator review
- [Phase G.2c]: Generator dry-run mode added under D-05 Claude's Discretion: uses static fixture under tests/fixtures/ instead of npm-installing — enables offline unit tests in under 0.1s without network or Node.js
- [Phase G.2c-tool-classification-rename]: tool-classification-drift workflow uses Node 22 (matches .mcp.json runtime) + Python 3.12 (matches existing CI workflows) + path-scoped triggers + dual PR+push:main triggers per D-07
- [Phase G.2c-tool-classification-rename]: Defensive 'npm --version' step in CI surfaces PATH issues as a clear error rather than a cryptic FileNotFoundError deep in the generator's subprocess.run stack
- [Phase G.2c]: Live mcp-confluent 1.3.0 registry has 54 tools (4 beyond CONTEXT.md's anticipated 50); proceeded with 54 as canonical — matches-the-live-registry truth outranks the snapshot count
- [Phase G.2c]: explain-disabled-tools classified as read-only via OVERRIDES — no verb-prefix match in D-05; semantically a describe/get metadata tool with no state mutation or data-plane exposure
- [Phase G.2c]: regenerate_tool_classification.py uses npm --ignore-scripts — postinstall native build of @confluentinc/kafka-javascript was the only failure mode; the tool-name.js file we parse is plain pre-built JS unaffected by the binary; keeps generator portable to clean CI runners
- [Phase G.2c]: Test Replacements D/E use delete-schema (not delete-topics) to preserve the original test's cross-resource-family semantic — break-glass-tier delete on a non-topics resource, per the plan's explicit rationale
- [Phase H.1]: Trip-wire entries citing evals.json use source_url: also-cite. (period) to keep YAML well-formed; evals.json is not vendored per D-02, so path field is SKILL.md sibling
- [Phase H.1]: Extra non-scaffold reference files (rest-api.md, multi-event-guide.md, python source files, sample schemas) preserved in vendor tree — plan's anti-references list only named 7 scaffolds; unlisted extras stayed for H.1-02/H.1-03 to evaluate
- [Phase H.1]: tools/vendor-sources.json kind field is free-form string (not enum) so future vendor kinds (claude-plugin in H.3b, terraform-module, etc.) slot in without schema migration
- [Phase H.1]: Three-way merge for cdc-source-connector-setup ordered as pre-deploy → deploy → debug (database-prerequisites → connector-configs → troubleshooting); mirrors operational reading order
- [Phase H.1]: All wiki YAML tag arrays use comma-separated flow sequence (tags: [a, b, c]) per the schema-registry-best-practices.md convention; verified via yaml.safe_load on every new article
- [Phase H.1]: Added 3 inbound graph edges for patterns/kafka-streams-topology-patterns to satisfy the ≥1-inbound rule (the plan's specified _graph block left it with 0 inbound)

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-05-16T16:07:46.387Z
Stopped at: Completed H.1-02-PLAN.md (10 parent articles ingested via source attestation)
Resume file: None
