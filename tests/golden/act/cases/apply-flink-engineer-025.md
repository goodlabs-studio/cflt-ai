---
id: apply-flink-engineer-025
request: "apply flink deployment plan with engineer profile"
expected_artifact: "module/flink"
floor_model: haiku
tags: [apply, flink, engineer-profile]
required_claims:
  - "module/flink"
  - "CONFIRM APPLY"
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

## Case: Flink deployment apply with engineer profile

**What the answer MUST contain:**
- Reference to `module/flink` as the executed fsi-dsp artifact
- CONFIRM APPLY confirmation step displayed before execution
- Incident article written to `wiki/incidents/` after execution

**What the answer MUST NOT contain:**
- Any indication that confirmation was skipped
- Inline Terraform resource blocks for any `confluent_` resource type

**Negative-space trigger:** NO

**Test goal:** Validates /dsp:apply for a Flink module deployment. Haiku floor model is appropriate for structural validation. Confirms confirmation gate fires and incident article is emitted for Flink workload applies per ACTA-04 activity log schema.
