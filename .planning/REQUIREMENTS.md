# Requirements: cflt-ai

**Defined:** 2026-04-28
**Last updated:** 2026-05-16 — v1.0 archived
**Core Value:** Canon overlay stack works — customers can fork and override safely

## v1.0 Requirements (Archived)

All 44 v1.0 requirements (HYG, CNTR, CANST, WIKI-01..05, KNOW, REVW, ACT, ACTA, ACTG) shipped 2026-05-16.
See [`milestones/v1.0-REQUIREMENTS.md`](milestones/v1.0-REQUIREMENTS.md) for the full archive with completion notes and tech-debt carry-forward.

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

v1.0 traceability archived to [`milestones/v1.0-REQUIREMENTS.md`](milestones/v1.0-REQUIREMENTS.md). The table below tracks active v2.0 requirements.

| Requirement | Phase | Status |
|-------------|-------|--------|
| WIKI-06 | Phase H.1 | Complete (H.1-02) |
| WIKI-07 | Phase H.1 | Complete (H.1-03) |
| WIKI-08 | Phase H.1 | Complete (H.1-03) |
| EVAL-01 | Phase H.2 | Complete (H.2-01) |
| EVAL-02 | Phase H.2 | Complete (H.2-02 + H.2-03) |
| EVAL-03 | Phase H.2 | Complete (H.2-02 + H.2-03 encode 9/9 trip-wires; H.2-04 lands `.github/workflows/skill-evals.yml` PR gate) |
| INST-01 | Phase H.3 | Complete (H.3a-01: install verified + overlay landed; H.3b-01: pin in tools/vendor-sources.json + .github/workflows/streaming-skills-drift.yml CI gate) |
| CAN-OVR-01 | Phase H.3 | Complete (H.3a-01) |
| SCAF-01 | Phase H.3 | Complete (H.3c-01: .claude/commands/dsp-scaffold.md skill + tools/scaffold_engine.py triage table, end-to-end for producer artifact-type) |
| SCAF-02 | Phase H.3 | Complete (H.3c-01: manifest-entry.yaml + provenance.json emit 15 D-08 keys including operator, profile, canon-stack hash, timestamp, upstream-skill version, upstream commit SHA) |
| SCAF-03 | Phase H.3 | Complete (H.3c-01: three-gate sequence — skill blocklist + read-only operator + cross-family canon refusal; activity-logged on every invocation; negative-space tests prove fail-closed under both read-only and developer/sandbox --prod) |
| PROFAM-01 | Phase H.4a | Complete (H.4a-01) |
| PROFAM-02 | Phase H.4a + H.4b | Complete (H.4a-01 + H.4b-01: developer-branch dispatch + full per-family negative-space matrix in tests/test_per_family_isolation.py) |
| DEVPROF-01 | Phase H.4b | Complete (H.4b-01: tools/profiles/developer/sandbox.json) |
| DEVCAN-01 | Phase H.4b | Complete (H.4b-01: canon/industry/fsi/developer-sandbox/) |
| DEVPROF-02 | Phase H.4b + H.4c | Complete (H.4b-01: negative-space isolation + dsp-apply fail-closed; H.4c-01: acme-bank customer-fork differential gating — 2 tool-level + 1 skill-level differentials proven) |

**Coverage:**
- v1.0 requirements: 44 total, all shipped — archived to `milestones/v1.0-REQUIREMENTS.md`
- v2.0 requirements: 16 total, all planned (H.1: 3 · H.2: 3 · H.3: 5 · H.4: 5)
- Mapped to phases: 16
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-28*
*Last updated: 2026-05-16 — v1.0 archived; v2.0 (Developer Persona + Quality Gates) active*
