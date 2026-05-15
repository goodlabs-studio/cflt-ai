# Requirements: cflt-ai

**Defined:** 2026-04-28
**Core Value:** Canon overlay stack works — customers can fork and override safely

## v1 Requirements

Requirements for v1 milestone (Phase 0 through Phase 3c).

### Hygiene

- [x] **HYG-01**: wiki-stats.py syntax errors fixed and tool runs without crashes
- [x] **HYG-02**: wiki-lint.py broken-link regex correctly matches all wiki-internal link formats including anchors
- [x] **HYG-03**: evaluate.md literal-ellipsis paths resolved to real file references
- [x] **HYG-04**: Flox manifest committed in cflt-ai and works on clean clone
- [x] **HYG-05**: Flox manifest committed in fsi-kafka-platform and works on clean clone

### Contract

- [x] **CNTR-01**: MANIFEST.yaml v1 published with capabilities blocks for every existing fsi-dsp asset
- [x] **CNTR-02**: Wiki citations migrated from prose references to MANIFEST.yaml ID form
- [x] **CNTR-03**: CI parity checks green in both repos (cflt-ai and fsi-kafka-platform)
- [x] **CNTR-04**: fsi-dsp blocks PRs that drop a stable ID without a major bump
- [x] **CNTR-05**: cflt-ai blocks PRs where any wiki citation fails to resolve against MANIFEST.yaml

### Canon Stack

- [x] **CANST-01**: Canon overlay stack scaffolding present (base → industry → customer → engagement layers)
- [x] **CANST-02**: Each overlay layer can override defaults from the layer above
- [x] **CANST-03**: Every override is an ADR in the layer that introduces it
- [x] **CANST-04**: Active stack recorded in artifact provenance footers

### Wiki

- [x] **WIKI-01**: LinuxONE wiki articles ingested from fsi-dsp adr/009 and LinuxONE guides
- [x] **WIKI-02**: Activity log directory live and emitting per overlay-scoped path
- [x] **WIKI-03**: last_validated field added to wiki articles with quarterly decay rule
- [x] **WIKI-04**: confidence:high articles drop to medium after 90 days without revalidation
- [x] **WIKI-05**: Auto-stub on coverage gap — every /ask miss appends to wiki/_queue.md

### Knowledge Skill

- [x] **KNOW-01**: /ask and /wiki:recommend collapsed into single skill with --mode flag (ephemeral | report | reconsolidate)
- [x] **KNOW-02**: Triage classifier routes queries: wiki-only / wiki+MCP / deep reasoning
- [x] **KNOW-03**: Golden test harness at tests/golden/ask/ with >= 30 cases including >= 5 negative-space cases
- [x] **KNOW-04**: Floor-model pass rate >= 90% on Haiku-floor cases
- [x] **KNOW-05**: Floor-model pass rate >= 95% on Sonnet-floor cases

### Review Skill

- [x] **REVW-01**: Claim extraction reproducibility >= 95% across runs (same doc → same claims)
- [x] **REVW-02**: Explicit premise-challenge step shipped and tested in harness
- [x] **REVW-03**: .docx output with full provenance footer (canon stack hash, manifest version, model floors, MCP versions)
- [x] **REVW-04**: Multi-document review supported (deck + tfvars + runbook as single input)
- [x] **REVW-05**: Golden test harness at tests/golden/review/ with >= 15 cases from sanitized customer docs
- [x] **REVW-06**: >= 1 customer overlay validated end-to-end with differential canon override

### Act Rail (Plan)

- [x] **ACT-01**: Terraform MCP wired into .mcp.json
- [x] **ACT-02**: Four-gate validation chain implemented (canon compliance → fsi-dsp coverage → confluent-docs schema → mcp-confluent state)
- [x] **ACT-03**: Each gate individually testable and bypassable in dev mode
- [x] **ACT-04**: /dsp:plan read-only act rail skill implemented
- [x] **ACT-05**: Golden test harness at tests/golden/act/ with >= 20 cases including negative-space
- [x] **ACT-06**: Agent never generates inline Terraform; never invokes mcp-confluent write tools directly
- [x] **ACT-07**: Structural correctness >= 95% (right artifact selected, right arguments, schemas validate)
- [x] **ACT-08**: Canon <-> fsi-dsp parity test running in both repos' CI and blocking on drift

### Act Rail (Apply)

- [x] **ACTA-01**: /dsp:apply skill with human-in-the-loop confirmation enforced
- [x] **ACTA-02**: Bypass attempts tested and blocked
- [x] **ACTA-03**: Three policy profiles implemented: read-only.json, engineer.json, break-glass.json
- [x] **ACTA-04**: Activity log captures every plan/apply with full provenance
- [x] **ACTA-05**: Wiki incident entry written per apply
- [x] **ACTA-06**: Structural-correctness metric holds for 30 days of real engagement use

### Act Rail (Profile Gating)

- [x] **ACTG-01**: Every mcp-confluent tool (50+) classified into a profile by name, not regex
- [x] **ACTG-02**: Per-profile negative-space test suite ensures forbidden tools fail closed
- [x] **ACTG-03**: Break-glass profile requires two-step confirmation with explicit override reason logged
- [x] **ACTG-04**: >= 1 customer fork demonstrates differential profile gating relative to base

## v2.0 Requirements

Active milestone — Developer Persona + Quality Gates. Triggered by `confluentinc/agent-skills` release (2026-03-13) which provides four production-ready developer skills we can incorporate.

### Wiki Ingest from Upstream Skills (H.1)

- **WIKI-06**: `/wiki:ingest` compiles ≥10 articles from `confluentinc/agent-skills/skills/*/references/` into `wiki/concepts/` and `wiki/patterns/`, each with upstream provenance footer (source path + commit SHA)
- **WIKI-07**: ≥8 trip-wire facts (Tableflow tombstone immutability, KS 4.x nested-class rename, Avro source path, OracleXStream `after.state.only` limitation, WarpStream SR format constraint, kafka-console-producer vs kafka-avro-console-producer, etc.) exist as standalone wiki articles with `confidence: high` and `last_validated: <today>`
- **WIKI-08**: `/wiki:validate` against MCP sources passes on every ingested article (zero drift findings); `wiki/_index.md` and `wiki/_graph.md` updated

### Eval Harness Extension (H.2)

- **EVAL-01**: `tests/evals/run_skill_evals.py` runner parametrizes over every `skills/*/evals/evals.json` × case using the `confluentinc/agent-skills` schema (`prompt`, `expected_output`, grep-checkable `expectations[]`)
- **EVAL-02**: Each of `/review`, `/wiki:ingest`, `/wiki:validate`, `/wiki:lint`, `/wiki:recommend`, `/dsp:plan`, `/dsp:apply` has `evals/evals.json` with ≥10 cases (existing `/ask` golden harness stays as-is)
- **EVAL-03**: `.github/workflows/skill-evals.yml` runs the harness on PR; merges blocked when any skill drops below 90% pass rate; ≥5 trip-wire facts from H.1 are encoded as `expectations[]` assertions

### Plugin Install + Canon Overlay + Scaffold (H.3)

- **INST-01**: `streaming-skills-plugin` installed via Claude marketplace; version pinned in `tools/vendor-plugins.json`; `.github/workflows/streaming-skills-drift.yml` fails PRs that bump the upstream plugin without updating the pin (mirrors G.2c drift-gate pattern)
- **CAN-OVR-01**: `wiki/patterns/fsi-canon-overlay-for-confluent-skills.md` exists with one section per upstream skill listing FSI canon overrides (mTLS, exactly_once_v2, schema format, compatibility, etc.); cflt-ai's CLAUDE.md hooks the overlay so it is read whenever an upstream skill activates
- **SCAF-01**: `/dsp:scaffold <artifact-type> <name>` cflt-ai skill exists and triages a scaffolding request to the right upstream skill, applying the active profile-family canon overlay as structured config
- **SCAF-02**: Scaffolded output registers as a new fsi-dsp `MANIFEST.yaml` capability entry with provenance footer (operator, profile, canon-stack hash, timestamp, upstream-skill version)
- **SCAF-03**: `/dsp:scaffold` is profile-gated and activity-logged; fails closed under `read-only` and refuses to scaffold a prod-canon artifact under `developer-sandbox` (negative-space tests prove the gate)

### Developer Profile Family + Bifurcated FSI Canon (H.4)

- **PROFAM-01**: Every profile JSON has a `family: "operator" | "developer"` field; `apply_engine.load_profile()` parses it; `check_tool_permitted()` branches on family (operator → tier cascade, developer → `tool_overrides` map); defaults to `"operator"` when absent for back-compat
- **PROFAM-02**: Per-profile-family negative-space test suite proves: operator profiles cannot invoke developer-family `tool_overrides` entries; developer profiles cannot invoke operator-tier-only tools (`delete-environment`, `create-cluster`, etc.); `/dsp:apply` fails closed under any developer profile
- **DEVPROF-01**: `tools/profiles/developer/sandbox.json` exists with `family: "developer"`, `primary_tooling.skills` allowlist for upstream confluent-agent-skills, `tool_overrides` promoting sandbox data-plane ops (produce-message, consume-messages, create-topics, etc.), `skill_blocklist` excluding `/dsp:apply`, soft `environment_guard` pattern
- **DEVCAN-01**: `canon/industry/fsi/developer-sandbox/` overlay exists with bifurcated FSI dev canon (OAUTHBEARER auth, at_least_once processing, JSON Schema OK, BACKWARD compatibility, RF=1 OK, dev topic naming pattern) — distinct from FSI prod overlay
- **DEVPROF-02**: `canon/customer/acme-bank/profiles/developer/sandbox.json` exists; test proves customer overlay produces ≥1 differential gating decision relative to base FSI dev canon (mirrors ACTG-04 for the developer family)

## v2.x Future Backlog

Deferred beyond v2.0. Tracked but not in current roadmap.

### Observability

- **OBS-01**: Observability MCP integration (Datadog, Dynatrace, Splunk)
- **OBS-02**: Incident-correlation feedback loop from observability into wiki

### Distribution

- **DIST-01**: Single Go binary for embedded contexts (CI runners, airgapped LinuxONE, K8s sidecars)

### Productization

- **PROD-01**: cflt-ai as standalone SKU vs. practice force multiplier (requires 3 engagement data points)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Model migration policy | Handled reactively via nightly harness matrix, not pre-designed |
| Custom application server | Claude Code is the right host for FSI engagement model through Phase 3 |
| Direct Terraform generation | Agent only invokes existing fsi-dsp artifacts; unresolvable requests become PR proposals |
| Real-time streaming from agent | Agent is request/response; streaming is in the data platform, not the agent |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| HYG-01 | Phase 0 | Complete |
| HYG-02 | Phase 0 | Complete |
| HYG-03 | Phase 0 | Complete |
| HYG-04 | Phase 0 | Complete |
| HYG-05 | Phase 0 | Complete |
| CNTR-01 | Phase 0 | Complete |
| CNTR-02 | Phase 0 | Complete |
| CNTR-03 | Phase 0 | Complete |
| CNTR-04 | Phase 0 | Complete |
| CNTR-05 | Phase 0 | Complete |
| CANST-01 | Phase 0 | Complete |
| CANST-02 | Phase 0 | Complete |
| CANST-03 | Phase 0 | Complete |
| CANST-04 | Phase 0 | Complete |
| WIKI-01 | Phase 0 | Complete |
| WIKI-02 | Phase 0 | Complete |
| WIKI-03 | Phase 1 | Complete |
| WIKI-04 | Phase 1 | Complete |
| WIKI-05 | Phase 1 | Complete |
| KNOW-01 | Phase 1 | Complete |
| KNOW-02 | Phase 1 | Complete |
| KNOW-03 | Phase 1 | Complete |
| KNOW-04 | Phase 1 | Complete |
| KNOW-05 | Phase 1 | Complete |
| REVW-01 | Phase 2 | Complete |
| REVW-02 | Phase 2 | Complete |
| REVW-03 | Phase 2 | Complete |
| REVW-04 | Phase 2 | Complete |
| REVW-05 | Phase 2 | Complete |
| REVW-06 | Phase 2 | Complete |
| ACT-01 | Phase 3a | Complete |
| ACT-02 | Phase 3a | Complete |
| ACT-03 | Phase 3a | Complete |
| ACT-04 | Phase 3a | Complete |
| ACT-05 | Phase 3a | Complete |
| ACT-06 | Phase 3a | Complete |
| ACT-07 | Phase 3a | Complete |
| ACT-08 | Phase 3a | Complete |
| ACTA-01 | Phase 3b | Complete |
| ACTA-02 | Phase 3b | Complete |
| ACTA-03 | Phase 3b | Complete |
| ACTA-04 | Phase 3b | Complete |
| ACTA-05 | Phase 3b | Complete |
| ACTA-06 | Phase 3b | Complete |
| ACTG-01 | Phase 3c | Complete |
| ACTG-02 | Phase 3c | Complete |
| ACTG-03 | Phase 3c | Complete |
| ACTG-04 | Phase 3c | Complete |
| WIKI-06 | Phase H.1 | Planned |
| WIKI-07 | Phase H.1 | Planned |
| WIKI-08 | Phase H.1 | Planned |
| EVAL-01 | Phase H.2 | Planned |
| EVAL-02 | Phase H.2 | Planned |
| EVAL-03 | Phase H.2 | Planned |
| INST-01 | Phase H.3 | Planned |
| CAN-OVR-01 | Phase H.3 | Planned |
| SCAF-01 | Phase H.3 | Planned |
| SCAF-02 | Phase H.3 | Planned |
| SCAF-03 | Phase H.3 | Planned |
| PROFAM-01 | Phase H.4 | Planned |
| PROFAM-02 | Phase H.4 | Planned |
| DEVPROF-01 | Phase H.4 | Planned |
| DEVCAN-01 | Phase H.4 | Planned |
| DEVPROF-02 | Phase H.4 | Planned |

**Coverage:**
- v1 requirements: 44 total, all complete
- v2.0 requirements: 16 total, all planned (H.1: 3 · H.2: 3 · H.3: 5 · H.4: 5)
- Mapped to phases: 60
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-28*
*Last updated: 2026-05-15 — added v2.0 (Developer Persona + Quality Gates) milestone*
