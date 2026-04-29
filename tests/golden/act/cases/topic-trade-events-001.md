---
id: topic-trade-events-001
request: "create a topic for trade events with replication and DR"
expected_artifact: "module/topic"
floor_model: sonnet
tags: [topic, terraform, dr, fsi]
required_claims:
  - "module/topic"
  - "confluent_kafka_topic"
forbidden_claims:
  - 'resource "confluent_kafka_topic"'
negative_space: false
---

## Case: Trade events topic with replication and DR

**What the answer MUST contain:**
- Reference to the module/topic fsi-dsp artifact (single-call governed topic)
- Mention of confluent_kafka_topic as the underlying resource managed by the module
- DR mirroring included in the module invocation

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks for confluent_kafka_topic (agent never hand-rolls Terraform)

**Negative-space trigger:** NO

**MANIFEST link:** fsi-dsp://module/topic — "Single-call governed topic: topic + schema + RBAC + DR mirror"
