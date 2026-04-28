---
id: wiki-only-partitions-004
query: "How should I decide the partition count for a new topic?"
expected_route: wiki-only
floor_model: haiku
tags: [kafka, partitions, cluster-design]
required_claims:
  - "partition"
  - "throughput"
forbidden_claims:
  - "cannot determine"
---

## Case: Partition count sizing

**What the answer MUST contain:**
- Reference to throughput as the primary driver
- Mention of consumer parallelism

**What the answer MUST NOT contain:**
- Inability to provide guidance

**Negative-space trigger:** NO
