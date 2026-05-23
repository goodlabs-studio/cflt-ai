---
id: review-linuxone-fips-skip-015
input_files:
  - tests/golden/review/fixtures/linuxone-fips-skip.md
expected_claims_min: 3
floor_model: haiku
tags: [fips, ocp, linuxone, fsi, gap-g02, trip-wire, wiki-02]
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

## Case: LinuxONE FIPS post-install skip (trip-wire G-02)

**What the review MUST find:**
- Claim that post-install FIPS enablement is "straightforward" on OCP → expect Corrected verdict
- Claim that `spec.tls.fips.enabled: true` will deliver FIPS compliance on a non-FIPS-at-install cluster → expect Corrected verdict
- Canon Compliance row citing KNOWN-GAPS G-02 / `fips-at-install-ocp-requirement` wiki article
- Recommendations: re-install OCP with `fips: true` in install-config.yaml; Red Hat does not support post-install FIPS

**What the review MUST NOT contain:**
- Endorsement of the post-install FIPS approach
- Suggestion that `spec.tls.fips.enabled` is effective on a non-FIPS OCP cluster

**Negative-space trigger:** NO
