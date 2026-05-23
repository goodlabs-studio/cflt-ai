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

### Validated (v1.0 — shipped 2026-05-16)

- ✓ Phase 0: All hygiene, contract, canon stack, and wiki bootstrap items — v1.0
- ✓ Phase 1: Unified /ask with --mode flag, triage classifier, decay rules, golden harness — v1.0
- ✓ Phase 2: Reproducible claim extraction, premise-challenge, .docx output, multi-doc, customer overlay — v1.0
- ✓ Phase 3a: Four-gate plan rail with structural correctness ≥95% and bidirectional canon ↔ fsi-dsp parity — v1.0
- ✓ Phase 3b: Human-gated /dsp:apply with three policy profiles, activity log, incident articles — v1.0
- ✓ Phase 3c: 54-tool mcp-confluent classification, per-profile negative-space tests, break-glass two-step, acme-bank customer fork — v1.0
- ✓ Phase F.1: FRANZ native modal pre-confirmed apply flow — v1.0
- ✓ Phase G.1: Terraform-module executor for /dsp-apply Step 7 — v1.0
- ✓ Phase G.2c: Tool-classification rename to live mcp-confluent 1.3.0 registry + bidirectional CI drift gate — v1.0

### Validated (v2.0 — shipped 2026-05-17)

- ✓ Phase H.1: 10 wiki articles + 9 trip-wires ingested from confluentinc/agent-skills@91d1871e with full MCP validation — v2.0
- ✓ Phase H.2: Eval harness across /review, /wiki:*, /dsp:plan, /dsp:apply with 175 cases at 90% CI threshold — v2.0
- ✓ Phase H.3a: streaming-skills-plugin installed; wiki/patterns/fsi-canon-overlay-for-confluent-skills.md authored with 4-section override tables; CLAUDE.md hook — v2.0
- ✓ Phase H.3b: streaming-skills-plugin pinned in tools/vendor-sources.json; .github/workflows/streaming-skills-drift.yml mirrors G.2c pattern — v2.0
- ✓ Phase H.3c: /dsp:scaffold wrapper with triage + 3 gates + manifest-entry.yaml + provenance.json (producer artifact-type end-to-end) — v2.0
- ✓ Phase H.4a: Profile-family schema extension (family: operator|developer field + apply_engine branching + back-compat default) — v2.0
- ✓ Phase H.4b: tools/profiles/developer/sandbox.json + canon/industry/fsi/developer-sandbox/ overlay + per-family negative-space test matrix — v2.0
- ✓ Phase H.4c: canon/customer/acme-bank/profiles/developer/sandbox.json + 3 differential gating decisions vs base FSI dev canon (ACTG-04 mirror) — v2.0

### Validated (v2.1 — shipped 2026-05-23)

- ✓ Phase 9: Submodule sync + canon-parity unblock — bumped `raw/repos/fsi-dsp` to upstream main HEAD; cleared 2 v2.0-audit test failures; added 14-day stale-submodule CI guard mirroring H.3b — v2.1
- ✓ Phase 10: Accelerator artifact-type registration — `type: accelerator` registered in MANIFEST.yaml (fsi-dsp PR #3 OPEN); cflt-ai authored first standalone manifest schema validator + 9 tests + manifest-schema.md — v2.1
- ✓ Phase 11: Act-rail wiring for accelerator dispatch — 5-layer MODULE_TO_CANON_KEY + accelerator-walking canon-parity + `execute_accelerator()` with per-layer ACTA-04 + 5 golden act cases + profile gating across read-only/engineer/break-glass — v2.1
- ✓ Phase 12: Wiki ingest of LinuxONE accelerator — 6 articles + 13 KNOWN-GAPS trip-wires + /review auditor-readonly Step 4.1 + 15 golden eval cases; bonus: closed Phase 9 carry-forward (`test_wiki_citations`) — v2.1

### Active (v2.2 — TBD)

Run `/gsd:new-milestone` to scope. Candidate items from v2.1 follow-up + carry-forward:

- [ ] fsi-dsp PR #3 post-merge pointer bump (bookkeeping — when upstream merges, fast-forward submodule and let 14-day drift CI clear)
- [ ] G.2 carry-forward: G.2a (mcp-confluent tool-call executor), G.2b (composite scenario executor — natural follow-on to v2.1 Phase 11 accelerator dispatch), G.2d (GitOps apply mode), G.2e (ansible-role executor)
- [ ] Extend `/dsp:scaffold` to remaining 4 artifact-types (consumer, kafka-streams-app, schema, cdc-pipeline)
- [ ] `scaffolded-producer` executor inside `raw/repos/fsi-dsp/`
- [ ] Promote `canon/industry/fsi/developer-sandbox/` CONTEXT-sourced override decisions to formal ADRs after first customer engagement

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
| Canon overlay stack (composition, not inheritance) | Customers need to override defaults without forking the whole system; ADR-backed overrides are auditable | ✓ Good — acme-bank customer fork demonstrated differential gating across /review, /dsp:plan, /dsp:apply in v1.0 |
| Claude Code as runtime (no custom server) | FSI engagement model runs through practitioner laptops; Claude Code is the right host through Phase 3 | ✓ Good — held through v1.0; FRANZ wrapper (F.1) added native-modal integration without changing runtime |
| fsi-dsp as submodule, not vendored | Separate repo lifecycle; CI parity enforced across both repos; MANIFEST.yaml is the contract | ✓ Good — held through v1.0; G.1 terraform-module executor consumes the submodule contract |
| Customer extensibility as core value | Trust compounds through the overlay stack; everything else (answers, act rail) depends on customers being able to fork safely | ✓ Good — ACTG-04 customer fork demonstrated in v1.0; v2.0 H.4 extends overlay model to developer-sandbox profile family |
| Phase exits on threshold, not dates | Quality gates prevent shipping broken skills; golden harness is the source of truth | ⚠️ Revisit — structural harness shipped (KNOW-04, KNOW-05, REVW-01, ACT-07) but LIVE-model evaluation was deferred from v1.0; v2.0 H.2 closes this gap |
| Pin upstream tooling at exact version with CI drift gate (G.2c pattern) | mcp-confluent 1.3.0 rename established the pattern: install pinned version, parse upstream, CI fails bidirectional drift; same approach scales to v2.0 H.3b (streaming-skills-plugin) and beyond | ✓ Good — G.2c shipped 54-tool kebab-case classification with bidirectional drift CI gate; pattern reusable |
| Big-bang rewrite over bilingual compatibility (G.2c pattern) | When fictional/stale upstream entries can be cleanly purged with zero prod callers, single PR + regenerated tests beats deprecation layer | ✓ Good — G.2c purged ~25 fictional snake_case entries cleanly; 214 tests passing post-rewrite |
| Two profile families, not one tier hierarchy (v2.0 architectural decision) | Operator (read-only/engineer/break-glass) and developer (sandbox/etc.) are orthogonal personas — different blast radius, different tooling, different canon overlay; one-tier-hierarchy creates categorical confusion | ✓ Good — v2.0 H.4 shipped: developer family lives orthogonally to operator tier cascade; per-family negative-space test matrix proves isolation; acme-bank customer fork extends to dev family via overlay |
| Stub generator for non-interactive scaffold output (v2.0 H.3c) | Upstream streaming-skills-plugin skills have HARD-GATE confirmation prompts; non-interactive execution wraps them with a stub generator (1 artifact-type end-to-end in H.3c, others marked NotImplementedError) | ✓ Good — H.3c shipped /dsp:scaffold for producer artifact with full provenance + MANIFEST entry proposal; remaining 4 artifact-types each become 1 follow-on phase |
| Free-form `kind` field in tools/vendor-sources.json (H.1 D-?, extended H.3b) | New vendor kinds (claude-plugin, terraform-module) slot in without schema migration | ✓ Good — H.3b extended schema with `kind: "claude-plugin"` alongside H.1's `wiki-source` with zero friction; both share bidirectional drift discipline |

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

*Last updated: 2026-05-23 after v2.1 milestone (LinuxONE Accelerator Integration) shipped — 4 phases, 13 plans, 13/13 requirements validated; fsi-dsp PR #3 awaiting upstream merge*

---
*Last updated: 2026-05-23 — v2.1 (LinuxONE Accelerator Integration) scoped*

---
*Last updated: 2026-05-17 after v2.0 milestone (Developer Persona + Quality Gates)*

---
*Last updated: 2026-05-16 after v1.0 milestone shipped — Foundation through Act Rail + post-roadmap F.1/G.1/G.2c. v2.0 (Developer Persona + Quality Gates) active.*
