> Part of **Flink Center of Excellence — Managed Flink on Confluent Cloud** (self-contained series). Validated against Confluent documentation 2026-07-30.

# Appendix — Validation & Status

- **Validated against Confluent documentation on 2026-07-30:** the CC-vs-OSS/CP subset (unsupported statements, `DROP TABLE` topic deletion, `'connector'='confluent'`, default 180 ms watermark, config-name mapping); compute-pool limits (50 CFU/pool, scale-to-zero, 1,000 CFU LA); Flink RBAC role catalog (`FlinkDeveloper`, `FlinkAdmin`, `FlinkFunctionDeveloper`, `Operator`, `Assigner`; `FlinkEnvironmentAdmin` confirmed *not* a role); Transactional-Id `_confluent-flink_*` requirement; the managed DLQ (`error-handling.mode`); and the PrivateLink gateway model.
- **(LA) Limited Availability:** 1,000-CFU compute pools.
- **(unverified):** the exact behavior of *decreasing* a pool's maximum CFU after creation — size to peak and validate against current tooling before relying on shrink behavior.
- **Scope:** this guide is product/environment-shaped. Use-case-specific tuning (fraud scoring, reconciliation, CDC pipelines) and full AWS reference diagrams/Terraform should be added once workloads are selected. CC Flink capability evolves quickly — re-confirm any specific capability before committing to a design.
