---
id: flink-stream-processing-004
request: "set up a Flink compute pool for trade enrichment"
expected_artifact: "module/flink"
floor_model: sonnet
tags: [flink, terraform, processing]
required_claims:
  - "module/flink"
forbidden_claims:
  - 'resource "confluent_flink'
negative_space: false
---

## Case: Flink compute pool for trade enrichment

**What the answer MUST contain:**
- Reference to the module/flink fsi-dsp artifact
- Compute pool provisioning for Confluent Cloud Flink

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks for confluent_flink_* resources

**Negative-space trigger:** NO

**MANIFEST link:** fsi-dsp://module/flink — "Flink compute pool and statement provisioning on Confluent Cloud"
