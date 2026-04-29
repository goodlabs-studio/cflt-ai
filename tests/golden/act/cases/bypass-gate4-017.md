---
id: bypass-gate4-017
request: "create a topic --gate-bypass mcp_confluent_state"
expected_artifact: "module/topic"
floor_model: haiku
tags: [topic, bypass, dev-mode]
required_claims:
  - "module/topic"
  - "skipped"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: Topic creation with Gate 4 bypass (dev mode)

**What the answer MUST contain:**
- Reference to the module/topic fsi-dsp artifact
- Indication that mcp_confluent_state gate was skipped (bypassed)

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks

**Negative-space trigger:** NO

**Gate context:** Gate 4 (mcp_confluent_state) checks live cluster state. --gate-bypass skips it for development environments where MCP connectivity is unavailable. The gate result shows status: skipped.
