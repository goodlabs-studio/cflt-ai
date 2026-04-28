---
phase: 02-review-skill
plan: "03"
subsystem: testing
tags: [golden-test-harness, review-skill, pytest, tdd, fixtures, yaml-front-matter, premise-challenge, overlay, multi-doc]

# Dependency graph
requires:
  - phase: 02-review-skill/02-01
    provides: /review skill contract (claim categories, premise-challenge step, overlay differential, report sections)
  - phase: 02-review-skill/02-02
    provides: acme-bank overlay (canon/customer/acme-bank/overrides.yaml with zstd and sub-100-microsecond)
  - phase: 01-knowledge-skill/01-03
    provides: tests/golden/ask/ harness pattern (load_case, ALL_CASES, TestGoldenHarnessStructure, parametrize)
provides:
  - tests/golden/review/ golden test harness with 16 structural cases and 8 synthetic fixtures
  - REVW-05 coverage: >= 15 cases with TDD RED-GREEN discipline
  - REVW-02 coverage: 4 premise-challenge cases (002, 004, 005, 010, 015)
  - REVW-04 coverage: 2 multi-doc cases (006, 014)
  - REVW-06 coverage: 3 overlay cases with acme-bank (005, 008, 015)
  - REVW-01 coverage: correction accuracy cases with expected_verdict_contains: Corrected
affects:
  - Phase 4 LLM eval: harness is the eval execution surface for /review skill
  - Phase 3 act-rail: pattern established for golden harness structure

# Tech tracking
tech-stack:
  added: []
  patterns:
    - TDD RED-GREEN for golden harness (commit failing tests, then author cases to satisfy)
    - YAML front matter + markdown body for /review case files (mirrors /ask harness pattern)
    - Fixture documents as synthetic test documents (15-50 lines, specific claim targets)
    - Parametrized pytest over CASES_DIR glob for per-case structural tests
    - Fixture path resolution relative to repo root via Path(__file__).resolve().parent.parent.parent.parent

key-files:
  created:
    - tests/golden/review/__init__.py
    - tests/golden/review/test_golden_review.py
    - tests/golden/review/README.md
    - tests/golden/review/cases/review-bad-acks-001.md
    - tests/golden/review/cases/review-bad-acks-premise-002.md
    - tests/golden/review/cases/review-correct-consumer-003.md
    - tests/golden/review/cases/review-fsi-latency-004.md
    - tests/golden/review/cases/review-fsi-overlay-latency-005.md
    - tests/golden/review/cases/review-multi-doc-006.md
    - tests/golden/review/cases/review-overlay-compression-007.md
    - tests/golden/review/cases/review-overlay-compression-diff-008.md
    - tests/golden/review/cases/review-schema-evolution-009.md
    - tests/golden/review/cases/review-schema-premise-010.md
    - tests/golden/review/cases/review-config-values-011.md
    - tests/golden/review/cases/review-behavior-assertion-012.md
    - tests/golden/review/cases/review-metrics-sla-013.md
    - tests/golden/review/cases/review-multi-doc-contradiction-014.md
    - tests/golden/review/cases/review-full-pipeline-015.md
    - tests/golden/review/cases/review-empty-premise-016.md
    - tests/golden/review/fixtures/bad-acks-producer.md
    - tests/golden/review/fixtures/correct-consumer-config.md
    - tests/golden/review/fixtures/fsi-latency-assumptions.md
    - tests/golden/review/fixtures/multi-doc-deck.md
    - tests/golden/review/fixtures/multi-doc-tfvars.tfvars
    - tests/golden/review/fixtures/multi-doc-runbook.md
    - tests/golden/review/fixtures/overlay-compression-doc.md
    - tests/golden/review/fixtures/schema-evolution-review.md
  modified: []

key-decisions:
  - "Golden review harness mirrors ask harness pattern exactly: load_case, ALL_CASES glob, parametrize, REQUIRED_FIELDS"
  - "FIXTURES_DIR is a separate constant (tests/golden/review/fixtures/) tested independently from CASES_DIR"
  - "overlay=null in YAML is explicit null (not omitted) — load_case().get('overlay') is None, not KeyError"
  - "Fixture path resolution uses 4x .parent traversal from test file to reach repo root"

patterns-established:
  - "Review case REQUIRED_FIELDS: id, input_files, expected_claims_min, floor_model, tags, required_report_sections, forbidden_content"
  - "Optional fields pattern: expected_verdict_contains (list), premise_challenge_expected (bool), overlay (string|null)"
  - "Fixture file naming: <topic>-<descriptor>.md|.tfvars (plain descriptive, not review-prefixed)"
  - "Case file naming: review-<topic>-<NNN>.md (review-prefixed, zero-padded 3 digits)"
  - "Negative-space trigger indicator in case body markdown"

requirements-completed: [REVW-01, REVW-02, REVW-03, REVW-04, REVW-05, REVW-06]

# Metrics
duration: 4min
completed: 2026-04-28
---

# Phase 02 Plan 03: Review Skill Golden Test Harness Summary

**Pytest golden test harness for /review skill with 16 structural cases (TDD RED-GREEN) covering claim extraction, premise-challenge, multi-doc, and customer overlay across 8 synthetic fixture documents**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-28T21:27:47Z
- **Completed:** 2026-04-28T21:31:47Z
- **Tasks:** 2
- **Files modified:** 27

## Accomplishments

- Created `tests/golden/review/` harness mirroring the Phase 1 `/ask` pattern exactly — same `load_case()` utility, same `pytest.mark.parametrize` over `ALL_CASES` glob, same YAML front matter + markdown body format
- Authored 8 synthetic fixture documents (15–50 lines each) targeting specific review behaviors: bad config, correct config, FSI latency assumptions, multi-doc set (deck/tfvars/runbook), overlay compression differential, schema evolution
- Authored 16 golden case files with full REVW requirement coverage: 4 premise-challenge (REVW-02), 3 acme-bank overlay (REVW-06), 2 multi-doc (REVW-04), 6 correction accuracy (REVW-01); 8 haiku + 8 sonnet floor distribution
- All 106 structural tests pass; full suite 347 tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test runner and README (RED phase)** - `23b07cf` (test)
2. **Task 2: Author 15+ golden cases and fixture documents (GREEN phase)** - `635eefe` (feat)

**Plan metadata:** (docs commit follows)

_Note: TDD task 1 committed failing tests before cases existed (RED phase confirmed), then Task 2 authored cases to satisfy all assertions (GREEN phase confirmed)._

## Files Created/Modified

- `tests/golden/review/__init__.py` - Python package marker
- `tests/golden/review/test_golden_review.py` - Structural test runner (TestGoldenReviewStructure + TestFloorModelDistribution)
- `tests/golden/review/README.md` - Case format spec, distribution requirements, fixture inventory
- `tests/golden/review/cases/review-bad-acks-001.md` - acks=1 correction accuracy case (haiku)
- `tests/golden/review/cases/review-bad-acks-premise-002.md` - acks premise challenge case (sonnet, REVW-02)
- `tests/golden/review/cases/review-correct-consumer-003.md` - All-Confirmed consumer config (haiku)
- `tests/golden/review/cases/review-fsi-latency-004.md` - FSI latency premise challenge (sonnet, REVW-02)
- `tests/golden/review/cases/review-fsi-overlay-latency-005.md` - FSI latency under acme-bank overlay (sonnet, REVW-02+06)
- `tests/golden/review/cases/review-multi-doc-006.md` - Three-file multi-doc review (sonnet, REVW-04)
- `tests/golden/review/cases/review-overlay-compression-007.md` - lz4 base canon aligned (haiku)
- `tests/golden/review/cases/review-overlay-compression-diff-008.md` - lz4 Deviates under acme-bank (haiku, REVW-06)
- `tests/golden/review/cases/review-schema-evolution-009.md` - Schema evolution architecture (sonnet)
- `tests/golden/review/cases/review-schema-premise-010.md` - Schema FULL compat premise challenge (sonnet, REVW-02)
- `tests/golden/review/cases/review-config-values-011.md` - config_value category coverage (haiku)
- `tests/golden/review/cases/review-behavior-assertion-012.md` - behavior_assertion category coverage (haiku)
- `tests/golden/review/cases/review-metrics-sla-013.md` - metric_sla category coverage (haiku)
- `tests/golden/review/cases/review-multi-doc-contradiction-014.md` - Cross-doc contradiction (sonnet, REVW-04)
- `tests/golden/review/cases/review-full-pipeline-015.md` - Full pipeline: overlay+premise (sonnet, REVW-02+06)
- `tests/golden/review/cases/review-empty-premise-016.md` - No-premise-challenge negative-space (haiku)
- `tests/golden/review/fixtures/bad-acks-producer.md` - Producer config with acks=1, idempotence=false, snappy
- `tests/golden/review/fixtures/correct-consumer-config.md` - Canon-compliant consumer config
- `tests/golden/review/fixtures/fsi-latency-assumptions.md` - Market data doc with 10ms SLA (wrong for FSI)
- `tests/golden/review/fixtures/multi-doc-deck.md` - Architecture slides with JSON Schema claim
- `tests/golden/review/fixtures/multi-doc-tfvars.tfvars` - Terraform vars with rf=2, min-isr=1, gzip
- `tests/golden/review/fixtures/multi-doc-runbook.md` - Ops runbook referencing deck/tfvars
- `tests/golden/review/fixtures/overlay-compression-doc.md` - lz4 recommendation (base aligned, overlay Deviates)
- `tests/golden/review/fixtures/schema-evolution-review.md` - FULL compat mode, Avro vs Protobuf comparison

## Decisions Made

- Golden review harness mirrors ask harness pattern exactly: `load_case`, `ALL_CASES` glob, parametrize, `REQUIRED_FIELDS`
- `FIXTURES_DIR` is a separate constant (`tests/golden/review/fixtures/`) tested independently from `CASES_DIR`
- `overlay=null` in YAML is explicit null (not omitted) — `load_case().get('overlay')` returns `None`, not `KeyError`
- Fixture path resolution uses 4x `.parent` traversal from test file to reach repo root

## Deviations from Plan

None — plan executed exactly as written. TDD RED-GREEN discipline followed: test runner committed before cases existed, confirmed 9 failures in RED phase, then all 106 tests passing in GREEN phase.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- All REVW requirements structurally covered by the harness
- Phase 2 review-skill phase is complete: /review command, .docx output, and golden harness all done
- Phase 4 will wire the harness to LLM evaluation via CI matrix (same pattern as /ask harness)
- No blockers

## Known Stubs

None. All case files reference fixture documents that exist on disk; no placeholder or mock data.

## Self-Check: PASSED

- All 27 created files exist on disk
- Commits 23b07cf (RED phase) and 635eefe (GREEN phase) confirmed in git log
- 106/106 structural tests pass (`python3 -m pytest tests/golden/review/ -v`)
- Full suite 347/347 tests pass with no regressions

---
*Phase: 02-review-skill*
*Completed: 2026-04-28*
