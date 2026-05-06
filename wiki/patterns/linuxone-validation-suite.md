---
title: LinuxONE Kafka Validation & Benchmarking Suite
tags: [kafka linuxone ibm s390x kraft validation benchmark fips fsi]
sources:
  - https://docs.confluent.io/platform/current/installation/versions-interoperability.html
  - https://docs.confluent.io/platform/current/kafka-metadata/kraft.html
  - https://github.com/confluentinc/ducktape
  - https://github.com/openmessaging/openmessaging-benchmark
  - https://www.ibm.com/products/linuxone/ai-processor
  - https://github.com/IBM/zDNN
  - https://www.ibm.com/support/pages/node/7262649
related: [concepts/linuxone-kafka-integration, concepts/sla-tiers, concepts/fsi-compliance, patterns/linuxone-kafka-tuning, patterns/linuxone-flink-validation-tuning, patterns/aks-kafka-tuning]
confidence: medium
last_updated: 2026-05-05
last_validated: 2026-05-05
validated_via: [confluent-docs (versions-interoperability.html, producer-configs.html), context7 (/websites/javadoc_io_doc_org_apache_kafka_kafka-clients_4_2_0)]
---

# LinuxONE Kafka Validation & Benchmarking Suite

## Summary

Aggressive validation and benchmarking plan for Apache Kafka / Confluent Platform 8.2 on IBM LinuxONE Emperor 5 (Telum II / s390x). Replaces the legacy ZooKeeper-era plan with a KRaft-native baseline, mTLS + OAUTHBEARER as the security default (Kerberos retained as fallback for legacy MDS/AD environments), and adds LinuxONE-specific tests that the canonical x86 plans do not cover: HiperSockets latency floor, Crypto Express FIPS 140-3 throughput, SMC-D for in-memory client traffic, container density on z/VM and KVM-on-LPAR, and NNPA (Telum II on-chip AI) co-residency under load. Test orchestration uses Ducktape with s390x runners; load generation uses `kafka-producer-perf-test`, `kafka-consumer-perf-test`, OpenMessaging Benchmark, and a custom HiperSockets micro-benchmark.

> Confluent ships Docker images for s390x but does not provide architecture-specific support except via the IBM "Confluent Platform for Z and LinuxONE" bundle — confirm support posture with IBM/Confluent before standing up production.

## Pattern

### 1. Test Topology

Three concurrent topologies cover 90% of FSI scenarios:

| Topology | Frame Layout | Purpose |
|----------|--------------|---------|
| **Single-frame, multi-LPAR** | 3 brokers + 3 KRaft controllers across 6 LPARs on one Emperor 5; client LPAR co-resident | Latency floor, HiperSockets validation, sub-ms ceiling tests |
| **Dual-frame DR** | 3-broker primary + 3-broker DR across two frames in same data center; cross-frame OSA-Express7S 25 GbE | Cluster Linking failover, RPO=0 attempt for compliance tier |
| **Hybrid edge** | 3 brokers on LinuxONE; 3 producers on x86 RHEL via OSA / SMC-R / RoCE | Mainframe-bridge SLA validation; the canonical FSI MQ-bridge pattern |

All topologies run **KRaft mode** (Confluent Platform 8.0+ requires it; ZooKeeper is gone). Co-locate KRaft controllers on dedicated LPARs — never share with brokers in production validation.

### 2. Installation & Upgrade

- **Cluster size:** 3 brokers + 3 dedicated KRaft controllers minimum. For partition scale tests, jump to 6+6.
- **Security profile:** mTLS broker↔broker, mTLS broker↔client, OAUTHBEARER for principals (matches ADR-006). Validate with a **Kerberos overlay** test only if integrating with legacy MDS/AD — otherwise skip; Kerberos is no longer the FSI default.
- **FIPS:** RHEL 9 FIPS mode + Crypto Express 8S (CEX8S) hardware crypto. Validate FIPS 140-3 (the 140-2 standard sunset by NIST in 2026; CEX8S supports 140-3). Confirm `update-crypto-policies --set FIPS:OSPP` and that the JVM uses the Bouncy Castle FIPS provider.
- **Validation gates:** before declaring install complete, all of:
  - `kafka-cluster.sh cluster-id` returns identical UUID on every broker
  - `kafka-metadata-quorum.sh describe --status` shows all 3 controllers in the voter set, no observer drift
  - `kafka-features.sh describe` shows `metadata.version` at the cluster's negotiated KRaft level
  - mTLS handshake succeeds via `openssl s_client` with FIPS-only cipher suite (`TLS_AES_256_GCM_SHA384`)
  - OAUTHBEARER token introspection round-trip < 50 ms

**Rolling upgrades** under load: drive 50% of throughput target via `kafka-producer-perf-test` while bouncing one broker at a time. URPs and OOSR must return to zero within 60 s of each restart. Use Ansible with `serial: 1` and a `wait_for` on `UnderReplicatedPartitions` JMX gauge.

### 3. Functional Tests

Eight modules. Each yields a pass/fail; partial passes block tier-up.

#### 3.1 Topic CRUD
- 50 topics across compatibility/partition matrices: `{6, 12, 24} × {RF=3, MIR=2}`.
- Alter retention, segment.bytes, compression.type live.
- Delete with `--if-exists`, recreate identical names within 5 s; controller must not stale.

#### 3.2 RBAC + MDS
- Roles: `developer-read`, `developer-write`, `connect-admin`, `cluster-admin`. Use the standard role-bindings module from the FSI DSP.
- Validate negative cases: read-only principal denied on produce, write principal denied on consumer-group commit outside its scope.
- Audit log forwarding to SIEM ([Audit Log SIEM Integration](audit-log-siem-integration.md)) must capture every denial within 30 s.

#### 3.3 Connect (distributed mode on LinuxONE)
- Confluent-certified connectors only: IBM MQ Source, JDBC Sink (DB2 z/OS via Hipersockets), HTTP Sink, S3 Sink (object storage off-platform).
- 5 connectors / 4 tasks each. Pause/resume, restart-tasks-on-failure, kill a worker — all tasks must rebalance within `scheduled.rebalance.max.delay.ms` (default 5 min; tune to 60 s for FSI).

#### 3.4 Schema Registry
- Avro and Protobuf both. JSON Schema only on dev tier.
- Compatibility regression: register N+1 schema with deliberate forbidden change (remove required field) under FULL_TRANSITIVE — must be rejected.
- Two-pass registration (the `fsi-dsp` pattern): first pass without check, second pass with `compatibility.level` enforced.

#### 3.5 Tiered Storage
- Topic with `segment.bytes=1073741824` (1 GiB), `retention.ms=604800000` (7d), `confluent.tier.enable=true`, target = IBM Cloud Object Storage on s390x or off-platform AWS S3 via OSA.
- Produce ≥ 5 segments worth (~5 GiB/partition); confirm cold-tier offload via `kafka-tier-storage-tool`.
- **L1-specific:** measure cold-read latency over OSA vs warm-read from local FS-cache; warm read should be < 1 ms, cold read should be < 250 ms for objects under 64 MiB.

#### 3.6 Cluster Linking
- Two 3-broker clusters, same frame initially (then dual-frame in the second pass). Bidirectional link.
- Run [DR — Cluster Linking](dr-cluster-linking.md) failover script end-to-end with `fsi-dr.sh`.
- **L1-specific gate:** verify the link traverses HiperSockets (intra-frame) or SMC-D (cross-LPAR same-frame) — not the OSA NIC. Use `tcpdump -i hsi0` to confirm.

#### 3.7 KRaft Controller Consistency
- 3 controllers, 100 topics with varied configs. Stop the active controller mid-DDL, allow election, restart, replay metadata log.
- Validate: post-restart `__cluster_metadata` topic snapshot offset matches active controller's high watermark; no metadata divergence.
- Failure injection: corrupt one controller's snapshot file — the controller must refuse to start and log a recoverable error pointing to `kafka-storage.sh format --recover`.

#### 3.8 Self-Balancing Cluster (SBC)
- 4-broker cluster, 30 topics × 12 partitions × RF=3.
- `confluent.balancer.heal.broker.failure.threshold.ms=600000` (10 min) per the legacy plan; tighten to 120 s for critical-tier.
- Stop one broker; SBC must rebalance to even partition distribution (variance ≤ 5%) within threshold.

### 4. Availability & Consistency

- **Power-loss simulation:** for KRaft, abrupt LPAR fence via z/VM `CP FORCE` mid-write. Producer with `acks=all` + `enable.idempotence=true` must produce zero duplicates and zero losses.
- **Network partition:** isolate one broker via OSA filter rules. Followers must drop from ISR within `replica.lag.time.max.ms` (default 30 s); producer with `acks=all` and `min.insync.replicas=2` must continue if 2 of 3 remain.
- **Disk failure:** scratch one broker's log dir. With `log.dirs` set to a single mount, the broker must self-fence; with multiple log dirs, only the failed dir goes offline (KIP-589 / KIP-963 — JBOD recovery validated in Kafka 4.0+).
- **GC pause:** force a 4 s G1 pause via `-XX:+PrintGCApplicationStoppedTime` and a synthetic allocation burst. Validate `replica.lag.time.max.ms=30000` is well above 95p pause time.

### 5. Performance & Scale

#### 5.1 Partition Scale
| Target | Brokers | Partitions/Broker | Notes |
|--------|---------|-------------------|-------|
| Baseline | 3 | 1,000 | Conservative; legacy plan number |
| Modern KRaft | 3 | 4,000 | Tested ceiling for KRaft 4.0+ on x86; expected to hold on s390x |
| Stretch | 6 | 8,000 | Push controller heap; expect tuning of `metadata.log.max.snapshot.interval.ms` |

For each: monitor `RequestHandlerAvgIdlePercent` (must stay > 0.3), `NetworkProcessorAvgIdlePercent` (> 0.3), controller heap `< 75%`.

#### 5.2 Throughput
Use `kafka-producer-perf-test.sh` with `--num-records 10000000 --record-size 1024 --throughput -1`.

| Test | Producer | Consumer | Pass criterion (single broker) |
|------|----------|----------|--------------------------------|
| Single-partition latency | 1 thread, `acks=all`, `linger.ms=0` | 1 thread | p99 < 5 ms intra-frame |
| Multi-partition throughput | 16 threads, `linger.ms=20`, `lz4` | 8 threads | ≥ 600 MB/s sustained |
| Compression compare | `lz4`, `zstd`, `snappy` | matching | zstd within 15% of lz4 throughput; gzip excluded |

#### 5.3 OpenMessaging Benchmark
Run the full OMB Kafka workload set on s390x runners. Compare against Edsv5 baseline from [AKS Kafka Tuning](aks-kafka-tuning.md). Expected: LinuxONE matches or exceeds x86 on intra-frame topologies; falls behind on cross-region cloud workloads (where OSA bandwidth dominates).

#### 5.4 LinuxONE-Specific Performance Tests

These are **not** in the canonical Kafka test suites. They are the differentiators that justify the platform.

##### HiperSockets Latency Floor
- Producer in LPAR A, broker in LPAR B, both on the same frame, traffic via `hsi0` (HiperSockets).
- 1 KB message, `acks=all`, `linger.ms=0`, `compression.type=none`.
- **Pass:** p99 producer-to-leader-ack < 800 µs; p999 < 1.5 ms.
- Compare against the same workload over OSA-Express 25 GbE — HiperSockets must show ≥ 5× latency advantage.

##### SMC-D vs HiperSockets vs OSA
SMC-D (Shared Memory Communications - Direct) is z/Linux's userspace shortcut for TCP between LPARs. Test all three transports for a `kafka-producer-perf-test` workload and record p50/p95/p99/p999. Expectation:

| Transport | p99 latency, 1 KB | Throughput |
|-----------|-------------------|------------|
| SMC-D | < 200 µs | ~ 10 GB/s ceiling |
| HiperSockets | < 800 µs | ~ 4 GB/s ceiling |
| OSA-Express7S 25 GbE | 2–5 ms | line rate |

##### Crypto Express FIPS Throughput
- mTLS-only listeners, force CEX8S offload via `setsebool -P kafka_crypto_offload=1` and per-jvm `-Dcom.ibm.crypto.provider.useIBMJCE=true`.
- Run sustained 1 GB/s producer load over mTLS for 30 minutes.
- Monitor `lscrypt -v` queue depth on CEX8S; queue depth > 80% sustained means saturation — add a second adapter or reduce TLS handshakes via long-lived connections.

##### Container Density
- On z/VM: 30 broker containers per LPAR (each broker capped at 4 vCPUs, 16 GiB).
- On Red Hat OpenShift Container Platform on LinuxONE: same density target via OCP nodes pinned to dedicated cores.
- Validate that JVM `-XX:ActiveProcessorCount` is honored under cgroups; container should not see all 60+ cores of the LPAR.

##### Telum II Co-Residency
Run a Flink job invoking the on-chip NNPA AI accelerator (zDNN) for inference on the same LPAR as a Kafka broker. Producer/consumer load must remain unaffected. The accelerator runs on dedicated silicon; the test confirms there is no shared-cache or memory-bandwidth interference.

### 6. Test Tooling

#### 6.1 Ducktape
- Maintain a fork or branch with s390x cluster spec. Confluent's upstream Ducktape now supports multi-arch runners (since 0.12) but service definitions for KRaft-only must be added.
- Emit results to a Kafka topic (`fsi.validation.results.v1`) for trend analysis. Topic schema: SLA-tier classified.

#### 6.2 Apache Kafka System Tests
- Pull a curated subset (replication, transactions, idempotence, ACLs, KRaft snapshot/recovery). Skip ZK-mode tests.
- Run on a Gradle daemon on an s390x build host; build times are roughly 1.4× x86 due to JIT warm-up.

#### 6.3 OpenMessaging Benchmark
- The reference Apache benchmark for cross-platform comparison. Run with `kafka-driver` and a 6-broker / 12-producer / 6-consumer fleet.

#### 6.4 Custom: HiperSockets Micro-Benchmark
A small Go or Java tool that opens a raw socket on `hsi0`, fires varying message sizes, and reports nanosecond-resolution RTT. Lives in `tooling/hipersockets-bench/`. The result is the absolute floor; Kafka latency must be within 2–3× of this floor or there is broker-side overhead to investigate.

### 7. Reporting

Each run produces a single Markdown report committed to `reports/validation/{date}-{topology}-{result}.md` with:
- Build SHA, Confluent Platform version, kernel, glibc, JDK, FIPS status
- Pass/fail per module above
- Latency histograms (HDR Histogram .hgrm output) for §5.2 and §5.4
- Anomaly callouts: any test that failed, recovered, or showed > 3σ deviation from prior run

Historical reports feed a Grafana dashboard sourced from the `fsi.validation.results.v1` topic.

## MCP Validation Notes

| Claim | Source | Result |
|-------|--------|--------|
| Confluent Platform 8.2 is current; CP 8.0+ requires KRaft (no ZooKeeper) | confluent-docs versions-interoperability.html | Confirmed |
| s390x support GA December 2025 for CP for Apache Flink | confluent-docs versions-interoperability.html | Confirmed verbatim: "Linux s390x is supported starting in December 2025... Confluent does not provide support for any issues specific to this architecture. If the same issue occurs with a supported architecture in addition to the unsupported Linux s390x, Confluent provides support" |
| Java 21 recommended for CP 8.2 (17 also supported) | confluent-docs versions-interoperability.html | Confirmed |
| Producer defaults exercised in §5.2 (acks=all, idempotence=true, linger.ms=0/5) | confluent-docs producer-configs.html + context7 javadoc_io kafka-clients 4_2_0 | Confirmed all stated defaults |

## Related

- [LinuxONE Kafka Integration](concepts/linuxone-kafka-integration.md) — the architectural rationale this validates
- [LinuxONE Kafka Tuning](linuxone-kafka-tuning.md) — tuning knobs the suite exercises
- [LinuxONE Flink Validation & Tuning](linuxone-flink-validation-tuning.md) — paired Flink suite with Telum II inference path
- [SLA Tiers](concepts/sla-tiers.md) — pass criteria mapped to tier
- [FSI Compliance](concepts/fsi-compliance.md) — audit-log evidence requirements
- [AKS Kafka Tuning](aks-kafka-tuning.md) — x86 reference for cross-platform comparison
