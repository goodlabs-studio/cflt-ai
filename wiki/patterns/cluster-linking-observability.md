---
title: Cluster Linking Observability — DR / RPO / RTO Dashboards
tags: [observability cluster-linking dr rpo rto mirror-topic confluent-cloud confluent-platform fsi metrics-api]
sources:
  - https://docs.confluent.io/cloud/current/multi-cloud/cluster-linking/dr-failover.html
  - https://docs.confluent.io/cloud/current/multi-cloud/cluster-linking/index.html
  - https://docs.confluent.io/cloud/current/multi-cloud/cluster-linking/metrics-cc.html
  - raw/repos/fsi-dsp/observability/grafana/dashboard-dr-readiness.json
  - raw/repos/fsi-dsp/observability/grafana/README.md
related:
  - patterns/dr-cluster-linking
  - patterns/dr-mirrormaker2
  - patterns/cfk-observability-baseline
  - concepts/confluent-platform-broker-jmx
  - concepts/observability-metrics-mapping
  - concepts/sla-tiers
  - patterns/fsi-l1-reference-architecture
confidence: medium
last_updated: 2026-05-20
last_validated: 2026-05-20
---

# Cluster Linking Observability — DR / RPO / RTO Dashboards

## Summary

Cluster Linking (CL) is the data-plane mechanism behind active-passive DR on Confluent Cloud (CC) and CC↔CP hybrid topologies. The observability story is shaped by two questions: "how much data could we lose right now?" (RPO, derived from mirror lag) and "how fast can we cut over?" (RTO, driven by client bootstrap + offset sync). This pattern documents the canonical metrics — CC Metrics API mirror lag + `cluster_link_destination_response_bytes`, REST/CLI `PartitionMirrorLag`, mirror topic states (`PENDING_STOPPED`, `STOPPED`, `SOURCE_UNAVAILABLE`) — wired into per-SLA-tier dashboards, plus the failover-readiness signals (consumer offset sync currency, ACL parity, secondary-region client connectivity) that distinguish a green DR dashboard from one that's only green by accident.

## Pattern

### When to use

- DR observability for CC↔CC, CC↔CP, or CP↔CP topologies linked via Cluster Linking
- FSI tenants with regulatory RPO / RTO obligations (compliance tier: RPO < 30s, RTO measurable in minutes)
- Active-passive or hub-spoke topologies (see [DR — Cluster Linking](dr-cluster-linking.md))

Use [DR — MirrorMaker 2](dr-mirrormaker2.md) observability instead for CFK/CP topologies that haven't moved to CL.

### Architecture

```
                ┌──────────────────┐                       ┌──────────────────┐
                │ Source cluster   │                       │ Destination     │
                │ (primary region) │──── cluster link ─────│ cluster (DR)    │
                │                  │                       │                  │
                │ topic.orders     │                       │ topic.orders    │
                │  (writable)      │                       │  (mirror,       │
                └──────────────────┘                       │   read-only)    │
                        │                                  └──────────────────┘
                        │                                          │
                        ▼                                          ▼
                 Metrics API + JMX                            Metrics API + JMX
                        │                                          │
                        └──────────────┬───────────────────────────┘
                                       ▼
                              ┌──────────────────┐
                              │ DR Readiness     │
                              │ Dashboard        │  (Grafana / Dynatrace / …)
                              │ (Row 1: lag)     │
                              │ (Row 2: states)  │
                              │ (Row 3: clients) │
                              └──────────────────┘
```

### Step 1 — Mirror lag (the RPO metric)

The single load-bearing CL metric is per-partition mirror lag — records the destination has not yet caught up to the source. Three surfaces:

| Surface | Source | Use |
|---|---|---|
| CC Metrics API | `io.confluent.kafka.server/cluster_link_destination_response_bytes` (confirmed 2026-05-20) plus the dedicated mirror lag metric documented at https://docs.confluent.io/cloud/current/multi-cloud/cluster-linking/metrics-cc.html — exposed per topic | Dashboard tile + alert rule per-topic-per-tier |
| CLI / REST | `confluent kafka mirror describe <topic> --link <link-name>` returns `PartitionMirrorLag` per partition; `confluent kafka mirror list --link <link-name>` returns `Max Per Partition Mirror Lag`. REST endpoints `/links/<link-name>/mirrors` and `/links/<link-name>/mirrors/<topic-name>` return a `mirror_lags` array with `last_source_fetch_offset` | Synthetic monitor + dashboard data source when Metrics API name drift is suspected |
| JMX (CP self-managed) | `kafka.server:type=ClusterLinkFetcherManager,name=ConsumerLag,clientId=*,link=*,topic=*,partition=*` | CP/CFK cluster linking; analogous to the JMX `FetcherLagMetrics` for follower lag |

> ⚠️ unverified — the exact CC Metrics API identifier for mirror lag (referenced in the docs anchor `cluster-link-lag-cc`) was not fully surfaced in the 2026-05-20 MCP fetch. Validate against the live tenant via the [Metrics Reference](https://docs.confluent.io/cloud/current/monitoring/metrics-reference.html) before writing alert rules. `cluster_link_destination_response_bytes` is confirmed and useful as a "is the link flowing?" proxy.

> ⚠️ unverified — the JMX MBean path for CP self-managed CL fetcher lag is plausible (mirrors the standard `kafka.server:type=FetcherLagMetrics` shape per [Confluent Platform Broker JMX](../concepts/confluent-platform-broker-jmx.md)) but was not directly MCP-confirmed in this pass. Verify with `jconsole` against a CP 7.5+ cluster before relying on the exact attribute name in production alerts.

### Step 2 — Time-based lag (the RPO conversation customers actually have)

Convert offset lag to seconds for tier-aware alerts. Two derivation patterns:

**Pattern A — divide by source throughput rate** (the fsi-dsp DR readiness dashboard uses this):

```promql
# PromQL — derived "mirror lag in seconds"
confluent_kafka_server_cluster_link_mirror_topic_offset_lag{kafka_id="$CLUSTER_ID"}
  / on(topic) rate(confluent_kafka_server_received_records{kafka_id="$CLUSTER_ID"}[5m])
```

```dql
# Dynatrace DQL equivalent
timeseries offset_lag = avg(confluent_kafka_server.cluster_link_mirror_topic_offset_lag),
           by:{topic}, from:now()-15m
| join (timeseries rcv = rate(confluent_kafka_server.received_records, time:5m), by:{topic})
       on:{topic}
| fieldsAdd mirror_lag_seconds = offset_lag[-1] / rcv[-1]
```

**Pattern B — message timestamp delta** (broker-side; more accurate at low throughput):

Read the latest offset on source vs destination and diff their `LogAppendTime` timestamps. Requires consumer instrumentation on both sides; useful when source throughput is intermittent (small denominator on Pattern A blows up the lag-seconds number).

### Step 3 — Mirror topic state machine

Mirror topics have a small but operationally critical state machine (MCP-confirmed 2026-05-20):

| State | What it means | Alert |
|---|---|---|
| (active, healthy) | Mirroring normally | — |
| `PENDING_STOPPED` | Transitional — `stop` command issued, not yet quiesced | Informational; if stuck > 5 min = P3 |
| `STOPPED` | Mirror is paused; `failover` / `promote` may have been called | Confirms failover progression; pair with `PartitionMirrorLag` at the time of stop |
| `SOURCE_UNAVAILABLE` | Source cluster unreachable from destination | P1 if not part of a deliberate failover |

The CLI surfaces this via `confluent kafka mirror list --mirror-status <state>`. Build a dashboard tile per state (count of mirror topics in that state). Alert on `SOURCE_UNAVAILABLE > 0` outside a maintenance window.

### Step 4 — Failover readiness checklist (the RTO conversation)

Mirror lag tells you RPO. RTO is **client-side** — bootstrap time, ACL parity, schema availability. Surface these as dashboard tiles:

| Signal | What it measures | Target |
|---|---|---|
| Cluster link state (`confluent_kafka_server_cluster_link_state`) | Is the link up and healthy? | `= 1` (active); 0 = link down |
| Mirror topic `lag = 0` OR `lag < consumer group lag` | Whether failover is safe right now | Tier-aware (critical: lag == 0; standard: lag < cg_lag) |
| Consumer offset sync currency (CL config: `consumer.offset.sync.enable=true`) | Are consumer offsets being mirrored? | Last sync timestamp within 60s |
| Mirror ACL sync currency (CL config: `acl.sync.enable=true`) | Are RBAC/ACLs synchronized? | Last sync timestamp within 5 min |
| DR cluster client bootstrap latency | Time to first record from DR bootstrap | < 30s; surfaced via synthetic monitor |
| Schema Registry availability on DR side | Mirrored schemas resolvable on DR? | HTTP 200 on `/subjects/<test>/versions/latest` |

### Step 5 — Per-SLA-tier alert thresholds (from ADR-008)

The fsi-dsp DR readiness dashboard ships with per-tier thresholds aligned to ADR-008 — these are the canonical FSI defaults:

| SLA Tier | Mirror lag warn | Mirror lag alert | DR priority |
|---|---|---|---|
| critical | 30s | 60s | P1 — immediate failover |
| compliance | 10s | 30s | P1 — immediate failover |
| standard | 5 min (300s) | 15 min (900s) | P2 — business hours |
| best-effort | 1 hour (3600s) | 4 hours (14400s) | P3 — next business day |

See [SLA Tiers](../concepts/sla-tiers.md) for tier definitions; thresholds reproduced here for convenience.

### Step 6 — Dashboard layout (Row 1 health, Row 2 lag, Row 3 readiness)

The fsi-dsp `dashboard-dr-readiness.json` template ships in all six provider directories (Grafana, Dynatrace, Splunk, Datadog, New Relic, Instana). Three-row layout:

- **Row 1 — Link health**: cluster link state per link, mirror topic count by state (active / PENDING_STOPPED / STOPPED / SOURCE_UNAVAILABLE)
- **Row 2 — Mirror lag**: per-topic lag in records (line chart), per-topic lag in seconds (derived; see Step 2), max lag across all topics (single-value with tier-aware threshold)
- **Row 3 — Failover readiness**: consumer offset sync currency, ACL sync currency, DR cluster synthetic-monitor results, schema-resolution test result

Click-through from Row 1 → Row 2 → Row 3 mirrors the diagnostic flow: "is the link healthy?" → "how far behind?" → "can we cut over right now?"

### Step 7 — Cross-provider query examples

See [Observability Metrics Mapping](../concepts/observability-metrics-mapping.md) for the full table. Highlights:

| Provider | "Max mirror lag across topics" |
|---|---|
| Grafana (PromQL) | `max(confluent_kafka_server_cluster_link_mirror_topic_offset_lag{kafka_id="$CLUSTER_ID"})` |
| Dynatrace (DQL) | `timeseries v = max(confluent_kafka_server.cluster_link_mirror_topic_offset_lag), by:{kafka_id} \| filter kafka_id == "$CLUSTER_ID"` |
| Datadog | `max:confluent_kafka_server.cluster_link_mirror_topic_offset_lag{kafka_id:$CLUSTER_ID}` |
| Splunk SPL | `index=kafka source=confluent_metrics metric_name="cluster_link_mirror_topic_offset_lag" kafka_id="$CLUSTER_ID" \| stats max(_value)` |
| New Relic NRQL | `SELECT max(cluster_link_mirror_topic_offset_lag) FROM ConfluentCloudMetric WHERE kafka_id = '$CLUSTER_ID'` |

## When to Use

- DR observability is a CC↔CC, CC↔CP, or CP↔CP active-passive deployment with Cluster Linking enabled
- Tenant has formal RPO / RTO obligations (FSI compliance or critical tier)
- A failover-readiness dashboard is needed to gate `failover` / `promote` commands during real incidents
- Hybrid Cloud / Bridge-to-Cloud topologies where the DR side is in a different cloud provider

## Caveats

- **5-minute CC Metrics API latency**: mirror lag from the Metrics API is published with a ~5 min offset. For critical-tier (sub-60s RPO) workloads, supplement with the CLI/REST `PartitionMirrorLag` via synthetic monitor — that surface is closer to real-time.
- **Mirror topic lag ≠ data loss bound**: lag in records doesn't account for compaction; on a heavily-compacted topic, a destination `n` records behind may have all the load-bearing data while a less-compacted topic with the same lag has lost more. Pair the metric with `confluent.value.schema.validation` audit if the topic has compaction enabled.
- **Cluster Linking does not support exactly-once semantics across the link**: transactional / EOS topics do not mirror cleanly. Don't try to instrument an RPO on an EOS source topic — the lag metric will mislead. See [Exactly-Once Semantics](../concepts/exactly-once-semantics.md).
- **`SOURCE_UNAVAILABLE` is "normal" during deliberate source-cluster shutdown** — don't page on it during a planned switchover. Suppress alerts during the maintenance window.
- **Consumer offset sync lag is a separate signal from mirror lag**: a topic can have `lag=0` while consumer offsets are stale. Alert on both. Critical-tier RTO depends on both being current.
- **PartitionMirrorLag CLI/REST is per-partition** — the dashboard tile should aggregate to topic max, not topic mean (a single hot partition is still a failover blocker even if the mean looks fine).
- **CP self-managed cluster linking** (CP 7.5+) exposes JMX MBeans but the exact attribute identifiers may differ from the broker-side conventions documented in [Confluent Platform Broker JMX](../concepts/confluent-platform-broker-jmx.md) — validate per CP release.
- **Bridge-to-cloud topologies**: when the destination is in a different cloud, network egress cost is real. Dashboard a "mirror cost projection" tile (lag bytes × egress unit cost) for cost-governance — separate from the operational RPO concern but tracks alongside.

## Related

- [DR — Cluster Linking](dr-cluster-linking.md) — operational pattern this dashboards
- [DR — MirrorMaker 2](dr-mirrormaker2.md) — alternative replication backend (different observability surface)
- [CFK Observability Baseline](cfk-observability-baseline.md) — host platform for self-managed CL observability
- [Confluent Platform Broker JMX](../concepts/confluent-platform-broker-jmx.md) — JMX MBean reference (CP self-managed CL)
- [Observability Metrics Mapping](../concepts/observability-metrics-mapping.md) — cross-provider query syntax for CL metrics
- [SLA Tiers](../concepts/sla-tiers.md) — tier-to-RPO/RTO threshold mapping
- [FSI Reference Architecture — LinuxONE](fsi-l1-reference-architecture.md) — operational→analytical bridge via CL → CC Tableflow → Databricks consumes this DR pattern
