---
title: FSI Exactly-Once Pattern
tags: [kafka fsi exactly-once transactions compliance]
sources: []
related: [concepts/exactly-once-semantics, concepts/sla-tiers, concepts/fsi-data-streaming-platform, patterns/dead-letter-queue-design]
confidence: medium
last_updated: 2026-04-11
last_validated: 2026-05-14
---

# FSI Exactly-Once Pattern

## Summary

End-to-end exactly-once semantics (EOS) in financial services requires a layered approach: idempotent producers prevent broker-level duplicates, transactional producers provide atomic multi-partition writes, `read_committed` consumers filter uncommitted data, the transactional outbox pattern ensures database-Kafka atomicity, and application-level idempotency keys guard against duplicate business effects at sink boundaries. In regulated environments (SOX, MiFID II, Dodd-Frank), EOS is not an optimization -- it is a compliance requirement. Duplicate or missing transactions constitute material misstatement, and failure modes like zombie producers or transaction timeouts carry regulatory implications that must be explicitly addressed in system design.

## Pattern

### Why EOS Matters in FSI

| Domain | Risk of Non-EOS | Regulatory Exposure |
|--------|-----------------|---------------------|
| Regulatory reporting | Duplicate/missing transactions inflate or understate reported balances | SOX Section 302/404 material misstatement; FFIEC examination findings |
| Payment processing | Double-debited wire transfers, duplicate settlements | Customer harm, litigation, regulator enforcement |
| Trade execution | Duplicate orders cause unintended market impact | MiFID II best execution violations; position risk |
| Reconciliation | End-of-day "breaks" proportional to semantic gaps | Operational cost; Dodd-Frank reporting accuracy |

Financial applications cannot afford anything less than exactly-once semantics -- they cannot have duplicates or lose messages when depositing or withdrawing money from a bank account.

### End-to-End EOS Layers

EOS is not a single configuration toggle. It is achieved through five cooperating layers:

```
Producer (L1+L2) --> Broker --> Consumer (L3) --> Application (L4+L5) --> External System
  idempotent +        txn        read_committed    outbox pattern       idempotency key
  transactional       log                          (DB+Kafka atomicity) (dedup at sink)
```

#### Layer 1: Idempotent Producer (Baseline)

The broker assigns each producer a PID and uses sequence numbers to deduplicate. Resending a message does not result in duplicate entries in the log, and log order is maintained.

```properties
# Idempotent producer -- mandatory baseline for all FSI producers
enable.idempotence=true
acks=all
# Retries are effectively infinite with idempotence enabled
retries=2147483647
max.in.flight.requests.per.connection=5
```

This layer prevents duplicate writes to Kafka but does NOT prevent duplicate business effects downstream.

#### Layer 2: Transactional Producer

Atomic multi-partition writes. All messages in a transaction are successfully written or none are. Offset commits are included in the transaction, making the read-process-write cycle atomic.

```properties
# Transactional producer -- required for atomic multi-topic writes
transactional.id=payments-processor-partition-0
enable.idempotence=true
acks=all
# transaction.timeout.ms must be tuned for peak load (see Failure Modes)
transaction.timeout.ms=60000
```

```java
// Transactional read-process-write cycle
producer.initTransactions();

while (running) {
    ConsumerRecords<String, PaymentEvent> records = consumer.poll(Duration.ofMillis(100));
    producer.beginTransaction();
    try {
        for (ConsumerRecord<String, PaymentEvent> record : records) {
            PaymentResult result = processPayment(record.value());
            producer.send(new ProducerRecord<>("payments.settlement.completed",
                record.key(), result));
        }
        // Commit offsets within the transaction -- atomic with output
        producer.sendOffsetsToTransaction(
            currentOffsets(records),
            consumer.groupMetadata());
        producer.commitTransaction();
    } catch (ProducerFencedException | OutOfOrderSequenceException e) {
        // Fatal -- this producer has been fenced by a newer instance
        producer.close();
        throw e;
    } catch (KafkaException e) {
        producer.abortTransaction();
        // Reset consumer position to last committed offset
    }
}
```

Critical: the mapping between input topic-partitions and `transactional.id` must remain consistent. If it changes, messages can leak through fencing, violating EOS guarantees.

#### Layer 3: Consumer with `read_committed`

Consumers only see messages from committed transactions. Messages from aborted transactions are filtered; messages from open transactions are withheld until commit or abort.

```properties
# Consumer -- must pair with transactional producer for EOS
isolation.level=read_committed
enable.auto.commit=false
auto.offset.reset=earliest
```

Latency impact: `read_committed` consumers cannot read ahead of open transactions. Long-running transactions increase end-to-end latency because consumers must wait for commit markers.

#### Layer 4: Transactional Outbox Pattern

Solves the dual-write problem: a service must update its database AND publish to Kafka atomically. Neither Kafka transactions nor DB transactions alone span both systems.

```
Service --> DB Transaction:
              1. UPDATE accounts SET balance = balance - 100 WHERE id = 'acct-123'
              2. INSERT INTO outbox (id, aggregate_type, payload, created_at)
                 VALUES (uuid, 'Payment', '{"amount":100}', NOW())
           --> COMMIT

Debezium CDC --> reads DB WAL/redo log --> publishes outbox rows to Kafka
```

The outbox table schema:

```sql
CREATE TABLE outbox (
    id            UUID PRIMARY KEY,
    aggregate_type VARCHAR(255) NOT NULL,
    aggregate_id   VARCHAR(255) NOT NULL,
    event_type     VARCHAR(255) NOT NULL,
    payload        JSONB NOT NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Debezium's Outbox Event Router SMT routes outbox events to the correct Kafka topic with proper key/value extraction. This guarantees database writes and event publishing are atomic -- they either both succeed or both fail.

#### Layer 5: Application-Level Idempotency Keys

Kafka producer idempotence prevents duplicate writes to brokers. It does not prevent duplicate business effects when a consumer processes the same message twice (e.g., after a rebalance with uncommitted offsets, or when consuming from a compacted topic).

Implementation strategies:

| Strategy | Mechanism | Strength | Use When |
|----------|-----------|----------|----------|
| DB upsert on event ID | `INSERT ... ON CONFLICT (event_id) DO NOTHING` | Strongest -- DB is source of truth | DB is the event sink |
| Idempotency key relay | Forward the same key to downstream REST calls | End-to-end | Calling external payment APIs |
| Processed-ID table | Track processed event IDs in a separate table, check before processing | Strong with DB transaction | Complex processing logic |
| Cache + DB fallback | In-memory/Redis cache for fast dedup, DB as authority | Performance optimization | High-throughput paths |

Cache-based deduplication alone is insufficient when correctness is critical. Production systems use cache as an optimization with the database as the final authority.

### Kafka Streams EOS

```properties
# Kafka Streams EOS -- exactly_once_v2 requires Kafka 2.5+
processing.guarantee=exactly_once_v2
# Older setting (deprecated): exactly_once
```

Internally, Kafka Streams wraps input consumption, state store updates, and output production in a single Kafka transaction. If EOS is enabled and local state diverges from the changelog topic, Kafka Streams deletes the state store and rebuilds from the changelog -- guaranteeing no duplicate or lost updates.

**Interactive Queries for real-time position views:** State stores materialized by Kafka Streams can be queried directly via the Interactive Query API. A wealth management firm maintaining real-time risk positions recalculates whenever business events arrive, exposing positions via a REST API layered over state stores.

Infrastructure requirement: minimum 3 brokers for EOS (production standard).

### Flink EOS with Kafka

Flink achieves end-to-end EOS by combining checkpointing with Kafka transactions via a two-phase commit protocol:

1. **Phase 1 (Pre-commit):** Flink prepares all sinks (Kafka producers) for commit
2. **Phase 2 (Commit):** If all preparations succeed, Flink commits the Kafka transaction; if any fails, abort

```properties
# Flink Kafka sink -- transaction timeout must exceed checkpoint interval
transaction.timeout.ms=120000
# Must not exceed broker's transaction.max.timeout.ms (default 900000 / 15 min)
```

**Confluent Cloud for Apache Flink:** EOS is enabled by default. Kafka transactions are committed approximately every minute. Latency under EOS is ~1 minute, dominated by the transaction commit interval. For at-least-once (sub-100ms latency), consumers can use `isolation.level=read_uncommitted` at the cost of potential duplicates.

> ⚠️ unverified -- Confluent Cloud Flink transaction commit interval is not documented as user-configurable. Contact Confluent Support for current tunability.

### Saga Pattern for Multi-Service Workflows

For distributed transactions spanning multiple services (e.g., debit account -> execute trade -> update ledger), the saga pattern replaces two-phase commit with a sequence of local transactions and compensating actions:

| Approach | Coordination | FSI Suitability |
|----------|-------------|-----------------|
| **Choreography** | Event-driven, no central coordinator. Each service publishes domain events triggering the next step. | Simpler services; harder to reason about failure paths |
| **Orchestration** | Central saga coordinator manages sequence, handles compensation. | Preferred for payment workflows; explicit failure handling |

Critical caveat: sagas lack isolation (the "I" in ACID). Concurrent saga executions can create data anomalies. FSI countermeasures:

- **Semantic locking:** Reserve resources during saga execution
- **Commutative updates:** Design updates that are order-independent
- **Versioned reads:** Use optimistic concurrency control on entity versions

### Audit Trail Design

Five non-negotiable requirements for FSI audit logging:

1. **Immutability:** Append-only Kafka log -- once written, events cannot be altered or deleted
2. **Retention:** 7+ years (SOX), stored in tiered storage or immutable object storage (S3 Object Lock, WORM)
3. **Security:** Encryption at rest and in transit, mTLS + RBAC, per-application service accounts
4. **Real-time processing:** Stream processing (Flink/Kafka Streams) for normalization, enrichment, and anomaly detection
5. **Lineage:** Schema Registry with `FULL` compatibility; correlation IDs threading through Kafka headers, service calls, and database records

Audit topic configuration:

```properties
# Dedicated audit log topic
retention.ms=-1
# Or use tiered storage for cost-effective long-term retention
confluent.tier.enable=true
cleanup.policy=delete
# Never compact -- every event version must be preserved
min.insync.replicas=2
replication.factor=3
```

| Regulation | Minimum Retention | Key Requirement |
|------------|-------------------|-----------------|
| SOX | 7 years | Full data lineage, change traceability |
| MiFID II | 5 years (7 for some records) | Trade reconstruction, best execution proof |
| Dodd-Frank | 5 years | Swap/derivative transaction records |
| PCI DSS | 1 year (varies by control) | Access logs, cardholder data audit |
| SOC 2 | 1 year | Tenant-level audit trails |

### Failure Modes and Mitigations

#### Transaction Timeout During Peak Load

If processing exceeds `transaction.timeout.ms` (default 60s), the broker bumps the producer epoch and aborts the transaction. The producer receives `ProducerFencedException` even with no competing producer.

In Kafka Streams: if multiple punctuators exceed the transaction timeout, or if state store recovery from changelog exceeds the timeout, the stream thread cannot start.

**Mitigation:**

```properties
# Increase for peak-load scenarios
# Must not exceed broker's transaction.max.timeout.ms (default 900000ms / 15 min)
transaction.timeout.ms=120000
```

Monitor transaction duration via broker metrics. Size processing to complete within timeout. Consider batching fewer records per transaction under sustained load.

**Regulatory implication:** Timed-out transactions are aborted and must be retried. Incorrect retry logic means lost transactions -- a regulatory violation.

#### Zombie Fencing (Producer Epoch)

When `initTransactions()` is called, the broker completes any open transactions for that `transactional.id` and increments the epoch. Producers with an older epoch are fenced -- their writes are rejected.

```
Producer A (epoch=1) --> network partition --> still thinks it's active
Producer B (epoch=2) --> initTransactions() --> epoch bumped to 2
Producer A (epoch=1) --> attempts write --> ProducerFencedException (fenced)
```

**Regulatory implication:** If `transactional.id` assignment is inconsistent (e.g., not stable across restarts, or not mapped 1:1 to input partitions), zombie producers can bypass fencing and produce duplicate financial events.

#### Split-Brain in Multi-DC

| Topology | RPO | Split-Brain Risk | FSI Suitability |
|----------|-----|------------------|-----------------|
| Active-passive + Cluster Linking | > 0 (seconds) | Low -- only one side accepts writes | Preferred for most FSI workloads |
| Stretch cluster (synchronous) | 0 | None -- single logical cluster | Best for compliance-tier data; requires 3 DCs, <10K TPS |
| Active-active | > 0 | High -- both sides accept writes | Not recommended without conflict resolution logic |

Stretch clusters provide RPO=0 but require three synchronized data centers and low-latency interconnects. Practical when transaction rates remain below 10,000/s and datacenters are geographically proximate.

**Regulatory implication:** Split-brain producing divergent financial records is a material reporting risk. Never deploy active-active without explicit conflict resolution logic in regulated environments.

### Mainframe Integration: IBM MQ to Kafka EOS Bridge

The canonical mainframe-to-Kafka bridge uses the IBM MQ Source Connector:

```
z/OS (CICS/IMS) --> IBM MQ --> MQ Source Connector --> Kafka
                                (exactly-once mode)
```

The MQ Source Connector supports exactly-once delivery when configured with Kafka transactions. Combined with `read_committed` consumers downstream, this extends EOS from the mainframe boundary into the streaming platform.

> ⚠️ unverified -- IBM MQ Source Connector exact EOS configuration properties and version requirements were not confirmed via MCP sources.

### SLA Tier Mapping

| SLA Tier | Latency Target | EOS Required? | Rationale |
|----------|---------------|---------------|-----------|
| Sub-millisecond (market data) | < 1ms | No -- at-least-once + dedup | EOS transaction overhead (~5-20ms) exceeds latency budget |
| Real-time risk (< 10ms) | < 10ms | Conditional -- use application-level idempotency | Transactional producer adds ~5ms; feasible with tuning |
| Compliance (< 100ms) | < 100ms | Yes -- full EOS stack | Latency budget accommodates transactions; regulatory mandate |
| Async (reconciliation) | Seconds to minutes | Yes -- full EOS stack | No latency pressure; correctness is paramount |

### Performance Considerations

| Factor | Impact | Mitigation |
|--------|--------|------------|
| Transactional producer overhead | ~5-20ms per transaction commit | Batch more records per transaction; overhead is independent of message count |
| `read_committed` consumer lag | Cannot read ahead of open transactions | Keep transactions short; avoid long-running processing within transaction boundaries |
| Kafka Streams EOS throughput | Lower than at-least-once due to transaction coordination | Accept trade-off for correctness; scale horizontally |
| Flink EOS latency (Confluent Cloud) | ~1 minute end-to-end | Use at-least-once + application dedup if sub-second latency required |
| State store rebuild on divergence | Full rebuild from changelog on EOS mismatch | Size changelog topics for fast replay; use standby replicas |

Key insight from Kafka transaction design: transaction overhead is independent of the number of messages in the transaction. Higher throughput comes from including more messages per transaction, not from fewer transactions.

## When to Use

- Payment processing pipelines where duplicate execution causes customer harm
- Regulatory reporting workflows subject to SOX, MiFID II, or Dodd-Frank accuracy requirements
- Trade execution systems where duplicate orders create market impact or position risk
- Any Kafka-to-database pipeline in FSI where the dual-write problem must be solved atomically
- End-of-day reconciliation pipelines where reducing "breaks" has measurable operational value
- Multi-service financial workflows (account debit -> trade execution -> ledger update) requiring saga orchestration
- Audit trail systems requiring immutable, traceable, exactly-once event capture with 7+ year retention

## Caveats

- EOS is a system property, not a config toggle -- all five layers (idempotent producer, transactional producer, `read_committed` consumer, outbox pattern, application idempotency) must be addressed for true end-to-end guarantees
- `transactional.id` must be stable across restarts and consistently mapped to input partitions; inconsistent assignment breaks zombie fencing
- Transaction timeout defaults (60s) are often too low for peak-load FSI workloads; tune `transaction.timeout.ms` but do not exceed broker's `transaction.max.timeout.ms`
- Kafka Streams `exactly_once_v2` requires Kafka 2.5+; the older `exactly_once` setting is deprecated and has higher coordination overhead
- Saga pattern lacks isolation -- concurrent sagas can produce data anomalies; use semantic locking or commutative updates as countermeasures
- Confluent Cloud Flink EOS introduces ~1 minute latency; not suitable for sub-second latency requirements without falling back to at-least-once + application dedup
- The outbox pattern adds operational complexity (Debezium CDC pipeline, outbox table management, WAL retention sizing) -- justified in FSI but not free
- Active-active multi-DC with EOS is not achievable without application-level conflict resolution; prefer active-passive + Cluster Linking or stretch clusters

## Related

- [Exactly-Once Semantics](concepts/exactly-once-semantics.md) -- foundational concept for Kafka EOS mechanisms
- [SLA Tiers](concepts/sla-tiers.md) -- tier definitions determining which workloads require EOS vs. at-least-once
- [FSI Data Streaming Platform](concepts/fsi-data-streaming-platform.md) -- overall FSI architecture context
- [Dead Letter Queue Design](patterns/dead-letter-queue-design.md) -- error handling pattern complementing EOS for poison messages
- [DR -- Cluster Linking](patterns/dr-cluster-linking.md) -- DR pattern with EOS implications for multi-DC deployments
