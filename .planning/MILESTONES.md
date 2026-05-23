# Milestones

## v2.1 LinuxONE Accelerator Integration (Shipped: 2026-05-23)

**Phases completed:** 4 phases, 13 plans, 22 tasks

**Key accomplishments:**

- Bumped fsi-dsp submodule from feat/module-cc-cluster-basic@2989473 to upstream main@5a86fd2 (LinuxONE accelerator + 30 commits ahead) and cleared the two v2.0-audit test failures (test_no_drift_on_current_state, test_version_is_1_0_0) in a single atomic commit.
- Added a stale-submodule CI guard (`tools/check_submodule_drift.py` + `.github/workflows/submodule-drift.yml` + 6 unit tests) that fails the workflow when `raw/repos/fsi-dsp` falls more than 14 days behind upstream main HEAD, mirroring the H.3b pattern (pure Python + `git ls-remote`, no Node.js, no API auth).
- Registered `type: accelerator` as a first-class MANIFEST.yaml capability with a 5-layer `apply_sequence` schema (RBAC → TLS → SR → audit → Flink), per-layer `canon_key` co-location, and explicit kustomize build/dry-run/apply commands — committed inside the fsi-dsp submodule on `feat/manifest-accelerator-type` (b117f3f); cflt-ai parent pointer ready for 10-02 to atomically bump.
- Authored cflt-ai's first standalone MANIFEST schema validator (`tools/check_manifest.py`) gating a closed 8-type enum + per-type required-field discipline for `type: accelerator`; extended `tests/test_manifest.py` with 9 new TestManifestSchemaValidator tests (2 positive + 4 negative-space + 1 regression + 1 enum-gate + 1 constant-shape lock); authored `tools/manifest-schema.md` covering all 8 types and the adding-a-new-type runbook; cross-linked from CONTRIBUTING.md; bumped the fsi-dsp submodule pointer 5a86fd2 -> b117f3f all in a single atomic commit (`ad2304f`) so MAN-01 lands as one rollback unit.
- Plan:
- MODULE_TO_CANON_KEY grew from 2 → 7 entries with 5 composite accelerator/confluent-on-linuxone:<layer> keys; check_parity() walker now traverses apply_sequence and emits [DRIFT-1] on three distinct failure modes; 19 tests pass against post-Phase-10 MANIFEST.
- `execute_accelerator()` walks 5 LinuxONE layers via kustomize-build → oc dry-run → oc apply, emits per-layer ACTA-04 entries with the new `layer_id` field, halts cleanly on any non-zero exit with `failed_layer` populated — 17 new tests, zero regressions.
- /dsp:plan gained --layer flag with layer-aware provenance hashing; 5 golden act-harness cases (one per LinuxONE kustomize layer) land at v1.0 90% threshold (actually 100%); cross-plan integration test enforces MODULE_TO_CANON_KEY parity with act-harness layer map.
- `execute_accelerator()` gains an additive `profile_name` kwarg that performs a pre-flight `check_profile_permits()` before any kustomize/oc invocation; read-only refuses, engineer permits, break-glass permits (two-step UI lives at /dsp:apply Step 6c) — 20 new parameterized test scenarios in 6 methods, all green, zero regressions.
- `wiki/_index.md`
- 13 LinuxONE KNOWN-GAPS (G-01..G-13) encoded as vendor-sources.json trip-wires; tools/wiki-lint.py --full now surfaces DRIFT-GAP / MISSING-GAP / MALFORMED-GAP findings non-fatally per H.1 D-09.
- Converted 6 raw `raw/repos/fsi-dsp/...` source paths across 4 observability wiki articles to stable `fsi-dsp://` URIs (deduped to 4 distinct citations via folder-level MANIFEST IDs), closing the test failure carried since commit `bd7f967`.

---

## v2.0 Developer Persona + Quality Gates (Shipped: 2026-05-17)

**Phases completed:** 0 phases, 0 plans, 0 tasks

**Key accomplishments:**

- (none recorded)

---

## v1.0 — Foundation through Act Rail (Shipped: 2026-05-16)

**Phases:** 9 shipped (Phase 0, 1, 2, 3a, 3b, 3c + post-roadmap F.1, G.1, G.2c)
**Plans:** 26 plans
**Coverage:** 44/44 v1.0 requirements validated (ACTG-04 audit gap resolved at closure)

### Delivered

Confluent operational and knowledge agent for FSI engagements, shipped as Claude Code skills against a wiki of validated canon and the customer-extensible fsi-dsp accelerator. Serves three personas across the engagement lifecycle: ICs/SEs answering peer-level questions, embedded SAs producing reviewable customer deliverables, and SREs/operators executing canon-compliant changes through approved fsi-dsp artifacts.

### Key accomplishments

- **Canon overlay stack with provenance** — Four-layer overlay (base → industry → customer → engagement); every override is an ADR; active stack recorded in every artifact's provenance footer; acme-bank customer fork demonstrates differential gating across all three skills
- **`/ask` unified knowledge skill** — Triage classifier routes queries (wiki-only / wiki+MCP / deep reasoning); `--mode ephemeral|report|reconsolidate`; 32-case golden harness; auto-stub on coverage gaps; quarterly decay rules drop confidence:high → medium without revalidation
- **`/review` customer-deliverable skill** — Reproducible claim extraction, premise-challenge step, .docx output with full provenance footer (canon stack hash, manifest version, model floors, MCP versions), multi-document corpus, acme-bank customer overlay producing differential canon verdicts
- **`/dsp:plan` four-gate act rail** — Read-only validation chain (canon compliance → fsi-dsp coverage → confluent-docs schema → mcp-confluent state); 22-case golden harness; bidirectional canon ↔ fsi-dsp parity CI blocking merges on drift; agent never generates inline Terraform
- **`/dsp:apply` human-gated infrastructure changes** — Mandatory `CONFIRM APPLY` step; three policy profiles (read-only, engineer, break-glass) with least-privilege enforcement; break-glass requires two-step confirmation; every apply emits provenance to activity log + wiki incident entry; FRANZ pre-confirmed flow (F.1) plus real terraform-module executor (G.1) shipped within the milestone
- **mcp-confluent tool gating** — 54-tool kebab-case classification table aligned with live registry 1.3.0 via generator script (G.2c); per-profile negative-space test suite (255 tests across 54 tools × 3 profiles + customer overlay); bidirectional CI drift gate fails PRs when classification diverges from upstream registry

### Tech debt carried into v2.0

- Structural-only verification (live LLM evaluation deferred): KNOW-04, KNOW-05, REVW-01, ACT-07 → addressed by H.2 (eval harness extension)
- Pass-through stub gates (live MCP validation deferred): ACT-02 gates 3 and 4 (confluent_docs_schema, mcp_confluent_state)
- G.2 sub-phases deferred to v2.0 backlog: G.2a (mcp-confluent tool-call executor), G.2b (composite scenario executor), G.2d (GitOps apply mode), G.2e (ansible-role executor)

### Archive

- `.planning/milestones/v1.0-ROADMAP.md`
- `.planning/milestones/v1.0-REQUIREMENTS.md`
- `.planning/milestones/v1.0-MILESTONE-AUDIT.md`

---
