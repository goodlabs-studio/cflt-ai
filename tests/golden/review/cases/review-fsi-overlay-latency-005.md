---
id: review-fsi-overlay-latency-005
input_files:
  - tests/golden/review/fixtures/fsi-latency-assumptions.md
expected_claims_min: 3
floor_model: sonnet
tags: [fsi, latency, market-data, premise-challenge, overlay, acme-bank]
required_report_sections:
  - "## Summary"
  - "## Claim Validation"
  - "## Premise Challenge"
  - "## Canon Compliance"
  - "## Recommendations"
forbidden_content:
  - "I don't know"
  - "cannot answer"
expected_verdict_contains:
  - "Corrected"
premise_challenge_expected: true
overlay: acme-bank
---

## Case: FSI market data latency under acme-bank overlay

**What the review MUST find:**
- Premise Challenge identifying latency assumptions, with overlay-specific callout
- Under acme-bank overlay, market_data tier is sub-100-microsecond (stricter than FSI base sub-millisecond)
- Canon Compliance table with Overlay Override column showing the acme-bank differential
- Corrected verdict on latency SLA claim, citing overlay-specific requirement
- Distinction between base FSI sub-millisecond and acme-bank sub-100-microsecond

**What the review MUST NOT contain:**
- Use of FSI base tier alone without noting acme-bank override
- Claim that 10ms is acceptable under any FSI profile

**Negative-space trigger:** YES (overlay makes the mismatch even more critical)
