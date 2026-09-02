---
title: ShadowTraffic — Schema-Driven Data Generation for Confluent Cloud
tags: [shadowtraffic, data-generation, avro, schema-registry, testing, kafka, confluent-cloud]
sources: [https://docs.shadowtraffic.io/overview/, https://docs.shadowtraffic.io/quickstart/, https://docs.shadowtraffic.io/connections/kafka/, https://docs.shadowtraffic.io/generator-configuration/avroSchemaHint/, https://docs.shadowtraffic.io/generator-configuration/schemaRegistrySubject/, https://docs.shadowtraffic.io/generator-configuration/throughput/, https://docs.shadowtraffic.io/generator-configuration/throttleMs/, https://docs.shadowtraffic.io/generator-configuration/maxEvents/, https://docs.shadowtraffic.io/generator-configuration/maxMs/, https://docs.shadowtraffic.io/functions/env/, https://docs.shadowtraffic.io/functions/now/, https://docs.shadowtraffic.io/functions/oneOf/, https://docs.shadowtraffic.io/functions/weightedOneOf/, https://docs.shadowtraffic.io/functions/sequentialString/, https://docs.shadowtraffic.io/functions/loadPropertiesFile/]
related: [concepts/schema-registry-best-practices, concepts/schema-aware-console-producer-required, concepts/confluent-cloud-private-networking, patterns/topic-naming]
confidence: medium
last_updated: 2026-08-24
last_validated: 2026-08-24
---

# ShadowTraffic — Schema-Driven Data Generation for Confluent Cloud

## Summary

ShadowTraffic is a container you run yourself (`shadowtraffic/shadowtraffic`) that produces synthetic records into Kafka (and other backends) from a single JSON config, instead of hand-writing a producer. The config has exactly two moving parts — `generators` (what to make, and how fast) and `connections` (where to send it) — and swapping to a different topic and Avro schema is a matter of editing the generator's field map and its schema-binding block, not rewriting a client. The trade-off: field-to-generator mapping is manual per schema (no schema-to-config autogeneration), and it's a licensed third-party product with no `confluent-docs`/`context7` coverage — this article is sourced directly from ShadowTraffic's own docs, hence `confidence: medium`.

## Pattern

### Config anatomy

```json
{
  "generators": [ /* what to produce */ ],
  "connections": { /* where to send it */ },
  "globalConfigs": { /* optional: settings applied to every generator */ }
}
```

**`generators[]`** — each entry has:
- `topic` (Kafka) — the destination topic
- `connection` — which key under `connections` to use; auto-binds to the only connection if there's just one, otherwise required
- `key` / `value` — object trees mapping field name → a `_gen` function that produces that field's value
- `localConfigs` — schema binding (see below) plus throughput/volume controls, and can override anything set in `globalConfigs`

**`connections{}`** — each named entry has:
- `kind: "kafka"` (also supports Postgres, MySQL, Oracle, S3, Azure Blob Storage, GCS, Redis, Databricks, Pub/Sub, webhooks, and others — the shape below is Kafka-specific)
- `producerConfigs` — the actual client properties: `bootstrap.servers`, `security.protocol`/`sasl.mechanism`/`sasl.jaas.config` for SASL_SSL auth, `schema.registry.url` + `basic.auth.credentials.source`/`basic.auth.user.info` for Schema Registry, and `key.serializer`/`value.serializer`

Keep credentials out of the versioned config entirely by loading `producerConfigs` from an external file instead of inlining it:

```json
"producerConfigs": {
  "_gen": "loadPropertiesFile",
  "file": "/home/config/client.properties",
  "overrides": {
    "key.serializer": "org.apache.kafka.common.serialization.StringSerializer",
    "value.serializer": "io.confluent.kafka.serializers.KafkaAvroSerializer"
  }
}
```
`client.properties` then holds the real `bootstrap.servers`, SASL JAAS config, and SR basic-auth pair — gitignored, filled in per environment, never committed.

### Binding to a schema — the fork that makes this schema-agnostic

Pick one `localConfigs` entry per generator:

1. **`avroSchemaHint`** — define the Avro schema inline. Use when no schema is registered yet, or you want ShadowTraffic to register/validate a new one on first send.
2. **`schemaRegistrySubject`** — reference a schema that's *already* registered, by exact subject name (`{"value": "<exact-subject>"}`). Use this for any existing Confluent Cloud topic. It's **required**, not optional, whenever the subject doesn't follow the default `TopicNameStrategy` naming (`<topic>-value`) — e.g. a `RecordNameStrategy` subject or a hand-registered/legacy name. Confirm the real subject first (`confluent schema-registry schema describe --subject ...`, or the Confluent Cloud UI) — don't assume it matches the topic name.

To point the same config at a **new** schema/topic: (1) confirm the target subject name, (2) rewrite the generator's `value` field map to match the new Avro record's fields, (3) update `schemaRegistrySubject` (or swap in `avroSchemaHint` if the schema doesn't exist yet). The `connections` block, credential file, and run command don't change.

### Mapping Avro fields to generator functions

This is the one manual step per schema — there's no schema-to-generator autogeneration. Get a type wrong and Schema Registry rejects the record at send time (loud failure, not silent):

| Avro field type | Typical `_gen` function(s) |
|---|---|
| `long` (esp. timestamps) | `now` → epoch millis; `uniformDistribution`; `sequentialInteger` |
| `string` | `sequentialString` (templated, e.g. `{"expr": "User_~d"}`); `characterString`; `uuid`; `ulid` |
| `int` | `sequentialInteger`; `uniformDistribution` |
| `double` / `float` | `normalDistribution`; `uniformDistribution` |
| `boolean` | `boolean` |
| `bytes` | `bytes` |
| enum-like string (fixed value set, equal odds) | `oneOf`: `{"choices": ["A", "B", "C"]}` |
| enum-like string (skewed odds) | `weightedOneOf`: `{"choices": [{"weight": 4, "value": "A"}, {"weight": 6, "value": "B"}]}` |
| nested record | a nested object using the same field→`_gen` shape |

### Runtime knobs, not config edits

Drive volume, rate, and credentials from the environment so one config file works unmodified across runs/environments:

| `localConfigs` key | Controls |
|---|---|
| `throughput` | approximate events/sec for this generator |
| `throttleMs` | minimum ms between events (alternative to `throughput`) |
| `maxEvents` | generator goes dormant after this many events |
| `maxMs` | generator stops after this many ms (can also be set in `globalConfigs` to apply to every generator) |
| `maxBytes` | byte-size cap on generated payloads |

Wrap any of these in the `env` preprocessing function to make them runtime flags instead of file edits:
```json
"throughput": { "_gen": "env", "var": "EVENTS_PER_SECOND", "as": "integer", "default": 5 }
```

### Running it

```bash
docker run --rm --env-file license.env \
  -v $(pwd)/config.json:/home/config.json \
  -v $(pwd)/client.properties:/home/config/client.properties \
  shadowtraffic/shadowtraffic:latest \
  --config /home/config.json --sample 10 --stdout   # dry run: prints, sends nothing
```
Drop `--sample`/`--stdout` for a live run that actually produces to the topic. License env vars (`LICENSE_ID`, `LICENSE_EMAIL`, `LICENSE_ORGANIZATION`, `LICENSE_EDITION`, `LICENSE_EXPIRATION`, `LICENSE_SIGNATURE`) load via `--env-file`.

## When to Use

- Need schema-conformant Avro/JSON/Protobuf traffic on a Confluent Cloud (or self-managed) topic without hand-writing a producer.
- Exercising a consumer, ksqlDB/Flink pipeline, or connector against realistic shapes/volumes for a demo, PoC, or load test.
- Standing up a new schema/topic quickly and repeatably — the `connections` block, `loadPropertiesFile` pattern, and run scripts carry over unchanged; only the field map and schema binding change per schema.

## Caveats

- Commercial license required beyond ShadowTraffic's free-tier limits; populate license vars via a gitignored `license.env`, never inline in the config.
- Field mapping is manual per schema — budget one iteration to get every field's `_gen` type right; a mismatch fails at Schema Registry validation, not silently.
- `schemaRegistrySubject` must be the *actual* registered subject name for every new schema — never assume the `TopicNameStrategy` default. See `patterns/topic-naming.md` for the naming-strategy background.
- If the target cluster sits behind PrivateLink or other private networking, the ShadowTraffic container must run from inside that network — see `concepts/confluent-cloud-private-networking.md`. A host with only public internet can't reach the bootstrap endpoint.
- Third-party tool, no `confluent-docs`/`context7` MCP coverage — this article reflects ShadowTraffic's published docs as of 2026-08-24, not a Confluent-validated source.

## Related

- [Schema Registry Best Practices](concepts/schema-registry-best-practices.md) — the governance/operational rules this data conforms to
- [Use Schema-Aware Console Producer for SR-Governed Topics](concepts/schema-aware-console-producer-required.md) — the same wire-format concern from the opposite direction (CLI tools that *don't* speak SR framing; ShadowTraffic's `KafkaAvroSerializer` does)
- [Confluent Cloud Private Networking](concepts/confluent-cloud-private-networking.md) — reachability caveat for PrivateLink-fronted clusters
- [Topic Naming](patterns/topic-naming.md) — the `TopicNameStrategy` default that `schemaRegistrySubject` exists to override
