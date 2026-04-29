---
id: role-connect-workers-010
request: "deploy Kafka Connect distributed workers"
expected_artifact: "role/cp_connect"
floor_model: sonnet
tags: [connect, ansible, cp]
required_claims:
  - "role/cp_connect"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: Kafka Connect distributed worker deployment via Ansible

**What the answer MUST contain:**
- Reference to the role/cp_connect fsi-dsp Ansible role
- Distributed workers context (not standalone mode)

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks

**Negative-space trigger:** NO

**MANIFEST link:** fsi-dsp://role/cp_connect — "Deploy and configure Kafka Connect distributed workers"
