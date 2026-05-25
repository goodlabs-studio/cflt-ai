---
id: review-skill-consult-kstream-rebalance-019
input_files:
  - tests/golden/review/fixtures/skill-consult-kstream-rebalance.md
expected_claims_min: 3
floor_model: sonnet
tags: [kafka-streams, rebalancing, skill-consultation, max-poll-interval, fsi-overlay]
required_report_sections:
  - "## Summary"
  - "## Claim Validation"
  - "## Canon Compliance"
  - "## Recommendations"
required_claims:
  - "max.poll.interval.ms"
  - "kafka-streams-programming"
  - "exactly_once_v2"
forbidden_content:
  - "I don't know"
  - "cannot answer"
expected_verdict_contains:
  - "Corrected"
premise_challenge_expected: false
overlay: null
---

## Case: Skill consultation routes KStream rebalance memo to kafka-streams-programming

**What the review MUST find:**
- Claim that `max.poll.interval.ms=1800000` is "the best fix" for rebalancing
  loops — expect `Corrected` verdict; skill-programming guidance says the root
  cause is usually processing-time bounds or partition ownership churn, not the
  poll interval alone. Increasing it masks the symptom.
- Claim that `processing.guarantee=at_least_once` is acceptable for production
  payments topology — expect `Corrected` verdict against the FSI overlay row
  that mandates `exactly_once_v2` for regulatory reporting (SOX 302/404).
- Skill column populated with `kafka-streams-programming` for at least one
  claim (KStream / topology / StreamsBuilder / GlobalKTable / tumbling window
  keywords appear throughout the memo).
- Canon Compliance table reflects the FSI overlay override for
  `processing.guarantee`.

**What the review MUST NOT contain:**
- Any statement that increasing `max.poll.interval.ms` is a sufficient
  standalone remediation.
- Any statement that `at_least_once` is FSI-acceptable for payments.

**Negative-space trigger:** NO (this is a positive coverage case for skill
consultation).

**Skill routing expectation:** at least one claim routes to
`kafka-streams-programming` per `tools/skill_routing.py`. The FSI overlay
section is loaded and the `processing.guarantee` row is applied to canon
compliance.
