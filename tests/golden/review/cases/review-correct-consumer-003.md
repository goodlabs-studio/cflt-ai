---
id: review-correct-consumer-003
input_files:
  - tests/golden/review/fixtures/correct-consumer-config.md
expected_claims_min: 4
floor_model: haiku
tags: [kafka, consumers, offset-management, consumer-groups]
required_report_sections:
  - "## Summary"
  - "## Claim Validation"
  - "## Canon Compliance"
  - "## Recommendations"
forbidden_content:
  - "I don't know"
  - "cannot answer"
  - "Corrected"
expected_verdict_contains:
  - "Confirmed"
premise_challenge_expected: false
overlay: null
---

## Case: Correct consumer config — all claims Confirmed

**What the review MUST find:**
- Confirmed verdict for auto.offset.reset=earliest
- Confirmed verdict for enable.auto.commit=false with explicit offset commit
- Confirmed verdict for one consumer group per logical application
- Canon Compliance table showing all areas compliant

**What the review MUST NOT contain:**
- Any Corrected verdicts (document is canon-compliant)
- Suggestions to enable auto-commit

**Negative-space trigger:** NO
