---
title: Kafka Streams Schema Patterns
tags: [kafka-streams, schema-registry, avro, protobuf, json-schema, confluent-agent-skills]
sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/schema-patterns.md]
related: [concepts/schema-registry-best-practices, concepts/schema-evolution-strategies, patterns/schema-registry-shared-types, concepts/avro-schema-source-directory, concepts/kafka-streams-debugging]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/kafka-streams-programming/references/schema-patterns.md
---

# Kafka Streams Schema Patterns

## Summary

Correct schema patterns for Kafka Streams (KS) applications using Avro, Protobuf, or JSON Schema. The non-obvious bits that bite teams in production: Avro source-directory convention (`src/main/avro/`, not `src/main/resources/avro/`); logical types nested inside `type` (the most common mistake); Java type mapping when the Avro plugin generates `Instant` for `timestamp-millis` (compile errors if your code uses `long`); Protobuf gradle plugin requirement; JSON Schema `json.value.type` config to avoid `LinkedHashMap` casts.

Sourced from `confluentinc/agent-skills@91d1871e` (Apache-2.0) — upstream maintains an eval gate at 90%+ pass before merge, so this article is `confidence: high` via source attestation rather than per-claim MCP re-validation. Trip-wire micro-articles in `wiki/concepts/` carry full MCP validation.

## Detail

### Avro

**Schema file location:** The Gradle Avro plugin expects schemas in `src/main/avro/`, NOT `src/main/resources/avro/`. If schemas are in `resources/`, the plugin reports `NO-SOURCE` and silently skips code generation; the build succeeds but no Java classes are produced, breaking compilation downstream. See [Avro Schema Source Directory](avro-schema-source-directory.md) for the canonical convention.

```
src/main/avro/
├── MyInput.avsc
└── MyOutput.avsc
```

**Logical types — correct nesting (most common Avro mistake):** Logical types MUST be nested inside the `type` field as a type definition object:

```json
// CORRECT
{
  "name": "timestamp",
  "type": {"type": "long", "logicalType": "timestamp-millis"}
}

// WRONG — silently ignored or generates Instant instead of long
{
  "name": "timestamp",
  "type": "long",
  "logicalType": "timestamp-millis"
}
```

**All logical type examples:**

```json
// timestamp-millis (ms since epoch)
{"name": "created_at", "type": {"type": "long", "logicalType": "timestamp-millis"}}
// timestamp-micros (μs since epoch)
{"name": "precise_ts", "type": {"type": "long", "logicalType": "timestamp-micros"}}
// date (days since epoch)
{"name": "birth_date", "type": {"type": "int", "logicalType": "date"}}
// time-millis (ms since midnight)
{"name": "start_time", "type": {"type": "int", "logicalType": "time-millis"}}
// decimal (fixed-point)
{"name": "amount", "type": {"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2}}
// uuid
{"name": "id", "type": {"type": "string", "logicalType": "uuid"}}
```

Nullable logical type:

```json
{"name": "deleted_at",
 "type": ["null", {"type": "long", "logicalType": "timestamp-millis"}],
 "default": null}
```

**Java type mapping with logical types (Avro plugin default):**

| Avro logicalType | Generated Java type |
|---|---|
| `timestamp-millis` | `java.time.Instant` |
| `timestamp-micros` | `java.time.Instant` |
| `date` | `java.time.LocalDate` |
| `time-millis` | `java.time.LocalTime` |
| `decimal` | `java.math.BigDecimal` |
| `uuid` | `java.util.UUID` |

**CRITICAL — common compilation error.** Avro 1.12+ with the Gradle Avro plugin generates `Instant` (not `long`) for `timestamp-millis`. All code touching these fields must use `java.time.Instant`. This affects topology aggregations, initializers, producers, and tests.

```java
// WRONG — `incompatible types: long cannot be converted to Instant`
stats.setLastOrderTime(0L);
updated.setTimestamp(Math.max(a.getTimestamp(), b.getTimestamp()));
order.setTimestamp(Instant.now().toEpochMilli());
event.setTimestamp(1000L);

// CORRECT
stats.setLastOrderTime(Instant.EPOCH);
updated.setTimestamp(a.getTimestamp().isAfter(b.getTimestamp()) ? a.getTimestamp() : b.getTimestamp());
order.setTimestamp(Instant.now());
event.setTimestamp(Instant.ofEpochMilli(1000L));
```

Same pattern for all logical types: `LocalDate` for `date`, `BigDecimal` for `decimal`, etc.

**Schema evolution defaults:** All optional fields should have defaults: `""` for strings, `0` for numbers, `false` for booleans, `null` for nullable unions. Enums should have a `default` (the first symbol) for forward compatibility.

```json
{
  "type": "record",
  "name": "Transaction",
  "namespace": "com.example",
  "fields": [
    {"name": "account_id", "type": "string"},
    {"name": "amount", "type": "double", "default": 0.0},
    {"name": "type", "type": {"type": "enum", "name": "TxnType",
      "symbols": ["CREDIT", "DEBIT"], "default": "CREDIT"}},
    {"name": "timestamp",
     "type": {"type": "long", "logicalType": "timestamp-millis"}, "default": 0}
  ]
}
```

For output schemas consumed by downstream apps: always use `BACKWARD` compatibility (new schema can read old data). This is the Schema Registry default per [Schema Registry Best Practices](schema-registry-best-practices.md).

### Protobuf

**Schema file location:**

```
src/main/proto/
├── my_input.proto
└── my_output.proto
```

**Gradle plugin requirement:** The `com.google.protobuf` Gradle plugin is required to compile `.proto` files into Java classes. Without it, proto files sit uncompiled and topology code fails with missing class errors (same failure mode as the Avro directory bug).

```groovy
plugins {
    id 'com.google.protobuf' version '0.9.4'
}

protobuf {
    protoc {
        artifact = 'com.google.protobuf:protoc:4.31.1'
    }
}

dependencies {
    implementation 'io.confluent:kafka-streams-protobuf-serde:8.2.0'
    implementation 'com.google.protobuf:protobuf-java:4.31.1'
}
```

**Example schema:**

```protobuf
syntax = "proto3";
package com.example;

option java_package = "com.example.proto";
option java_outer_classname = "TransactionProtos";

import "google/protobuf/timestamp.proto";

message Transaction {
  string account_id = 1;
  double amount = 2;
  TxnType type = 3;
  google.protobuf.Timestamp timestamp = 4;
}

enum TxnType {
  CREDIT = 0;
  DEBIT = 1;
}
```

Use `option java_package` and `option java_outer_classname` to control the generated Java location and name.

**Timestamps:** Use `google.protobuf.Timestamp` — it handles seconds + nanos. Import `google/protobuf/timestamp.proto`.

```java
import com.google.protobuf.Timestamp;
Timestamp ts = Timestamp.newBuilder()
    .setSeconds(System.currentTimeMillis() / 1000)
    .setNanos(0)
    .build();
```

**Serde configuration:** For `KafkaProtobufSerde`, the deserializer returns `DynamicMessage` by default. To get typed messages, set `specific.protobuf.value.type`:

```java
Map<String, Object> serdeConfig = new HashMap<>();
serdeConfig.put("schema.registry.url", srUrl);
serdeConfig.put("specific.protobuf.value.type", Transaction.class.getName());
KafkaProtobufSerde<Transaction> serde = new KafkaProtobufSerde<>();
serde.configure(serdeConfig, false);
```

Analogous to JSON Schema's `json.value.type` — without it, you get `DynamicMessage` instead of your generated class.

**Schema evolution:** Proto3 fields are optional by default and have zero-value defaults. New fields with new numbers are backward compatible. **Never reuse field numbers** — mark removed fields as `reserved`.

### JSON Schema

**No code generation** — define POJOs manually with Jackson annotations.

```
src/main/java/com/example/<appname>/model/
├── Transaction.java
└── AccountSummary.java
```

POJOs need: (1) a no-arg constructor (Jackson requirement), (2) getters and setters, (3) `@JsonProperty` for names that differ from Java convention.

```java
import com.fasterxml.jackson.annotation.JsonProperty;

public class Transaction {
    @JsonProperty("account_id")
    private String accountId;
    private double amount;
    private String type;
    private long timestamp;

    // No-arg constructor REQUIRED for Jackson deserialization
    public Transaction() {}

    public Transaction(String accountId, double amount, String type, long timestamp) {
        this.accountId = accountId;
        this.amount = amount;
        this.type = type;
        this.timestamp = timestamp;
    }

    public String getAccountId() { return accountId; }
    public void setAccountId(String accountId) { this.accountId = accountId; }
    public double getAmount() { return amount; }
    public void setAmount(double amount) { this.amount = amount; }
    public String getType() { return type; }
    public void setType(String type) { this.type = type; }
    public long getTimestamp() { return timestamp; }
    public void setTimestamp(long timestamp) { this.timestamp = timestamp; }
}
```

**Critical — always set `json.value.type`.** Without it, the serde deserializes to `LinkedHashMap` instead of your POJO, causing `ClassCastException` at runtime. This affects BOTH explicit serde instances AND the default value serde.

```java
Map<String, Object> serdeConfig = new HashMap<>(baseConfig);
serdeConfig.put("json.value.type", Transaction.class.getName());
KafkaJsonSchemaSerde<Transaction> serde = new KafkaJsonSchemaSerde<>();
serde.configure(serdeConfig, false);
```

**Default value serde gotcha:** When `default.value.serde=KafkaJsonSchemaSerde`, internal topics (changelog, repartition) use it. But `json.value.type` can only be set to one class globally. If your topology has multiple value types (input: `Transaction`, output: `AccountSummary`), the default can only handle one.

Solution: set the default to the type used in state stores (the aggregation output), and use explicit serdes for everything else:

```java
// application.properties:
// default.value.serde=io.confluent.kafka.streams.serdes.json.KafkaJsonSchemaSerde
// json.value.type=com.example.model.AccountSummary   <-- changelog type

// Topology code: explicit serde for input
KafkaJsonSchemaSerde<Transaction> txnSerde = new KafkaJsonSchemaSerde<>();
txnSerde.configure(Map.of(
    "schema.registry.url", srUrl,
    "json.value.type", Transaction.class.getName()
), false);

KStream<String, Transaction> input = builder.stream(
    "transactions",
    Consumed.with(Serdes.String(), txnSerde));
```

## Related

- [Schema Registry Best Practices](schema-registry-best-practices.md) — operational surface (TopicNameStrategy, compatibility-per-subject, register-in-CI)
- [Schema Evolution Strategies](schema-evolution-strategies.md) — tier-based compatibility, evolution runbook
- [Schema Registry Shared-Types Library](../patterns/schema-registry-shared-types.md) — versioned shared types via schema references
- [Avro Schema Source Directory](avro-schema-source-directory.md) — `src/main/avro/` plugin convention (trip-wire)
- [Kafka Streams Debugging](kafka-streams-debugging.md) — deserialization errors, schema-incompatibility triage

---

*Source: confluentinc/agent-skills@91d1871e · skills/kafka-streams-programming/references/schema-patterns.md · Ingested 2026-05-16 · Apache-2.0*
