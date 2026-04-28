---
id: wiki-only-acks-001
query: "What is the difference between acks=1 and acks=all?"
expected_route: wiki-only
floor_model: haiku
tags: [kafka, producers, durability]
required_claims:
  - "acks=all"
  - "min.insync.replicas"
forbidden_claims:
  - "I don't know"
---

## Case: Producer acks semantics

**What the answer MUST contain:**
- Explanation that `acks=all` requires all ISR replicas to acknowledge
- Reference to `min.insync.replicas` as the controlling parameter

**What the answer MUST NOT contain:**
- Refusal or uncertainty language

**Negative-space trigger:** NO
