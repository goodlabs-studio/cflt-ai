---
phase: 02-review-skill
plan: 02
subsystem: tools
tags: [docx, review, provenance, canon-overlay, customer-overlay, python-docx, testing]

# Dependency graph
requires:
  - phase: 02-review-skill/02-01
    provides: /review skill invocation contract (Step 6 calls review-to-docx.py), report format (sections, tables, provenance line)
  - phase: 00-foundation
    provides: canon/stack.py (resolve_stack, active_layers), canon/base/defaults.yaml, canon/industry/fsi/overrides.yaml

provides:
  - tools/review-to-docx.py: CLI converter (markdown review report -> .docx) with CANST-04 provenance footer
  - tests/test_review_to_docx.py: 10 unit tests for docx converter (REVW-03 Nyquist compliance)
  - canon/customer/acme-bank/overrides.yaml: Customer overlay with zstd compression and sub-100-microsecond latency
  - canon/customer/acme-bank/adrs/adr-001.md: ADR for producer compression_type override
  - canon/customer/acme-bank/adrs/adr-002.md: ADR for tightened latency SLA tiers
  - tools/__init__.py: importlib alias enabling `from tools.review_to_docx import ...` despite hyphenated filename

affects: [02-03-golden-harness, customer-overlay-validation]

# Tech tracking
tech-stack:
  added:
    - python-docx (already installed; first use of table rendering with explicit column widths via OxmlElement)
    - pyyaml (already installed; used for MANIFEST.yaml version read)
  patterns:
    - "Importlib alias in __init__.py: hyphenated filename (review-to-docx.py) exposed as tools.review_to_docx module via sys.modules"
    - "Explicit column widths via OxmlElement/tcW dxa units (1440 units per inch) — avoids overflow on narrow columns"
    - "Three table layout presets: Claim Validation (5-col), Premise Challenge (5-col), Canon Compliance (3-col)"
    - "CANST-04 provenance footer format: Canon/Hash/MANIFEST/Floor/MCP/Generated/Operator as single Pt(8) grey paragraph"
    - "Customer overlay with no-override-without-ADR rule enforced via override_source field on each group"

key-files:
  created:
    - tools/review-to-docx.py
    - tools/__init__.py
    - tests/test_review_to_docx.py
    - canon/customer/acme-bank/overrides.yaml
    - canon/customer/acme-bank/adrs/adr-001.md
    - canon/customer/acme-bank/adrs/adr-002.md
  modified: []

key-decisions:
  - "tools/__init__.py uses importlib to register review-to-docx.py as tools.review_to_docx — only clean solution for hyphenated module name without renaming the CLI entry point"
  - "Column widths set via OxmlElement/dxa units rather than column_width property — more reliable across python-docx versions"
  - "Provenance footer appended as final document element (not Word document footer) — appears in paragraph flow, not page footer frame"
  - "acme-bank overlays two canon areas (producer compression, latency tiers) producing measurable differential verdicts for golden harness testing"

patterns-established:
  - "Tools importability pattern: tools/__init__.py registers hyphenated-named tools as underscore-named modules via importlib"
  - "Customer overlay pattern: overrides.yaml with override_source per group, ADR per override in adrs/ subdirectory"
  - "Docx provenance footer: Pt(8) grey run as last paragraph — consistent with report format from review.md Step 6"

requirements-completed: [REVW-03, REVW-06]

# Metrics
duration: 3min
completed: 2026-04-28
---

# Phase 2 Plan 02: docx Converter and Customer Overlay Summary

**Markdown-to-docx review converter with CANST-04 provenance footer, 10-test Nyquist suite, and acme-bank customer overlay producing differential canon verdicts on compression and latency**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-28T21:22:26Z
- **Completed:** 2026-04-28T21:25:26Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Created `tools/review-to-docx.py`: CLI tool converting /review markdown reports to .docx; parses sections, renders tables with explicit column widths, adds CANST-04 provenance footer (canon hash, MANIFEST version, floor model, MCP versions, timestamp, operator)
- Created `tests/test_review_to_docx.py`: 10 pytest unit tests (all passing) verifying docx creation, footer fields, section parsing, table extraction, provenance dict structure and ISO timestamp
- Created `canon/customer/acme-bank/` overlay with two ADR-backed overrides that produce different compliance verdicts than base+FSI canon: `producer.compression_type=zstd` (vs base `lz4`) and `latency_tiers.market_data=sub-100-microsecond` (vs FSI `sub-millisecond`)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create review-to-docx.py converter with provenance footer** - `ebc19db` (feat)
2. **Task 2: Create unit tests for review-to-docx.py (Nyquist compliance)** - `815eee9` (test)
3. **Task 3: Create acme-bank customer overlay with ADRs** - `04137b9` (feat)

**Plan metadata:** (see final commit below)

## Files Created/Modified
- `tools/review-to-docx.py` - CLI: argparse (input_path, --floor-model, --operator, --mcp-versions); build_review_docx, build_provenance, add_provenance_footer, parse_markdown_report, get_manifest_version, set_col_width
- `tools/__init__.py` - importlib alias so `from tools.review_to_docx import ...` works despite hyphen in filename
- `tests/test_review_to_docx.py` - 10 pytest tests across TestBuildReviewDocx, TestParseMarkdownReport, TestBuildProvenance
- `canon/customer/acme-bank/overrides.yaml` - compression_type=zstd, latency_tiers.market_data=sub-100-microsecond
- `canon/customer/acme-bank/adrs/adr-001.md` - ADR for zstd (7-year retention, storage-constrained)
- `canon/customer/acme-bank/adrs/adr-002.md` - ADR for sub-100-microsecond (algo trading latency requirements)

## Decisions Made
- `tools/__init__.py` uses importlib to expose `review-to-docx.py` as `tools.review_to_docx` — only clean solution for hyphenated CLI filename without renaming the entry point or requiring users to install the package
- Provenance footer implemented as final paragraph in paragraph flow (not Word native footer frame) — simpler, fully visible in body text, matches the line format in review.md Step 6 report output
- Column widths set via OxmlElement `w:tcW` with dxa units — reliable across python-docx versions; three presets for the three table types defined in review.md
- acme-bank overlay selects zstd and sub-100-microsecond as its two differentials — these produce verdict changes on the most common review claims (compression recommendation, latency SLA adequacy)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added tools/__init__.py to enable module importability**
- **Found during:** Task 1 verification (importability check)
- **Issue:** `from tools.review_to_docx import` failed with ModuleNotFoundError because `review-to-docx.py` (hyphenated) is not a valid Python module name, and `tools/` had no `__init__.py`
- **Fix:** Created `tools/__init__.py` with importlib registration that pre-loads `review-to-docx.py` under the `tools.review_to_docx` key in `sys.modules`
- **Files modified:** tools/__init__.py (created)
- **Verification:** `from tools.review_to_docx import build_review_docx, build_provenance, add_provenance_footer` succeeds; all 10 tests pass
- **Committed in:** ebc19db (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Fix was necessary for module importability as specified in plan acceptance criteria. No scope creep.

## Issues Encountered
- Hyphenated filename `review-to-docx.py` is not directly importable as a Python module. Resolved via importlib alias in `tools/__init__.py`. The CLI entry point name is preserved as specified.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 03 (golden harness) can now write differential harness cases that call `resolve_stack(customer='acme-bank')` and compare verdicts against base canon — the two differentials (compression, latency) are live and verified
- The `build_review_docx` function is importable and testable for integration into harness output validation
- `python3 tools/review-to-docx.py <report.md>` is a working CLI invocation for /review --output docx step

---
*Phase: 02-review-skill*
*Completed: 2026-04-28*
