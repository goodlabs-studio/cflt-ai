# Phase 12: Wiki ingest of LinuxONE accelerator — Context

**Gathered:** 2026-05-23
**Status:** Ready for planning
**Mode:** Auto-generated with locked decisions (autonomous run; ingest pattern locked from H.1 precedent)

<domain>
## Phase Boundary

Mirror the H.1 ingest pattern for the LinuxONE accelerator. Compile ≥6 wiki articles from the upstream accelerator's `DESIGN.md`, `KNOWN-GAPS.md`, `MIGRATION.md`, and embedded patterns. Encode all 13 `KNOWN-GAPS.md` entries (G-01..G-13) as `tools/vendor-sources.json` trip-wires. Extend the golden eval harness with ≥15 cases across `/ask` and `/review`. After Phase 12, the wiki has authoritative coverage of LinuxONE-on-CFK, `/wiki:lint --full` surfaces drift on upstream gap status changes, and `/review` flags claims contradicting the auditor-readonly payload-isolation pattern.

**Bonus scope (carry-forward):** Fix the 4 pre-existing wiki articles flagged in Phase 09's `deferred-items.md` (`test_no_raw_fsi_dsp_paths_in_sources`) — convert raw `raw/repos/fsi-dsp/...` paths to `fsi-dsp://<id>` form. This aligns with Phase 12's ingest discipline (proper source attestation per H.1 D-07) and clears the test failure carried since commit `bd7f967`.

</domain>

<decisions>
## Implementation Decisions

### 6 wiki articles (locked)

Targets, paths, and source files for each:

1. **`wiki/patterns/linuxone-on-cfk-reference-architecture.md`** — LinuxONE-on-CFK ref arch. Source: `accelerators/confluent-on-linuxone/DESIGN.md` (sections on stack composition, layer ordering, attribution).
2. **`wiki/patterns/x86-to-linuxone-cluster-linking-migration.md`** — x86→LinuxONE migration with regulatory evidence checklist. Source: `accelerators/confluent-on-linuxone/MIGRATION.md` (all 5 sections).
3. **`wiki/concepts/fips-at-install-ocp-requirement.md`** — FIPS-at-install OCP constraint + FIPS-validated cert-manager. Source: `KNOWN-GAPS.md` G-02 + `DESIGN.md` mTLS section.
4. **`wiki/patterns/auditor-readonly-rbac-payload-isolation.md`** — DeveloperRead is consume-granting; topic-scoped binding is the only payload-isolation path. Source: `DESIGN.md` decision D-02 + `layers/01-rbac/README.md`.
5. **`wiki/concepts/s390x-custom-image-build-pipeline.md`** — Connect + Flink SQL-runner image build (multi-arch, JKS, IBM Semeru). Source: `KNOWN-GAPS.md` G-08 + G-12 + `layers/05-flink/sql-runner/README.md`.
6. **`wiki/patterns/flink-on-cfk-fsi-example-jobs.md`** — Tumbling-window TPS + temporal stream-table enrichment join. Source: `accelerators/confluent-on-linuxone/layers/05-flink/applications/`.

**Frontmatter discipline (per H.1 D-07):** Every article has `confidence: high`, `last_validated: 2026-05-23`, `source: fsi-dsp://accelerator/confluent-on-linuxone` (or layer-scoped: `fsi-dsp://accelerator/confluent-on-linuxone:05-flink`), `tags:` flow sequence.

### 13 KNOWN-GAPS trip-wires (locked)

Encode G-01..G-13 in `tools/vendor-sources.json` (extending the existing H.1 vendor-source-drift mechanism). Each trip-wire entry:
```json
{
  "id": "G-01",
  "title": "Fetch-by-SHA requires network access at activation",
  "status": "open",
  "workaround": "Pre-fetch + artifact-cache OR mirror upstream OR OCP egress NetworkPolicy",
  "fsi_impact": "Air-gapped environments not directly supported — operator must mitigate",
  "source": "accelerators/confluent-on-linuxone/KNOWN-GAPS.md",
  "source_id": "fsi-dsp://accelerator/confluent-on-linuxone"
}
```

`/wiki:lint --full` extension: read the trip-wires JSON, compare each `status` against upstream KNOWN-GAPS.md current value, emit DRIFT/MALFORMED/UNKNOWN findings (non-fatal per H.1 D-09).

### Auditor-readonly review pattern (locked)

`/review` skill (`tools/review-engine.py` or equivalent — discover path) gains a claim-flag rule. When a review document claims any of these (or paraphrases):
- "DeveloperRead on the cluster is sufficient for auditor isolation"
- "auditor binding can be at cluster scope"
- "any read-only role can be used for audit access"

…flag with the canonical correction: "DeveloperRead is consume-granting at the topic-prefix scope it's bound to; auditor isolation requires topic-scoped binding to `confluent-audit-log-events` + SR subjects ONLY, explicitly NOT to `payments.*` business topics (per layer-01 RBAC pattern). See wiki/patterns/auditor-readonly-rbac-payload-isolation.md."

Golden review fixture at `tests/golden/review/cases/auditor-isolation-violation.md` exercising this.

### 15+ golden eval cases (locked)

Distribute across the 6 new articles + auditor pattern + 5+ trip-wires:
- **`/ask` cases (≥10):** One per article (6) + 4 cross-cutting (FSI deploy, accelerator dispatch, migration evidence, trip-wire G-02 FIPS gap)
- **`/review` cases (≥5):** auditor-readonly violation + 4 trip-wire-as-claim violations (G-08 image build, G-12 SQL-runner image, G-02 FIPS, G-13 checkpoint encryption)

Run at H.2 90% CI threshold (`EVAL-02` floor).

### Carry-forward fix (locked — Plan 12-X final)

4 pre-existing wiki articles flagged in Phase 09's deferred-items.md. Convert each `sources:` entry:
- `raw/repos/fsi-dsp/observability/metrics-mapping.md` → `fsi-dsp://reference/observability-metrics-mapping`
- `raw/repos/fsi-dsp/observability/grafana/jmx-exporter-config.yaml` → `fsi-dsp://reference/observability-jmx-exporter-config`
- `raw/repos/fsi-dsp/observability/grafana/README.md` → `fsi-dsp://reference/observability-grafana-readme`
- `raw/repos/fsi-dsp/observability/grafana/dashboard-dr-readiness.json` → `fsi-dsp://reference/observability-dashboard-dr-readiness`

(Exact MANIFEST IDs to verify at planning time — these MIGHT not yet exist as MANIFEST entries; if missing, fall back to the most-specific existing reference ID. Surface as a follow-up if no MANIFEST coverage exists.)

After fix: `pytest tests/test_wiki_citations.py::TestNoRawPaths::test_no_raw_fsi_dsp_paths_in_sources` exits 0. Phase 12 closes both v2.1 wiki ingest AND the v2.0 hygiene debt.

### Claude's Discretion

- Article-internal heading shape: match the dominant pattern in `wiki/concepts/` / `wiki/patterns/` (discover during planning)
- Whether to use a single trip-wire schema or per-gap-status variants: match existing H.1 trip-wire shape in `tools/vendor-sources.json`

</decisions>

<code_context>
## Existing Code Insights

- **Wiki structure:** `wiki/{concepts,patterns,incidents,synthesis,activity}/` — concepts for definitions, patterns for how-to/applied
- **`wiki/_index.md`, `wiki/_graph.md`, `wiki/_queue.md`** — metadata files; new articles need _graph edges (≥1 inbound per H.1 discipline)
- **`tools/vendor-sources.json`** — H.1's vendor-source-drift state file; extend with linuxone-accelerator entries
- **`tools/wiki-lint.py`** — H.1's lint tool; `--full` mode includes vendor-drift checks
- **`tests/test_wiki_citations.py`** — the test asserting no raw fsi-dsp paths in `sources:` (currently failing pre-Phase-9, will continue to fail until Phase 12 cleanup lands)
- **`tests/golden/ask/`, `tests/golden/review/`** — H.2 eval harness layout
- **`raw/repos/fsi-dsp/accelerators/confluent-on-linuxone/`** — primary source (DESIGN.md, KNOWN-GAPS.md, MIGRATION.md, layers/*/README.md)

</code_context>

<specifics>
## Specific Ideas

- **Provenance footer:** Every article cites upstream by `fsi-dsp://<id>` form. Inline `⚠️ unverified` markers per H.1 D-08 for any claim not directly grounded in DESIGN.md / KNOWN-GAPS.md / MIGRATION.md.
- **Article cross-linking:** auditor-readonly-rbac-payload-isolation links to fsi-canon-overlay-for-confluent-skills (H.3a); linuxone-on-cfk-ref-arch links to fsi-data-streaming-platform; x86-to-linuxone-migration links to cluster-linking-topology.
- **Carry-forward fix landing:** Single atomic commit at end of phase (after new articles + tests + trip-wires). Mirrors Phase 9/10 atomic-landing discipline.

</specifics>

<deferred>
## Deferred Ideas

- **Connect + Flink SQL-runner image build CI** — KNOWN-GAPS G-08 + G-12 require pre-built s390x images; CI integration not in scope (would need actual s390x build runners)
- **Live `/wiki:validate` drift sweep** — the H.1 drift mechanism is in place; full pre-merge drift validation is operator-triggered, not Phase 12 work
- **Multi-accelerator pattern generalization** — Phase 12 documents only confluent-on-linuxone; future accelerators get their own ingest phase

</deferred>
