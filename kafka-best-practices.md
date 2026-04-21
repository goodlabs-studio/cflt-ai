# Kafka Best Practices: Confluent Cloud on Azure AKS

> **C4E Wiki Stub** | GoodLabs Studio | Last Updated: April 2026
> Covers: Consumer Lag, Publish Lag, Keep-Alive, Rebalance Prevention, Azure AKS Integration

---

## Table of Contents

1. [Broker / Topic Configuration](#1-broker--topic-configuration)
2. [Producer Configuration](#2-producer-configuration)
3. [Consumer Configuration](#3-consumer-configuration)
4. [Application-Level Behaviors](#4-application-level-behaviors)
5. [Azure AKS Integration](#5-azure-aks-integration)
6. [Confluent Cloud Dedicated Cluster Operations](#6-confluent-cloud-dedicated-cluster-operations)
7. [Monitoring & Alerting](#7-monitoring--alerting)

---

## 1. Broker / Topic Configuration

> Set via `confluent kafka cluster configuration update` (Dedicated clusters only) or at topic level.

### Broker-Level (Dedicated Clusters — CLI Only)

```properties
num.replica.fetchers=4                # faster ISR catch-up after broker restart
```

### Topic-Level (All Cluster Types)

```properties
min.insync.replicas=2                 # require 2 ISR acks — durability floor for FSI
unclean.leader.election.enable=false  # never elect out-of-sync replica as leader
retention.ms=3600000                  # 1hr for fraud/time-sensitive topics
                                      # adjust per topic SLA
```

### What Brokers Do NOT Control

The following are **client-side only** — the broker has no equivalent setting and never sees these values:

- `linger.ms`
- `batch.size`
- `compression.type`
- `max.block.ms`
- `fetch.max.wait.ms`

---

## 2. Producer Configuration

> All settings apply to the **Kafka producer client** running in your AKS pod. No broker changes required.

### Batching

```properties
# Immediate dispatch, sane batching for bursts
linger.ms=0                           # send immediately — never wait to fill batch
                                      # NOTE: default changed from 0 to 5ms in Kafka 4.0+
                                      # Explicitly set 0 for latency-critical producers
batch.size=16384                      # default 16KB — absorbs micro-bursts at no cost
                                      # NEVER set to 0 — causes 1 record = 1 ProduceRequest
compression.type=none                 # or lz4 at low TPS; full compression not worth it
                                      # under ~100 TPS
```

> **Why batch.size=0 is harmful:** Creates a new ProducerBatch object per record (GC churn),
> defeats TCP pipelining, and triggers Nagle algorithm at low TPS. `linger.ms=0` alone already
> gives immediate dispatch behavior.

### Timeouts — Must Be Internally Consistent

```properties
request.timeout.ms=30000              # wait for broker ack after send
delivery.timeout.ms=180000            # total budget: linger + request + retries
                                      # must satisfy: delivery >= linger + (retries × request)
max.block.ms=5000                     # fail fast if broker unreachable
                                      # default 60s is too long for fraud detection
```

### Reliability

```properties
acks=all                              # require full ISR ack — FSI minimum
retries=10                            # generous retry count
retry.backoff.ms=250
enable.idempotence=true               # dedup on retry — requires acks=all
```

### Pipeline & Connection

```properties
max.in.flight.requests.per.connection=5   # allow pipelining — never set to 1
                                          # unless EOS strictly required
socket.keepalive.enable=true              # CRITICAL: default is FALSE
                                          # without this, idle sockets age silently
                                          # toward Azure ILB 4-min kill timeout
connections.max.idle.ms=180000            # recycle connection at 3min —
                                          # before Azure ILB fires at 4min
reconnect.backoff.ms=100
reconnect.backoff.max.ms=1000             # cap at 1s — default 10s = 10s fraud blind spot
```

### Metadata

```properties
metadata.max.age.ms=60000             # refresh every 60s — reduces stall visibility
                                      # on sparse send patterns
```

---

## 3. Consumer Configuration

> All settings apply to the **Kafka consumer client**. No broker changes required unless noted.

### Polling

```properties
fetch.min.bytes=1                     # return immediately — don't wait for data
                                      # Use 1 for critical SLA tier (fraud, market data)
                                      # Use 1024 for standard/best-effort tiers to reduce
                                      # broker fetch request load
fetch.max.wait.ms=0                   # CRITICAL for fraud detection
                                      # default 500ms = unacceptable latency floor
                                      # CAVEAT: increases broker FetchRequest load —
                                      # only justified for sub-10ms SLA tiers.
                                      # Use 500-1000ms for standard/best-effort workloads.
max.poll.records=10                   # small batches = fast per-poll completion
                                      # reduces risk of exceeding max.poll.interval.ms
                                      # under backpressure
```

### Heartbeat & Session

```properties
heartbeat.interval.ms=3000            # send heartbeat every 3s
session.timeout.ms=45000              # broker tolerates 15 missed heartbeats (45/3)
                                      # increase to 90000 if AKS pod restarts are slow
max.poll.interval.ms=600000           # MUST be > (max.poll.records × worst_case_record_ms)
                                      # default 5min is often too short under backpressure
```

### Offset Commit

```properties
enable.auto.commit=false              # always manage offsets manually in production
                                      # auto.commit hides real lag metrics
                                      # and creates duplicate-processing risk on rebalance
```

### Rebalance Strategy

```properties
partition.assignment.strategy=org.apache.kafka.clients.consumer.CooperativeStickyAssignor
# Replaces default eager rebalancer
# Eager:       ALL partitions revoked on any rebalance — entire group freezes
# Cooperative: only MOVING partitions revoked — unaffected partitions keep consuming
```

> **Migration from Eager to Cooperative (two-phase rolling restart):**
> 1. **Phase 1:** Set `partition.assignment.strategy` to
>    `[RangeAssignor, CooperativeStickyAssignor]` (dual-assignor). Rolling restart all consumers.
>    This phase is backward-compatible — eager consumers can coexist with cooperative-capable ones.
> 2. **Phase 2:** Remove `RangeAssignor`, leaving only `CooperativeStickyAssignor`.
>    Rolling restart again. All consumers now use cooperative protocol.
>
> **KIP-848 (Kafka 4.0+):** Server-side rebalancing moves assignment computation to the broker.
> Set `group.protocol=consumer` to opt in. Up to 20x faster rebalances — expected to become
> the default in Kafka 5.0. Supported on Confluent Cloud (GA June 2025) and Confluent Platform 8.0.

### Static Group Membership (Eliminates Rebalance on Pod Restart)

```properties
group.instance.id=fraud-consumer-az1-pod0   # unique per pod, stable across restarts
session.timeout.ms=60000                     # broker waits this long before treating
                                             # static member as dead
```

> **In Kubernetes:** Use `metadata.name` as the source for `group.instance.id`.
> Deploy consumers as **StatefulSet** (not Deployment) for stable pod names.

### Follower Fetching (`client.rack`)

```properties
client.rack=azure-eastus2-az1          # match your AZ — enables follower fetching
                                       # consumer reads from nearest ISR replica
                                       # reduces cross-AZ network cost and latency
```

> In AKS, derive `client.rack` from the node's `topology.kubernetes.io/zone` label
> via the Kubernetes downward API. Requires broker-side `replica.selector.class=
> org.apache.kafka.common.replica.RackAwareReplicaSelector` (Confluent Cloud enables
> this by default for Dedicated clusters).

### Connection

```properties
socket.keepalive.enable=true
connections.max.idle.ms=180000
reconnect.backoff.max.ms=1000
```

---

## 4. Application-Level Behaviors

### 4.1 Decouple Poll Loop from Processing

The single most important pattern for preventing rebalance under backpressure.

**Anti-pattern (coupled loop):**
```java
while (true) {
    records = consumer.poll(Duration.ofMillis(500));
    for (record : records) {
        process(record);         // slow — blocks next poll()
        writeToDatabase(record); // slow — blocks next poll()
    }
    consumer.commitSync();       // blocks next poll()
}
```

**Correct pattern (decoupled):**
```java
BlockingQueue<ConsumerRecord> queue = new LinkedBlockingQueue<>(1000);

// Poll thread — only job is keep polling and maintaining heartbeat
while (true) {
    records = consumer.poll(Duration.ofMillis(100));
    for (record : records) {
        queue.put(record);       // hand off immediately, never block
    }
}

// Separate worker thread(s)
while (true) {
    record = queue.take();
    process(record);             // fraud engine, DB writes, etc.
    trackOffset(record);         // manage offsets in worker, not poll thread
}
```

### 4.2 Manual Offset Management with Decoupled Processing

```java
Map<TopicPartition, OffsetAndMetadata> pendingOffsets = new ConcurrentHashMap<>();

// Worker signals completion
pendingOffsets.put(
    new TopicPartition(record.topic(), record.partition()),
    new OffsetAndMetadata(record.offset() + 1)
);

// Poll thread commits periodically — async to avoid blocking
consumer.commitAsync(pendingOffsets, (offsets, ex) -> {
    if (ex != null) log.warn("Commit failed, will retry next cycle: {}", ex.getMessage());
});
```

### 4.3 Pause / Resume on Backpressure

Stay in the consumer group while downstream recovers. Never let slow processing trigger rebalance.

```java
Set<TopicPartition> partitions = consumer.assignment();

// Signal backpressure from downstream (fraud engine, DB)
consumer.pause(partitions);

// Keep polling — empty results but heartbeat continues
while (isBackpressured()) {
    consumer.poll(Duration.ofMillis(100));
}

// Resume when downstream clears
consumer.resume(partitions);
```

### 4.4 Graceful Shutdown

Prevents uncommitted offsets and unnecessary rebalance on pod termination.

```java
Runtime.getRuntime().addShutdownHook(new Thread(() -> {
    consumer.wakeup();              // interrupts poll() — throws WakeupException
}));

try {
    while (true) {
        consumer.poll(Duration.ofMillis(500));
        // process...
    }
} catch (WakeupException e) {
    // expected — shutdown in progress
} finally {
    consumer.commitSync();          // flush last offsets
    consumer.close();               // sends LeaveGroup RPC — immediate rebalance
                                    // instead of waiting session.timeout.ms
}
```

### 4.5 JVM Tuning for Low-Latency Consumers

```bash
# G1GC baseline
-XX:+UseG1GC
-XX:MaxGCPauseMillis=20
-XX:G1HeapRegionSize=16m
-XX:+ParallelRefProcEnabled
-XX:InitiatingHeapOccupancyPercent=35
-XX:+AlwaysPreTouch                # pre-allocate heap — eliminates page fault pauses
-Xms2g -Xmx2g                     # fixed heap — no resize pauses

# ZGC — preferred for fraud detection (JDK 15+)
-XX:+UseZGC                        # sub-ms GC pauses
```

---

## 5. Azure AKS Integration

### 5.1 AKS Pod Spec — Fraud Consumer

```yaml
apiVersion: apps/v1
kind: StatefulSet                       # NOT Deployment — required for stable group.instance.id
metadata:
  name: fraud-consumer
spec:
  template:
    spec:
      priorityClassName: high-priority  # prevent eviction during AKS maintenance

      containers:
      - name: fraud-consumer
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
          limits:
            cpu: "2"                    # MUST equal request
            memory: "4Gi"              # CFS throttle on burst kills heartbeat thread

        env:
        - name: KAFKA_GROUP_INSTANCE_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name  # fraud-consumer-0, -1, -2 — stable across restarts

        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 5"]

      terminationGracePeriodSeconds: 60

      # Spread across AZs — survive single-AZ maintenance
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
```

### 5.2 PodDisruptionBudget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: fraud-consumer-pdb
spec:
  minAvailable: 1                       # always keep at least 1 consumer alive
  selector:
    matchLabels:
      app: fraud-consumer
```

### 5.3 Azure ILB Idle Timeout

Azure Internal Load Balancer kills idle TCP connections at **4 minutes** with no RST/FIN.
Kafka clients don't detect this until the next write attempt.

```yaml
# Service annotation — minimum configurable is 4 min on Azure
metadata:
  annotations:
    service.beta.kubernetes.io/azure-load-balancer-tcp-idle-timeout: "4"
```

Mitigate via client config:
```properties
connections.max.idle.ms=180000    # 3 min — recycle before ILB fires
socket.keepalive.enable=true      # OS-level keepalive probes
```

### 5.4 AKS Maintenance Windows

```bash
# Pin maintenance to known off-peak window
az aks maintenanceconfiguration add \
  --resource-group <rg> \
  --cluster-name <cluster> \
  --name default \
  --weekday Monday \
  --start-hour 2
```

### 5.5 Private Link (Recommended for FSI Production)

```
Public endpoint:  AKS pod → Azure ILB → Public Internet → Confluent
Private Link:     AKS pod → Private Endpoint → Confluent VNet (direct)
```

Private Link eliminates the ILB idle timeout problem entirely and improves
security posture (traffic stays on Azure backbone). RTT improvement is environment-
dependent — primary benefits are ILB bypass and private connectivity, not quantified
latency reduction.
Verify current connectivity:
```bash
nslookup lkc-<yourcluster>.azure.confluent.cloud
# 10.x.x.x = Private Link (good)
# Public IP = public endpoint (ILB timeout risk)
```

---

## 6. Confluent Cloud Dedicated Cluster Operations

### Maintenance Window Control

Dedicated clusters **do not have a self-service UI** for broker maintenance windows.
Control plane maintenance (API availability) is separate from data plane (broker rolling restarts).

Actions:
- Open support ticket with exact UTC timestamps to confirm broker restart activity
- Request Access Transparency enrollment (Limited Availability as of early 2026)
- Request preferred maintenance window via account team
- Subscribe to `status.confluent.cloud` for your Azure region

### Access Transparency

Provides audit log visibility into when Confluent personnel access your cluster for maintenance.
Required for FSI compliance. Request enrollment via account team.

### Useful CLI Commands

```bash
# Confirm cluster type and details
confluent kafka cluster describe <lkc-id> --environment <env-id>

# Update broker config (Dedicated only)
confluent kafka cluster configuration update \
  --cluster <lkc-id> \
  --config num.replica.fetchers=4

# Update topic config
confluent kafka topic update <topic-name> \
  --config min.insync.replicas=2 \
  --config unclean.leader.election.enable=false

# Check audit logs
confluent audit-log describe --environment <env-id> --cluster <lkc-id>
```

---

## 7. Monitoring & Alerting

### Key Confluent Cloud Metrics

```
confluent_kafka_server_request_latency_p99     alert threshold: > 50ms
confluent_kafka_server_active_connection_count  alert on sudden drop
confluent_kafka_server_network_io_time          alert on spike
```

### Key Client JMX Metrics

```
# Producer
kafka.producer:type=producer-metrics,client-id=*
  connection-count          # should be stable — spike = reconnecting
  connection-creation-rate  # elevated = repeated reconnects
  request-latency-avg       # your publish SLA metric

# Consumer
kafka.consumer:type=consumer-fetch-manager-metrics
  fetch-latency-avg         # must stay under fraud SLA
  records-lag-max           # primary lag indicator
```

### Node Connectivity Errors

`Connection to Node 1 could not be established` across all AZs simultaneously indicates
**bootstrap broker metadata loss** — not a physical node failure. Node 1 is the client's
internal ID for the bootstrap broker, not a physical broker number.

Correlate with:
- `status.confluent.cloud` maintenance history
- Azure Activity Log for node events
- Consumer group rebalance timestamps in Control Center

---

## Quick Reference: Config Scope

| Property | Scope | Where to Set |
|---|---|---|
| `linger.ms` | Producer client | App config / ConfigMap |
| `batch.size` | Producer client | App config / ConfigMap |
| `compression.type` | Producer client | App config / ConfigMap |
| `max.block.ms` | Producer client | App config / ConfigMap |
| `delivery.timeout.ms` | Producer client | App config / ConfigMap |
| `request.timeout.ms` | Producer client | App config / ConfigMap |
| `acks` | Producer client | App config / ConfigMap |
| `enable.idempotence` | Producer client | App config / ConfigMap |
| `max.in.flight.requests.per.connection` | Producer client | App config / ConfigMap |
| `socket.keepalive.enable` | Producer + Consumer client | App config / ConfigMap |
| `connections.max.idle.ms` | Producer + Consumer client | App config / ConfigMap |
| `reconnect.backoff.max.ms` | Producer + Consumer client | App config / ConfigMap |
| `metadata.max.age.ms` | Producer + Consumer client | App config / ConfigMap |
| `fetch.min.bytes` | Consumer client | App config / ConfigMap |
| `fetch.max.wait.ms` | Consumer client | App config / ConfigMap |
| `max.poll.records` | Consumer client | App config / ConfigMap |
| `max.poll.interval.ms` | Consumer client | App config / ConfigMap |
| `session.timeout.ms` | Consumer client | App config / ConfigMap |
| `heartbeat.interval.ms` | Consumer client | App config / ConfigMap |
| `enable.auto.commit` | Consumer client | App config / ConfigMap |
| `group.instance.id` | Consumer client | Pod env var |
| `partition.assignment.strategy` | Consumer client | App config / ConfigMap |
| `client.rack` | Consumer client | App config / ConfigMap |
| `min.insync.replicas` | Topic | Confluent CLI |
| `unclean.leader.election.enable` | Topic | Confluent CLI |
| `num.replica.fetchers` | Broker (Dedicated only) | Confluent CLI |
| `retention.ms` | Topic | Confluent CLI |

---

*GoodLabs Studio C4E — FSI Kafka Platform Accelerator*
*Related: `fsi-kafka-platform` repo, Kafka DR Proposal, Oracle Co-Dependency section*
