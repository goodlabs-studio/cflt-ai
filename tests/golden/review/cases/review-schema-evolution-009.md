---
id: review-schema-evolution-009
input_files:
  - tests/golden/review/fixtures/schema-evolution-review.md
expected_claims_min: 4
floor_model: sonnet
tags: [schema-registry, avro, protobuf, compatibility, evolution]
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

## Case: Schema evolution architecture review

**What the review MUST find:**
- Confirmed verdict for FULL compatibility mode choice for shared consumer contracts
- Confirmed verdict for Avro format selection (aligns with canon for Java/Python stack)
- Confirmed verdict for TopicNameStrategy usage
- Note that FULL is stricter than BACKWARD but justifiable for shared contracts
- Accurate characterization of Protobuf's self-describing wire format advantage

**What the review MUST NOT contain:**
- Claim that BACKWARD mode is sufficient for shared consumer contracts (document correctly chose FULL)
- Factual errors in the Avro vs Protobuf comparison

**Negative-space trigger:** NO
