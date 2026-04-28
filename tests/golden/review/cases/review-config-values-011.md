---
id: review-config-values-011
input_files:
  - tests/golden/review/fixtures/bad-acks-producer.md
expected_claims_min: 3
floor_model: haiku
tags: [kafka, producers, config-values, compression, snappy]
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

## Case: Config value category coverage — producer settings

**What the review MUST find:**
- All three config_value category claims extracted: acks=1, enable.idempotence=false, compression.type=snappy
- Corrected verdict for acks=1 (must be acks=all)
- Corrected verdict for enable.idempotence=false (must be true)
- At minimum a note on snappy vs lz4 (canon prefers lz4 for throughput)

**What the review MUST NOT contain:**
- Missing the snappy compression claim
- Missing the idempotence setting claim

**Negative-space trigger:** NO
