---
id: deep-dr-architecture-001
query: "Design a disaster recovery architecture for a multi-region FSI Kafka deployment with RPO < 10 seconds"
expected_route: deep
floor_model: sonnet
tags: [dr, fsi, cluster-linking, multi-region, architecture]
required_claims:
  - "Cluster Linking"
  - "RPO"
  - "region"
forbidden_claims:
  - "simple"
  - "just use"
---

## Case: Multi-region FSI DR architecture design

**What the answer MUST contain:**
- Cluster Linking as the preferred replication mechanism
- RPO analysis tied to replication lag
- Multi-region topology description

**What the answer MUST NOT contain:**
- Oversimplified one-liner recommendations
- "Just use X" without trade-off reasoning

**Negative-space trigger:** NO
