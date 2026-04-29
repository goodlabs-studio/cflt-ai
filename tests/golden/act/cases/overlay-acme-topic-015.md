---
id: overlay-acme-topic-015
request: "create a topic for trade events --overlay acme-bank"
expected_artifact: "module/topic"
floor_model: sonnet
tags: [topic, overlay, fsi]
required_claims:
  - "module/topic"
  - "acme-bank"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: Topic creation with customer overlay (acme-bank)

**What the answer MUST contain:**
- Reference to the module/topic fsi-dsp artifact
- Mention of the acme-bank overlay being applied to the canon stack

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks

**Negative-space trigger:** NO

**MANIFEST link:** fsi-dsp://module/topic — "Single-call governed topic: topic + schema + RBAC + DR mirror"

**Overlay context:** acme-bank overlay layer applies customer-specific overrides on top of base + FSI canon defaults.
