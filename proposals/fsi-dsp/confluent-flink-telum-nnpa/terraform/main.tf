# =============================================================================
# main.tf — Grafana dashboards + alerting as code
# =============================================================================
# Terraform is PERIPHERAL in this build. There is no meaningful provider for
# PR/SM, z/VM, or LPAR configuration — Ansible is the infra workhorse (see
# ../README.md §1). TF earns its keep in exactly two places:
#
#   1. Grafana config-as-code (this file)
#   2. Any surrounding cloud adjuncts (DNS, off-box Kafka mirrors)
#
# The Prometheus recording rules and fallback alerts themselves live as a
# PrometheusRule CR (../observability/), because they must version with the
# workload, not with the dashboard.
# =============================================================================

terraform {
  required_version = ">= 1.7.0"
  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = "~> 3.0"
    }
  }
}

provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_auth
}

resource "grafana_folder" "telum" {
  title = "Confluent + Telum NNPA"
}

# -----------------------------------------------------------------------------
# Inference dashboard — the panel set that makes the Telum claim provable.
# The coverage_hash template variable is the join key between "which model build"
# and "which latency regime". Without it a regression is unattributable.
# -----------------------------------------------------------------------------
resource "grafana_dashboard" "inference" {
  folder    = grafana_folder.telum.uid
  overwrite = true
  config_json = jsonencode({
    title         = "Fraud Scoring — NNPA Inference"
    uid           = "telum-inference"
    timezone      = "utc"
    refresh       = "30s"
    schemaVersion = 39

    templating = {
      list = [
        {
          name       = "coverage_hash"
          type       = "query"
          datasource = { type = "prometheus", uid = var.prometheus_datasource_uid }
          query      = "label_values(flink_taskmanager_job_task_operator_inference_count, coverage_hash)"
          refresh    = 2
        },
      ]
    }

    panels = [
      {
        # Tail ratio, not absolute latency. NNPA-resident scoring is tight;
        # a blown-out p99/p50 is the fallback fingerprint.
        id      = 1
        title   = "Inference tail ratio (p99/p50) — fallback tripwire"
        type    = "timeseries"
        gridPos = { h = 8, w = 12, x = 0, y = 0 }
        targets = [{
          expr         = "fsi:inference_latency:tail_ratio{coverage_hash=~\"$coverage_hash\"}"
          legendFormat = "{{ model_version }}"
        }]
        fieldConfig = {
          defaults = {
            thresholds = {
              mode = "absolute"
              # >10 => almost certainly on the IFLs, not the accelerator.
              steps = [
                { color = "green", value = null },
                { color = "orange", value = 5 },
                { color = "red", value = 10 },
              ]
            }
          }
        }
      },
      {
        id      = 2
        title   = "Inference latency p50 / p99"
        type    = "timeseries"
        gridPos = { h = 8, w = 12, x = 12, y = 0 }
        targets = [
          { expr = "fsi:inference_latency_seconds:p50{coverage_hash=~\"$coverage_hash\"}", legendFormat = "p50" },
          { expr = "fsi:inference_latency_seconds:p99{coverage_hash=~\"$coverage_hash\"}", legendFormat = "p99" },
        ]
        fieldConfig = { defaults = { unit = "s" } }
      },
      {
        # The triad panel: latency + CPU + throughput on one axis set. Reading
        # these together is what separates "fallback" from "simply busy".
        id      = 3
        title   = "Fallback triad — latency vs IFL burn vs throughput"
        type    = "timeseries"
        gridPos = { h = 8, w = 12, x = 0, y = 8 }
        targets = [
          { expr = "fsi:inference_latency_seconds:p99", legendFormat = "p99 latency" },
          { expr = "avg(rate(node_cpu_seconds_total{mode!=\"idle\"}[5m]))", legendFormat = "IFL utilisation" },
          { expr = "fsi:inference:throughput_rps", legendFormat = "throughput rps" },
        ]
      },
      {
        # One inference TM per Telum chip. >1 on any node means two TaskManagers
        # share a single accelerator while another chip idles.
        id      = 4
        title   = "Inference TaskManagers per node (must be exactly 1)"
        type    = "stat"
        gridPos = { h = 8, w = 12, x = 12, y = 8 }
        targets = [{
          expr         = "count by (node) (kube_pod_info{namespace=\"confluent\"} * on (pod) group_left() kube_pod_labels{label_goodlabs_io_workload=\"flink-inference\"})"
          legendFormat = "{{ node }}"
        }]
        fieldConfig = {
          defaults = {
            thresholds = {
              mode  = "absolute"
              steps = [{ color = "red", value = null }, { color = "green", value = 1 }, { color = "red", value = 2 }]
            }
          }
        }
      },
    ]
  })
}

# -----------------------------------------------------------------------------
# Route NNPA-fallback alerts somewhere a human will actually see them. A silent
# fallback that pages nobody is indistinguishable from no fallback at all.
# -----------------------------------------------------------------------------
resource "grafana_contact_point" "telum_oncall" {
  name = "telum-oncall"

  dynamic "email" {
    for_each = length(var.alert_email_addresses) > 0 ? [1] : []
    content {
      addresses               = var.alert_email_addresses
      single_email            = false
      disable_resolve_message = false
    }
  }
}

resource "grafana_notification_policy" "telum" {
  group_by      = ["alertname", "coverage_hash"]
  contact_point = grafana_contact_point.telum_oncall.name

  policy {
    matcher {
      label = "component"
      match = "="
      value = "telum-nnpa"
    }
    contact_point   = grafana_contact_point.telum_oncall.name
    group_by        = ["alertname", "model_version", "coverage_hash"]
    group_wait      = "30s"
    group_interval  = "5m"
    repeat_interval = "4h"
  }
}
