---
title: Dead Letter Queue Design
tags: [kafka patterns error-handling connect spring-kafka streams]
sources: []
related: [concepts/exactly-once-semantics, concepts/consumer-group-rebalancing, patterns/fsi-exactly-once, patterns/topic-naming, concepts/consumer-lag-monitoring]
confidence: medium
last_updated: 2026-04-11
last_validated: 2026-04-28
---

# Dead Letter Queue Design

## Summary

A Dead Letter Queue (DLQ) is a dedicated Kafka topic where messages that cannot be successfully processed are routed, preserving the original payload with error context metadata for later diagnosis and replay. Kafka has no native DLQ primitive -- every DLQ implementation is application-level (manual consumer code, Kafka Streams exception handlers) or framework-level (Kafka Connect's built-in DLQ, Spring Kafka's `DeadLetterPublishingRecoverer`). The core trade-off is between pipeline continuity (skip failures, keep processing) and data completeness (no message silently dropped), with pattern complexity scaling from a simple single-topic DLQ to multi-level non-blocking retry topologies.

## Pattern

### Architecture Variants

Four DLQ patterns exist, each adding capability at the cost of operational complexity:

| Pattern | Topology | Retry Behavior | Best For |
|---------|----------|----------------|----------|
| Simple DLQ | `source -> consumer -> dlq` | None -- immediate route on first failure | Low-volume, non-retriable errors (schema violations) |
| Retry + DLQ | `source -> consumer (N retries) -> dlq` | In-process blocking retries with backoff | Simple apps with occasional transient failures |
| Multi-Level DLQ | `source -> retry-1 -> retry-2 -> ... -> dlq` | Non-blocking via separate retry topics | High-throughput systems (Uber pattern) |
| Error Categorization | Classify exception, then route | Retriable -> retry topics; non-retriable -> DLQ | Production systems requiring efficient failure routing |

#### Simple DLQ

```
source-topic --> consumer --> [failure] --> dlq-topic
                    |
                    +--> [success] --> downstream
```

Failed messages go directly to a single DLQ topic with no retries. Appropriate when failures are rare and expected to be permanent (corrupt payloads, schema violations). Trade-off: conflates transient and permanent failures in the same topic.

#### Retry + DLQ

```
source-topic --> consumer --> [failure, attempt < N] --> in-process retry with backoff
                    |                                         |
                    |         [failure, attempt >= N] --------+--> dlq-topic
                    +--> [success] --> downstream
```

Consumer retries N times (typically 3-5) with exponential backoff before routing to DLQ. Drawback: **blocking retries** prevent the consumer from processing subsequent messages on that partition during backoff, creating head-of-line blocking at scale.

#### Multi-Level DLQ (Non-Blocking Retry Topics)

```
source-topic --> consumer-1 --> [failure] --> retry-1 (1s delay)
                                                  |
                                             consumer-2 --> [failure] --> retry-2 (10s delay)
                                                                              |
                                                                         consumer-3 --> [failure] --> retry-3 (60s delay)
                                                                                                          |
                                                                                                     consumer-4 --> [failure] --> dlq-topic
```

Each retry level is a separate Kafka topic with its own consumer group. Delay is enforced by the retry-level consumer checking a "not-before" timestamp header and pausing partition consumption until the delay elapses. The main consumer continues processing immediately -- no head-of-line blocking. This is the [Uber Engineering pattern](https://www.uber.com/us/en/blog/reliable-reprocessing/) and the recommended approach for high-throughput systems.

Spring Kafka's `@RetryableTopic` automates this pattern, creating topics like `orders.placed-retry-1000`, `orders.placed-retry-2000`, `orders.placed-dlt`.

#### Error Categorization

```
source-topic --> consumer --> classify(exception)
                                  |
                    [retriable] --+--> retry-topic (with backoff)
                                  |
                    [non-retriable] --> dlq-topic (immediate)
```

The consumer classifies exceptions before routing:

| Category | Exception Types | Action |
|----------|----------------|--------|
| Retriable (transient) | `ConnectException`, `TimeoutException`, `RetriableException`, HTTP 5xx | Route to retry topics with backoff |
| Non-retriable (poison pill) | `SerializationException`, `DeserializationException`, `JsonParseException`, validation failures | Route directly to DLQ, skip retries |

This is the recommended production approach. Retrying a deserialization error is wasted effort; routing a transient timeout directly to DLQ loses recoverable messages.

### Kafka Connect DLQ

Kafka Connect has built-in DLQ support via [KIP-298](https://cwiki.apache.org/confluence/display/KAFKA/KIP-298:+Error+Handling+in+Connect). This applies to **sink connectors only** -- source connector errors are handled at the task level (no per-record DLQ).

#### Configuration Reference

| Property | Default | Description |
|----------|---------|-------------|
| `errors.tolerance` | `none` | `none` = fail immediately; `all` = skip errors and continue. **Must be `all` to enable DLQ.** |
| `errors.deadletterqueue.topic.name` | `""` (empty) | Target topic for failed records. If empty with `errors.tolerance=all`, failed records are **silently dropped**. |
| `errors.deadletterqueue.topic.replication.factor` | `3` | Replication factor for auto-created DLQ topic. |
| `errors.deadletterqueue.context.headers.enable` | `false` | Adds error context headers to DLQ records. **Should always be `true` in production.** |
| `errors.retry.timeout` | `0` | Total time in ms for retries. `0` = no retries. `-1` = infinite retries. |
| `errors.retry.delay.max.ms` | `60000` | Maximum delay between retry attempts. Exponential backoff with jitter. |
| `errors.log.enable` | `false` | Log failed records. |
| `errors.log.include.messages` | `false` | Include record content in logs. **Caution: may log PII.** |

> `errors.retry.timeout` default is documented inconsistently across sources. Apache Kafka source code defines the default as `0` (no retries). Treat `0` as canonical.

#### Recommended Production Configuration

```properties
# Enable error tolerance -- required to activate DLQ
errors.tolerance=all

# DLQ topic -- use dlq.<connector-name> convention
errors.deadletterqueue.topic.name=dlq.jdbc-sink-orders
errors.deadletterqueue.topic.replication.factor=3

# Context headers -- always enable; without these you see failures but cannot diagnose them
errors.deadletterqueue.context.headers.enable=true

# Retry -- 5 minutes total with up to 60s between attempts
errors.retry.timeout=300000
errors.retry.delay.max.ms=60000

# Logging -- enable but do not log message content in production
errors.log.enable=true
errors.log.include.messages=false
```

#### Connect DLQ Context Headers

When `errors.deadletterqueue.context.headers.enable=true`, these headers are added:

| Header | Content |
|--------|---------|
| `__connect.errors.topic` | Original source topic |
| `__connect.errors.partition` | Original partition number |
| `__connect.errors.offset` | Original offset |
| `__connect.errors.connector.name` | Connector name |
| `__connect.errors.task.id` | Task ID that failed |
| `__connect.errors.stage` | Processing stage (`VALUE_CONVERTER`, `TRANSFORMATION`, `SINK_PUT`) |
| `__connect.errors.class.name` | Component class that failed |
| `__connect.errors.exception.class.name` | Exception class |
| `__connect.errors.exception.message` | Exception message |
| `__connect.errors.exception.stacktrace` | Full stack trace |

### Spring Kafka DLQ

#### Blocking Retries with `DefaultErrorHandler`

```java
@Bean
public DefaultErrorHandler errorHandler(KafkaTemplate<Object, Object> template) {
    DeadLetterPublishingRecoverer recoverer =
        new DeadLetterPublishingRecoverer(template,
            (record, ex) -> new TopicPartition(
                record.topic() + ".DLT", record.partition()));

    DefaultErrorHandler handler = new DefaultErrorHandler(
        recoverer,
        new FixedBackOff(1000L, 3L));  // 1s interval, 3 attempts

    // Non-retriable exceptions skip retries, go directly to DLT
    handler.addNotRetryableExceptions(
        DeserializationException.class,
        JsonParseException.class);

    return handler;
}
```

`DeadLetterPublishingRecoverer` automatically adds headers: `KafkaHeaders.DLT_ORIGINAL_TOPIC`, `DLT_ORIGINAL_PARTITION`, `DLT_ORIGINAL_OFFSET`, `DLT_ORIGINAL_TIMESTAMP`, `DLT_EXCEPTION_FQCN`, `DLT_EXCEPTION_MESSAGE`, `DLT_EXCEPTION_STACKTRACE`.

Default DLT topic naming: `<ORIGINAL_TOPIC>.DLT`.

#### Non-Blocking Retries with `@RetryableTopic`

```java
@RetryableTopic(
    attempts = "4",
    backoff = @Backoff(delay = 1000, multiplier = 2, maxDelay = 8000),
    include = {TransientException.class},
    exclude = {DeserializationException.class},
    dltStrategy = DltStrategy.FAIL_ON_ERROR,
    autoCreateTopics = "true"
)
@KafkaListener(topics = "orders.placed")
public void listen(ConsumerRecord<String, String> record) {
    processOrder(record);
}
```

Creates topics: `orders.placed-retry-1000`, `orders.placed-retry-2000`, `orders.placed-retry-4000`, `orders.placed-dlt`.

`DltStrategy` options:

| Strategy | Behavior |
|----------|----------|
| `ALWAYS_RETRY_ON_ERROR` | Retry DLT processing failures (default) |
| `FAIL_ON_ERROR` | Fail on DLT processing error |
| `NO_DLT` | No DLT topic; after retries exhausted, processing ends |

### Kafka Streams DLQ

Kafka Streams has no built-in DLQ mechanism. Three exception handler interfaces exist:

**`DeserializationExceptionHandler`** (read path, config: `default.deserialization.exception.handler`):

- `LogAndFailExceptionHandler` -- logs and stops the application. **This is the default.**
- `LogAndContinueExceptionHandler` -- logs and skips the record.
- Custom handler for DLQ routing:

```java
public class DlqDeserializationHandler implements DeserializationExceptionHandler {
    private KafkaProducer<byte[], byte[]> dlqProducer;
    private String dlqTopic;

    @Override
    public void configure(Map<String, ?> configs) {
        this.dlqProducer = (KafkaProducer<byte[], byte[]>) configs.get("dlq.producer");
        this.dlqTopic = (String) configs.get("dlq.topic");
    }

    @Override
    public DeserializationHandlerResponse handle(ProcessorContext context,
            ConsumerRecord<byte[], byte[]> record, Exception exception) {
        ProducerRecord<byte[], byte[]> dlqRecord =
            new ProducerRecord<>(dlqTopic, record.key(), record.value());
        dlqRecord.headers()
            .add("x-error-class", exception.getClass().getName().getBytes());
        dlqProducer.send(dlqRecord);
        return DeserializationHandlerResponse.CONTINUE;
    }
}
```

**`ProductionExceptionHandler`** (write path, config: `default.production.exception.handler`):
- Handles failures when Streams produces output records (serialization errors, broker write failures).
- Default: `DefaultProductionExceptionHandler` returns `FAIL`.
- Custom implementations can return `CONTINUE` to skip or route to DLQ.

**`ProcessingExceptionHandler`** (KIP-1033, Kafka 3.9+):
- Handles exceptions during record processing logic, filling the gap where processing errors previously required try/catch in processor code.
- Verify availability in your target Kafka version before relying on this.

### DLQ Topic Design

#### Naming Conventions

| Convention | Example | When to Use |
|-----------|---------|-------------|
| `<original-topic>.dlq` | `orders.placed.dlq` | Consumer applications -- maintains topic lineage |
| `<application>.errors` | `payment-service.errors` | Single app consuming multiple topics |
| `dlq.<connector-name>` | `dlq.jdbc-sink-orders` | Kafka Connect -- groups by connector identity |

See [Topic Naming](topic-naming.md) for broader naming conventions.

#### DLQ Record Headers

Every DLQ record should carry these headers:

| Header | Purpose |
|--------|---------|
| `x-original-topic` | Source topic for replay targeting |
| `x-original-partition` | Partition number |
| `x-original-offset` | Exact identification |
| `x-original-timestamp` | Original event time |
| `x-error-class` | Exception class for categorization |
| `x-error-message` | Human-readable error description |
| `x-error-stacktrace` | Full stack trace (optional -- large but invaluable) |
| `x-retry-count` | Retries attempted before DLQ |
| `x-first-failure-timestamp` | When first failure occurred (SLA tracking) |
| `x-application-id` | Consumer group or application that failed |

#### Schema Strategy: Headers vs. Envelope

Two approaches for DLQ record structure:

**Headers-based (recommended)**: Original key/value preserved verbatim as the DLQ record body; error metadata in headers. This is what Kafka Connect and Spring Kafka use. Simplifies replay -- re-produce the DLQ record's key and value to the original topic directly.

**Envelope schema**: Wrap original message in a structured envelope with error metadata fields. Adds complexity and makes replay harder (must unwrap). Only use when headers are insufficient (e.g., tooling that cannot read headers).

#### Retention Policy

- DLQ retention should be **longer than source topic retention**. If source is 7 days, set DLQ to 30-90 days.
- Rationale: operators need time to discover, diagnose, fix root cause, and replay. Messages must not age out before investigation.
- Use `cleanup.policy=delete` (not compact) -- you want the full history of failures, not just the latest per key.

### Reprocessing Strategies

#### Manual Replay

After fixing the root cause, re-produce DLQ messages to the original topic. Build a replay utility that:

1. Reads from the DLQ topic
2. Filters by error class, time range, or original topic
3. Re-produces to the original topic preserving key and original headers
4. Tracks replay status (which DLQ offsets have been replayed)

#### Automated Replay with Circuit Breaker

For DLQ topics containing primarily transient failures:

```
dlq-topic --> replay-consumer --> [attempt processing]
                                      |
                [success] --> commit offset
                                      |
                [failure] --> circuit breaker check
                    [open] ----> pause replay, alert
                    [closed] --> retry with backoff
```

Key considerations:
- Circuit breaker opens after N consecutive failures (e.g., 10). When open, stop replaying and alert on-call.
- **Rate-limit replay**: after an outage that accumulated 100K messages, replaying at full speed overwhelms downstream. Cap at a sustainable rate (e.g., 100 msg/s).

#### Selective Replay

Not all DLQ messages should be replayed. Filter by:
- `x-error-class`: only replay `TimeoutException`, skip `DeserializationException`
- Time window: only replay messages from the outage period
- Key or partition: only replay messages for a specific customer or shard

### Monitoring

| Metric | Signal | Alert Threshold |
|--------|--------|-----------------|
| DLQ message rate (msgs/sec) | Error rate proxy | > 5% of main topic throughput |
| DLQ consumer lag | Replay processing backlog | Growing lag |
| DLQ topic size (total messages) | Unresolved failures | > threshold (e.g., 1000) |
| DLQ message age (oldest unprocessed) | Time-to-resolution SLA | > 24 hours |
| Error type distribution | Systemic vs. isolated | Single error class > 80% of volume |
| Replay success rate | Fix effectiveness | < 80% after fix deployed |

Alerting heuristics:
- DLQ rate > 5% of main topic = systemic issue (downstream outage, not poison pills)
- Messages older than 24 hours = retention violation risk, needs operator attention
- Single error class dominating = single root cause, fix that one thing
- Replay success < 80% = fix is incomplete, stop replay and investigate

See [Consumer Lag Monitoring](../concepts/consumer-lag-monitoring.md) for general lag monitoring patterns.

## When to Use

- **Poison pill mitigation**: a malformed or schema-incompatible message blocks the consumer indefinitely without a DLQ -- the consumer cannot commit past it
- **Transient failure isolation**: downstream dependency outages (database down, HTTP 503) should not block the entire partition or discard the message
- **Pipeline continuity**: decouple failure handling from the main processing path; the consumer commits and continues, failed messages land in the DLQ for later investigation
- **Regulatory environments (FSI)**: exactly-once processing pipelines need a defined path for messages that cannot be processed, with full audit trail of what failed and why
- **Kafka Connect sink connectors**: any connector processing external data (JDBC, Elasticsearch, S3) where individual records can fail independently
- **High-throughput systems**: multi-level retry topology (Uber pattern) when blocking retries create unacceptable head-of-line blocking

## Caveats

- **Kafka has no native DLQ**: every DLQ is an application/framework convention. There is no broker-level guarantee that DLQ routing is atomic with offset commit unless you use transactions.
- **Kafka Connect DLQ is sink-only**: source connector errors fail the task; there is no per-record DLQ for source connectors.
- **Silent message loss**: setting `errors.tolerance=all` without `errors.deadletterqueue.topic.name` silently drops failed records. Always configure both together.
- **DLQ ordering**: messages in the DLQ topic are ordered by failure time, not by original event time. Replay may reorder relative to the original stream.
- **Blocking retries block partitions**: in-process retry with backoff (Pattern B, `DefaultErrorHandler`) prevents processing of subsequent messages on that partition. At scale, use non-blocking retry topics instead.
- **DLQ is not a substitute for fixing root causes**: a growing DLQ indicates a systemic problem. Monitor and alert; do not treat DLQ as a permanent parking lot.
- **Schema considerations**: DLQ records may not conform to the source topic's schema (the whole point is they failed processing). Use `bytes` or raw format for DLQ topics, not the source schema.
- **Exactly-once and DLQ**: the DLQ producer should be a separate `KafkaProducer` instance from any transactional producer to avoid coupling DLQ writes to processing transactions. Commit offsets after the DLQ produce succeeds.
- **`errors.retry.timeout` inconsistency**: documented default varies across sources. Apache Kafka source code defines `0` (no retries) as canonical.

## Related

- [Exactly-Once Semantics](../concepts/exactly-once-semantics.md) -- DLQ interaction with transactional producers and idempotent delivery
- [Consumer Group Rebalancing](../concepts/consumer-group-rebalancing.md) -- rebalance behavior during blocking retry backoff periods
- [FSI Exactly-Once](fsi-exactly-once.md) -- regulatory requirements for failure handling in financial services pipelines
- [Topic Naming](topic-naming.md) -- naming conventions applicable to DLQ and retry topics
- [Consumer Lag Monitoring](../concepts/consumer-lag-monitoring.md) -- monitoring DLQ consumer group lag for replay consumers
