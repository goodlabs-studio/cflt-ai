# confluent-cloud-cost-exporter: Setup and Usage Guide

Repo: https://github.com/mcolomerc/confluent-cloud-cost-exporter (reviewed at commit `46ef4b1`, 2025-01-08, VERSION 0.0.4)
Review method: static read of the code by three agents (core/API, exporters/config, deployment/dashboards). Nothing was built, run or fetched against Confluent Cloud. Findings with file refs are from the code; items marked **UNVERIFIED** were not checked against live Confluent docs.

## 1. Verdict

A small Go service (~1k lines) that polls the Confluent Cloud **Billing API** and republishes the line items as Prometheus text (`/probe`), JSON (`/json`), or Avro on a Kafka topic (cron mode). Ships with Grafana and Kibana dashboards.

| Question | Answer |
|---|---|
| Granularity | Daily line items per resource (`lkc-`, `lcc-`, `lsrc-`, `lksqlc-`...), product, line_type, environment |
| Per-topic cost? | No |
| Per-business-unit / chargeback? | No. No tag, service-account or consumer-group attribution. Environment and resource ID only |
| Invoice reconciliation | Partial. Raw API amounts, but only one fixed day per fetch (see 5) |
| Production readiness | Demo/PoC grade. Needs hardening before FSI use (see 6) |

**Fit for BU-level granular cost tracking: poor on its own.** It is a good free baseline for environment and cluster-level cost dashboards. If BUs map 1:1 to environments or clusters it is enough. If BUs share clusters (the usual case), you need an attribution layer. That is what Mikan (consumer group, service account, topic) is for.

## 2. Architecture

```
Confluent Cloud Billing API  GET https://api.confluent.cloud/billing/v1/costs?start_date=&end_date=
            |  (HTTP Basic, Cloud API key; in-memory TTL cache keyed by URL)
            v
   exporter (gin, default :8080, Docker :7979)
     |- web mode (default):   GET /probe  (Prometheus)   GET /json  (JSON array)
     '- cron mode:            gocron (UTC) -> Avro -> Kafka topic + Schema Registry
```

Web and cron modes are mutually exclusive. If `cron.expression` is set, no HTTP server starts.

Optional stack in the repo: Prometheus + Grafana (`docker-compose-pg.yaml`, where "pg" means Prometheus/Grafana, not Postgres) or Metricbeat + Elasticsearch + Kibana (`docker-compose-elk.yaml`).

## 3. Prerequisites

- Docker and Compose v2 (use `docker compose`, not the v1 `docker-compose` the README shows).
- A Confluent Cloud **Cloud API key** (not a cluster key). The repo README says a service account with **OrganizationAdmin**. **UNVERIFIED:** BillingAdmin may be sufficient for the Billing API; confirm in current Confluent RBAC docs and use the least-privileged role that works.
- For the dashboards' operational panels: the same key needs Metrics API access (MetricsViewer is enough for that part).
- Run it from your own machine or a sandbox. Per the safety rule, this tooling session did not run it and should not be pointed at client accounts. Use the client's key only in the client's environment or a sanctioned sandbox.

## 4. Setup

### 4a. Quickest: single container (cost JSON/Prometheus only)

```bash
# CI publishes mcolomerc/confluent_cloud_cost_exporter:latest (amd64 only).
# The README's image name (confluent/confluent_cloud_cost_exporter) is wrong.
docker run -d --name cc-cost-exporter -p 7979:7979 \
  -e PORT=7979 \
  -e CONFLUENT_CLOUD_API_KEY="$CC_KEY" \
  -e CONFLUENT_CLOUD_API_SECRET="$CC_SECRET" \
  -e DAYS_AGO=3 -e WINDOW=1 -e CACHE_EXPIRATION=240m \
  mcolomerc/confluent_cloud_cost_exporter:latest

curl -s localhost:7979/json | jq '.[0]'
curl -s localhost:7979/probe | head
```

Apple Silicon: add `--platform linux/amd64`, or build from source (4b).

### 4b. Build from source

```bash
git clone https://github.com/mcolomerc/confluent-cloud-cost-exporter && cd confluent-cloud-cost-exporter
docker build -t cc-cost-exporter confluent_cloud_cost_exporter/
```

The image is multi-stage (golang:1.22, `CGO_ENABLED=1`, debian bookworm-slim, runs as `nobody`). `config.yml` is baked in with placeholder credentials; override via env vars or mount your own at `/bin/config.yml`.

### 4c. Prometheus + Grafana stack

```bash
cp docker-compose-pg.yaml docker-compose.yml     # note docker-compose.yaml in the repo is the ELK file
mkdir env
cp prometheus/prometheus-template.yml env/prometheus.yml
# edit env/prometheus.yml: API key/secret, lkc-<id> and lsrc-<id> placeholders
# edit docker-compose.yml: API key/secret; CHANGE the Grafana admin password (default 1234)
docker compose build && docker compose up -d
```

Check Prometheus targets at `:9090/targets`, then Grafana at `:3000`. Dashboards are auto-provisioned: "Confluent Cloud Cost" (`confluent_billing.json`) is the useful one.

Prometheus scrape job for the exporter (from the template):

```yaml
- job_name: confluent_cost_exporter
  metrics_path: /probe
  scrape_interval: 5m
  scrape_timeout: 30s
  honor_labels: true
  static_configs:
    - targets: ['confluent_cost_exporter:7979']
```

### 4d. ELK variant

Same steps with `docker-compose-elk.yaml` and `metricbeat/metricbeat-template.yml` copied to `env/metricbeat.yml`. Metricbeat's `http` module polls `/json` (`json.is_array: true`, every 5m). Import `kibana/dashboards/*.ndjson` manually in Kibana. No index template is shipped, so you may hit the README's "long to float" mapping error on `quantity`. The `/json` endpoint serializes whole numbers as `1.0` to dodge it, but pre-create a mapping to be safe.

### 4e. Kafka output (cron mode)

Writes each cost record as Avro to a topic, so you can land costs in Kafka/Tableflow/Flink instead of Prometheus.

```yaml
cron:
  expression: "0 6 * * *"          # UTC; enabling this disables the HTTP server
  target:
    kafka:
      bootstrap: pkc-xxxxx.region.provider.confluent.cloud:9092
      credentials: { key: <kafka-key>, secret: <kafka-secret> }   # set in YAML ONLY, see pitfall 6.2
      schemaRegistry:
        endpoint: https://psrc-xxxxx.region.provider.confluent.cloud
        credentials: { key: <sr-key>, secret: <sr-secret> }
      topic: confluent.cloud.costs   # pre-create it; not auto-created
```

Limits: SASL_SSL/PLAIN with API key only (Confluent Cloud targets only, no mTLS/OAuth/PLAINTEXT, so it cannot be tested against a local KRaft cluster without code changes). Message key is the raw `end_date` string. Schema auto-registers as `<topic>-value`. Create the topic and tune partitions yourself.

## 5. Configuration reference

Loaded via cleanenv: YAML first, then env vars override.

| Key | Env var | Default | Meaning |
|---|---|---|---|
| `endpoints.costs` | `CONFLUENT_COSTS_URL` | `https://api.confluent.cloud/billing/v1/costs` | Billing API URL |
| `credentials.key` / `.secret` | `CONFLUENT_CLOUD_API_KEY` / `_SECRET` | none | Cloud API key, Basic auth |
| `period.daysAgo` | `DAYS_AGO` | 3 | end_date = today - daysAgo |
| `period.window` | `WINDOW` | 1 | start_date = end_date - window days |
| `web.cache.expiration` | `CACHE_EXPIRATION` | 60m in code, 240m in config.yml/compose (README says 30m) | In-memory TTL, keyed by URL |
| `web.prometheus.modules.default.metrics[]` | none | see config.yml | JSONPath-driven metric definitions |
| `cron.expression` | `CRON_EXPRESSION` | empty (web mode) | gocron cron, UTC; non-empty switches to Kafka mode |
| `cron.target.kafka.bootstrap` | `BOOTSTRAP` | none | Kafka bootstrap |
| `cron.target.kafka.topic` | `TOPIC` | none | Destination topic |
| `cron.target.kafka.schemaRegistry.endpoint` | `SCHEMA_REGISTRY_URL` | none | README says `SCHEMA_REGISTRY_ENDPOINT`; code reads `_URL` |
| `...schemaRegistry.credentials.key`/`.secret` | `SCHEMA_REGISTRY_API_KEY` / `_SECRET` | none | SR creds |
| none | `PORT` | gin 8080; Docker 7979 | Listen port |
| none | `GIN_MODE` | debug; Docker release | gin mode |
| CLI `-config` | none | `./config.yml` | Config path |

## 6. Usage

### 6.1 Understand the time window first (biggest gotcha)

Each fetch asks for **one window**: `[today - daysAgo - window, today - daysAgo]`. Defaults give one day, three days back, because billing data lags ~72h. The window never advances to cover history and nothing backfills. Consequences:

- "Cost by day" shows only one day.
- For a month-to-date view, set `WINDOW=30` (the code comment cites a 1-month max window and 1-year max lookback; **not validated in code and UNVERIFIED against API docs**).
- For history, run in cron mode into Kafka and keep the data downstream.

### 6.2 Prometheus metric

One untyped metric, `confluent_cloud_cost_amount` (value = `amount`), with labels: `id`, `resource` (display name), `environment`, `unit`, `product`, `line_type`, `network_access_type`, `start`, `end_date`, `granularity`, `discount`, `price`, `original_amount`, `quantity`.

Useful queries (as used by the shipped dashboard):

```promql
sum by (environment) (confluent_cloud_cost_amount)       # cost per environment
sum by (product)     (confluent_cloud_cost_amount)       # KAFKA, CONNECT, KSQL, SCHEMA_REGISTRY...
sum by (id, resource)(confluent_cloud_cost_amount{id=~"lkc.*"})   # per Kafka cluster
sum by (end_date)    (confluent_cloud_cost_amount)       # per day
```

Do not use `rate()`. This is a daily snapshot, not a counter.

### 6.3 JSON

`GET /json` returns a bare array of cost records with `amount`, `discount_amount`, `original_amount`, `price`, `quantity`, `start_date`, `end_date`, `granularity`, `line_type`, `network_access_type`, `product`, `unit`, and `resource{id, display_name, environment{id}}`. Useful for feeding your own allocation logic (for example mapping `resource.id` or `environment.id` to a BU table in a notebook or Flink job).

### 6.4 Getting to business-unit granularity

The exporter stops at environment and resource. Options, in order of effort:

1. **Environment-per-BU or cluster-per-BU:** a static lookup table joined to `/json` or the Kafka topic. Done.
2. **Shared clusters:** attribute within a cluster using the Metrics API (`confluent_kafka_server_received_bytes`/`sent_bytes` by topic/principal) to apportion the cluster's cost. Approximate; this is what the Grafana `ccloud.json` dashboard half-does per topic. You build and own the allocation model.
3. **Purpose-built:** Mikan, which does workload attribution, discount application and invoice reconciliation.

## 7. Issues to know before adopting

Ranked by impact for a financial-services client.

1. **Silent failures.** On any Billing API error (including non-200), `GetCosts` logs and returns `nil, nil`. `/probe` and `/json` return an empty 200, and cron mode produces zero messages. A broken key looks like "zero cost". Alert on absent series. (`pkg/services/costs.go:88-92`)
2. **Env var collision in Kafka mode.** `KafkaConfig` embeds `Credentials`, whose env tags are `CONFLUENT_CLOUD_API_KEY/SECRET`. Setting those env vars can overwrite the Kafka credentials. The `KAFKA_API_KEY/SECRET` vars are dead. Set Kafka credentials in YAML only. (`config.go:65-74`)
3. **Money precision bug.** `KeepZero.MarshalJSON` formats with 32-bit float precision, so amounts in `/json` and the Avro path can be rounded. Do not use it for invoice reconciliation without fixing this. (`costs.go:50-55`)
4. **No pagination.** Only the first page of the Billing API response is read, so large accounts may be silently truncated.
5. **Kafka mode is not idempotent.** Key is `end_date` only (hot key, no record ID), the cache can re-emit the same window on each cron run, `Produce` and transform errors are ignored, and `Flush` never runs. Expect duplicates and loss on shutdown. No `enable.idempotence`, no compression, nothing configurable.
6. **Prometheus design.** `price`, `quantity`, `discount`, `original_amount` and dates are labels, not values. This is high cardinality and churn. A pedantic registry returns 500 on duplicate label sets. The metric is untyped. No `/metrics`, `/health`, or self-metrics. No timeout, retry or backoff on the HTTP client, and no singleflight on cache expiry.
7. **Secrets and exposure.** The API key ID is printed to stdout and every URL is logged. Credentials sit in plaintext YAML and env. Endpoints `/probe` and `/json` are unauthenticated. The compose files hardcode Grafana `admin/1234`, publish 3000/9090/7979 (and 9200/9300 in ELK, with `xpack.security.enabled=false`). Prometheus exposes `/api/v1/status/config`, which reveals the secret in `prometheus.yml`. Don't use the compose files as-is anywhere beyond localhost.
8. **Stale dependencies and images.** Grafana 8.1.3 (2021), deprecated `grafana-piechart-panel` plugin, unpinned `prom/prometheus`, old GitHub Actions, one test, no CI tests, amd64 only image. A single commit in history, last updated January 2025.
9. **Dashboard bugs.** In `ccloud.json`, Connect panels filter `connector_id=~"$cluster"` (a Kafka cluster variable) so they will be empty; "Retained bytes" divides by a hardcoded 3; the datasource UID is hardcoded in places. `monitor_services.json` is mostly dead panels (no cAdvisor, node-exporter or `prometheus` self-scrape job). Metrics API metric names in the dashboards are **UNVERIFIED** against the current Metrics API reference.
10. **README errors.** Wrong image name, wrong directory links, wrong cache default and wrong SR env var name, an invalid JSON sample. Trust this guide's table over the README.

## 8. Recommendation

- **As a quick win** (environment/cluster cost visibility, a day or two of effort): run 4a or 4c on localhost, change the Grafana password, drop the dead dashboard, and fix pitfall 1 with an alert on absent series.
- **For the DTCC BU requirement:** do not build on this. Use it at most as a reference for the Billing API call shape. Either adopt Mikan or build a small Flink/SQL allocation job over the Billing API plus Metrics API. If forking this repo, the minimum fixes are: return errors from `GetCosts`, add pagination, fix `KeepZero`, move numeric fields out of labels, make the window advance and backfill, and add a record ID plus idempotence to the Kafka path.
- Next step if wanted: a fork with those fixes, tested only against a mock Billing API on localhost (no client accounts).

## 9. Grafana Cloud integration

The repo has no Grafana Cloud support. Its Grafana pieces are a self-hosted Grafana 8.1.3 with file provisioning. Grafana Cloud is a hosted Prometheus-compatible backend, so the exporter fits it only through a collector that scrapes `/probe` and remote-writes. The Alloy snippet below follows the Grafana Alloy docs (`prometheus.scrape`, `prometheus.remote_write` with `basic_auth`). The rest is my analysis of the exporter code, not tested against a Grafana Cloud stack.

### 9.1 Options

| Path | How | Verdict |
|---|---|---|
| **A. Alloy scrape + remote_write** | Exporter runs next to Grafana Alloy (or Prometheus agent mode). Alloy scrapes `/probe` and pushes to Grafana Cloud Metrics. | Recommended. Fits the exporter's pull-only design. |
| B. Infinity (JSON API) data source on `/json` | Grafana queries the exporter directly. | Only if Grafana Cloud can reach the exporter. That means a public endpoint (the exporter has no auth, so no) or Grafana's Private Data Source Connect agent. **UNVERIFIED** setup details. Skip unless you need raw line items in tables. |
| C. Kafka cron mode | Costs land in a topic. | Doesn't reach Grafana Cloud without another consumer and sink. Use for the warehouse or Flink path, not for dashboards. |

### 9.2 Path A: Alloy config

```alloy
// config.alloy: runs on the same host/network as the exporter; the exporter port is never exposed publicly
prometheus.scrape "cc_cost" {
  targets         = [{ __address__ = "confluent_cost_exporter:7979" }]
  metrics_path    = "/probe"          // the exporter has no /metrics
  scrape_interval = "5m"              // data is a daily snapshot; faster adds nothing
  scrape_timeout  = "30s"
  honor_labels    = true              // matches the repo's prometheus template; keeps the exporter's `id` label
  job_name        = "confluent_cost_exporter"
  forward_to      = [prometheus.relabel.cc_cost.receiver]
}

prometheus.relabel "cc_cost" {
  // Cardinality control: see 9.3 before enabling
  // rule { action = "labeldrop"  regex = "price|quantity|discount|original_amount|start" }
  forward_to = [prometheus.remote_write.grafana_cloud.receiver]
}

prometheus.remote_write "grafana_cloud" {
  endpoint {
    url = "https://prometheus-<region>.grafana.net/api/prom/push"   // from your stack's Prometheus details page
    basic_auth {
      username = sys.env("GC_PROM_USER")        // numeric instance ID
      password = sys.env("GC_API_TOKEN")        // access policy token, metrics:write only
    }
  }
}
```

Deploy Alloy and the exporter as two containers on one Docker network. Keep the Confluent key only on the exporter container and the Grafana token only on Alloy. Use a token scoped to `metrics:write`.

### 9.3 Problems specific to this exporter on Grafana Cloud

1. **Active-series cost.** Grafana Cloud bills and rate-limits by active series. The exporter puts `price`, `quantity`, `discount`, `original_amount`, `start` and `end_date` in labels, so every distinct line item and every day creates a new series. A mid-size org is likely hundreds to low thousands of series per day, and old days stop being active after a while. It is manageable, but check the number first.
2. **Dropping labels is not safe by default.** If you `labeldrop` the numeric labels, two line items that differ only in `price` or `discount` (for example tiered pricing) collapse into the same label set. Prometheus/Mimir then rejects the duplicate sample or keeps one, which silently under-reports cost. Either keep the labels, or first fix the exporter (move these to values or aggregate before exposing). The exporter's pedantic registry already fails the whole scrape with a 500 on exact duplicates, so test with your real data.
3. **Time axis is meaningless.** Samples are stamped at scrape time, not at the billing day. Historical days appear as the day you scraped them. Use `end_date` as a grouping label (as the shipped dashboard does) with `sum by (end_date)` instant queries, not time-series panels or `rate()`. Do not expect remote_write to backfill history; ingestion rejects samples that are too old.
4. **One day only by default.** With `DAYS_AGO=3`, `WINDOW=1` Grafana Cloud will show a single day. Set `WINDOW` wider for month-to-date (see 6.1), or keep history in the warehouse.
5. **Silent failure becomes silent zero.** Pitfall 7.1 means a bad key yields an empty 200 and Alloy reports the scrape as healthy (`up=1`). Add an alert on absence:

   ```promql
   absent_over_time(confluent_cloud_cost_amount[1d])
   ```

   Also alert on `up{job="confluent_cost_exporter"} == 0`.

### 9.4 Dashboards

- Provisioning in the compose stack does not apply to Grafana Cloud. Import JSON via the UI (Dashboards, New, Import) or the HTTP API / Terraform `grafana_dashboard`.
- `confluent_billing.json` uses the default data source, so it should work after import once the Grafana Cloud Prometheus data source is the default. Check the variables (`label_values(confluent_cloud_cost_amount, ...)`) resolve.
- `ccloud.json` hardcodes data source name `Prometheus` in ~62 places and a UID (`PBFA97CFB590B2093`) in others. On import, map the data source. Grafana Cloud's default data source is named like `grafanacloud-<stack>-prom`, so expect to rewrite these. Its Connect panels are broken regardless (pitfall 7.9).
- Skip `monitor_services.json`. It needs cAdvisor and node-exporter.

### 9.5 Confluent Cloud operational metrics (the `ccloud.json` half)

The repo scrapes the Metrics API export endpoint (`api.telemetry.confluent.cloud/v2/metrics/cloud/export`) with a Prometheus job. For Grafana Cloud, the same job can live in Alloy (`prometheus.scrape` with `basic_auth`, `metrics_path=/v2/metrics/cloud/export`, `params` for `resource.kafka.id`) and forward to the same remote_write. Grafana Cloud may also ship a ready-made Confluent Cloud integration; **UNVERIFIED**, check the Connections page in your stack before building your own. This path is independent of the cost exporter and is the more valuable source for per-topic usage if you plan to apportion cluster cost (6.4).

### 9.6 FSI / client considerations

- Cost data (accounts, environment IDs, cluster names, spend) leaves the client's perimeter for a SaaS vendor. For a regulated client that is a vendor-risk and data-residency question to settle before wiring this up, and a point in favor of the self-hosted Mikan whitepaper's pitch. Grafana Cloud stack region should match the client's residency requirements.
- Network egress: Alloy needs outbound HTTPS to Grafana Cloud and the exporter needs outbound to `api.confluent.cloud`. Neither requires inbound exposure.
- Use a dedicated Confluent service account key for the exporter, not a personal key. Rotate it, because the exporter logs the key ID.
- Per the safety rule, test the Alloy pipeline with a throwaway Grafana Cloud stack and a mock Billing API, not a client key or client tenant, from this tooling.

### 9.7 Recommendation

Path A is workable for environment/cluster-level cost dashboards, in about half a day. Resolve the cardinality and duplicate-label questions (9.3 items 1 and 2) against real data before you commit. For BU attribution it does not change the verdict in section 1: Grafana Cloud only displays what the exporter emits.
