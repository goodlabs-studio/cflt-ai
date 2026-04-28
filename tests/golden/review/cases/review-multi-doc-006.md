---
id: review-multi-doc-006
input_files:
  - tests/golden/review/fixtures/multi-doc-deck.md
  - tests/golden/review/fixtures/multi-doc-tfvars.tfvars
  - tests/golden/review/fixtures/multi-doc-runbook.md
expected_claims_min: 6
floor_model: sonnet
tags: [kafka, multi-doc, schema-registry, json-schema, replication, partitions]
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

## Case: Multi-document review — deck, tfvars, runbook

**What the review MUST find:**
- Claims attributed to each source document separately (deck-1, deck-2; tfvars-1, etc.)
- Corrected verdict on JSON Schema usage in deck (canon requires Avro or Protobuf in production)
- Corrected verdict on replication_factor=2 in tfvars (canon requires 3)
- Corrected verdict on min.isr=1 in tfvars (canon requires 2)
- Corrected verdict on partition_count=3 if throughput formula is considered
- Cross-document noting that runbook acknowledges replication_factor=2 trade-off

**What the review MUST NOT contain:**
- Single undifferentiated claim pool (claims must be labeled by source)
- Endorsement of JSON Schema for production without qualification
- Endorsement of replication_factor=2 as sufficient

**Negative-space trigger:** NO
