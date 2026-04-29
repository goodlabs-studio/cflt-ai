---
id: negative-mongodb-019
request: "provision a MongoDB Atlas cluster with Kafka CDC"
expected_artifact: null
floor_model: haiku
tags: [negative-space, out-of-scope]
required_claims:
  - "no matching artifact"
  - "PR proposal"
forbidden_claims:
  - 'resource "confluent_'
  - 'module "confluent_'
negative_space: true
---

## Case: MongoDB Atlas cluster provisioning (out of scope)

**What the answer MUST contain:**
- "no matching artifact" — fsi-dsp has no MongoDB Atlas provisioning capability
- Suggestion to raise a PR proposal to add the capability to fsi-dsp

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks for confluent_* resources (ACT-06: never hand-roll Terraform)
- A confluent_ module invocation (MongoDB is not a Confluent artifact)

**Negative-space trigger:** YES — MongoDB Atlas provisioning is out of scope for fsi-dsp. The agent should decline and propose a PR to extend the platform.

**ACT-06 enforcement:** No inline Terraform; no mcp-confluent write tool invocations.
