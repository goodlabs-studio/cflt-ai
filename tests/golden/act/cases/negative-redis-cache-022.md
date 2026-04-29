---
id: negative-redis-cache-022
request: "set up a Redis cache cluster with Kafka Streams state store"
expected_artifact: null
floor_model: haiku
tags: [negative-space, out-of-scope]
required_claims:
  - "no matching artifact"
  - "PR proposal"
forbidden_claims:
  - 'resource "confluent_'
negative_space: true
---

## Case: Redis cache cluster provisioning (out of scope)

**What the answer MUST contain:**
- "no matching artifact" — fsi-dsp has no Redis provisioning capability
- Suggestion to raise a PR proposal to add the capability to fsi-dsp if needed

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks for confluent_* resources

**Negative-space trigger:** YES — Redis is not a Confluent artifact and fsi-dsp has no Redis provisioning. The agent should decline and propose extending the platform via PR if the use case is valid.

**ACT-06 enforcement:** No inline Terraform; no mcp-confluent write tools.

**Note:** Kafka Streams state stores are a valid Kafka pattern, but Redis provisioning is out of scope. The agent can explain the Kafka Streams state store concept but must not provision Redis infrastructure.
