---
id: role-rbac-bindings-009
request: "provision RBAC role bindings for the trading team"
expected_artifact: "role/cp_rbac"
floor_model: haiku
tags: [rbac, ansible, security]
required_claims:
  - "role/cp_rbac"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: RBAC role bindings for trading team on Confluent Platform

**What the answer MUST contain:**
- Reference to the role/cp_rbac fsi-dsp Ansible role
- RBAC provisioning context for on-premises Confluent Platform

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks

**Negative-space trigger:** NO

**MANIFEST link:** fsi-dsp://role/cp_rbac — "Provision role bindings for Confluent Platform RBAC"
