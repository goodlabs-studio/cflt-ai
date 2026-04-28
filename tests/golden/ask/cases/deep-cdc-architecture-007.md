---
id: deep-cdc-architecture-007
query: "Design a CDC pipeline from Oracle to Confluent Cloud with schema evolution and exactly-once"
expected_route: deep
floor_model: sonnet
tags: [cdc, oracle, confluent-cloud, schema-evolution, exactly-once, architecture]
required_claims:
  - "CDC"
  - "Oracle"
  - "schema evolution"
  - "exactly-once"
forbidden_claims:
  - "simple"
  - "trivial"
---

## Case: Oracle CDC to Confluent Cloud with EOS

**What the answer MUST contain:**
- Connector selection (Debezium or Oracle CDC source connector)
- Schema evolution strategy with Schema Registry
- Exactly-once delivery considerations at each layer

**What the answer MUST NOT contain:**
- Dismissal of complexity in this integration

**Negative-space trigger:** NO
