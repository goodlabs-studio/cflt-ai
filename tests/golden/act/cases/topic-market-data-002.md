---
id: topic-market-data-002
request: "provision a high-throughput topic for market data feed"
expected_artifact: "module/topic"
floor_model: sonnet
tags: [topic, terraform, market-data]
required_claims:
  - "module/topic"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: High-throughput market data topic

**What the answer MUST contain:**
- Reference to the module/topic fsi-dsp artifact
- Guidance appropriate for sub-millisecond market data SLA tier

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks (no hand-rolled confluent_* resources)

**Negative-space trigger:** NO

**MANIFEST link:** fsi-dsp://module/topic — "Single-call governed topic: topic + schema + RBAC + DR mirror"
