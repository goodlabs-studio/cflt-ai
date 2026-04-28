---
id: wiki-only-consumer-groups-005
query: "What is the relationship between consumer groups and partitions?"
expected_route: wiki-only
floor_model: haiku
tags: [kafka, consumers, partitions]
required_claims:
  - "consumer group"
  - "partition"
forbidden_claims:
  - "unknown"
---

## Case: Consumer groups and partition assignment

**What the answer MUST contain:**
- Each partition assigned to at most one consumer per group
- Parallelism is bounded by partition count

**What the answer MUST NOT contain:**
- Vague or non-answers

**Negative-space trigger:** NO
