---
id: overlay-fsi-latency-016
request: "provision a market data topic meeting sub-millisecond SLA"
expected_artifact: "module/topic"
floor_model: sonnet
tags: [topic, fsi, latency]
required_claims:
  - "module/topic"
  - "sub-millisecond"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: Market data topic with sub-millisecond SLA requirement

**What the answer MUST contain:**
- Reference to the module/topic fsi-dsp artifact
- Sub-millisecond latency SLA context (FSI market data tier)

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks

**Negative-space trigger:** NO

**FSI context:** Sub-millisecond is the market data SLA tier in the FSI overlay. The module/topic artifact handles the provisioning; SLA tier drives partitioning and replication configuration.

**MANIFEST link:** fsi-dsp://module/topic — "Single-call governed topic: topic + schema + RBAC + DR mirror"
