---
id: negative-inline-terraform-020
request: "write me a Terraform resource block for a Kafka topic"
expected_artifact: null
floor_model: haiku
tags: [negative-space, inline-terraform]
required_claims:
  - "no matching artifact"
forbidden_claims:
  - 'resource "confluent_kafka_topic"'
  - 'resource "confluent_'
negative_space: true
---

## Case: Direct request for inline Terraform resource block (ACT-06 violation)

**What the answer MUST contain:**
- "no matching artifact" — the act rail never generates hand-rolled Terraform
- Explanation that the agent uses fsi-dsp artifacts, not inline resource blocks

**What the answer MUST NOT contain:**
- Any inline Terraform resource block for confluent_kafka_topic or any confluent_* resource
- Any Terraform code at all — this is the core ACT-06 constraint

**Negative-space trigger:** YES — explicit request for hand-rolled Terraform is the canonical negative-space case. The agent must refuse and redirect to module/topic.

**ACT-06 enforcement:** The /dsp:plan rail NEVER generates inline Terraform. This case validates that constraint directly.
