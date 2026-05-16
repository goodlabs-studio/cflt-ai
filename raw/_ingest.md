---
title: Ingest Queue
last_updated: 2026-05-15
---

# Ingest Queue

Files listed here are pending compilation into the wiki.
Run: `python tools/wiki-compile.py --delta` to process.

## Pending

<!-- format:
- path: raw/articles/my-article.md
  source_url: https://...
  added: YYYY-MM-DD
  notes: optional context for the compiler
-->

- path: kafka-best-practices.md
  added: 2026-04-17
  notes: C4E wiki stub covering broker, producer, consumer, app-level, AKS, CC ops, and monitoring guidance for fraud detection on CC + Azure AKS. Compile into wiki/concepts/azure-connection-management.md and wiki/patterns/latency-optimized-kafka-client.md.

- path: kafka-recommendations.md
  added: 2026-04-17
  notes: Detailed 4-phase triage/remediation plan for e2e latency on CC Dedicated + Azure AKS. Keep as report in outputs/reports/. Source for wiki stubs on azure-connection-management and latency-optimized-kafka-client.

# === Phase H.1: confluent-agent-skills@91d1871e ingest queue ===

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/SKILL.md
  added: 2026-05-16
  notes: |
    Trip-wire #1 (H.1). Target: wiki/concepts/tableflow-changelog-mode-immutability.md (concept, ≤500 words).
    Single-fact-focused: "Tableflow changelog mode is immutable after first materialization."
    FULL MCP-validation gate (D-07): query confluent-docs for Tableflow materialization semantics,
    especially `changelog` mode behavior on schema/topic changes. Set confidence: high only after the
    MCP gate passes. Extend frontmatter with source/upstream_path. related: patterns/cdc-to-tableflow-flink-decode
    (parent #7), patterns/cdc-tableflow-flink-decode-required (sibling trip-wire #2),
    concepts/oracle-xstream-source-limitations (sibling #3).

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/SKILL.md
  added: 2026-05-16
  notes: |
    Trip-wire #2 (H.1). Target: wiki/patterns/cdc-tableflow-flink-decode-required.md (pattern, ≤500 words).
    Single-fact-focused: "Don't enable Tableflow on a CDC source topic — tombstones break APPEND mode;
    decode via Flink first, sink to a clean topic, then enable Tableflow on the clean topic."
    FULL MCP-validation gate (D-07): confluent-docs for Tableflow APPEND vs CHANGELOG mode tombstone
    handling. Frontmatter source/upstream_path. related: patterns/cdc-to-tableflow-flink-decode (parent #7),
    concepts/tableflow-changelog-mode-immutability (sibling #1).

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/SKILL.md
  added: 2026-05-16
  notes: |
    Trip-wire #3 (H.1). Target: wiki/concepts/oracle-xstream-source-limitations.md (concept, ≤500 words).
    Single-fact-focused: "OracleXStreamSource doesn't support `after.state.only` — workaround is a
    Flink transform on the source topic before sinking to the target topic."
    FULL MCP-validation gate (D-07): confluent-docs for OracleXStreamSource connector config.
    Frontmatter source/upstream_path. related: wiki/concepts/cdc-source-connector-setup (parent #8 — where
    connector configs live).

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/SKILL.md
  source_url: also-cite. raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/evals/evals.json
  added: 2026-05-16
  notes: |
    Trip-wire #4 (H.1). Target: wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md
    (concept, ≤500 words). Single-fact-focused: "In Kafka Streams 4.x, StreamsUncaughtExceptionHandler
    lives in `org.apache.kafka.streams.errors`, NOT as a nested class under `KafkaStreams`. Import path
    changed in the 4.x refactor."
    FULL MCP-validation gate (D-07): confluent-docs for KS 4.x package structure; context7 fallback for
    KIP references if applicable. Include a 3-line code snippet showing the correct import statement
    (Java). NOTE: the evals/evals.json file referenced in source_url is intentionally NOT vendored
    (excluded in Task 1 per D-02 — see also D-02/D-05 tension note above); cite its existence in the
    wiki body as upstream proof of the trip-wire's importance, but the citation path is the SKILL.md,
    not the evals.json. Frontmatter source/upstream_path.
    related: wiki/concepts/kafka-streams-debugging (parent #2),
    wiki/concepts/kafka-streams-production-hardening (parent #3).

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/SKILL.md
  source_url: also-cite. raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/evals/evals.json
  added: 2026-05-16
  notes: |
    Trip-wire #5 (H.1). Target: wiki/concepts/avro-schema-source-directory.md (concept, ≤500 words).
    Single-fact-focused: "Avro schemas live in `src/main/avro/` (the Avro Maven plugin convention),
    NOT `src/main/resources/avro/`. Code generation breaks silently if put in resources/."
    FULL MCP-validation gate (D-07): context7 for Avro Maven Plugin canonical layout; confluent-docs
    fallback for Confluent Schema Registry Maven Plugin layout. Include a 4-line `pom.xml` snippet
    showing the plugin's expected source directory. Frontmatter source/upstream_path. evals.json source
    cited by path in body prose only (file not vendored per D-02 — see D-02/D-05 tension note above).
    related: wiki/concepts/kafka-streams-debugging (parent #2),
    wiki/concepts/kafka-streams-schema-patterns (parent #4).

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/SKILL.md
  source_url: also-cite. raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/evals/evals.json
  added: 2026-05-16
  notes: |
    Trip-wire #6 (H.1). Target: wiki/concepts/schema-aware-console-producer-required.md (concept, ≤500 words).
    Single-fact-focused: "`kafka-console-producer` doesn't speak Schema Registry — using it against a
    SR-governed topic ships records WITHOUT the magic-byte+schema-id prefix and breaks all SR-aware
    consumers. Use `kafka-avro-console-producer` (or `kafka-protobuf-console-producer` / `kafka-json-schema-console-producer`)
    for verification on SR-governed topics."
    FULL MCP-validation gate (D-07): confluent-docs for `kafka-avro-console-producer` CLI usage and the
    wire format magic-byte. Include a 2-line CLI invocation example. Frontmatter source/upstream_path.
    evals.json source cited by path in body prose only (file not vendored per D-02 — see D-02/D-05
    tension note above).
    related: wiki/concepts/schema-registry-best-practices, wiki/concepts/kafka-streams-debugging (parent #2).

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/developing-kafka-python-client/SKILL.md
  source_url: also-cite. raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/warpstream-optimization.md
  added: 2026-05-16
  notes: |
    Trip-wire #7 (H.1). Target: wiki/concepts/warpstream-schema-registry-format-constraint.md (concept, ≤500 words).
    Single-fact-focused: "WarpStream's built-in Schema Registry only supports Avro and Protobuf;
    `GET /schemas/types` returns `[\"AVRO\",\"PROTOBUF\"]` — no JSON Schema support."
    FULL MCP-validation gate (D-07): cannot validate via confluent-docs (WarpStream is not Confluent);
    rely on context7 search of WarpStream's docs OR mark verifiable claims with ⚠️ unverified inline
    and downgrade confidence to medium IF the majority of claims are unverifiable; otherwise keep high.
    MANDATORY: include the verbatim "FSI context" paragraph from CONTEXT.md <specifics> immediately
    after the trip-wire claim — this is non-negotiable per the vendor-backing rule (feedback memory).
    Frontmatter source/upstream_path (upstream_path is the SKILL.md path).
    related: wiki/concepts/schema-registry-best-practices,
    wiki/concepts/warpstream-config-overrides (sibling #8),
    wiki/concepts/exactly-once-v2-warpstream-throughput-cost (sibling #9).

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/warpstream-optimization.md
  added: 2026-05-16
  notes: |
    Trip-wire #8 (H.1). Target: wiki/concepts/warpstream-config-overrides.md (concept, ≤500 words).
    Single-fact-focused: "WarpStream does not honor `fetch.min.bytes` (silently ignored), and
    `replication.factor` is cosmetic (the WarpStream tier always replicates 3-way internally regardless
    of the value set on topic creation)."
    FULL MCP-validation gate (D-07): same caveat as #7 — context7 fallback, inline ⚠️ unverified where
    WarpStream docs are silent.
    MANDATORY: include the verbatim "FSI context" paragraph from CONTEXT.md <specifics>.
    Frontmatter source/upstream_path. related: wiki/concepts/warpstream-schema-registry-format-constraint
    (sibling #7), wiki/concepts/exactly-once-v2-warpstream-throughput-cost (sibling #9),
    wiki/concepts/kafka-streams-config-baseline (parent #5).

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/warpstream-optimization.md
  added: 2026-05-16
  notes: |
    Trip-wire #9 (H.1). Target: wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md (concept, ≤500 words).
    Single-fact-focused: "Enabling `processing.guarantee=exactly_once_v2` in Kafka Streams turns on
    idempotent producers internally, which throttles in-flight request concurrency. On WarpStream's
    S3-backed storage tier this translates to a meaningful throughput hit; on classic Kafka the cost is
    present but smaller. Quantify before turning on for high-throughput WarpStream pipelines."
    FULL MCP-validation gate (D-07): confluent-docs for `processing.guarantee=exactly_once_v2`
    semantics and idempotent producer constraints (max.in.flight.requests.per.connection ≤5).
    context7 fallback for WarpStream-specific impact.
    MANDATORY: include the verbatim "FSI context" paragraph from CONTEXT.md <specifics>.
    Frontmatter source/upstream_path. related: wiki/concepts/exactly-once-semantics,
    wiki/concepts/warpstream-config-overrides (sibling #8),
    wiki/concepts/kafka-streams-production-hardening (parent #3).

## Processed

- path: <none — MCP-only ingest>
  source_url: |
    https://docs.confluent.io/cloud/current/networking/aws-platt.md
    https://docs.confluent.io/cloud/current/networking/azure-platt.md
    https://docs.confluent.io/cloud/current/networking/gcp-platt.md
    https://docs.confluent.io/cloud/current/networking/private-links/aws-privatelink-gateway.md
    https://docs.confluent.io/cloud/current/networking/private-links/azure-privatelink-gateway.md
    https://docs.confluent.io/cloud/current/networking/private-links/gcp-private-service-connect-gateway.md
    https://docs.confluent.io/cloud/current/flink/concepts/flink-private-networking.md
    https://docs.confluent.io/cloud/current/flink/concepts/flink-private-networking-egress.md
  added: 2026-05-15
  notes: |
    /wiki:ingest invoked with target wiki/concepts/private-networking.md and the
    following topic anchors: PrivateLink Gateway (replacing PLATT, AWS 2026-02-12 /
    Azure+GCP 2026-05-04), Azure/AWS/GCP Private Link setup, Enterprise vs Dedicated
    cluster requirements, Flink-to-Kafka internal routing (gateway covers client→Flink
    only; Flink↔Kafka stays on Confluent fabric), egress PrivateLink for external
    services (AWS/Azure only — no GCP), and the Azure ILB idle-timeout bypass via
    Private Link. No raw/ source file — content compiled directly from confluent-docs
    MCP pages (PLATT pages per cloud, PrivateLink Gateway pages per cloud, Flink
    private-networking ingress and egress pages). All claims validated against those
    MCP sources except the Azure ILB idle-timeout default/max values, which carry an
    inline ⚠️ unverified tag (architectural claim — that Private Link bypasses the
    ILB — is sound; specific timeout numbers should be reconfirmed via current Azure
    docs before customer-facing use). confidence: high.
  compiled: 2026-05-15
  wiki_articles:
    - wiki/concepts/private-networking.md

- path: <none — MCP-only ingest>
  source_url: |
    https://docs.confluent.io/cloud/current/flink/overview.md
    https://docs.confluent.io/cloud/current/flink/concepts/compute-pools.md
    https://docs.confluent.io/cloud/current/flink/concepts/statements.md
    https://docs.confluent.io/cloud/current/flink/concepts/autopilot.md
    https://docs.confluent.io/cloud/current/flink/concepts/schema-statement-evolution.md
    https://docs.confluent.io/cloud/current/flink/concepts/timely-stream-processing.md
    https://docs.confluent.io/cloud/current/flink/operate-and-deploy/flink-rbac.md
  added: 2026-05-15
  notes: |
    /wiki:ingest invoked with target wiki/concepts/flink-confluent-cloud-setup.md and
    seven topic anchors (compute pools, catalog/db/table mapping, dual-plane RBAC,
    statement lifecycle, Autopilot, watermarks, statement evolution + carry-over
    offsets). No raw/ source file — content compiled directly from confluent-docs MCP
    pages (CC Flink overview, compute pools, statements, autopilot, schema-statement
    evolution, timely-stream-processing, flink-rbac). All verifiable claims validated
    against those MCP pages. confidence: high.
  compiled: 2026-05-15
  wiki_articles:
    - wiki/concepts/flink-confluent-cloud-setup.md

- path: raw/articles/shared-schema-howto.md
  added: 2026-05-15
  notes: |
    FSI shared-types library walk-through (Money, MemberId, UsAddress, payments-value
    referencing both). Compiled into a new pattern article covering library layout,
    schema references mechanics (name+subject+exact version, registered first, pinned),
    Schema Registry ID assignment behavior, and the FULL_TRANSITIVE → BACKWARD_TRANSITIVE
    interaction across shared and domain subjects. NFCU references replaced with
    "FSI firm" / `com.fsifirm.common` namespace per ingest args. Validated schema
    references mechanics and subject-version-ID semantics via confluent-docs
    (Confluent Platform serdes-develop, schema-references and subject-name-strategy
    sections).
  compiled: 2026-05-15
  wiki_articles:
    - wiki/patterns/schema-registry-shared-types.md

- path: outputs/reports/confluent-best-practices-quickstart.md
  added: 2026-05-13
  notes: |
    786-line FSI-flavored quickstart spanning producers, consumers, topics/clusters
    (CC vs CP), Schema Registry, Connect, Flink, Tableflow, K8s/CFK, security,
    networking, capacity planning, triage tree, and Top-20-gotchas appendix.
    Validated via /review (outputs/reports/confluent-best-practices-quickstart-review-2026-05-12.md).
    Split into 8 focused articles per ingest routing hints. Recency-sensitive
    items (CC cluster/Freight specs, per-CKU limits, Tableflow GA surface,
    KIP-848 client matrix, Custom Connector on PrivateLink) flagged inline
    with ⚠️ unverified; confidence set to medium pending an MCP revalidation
    pass via /wiki:validate.
    fsi-dsp follow-up still pending: verify
    reference/java-producer/FsiProducer.java and reference/java-consumer/FsiConsumer.java
    exist in fsi-dsp; propose PRs if not.
  compiled: 2026-05-13
  wiki_articles:
    - wiki/patterns/producer-config-fsi.md
    - wiki/patterns/consumer-config-fsi.md
    - wiki/concepts/cc-cluster-tiers.md
    - wiki/concepts/schema-registry-best-practices.md
    - wiki/patterns/connect-deployment-models.md
    - wiki/patterns/flink-runtime-models.md
    - wiki/concepts/network-connectivity-by-tier.md
    - wiki/synthesis/confluent-gotchas-top-20.md

- path: raw/repos/fsi-dsp/README.md
  source_url: https://github.com/goodlabs-studio/fsi-dsp
  notes: Top-level platform overview — compile into wiki/concepts/ and wiki/patterns/
  compiled: 2026-04-11
  wiki_articles:
    - wiki/concepts/fsi-data-streaming-platform.md
    - wiki/patterns/fsi-governance-automation.md

- path: raw/repos/fsi-dsp/docs/dr-runbook.md
  notes: DR procedures for CL, MM2, MRC — compile into wiki/patterns/dr-*
  compiled: 2026-04-11
  wiki_articles:
    - wiki/patterns/dr-cluster-linking.md
    - wiki/patterns/dr-mirrormaker2.md
    - wiki/patterns/dr-multi-region-cluster.md

- path: raw/repos/fsi-dsp/docs/schema-guide.md
  notes: Schema naming, compatibility, evolution — expand wiki/concepts/schema-evolution-strategies.md
  compiled: 2026-04-11
  wiki_articles:
    - wiki/concepts/schema-evolution-strategies.md

- path: raw/repos/fsi-dsp/docs/compliance-guide.md
  notes: FSI regulatory reference — new wiki/concepts/fsi-compliance.md
  compiled: 2026-04-11
  wiki_articles:
    - wiki/concepts/fsi-compliance.md

- path: raw/repos/fsi-dsp/ansible/vars/sla_tiers.yml
  notes: SLA tier definitions — new wiki/concepts/sla-tiers.md
  compiled: 2026-04-11
  wiki_articles:
    - wiki/concepts/sla-tiers.md

- path: raw/repos/fsi-dsp/ansible/vars/naming_rules.yml
  notes: Topic naming rules — expand wiki/concepts/ or new wiki/patterns/topic-naming.md
  compiled: 2026-04-11
  wiki_articles:
    - wiki/patterns/topic-naming.md

- path: raw/repos/fsi-dsp/docs/adr
  notes: Compile all ADRs into wiki/synthesis/adr-index.md with summaries
  compiled: 2026-04-11
  wiki_articles:
    - wiki/synthesis/adr-index.md

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/topology-patterns.md
  added: 2026-05-16
  notes: |
    Parent article #1 of 10 (H.1). Target: wiki/patterns/kafka-streams-topology-patterns.md (pattern template).
    Frontmatter: extend with `source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4`
    and `upstream_path: skills/kafka-streams-programming/references/topology-patterns.md`.
    Provenance footer per CONTEXT.md D-03 shape.
    Confidence: high via source attestation (D-07) — skip the full MCP re-validation gate; upstream evals
    gate at 90%+ before merge so source attestation suffices. /wiki:ingest Step 3d remains for cross-link
    accuracy but does not block confidence: high.
    related: cross-link to existing wiki articles where natural (e.g., concepts/exactly-once-semantics,
    patterns/dr-cluster-linking) plus the trip-wires this article seeds (#4, #5, #6).
  compiled: 2026-05-16
  wiki_articles:
    - wiki/patterns/kafka-streams-topology-patterns.md

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/debugging.md
  added: 2026-05-16
  notes: |
    Parent article #2. Target: wiki/concepts/kafka-streams-debugging.md (concept template).
    Extend frontmatter with source/upstream_path. confidence: high via source attestation (D-07).
    Seeds trip-wires #4 (uncaught-exception-handler-import), #5 (avro-schema-source-directory),
    #6 (schema-aware-console-producer). related: cross-link to those trip-wire articles via `related:`.
  compiled: 2026-05-16
  wiki_articles:
    - wiki/concepts/kafka-streams-debugging.md

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/production-hardening.md
  added: 2026-05-16
  notes: |
    Parent article #3. Target: wiki/concepts/kafka-streams-production-hardening.md (concept).
    Extend frontmatter with source/upstream_path. confidence: high via source attestation.
    related: cross-link to concepts/exactly-once-semantics, patterns/producer-config-fsi,
    patterns/consumer-config-fsi.
  compiled: 2026-05-16
  wiki_articles:
    - wiki/concepts/kafka-streams-production-hardening.md

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/schema-patterns.md
  added: 2026-05-16
  notes: |
    Parent article #4. Target: wiki/concepts/kafka-streams-schema-patterns.md (concept).
    Extend frontmatter. confidence: high via source attestation.
    related: concepts/schema-registry-best-practices, concepts/schema-evolution-strategies,
    patterns/schema-registry-shared-types.
  compiled: 2026-05-16
  wiki_articles:
    - wiki/concepts/kafka-streams-schema-patterns.md

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/config-baseline.md
  added: 2026-05-16
  notes: |
    Parent article #5. Target: wiki/concepts/kafka-streams-config-baseline.md (concept).
    Extend frontmatter. confidence: high via source attestation.
    related: patterns/producer-config-fsi, patterns/consumer-config-fsi.
  compiled: 2026-05-16
  wiki_articles:
    - wiki/concepts/kafka-streams-config-baseline.md

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/architecture.md
  added: 2026-05-16
  notes: |
    Parent article #6. Target: wiki/concepts/kafka-streams-architecture.md (concept).
    Extend frontmatter. confidence: high via source attestation.
    related: concepts/fsi-data-streaming-platform, concepts/exactly-once-semantics,
    patterns/flink-runtime-models.
  compiled: 2026-05-16
  wiki_articles:
    - wiki/concepts/kafka-streams-architecture.md

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/flink-sql-patterns.md
  added: 2026-05-16
  notes: |
    Parent article #7. Target: wiki/patterns/cdc-to-tableflow-flink-decode.md (pattern).
    Extend frontmatter (upstream_path: skills/confluent-cloud-cdc-tableflow/references/flink-sql-patterns.md).
    confidence: high via source attestation.
    Seeds trip-wires #1 (tableflow-changelog-mode-immutability), #2 (cdc-tableflow-flink-decode-required).
    related: concepts/exactly-once-semantics, concepts/flink-checkpointing,
    concepts/flink-confluent-cloud-setup, and the two trip-wire descendants.
  compiled: 2026-05-16
  wiki_articles:
    - wiki/patterns/cdc-to-tableflow-flink-decode.md

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/connector-configs.md
  source_url: |
    Also merges:
      raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/database-prerequisites.md
      raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/references/troubleshooting.md
  added: 2026-05-16
  notes: |
    Parent article #8 — THREE-WAY MERGE into a single wiki/concepts/cdc-source-connector-setup.md.
    Section ordering (Claude's Discretion per CONTEXT.md): (1) Database prerequisites first, (2) Connector
    config recipes second, (3) Troubleshooting last as a triage table — mirrors operational reading order
    (pre-deploy → deploy → debug). Cite all three upstream_paths in frontmatter as a yaml list:
      upstream_path:
        - skills/confluent-cloud-cdc-tableflow/references/connector-configs.md
        - skills/confluent-cloud-cdc-tableflow/references/database-prerequisites.md
        - skills/confluent-cloud-cdc-tableflow/references/troubleshooting.md
    Provenance footer should list all three files. Seeds trip-wire #3 (oracle-xstream-source-limitations).
    confidence: high via source attestation. related: patterns/cdc-to-tableflow-flink-decode,
    patterns/connect-deployment-models.
  compiled: 2026-05-16
  wiki_articles:
    - wiki/concepts/cdc-source-connector-setup.md

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/detection-patterns.md
  source_url: |
    Also merges:
      raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/code-migration.md
  added: 2026-05-16
  notes: |
    Parent article #9 — TWO-WAY MERGE into wiki/patterns/schema-registry-adoption-playbook.md (pattern).
    Section ordering: (1) Detection patterns first (scan existing Kafka usage), (2) Code migration second
    (Terraform generation + producer/consumer migration). upstream_path is a yaml list of both files.
    Provenance footer lists both. confidence: high via source attestation.
    related: concepts/schema-registry-best-practices, concepts/schema-evolution-strategies,
    patterns/fsi-governance-automation.
  compiled: 2026-05-16
  wiki_articles:
    - wiki/patterns/schema-registry-adoption-playbook.md

- path: raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/schema-inference.md
  source_url: |
    Also merges:
      raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/references/categorization.md
  added: 2026-05-16
  notes: |
    Parent article #10 — TWO-WAY MERGE into wiki/concepts/schema-inference-and-pii-categorization.md (concept).
    Section ordering: (1) Schema inference (deriving Avro from data samples), (2) Categorization (PII
    tagging on inferred schemas). upstream_path lists both. Provenance footer lists both.
    confidence: high via source attestation.
    related: concepts/schema-registry-best-practices, concepts/fsi-compliance,
    patterns/schema-registry-shared-types.
  compiled: 2026-05-16
  wiki_articles:
    - wiki/concepts/schema-inference-and-pii-categorization.md
