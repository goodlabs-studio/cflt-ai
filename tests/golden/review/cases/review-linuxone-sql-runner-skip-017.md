---
id: review-linuxone-sql-runner-skip-017
input_files:
  - tests/golden/review/fixtures/linuxone-sql-runner-skip.md
expected_claims_min: 3
floor_model: haiku
tags: [flink, sql-runner, s390x, linuxone, gap-g12, trip-wire, wiki-02]
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

## Case: LinuxONE SQL-runner image — placeholder treated as templated (trip-wire G-12)

**What the review MUST find:**
- Claim that the CMF operator auto-resolves `<PLACEHOLDER_CP_FLINK_SQL_RUNNER_IMAGE>` → expect Corrected verdict
- Claim that FlinkApplications will work out-of-the-box without a custom s390x SQL-runner image → expect Corrected verdict
- Canon Compliance row citing KNOWN-GAPS G-12 / `s390x-custom-image-build-pipeline` wiki article
- Recommendations: build the s390x SQL-runner image with `docker buildx`, push to registry, replace ALL `<PLACEHOLDER_CP_FLINK_SQL_RUNNER_IMAGE>` references before applying layer 05

**What the review MUST NOT contain:**
- Endorsement of the placeholder-as-templating-variable misreading
- Suggestion that the SQL-runner image can be deferred without consequence

**Negative-space trigger:** NO
