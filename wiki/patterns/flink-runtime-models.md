---
title: Flink Runtime Models — CC Managed, CMF, and Self-Managed
tags: [flink, confluent-cloud, cmf, cfk, runtime, state-ttl, watermarks, upsert-kafka]
sources: [outputs/reports/confluent-best-practices-quickstart.md]
related: [concepts/flink-checkpointing, patterns/linuxone-flink-validation-tuning, concepts/exactly-once-semantics, concepts/schema-registry-best-practices]
confidence: medium
last_updated: 2026-05-13
last_validated: 2026-05-13
---

# Flink Runtime Models — CC Managed, CMF, and Self-Managed

## Summary

Three ways to run Flink against Confluent: **Confluent Cloud for Apache Flink** (serverless SQL/Table API), **Confluent Manager for Apache Flink (CMF)** on CFK/K8s, and **self-managed open-source Flink**. The defaults that apply on every model: bounded watermarks with idleness timeout, `state-ttl` on every non-windowed stateful op, `upsert-kafka` for changelog output, `scan.startup.mode=earliest-offset` for deterministic replay, Table API over DataStream API for new work. Pairs with `concepts/flink-checkpointing.md` (checkpoint mechanics) and `patterns/linuxone-flink-validation-tuning.md` (CMF on s390x specifics).

## Pattern

### The three runtime models

| Model | What it is | You own |
|---|---|---|
| **Confluent Cloud for Apache Flink** (fully managed) | Serverless Flink SQL (+ Table API). Kafka topics auto-appear as tables (catalog = environment, database = cluster). Compute pools sized in **CFUs**. Checkpointing fully managed. | Statement SQL, statement properties, `max_cfu` per pool, state TTL. *Not* checkpoint intervals, state backends, parallelism internals. |
| **Confluent Manager for Apache Flink (CMF)** on CFK/K8s | Confluent-supported Flink Operator + management plane for CP. Application & session deployments. | Everything: checkpointing (`execution.checkpointing.interval`), state backend (RocksDB + incremental + S3/filesystem for checkpoints), parallelism, `taskmanager.numberOfTaskSlots`, memory (`taskmanager.memory.process.size` + managed-memory fraction), restart strategy, K8s HA, savepoints/upgrades. See `fsi-dsp:scenarios/cfk-openshift/flink/`. |
| **Self-managed open-source Flink** against CC/CP Kafka | DIY. Supported by the community, not Confluent. | All of the above, plus you're on your own for support. |

> ⚠️ On CC, the surface is SQL + Table API. There is no DataStream API on CC. Confirm current capability via `confluent-docs` MCP if you're committing to a customer.

### Best practices (apply on every model)

- **Watermarks** — `BOUNDED_OUT_OF_ORDERNESS` with a *bounded* delay; never unbounded (Canon). And set **`table.exec.source.idle-timeout`** (or per-source idleness) — otherwise a quiet partition stalls the global watermark and **windows never fire** ("my aggregation produces nothing" — almost always this).
- **State TTL — the big one.** Unbounded **regular joins** and **non-windowed aggregations** keep state **forever** unless you set `sql.state-ttl` (CC) / `table.exec.state.ttl` (CP). This is the #1 surprise CFU/cost blow-up and OOM cause. Set a TTL on *every* non-windowed stateful operator. Prefer **interval joins**, **temporal (versioned-table) joins**, and **lookup joins** — they have bounded state by construction.
- **Windows** — tumbling < sliding/hop < session in resource cost (Canon: prefer tumbling). Use modern **window TVFs** (`TUMBLE`, `HOP`, `CUMULATE`) over legacy grouped-window syntax. `CUMULATE` for early-fire dashboards.
- **Changelog output** — `upsert-kafka` for CDC-style / aggregated output keyed by PK (Canon); plain `kafka` connector for append-only streams.
- **Determinism** — `scan.startup.mode=earliest-offset` for reproducible replay (Canon); `latest-offset` for ephemeral/exploratory.
- **Schema** — Flink reads Avro/Protobuf/JSON-SR from Schema Registry automatically on CC; mind key format vs value format.
- **Table API over DataStream API** for new work unless you need low-level control (Canon).
- **CP serialization** — POJO/Avro/Row types — **never let it fall back to Kryo** (silent throughput killer; you'll see it in the logs as "must be processed as GenericType").
- **Don't** build huge fan-out regular joins on non-key columns — that's the state-explosion footgun.

### CC compute pool sizing

- Start `max_cfu` = **5 dev / 10–20 staging / 20–50 prod** (`fsi-dsp:modules/flink/variables.tf` validation set: 5/10/20/30/40/50).
- CFU burn ∝ statement parallelism × state size × throughput. **The biggest single variable is state** — so set `sql.state-ttl` on every unbounded stateful op before sizing anything.
- **`max_cfu` cannot be decreased after creation** — size to realistic peak, not paranoid peak.
- One pool per environment/team boundary (isolation + billing clarity). Pool exhaustion → statements stuck `PENDING`; raise `max_cfu` or split work.

## When to Use

- **CC Flink** — first choice for new SQL/Table API workloads on Confluent Cloud. No checkpoint or state-backend ops.
- **CMF on CFK** — you're on CP/CFK already, want Confluent-supported Flink, and need control over checkpointing/state-backend/parallelism. Also: LinuxONE/s390x deployments (see `patterns/linuxone-flink-validation-tuning.md`).
- **Self-managed Flink** — you genuinely need open-source freedom, custom connectors not yet supported on CMF, or a specific upstream Flink version Confluent hasn't picked up.

## Caveats

- **Watermarks don't advance if a partition is idle** → windows never fire → silent output. Set `table.exec.source.idle-timeout`.
- **Unbounded regular joins / non-windowed aggregations keep state forever** without `state-ttl`. The #1 CFU blow-up cause on CC. Prefer interval/temporal/lookup joins.
- **`max_cfu` cannot be decreased** after pool creation on CC.
- **No DataStream API on CC.** SQL + Table API only.
- **CP serialization fallback to Kryo is silent throughput death.** Use Avro/Row/POJO with proper getters/setters.

### Triage

| Symptom | Cause | First moves |
|---|---|---|
| Backpressure (high `busyTimeMsPerSecond` / `backPressuredTimeMsPerSecond`) | Downstream operator bottleneck — skewed keys, slow sink, under-parallelized, RocksDB disk I/O | Find the first backpressured operator from the *sink* upward; that's the culprit. Rebalance keys / add parallelism / speed the sink. |
| Checkpoints timing out / failing (CP) — or statement `DEGRADED` (CC) | Backpressure (barriers can't flow), huge state, slow checkpoint storage, RocksDB pressure | CP: enable **unaligned checkpoints**, tune RocksDB, faster checkpoint store, raise timeout, reduce state (TTL!). CC: usually a schema/permission issue on a source/sink topic, or pool out of CFUs. |
| Windows never produce output | Watermark not advancing — idle partition with no idleness timeout, or watermark delay too tight, or event-time skew | Set `table.exec.source.idle-timeout`; check source's event-time field; loosen the bound. |
| State growth / OOM / runaway CFUs | Missing TTL on regular join or non-windowed agg; `COUNT(DISTINCT ...)` over unbounded high-cardinality key; `GROUP BY` on a near-unique key | Add `state-ttl`; switch to interval/temporal/lookup join; reconsider the key. |
| Statement stuck `PENDING` (CC) | Compute pool out of CFU capacity | Raise `max_cfu` (cannot be decreased); or split work across pools. |
| Job won't restore from savepoint after code change (CP) | Operator UID / job graph changed → state can't be mapped | Assign stable operator UIDs; restore with `--allowNonRestoredState` or start fresh. |
| "GenericType / Kryo" in CP logs, throughput tanks | Type the framework couldn't analyze → Kryo serialization | Use Avro/Row/POJO with proper getters/setters; register types; never ship Kryo in prod. |

## Related

- [Flink Checkpointing](../concepts/flink-checkpointing.md) — Chandy-Lamport barriers, aligned vs unaligned, state backends
- [LinuxONE Flink Validation & Tuning](linuxone-flink-validation-tuning.md) — CMF on s390x, Telum II inference from Flink UDFs
- [Exactly-Once Semantics](../concepts/exactly-once-semantics.md) — Flink two-phase commit
- [Schema Registry Best Practices](../concepts/schema-registry-best-practices.md) — Flink auto-reads SR
- [Top 20 Confluent Gotchas](../synthesis/confluent-gotchas-top-20.md) — #14 (state-TTL), #15 (idleness timeout), #16 (max_cfu)
