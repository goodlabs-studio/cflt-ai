---
id: flink-cdc-pipeline-005
request: "provision Flink SQL for CDC processing from Oracle"
expected_artifact: "module/flink"
floor_model: haiku
tags: [flink, terraform, cdc]
required_claims:
  - "module/flink"
  - "CDC"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: Flink CDC pipeline from Oracle

**What the answer MUST contain:**
- Reference to the module/flink fsi-dsp artifact
- CDC processing context (Oracle source, Flink SQL)

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks (no hand-rolled confluent_* resources)

**Negative-space trigger:** NO

**MANIFEST link:** fsi-dsp://module/flink — "Flink compute pool and statement provisioning on Confluent Cloud"
