---
title: Kafka Streams 4.x StreamsUncaughtExceptionHandler Import Path
tags: [trip-wire, kafka-streams, java, error-handling, confluent-agent-skills]
sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/SKILL.md]
related: [concepts/kafka-streams-debugging, concepts/kafka-streams-production-hardening, concepts/avro-schema-source-directory, concepts/schema-aware-console-producer-required]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/kafka-streams-programming/SKILL.md
---

# Kafka Streams 4.x StreamsUncaughtExceptionHandler Import Path

## Summary

In Kafka Streams 4.x, `StreamsUncaughtExceptionHandler` lives in the `org.apache.kafka.streams.errors` package. It is **NOT** a nested class under `KafkaStreams` (that was the 2.8–3.x shape). Code copy-pasted from older guides — or from AI assistants trained on pre-4.x snippets — fails to compile with `cannot find symbol: class StreamsUncaughtExceptionHandler` or `KafkaStreams.StreamsUncaughtExceptionHandler is not visible`. Validated against confluent-docs via /wiki:ingest Step 3d on 2026-05-16. This trip-wire is encoded as an upstream eval assertion at `skills/kafka-streams-programming/evals/evals.json` — it would fail an upstream merge if violated.

## Detail

The KIP-671 handler moved from `KafkaStreams.StreamsUncaughtExceptionHandler` (nested) to the top-level `org.apache.kafka.streams.errors.StreamsUncaughtExceptionHandler` class during the 4.x refactor. The response enum moved with it: `StreamThreadExceptionResponse` is now a nested class under `StreamsUncaughtExceptionHandler` itself, not under `KafkaStreams`.

**Failure mode:** an engineer (human or AI) copies a snippet from an older Kafka Streams tutorial or stack-overflow post and runs `mvn compile`. The build fails immediately at the import statement. Less obviously, an editor's auto-complete may resolve `StreamsUncaughtExceptionHandler` to a stale fully-qualified name (caching a pre-4.x JAR), masking the issue until a clean build.

### Correct imports and handler shape (KS 4.x)

```java
import org.apache.kafka.streams.errors.StreamsUncaughtExceptionHandler;
import org.apache.kafka.streams.errors.StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse;

streams.setUncaughtExceptionHandler(exception ->
    StreamThreadExceptionResponse.SHUTDOWN_CLIENT);
```

For a MaxFailures-style handler (the upstream skill's canonical production pattern), see the implementation example in `concepts/kafka-streams-production-hardening` § Layer 4.

### Wrong (pre-4.x) — will not compile against 4.x

```java
// DON'T — nested-class form was removed in 4.x
streams.setUncaughtExceptionHandler(new KafkaStreams.StreamsUncaughtExceptionHandler() { ... });
```

### Detection

Add a smoke-test compile in CI that imports `StreamsUncaughtExceptionHandler` from the canonical package; any drift surfaces immediately:

```java
import org.apache.kafka.streams.errors.StreamsUncaughtExceptionHandler;  // must resolve
```

## Related

- Parent: `concepts/kafka-streams-debugging` — the broader symptom-organized diagnostics catalogue that includes thread-failure debugging.
- Parent: `concepts/kafka-streams-production-hardening` — the four-tier error-handling pattern (Layer 4 is this handler).
- Sibling KS-programming trip-wire: `concepts/avro-schema-source-directory` — companion compile-time gotcha.
- Sibling KS-programming trip-wire: `concepts/schema-aware-console-producer-required` — runtime SR verification gotcha.

---

*Source: confluentinc/agent-skills@91d1871e · skills/kafka-streams-programming/SKILL.md · Ingested 2026-05-16 (full MCP-validation gate per D-07) · Apache-2.0*
