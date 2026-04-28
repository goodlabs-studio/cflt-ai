---
id: wiki-only-batching-011
query: "How do batch.size and linger.ms interact in Kafka producer batching?"
expected_route: wiki-only
floor_model: haiku
tags: [kafka, producers, performance, batching]
required_claims:
  - "batch.size"
  - "linger.ms"
forbidden_claims:
  - "cannot explain"
---

## Case: Producer batching configuration

**What the answer MUST contain:**
- batch.size as the size trigger for flushing a batch
- linger.ms as the time trigger before sending an incomplete batch

**What the answer MUST NOT contain:**
- Inability to explain the interaction

**Negative-space trigger:** NO
