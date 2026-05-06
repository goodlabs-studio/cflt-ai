# PROJECT.md

## Project

cflt-ai is a Confluent operational and knowledge agent for FSI engagements, built as Claude Code skills against a compounding wiki of validated canon and a customer-extensible accelerator (fsi-dsp) of opinions-as-code. The agent serves three personas across an engagement lifecycle: ICs and SEs answering peer-level questions, embedded SAs producing reviewable customer deliverables, and SREs/operators executing canon-compliant changes. The north star is a Confluent practitioner whose answers compound, never confidently lies, and only acts through artifacts the customer's IaC review process has already approved.

## Constraints (immutable)

- **Canon overlay stack.** Base (GoodLabs) → industry (FSI, healthcare) → customer → engagement. Each layer overrides defaults from above; every override is an ADR in the layer that introduces it; the active stack is recorded in every artifact's provenance footer.
- **MANIFEST.yaml is the contract.** fsi-dsp publishes identifiers (`adr/009`, `module/topic`, `role/cp_dr_mm2`, etc.); cflt-ai cites by ID. `schema_version` is semver; stable IDs never change without a major bump. CI in both repos enforces this — fsi-dsp blocks PRs that drop a stable ID without a major bump; cflt-ai blocks PRs where any wiki citation fails to resolve. Manifest entries carry `capabilities` blocks describing what the artifact does in canonical terms; gate two of the act rail resolves against these.
- **Four-gate act rail.** Every act-rail invocation passes canon compliance → fsi-dsp coverage → confluent-docs schema validation → mcp-confluent state check, in order, each blocking. The agent never generates Terraform or invokes mcp-confluent writes directly; it only invokes existing fsi-dsp artifacts. If a request can't be satisfied through existing artifacts, the answer is a PR proposal against fsi-dsp, not hand-rolled HCL.
- **Eval gates phases.** No phase ships on calendar. Each phase exits when its golden harness hits the threshold. Floor model is pinned per case; the floor regressing blocks merge. Nightly matrix runs the full lineup and alerts on regression.
- **Activity log is mandatory.** Every skill invocation appends to `<active-overlay>/activity/YYYY-MM.md` — base canon writes to `wiki/activity/`, customer fork writes to its overlay path, engagement overlay writes to its own. Schema: skill, mode, timestamp, user, sources consulted, MCP calls made, artifacts produced, gates passed/failed, canon stack hash, model floors used.

## Personas

- **IC / SE.** Confluent practitioners asking peer-level questions. Read-mostly, latency-sensitive. Answers are opinionated and direct; a structured *consider this:* footer surfaces canon-level concerns without blocking the answer. Premise-challenge is implicit, not explicit. Mode: `ephemeral`.
- **Embedded SA.** Producing customer deliverables. Premise-challenge step is mandatory and explicit; reviews actively interrogate whether the question is well-formed before answering it. Output is a signed `.docx` with full provenance footer. Mode: `report`.
- **SRE / Operator.** Executing changes. Profile-gated (`read-only` / `engineer` / `break-glass`). Every action invokes fsi-dsp artifacts; never hand-rolled. Mode: `reconsolidate`.

`/ask` and `/wiki:recommend` collapse into a single skill controlled by `--mode {ephemeral|report|reconsolidate}`. Three skills total at maturity: the unified knowledge skill, `/review` for deliverable evaluation, `/dsp:plan` and `/dsp:apply` for the act rail.

## Phases

Each phase exits on threshold, not date. Phase N+1 cannot begin until Phase N exits.

**Phase 0 — Hygiene + Contract.** Exit: three bugs fixed (`wiki-stats.py` syntax, `wiki-lint.py` broken-link regex, `evaluate.md` literal-ellipsis paths); Flox manifest committed in both repos and works on clean clone; `MANIFEST.yaml` v1 published with `capabilities` blocks for every existing fsi-dsp asset; wiki citations migrated to ID form; CI parity checks green in both repos; canon overlay stack scaffolding present (even if only base canon populated); LinuxONE wiki articles ingested from fsi-dsp `adr/009` and the LinuxONE guides; activity log directory live and emitting.

**Phase 1 — Eval harness + unified knowledge skill tightened.** Exit: `/ask` and `/wiki:recommend` collapsed into single skill with `--mode` flag; `tests/golden/ask/` ≥ 30 cases including ≥ 5 negative-space cases; floor-model pass rate ≥ 90% on Haiku-floor cases and ≥ 95% on Sonnet-floor cases; triage classifier (wiki-only / wiki+MCP / deep reasoning) validated independently in harness; `last_validated` field added, quarterly decay rule live, `confidence: high` articles drop to `medium` after 90 days without revalidation; auto-stub on coverage gap working (every `/ask` miss appends to `wiki/_queue.md`).

**Phase 2 — `/review` tightened.** Exit: `tests/golden/review/` ≥ 15 cases drawn from sanitized customer docs; claim extraction reproducibility ≥ 95% across runs (same doc → same claims); explicit premise-challenge step shipped and tested in harness; `.docx` output with full provenance footer (canon stack hash, manifest version, model floors, MCP versions, reproducibility command); multi-document review supported (deck + tfvars + runbook as a single input); ≥ one customer overlay validated end-to-end with differential canon override.

**Phase 3a — `/dsp:plan` (read-only act).** Exit: Terraform MCP wired into `.mcp.json`; four-gate validation chain implemented with each gate individually testable and bypassable in dev mode for debugging; `tests/golden/act/` ≥ 20 cases including negative-space coverage (agent must not generate inline Terraform; must not invoke `mcp-confluent` write tools directly even when capable); structural correctness ≥ 95% (right artifact selected, right arguments, schemas validate); canon ↔ fsi-dsp parity test running in both repos' CI and blocking on drift.

**Phase 3b — `/dsp:apply`.** Exit: human-in-the-loop confirmation enforced and tested for bypass attempts; three policy profiles (`read-only.json`, `engineer.json`, `break-glass.json`) implemented with explicit per-tool classification; activity log captures every plan/apply with full provenance and writes a wiki incident entry per apply; Phase 3a structural-correctness metric holds for 30 days of real engagement use without regression.

**Phase 3c — mcp-confluent direct writes, profile-gated.** Exit: every mcp-confluent tool (50+) classified into a profile by name, not regex; per-profile negative-space test suite ensures forbidden tools fail closed; break-glass profile requires two-step confirmation with explicit override reason logged; ≥ one customer fork demonstrates differential profile gating relative to base.

## Open questions (deferred, not decided)

- Model migration policy when Anthropic ships a new family — handled reactively via the nightly harness matrix, not pre-designed.
- Productization path (cflt-ai as standalone SKU vs. force multiplier for the GoodLabs practice) — deferred until three customer engagements provide utilization and win-rate data.
- Single Go binary distribution for embedded contexts (CI runners, airgapped LinuxONE side-deploys, K8s sidecars) — Phase 4+, not foundational. The Claude Code host is the right call for the FSI engagement model through Phase 3.
- Observability MCP integration (Datadog, Dynatrace, Splunk) and the incident-correlation feedback loop — Phase 4. The architecture admits it cleanly; it is not on the critical path to a defensible act rail.
