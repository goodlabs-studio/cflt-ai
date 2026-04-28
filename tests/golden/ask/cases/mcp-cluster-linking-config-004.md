---
id: mcp-cluster-linking-config-004
query: "What is the configuration for auto.create.mirror.topics.enable in Cluster Linking?"
expected_route: wiki+mcp
floor_model: sonnet
tags: [cluster-linking, configuration, dr]
required_claims:
  - "auto.create.mirror.topics.enable"
  - "false"
forbidden_claims:
  - "cannot find"
---

## Case: Cluster Linking auto-create mirror topics config

**What the answer MUST contain:**
- The config key auto.create.mirror.topics.enable
- Recommendation to set false in production for explicit control

**What the answer MUST NOT contain:**
- Claims of inability to find the configuration

**Negative-space trigger:** NO
