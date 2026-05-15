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
- [x] **Phase G.2c: Tool-classification rename** - Aligned tool_classification.json with live mcp-confluent 1.3.0 (54 kebab-case tools, fictional snake_case purged); bidirectional CI drift gate; ACTG-01..04 preserved (completed 2026-05-15)
- [ ] **Phase G.2: Composite + GitOps + tool-call execution** - Promoted from backlog 999.3; G.2c shipped; G.2a/G.2b/G.2d/G.2e remain (see Phase Details)

**Milestone v2.0 — Developer Persona + Quality Gates**

- [ ] **Phase H.1: Wiki ingest from confluent-agent-skills references** - Compile ~10 peer-reviewed Confluent reference articles (topology-patterns, debugging, production-hardening, cdc-to-tableflow, schema-registry-migration) into wiki; lift trip-wire facts as high-confidence wiki articles
- [ ] **Phase H.2: Eval harness extension to all skills** - Port confluentinc/agent-skills evals.json pattern (prompt + grep-checkable expectations[] at 90% threshold blocks merge) to /review, /wiki:*, /dsp:plan, /dsp:apply — closes silent-drift gap
- [ ] **Phase H.3: Confluent skill plugin install + FSI canon overlay + /dsp:scaffold** - Install streaming-skills-plugin (version-pinned with CI drift gate); author wiki overlay article documenting FSI overrides on top of upstream skills; build /dsp:scaffold wrapper that materializes scaffolded output as canon-compliant fsi-dsp artifacts
- [ ] **Phase H.4: Developer-sandbox profile family + bifurcated FSI canon** - Introduce orthogonal "developer" profile family alongside operator (read-only/engineer/break-glass); apply_engine branches on family; FSI canon bifurcates into prod vs dev overlays; acme-bank developer overlay demonstrates customer fork differential gating

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
- [x] G.2c-02-PLAN.md — Regenerate tool_classification.json against mcp-confluent@1.3.0; rewrite hard-coded snake_case test refs (ACTG-01, ACTG-02, ACTG-03, ACTG-04)
- [x] G.2c-03-PLAN.md — Add tool-classification-drift CI workflow (ACTG-01)
- [ ] G.2d-PLAN.md — GitOps apply mode (depends on `fsi-dsp-state` infrastructure)
- [ ] G.2e-PLAN.md — Ansible-role executor (deferred until on-prem FSI engagement requires it)

**Recommended execution order:** G.2c → G.2a → G.2b → G.2d → G.2e. G.2c is a hygiene fix that unblocks G.2a (G.2a's executor must look up real kebab-case tool names in classification); G.2a is the smallest executor and proves the MCP-stdio-from-Python plumbing; G.2b consumes the executor pattern from G.2a + G.1; G.2d is the largest architectural change (CI repo, service accounts); G.2e waits for demand.

**G.2c wave structure:** G.2c-01 (wave 1) authors the generator. G.2c-02 and G.2c-03 (both wave 2) can run in parallel — they share no files (02 modifies `tools/profiles/tool_classification.json` + `tests/test_apply_engine.py`; 03 modifies `.github/workflows/tool-classification-drift.yml`).

---

# Milestone v2.0 — Developer Persona + Quality Gates

**Theme:** Expand cflt-ai from SA-only (operator profiles) to cover the developer persona inside customer engagements, and introduce evaluation discipline across every skill so quality stops drifting silently. Triggered by the `confluentinc/agent-skills` release (2026-03-13) which provides four production-ready developer skills (kafka-streams, python-client, schema-registry, CDC-to-Tableflow) we can incorporate as upstream tooling.

**Recommended execution order:** H.1 → H.3a (install + canon overlay article) → H.4 (developer-sandbox profile family) → H.3b (version-pin CI gate) → H.3c (/dsp:scaffold wrapper) → H.2 (eval harness extension). H.3c depends on H.4 because `/dsp:scaffold` needs to know which canon family (operator-prod vs developer-sandbox) to materialize.

### Phase H.1: Wiki ingest from confluent-agent-skills references
**Goal:** Compile the peer-reviewed reference articles inside `confluentinc/agent-skills/skills/*/references/` into our wiki, and lift the embedded trip-wire facts into individual high-confidence articles. After H.1, our wiki has authoritative coverage of Kafka Streams topology/debugging/production-hardening, Schema Registry adoption playbook, CDC-to-Tableflow pipeline construction, and the dozen-or-so hard-won correctness facts (Tableflow tombstone immutability, KS 4.x nested-class rename, Avro source path, OracleXStream `after.state.only` limitation, WarpStream SR format constraint, etc.).
**Depends on:** Nothing (additive content work). Best to run before H.3 so `/dsp:scaffold` has wiki articles to cite.
**Requirements:** WIKI-06, WIKI-07, WIKI-08
**Success Criteria** (what must be TRUE):
  1. `/wiki:ingest` has compiled at least 10 articles sourced from the four `confluentinc/agent-skills` reference directories (kafka-streams-programming, developing-kafka-python-client, kafka-schema-registry, confluent-cloud-cdc-tableflow)
  2. At least 8 trip-wire facts exist as individual `wiki/concepts/` or `wiki/patterns/` articles with `confidence: high` and `last_validated: <today>` frontmatter, each citing the upstream source path
  3. `/wiki:validate` against MCP sources passes on every ingested article (zero drift findings)
  4. `wiki/_index.md` and `wiki/_graph.md` are updated to reflect new articles
  5. Source provenance footers in each article reference the upstream `confluentinc/agent-skills@<commit-sha>` so re-ingest after upstream updates is mechanical
**Plans:** 0/3 plans (planned: ingest pipeline run, trip-wire article authoring, validation pass)

### Phase H.2: Eval harness extension to all cflt-ai skills
**Goal:** Every cflt-ai skill has an `evals/evals.json` file scoring prompts against grep-checkable `expectations[]` assertions, with CI failing PRs that drop below 90% pass rate. Closes the silent-drift gap where `/review`, `/wiki:*`, `/dsp:plan`, and `/dsp:apply` have no behavioral regression guard today. Ports the `confluentinc/agent-skills` evals.json schema verbatim so future cross-pollination is straightforward.
**Depends on:** Nothing structurally, but most useful after H.1 (so trip-wire facts become eval expectations) and H.3 (so /dsp:scaffold has evals from day one). Run last in milestone for maximum coverage.
**Requirements:** EVAL-01, EVAL-02, EVAL-03
**Success Criteria** (what must be TRUE):
  1. `evals/evals.json` exists for each of: /review, /wiki:ingest, /wiki:validate, /wiki:lint, /wiki:recommend, /dsp:plan, /dsp:apply (existing /ask harness stays as-is; it predates this schema and works)
  2. Each skill's evals file has ≥10 cases, each with `prompt`, `expected_output`, and `expectations[]` array of grep-checkable assertions
  3. A pytest-based runner at `tests/evals/run_skill_evals.py` parametrizes over every skill × case and reports pass rate per skill
  4. A new CI workflow `.github/workflows/skill-evals.yml` runs the harness on PR; merges blocked when any skill drops below 90% pass rate (matches the `confluentinc/agent-skills` threshold)
  5. At least 5 trip-wire facts from H.1 are encoded as `expectations[]` lines so wiki + skills stay in sync (e.g., "asks about target environment before generating producer code", "uses kafka-avro-console-producer not kafka-console-producer")
**Plans:** 0/4 plans (planned: harness runner + schema, per-skill evals authoring split across 2 plans, CI workflow + threshold gate)

### Phase H.3: confluent-agent-skills install + FSI canon overlay + /dsp:scaffold
**Goal:** Install `streaming-skills-plugin` so the four upstream Confluent skills become available inside Claude Code sessions; pin its version with a CI drift check that mirrors G.2c's pattern; author wiki overlay articles that document the FSI-specific overrides on top of upstream skill defaults (mTLS, exactly_once_v2, schema format, etc.); build a new `/dsp:scaffold <artifact-type> <name>` skill that wraps the upstream scaffolders so their output materializes as a canon-compliant fsi-dsp artifact (registered in MANIFEST.yaml, activity-logged, profile-gated, ready for downstream `/dsp:apply`).
**Depends on:** H.1 (the canon overlay article needs the ingested reference articles to cite). H.4 is a soft prereq for H.3c — `/dsp:scaffold` needs the profile family to know which canon to materialize.
**Requirements:** INST-01, CAN-OVR-01, SCAF-01, SCAF-02, SCAF-03

**Sub-phases (each its own PLAN.md):**

- **H.3a: Plugin install + canon-overlay wiki article** (~half day) — `/plugin marketplace add confluentinc/agent-skills`; `/plugin install streaming-skills-plugin@confluent-agent-skills`; author `wiki/patterns/fsi-canon-overlay-for-confluent-skills.md` per upstream skill (4 sections), each listing the FSI-canon overrides that must apply on top of the upstream defaults; hook into cflt-ai's CLAUDE.md so the overlay article is read whenever an upstream skill activates. Smallest, fastest, immediate value.
- **H.3b: Version pin + CI drift gate** (~half day) — Pin `streaming-skills-plugin` version inside `.planning/config.json` (or a new `tools/vendor-plugins.json`); add `.github/workflows/streaming-skills-drift.yml` that warns on upstream plugin manifest changes. Mirrors the G.2c pattern exactly — same generator/`--check`/CI-gate shape.
- **H.3c: `/dsp:scaffold` skill** (~1 week) — New cflt-ai skill that triages a scaffolding request, picks the right upstream skill to invoke, applies the active profile-family canon overlay as structured config (not just prose), invokes the upstream skill, then registers the scaffolded output as an artifact entry in fsi-dsp's `MANIFEST.yaml` with a capability block and provenance footer. Profile-gated (engineer family can scaffold prod artifacts; developer-sandbox family can scaffold dev artifacts; read-only cannot scaffold at all). Activity-logged. Hard prereq: H.4 (canon family must exist before scaffold can apply it).

**Success Criteria** (what must be TRUE):
  1. `streaming-skills-plugin` is installed and version-pinned in repo; pinned version visible in `tools/vendor-plugins.json` (or equivalent)
  2. `.github/workflows/streaming-skills-drift.yml` exists and fails on PR when the upstream plugin's `plugin.json` version field changes without a matching pin update
  3. `wiki/patterns/fsi-canon-overlay-for-confluent-skills.md` exists with per-upstream-skill override tables (4 sections: kafka-streams, python-client, schema-registry, CDC-tableflow)
  4. `/dsp:scaffold <artifact-type> <name>` exists as a cflt-ai skill and runs end-to-end for at least one artifact type (e.g., `/dsp:scaffold producer my-payments-producer`)
  5. Scaffolded output for that one type appears as a new MANIFEST.yaml capability entry in fsi-dsp with full provenance (operator, profile, canon-stack hash, timestamp, upstream-skill version)
  6. `/dsp:scaffold` refuses to run under `read-only` profile and refuses to scaffold a prod-canon artifact under `developer-sandbox` profile (negative-space tests prove fail-closed)
**Plans:** 0/3 plans (H.3a, H.3b, H.3c — one PLAN.md per sub-phase)

### Phase H.4: Developer-sandbox profile family + bifurcated FSI canon
**Goal:** Introduce a second profile family — `developer` — alongside the existing operator tier hierarchy. The developer family doesn't extend the read-only/engineer/break-glass cascade; it runs orthogonally with its own allowed-skills list, its own data-plane scope (sandbox-only mcp-confluent write ops like produce-message/consume-messages/create-topics), and its own canon overlay. FSI canon bifurcates into a prod overlay (operator-tier, mTLS + exactly_once_v2 + Avro/Protobuf + FULL compatibility) and a dev overlay (developer-tier, OAUTHBEARER + at_least_once + JSON Schema OK + BACKWARD compatibility). acme-bank gets a developer overlay demonstrating customer-fork differential gating, mirroring ACTG-04 for the developer family.
**Depends on:** Nothing structurally — can run parallel to H.3a/H.3b. Hard prereq for H.3c (scaffold wrapper needs to know which canon family to materialize).
**Requirements:** PROFAM-01, PROFAM-02, DEVPROF-01, DEVCAN-01, DEVPROF-02

**Sub-phases:**

- **H.4a: Profile-family schema extension** (~half day) — Add `family: "operator" | "developer"` field to every profile JSON; update `apply_engine.load_profile()` and `check_tool_permitted()` to read the family and branch behavior (operator → tier cascade; developer → `tool_overrides` map). Default to `"operator"` when absent for back-compat. No behavior change yet — just schema groundwork.
- **H.4b: Developer-sandbox profile + FSI dev canon overlay** (~1 day) — Author `tools/profiles/developer/sandbox.json` with `family: "developer"`, `primary_tooling.skills` allowlist for upstream confluent-agent-skills, `tool_overrides` promoting data-plane ops (produce-message, consume-messages, create-topics, delete-topics, alter-topic-config, create-flink-statement, delete-flink-statements) to `developer-sandbox` tier, `skill_blocklist` excluding `/dsp:apply`, and a soft `environment_guard` pattern matching sandbox/dev cluster names. Author `canon/industry/fsi/developer-sandbox/` overlay with the bifurcated dev defaults. Negative-space test matrix: per-profile-family parametrized assertion that no operator-tier-only tool runs under developer-sandbox, and `/dsp:apply` is fail-closed under developer-sandbox.
- **H.4c: acme-bank developer overlay + customer-fork demo** (~half day) — Mirror Phase 3c ACTG-04 for the developer family. `canon/customer/acme-bank/profiles/developer/sandbox.json` overlays the FSI developer canon with acme-specific topic naming, environment patterns (e.g., `acme-*-sandbox`), pre-approved upstream connector list, additional skill_blocklist entries. Test demonstrates the customer overlay produces a differential result against base FSI dev canon.

**Success Criteria** (what must be TRUE):
  1. Every profile JSON file has a `family` field, value `"operator"` or `"developer"`; `load_profile()` parses it; `check_tool_permitted()` branches on it (verified by unit tests)
  2. `tools/profiles/developer/sandbox.json` exists with the shape documented in H.4 context and passes JSON Schema validation
  3. `canon/industry/fsi/developer-sandbox/` overlay exists and contains every Confluent Canon dimension from CLAUDE.md with explicit dev-tier values (auth, processing.guarantee, schema format, compatibility, RF, ISR, retention, naming convention)
  4. Per-profile-family negative-space test suite runs and proves: operator profiles cannot invoke `tool_overrides` entries from developer family, and developer profiles cannot invoke operator-tier-only tools (e.g., `delete-environment`, `create-cluster`); `/dsp:apply` fails closed under developer-sandbox with explicit error message
  5. `canon/customer/acme-bank/profiles/developer/sandbox.json` exists and a test demonstrates the customer overlay produces at least one differential gating decision relative to base FSI dev canon
**Plans:** 0/3 plans (H.4a, H.4b, H.4c — one PLAN.md per sub-phase)

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

**Milestone v1.0 execution order:**
Phases execute in sequence: 0 → 1 → 2 → 3a → 3b → 3c → F.1 → G.1 → G.2

**Milestone v2.0 recommended order:**
H.1 → H.3a → H.4 → H.3b → H.3c → H.2 (H.3c soft-depends on H.4; H.2 closes the milestone with eval coverage of every prior delivery)

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
| G.2c. Tool-classification rename | 3/3 | Complete    | 2026-05-15 |
| G.2. Composite + GitOps + tool-call execution | 1/5 | G.2c done; G.2a/b/d/e planning needed | - |
| **v2.0** | | | |
| H.1. Wiki ingest from agent-skills refs | 0/3 | Planning needed | - |
| H.2. Eval harness extension | 0/4 | Planning needed | - |
| H.3. confluent-agent-skills install + canon overlay + /dsp:scaffold | 0/3 | Planning needed | - |
| H.4. Developer-sandbox profile family + bifurcated FSI canon | 0/3 | Planning needed | - |
