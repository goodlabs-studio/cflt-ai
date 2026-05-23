---
id: review-linuxone-checkpoint-unencrypted-018
input_files:
  - tests/golden/review/fixtures/linuxone-checkpoint-unencrypted.md
expected_claims_min: 3
floor_model: haiku
tags: [flink, checkpoint, encryption, linuxone, gap-g13, trip-wire, pci-dss, wiki-02]
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

## Case: LinuxONE checkpoint state unencrypted (trip-wire G-13)

**What the review MUST find:**
- Claim that checkpoint state is transient and therefore exempt from encryption-at-rest → expect Corrected verdict
- Claim that PCI-DSS 3.4 does not apply to short-lived processing state → expect Corrected verdict
- Canon Compliance row citing KNOWN-GAPS G-13 + PCI-DSS 3.4 + GLBA Safeguards Rule
- Recommendations: use an OCP encrypted StorageClass (LUKS2 / CPACF) OR S3-compatible endpoint with SSE-KMS; replace `<PLACEHOLDER_ENCRYPTED_CHECKPOINT_STORAGE_URI>` before applying layer 05

**What the review MUST NOT contain:**
- Endorsement of unencrypted `gp3` StorageClass for FSI Flink checkpoint state
- Suggestion that transient duration removes the encryption-at-rest requirement

**Negative-space trigger:** NO
