---
id: review-skill-mcp-conflict-021
input_files:
  - tests/golden/review/fixtures/skill-mcp-conflict.md
expected_claims_min: 3
floor_model: sonnet
tags: [cdc, tableflow, skill-consultation, skill-mcp-conflict, debezium]
required_report_sections:
  - "## Summary"
  - "## Claim Validation"
  - "## Canon Compliance"
  - "## Recommendations"
required_claims:
  - "confluent-cloud-cdc-tableflow"
  - "Tableflow"
forbidden_content:
  - "I don't know"
  - "cannot answer"
expected_verdict_contains:
  - "Corrected"
premise_challenge_expected: false
overlay: null
---

## Case: Skill consultation routes CDC/Tableflow design to confluent-cloud-cdc-tableflow

**What the review MUST find:**
- Claim that `JSON_SR` is acceptable for the Debezium connector — expect
  `Corrected` against the FSI overlay row that mandates Avro or Protobuf
  in production (JSON_SR is acceptable for the upstream skill's tutorials
  but the FSI overlay overrides that default).
- Claim that automatic Tableflow schema evolution is sufficient — expect
  the skill consultation to surface that Tableflow column-add evolution
  is supported, but column-rename evolution requires explicit handling
  (skill's references body covers this nuance).
- Skill column populated with `confluent-cloud-cdc-tableflow` for at least
  one claim (Debezium, Tableflow, Iceberg keywords).

**Skill-MCP conflict handling (the heart of this case):**

The skill's `references/` body and the upstream Confluent docs may treat
column-rename evolution slightly differently — the skill emphasizes the
operator burden of explicit transforms, while `confluent-docs` may describe
the generic "schema evolution supported" capability. When skill_verdict and
mcp_verdict disagree on this nuance, the report MUST:

1. Use MCP's verdict in the `Verdict` column (MCP authoritative).
2. Append a ⚠️ Skill-MCP conflict note in the Corrections section citing
   both perspectives.

This case validates that the conflict-handling logic in `/review` Step 4.0.5
is exercised end-to-end.

**What the review MUST NOT contain:**
- Any statement that Tableflow magically handles all schema changes
  without operator intervention.
- Suppression of the skill consultation result when it conflicts with MCP
  (both verdicts must appear in the report).

**Negative-space trigger:** NO.
