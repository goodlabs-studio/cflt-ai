**Confluent Cloud on Azure AKS**

Remediation Recommendations & Triage Guide

GoodLabs Studio  |  FSI Platform Engineering

April 2026  |  CONFIDENTIAL

# **TL;DR — What to Fix and In What Order**

| Core Finding Your Confluent Cloud Dedicated cluster on Azure AKS has four compounding issues: (1) a producer misconfiguration (batch.size=0) that creates unnecessary broker round trips; (2) TCP connections silently killed by Azure ILB before the client detects them; (3) Confluent-initiated broker maintenance aligning with your production windows; and (4) consumer rebalance behavior that amplifies lag during backpressure. None of these require Confluent support to resolve — items 1 through 3 are client config changes deployable today. |
| :---- |

## **Priority Order**

| \# | Action | Impact | Effort | Owner |
| :---- | :---- | :---- | :---- | :---- |
| 1 | Fix batch.size=0 → 16384 | CRITICAL | \< 1hr | App Team |
| 2 | Enable socket.keepalive.enable=true | CRITICAL | \< 1hr | App Team |
| 3 | Set connections.max.idle.ms=180000 | HIGH | \< 1hr | App Team |
| 4 | Set reconnect.backoff.max.ms=1000 | HIGH | \< 1hr | App Team |
| 5 | Set fetch.max.wait.ms=0 | HIGH | \< 1hr | App Team |
| 6 | Decouple poll loop from processing | HIGH | 1-2 days | App Team |
| 7 | Switch to CooperativeStickyAssignor | HIGH | \< 1hr | App Team |
| 8 | Migrate consumers to StatefulSet \+ group.instance.id | MEDIUM | 1 day | Platform |
| 9 | Pin AKS maintenance window | MEDIUM | \< 1hr | Platform |
| 10 | Open Confluent support ticket re: broker restart schedule | MEDIUM | \< 1hr | Ops |
| 11 | Evaluate Private Link for lkc cluster | MEDIUM | 2-3 days | Platform |
| 12 | Request Access Transparency enrollment | LOW | \< 1hr | Ops |

| Immediate Win (30 Minutes) Items 1-5 are single-line config changes in a Kubernetes ConfigMap. Rolling restart the producer and consumer deployments. No Confluent changes needed. These five changes address the root causes of both the publish lag and the Node 1 connection errors. |
| :---- |

# **Problem Summary**

## **1\. Producer Misconfiguration (batch.size=0)**

batch.size=0 means every record becomes its own ProduceRequest to the broker — one record, one full TCP round trip. At 50 TPS this is manageable because TCP connections stay warm. At 20 TPS, 50ms gaps between records allow the Nagle algorithm to fire, in-flight pipeline slots drain between sparse sends, and metadata refresh stalls become visible with no batch buffer to absorb them.

*Additionally, batch.size=0 creates a new ProducerBatch object per record, causing constant GC pressure. The standard behavior of linger.ms=0 already achieves immediate dispatch — batch.size=0 adds cost with zero benefit.*

## **2\. TCP Keep-Alive Disabled (socket.keepalive.enable Default \= false)**

The Kafka Java client defaults socket.keepalive.enable to false. On Azure, the Internal Load Balancer kills idle TCP connections at 4 minutes with no RST or FIN — the client never learns the connection is dead. The next write attempt on a dead socket triggers reconnect, and with reconnect.backoff.max.ms at the default 10 seconds, this creates a 10-second fraud detection blind spot on every idle-timeout event.

## **3\. Confluent Cloud Broker Maintenance on Production Windows**

Connection errors logged as "Connection to Node 1 could not be established" across all AZs simultaneously are consistent with Confluent-initiated rolling broker restarts, not individual broker failures. The observed pattern — recurring on the 2nd and 4th week of the month at 1-2AM and 6-9PM — aligns with Confluent's maintenance cadence. Dedicated cluster maintenance windows are not configurable via the UI and require a support ticket to influence.

## **4\. Consumer Rebalance Under Backpressure**

The default Kafka consumer serializes polling with processing. When a downstream system (fraud engine, database write) is slow, the time between poll() calls can exceed max.poll.interval.ms, causing the broker to evict the consumer from the group and trigger a rebalance. Rebalance stops all consumption across the entire consumer group — not just the slow consumer — compounding lag.

The default eager rebalancer revokes all partition assignments on any rebalance event. For a 12-partition fraud consumer group, one slow pod stops all 12 partitions from being consumed during the rebalance window.

# **Triage Guide by Symptom**

| Symptom | Most Likely Cause | First Check |
| :---- | :---- | :---- |
| Node 1 could not be established — all AZs simultaneously | Confluent broker rolling restart or Azure backbone event | status.confluent.cloud history \+ open support ticket with timestamps |
| Publish lag worse at 20 TPS than 50 TPS | batch.size=0 \+ TCP Nagle firing in idle gaps | Confirm batch.size config in producer ConfigMap |
| Consumer lag spikes then recovers every 2-4 weeks | AKS node drain or Confluent maintenance causing rebalance | kubectl get events \+ az monitor activity-log for node reboots |
| Consumer group stuck in REBALANCING state | max.poll.interval.ms exceeded due to slow processing | Reduce max.poll.records; decouple poll from processing |
| Lag on subset of partitions only | Hot partition or single consumer instance issue | Check hot\_partition metric in Confluent Cloud console |
| Intermittent disconnects at 1-2AM and 6-9PM | Confluent maintenance (1-2AM) \+ Azure ILB idle timeout (6-9PM) | Correlate with status page; verify connections.max.idle.ms setting |
| Fraud detection latency spikes up to 500ms | fetch.max.wait.ms at default (500ms) — consumer waiting for batch fill | Set fetch.max.wait.ms=0 immediately |

# **Detailed Recommendations**

## **Phase 1 — ConfigMap Changes (Today)**

All five changes below are single-property edits to your Kafka client configuration. They require a ConfigMap update and rolling pod restart only. No Confluent Cloud changes, no infrastructure work.

### **1.1  Fix batch.size**

| Property | Current | Recommended |
| :---- | :---- | :---- |
| batch.size | 0 | 16384 |
| linger.ms | 0 | 0 (keep as-is) |

linger.ms=0 already provides immediate dispatch. Restoring batch.size to 16384 allows micro-burst absorption without changing dispatch behavior. At 20-50 TPS, batches will rarely fill — the cost is zero, the benefit is eliminating the per-record ProduceRequest overhead and GC churn.

> **Note:** The `linger.ms` default changed from 0 to 5ms in Kafka 4.0+. For latency-critical producers, explicitly set `linger.ms=0` to ensure immediate dispatch regardless of Kafka version.

### **1.2  Enable TCP Keep-Alive and Connection Recycling**

| Property | Default | Recommended |
| :---- | :---- | :---- |
| socket.keepalive.enable | false | true |
| connections.max.idle.ms | 540000 (9min) | 180000 (3min) |
| reconnect.backoff.max.ms | 10000 (10s) | 1000 (1s) |

socket.keepalive.enable=true instructs the OS to send TCP keepalive probes on idle connections. connections.max.idle.ms=180000 forces Kafka-level connection recycling at 3 minutes, one minute before the Azure ILB 4-minute kill threshold. reconnect.backoff.max.ms=1000 limits reconnect delay to 1 second — the default 10-second cap creates unacceptable fraud detection gaps.

### **1.3  Fix Consumer Fetch Latency**

| Property | Default | Recommended |
| :---- | :---- | :---- |
| fetch.max.wait.ms | 500 | 0 |
| fetch.min.bytes | 1 | 1 (keep as-is) |
| max.poll.records | 500 | 10 |

fetch.max.wait.ms=500 means the consumer waits up to 500ms for the broker to accumulate fetch.min.bytes before responding. For fraud detection, this is an artificial 500ms floor on consumer latency. Setting it to 0 forces the broker to respond immediately with whatever data is available.

> **Trade-off:** `fetch.max.wait.ms=0` increases broker FetchRequest load because every poll triggers an immediate response regardless of data availability. This is justified for sub-10ms SLA tiers (fraud detection, market data). For standard or best-effort workloads, use 500-1000ms to reduce broker load.

Reducing max.poll.records from 500 to 10 ensures each poll batch completes processing quickly, reducing the risk of exceeding max.poll.interval.ms under backpressure.

## **Phase 2 — Application Changes (1-2 Days)**

### **2.1  Decouple Poll Loop from Processing**

The primary cause of rebalance-under-backpressure is the coupled poll-process-commit loop. When downstream systems (fraud engine, database) are slow, the time between poll() calls grows. If it exceeds max.poll.interval.ms, the broker evicts the consumer.

The fix is to introduce an internal BlockingQueue between the poll thread and a separate worker thread pool. The poll thread's only job is to call poll() and enqueue records. It never blocks on processing. The worker threads handle processing and offset tracking independently.

This change requires careful offset management: offsets must only be committed after the worker confirms processing is complete, not on the poll thread's timer. This is a 1-2 day development effort with testing.

### **2.2  Implement pause() / resume() for Backpressure**

When downstream systems signal backpressure (queue full, DB throttling), call consumer.pause(assignedPartitions) to stop fetching new records. Continue calling poll() on a short interval to maintain heartbeats and keep the consumer in the group. Call resume() when downstream capacity recovers. This is the correct Kafka API for backpressure handling — it does not trigger rebalance.

### **2.3  Implement Graceful Shutdown**

Register a JVM shutdown hook that calls consumer.wakeup() to interrupt poll(), then in the finally block call commitSync() and consumer.close(). The close() call sends a LeaveGroup RPC to the broker, triggering an immediate rebalance rather than waiting for session.timeout.ms to expire. This is critical for clean rolling deployments on AKS.

## **Phase 3 — Platform Changes (1 Week)**

### **3.1  Switch to CooperativeStickyAssignor**

Change partition.assignment.strategy to CooperativeStickyAssignor on all consumers in the fraud detection group. This is a one-line config change but requires a coordinated rolling restart of all consumers in the group to complete the protocol transition. Plan a maintenance window.

Impact: when any future rebalance occurs (maintenance, pod restart, scale event), only the partitions that need to move are revoked. Partitions that stay on the same consumer continue processing without interruption.

### **3.2  Enable Follower Fetching (`client.rack`)**

Set `client.rack` on all consumers to match the pod's availability zone. This enables follower fetching — consumers read from the nearest ISR replica instead of always crossing AZs to the leader. Reduces cross-AZ data transfer costs and latency.

```properties
client.rack=azure-eastus2-az1    # derive from topology.kubernetes.io/zone via downward API
```

Confluent Cloud Dedicated clusters enable `RackAwareReplicaSelector` by default. No broker-side changes needed.

### **3.3  Migrate to StatefulSet with Static Group Membership**

Convert fraud consumer Deployments to StatefulSets to guarantee stable pod names (fraud-consumer-0, \-1, \-2). Set group.instance.id to the pod name via the Kubernetes downward API. With static membership, a pod that restarts and rejoins within session.timeout.ms is recognized by the broker as the same consumer — no rebalance fires.

Add a PodDisruptionBudget with minAvailable=1 to prevent AKS node drain from evicting all consumers simultaneously.

### **3.4  Pin AKS Maintenance Window**

| Component | Action | Command |
| :---- | :---- | :---- |
| AKS | Pin maintenance to Monday 2AM | az aks maintenanceconfiguration add \--weekday Monday \--start-hour 2 |
| Confluent | Request preferred window via support ticket | Open ticket with exact UTC timestamps |
| Azure ILB | Verify idle timeout setting | Check service annotation \+ connections.max.idle.ms |

## **Phase 4 — Infrastructure Evaluation (2-4 Weeks)**

### **4.1  Private Link Assessment**

Currently connecting to lkc-\*.azure.confluent.cloud via public endpoint. This routes through Azure ILB and the public internet, introducing the idle timeout risk.

Private Link connects AKS pods directly to the Confluent VNet via a private endpoint, eliminating the ILB hop entirely. For an FSI fraud detection workload with sub-millisecond latency requirements, this is the correct target architecture. Evaluate against networking team capacity and Confluent account team for sizing.

Verify current state: nslookup lkc-\<id\>.azure.confluent.cloud. A 10.x.x.x response confirms Private Link is active. A public IP confirms exposure to the ILB timeout risk.

### **4.2  Access Transparency Enrollment**

Request enrollment in Confluent's Access Transparency program (Limited Availability as of early 2026\) via your account team. This provides an audit log of when Confluent personnel access the cluster for maintenance, enabling correlation of connection events with Confluent-side activity. Required for FSI compliance posture.

## **SLA-Tier Configuration Overlay**

Settings that change per SLA tier. Critical tier values are used throughout this document (fraud detection use case).

| Property | Critical (<10ms) | Standard (<100ms) | Best-Effort (async) |
| :---- | :---- | :---- | :---- |
| `linger.ms` | 0 | 5-10 | 20-50 |
| `batch.size` | 16384 | 32768-65536 | 131072 |
| `compression.type` | none | lz4 | zstd |
| `fetch.min.bytes` | 1 | 1024 | 4096 |
| `fetch.max.wait.ms` | 0 | 500 | 1000 |
| `max.poll.records` | 10 | 100-500 | 500-1000 |
| GC | ZGC | G1GC | G1GC |

# **Complete Configuration Reference**

## **Producer — Recommended Settings**

Apply to: Kafka producer ConfigMap / application.properties

\# Batching

linger.ms=0

batch.size=16384

compression.type=none                   \# see decision tree below

\# Timeouts

request.timeout.ms=30000

delivery.timeout.ms=180000

max.block.ms=5000

\# Reliability

acks=all

retries=10

retry.backoff.ms=250

enable.idempotence=true

\# Connection

socket.keepalive.enable=true

connections.max.idle.ms=180000

reconnect.backoff.ms=100

reconnect.backoff.max.ms=1000

max.in.flight.requests.per.connection=5

metadata.max.age.ms=60000

### **Compression Decision Tree**

- **Low TPS, latency-critical (fraud detection):** `compression.type=none` — compression overhead exceeds benefit; records are small and sparse.
- **Moderate throughput (100-10K TPS):** `compression.type=lz4` — best speed-to-ratio trade-off; low CPU overhead.
- **Storage-constrained or high fan-out:** `compression.type=zstd` — 3-5x compression ratio; higher CPU but significant storage savings.
- **Avoid `gzip`** — highest CPU cost, worst throughput (~830 msg/s vs ~3400 for lz4). Only if external compatibility requires it.

## **Consumer — Recommended Settings**

Apply to: Kafka consumer ConfigMap / application.properties

\# Fetch

fetch.min.bytes=1

fetch.max.wait.ms=0

max.poll.records=10

\# Heartbeat

heartbeat.interval.ms=3000

session.timeout.ms=45000

max.poll.interval.ms=600000

\# Offset

enable.auto.commit=false

\# Rebalance

partition.assignment.strategy=org.apache.kafka.clients.consumer.CooperativeStickyAssignor

group.instance.id=${POD\_NAME}

\# Connection

socket.keepalive.enable=true

connections.max.idle.ms=180000

reconnect.backoff.max.ms=1000

## **Topic Configuration (via Confluent CLI)**

Apply to: fraud-events and related high-priority topics

min.insync.replicas=2

unclean.leader.election.enable=false

retention.ms=3600000

# **Next Steps**

## **This Week**

1. Update producer and consumer ConfigMaps with Phase 1 settings (batch.size, socket.keepalive.enable, connections.max.idle.ms, reconnect.backoff.max.ms, fetch.max.wait.ms).

2. Rolling restart producer and consumer pods.

3. Open Confluent support ticket with exact UTC timestamps of all observed connection errors. Request confirmation of broker maintenance activity and preferred window enrollment.

4. Verify nslookup result for lkc-\*.azure.confluent.cloud to confirm Private Link status.

5. Subscribe to status.confluent.cloud for Azure region.

## **Next Sprint**

6. Implement decoupled poll/process pattern in fraud consumer application.

7. Implement consumer.pause()/resume() for backpressure handling.

8. Implement graceful shutdown hook.

9. Convert fraud consumer Deployment to StatefulSet with group.instance.id.

10. Add PodDisruptionBudget.

11. Pin AKS maintenance window via az aks maintenanceconfiguration add.

## **This Quarter**

12. Complete Private Link assessment and migration plan.

13. Request Access Transparency enrollment from Confluent account team.

14. Coordinate CooperativeStickyAssignor rollout with maintenance window.

15. Instrument client JMX metrics: connection-count, fetch-latency-avg, records-lag-max.

| FSI Compliance Note Access Transparency (audit log of Confluent personnel access) and a documented maintenance window SLA are both components of a defensible FSI operational posture. Both require engagement with the Confluent account team rather than self-service configuration. Initiate that conversation in parallel with the Phase 1 config changes. |
| :---- |

