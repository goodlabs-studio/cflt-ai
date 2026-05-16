# Milestones

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
