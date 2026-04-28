---
id: review-overlay-compression-diff-008
input_files:
  - tests/golden/review/fixtures/overlay-compression-doc.md
expected_claims_min: 3
floor_model: haiku
tags: [kafka, producers, compression, lz4, zstd, overlay, acme-bank]
required_report_sections:
  - "## Summary"
  - "## Claim Validation"
  - "## Canon Compliance"
  - "## Recommendations"
forbidden_content:
  - "I don't know"
  - "cannot answer"
expected_verdict_contains:
  - "Corrected"
premise_challenge_expected: false
overlay: acme-bank
---

## Case: lz4 compression — Deviates under acme-bank overlay

**What the review MUST find:**
- Corrected verdict for lz4 recommendation when acme-bank overlay is active
- Canon Compliance table with Overlay Override column showing acme-bank requires zstd
- Specific callout that acme-bank customer/acme-bank/adr-001 mandates zstd (storage-constrained cluster)
- Recommendation to switch to zstd for acme-bank deployments

**What the review MUST NOT contain:**
- Confirmed verdict for lz4 under acme-bank overlay (lz4 Deviates under this customer's config)
- Missing reference to the overlay-specific override

**Negative-space trigger:** YES (document is correct under base canon but wrong under customer overlay — structural test must distinguish)
