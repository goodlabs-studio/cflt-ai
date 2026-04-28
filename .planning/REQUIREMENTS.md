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
- [ ] **CNTR-02**: Wiki citations migrated from prose references to MANIFEST.yaml ID form
- [ ] **CNTR-03**: CI parity checks green in both repos (cflt-ai and fsi-kafka-platform)
- [ ] **CNTR-04**: fsi-dsp blocks PRs that drop a stable ID without a major bump
- [ ] **CNTR-05**: cflt-ai blocks PRs where any wiki citation fails to resolve against MANIFEST.yaml

### Canon Stack

- [x] **CANST-01**: Canon overlay stack scaffolding present (base → industry → customer → engagement layers)
- [x] **CANST-02**: Each overlay layer can override defaults from the layer above
- [x] **CANST-03**: Every override is an ADR in the layer that introduces it
- [x] **CANST-04**: Active stack recorded in artifact provenance footers

### Wiki

- [x] **WIKI-01**: LinuxONE wiki articles ingested from fsi-dsp adr/009 and LinuxONE guides
- [x] **WIKI-02**: Activity log directory live and emitting per overlay-scoped path
- [ ] **WIKI-03**: last_validated field added to wiki articles with quarterly decay rule
- [ ] **WIKI-04**: confidence:high articles drop to medium after 90 days without revalidation
- [ ] **WIKI-05**: Auto-stub on coverage gap — every /ask miss appends to wiki/_queue.md

### Knowledge Skill

- [ ] **KNOW-01**: /ask and /wiki:recommend collapsed into single skill with --mode flag (ephemeral | report | reconsolidate)
- [ ] **KNOW-02**: Triage classifier routes queries: wiki-only / wiki+MCP / deep reasoning
- [ ] **KNOW-03**: Golden test harness at tests/golden/ask/ with >= 30 cases including >= 5 negative-space cases
- [ ] **KNOW-04**: Floor-model pass rate >= 90% on Haiku-floor cases
- [ ] **KNOW-05**: Floor-model pass rate >= 95% on Sonnet-floor cases

### Review Skill

- [ ] **REVW-01**: Claim extraction reproducibility >= 95% across runs (same doc → same claims)
- [ ] **REVW-02**: Explicit premise-challenge step shipped and tested in harness
- [ ] **REVW-03**: .docx output with full provenance footer (canon stack hash, manifest version, model floors, MCP versions)
- [ ] **REVW-04**: Multi-document review supported (deck + tfvars + runbook as single input)
- [ ] **REVW-05**: Golden test harness at tests/golden/review/ with >= 15 cases from sanitized customer docs
- [ ] **REVW-06**: >= 1 customer overlay validated end-to-end with differential canon override

### Act Rail (Plan)

- [ ] **ACT-01**: Terraform MCP wired into .mcp.json
- [ ] **ACT-02**: Four-gate validation chain implemented (canon compliance → fsi-dsp coverage → confluent-docs schema → mcp-confluent state)
- [ ] **ACT-03**: Each gate individually testable and bypassable in dev mode
- [ ] **ACT-04**: /dsp:plan read-only act rail skill implemented
- [ ] **ACT-05**: Golden test harness at tests/golden/act/ with >= 20 cases including negative-space
- [ ] **ACT-06**: Agent never generates inline Terraform; never invokes mcp-confluent write tools directly
- [ ] **ACT-07**: Structural correctness >= 95% (right artifact selected, right arguments, schemas validate)
- [ ] **ACT-08**: Canon <-> fsi-dsp parity test running in both repos' CI and blocking on drift

### Act Rail (Apply)

- [ ] **ACTA-01**: /dsp:apply skill with human-in-the-loop confirmation enforced
- [ ] **ACTA-02**: Bypass attempts tested and blocked
- [ ] **ACTA-03**: Three policy profiles implemented: read-only.json, engineer.json, break-glass.json
- [ ] **ACTA-04**: Activity log captures every plan/apply with full provenance
- [ ] **ACTA-05**: Wiki incident entry written per apply
- [ ] **ACTA-06**: Structural-correctness metric holds for 30 days of real engagement use

### Act Rail (Profile Gating)

- [ ] **ACTG-01**: Every mcp-confluent tool (50+) classified into a profile by name, not regex
- [ ] **ACTG-02**: Per-profile negative-space test suite ensures forbidden tools fail closed
- [ ] **ACTG-03**: Break-glass profile requires two-step confirmation with explicit override reason logged
- [ ] **ACTG-04**: >= 1 customer fork demonstrates differential profile gating relative to base

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

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
| CNTR-02 | Phase 0 | Pending |
| CNTR-03 | Phase 0 | Pending |
| CNTR-04 | Phase 0 | Pending |
| CNTR-05 | Phase 0 | Pending |
| CANST-01 | Phase 0 | Complete |
| CANST-02 | Phase 0 | Complete |
| CANST-03 | Phase 0 | Complete |
| CANST-04 | Phase 0 | Complete |
| WIKI-01 | Phase 0 | Complete |
| WIKI-02 | Phase 0 | Complete |
| WIKI-03 | Phase 1 | Pending |
| WIKI-04 | Phase 1 | Pending |
| WIKI-05 | Phase 1 | Pending |
| KNOW-01 | Phase 1 | Pending |
| KNOW-02 | Phase 1 | Pending |
| KNOW-03 | Phase 1 | Pending |
| KNOW-04 | Phase 1 | Pending |
| KNOW-05 | Phase 1 | Pending |
| REVW-01 | Phase 2 | Pending |
| REVW-02 | Phase 2 | Pending |
| REVW-03 | Phase 2 | Pending |
| REVW-04 | Phase 2 | Pending |
| REVW-05 | Phase 2 | Pending |
| REVW-06 | Phase 2 | Pending |
| ACT-01 | Phase 3a | Pending |
| ACT-02 | Phase 3a | Pending |
| ACT-03 | Phase 3a | Pending |
| ACT-04 | Phase 3a | Pending |
| ACT-05 | Phase 3a | Pending |
| ACT-06 | Phase 3a | Pending |
| ACT-07 | Phase 3a | Pending |
| ACT-08 | Phase 3a | Pending |
| ACTA-01 | Phase 3b | Pending |
| ACTA-02 | Phase 3b | Pending |
| ACTA-03 | Phase 3b | Pending |
| ACTA-04 | Phase 3b | Pending |
| ACTA-05 | Phase 3b | Pending |
| ACTA-06 | Phase 3b | Pending |
| ACTG-01 | Phase 3c | Pending |
| ACTG-02 | Phase 3c | Pending |
| ACTG-03 | Phase 3c | Pending |
| ACTG-04 | Phase 3c | Pending |

**Coverage:**
- v1 requirements: 44 total
- Mapped to phases: 44
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-28*
*Last updated: 2026-04-28 after roadmap creation*
