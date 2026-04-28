---
id: review-full-pipeline-015
input_files:
  - tests/golden/review/fixtures/overlay-compression-doc.md
expected_claims_min: 3
floor_model: sonnet
tags: [kafka, producers, compression, overlay, acme-bank, premise-challenge, full-pipeline]
required_report_sections:
  - "## Summary"
  - "## Claim Validation"
  - "## Premise Challenge"
  - "## Canon Compliance"
  - "## Recommendations"
  - "## Gaps"
forbidden_content:
  - "I don't know"
  - "cannot answer"
expected_verdict_contains:
  - "Corrected"
premise_challenge_expected: true
overlay: acme-bank
---

## Case: Full pipeline — overlay + premise challenge on compression doc

**What the review MUST find:**
- Corrected verdict for lz4 recommendation under acme-bank overlay (must use zstd)
- Premise Challenge: document assumes throughput-optimization is the primary constraint; acme-bank's storage constraint changes this
- Overlay Override column in Canon Compliance table
- Gaps section present (even if empty, required section)
- Provenance footer referencing acme-bank overlay

**What the review MUST NOT contain:**
- Missing Premise Challenge section (it IS required in this case)
- Missing Overlay Override column in Canon Compliance
- Confirmed verdict for lz4 under acme-bank overlay

**Negative-space trigger:** YES (both premise and verdict flip under overlay)
