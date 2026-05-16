---
title: Kafka Streams Production Hardening
tags: [kafka-streams, production, resilience, fsi, confluent-agent-skills]
sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/production-hardening.md]
related: [concepts/exactly-once-semantics, patterns/fsi-exactly-once, patterns/producer-config-fsi, patterns/consumer-config-fsi, concepts/kafka-streams-debugging, concepts/kafka-streams-architecture, concepts/exactly-once-v2-warpstream-throughput-cost, patterns/dead-letter-queue-design]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/kafka-streams-programming/references/production-hardening.md
---

# Kafka Streams Production Hardening

## Summary

Production-readiness checklist for Kafka Streams (KS) applications: the four-tier error-handling model (deserialization, processing, production, uncaught), structured JSON logging, separate liveness/readiness HTTP probes, container Dockerfile with the correct JVM percentages, deployment sizing with persistent volumes for stateful apps, and KIP-1034 DLQ routing. Transforms a working topology into one that survives K8s rollouts, rebalances, and bad input data.

Sourced from `confluentinc/agent-skills@91d1871e` (Apache-2.0) — upstream maintains an eval gate at 90%+ pass before merge, so this article is `confidence: high` via source attestation rather than per-claim MCP re-validation. Trip-wire micro-articles in `wiki/concepts/` carry full MCP validation.

## Detail

### Error handling — four-tier model

Configure all four layers in production. Each catches a different category of failure.

| Layer | Catches | Dev | Prod |
|---|---|---|---|
| Deserialization | Bad input bytes, schema mismatch, missing magic byte | `LogAndContinueExceptionHandler` | DLQ (KIP-1034) |
| Processing (KIP-1034) | Exceptions inside topology lambdas (map, filter, aggregate, joiners) | `LogAndContinueProcessingExceptionHandler` | `DeadLetterQueueExceptionHandler` |
| Production | Failures writing output/changelog (serialization, oversized record, broker down) | Default | Custom `ProductionExceptionHandler` |
| Uncaught (KIP-671) | Anything that kills a stream thread | `REPLACE_THREAD` | MaxFailures pattern |

**MaxFailures pattern (rate-limited thread replacement):** If N failures (default 5) happen within M milliseconds (default 1 min), something is fundamentally broken — shut down the app. Otherwise replace the failed thread and keep processing. Always shut down on `UnsupportedVersionException` (broker version mismatch).

```java
import org.apache.kafka.streams.errors.StreamsUncaughtExceptionHandler;
import org.apache.kafka.streams.errors.StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse;

public class MaxFailuresUncaughtExceptionHandler implements StreamsUncaughtExceptionHandler {
    private final int maxFailures;
    private final long maxTimeIntervalMillis;
    private Instant previousErrorTime;
    private int currentFailureCount;

    public MaxFailuresUncaughtExceptionHandler(int maxFailures, long maxTimeIntervalMillis) {
        this.maxFailures = maxFailures;
        this.maxTimeIntervalMillis = maxTimeIntervalMillis;
    }

    @Override
    public StreamThreadExceptionResponse handle(Throwable throwable) {
        currentFailureCount++;
        Instant now = Instant.now();
        if (previousErrorTime == null) previousErrorTime = now;
        long millisBetweenFailure = Duration.between(previousErrorTime, now).toMillis();
        if (currentFailureCount >= maxFailures) {
            if (millisBetweenFailure <= maxTimeIntervalMillis) {
                return StreamThreadExceptionResponse.SHUTDOWN_APPLICATION;
            }
            currentFailureCount = 0;
            previousErrorTime = null;
        }
        previousErrorTime = now;
        Throwable cause = throwable;
        while (cause.getCause() != null) cause = cause.getCause();
        if (cause instanceof org.apache.kafka.common.errors.UnsupportedVersionException) {
            return StreamThreadExceptionResponse.SHUTDOWN_APPLICATION;
        }
        return StreamThreadExceptionResponse.REPLACE_THREAD;
    }
}
```

The `StreamsUncaughtExceptionHandler` interface lives in `org.apache.kafka.streams.errors` in KS 4.x — see [Kafka Streams 4.x uncaught exception handler import](kafka-streams-4x-uncaught-exception-handler-import.md) for the exact import path (it changed in the 4.x refactor).

**Custom `ProductionExceptionHandler`** typically continues past `RecordTooLargeException` (skip oversized) and fails on serialization errors (those are bugs):

```java
public class SafeProductionExceptionHandler implements ProductionExceptionHandler {
    @Override
    public ProductionExceptionHandlerResponse handle(ErrorHandlerContext ctx,
            ProducerRecord<byte[], byte[]> record, Exception exception) {
        if (exception instanceof RecordTooLargeException) {
            return ProductionExceptionHandlerResponse.CONTINUE;
        }
        return ProductionExceptionHandlerResponse.FAIL;
    }

    @Override
    public ProductionExceptionHandlerResponse handleSerializationException(
            ErrorHandlerContext ctx, ProducerRecord record, Exception exception) {
        return ProductionExceptionHandlerResponse.FAIL;
    }
}
```

### Logging — structured JSON

**Dev:** `slf4j-simple:2.0.16` (console, no config).

**Prod:** Logback + JSON encoder for log aggregation.

```groovy
implementation 'ch.qos.logback:logback-classic:1.5.16'
implementation 'net.logstash.logback:logstash-logback-encoder:8.0'
```

`src/main/resources/logback.xml`:

```xml
<configuration>
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="net.logstash.logback.encoder.LogstashEncoder">
            <includeMdcKeyName>application.id</includeMdcKeyName>
            <includeMdcKeyName>thread.id</includeMdcKeyName>
        </encoder>
    </appender>
    <logger name="org.apache.kafka" level="WARN"/>
    <logger name="com.example" level="INFO"/>
    <logger name="org.apache.kafka.streams.processor.internals.StoreChangelogReader" level="INFO"/>
    <root level="INFO">
        <appender-ref ref="STDOUT"/>
    </root>
</configuration>
```

JSON lines to stdout; container runtimes and log collectors pick up natively. No file rotation — the orchestrator handles log lifecycle.

### Health checks — separate liveness and readiness

`KafkaStreams.State` exposes the lifecycle (`CREATED`, `REBALANCING`, `RUNNING`, `PENDING_SHUTDOWN`, `PENDING_ERROR`, `ERROR`, `NOT_RUNNING`). Expose via HTTP for K8s probes using the JDK's `com.sun.net.httpserver.HttpServer` (no web-framework dependency).

```java
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;

public class HealthCheckServer {
    public static void start(KafkaStreams streams, int port) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);

        // Liveness: JVM healthy and Streams not in ERROR state
        server.createContext("/health/live", exchange -> {
            KafkaStreams.State state = streams.state();
            boolean alive = state != KafkaStreams.State.ERROR
                         && state != KafkaStreams.State.NOT_RUNNING;
            int status = alive ? 200 : 503;
            String body = "{\"status\":\"" + (alive ? "UP" : "DOWN") + "\",\"state\":\"" + state + "\"}";
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(status, body.length());
            exchange.getResponseBody().write(body.getBytes());
            exchange.getResponseBody().close();
        });

        // Readiness: Streams fully RUNNING
        server.createContext("/health/ready", exchange -> {
            boolean ready = streams.state() == KafkaStreams.State.RUNNING;
            int status = ready ? 200 : 503;
            String body = "{\"status\":\"" + (ready ? "UP" : "DOWN") + "\",\"state\":\"" + streams.state() + "\"}";
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(status, body.length());
            exchange.getResponseBody().write(body.getBytes());
            exchange.getResponseBody().close();
        });

        server.setExecutor(null);
        server.start();
    }
}
```

K8s deployment:

```yaml
livenessProbe:
  httpGet: { path: /health/live, port: 8080 }
  initialDelaySeconds: 30
  periodSeconds: 10
readinessProbe:
  httpGet: { path: /health/ready, port: 8080 }
  initialDelaySeconds: 30
  periodSeconds: 10
```

The distinction matters: during rebalance the app is alive (don't kill it) but not ready (don't send traffic to IQ endpoints). Without separate probes, K8s restarts apps during normal rebalances — cascading restarts.

### Dockerfile

```dockerfile
FROM eclipse-temurin:17-jre-alpine

RUN addgroup -S streams && adduser -S streams -G streams
WORKDIR /app
COPY build/libs/*-all.jar app.jar

# State directory — must match state.dir in application.properties.
# Do NOT use /tmp — container runtimes may clear it on restart, losing state.
RUN mkdir -p /var/kafka-streams/state && chown streams:streams /var/kafka-streams/state

USER streams

# -XX:+UseG1GC               : best GC for KS (mixed heap + off-heap RocksDB)
# -XX:MaxGCPauseMillis=20    : keep GC pauses short to avoid session timeouts
# -XX:MaxRAMPercentage=75    : leave 25% for RocksDB off-heap (block cache, memtables)
# -XX:+UseContainerSupport   : respect container limits (default in JDK 17+)
ENV JAVA_OPTS="-XX:+UseG1GC -XX:MaxGCPauseMillis=20 -XX:MaxRAMPercentage=75 -XX:+UseContainerSupport"

EXPOSE 8080
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

**Memory note:** RocksDB uses significant off-heap memory (block cache, write buffers, bloom filters). Setting `-Xmx` to the full container limit will OOM-kill the pod. `MaxRAMPercentage=75` leaves headroom. For stateful apps with many partitions, you may need lower — see [Architecture § Memory](kafka-streams-architecture.md#memory).

### Deployment sizing

Parallelism rule: `instances × num.stream.threads ≤ input_partitions`. More = idle hot standbys.

- **Stateless:** scale horizontally; more threads/instance (match CPU); fewer instances. Constraints: CPU, network.
- **Stateful:** scale carefully. Prefer fewer large instances over many small (restoration is expensive). Calculate RocksDB memory.

Container resources:

```yaml
resources:
  requests: { memory: "2Gi", cpu: "1000m" }   # 1 core/thread
  limits:   { memory: "2Gi" }                  # NO CPU limit (throttling → rebalances)
```

Memory = JVM heap (75%) + RocksDB (25%). **Never limit CPU** — throttling causes poll timeouts and rebalance loops.

**Persistent Volumes (critical for stateful apps):** Always use PVCs for stateful KS apps in K8s. Ephemeral storage forces full state restoration on every restart (hours for large stores).

```yaml
volumeClaimTemplates:
- metadata:
    name: state-store
  spec:
    accessModes: ["ReadWriteOnce"]
    storageClassName: "ssd"
    resources:
      requests:
        storage: "50Gi"   # 3x expected state size (SST + WAL + compaction)
```

Mount at `state.dir`. Size at 3× expected state to accommodate SST files, WAL, and compaction overhead. Alert at 70% disk utilization.

**Cloud LB idle timeouts:** Cloud LBs (especially Azure) drop idle TCP connections after 4-30 min. If a stream thread is busy in a long RocksDB operation and doesn't send traffic, the connection is dropped. Set OS-level TCP keepalive and `connections.max.idle.ms` < LB idle timeout. Fix root-cause long-running operations (see [Debugging § Large State Store Pathology](kafka-streams-debugging.md)).

Critical timeouts to align for production:

```properties
consumer.max.poll.interval.ms=600000   # 10 min — match worst-case processing time
consumer.session.timeout.ms=45000       # 45 s — heartbeat detection
consumer.request.timeout.ms=600000      # Match max.poll.interval.ms
# For EOS: transaction.timeout.ms <= max.poll.interval.ms
```

### DLQ with KIP-1034

`processing.exception.handler=org.apache.kafka.streams.errors.DeadLetterQueueExceptionHandler`

DLQ naming: `<application.id>-<source-topic>-dlq`. Headers include original topic/partition/offset, exception, timestamp.

**Pre-create DLQ topics** (production clusters have `auto.create.topics.enable=false`):

```bash
kafka-topics --create --topic my-app-input-dlq --partitions 4 --replication-factor 3 \
  --config retention.ms=604800000 --bootstrap-server <broker>
# CC: confluent kafka topic create my-app-input-dlq --partitions 4
```

| Handler | Use |
|---|---|
| `LogAndContinueExceptionHandler` | Dev |
| `DeadLetterQueueExceptionHandler` | Production |
| `LogAndFailExceptionHandler` | Strict correctness (test/regulated) |
| Custom | Complex routing |

### EOS production considerations

`exactly_once_v2` (never v1) — but be aware: enabling it turns on idempotent producers internally and caps `max.in.flight.requests.per.connection=5`. On WarpStream this has measurable throughput cost; see [exactly_once_v2 WarpStream throughput cost](exactly-once-v2-warpstream-throughput-cost.md). On classic Kafka the cost is present but smaller. Quantify before turning on for high-throughput pipelines.

Production EOS checklist:

1. `processing.guarantee=exactly_once_v2` (NOT `exactly_once`).
2. `commit.interval.ms` is NOT set (EOS overrides to 100 ms internally for correctness).
3. `transaction.timeout.ms` ≥ worst-case processing time.
4. `num.standby.replicas=1` for resilience.
5. `replication.factor=3` for internal topics.
6. Downstream consumers use `isolation.level=read_committed`.
7. Broker has `transaction.state.log.replication.factor=3` and `min.isr=2`.
8. On CC, the app runs at least once per 7 days (transactional ID expiry).
9. `consumer.max.poll.interval.ms ≥ transaction.timeout.ms`.

## Related

- [Exactly-Once Semantics](exactly-once-semantics.md) — idempotent producers, transactional two-phase commit
- [FSI Exactly-Once Pattern](../patterns/fsi-exactly-once.md) — five-layer EOS for financial services
- [FSI Producer Configuration](../patterns/producer-config-fsi.md) — producer-layer config baseline
- [FSI Consumer Configuration](../patterns/consumer-config-fsi.md) — consumer-layer config baseline
- [Kafka Streams Debugging](kafka-streams-debugging.md) — diagnostic counterpart
- [Kafka Streams Architecture](kafka-streams-architecture.md) — RocksDB memory formula, threading model
- [exactly_once_v2 WarpStream Throughput Cost](exactly-once-v2-warpstream-throughput-cost.md) — EOS cost on WarpStream
- [Dead Letter Queue Design](../patterns/dead-letter-queue-design.md) — DLQ architecture variants

---

*Source: confluentinc/agent-skills@91d1871e · skills/kafka-streams-programming/references/production-hardening.md · Ingested 2026-05-16 · Apache-2.0*
