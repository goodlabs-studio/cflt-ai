# Chitragupta for Confluent Cloud — Setup and Operations Runbook

Date: 2026-10-21 · Tool version tested: 2.3.0 (demo only) · Wiki context: `wiki/patterns/chitragupta-confluent-cloud-chargeback.md`

**Source rule:** every step below comes from the Chitragupta docs (`https://awalia.dev/chitragupta/latest/`) unless marked **[Inference]** (my recommendation, not in the docs) or **[Tested]** (observed in a local synthetic-data demo). The real Billing/Metrics API pipeline has **not** been tested.

> **Client-system rule:** run Section 3 onward only against a Confluent Cloud org you own. For a client org, hand this runbook to the client to execute from their own environment.

---

## 1. Decisions before you start

| Decision | Options | Recommendation |
|---|---|---|
| How BUs map to spend | (a) one CC environment per BU → `group_by=environment_id`; (b) tags on resources/identities → `group_by=tag:<key>` | (a) if BUs already map to environments, else (b). **[Inference]** |
| Storage | SQLite (single instance, ~10 GB/tenant guidance) or PostgreSQL (one DB per tenant) | SQLite for pilot, Postgres for production |
| Metrics source | None (usage portions degrade to even split) or CC Metrics API key (`api.telemetry.confluent.cloud`) | Configure it. Without it, `allocation_detail` shows fallback tiers. |
| Topic attribution | Off, or on (needs Prometheus holding per-topic `received_bytes`, `sent_bytes`, `retained_bytes`) | Off for pilot |
| Even-split lines | Connectors, Schema Registry, ksqlDB, KAFKA_BASE, partitions, storage are split evenly among identities | Agree with finance up front how a BU owner will be told about these. **[Inference]** |
| Security sign-off | Service account needs `OrganizationAdmin` + `BillingAdmin` + `MetricsViewer` | Get this approved before creating it (see 3.1) |

## 2. Prerequisites

- Docker Engine 24+ and Compose v2+ (recommended), or Python 3.14+ with `uv` (`pip install uv`).
- Confluent CLI, logged in to the target org.
- Port availability on the host: 8080 (API), 8081 (UI), 3000 (Grafana, optional).

## 3. Confluent Cloud identity and credentials

### 3.1 Service account and roles

The docs state `OrganizationAdmin` is broader than ideal because CCloud RBAC has no narrower scope for the APIs used (Objects API, Metrics API, connector/ksqlDB principals). Record this in your risk register.

```bash
confluent login
confluent iam sa create chargeback_handler --description "Chargeback handler user"
# note the sa-xxxxxxx ID returned

confluent iam rbac role-binding create --principal User:<sa_id> --role MetricsViewer
confluent iam rbac role-binding create --principal User:<sa_id> --role OrganizationAdmin
confluent iam rbac role-binding create --principal User:<sa_id> --role BillingAdmin
```

### 3.2 Cloud API key

```bash
confluent api-key create --resource cloud --service-account <sa_id>
```

Optional: a separate Metrics API key (for usage-ratio allocation). Optional: per-region Flink keys for CFU allocation.

**Key handling [Inference]:** store the key and secret in your secret manager; pass them to the container as environment variables only; never commit `.env`; plan a rotation date. An expired key is a documented cause of tenant suspension (see 7).

## 4. Pilot deployment (Docker Compose)

```bash
git clone https://github.com/waliaabhishek/chitragupta.git
cd chitragupta/examples/ccloud-full
cp .env.example .env
```

Edit `.env`:

```
CCLOUD_API_KEY=<key from 3.2>
CCLOUD_API_SECRET=<secret from 3.2>
CCLOUD_TENANT_ID=my-org     # any string — internal partition key, NOT the CCloud org ID
```

```bash
docker compose up -d
docker compose logs chitragupta -f
```

| Service | URL |
|---|---|
| API | http://localhost:8080 |
| UI | http://localhost:8081 |
| Grafana | http://localhost:3000 (admin/password) |

Other examples in the repo: `ccloud-grafana/` (worker + Grafana only), `self-managed-full/`.

No-Docker alternative:

```bash
uv sync
cp examples/ccloud-full/config.yaml config.yaml   # set connection_string to a local path, e.g. sqlite:///data/chargeback.db
export CCLOUD_API_KEY=... CCLOUD_API_SECRET=... CCLOUD_TENANT_ID=my-org
uv run python src/main.py --config-file config.yaml --run-once      # one pass
uv run python src/main.py --config-file config.yaml --mode both     # continuous + API
```

## 5. Configuration reference (the keys that matter)

```yaml
tenants:
  my-ccloud-org:
    ecosystem: confluent_cloud
    tenant_id: my-ccloud-org
    lookback_days: 200        # acquisition/recalc window, max 364, must exceed cutoff_days
    cutoff_days: 5            # newest N days skipped (billing lag), max 30
    retention_days: 250       # delete older data, max 730
    storage:
      connection_string: "sqlite:///data/ccloud.db"   # each tenant needs its OWN database
    plugin_settings:
      ccloud_api:
        key: ${CCLOUD_API_KEY}
        secret: ${CCLOUD_API_SECRET}
      billing_api:
        days_per_query: 15    # max 30; raise on HTTP 429
      metrics:                # optional; enables usage-ratio allocation
        type: prometheus
        url: https://api.telemetry.confluent.cloud
        auth_type: basic
        username: ${METRICS_API_KEY}
        password: ${METRICS_API_SECRET}
      chargeback_granularity: daily     # hourly | daily | monthly
      topic_attribution:
        enabled: false
      emitters:
        - type: csv
          aggregation: daily
          params: { output_dir: ./output }
```

- `${VAR}` fails startup if unset; `${VAR:-default}` supplies a fallback.
- `allocator_params.kafka_cku_usage_ratio` / `kafka_cku_shared_ratio` default to 0.70 / 0.30 and must sum to 1.0, or startup fails.
- Config is validated before any network calls; errors show the field path.

## 6. First run and verification

First run: creates storage and runs migrations, pulls billing for `lookback_days`, discovers resources and identities, allocates costs, writes chargeback rows, runs emitters, then sleeps `features.refresh_interval` (default 1800s).

Run modes: `--mode worker` (pipeline only), `--mode api` (API only), `--mode both`, `--run-once`, `--emit-once` (replay emitters only).

Checks:

```bash
curl localhost:8080/health                                # {"status":"ok","version":"..."}
curl localhost:8080/api/v1/readiness
curl localhost:8080/api/v1/tenants                        # dates_calculated, dates_pending
curl localhost:8080/api/v1/tenants/<tenant>/pipeline/status
```

Expected log line (example from docs): `Tenant my-org: gathered=14, pending=0, calculated=14, rows=320`. A healthy first run has `pending=0` and non-zero `rows` (docs do not state this explicitly; reasonable reading).

**Reconcile before trusting it [Inference]:** compare one closed month's total from `chargebacks/aggregate` against the Confluent Cloud invoice. The docs say Chitragupta never changes the billed total, so any gap means missing dates (check `cutoff_days`, `gathered=0`) or a scope mismatch.

## 7. BU mapping via tags

Tags attach to entity type `resource` or `identity`, and resolve onto chargeback rows at query time. When a resource and its linked identity share a key, the resource tag wins.

1. **Define the taxonomy [Inference]:** one key (for example `bu`), a controlled value list, and an owner who approves changes.
2. **Inventory what needs tagging:** `GET /api/v1/tenants/<t>/resources`, `GET .../identities`, and `GET .../inventory/summary`.
3. **Tag in bulk:**

```bash
B=http://localhost:8080/api/v1/tenants/<tenant>
H='Content-Type: application/json'

# single entity (201; 409 if the key already exists on that entity)
curl -X POST $B/entities/resource/<lkc-id>/tags -H "$H" \
  -d '{"tag_key":"bu","tag_value":"retail","created_by":"you"}'

# many entities
curl -X POST $B/tags/bulk -H "$H" -d '{ ...items..., "created_by":"you", "override_existing": false }'

# everything seen in chargebacks for an identity
curl -X POST $B/tags/bulk-by-filter -H "$H" -d '{ ...filters..., "tag_key":"bu", "display_name":"retail", "created_by":"you" }'
```

Check the exact request bodies against `GET /openapi.json` on your running instance before scripting; I confirmed the single-entity schema only (`tag_key`, `tag_value`, `created_by`). Tag keys: docs say alphanumeric start, then alphanumerics/`_`/`-`, max 63 chars. **[Tested]** the 2.3.0 API accepted 64- and 100-char keys (OpenAPI `maxLength` 100); treat 63 as the safe limit.

4. **Roll up:**

```bash
curl "$B/chargebacks/aggregate?group_by=tag:bu&group_by=product_type&time_bucket=month&start_date=2026-09-01&end_date=2026-09-30"
```

- `group_by` also accepts `identity_id`, `resource_id`, `product_type`, `product_category`, `cost_type`, `allocation_method`, `environment_id`. Untagged rows land in `UNTAGGED`.
- Filter with `tag:bu=retail` (multiple params ANDed, comma values ORed; untagged rows excluded).
- **[Tested]** Tagging a resource with a new key changed the rollup immediately, with no pipeline re-run.
- Drive `UNTAGGED` toward zero before issuing any BU report **[Inference]**.

5. **Export and compare:** `POST $B/export` (CSV; default columns include `tags`, serialised `key=value;key=value`) and `GET $B/chargebacks/comparison` (baseline vs comparison periods).

**Unknown, test before relying on it:** the docs do not say whether tags survive a `lookback_days` recalculation, and describe no audit trail or approval flow for tag edits. Export your tags (`GET $B/tags`) on a schedule as a backup **[Inference]**.

## 8. Production hardening

- **Storage:** PostgreSQL needs `psycopg2` (`uv add psycopg2-binary`); connection string `postgresql+psycopg2://user:pass@host:5432/dbname`; one database per tenant.
- **API auth:** none built in. Put it behind a reverse proxy or gateway. Do not expose `preview.artifact_root` publicly.
- **Run model:** use `--mode both` in a single process per tenant database (SQLite is single-writer; Postgres for multi-process).
- **systemd (worker):** `ExecStart=uv run python src/main.py --config-file /etc/chargeback/config.yaml --mode worker`, `Restart=on-failure`, `RestartSec=30`.
- **Standalone Docker:**

```bash
docker run -v ./config:/app/config:ro -v ./data:/app/data \
  -e CCLOUD_API_KEY=... -e CCLOUD_API_SECRET=... \
  chitragupta --config-file /app/config/config.yaml --mode both
```

- **Refresh interval:** set `features.refresh_interval` to at least 2x a typical run duration to avoid "skipped — already in progress".
- **Logging:** `level: INFO`; a JSON-style `format` for Loki/ELK; trace with `request_id`, `pipeline_run_id`, `calculation_id`. Do not add secrets to wrapper logs.

## 9. Monitoring and alerting

| Signal | Source | Action |
|---|---|---|
| Service up | `GET /health`, `GET /api/v1/readiness` (cached 2s) | Standard liveness/readiness |
| Run results | `pipeline/status` → `last_result` (`dates_gathered`, `dates_calculated`, `chargeback_rows_written`, `errors`) | Alert on `errors` non-empty or `gathered` dropping |
| Tenant suspended | Log: `ALERT: Tenant X has been permanently suspended` | Fix root cause, restart (see 10) |
| Partial run | Log: `Tenant X completed with errors: [...]` | Read the `errors` list |
| Timeouts | Run longer than `tenant_execution_timeout_seconds` (default 3600) | Raise timeout or reduce lookback |
| Topic attribution failures | `attribution_method = 'ATTRIBUTION_FAILED'` rows | Check Prometheus connectivity |

## 10. Troubleshooting (Confluent Cloud relevant)

| Symptom | Cause | Fix |
|---|---|---|
| HTTP 429 from the Billing API | Rate limit; several tenants on one org share it | Raise `billing_api.days_per_query` (max 30), raise `min_refresh_gap_seconds` |
| Rows missing for recent dates | `cutoff_days` skips them on purpose | Wait, or lower `cutoff_days`; look for `gathered=0` in logs |
| "lookback_days must be > cutoff_days" | Config | Defaults are 200 and 5 |
| Tenant permanently suspended | Gather failures exceeded `gather_failure_threshold` (5), e.g. expired API key | Fix cause, restart the engine (resets state) |
| Everything in UNALLOCATED / empty CSV | No identities resolved | Check identity discovery and credentials/roles |
| High memory on first run | Large lookback fetched at once | Lower `billing_api.days_per_query` |
| Slow initial backfill | Many dates | Set `tenant_execution_timeout_seconds: 0` during backfill, drop `lookback_days` to 30-60 afterwards |
| "No WorkflowRunner available" | Pipeline triggered while in `--mode api` | Use `--mode both` |
| HTTP 409 on pipeline run | Run already in progress | Check `pipeline/status` |
| "database is locked" | Two writers on SQLite, or stale lock | One process per DB; for a stale lock stop the engine, delete `-wal`/`-shm`, restart; or move to Postgres |
| "Can't locate revision" | Schema ahead of code | `alembic history`; upgrade code or downgrade; else back up and recreate |
| "tenants A and B share storage connection_string" | Two tenants, one DB | Separate paths |
| Stale API data | API-only mode | `--mode both` or `POST .../pipeline/run` |

## 11. Upgrade and rollback

Migrations run automatically at startup, and the docs state there is no undo once the process starts. **Back up first.**

```bash
# SQLite, per tenant database
cp data/chargeback.db data/chargeback.db.bak
cp data/chargeback.db-wal data/chargeback.db-wal.bak 2>/dev/null
cp data/chargeback.db-shm data/chargeback.db-shm.bak 2>/dev/null
# PostgreSQL
pg_dump -Fc -f chargeback_backup_$(date +%Y%m%d).dump dbname
```

Also keep a copy of `config.yaml`; if FOCUS Preview is enabled, back up `preview.artifact_root` at the same point in time as the database.

```bash
docker compose down && docker compose pull && docker compose up -d
docker compose logs -f chitragupta | head -50
curl http://localhost:8080/health
```

Rollback: stop the engine, restore the backup (SQLite files, or `pg_restore -c -d dbname <dump>`), revert to the previous image tag, start the old version. Restoring from backup is preferred over `alembic downgrade`. PostgreSQL 17 is the version the docs verify; no claim is made for others.

## 12. Data retention

- Tenant data: `retention_days` (default 250, 1-730); cleanup runs after each pipeline cycle, in whole UTC calendar days.
- Topic attribution: `topic_attribution.retention_days` (default 90, 1-365), independent of the tenant setting.
- `lookback_days` is an acquisition window, not an archive. Setting `retention_days` above `lookback_days` keeps all data inside the recalculation window.
- There is no CLI for selective cleanup; wiping a tenant means stopping the service and removing or recreating its database.
- The retention page does not mention tags, so their retention behaviour is undocumented.
- **Keep BU reports [Inference]:** export each closed month's BU rollup to CSV and archive it, so reports do not depend on retention or recalculation.

## 13. Teardown

```bash
docker compose down        # keep data
docker compose down -v     # also delete the database volume
```

## 14. Open items to verify on a real (sandbox) org

1. Does the CKU split match the documented 70/30 usage/shared? (The synthetic demo showed 100% usage; demo data is generated.)
2. Do tags survive recalculation of the lookback window?
3. Invoice reconciliation for one closed month.
4. Share of spend that lands in even-split lines versus usage-based lines for your org.
5. Security review outcome on `OrganizationAdmin` + `BillingAdmin`.

## 15. Local synthetic demo (no credentials)

From the docs' Demo page: `git clone` the repo, then `./demo --showcase` (or `./demo` for the clean profile). UI at http://127.0.0.1:8081, API at http://127.0.0.1:8080, optional `--grafana`. `./demo status`, `./demo logs`, `./demo down` (keeps data), `./demo reset --showcase` (wipes data and tag edits). All data is synthetic.

## Sources

- https://awalia.dev/chitragupta/latest/configuration/ccloud-reference/
- .../getting-started/ (prerequisites, quickstart, configuration, first-run, demo)
- .../architecture/ (cost-model, identity-resolution)
- .../operations/ (deployment, monitoring, troubleshooting, upgrading, data-retention)
- .../api-reference/
