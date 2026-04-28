---
id: review-fsi-latency-004
input_files:
  - tests/golden/review/fixtures/fsi-latency-assumptions.md
expected_claims_min: 3
floor_model: sonnet
tags: [fsi, latency, market-data, architecture, premise-challenge]
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
overlay: null
---

## Case: FSI market data latency — premise challenge on <10ms SLA

**What the review MUST find:**
- Premise Challenge identifying that the document assumes <10ms is sufficient for market data
- Challenge based on FSI canon latency tiers: market data tier is sub-millisecond, not <10ms
- Corrected verdict on the latency SLA claim
- Note that standard 1GbE and commodity servers cannot achieve sub-millisecond market data delivery

**What the review MUST NOT contain:**
- Endorsement of 10ms as acceptable for market data distribution
- Claim that standard datacenter connectivity is sufficient for market data without qualification

**Negative-space trigger:** YES (document's latency claim is directionally wrong for FSI market data tier)
