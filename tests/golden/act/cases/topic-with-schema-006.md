---
id: topic-with-schema-006
request: "create a governed topic with Avro schema and RBAC bindings"
expected_artifact: "module/topic"
floor_model: sonnet
tags: [topic, terraform, schema, rbac]
required_claims:
  - "module/topic"
  - "schema"
  - "RBAC"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: Governed topic with Avro schema and RBAC

**What the answer MUST contain:**
- Reference to the module/topic fsi-dsp artifact (which bundles topic + schema + RBAC)
- Mention of schema registration and RBAC role bindings included in the module

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks for individual confluent_* resources

**Negative-space trigger:** NO

**MANIFEST link:** fsi-dsp://module/topic — "Single-call governed topic: topic + schema + RBAC + DR mirror"
