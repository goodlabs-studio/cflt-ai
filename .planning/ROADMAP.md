# Roadmap: cflt-ai

## Overview

Six phases deliver a Confluent operational and knowledge agent for FSI engagements. Phase 0 fixes foundational hygiene and establishes the canon overlay stack and MANIFEST.yaml contract. Phase 1 unifies the knowledge skill with a tested triage path. Phase 2 hardens the review skill with reproducible claim extraction and customer-ready output. Phases 3a through 3c build the act rail incrementally — read-only plan, human-gated apply, then full per-profile tool classification — so that agent-driven Confluent operations are always canon-compliant and auditable. Each phase exits on measurable threshold, not calendar.

## Phases

**Phase Numbering:**
- Integer phases (0, 1, 2, 3): Planned milestone work
- Sub-phases (3a, 3b, 3c): Independent delivery boundaries within Phase 3 act rail

- [ ] **Phase 0: Foundation** - Fix bugs, establish MANIFEST.yaml contract, scaffold canon overlay stack, and get both repos to clean-clone health
- [ ] **Phase 1: Knowledge Skill** - Unify /ask + /wiki:recommend, add triage classifier, golden harness, and wiki decay rules
- [ ] **Phase 2: Review Skill** - Reproducible claim extraction, premise-challenge step, .docx output, multi-document support, customer overlay validation
- [ ] **Phase 3a: Act Rail — Plan** - Four-gate validation chain, /dsp:plan read-only rail, structural-correctness harness, CI parity in both repos
- [ ] **Phase 3b: Act Rail — Apply** - /dsp:apply with human-in-the-loop confirmation, three policy profiles, activity log, incident entries
- [ ] **Phase 3c: Act Rail — Profile Gating** - Per-tool classification of all 50+ mcp-confluent tools, negative-space test suites, break-glass two-step, customer fork demo

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
**Plans:** 1/6 plans executed

Plans:
- [x] 00-01-PLAN.md — Fix wiki tool bugs (HYG-01, HYG-02, HYG-03) and verify Flox environment (HYG-04)
- [ ] 00-02-PLAN.md — Author MANIFEST.yaml v1 and create fsi-dsp Flox manifest (CNTR-01, HYG-05)
- [ ] 00-03-PLAN.md — Scaffold four-layer canon overlay stack with defaults, overrides, and stack resolution (CANST-01 through CANST-04)
- [ ] 00-04-PLAN.md — Create wiki activity log and author ADR-009 LinuxONE (WIKI-02, WIKI-01 partial)
- [ ] 00-05-PLAN.md — Migrate wiki citations to fsi-dsp:// IDs and compile LinuxONE article (CNTR-02, WIKI-01)
- [ ] 00-06-PLAN.md — Create CI parity workflows for citation resolution and ID stability (CNTR-03, CNTR-04, CNTR-05)

### Phase 1: Knowledge Skill
**Goal**: A single unified /ask skill with triage routing, a tested golden harness, and wiki decay rules that keep coverage honest
**Depends on**: Phase 0
**Requirements**: WIKI-03, WIKI-04, WIKI-05, KNOW-01, KNOW-02, KNOW-03, KNOW-04, KNOW-05
**Success Criteria** (what must be TRUE):
  1. Running `/ask` with `--mode ephemeral`, `--mode report`, or `--mode reconsolidate` routes correctly through the triage classifier (wiki-only / wiki+MCP / deep reasoning) with no flag error
  2. The golden harness at tests/golden/ask/ contains >= 30 cases (>= 5 negative-space), passes at >= 90% on Haiku floor and >= 95% on Sonnet floor
  3. Wiki articles older than 90 days without revalidation drop from confidence:high to confidence:medium automatically
  4. Every /ask query that misses wiki coverage appends a stub to wiki/_queue.md for follow-up
**Plans**: TBD

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
**Plans**: TBD

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
**Plans**: TBD

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
**Plans**: TBD

### Phase 3c: Act Rail — Profile Gating
**Goal**: Every mcp-confluent tool is explicitly classified into a profile by name, per-profile negative-space suites prove forbidden tools fail closed, break-glass requires two-step confirmation, and a customer fork demonstrates differential gating
**Depends on**: Phase 3b
**Requirements**: ACTG-01, ACTG-02, ACTG-03, ACTG-04
**Success Criteria** (what must be TRUE):
  1. All 50+ mcp-confluent tools appear in an explicit classification table (by tool name, not regex pattern), with no tool unclassified
  2. Per-profile negative-space test suites run and confirm that tools forbidden by a profile return a closed failure, not a partial result
  3. The break-glass profile requires two distinct confirmation prompts and logs the override reason before any tool executes
  4. At least one customer fork exists with a profile configuration that differs from base, and a test demonstrates the differential gating works
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in sequence: 0 -> 1 -> 2 -> 3a -> 3b -> 3c

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 0. Foundation | 1/6 | In Progress|  |
| 1. Knowledge Skill | 0/TBD | Not started | - |
| 2. Review Skill | 0/TBD | Not started | - |
| 3a. Act Rail — Plan | 0/TBD | Not started | - |
| 3b. Act Rail — Apply | 0/TBD | Not started | - |
| 3c. Act Rail — Profile Gating | 0/TBD | Not started | - |
