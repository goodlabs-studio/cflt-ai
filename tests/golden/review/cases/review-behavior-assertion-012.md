---
id: review-behavior-assertion-012
input_files:
  - tests/golden/review/fixtures/correct-consumer-config.md
expected_claims_min: 3
floor_model: haiku
tags: [kafka, consumers, rebalance, offset-commit, behavior-assertion]
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

## Case: Behavior assertion category — consumer rebalance and offset commit

**What the review MUST find:**
- Behavior assertion claims extracted: rebalance on member failure, at-least-once on explicit commit
- Confirmed verdicts for the behavior assertions (they are accurate)
- Confirmed that uncommitted offsets are reprocessed after rebalance

**What the review MUST NOT contain:**
- Incorrect characterization of Kafka consumer rebalance semantics
- Suggestion that auto-commit provides equivalent guarantees to explicit commit

**Negative-space trigger:** NO
