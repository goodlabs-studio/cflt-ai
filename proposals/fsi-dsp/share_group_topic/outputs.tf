# =============================================================================
# share_group_topic — Outputs
# =============================================================================

output "topic_name" {
  description = "Fully-qualified queue topic name."
  value       = confluent_kafka_topic.this.topic_name
}

output "share_group_id" {
  description = "The share group authorized to consume this topic."
  value       = var.share_group_id
}

output "consumption_model" {
  description = "Documents the delivery contract for downstream consumers and audits."
  value       = "share-group (KIP-932): at-least-once, unordered, per-record acknowledgement"
}
