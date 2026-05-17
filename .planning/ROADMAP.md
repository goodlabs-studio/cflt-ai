# Roadmap: cflt-ai

## Milestones

- ✅ **v1.0 — Foundation through Act Rail** — 9 phases, 26 plans (shipped 2026-05-16). See [`milestones/v1.0-ROADMAP.md`](milestones/v1.0-ROADMAP.md).
- ✅ **v2.0 — Developer Persona + Quality Gates** — 8 phases, 13 plans (shipped 2026-05-17). See [`milestones/v2.0-ROADMAP.md`](milestones/v2.0-ROADMAP.md).

## Phases

<details>
<summary>✅ v1.0 — Foundation through Act Rail (SHIPPED 2026-05-16)</summary>

- [x] Phase 0: Foundation (6/6 plans) — 2026-04-28
- [x] Phase 1: Knowledge Skill (3/3 plans)
- [x] Phase 2: Review Skill (3/3 plans) — 2026-04-28
- [x] Phase 3a: Act Rail — Plan (3/3 plans) — 2026-04-29
- [x] Phase 3b: Act Rail — Apply (3/3 plans) — 2026-04-29
- [x] Phase 3c: Act Rail — Profile Gating (3/3 plans) — 2026-04-29
- [x] Phase F.1: FRANZ pre-confirmed apply (1/1 plan) — 2026-05-13
- [x] Phase G.1: Terraform-module executor (1/1 plan) — 2026-05-14
- [x] Phase G.2c: Tool-classification rename (3/3 plans) — 2026-05-15

Full details: [`milestones/v1.0-ROADMAP.md`](milestones/v1.0-ROADMAP.md)

</details>

<details>
<summary>✅ v2.0 — Developer Persona + Quality Gates (SHIPPED 2026-05-17)</summary>

- [x] Phase H.1: Wiki ingest from agent-skills refs (3/3 plans) — 2026-05-16
- [x] Phase H.2: Eval harness extension (4/4 plans) — 2026-05-17
- [x] Phase H.3a: Plugin install + canon-overlay article (1/1 plan) — 2026-05-17
- [x] Phase H.4a: Profile-family schema extension (1/1 plan) — 2026-05-17
- [x] Phase H.4b: Developer-sandbox profile + FSI dev canon (1/1 plan) — 2026-05-17
- [x] Phase H.4c: acme-bank developer overlay (1/1 plan) — 2026-05-17
- [x] Phase H.3b: Version pin + CI drift gate (1/1 plan) — 2026-05-17
- [x] Phase H.3c: /dsp:scaffold wrapper (1/1 plan) — 2026-05-17

Full details: [`milestones/v2.0-ROADMAP.md`](milestones/v2.0-ROADMAP.md)
Audit: [`milestones/v2.0-MILESTONE-AUDIT.md`](milestones/v2.0-MILESTONE-AUDIT.md)

</details>

### 📋 v2.1 — Planning (next milestone)

Run `/gsd:new-milestone` to scope the next milestone. Candidate backlog items below.

## Backlog (999.x — parking lot)

Forward-looking work captured during recent sessions. Not committed to a milestone; promoted into a real phase when scope and timing firm up.

### Deferred sub-phases (G.2 carry-forward — promoted at sequencing-time)

- [ ] **G.2a: mcp-confluent tool-call executor** — Dispatch `artifact.type == "mcp-confluent-tool"` to a tool-call sequence executor via stdio MCP from Python. Smallest, most isolated of the remaining G.2 work; proves the MCP-stdio-from-Python plumbing. Unblocked now that G.2c has corrected the tool classification.
- [ ] **G.2b: Composite scenario executor** — Dispatch `artifact.type == "scenario"` to a chained executor that walks an `apply_sequence` field in MANIFEST (fsi-dsp PR required). Re-entrant via the existing dispatcher.
- [ ] **G.2d: GitOps apply mode** — Add `apply_mode: "direct" | "gitops"` to overlay config. When `gitops`, executor renders tfvars patch and opens a PR against `fsi-dsp-state` repo; CI runs `terraform apply` under service-account identity. Production-grade FSI path.
- [ ] **G.2e: Ansible-role executor** — Dispatch `artifact.type == "ansible-role"` to `ansible-playbook` against a target inventory. Deferred until an on-prem FSI engagement requires it.

### v2.0 tech debt (per audit — none blocking)

- Extend `/dsp:scaffold` to cover the remaining 4 artifact-types (consumer, kafka-streams-app, schema, cdc-pipeline) — each one phase.
- Add `scaffolded-producer` executor inside `raw/repos/fsi-dsp/` (separate PR) so `/dsp:plan` + `/dsp:apply` can consume scaffolded artifacts.
- Promote CONTEXT-sourced override decisions in `canon/industry/fsi/developer-sandbox/` to formal ADRs after the first customer engagement uses the developer profile in practice.
- Resolve 2 pre-existing test failures (test_check_canon_parity, test_manifest — fsi-dsp submodule version drift).

### 999.1: Phase G.1 — Terraform-module executor for /dsp-apply Step 7 (DELIVERED in v1.0)

Shipped on branch `feat/franz-phase-g1-topic-execution`. `tools/apply_engine.py` gains `ExecutionResult` dataclass + `execute_artifact()` dispatcher + `execute_terraform_module()` runner. Workspace layout: `outputs/runs/<plan_slug>/` per-plan-slug Terraform workspaces.

### 999.2: fsi-dsp PR — module/cc-cluster-basic artifact (DELIVERED, in review)

PR opened against `goodlabs-studio/fsi-dsp` (#2). Once merged, cflt-ai's `raw/repos/fsi-dsp` submodule pointer should be bumped in a follow-up commit. Sibling tier modules (`module/cc-cluster-standard`, `module/cc-cluster-enterprise`, `module/cc-cluster-dedicated`) track as 999.2a–c when prioritized.

### 999.3: PROMOTED → Phase G.2 (partially delivered in v1.0)

G.2c shipped in v1.0. G.2a, G.2b, G.2d, G.2e carry forward (see above). Detailed scope retained for promotion when sequencing demands.

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 0. Foundation | v1.0 | 6/6 | Complete | 2026-04-28 |
| 1. Knowledge Skill | v1.0 | 3/3 | Complete | - |
| 2. Review Skill | v1.0 | 3/3 | Complete | 2026-04-28 |
| 3a. Act Rail — Plan | v1.0 | 3/3 | Complete | 2026-04-29 |
| 3b. Act Rail — Apply | v1.0 | 3/3 | Complete | 2026-04-29 |
| 3c. Act Rail — Profile Gating | v1.0 | 3/3 | Complete | 2026-04-29 |
| F.1. FRANZ pre-confirmed apply | v1.0 | 1/1 | Complete | 2026-05-13 |
| G.1. Terraform-module executor | v1.0 | 1/1 | Complete | 2026-05-14 |
| G.2c. Tool-classification rename | v1.0 | 3/3 | Complete | 2026-05-15 |
| H.1. Wiki ingest from agent-skills refs | v2.0 | 3/3 | Complete | 2026-05-16 |
| H.2. Eval harness extension | v2.0 | 4/4 | Complete | 2026-05-17 |
| H.3a. Plugin install + canon-overlay article | v2.0 | 1/1 | Complete | 2026-05-17 |
| H.4a. Profile-family schema extension | v2.0 | 1/1 | Complete | 2026-05-17 |
| H.4b. Developer-sandbox profile + FSI dev canon | v2.0 | 1/1 | Complete | 2026-05-17 |
| H.4c. acme-bank developer overlay | v2.0 | 1/1 | Complete | 2026-05-17 |
| H.3b. Version pin + CI drift gate | v2.0 | 1/1 | Complete | 2026-05-17 |
| H.3c. /dsp:scaffold wrapper | v2.0 | 1/1 | Complete | 2026-05-17 |
| G.2a. mcp-confluent tool-call executor | backlog | 0/1 | Not started | - |
| G.2b. Composite scenario executor | backlog | 0/1 | Not started | - |
| G.2d. GitOps apply mode | backlog | 0/1 | Not started | - |
| G.2e. Ansible-role executor | backlog | 0/1 | Deferred (on-prem demand) | - |
