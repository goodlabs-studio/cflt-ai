# Roadmap: cflt-ai

## Overview

Six phases deliver a Confluent operational and knowledge agent for FSI engagements. Phase 0 fixes foundational hygiene and establishes the canon overlay stack and MANIFEST.yaml contract. Phase 1 unifies the knowledge skill with a tested triage path. Phase 2 hardens the review skill with reproducible claim extraction and customer-ready output. Phases 3a through 3c build the act rail incrementally — read-only plan, human-gated apply, then full per-profile tool classification — so that agent-driven Confluent operations are always canon-compliant and auditable. Each phase exits on measurable threshold, not calendar.

## Phases

**Phase Numbering:**
- Integer phases (0, 1, 2, 3): Planned milestone work
- Sub-phases (3a, 3b, 3c): Independent delivery boundaries within Phase 3 act rail

- [x] **Phase 0: Foundation** - Fix bugs, establish MANIFEST.yaml contract, scaffold canon overlay stack, and get both repos to clean-clone health (completed 2026-04-28)
- [ ] **Phase 1: Knowledge Skill** - Unify /ask + /wiki:recommend, add triage classifier, golden harness, and wiki decay rules
- [x] **Phase 2: Review Skill** - Reproducible claim extraction, premise-challenge step, .docx output, multi-document support, customer overlay validation (completed 2026-04-28)
- [x] **Phase 3a: Act Rail — Plan** - Four-gate validation chain, /dsp:plan read-only rail, structural-correctness harness, CI parity in both repos (completed 2026-04-29)
- [x] **Phase 3b: Act Rail — Apply** - /dsp:apply with human-in-the-loop confirmation, three policy profiles, activity log, incident entries (completed 2026-04-29)
- [x] **Phase 3c: Act Rail — Profile Gating** - Per-tool classification of all 50+ mcp-confluent tools, negative-space test suites, break-glass two-step, customer fork demo (completed 2026-04-29)
- [x] **Phase F.1: FRANZ pre-confirmed apply** - Native modal flows through to skill as --pre-confirmed flag; activity log records confirmation_source (completed 2026-05-13)
- [x] **Phase G.1: Terraform-module executor** - /dsp-apply Step 7 dispatches by artifact.type; terraform-module artifacts execute real terraform init/plan/apply with per-plan-slug state (completed 2026-05-14)
- [ ] **Phase G.2: Composite + GitOps + tool-call execution** - Promoted from backlog 999.3; broken into G.2a–G.2e (see Phase Details)

## Phase Details

### Phase 0: Foundation
**Goal**: Both repos are clean-clone healthy, tooling runs without crashes, MANIFEST.yaml v1 is the binding contract between cflt-ai and fsi-dsp, and the canon overlay stack scaffolding is in place
**Depends on**: Nothing (first phase)
**Requirements**: HYG-01, HYG-02, HYG-03, HYG-04, HYG-05, CNTR-01, CNTR-02, CNTR-03, CNTR-04, CNTR-05, CANST-01, CANST-02, CANST-03, CANST-04, WIKI-01, WIKI-02
**Success Criteria** (what must be TRUE):
  1. wiki-stats.py and wiki-lint.py run to completion without crashes or regex errors on the current wiki corpus
  2. A fresh `git clone` of cflt-ai and fsi-kafka-platform, followed by `flox activate`, produces a working environment with all CLI tools available
  3. MANIFEST.yaml v1 exists in fsi-dsp with capabilities blocks for every existing asset, and both repos' CI blocks PRs that break ID stability or citation resolution
  4. Overlay stack directory structure exists (base → industry → customer → engagement), each layer can override the layer above, and every override is an ADR
  5. LinuxONE wiki articles are ingested and activity log directories are live and emitting per overlay-scoped path
**Plans:** 6/6 plans complete

Plans:
- [x] 00-01-PLAN.md — Fix wiki tool bugs (HYG-01, HYG-02, HYG-03) and verify Flox environment (HYG-04)
- [x] 00-02-PLAN.md — Author MANIFEST.yaml v1 and create fsi-dsp Flox manifest (CNTR-01, HYG-05)
- [x] 00-03-PLAN.md — Scaffold four-layer canon overlay stack with defaults, overrides, and stack resolution (CANST-01 through CANST-04)
- [x] 00-04-PLAN.md — Create wiki activity log and author ADR-009 LinuxONE (WIKI-02, WIKI-01 partial)
- [x] 00-05-PLAN.md — Migrate wiki citations to fsi-dsp:// IDs and compile LinuxONE article (CNTR-02, WIKI-01)
- [x] 00-06-PLAN.md — Create CI parity workflows for citation resolution and ID stability (CNTR-03, CNTR-04, CNTR-05)

### Phase 1: Knowledge Skill
**Goal**: A single unified /ask skill with triage routing, a tested golden harness, and wiki decay rules that keep coverage honest
**Depends on**: Phase 0
**Requirements**: WIKI-03, WIKI-04, WIKI-05, KNOW-01, KNOW-02, KNOW-03, KNOW-04, KNOW-05
**Success Criteria** (what must be TRUE):
  1. Running `/ask` with `--mode ephemeral`, `--mode report`, or `--mode reconsolidate` routes correctly through the triage classifier (wiki-only / wiki+MCP / deep reasoning) with no flag error
  2. The golden harness at tests/golden/ask/ contains >= 30 cases (>= 5 negative-space), passes at >= 90% on Haiku floor and >= 95% on Sonnet floor
  3. Wiki articles older than 90 days without revalidation drop from confidence:high to confidence:medium automatically
  4. Every /ask query that misses wiki coverage appends a stub to wiki/_queue.md for follow-up
**Plans:** 3 plans

Plans:
- [x] 01-01-PLAN.md — Add last_validated decay lifecycle to wiki articles and tooling (WIKI-03, WIKI-04)
- [x] 01-02-PLAN.md — Consolidate /ask with mode routing, triage classifier, and auto-stub (KNOW-01, KNOW-02, WIKI-05)
- [x] 01-03-PLAN.md — Build golden test harness with 32 cases and structural pytest runner (KNOW-03, KNOW-04, KNOW-05)

### Phase 2: Review Skill
**Goal**: The /review skill produces reproducible, customer-ready output — deterministic claim extraction, premise-challenge step, .docx with full provenance, multi-document input, and at least one validated customer overlay
**Depends on**: Phase 1
**Requirements**: REVW-01, REVW-02, REVW-03, REVW-04, REVW-05, REVW-06
**Success Criteria** (what must be TRUE):
  1. Running /review on the same document twice produces identical claims >= 95% of the time (measured by the golden harness)
  2. The premise-challenge step executes as a distinct, named step in every review run and is exercised by at least one golden harness case
  3. /review --output docx produces a .docx file containing a provenance footer with canon stack hash, manifest version, model floors, and MCP versions
  4. /review accepts a mixed input set (e.g., deck + tfvars + runbook) and treats them as a single review scope
  5. At least one customer overlay is configured and a review run under that overlay produces a differential result relative to base canon
**Plans:** 3/3 plans complete

Plans:
- [x] 02-01-PLAN.md — Rewrite /review skill with structured claim extraction, premise-challenge step, multi-doc input, and --output/--overlay flags (REVW-01, REVW-02, REVW-04)
- [x] 02-02-PLAN.md — Build review-to-docx.py converter with provenance footer and create acme-bank customer overlay (REVW-03, REVW-06)
- [x] 02-03-PLAN.md — Build golden test harness with 16 cases, 8 fixtures, and structural pytest runner (REVW-05, exercises REVW-01 through REVW-06)

### Phase 3a: Act Rail — Plan
**Goal**: A read-only /dsp:plan rail that selects and validates fsi-dsp artifacts through a four-gate chain, with structural correctness >= 95% and CI parity enforcing canon/fsi-dsp alignment in both repos
**Depends on**: Phase 2
**Requirements**: ACT-01, ACT-02, ACT-03, ACT-04, ACT-05, ACT-06, ACT-07, ACT-08
**Success Criteria** (what must be TRUE):
  1. Terraform MCP is wired into .mcp.json and reachable by the act rail
  2. /dsp:plan produces a plan referencing an existing fsi-dsp artifact with correct arguments, never generating inline Terraform or invoking write tools directly
  3. Each of the four gates (canon compliance, fsi-dsp coverage, confluent-docs schema, mcp-confluent state) can be individually tested and bypassed in dev mode without affecting the others
  4. The golden harness at tests/golden/act/ contains >= 20 cases (including negative-space), structural correctness >= 95%
  5. Canon-to-fsi-dsp parity CI runs in both repos and blocks merges on drift
**Plans:** 3/3 plans complete

Plans:
- [x] 03A-01-PLAN.md — Wire Terraform MCP, build four-gate chain module, and unit tests (ACT-01, ACT-02, ACT-03, ACT-06)
- [x] 03A-02-PLAN.md — Create /dsp:plan skill file, canon parity checker with tests, and CI workflow (ACT-04, ACT-06, ACT-08)
- [x] 03A-03-PLAN.md — Build golden test harness with 22 cases and structural pytest runner (ACT-05, ACT-07)

### Phase 3b: Act Rail — Apply
**Goal**: /dsp:apply executes planned changes with mandatory human confirmation, three policy profiles enforce least-privilege, and every operation is logged with full provenance
**Depends on**: Phase 3a
**Requirements**: ACTA-01, ACTA-02, ACTA-03, ACTA-04, ACTA-05, ACTA-06
**Success Criteria** (what must be TRUE):
  1. /dsp:apply requires an explicit human confirmation step; attempted bypasses are blocked and logged
  2. Three policy profile files (read-only.json, engineer.json, break-glass.json) exist and are enforced; operations outside the active profile fail closed
  3. Every plan and apply appends to the activity log with the full provenance schema (artifact ID, canon stack hash, model, operator, timestamp)
  4. Every apply produces a wiki incident entry
  5. Structural-correctness metric holds >= 95% across 30 days of real engagement use
**Plans:** 3/3 plans complete

Plans:
- [x] 03B-01-PLAN.md — Profile JSON files + apply_engine.py with TDD unit tests (ACTA-02, ACTA-03, ACTA-04, ACTA-05)
- [x] 03B-02-PLAN.md — /dsp:apply skill file with 9-step structure and mandatory human confirmation (ACTA-01)
- [x] 03B-03-PLAN.md — Golden test harness with 10 apply cases and extended test runner (ACTA-06)

### Phase 3c: Act Rail — Profile Gating
**Goal**: Every mcp-confluent tool is explicitly classified into a profile by name, per-profile negative-space suites prove forbidden tools fail closed, break-glass requires two-step confirmation, and a customer fork demonstrates differential gating
**Depends on**: Phase 3b
**Requirements**: ACTG-01, ACTG-02, ACTG-03, ACTG-04
**Success Criteria** (what must be TRUE):
  1. All 50+ mcp-confluent tools appear in an explicit classification table (by tool name, not regex pattern), with no tool unclassified
  2. Per-profile negative-space test suites run and confirm that tools forbidden by a profile return a closed failure, not a partial result
  3. The break-glass profile requires two distinct confirmation prompts and logs the override reason before any tool executes
  4. At least one customer fork exists with a profile configuration that differs from base, and a test demonstrates the differential gating works
**Plans:** 3/3 plans complete

Plans:
- [x] 03C-01-PLAN.md — Classification table (50+ tools), profile JSON updates, acme-bank customer overlay (ACTG-01, ACTG-04)
- [x] 03C-02-PLAN.md — Extend apply_engine.py with tool classification check, customer overlay loading, two-step break-glass in dsp-apply.md (ACTG-01, ACTG-03, ACTG-04)
- [x] 03C-03-PLAN.md — Per-profile negative-space test suite with full tool x profile parametrized matrix (ACTG-01, ACTG-02, ACTG-03, ACTG-04)

### Phase G.2: Composite + GitOps + tool-call execution

**Goal:** Close the executor gap left by G.1. After G.2, `/dsp-apply` can execute every artifact type registered in MANIFEST: terraform-module (✅ G.1), scenarios (composite chains of modules), ansible-roles (on-prem CP via ansible-playbook), and ad-hoc mcp-confluent tool calls (data-plane ops that don't need a module). GitOps mode for FSI overlays replaces direct `terraform apply` with a tfvars-patch PR against `fsi-dsp-state` + service-account CI.

**Depends on:** Phase G.1 (the dispatcher signature and `outputs/runs/<plan_slug>/` workspace convention are reused).

**Requirements:** Carry forward ACTA-01..ACTA-06, ACTG-01..ACTG-04 from Phase 3b/3c; add new requirements per sub-phase plan when planning.

**Sub-phases (each its own PLAN.md via `/gsd:plan-phase`):**

- **G.2a: mcp-confluent tool-call executor** — Smallest, most isolated. Dispatch `artifact.type == "mcp-confluent-tool"` (new artifact type) to a tool-call sequence executor that invokes the configured mcp-confluent tools via stdio MCP from Python. Use `check_tool_permitted()` for profile gating. Forces the `tool_classification.json` name-mismatch fix (current entries use pre-1.x snake_case `confluent_kafka_topic_list`; the live 1.2.x package uses kebab-case `list-topics`). **Recommended starting sub-phase** — narrow scope, immediate value for one-off ops, fixes a latent bug.
- **G.2b: Composite scenario executor** — Dispatch `artifact.type == "scenario"` to a chained executor that walks an `apply_sequence` field in MANIFEST (fsi-dsp PR required to add it). Sequence is a list of `{artifact_id, args_mapping}` entries; each entry resolves via the existing dispatcher (re-entrant). Failure semantics: first-failure stops; partial state surfaced in incident article with per-step status list. Most useful when the user wants `scenario/cc-gcp` to *actually* compose `module/cc-cluster-basic` → topic + SR + RBAC + DR end-to-end.
- **G.2c: Tool-classification rename** — Standalone hygiene fix: align `tool_classification.json` keys with the actual mcp-confluent 1.3.0 tool names (50 kebab-case tools), delete the ~25 fictional snake_case entries inherited from training data, add CI drift gate. Generator script is the single source of truth; CI runs `--check` on PR and push-to-main.
- **G.2d: GitOps apply mode** — Add `apply_mode: "direct" | "gitops"` to overlay config. When `gitops`, the executor renders the tfvars patch, opens a PR against an `fsi-dsp-state` repo, and a CI workflow runs `terraform apply` under service-account identity. Activity log records the PR URL; incident article cites the resulting commit SHA. This is the production-grade FSI path; `industry/fsi` overlay flips to `gitops` by default. Requires a new `fsi-dsp-state` repo (or directory in fsi-dsp) and a CI workflow there.
- **G.2e: Ansible-role executor** — Dispatch `artifact.type == "ansible-role"` to `ansible-playbook` against a target inventory. Inventory location comes from overlay config. Out of scope unless an active FSI engagement actually targets on-prem CP/CFK; until then this stays planned-but-deferred.

**Success Criteria:**
1. Every artifact type in MANIFEST has at least one executor that returns a non-`skipped` ExecutionResult.
2. `tool_classification.json` keys match the live mcp-confluent tool registry — a CI check fails the PR if a tool name diverges.
3. `scenario/cc-gcp` end-to-end applies cluster + topics + SR + RBAC against a CC sandbox env with all steps recorded in one incident article.
4. `industry/fsi` overlay can be flipped to `apply_mode: "gitops"` and the resulting apply opens a PR instead of touching CC directly.
5. Partial-failure scenarios produce an incident article with per-step status — no silent data loss.

**Plans:** 0/5 sub-phases complete; G.2c sub-phase has 3/3 plans authored

Plans:
- [ ] G.2a-PLAN.md — mcp-confluent tool-call executor
- [ ] G.2b-PLAN.md — Composite scenario executor (depends on fsi-dsp PR adding `apply_sequence`)
- [x] G.2c-01-PLAN.md — Build regenerate_tool_classification.py generator + checker (ACTG-01)
- [ ] G.2c-02-PLAN.md — Regenerate tool_classification.json against mcp-confluent@1.3.0; rewrite hard-coded snake_case test refs (ACTG-01, ACTG-02, ACTG-03, ACTG-04)
- [ ] G.2c-03-PLAN.md — Add tool-classification-drift CI workflow (ACTG-01)
- [ ] G.2d-PLAN.md — GitOps apply mode (depends on `fsi-dsp-state` infrastructure)
- [ ] G.2e-PLAN.md — Ansible-role executor (deferred until on-prem FSI engagement requires it)

**Recommended execution order:** G.2c → G.2a → G.2b → G.2d → G.2e. G.2c is a hygiene fix that unblocks G.2a (G.2a's executor must look up real kebab-case tool names in classification); G.2a is the smallest executor and proves the MCP-stdio-from-Python plumbing; G.2b consumes the executor pattern from G.2a + G.1; G.2d is the largest architectural change (CI repo, service accounts); G.2e waits for demand.

**G.2c wave structure:** G.2c-01 (wave 1) authors the generator. G.2c-02 and G.2c-03 (both wave 2) can run in parallel — they share no files (02 modifies `tools/profiles/tool_classification.json` + `tests/test_apply_engine.py`; 03 modifies `.github/workflows/tool-classification-drift.yml`).

## Backlog (999.x — parking lot)

Forward-looking work captured during recent sessions. Not committed to a milestone; promoted into a real phase when scope and timing firm up.

### 999.1: Phase G.1 — Terraform-module executor for /dsp-apply Step 7 (DELIVERED)

**Status:** Shipped on branch `feat/franz-phase-g1-topic-execution`.

**What landed:**
- `tools/apply_engine.py` gains `ExecutionResult` dataclass + `execute_artifact()` dispatcher + `execute_terraform_module()` runner. Dispatches on `artifact.type`; `"terraform-module"` artifacts run real `terraform init` + `plan` + `apply` against the fsi-dsp module path. All other artifact types return `status="skipped"` (the new explicit form of the historical "deferred-to-mcp-runtime" stub).
- Workspace layout: `outputs/runs/<plan_slug>/` — one Terraform workspace per plan-slug so re-applies converge idempotently rather than duplicating resources. Local backend; `.gitignored`.
- Credentials: `CONFLUENT_CLOUD_API_KEY` / `_API_SECRET` (set by FRANZ from the managed `mcp.env`) are auto-shimmed into `TF_VAR_*` so the Confluent Terraform provider picks them up. Operator's user-mode TFE auth is not used in G.1.
- `.claude/commands/dsp-apply.md` Step 7 rewritten to call the dispatcher and pass the structured result through to Step 8/9.
- Test coverage: `tests/test_apply_executor.py` (12 tests — dispatcher, dry-run, full-apply, failure short-circuit, credentials passthrough, tfvars rendering with invalid-identifier filtering).
- Existing test `test_engineer_denies_destructive` updated to reflect the F.1 profile change that added `scenario/cc-{aws,azure,gcp}` to engineer; on-prem `scenario/{cfk-openshift,cp-rhel,private-cloud}` are the new negative-space asserts.

**Verification target (manual, requires CC sandbox env):** click apply on a `module/topic` plan in FRANZ, see a real topic appear in Confluent Cloud Console, activity log records `execution_result="success"` with non-zero duration.

### 999.3: PROMOTED → Phase G.2 (active)

See `## Phase Details > Phase G.2: Composite + GitOps + tool-call execution` below for the full sub-phase breakdown (G.2a–G.2e). Backlog entry retained as a redirect.

### 999.2: fsi-dsp PR — module/cc-cluster-basic artifact (DELIVERED, in review)

**Status:** PR opened against `goodlabs-studio/fsi-dsp` — https://github.com/goodlabs-studio/fsi-dsp/pull/2 — pending review. Once merged, cflt-ai's `raw/repos/fsi-dsp` submodule pointer should be bumped in a follow-up commit.

**What landed in the PR:**
- `modules/cc-cluster-basic/{main,variables,outputs}.tf` + `tests/validation.tftest.hcl` — Basic-tier CC cluster provisioner with regex-validated inputs, hardcoded SINGLE_ZONE availability, `prevent_destroy=true` guard.
- Outputs (`kafka_cluster_id`, `kafka_rest_endpoint`, `kafka_cluster_crn`, `bootstrap_endpoint`, `environment_id`, `display_name`, `tier`) shaped for `scenario/cc-*.clusters.auto.tfvars` consumption.
- `MANIFEST.yaml` version bump `1.1.0` → `1.2.0` (additive).
- Documented limitations: Basic cannot satisfy FSI production canon (single-zone, no CL destination, no mTLS, no private networking, no BYOK, no SG Advanced).

**Follow-up scope below:**



- Sibling tier modules (`module/cc-cluster-standard`, `module/cc-cluster-enterprise`, `module/cc-cluster-dedicated`) — separate artifacts (not flags), each has different canon implications around DR / mTLS / Cluster Linking. Track as 999.2a–c when prioritized.
- Bump cflt-ai's `raw/repos/fsi-dsp` submodule pointer to the merge SHA after PR #2 lands.
- Add `module/cc-cluster-basic` to `engineer.json` and `break-glass.json` allowed_operations once it's in MANIFEST main.
- `scenario/cc-*` plans can then chain cluster create → topic + SR + RBAC + DR under one fsi-dsp apply — gated by Phase G.2b (composite scenario executor).

## Progress

**Execution Order:**
Phases execute in sequence: 0 -> 1 -> 2 -> 3a -> 3b -> 3c

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 0. Foundation | 6/6 | Complete   | 2026-04-28 |
| 1. Knowledge Skill | 0/3 | Planning complete | - |
| 2. Review Skill | 3/3 | Complete   | 2026-04-28 |
| 3a. Act Rail — Plan | 0/3 | Complete    | 2026-04-29 |
| 3b. Act Rail — Apply | 0/3 | Complete    | 2026-04-29 |
| 3c. Act Rail — Profile Gating | 2/3 | Complete    | 2026-04-29 |
| F.1. FRANZ pre-confirmed apply | 1/1 | Complete    | 2026-05-13 |
| G.1. Terraform-module executor | 1/1 | Complete    | 2026-05-14 |
| G.2. Composite + GitOps + tool-call execution | 0/5 | Planning needed | - |
