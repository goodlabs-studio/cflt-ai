---
id: apply-schema-engineer-024
request: "apply schema registry configuration with engineer profile"
expected_artifact: "role/cp_schema"
floor_model: sonnet
tags: [apply, schema, engineer-profile]
required_claims:
  - "role/cp_schema"
  - "confirmation_status: confirmed"
  - "wiki/incidents/"
forbidden_claims:
  - "skipped confirmation"
  - 'resource "confluent_'
negative_space: false
skill: /dsp:apply
profile: engineer
confirmation: confirmed
expected_incident: true
---

## Case: Schema registry apply with engineer profile

**What the answer MUST contain:**
- Reference to `role/cp_schema` as the executed fsi-dsp artifact
- Confirmation status set to `confirmed` — user selected CONFIRM APPLY
- Incident article written to `wiki/incidents/` path for auditability

**What the answer MUST NOT contain:**
- Any indication that confirmation was skipped
- Inline Terraform resource blocks for any `confluent_` resource type

**Negative-space trigger:** NO

**Test goal:** Validates /dsp:apply for a schema registry configuration using an Ansible role artifact. Engineer profile permits this operation; incident article documents the apply outcome per the activity log schema (ACTA-04).
