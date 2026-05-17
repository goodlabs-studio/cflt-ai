# Phase 2: Review Skill - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

The /review skill produces reproducible, customer-ready output: deterministic claim extraction with >= 95% reproducibility, a premise-challenge step that interrogates unstated assumptions before validation, .docx output with full provenance footer, multi-document input treating mixed file sets as a single review scope, and at least one validated customer overlay demonstrating differential canon behavior.

</domain>

<decisions>
## Implementation Decisions

### Claim Extraction Determinism
- Structured extraction schema with numbered claim categories (config values, behavior assertions, architecture choices, metrics, comparisons) — forces consistent claim boundaries
- Claims extracted into YAML/JSON intermediate format before rendering to markdown table — enables golden harness comparison and reproducibility measurement
- Extraction proceeds in document-order, section-by-section, with explicit "stop when exhausted" — determinism from structured prompting, not temperature controls
- A "claim" is any statement making a falsifiable technical assertion — configs, behaviors, defaults, comparisons, metrics — consistent with existing Step 2 categories

### Premise-Challenge Step
- New Step 2.5 — after claim extraction (Step 2), before wiki cross-reference (Step 3); challenges the document's premises before validating individual claims
- Constructive critique depth — identify unstated assumptions, question whether premises hold in the customer's context (FSI SLA tiers, regulatory requirements), flag logical gaps
- Dedicated "## Premise Challenge" section in report with table: Premise / Assumption / Challenge / Severity (Critical/Moderate/Minor)
- Overlay-aware challenges: "under your FSI overlay, this premise conflicts with X" when a customer overlay changes the baseline

### .docx Output & Provenance
- python-docx library for .docx generation — pure Python, no external dependencies, write `tools/review-to-docx.py` converter
- Provenance footer schema matches CANST-04: canon stack hash (16-char truncated SHA-256), MANIFEST.yaml version, floor model used, MCP server versions called, timestamp, operator
- Structured formatting with heading styles (Heading1 for title, Heading2 for sections), proper table formatting for claim tables, provenance as footer paragraph with smaller font
- Generated via `--output docx` flag on /review — produces both .md and .docx side by side in `outputs/reports/`

### Multi-Document Input & Customer Overlay
- Multiple documents specified as space-separated paths: `/review deck.pdf runbook.md vars.tfvars` — treated as single review scope
- Each doc's claims extracted separately (labeled by source file), then merged into a single claim validation pass — cross-doc contradictions flagged explicitly
- Customer overlay directory at `canon/overlays/<customer>/` with override YAML files that modify canon defaults — consistent with CANST-01/02 scaffolding from Phase 0
- Overlay validation: golden harness case runs same review twice — once with base canon, once with customer overlay — differential results (different verdicts on at least one claim)

### Claude's Discretion
- Internal wording of claim category definitions and extraction prompting
- Exact premise-challenge question templates
- python-docx style choices (fonts, colors, spacing)
- Golden harness case selection strategy for the 15+ review test cases
- Specific sanitized customer doc content for test fixtures

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.claude/commands/review.md` — current /review skill with 6-step process (will be extended with premise-challenge step, --output flag, multi-doc support)
- `.claude/commands/ask.md` — established mode/flag parsing pattern (--mode, --force-route) to follow for --output flag
- `canon/stack.py` — canon stack hash computation (16-char truncated SHA-256) from Phase 0
- `tools/wiki-lint.py` — front matter parsing patterns reusable for claim YAML handling
- `tests/golden/ask/` — golden harness pattern (YAML front matter + markdown body) to replicate for `tests/golden/review/`
- `wiki/_queue.md` — auto-stub pattern from /ask to preserve in /review

### Established Patterns
- Skills are markdown files in `.claude/commands/` with Step 1-N process + output format
- Golden test cases use YAML front matter with fields: query, expected_route, floor_model, tags + markdown body
- Reports written to `outputs/reports/` with slug-based filenames
- Python CLI tools in `tools/` with argparse, CFLT_WIKI_ROOT env var
- Tests use pytest with fixture-based setup, test classes per logical domain
- Activity log entry per skill invocation with full provenance schema

### Integration Points
- `.claude/commands/review.md` — primary entry point (user types `/review`)
- `tools/review-to-docx.py` — new converter tool
- `tests/golden/review/` — new golden test harness directory
- `canon/overlays/` — customer overlay directory (scaffolded in Phase 0)
- `outputs/reports/` — report output directory (existing)
- Provenance footer uses `canon/stack.py` hash computation

</code_context>

<specifics>
## Specific Ideas

- Premise-challenge should catch FSI-specific gaps: "this design assumes sub-10ms latency but your SLA tier requires sub-millisecond for market data"
- .docx output must be customer-presentable — professional formatting, not a raw dump
- Multi-document input should handle the common review scenario: customer sends a deck + their tfvars + their runbook, all reviewed as one coherent scope
- Golden harness should include at least one case with a deliberately bad document (wrong acks, wrong replication factor) to test correction accuracy

</specifics>

<deferred>
## Deferred Ideas

- PDF input parsing (extract text from customer PDFs) — requires pdfplumber or similar, separate concern
- Automated review scheduling (nightly review of tracked customer docs) — Phase 4+
- Review diff mode (compare two versions of the same document) — future enhancement

</deferred>
