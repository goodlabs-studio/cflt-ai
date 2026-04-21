---
title: AKS Kafka Tuning
tags: [kafka azure kubernetes cfk performance]
sources:
  - https://learn.microsoft.com/en-us/azure/aks/kafka-overview
  - https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/storage-optimized/lsv3-series
  - https://learn.microsoft.com/en-us/azure/virtual-machines/disks-types
  - https://docs.confluent.io/operator/current/co-plan.html
related: [concepts/producer-batching-config, concepts/fsi-data-streaming-platform, concepts/sla-tiers, patterns/dr-cluster-linking, concepts/consumer-lag-monitoring]
confidence: medium
last_updated: 2026-04-17
---

# AKS Kafka Tuning

## Summary

End-to-end performance tuning pattern for Apache Kafka on Azure Kubernetes Service (AKS), covering VM SKU selection, storage tiering (Premium SSD v2, Ultra Disk, ephemeral NVMe), network configuration, broker JVM and config tuning, OS-level sysctl parameters, CFK/Strimzi operator specifics, and monitoring. The primary trade-off is raw I/O performance (Lsv3 with local NVMe) versus operational simplicity and durability (Edsv5 with Premium SSD v2). For most production workloads, Premium SSD v2 on Edsv5-series VMs provides the best price-performance ratio.

## Pattern

### 1. VM SKU Selection

Three VM families matter for Kafka on AKS. The right choice depends on whether your bottleneck is memory/page-cache, storage I/O, or remote disk throughput.

#### Edsv5 -- Memory-Optimized (Recommended Default)

| SKU | vCPUs | RAM | Temp Disk | Network | Uncached Remote IOPS | Notes |
|-----|-------|-----|-----------|---------|----------------------|-------|
| Standard_E8ds_v5 | 8 | 64 GiB | 300 GiB | 12,500 Mbps | 12,800 | Small clusters, 1 broker/node |
| Standard_E16ds_v5 | 16 | 128 GiB | 600 GiB | 12,500 Mbps | 25,600 | Sweet spot for medium clusters |
| Standard_E32ds_v5 | 32 | 256 GiB | 1,200 GiB | 16,000 Mbps | 51,200 | Large clusters, high partition counts |

High memory-to-core ratio (8 GiB/vCPU) gives ample page cache headroom. Supports Premium Storage, Accelerated Networking, and Live Migration. Intel Ice Lake / Emerald Rapids processors.

#### Lsv3 -- Storage-Optimized (Extreme I/O)

| SKU | vCPUs | RAM | NVMe Disks | NVMe IOPS | NVMe Throughput | Network |
|-----|-------|-----|------------|-----------|-----------------|---------|
| Standard_L8s_v3 | 8 | 64 GiB | 1x 1.92 TB | 400,000 | 2,000 MB/s | 12,500 Mbps |
| Standard_L16s_v3 | 16 | 128 GiB | 2x 1.92 TB | 800,000 | 4,000 MB/s | 12,500 Mbps |
| Standard_L32s_v3 | 32 | 256 GiB | 4x 1.92 TB | 1.5M | 8,000 MB/s | 16,000 Mbps |
| Standard_L48s_v3 | 48 | 384 GiB | 6x 1.92 TB | 2.2M | 14,000 MB/s | 24,000 Mbps |
| Standard_L64s_v3 | 64 | 512 GiB | 8x 1.92 TB | 2.9M | 16,000 MB/s | 30,000 Mbps |
| Standard_L80s_v3 | 80 | 640 GiB | 10x 1.92 TB | 3.8M | 20,000 MB/s | 32,000 Mbps |

Directly-mapped local NVMe delivers orders of magnitude better IOPS and latency than any network-attached disk. **Local NVMe is ephemeral -- data is lost on VM deallocation.** You must rely entirely on Kafka replication (RF=3, `min.insync.replicas=2`) for durability. Lsv3 does not support Premium Storage caching or Live Migration.

#### Ebsv5 -- Storage Throughput-Optimized

| SKU | vCPUs | RAM | Network | Remote Storage IOPS | Remote Throughput |
|-----|-------|-----|---------|---------------------|-------------------|
| Standard_E8bs_v5 | 8 | 64 GiB | 12,500 Mbps | 12,800 | 400 MB/s |
| Standard_E16bs_v5 | 16 | 128 GiB | 12,500 Mbps | 25,600 | 600 MB/s |
| Standard_E32bs_v5 | 32 | 256 GiB | 16,000 Mbps | 51,200 | 865 MB/s |

Higher remote disk throughput caps than standard Edsv5. Consider when Premium SSD v2 or Ultra Disk throughput is the bottleneck rather than IOPS.

#### Ddsv5 -- General Purpose (Budget)

| SKU | vCPUs | RAM | Network | Brokers/Node |
|-----|-------|-----|---------|--------------|
| Standard_D8ds_v5 | 8 | 32 GiB | 12,500 Mbps | 1-3 |
| Standard_D16ds_v5 | 16 | 64 GiB | 12,500 Mbps | 3-6 |

From Microsoft's AKS Kafka guide for small-to-medium clusters. Only 4 GiB/vCPU -- leaves less page cache after JVM heap allocation. Fine for dev/staging; tight for production.

### 2. Storage Configuration

#### Disk Type Comparison

| Property | Premium SSD v2 | Ultra Disk | Ephemeral NVMe (Lsv3) |
|----------|---------------|------------|----------------------|
| Max IOPS | 80,000/disk | 400,000/disk | 400,000+ per NVMe device |
| Max Throughput | 1,200 MB/s | 10,000 MB/s | 2,000+ MB/s per device |
| Latency | Sub-millisecond | Sub-millisecond | Sub-100 microsecond |
| Persistent | Yes (network-attached) | Yes (network-attached) | No (ephemeral) |
| Flexible Sizing | IOPS/throughput/capacity independent | IOPS/throughput/capacity independent | Fixed per SKU |
| Cost Model | Per-GiB + provisioned IOPS + throughput | Per-GiB + provisioned IOPS + throughput + VM reservation | Included in VM price |

**Recommendation hierarchy:**

1. **Premium SSD v2** -- Best default. Independent IOPS/throughput/capacity tuning without fixed disk tiers. Sub-millisecond latency. Cost-efficient because you provision exactly the IOPS you need.
2. **Ultra Disk** -- Only when you need >80K IOPS or >1,200 MB/s per disk. Adds a per-vCPU reservation fee on the VM. Kafka rarely needs this.
3. **Ephemeral NVMe** -- Highest raw performance, lowest latency. Only viable when Kafka replication provides your durability guarantee.

#### IOPS and Throughput Sizing Per Broker

From Microsoft's AKS Kafka deployment guide (starting points):

| Cluster Size | Disk Size | IOPS | Bandwidth |
|-------------|-----------|------|-----------|
| Small (3-9 brokers) | 1 TB | 5,000 | 250 MB/s |
| Medium (10-19 brokers) | 2 TB | 10,000 | 500 MB/s |
| Large (20+ brokers) | 4 TB | 20,000 | 1,000 MB/s |

Calculate actual requirements from: `(peak_produce_MB/s + peak_replicate_MB/s + peak_consume_MB/s) * retention_hours * 3600 / disk_count` for capacity.

#### StorageClass Configuration

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: kafka-premium-ssd-v2
provisioner: disk.csi.azure.com
parameters:
  skuName: PremiumV2_LRS              # Premium SSD v2
  DiskIOPSReadWrite: "5000"           # Tune to workload; start at 5K for small clusters
  DiskMBpsReadWrite: "250"            # Tune to workload
  cachingMode: None                    # CRITICAL: Premium SSD v2 does NOT support host caching
  fsType: ext4                         # ext4 preferred over xfs for Kafka sequential writes
reclaimPolicy: Retain                  # Retain disks on PVC deletion for data recovery
allowVolumeExpansion: true             # Allow online disk expansion
volumeBindingMode: WaitForFirstConsumer  # CRITICAL: ensures disk created in same AZ as pod
```

`cachingMode: None` is mandatory for Premium SSD v2. Without it, AKS attaches the disk with read-only host caching, which is unsupported and causes silent performance degradation.

#### JBOD / Multiple `log.dirs`

Strimzi and CFK both support JBOD storage, mapping to multiple `log.dirs` entries. Each disk gets its own PVC:

```yaml
storage:
  type: jbod
  volumes:
    - id: 0
      type: persistent-claim
      size: 500Gi
      deleteClaim: false
      class: kafka-premium-ssd-v2
    - id: 1
      type: persistent-claim
      size: 25Gi
      kraftMetadata: shared
      deleteClaim: false
      class: kafka-premium-ssd-v2
```

Kafka stripes partitions across `log.dirs`, so 2-4 disks per broker doubles to quadruples I/O parallelism. On Lsv3, each NVMe device maps naturally to a separate `log.dir`.

### 3. Network Configuration

#### Azure ILB Idle Timeout and TCP Keep-Alive

Azure Internal Load Balancer kills idle TCP connections at **4 minutes** with no RST/FIN — the Kafka client never learns the connection is dead. The next write/read attempt triggers reconnect. With `reconnect.backoff.max.ms` at the default 10 seconds, this creates detection blind spots for latency-sensitive workloads.

**Client-side mitigation (apply to all producers and consumers):**

```properties
socket.keepalive.enable=true         # OS-level TCP keepalive probes — default is FALSE
connections.max.idle.ms=180000       # 3 min — recycle connections before ILB 4-min kill
reconnect.backoff.max.ms=1000        # cap at 1s — default 10s is too slow for fraud detection
```

**Infrastructure-side mitigation:**

```yaml
# Azure LB annotation — minimum configurable idle timeout is 4 min
metadata:
  annotations:
    service.beta.kubernetes.io/azure-load-balancer-tcp-idle-timeout: "4"
```

**Best mitigation: Private Link.** Private Link eliminates the ILB hop entirely — traffic stays on Azure backbone. See [Private Networking](../concepts/private-networking.md) (stub) for setup.

#### Follower Fetching (`client.rack`)

Kafka consumers can read from the nearest ISR replica (follower fetching) instead of always reading from the leader. This reduces cross-AZ data transfer costs and latency.

```properties
# Consumer config — set to match the consumer's availability zone
client.rack=azure-eastus2-az1
```

Requires broker-side configuration:
- `replica.selector.class=org.apache.kafka.common.replica.RackAwareReplicaSelector`
- Confluent Cloud Dedicated clusters enable this by default.
- CFK/CP: Set `broker.rack` via topology key and enable `RackAwareReplicaSelector`.

In AKS, derive `client.rack` from the node's `topology.kubernetes.io/zone` label via the Kubernetes downward API:

```yaml
env:
  - name: KAFKA_CLIENT_RACK
    valueFrom:
      fieldRef:
        fieldPath: metadata.labels['topology.kubernetes.io/zone']
```

#### Azure CNI vs Kubenet

Azure CNI is required for production Kafka. Kubenet adds a NAT hop for pod-to-pod traffic, increasing latency and complicating `advertised.listeners`.

Recommended: **Azure CNI Overlay with Cilium** -- pods get overlay IPs (no VNet IP exhaustion), and Cilium's eBPF dataplane bypasses iptables for higher throughput.

```bash
az aks create \
  --network-plugin azure \
  --network-plugin-mode overlay \
  --network-dataplane cilium \
  --pod-cidr 10.244.0.0/16 \
  ...
```

#### Accelerated Networking

Must be enabled on all broker node pools. Bypasses the host networking stack via SR-IOV for near-bare-metal latency. All Edsv5 and Lsv3 SKUs support it. Verify:

```bash
az aks nodepool show --cluster-name <cluster> --name kafka-brokers \
  --resource-group <rg> --query "enableAcceleratedNetworking"
```

#### Proximity Placement Groups

For latency-sensitive workloads (sub-millisecond SLA tiers), co-locate broker VMs within a proximity placement group to minimize inter-node network hops. Trade-off: reduces AZ spread, so only use within a single AZ for a subset of brokers if needed.

#### External Access

| Method | Pros | Cons |
|--------|------|------|
| LoadBalancer (per-broker) | Clean DNS, TLS termination, static IPs | Expensive; Azure Basic LB deprecated Sept 2025 |
| NodePort | Cheaper, simpler | Port conflicts, exposes node IPs, harder TLS |
| Ingress (TCP/SNI) | Single LB | Complex; not natively supported for TCP by most ingress controllers |

Use Azure Standard Load Balancer with per-broker `Service` of type `LoadBalancer` for external access. For internal-only clusters, use `ClusterIP` listeners.

### 4. AKS Node Pool Design

#### Dedicated Pools

| Node Pool | Purpose | Recommended SKU | Min Nodes |
|-----------|---------|-----------------|-----------|
| `kafka-brokers` | Broker pods | Standard_E16ds_v5 | 3 (one per AZ) |
| `kafka-controllers` | KRaft controller pods | Standard_E8ds_v5 | 3 (one per AZ) |
| `kafka-connect` | Connect workers | Standard_D8ds_v5 | 2+ |
| `system` | System pods, operators, monitoring | Standard_D4ds_v5 | 3 |

Taint broker/controller pools (`app=kafka:NoSchedule`) with matching tolerations to prevent non-Kafka pods from landing on those nodes. This is the primary mechanism for page cache isolation.

#### AZ Spread with Topology Constraints

```yaml
topologySpreadConstraints:
  - labelSelector:
      matchLabels:
        kafkaRole: broker
    maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
  - labelSelector:
      matchLabels:
        kafkaRole: broker
    maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: ScheduleAnyway
```

Enable rack awareness so Kafka distributes replicas across AZs:

```yaml
rack:
  topologyKey: topology.kubernetes.io/zone
```

### 5. Broker JVM Tuning

#### Heap and GC Configuration

Based on LinkedIn's production configuration (cited in Microsoft's AKS Kafka guide). Each broker pod reserves ~8 GiB (6 GiB heap + 2 GiB off-heap). Controllers reserve ~4 GiB (3 GiB heap + 1 GiB off-heap).

```yaml
jvmOptions:
  "-Xms": "6g"
  "-Xmx": "6g"
  "-XX":
    UseG1GC: "true"
    MaxGCPauseMillis: "20"
    InitiatingHeapOccupancyPercent: "35"
    G1HeapRegionSize: "16M"
    MetaspaceSize: "96m"
    MinMetaspaceFreeRatio: "50"
    MaxMetaspaceFreeRatio: "80"
    ExplicitGCInvokesConcurrent: "true"
```

| GC Option | When to Use |
|-----------|-------------|
| G1GC (`-XX:+UseG1GC`) | Default for Kafka. Predictable pause times, good for heaps 4-8 GiB. |
| ZGC (`-XX:+UseZGC`) | Heaps >8 GiB with strict latency requirements. Sub-millisecond pauses. Higher CPU overhead. |
| Parallel GC (`-XX:+UseParallelGC`) | Batch/throughput workloads where pause time is acceptable. |

#### Page Cache Rule of Thumb

Leave at least 60% of node memory for OS page cache. Kafka relies on the page cache for consumer read performance near the log head.

| Node SKU | RAM | Brokers | JVM Reserved | Available for Page Cache |
|----------|-----|---------|-------------|------------------------|
| Standard_E16ds_v5 | 128 GiB | 1 | 8 GiB | ~120 GiB |
| Standard_E16ds_v5 | 128 GiB | 2 | 16 GiB | ~112 GiB |
| Standard_D8ds_v5 | 32 GiB | 1 | 8 GiB | ~24 GiB (tight) |

One broker per node is strongly preferred for production to eliminate page cache contention.

### 6. Broker Configuration Parameters

```properties
# Threading -- tune to vCPU count
num.network.threads=8              # Set to vCPU count or slightly less
num.io.threads=16                  # Set to 2x vCPU count or match disk_count * 2
queued.max.requests=500            # Default; increase if network threads saturate

# Socket buffers -- critical for 10+ Gbps networks
socket.send.buffer.bytes=1310720   # 1.25 MiB (default 100 KiB is too small)
socket.receive.buffer.bytes=1310720

# Replication
num.replica.fetchers=4             # Default 1; increase to 4-8 for high partition counts
replica.fetch.max.bytes=10485760   # 10 MiB; increase for large message workloads
replica.fetch.wait.max.ms=500

# Durability
default.replication.factor=3
min.insync.replicas=2
offsets.topic.replication.factor=3
transaction.state.log.replication.factor=3
transaction.state.log.min.isr=2

# Log management
log.segment.bytes=1073741824       # 1 GiB segments
log.retention.hours=168            # 7 days default; tune to workload
log.retention.check.interval.ms=300000
```

### 7. OS-Level Tuning (sysctl)

Apply via init containers or DaemonSet on broker nodes:

```properties
# Minimize swapping -- Kafka must not swap
vm.swappiness=1

# Dirty page ratios -- control write-back behavior for sequential I/O
vm.dirty_ratio=80                  # Allow up to 80% of memory as dirty pages before forced flush
vm.dirty_background_ratio=5        # Start background flush at 5% dirty

# Network buffer sizing -- match socket buffer config
net.core.rmem_max=16777216         # 16 MiB max receive buffer
net.core.wmem_max=16777216         # 16 MiB max send buffer
net.core.rmem_default=1310720
net.core.wmem_default=1310720
net.ipv4.tcp_rmem=4096 1310720 16777216
net.ipv4.tcp_wmem=4096 1310720 16777216

# Connection backlog
net.core.somaxconn=32768
net.core.netdev_max_backlog=16384

# File descriptors -- Kafka opens many segment files
fs.file-max=1000000
```

Example init container for sysctl tuning:

```yaml
initContainers:
  - name: sysctl-tuning
    image: busybox:1.36
    command:
      - sh
      - -c
      - |
        sysctl -w vm.swappiness=1
        sysctl -w vm.dirty_ratio=80
        sysctl -w vm.dirty_background_ratio=5
        sysctl -w net.core.rmem_max=16777216
        sysctl -w net.core.wmem_max=16777216
    securityContext:
      privileged: true
```

### 8. CFK on AKS

#### CFK Operator Deployment

CFK 3.2 supports Kubernetes 1.27-1.35. Deploy with Helm:

```bash
helm repo add confluentinc https://packages.confluent.io/helm
helm repo update
helm install confluent-operator confluentinc/confluent-for-kubernetes \
  --namespace confluent --create-namespace
```

#### CFK Production Sizing

From Confluent's deployment planning guide:

| Component | Prod Pods | CPU (per pod) | Memory (per pod) | Storage |
|-----------|-----------|---------------|------------------|---------|
| KRaft Controllers | 5 | 1 core | 4 GiB | 64 GiB SSD |
| Kafka Brokers | 3+ | 8 cores | 64 GiB | 1-12 TB |
| Connect Workers | 2+ | 6 cores | 12 GiB | 50 GiB |
| Schema Registry | 2 | 1 core | 2 GiB | -- |
| ksqlDB | 2 | 2 cores | 16 GiB | 100 GiB SSD |
| Control Center | 1 | 4 cores | 8 GiB | 200 GiB SSD |

#### Example CFK Kafka CR

```yaml
apiVersion: platform.confluent.io/v1beta1
kind: Kafka
metadata:
  name: kafka
  namespace: confluent
spec:
  replicas: 3
  image:
    application: confluentinc/cp-server:7.8.0
    init: confluentinc/confluent-init-container:2.10.0
  dataVolumeCapacity: 1Ti
  storageClass:
    name: kafka-premium-ssd-v2
  podTemplate:
    resources:
      requests:
        cpu: "4"
        memory: "16Gi"
      limits:
        cpu: "8"
        memory: "32Gi"             # Do NOT set equal to requests; leave headroom for page cache
    affinity:
      nodeAffinity:
        requiredDuringSchedulingIgnoredDuringExecution:
          nodeSelectorTerms:
            - matchExpressions:
                - key: app
                  operator: In
                  values: ["kafka"]
    tolerations:
      - key: app
        operator: Equal
        value: kafka
        effect: NoSchedule
    topologySpreadConstraints:
      - labelSelector:
          matchLabels:
            platform.confluent.io/type: kafka
        maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
  oneReplicaPerNode: true
  configOverrides:
    server:
      - "num.network.threads=8"
      - "num.io.threads=16"
      - "socket.send.buffer.bytes=1310720"
      - "socket.receive.buffer.bytes=1310720"
      - "num.replica.fetchers=4"
      - "min.insync.replicas=2"
      - "default.replication.factor=3"
    jvm:
      - "-Xms6G"
      - "-Xmx6G"
      - "-XX:+UseG1GC"
      - "-XX:MaxGCPauseMillis=20"
      - "-XX:InitiatingHeapOccupancyPercent=35"
      - "-XX:G1HeapRegionSize=16M"
```

#### Pod Disruption Budgets

For Kafka with RF=3 and `min.insync.replicas=2`:

```yaml
spec:
  podTemplate:
    podDisruptionBudget:
      maxUnavailable: 1            # Only 1 broker down at a time
```

For larger clusters (6+ brokers), `maxUnavailable: 2` is acceptable.

#### Immutable CFK Settings

These cannot be changed after initial deployment -- plan carefully:

- RBAC enablement
- TLS certificate mechanisms
- Authentication mechanisms
- Storage classes
- External access methods for Kafka brokers

### 9. Monitoring

#### Azure-Native Stack

- **Azure Monitor for containers** -- Node-level CPU, memory, disk I/O, network metrics
- **Azure Managed Prometheus** + **Azure Managed Grafana** -- JMX metrics via Prometheus exporter sidecar
- Key Azure disk metrics: `DiskIOPSConsumedPercentage`, `DiskBandwidthConsumedPercentage` (alerts at 80%)

#### Prometheus/Grafana Stack

Deploy JMX Exporter as a sidecar or use Strimzi's built-in Kafka Exporter:

| Metric | Alert Threshold | Meaning |
|--------|----------------|---------|
| `kafka_server_UnderReplicatedPartitions` | > 0 for 5 min | ISR shrinkage; possible disk or network issue |
| `kafka_server_OfflinePartitionsCount` | > 0 | Partitions without a leader |
| `kafka_consumer_group_lag` | Workload-dependent | Consumer falling behind |
| `kafka_network_RequestMetrics_TotalTimeMs` | p99 > 100ms | Broker request latency degradation |
| `jvm_gc_pause_seconds` | p99 > 50ms | GC pauses impacting broker |
| `kafka_server_ReplicaFetcherManager_MaxLag` | Growing trend | Replication falling behind |

## When to Use

- Self-managed Kafka (Strimzi or CFK) on AKS requiring full configuration control
- FSI workloads where regulatory requirements prevent fully managed services
- Multi-region architectures combining AKS-hosted Kafka with Confluent Cloud via [Cluster Linking](../patterns/dr-cluster-linking.md)
- Workloads needing specific Kafka features (tiered storage, custom plugins) not available in Azure Event Hubs
- Teams with existing Kubernetes operational expertise on Azure

## Caveats

- **Premium SSD v2 limitations:** Cannot be used as OS disks. Only available with zonal VMs (must use availability zones, not availability sets). No host caching.
- **Lsv3 ephemeral storage risk:** Data loss on any VM stop/dealloc/maintenance event. Not suitable for long retention unless you accept full partition rebuild times.
- **VM-level IOPS caps:** Azure enforces layered throttling at both disk and VM levels. Standard_E16ds_v5 uncached IOPS limit is 25,600 -- if you attach three disks each provisioned at 10,000 IOPS, you hit the VM cap before the disk cap.
- **Kubernetes page cache sharing:** No cgroup-level isolation for page cache. The only mitigation is workload isolation via dedicated node pools. Never set memory limits equal to requests on broker pods -- the OOM killer activates before the node can use free memory for page cache.
- **Pod eviction during AKS upgrades:** Without PDBs and Strimzi Drain Cleaner (or CFK equivalent), multiple broker pods can be evicted simultaneously during node pool upgrades. Use `--max-surge 1` on node pool upgrades and `maxUnavailable: 1` PDBs.
- **DNS resolution latency:** Enable NodeLocal DNSCache (`--enable-node-local-dns`), set `ndots: 2` in pod DNS config, and scale CoreDNS replicas for large clusters.
- **Azure Basic LB deprecation:** Azure Basic Load Balancer is deprecated as of September 2025. Use Standard Load Balancer for all new deployments.
- **Microsoft sizing tables are starting points**, not benchmarked production numbers. Load test with actual message sizes, partition counts, and consumer fan-out before committing to a storage configuration.

## Related

- [Producer Batching Config](../concepts/producer-batching-config.md) -- Client-side tuning that pairs with broker-side socket buffer and thread config
- [FSI Data Streaming Platform](../concepts/fsi-data-streaming-platform.md) -- Architecture context for financial services deployments on AKS
- [SLA Tiers](../concepts/sla-tiers.md) -- Latency tier definitions (sub-ms, <10ms, <100ms) that drive VM and storage selection
- [DR with Cluster Linking](../patterns/dr-cluster-linking.md) -- Cross-region replication between AKS-hosted clusters
- [Consumer Lag Monitoring](../concepts/consumer-lag-monitoring.md) -- Monitoring patterns referenced in the observability section
