---
id: wiki-only-eos-008
query: "How does exactly-once semantics work in Kafka?"
expected_route: wiki-only
floor_model: haiku
tags: [kafka, exactly-once, transactions]
required_claims:
  - "idempotence"
  - "transactional"
forbidden_claims:
  - "impossible"
---

## Case: Exactly-once semantics overview

**What the answer MUST contain:**
- Idempotent producers (enable.idempotence=true)
- Transactional two-phase commit mechanism

**What the answer MUST NOT contain:**
- Claims that EOS is impossible in Kafka

**Negative-space trigger:** NO
