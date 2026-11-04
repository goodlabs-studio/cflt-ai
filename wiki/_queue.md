---
title: Work Queue
last_updated: 2026-05-18
---

# Wiki Work Queue

Articles flagged for creation, expansion, or verification.
The LLM reads this at session start and clears items when complete.

## Stubs to Create

<!-- format: - [ ] wiki/concepts/<slug>.md — brief description of needed content -->
- [x] wiki/patterns/flink-event-routing.md — compiled 2026-05-18 via /wiki:ingest. Pattern article covering the canonical raw → stateless Flink statement → derived topic shape, three load-bearing rationales (replayability via earliest-offset replay, schema decoupling from upstream wire format, debuggability with raw topic as ground truth), the operator table separating stateless/bounded routing operators from unbounded ones that disqualify a workload from the pattern, multi-INSERT split idiom, CC compute-pool sizing for stateless routing, and the producer-side anti-pattern (Connect SMTs, app-side branching, Debezium predicates, producer-side flattening, pre-filtered fan-out) with the narrow CSFLE-at-SR exception for PII redaction. MCP-only ingest; one inline ⚠️ unverified marker on per-CFU throughput ceilings for stateless routing (heuristic calibrated against flink-runtime-models defaults). confidence: medium pending /wiki:validate against current confluent-docs Flink SQL + compute-pool pages.
- [x] wiki/patterns/latency-optimized-kafka-client.md — **RESOLVED 2026-05-18** via `outputs/reports/wiki-validation-2026-05-18-latency-optimized-kafka-client.md`. Article exists and validates cleanly: 19 producer/consumer/connection defaults confirmed against confluent-docs (CP current). `linger.ms` Kafka 4.0 / KIP-1083 default change marker resolved inline. Confidence promoted `medium` → `high`. Remaining ⚠️ marker is a cross-pointer to the Azure overlay article, not a claim made by this article.
- [x] wiki/concepts/confluent-cloud-gateway.md — compiled 2026-05-18 via /wiki:ingest. Concept article covering protocol-aware proxy capabilities (custom domains, auth swapping, traffic control, fencing/unfencing), CFK/Docker deployment, DR switchover use case with stateful-vs-stateless discrimination, and disambiguation from CC PrivateLink Gateway. MCP direct-URL fetches for Confluent Gateway docs returned 302s; confidence: medium with ⚠️ unverified markers on 1.1.0/1.2 version-feature pairing, CFK CRD naming, and the 1.5–2× sizing heuristic.
- [x] wiki/patterns/dr-application-routing.md — compiled 2026-05-18 via /wiki:ingest. Pattern article covering the client-plane gap left by data-plane DR (CL/MM2/MRC): three solution classes (DNS abstraction via Consul, protocol proxy via Confluent Gateway/ORKA/Kroxylicious, CC One-Click DR), decision matrix on RTO/restart/listener-config/auth-swap/correctness/vendor-surface, and explicit workload-class discriminator per resolved §5.1 and §5.3 validation reports. ORKA-specific stateful-preservation claims explicitly NOT attributed (vendor-internal). confidence: medium with ⚠️ unverified on One-Click DR GA/surface area pending current confluent-docs revalidation.

## Articles to Expand

<!-- format: - [ ] wiki/concepts/<slug>.md — what is missing -->
- [ ] wiki/patterns/flink-coe-aws-privatelink-refarch.md — stub / confidence: low; expand and MCP-validate (queued by /wiki:lint 2026-11-04)
- [ ] wiki/patterns/flink-coe-optimization.md — stub / confidence: low; expand and MCP-validate (queued by /wiki:lint 2026-11-04)
- [ ] wiki/patterns/flink-coe-security.md — stub / confidence: low; expand and MCP-validate (queued by /wiki:lint 2026-11-04)
- [x] [Queues for Kafka (Share Groups)](wiki/concepts/queues-for-kafka-share-groups.md) — **RESOLVED 2026-06-09** via `outputs/reports/wiki-validation-2026-06-09-queues-for-kafka-share-groups.md`. Promoted confidence:medium → high; group.share.* config names/defaults, ack modes, kafka-share-groups CLI, share.version=1 enablement, and GA (AK 4.2.0 / CC) all MCP-confirmed and markers cleared. One ⚠️ unverified remains by design: exact share-group **metric identities** (Monitoring bullet) — resolve against the observability mapping before alerting.

## Unverified Claims to Resolve

- [ ] wiki/concepts/cluster-linking-topology.md line 68 (Hub-and-Spoke): "Default limit of 10 source clusters per hub" — not found in CP docs pages fetched 2026-09-14 (CC-side limit); ⚠️ unverified this pass — re-check against the Confluent Cloud Cluster Linking limits page.
- [ ] wiki/concepts/cluster-linking-topology.md line 91–93 (CFK ClusterLink CRD): 300-second reconcile, mirror topics created outside CFK deleted on reconcile, failover on CR delete — not checked this pass (CFK docs not fetched); ⚠️ unverified.

<!-- format: - [ ] <article> line N: "<claim>" — source needed -->
- [x] external DR framework document §5.1: "ORKA returns empty fetch responses to pause consumers" — **RESOLVED 2026-05-15** via `outputs/reports/wiki-validation-2026-05-15.md`. Protocol mechanism (FetchResponse interception without rebalance) **confirmed** via Kroxylicious `FetchResponseFilter` upstream + Kafka heartbeat decoupling. ORKA-specific implementation **remains vendor-internal** (no public GoodLabs docs); requires vendor disclosure or wireshark capture to verify. Wiki may describe the *generic* proxy-pause pattern; do not attribute the specific mechanism to ORKA without a vendor citation.
- [x] external DR framework document §5.3: "Kafka guarantees preserved (no duplicates, no missed messages)" — **RESOLVED 2026-05-18** via `outputs/reports/wiki-validation-2026-05-18-orka-guarantees.md`. Scope-limited: (A) **confirmed** for stateless consumers under planned `mirror promote` + CL `consumer.offset.sync.enable=true`; (B) **refuted as a general claim** — Confluent's own client-switchover guidance cautions against this for Kafka Streams / stateful apps (changelog, repartition, in-flight EOS txns, RocksDB state are outside CL's replication boundary); (C) ORKA-specific extension to stateful blue/green is **vendor-internal** (no public GoodLabs docs). When `dr-application-routing.md` stub is authored, it must discriminate workload class explicitly and not attribute stateful guarantee-preservation to ORKA without vendor citation.
- [x] wiki/patterns/fsi-exactly-once.md: "Confluent Cloud Flink transaction commit interval is not documented as user-configurable" — **RESOLVED 2026-06-15** against `confluent-docs` (CC Flink *Delivery Guarantees and Latency*). The ~1-minute commit interval is documented as fixed platform behavior; the only documented user-facing latency lever is consumer `isolation.level`. No support ticket needed — claim is docs-confirmed and the inline marker was retired.
- [x] wiki/concepts/queues-for-kafka-share-groups.md line 63: "`group.share.enable` | Master switch" — **RESOLVED 2026-06-09**: replaced with `share.version=1` feature-flag enablement (`kafka-features.sh upgrade --feature share.version=1`, Kafka 4.1+).
- [x] wiki/concepts/queues-for-kafka-share-groups.md Maturity: "EA/Preview in 4.0, GA targeted later" — **RESOLVED 2026-06-09**: rewritten to EA 4.0 → Preview 4.1 → **GA in Apache Kafka 4.2.0 (Feb 2026)**, GA on CC / shipping CP alongside 4.2. Marker dropped.
- [x] wiki/concepts/queues-for-kafka-share-groups.md config defaults — **RESOLVED 2026-06-09**: filled `group.share.record.lock.duration.ms`=30000, `group.share.delivery.count.limit`=5, `group.share.session.timeout.ms`=45000, `group.share.heartbeat.interval.ms`=5000, `group.share.max.size`=200, `share.acknowledgement.mode`=implicit. Markers dropped.
- [x] wiki/concepts/queues-for-kafka-share-groups.md (How delivery works) — **RESOLVED 2026-06-09**: added **RENEW** acknowledgement type (Kafka 4.2 GA).
- [x] wiki/patterns/fsi-exactly-once.md line 288: "IBM MQ Source Connector exact EOS configuration properties and version requirements" — **RESOLVED 2026-05-18** via `outputs/reports/wiki-validation-2026-05-18-fsi-exactly-once.md`. Confirmed via `confluent-docs` MCP (`kafka-connectors/ibmmq-source/current/overview.html`): EOS requires worker-level `exactly.once.source.support=enabled`, distributed mode, ACLs, `state.topic.name` set, `tasks.max=1`, downstream `isolation.level=read_committed`; version 12.x+. Article enriched and inline `⚠️ unverified` marker removed.

## Lint Findings

<!-- format: - [ ] finding from last lint run -->
<!-- Last lint run: 2026-11-04 (python tools/wiki-lint.py --full): 192 findings, 0 broken links. Orphans auto-fixed in _index.md; stale articles flagged for /wiki:validate (not date-bumped — content is version-bearing). -->
- [ ] stub: wiki/patterns/flink-coe-aws-privatelink-refarch.md
- [ ] stub: wiki/patterns/flink-coe-optimization.md
- [ ] stub: wiki/patterns/flink-coe-security.md
- [x] orphan: wiki/activity/2026-06.md — **FIXED 2026-11-04**: added to wiki/_index.md
- [x] orphan: wiki/activity/2026-08.md — **FIXED 2026-11-04**: added to wiki/_index.md
- [x] orphan: wiki/activity/2026-09.md — **FIXED 2026-11-04**: added to wiki/_index.md
- [x] orphan: wiki/activity/2026-10.md — **FIXED 2026-11-04**: added to wiki/_index.md
- [x] orphan: wiki/incidents/confluent-cloud-on-gcp-starter-2026-05-11.md — **FIXED 2026-11-04**: added to wiki/_index.md
- [ ] stale: wiki/concepts/avro-schema-source-directory.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/azure-connection-management.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/cdc-source-connector-setup.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/confluent-cloud-private-networking.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/confluent-platform-broker-jmx.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/consumer-group-rebalancing.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/consumer-lag-monitoring.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/exactly-once-semantics.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/flink-checkpointing.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/fsi-compliance.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/kafka-connect-deployment-models.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/kafka-streams-architecture.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/kafka-streams-config-baseline.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/kafka-streams-debugging.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/kafka-streams-production-hardening.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/kafka-streams-schema-patterns.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/ksqldb-observability.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/network-connectivity-by-tier.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/observability-metrics-mapping.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/oic-kafka-integration.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/oracle-xstream-source-limitations.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/producer-batching-config.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/queues-for-kafka-share-groups.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/s390x-custom-image-build-pipeline.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/schema-aware-console-producer-required.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/schema-evolution-strategies.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/schema-registry-observability.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/tableflow-changelog-mode-immutability.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/tableflow-iceberg-delta.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/warpstream-config-overrides.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/concepts/warpstream-schema-registry-format-constraint.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/aks-kafka-tuning.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/archival-storage-long-retention-topics.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/audit-log-siem-integration.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/auditor-readonly-rbac-payload-isolation.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/cdc-tableflow-flink-decode-required.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/cdc-to-tableflow-flink-decode.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/cfk-observability-baseline.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/cluster-linking-observability.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/connect-deployment-models.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/consumer-config-fsi.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/cp-mtls-self-signed-setup.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/cp-tls-debugging-by-component.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/dr-mirrormaker2.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/dr-multi-region-cluster.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/flink-coe-aws-privatelink-refarch.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/flink-coe-managed-cc-overview.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/flink-coe-optimization.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/flink-coe-security.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/flink-event-routing.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/flink-on-cfk-fsi-example-jobs.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/flink-runtime-models.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/fsi-exactly-once.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/fsi-governance-automation.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/kafka-streams-topology-patterns.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/latency-optimized-kafka-client.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/low-latency-kafka-azure.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/oci-audit-events-to-splunk.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/producer-config-fsi.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/schema-registry-adoption-playbook.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/schema-registry-shared-types.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/terraform-cicd-confluent-private-networking.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/topic-naming.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/patterns/x86-to-linuxone-cluster-linking-migration.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/synthesis/adr-index.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] stale: wiki/synthesis/confluent-gotchas-top-20.md — >90 days; run /wiki:validate before bumping last_updated
- [ ] low-confidence: wiki/patterns/flink-coe-aws-privatelink-refarch.md
- [ ] low-confidence: wiki/patterns/flink-coe-optimization.md
- [ ] low-confidence: wiki/patterns/flink-coe-security.md
- [ ] unverified: wiki/activity/2026-09.md
- [ ] unverified: wiki/concepts/azure-connection-management.md
- [ ] unverified: wiki/concepts/confluent-cloud-cluster-sku-selection.md
- [ ] unverified: wiki/concepts/confluent-cloud-private-networking.md
- [ ] unverified: wiki/concepts/confluent-platform-broker-jmx.md
- [ ] unverified: wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md
- [ ] unverified: wiki/concepts/kafka-connect-deployment-models.md
- [ ] unverified: wiki/concepts/ksqldb-observability.md
- [ ] unverified: wiki/concepts/linuxone-jdk-tls-gotchas.md
- [ ] unverified: wiki/concepts/observability-metrics-mapping.md
- [ ] unverified: wiki/concepts/oic-kafka-integration.md
- [ ] unverified: wiki/concepts/queues-for-kafka-share-groups.md
- [ ] unverified: wiki/concepts/schema-registry-observability.md
- [ ] unverified: wiki/concepts/tableflow-iceberg-delta.md
- [ ] unverified: wiki/concepts/warpstream-config-overrides.md
- [ ] unverified: wiki/concepts/warpstream-schema-registry-format-constraint.md
- [ ] unverified: wiki/patterns/cluster-linking-observability.md
- [ ] unverified: wiki/patterns/cp-tls-debugging-by-component.md
- [ ] unverified: wiki/patterns/dr-application-routing.md
- [ ] unverified: wiki/patterns/flink-event-routing.md
- [ ] unverified: wiki/patterns/kcp-msk-migration-bastion-host.md
- [ ] unverified: wiki/patterns/latency-optimized-kafka-client.md
- [ ] unverified: wiki/patterns/x86-to-linuxone-cluster-linking-migration.md
- [ ] unverified: wiki/synthesis/confluent-gotchas-top-20.md
- [ ] decayed: wiki/concepts/avro-schema-source-directory.md
- [ ] decayed: wiki/concepts/azure-connection-management.md
- [ ] decayed: wiki/concepts/cdc-source-connector-setup.md
- [ ] decayed: wiki/concepts/confluent-cloud-private-networking.md
- [ ] decayed: wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md
- [ ] decayed: wiki/concepts/fsi-data-streaming-platform.md
- [ ] decayed: wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md
- [ ] decayed: wiki/concepts/kafka-streams-architecture.md
- [ ] decayed: wiki/concepts/kafka-streams-config-baseline.md
- [ ] decayed: wiki/concepts/kafka-streams-debugging.md
- [ ] decayed: wiki/concepts/kafka-streams-production-hardening.md
- [ ] decayed: wiki/concepts/kafka-streams-schema-patterns.md
- [ ] decayed: wiki/concepts/network-connectivity-by-tier.md
- [ ] decayed: wiki/concepts/oracle-xstream-source-limitations.md
- [ ] decayed: wiki/concepts/queues-for-kafka-share-groups.md
- [ ] decayed: wiki/concepts/s390x-custom-image-build-pipeline.md
- [ ] decayed: wiki/concepts/schema-aware-console-producer-required.md
- [ ] decayed: wiki/concepts/schema-evolution-strategies.md
- [ ] decayed: wiki/concepts/schema-registry-observability.md
- [ ] decayed: wiki/concepts/tableflow-changelog-mode-immutability.md
- [ ] decayed: wiki/concepts/tableflow-iceberg-delta.md
- [ ] decayed: wiki/concepts/warpstream-config-overrides.md
- [ ] decayed: wiki/concepts/warpstream-schema-registry-format-constraint.md
- [ ] decayed: wiki/patterns/archival-storage-long-retention-topics.md
- [ ] decayed: wiki/patterns/auditor-readonly-rbac-payload-isolation.md
- [ ] decayed: wiki/patterns/cdc-tableflow-flink-decode-required.md
- [ ] decayed: wiki/patterns/cdc-to-tableflow-flink-decode.md
- [ ] decayed: wiki/patterns/cfk-observability-baseline.md
- [ ] decayed: wiki/patterns/cp-mtls-self-signed-setup.md
- [ ] decayed: wiki/patterns/cp-tls-debugging-by-component.md
- [ ] decayed: wiki/patterns/dead-letter-queue-design.md
- [ ] decayed: wiki/patterns/dr-mirrormaker2.md
- [ ] decayed: wiki/patterns/dr-multi-region-cluster.md
- [ ] decayed: wiki/patterns/flink-coe-managed-cc-overview.md
- [ ] decayed: wiki/patterns/flink-on-cfk-fsi-example-jobs.md
- [ ] decayed: wiki/patterns/fsi-canon-overlay-for-confluent-skills.md
- [ ] decayed: wiki/patterns/fsi-exactly-once.md
- [ ] decayed: wiki/patterns/fsi-governance-automation.md
- [ ] decayed: wiki/patterns/kafka-streams-topology-patterns.md
- [ ] decayed: wiki/patterns/latency-optimized-kafka-client.md
- [ ] decayed: wiki/patterns/schema-registry-adoption-playbook.md
- [ ] decayed: wiki/patterns/schema-registry-shared-types.md
- [ ] decayed: wiki/patterns/terraform-cicd-confluent-private-networking.md
- [ ] decayed: wiki/patterns/topic-naming.md
- [ ] decayed: wiki/patterns/x86-to-linuxone-cluster-linking-migration.md
- [ ] decayed: wiki/synthesis/adr-index.md
- [ ] vendor-drift: DRIFT: wiki/patterns/fsi-canon-overlay-for-confluent-skills.md: source=1.0.0..., pin=91d1871ef8c3...
- [ ] missing-source: STALE-SOURCE-2 wiki/concepts/confluent-platform-broker-jmx.md: URI 'fsi-dsp://observability/grafana' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/concepts/fips-at-install-ocp-requirement.md: URI 'fsi-dsp://accelerator/confluent-on-linuxone' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/concepts/fsi-compliance.md: URI 'fsi-dsp://script/validate-fips' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/concepts/fsi-compliance.md: URI 'fsi-dsp://adr/006' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/concepts/fsi-data-streaming-platform.md: URI 'fsi-dsp://scenario/cc-aws' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/concepts/fsi-data-streaming-platform.md: URI 'fsi-dsp://module/topic' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/concepts/linuxone-kafka-integration.md: URI 'fsi-dsp://adr/009' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/concepts/observability-metrics-mapping.md: URI 'fsi-dsp://observability/metrics-mapping' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/concepts/s390x-custom-image-build-pipeline.md: URI 'fsi-dsp://accelerator/confluent-on-linuxone' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/concepts/schema-evolution-strategies.md: URI 'fsi-dsp://adr/001' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/concepts/schema-evolution-strategies.md: URI 'fsi-dsp://adr/002' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/concepts/sla-tiers.md: URI 'fsi-dsp://role/cp_topic' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/auditor-readonly-rbac-payload-isolation.md: URI 'fsi-dsp://accelerator/confluent-on-linuxone' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/cfk-observability-baseline.md: URI 'fsi-dsp://observability/grafana' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/cluster-linking-observability.md: URI 'fsi-dsp://observability/grafana' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/dr-cluster-linking.md: URI 'fsi-dsp://adr/005' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/dr-cluster-linking.md: URI 'fsi-dsp://script/mirror-failover' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/dr-mirrormaker2.md: URI 'fsi-dsp://adr/005' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/dr-mirrormaker2.md: URI 'fsi-dsp://script/mirror-failback' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/dr-mirrormaker2.md: URI 'fsi-dsp://role/cp_dr_mm2' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/dr-multi-region-cluster.md: URI 'fsi-dsp://adr/008' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/dr-multi-region-cluster.md: URI 'fsi-dsp://script/fsi-dr' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/flink-on-cfk-fsi-example-jobs.md: URI 'fsi-dsp://accelerator/confluent-on-linuxone' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/fsi-governance-automation.md: URI 'fsi-dsp://role/cp_topic' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/fsi-governance-automation.md: URI 'fsi-dsp://role/cp_schema' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/fsi-governance-automation.md: URI 'fsi-dsp://role/cp_rbac' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/linuxone-on-cfk-reference-architecture.md: URI 'fsi-dsp://accelerator/confluent-on-linuxone' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/linuxone-on-cfk-reference-architecture.md: URI 'fsi-dsp://adr/013' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/topic-naming.md: URI 'fsi-dsp://adr/007' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/topic-naming.md: URI 'fsi-dsp://role/cp_topic' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/topic-naming.md: URI 'fsi-dsp://module/topic' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/x86-to-linuxone-cluster-linking-migration.md: URI 'fsi-dsp://accelerator/confluent-on-linuxone' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/patterns/x86-to-linuxone-cluster-linking-migration.md: URI 'fsi-dsp://adr/005' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/synthesis/adr-index.md: URI 'fsi-dsp://adr/001' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/synthesis/adr-index.md: URI 'fsi-dsp://adr/002' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/synthesis/adr-index.md: URI 'fsi-dsp://adr/003' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/synthesis/adr-index.md: URI 'fsi-dsp://adr/004' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/synthesis/adr-index.md: URI 'fsi-dsp://adr/005' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/synthesis/adr-index.md: URI 'fsi-dsp://adr/006' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/synthesis/adr-index.md: URI 'fsi-dsp://adr/007' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/synthesis/adr-index.md: URI 'fsi-dsp://adr/008' resolves to no MANIFEST capability — id removed or never registered
- [ ] missing-source: STALE-SOURCE-2 wiki/synthesis/adr-index.md: URI 'fsi-dsp://adr/009' resolves to no MANIFEST capability — id removed or never registered

## Candidate Articles (from lint / Q&A sessions)

<!-- format: - [ ] <proposed title> — rationale -->

## Auto-Stubs

<!-- Auto-generated by /ask when wiki search returns zero results. Deduped by topic keyword. -->
<!-- format: - [ ] <!-- auto-stub: <slug> --> wiki/concepts/<slug>.md — Auto-queued from /ask -->
<!--         Query: "<query>" | Date: YYYY-MM-DD | Mode: <mode> -->
- [x] <!-- auto-stub: oic-kafka-integration --> wiki/concepts/oic-kafka-integration.md — compiled 2026-05-18 via /wiki:ingest from outputs/reports/oic-cc-acks-all-timeouts-review-2026-04-29.md. Concept article covers OIC Connectivity Agent architecture (JVM hop in OCI publishing to CC on Azure/AWS), GZIP-only compression constraint, partial property passthrough (highest-severity premise from the /review), cross-cloud OCI→Azure RTT timeout overrides on the FSI producer baseline, Azure ILB silent-kill mitigation, CC cluster-side settings, three-layer acks=all timeout triage tree, and EOS implications. confidence: medium with ⚠️ unverified markers on: (1) GZIP-only behavior (Oracle product, not in confluent-docs), (2) Oracle's honored/overridden/ignored property matrix, (3) OIC adapter transactional.id support. Kafka-side claims cross-checked against producer-batching-config, azure-connection-management, producer-config-fsi, and exactly-once-semantics.
- [x] <!-- auto-stub: confluent-cloud-cluster-sku-selection --> wiki/concepts/confluent-cloud-cluster-sku-selection.md — compiled 2026-05-18 via /wiki:ingest. Concept article covering the decision workflow from feature-ceiling question to `confluent kafka cluster create` invocation; ephemeral Basic / prod Enterprise default / Dedicated escape hatch; SKU vs availability vs networking as three orthogonal axes; explicit FSI guardrails (Basic/Standard not prod-capable, fixed RF/min.insync/unclean invariants). Trusts already-MCP-validated `cc-cluster-tiers.md` (2026-05-14) for the tier matrix facts rather than re-deriving them. Two inline ⚠️ unverified markers on: (1) exact (SKU × cloud × region) availability matrix (resolve via `confluent kafka region list` at quote time), (2) `--availability single-zone` CLI flag spelling pending `confluent kafka cluster create --help` re-fetch. confidence: medium.
      Query: "Create a Confluent Cloud Basic Kafka cluster named smoke-test-01 in env-xxxxxx on GCP us-east1" | Date: 2026-05-11 | Mode: ephemeral
- [x] confluent-cloud-cluster-types — addressed by wiki/concepts/cc-cluster-tiers.md (compiled 2026-05-13 from quickstart)
- [x] tableflow-iceberg-delta — addressed by wiki/concepts/tableflow-iceberg-delta.md (compiled 2026-05-18 via /wiki:ingest; MCP-validated against confluent-docs Tableflow overview, catalog integration, schema, and storage concept pages; BYOB→BYOS correction applied)
- [x] kafka-connect-deployment-models — addressed by wiki/concepts/kafka-connect-deployment-models.md (compiled 2026-05-18 via /wiki:ingest; complements the existing pattern article with framework-level architecture)
- [x] linuxone-on-cfk-reference-architecture — compiled 2026-05-23 via Phase 12 plan 12-01 from fsi-dsp://accelerator/confluent-on-linuxone DESIGN.md/README.md (net-new article; not previously queued)
- [x] x86-to-linuxone-cluster-linking-migration — compiled 2026-05-23 via Phase 12 plan 12-01 from fsi-dsp://accelerator/confluent-on-linuxone MIGRATION.md (net-new article; not previously queued)
- [x] fips-at-install-ocp-requirement — compiled 2026-05-23 via Phase 12 plan 12-01 from KNOWN-GAPS.md G-02 + DESIGN.md L126–141 (net-new trip-wire article; not previously queued)
- [x] auditor-readonly-rbac-payload-isolation — compiled 2026-05-23 via Phase 12 plan 12-01 from DESIGN.md D-02 + layers/01-rbac (net-new canonical FSI RBAC pattern; not previously queued)
- [x] s390x-custom-image-build-pipeline — compiled 2026-05-23 via Phase 12 plan 12-01 from KNOWN-GAPS G-05/G-08/G-12 (net-new article; not previously queued)
- [x] flink-on-cfk-fsi-example-jobs — compiled 2026-05-23 via Phase 12 plan 12-01 from layers/05-flink/applications/ + DESIGN.md L176–200 (net-new article; not previously queued)
- [ ] <!-- auto-stub: object-storage-source-connectors --> wiki/concepts/object-storage-source-connectors.md — Auto-queued from /ask. Genuine coverage gap: all existing storage-connector canon is SINK-direction (ADLS Gen2 sink runbook, archival-storage pattern). Needed: the object-storage SOURCE connector family (Azure Blob Storage Source, S3 Source, GCS Source) and the RESTORE_BACKUP-vs-GENERIC mode split; generalized-mode ingest config (`mode=GENERIC`, `topic.regex.list`, `topics.dir`, `CloudStorage*Format` classes, `behavior.on.error`+`parse.error.topic.prefix`); the load-bearing gotchas (offsets tied to connector NAME, no reload on rename/overwrite, at-least-once); and the auth gap (SAS/account-key only, no managed identity). Source material already validated in `outputs/runbooks/adls-blob-source-generalized-aks-runbook.md` (MCP 2026-08-05).
      Query: "ADLS source connector runbook for self-managed Connect on AKS" | Date: 2026-08-05 | Mode: ephemeral
- [ ] <!-- auto-stub: oss-kafka-source-cluster-linking-migration --> wiki/concepts/oss-kafka-source-cluster-linking-migration.md — Auto-queued from /review
      Claim: "Link direction (source- vs destination-initiated) decided per Discovery P4" | Date: 2026-09-14 | Source: destination-cluster-preflight-checklist.md
      Gap: existing CL articles cover CC↔CC and CP↔CP (x86→LinuxONE). Nothing covers an open-source Kafka source: destination-initiated only (source-initiated needs CP 7.8+ source), Kafka 3.8+ source row in the support matrix, transactional topics unsupported, v0/v1 batches fail the mirror, link principal ACLs on an AclAuthorizer source, no REST API needed on either side, offsets.retention.minutes rule. MCP-validated in outputs/reports/osk-to-cp-migration-preflight-review-2026-09-14.md. Also: cluster-linking-topology.md Limitations says transactional records replicate without cross-topic atomicity; confluent-docs says transactional topics are unsupported — /wiki:validate.
- [ ] <!-- auto-stub: cp-ansible-deployment-prerequisites --> wiki/concepts/cp-ansible-deployment-prerequisites.md — Auto-queued from /review
      Claim: "Python version on target hosts matches cp-ansible's supported version" | Date: 2026-09-14 | Source: destination-cluster-preflight-checklist.md
      Gap: no wiki coverage of Ansible Playbooks for Confluent Platform. Needed: CP↔cp-ansible 1:1 version table, Ansible 9–11 / Python 3.10–3.12 for CP 8.x (both nodes), RHEL 8 only with Ansible 9.x, KRaft-only inventory (kraft_controller group) on 8.x, sudo/locale/time-sync/IPv6 prerequisites, Cluster Linking enabled by default since 7.0, audit-logs and RBAC roles. Source: confluent-docs ansible-requirements.html (fetched 2026-09-14).
- [ ] <!-- auto-stub: gateway-observability-grafana-wiring --> wiki/concepts/gateway-observability-grafana-wiring.md — Auto-queued from /review
      Claim: "The gateway admin endpoint on port 9190 exposes /metrics (Prometheus) and JVM metrics enabled by default; wire into the CFK/on-prem Grafana tier alongside broker JMX" | Date: 2026-08-05 | Source: confluent-gateway.md
- [ ] <!-- auto-stub: gateway-centralized-governance-vs-schema-registry --> wiki/concepts/gateway-centralized-governance-vs-schema-registry.md — Auto-queued from /review
      Claim: "Confluent Gateway 1.3.0 centralized governance (EA, Docker-only) enforces schema ID enforcement, deep schema validation, and encryption at the proxy — how this relates to and does not replace native Schema Registry governance" | Date: 2026-08-05 | Source: confluent-gateway.md
- [x] confluent-gateway-terraform-iac — **RESOLVED 2026-08-06**: folded into wiki/concepts/confluent-gateway.md's "Naming and disambiguation" and "Deployment, sizing, and licensing" sections — no Terraform resource exists for either Gateway edition; `confluent_gateway` is the unrelated PrivateLink Gateway resource. No standalone article needed.
      Query: "Is Confluent Gateway controlled by Terraform? If not, what other external components are needed to spin it up outside using terraform?" | Date: 2026-08-06 | Mode: ephemeral
- [x] confluent-cloud-gateway-edition-vs-private-cloud — **RESOLVED 2026-08-06**: initially compiled as a standalone wiki/concepts/confluent-cloud-gateway.md, then **merged back into wiki/concepts/confluent-gateway.md** per explicit follow-up direction — the two backend flavors (`cpc-gateway` self-managed vs `confluent-gateway-for-cloud` CC) are one product differing only by image/license/target, so they live on one page as a "Backend flavor: connecting to a Confluent Cloud cluster" subsection (pointing a route at a CC cluster, auth-swap-vs-passthrough, the SASL/OAUTHBEARER-passthrough-after-failover gotcha). confluent-cloud-private-networking.md (the genuinely separate PrivateLink networking product) keeps its own dedicated page with a strengthened disambiguation callout.
      Query: "How do I point my Confluent Gateway (running on K8s) to my Confluent Cloud cluster?" | Date: 2026-08-06 | Mode: ephemeral
- [ ] <!-- auto-stub: gateway-ha-pod-vs-region-failover --> wiki/concepts/gateway-ha-pod-vs-region-failover.md — Auto-queued from /ask
      Query: "Is there a way to deploy my CC Gateway Highly Available with auto switchover for clients if one pod dies or one region dies?" | Date: 2026-08-06 | Mode: ephemeral
      Note: pod-level HA is free via standard K8s Service/replica behavior; region-level failover (backend cluster or gateway tier itself) has no documented automatic trigger in either Gateway edition — always operator-initiated restart. See outputs/reports/confluent-gateway-iac-cc-connectivity-ha-2026-08-06.md.
- [ ] <!-- auto-stub: confluent-cloud-schema-registry-contexts --> wiki/concepts/confluent-cloud-schema-registry-contexts.md — Auto-queued from /review
      Claim: "Schema contexts are a Confluent Platform feature and are not supported in Confluent Cloud Schema Registry" | Date: 2026-08-07 | Source: confluent-terraform-modules/README.md
