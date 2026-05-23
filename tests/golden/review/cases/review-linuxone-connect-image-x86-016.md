---
id: review-linuxone-connect-image-x86-016
input_files:
  - tests/golden/review/fixtures/linuxone-connect-image-x86.md
expected_claims_min: 3
floor_model: haiku
tags: [connect, s390x, linuxone, gap-g08, trip-wire, image-build, wiki-02]
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

## Case: LinuxONE Connect image — x86 base used without s390x rebuild (trip-wire G-08)

**What the review MUST find:**
- Claim that upstream `confluentinc/confluent-kafka-connect:8.2.0` is usable on s390x without rebuilding → expect Corrected verdict
- Canon Compliance row citing KNOWN-GAPS G-08 / `s390x-custom-image-build-pipeline` wiki article
- Recommendations: `docker buildx build --platform linux/s390x` is required; pre-install connector JARs into the s390x base image
- Reference to the s390x image build pipeline

**What the review MUST NOT contain:**
- Endorsement of the multi-arch-pull-handles-it approach for s390x Connect
- Suggestion that ConfigMap-mounted JARs replace the need for a custom-built s390x image

**Negative-space trigger:** NO
