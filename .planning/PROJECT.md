# cflt-ai

## What This Is

A Confluent operational and knowledge agent for FSI engagements, built as Claude Code skills against a compounding wiki of validated canon and a customer-extensible accelerator (fsi-dsp) of opinions-as-code. The agent serves three personas across an engagement lifecycle: ICs/SEs answering peer-level questions, embedded SAs producing reviewable customer deliverables, and SREs/operators executing canon-compliant changes through approved fsi-dsp artifacts.

## Core Value

The canon overlay stack works — customers can fork and override safely. Base (GoodLabs) → industry (FSI) → customer → engagement. Each layer overrides defaults from above, every override is an ADR, and the active stack is recorded in every artifact's provenance footer. If this doesn't work, nothing else matters.

## Requirements

### Validated

- ✓ Wiki knowledge base with concepts/ and patterns/ articles — existing
- ✓ `/ask` skill with MCP-validated answers — existing
- ✓ `/review` skill for document evaluation — existing
- ✓ `/wiki:ingest`, `/wiki:validate`, `/wiki:lint`, `/wiki:recommend` skills — existing
- ✓ MCP server integration (context7, confluent-docs, mcp-confluent) — existing
- ✓ Wiki metadata system (_index.md, _graph.md, _queue.md) — existing
- ✓ CLI tools (wiki-lint.py, wiki-search.py, wiki-stats.py, wiki-compile.py) — existing
- ✓ fsi-dsp submodule linked with Ansible roles, Terraform modules, ADRs — existing
- ✓ CLAUDE.md Confluent Canon with FSI overlay — existing
- ✓ GitHub Actions CI for wiki linting — existing
- ✓ Setup script (bin/setup) for first-run initialization — existing

### Active

- [ ] Phase 0: Fix known bugs (wiki-stats.py, wiki-lint.py, evaluate.md)
- [ ] Phase 0: Flox manifest committed and works on clean clone (both repos)
- [ ] Phase 0: MANIFEST.yaml v1 with capabilities blocks for all fsi-dsp assets
- [ ] Phase 0: Wiki citations migrated to ID form
- [ ] Phase 0: CI parity checks green in both repos
- [ ] Phase 0: Canon overlay stack scaffolding present
- [ ] Phase 0: LinuxONE wiki articles ingested from fsi-dsp
- [ ] Phase 0: Activity log directory live and emitting
- [ ] Phase 1: Unified /ask + /wiki:recommend with --mode flag
- [ ] Phase 1: Golden test harness (tests/golden/ask/) with 30+ cases
- [ ] Phase 1: Triage classifier (wiki-only / wiki+MCP / deep reasoning)
- [ ] Phase 1: last_validated decay rule + auto-stub on coverage gaps
- ✓ Phase 2: Claim extraction reproducibility >= 95% — Validated in Phase 02: review-skill
- ✓ Phase 2: Premise-challenge step in /review — Validated in Phase 02: review-skill
- ✓ Phase 2: .docx output with full provenance footer — Validated in Phase 02: review-skill
- ✓ Phase 2: Multi-document review support — Validated in Phase 02: review-skill
- ✓ Phase 2: Customer overlay validated end-to-end — Validated in Phase 02: review-skill
- [ ] Phase 3a: Four-gate validation chain (individually testable, dev-bypassable)
- [ ] Phase 3a: /dsp:plan read-only act rail
- [ ] Phase 3a: Structural correctness >= 95% (right artifact, right args)
- [ ] Phase 3a: Canon <-> fsi-dsp parity CI in both repos
- [ ] Phase 3b: /dsp:apply with human-in-the-loop confirmation
- [ ] Phase 3b: Three policy profiles (read-only, engineer, break-glass)
- [ ] Phase 3b: Activity log captures every plan/apply with provenance
- [ ] Phase 3c: Every mcp-confluent tool classified by profile (by name, not regex)
- [ ] Phase 3c: Per-profile negative-space test suites
- [ ] Phase 3c: Break-glass two-step confirmation with override logging
- [ ] Phase 3c: Customer fork with differential profile gating

### Out of Scope

- Model migration policy — handled reactively via nightly harness matrix
- Productization path (SKU vs. practice force multiplier) — deferred until 3 customer engagements provide data
- Single Go binary distribution — Phase 4+, not foundational
- Observability MCP integration (Datadog, Dynatrace, Splunk) — Phase 4, architecture admits it cleanly

## Context

- **Two repos:** cflt-ai (this repo, knowledge agent) and fsi-kafka-platform (upstream of fsi-dsp submodule at raw/repos/fsi-dsp/)
- **Runtime:** Claude Code as host — no separate backend deployment
- **Stack:** Python CLI tools, Markdown wiki, MCP servers (context7, confluent-docs, mcp-confluent), Flox dev environments
- **Personas:** IC/SE (ephemeral mode), Embedded SA (report mode), SRE/Operator (reconsolidate mode)
- **Target audience for v1:** GoodLabs peers using personally or on live FSI engagements; gather feedback for v2.0 after adoption period
- **FSI context:** Latency SLA tiers (sub-ms market data, <10ms risk, <100ms compliance, async reconciliation); exactly-once for regulatory reporting; IBM MQ bridge pattern for mainframe integration
- **IBM acquisition of Confluent (2026):** Relevant to vendor positioning in customer conversations

## Constraints

- **Canon overlay stack:** Base → industry → customer → engagement; each override is an ADR; active stack recorded in every artifact provenance footer
- **MANIFEST.yaml contract:** fsi-dsp publishes stable IDs; cflt-ai cites by ID; CI enforces ID stability and resolution in both repos
- **Four-gate act rail:** canon compliance → fsi-dsp coverage → confluent-docs schema → mcp-confluent state; each gate blocking; agent never generates hand-rolled Terraform
- **Eval gates phases:** No phase ships on calendar; each exits when golden harness hits threshold; floor model pinned per case
- **Activity log mandatory:** Every skill invocation appends to overlay-scoped activity log with full schema

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Canon overlay stack (composition, not inheritance) | Customers need to override defaults without forking the whole system; ADR-backed overrides are auditable | — Pending |
| Claude Code as runtime (no custom server) | FSI engagement model runs through practitioner laptops; Claude Code is the right host through Phase 3 | — Pending |
| fsi-dsp as submodule, not vendored | Separate repo lifecycle; CI parity enforced across both repos; MANIFEST.yaml is the contract | — Pending |
| Customer extensibility as core value | Trust compounds through the overlay stack; everything else (answers, act rail) depends on customers being able to fork safely | — Pending |
| Phase exits on threshold, not dates | Quality gates prevent shipping broken skills; golden harness is the source of truth | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-28 after Phase 02 (review-skill) completion*
