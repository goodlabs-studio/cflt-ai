> Part of **Flink Center of Excellence — Managed Flink on Confluent Cloud** (self-contained series). Validated against Confluent documentation 2026-07-30.

# Part 2 — Optimization (CFUs, Autopilot, State, Statement Lifecycle)

On Managed Flink you do **not** tune parallelism, checkpoint intervals, or state backends — Autopilot and the serverless runtime own those. What you control is CFU pool sizing, state growth, watermark tolerance, and statement lifecycle. Cost is driven by **throughput rate and state size, not event count.**

## CFU sizing & Autopilot

- **Maximum 50 CFU per compute pool** (both default and user-created). A single statement can scale up to the full pool capacity, so the practical maximum for one statement is 50 CFU. Pools with up to **1,000 CFU are available as Limited Availability (LA)** for large job fleets; even there, a single job's maximum remains 50 CFU, and concurrent jobs cannot collectively exceed the pool ceiling.
- **Pools scale down to zero** when no statement is running — no cost at rest.
- **CFU burn is proportional to throughput rate × state size**, not total event count — e.g. tens of millions of events at hundreds-to-low-thousands events/sec typically settle at ~1–3 CFU via Autopilot.
- **Autopilot** handles autoscaling and parallelism inside the pool — there is no manual parallelism knob. It ramps over several minutes on a backfill; watch the "Messages Behind" metric (it spikes, then converges to zero).
- **Size to realistic peak.** Reducing a pool's maximum CFU after creation is a change to validate against current tooling behavior before relying on it (the CLI/Terraform behavior for lowering the ceiling is version-dependent and was not confirmed against docs here) *(unverified)*. Run larger workloads by distributing statements across multiple pools.
- One pool per team/environment boundary. `OrganizationAdmin` can raise the default 50-CFU platform limit.

## State & watermarks (the cost blow-up)

- **`sql.state-ttl` on every non-windowed stateful operator.** Unbounded regular joins and non-windowed aggregations keep state forever otherwise — the #1 CFU blow-up and out-of-memory cause. Prefer interval, temporal (versioned-table), and lookup joins — they are bounded by construction. Pure filter/projection statements are stateless and need no TTL.
- **Default watermark = ~180 ms** bounded out-of-orderness on `$rowtime`. Retune for batch-loaded/historical data (high out-of-orderness) or windows never fire. Set an idleness timeout (`sql.tables.scan.idle-timeout`) so a quiet partition does not stall the global watermark and silently prevent all window output.

## Statement lifecycle (immutability drives your deploy model)

- **Statements are immutable** — the SQL cannot be edited after submission. To change a statement you stop the old one and create a new one.
- **Statements snapshot their catalog objects at creation** — a later change to a source schema or watermark does **not** propagate to a running statement.
- **Stateless carry-over offsets:** for a stateless (filter/projection) statement, `SET 'sql.tables.initial-offset-from' = '<old-statement-name>';` lets the new statement resume from the old one's offsets. This is **not valid** for aggregations, windows, pattern-matching, or upsert sinks.
- **Checkpoint interval, state backend, and storage are not user-configurable on CC** (they are on CMF). If you must tune them, that is a reason to use CMF, not CC.

## Quick triage

| Symptom | Likely cause | First moves |
|---|---|---|
| Statement stuck `PENDING` | Compute pool out of CFU capacity | Raise the pool maximum, or split work across pools |
| Windows never produce output | Watermark not advancing — idle partition with no idleness timeout, or event-time skew | Set `sql.tables.scan.idle-timeout`; check the source event-time field; loosen the bound |
| Runaway CFUs / state growth | Missing TTL on a regular join or non-windowed aggregation; high-cardinality `GROUP BY`/`COUNT(DISTINCT)` | Add `sql.state-ttl`; switch to interval/temporal/lookup join; reconsider the key |
| Backfill slow to catch up | Autopilot still ramping | Watch "Messages Behind"; it converges — avoid over-provisioning reactively |

---
