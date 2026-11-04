# Create a Confluent Cloud Kafka Cluster via REST API

Reference for provisioning a Kafka cluster with the Confluent Cloud Cluster Management (`cmk/v2`) API.

**Sources (fetched 2026-10-09 via `confluent-docs`):**
- Create a Kafka Cluster: https://docs.confluent.io/cloud/current/clusters/create-cluster.md
- Confluent Cloud APIs (auth): https://docs.confluent.io/cloud/current/api.md
- Cluster API reference: https://docs.confluent.io/cloud/current/ccloud/clusters-cmk-v-2/

---

## Prerequisites

1. **Environment ID** (`env-xxxxxx`). Find it in the Cloud Console or with `confluent environment list`.
2. **Cloud API key** (not a Kafka cluster key). Create it in the Cloud Console under API keys, or with `confluent api-key create --resource cloud`. The owning principal needs OrganizationAdmin or EnvironmentAdmin.
3. Operator or admin access to the environment.

## Authentication

- Base URL: `https://api.confluent.cloud`. HTTPS only.
- HTTP Basic auth: username = Cloud API key ID, password = Cloud API key secret.
- Header form: `Authorization: Basic base64("<KEY_ID>:<KEY_SECRET>")`.

```shell
export CC_CLOUD_KEY="<cloud-api-key-id>"
export CC_CLOUD_SECRET="<cloud-api-key-secret>"
export CC_ENV_ID="env-xxxxxx"
```

## Create a Basic cluster

```shell
# Basic is the lowest-cost tier, suited to dev/test. Use Standard or Enterprise for production.
curl -sS -X POST "https://api.confluent.cloud/cmk/v2/clusters" \
  -u "${CC_CLOUD_KEY}:${CC_CLOUD_SECRET}" \
  -H "Content-Type: application/json" \
  -d '{
    "spec": {
      "display_name": "demo-basic-cluster",
      "availability": "Low",
      "cloud": "AWS",
      "region": "us-east-1",
      "config": { "kind": "Basic" },
      "environment": { "id": "'"${CC_ENV_ID}"'" }
    }
  }'
```

- Success: `HTTP 202 Accepted`, body describes the cluster with `status.phase` = `PROVISIONING`.
- Provisioning takes up to ~5 minutes.
- Response includes `spec.kafka_bootstrap_endpoint` and `spec.http_endpoint`, which clients need.

## Request fields

| Field | Required | Notes |
|---|---|---|
| `spec.display_name` | Yes | 64 characters or fewer. Allowed: letters, numbers, whitespace, `. , & _ + \| [ ] / -` |
| `spec.availability` | Yes | Orgs created on/after 2024-04-16: `Low` (99.5%/99.9%) or `High` (99.99%) for Basic, Standard, Enterprise. Older orgs: `SINGLE_ZONE` or `MULTI_ZONE`. Dedicated: `SINGLE_ZONE` or `MULTI_ZONE`. |
| `spec.cloud` | Yes | `AWS`, `GCP`, or `AZURE` |
| `spec.region` | Yes | Valid region for the provider. **Cannot be changed after creation.** |
| `spec.config.kind` | Yes | `Basic`, `Standard`, `Enterprise`, `Dedicated`, `Freight` |
| `spec.config.cku` | Dedicated only | Integer CKU count. Multi-zone needs at least 2. |
| `spec.config.encryption_key` | Optional | BYOK key, Dedicated/Enterprise/Freight |
| `spec.environment.id` | Yes | `env-xxxxxx` |
| `spec.network` | Private networking only | `{"id": "n-xxxxx", "environment": "env-xxxxxx"}`. Create the network first. |

Upgrade path: Basic can be upgraded to Standard. Standard cannot be downgraded to Basic.

## Other cluster types

**Standard or Enterprise, private network:**
```json
{
  "spec": {
    "display_name": "ProdKafkaCluster",
    "availability": "High",
    "cloud": "AWS",
    "region": "us-east-1",
    "config": { "kind": "Enterprise" },
    "environment": { "id": "env-xxxxxx" },
    "network": { "id": "n-xxxxx", "environment": "env-xxxxxx" }
  }
}
```

**Dedicated, public endpoint:**
```json
{
  "spec": {
    "display_name": "ProdKafkaCluster",
    "availability": "SINGLE_ZONE",
    "cloud": "GCP",
    "region": "us-east4",
    "config": { "kind": "Dedicated", "cku": 2 },
    "environment": { "id": "env-xxxxxx" }
  }
}
```

**Dedicated, private network:** add the same `network` object as above.

## Terraform alternative

Resource `confluent_kafka_cluster` in the `confluentinc/confluent` provider. Docs: https://registry.terraform.io/providers/confluentinc/confluent/latest/docs/resources/confluent_kafka_cluster

## CLI alternative

```shell
confluent kafka cluster create my_new_cluster --cloud "aws" --region "us-west-2"
```

---

## Not yet verified

- Status polling (`GET /cmk/v2/clusters/{id}`) and delete (`DELETE /cmk/v2/clusters/{id}`) were not confirmed against the docs in this session. Verify in the Cluster API reference before use.
- The full Cloud API reference page (`api.md`) exceeds the fetch size limit. Only the auth section was checked.
