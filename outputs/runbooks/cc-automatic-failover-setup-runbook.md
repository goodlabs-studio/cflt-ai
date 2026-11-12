# Confluent Cloud one-click DR: setup guide and runbook

GoodLabs Studio · v0.2 · 2026-11-12 · Draft for review

## 1. Purpose and summary

This page sets up one-click DR on Confluent Cloud. Confluent calls the feature Automatic Failover. Two Dedicated clusters in different regions are joined into a switchover pair. Clients connect to one global bootstrap URL, and a single failover command moves every client to the other cluster.

We recommend the platform team owns the whole DR pair: both clusters, the one bidirectional cluster link, the switchover pair and the failover decision. App teams own their topics, consumer groups and principals through prefix RBAC. They don't own cluster links. Automatic Failover allows only one link per pair, and that link must mirror every topic, so per-team links aren't possible.

We don't plan on the Console for this setup end to end. The docs give no Console path for the bidirectional cluster link, the switchover pair, the endpoint pair or failover. We use the Console for clusters, networking, identity and checks, and the Confluent CLI for the link, the pair and failover. Terraform can manage the pair and endpoint resources but can't trigger failover or restore.

| Section | What it covers |
|---|---|
| 2 | How the pieces fit together |
| 3 | Readiness checks before any build work |
| 4 | High-level guide: what happens where, and who owns it |
| 5 | The setup runbook, phase by phase, with checks and rollback |
| 6 | Failover, restore and failback commands |
| 7 | Open questions and next steps |

Everything in this page comes from the Confluent Cloud Automatic Failover tutorial, the `switchover/v1` API reference and OpenAPI spec, the `confluent switchover` CLI reference and the Schema Linking docs, checked on 2026-11-12. Anything we haven't tested is in a recommendation callout with a test.

## 2. How it works

### 2.1 What is deployed

| Component | What it is | Owner |
|---|---|---|
| Primary cluster | Dedicated cluster in region A. Active in normal running. | Platform team |
| Secondary cluster | Dedicated cluster in region B, same CKU count. Holds mirror topics in normal running. | Platform team |
| Bidirectional cluster link | One link, same name and same link ID on both clusters. Mirrors all topics, consumer offsets and ACLs. | Platform team |
| Switchover pair (`sw-…`) | The cluster-level pairing. Exactly one member is active. Failover is an operation on this object. | Platform team |
| Switchover endpoint (`se-…`) | Pairs one PrivateLink endpoint on each cluster and gives the global bootstrap URL. | Platform team |
| Global bootstrap URL | `glkc-<sw-id>-<se-id>.global.glb.confluent.cloud:9092`. Resolves to whichever member is active. | Platform team publishes it; app teams use it |
| Schema Linking exporter | Copies schemas to the secondary environment's Schema Registry. Not part of Automatic Failover. | Platform team |

### 2.2 Normal running and failover

1. Clients bootstrap from the global URL, which resolves to the primary cluster.
2. Producers write to the primary. The link mirrors every topic, consumer offset and ACL to the secondary.
3. An operator runs `confluent switchover pair failover`. Mirror topics on the secondary become writable topics, and the link direction reverses.
4. The global URL now resolves to the secondary. Clients on Kafka 4.0 or later re-bootstrap and reconnect there.
5. After recovery, a planned failover moves the active role back. An unplanned failover needs a restore step first.

The docs give an order of magnitude for an unplanned failover of about 50 seconds plus about 1 second per topic. A planned failover also waits for consumer lag to drain. Neither figure is an RTO. The measured RTO comes from the acceptance test in Phase 8.

## 3. Readiness checks

Run these before Phase 1. Any "No" stops the build.

| Check | Requirement | Why it matters |
|---|---|---|
| Cluster type | Dedicated or Enterprise on both sides. This page assumes Dedicated. | Basic, Standard and Freight aren't supported. |
| Region | Neither cluster in AWS `us-west-2`. | Excluded during Limited Availability. |
| Organization | Both clusters in the same organization. Different environments are allowed. | Pairs can't span organizations. |
| Consumer groups | Under 1,000 active groups per cluster. | Limited Availability limit. |
| Client versions | Every producer and consumer on Kafka client 4.0 or later (Java, librdkafka, Python, Go, .NET, Node.js). | Older clients can't re-bootstrap. REST Proxy clients aren't supported. |
| Client credentials | OAuth or Global API keys. | Cluster-scoped API keys can't fail over. |
| Transactions | No pipeline depends on exactly-once across failover. | Mirror topics don't support transactions. Failover can leave hung transactions. |
| Stateful apps | Kafka Streams, ksqlDB, Flink and managed connectors have a separate failover plan. | Automatic Failover doesn't move them. |
| Other links | Neither cluster is the destination of another link, has another bidirectional link, or is the source of a source-initiated link. | These break the pair or stop replicating when the cluster is passive. |
| Link connection mode | The DR link uses `connection.mode=OUTBOUND` (the default) on both clusters. | `INBOUND` isn't supported for the pair's link. |
| DNS | Internal resolvers can resolve `*.global.glb.confluent.cloud` over public DNS. | Clients can't find the global URL otherwise. |
| Forward proxies | Any proxy in the client path passes TLS SNI unchanged. | Stripping or rewriting SNI breaks failover. |
| Tooling | Confluent CLI 4.78.0 or later. Terraform provider `confluentinc/confluent` 2.88.0 or later. | Older versions don't have the switchover commands or resources. |
| Cloud tags | Tags, including CSFLE tags, are applied on both clusters. | Tags don't sync between paired clusters. |
| Billing | Budget approved. Billing starts 2026-12-01. | No charge before that date. |

## 4. High-level guide

### 4.1 What happens where

| Phase | Task | Console | CLI | Terraform |
|---|---|---|---|---|
| 1 | Environments, clusters, networks, PrivateLink access | Yes | Yes | Yes (preferred) |
| 1 | BYOK on both clusters, before pairing | Yes | Yes | Yes |
| 2 | Link service account, role bindings, Global API key | Yes | Yes | Yes |
| 3 | Bidirectional cluster link | No | Yes | Yes |
| 4 | Switchover pair | No (not documented) | Yes | Yes |
| 5 | Endpoint pair | No (not documented) | Yes | Yes |
| 6 | Schema Linking exporter | Partly | Yes | Yes |
| 7 | Client role bindings on both clusters | Yes | Yes | Yes (preferred) |
| 8 | Acceptance test | No | Yes | No |
| Ongoing | Lag and link monitoring | Yes | Yes | No |
| Ops | Failover, restore, failback | No (not documented) | Yes | No |

We recommend Terraform for every resource in Phases 1 to 7, with the CLI commands in this page as the reference and the manual fallback. Failover stays a CLI or REST operation run by whoever owns incidents.

### 4.2 Steps in the Console

1. Create or pick the environments. One environment per region is the simplest model. The pair can live in either.
2. In each environment's **Network management** tab, create a Confluent Cloud network in the target region with PrivateLink, and register only the AWS accounts that host the DR clients.
3. Create one Dedicated cluster per region on those networks, with the same CKU count. Turn on BYOK on both before pairing if it's used.
4. Create the service account for the link and grant it `CloudClusterAdmin` on both clusters.
5. Create the AWS VPC endpoints for both clusters. Clients in region A must reach the region B endpoint, and the reverse.
6. Switch to the CLI for Phases 3 to 5.
7. Use the Console afterwards to check the link and mirror topics on the secondary cluster, and to watch mirroring lag.

## 5. Setup runbook

### 5.1 Variables

Set these once in the operator's shell. Never commit secrets.

```bash
export ORG=<org-id>
export PRIMARY_ENV=<env-id>          SECONDARY_ENV=<env-id>
export PRIMARY_LKC=<lkc-id>          SECONDARY_LKC=<lkc-id>
export PRIMARY_LKC_BOOTSTRAP=<host:9092>
export SECONDARY_LKC_BOOTSTRAP=<host:9092>
export PRIMARY_NETWORK=<n-id>        SECONDARY_NETWORK=<n-id>   # PrivateLink networks, used in Phase 5
export PAIR_ENV=$PRIMARY_ENV         # environment that hosts the switchover pair
export PRIMARY_CLUSTER_CRN="crn://confluent.cloud/organization=$ORG/environment=$PRIMARY_ENV/cloud-cluster=$PRIMARY_LKC"
export SECONDARY_CLUSTER_CRN="crn://confluent.cloud/organization=$ORG/environment=$SECONDARY_ENV/cloud-cluster=$SECONDARY_LKC"
```

The operator runs Confluent CLI 4.78.0 or later and needs `OrganizationAdmin` or `EnvironmentAdmin`. The pair and failover API doesn't accept OAuth during Limited Availability, so the operator uses a Cloud API key from a service account with one of those roles.

### 5.2 Phase 1: clusters and networking

Owner: platform team. Tool: Console or Terraform.

1. Create both Dedicated clusters, one per region, same CKU count, on PrivateLink networks.
2. Turn on BYOK on both clusters if it's used. It can't be added after pairing.
3. Create the PrivateLink endpoints in AWS for both clusters, and the private DNS records for each.
4. Confirm cross-region reachability: a host in region A connects to the region B cluster endpoint, and the reverse.

Exit criteria: both clusters are running, and both are reachable from both client regions over PrivateLink.

Rollback: delete the clusters and networks. Nothing depends on them yet.

### 5.3 Phase 2: identity for the link

Owner: platform team. Tool: Console, CLI or Terraform.

```bash
# Service account used only by the DR link
confluent iam service-account create dr-link-sa --description "Cluster link identity for DR pair"
export CL_SA=<sa-id>

# CloudClusterAdmin on both clusters, so the link can manage topics during failover
confluent iam rbac role-binding create --principal User:$CL_SA \
  --role CloudClusterAdmin --environment $PRIMARY_ENV --cloud-cluster $PRIMARY_LKC
confluent iam rbac role-binding create --principal User:$CL_SA \
  --role CloudClusterAdmin --environment $SECONDARY_ENV --cloud-cluster $SECONDARY_LKC
```

Then create a Global API key for `dr-link-sa`. A cluster-scoped key won't work in both directions.

```bash
confluent api-key create --resource global --service-account $CL_SA \
  --description "dr-link global key" -o json
```

 In Terraform, put `prevent_destroy` on this key, because deleting it breaks both directions of the link.

The link identity must be able to `LIST` and `DESCRIBE` all topics and mirror topics on the secondary. The docs warn that missing permissions can cause data loss.

Exit criteria: `dr-link-sa` has `CloudClusterAdmin` on both clusters and a Global API key.

### 5.4 Phase 3: bidirectional cluster link

Owner: platform team. Tool: CLI or Terraform.

Write one config file, `dr-link.config`, used for both directions:

```properties
# Both sides are peers; required by Automatic Failover
link.mode=BIDIRECTIONAL
# Mirror every current and future topic, so new topics are protected without a ticket
auto.create.mirror.topics.enable=true
auto.create.mirror.topics.filters={"topicFilters": [{"name": "*","patternType": "LITERAL","filterType": "INCLUDE"}]}
topic.config.sync.ms=1000
# Carry committed offsets across, so consumers resume near where they stopped
consumer.offset.sync.enable=true
consumer.offset.group.filters={"groupFilters": [{"name": "*","patternType": "LITERAL","filterType": "INCLUDE","topicTypes": ["LOCAL_MIRROR"]}]}
consumer.offset.sync.ms=1000
# Carry ACLs across; RBAC role bindings are NOT synced and are handled in Phase 7
acl.sync.enable=true
acl.filters={ "aclFilters": [ { "resourceFilter": { "resourceType": "any", "patternType": "any" }, "accessFilter": { "operation": "any", "permissionType": "any" } } ] }
acl.sync.ms=1000
# Remote side: the Global API key of dr-link-sa
security.protocol=SASL_SSL
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username="$CL_API_KEY" password="$CL_API_KEY_SECRET";
# Local side: the same key, so one file works in both directions
local.security.protocol=SASL_SSL
local.sasl.mechanism=PLAIN
local.sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username="$CL_API_KEY" password="$CL_API_KEY_SECRET";
```

Fill in the key and secret from a secrets store when the file is written, and delete the file afterwards. If the link uses OAuth instead, use `OAUTHBEARER` on both sides and leave out `extension_logicalCluster`, so the same file works in both directions.

Don't set `connection.mode`. The default, `OUTBOUND`, is required on both clusters. Never put the global bootstrap URL in a link config. The docs say it causes all topics to fail.

`auto.create.mirror.topics.enable=true` departs from our usual default of `false`. Automatic Failover requires every topic to be mirrored, and mirroring `*` automatically is how new topics stay protected.

Create the link on the primary first. Wait for the command to succeed before creating the secondary side. If both sides are created at about the same time they can get different link IDs, and the pair later fails with `REMOTE_LINK_NOT_FOUND`.

```bash
confluent kafka link create dr-link --remote-cluster $SECONDARY_LKC \
  --remote-bootstrap-server $SECONDARY_LKC_BOOTSTRAP \
  --config dr-link.config \
  --cluster $PRIMARY_LKC --environment $PRIMARY_ENV

# Only after the command above succeeds
confluent kafka link create dr-link --remote-cluster $PRIMARY_LKC \
  --remote-bootstrap-server $PRIMARY_LKC_BOOTSTRAP \
  --config dr-link.config \
  --cluster $SECONDARY_LKC --environment $SECONDARY_ENV
```

Check:

```bash
confluent kafka link list --cluster $PRIMARY_LKC --environment $PRIMARY_ENV
confluent kafka link list --cluster $SECONDARY_LKC --environment $SECONDARY_ENV
```

Exit criteria: both sides show `ACTIVE` and the same link ID.

Rollback: if the IDs differ, delete the link on both clusters with `confluent kafka link delete dr-link` and create it again, one side at a time.

### 5.5 Phase 4: switchover pair

Owner: platform team. Tool: CLI or Terraform.

Before pairing, the secondary cluster must have no producers, no consumers and no active consumer groups. Otherwise mirror topics can get stuck in `PENDING_STOPPED`.

```bash
confluent switchover pair create dr-pair \
  --member name=primary,crn=$PRIMARY_CLUSTER_CRN \
  --member name=secondary,crn=$SECONDARY_CLUSTER_CRN \
  --active-member primary \
  --environment $PAIR_ENV
export SW=<sw-id>

confluent switchover pair describe $SW --environment $PAIR_ENV
```

Exit criteria: the pair reaches `READY_TO_FAILOVER`.

Anyone who only reads the pair (on-call, monitoring) needs `EnvironmentOperator` on `$PAIR_ENV`. `CloudClusterAdmin` alone returns 403.

### 5.6 Phase 5: endpoint pair and global bootstrap URL

Owner: platform team. Tool: CLI or Terraform.

Pair one PrivateLink endpoint on each cluster. Both endpoints must be the same type. For PrivateLink the type is `private`, and each side names its cluster's network by CRN. The CLI reference allows exactly one of `network` or `access-point` per side. Dedicated PrivateLink clusters use `network`.

```bash
confluent switchover endpoint create dr-pair-endpoint \
  --parent-resource-crn crn://confluent.cloud/organization=$ORG/environment=$PAIR_ENV/switchover-pair=$SW \
  --endpoint name=primary-ep,type=private,network=crn://confluent.cloud/organization=$ORG/environment=$PRIMARY_ENV/network=$PRIMARY_NETWORK \
  --endpoint name=secondary-ep,type=private,network=crn://confluent.cloud/organization=$ORG/environment=$SECONDARY_ENV/network=$SECONDARY_NETWORK \
  --environment $PAIR_ENV
export SE=<se-id>

confluent switchover endpoint describe $SE --environment $PAIR_ENV
```

> **Recommendation for the platform team:** The tutorial only walks through public endpoints. The `private` type and network CRN come from the CLI reference and the API spec, not from a worked example. To test: on the sandbox pair, the endpoint reaches `READY`, the global URL resolves to the PrivateLink endpoint of the active cluster from both client regions, and a client in each region connects through it. Must pass before the production build.

No CLI command, API response or Terraform output returns the global URL. Build it from the two IDs:

```text
glkc-<sw-id>-<se-id>.global.glb.confluent.cloud:9092
```

Exit criteria: the endpoint is `READY`, and the global URL resolves from both client regions to the primary cluster's PrivateLink endpoint.

### 5.7 Phase 6: schemas

Owner: platform team. Tool: CLI or Terraform.

Automatic Failover doesn't fail over Schema Registry. Set up a Schema Linking exporter from the primary environment's Schema Registry to the secondary's, and keep the secondary in `IMPORT` mode so only the exporter writes there.

1. If schemas live in the default context, export into the secondary's default context. ksqlDB, broker-side Schema ID Validation and the topic viewer on mirror topics need that.
2. If the client uses named contexts per business unit, run one exporter per context and keep the context name the same on the secondary.
3. Set `confluent.key.schema.validation` and `confluent.value.schema.validation` on topics in Terraform, on both clusters. Cluster Linking doesn't copy them. If topics also use `confluent.schema.validation.context.name`, set it on both clusters the same way. That one is our addition, not named in the Automatic Failover docs.

Exporters are limited to 10 per environment with the Essentials package and 100 with Advanced.

### 5.8 Phase 7: client onboarding

Owner: app teams, with platform review. Tool: Terraform.

1. Create every client role binding on **both** clusters. RBAC bindings don't sync. ACLs do. Producers need `DeveloperWrite` on their topics. Consumers need `DeveloperRead` on their topics and `DeveloperRead` on their consumer groups. The principal is a service account for API keys, or an identity pool for OAuth.
2. Move clients to OAuth or Global API keys. OAuth clients must remove `extension_logicalCluster` from their JAAS config.
3. Apply this client baseline:

```properties
# The only bootstrap a client ever uses; never a member cluster's own bootstrap
bootstrap.servers=glkc-<sw-id>-<se-id>.global.glb.confluent.cloud:9092
# Go back to the global URL when cached metadata goes stale after failover
metadata.recovery.strategy=rebootstrap
# Producers otherwise wait 5 minutes before re-bootstrapping after an unplanned failover
metadata.recovery.rebootstrap.trigger.ms=30000
```

4. Restart the clients to pick up the change.

Lowering `metadata.recovery.rebootstrap.trigger.ms` means a short network blip can also trigger a re-bootstrap. 30 seconds is our starting value. Tune it per workload.

### 5.9 Phase 8: acceptance test

Owner: platform team and one app team. Run in a sandbox pair first, then in production during an agreed window.

1. Produce to a test topic on the global URL. Confirm the mirror topic exists on the secondary and lag returns to zero.
2. Run a `PLANNED` failover to the secondary. Record the time until producers and consumers resume.
3. Confirm consumers resume near their last committed offset, with duplicates only, no gaps.
4. Fail back with a `PLANNED` failover to the primary.
5. In the sandbox only, run an `UNPLANNED` failover, then restore and fail back.

Exit criteria: measured RTO for both failover types is recorded in the DR plan, and the failback leaves the pair in `READY_TO_FAILOVER`.

### 5.10 Monitoring

Owner: platform team. Tool: Console, CLI or Metrics API.

Check mirroring lag per partition on the secondary:

```bash
confluent kafka mirror describe <topic> --link dr-link \
  --cluster $SECONDARY_LKC --environment $SECONDARY_ENV
```

Alert on two Metrics API values: MaxLag (the most messages behind on any mirrored partition, per topic or per link), which shows how much data would be lost in an unplanned failover, and Mirroring Throughput. Check the pair stays `READY_TO_FAILOVER` with `confluent switchover pair describe $SW --environment $PAIR_ENV`.

### 5.11 Rollback of the whole build

Undo in reverse order: client bootstrap back to the primary cluster's own bootstrap, then the endpoint pair, then the switchover pair, then the link. Delete the endpoint before the pair. Deleting the pair doesn't delete its endpoints.

```bash
confluent switchover endpoint delete $SE --environment $PAIR_ENV --force
# If this fails with "endpoint must be deleted first", wait a moment and retry
confluent switchover pair delete $SW --environment $PAIR_ENV --force
```

In Terraform, remove the `prevent_destroy` block from the link's Global API key before destroying anything that includes it.

> **Recommendation for the platform team:** The docs only show the delete commands as part of a full teardown, where the clusters are deleted next. They don't say what state the clusters and link are left in when only the pair goes. To test: in the sandbox, delete the endpoint, then the pair, and confirm both clusters and the link stay `ACTIVE` with no topic changes. Must pass before the production build.

## 6. Operating the pair

Failover, restore and failback all prompt for confirmation. Add `--force` only in automation.

**Planned failover.** Use when the primary is up, such as for maintenance. No data loss, and failback needs no restore.

```bash
confluent switchover pair failover $SW --active-member secondary \
  --failover-type PLANNED --environment $PAIR_ENV
```

**Unplanned failover.** Use when the primary is down. Data not yet mirrored isn't on the secondary. You can start planned and escalate to unplanned if it takes too long.

```bash
confluent switchover pair failover $SW --active-member secondary \
  --failover-type UNPLANNED --environment $PAIR_ENV
```

**Restore.** Required after an unplanned failover, before failback. It truncates unreplicated data on the original primary permanently. If those records matter, open a Confluent Support case first so consumers can be allow-listed to read them off the passive cluster. Make sure the truncation doesn't reach tiered storage, or the topic goes to `PENDING_RESTORE_MIRROR` and has to be recreated.

```bash
confluent switchover pair failover $SW --failover-type RESTORE --environment $PAIR_ENV
```

**Failback.** A planned failover back to the primary, once lag is small.

```bash
confluent switchover pair failover $SW --active-member primary \
  --failover-type PLANNED --environment $PAIR_ENV
```

**While failed over.** Make topic config changes directly on the active cluster, with the CLI, API or Console. Mirror topics aren't visible through the switchover commands in this state.

Outside Automatic Failover, the incident runbook also covers: reversing the Schema Linking exporter, moving managed connectors, Flink statements and ksqlDB, and rebuilding Kafka Streams state. Fully managed connector offsets aren't replicated by the link, so read them with the connector offsets API before failover and set them on the other side. Self-managed connector offsets live in regular topics and are mirrored. Kafka Streams and ksqlDB can't run against mirror topics on the passive side, so their state rebuild time adds to RTO.

## 7. Open questions and next steps

### 7.1 Open questions

| Question | Who answers | Why it matters |
|---|---|---|
| Does the Console support the bidirectional link, switchover pairs and failover yet? | Confluent account team | The docs don't show it. Today this is a CLI operation. |
| Must the pair's clusters share one environment? | Confluent account team | The API reference says same environment; the tutorial says different environments are allowed. Hosting the pair in the primary environment fits both readings. |
| Does Confluent Cloud Flink read schemas from named contexts? | Confluent account team | Decides whether per-business-unit contexts work for Flink jobs. |
| Is a written RTO or SLA available for failover? | Confluent account team | The docs give only an order of magnitude. |

### 7.2 Next steps

1. Platform team runs Phases 1 to 8 on a sandbox pair, including the two recommendation tests above.
2. App teams inventory client versions and credential types against section 3.
3. Platform team writes the Terraform modules for Phases 1 to 7 from the sandbox build.
4. Whoever owns incidents adds section 6 and the out-of-scope steps to the incident runbook, and names who may trigger failover.
