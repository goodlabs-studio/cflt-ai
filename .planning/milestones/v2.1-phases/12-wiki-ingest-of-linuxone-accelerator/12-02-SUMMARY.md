---
phase: 12-wiki-ingest-of-linuxone-accelerator
plan: 02
subsystem: tooling
tags: [vendor-sources, wiki-lint, trip-wires, known-gaps, linuxone, drift-detection, fsi]

# Dependency graph
requires:
  - phase: H.1
    provides: "vendor-source-drift mechanism — tools/vendor-sources.json + tools/wiki-lint.py drift surface (passive per D-09)"
provides:
  - "13 KNOWN-GAPS trip-wires (G-01..G-13) encoded in tools/vendor-sources.json under linuxone-accelerator-gaps key"
  - "check_gap_drift(repo_root, vendor_pins) function in tools/wiki-lint.py emitting DRIFT-GAP / MISSING-GAP / MALFORMED-GAP findings"
  - "Passive drift surface for KNOWN-GAPS status changes — exits 0 per H.1 D-09"
  - "tests/test_wiki_lint_gap_drift.py — 14 tests validating JSON shape + check_gap_drift behavior"
affects:
  - 12-03  # golden eval cases reference G-02, G-08, G-12, G-13 as canonical trip-wire claims
  - 12-04  # carry-forward fix may interact with vendor-sources.json layout

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gap-register trip-wires: vendor-sources.json[\"<key>\"][\"trip_wires\"] list keyed by gap ID, status compared case-insensitively against upstream Markdown table row via regex"
    - "Three new finding categories follow H.1 D-09 passive posture: surface but exit 0"

key-files:
  created:
    - tests/test_wiki_lint_gap_drift.py
  modified:
    - tools/vendor-sources.json
    - tools/wiki-lint.py

key-decisions:
  - "Case-insensitive + whitespace-stripped status comparison (Open == 'open' == ' OPEN ') — matches operator-intent semantics over byte-equality"
  - "Back-compat default: missing linuxone-accelerator-gaps key OR missing KNOWN-GAPS.md returns empty findings silently (no warning, no exception)"
  - "MISSING-GAP naming chosen over MISSING-VENDOR to avoid collision with H.1's UNKNOWN VENDOR finding category"
  - "Findings exposed as 3 separate keys (gap_drift, missing_gap, malformed_gap) for label clarity in --full output"

patterns-established:
  - "Trip-wire schema (7 fields): id, title, status, workaround, fsi_impact, source, source_id — directly portable to other gap-register sources (future accelerators)"
  - "Upstream table-row regex: ^\\|\\s*<ID>\\s*\\|.*\\|\\s*([^|]+?)\\s*\\|\\s*$ — anchors on trailing pipe to extract last cell (Status column) from Markdown table"

requirements-completed: [WIKI-02]

# Metrics
duration: 4min
completed: 2026-05-23
---

# Phase 12 Plan 02: KNOWN-GAPS trip-wires + wiki-lint gap drift surface Summary

**13 LinuxONE KNOWN-GAPS (G-01..G-13) encoded as vendor-sources.json trip-wires; tools/wiki-lint.py --full now surfaces DRIFT-GAP / MISSING-GAP / MALFORMED-GAP findings non-fatally per H.1 D-09.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-23T17:47:57Z
- **Completed:** 2026-05-23T17:51:47Z
- **Tasks:** 2 (TDD: 1 RED + 1 GREEN)
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments

- All 13 entries from `accelerators/confluent-on-linuxone/KNOWN-GAPS.md` (G-01..G-13) encoded verbatim in `tools/vendor-sources.json` under new `linuxone-accelerator-gaps` top-level key; each entry has all 7 required fields
- `check_gap_drift(repo_root, vendor_pins)` added to `tools/wiki-lint.py` — reads trip-wires, compares declared status against upstream Markdown table row via regex, emits 3 finding categories
- `lint_wiki()` invokes `check_gap_drift` when `--full` is set; populates `gap_drift`, `missing_gap`, `malformed_gap` keys; exit code remains 0 (passive posture preserved)
- `main()` labels dict extended with human-readable descriptions for the 3 new finding categories
- 14 tests in `tests/test_wiki_lint_gap_drift.py` covering JSON shape (5), drift detection happy/sad paths (7), defensive edge cases (2), and subprocess exit-code (1) — all PASS
- Zero regression: `test_wiki_lint_drift.py`, `test_check_streaming_skills_drift.py`, `test_wiki_decay.py` all still pass

## Task Commits

1. **Task 1: Author failing tests (RED)** — `5dbb965` (test)
2. **Task 2: Encode trip-wires + check_gap_drift (GREEN)** — `522a442` (feat)

_TDD discipline: RED commit landed 13 failing tests; GREEN commit landed both data (vendor-sources.json) and code (wiki-lint.py) in a single atomic commit since they are co-dependent for the test suite to pass._

## Files Created/Modified

- `tests/test_wiki_lint_gap_drift.py` (created) — 14 tests; importlib-based loader for hyphenated module name `wiki-lint.py`; tmp_path-based synthetic-repo fixtures
- `tools/vendor-sources.json` (modified) — added `linuxone-accelerator-gaps` top-level key with `upstream`, `vendored_path`, `ingested_at`, `kind: gap-register`, and `trip_wires` list of 13 entries; existing `confluent-agent-skills` and `streaming-skills-plugin` blocks byte-unchanged
- `tools/wiki-lint.py` (modified) — added `check_gap_drift()` function (~50 LOC); extended `lint_wiki()` findings dict with 3 new keys; extended `--full` branch to invoke gap-drift check; extended `main()` labels

## JSON Shape Committed (excerpt)

```json
{
  "linuxone-accelerator-gaps": {
    "upstream": "https://github.com/goodlabs-studio/fsi-dsp",
    "vendored_path": "raw/repos/fsi-dsp/accelerators/confluent-on-linuxone/KNOWN-GAPS.md",
    "ingested_at": "2026-05-23",
    "kind": "gap-register",
    "trip_wires": [
      {
        "id": "G-01",
        "title": "Fetch-by-SHA requires network access at activation",
        "status": "Open",
        "workaround": "Pre-fetch + artifact-cache OR mirror upstream OR OCP egress NetworkPolicy allowing github.com",
        "fsi_impact": "Air-gapped FSI environments not directly supported — operator must mitigate",
        "source": "accelerators/confluent-on-linuxone/KNOWN-GAPS.md",
        "source_id": "fsi-dsp://accelerator/confluent-on-linuxone"
      }
      /* ... G-02 through G-13, all with identical 7-field schema ... */
    ]
  }
}
```

All 13 trip-wires share `source_id: "fsi-dsp://accelerator/confluent-on-linuxone"` (top-level accelerator ID; layer-specific IDs deferred — gap tracking operates at accelerator scope).

## Function Signatures Added

```python
def check_gap_drift(repo_root: Path, vendor_pins) -> dict:
    """Returns {"gap_drift": [...], "missing_gap": [...], "malformed_gap": [...]}.
    Silent skip when vendor_pins is None, key absent, or KNOWN-GAPS.md not checked out."""
```

Wired into `lint_wiki()` inside the `if full:` block (alongside orphan detection); 3 new keys added to the `findings` dict initializer; 3 new entries added to `main()` `labels` dict.

## Decisions Made

- **Case-insensitive status comparison** (CONTEXT decision implicit, made explicit during planning): operator intent is to track semantic equivalence (`Open` ≡ `open` ≡ ` OPEN `), not byte-equality. Implemented via `.strip().lower()` on both sides.
- **MISSING-GAP naming** (CONTEXT used "UNKNOWN", plan locked "MISSING-GAP"): chose `MISSING-GAP` over `MISSING-VENDOR` to avoid label collision with H.1's existing `UNKNOWN VENDOR` finding (different semantic — vendor missing vs. upstream gap row missing).
- **Three separate finding keys** (vs. one combined key): preserves H.1 pattern of one finding-category-per-label, makes `--full` output self-documenting via the `labels` dict.
- **Back-compat silent skip** when KNOWN-GAPS.md absent: enables running `wiki-lint.py --full` in environments without the fsi-dsp submodule checked out (CI minimal-deps scenarios).

## Deviations from Plan

None - plan executed exactly as written. The plan's reference implementation for `check_gap_drift` and the test list of 12 cases were both followed; 2 additional defensive tests added (`test_check_gap_drift_handles_missing_vendor_pins_arg`, `test_check_gap_drift_handles_missing_known_gaps_file`) for the explicit back-compat paths documented in the plan body — these aren't deviations, they cover the documented behavior with explicit tests.

## Issues Encountered

None during 12-02. Two pre-existing test_wiki_citations failures remain in the test suite — both are out of 12-02's file scope:
- `test_no_raw_fsi_dsp_paths_in_sources` — deferred to Phase 12-04 carry-forward fix per CONTEXT.md
- `test_all_citations_resolve_against_manifest` — triggered by 12-01's new articles claiming layer-scoped IDs (`fsi-dsp://accelerator/confluent-on-linuxone:01-rbac`, `:02-tls`) that need MANIFEST entries. 12-01 or 12-04 owns this.

## Verification Evidence

```
$ python3 -m pytest tests/test_wiki_lint_gap_drift.py -v
14 passed in 0.04s

$ python3 tools/wiki-lint.py --full ; echo "exit=$?"
Wiki lint findings (26 total):
  Orphaned articles (4) — 12-01's new wiki articles, expected
  Unverified inline claims (21) — pre-existing, out of 12-02 scope
  Vendor-source DRIFT (1) — pre-existing, out of 12-02 scope
exit=0   # passive posture preserved

$ python3 -m pytest tests/test_wiki_lint_drift.py tests/test_check_streaming_skills_drift.py tests/test_wiki_decay.py
21 passed in 0.30s   # zero regression
```

## Next Phase Readiness

- **Plan 12-03** (golden eval cases) references 4-5 trip-wires (G-02 FIPS, G-08 Connect image, G-12 SQL-runner image, G-13 checkpoint encryption) as canonical claim sources in `/review` golden cases — all present and addressable by ID now.
- **Plan 12-04** (carry-forward citation fixes) — vendor-sources.json shape is stable; carry-forward landing won't conflict.
- **WIKI-02 requirement** (13 KNOWN-GAPS trip-wires + lint drift surface) — structurally satisfied; ready to mark complete.

## Self-Check: PASSED

- File `tests/test_wiki_lint_gap_drift.py` exists: FOUND
- File `tools/vendor-sources.json` modified with 13 trip-wires: FOUND (verified via python3 -c assertion)
- File `tools/wiki-lint.py` modified with check_gap_drift: FOUND (grep confirms `def check_gap_drift`)
- Commit `5dbb965` (RED): FOUND in git log
- Commit `522a442` (GREEN): FOUND in git log
- All 14 new tests pass: VERIFIED
- `python3 tools/wiki-lint.py --full` exits 0: VERIFIED
- No regression in existing test suites: VERIFIED (21 pre-existing tests still pass)

---
*Phase: 12-wiki-ingest-of-linuxone-accelerator*
*Completed: 2026-05-23*
