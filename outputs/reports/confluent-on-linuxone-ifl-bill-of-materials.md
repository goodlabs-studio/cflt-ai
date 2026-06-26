---
title: Confluent on LinuxONE — Bill of Materials & IFL Sizing
date: 2026-06-16
scope: Production Medium (100 MB/s) anchor, with PoC and Enterprise tiers
sources_validated: confluent-docs MCP (CP 8.2/8.3 system-requirements + s390x support), 2026-06-16
---

# Confluent on LinuxONE — Bill of Materials & IFL Sizing

> **Provenance.** Two kinds of numbers live in this report, kept deliberately separate:
> - **Confluent canon** — per-component hardware from Confluent's own docs, MCP-validated
>   via `confluent-docs`. See [Confluent published guidance](#confluent-published-guidance-mcp-validated).
> - **GoodLabs field heuristic** — the throughput→IFL tier bands and the 100 MB/s BOM.
>   These are field-calibrated estimates, **not** Confluent-published. Marked as such
>   wherever they appear.
>
> Confluent publishes **no LinuxONE/Z-specific sizing** — its guidance is explicitly
> architecture-agnostic ("the CPU resource requirement is the same for all platforms").
> The IFL translation below is ours; Confluent counts cores ≈ CPU-units 1:1 and never
> mentions IFLs.

## IFLs vs. vCPUs vs. Pods — the three units

These three count *different things*. Conflating them is the usual source of
mis-sizing.

| Unit | What it is | Who allocates it | How you count it |
|------|-----------|------------------|------------------|
| **Pod** | The smallest deployable unit in OpenShift. Each Confluent process runs in its own pod — one Kafka broker = one pod, one Flink TaskManager = one pod, one Connect worker = one pod. A pod *declares* a CPU + memory request. | The platform team, via CR replica counts. | Headcount of running processes. |
| **vCPU** (logical CPU) | The scheduling unit Kubernetes/OpenShift bills against. A pod's CPU request/limit is expressed in vCPU. One vCPU = **one hardware thread**. | OpenShift scheduler, from the sum of pod requests. | Σ of all pod CPU requests. |
| **IFL** (Integrated Facility for Linux) | A **physical** IBM Z processor core licensed to run Linux. This is what you actually buy/provision on the LinuxONE box. | The hardware/LPAR plan. | Physical cores in the LPAR. |

**The relationship (the only formula you need):**

```
Pods request vCPU   →   OpenShift sums vCPU   →   Physical IFLs = vCPU ÷ 2

(LinuxONE runs SMT-2: each IFL exposes 2 hardware threads,
 so OpenShift sees 2 vCPU per IFL.)
```

You **buy IFLs**, you **schedule vCPU**, you **run pods**. A 16-pod deployment
requesting 14 vCPU needs ~7 IFLs of physical capacity.

> SMT-2 nuance: two threads per IFL give ~1.4–1.7× the throughput of one, **not 2×**.
> The ÷2 is correct for *schedulable capacity*; the IFL counts in the tier table
> below already fold in operational headroom — do not also multiply by a utilization
> factor.

## Confluent published guidance (MCP-validated)

Validated 2026-06-16 against `confluent-docs` (CP 8.2/8.3 *System Requirements* and
*Linux on IBM Z (s390x) support*). These are Confluent's numbers — quote them as canon.

**Platform support.** s390x (Linux on IBM Z) is a first-class CP architecture from
**8.2.0+**. Supported on s390x: RPM/Debian/Tarball install, Docker images, **Confluent
for Kubernetes**, **Confluent Platform for Apache Flink**, Confluent CLI, most connectors.
**Not yet supported on s390x:** `FIPS mode`, IPv6, Unified Stream Manager Agent,
connectors that rely on native OS libraries. **Linux on IBM Z only — z/OS is not
supported** (use the Connect-on-z/OS bridge for mainframe sources). Requires a separate
IBM Z software entitlement from IBM.

> Cross-check: this confirms the accelerator's KNOWN-GAPS **G-02 (FIPS-at-install)** is a
> genuine platform gap, not a config defect — FIPS mode is documented as unsupported on s390x.

**Per-component hardware (architecture-agnostic reference).** Confluent's *"good starting
point based on production clusters; actual requirements depend on your workload."* The CPU
figure is identical whether bare-metal or Kubernetes (cores ≈ CPU-units, 1:1, no SMT
accounting).

| Component | Nodes | RAM | CPU | Storage |
|-----------|------:|-----|-----|---------|
| **Kafka broker** | 3 | 64 GB | **24 cores** | 12 × 1 TB; RAID 10 optional; OS disk separate |
| **KRaft controller** | 3–5 | 4 GB | 4 cores | 64 GB SSD |
| **Confluent Manager for Flink (CMF)** | 1 pod | 4 GB | 3 cores | 10 GB PV — *manages 150 Flink apps* |
| **Connect** | 2 | 0.5–4 GB heap | not CPU-bound ("more cores > faster cores") | install-time only |
| **Schema Registry** | 2 | 1 GB heap | not CPU-bound | install-time only |
| **REST Proxy** | 2 | 1 GB + 64 MB/producer + 16 MB/consumer | 16 cores | install-time only |
| **ksqlDB** | 2 | 20 GB | 4 cores | ≥ 100 GB SSD |
| **Control Center** (next-gen) | 1 | ≥ 8 GB | 4+ cores | 200 GB SSD |

**Flink sizing.** Confluent publishes sizing only for **CMF** (the Flink control plane:
3 cores / 4 GB to manage 150 apps). There is **no per-`FlinkApplication`
JobManager/TaskManager table** — that's generic Flink capacity planning, left to the
workload (which is why the accelerator hard-codes its own JM/TM resources). CC Flink is
serverless (CFU-based) with no infra sizing.

## Sizing tiers — GoodLabs field heuristic (NOT Confluent canon)

⚠️ **Field heuristic.** The throughput→IFL bands below are GoodLabs field estimates for
fast LPAR planning. Confluent publishes the per-component reference above, **not** a
throughput→IFL curve — do not cite this table as vendor guidance.

| Deployment Scale | Data Throughput | Total Physical IFLs | Min. System Memory | Best Deployment Pattern |
|------------------|-----------------|---------------------|--------------------|-------------------------|
| Proof of Concept / Dev | < 10 MB/s | 2 – 3 IFLs | 32 GB | Single LPAR / shared KVM |
| **Production Medium** | **100 MB/s** | **6 – 8 IFLs** | **256 GB** | **Red Hat OpenShift (RHOCP)** |
| Enterprise Large | > 500 MB/s | 16+ IFLs | 512 GB+ | Dedicated IFL LPARs per cluster tier |

## Broker re-anchor: from Confluent's 24-core reference to 100 MB/s

Confluent's reference broker is **24 cores / 64 GB** — but that's a *full-throughput*
starting point, not a 100 MB/s figure. Taken literally on LinuxONE it implies:

```
24 CPU-units (K8s)  ÷ 2 (SMT-2)  = 12 IFLs per broker   →  3 brokers ≈ 36 IFLs (brokers alone)
```

That lands in Confluent's high-throughput regime (≫ 100 MB/s), i.e. the Enterprise tier.
For 100 MB/s you **scale the broker down** from the reference:

| | Confluent reference (full load) | 100 MB/s anchor (scaled) |
|---|---|---|
| Throughput target | high (≫ 100 MB/s) | 100 MB/s |
| CPU / broker | 24 cores | **~4 vCPU** (≈ 1/6 of reference; brokers scale ~linearly with MB/s) |
| RAM / broker | 64 GB | 32 GB (heap modest; rest is page cache) |
| Brokers | 3 | 3 |

The scale-down is the **GoodLabs field heuristic** — Confluent gives the full-load anchor;
the linear-with-throughput interpolation to 100 MB/s is ours. The BOM below uses the scaled
**4 vCPU/broker**. (The earlier draft used 2 vCPU/broker; 4 is the more defensible read of
the 24-core reference at 100 MB/s.)

## Bill of materials — Production Medium (100 MB/s) — field heuristic

⚠️ Per-pod vCPU/memory are GoodLabs estimates scaled from the Confluent reference above —
not Confluent-published. RF=3, `min.insync.replicas=2`, KRaft. Canon partition starting
point: `6 × 100 = 600`. One row per component tier.

| Component (pod) | Pods | vCPU / pod | vCPU total | Mem / pod | Mem total | Local storage |
|-----------------|-----:|-----------:|-----------:|----------:|----------:|---------------|
| Kafka brokers | 3 | 4 | 12.0 | 32 GB | 96 GB | ~2 TB/broker (NVMe/FCP) |
| KRaft controllers | 3 | 0.5 | 1.5 | 4 GB | 12 GB | 10 GB/pod |
| Schema Registry | 2 | 0.5 | 1.0 | 4 GB | 8 GB | — |
| Connect (workers) | 2 | 1 | 2.0 | 8 GB | 16 GB | — |
| Flink (1 job: JobManager + TaskManager) | 2 | 1 / 2 | 3.0 | 2 / 6 GB | 8 GB | — |
| Control Center + Prometheus | 2 | 1 / 0.5 | 1.5 | 6 / 4 GB | 10 GB | 10 GB |
| REST Proxy | 1 | 0.5 | 0.5 | 2 GB | 2 GB | — |
| **Totals** | **15** | | **~21.5 vCPU** | | **~152 GB** | **~6 TB hot** |

**IFL rollup:**

- Σ requests ≈ **21.5 vCPU** → **÷ 2 (SMT-2) ≈ 11 physical IFLs**.
- Memory: ~152 GB of pod requests → provision **256 GB system memory**. The gap is
  OpenShift/OS overhead plus the **Kafka page cache**, which is not a pod request but
  is where broker read/write performance actually lives.
- **Storage is retention-driven, not throughput-driven.** Local volumes hold the *hot*
  set only (~hours): `100 MB/s × RF 3 × hot_window`. For regulatory retention (OFAC/AML
  up to 7 years) use **Tiered Storage** to an object store — keep broker NVMe modest.

> **Reconciliation — the bottom-up BOM (~11 IFLs) exceeds the 6–8 IFL band.** That gap is
> the whole reason the tier band is a *heuristic*: it assumes a leaner broker (~2 vCPU)
> **or** a higher per-broker throughput in Confluent's 24-core reference than the 1/6 scale
> used here. Brokers are the entire swing — at 2 / 3 / 4 vCPU/broker the total is
> ~16 / ~18 / ~21 vCPU → **~8 / ~9 / ~11 IFLs**. **Treat 6–8 IFLs as optimistic and
> ~8–11 IFLs as the defensible bottom-up bracket for 100 MB/s**; pin the real number with a
> load test once peak MB/s and per-broker partition counts are known.

## Scaling the anchor

- **< 10 MB/s (PoC/Dev):** drop to 1 broker tier, single Flink slot, no C3/Prometheus →
  ~4–5 vCPU → **2–3 IFLs**, 32 GB, single LPAR.
- **> 500 MB/s (Enterprise):** brokers dominate and scale ~linearly with throughput
  (canon `6 × peak MB/s` partitions also drives broker CPU). Separate the broker, Flink,
  and Connect tiers onto **dedicated IFL LPARs** so a Flink backfill can't starve broker
  I/O → **16+ IFLs**, 512 GB+.

## Notes on the committed accelerator

The `confluent-on-linuxone` accelerator (`overlays/prod`, upstream SHA `05828eb`) pins
**replica counts and storage but no broker CPU** — only the two Flink apps pin CPU
(6 vCPU). Its replica shape (3 brokers / 3 controllers / 3 SR) matches the Production
Medium row above; the per-pod vCPU/memory here are the prod-sizing values you would add
to the `Kafka`/`Connect`/`SchemaRegistry` CRs before running at 100 MB/s. The manifest's
`100Gi`/broker volume is demo-only — replace per the retention formula above.
