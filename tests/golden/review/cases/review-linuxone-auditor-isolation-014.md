---
id: review-linuxone-auditor-isolation-014
input_files:
  - tests/golden/review/fixtures/linuxone-auditor-isolation-violation.md
expected_claims_min: 3
floor_model: haiku
tags: [rbac, mds, audit, linuxone, fsi, payload-isolation, wiki-03]
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

## Case: LinuxONE auditor-isolation violation (WIKI-03)

**What the review MUST find:**
- Claim that cluster-scoped DeveloperRead is sufficient for auditor isolation → expect Corrected verdict
- Canon Compliance row noting deviation from layer-01 RBAC payload-isolation pattern
- Recommendations section cites `wiki/patterns/auditor-readonly-rbac-payload-isolation.md`
- Canonical correction text contains "DeveloperRead is consume-granting" verbatim

**What the review MUST NOT contain:**
- Any statement endorsing cluster-scoped DeveloperRead for auditor isolation
- Any claim that the customer's approach is acceptable

**Negative-space trigger:** NO
