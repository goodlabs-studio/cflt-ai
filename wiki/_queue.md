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
- [ ] [Queues for Kafka (Share Groups)](wiki/concepts/queues-for-kafka-share-groups.md) — authored at confidence:medium; promote to high via /wiki:validate once the Confluent share-groups doc page is reachable through confluent-docs. Resolve the ⚠️ unverified markers: group.share.* config names/defaults, KafkaShareConsumer ack modes, kafka-share-groups CLI path, GA version + CP/CC availability, and share-group metric identities.

## Unverified Claims to Resolve

<!-- format: - [ ] <article> line N: "<claim>" — source needed -->
- [ ] wiki/patterns/low-latency-kafka-azure.md line 51: "`fetch.min.bytes` | 1024" — MCP finding (confluent-docs producer-configs current): actual Apache Kafka / CP default is `1`. Surfaced during validation of `latency-optimized-kafka-client.md` on 2026-05-18 (see `outputs/reports/wiki-validation-2026-05-18-latency-optimized-kafka-client.md`). Suggested: change "Default" column from `1024` to `1`; rationale ("Broker returns immediately with any data") stays.
- [x] kafka-dr-framework-v3.md §5.1: "ORKA returns empty fetch responses to pause consumers" — **RESOLVED 2026-05-15** via `outputs/reports/wiki-validation-2026-05-15.md`. Protocol mechanism (FetchResponse interception without rebalance) **confirmed** via Kroxylicious `FetchResponseFilter` upstream + Kafka heartbeat decoupling. ORKA-specific implementation **remains vendor-internal** (no public GoodLabs docs); requires NDA disclosure or wireshark capture to verify. Wiki may describe the *generic* proxy-pause pattern; do not attribute the specific mechanism to ORKA without a vendor citation.
- [x] kafka-dr-framework-v3.md §5.3: "Kafka guarantees preserved (no duplicates, no missed messages)" — **RESOLVED 2026-05-18** via `outputs/reports/wiki-validation-2026-05-18-orka-guarantees.md`. Scope-limited: (A) **confirmed** for stateless consumers under planned `mirror promote` + CL `consumer.offset.sync.enable=true`; (B) **refuted as a general claim** — Confluent's own client-switchover guidance cautions against this for Kafka Streams / stateful apps (changelog, repartition, in-flight EOS txns, RocksDB state are outside CL's replication boundary); (C) ORKA-specific extension to stateful blue/green is **vendor-internal** (no public GoodLabs docs). When `dr-application-routing.md` stub is authored, it must discriminate workload class explicitly and not attribute stateful guarantee-preservation to ORKA without vendor citation.
- [ ] wiki/patterns/fsi-exactly-once.md line 185: "Confluent Cloud Flink transaction commit interval is not documented as user-configurable" — needs Confluent Support ticket to confirm tunability
- [x] wiki/patterns/fsi-exactly-once.md line 288: "IBM MQ Source Connector exact EOS configuration properties and version requirements" — **RESOLVED 2026-05-18** via `outputs/reports/wiki-validation-2026-05-18-fsi-exactly-once.md`. Confirmed via `confluent-docs` MCP (`kafka-connectors/ibmmq-source/current/overview.html`): EOS requires worker-level `exactly.once.source.support=enabled`, distributed mode, ACLs, `state.topic.name` set, `tasks.max=1`, downstream `isolation.level=read_committed`; version 12.x+. Article enriched and inline `⚠️ unverified` marker removed.

## Lint Findings

<!-- format: - [ ] finding from last lint run -->
<!-- Last lint run: 2026-05-07 after Phase A+B peer-review pass on the four LinuxONE patterns + new linuxone-platform-foundations concept doc. Lint clean except for the pre-existing fsi-exactly-once unverified markers (already tracked above). -->
- [ ] unverified: wiki/patterns/fsi-exactly-once.md (1 remaining inline `⚠️ unverified` marker on CC Flink commit interval; IBM MQ marker resolved 2026-05-18)

## Candidate Articles (from lint / Q&A sessions)

<!-- format: - [ ] <proposed title> — rationale -->

## Auto-Stubs

<!-- Auto-generated by /ask when wiki search returns zero results. Deduped by topic keyword. -->
<!-- format: - [ ] <!-- auto-stub: <slug> --> wiki/concepts/<slug>.md — Auto-queued from /ask -->
<!--         Query: "<query>" | Date: YYYY-MM-DD | Mode: <mode> -->
- [x] <!-- auto-stub: oic-kafka-integration --> wiki/concepts/oic-kafka-integration.md — compiled 2026-05-18 via /wiki:ingest from outputs/reports/oic-cc-acks-all-timeouts-review-2026-04-29.md. Concept article covers OIC Connectivity Agent architecture (JVM hop in OCI publishing to CC on Azure/AWS), GZIP-only compression constraint, partial property passthrough (highest-severity premise from the /review), cross-cloud OCI→Azure RTT timeout overrides on the FSI producer baseline, Azure ILB silent-kill mitigation, CC cluster-side settings, three-layer acks=all timeout triage tree, and EOS implications. confidence: medium with ⚠️ unverified markers on: (1) GZIP-only behavior (Oracle product, not in confluent-docs), (2) Oracle's honored/overridden/ignored property matrix, (3) OIC adapter transactional.id support. Kafka-side claims cross-checked against producer-batching-config, azure-connection-management, producer-config-fsi, and exactly-once-semantics.
- [x] <!-- auto-stub: confluent-cloud-cluster-sku-selection --> wiki/concepts/confluent-cloud-cluster-sku-selection.md — compiled 2026-05-18 via /wiki:ingest. Concept article covering the decision workflow from feature-ceiling question to `confluent kafka cluster create` invocation; ephemeral Basic / prod Enterprise default / Dedicated escape hatch; SKU vs availability vs networking as three orthogonal axes; explicit FSI guardrails (Basic/Standard not prod-capable, fixed RF/min.insync/unclean invariants). Trusts already-MCP-validated `cc-cluster-tiers.md` (2026-05-14) for the tier matrix facts rather than re-deriving them. Two inline ⚠️ unverified markers on: (1) exact (SKU × cloud × region) availability matrix (resolve via `confluent kafka region list` at quote time), (2) `--availability single-zone` CLI flag spelling pending `confluent kafka cluster create --help` re-fetch. confidence: medium.
      Query: "Create a Confluent Cloud Basic Kafka cluster named franz-smoke-01 in env-9y7opm on GCP us-east1" | Date: 2026-05-11 | Mode: ephemeral
- [x] confluent-cloud-cluster-types — addressed by wiki/concepts/cc-cluster-tiers.md (compiled 2026-05-13 from quickstart)
- [x] tableflow-iceberg-delta — addressed by wiki/concepts/tableflow-iceberg-delta.md (compiled 2026-05-18 via /wiki:ingest; MCP-validated against confluent-docs Tableflow overview, catalog integration, schema, and storage concept pages; BYOB→BYOS correction applied)
- [x] kafka-connect-deployment-models — addressed by wiki/concepts/kafka-connect-deployment-models.md (compiled 2026-05-18 via /wiki:ingest; complements the existing pattern article with framework-level architecture)
- [x] linuxone-on-cfk-reference-architecture — compiled 2026-05-23 via Phase 12 plan 12-01 from fsi-dsp://accelerator/confluent-on-linuxone DESIGN.md/README.md (net-new article; not previously queued)
- [x] x86-to-linuxone-cluster-linking-migration — compiled 2026-05-23 via Phase 12 plan 12-01 from fsi-dsp://accelerator/confluent-on-linuxone MIGRATION.md (net-new article; not previously queued)
- [x] fips-at-install-ocp-requirement — compiled 2026-05-23 via Phase 12 plan 12-01 from KNOWN-GAPS.md G-02 + DESIGN.md L126–141 (net-new trip-wire article; not previously queued)
- [x] auditor-readonly-rbac-payload-isolation — compiled 2026-05-23 via Phase 12 plan 12-01 from DESIGN.md D-02 + layers/01-rbac (net-new canonical FSI RBAC pattern; not previously queued)
- [x] s390x-custom-image-build-pipeline — compiled 2026-05-23 via Phase 12 plan 12-01 from KNOWN-GAPS G-05/G-08/G-12 (net-new article; not previously queued)
- [x] flink-on-cfk-fsi-example-jobs — compiled 2026-05-23 via Phase 12 plan 12-01 from layers/05-flink/applications/ + DESIGN.md L176–200 (net-new article; not previously queued)
