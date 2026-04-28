---
id: review-overlay-compression-007
input_files:
  - tests/golden/review/fixtures/overlay-compression-doc.md
expected_claims_min: 3
floor_model: haiku
tags: [kafka, producers, compression, lz4]
required_report_sections:
  - "## Summary"
  - "## Claim Validation"
  - "## Canon Compliance"
  - "## Recommendations"
forbidden_content:
  - "I don't know"
  - "cannot answer"
expected_verdict_contains:
  - "Confirmed"
premise_challenge_expected: false
overlay: null
---

## Case: lz4 compression — base canon aligned, no overlay

**What the review MUST find:**
- Confirmed verdict for compression.type=lz4 recommendation (aligns with base canon)
- Canon Compliance table showing lz4 as compliant with base producer defaults
- Comparison claim about lz4 vs zstd is factually accurate

**What the review MUST NOT contain:**
- Corrected verdict on lz4 recommendation (it IS correct under base canon)
- Reference to acme-bank override (no overlay is active in this case)

**Negative-space trigger:** NO
