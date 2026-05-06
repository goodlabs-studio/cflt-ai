---
title: Wiki Index
last_updated: 2026-05-05
---

# cflt-ai Wiki Index

Master index of all articles. One line per article: path | summary | tags.
The LLM maintains this file. Do not edit manually.

## Format

```
[Title](path/to/article.md) — one-line summary — #tag1 #tag2
```

## Concepts

[FSI Data Streaming Platform](concepts/fsi-data-streaming-platform.md) — Universal automation-first platform for governed Kafka/Flink/SR across six deployment models (CC, CFK, CP) — #kafka #fsi #confluent-cloud #confluent-platform #cfk
[SLA Tiers](concepts/sla-tiers.md) — Four tiers (critical, standard, best-effort, compliance) driving governance defaults: compatibility, partitions, retention, DR targets — #kafka #fsi #governance #sla
[Schema Evolution Strategies](concepts/schema-evolution-strategies.md) — Avro-first schema governance with tier-based compatibility modes, evolution runbooks, and versioned topic migration — #schema-registry #avro #fsi #governance
[FSI Compliance](concepts/fsi-compliance.md) — CI/CD audit trail mapping to OCC/FFIEC, PRA, MAS, APRA, OSFI regulatory frameworks — #fsi #compliance #audit #ci-cd #governance
[Cluster Linking Topology](concepts/cluster-linking-topology.md) — Built-in Confluent Server capability for broker-level, offset-preserving topic replication; six topology patterns (active-passive, active-active, hub-spoke, mesh, share, migrate) — #kafka #confluent-cloud #cluster-linking #dr #cfk
[Consumer Group Rebalancing](concepts/consumer-group-rebalancing.md) — Three protocol generations (eager, cooperative/KIP-429, server-side/KIP-848) with assignment strategies, static membership (KIP-345), and rebalance tuning — #kafka #performance
[Consumer Lag Monitoring](concepts/consumer-lag-monitoring.md) — Offset and time-based lag monitoring via CLI, JMX, broker-side emitters, CC Metrics API, and third-party tools (Burrow, Kafka Lag Exporter); layered alert strategies — #kafka #observability #performance
[Exactly-Once Semantics](concepts/exactly-once-semantics.md) — Idempotent producers, transactional two-phase commit, consumer isolation levels, Kafka Streams EOS v1/v2, Flink two-phase commit, Connect EOS (KIP-618); Kafka-internal scope and limitations — #kafka #fsi #exactly-once #transactions
[Flink Checkpointing](concepts/flink-checkpointing.md) — Chandy-Lamport barrier mechanism, aligned vs unaligned checkpoints, state backends (HashMap/RocksDB), incremental checkpoints, Kafka source/sink interaction, CC Flink managed checkpointing — #flink #confluent-cloud #performance
[Producer Batching Configuration](concepts/producer-batching-config.md) — RecordAccumulator internals, batch.size/linger.ms interaction, compression trade-offs, tuning profiles (latency/throughput/balanced), acks interaction, JMX monitoring metrics — #kafka #performance #producers
[LinuxONE Kafka Integration](concepts/linuxone-kafka-integration.md) — IBM LinuxONE as preferred compute for z/OS Kafka offload via MQ Source Connector bridge pattern — #linuxone #ibm #mainframe #z/os #mq #kafka-connect #fips #dr

## Patterns

[FSI Governance Automation](patterns/fsi-governance-automation.md) — Governance-as-code: single Terraform module produces fully governed topic with SLA-tier defaults; Ansible parity for CP/CFK — #kafka #fsi #terraform #ansible #ci-cd #governance
[Topic Naming Convention](patterns/topic-naming.md) — `{domain}.{application}.{version}.{entity}` with dot separators, regex validation, and prefix-based RBAC — #kafka #governance #naming #fsi
[DR — Cluster Linking](patterns/dr-cluster-linking.md) — Active-passive DR for CC using bidirectional CL; 6-step failover with Consul atomic endpoint flip — #kafka #confluent-cloud #dr #cluster-linking #fsi
[DR — MirrorMaker 2](patterns/dr-mirrormaker2.md) — DR for CFK/CP using MM2 connectors; simpler failover (no promotion), connector direction reversal for failback — #kafka #mirrormaker2 #dr #cfk #confluent-platform #fsi
[DR — Multi-Region Cluster](patterns/dr-multi-region-cluster.md) — RPO=0 DR on CP using 2.5-cluster synchronous replication with automatic observer promotion — #kafka #confluent-platform #dr #mrc #fsi
[AKS Kafka Tuning](patterns/aks-kafka-tuning.md) — VM SKU selection (Edsv5/Lsv3/Ebsv5), storage tiering (Premium SSD v2/Ultra/NVMe), network config, broker JVM tuning, OS sysctl, CFK on AKS, monitoring — #kafka #azure #kubernetes #cfk #performance
[Dead Letter Queue Design](patterns/dead-letter-queue-design.md) — DLQ architecture variants (simple, retry, multi-level, error categorization), Kafka Connect/Spring Kafka/Streams implementations, topic design, reprocessing strategies, monitoring — #kafka #patterns #error-handling #connect #spring-kafka #streams
[FSI Exactly-Once Pattern](patterns/fsi-exactly-once.md) — Five-layer EOS for financial services: idempotent/transactional producers, read_committed consumers, outbox pattern, application idempotency keys; saga orchestration, audit trails, failure modes — #kafka #fsi #exactly-once #transactions #compliance
[Audit Log SIEM Integration](patterns/audit-log-siem-integration.md) — Forwarding Confluent Cloud audit log events (auth failures, RBAC denials, config changes, access transparency) to SIEM/observability platforms via HTTP Sink Connector pipeline — #kafka #confluent-cloud #observability #security #fsi #audit #compliance #dynatrace #splunk
[LinuxONE Kafka Validation & Benchmarking Suite](patterns/linuxone-validation-suite.md) — KRaft-native validation plan for CP 8.2 on Emperor 5; HiperSockets/SMC-D/CEX8S/NNPA tests beyond canonical x86 suites — #kafka #linuxone #ibm #s390x #kraft #validation #benchmark #fips #fsi
[LinuxONE Kafka Tuning](patterns/linuxone-kafka-tuning.md) — Validated Kafka 4.2 / CP 8.2 tuning with FSI tier overlay; HiperSockets MTU, SMC-D, Crypto Express offload, NUMA pinning, KRaft-specific knobs — #kafka #linuxone #ibm #s390x #kraft #tuning #fips #fsi
[LinuxONE Flink Validation, Tuning & Telum II Inference](patterns/linuxone-flink-validation-tuning.md) — CMF on s390x validation + tuning; sub-ms anomaly detection via on-chip Telum II NNPA invoked from Flink UDFs — #flink #linuxone #ibm #s390x #telum #nnpa #zdnn #validation #tuning #fsi
[FSI Reference Architecture — LinuxONE + Off-Platform Analytics](patterns/fsi-l1-reference-architecture.md) — L1 operational plane (Mongo, Cockroach, Postgres, Redis, Neo4j, Confluent, Flink+Telum II) with off-platform analytics via Cluster Linking → CC Tableflow → Databricks — #fsi #linuxone #reference-architecture #confluent #mongodb #cockroachdb #postgres #redis #neo4j #databricks #telum

## Incidents

<!-- LLM populates this section -->

## Releases

<!-- LLM populates this section -->

## Synthesis

[ADR Index](synthesis/adr-index.md) — Summary of 8 architecture decision records: Avro, compatibility tiers, Consul, Connect on-prem, CL over MRC, OAuth, naming, DR tiers — #adr #fsi #architecture

## Activity

Append-only audit trail of skill invocations. One file per calendar month; see [activity/README.md](activity/README.md) for format.

[2026-04](activity/2026-04.md) — Skill invocations during April 2026 — #activity
[2026-05](activity/2026-05.md) — Skill invocations during May 2026 — #activity
