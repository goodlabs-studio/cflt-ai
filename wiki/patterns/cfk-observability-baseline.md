---
title: CFK Observability Baseline — Prometheus, JMX, and Helm
tags: [observability cfk kubernetes prometheus grafana jmx helm servicemonitor confluent-platform fsi]
sources:
  - https://docs.confluent.io/operator/current/co-monitor-cp.html
  - https://docs.confluent.io/operator/current/co-deploy-cfk.html
  - raw/repos/fsi-dsp/observability/grafana/jmx-exporter-config.yaml
  - raw/repos/fsi-dsp/observability/grafana/README.md
  - https://github.com/confluentinc/jmx-monitoring-stacks/tree/main/jmxexporter-prometheus-grafana/cfk
related:
  - patterns/aks-kafka-tuning
  - concepts/confluent-platform-broker-jmx
  - concepts/observability-metrics-mapping
  - concepts/schema-registry-observability
  - patterns/flink-runtime-models
confidence: high
last_updated: 2026-05-20
last_validated: 2026-05-20
---

# CFK Observability Baseline — Prometheus, JMX, and Helm

## Summary

Confluent for Kubernetes (CFK) deploys Kafka, ZooKeeper/KRaft, Schema Registry, Connect, ksqlDB, and Control Center as a set of operator-managed CRDs. The observability baseline is opinionated: JMX → Prometheus exporter sidecar (bundled `confluentinc/cp-enterprise-prometheus:2.0.0`) → Prometheus scrape → Grafana dashboards. This pattern documents the canonical wiring — CRD `spec.metrics` fields, Vault-injected JMX credentials, ServiceMonitor scrape patterns, and the FSI-specific overlay — so a new CFK deployment can ship a fully-instrumented cluster on day one.

## Pattern

### When to use

- Deploying Confluent Platform on Kubernetes via CFK Helm chart (`confluentinc/confluent-for-kubernetes`), CFK download bundle, or OpenShift OperatorHub
- Self-managed K8s deployments (CFK 3.2+ on EKS, AKS, GKE, OpenShift 4.x)
- FSI tenants where audit-log security (mTLS + RBAC + Vault credentials) is a hard requirement and the SaaS observability stack (CC Metrics API) is not in scope or insufficient

Do **not** use this pattern for:
- Confluent Cloud managed clusters — use the CC Metrics API + provider extension path documented in [Observability Metrics Mapping](../concepts/observability-metrics-mapping.md)
- Vanilla self-managed CP on RHEL/VMs without K8s — use the JMX exporter agent directly without ServiceMonitor (see [AKS Kafka Tuning](aks-kafka-tuning.md) for the broker side and [Confluent Platform Broker JMX](../concepts/confluent-platform-broker-jmx.md) for the MBean tree)

### Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│ Kubernetes namespace: confluent                                      │
│                                                                      │
│  ┌────────────────────┐    ┌────────────────────┐   ┌────────────┐  │
│  │ Kafka StatefulSet  │    │ SR / Connect /     │   │ KRaft      │  │
│  │ (broker pods)      │    │ ksqlDB Pods        │   │ controller │  │
│  │                    │    │                    │   │            │  │
│  │ ┌─────────────┐    │    │ ┌─────────────┐   │   │ pods       │  │
│  │ │ broker      │    │    │ │ component   │   │   │            │  │
│  │ └─────────────┘    │    │ └─────────────┘   │   └────────────┘  │
│  │ ┌─────────────┐    │    │ ┌─────────────┐   │                   │
│  │ │ jmx exporter│──────┐  │ │ jmx exporter│──┐│                   │
│  │ │  sidecar    │    │ │  │ │  sidecar    │  ││                   │
│  │ └─────────────┘    │ │  │ └─────────────┘  ││                   │
│  └────────────────────┘ │  └────────────────────┘                  │
│                         │                       │                   │
│             :7203/metrics                :7203/metrics              │
│                         │                       │                   │
│                         ▼                       ▼                   │
│                   ┌─────────────────────────────────┐               │
│                   │ ServiceMonitor (Prom Operator)  │               │
│                   └────────────────┬────────────────┘               │
└─────────────────────────────────────┼───────────────────────────────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │  Prometheus  │──┐
                              └──────────────┘  │
                              ┌──────────────┐  │
                              │   Grafana    │◀─┘
                              └──────────────┘
```

### Step 1 — Enable metrics in the CFK CR

CFK exposes a `spec.metrics` block on every component CR (`Kafka`, `SchemaRegistry`, `Connect`, `KsqlDB`, `KRaft`, `Zookeeper`). The minimal config — JMX enabled with the bundled Prometheus exporter:

```yaml
apiVersion: platform.confluent.io/v1beta1
kind: Kafka
metadata:
  name: kafka
  namespace: confluent
spec:
  replicas: 3
  image:
    application: confluentinc/cp-server:7.7.0
  metrics:
    authentication:
      type: mtls
    prometheus:
      blacklist: []
      whitelist: []
      rules: []
  podTemplate:
    annotations:
      prometheus.io/scrape: "true"
      prometheus.io/port: "7203"
      prometheus.io/path: "/metrics"
```

CFK ships `confluentinc/cp-enterprise-prometheus:2.0.0` as a sidecar that exposes JMX metrics on the well-known prom-exporter port. The sidecar lifecycle is managed by the operator — you don't define it manually.

### Step 2 — JMX authentication via Vault injection (FSI-tier)

For FSI tenants, JMX must require authentication. The canonical CFK pattern uses Vault sidecar injection to mount `/vault/secrets/jmx/jmxremote.password` (`0600`) and `jmxremote.access` (`0644`) into each pod:

```yaml
apiVersion: platform.confluent.io/v1beta1
kind: Kafka
metadata:
  name: kafka
spec:
  metrics:
    jmx:
      authentication:
        directoryPathInContainer: /vault/secrets/jmx
      accessControl:
        enabled: true
        directoryPathInContainer: /vault/secrets/jmx
  podTemplate:
    annotations:
      vault.hashicorp.com/agent-inject: "true"
      vault.hashicorp.com/role: "confluent-operator"
      vault.hashicorp.com/agent-run-as-user: "1001"
      vault.hashicorp.com/agent-run-as-group: "1001"

      # JMX password file (0600)
      vault.hashicorp.com/agent-inject-secret-jmx-password: "secret/kafka/jmx/password"
      vault.hashicorp.com/secret-volume-path-jmx-password: "/vault/secrets/jmx"
      vault.hashicorp.com/agent-inject-file-jmx-password: "jmxremote.password"
      vault.hashicorp.com/agent-inject-perms-jmx-password: "0600"

      # JMX access file (0644)
      vault.hashicorp.com/agent-inject-secret-jmx-access: "secret/kafka/jmx/access"
      vault.hashicorp.com/secret-volume-path-jmx-access: "/vault/secrets/jmx"
      vault.hashicorp.com/agent-inject-file-jmx-access: "jmxremote.access"
      vault.hashicorp.com/agent-inject-perms-jmx-access: "0644"
```

The Kubernetes `Secret` + `secretRef` form works too; Vault is preferred when the FSI tenant already runs a Vault control plane and wants secret rotation off the K8s lifecycle.

### Step 3 — Prometheus scrape via ServiceMonitor (Prometheus Operator)

If using the Prometheus Operator (kube-prometheus-stack or similar), define a `ServiceMonitor` per component:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kafka-broker-metrics
  namespace: confluent
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: kafka
      type: kafka
  endpoints:
    - port: prometheus
      interval: 30s
      path: /metrics
      scheme: https
      tlsConfig:
        ca:
          secret:
            name: prometheus-client-tls
            key: ca.crt
        cert:
          secret:
            name: prometheus-client-tls
            key: tls.crt
        keySecret:
          name: prometheus-client-tls
          key: tls.key
```

Without the operator, use a `prometheus.io/scrape: "true"` pod annotation (Step 1) and let Prometheus discover pods directly.

### Step 4 — JMX exporter rule set

The bundled CFK Prometheus exporter ships with a default rule set. To override (e.g., add a CL mirror lag rule), supply your own ConfigMap and reference it under `spec.metrics.prometheus.rules`. The fsi-dsp `jmx-exporter-config.yaml` source (9 patterns covering UnderReplicatedPartitions, BytesIn/OutPerSec, ActiveControllerCount, PartitionCount, FetcherLagMetrics, RequestsPerSec, IsrShrinks/Expands) is a known-good baseline — see [Confluent Platform Broker JMX](../concepts/confluent-platform-broker-jmx.md) for the full MBean → exporter-rule mapping.

### Step 5 — Grafana dashboards

Two reference paths:

1. **Confluent's `jmx-monitoring-stacks` repo** — `confluentinc/jmx-monitoring-stacks/jmxexporter-prometheus-grafana/cfk` ships a Helm chart that deploys Prometheus, Grafana, and the JMX exporter rules together with pre-built dashboards.
2. **fsi-dsp's 5 dashboard templates** — `dashboard-cluster-health.json`, `dashboard-consumer-lag.json`, `dashboard-connect-status.json`, `dashboard-dr-readiness.json`, `dashboard-flink-jobs.json` — template-variable-driven, ADR-008-tier-aware alert thresholds, import directly via Grafana API or UI.

The fsi-dsp templates use these placeholders that must be replaced before import:

| Variable | Default | Description |
|---|---|---|
| `{{CLUSTER_ID}}` | (empty) | Target Kafka cluster ID (e.g., `lkc-xxxxx` for CC, or CFK cluster name) |
| `{{DOMAIN_PREFIX}}` | `*` | Topic filter regex (e.g., `corebanking`, `fraud`, `*`) |
| `{{ENVIRONMENT}}` | `prod` | Environment label |
| `{{JMX_EXPORTER_HOST}}` | `localhost` | JMX scrape target (typically the in-pod sidecar) |
| `{{JMX_EXPORTER_PORT}}` | `9101` or `7203` | Port (matches docker-compose convention; differs for CFK bundled exporter) |
| `{{MIRROR_LAG_WARN_<TIER>}}` / `{{MIRROR_LAG_ALERT_<TIER>}}` | per SLA tier | DR readiness alert thresholds — see [SLA Tiers](../concepts/sla-tiers.md) and [Cluster Linking Observability](cluster-linking-observability.md) |

### Step 6 — Log aggregation

Logs ship separately from metrics. Two patterns:

| Pattern | When to use | Notes |
|---|---|---|
| **Fluentd / Fluent Bit → Loki** | Cost-sensitive, Grafana stack alignment | Loki + Grafana queries on the same UI as metrics |
| **Fluent Bit → Elasticsearch / OpenSearch** | FSI tenants that already run Elastic | Pairs with audit-log routing — see [Audit Log SIEM Integration](audit-log-siem-integration.md) |

DaemonSet topology for the log collector; pod-level structured-JSON logging from each Confluent component. Tag with `confluent_component`, `cluster_id`, `topic` for query parity with metrics.

### FSI overlay

- **mTLS everywhere**: `spec.metrics.authentication.type=mtls`, ServiceMonitor with `tlsConfig`, never plaintext JMX scrape across pods
- **Vault for JMX credentials**: never use Kubernetes Secrets for FSI-tier JMX credentials directly; let Vault rotation drive the secret lifecycle
- **RBAC service accounts per component**: separate service accounts for `Kafka`, `SchemaRegistry`, `Connect`, etc. — never a shared "confluent" SA
- **Network policy**: restrict ServiceMonitor scrape ingress to the Prometheus pod's IP/label; block lateral JMX access from anywhere else
- **Audit log retention**: route Kafka audit-log topic to Splunk via the [Audit Log SIEM Integration](audit-log-siem-integration.md) pattern; do not depend on Dynatrace/Grafana event retention for compliance

## Caveats

- **CFK bundled exporter port differs from open-source convention**: `confluentinc/cp-enterprise-prometheus:2.0.0` exposes `/metrics` on port `7203` by default, not the open-source JMX exporter's conventional `9101`. Standardize the port in your scrape config; don't assume one or the other.
- **`platform.confluent.io/jmx-rmi-server-urls` annotation** is required when JMX clients (external Prometheus, JConsole) need to connect through a NodePort or LoadBalancer rather than via the pod's in-cluster service. Format: `<external-ip>:<port>` comma-separated for each broker.
- **`automountServiceAccountToken`**: CFK operator pods require this `true` (default). Component pods (Kafka, SR, etc.) can disable it for FSI hardening if no in-cluster API access is needed; defer per-tenant.
- **Webhook overhead**: CFK validating webhooks (`kafka-pods.webhooks.platform.confluent.io`, `evictions.webhooks.platform.confluent.io`, etc.) protect against unsafe pod deletion. Disabled by default since CFK 2.8; enable for FSI tenants — they prevent `min.insync.replicas` violations during K8s maintenance. Memory limit may need bump (1024Mi) for clusters > 100k partitions.
- **PV reclaim policy**: ALWAYS `Retain` for FSI. CFK webhooks block CR deletion when `ReclaimPolicy: Delete` to prevent accidental data loss, but the default still requires deliberate override on PV provisioning class.
- **OpenShift OperatorHub deployments have limited Helm customization** — CFK installed via OperatorHub via Subscription can only override a subset of values. For deep customization (custom metrics rules, Vault annotations), use the Helm bundle path instead.
- **5-minute CC Metrics API offset**: If hybrid (some CFK on-prem, some CC), correlate metrics carefully — CC Metrics API publishes with a ~5 min lag; CFK JMX is real-time. Don't draw alert correlations across the time-skew boundary.

## Related

- [AKS Kafka Tuning](aks-kafka-tuning.md) — Azure-specific tuning (VM SKU, Premium SSD v2) that this pattern's observability stack monitors
- [Confluent Platform Broker JMX](../concepts/confluent-platform-broker-jmx.md) — MBean reference behind the JMX exporter rules
- [Observability Metrics Mapping](../concepts/observability-metrics-mapping.md) — cross-provider query syntax once Prometheus is producing metrics
- [Schema Registry Observability](../concepts/schema-registry-observability.md) — SR JMX MBeans this baseline scrapes
- [Flink Runtime Models](flink-runtime-models.md) — CMF on CFK adds Flink JM/TM JMX surfaces that ride this same Prometheus pipeline
- [Audit Log SIEM Integration](audit-log-siem-integration.md) — Splunk routing for the audit-log topic (complement to the metrics pipeline)
