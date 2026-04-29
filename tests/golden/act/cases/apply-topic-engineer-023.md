---
id: apply-topic-engineer-023
request: "apply plan for topic creation with engineer profile"
expected_artifact: "module/topic"
floor_model: sonnet
tags: [apply, topic, engineer-profile, acta-01]
required_claims:
  - "wiki/incidents/"
  - "confirmation_status: confirmed"
  - "execution_result"
  - "module/topic"
forbidden_claims:
  - "skipped confirmation"
  - 'resource "confluent_'
negative_space: false
skill: /dsp:apply
profile: engineer
confirmation: confirmed
expected_incident: true
---

## Case: Topic creation apply with engineer profile

**What the answer MUST contain:**
- Reference to `module/topic` as the executed fsi-dsp artifact
- Confirmation status set to `confirmed` — CONFIRM APPLY was selected
- An execution_result field in the activity log output
- Incident article written to `wiki/incidents/` path

**What the answer MUST NOT contain:**
- Any indication that confirmation was skipped
- Inline Terraform resource blocks for any `confluent_` resource type

**Negative-space trigger:** NO

**Test goal:** Validates the happy path for /dsp:apply — engineer profile, confirmed by user, incident article written with provenance. This is the baseline positive case for the act rail apply path per ACTA-01.
