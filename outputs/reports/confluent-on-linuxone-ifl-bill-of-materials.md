---
title: Confluent-on-LinuxONE — IFL Bill of Materials
date: 2026-06-16
source: fsi-dsp://accelerator/confluent-on-linuxone
upstream_sha: 05828eb90b3c508fddd99475b7d3fd42b00f67a3
confidence: medium
---

# Confluent-on-LinuxONE — IFL Bill of Materials

Derived from the `confluent-on-linuxone` accelerator (`overlays/prod`) plus the
pinned Mondics upstream manifest (`base/upstream/confluent-platform-c3++.yaml`,
SHA `05828eb`). **Hard facts** = pinned in committed/fetched CRs. **Planning
assumptions** = explicitly flagged where the manifest leaves `resources:` unset.

## Key finding

The accelerator pins **replica counts and persistent storage** on every core
Confluent component, but **does not pin CPU/memory** on the broker tier — the
upstream `c3++` manifest carries no `resources:` blocks. Only the **two Flink
applications (layer 05) pin CPU** (6 vCPU total, prod overlay). Everything else
schedules at **CFK operator defaults**. So the IFL number is *not* fully
determined by the repo; it's a planning estimate anchored on the pinned facts.

## Component inventory (HARD — from CRs)

| Component | Kind | Source | Replicas | Storage/pod | CPU pinned? |
|-----------|------|--------|---------:|------------:|:-----------:|
| KRaft controllers | `KRaftController` | upstream c3++ | 3 | 10 GiB | ✗ (CFK default) |
| Kafka brokers | `Kafka` | upstream c3++ | 3 | 100 GiB | ✗ (CFK default) |
| Schema Registry | `SchemaRegistry` | upstream c3++ | 3 | — | ✗ (CFK default) |
| ksqlDB | `KsqlDB` | upstream c3++ | 1 | 10 GiB | ✗ (CFK default) |
| Control Center (next-gen) | `ControlCenter` | upstream c3++ | 1 | 10 GiB | ✗ (CFK default) |
| — embedded Prometheus | service | upstream c3++ | 1 | 10 GiB | ✗ |
| — embedded Alertmanager | service | upstream c3++ | 1 | — | ✗ |
| REST Proxy | `KafkaRestProxy` | upstream c3++ | 1 | — | ✗ (CFK default) |
| Connect — lakehouse sinks | `Connect` | layer 06 | 2 | — | ✗ (CFK default) |
| Connect — database connectors | `Connect` | layer 07 | 2 | — | ✗ (CFK default) |
| Flink — txn-volume JobManager | `FlinkApplication` | layer 05 | 1 | — | ✓ 1 vCPU / 2 GiB |
| Flink — txn-volume TaskManager | `FlinkApplication` | layer 05 | 1¹ | — | ✓ 2 vCPU / 4 GiB |
| Flink — enrichment JobManager | `FlinkApplication` | layer 05 | 1 | — | ✓ 1 vCPU / 2 GiB |
| Flink — enrichment TaskManager | `FlinkApplication` | layer 05 | 1¹ | — | ✓ 2 vCPU / 8 GiB |
| **Totals** | | | **~22 pods** | **~360 GiB** | **6 vCPU pinned** |

¹ prod overlay sets `parallelism: 2`; `taskmanager.numberOfTaskSlots: 4` → one TaskManager pod per job.

Note: the upstream `Connect` in `c3++` is **commented out** — the FSI layers 06/07
replace it with two governed Connect clusters. The `producer-app-data.yaml` sample
workload is omitted (validation-only).

## vCPU → IFL translation

OpenShift on LinuxONE runs **SMT-2**: each IFL (a dedicated physical Linux core)
presents as **2 logical CPUs**, and Kubernetes CPU requests/limits are in logical-CPU
units. Therefore:

```
IFLs (to schedule)      = Σ(logical vCPU) / 2
IFLs (with headroom)    = Σ(logical vCPU) / 2 / target_utilization
```

⚠️ **Throughput caveat:** SMT-2 yields ~1.4–1.7× single-thread throughput, **not 2×**.
The /2 divisor is correct for *schedulable capacity* (what K8s requests map to), but
do **not** assume 2 vCPU of real work per IFL — size with headroom, especially for the
latency-sensitive broker and Flink tiers.

## IFL estimate

Two scenarios, because the broker-tier CPU is unpinned:

### Scenario A — as-written (CFK defaults)
The manifest requests no CPU on the core tier, so pods schedule at CFK's modest
operator defaults. This is the **floor to schedule**, not an FSI-prod sizing — it
under-provisions brokers for any real throughput. Order of magnitude: **~6–10 IFLs**
packed (dominated by the 6 pinned Flink vCPU + small default requests). Do not quote
this as a production number.

### Scenario B — FSI-prod-recommended (planning assumption)
Per-pod vCPU sized for prod-grade controls at demo/early-prod throughput. One row per
component tier (data-flow order); no row sums another. `PINNED` = CPU set in the
manifest; `est.` = planning estimate (manifest leaves CPU unset → CFK default).

| Tier | Pods | vCPU/pod | Tier vCPU | Source |
|------|-----:|---------:|----------:|:------:|
| Stream Processing — Apache Flink (JM + TM ×2 jobs) | 4 | 1 / 2 | **6** | `PINNED` |
| Kafka Brokers | 3 | 3 | **9** | `est.` |
| KRaft Controllers | 3 | 1 | **3** | `est.` |
| Schema Registry | 3 | 1 | **3** | `est.` |
| Connect (Lakehouse + Database) | 4 | 1 | **4** | `est.` |
| Control Center + Prometheus + Alertmanager | 3 | 2 / 1 / 0.5 | **3.5** | `est.` |
| REST Proxy | 1 | 1 | **1** | `est.` |
| ksqlDB | 1 | 1 | **1** | `est.` |
| **Total logical vCPU** | **~22** | | **~30.5** | |

IFL totals are computed on the **summary**, never per tier (a single tier is a
fraction of an IFL and misleads if shown alone):

- **Packed (100%):** 30.5 / 2 ≈ **15–16 IFLs**
- **At 60% target utilization:** ≈ **25 IFLs**  ← recommended worker-tier allocation
- **At 50% (latency-conservative):** ≈ **30 IFLs**

**Bottom line:** the accelerator's prod footprint fits in roughly **16 IFLs packed /
~24–26 IFLs with FSI headroom** for the OpenShift *worker* tier — modest for a z16 /
LinuxONE 4 (a single drawer carries dozens of IFLs). Excludes OCP control-plane / infra
nodes (often x86 or separate IFL pool) and the ~360 GiB persistent storage (300 GiB of
it Kafka log volumes).

## To harden this number

1. Decide real broker throughput → set explicit `spec.podTemplate.resources` on the
   `Kafka` CR (the canon default of `6 × peak MB/s` partitions also drives broker CPU).
2. Pin CPU on the Connect clusters (currently default) per connector workload.
3. Confirm SMT mode on the target LPAR (`lscpu` / OCP `MachineConfig`) — if SMT is
   disabled, IFLs = Σ vCPU (no /2).
4. Add OCP platform overhead (control-plane + infra nodes) to the LPAR IFL plan.
