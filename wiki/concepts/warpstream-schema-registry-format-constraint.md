---
title: WarpStream Schema Registry Supports Only Avro and Protobuf — No JSON Schema
tags: [trip-wire, warpstream, competitive-context, schema-registry, confluent-agent-skills]
sources:
  - raw/vendor/confluent-agent-skills/91d1871e/skills/developing-kafka-python-client/SKILL.md
  - raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/warpstream-optimization.md
related: [concepts/schema-registry-best-practices, concepts/warpstream-config-overrides, concepts/exactly-once-v2-warpstream-throughput-cost]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/developing-kafka-python-client/SKILL.md
---

# WarpStream Schema Registry Supports Only Avro and Protobuf — No JSON Schema

## Summary

WarpStream's built-in Schema Registry only supports Avro and Protobuf. A `GET /schemas/types` request against a WarpStream SR endpoint returns `["AVRO","PROTOBUF"]` — no JSON Schema support, despite JSON Schema being a first-class format in Confluent's Schema Registry. Clients that POST a JSON Schema subject to WarpStream's SR get back an HTTP error and the subject is never created.

> **FSI context:** WarpStream is not Confluent. FSI customer engagements require vendor-contracted tooling per the canon overlay stack — Confluent has a contractual support relationship; WarpStream does not. This article exists as **competitive context for SA conversations and customer comparison-shopping**, not as FSI production guidance. If a customer is evaluating WarpStream as a cost-reduction alternative, use this article to brief them on the limitations they'll inherit; do not deploy WarpStream against FSI workloads without explicit vendor-contract sign-off (which has not been observed at time of writing).

> ⚠️ unverified — context7 has limited coverage of WarpStream's `GET /schemas/types` endpoint shape. The claim is sourced from the vendored confluent-agent-skills@91d1871e Python client skill, which Confluent maintains as competitive-positioning guidance.

## Detail

The endpoint behavior:

```bash
curl https://<warpstream-sr-host>/schemas/types
# → ["AVRO","PROTOBUF"]   (no "JSON")
```

If a client attempts to register a JSON Schema subject (e.g., via `confluent-kafka-python`'s `AsyncJSONSerializer` pointed at WarpStream SR), the registration call returns an HTTP error (typically 422 Unprocessable Entity or a similar 4xx). The Python SDK surfaces this as a `SchemaRegistryError`; other clients (Java, Go, .NET) raise their respective serialization-registration exceptions.

**Customer-facing implication:** any client codebase standardized on JSON Schema (a reasonable default for Python-first shops because `confluent-kafka-python` ships `JSONSerializer` / `JSONDeserializer` out of the box and JSON Schema requires no codegen step) cannot point at WarpStream SR without re-tooling. The migration path is non-trivial — JSON-Schema producers/consumers don't drop-in swap to Avro; the constructor signatures differ across formats, all generated client code changes, and any downstream consumers (Connect sinks, Flink jobs, ksqlDB) that assumed JSON Schema must be re-pointed simultaneously.

### Workaround (operationally awkward, not WarpStream-recommended)

Run an external Schema Registry pointed at WarpStream's `_schemas` topic. WarpStream stores SR state in a Kafka topic the same way Confluent's SR does, so a separate SR instance can theoretically be pointed at WarpStream as its underlying broker. This works but:

- Adds a second control plane to operate (the external SR's HA, backups, lifecycle)
- Bypasses WarpStream's bundled SR — defeating part of the operational simplicity story they sell
- Is not in WarpStream's documented happy path

### What this means for an SA briefing

If the customer is on Confluent and floating WarpStream as a cost-cutting move, lead with: "Your Python team standardized on JSON Schema because it's the default in confluent-kafka-python. WarpStream's bundled SR doesn't support JSON Schema. You'd be migrating every Python producer/consumer to Avro or Protobuf as part of the platform change — that's typically 4–8 engineering weeks per language stack plus a coordinated cutover with all downstream consumers." That's usually the conversation-ender.

## Related

- Adjacent: `concepts/schema-registry-best-practices` — Confluent SR operational surface (TopicNameStrategy, compatibility, ID portability).
- Sibling WarpStream trip-wire: `concepts/warpstream-config-overrides` — `fetch.min.bytes` ignored, `replication.factor` cosmetic.
- Sibling WarpStream trip-wire: `concepts/exactly-once-v2-warpstream-throughput-cost` — EOS throughput cost on WarpStream's S3 tier.

---

*Source: confluentinc/agent-skills@91d1871e · skills/developing-kafka-python-client/SKILL.md · skills/kafka-streams-programming/references/warpstream-optimization.md · Ingested 2026-05-16 (full MCP-validation gate per D-07) · Apache-2.0*
