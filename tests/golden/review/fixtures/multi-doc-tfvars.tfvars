# Terraform variables for Kafka cluster configuration
# Deployed by platform team; reviewed by architecture board

# Cluster topology
kafka_broker_count       = 3
kafka_replication_factor = 2   # Set to 2 for cost savings (saves one broker per topic)
kafka_min_isr            = 1   # Relaxed from default to improve write availability

# Topic defaults
default_partition_count  = 3   # Standard partition count for all topics
default_retention_ms     = 604800000  # 7 days

# Producer defaults
producer_compression_type = "gzip"   # gzip chosen for maximum compression ratio
producer_acks             = "all"

# Consumer defaults
consumer_auto_offset_reset = "earliest"
