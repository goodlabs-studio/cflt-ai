---
id: topic-compliance-audit-003
request: "create a compliance audit topic with 7-year retention"
expected_artifact: "module/topic"
floor_model: haiku
tags: [topic, terraform, compliance]
required_claims:
  - "module/topic"
  - "retention"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: Compliance audit topic with long retention

**What the answer MUST contain:**
- Reference to the module/topic fsi-dsp artifact
- Discussion of retention configuration (7-year is FSI regulatory requirement for OFAC/AML)

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks (no hand-rolled confluent_* resources)

**Negative-space trigger:** NO

**MANIFEST link:** fsi-dsp://module/topic — "Single-call governed topic: topic + schema + RBAC + DR mirror"
