---
id: role-cp-topic-007
request: "configure a topic on Confluent Platform on RHEL"
expected_artifact: "role/cp_topic"
floor_model: haiku
tags: [topic, ansible, cp]
required_claims:
  - "role/cp_topic"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: Topic configuration on Confluent Platform (RHEL/on-prem)

**What the answer MUST contain:**
- Reference to the role/cp_topic fsi-dsp Ansible role
- On-premises Confluent Platform context (not Confluent Cloud)

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks (Ansible role, not Terraform module)

**Negative-space trigger:** NO

**MANIFEST link:** fsi-dsp://role/cp_topic — "Create and manage governed Kafka topics on Confluent Platform"
