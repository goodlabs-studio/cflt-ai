---
id: mcp-acks-config-001
query: "What is the default value of acks in Kafka 3.x producers?"
expected_route: wiki+mcp
floor_model: haiku
tags: [kafka, producers, configuration, version-specific]
required_claims:
  - "acks=all"
  - "default"
forbidden_claims:
  - "I cannot verify"
---

## Case: Default acks in Kafka 3.x

**What the answer MUST contain:**
- Statement about the default value of acks (acks=all as of Kafka 3.0+)
- Reference to the version-specific change

**What the answer MUST NOT contain:**
- Refusal to verify version-specific config

**Negative-space trigger:** NO
