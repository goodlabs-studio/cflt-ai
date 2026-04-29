---
id: bypass-gate3-018
request: "set up Flink pool --gate-bypass confluent_docs_schema"
expected_artifact: "module/flink"
floor_model: haiku
tags: [flink, bypass, dev-mode]
required_claims:
  - "module/flink"
  - "skipped"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: Flink pool setup with Gate 3 bypass (dev mode)

**What the answer MUST contain:**
- Reference to the module/flink fsi-dsp artifact
- Indication that confluent_docs_schema gate was skipped (bypassed)

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks

**Negative-space trigger:** NO

**Gate context:** Gate 3 (confluent_docs_schema) validates the plan against live Confluent docs. --gate-bypass skips it for offline or air-gapped development. The gate result shows status: skipped.
