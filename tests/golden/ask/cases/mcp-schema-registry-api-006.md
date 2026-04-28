---
id: mcp-schema-registry-api-006
query: "What is the API endpoint to check schema compatibility in Confluent Cloud Schema Registry?"
expected_route: wiki+mcp
floor_model: sonnet
tags: [schema-registry, api, confluent-cloud]
required_claims:
  - "compatibility"
  - "/subjects/"
forbidden_claims:
  - "I don't know the API"
---

## Case: Schema Registry compatibility check API

**What the answer MUST contain:**
- The /subjects/{subject}/versions endpoint pattern
- Compatibility test endpoint reference

**What the answer MUST NOT contain:**
- Admissions of not knowing the Schema Registry API

**Negative-space trigger:** NO
