---
id: scenario-cc-aws-012
request: "stand up a Confluent Cloud starter kit on AWS"
expected_artifact: "scenario/cc-aws"
floor_model: haiku
tags: [scenario, aws, cloud]
required_claims:
  - "scenario/cc-aws"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: Confluent Cloud on AWS starter kit

**What the answer MUST contain:**
- Reference to the scenario/cc-aws fsi-dsp scenario
- Confluent Cloud on AWS context (not bare Terraform resources)

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks (use the scenario artifact, not hand-rolled resources)

**Negative-space trigger:** NO

**MANIFEST link:** fsi-dsp://scenario/cc-aws — "Confluent Cloud on AWS starter kit"
