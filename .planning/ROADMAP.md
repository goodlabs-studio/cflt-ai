# Roadmap: cflt-ai

## Milestones

- ✅ **v1.0 — Foundation through Act Rail** — 9 phases, 26 plans (shipped 2026-05-16). See [`milestones/v1.0-ROADMAP.md`](milestones/v1.0-ROADMAP.md).
- 🚧 **v2.0 — Developer Persona + Quality Gates** — 8 phases planned, 2 complete

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

### 🚧 v2.0 — Developer Persona + Quality Gates

- [x] **Phase H.1: Wiki ingest from confluent-agent-skills references** — Compile ~10 peer-reviewed Confluent reference articles into wiki; lift trip-wire facts as high-confidence wiki articles (completed 2026-05-16)
- [x] **Phase H.2: Eval harness extension to all skills** — Port confluentinc/agent-skills evals.json pattern (prompt + grep-checkable expectations[] at 90% threshold blocks merge) to /review, /wiki:*, /dsp:plan, /dsp:apply (completed 2026-05-17)
- [x] **Phase H.3a: Plugin install + canon-overlay wiki article** — Install streaming-skills-plugin; author wiki overlay documenting FSI overrides on top of upstream skills; hook into CLAUDE.md so overlay loads when upstream skills activate (completed 2026-05-17)
- [x] **Phase H.4a: Profile-family schema extension** — Add `family: "operator" | "developer"` field to every profile JSON; branch apply_engine on family; back-compat default to operator (Complete 2026-05-17)
- [x] **Phase H.4b: Developer-sandbox profile + FSI dev canon overlay** — Author developer-sandbox profile with `tool_overrides` for data-plane ops; bifurcate FSI canon into prod/dev overlays; negative-space test matrix proves operator-only tools fail closed under developer family (Complete 2026-05-17)
- [ ] **Phase H.4c: acme-bank developer overlay** — Customer-fork demo: acme-bank developer overlay produces differential gating against base FSI dev canon; mirrors v1.0 ACTG-04 for the developer family
- [ ] **Phase H.3b: Version pin + CI drift gate** — Pin streaming-skills-plugin version in `tools/vendor-plugins.json`; add `.github/workflows/streaming-skills-drift.yml` mirroring G.2c pattern exactly
- [ ] **Phase H.3c: /dsp:scaffold wrapper** — New cflt-ai skill wrapping upstream scaffolders; materializes output as canon-compliant fsi-dsp artifact (MANIFEST entry, activity log, profile-gated). Hard prereq: H.4c (canon family must exist)

### Deferred sub-phases (G.2 carry-forward)

These were promoted from backlog 999.3 into Phase G.2 but only G.2c shipped earlier. The remaining sub-phases carry into v2.0 backlog; promote individually when sequencing demands.

- [ ] **G.2a: mcp-confluent tool-call executor** — Dispatch `artifact.type == "mcp-confluent-tool"` to a tool-call sequence executor via stdio MCP from Python. Smallest, most isolated of the remaining G.2 work; proves the MCP-stdio-from-Python plumbing. Unblocked now that G.2c has corrected the tool classification.
- [ ] **G.2b: Composite scenario executor** — Dispatch `artifact.type == "scenario"` to a chained executor that walks an `apply_sequence` field in MANIFEST (fsi-dsp PR required). Re-entrant via the existing dispatcher.
- [ ] **G.2d: GitOps apply mode** — Add `apply_mode: "direct" | "gitops"` to overlay config. When `gitops`, executor renders tfvars patch and opens a PR against `fsi-dsp-state` repo; CI runs `terraform apply` under service-account identity. Production-grade FSI path.
- [ ] **G.2e: Ansible-role executor** — Dispatch `artifact.type == "ansible-role"` to `ansible-playbook` against a target inventory. Deferred until an on-prem FSI engagement requires it.

## Phase Details

**Theme:** Expand cflt-ai from SA-only (operator profiles) to cover the developer persona inside customer engagements, and introduce evaluation discipline across every skill so quality stops drifting silently. Triggered by the `confluentinc/agent-skills` release (2026-03-13) which provides four production-ready developer skills (kafka-streams, python-client, schema-registry, CDC-to-Tableflow) we can incorporate as upstream tooling.

**Recommended execution order:** H.1 → H.2 → H.3a → H.4a → H.4b → H.4c → H.3b → H.3c. H.3c is last because `/dsp:scaffold` needs both the installed plugin (H.3a/b) and the developer canon family (H.4b/c) to materialize artifacts under the correct profile family. H.3b is grouped late so H.4a–c can proceed in parallel with overlay-article work in H.3a; the version-pin gate has no functional dependency on the canon work.

**Restructure note (2026-05-17):** Original H.3 and H.4 phases were split into 6 first-class GSD phases (H.3a, H.3b, H.3c, H.4a, H.4b, H.4c) so each sub-phase becomes a single-plan unit the GSD tooling can drive sequentially. Goal and success-criteria text below preserves the original H.3/H.4 substance.

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
**Plans:** 3/3 plans complete
- [x] H.1-01-PLAN.md — Vendor agent-skills@91d1871e, author tools/vendor-sources.json, populate raw/_ingest.md with 19 pending entries
- [x] H.1-02-PLAN.md — Ingest 10 parent articles (concepts + patterns) with source attestation per D-07; update _index.md and _graph.md
- [x] H.1-03-PLAN.md — Author 9 trip-wires with full MCP-validation gate (verbatim FSI-context paragraph for WarpStream); extend tools/wiki-lint.py with drift detection per D-09

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
**Plans:** 4/4 plans complete
- [x] H.2-01-PLAN.md — Pytest runner + MD/JSON adapters + 90% per-skill threshold gate + adapter unit tests
- [x] H.2-02-PLAN.md — Author 4 new wiki-skill evals.json (40 cases incl. 2 D-08 trip-wires in /wiki:ingest)
- [x] H.2-03-PLAN.md — Author 3 thin-wrapper evals.json for /review, /dsp:plan, /dsp:apply (55 cases incl. 7 D-08 trip-wires)
- [x] H.2-04-PLAN.md — CI workflow .github/workflows/skill-evals.yml + final phase-exit regression gate

### Phase H.3a: Plugin install + canon-overlay wiki article
**Goal:** Install `streaming-skills-plugin` so the four upstream Confluent skills (kafka-streams, python-client, schema-registry, CDC-tableflow) become available inside Claude Code sessions, and author a wiki overlay article documenting the FSI-specific overrides on top of upstream skill defaults (mTLS, exactly_once_v2, schema format, compatibility mode, etc.). Hook into cflt-ai's CLAUDE.md so the overlay article is read whenever an upstream skill activates. Smallest, fastest, immediate value — proves the install path and gives developers FSI guardrails the moment they invoke an upstream skill.
**Depends on:** H.1 (canon overlay article cites ingested reference articles).
**Requirements:** INST-01, CAN-OVR-01
**Success Criteria** (what must be TRUE):
  1. `streaming-skills-plugin` is installed (via `/plugin install streaming-skills-plugin@confluent-agent-skills` or marketplace add + install); install state visible in claude config; the four upstream skills appear in `/help` skill listings.
  2. `wiki/patterns/fsi-canon-overlay-for-confluent-skills.md` exists with per-upstream-skill override tables (4 sections: kafka-streams, python-client, schema-registry, CDC-tableflow), each listing FSI overrides that must apply on top of upstream defaults.
  3. CLAUDE.md (cflt-ai project file) references the overlay article in the canon section so upstream-skill activations pick up the FSI overrides automatically.
  4. `/wiki:validate` against MCP sources passes on the overlay article (zero drift findings); article has `confidence: high` frontmatter with `last_validated: <today>`.
**Plans:** 1/1 plan complete (H.3a-01-PLAN.md → H.3a-01-SUMMARY.md, 2026-05-17)

### Phase H.4a: Profile-family schema extension
**Goal:** Add `family: "operator" | "developer"` field to every profile JSON; update `apply_engine.load_profile()` and `check_tool_permitted()` to read the family and branch behavior (operator → existing tier cascade; developer → new `tool_overrides` map). Default to `"operator"` when absent for back-compat. No behavior change yet — just schema groundwork that unblocks H.4b.
**Depends on:** Nothing structural.
**Requirements:** PROFAM-01, PROFAM-02
**Success Criteria** (what must be TRUE):
  1. Every existing profile JSON has a `family: "operator"` field; absence of field defaults to `"operator"` in `load_profile()` (verified by unit test on a fixture profile with no family field).
  2. `check_tool_permitted()` branches on family — operator path uses the existing tier cascade, developer path reads a `tool_overrides` map; both branches unit-tested (developer branch tested via fixture profile, no real developer profile required yet).
  3. JSON Schema for profiles validates the new `family` field and rejects unknown values with a clear error.
  4. All existing operator-profile tests still pass — zero behavior change for operator family.
**Plans:** 1/1 plan complete (H.4a-01-PLAN.md → H.4a-01-SUMMARY.md, 2026-05-17)

### Phase H.4b: Developer-sandbox profile + FSI dev canon overlay
**Goal:** Author `tools/profiles/developer/sandbox.json` with `family: "developer"`, `primary_tooling.skills` allowlist for upstream confluent-agent-skills, `tool_overrides` promoting data-plane ops (produce-message, consume-messages, create-topics, delete-topics, alter-topic-config, create-flink-statement, delete-flink-statements) to `developer-sandbox` tier, `skill_blocklist` excluding `/dsp:apply`, and a soft `environment_guard` pattern matching sandbox/dev cluster names. Author `canon/industry/fsi/developer-sandbox/` overlay with the bifurcated dev defaults (OAUTHBEARER, at_least_once, JSON Schema OK, BACKWARD compatibility). Negative-space test matrix proves operator-tier-only tools fail closed under developer-sandbox and `/dsp:apply` refuses to run.
**Depends on:** H.4a (family schema must exist).
**Requirements:** DEVPROF-01, DEVCAN-01, DEVPROF-02
**Success Criteria** (what must be TRUE):
  1. `tools/profiles/developer/sandbox.json` exists with the shape documented above and passes JSON Schema validation.
  2. `canon/industry/fsi/developer-sandbox/` overlay exists and contains every Confluent Canon dimension from CLAUDE.md with explicit dev-tier values (auth, processing.guarantee, schema format, compatibility, RF, ISR, retention, naming convention).
  3. Per-profile-family negative-space test suite runs and proves: operator profiles cannot invoke `tool_overrides` entries from developer family, and developer profiles cannot invoke operator-tier-only tools (e.g., `delete-environment`, `create-cluster`); `/dsp:apply` fails closed under developer-sandbox with explicit error message referencing the family.
**Plans:** 1/1 plan (H.4b-01-PLAN.md ✓ — see H.4b-01-SUMMARY.md)

### Phase H.4c: acme-bank developer overlay
**Goal:** Mirror v1.0 Phase 3c ACTG-04 for the developer family. `canon/customer/acme-bank/profiles/developer/sandbox.json` overlays the FSI developer canon with acme-specific topic naming, environment patterns (e.g., `acme-*-sandbox`), pre-approved upstream connector list, additional `skill_blocklist` entries. Test demonstrates the customer overlay produces a differential gating result against base FSI dev canon — proves customer-fork differential gating works for the developer family the same way it does for the operator family.
**Depends on:** H.4b (FSI dev canon overlay must exist to fork from).
**Requirements:** DEVPROF-02 (customer-fork extension)
**Success Criteria** (what must be TRUE):
  1. `canon/customer/acme-bank/profiles/developer/sandbox.json` exists and a test demonstrates the customer overlay produces at least one differential gating decision relative to base FSI dev canon (e.g., a tool/topic/connector permitted under base FSI dev canon is denied under acme-bank, or vice versa).
  2. acme-bank developer overlay test mirrors the ACTG-04 pattern from v1.0 Phase 3c — same assertion shape for engineer family, adapted to developer family.
**Plans:** 0/1 plan (H.4c-01-PLAN.md)

### Phase H.3b: Version pin + CI drift gate
**Goal:** Pin `streaming-skills-plugin` version inside `tools/vendor-plugins.json` (new file, or merge into existing `tools/vendor-sources.json` schema); add `.github/workflows/streaming-skills-drift.yml` that fails on PR when the upstream plugin manifest version changes without a matching pin update. Mirrors the G.2c pattern exactly — same generator / `--check` mode / CI-gate shape — so the upstream-pin discipline is consistent across vendor sources (H.1) and vendor plugins (here).
**Depends on:** H.3a (plugin must be installed to know what to pin).
**Requirements:** INST-01 (drift gate)
**Success Criteria** (what must be TRUE):
  1. `tools/vendor-plugins.json` exists (or extended `tools/vendor-sources.json` with a `claude-plugin` kind) and contains the pinned `streaming-skills-plugin` version + upstream commit/ref.
  2. `.github/workflows/streaming-skills-drift.yml` exists, runs on PR, and fails when the upstream plugin's `plugin.json` version field differs from the pinned version without a matching update to the pin file.
  3. Drift-gate generator has a `--check` mode that exits non-zero on drift (mirrors G.2c's generator/`--check` shape exactly; same script pattern, swapped target).
**Plans:** 0/1 plan (H.3b-01-PLAN.md)

### Phase H.3c: /dsp:scaffold wrapper
**Goal:** New cflt-ai skill `/dsp:scaffold <artifact-type> <name>` that triages a scaffolding request, picks the right upstream skill to invoke (from streaming-skills-plugin), applies the active profile-family canon overlay as structured config (not just prose hints), invokes the upstream skill, then registers the scaffolded output as an artifact entry in fsi-dsp's `MANIFEST.yaml` with a capability block and provenance footer. Profile-gated (engineer family can scaffold prod artifacts; developer-sandbox family can scaffold dev artifacts; read-only cannot scaffold at all). Activity-logged with full provenance.
**Depends on:** H.3a (plugin installed), H.3b (pin in place so scaffold output references a stable upstream version), H.4c (canon families exist so scaffold can apply the right one).
**Requirements:** SCAF-01, SCAF-02, SCAF-03
**Success Criteria** (what must be TRUE):
  1. `/dsp:scaffold <artifact-type> <name>` exists as a cflt-ai skill and runs end-to-end for at least one artifact type (e.g., `/dsp:scaffold producer my-payments-producer`).
  2. Scaffolded output for that one type appears as a new MANIFEST.yaml capability entry in fsi-dsp with full provenance (operator, profile, canon-stack hash, timestamp, upstream-skill version).
  3. `/dsp:scaffold` refuses to run under `read-only` profile and refuses to scaffold a prod-canon artifact under `developer-sandbox` profile (negative-space tests prove fail-closed with explicit error messages).
**Plans:** 0/1 plan (H.3c-01-PLAN.md)

## Backlog (999.x — parking lot)

Forward-looking work captured during recent sessions. Not committed to a milestone; promoted into a real phase when scope and timing firm up.

### 999.1: Phase G.1 — Terraform-module executor for /dsp-apply Step 7 (DELIVERED in v1.0)

Shipped on branch `feat/franz-phase-g1-topic-execution`. `tools/apply_engine.py` gains `ExecutionResult` dataclass + `execute_artifact()` dispatcher + `execute_terraform_module()` runner. Workspace layout: `outputs/runs/<plan_slug>/` per-plan-slug Terraform workspaces.

### 999.2: fsi-dsp PR — module/cc-cluster-basic artifact (DELIVERED, in review)

PR opened against `goodlabs-studio/fsi-dsp` (#2). Once merged, cflt-ai's `raw/repos/fsi-dsp` submodule pointer should be bumped in a follow-up commit. Sibling tier modules (`module/cc-cluster-standard`, `module/cc-cluster-enterprise`, `module/cc-cluster-dedicated`) track as 999.2a–c when prioritized.

### 999.3: PROMOTED → Phase G.2 (partially delivered in v1.0)

G.2c shipped in v1.0. G.2a, G.2b, G.2d, G.2e carry forward into v2.0 backlog (see active phases list above). Detailed scope retained for promotion when sequencing demands.

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
| H.4b. Developer-sandbox profile + FSI dev canon | v2.0 | 0/1 | Not started | - |
| H.4c. acme-bank developer overlay | v2.0 | 0/1 | Not started | - |
| H.3b. Version pin + CI drift gate | v2.0 | 0/1 | Not started | - |
| H.3c. /dsp:scaffold wrapper | v2.0 | 0/1 | Not started | - |
| G.2a. mcp-confluent tool-call executor | v2.0 carry | 0/1 | Not started | - |
| G.2b. Composite scenario executor | v2.0 carry | 0/1 | Not started | - |
| G.2d. GitOps apply mode | v2.0 carry | 0/1 | Not started | - |
| G.2e. Ansible-role executor | v2.0 carry | 0/1 | Deferred (on-prem demand) | - |
