---
id: review-schema-premise-010
input_files:
  - tests/golden/review/fixtures/schema-evolution-review.md
expected_claims_min: 4
floor_model: sonnet
tags: [schema-registry, avro, protobuf, compatibility, premise-challenge]
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
  - "Confirmed"
premise_challenge_expected: true
overlay: null
---

## Case: Schema evolution — premise challenge on FULL compatibility assumption

**What the review MUST find:**
- Premise Challenge identifying the implicit assumption that all consumer teams are coordinated enough for FULL mode
- Challenge that FULL mode requires coordination for field removal — the document does not establish this precondition
- Premise Challenge also on TopicNameStrategy: assumes only one event type per topic (unstated premise)
- Confirmed verdicts where document claims are accurate

**What the review MUST NOT contain:**
- Uncritical acceptance of all FULL compatibility assumptions without noting coordination requirements
- Incorrect characterization of subject naming strategies

**Negative-space trigger:** YES (premises around team coordination for FULL mode are worth challenging)
