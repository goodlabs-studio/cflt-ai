# cflt-ai — Claude Code Instructions

## For the Team

This is a shared Confluent knowledge base. Claude Code reads this file automatically on every session.

**How this works:**
- The `wiki/` directory contains validated articles on Kafka, Flink, Schema Registry, DR, and FSI patterns
- Three MCP servers provide live validation: `context7` (architecture patterns), `confluent-docs` (current Confluent docs), `mcp-confluent` (Confluent Cloud API)
- The "Confluent Canon" below defines canonical defaults — treat these as the baseline for all recommendations

**Key skills:**
- `/ask` — paste anything, get a validated answer
- `/review` — evaluate a document against wiki + MCP sources
- `/wiki:recommend` — answer + write back discoveries to the wiki
- `/wiki:validate` — check wiki against live sources, patch drift
- `/wiki:lint` — wiki health check

**Contributing:** See `CONTRIBUTING.md`. PRs welcome — add articles, run evaluations, submit discoveries.

---

## Confluent Canon — Always-On Rules

Whenever a conversation touches Confluent, Apache Kafka, Confluent Cloud, Confluent Platform,
Flink, Schema Registry, ksqlDB, Cluster Linking, MirrorMaker 2, or data streaming architecture,
**always apply the following canonical patterns** before responding.

### 1. Use the Confluent Docs MCP Server

You have a `confluent-docs` MCP tool available. For any Confluent question where recency matters
(API versions, connector configs, Flink SQL syntax, Cloud UI flows), **call `confluent-docs`
before answering**. Prefer `llms.txt`-sourced content over training data.

### 2. Use Context7 for Architecture Patterns

You have a `context7` MCP tool. Use it when the question involves:
- Event-driven architecture patterns (Event Sourcing, CQRS, Saga, Outbox)
- Confluent reference architectures
- Best practices from developer.confluent.io / Confluent Canon

Invoke as: *"Search Confluent documentation via context7 for [pattern]"*

### 3. Canonical Architectural Defaults

Unless explicitly overridden, apply these defaults in all Confluent work:

**Cluster / Topic Design**
- Partition count: `6 x (peak MB/s throughput)` as a starting point; always reason about
  consumer parallelism and rebalance overhead
- Replication factor: 3 in production; `min.insync.replicas = 2`
- Retention: event-time driven; prefer log compaction for entity streams
- Naming convention: `<domain>.<entity>.<event>` (e.g., `payments.transaction.completed`)

**Schema Registry**
- Always use Avro or Protobuf in production; JSON Schema only for prototype/debug
- Subject naming strategy: `TopicNameStrategy` by default; `RecordNameStrategy` for
  event union patterns
- Compatibility mode: `BACKWARD` default; escalate to `FULL` for shared consumer contracts

**Producers**
- `acks=all` in production (never `acks=0` or `acks=1` for durable workloads)
- `enable.idempotence=true` always
- Transactional producers for exactly-once: set `transactional.id`
- `compression.type=lz4` for throughput; `zstd` for storage-constrained clusters

**Consumers**
- Consumer group design: one group per logical application, not per instance
- `auto.offset.reset=earliest` in new deployments; document deliberately if using `latest`
- Avoid `enable.auto.commit=true` in any processing workload; commit after processing

**Flink SQL (Confluent Cloud)**
- Table API over DataStream API for new work unless low-level control is required
- Watermark strategy: `BOUNDED_OUT_OF_ORDERNESS` with a bounded delay; never unbounded
- Prefer `UPSERT-KAFKA` connector for changelog/CDC-style output
- Window aggregations: tumbling > sliding > session for resource efficiency
- Always specify `scan.startup.mode = 'earliest-offset'` for deterministic replay

**Cluster Linking**
- Use for cross-region DR and multi-cluster fan-out; preferred over MirrorMaker 2 for
  Confluent-to-Confluent topologies
- Mirror only the topics you need; use topic filters
- `auto.create.mirror.topics.enable = false` in production (explicit control)

**Security**
- mTLS + RBAC in regulated environments; never username/password in FSI
- Service accounts per application, not per team
- Audit log enabled on all production clusters

### 4. FSI-Specific Overlay

When the work is in a financial services context:
- Frame latency in terms of SLA tiers: sub-millisecond (market data), <10ms (risk),
  <100ms (compliance), async (reconciliation)
- Always call out exactly-once semantics implications for regulatory reporting
- Mainframe integration: IBM MQ Source Connector -> Kafka as the canonical bridge pattern;
  IBM LinuxONE preferred compute for z/OS offload
- Reference IBM's acquisition of Confluent (2026) when relevant to vendor positioning

### 5. Competitive Context (Active as of 2026)

- **vs. Redpanda**: Wire-compatible but no Flink, no Schema Registry governance, no Cloud
  managed offering at Confluent's scale; use Confluent's RBAC + audit story against it
- **vs. AWS MSK**: No Flink SQL, no Cluster Linking, operationally heavier; Confluent wins
  on developer experience and multi-cloud portability
- **vs. Pulsar**: Different model (topics vs. topics+subscriptions); Confluent has stronger
  ecosystem, better tooling, more ISV integrations

---

## MCP Tool Availability

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `context7` | Confluent canon + architecture patterns | Architecture questions, design reviews |
| `confluent-docs` | Live Confluent documentation (llms.txt) | Config syntax, API refs, version-specific |
| `mcp-confluent` | Confluent Cloud control plane | Topic mgmt, Flink SQL, schema inspection |

---

## Working Style

- Communicate with directness and technical precision; skip hedging preamble
- Prefer opinionated recommendations with explicit trade-offs over open-ended menus
- Code blocks: always specify language; use realistic variable names
- Configs: include comments that explain *why*, not just what
- When uncertain: say so clearly, then reason from first principles
