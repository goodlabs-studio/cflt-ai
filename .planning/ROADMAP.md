# Roadmap: cflt-ai

## Milestones

- ✅ **v1.0 — Foundation through Act Rail** — 9 phases, 26 plans (shipped 2026-05-16). See [`milestones/v1.0-ROADMAP.md`](milestones/v1.0-ROADMAP.md).
- ✅ **v2.0 — Developer Persona + Quality Gates** — 8 phases, 13 plans (shipped 2026-05-17). See [`milestones/v2.0-ROADMAP.md`](milestones/v2.0-ROADMAP.md).
- 🚧 **v2.1 — LinuxONE Accelerator Integration** — 4 phases planned, 0 complete

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

### 🚧 v2.1 — LinuxONE Accelerator Integration

- [ ] **Phase 9: Submodule sync + canon-parity unblock** — Bump `raw/repos/fsi-dsp` submodule pointer to upstream `main` (23+ commits ahead, includes the LinuxONE accelerator + 2989473 merge); clear the two pre-existing canon-parity / manifest test failures from the v2.0 audit; add a stale-submodule CI guard. Foundational; nothing else in v2.1 can land cleanly until the submodule reflects the accelerator's existence on disk.
- [x] **Phase 10: Accelerator artifact-type registration** — Land `type: accelerator` in upstream fsi-dsp `MANIFEST.yaml` (separate PR) and accept the new type in cflt-ai's manifest schema validator without regressing on `ansible-role`, `terraform-module`, `scenario`, `adr`, or `reference`. The type contract MUST exist before downstream consumers (11) wire to it. (completed 2026-05-23)
- [x] **Phase 11: Act-rail wiring for accelerator dispatch** — Extend `/dsp:plan` Gate 1 (canon compliance) and `/dsp:apply` Step 7 (executor) to handle accelerator artifacts: 5-layer MODULE_TO_CANON_KEY map (`01-rbac` → `fsi.security.mds-rbac`, `02-tls` → `fsi.security.tls-fips`, `03-schema-governance` → `fsi.schema.compatibility-full-transitive`, `04-audit` → `fsi.audit.events-retention`, `05-flink` → `fsi.flink.environment-mtls`); layer-aware kustomize apply_sequence (build → `oc apply --dry-run=server` → `oc apply`); per-layer activity-log entries; bidirectional canon-parity CI extended to accelerator MANIFEST entries (G.2c CI pattern). Largest phase. (completed 2026-05-23)
- [x] **Phase 12: Wiki ingest of LinuxONE accelerator** — Mirror the H.1 ingest pattern for the LinuxONE accelerator: ≥6 articles covering reference architecture / x86→LinuxONE Cluster Linking migration / FIPS-at-install / auditor-readonly RBAC isolation / custom s390x image build / Flink-on-CFK example jobs; 13 KNOWN-GAPS entries (G-01..G-13) encoded as `tools/vendor-sources.json` trip-wires; ≥15 golden eval cases across `/ask` and `/review`; `/review` flags claims contradicting the auditor-readonly payload-isolation pattern. (completed 2026-05-23)

## Phase Details

**Theme:** Integrate the new `accelerators/confluent-on-linuxone/` tier from upstream fsi-dsp into cflt-ai's canon, wiki, and act rail. After this milestone, `/ask`, `/review`, `/dsp:plan`, and `/dsp:apply` can reason about and dispatch accelerator artifacts with full provenance, and the wiki has authoritative coverage of the LinuxONE-on-CFK reference architecture, the 13 known gaps, and the x86→LinuxONE migration evidence checklist.

**Recommended execution order:** Phase 9 → 10 → 11 → 12. Phase 9 is foundational (clears v2.0 audit debt and unblocks everything downstream). Phase 10 lands the type contract (may require an upstream fsi-dsp PR merge before 11 can land cleanly). Phase 11 is the largest and depends on the type contract being in place. Phase 12 sequences last so wiki articles can cite the new MANIFEST entries by stable ID (though it can parallelize with late-11 work if dependencies allow).

### Phase 9: Submodule sync + canon-parity unblock
**Goal:** Bump the `raw/repos/fsi-dsp` submodule pointer from local `feat/module-cc-cluster-basic@2989473` to upstream `main` HEAD (currently `5a86fd2`, 23+ commits ahead including the LinuxONE accelerator + the 2989473 branch's own merge into main); resolve the two pre-existing test failures from the v2.0 audit (`test_check_canon_parity`, `test_manifest`); add a stale-submodule CI guard that enforces tracking of upstream `main` within an allowed drift window. After 9, the submodule reflects the LinuxONE accelerator on disk and the v2.0 audit debt is cleared.
**Depends on:** Nothing (foundational; clears v2.0 audit debt). Hard prerequisite for 10, 11, 12.
**Requirements:** SUBM-01, SUBM-02, SUBM-03
**Success Criteria** (what must be TRUE):
  1. `git submodule update --remote raw/repos/fsi-dsp` advances the local pointer to upstream `main` HEAD (verifiable via `git -C raw/repos/fsi-dsp rev-parse HEAD` matching `git ls-remote origin main`); no manual conflict resolution required.
  2. `pytest tests/test_check_canon_parity.py tests/test_manifest.py` passes — the two pre-existing failures from the v2.0 audit are resolved at the same commit that bumps the pointer.
  3. `.github/workflows/submodule-drift.yml` (or equivalent) exists, runs on PR + push:main, and fails when the submodule is >14 days behind upstream `main` HEAD with a clear remediation message (`git submodule update --remote raw/repos/fsi-dsp && git add raw/repos/fsi-dsp && git commit`).
  4. Full repo test suite (`pytest tests/`) passes at the bumped submodule pointer — no regressions in any v1.0/v2.0 phase introduced by the submodule advance.
**Plans:** 2 plans
- [x] 09-01-PLAN.md — Bump submodule + clear two v2.0-audit test failures (atomic commit)
- [x] 09-02-PLAN.md — Stale-submodule CI guard (14-day drift window, mirrors H.3b)

### Phase 10: Accelerator artifact-type registration
**Goal:** Land `type: accelerator` as a first-class MANIFEST.yaml artifact type in upstream fsi-dsp (separate PR; mirrors the 999.2 cc-cluster-basic upstream-PR pattern) and extend cflt-ai's manifest schema validator to accept the new type without regressing on existing types. After 10, the type contract exists end-to-end and downstream consumers in 11 can wire to a stable artifact shape.
**Depends on:** 9 (submodule must reflect upstream main so the accelerator directory is visible to local CI before the schema work begins).
**Requirements:** MAN-01
**Success Criteria** (what must be TRUE):
  1. An fsi-dsp PR is opened (or merged) that registers `accelerators/confluent-on-linuxone/` as a MANIFEST.yaml entry with `type: accelerator` and an `apply_sequence` block declaring the 5 kustomize layers; PR passes upstream CI.
  2. cflt-ai's manifest schema validator (`tools/check_manifest.py` or equivalent) accepts `type: accelerator` entries; the validator's enum/dispatch is extended without breaking validation of existing `ansible-role`, `terraform-module`, `scenario`, `adr`, or `reference` entries (proven via the existing test_manifest suite passing post-change).
  3. A new positive-coverage unit test asserts that an `accelerator`-typed fixture entry validates cleanly; a corresponding negative-space test asserts that a malformed accelerator entry (missing `apply_sequence`, unknown layer name, etc.) fails validation with a clear error.
  4. The new type is documented in cflt-ai's MANIFEST contract reference (CONTRIBUTING.md or `tools/manifest-schema.md`) so future contributors know `accelerator` is a recognized artifact-type alongside the v1.0/v2.0 types.
**Plans:** 3/3 plans complete
- [x] 10-01-PLAN.md — Register accelerator MANIFEST entry inside fsi-dsp submodule (feature branch)
- [x] 10-02-PLAN.md — cflt-ai validator + 9 tests + 2 fixtures + schema docs (atomic commit with submodule pointer bump)
- [ ] 10-03-PLAN.md — Human-action checkpoint: upstream PR-open + post-merge pointer follow-up

### Phase 11: Act-rail wiring for accelerator dispatch
**Goal:** Extend the `/dsp:plan` four-gate rail and the `/dsp:apply` executor to handle accelerator artifacts end-to-end. Gate 1 (canon compliance) gains a 5-layer MODULE_TO_CANON_KEY map covering RBAC, TLS, schema governance, audit, and Flink layers, with unknown-layer cases producing blocking `DRIFT-1` violations per the G.1 terraform-module precedent. The executor dispatches the kustomize `apply_sequence` layer-by-layer (build → `oc apply --dry-run=server` → `oc apply`), records per-layer outcomes in the activity log per ACTA-04, and extends bidirectional canon-parity CI to accelerator MANIFEST entries (mirrors the G.2c pattern: drift between cflt-ai's canon map and upstream MANIFEST blocks merge in both repos). Largest phase in v2.1.
**Depends on:** 10 (the `type: accelerator` MANIFEST contract must exist before the plan rail and executor can dispatch against it).
**Requirements:** MAN-02, MAN-03, MAN-04, MAN-05
**Success Criteria** (what must be TRUE):
  1. `/dsp:plan create accelerator confluent-on-linuxone --layer 01-rbac` (and equivalents for `02-tls`, `03-schema-governance`, `04-audit`, `05-flink`) returns a structurally-correct plan referencing the accelerator artifact by MANIFEST ID, with full canon-stack provenance footer (operator, profile, canon-stack hash, manifest version, timestamp); golden act-harness gains ≥5 accelerator cases (one per layer) that pass at the v1.0 90% threshold.
  2. `/dsp:apply` dispatches the kustomize `apply_sequence` layer-by-layer (build → `oc apply --dry-run=server` → `oc apply`); each layer produces a discrete activity-log entry per ACTA-04 (operator, profile, plan_ref, gate_results, execution_result, layer_id, duration_seconds); a failed dry-run on any layer halts the sequence and writes a blocked-outcome entry before any real apply runs.
  3. `MODULE_TO_CANON_KEY` covers all 5 accelerator layers with the canonical mappings (`01-rbac` → `fsi.security.mds-rbac`, `02-tls` → `fsi.security.tls-fips`, `03-schema-governance` → `fsi.schema.compatibility-full-transitive`, `04-audit` → `fsi.audit.events-retention`, `05-flink` → `fsi.flink.environment-mtls`); a negative-space test confirms that requesting an unknown layer name produces a blocking `DRIFT-1` violation with the same shape G.1 emits for unknown terraform-modules.
  4. Bidirectional canon-parity CI (`.github/workflows/canon-parity.yml` or equivalent) is extended to walk accelerator MANIFEST entries; PRs that drift the cflt-ai map from upstream MANIFEST fail in both repos with a clear remediation message (mirrors the G.2c CI shape; same `--check` mode pattern).
  5. `/dsp:apply` respects existing profile gating for accelerator artifacts: `read-only` profile refuses any accelerator apply with explicit error; `engineer` profile permits all 5 layers; `break-glass` enforces the existing two-step confirmation before any real apply. Negative-space tests prove fail-closed for each profile family.

**Plans:** 4/4 plans complete
- [x] 11-01-PLAN.md — MODULE_TO_CANON_KEY extension + parity walker (MAN-04, MAN-05)
- [x] 11-02-PLAN.md — execute_accelerator() executor + ACTA-04 per-layer (MAN-03)
- [x] 11-03-PLAN.md — /dsp:plan act-harness extension + 5 golden cases (MAN-02)
- [x] 11-04-PLAN.md — Profile gating for accelerator dispatch (MAN-03 completion)


### Phase 12: Wiki ingest of LinuxONE accelerator
**Goal:** Mirror the H.1 ingest pattern for the LinuxONE accelerator. Compile ≥6 wiki articles from the upstream accelerator's `DESIGN.md`, `KNOWN-GAPS.md`, `MIGRATION.md`, and embedded patterns (LinuxONE-on-CFK reference architecture; x86→LinuxONE Cluster Linking with regulatory evidence checklist; FIPS-at-install OCP requirement; auditor-readonly RBAC payload-isolation pattern; custom s390x image build pipeline for Connect + Flink SQL-runner; Flink-on-CFK FSI example jobs). Encode all 13 `KNOWN-GAPS.md` entries (G-01..G-13) as `tools/vendor-sources.json` trip-wires with status, workaround, and FSI impact. Extend the golden eval harness with ≥15 cases across `/ask` and `/review` so coverage holds at the H.2 EVAL-02 floor. After 12, `/ask` and `/review` can reason about LinuxONE deployments with full provenance, and `/wiki:lint --full` surfaces drift when upstream gap status changes.
**Depends on:** 10 (wiki articles cite MANIFEST entries by stable ID; the `type: accelerator` contract must exist first). Can parallelize with late-11 work but easier to sequence after 11 so articles can cross-reference the canon-key map.
**Requirements:** WIKI-01, WIKI-02, WIKI-03, WIKI-04, WIKI-05
**Success Criteria** (what must be TRUE):
  1. `/ask "How do I deploy Confluent Platform on IBM LinuxONE for FSI?"` returns an answer citing the new LinuxONE-on-CFK reference-architecture wiki article with `confidence: high` and provenance footer pointing to upstream `accelerators/confluent-on-linuxone/DESIGN.md` at the pinned SHA from 9.
  2. ≥6 wiki articles exist under `wiki/concepts/` or `wiki/patterns/` covering the six target topics (LinuxONE-on-CFK ref arch, x86→LinuxONE Cluster Linking migration + regulatory evidence checklist, FIPS-at-install OCP requirement, auditor-readonly RBAC payload-isolation pattern, custom s390x image build pipeline, Flink-on-CFK FSI example jobs); each has `confidence: high`, `last_validated: <ingest date>`, and an upstream source attestation per H.1 D-07.
  3. All 13 `KNOWN-GAPS.md` entries (G-01..G-13) are present in `tools/vendor-sources.json` as trip-wires with `status`, `workaround`, and FSI-impact fields; `/wiki:lint --full` surfaces drift findings when upstream gap status changes (DRIFT / MALFORMED / UNKNOWN-VENDOR findings, non-fatal per H.1 D-09).
  4. `/review` against a fixture customer LinuxONE deployment doc flags any claim that contradicts the auditor-readonly payload-isolation pattern (e.g., a claim that `DeveloperRead` on the cluster is sufficient for auditor isolation is flagged with the topic-scoped binding workaround as the canonical correction); golden review case ships at the EVAL-02 floor.
  5. Golden eval harness gains ≥15 new cases (≥10 each across `/ask` and `/review` per EVAL-02 floor) covering the 6 articles + auditor-readonly pattern + at least 5 trip-wire facts encoded as `expectations[]` lines; harness passes at the H.2 90% CI threshold on the new cases.

**Plans:** 4/4 plans complete
- [x] 12-01-PLAN.md — 6 wiki articles + _index/_graph wiring (WIKI-04)
- [x] 12-02-PLAN.md — 13 KNOWN-GAPS trip-wires + wiki-lint --full extension (WIKI-02)
- [x] 12-03-PLAN.md — /review auditor-readonly Step 4.1 + 5 review cases + 10 ask cases (WIKI-01, WIKI-03, WIKI-05)
- [x] 12-04-PLAN.md — Carry-forward fix: 4 observability articles raw-path → fsi-dsp:// (closes Phase 09 deferred-items)

## Backlog (999.x — parking lot)

Forward-looking work captured during recent sessions. Not committed to a milestone; promoted into a real phase when scope and timing firm up.

### Deferred sub-phases (G.2 carry-forward — promoted at sequencing-time)

- [ ] **G.2a: mcp-confluent tool-call executor** — Dispatch `artifact.type == "mcp-confluent-tool"` to a tool-call sequence executor via stdio MCP from Python. Smallest, most isolated of the remaining G.2 work; proves the MCP-stdio-from-Python plumbing. Unblocked now that G.2c has corrected the tool classification.
- [ ] **G.2b: Composite scenario executor** — Dispatch `artifact.type == "scenario"` to a chained executor that walks an `apply_sequence` field in MANIFEST (fsi-dsp PR required). Re-entrant via the existing dispatcher. Natural follow-on to v2.1 11 (accelerator dispatch shares the layered apply_sequence shape).
- [ ] **G.2d: GitOps apply mode** — Add `apply_mode: "direct" | "gitops"` to overlay config. When `gitops`, executor renders tfvars patch and opens a PR against `fsi-dsp-state` repo; CI runs `terraform apply` under service-account identity. Production-grade FSI path.
- [ ] **G.2e: Ansible-role executor** — Dispatch `artifact.type == "ansible-role"` to `ansible-playbook` against a target inventory. Deferred until an on-prem FSI engagement requires it.

### v2.0 tech debt (per audit — none blocking)

- Extend `/dsp:scaffold` to cover the remaining 4 artifact-types (consumer, kafka-streams-app, schema, cdc-pipeline) — each one phase.
- Add `scaffolded-producer` executor inside `raw/repos/fsi-dsp/` (separate PR) so `/dsp:plan` + `/dsp:apply` can consume scaffolded artifacts.
- Promote CONTEXT-sourced override decisions in `canon/industry/fsi/developer-sandbox/` to formal ADRs after the first customer engagement uses the developer profile in practice.

### 999.1: Phase G.1 — Terraform-module executor for /dsp-apply Step 7 (DELIVERED in v1.0)

Shipped on branch `feat/franz-phase-g1-topic-execution`. `tools/apply_engine.py` gains `ExecutionResult` dataclass + `execute_artifact()` dispatcher + `execute_terraform_module()` runner. Workspace layout: `outputs/runs/<plan_slug>/` per-plan-slug Terraform workspaces.

### 999.2: fsi-dsp PR — module/cc-cluster-basic artifact (DELIVERED, in review)

PR opened against `goodlabs-studio/fsi-dsp` (#2). Once merged, cflt-ai's `raw/repos/fsi-dsp` submodule pointer should be bumped in a follow-up commit. Sibling tier modules (`module/cc-cluster-standard`, `module/cc-cluster-enterprise`, `module/cc-cluster-dedicated`) track as 999.2a–c when prioritized. **NOTE:** v2.1 Phase 9 picks up the pointer bump alongside the LinuxONE accelerator landing.

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
| 9. Submodule sync + canon-parity unblock | v2.1 | 0/2 | Not started | - |
| 10. Accelerator artifact-type registration | v2.1 | 2/3 | Complete    | 2026-05-23 |
| 11. Act-rail wiring for accelerator dispatch | v2.1 | 4/4 | Complete    | 2026-05-23 |
| 12. Wiki ingest of LinuxONE accelerator | v2.1 | 4/4 | Complete   | 2026-05-23 |
| G.2a. mcp-confluent tool-call executor | backlog | 0/1 | Not started | - |
| G.2b. Composite scenario executor | backlog | 0/1 | Not started | - |
| G.2d. GitOps apply mode | backlog | 0/1 | Not started | - |
| G.2e. Ansible-role executor | backlog | 0/1 | Deferred (on-prem demand) | - |
