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

### 999.3: Phase G.2 — Scenario/composite executor + GitOps mode

**Surface:** `tools/apply_engine.py`, `.claude/commands/dsp-apply.md`, possibly `MANIFEST.yaml` (apply-sequence declaration).

**Today (after G.1):** `terraform-module` artifacts execute; everything else returns `status="skipped"`. That covers `module/topic` and `module/flink`. Scenarios (`scenario/cc-*`, `scenario/cfk-openshift`, etc.) and ansible roles (`role/cp_*`) still no-op.

**Goals:**
- **Composite execution**: `scenario/cc-*` artifacts chain a sequence of modules (topic + schema + RBAC + cluster-link). Need an `apply_sequence` field in `MANIFEST.yaml` (fsi-dsp PR — coordinates with 999.2's `module/cc-cluster-basic` work), or an embedded recipe per scenario in apply_engine. Failure semantics: first-failure stops, partial state surfaced in the incident article.
- **mcp-confluent tool-call executor**: for ad-hoc data-plane operations that DON'T need a full terraform module (e.g., a one-off `create-topics` call). Would dispatch by classification table.
- **GitOps mode for FSI overlays**: instead of running `terraform apply` directly, render the tfvars patch and open a PR against an `fsi-dsp-state` repo + trigger CI. Service-account identity, not operator identity. Activated by overlay config flag (e.g. `apply_mode: "gitops"` on `industry/fsi`).
- **Ansible-role executor**: `role/cp_*` artifacts target Confluent Platform (on-prem) rather than Cloud. Would invoke `ansible-playbook` against a target inventory. Out of scope unless an FSI engagement actually needs on-prem.
- **Tool-classification name fix**: `tool_classification.json` currently uses pre-1.x mcp-confluent names (`confluent_kafka_topic_list`) that don't match the actual 1.2.x package (`list-topics`). Latent bug — only fires when something tries to call `check_tool_permitted()` against a real mcp-confluent tool. G.2's mcp-confluent executor is the first thing that would hit this.

### 999.2: fsi-dsp PR — module/cc-cluster-basic artifact

**Surface:** `fsi-dsp` repo (separate from cflt-ai), `MANIFEST.yaml` v1.2.0

**Today:** MANIFEST v1.1.0 has no cluster-provisioning artifact. Requests like *"Create a Basic Kafka cluster named franz-smoke-01 on GCP us-east1"* match `scenario/cc-gcp` mechanically but trigger a coverage-gap note because `scenario/cc-gcp` *consumes* an existing cluster (it wires topics + SR + RBAC + DR on top of a known `kafka_cluster_id`). Per **ACT-06**, the planner refuses to generate inline `confluent_kafka_cluster` HCL; the operator has to provision out-of-band via `confluent kafka cluster create` or hand-rolled Terraform.

**Goal:** Add `module/cc-cluster-basic` to fsi-dsp:
- Type: `terraform-module`
- Path: `modules/cc-cluster-basic`
- Wraps `confluent_kafka_cluster` with the `basic { }` block plus a `confluent_environment` data source
- Variable surface: `display_name`, `environment_id`, `cloud`, `region`, `availability` (defaulted to `SINGLE_ZONE` since Basic is single-zone only)
- Outputs: `kafka_cluster_id`, `kafka_rest_endpoint`, `kafka_cluster_crn` — exactly the inputs `scenario/cc-gcp` expects in `clusters.auto.tfvars`
- Register in `MANIFEST.yaml` per CNTR-04 with capability metadata for gate 2 to match

**Follow-ups once landed:**
- Mirror modules for `standard`, `enterprise`, `dedicated` tiers (separate artifacts, not flags — different canon implications around DR/mTLS/Cluster Linking)
- Update both `engineer.json` and `break-glass.json` allowed_operations to include the new module IDs
- `scenario/cc-*` plans could then chain: cluster create → topic+SR+RBAC+DR layer, all under one fsi-dsp apply

**Dependency on 999.1:** Independent — adding the artifact only requires fsi-dsp PR work. Whether it actually *creates* a cluster on apply is gated by 999.1's Step 7 execution backend.

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
