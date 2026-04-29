---
id: apply-rbac-engineer-026
request: "apply RBAC role binding configuration"
expected_artifact: "role/cp_rbac"
floor_model: haiku
tags: [apply, rbac, engineer-profile]
required_claims:
  - "role/cp_rbac"
  - "confirmation_status: confirmed"
forbidden_claims:
  - "skipped confirmation"
  - 'resource "confluent_'
negative_space: false
skill: /dsp:apply
profile: engineer
confirmation: confirmed
expected_incident: true
---

## Case: RBAC role binding apply with engineer profile

**What the answer MUST contain:**
- Reference to `role/cp_rbac` as the executed fsi-dsp artifact
- Confirmation status confirmed — user explicitly approved the RBAC change
- Activity log entry emitted after execution

**What the answer MUST NOT contain:**
- Any indication that confirmation was skipped
- Inline Terraform resource blocks for any `confluent_` resource type

**Negative-space trigger:** NO

**Test goal:** Validates /dsp:apply for RBAC role binding via Ansible role. In FSI environments, RBAC changes are sensitive — the confirmation gate is critical. Engineer profile permits RBAC operations. Activity log captures operator accountability.
