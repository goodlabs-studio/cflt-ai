---
id: deep-multi-region-design-004
query: "Design a multi-region Kafka architecture with active-active writes and data residency"
expected_route: deep
floor_model: sonnet
tags: [kafka, multi-region, active-active, data-residency, architecture]
required_claims:
  - "active-active"
  - "data residency"
  - "region"
forbidden_claims:
  - "trivial"
  - "just"
---

## Case: Active-active multi-region with data residency

**What the answer MUST contain:**
- Active-active write conflict handling strategy
- Data residency constraints and how to enforce them
- Cluster Linking or equivalent replication topology

**What the answer MUST NOT contain:**
- Dismissive "just do X" guidance without architecture detail

**Negative-space trigger:** NO
