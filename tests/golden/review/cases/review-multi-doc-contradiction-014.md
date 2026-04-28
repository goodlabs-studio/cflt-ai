---
id: review-multi-doc-contradiction-014
input_files:
  - tests/golden/review/fixtures/multi-doc-deck.md
  - tests/golden/review/fixtures/multi-doc-tfvars.tfvars
expected_claims_min: 4
floor_model: sonnet
tags: [kafka, multi-doc, json-schema, replication, partitions, contradiction]
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

## Case: Multi-document cross-file contradiction detection

**What the review MUST find:**
- Claims attributed by source file (deck-*, tfvars-*)
- Deck claims JSON Schema format — Corrected (canon requires Avro/Protobuf in production)
- tfvars claims replication_factor=2 — Corrected (canon requires 3)
- tfvars claims min_isr=1 — Corrected (canon requires 2)
- Cross-document note: deck says replication factor 3, tfvars sets it to 2 — contradiction
- Canon Compliance table covering both documents

**What the review MUST NOT contain:**
- Single undifferentiated claim pool mixing deck and tfvars claims
- Missing the internal contradiction between deck and tfvars on replication factor

**Negative-space trigger:** NO
