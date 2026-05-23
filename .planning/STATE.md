---
gsd_state_version: 1.0
milestone: v2.1
milestone_name: — LinuxONE Accelerator Integration
status: executing
stopped_at: Completed 12-01-PLAN.md
last_updated: "2026-05-23T17:57:31.460Z"
last_activity: 2026-05-23
progress:
  total_phases: 4
  completed_phases: 3
  total_plans: 13
  completed_plans: 11
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-23)

**Core value:** Canon overlay stack works — customers can fork and override safely
**Current focus:** Phase 12 — wiki-ingest-of-linuxone-accelerator

## Current Position

Phase: 12 (wiki-ingest-of-linuxone-accelerator) — EXECUTING
Plan: 2 of 4
Status: Ready to execute
Last activity: 2026-05-23

Progress: [░░░░░░░░░░] 0%  (0/4 phases complete)

## v2.1 Reference

Active milestone — 4 phases planned, 13 requirements mapped.
Roadmap: `.planning/ROADMAP.md` (v2.1 section)
Requirements: `.planning/REQUIREMENTS.md` (13/13 mapped across 9–12)

**Phase sequence:** 9 (submodule) → 10 (type contract) → 11 (act rail dispatch) → 12 (wiki ingest).

## v2.0 Reference

Shipped: 2026-05-17 — 8 phases, 13 plans, 16/16 requirements validated.
Archive: `.planning/milestones/v2.0-{ROADMAP,REQUIREMENTS,MILESTONE-AUDIT}.md`
Tag: `v2.0`

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
| Phase H.1 P03 | 10 | 4 tasks | 13 files |
| Phase H.2 P01 | 6 | 2 tasks | 4 files |
| Phase H.2 P02 | 3 | 2 tasks | 4 files |
| Phase H.2 P03 | 3min | 3 tasks | 3 files |
| Phase H.2-eval-harness-extension P04 | 2min | 2 tasks | 1 files |
| Phase H.3a P01 | 8min | 5 tasks | 6 files |
| Phase H.4a-profile-family-schema-extension P01 | 4min | 5 tasks | 7 files |
| Phase H.4b-developer-sandbox-profile-fsi-dev-canon P01 | 18min | 6 tasks | 7 files |
| Phase H.4c-acme-bank-developer-overlay P01 | 3min | 3 tasks | 4 files |
| Phase H.3b-version-pin-ci-drift-gate P01 | 10m | 5 tasks | 4 files |
| Phase H.3c-dsp-scaffold-wrapper P01 | 6m | 6 tasks | 6 files |
| Phase 09-submodule-sync-canon-parity-unblock P01 | 4min | 3 tasks | 2 files |
| Phase 09-submodule-sync-canon-parity-unblock P02 | 4min | 3 tasks | 3 files |
| Phase 10-accelerator-artifact-type-registration P01 | 3min | 1 tasks | 1 files |
| Phase 10-accelerator-artifact-type-registration P02 | 4min | 3 tasks | 7 files |
| Phase 11 P01 | 6min | 2 tasks | 3 files |
| Phase 11 P02 | 7min | 2 tasks | 2 files |
| Phase 11 P03 | 5min | 2 tasks | 7 files |
| Phase 11 P04 | 3 min | 2 tasks | 4 files |
| Phase 12-wiki-ingest-of-linuxone-accelerator P02 | 4min | 2 tasks | 3 files |
| Phase 12 P01 | 25min | 2 tasks | 9 files |

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
- [Phase H.1]: [Phase H.1] tools/wiki-lint.py extended with passive vendor-source drift detection per D-09 (check_vendor_drift reads source: from frontmatter, compares against tools/vendor-sources.json pin; emits DRIFT/MALFORMED/UNKNOWN-VENDOR findings without failing the lint run)
- [Phase H.1]: [Phase H.1] WarpStream trip-wires (#7/#8/#9) retain confidence: high because majority of claims are sourced from upstream confluent-maintained competitive guidance; ⚠️ unverified inline markers cover the minority (endpoint shapes, exact throughput-delta percentages) where context7 has limited published coverage
- [Phase H.1]: [Phase H.1] Trip-wire #5 (Avro src dir) generalized from upstream's Gradle-plugin language to cover BOTH Gradle Avro plugin AND Apache Maven Avro plugin — both default sourceDirectory to src/main/avro/
- [Phase H.1]: [Phase H.1] wiki-lint drift findings stay non-fatal (exit 0) per D-09 passive posture; surface for routine /wiki:validate review, do not block CI
- [Phase H.2]: Combined required_claims + required_report_sections into expectations[] positive; combined forbidden_claims + forbidden_content into NOT-prefixed expectations[] negative — single _collect_expectations() helper covers all three MD harness shapes (/ask, /review, /act)
- [Phase H.2]: Positional EvalCase construction in adapters — avoids model= substring collision with floor_model= kwarg in the D-04 lock grep; field-order discipline asserted by test_eval_case_namedtuple_fields as a public contract
- [Phase H.2]: Fixture named sample_evals.json (NOT evals.json) to stay off the runner's tests/evals/*/evals.json glob; test_real_runner_does_not_pick_up_fixture asserts this isolation belt-and-suspenders
- [Phase H.2]: test_all_seven_new_skills_discovered intentionally fails RED in Plan 01 — closure trigger for Plans 02 and 03 (goes GREEN automatically when those plans author the 7 evals.json files)
- [Phase H.2-eval-harness-extension]: [H.2-02] Trip-wire strings (D-08 #5 avro and #8 warpstream) copied verbatim into /wiki:ingest evals.json at ids 2 and 3; backticks preserved unescaped (JSON permits)
- [Phase H.2-eval-harness-extension]: [H.2-02] 40 wiki-skill cases drawn from real signals (raw/_ingest.md Processed entries, wiki/_queue.md Stubs, tools/wiki-lint.py logic, Phase 01/02 STATE decisions) — zero synthetic fixtures
- [Phase H.2]: H.2-03: Boilerplate prompt+expectations across case_ref wrapper cases — discriminating power comes from the referenced MD case, not the JSON wrapper
- [Phase H.2]: H.2-03: 7 H.1 trip-wire strings encoded bytewise-verbatim (em-dashes U+2014 preserved) — runner uses these as grep targets per D-04 structural-only
- [Phase H.2]: H.2-03: Combined with H.2-02, test_all_seven_new_skills_discovered transitioned RED→GREEN — all 7 named skills now have evals.json coverage at the 10-case floor (EVAL-02 satisfied)
- [Phase H.2-eval-harness-extension]: Three pytest invocations split into distinct workflow steps (runner / adapters / golden) — failure-attribution in the GitHub UI is worth the marginal YAML
- [Phase H.2-eval-harness-extension]: Threshold enforcement inside pytest (test_threshold_per_skill assertion), NOT as a separate workflow gate — D-06 lives in one tested code path
- [Phase H.2-eval-harness-extension]: Zero secrets, zero model SDKs in CI — D-04 structural-only enforced architecturally in the runner and visible structurally in the workflow shape
- [Phase H.3a]: wiki/_graph.md uses line-based 'source → target : relation' format throughout — H.3a overlay graph block added in this convention (not the ### block format described in plan task spec) per Rule 3 deviation; reformatting the existing 360-line graph was out of scope
- [Phase H.3a]: Dual-source attestation for canon-overlay rows: 'Upstream Default' column cites SKILL.md path:line; 'Canon Source' column cites CLAUDE.md §; FSI Override is the documented delta — eliminates need for MCP cross-check on canon-grounded claims
- [Phase H.3a]: Inbound graph edges selected by cross-reference density: fsi-governance-automation (15), fsi-exactly-once (12), topic-naming (12) — picked top 3 for maximum SA-traversal discoverability
- [Phase H.3a]: Canon-overlay article frontmatter uses free-form 'source: streaming-skills-plugin@1.0.0' field per D-10; wiki-lint UNKNOWN VENDOR finding is expected — H.3b formalizes the pin in tools/vendor-plugins.json and the finding will clear
- [Phase H.4a-profile-family-schema-extension]: Profile-family branching landed at apply_engine.check_tool_permitted() entry — operator branch byte-identical to v1.0 (proven via 162-decision snapshot); developer branch reads tool_overrides map (proven via test-dev-fixture); pure-Python validation, no jsonschema dep
- [Phase H.4a-profile-family-schema-extension]: Back-compat default: load_profile() injects family=operator when absent + stderr-notes the legacy shape; lets acme-bank customer-overlay engineer.json (no family field) keep working unchanged until H.4c explicitly adds the field
- [Phase H.4a-profile-family-schema-extension]: Snapshot pattern: tests/snapshots/h4a_operator_permits.json captures all 3×54=162 operator-branch permit decisions; regenerator one-liner lives in test docstring so it travels with the test; future tool_classification.json shifts force a visible-diff PR
- [Phase H.4b-developer-sandbox-profile-fsi-dev-canon]: Substituted 4 D-01 tool names to match tool_classification reality (describe-* → get-/read-/list-/search- equivalents); preserved 15 tool_overrides count
- [Phase H.4b-developer-sandbox-profile-fsi-dev-canon]: _layer_order_for(family, canon_layer) helper extracted from LAYER_ORDER constant; module-level LAYER_ORDER retained as operator default for back-compat
- [Phase H.4b-developer-sandbox-profile-fsi-dev-canon]: Customer-overlay branch in load_profile() routes via _profile_path so H.4c acme-bank developer/sandbox.json works without further engine plumbing
- [Phase H.4c-acme-bank-developer-overlay]: Customer overlay is a complete profile (D-01) — load_profile returns the overlay file directly when customer=acme-bank; customer_overrides field is documentation/audit only
- [Phase H.4c-acme-bank-developer-overlay]: Three differential signals (D-02) — 2 tool-level (delete-topics, alter-topic-config removed) + 1 skill-level (dsp-plan blocked) — robust against future base-canon shifts
- [Phase H.4c-acme-bank-developer-overlay]: Zero engine changes (D-04) — H.4b's _profile_path + customer branch already handles slash-separated profile names for customer-overlay lookup
- [Phase H.4c-acme-bank-developer-overlay]: ADR-004 ships as Accepted stub (D-05) cross-referencing adr-003 — formal ADR promotion deferred until first acme engagement validates the dev overlay in practice
- [Phase H.3b-version-pin-ci-drift-gate]: Pinned streaming-skills-plugin at commit 91d1871e; CI drift gate via git ls-remote (no Node.js, no API auth) mirrors G.2c pattern
- [Phase H.3c-dsp-scaffold-wrapper]: Three-gate sequence (skill-blocklist → read-only → cross-family) ordered for activity-log granularity; gate-1 fires first because skill_blocklist is the explicit profile intent, gate-2 is belt-and-suspenders for legacy operator profiles without blocklist field
- [Phase H.3c-dsp-scaffold-wrapper]: Producer stub generator reads resolved canon dict (acks/compression/idempotence/sr-format/auth) — proves end-to-end canon-stack wiring without invoking the upstream skill's interactive HARD-GATE flow
- [Phase H.3c-dsp-scaffold-wrapper]: Activity-log entries are written on every invocation (success, blocked, not-implemented) — audit-trail completeness outranks log silence; matches ACTA-04 schema
- [Phase H.3c-dsp-scaffold-wrapper]: _safe_relative() helper added so provenance.scaffold_dir is always populated even when OUTPUT_ROOT is monkeypatched outside PROJECT_ROOT (test isolation); production paths still emit repo-relative string
- [Phase 09-submodule-sync-canon-parity-unblock]: Atomic commit pattern: submodule bump + dependent test fix in ONE commit (easier to revert if downstream regressions surface)
- [Phase 09-submodule-sync-canon-parity-unblock]: No tools/check-canon-parity.py edit needed — DRIFT-1 violation resolved purely by submodule bump (module/cc-cluster-basic never reached upstream main)
- [Phase 09-submodule-sync-canon-parity-unblock]: Explicit fetch+checkout origin/main over git submodule update --remote (.gitmodules has no branch= field, --remote would no-op or chase wrong branch)
- [Phase 09-submodule-sync-canon-parity-unblock]: Pre-existing test_wiki_citations failure (6 observability articles use raw paths in sources:) deferred — confirmed not caused by Phase 09 via git stash repro on pre-bump tree; logged to deferred-items.md
- [Phase 09-submodule-sync-canon-parity-unblock]: Mirror H.3b shape exactly (not G.2c) for submodule drift gate: pure Python + git ls-remote, no Node.js, no API auth
- [Phase 09-submodule-sync-canon-parity-unblock]: Comparison axis: SHA-match early-return → timestamp-delta fallback; pure SHA equality (H.3b's check) would falsely report drift on any upstream advance within window
- [Phase 09-submodule-sync-canon-parity-unblock]: 14-day drift window (DRIFT_WINDOW_DAYS=14) — absorbs normal review-and-merge cycle on upstream main; narrow enough to catch silent rot before downstream v2.1 phases regress
- [Phase 09-submodule-sync-canon-parity-unblock]: Fail-closed on transient errors (EXIT_TRANSIENT_ERR=3) — ls-remote failure / timestamp-unresolvable never treated as 'no drift'; auto-fetch deliberately avoided (would hide drift behind side effect)
- [Phase 10-accelerator-artifact-type-registration]: type: accelerator schema landed verbatim from CONTEXT.md decisions (apply_sequence + per-layer canon_key + 3 explicit build/dry-run/apply commands); per-layer canon_key co-located in MANIFEST is the single source of truth (Phase 11 MODULE_TO_CANON_KEY derives FROM this, not declared independently — G.2c cleanup lesson)
- [Phase 10-accelerator-artifact-type-registration]: fsi-dsp/CLAUDE.md NOT edited — auto-generated file, schema docs land in cflt-ai's CONTRIBUTING.md / tools/manifest-schema.md (10-02 Task 4) and upstream PR body (10-03) instead
- [Phase 10-accelerator-artifact-type-registration]: Submodule parent-pointer bump deliberately left unstaged in this plan — 10-02 picks it up atomically alongside the validator commit (single rollback unit if Phase 11 surfaces issues)
- [Phase 10-accelerator-artifact-type-registration]: Pure-Python validator (no jsonschema/pydantic) — matches tools/check-canon-parity.py + tools/check_submodule_drift.py shape; KNOWN_TYPES locked via test_known_types_constant_shape for lock-step doc/code drift discipline
- [Phase 10-accelerator-artifact-type-registration]: Schema-shape vs path-existence kept orthogonal — validate_capability() skips path-on-disk check; that's TestManifestPathsExist's job; lets validator run as fast pre-commit gate without submodule checkout
- [Phase 10-accelerator-artifact-type-registration]: Atomic commit ad2304f bundles submodule pointer + validator + tests + fixtures + docs — single git revert returns repo to pre-MAN-01 baseline; mirrors Phase 9 atomic-landing discipline
- [Phase 10-accelerator-artifact-type-registration]: 9-test coverage matrix for new type (2 positive + 4 negative-space + 1 cross-type regression + 1 enum-gate + 1 constant-shape lock) — reusable template for future type additions
- [Phase 11]: [Phase 11-act-rail-wiring-for-accelerator-dispatch]: fsi.* canon keys placed in canon/industry/fsi/overrides.yaml (not defaults.yaml) — base canon stays vendor-neutral; check_parity unions both via new fsi_overrides_path arg
- [Phase 11]: [Phase 11-act-rail-wiring-for-accelerator-dispatch]: Composite-key shape '<artifact-id>:<layer-name>' (flat string, no nested dict) — keeps MODULE_TO_CANON_KEY walker grep-friendly and uniform across terraform-module + accelerator entries per CONTEXT D-04 lock
- [Phase 11]: [Phase 11-act-rail-wiring-for-accelerator-dispatch]: Three distinct [DRIFT-1] accelerator shapes (unknown composite, canon_key mismatch naming both sides, orphan canon-key) — auditable CI output; mirror direction-1 discipline from terraform-module loop
- [Phase 11]: [Phase 11-act-rail-wiring-for-accelerator-dispatch]: check_parity() gains optional fsi_overrides_path arg (PROJECT_ROOT default) — production behavior unchanged but tempdir tests inject non-existent path to isolate synthetic fixtures from real fsi keys; CLI --fsi-overrides-path flag added symmetrically
- [Phase 11]: [Phase 11-act-rail-wiring-for-accelerator-dispatch]: CANON_INFRA_KEYS filters out composite keys (those containing ':') — direction-2 WARN-2 reverse-lookup stays terraform-module-only; accelerator reverse direction enforced by per-layer canon_key field on MANIFEST
- [Phase 11]: Per-layer ACTA-04 emission lives inside execute_accelerator() (via _emit_layer_log) — not in /dsp:apply Step 8 caller. Deviates from terraform-module's caller-emits-summary pattern; only viable home since /dsp:apply has no visibility into layer iteration. CONTEXT.md D-03 locked the one-entry-per-layer shape.
- [Phase 11]: ExecutionResult.failed_layer = None default + emit_activity_log_apply layer_id = None default = back-compat for terraform-module callers. Byte-identical entry shape when layer_id omitted (TestEmitActivityLogLayerIdBackCompat asserts this).
- [Phase 11]: fake_binaries fixture lives at module scope (not class scope) in tests/test_apply_executor.py — Plan 11-04 TestAcceleratorProfileGating reuses without re-declaration.
- [Phase 11]: /dsp:plan --layer hash derived at skill-spec level via sha256(stack_hash:canon_key)[:12] — keeps canon/stack.py vendor-agnostic
- [Phase 11]: Cross-plan integration test imports MODULE_TO_CANON_KEY via importlib.util to assert act-harness layer map equals parity walker's source-of-truth dict
- [Phase 11]: VALID_ARTIFACT_TYPES extended with single accelerator/confluent-on-linuxone ID (not 5 composites) — composites belong in MODULE_TO_CANON_KEY for per-layer parity, not in the act-harness validator
- [Phase 11]: Break-glass two-step confirmation is /dsp:apply Step 6c's responsibility, NOT execute_accelerator()'s — profile-level permission in profile JSON, interactive UI in skill spec (separation of concerns)
- [Phase 11]: profile_name=None default bypasses the pre-flight gate (back-compat with Plan 11-02 tests) — caller is responsible for gating when None is supplied
- [Phase 11]: Refused dispatch emits a single blocked-by-profile ACTA-04 entry (no layer_id) — preserves the invariant that layer_id is present iff a layer was iterated
- [Phase 12-wiki-ingest-of-linuxone-accelerator]: 12-02: Case-insensitive + whitespace-stripped status comparison in check_gap_drift; MISSING-GAP naming chosen over MISSING-VENDOR to avoid label collision with H.1's UNKNOWN VENDOR
- [Phase 12]: Replaced layer-scoped fsi-dsp source IDs (:NN-layer) with top-level accelerator ID; MANIFEST.yaml only indexes capabilities[].id (top-level), not apply_sequence sub-paths.
- [Phase 12]: Article 4 (auditor-readonly) reformatted bold markdown to keep verbatim grep-target strings contiguous for Plan 12-03 review-engine match.

### Pending Todos

None yet.

### Blockers/Concerns

None yet — note that 10 may require an upstream fsi-dsp PR merge before 11 can land cleanly; sequence accordingly when planning.

## Session Continuity

Last session: 2026-05-23T17:57:31.458Z
Stopped at: Completed 12-01-PLAN.md
Resume file: None
