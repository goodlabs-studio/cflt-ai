---
title: Chitragupta — Confluent Cloud Chargeback by Business Unit and Usage
tags: [chitragupta chargeback showback finops confluent-cloud billing-api metrics-api prometheus rbac tagging cost-allocation docker]
sources:
  - https://awalia.dev/chitragupta/latest/configuration/ccloud-reference/
  - https://awalia.dev/chitragupta/latest/getting-started/prerequisites/
  - https://awalia.dev/chitragupta/latest/getting-started/quickstart/
  - https://awalia.dev/chitragupta/latest/getting-started/configuration/
  - https://awalia.dev/chitragupta/latest/getting-started/first-run/
  - https://awalia.dev/chitragupta/latest/architecture/cost-model/
  - https://awalia.dev/chitragupta/latest/architecture/identity-resolution/
  - https://awalia.dev/chitragupta/latest/operations/deployment/
  - https://awalia.dev/chitragupta/latest/api-reference/
related: [patterns/cc-api-key-oauth-access-management, concepts/cc-cluster-tiers]
confidence: medium
last_updated: 2026-10-21
last_validated: 2026-10-21
---

# Chitragupta — Confluent Cloud Chargeback by Business Unit and Usage

## Summary

Chitragupta (github.com/waliaabhishek/chitragupta) is an open-source chargeback engine. For Confluent Cloud it pulls Confluent's own Billing API lines, then distributes each line's total across identities (service accounts, users, identity pools) by usage ratio or even split. It never changes the billed total. Business-unit breakdown is **not a built-in concept for Confluent Cloud**: the documented mechanism is key/value **tags** on resources and identities, resolved onto chargeback rows at query time and rolled up with `group_by=tag:<key>`. Everything here is from the project's own docs, not MCP-validated against Confluent docs (a third-party tool, so `confluent-docs` doesn't cover it) — hence `confidence: medium`.

## Pattern

### Prerequisites

- Docker Engine 24+ and Compose v2+ (recommended), or Python 3.14+ with `uv` for a no-Docker run.
- A Confluent Cloud org and the Confluent CLI.
- A service account with **three** role bindings: `MetricsViewer`, `OrganizationAdmin`, `BillingAdmin`. The docs state OrganizationAdmin is broader than ideal because CCloud RBAC has no narrower scope for the APIs used (Objects API, Metrics API, connector/ksqlDB principals). Flag this to any security reviewer.
- Optional: a separate Metrics API key (enables usage-ratio allocation) and a Prometheus holding per-topic `received_bytes`, `sent_bytes`, `retained_bytes` (needed for topic attribution only).

### Setup steps

1. Create the service account, role bindings and a Cloud API key:

   ```bash
   confluent login
   confluent iam sa create chargeback_handler --description "Chargeback handler user"
   confluent iam rbac role-binding create --principal User:<sa_id> --role MetricsViewer
   confluent iam rbac role-binding create --principal User:<sa_id> --role OrganizationAdmin
   confluent iam rbac role-binding create --principal User:<sa_id> --role BillingAdmin
   confluent api-key create --resource cloud --service-account <sa_id>
   ```

2. Clone and start the full example (pipeline + API + Grafana + UI):

   ```bash
   git clone https://github.com/waliaabhishek/chitragupta.git
   cd chitragupta/examples/ccloud-full
   cp .env.example .env   # CCLOUD_API_KEY, CCLOUD_API_SECRET, CCLOUD_TENANT_ID
   docker compose up -d
   ```

   `CCLOUD_TENANT_ID` is any string — an internal partition key, **not** the CCloud org ID. Other examples: `ccloud-grafana/` (worker + Grafana only), `self-managed-full/`.

3. Verify: `curl localhost:8080/health`. Ports: API `:8080`, Grafana `:3000` (admin/password), UI `:8081`. First build takes ~1–2 minutes; dashboards fill after the first pipeline run.

4. No-Docker alternative:

   ```bash
   uv sync
   uv run python src/main.py --config-file config.yaml --run-once   # or --mode both
   ```

### Configuration (`config.yaml`)

YAML with `${ENV}` and `${VAR:-default}` substitution. Each tenant needs its **own** `storage.connection_string` (startup rejects shared databases).

```yaml
tenants:
  my-ccloud-org:
    ecosystem: confluent_cloud
    tenant_id: my-ccloud-org
    lookback_days: 200          # acquisition/recalc window, max 364
    cutoff_days: 5              # skip recent dates: billing lag
    retention_days: 250
    storage:
      connection_string: "sqlite:///data/ccloud.db"   # Postgres for multi-instance
    plugin_settings:
      ccloud_api: { key: ${CCLOUD_API_KEY}, secret: ${CCLOUD_API_SECRET} }
      metrics:                  # optional; enables usage-ratio allocation
        type: prometheus
        url: https://api.telemetry.confluent.cloud
        auth_type: basic
        username: ${METRICS_API_KEY}
        password: ${METRICS_API_SECRET}
      chargeback_granularity: daily    # hourly | daily | monthly
      topic_attribution: { enabled: false }   # needs Prometheus per-topic metrics
      emitters:
        - { type: csv, aggregation: daily, params: { output_dir: ./output } }
```

Other documented keys: `billing_api.days_per_query` (15, max 30), `flink` (per-region key/secret list), `min_refresh_gap_seconds` (1800), `allocator_params`.

### Run modes

| Flag | Behavior |
|------|----------|
| `--mode worker` | pipeline only |
| `--mode api` | REST API only |
| `--mode both` | pipeline + API (simplest) |
| `--run-once` | one pass, then exit |
| `--emit-once` | replay emitters only; no billing fetch or recalculation |

Default refresh interval is 1800s. Expected first-run log line: `Tenant my-org: gathered=14, pending=0, calculated=14, rows=320`. Storage: SQLite (single instance, ~10 GB/tenant guidance) or PostgreSQL (one DB per tenant, `psycopg2`).

### How cost is allocated by usage

Per-line total is fixed; the engine only distributes it, scaled by `active_fraction` for partial-window resources. Rows carry `cost_type` (`USAGE`/`SHARED`) and `allocation_detail` (which fallback tier applied).

| Product type | Allocation |
|--------------|------------|
| `KAFKA_NUM_CKU(S)` | 70% usage (bytes in+out) / 30% even split — tunable via `allocator_params.kafka_cku_usage_ratio` + `kafka_cku_shared_ratio` (must sum to 1.0) |
| `KAFKA_NETWORK_READ/WRITE` | usage ratio (needs Metrics API) |
| `KAFKA_BASE`, `KAFKA_PARTITION`, `KAFKA_STORAGE` | even split |
| `FLINK_NUM_CFU(S)` | by statement owner's CFU usage |
| Schema Registry, connectors, ksqlDB | even split |
| `AUDIT_LOG_READ`, `SUPPORT` | org-wide even split, remainder to `UNALLOCATED` |
| `TABLEFLOW_*`, `CLUSTER_LINKING_*` | to the resource |
| Unknown types | `UNALLOCATED` |

Fallback chain: usage ratio → even split across active identities → even split across all tenant identities → the resource ID itself. Missing metrics degrade usage portions to even split. Topic attribution is a separate overlay that splits Kafka cluster cost to topics (default mappings: write→`bytes_in`, read→`bytes_out`, storage→retained bytes); failed fetches write `__UNATTRIBUTED__` / `ATTRIBUTION_FAILED` sentinel rows.

### Business-unit breakdown via tags

Tags attach to entity type `resource` or `identity` and resolve onto chargeback rows at query time. No endpoint is named "business unit"; a key such as `team` or `bu` plays that role.

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/entities/{type}/{id}/tags` | create (409 if key exists) |
| PUT / DELETE | `.../tags/{tag_key}` | update / remove |
| POST | `/tags/bulk` | many entities (`override_existing`) |
| POST | `/tags/bulk-by-filter` | tag entities found in chargebacks matching filters (`identity_id`, dates, `tag_key`, `display_name` → tag value) |
| GET | `/tags`, `/tags/keys`, `/tags/keys/{key}/values` | discovery |

Tag keys: alphanumeric start, then alphanumerics, `_`, `-`; docs say max 63 chars, but a local test (v2.3.0) accepted 64- and 100-char keys (OpenAPI schema: `maxLength` 100) — treat 63 as the safe limit. If a resource and its linked identity share a key, **the resource tag wins**.

Roll up (all under `/api/v1/tenants/{tenant}/`):

```
GET chargebacks/aggregate?group_by=tag:bu&group_by=product_type&time_bucket=month
```

- `group_by` accepts `identity_id`, `resource_id`, `product_type`, `product_category`, `cost_type`, `allocation_method`, `environment_id`, and `tag:{key}`. Untagged rows land in an `UNTAGGED` bucket.
- `time_bucket`: `hour | day | week | month`. Filter by `tag:{key}=value` (params ANDed, comma values ORed; untagged excluded).
- `POST .../export` streams CSV with a `tags` column (`key=value;key=value`).
- `GET .../chargebacks/comparison` compares two periods (`baseline_*` vs `comparison_*`, `group_by=principal|resource|environment`).

If each BU already has its own CC environment, `group_by=environment_id` needs no tagging at all.

## When to Use

- Showback/chargeback of Confluent Cloud spend to BUs or applications where Confluent's native billing view is too coarse (per-principal, per-topic, per-product).
- Multi-tenant shared clusters where Kafka CKU, network and storage need splitting by measured usage.
- You can accept running a small sidecar stack (API + worker + DB) and its API keys.

### Local test results (synthetic demo, 2026-10-21)

Tested with the docs' no-credential demo (`./demo --showcase`, v2.3.0, Docker; two containers: API `:8080`, UI `:8081`). Synthetic data only — the real Billing/Metrics API pipeline was **not** tested.

- **Works as documented:** `group_by=tag:<key>` rollup (with `UNTAGGED` bucket), `tag:<key>=value` filter, tag create (201) / duplicate (409) / delete (204). Tagging one resource with a new `bu` key split the month into `bu=retail` and `UNTAGGED` immediately, with no pipeline re-run.
- **Differs from docs:** tag keys of 64 and 100 chars were accepted (docs: 63 max). Demo data shows `KAFKA_NUM_CKUS` and `KAFKA_PARTITION` as 100% `usage_ratio`/`cost_type=usage`, whereas the docs describe 70/30 usage/shared for CKU and even split for partitions. The demo is generated data, so this is unresolved until a real-org run.
- **Handy for inspection:** the running API serves `/openapi.json` (authoritative request schemas) and `GET /api/v1/tenants` (per-tenant `dates_calculated`, `dates_pending`).
- **Check it is running:** `curl localhost:8080/health`; `docker ps --filter name=demo-`; `./demo status`; UI at `http://127.0.0.1:8081`. Stop with `./demo down`, reset data with `./demo reset --showcase`.

## Caveats

- **Broad permissions:** `OrganizationAdmin` + `BillingAdmin` on the service account. Treat the API key as highly sensitive; consider a dedicated sandbox org for evaluation.
- **No built-in API auth.** Put the API behind a reverse proxy. Never expose `preview.artifact_root` publicly.
- **BU mapping is DIY.** The `principal_to_team` mapping documented in Identity Resolution is self-managed-Kafka only. No docs found for tagging via UI/Grafana, or for whether tags survive the `lookback_days` recalculation — verify before relying on them.
- **Usage accuracy needs a Metrics API key / Prometheus.** Without it, usage portions silently fall back to even split (check `allocation_detail`).
- **Billing lag:** the newest `cutoff_days` (default 5) are skipped; recent spend won't appear immediately.
- **Totals are Confluent's.** Chitragupta redistributes; it does not recompute pricing. FOCUS Mapping Preview (opt-in, `direct_payg`, USD only) is a separate export path and out of scope here.
- **Client environments:** per the never-connect rule, run this against sandbox orgs here; for client orgs, hand over the config and have the client run it from their own environment.
- **Not covered by the fetched docs:** the Troubleshooting, Upgrading, Data Retention and FOCUS Mapping Preview pages.

## Related

- [Confluent Cloud Access Management — API Keys vs OAuth](patterns/cc-api-key-oauth-access-management.md) — service-account and API key handling for the chargeback service account
- [Confluent Cloud Cluster Tiers](concepts/cc-cluster-tiers.md) — CKU/cluster-type context for the cost lines being allocated
