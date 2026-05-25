---
id: review-skill-consult-python-avro-020
input_files:
  - tests/golden/review/fixtures/skill-consult-python-avro.md
expected_claims_min: 4
floor_model: sonnet
tags: [python-client, schema-registry, skill-consultation, fsi-overlay, json-schema]
required_report_sections:
  - "## Summary"
  - "## Claim Validation"
  - "## Canon Compliance"
  - "## Recommendations"
required_claims:
  - "developing-kafka-python-client"
  - "Avro"
  - "acks"
forbidden_content:
  - "I don't know"
  - "cannot answer"
expected_verdict_contains:
  - "Corrected"
premise_challenge_expected: false
overlay: null
---

## Case: Skill consultation routes Python producer scaffold to developing-kafka-python-client

**What the review MUST find:**
- Claim `JSONSerializer` is the default serializer choice — expect `Corrected`
  verdict; FSI canon and the FSI overlay row for
  `developing-kafka-python-client` mandate Avro or Protobuf in production
  (JSON Schema only for prototype/debug).
- Claim `acks=1` is appropriate — expect `Corrected` verdict against canon
  `acks=all` for durable workloads.
- Claim `enable.idempotence=false` reduces overhead — expect `Corrected`
  verdict against canon `enable.idempotence=true` always.
- Claim that Schema Registry should be "optional" for `notifications` —
  expect `Corrected` verdict (canon requires SR for any production topic
  with consumers beyond the producer team).
- Skill column populated with `developing-kafka-python-client` for at least
  one claim (priority routing — Python context wins over SR).
- Canon Compliance table reflects the FSI overlay overrides for serialization
  format, acks, idempotence.

**What the review MUST NOT contain:**
- Any statement that JSON Schema is the recommended production default.
- Any statement that `acks=1` is durable.
- Any statement that idempotence is optional in production.

**Negative-space trigger:** NO.

**Priority routing expectation:** `route_claim("AvroProducer with Schema
Registry")` returns `developing-kafka-python-client` (NOT `kafka-schema-registry`)
because Python context wins per `_priority_order` in `tools/skill-routing.json`.
This case exercises that ordering.
