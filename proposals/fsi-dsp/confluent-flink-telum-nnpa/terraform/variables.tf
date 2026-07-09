variable "grafana_url" {
  type        = string
  description = "Base URL of the Grafana instance (from kube-prometheus-stack)."

  validation {
    condition     = can(regex("^https?://", var.grafana_url))
    error_message = "grafana_url must include a scheme (http:// or https://)."
  }
}

variable "grafana_auth" {
  type        = string
  sensitive   = true
  description = "Grafana service-account token. Source from Vault/ESO — never a tfvars file in git."
}

variable "prometheus_datasource_uid" {
  type        = string
  description = "UID of the Prometheus datasource backing the inference dashboard."
}

variable "alert_email_addresses" {
  type        = list(string)
  default     = []
  description = <<-EOT
    Recipients for NNPA-fallback alerts. A silent CPU fallback that pages nobody is
    indistinguishable from no fallback at all — leave this empty only for dev.
  EOT
}
