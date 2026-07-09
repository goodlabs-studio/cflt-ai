output "folder_uid" {
  value       = grafana_folder.telum.uid
  description = "Grafana folder holding the Telum NNPA dashboards."
}

output "inference_dashboard_url" {
  value       = "${var.grafana_url}/d/telum-inference"
  description = "Direct link to the fraud-scoring inference dashboard."
}

output "contact_point_name" {
  value       = grafana_contact_point.telum_oncall.name
  description = "Contact point receiving NNPA-fallback alerts."
}
