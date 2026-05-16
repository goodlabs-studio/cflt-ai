# Roadmap: cflt-ai

## Milestones

- ✅ **v1.0 — Foundation through Act Rail** — 9 phases, 26 plans (shipped 2026-05-16). See [`milestones/v1.0-ROADMAP.md`](milestones/v1.0-ROADMAP.md).
- 🚧 **v2.0 — Developer Persona + Quality Gates** — 4 phases planned, 0 complete

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

- [ ] **Phase H.1: Wiki ingest from confluent-agent-skills references** — Compile ~10 peer-reviewed Confluent reference articles into wiki; lift trip-wire facts as high-confidence wiki articles
- [ ] **Phase H.2: Eval harness extension to all skills** — Port confluentinc/agent-skills evals.json pattern (prompt + grep-checkable expectations[] at 90% threshold blocks merge) to /review, /wiki:*, /dsp:plan, /dsp:apply
- [ ] **Phase H.3: Confluent skill plugin install + FSI canon overlay + /dsp:scaffold** — Install streaming-skills-plugin (version-pinned with CI drift gate); author wiki overlay article documenting FSI overrides on top of upstream skills; build /dsp:scaffold wrapper that materializes scaffolded output as canon-compliant fsi-dsp artifacts
- [ ] **Phase H.4: Developer-sandbox profile family + bifurcated FSI canon** — Introduce orthogonal "developer" profile family alongside operator; apply_engine branches on family; FSI canon bifurcates into prod vs dev overlays; acme-bank developer overlay demonstrates customer fork differential gating

### Carry-forward from v1.0 G.2 (deferred sub-phases)

These were promoted from backlog 999.3 into Phase G.2 but only G.2c shipped within v1.0. The remaining sub-phases carry into v2.0 backlog; promote individually when sequencing demands.

- [ ] **G.2a: mcp-confluent tool-call executor** — Dispatch `artifact.type == "mcp-confluent-tool"` to a tool-call sequence executor via stdio MCP from Python. Smallest, most isolated of the remaining G.2 work; proves the MCP-stdio-from-Python plumbing. Unblocked now that G.2c has corrected the tool classification.
- [ ] **G.2b: Composite scenario executor** — Dispatch `artifact.type == "scenario"` to a chained executor that walks an `apply_sequence` field in MANIFEST (fsi-dsp PR required). Re-entrant via the existing dispatcher.
- [ ] **G.2d: GitOps apply mode** — Add `apply_mode: "direct" | "gitops"` to overlay config. When `gitops`, executor renders tfvars patch and opens a PR against `fsi-dsp-state` repo; CI runs `terraform apply` under service-account identity. Production-grade FSI path.
- [ ] **G.2e: Ansible-role executor** — Dispatch `artifact.type == "ansible-role"` to `ansible-playbook` against a target inventory. Deferred until an on-prem FSI engagement requires it.

## Phase Details

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
**Plans:** 0/3 plans
- [x] H.1-01-PLAN.md — Vendor agent-skills@91d1871e, author tools/vendor-sources.json, populate raw/_ingest.md with 19 pending entries
- [ ] H.1-02-PLAN.md — Ingest 10 parent articles (concepts + patterns) with source attestation per D-07; update _index.md and _graph.md
- [ ] H.1-03-PLAN.md — Author 9 trip-wires with full MCP-validation gate (verbatim FSI-context paragraph for WarpStream); extend tools/wiki-lint.py with drift detection per D-09

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
| H.1. Wiki ingest from agent-skills refs | v2.0 | 0/3 | Not started | - |
| H.2. Eval harness extension | v2.0 | 0/4 | Not started | - |
| H.3. confluent-agent-skills install + overlay + /dsp:scaffold | v2.0 | 0/3 | Not started | - |
| H.4. Developer-sandbox profile family + bifurcated FSI canon | v2.0 | 0/3 | Not started | - |
| G.2a. mcp-confluent tool-call executor | v2.0 carry | 0/1 | Not started | - |
| G.2b. Composite scenario executor | v2.0 carry | 0/1 | Not started | - |
| G.2d. GitOps apply mode | v2.0 carry | 0/1 | Not started | - |
| G.2e. Ansible-role executor | v2.0 carry | 0/1 | Deferred (on-prem demand) | - |
