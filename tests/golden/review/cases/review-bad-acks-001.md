---
id: review-bad-acks-001
input_files:
  - tests/golden/review/fixtures/bad-acks-producer.md
expected_claims_min: 3
floor_model: haiku
tags: [kafka, producers, acks, idempotence, durability]
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

## Case: Bad acks configuration correction

**What the review MUST find:**
- Claim that `acks=1` is recommended — expect Corrected verdict against canon `acks=all`
- Claim that `enable.idempotence=false` is acceptable — expect Corrected verdict (canon requires true)
- At least 3 extractable claims total
- Canon Compliance table showing deviations on acks and idempotence

**What the review MUST NOT contain:**
- Any statement that acks=1 is acceptable for durable production workloads
- Any statement that idempotence is optional

**Negative-space trigger:** NO
