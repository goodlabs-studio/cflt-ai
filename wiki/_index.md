---
title: Wiki Index
last_updated: 2026-05-16
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
[LinuxONE Platform Foundations](concepts/linuxone-platform-foundations.md) — L1-specific foundations spanning Kafka/Flink/data layer: STP time sync, CBU capacity-on-demand, SMC-R cross-frame transport, UKO key lifecycle, Telum II / Spyre two-tier inference, crun on s390x, IBM benchmark anchors — #linuxone #ibm #s390x #stp #ctn #cbu #smc-r #roce #uko #keys #telum #spyre #crun #fsi
[Confluent Cloud Cluster Tiers](concepts/cc-cluster-tiers.md) — Five CC cluster types (Basic, Standard, Enterprise, Dedicated, Freight) — decision rule, fixed invariants, capacity-planning skeleton — #kafka #confluent-cloud #cluster-types #fsi
[Schema Registry Best Practices](concepts/schema-registry-best-practices.md) — TopicNameStrategy, compatibility-per-subject, register-in-CI, schema IDs are not portable across envs, CSFLE — #schema-registry #avro #governance #fsi
[Network Connectivity by Cluster Tier](concepts/network-connectivity-by-tier.md) — CC networking modes mapped to tier (public/PrivateLink/peering/TGW); CP advertised.listeners; cross-AZ cost surface — #networking #confluent-cloud #privatelink #fsi
[Private Networking — PrivateLink Gateway, PNI, Peering, TGW](concepts/private-networking.md) — PLATT→Gateway transition (AWS 2026-02-12, Azure/GCP 2026-05-04), three-resource model, Flink-to-Kafka internal routing, egress PrivateLink, Azure ILB bypass — #networking #confluent-cloud #privatelink #private-service-connect #pni #fsi
[Flink on Confluent Cloud — Setup, RBAC, Lifecycle, and Statement Evolution](concepts/flink-confluent-cloud-setup.md) — Compute pools (CFUs, region-scoped), catalog/database/table auto-mapping, dual control-plane + data-plane RBAC, statement lifecycle (immutability, state limits), Autopilot scaling, watermarks/alignment defaults, materialized tables vs carry-over-offsets evolution — #flink #confluent-cloud #compute-pools #rbac #autopilot #watermarks #statement-evolution
[Kafka Streams Architecture](concepts/kafka-streams-architecture.md) — Threading model (StreamThread, Task, Subtopology, GlobalStreamThread), partition-to-task mapping, state stores, commit/flush cycle, changelog and repartition topics, canonical RocksDB memory formula — #kafka-streams #architecture #topology #confluent-agent-skills
[Kafka Streams Config Baseline](concepts/kafka-streams-config-baseline.md) — Canonical config baseline for new KS apps: core properties, security patterns (SASL_SSL/SCRAM/mTLS/OAUTHBEARER), per-environment specifics (AK/CP/CC/WarpStream), default-serde selection, EOS configuration — #kafka-streams #configuration #tuning #confluent-agent-skills
[Kafka Streams Debugging](concepts/kafka-streams-debugging.md) — Symptom-organized diagnostics: startup failures, processing stalls, rebalance storms, deserialization errors, state-store pathology, thread failures, memory issues, EOS/transaction cascades — #kafka-streams #debugging #troubleshooting #confluent-agent-skills
[Kafka Streams Production Hardening](concepts/kafka-streams-production-hardening.md) — Four-tier error handling (deserialization, processing, production, uncaught), structured JSON logging, separate liveness/readiness probes, Dockerfile, deployment sizing with PVCs, KIP-1034 DLQ — #kafka-streams #production #fsi #confluent-agent-skills
[Kafka Streams Schema Patterns](concepts/kafka-streams-schema-patterns.md) — Correct Avro/Protobuf/JSON Schema patterns: source-directory convention, logical-type nesting, Java type mapping (Instant for timestamp-millis), Protobuf gradle plugin, JSON Schema json.value.type — #kafka-streams #schema-registry #avro #confluent-agent-skills
[CDC Source Connector Setup](concepts/cdc-source-connector-setup.md) — Database prerequisites + connector configs + troubleshooting for PostgreSQL, MySQL, SQL Server, Oracle XStream, DynamoDB CDC V2 on Confluent Cloud — #cdc #connect #confluent-cloud #confluent-agent-skills
[Schema Inference and PII Categorization](concepts/schema-inference-and-pii-categorization.md) — Deriving schemas from code/data/inline structures across 5 languages + tagging fields with confluent:tags (PII/PRIVATE/SENSITIVE/PHI) for CSFLE — #schema-registry #pii #csfle #fsi #confluent-agent-skills
[Avro Schema Source Directory](concepts/avro-schema-source-directory.md) — Trip-wire: Avro schemas live in src/main/avro/ NOT src/main/resources/avro/; code generation breaks silently if misplaced — #trip-wire #avro #confluent-agent-skills
[exactly_once_v2 on WarpStream — Throughput Cost](concepts/exactly-once-v2-warpstream-throughput-cost.md) — Trip-wire: EOS v2 enables idempotent producer throttling; meaningful throughput hit on WarpStream's S3-backed tier — #trip-wire #warpstream #competitive-context #exactly-once #confluent-agent-skills
[Kafka Streams 4.x Uncaught Exception Handler Import](concepts/kafka-streams-4x-uncaught-exception-handler-import.md) — Trip-wire: StreamsUncaughtExceptionHandler is in org.apache.kafka.streams.errors in KS 4.x, no longer a nested class under KafkaStreams — #trip-wire #kafka-streams #confluent-agent-skills
[Oracle XStream Source Limitations](concepts/oracle-xstream-source-limitations.md) — Trip-wire: OracleXStreamSource doesn't support after.state.only; workaround via Flink transform — #trip-wire #cdc #oracle #confluent-agent-skills
[Schema-Aware Console Producer Required](concepts/schema-aware-console-producer-required.md) — Trip-wire: kafka-console-producer doesn't speak Schema Registry; use kafka-avro-console-producer for SR-governed topics — #trip-wire #schema-registry #cli #confluent-agent-skills
[Tableflow Changelog Mode Immutability](concepts/tableflow-changelog-mode-immutability.md) — Trip-wire: Tableflow CHANGELOG mode is immutable after first materialization; cannot switch to APPEND without recreate — #trip-wire #tableflow #confluent-cloud #confluent-agent-skills
[WarpStream Config Overrides](concepts/warpstream-config-overrides.md) — Trip-wire: WarpStream silently ignores fetch.min.bytes; replication.factor is cosmetic (always 3-way internally) — #trip-wire #warpstream #competitive-context #configuration #confluent-agent-skills
[WarpStream Schema Registry Format Constraint](concepts/warpstream-schema-registry-format-constraint.md) — Trip-wire: WarpStream built-in SR only supports Avro and Protobuf; no JSON Schema — #trip-wire #warpstream #competitive-context #schema-registry #confluent-agent-skills

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
[Low-Latency Kafka Clients on Azure](patterns/low-latency-kafka-azure.md) — Three-layer profile (latency tuning, ILB-aware connection management, rebalance avoidance) for sub-100ms Kafka workloads on Azure; cites named fsi-dsp `*-low-latency-azure` reference artifacts — #kafka #azure #latency #fsi #performance #fraud-detection #rebalance #ilb
[LinuxONE Kafka Validation & Benchmarking Suite](patterns/linuxone-validation-suite.md) — KRaft-native validation plan for CP 8.2 on Emperor 5; HiperSockets/SMC-D/CEX8S/NNPA tests beyond canonical x86 suites — #kafka #linuxone #ibm #s390x #kraft #validation #benchmark #fips #fsi
[LinuxONE Kafka Tuning](patterns/linuxone-kafka-tuning.md) — Validated Kafka 4.2 / CP 8.2 tuning with FSI tier overlay; HiperSockets MTU, SMC-D, Crypto Express offload, NUMA pinning, KRaft-specific knobs — #kafka #linuxone #ibm #s390x #kraft #tuning #fips #fsi
[LinuxONE Flink Validation, Tuning & Telum II Inference](patterns/linuxone-flink-validation-tuning.md) — CMF on s390x validation + tuning; sub-ms anomaly detection via on-chip Telum II NNPA invoked from Flink UDFs — #flink #linuxone #ibm #s390x #telum #nnpa #zdnn #validation #tuning #fsi
[FSI Reference Architecture — LinuxONE + Off-Platform Analytics](patterns/fsi-l1-reference-architecture.md) — L1 operational plane (Mongo, Cockroach, Postgres, Redis, Neo4j, Confluent, Flink+Telum II) with off-platform analytics via Cluster Linking → CC Tableflow → Databricks — #fsi #linuxone #reference-architecture #confluent #mongodb #cockroachdb #postgres #redis #neo4j #databricks #telum
[FSI Producer Configuration](patterns/producer-config-fsi.md) — Canonical FSI producer baseline (idempotence + acks=all + lz4 + batched) with transactional and latency-tier overlays — #kafka #fsi #producers #idempotence #transactions
[FSI Consumer Configuration](patterns/consumer-config-fsi.md) — Canonical FSI consumer baseline (manual commit, CooperativeStickyAssignor explicit, static membership, fetch-from-follower) with lag triage — #kafka #fsi #consumers #rebalancing #lag
[Kafka Connect Deployment Models](patterns/connect-deployment-models.md) — Three models (fully-managed CC, Custom Connector on CC, self-managed); decision matrix; performance tuning; EOS source — #kafka #connect #fsi #eos #dlq
[Flink Runtime Models — CC Managed, CMF, and Self-Managed](patterns/flink-runtime-models.md) — Three Flink runtime options and the defaults that apply on all of them (bounded watermarks, state-ttl, upsert-kafka) — #flink #confluent-cloud #cmf #cfk #runtime
[Schema Registry Shared-Types Library](patterns/schema-registry-shared-types.md) — Versioned shared types (Money, MemberId, UsAddress) under a reserved namespace with FULL_TRANSITIVE compat; domain subjects pull them in via pinned schema references — #schema-registry #avro #references #governance #fsi #shared-types
[Kafka Streams Topology Patterns](patterns/kafka-streams-topology-patterns.md) — Canonical KS topology shapes — stateless transforms, enrichment joins, aggregations, windowing decision tree, suppression, deduplication, splitting, Processor API, exactly-once decision — #kafka-streams #topology #dsl #confluent-agent-skills
[CDC to Tableflow — Flink Decode Pattern](patterns/cdc-to-tableflow-flink-decode.md) — Debezium → Kafka raw → Flink decode → clean topic (changelog.mode=upsert) → Tableflow → Iceberg/Delta; never enable Tableflow on raw CDC (tombstones break APPEND) — #tableflow #cdc #flink #confluent-cloud #confluent-agent-skills
[Schema Registry Adoption Playbook](patterns/schema-registry-adoption-playbook.md) — Detection patterns (build files, producers, consumers, custom serializers, risk flags) + code migration recipes (Avro/Protobuf/JSON Schema) across 5 languages with category-based rollout order — #schema-registry #adoption #migration #terraform #confluent-agent-skills
[CDC-Tableflow — Flink Decode Required](patterns/cdc-tableflow-flink-decode-required.md) — Trip-wire pattern: Don't enable Tableflow on CDC source topics; tombstones break APPEND mode; decode through Flink to a clean topic first — #trip-wire #pattern #tableflow #cdc #flink #confluent-cloud #confluent-agent-skills

## Incidents

<!-- LLM populates this section -->

## Releases

<!-- LLM populates this section -->

## Synthesis

[ADR Index](synthesis/adr-index.md) — Summary of 8 architecture decision records: Avro, compatibility tiers, Consul, Connect on-prem, CL over MRC, OAuth, naming, DR tiers — #adr #fsi #architecture
[Top 20 Confluent Gotchas](synthesis/confluent-gotchas-top-20.md) — Fast scan-and-recognize triage index across producers, consumers, schemas, Connect, Flink, K8s, networking — #kafka #gotchas #troubleshooting #fsi #synthesis

## Activity

Append-only audit trail of skill invocations. One file per calendar month; see [activity/README.md](activity/README.md) for format.

[2026-04](activity/2026-04.md) — Skill invocations during April 2026 — #activity
[2026-05](activity/2026-05.md) — Skill invocations during May 2026 — #activity
