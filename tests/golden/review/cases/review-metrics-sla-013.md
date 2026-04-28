---
id: review-metrics-sla-013
input_files:
  - tests/golden/review/fixtures/fsi-latency-assumptions.md
expected_claims_min: 2
floor_model: haiku
tags: [fsi, latency, metrics-sla, market-data]
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
overlay: null
---

## Case: Metric/SLA category — latency threshold claim

**What the review MUST find:**
- metric_sla category claim extracted: 10ms end-to-end latency SLA for market data
- Corrected verdict on the 10ms claim (FSI canon market_data tier is sub-millisecond)
- Reference to FSI canon latency tier definitions
- Specific callout that 150,000 msg/s throughput claim (if present) is a metric that can be verified

**What the review MUST NOT contain:**
- Acceptance of 10ms as the correct market data SLA
- Missing the numeric latency claim as a metric_sla category claim

**Negative-space trigger:** YES (latency number is wrong for FSI market data context)
