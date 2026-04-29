---
id: role-schema-registry-008
request: "register Avro schemas in Schema Registry on-prem"
expected_artifact: "role/cp_schema"
floor_model: haiku
tags: [schema, ansible, cp]
required_claims:
  - "role/cp_schema"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: Avro schema registration on-prem via Ansible

**What the answer MUST contain:**
- Reference to the role/cp_schema fsi-dsp Ansible role
- On-premises Schema Registry context

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks (Ansible role context, not Terraform)

**Negative-space trigger:** NO

**MANIFEST link:** fsi-dsp://role/cp_schema — "Register and manage Avro schemas in Confluent Schema Registry"
