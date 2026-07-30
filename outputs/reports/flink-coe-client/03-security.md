> Part of **Flink Center of Excellence — Managed Flink on Confluent Cloud** (self-contained series). Validated against Confluent documentation 2026-07-30.

# Part 3 — Security (RBAC, Service Accounts, Principals)

CC Flink needs **two role planes** — control-plane (Flink) roles to submit and manage statements, *and* data-plane (Kafka / Schema Registry) roles for the topics and subjects a statement touches. Missing either fails at submit time or at first topic access. Production statements must run **as service accounts, not users.**

## Control-plane (Flink) roles

| Role | Grants |
|---|---|
| `FlinkDeveloper` | Create and run statements, manage artifacts and your own workspaces. Can be scoped at the compute-pool level to restrict a user to specific pools. |
| `FlinkAdmin` | All FlinkDeveloper capabilities plus creating and managing compute pools (workload isolation / cost control). |
| `FlinkFunctionDeveloper` | Manage user-defined-function (UDF) artifacts and external connectivity. |
| `Operator` | Metadata access to Flink tables, databases, and catalogs. |
| `Assigner` (granted on the service account) | Delegate statement execution to a service account — required for the OAuth identity-pool → service-account pattern (the identity pool authenticates; the service account executes). |

> Note: **`FlinkEnvironmentAdmin` is not a real role** — confirmed absent from the Confluent role catalog. Some third-party materials mislabel `FlinkDeveloper` as `FlinkEnvironmentAdmin`; use `FlinkDeveloper`.

## Data-plane (Kafka / Schema Registry) roles the statement's principal needs

- `DeveloperRead` on **source** topics; `DeveloperWrite` on **sink** topics.
- **Both `DeveloperRead` and `DeveloperWrite` on Transactional-Id `_confluent-flink_*`** — required for **all** Flink statements (Flink uses Kafka transactions for exactly-once semantics), not just sinks.
- `DeveloperRead` on **source** Schema Registry subjects; `DeveloperWrite` on **sink** subjects. The sink-subject write is required because the Avro/Confluent format defaults to auto-registering schemas — **without it, sink writes fail with a 403** (which, in a self-managed runtime, manifests as a crash-loop).

## Service-account principal model

- **Bind production statements to service accounts, not user accounts** — this prevents disruption when a person's status changes. The `Assigner` role on the service account is what lets a human submit statements that *run as* that service account.
- **In Terraform**, a Flink statement must have a principal: set `flink_principal_id` on the Confluent provider (or the `FLINK_PRINCIPAL_ID` environment variable), or a `principal { id = … }` block on the statement resource. Omitting it fails with `one of provider.flink principal id … must be set`.
- **`DROP TABLE` deletes the underlying topic and data** — withhold table-drop from developer roles and change-control any drop.

## FSI hardening notes (from comparable regulated deployments)

- **Bind roles to identity-provider groups, never to individuals** — revocation flows through group membership, which satisfies SOX/FFIEC access-change logging. Scope Flink roles to the environment (or pool), not organization-wide.
- **Least-privilege binding shape:** separate bindings for (1) source-topic read, (2) sink-topic write + Transactional-Id, (3) source-subject read, (4) sink-subject write — so each is independently auditable and revocable.
- **Flink topic access is auto-audited** — every authorization decision on a Flink topic access is emitted to the audit-log event stream; statement submit/cancel is also captured. This is the enforcement point for proving access controls at audit time.
- **Contrast with CMF (self-managed):** on CMF, the job's Kafka identity is an mTLS certificate whose CN/SAN matches the service account; checkpoint state must be written to encrypted storage (unencrypted checkpoints can contain transaction amounts / account numbers — a PCI-DSS / GLBA finding). Neither applies to CC, where checkpoints are managed and endpoints are reached via API key / OAuth / mTLS to the managed service.

---
