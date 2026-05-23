# Deferred Items — Phase 09

Out-of-scope issues discovered during Phase 09 execution. Per GSD SCOPE BOUNDARY rule: only auto-fix issues directly caused by the current plan's changes; pre-existing failures in unrelated files go here.

## Pre-existing test failure — `test_wiki_citations.py::TestNoRawPaths::test_no_raw_fsi_dsp_paths_in_sources`

**Discovered:** 2026-05-23 during Phase 09 Plan 01 Task 3 full-suite regression check.

**Status:** Pre-existing — reproduced on the pre-bump tree via `git stash && pytest ...`. Not caused by the submodule pointer bump or the test_manifest.py fix.

**Origin commit:** `bd7f967 feat(wiki): observability expansion — 6 articles closing CC vs self-managed gap`

**Failure:**
```
AssertionError: 6 wiki articles still use raw file paths in sources:
  - wiki/concepts/confluent-platform-broker-jmx.md: 'raw/repos/fsi-dsp/observability/grafana/jmx-exporter-config.yaml'
  - wiki/concepts/observability-metrics-mapping.md: 'raw/repos/fsi-dsp/observability/metrics-mapping.md'
  - wiki/patterns/cfk-observability-baseline.md: 'raw/repos/fsi-dsp/observability/grafana/jmx-exporter-config.yaml'
  - wiki/patterns/cfk-observability-baseline.md: 'raw/repos/fsi-dsp/observability/grafana/README.md'
  - wiki/patterns/cluster-linking-observability.md: 'raw/repos/fsi-dsp/observability/grafana/dashboard-dr-readiness.json'
  - wiki/patterns/cluster-linking-observability.md: 'raw/repos/fsi-dsp/observability/grafana/README.md'
```

**Fix shape (when addressed):** Convert each `raw/repos/fsi-dsp/...` source reference to `fsi-dsp://<id>` form using MANIFEST.yaml stable IDs. This is a wiki-article cleanup task, orthogonal to the submodule-sync work in Phase 09.

**Recommended phase:** Address as a hygiene PR or fold into Phase 12 (wiki ingest of LinuxONE accelerator) — the observability wiki additions need provenance discipline aligned with the Phase 12 ingest pattern.

**Not blocking Phase 09:** The two failures Phase 09 was scoped to clear (`test_no_drift_on_current_state`, `test_version_is_1_0_0`) are both green after the bump + test fix. The full-suite delta from Phase 09's changes is +2 PASS, 0 new failures.
