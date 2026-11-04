---
title: Schema Linking Between Two Confluent Cloud Regions — Implementation (Config, REST, Terraform)
tags: [schema-registry, schema-linking, confluent-cloud, dr, multi-region, terraform, rest-api, import-mode, exporter, oauth, fsi]
sources: [https://docs.confluent.io/cloud/current/sr/schema-linking.html, https://docs.confluent.io/platform/current/schema-registry/develop/api.html, https://docs.confluent.io/confluent-cli/current/command-reference/schema-registry/exporter/confluent_schema-registry_exporter_create.html, https://docs.confluent.io/confluent-cli/current/command-reference/schema-registry/cluster/confluent_schema-registry_cluster_update.html, https://registry.terraform.io/providers/confluentinc/confluent/latest/docs/resources/confluent_schema_exporter, https://registry.terraform.io/providers/confluentinc/confluent/latest/docs/resources/confluent_schema_registry_cluster_mode]
related: [patterns/schema-linking-cp-to-cc-mtls, patterns/dr-cluster-linking, concepts/cluster-linking-topology, concepts/schema-registry-best-practices]
confidence: medium
last_updated: 2026-10-22
last_validated: 2026-10-22
---

# Schema Linking Between Two Confluent Cloud Regions — Implementation

## Summary

Confluent Cloud has **one Schema Registry (SR) per environment, in one region**, so cross-region linking means **two environments**. An **exporter**, created on the *source* SR, pushes schemas to the *destination* SR using destination credentials in the exporter's `config`. For DR, the destination SR is put in **`IMPORT` mode** so only the exporter can write to it and schema IDs are preserved. Steps in order: (1) credentials + RBAC, (2) destination to `IMPORT`, (3) exporter config + create, (4) verify. Sections 2–4 give each as CLI, REST, and Terraform. Checked against the live Confluent docs, CLI reference, SR API reference and Terraform provider 2.91.0 on 2026-10-22; not exercised against a live tenant (`mcp-confluent` was down).

## 1. Decisions to make before you type anything

| Decision | DR default | Why |
|---|---|---|
| `contextType` | **`NONE`** | Copies subjects as-is, so source default context → destination default context, same schema IDs. |
| Destination mode | `IMPORT` (global) | Blocks local writes; only the exporter writes. |
| Subjects | `[":*:"]` (all contexts) or an explicit list | `["*"]` is the default and means **default context only**. |
| Auth | Service-account API key (OAuth in §5) | Never a user's key. |

`contextType` caveat: the Schema Linking page also lists `DEFAULT` and `REPLACE`, but the **SR REST API reference, the CLI help and the Terraform resource list only `CUSTOM`, `NONE`, `AUTO`**. The CLI accepts `auto|custom|none`. Use `NONE` for DR; treat `DEFAULT` as untested.

If you instead want a side-by-side copy without touching the destination's own default context (active/active schemas), leave `contextType` as `AUTO` (lands in `.lsrc-<source-id>`) and put **only that context** into `IMPORT` (§2, context-level mode).

Placeholders used below:

```bash
# Source (primary, region A)
export SRC=https://psrc-aaaaa.us-east-1.aws.confluent.cloud
export SRC_ID=lsrc-aaaaa1          # source SR cluster ID
export SRC_KEY=...; export SRC_SECRET=...      # SR API key, source SR
# Destination (DR, region B)
export DST=https://psrc-bbbbb.us-west-2.aws.confluent.cloud
export DST_ID=lsrc-bbbbb1
export DST_KEY=...; export DST_SECRET=...      # SR API key, destination SR (owned by the exporter service account)
```

Get the IDs and endpoints from the Console (environment → right panel → **Stream Governance API**) or:

```bash
confluent environment use <env-id>
confluent schema-registry cluster describe     # Cluster = lsrc-…, Endpoint URL, Mode, Region
```

## 2. Prerequisite: service account, API key, RBAC, IMPORT mode

### 2.1 Service account, SR API key, role bindings (CLI)

The docs require the CLI for service-account-owned SR API keys; the Console can't create them for Schema Linking.

```bash
# Destination env: the identity the exporter writes as
confluent environment use <env-dr>
confluent iam service-account create schema-link-exporter \
  --description "Exporter writes into DR Schema Registry"
# → sa-xxxxxx

confluent api-key create --service-account sa-xxxxxx \
  --resource $DST_ID --description "Schema Linking destination key"
# Save key+secret now; the secret can't be retrieved later. These become DST_KEY / DST_SECRET.

confluent iam rbac role-binding create \
  --principal User:sa-xxxxxx --role ResourceOwner \
  --environment <env-dr> --schema-registry-cluster $DST_ID \
  --resource "Subject:*"
```

Source side: whoever creates the exporter needs `ResourceOwner` on the exported subjects (or `EnvironmentAdmin`, `DataSteward`, `OrganizationAdmin`), plus an SR API key for the source SR:

```bash
confluent environment use <env-primary>
confluent api-key create --resource $SRC_ID --description "Exporter admin (source SR)"
confluent iam rbac role-binding create \
  --principal User:<u-or-sa-id> --role ResourceOwner \
  --environment <env-primary> --schema-registry-cluster $SRC_ID \
  --resource "Subject:*"
```

Context-scoped bindings (for `AUTO`/`CUSTOM`): in the Console go to **Access and Accounts** → the service account → add access → Schema Registry → prefix rule `:.<context>:*` with `ResourceOwner`.

### 2.2 Set the DR Schema Registry to IMPORT mode

`IMPORT` mode goes on the **destination**. By default Schema Registry refuses to switch to `IMPORT` if it already contains schemas; add `force` to override (the docs call this out as useful in DR with Schema Linking). Do this before creating the exporter, and with the **destination's** credentials.

**CLI** (flag confirmed in the CLI reference: `--mode` accepts `readwrite`, `readonly`, `import`):

```bash
confluent environment use <env-dr>
confluent schema-registry cluster update --mode import
confluent schema-registry cluster describe        # Mode should now read IMPORT
```

The CLI has no `--force`. If the destination already has schemas and you need to override, use REST.

**REST** (global mode):

```bash
curl -s -u "$DST_KEY:$DST_SECRET" -X PUT "$DST/mode" \
  -H 'Content-Type: application/vnd.schemaregistry.v1+json' \
  -d '{"mode":"IMPORT"}'
# → {"mode":"IMPORT"}

# Destination already has schemas? Force it:
curl -s -u "$DST_KEY:$DST_SECRET" -X PUT "$DST/mode?force=true" \
  -H 'Content-Type: application/vnd.schemaregistry.v1+json' \
  -d '{"mode":"IMPORT"}'

# Verify
curl -s -u "$DST_KEY:$DST_SECRET" "$DST/mode"
```

Per-subject and per-context variants:

```bash
# One subject
curl -s -u "$DST_KEY:$DST_SECRET" -X PUT "$DST/mode/orders-value" \
  -H 'Content-Type: application/vnd.schemaregistry.v1+json' -d '{"mode":"IMPORT"}'

# One context, for AUTO/CUSTOM links so the default context stays READWRITE
curl -s -u "$DST_KEY:$DST_SECRET" -X PUT "$DST/mode/:.lsrc-aaaaa1:" \
  -H 'Content-Type: application/vnd.schemaregistry.v1+json' -d '{"mode":"IMPORT"}'
# context-level force: PUT "$DST/mode/:.lsrc-aaaaa1:?force=true"
```

Modes accepted by the API: `IMPORT`, `READONLY`, `READWRITE` (default), `FORWARD`. Error `42204` = invalid mode.

**Terraform** (resource `confluent_schema_registry_cluster_mode`, accepts `READWRITE`, `READONLY`, `READONLY_OVERRIDE`, `IMPORT`; has a `force` boolean, default `false`, which blocks a switch to `IMPORT` if the registry has schemas):

```hcl
resource "confluent_schema_registry_cluster_mode" "dr" {
  schema_registry_cluster {
    id = data.confluent_schema_registry_cluster.dr.id
  }
  rest_endpoint = data.confluent_schema_registry_cluster.dr.rest_endpoint
  mode          = "IMPORT"
  # force = true   # only if the DR SR already has schemas. Must be unset when using `terraform import`.

  credentials {
    key    = var.dr_sr_admin_key     # DR SR key allowed to change mode (not the exporter's key)
    secret = var.dr_sr_admin_secret
  }

  lifecycle {
    prevent_destroy = true           # provider recommendation for prod
  }
}
```

**Mode is global to the destination SR.** In `IMPORT`, regular clients can't register schemas there, which is the point for a passive DR region, but it's why the DR SR can't also serve as a live write registry. Flip it to `READWRITE` on failover (§6).

## 3. The exporter config file and CLI

The exporter's `config` is a **client config for talking to the destination SR**, so it carries the *destination* URL and credentials. It's created on the **source**.

### 3.1 `config.txt` (API key auth)

```properties
# DESTINATION Schema Registry (region B), not the source
schema.registry.url=https://psrc-bbbbb.us-west-2.aws.confluent.cloud
basic.auth.credentials.source=USER_INFO
# Destination SR API key owned by the exporter service account (§2.1)
basic.auth.user.info=<DST_KEY>:<DST_SECRET>
```

Rules from the docs: `schema.registry.url` must be an **FQDN**, not an IP. For the private path between two CC SRs use `https://<lsrc-id>.<region>.<cloud>.private.confluent.cloud` (not CCN, PNI, or Multi-PLATT `accesspoint.glb` endpoints). Behind a proxy (CP→CC) add `proxy.host=https://<fqdn>` and `proxy.port=<port>`.

### 3.2 Create the exporter (CLI, source environment)

```bash
confluent environment use <env-primary>

confluent schema-registry exporter create dr-link \
  --subjects ":*:" \
  --context-type none \
  --config ~/config.txt

# → Created schema exporter "dr-link".
```

Flags (from the CLI reference): `--config` (file path or `k=v,k=v`), `--subjects` (default `*`), `--subject-format` (e.g. `'dc_${subject}'`), `--context-type` (`auto|custom|none`, default `auto`), `--context-name`, `--schema-registry-endpoint`, `--environment`, `-o json|yaml`.

Variants:

```bash
# Specific subjects only
confluent schema-registry exporter create dr-link \
  --subjects payments.transaction.completed-value,payments.transaction.completed-key \
  --context-type none --config ~/config.txt

# Prefix wildcard
confluent schema-registry exporter create dr-link --subjects "payments.*" --context-type none --config ~/config.txt

# Side-by-side custom context on the destination (leave destination default context alone)
confluent schema-registry exporter create dr-link --subjects ":*:" \
  --context-type custom --context-name .primary --config ~/config.txt
```

Subject patterns accepted: explicit list; `prefix*`; `*` (default context only); `:*:` (all contexts); `:.ctx:*` (all subjects in a context); `:.ctx:prefix-*`.

### 3.3 Operate and verify

```bash
confluent schema-registry exporter list
confluent schema-registry exporter describe dr-link                 # passwords shown as [hidden]
confluent schema-registry exporter configuration describe dr-link
confluent schema-registry exporter status describe dr-link          # State RUNNING, Offset advancing
```

`STARTING` while it back-fills, then `RUNNING`. If it sits in `PAUSED` with errors, check the destination service account's role bindings first.

Change an exporter (must be paused; reset to re-scan existing schemas for newly added subjects):

```bash
confluent schema-registry exporter pause dr-link
confluent schema-registry exporter update dr-link --subjects ":*:"     # subjects, context-type, context-name, config
confluent schema-registry exporter reset dr-link                       # offset → -1, re-export everything on resume
confluent schema-registry exporter resume dr-link
```

Delete: `pause` then `delete`.

## 4. REST

All exporter calls go to the **source** SR with **source** credentials. The destination's credentials live inside the request's `config`.

### 4.1 Create

Request fields (SR API reference): `name`, `contextType` (`CUSTOM|NONE|AUTO`, default `AUTO`), `context` (only when `CUSTOM`), `subjects` (list), `subjectRenameFormat`, `kekRenameFormat`, `config` (map, **required**).

```bash
curl -s -u "$SRC_KEY:$SRC_SECRET" -X POST "$SRC/exporters" \
  -H 'Content-Type: application/vnd.schemaregistry.v1+json' \
  -d @- <<EOF
{
  "name": "dr-link",
  "contextType": "NONE",
  "subjects": [":*:"],
  "config": {
    "schema.registry.url": "$DST",
    "basic.auth.credentials.source": "USER_INFO",
    "basic.auth.user.info": "$DST_KEY:$DST_SECRET"
  }
}
EOF
# → {"name":"dr-link"}
```

With rename and a custom context:

```json
{
  "name": "dr-link-custom",
  "contextType": "CUSTOM",
  "context": ".primary",
  "subjects": ["payments.*"],
  "subjectRenameFormat": "dc_${subject}",
  "config": { "schema.registry.url": "...", "basic.auth.credentials.source": "USER_INFO", "basic.auth.user.info": "..." }
}
```

Errors: `40950` bad name, `40951` bad config, `40952` bad subjects, `40960` already exists, `40964` too many exporters.

### 4.2 Status and lifecycle

```bash
curl -s -u "$SRC_KEY:$SRC_SECRET" "$SRC/exporters"                       # list names
curl -s -u "$SRC_KEY:$SRC_SECRET" "$SRC/exporters/dr-link"               # info
curl -s -u "$SRC_KEY:$SRC_SECRET" "$SRC/exporters/dr-link/config"        # config
curl -s -u "$SRC_KEY:$SRC_SECRET" "$SRC/exporters/dr-link/status"
# → {"name":"dr-link","state":"RUNNING","offset":100,"ts":1631206325,"trace":""}
#   state: STARTING | RUNNING | PAUSED; trace holds the error text if it stopped

curl -s -u "$SRC_KEY:$SRC_SECRET" -X PUT "$SRC/exporters/dr-link/pause"
curl -s -u "$SRC_KEY:$SRC_SECRET" -X PUT "$SRC/exporters/dr-link/reset"    # 409/40963 if not paused first
curl -s -u "$SRC_KEY:$SRC_SECRET" -X PUT "$SRC/exporters/dr-link/resume"
curl -s -u "$SRC_KEY:$SRC_SECRET" -X DELETE "$SRC/exporters/dr-link"
```

Update (pause first):

```bash
curl -s -u "$SRC_KEY:$SRC_SECRET" -X PUT "$SRC/exporters/dr-link" \
  -H 'Content-Type: application/vnd.schemaregistry.v1+json' \
  -d '{"subjects":[":*:"],"contextType":"NONE","config":{ ... full config ... }}'
# Config only: PUT /exporters/dr-link/config
```

### 4.3 Verify on the destination

```bash
# Subjects landed
curl -s -u "$DST_KEY:$DST_SECRET" "$DST/subjects?subjectPrefix=:*:"

# Same ID → same schema on both sides (contextType NONE into IMPORT)
curl -s -u "$SRC_KEY:$SRC_SECRET" "$SRC/schemas/ids/100"
curl -s -u "$DST_KEY:$DST_SECRET" "$DST/schemas/ids/100"

# Destination mode
curl -s -u "$DST_KEY:$DST_SECRET" "$DST/mode"
```

Smoke test: register a schema on the source, then `GET $DST/subjects/<subject>/versions` and confirm it appears within seconds.

## 5. OAuth instead of API keys

Replace `basic.auth.*` in the exporter `config` with bearer settings. Required: an IdP registered in Confluent Cloud, an identity pool bound to a role on the destination SR.

```json
{
  "name": "dr-link",
  "contextType": "NONE",
  "subjects": [":*:"],
  "config": {
    "schema.registry.url": "https://psrc-bbbbb.us-west-2.aws.confluent.cloud",
    "bearer.auth.credentials.source": "OAUTHBEARER",
    "bearer.auth.issuer.endpoint.url": "https://login.example.com/oauth2/v2.0/token",
    "bearer.auth.client.id": "<client-id>",
    "bearer.auth.client.secret": "<from-vault>",
    "bearer.auth.scope": "<scope>",
    "bearer.auth.logical.cluster": "lsrc-bbbbb1",
    "bearer.auth.identity.pool.id": "pool-xxxxx"
  }
}
```

`bearer.auth.logical.cluster` is the **destination** SR ID. `identity.pool.id` is only required if you aren't using auto pool mapping. Optional: `bearer.auth.sub.claim.name`, `bearer.auth.scope.claim.name`, `bearer.auth.cache.expiry.buffer.seconds` (default 300). In the same shape, the file form for the CLI is a `key=value` file with the same properties.

## 6. DR failover and failback (commands)

Steady state: primary `READWRITE`, DR `IMPORT`, link primary → DR.

**Return path after an outage** (primary is back and must catch up on schemas registered on DR during the outage):

```bash
# 1. Pause the original link
curl -s -u "$SRC_KEY:$SRC_SECRET" -X PUT "$SRC/exporters/dr-link/pause"

# 2. Put original primary into IMPORT (force: it has schemas)
curl -s -u "$SRC_KEY:$SRC_SECRET" -X PUT "$SRC/mode?force=true" \
  -H 'Content-Type: application/vnd.schemaregistry.v1+json' -d '{"mode":"IMPORT"}'

# 3. Create a reverse exporter on DR → primary (same body as §4.1, with SRC/DST swapped) and wait for RUNNING with the offset caught up
curl -s -u "$DST_KEY:$DST_SECRET" -X POST "$DST/exporters" ...   # name e.g. dr-to-primary
```

Then either:

```bash
# Fail forward: DR becomes primary, original primary stays IMPORT
curl -s -u "$DST_KEY:$DST_SECRET" -X PUT "$DST/mode" \
  -H 'Content-Type: application/vnd.schemaregistry.v1+json' -d '{"mode":"READWRITE"}'

# Fail back: original primary active again
curl -s -u "$DST_KEY:$DST_SECRET" -X PUT "$DST/exporters/dr-to-primary/pause"
curl -s -u "$SRC_KEY:$SRC_SECRET" -X PUT "$SRC/mode" \
  -H 'Content-Type: application/vnd.schemaregistry.v1+json' -d '{"mode":"READWRITE"}'
curl -s -u "$DST_KEY:$DST_SECRET" -X PUT "$DST/mode" \
  -H 'Content-Type: application/vnd.schemaregistry.v1+json' -d '{"mode":"IMPORT"}'
curl -s -u "$SRC_KEY:$SRC_SECRET" -X PUT "$SRC/exporters/dr-link/resume"
```

During an actual outage the primary SR is unreachable, so the first action is only on the DR side: `PUT $DST/mode` to `READWRITE` so applications can register schemas. Keep these REST commands as the break-glass path; don't rely on a pipeline that needs both regions.

## 7. Terraform end to end

Provider `confluentinc/confluent` 2.91.0. Two environments, two SRs, one exporter. Because credentials differ per SR, either use provider aliases/workspaces per SR or per-resource `credentials` blocks (Option #1 in the provider docs, which puts keys in state; Option #2 keeps them in provider config).

### 7.1 Providers

```hcl
terraform {
  required_providers {
    confluent = {
      source  = "confluentinc/confluent"
      version = "~> 2.91"
    }
  }
}

provider "confluent" {
  cloud_api_key    = var.confluent_cloud_api_key    # control plane: env, SA, API key, role binding
  cloud_api_secret = var.confluent_cloud_api_secret
}
```

### 7.2 Environments and SR lookups

```hcl
resource "confluent_environment" "primary" {
  display_name = "payments-primary"
  stream_governance { package = "ADVANCED" }   # ESSENTIALS also supports Schema Linking
}

resource "confluent_environment" "dr" {
  display_name = "payments-dr"
  stream_governance { package = "ADVANCED" }
}

# Region of each SR follows the region chosen when Stream Governance is provisioned for the env
data "confluent_schema_registry_cluster" "primary" {
  environment { id = confluent_environment.primary.id }
}

data "confluent_schema_registry_cluster" "dr" {
  environment { id = confluent_environment.dr.id }
}
```

### 7.3 Exporter identity and RBAC on the destination

```hcl
resource "confluent_service_account" "exporter" {
  display_name = "schema-link-exporter"
  description  = "Exporter writes into the DR Schema Registry"
}

resource "confluent_api_key" "dr_sr" {
  display_name = "schema-link-dr-sr-key"
  owner {
    id          = confluent_service_account.exporter.id
    api_version = confluent_service_account.exporter.api_version
    kind        = confluent_service_account.exporter.kind
  }
  managed_resource {
    id          = data.confluent_schema_registry_cluster.dr.id
    api_version = data.confluent_schema_registry_cluster.dr.api_version
    kind        = data.confluent_schema_registry_cluster.dr.kind
    environment { id = confluent_environment.dr.id }
  }
}

resource "confluent_role_binding" "exporter_dr_subjects" {
  principal   = "User:${confluent_service_account.exporter.id}"
  role_name   = "ResourceOwner"
  crn_pattern = "${data.confluent_schema_registry_cluster.dr.resource_name}/subject=*"
}
```

For context-scoped links narrow `crn_pattern` to the context prefix (CRN form for a context prefix not verified; test one binding first).

### 7.4 Destination IMPORT mode (see §2.2)

`confluent_schema_registry_cluster_mode.dr` exactly as in §2.2. Keep `force = true` out unless the DR SR already holds schemas.

### 7.5 The exporter

Created on the **source** SR; the `destination_schema_registry_cluster` block is the target. Argument reference from the provider docs: `name` (required), `context_type` (`CUSTOM|NONE|AUTO`, default `AUTO`), `context`, `subject_rename_format`, `subjects`, `destination_schema_registry_cluster` (required), `config` (map of **non-sensitive** settings), `status` (`RUNNING|PAUSED`), `reset_on_update` (bool, default `false`).

```hcl
resource "confluent_schema_exporter" "primary_to_dr" {
  schema_registry_cluster {
    id = data.confluent_schema_registry_cluster.primary.id
  }
  rest_endpoint = data.confluent_schema_registry_cluster.primary.rest_endpoint

  credentials {                                  # SOURCE SR key (creates the exporter)
    key    = var.primary_sr_key
    secret = var.primary_sr_secret
  }

  name         = "dr-link"
  context_type = "NONE"                          # DR: source default context → destination default context
  subjects     = [":*:"]                         # all contexts; ["*"] = default context only
  # subject_rename_format = "dc_$${subject}"     # escape ${} in HCL as $${}
  status       = "RUNNING"
  reset_on_update = true                         # re-scan after subject/context changes (see note)

  destination_schema_registry_cluster {
    id            = data.confluent_schema_registry_cluster.dr.id
    rest_endpoint = data.confluent_schema_registry_cluster.dr.rest_endpoint
    credentials {                                # DESTINATION key, owned by the exporter service account
      key    = confluent_api_key.dr_sr.id
      secret = confluent_api_key.dr_sr.secret
    }
  }

  depends_on = [
    confluent_schema_registry_cluster_mode.dr,      # destination must be IMPORT first
    confluent_role_binding.exporter_dr_subjects,
  ]
}
```

Behaviors from the provider docs:
- **Updating exporter config requires the exporter to be paused.** The provider pauses automatically **only before delete**. For an update, apply once with `status = "PAUSED"` plus your change, then again with `status = "RUNNING"`. `reset_on_update = true` makes the provider reset the offset on update so newly added subjects' existing schemas get exported.
- **Import:** `terraform import confluent_schema_exporter.primary_to_dr <SRC_SR_ID>/dr-link`, with `IMPORT_SCHEMA_REGISTRY_ID`, `IMPORT_SCHEMA_REGISTRY_REST_ENDPOINT`, and (non-OAuth) `IMPORT_SCHEMA_REGISTRY_API_KEY` / `IMPORT_SCHEMA_REGISTRY_API_SECRET` set. Clear shell history afterward.
- **Sensitive values in state:** resource-level `credentials` blocks are stored unencrypted in state. Use an encrypted remote backend, or Option #2 (provider-level `schema_registry_*` settings, one SR per workspace).

### 7.6 Terraform with OAuth

Provider block carries the OAuth settings; the resource drops **both** `credentials` blocks and must set `destination_schema_registry_cluster.id`.

```hcl
provider "confluent" {
  oauth {
    oauth_external_token_url     = var.oauth_external_token_url
    oauth_external_client_id     = var.oauth_external_client_id
    oauth_external_client_secret = var.oauth_external_client_secret
    oauth_external_token_scope   = var.oauth_external_token_scope
    oauth_identity_pool_id       = var.oauth_identity_pool_id   # required for Entra ID, optional for Okta
  }
}

resource "confluent_schema_exporter" "primary_to_dr" {
  schema_registry_cluster { id = data.confluent_schema_registry_cluster.primary.id }
  rest_endpoint = data.confluent_schema_registry_cluster.primary.rest_endpoint

  name         = "dr-link"
  context_type = "NONE"
  subjects     = [":*:"]

  destination_schema_registry_cluster {
    id            = data.confluent_schema_registry_cluster.dr.id    # required with OAuth
    rest_endpoint = data.confluent_schema_registry_cluster.dr.rest_endpoint
  }
}
```

### 7.7 Failover in Terraform

Model mode as a function of a single variable, and keep §6 as the break-glass path:

```hcl
variable "active_region" { type = string }   # "primary" | "dr"

resource "confluent_schema_registry_cluster_mode" "primary" {
  schema_registry_cluster { id = data.confluent_schema_registry_cluster.primary.id }
  rest_endpoint = data.confluent_schema_registry_cluster.primary.rest_endpoint
  mode          = var.active_region == "primary" ? "READWRITE" : "IMPORT"
  force         = true          # switching back to IMPORT on a populated SR
  credentials {
    key    = var.primary_sr_key
    secret = var.primary_sr_secret
  }
}
# confluent_schema_registry_cluster_mode.dr: mode = var.active_region == "dr" ? "READWRITE" : "IMPORT"
```

A regional outage makes the failed SR unreachable to Terraform, so a normal `apply` will fail on refresh. Target the surviving side (`-target`, `-refresh=false`) or use REST.

## 8. Gotchas that bite in practice

- **`IMPORT` is on the destination, and applies before the exporter is created.** Create the exporter against a destination that's still `READWRITE` and you can end up with conflicting local IDs; with `contextType: NONE` the destination's own default-context schemas collide with incoming IDs.
- **`force` is how you reuse a non-empty DR SR.** Without it, REST/Terraform/the CLI refuse the switch.
- **`["*"]` is only the default context.** Use `":*:"` to include custom contexts.
- **Exporter state `PAUSED` with errors** is usually missing role bindings on the destination (the exporter stops if the creator's destination permissions are removed). Check `trace` in `GET /exporters/{name}/status`.
- **Exporters outlive their creator's access.** Alert on exporter create/update in the audit log.
- **Limit:** 10 exporters per environment on Essentials, 100 on Advanced per the limitations section; another section says 10 per SR. Confirm for the client's package.
- **CSFLE:** the exporter copies DEKs, KEK pointers, and rulesets; the destination principal needs `DeveloperWrite` on the KEK or the exporter pauses.
- **Data plane is separate.** Schema Linking moves schemas only. Pair with Cluster Linking for topics, and have DR consumers use the context whose IDs match the producer's ([[dr-cluster-linking]]).

## 9. Monitoring

Metrics API: `io.confluent.kafka.schema_registry/exporter_tasks` grouped by `exporter_state` and `has_error` (alert on `FAILED`, or `PAUSED` when unintended), and `.../schema_transfer_success_total` filtered by `metric.exporter_name` and `resource.schema_registry.id`. Metrics arrive in one-minute intervals.

## Related

- [Schema Linking CP → CC With mTLS](schema-linking-cp-to-cc-mtls.md) — hybrid CP source variant (proxy and OAuth config)
- [DR with Cluster Linking](dr-cluster-linking.md) — data-plane half of the DR story
- [Cluster Linking Topology](../concepts/cluster-linking-topology.md) — topologies Schema Linking mirrors
- [Schema Registry Best Practices](../concepts/schema-registry-best-practices.md) — compatibility, subject strategy, IDs not portable across envs
