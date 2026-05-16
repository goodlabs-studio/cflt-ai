---
title: Concept Graph / Backlink Registry
last_updated: 2026-05-16
---

# Backlink Registry

Tracks which articles reference which. The LLM maintains this file.

## Format

```
[source article] → [target article] : relationship description
```

## Backlinks

concepts/fsi-data-streaming-platform → concepts/sla-tiers : tier system drives all governance defaults
concepts/fsi-data-streaming-platform → concepts/schema-evolution-strategies : schema governance for the platform
concepts/fsi-data-streaming-platform → concepts/fsi-compliance : compliance audit trail for CI/CD
concepts/fsi-data-streaming-platform → patterns/fsi-governance-automation : governance-as-code pattern
concepts/fsi-data-streaming-platform → patterns/dr-cluster-linking : CL DR for CC deployments
concepts/fsi-data-streaming-platform → patterns/dr-mirrormaker2 : MM2 DR for CFK/CP deployments
concepts/fsi-data-streaming-platform → patterns/dr-multi-region-cluster : MRC RPO=0 for CP
concepts/fsi-data-streaming-platform → patterns/topic-naming : naming convention
concepts/fsi-data-streaming-platform → synthesis/adr-index : architecture decisions

concepts/sla-tiers → concepts/fsi-data-streaming-platform : platform overview
concepts/sla-tiers → concepts/schema-evolution-strategies : compatibility modes derived from tier
concepts/sla-tiers → patterns/fsi-governance-automation : tiers propagate through IaC
concepts/sla-tiers → patterns/dr-cluster-linking : DR thresholds per tier
concepts/sla-tiers → patterns/dr-mirrormaker2 : MM2 lag monitoring per tier
concepts/sla-tiers → patterns/dr-multi-region-cluster : compliance tier drives RPO=0
concepts/sla-tiers → synthesis/adr-index : ADR-002, ADR-008

concepts/schema-evolution-strategies → concepts/sla-tiers : compatibility modes per tier
concepts/schema-evolution-strategies → patterns/topic-naming : version segment for breaking changes
concepts/schema-evolution-strategies → patterns/fsi-governance-automation : Terraform module enforcement
concepts/schema-evolution-strategies → concepts/fsi-compliance : audit trail for schema changes
concepts/schema-evolution-strategies → synthesis/adr-index : ADR-001, ADR-002

concepts/fsi-compliance → concepts/fsi-data-streaming-platform : platform context
concepts/fsi-compliance → patterns/fsi-governance-automation : CI/CD pattern producing audit trail
concepts/fsi-compliance → concepts/sla-tiers : tier definitions
concepts/fsi-compliance → concepts/schema-evolution-strategies : schema governance enforced by CI

patterns/fsi-governance-automation → concepts/fsi-data-streaming-platform : platform overview
patterns/fsi-governance-automation → concepts/sla-tiers : tier defaults
patterns/fsi-governance-automation → patterns/topic-naming : naming enforcement
patterns/fsi-governance-automation → concepts/schema-evolution-strategies : compatibility modes
patterns/fsi-governance-automation → concepts/fsi-compliance : audit trail

patterns/topic-naming → concepts/schema-evolution-strategies : versioned topic migration
patterns/topic-naming → patterns/fsi-governance-automation : module validates names
patterns/topic-naming → concepts/sla-tiers : tier selection per topic
patterns/topic-naming → synthesis/adr-index : ADR-007

patterns/dr-cluster-linking → patterns/dr-mirrormaker2 : alternative backend
patterns/dr-cluster-linking → patterns/dr-multi-region-cluster : RPO=0 alternative
patterns/dr-cluster-linking → concepts/sla-tiers : RPO/RTO targets per tier
patterns/dr-cluster-linking → concepts/cluster-linking-topology : CL architecture
patterns/dr-cluster-linking → synthesis/adr-index : ADR-003, ADR-005

patterns/dr-mirrormaker2 → patterns/dr-cluster-linking : alternative for CC
patterns/dr-mirrormaker2 → patterns/dr-multi-region-cluster : RPO=0 on CP
patterns/dr-mirrormaker2 → concepts/sla-tiers : tier-based RPO/RTO

patterns/dr-multi-region-cluster → patterns/dr-cluster-linking : async DR for CC
patterns/dr-multi-region-cluster → patterns/dr-mirrormaker2 : async DR for CFK/CP
patterns/dr-multi-region-cluster → concepts/sla-tiers : compliance tier requirement
patterns/dr-multi-region-cluster → synthesis/adr-index : ADR-005, ADR-008

synthesis/adr-index → concepts/fsi-data-streaming-platform : platform these decisions govern
synthesis/adr-index → concepts/sla-tiers : tier system (ADR-002, ADR-008)
synthesis/adr-index → concepts/schema-evolution-strategies : Avro and compatibility (ADR-001, ADR-002)
synthesis/adr-index → patterns/fsi-governance-automation : implements decisions
synthesis/adr-index → patterns/topic-naming : naming convention (ADR-007)
synthesis/adr-index → patterns/dr-cluster-linking : CL decision (ADR-005)
synthesis/adr-index → patterns/dr-mirrormaker2 : MM2 procedures
synthesis/adr-index → patterns/dr-multi-region-cluster : MRC RPO=0 (ADR-005, ADR-008)

concepts/cluster-linking-topology → patterns/dr-cluster-linking : CL DR pattern using CL
concepts/cluster-linking-topology → concepts/fsi-data-streaming-platform : platform monitoring context
concepts/cluster-linking-topology → concepts/sla-tiers : RPO/RTO targets per tier

concepts/consumer-group-rebalancing → concepts/consumer-lag-monitoring : lag spikes during rebalances
concepts/consumer-group-rebalancing → concepts/exactly-once-semantics : rebalance impact on EOS
concepts/consumer-group-rebalancing → concepts/producer-batching-config : producer-side tuning
concepts/consumer-group-rebalancing → patterns/aks-kafka-tuning : static membership in Kubernetes, CooperativeStickyAssignor

concepts/consumer-lag-monitoring → concepts/consumer-group-rebalancing : rebalances cause lag spikes
concepts/consumer-lag-monitoring → concepts/sla-tiers : tier-based lag alert thresholds
concepts/consumer-lag-monitoring → concepts/fsi-data-streaming-platform : platform monitoring context

concepts/exactly-once-semantics → concepts/consumer-group-rebalancing : rebalance behavior during transactions
concepts/exactly-once-semantics → concepts/consumer-lag-monitoring : LSO-based lag under read_committed
concepts/exactly-once-semantics → patterns/fsi-exactly-once : regulatory reporting and audit for EOS
concepts/exactly-once-semantics → concepts/flink-checkpointing : checkpoint mechanics for Flink 2PC
concepts/exactly-once-semantics → concepts/producer-batching-config : batching interaction with idempotence

concepts/flink-checkpointing → concepts/exactly-once-semantics : end-to-end delivery guarantees
concepts/flink-checkpointing → concepts/consumer-lag-monitoring : offset commits feed consumer lag metrics

concepts/producer-batching-config → concepts/exactly-once-semantics : idempotence constraints on batching
concepts/producer-batching-config → concepts/consumer-lag-monitoring : downstream impact on e2e latency
concepts/producer-batching-config → patterns/aks-kafka-tuning : platform-specific producer tuning

patterns/aks-kafka-tuning → concepts/producer-batching-config : client-side tuning pairing
patterns/aks-kafka-tuning → concepts/fsi-data-streaming-platform : FSI architecture context
patterns/aks-kafka-tuning → concepts/sla-tiers : latency tiers drive VM/storage selection
patterns/aks-kafka-tuning → patterns/dr-cluster-linking : cross-region replication
patterns/aks-kafka-tuning → concepts/consumer-lag-monitoring : monitoring patterns

patterns/dead-letter-queue-design → concepts/exactly-once-semantics : DLQ interaction with transactions
patterns/dead-letter-queue-design → concepts/consumer-group-rebalancing : rebalance during retry backoff
patterns/dead-letter-queue-design → patterns/fsi-exactly-once : FSI failure handling requirements
patterns/dead-letter-queue-design → patterns/topic-naming : naming conventions for DLQ topics
patterns/dead-letter-queue-design → concepts/consumer-lag-monitoring : DLQ consumer lag monitoring

patterns/fsi-exactly-once → concepts/exactly-once-semantics : foundational EOS mechanisms
patterns/fsi-exactly-once → concepts/sla-tiers : tier definitions for EOS requirements
patterns/fsi-exactly-once → concepts/fsi-data-streaming-platform : overall FSI architecture
patterns/fsi-exactly-once → patterns/dead-letter-queue-design : error handling complementing EOS
patterns/fsi-exactly-once → patterns/dr-cluster-linking : DR with EOS implications

concepts/linuxone-kafka-integration → concepts/fsi-data-streaming-platform : platform overview including LinuxONE context
concepts/linuxone-kafka-integration → concepts/sla-tiers : latency tiers (market_data, risk) drive LinuxONE adoption
concepts/linuxone-kafka-integration → concepts/fsi-compliance : FIPS 140-2 and audit trail requirements
concepts/linuxone-kafka-integration → patterns/dr-cluster-linking : DR pattern for LinuxONE-produced topics

patterns/audit-log-siem-integration → concepts/fsi-data-streaming-platform : observability templates cover operational metrics; audit log is the security complement
patterns/audit-log-siem-integration → concepts/fsi-compliance : audit trail for regulatory frameworks
patterns/audit-log-siem-integration → concepts/consumer-lag-monitoring : operational metrics monitoring (other half of observability)
patterns/audit-log-siem-integration → patterns/fsi-exactly-once : audit logging requirements for transactional processing

patterns/low-latency-kafka-azure → concepts/sla-tiers : sub-100ms latency tier framing
patterns/low-latency-kafka-azure → concepts/fsi-data-streaming-platform : Azure deployment model context
patterns/low-latency-kafka-azure → concepts/consumer-group-rebalancing : cooperative-sticky + static membership rationale
patterns/low-latency-kafka-azure → concepts/producer-batching-config : latency-favored tuning (linger.ms=0, batch.size=16384, compression=none)
patterns/low-latency-kafka-azure → patterns/aks-kafka-tuning : Azure-specific deployment patterns
patterns/low-latency-kafka-azure → patterns/dr-cluster-linking : DR pattern compatible with this client profile

patterns/producer-config-fsi → concepts/producer-batching-config : batching internals
patterns/producer-config-fsi → concepts/exactly-once-semantics : idempotent + transactional producer mechanics
patterns/producer-config-fsi → patterns/fsi-exactly-once : producer layer of five-layer EOS
patterns/producer-config-fsi → patterns/low-latency-kafka-azure : sub-100ms overlay
patterns/producer-config-fsi → concepts/schema-registry-best-practices : auto.register policy and CI
patterns/producer-config-fsi → patterns/topic-naming : naming canon for keyed topics
patterns/producer-config-fsi → synthesis/confluent-gotchas-top-20 : producer-specific gotchas

patterns/consumer-config-fsi → concepts/consumer-group-rebalancing : eager/cooperative/KIP-848 protocols
patterns/consumer-config-fsi → concepts/consumer-lag-monitoring : offset and time lag, CC Metrics API
patterns/consumer-config-fsi → concepts/exactly-once-semantics : read_committed isolation
patterns/consumer-config-fsi → patterns/producer-config-fsi : paired producer baseline
patterns/consumer-config-fsi → patterns/low-latency-kafka-azure : fraud-tier overlay
patterns/consumer-config-fsi → patterns/dead-letter-queue-design : poison-pill routing
patterns/consumer-config-fsi → synthesis/confluent-gotchas-top-20 : consumer-specific gotchas

concepts/cc-cluster-tiers → concepts/network-connectivity-by-tier : networking mapped to tier
concepts/cc-cluster-tiers → patterns/dr-cluster-linking : tier requirements for CL source
concepts/cc-cluster-tiers → concepts/fsi-data-streaming-platform : platform overview / six deployment models
concepts/cc-cluster-tiers → concepts/sla-tiers : FSI SLA tiers vs CC cluster tiers (naming overlap)
concepts/cc-cluster-tiers → synthesis/confluent-gotchas-top-20 : gotcha #7 (RF/min.insync/unclean fixed)

concepts/schema-registry-best-practices → concepts/schema-evolution-strategies : tier-based compatibility policy
concepts/schema-registry-best-practices → patterns/fsi-governance-automation : Terraform enforcement of compat
concepts/schema-registry-best-practices → patterns/topic-naming : versioned-topic exception (ADR-007)
concepts/schema-registry-best-practices → patterns/producer-config-fsi : auto.register.schemas=false enforcement
concepts/schema-registry-best-practices → concepts/fsi-compliance : schema-change audit trail
concepts/schema-registry-best-practices → synthesis/confluent-gotchas-top-20 : gotchas #8, #9, #10

patterns/connect-deployment-models → patterns/dead-letter-queue-design : DLQ topic design
patterns/connect-deployment-models → concepts/exactly-once-semantics : KIP-618 EOS source
patterns/connect-deployment-models → patterns/fsi-governance-automation : Terraform connector deployment
patterns/connect-deployment-models → patterns/fsi-exactly-once : outbox/upsert as consumer-side EOS
patterns/connect-deployment-models → concepts/schema-registry-best-practices : converter/SR config
patterns/connect-deployment-models → synthesis/confluent-gotchas-top-20 : gotchas #11, #12, #13

patterns/flink-runtime-models → concepts/flink-checkpointing : checkpoint mechanics on CMF
patterns/flink-runtime-models → patterns/linuxone-flink-validation-tuning : CMF on s390x
patterns/flink-runtime-models → concepts/exactly-once-semantics : Flink two-phase commit
patterns/flink-runtime-models → concepts/schema-registry-best-practices : Flink reads SR automatically
patterns/flink-runtime-models → synthesis/confluent-gotchas-top-20 : gotchas #14, #15, #16

concepts/network-connectivity-by-tier → concepts/cc-cluster-tiers : tier matrix extended on networking axis
concepts/network-connectivity-by-tier → patterns/dr-cluster-linking : Consul endpoint flip, CC↔CC private
concepts/network-connectivity-by-tier → patterns/low-latency-kafka-azure : ILB-aware, fetch-from-follower
concepts/network-connectivity-by-tier → patterns/aks-kafka-tuning : advertised listeners on CFK
concepts/network-connectivity-by-tier → synthesis/confluent-gotchas-top-20 : gotchas #18, #20
concepts/network-connectivity-by-tier → concepts/private-networking : deep dive on PrivateLink Gateway mechanics

concepts/private-networking → concepts/network-connectivity-by-tier : tier-to-mode mapping (parent article)
concepts/private-networking → concepts/cc-cluster-tiers : Enterprise vs Dedicated tier requirements
concepts/private-networking → patterns/dr-cluster-linking : CL over private, CC↔CP reachability planning
concepts/private-networking → patterns/low-latency-kafka-azure : Azure ILB connection-management for self-managed paths
concepts/private-networking → concepts/fsi-data-streaming-platform : six deployment models context

synthesis/confluent-gotchas-top-20 → patterns/producer-config-fsi : producer gotchas resolution
synthesis/confluent-gotchas-top-20 → patterns/consumer-config-fsi : consumer gotchas resolution
synthesis/confluent-gotchas-top-20 → concepts/cc-cluster-tiers : tier-specific gotchas
synthesis/confluent-gotchas-top-20 → concepts/schema-registry-best-practices : schema gotchas
synthesis/confluent-gotchas-top-20 → concepts/schema-evolution-strategies : compatibility direction gotcha
synthesis/confluent-gotchas-top-20 → patterns/connect-deployment-models : Connect gotchas
synthesis/confluent-gotchas-top-20 → patterns/flink-runtime-models : Flink gotchas
synthesis/confluent-gotchas-top-20 → concepts/network-connectivity-by-tier : networking gotchas
synthesis/confluent-gotchas-top-20 → concepts/consumer-group-rebalancing : rebalance gotcha context
synthesis/confluent-gotchas-top-20 → patterns/fsi-exactly-once : outbox/idempotent-consumer for EOS into a DB

patterns/schema-registry-shared-types → concepts/schema-registry-best-practices : operational surface (subject strategy, ID portability, references API)
patterns/schema-registry-shared-types → concepts/schema-evolution-strategies : compatibility-by-tier and evolution runbook
patterns/schema-registry-shared-types → patterns/topic-naming : domain naming convention
patterns/schema-registry-shared-types → patterns/fsi-governance-automation : Terraform registers shared types before referencing subjects
patterns/schema-registry-shared-types → concepts/fsi-compliance : schema-change audit trail

concepts/schema-registry-best-practices → patterns/schema-registry-shared-types : shared-types library pattern using references
concepts/schema-evolution-strategies → patterns/schema-registry-shared-types : shared-types library example of FULL_TRANSITIVE in practice

concepts/flink-confluent-cloud-setup → patterns/flink-runtime-models : cross-runtime defaults (watermarks, state-ttl, upsert-kafka) and compute-pool sizing
concepts/flink-confluent-cloud-setup → concepts/flink-checkpointing : Chandy-Lamport mechanics (fully managed on CC)
concepts/flink-confluent-cloud-setup → concepts/schema-evolution-strategies : tier-based compatibility selection (FULL/FULL_TRANSITIVE for Flink)
concepts/flink-confluent-cloud-setup → concepts/schema-registry-best-practices : TopicNameStrategy + operational surface
concepts/flink-confluent-cloud-setup → concepts/exactly-once-semantics : Flink two-phase commit foundation
concepts/flink-confluent-cloud-setup → concepts/fsi-compliance : audit-log requirements for production service accounts

patterns/flink-runtime-models → concepts/flink-confluent-cloud-setup : CC-specific setup deep dive (compute pools, RBAC, lifecycle)
concepts/flink-checkpointing → concepts/flink-confluent-cloud-setup : CC managed checkpointing context
concepts/schema-evolution-strategies → concepts/flink-confluent-cloud-setup : statement evolution and carry-over offsets
concepts/schema-registry-best-practices → concepts/flink-confluent-cloud-setup : Flink reads/writes SR subjects under dual-plane RBAC

## H.1 — confluent-agent-skills ingest (2026-05-16)

# Parent #1: kafka-streams-topology-patterns — outbound
patterns/kafka-streams-topology-patterns → concepts/exactly-once-semantics : EOS implications for stateful topologies
patterns/kafka-streams-topology-patterns → concepts/consumer-group-rebalancing : rebalance behavior under stateful operators
patterns/kafka-streams-topology-patterns → concepts/kafka-streams-architecture : architecture context for topology choices
patterns/kafka-streams-topology-patterns → concepts/kafka-streams-debugging : debugging stateful topologies

# Parent #2: kafka-streams-debugging — outbound
concepts/kafka-streams-debugging → concepts/kafka-streams-production-hardening : production diagnostics complement
concepts/kafka-streams-debugging → concepts/kafka-streams-4x-uncaught-exception-handler-import : trip-wire on KS 4.x import
concepts/kafka-streams-debugging → concepts/avro-schema-source-directory : trip-wire on Avro source dir
concepts/kafka-streams-debugging → concepts/schema-aware-console-producer-required : trip-wire on console-producer verification
concepts/kafka-streams-debugging → synthesis/confluent-gotchas-top-20 : cross-pollination with gotchas index

# Parent #3: kafka-streams-production-hardening — outbound
concepts/kafka-streams-production-hardening → concepts/exactly-once-semantics : EOS production posture
concepts/kafka-streams-production-hardening → patterns/fsi-exactly-once : FSI five-layer EOS pattern
concepts/kafka-streams-production-hardening → concepts/exactly-once-v2-warpstream-throughput-cost : trip-wire on EOS cost on WarpStream
concepts/kafka-streams-production-hardening → concepts/kafka-streams-debugging : debugging counterpart
concepts/kafka-streams-production-hardening → patterns/producer-config-fsi : producer-layer config baseline

# Parent #4: kafka-streams-schema-patterns — outbound
concepts/kafka-streams-schema-patterns → concepts/schema-registry-best-practices : SR operational surface
concepts/kafka-streams-schema-patterns → concepts/schema-evolution-strategies : compatibility policy
concepts/kafka-streams-schema-patterns → patterns/schema-registry-shared-types : shared-types library pattern
concepts/kafka-streams-schema-patterns → concepts/avro-schema-source-directory : trip-wire on Avro source dir

# Parent #5: kafka-streams-config-baseline — outbound
concepts/kafka-streams-config-baseline → patterns/producer-config-fsi : producer baseline pairing
concepts/kafka-streams-config-baseline → patterns/consumer-config-fsi : consumer baseline pairing
concepts/kafka-streams-config-baseline → concepts/warpstream-config-overrides : trip-wire on WarpStream config drift
concepts/kafka-streams-config-baseline → concepts/kafka-streams-architecture : architectural rationale for defaults

# Parent #6: kafka-streams-architecture — outbound
concepts/kafka-streams-architecture → concepts/exactly-once-semantics : EOS in stream processing
concepts/kafka-streams-architecture → concepts/flink-checkpointing : alternative streaming runtime context
concepts/kafka-streams-architecture → patterns/flink-runtime-models : Flink vs Kafka Streams runtime trade-offs
concepts/kafka-streams-architecture → concepts/fsi-data-streaming-platform : platform context

# Parent #7: cdc-to-tableflow-flink-decode — outbound
patterns/cdc-to-tableflow-flink-decode → concepts/tableflow-changelog-mode-immutability : trip-wire on Tableflow immutability
patterns/cdc-to-tableflow-flink-decode → patterns/cdc-tableflow-flink-decode-required : trip-wire elaborating decode requirement
patterns/cdc-to-tableflow-flink-decode → concepts/cdc-source-connector-setup : pre-pipeline connector setup
patterns/cdc-to-tableflow-flink-decode → concepts/flink-checkpointing : checkpointing for the Flink decode step
patterns/cdc-to-tableflow-flink-decode → concepts/flink-confluent-cloud-setup : CC Flink setup context
patterns/cdc-to-tableflow-flink-decode → concepts/exactly-once-semantics : EOS across the pipeline

# Parent #8: cdc-source-connector-setup — outbound
concepts/cdc-source-connector-setup → patterns/cdc-to-tableflow-flink-decode : operational counterpart pattern
concepts/cdc-source-connector-setup → concepts/oracle-xstream-source-limitations : trip-wire on after.state.only
concepts/cdc-source-connector-setup → patterns/connect-deployment-models : Connect deployment patterns

# Parent #9: schema-registry-adoption-playbook — outbound
patterns/schema-registry-adoption-playbook → concepts/schema-registry-best-practices : operational surface for SR
patterns/schema-registry-adoption-playbook → concepts/schema-evolution-strategies : compatibility policy
patterns/schema-registry-adoption-playbook → patterns/fsi-governance-automation : Terraform enforcement of registered subjects
patterns/schema-registry-adoption-playbook → patterns/schema-registry-shared-types : shared-types library
patterns/schema-registry-adoption-playbook → concepts/schema-inference-and-pii-categorization : inference + PII tagging sibling

# Parent #10: schema-inference-and-pii-categorization — outbound
concepts/schema-inference-and-pii-categorization → concepts/schema-registry-best-practices : SR operational surface
concepts/schema-inference-and-pii-categorization → concepts/fsi-compliance : PII categorization connects to compliance
concepts/schema-inference-and-pii-categorization → patterns/schema-registry-shared-types : shared types include PII-tagged fields
concepts/schema-inference-and-pii-categorization → patterns/schema-registry-adoption-playbook : adoption playbook sibling

# Inbound (existing wiki → new H.1 articles) — backfill so every new article has ≥1 inbound
concepts/exactly-once-semantics → concepts/kafka-streams-production-hardening : EOS production application
concepts/exactly-once-semantics → concepts/kafka-streams-architecture : EOS in stream processing
concepts/schema-registry-best-practices → concepts/kafka-streams-schema-patterns : KS-specific schema patterns
concepts/schema-registry-best-practices → patterns/schema-registry-adoption-playbook : adoption playbook for SR
concepts/schema-registry-best-practices → concepts/schema-inference-and-pii-categorization : inference + PII categorization
patterns/connect-deployment-models → concepts/cdc-source-connector-setup : CDC source connector deployment specifics
concepts/flink-checkpointing → patterns/cdc-to-tableflow-flink-decode : checkpointing in the CDC decode pipeline
patterns/producer-config-fsi → concepts/kafka-streams-config-baseline : KS-specific config baseline
patterns/consumer-config-fsi → concepts/kafka-streams-config-baseline : KS-specific config baseline
synthesis/confluent-gotchas-top-20 → concepts/kafka-streams-debugging : debugging-focused gotchas
patterns/kafka-streams-topology-patterns → concepts/schema-registry-best-practices : SR operational surface for KS state
concepts/kafka-streams-config-baseline → concepts/exactly-once-semantics : EOS configuration anchor
concepts/kafka-streams-architecture → patterns/kafka-streams-topology-patterns : runtime model that informs topology choices
concepts/kafka-streams-debugging → patterns/kafka-streams-topology-patterns : debugging counterpart for topology patterns
concepts/kafka-streams-production-hardening → patterns/kafka-streams-topology-patterns : production posture for EOS topology decisions

# Trip-wires — outbound (close forward-references from H.1-02 parents)
# Trip-wire #1: tableflow-changelog-mode-immutability
concepts/tableflow-changelog-mode-immutability → patterns/cdc-to-tableflow-flink-decode : parent ingest article (back-link per D-06)
concepts/tableflow-changelog-mode-immutability → patterns/cdc-tableflow-flink-decode-required : sibling trip-wire (Tableflow + CDC)
concepts/tableflow-changelog-mode-immutability → concepts/oracle-xstream-source-limitations : sibling trip-wire (CDC-Tableflow cluster)

# Trip-wire #2: cdc-tableflow-flink-decode-required
patterns/cdc-tableflow-flink-decode-required → patterns/cdc-to-tableflow-flink-decode : parent ingest article (back-link per D-06)
patterns/cdc-tableflow-flink-decode-required → concepts/tableflow-changelog-mode-immutability : sibling trip-wire
patterns/cdc-tableflow-flink-decode-required → concepts/cdc-source-connector-setup : parent for CDC connector configs

# Trip-wire #3: oracle-xstream-source-limitations
concepts/oracle-xstream-source-limitations → concepts/cdc-source-connector-setup : parent ingest article (back-link per D-06)
concepts/oracle-xstream-source-limitations → concepts/tableflow-changelog-mode-immutability : sibling trip-wire (CDC-Tableflow cluster)
concepts/oracle-xstream-source-limitations → patterns/cdc-tableflow-flink-decode-required : sibling trip-wire (decode pattern obviates after.state.only shortcuts)

# Trip-wire #4: kafka-streams-4x-uncaught-exception-handler-import
concepts/kafka-streams-4x-uncaught-exception-handler-import → concepts/kafka-streams-debugging : parent ingest article (back-link per D-06)
concepts/kafka-streams-4x-uncaught-exception-handler-import → concepts/kafka-streams-production-hardening : closely-related parent (Layer 4 error handling)
concepts/kafka-streams-4x-uncaught-exception-handler-import → concepts/avro-schema-source-directory : sibling KS-programming trip-wire
concepts/kafka-streams-4x-uncaught-exception-handler-import → concepts/schema-aware-console-producer-required : sibling KS-programming trip-wire

# Trip-wire #5: avro-schema-source-directory
concepts/avro-schema-source-directory → concepts/kafka-streams-debugging : parent ingest article (back-link per D-06)
concepts/avro-schema-source-directory → concepts/kafka-streams-schema-patterns : parent for schema-patterns context
concepts/avro-schema-source-directory → concepts/kafka-streams-4x-uncaught-exception-handler-import : sibling KS-programming trip-wire

# Trip-wire #6: schema-aware-console-producer-required
concepts/schema-aware-console-producer-required → concepts/schema-registry-best-practices : SR operational surface
concepts/schema-aware-console-producer-required → concepts/kafka-streams-debugging : parent ingest article (back-link per D-06)
concepts/schema-aware-console-producer-required → concepts/kafka-streams-4x-uncaught-exception-handler-import : sibling KS-programming trip-wire

# Trip-wire #7: warpstream-schema-registry-format-constraint
concepts/warpstream-schema-registry-format-constraint → concepts/schema-registry-best-practices : SR operational surface
concepts/warpstream-schema-registry-format-constraint → concepts/warpstream-config-overrides : sibling WarpStream trip-wire
concepts/warpstream-schema-registry-format-constraint → concepts/exactly-once-v2-warpstream-throughput-cost : sibling WarpStream trip-wire

# Trip-wire #8: warpstream-config-overrides
concepts/warpstream-config-overrides → concepts/kafka-streams-config-baseline : parent ingest article (back-link per D-06)
concepts/warpstream-config-overrides → concepts/warpstream-schema-registry-format-constraint : sibling WarpStream trip-wire
concepts/warpstream-config-overrides → concepts/exactly-once-v2-warpstream-throughput-cost : sibling WarpStream trip-wire

# Trip-wire #9: exactly-once-v2-warpstream-throughput-cost
concepts/exactly-once-v2-warpstream-throughput-cost → concepts/exactly-once-semantics : EOS foundation
concepts/exactly-once-v2-warpstream-throughput-cost → concepts/kafka-streams-production-hardening : parent ingest article (back-link per D-06)
concepts/exactly-once-v2-warpstream-throughput-cost → concepts/warpstream-config-overrides : sibling WarpStream trip-wire
concepts/exactly-once-v2-warpstream-throughput-cost → concepts/warpstream-schema-registry-format-constraint : sibling WarpStream trip-wire
