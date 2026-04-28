---
id: review-bad-acks-premise-002
input_files:
  - tests/golden/review/fixtures/bad-acks-producer.md
expected_claims_min: 3
floor_model: sonnet
tags: [kafka, producers, acks, idempotence, premise-challenge]
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

## Case: Bad acks — premise challenge on durability assumption

**What the review MUST find:**
- Corrections for acks=1 and enable.idempotence=false
- Premise Challenge section identifying the implicit assumption that consumer-side deduplication is sufficient
- Challenge that the premise of consumer-side dedup as durability substitute is not guaranteed in failure scenarios

**What the review MUST NOT contain:**
- Endorsement of consumer-side-only deduplication as a substitute for producer idempotence

**Negative-space trigger:** NO
