---
title: "USM Support Matrix and Implementation: CP 7.9.x vs CP 8.1.x"
tags: [usm, unified-stream-manager, confluent-platform, rhel8, ansible, upgrade, support-matrix, fsi]
related: [patterns/usm-enablement-cp-on-rhel8, patterns/schema-linking-cp-to-cc-mtls, patterns/cp-mtls-self-signed-setup]
confidence: medium
last_updated: 2026-10-13
last_validated: 2026-10-13
---

# USM Support Matrix and Implementation: CP 7.9.x vs CP 8.1.x

## Summary

Both lines can run USM on RHEL 8. **Latest patches today (Oct 13, 2026): CP 7.9.10 and CP 8.1.6.** Pick by support runway and by what you want to do next, not by USM capability: the USM Agent is versioned independently of CP and behaves the same on either line. The only version-specific USM facts are the minimum CP patch, which cp-ansible line deploys the Agent, and the support dates.

**Recommendation:** 8.1.6 if the client wants support past Feb 2027 and can fund a second upgrade at the end of 2027. 7.9.10 if they want the smallest change now and accept a forced move by Feb 2028 (Platinum). Do not stop at the USM floors (7.9.6 / 8.1.0); both lines shipped a USM telemetry deadlock fix and security fixes after those.

All facts below are from `confluent-docs` (Oct 13, 2026) unless marked **(inference)** or **(not verified)**.

## 1. Matrix: CP line vs USM

| | **CP 7.9.x** | **CP 8.1.x** |
|---|---|---|
| Latest patch | **7.9.10** | **8.1.6** |
| Kafka version | 3.9 | 4.1 |
| Minimum CP patch for USM | **7.9.6** | **8.1.0** (matrix says "8.1.x") |
| Recommended USM floor (my pick) | 7.9.7 or later; target 7.9.10 | 8.1.3 or later; target 8.1.6 |
| USM Agent 1.0.x | Yes (7.9.6+) | Yes |
| USM Agent 1.1.x | Yes (7.9.6+) | Yes |
| USM Agent 1.2.x | Yes (7.9.6+) | Yes |
| Latest Agent | 1.2.1 (Aug 24, 2026) | 1.2.1 |
| Native Agent on RHEL 8 | Agent 1.2.0+ | Agent 1.2.0+ |
| Agent via Podman on RHEL 8 | Agent 1.0.x / 1.1.x | Agent 1.0.x / 1.1.x |
| RHEL 8 supported for CP itself | Yes | **Yes (last 8.x line that is)** |
| cp-ansible line that deploys USM | 7.9.x: Agent 1.0.x to 1.1.x listed | 8.1.x: Agent 1.0.x to 1.1.x listed |
| `confluent_package_version` mandatory in cp-ansible | From cp-ansible **7.9.10** | From cp-ansible **8.1.6** |
| Dual-stack (IPv4+IPv6) Agent networking | No (needs CP 8.2+, Agent 1.1.0+) | No (needs CP 8.2+) |
| ZooKeeper | Last line supporting it; client is already on KRaft | Removed |
| Control Center | Legacy bundled; cp-ansible lists C3 Next-Gen 2.0 to 2.1 | Next-Gen 2.3.x (separate package) |
| Community end of support | Feb 19, 2027 | Oct 15, 2026 |
| Enterprise Standard end of support | Feb 19, 2027 | Oct 15, 2027 |
| **Enterprise Platinum end of support** | **Feb 19, 2028** | **Oct 15, 2028** |
| Fixes for USM issues | USM telemetry deadlock fixed in **7.9.7** | USM telemetry deadlock fixed in **8.1.3** |
| Next hop OS requirement | 8.x: RHEL 8 still OK (8.1) | 8.2 and 8.3 require **RHEL 9+** |

USM Agent lifecycle (same on both lines): 1.2.0 released June 19, 2026; standard end of life Dec 19, 2026; standard end of support June 19, 2028; no Platinum tier; patches limited to two quarterly releases in the first six months. 1.2.1 is a security and maintenance patch.

## 2. Patch equivalence (what you get by landing on a given patch)

| Change | 7.9.x | 8.1.x |
|---|---|---|
| Connect credential masking improvements (`connect.password.field.masking.disable`) | 7.9.6 | 8.1.2 |
| JSON Schema serializer security fix (CONFSA-2026-06) | 7.9.7 | 8.1.3 |
| ksqlDB security fixes (CONFSA-2026-03/04/05) | 7.9.7 | 8.1.3 |
| **USM broker telemetry deadlock fix** | **7.9.7** | **8.1.3** |
| Opt-in DoS hardening (`confluent.bounded.request.*`, `transaction.id.max.length`, `max.decompressed.message.bytes`) and Cluster Linking OAuth URL validation | 7.9.9 | 8.1.5 |
| mTLS principal mapping from certificate SAN URI (`SANURIRULE:`) | Not in 7.9 release notes | 8.1.6 |

The advisory text is on the Confluent support portal and was not read; check severity before the client's change review.

Procurement note (8.1 release notes): USM is designed to share only telemetry and resource metadata with Confluent Cloud, and the notes say this lets you adopt USM without accepting the full Confluent Cloud data processing addendum. Have the client's legal team confirm that against their contract.

## 3. Doc conflicts and gaps that affect implementation

1. **Ansible USM page vs everything else.** `ansible-usm.html` says the Agent "cannot be deployed on RHEL 8" and lists CP and Ansible 8.1.x or later. The versions page, USM Get Started, USM Sizing and the Agent support policy all say RHEL 8 works (native from Agent 1.2.0, Podman for 1.0.x/1.1.x) and the matrix lists CP 7.9.6+.
2. **cp-ansible matrix lags the Agent.** It lists USM Agent 1.0.x to 1.1.x for every cp-ansible line from 7.9 through 8.3, with no 1.2.x entry, yet the cp-ansible 8.3.2 release notes mention Agent 1.3.0 packages. The **7.9.x branch source defaults to Agent 1.2.1**, which confirms the table is stale (section 3b). Remaining question: whether the RHEL 8 native install actually works under cp-ansible 7.9.x, since the Ansible USM page still says "cannot be deployed on RHEL 8".
3. **Podman route.** No page says whether cp-ansible drives the Podman deployment for Agent 1.0.x/1.1.x. **(not verified)**
4. **7.9.10 and 8.1.6 specifically.** The Agent matrix says "7.9.6+" and "8.1.x"; no page names 7.9.10 or 8.1.6. Range reading only.

**Ask Confluent Support/SE before committing:** can cp-ansible deploy Agent 1.2.x natively on RHEL 8, on both the 7.9.10 and 8.1.6 lines? If not, put the Agent on a RHEL 9 host (the brokers can stay on RHEL 8; **(inference)**: the Agent is a separate proxy host).

## 3a. Manual provisioning vs adopting cp-ansible

**What the docs allow.** The USM "Deploy" page says to deploy the Agent "using one of the following supported toolsets": Confluent for Kubernetes or Confluent Ansible. No page I read documents a manual install of the Agent, and none lists the broker, controller and Connect settings (the embedded reporters) that point them at the Agent. So a manual path is **undocumented**, which means unsupported in practice. It may be technically possible; the Agent is an Envoy-based proxy with a properties file **(inference)**. A hand-rolled install would also leave you without a supported way to take Agent upgrades, and Agent minors arrive often because each gets at most two patches.

**What adopting cp-ansible "just for this" really means.** The Agent deploy is not isolated. The documented run is `--tags=usm_agent,kafka_controller,kafka_broker,kafka_connect`, which redeploys controllers, brokers and Connect so they report to the Agent. On an estate that wasn't installed with cp-ansible, that means cp-ansible takes over templating `server.properties` and the service units on every node.

| Option | Effort | Risk | Supportable |
|---|---|---|---|
| **A. Full cp-ansible adoption, then USM** | High: inventory for every node, secrets, certs, listeners | High on prod unless rehearsed; the playbooks rewrite broker config | Yes, documented path |
| **B. cp-ansible for the Agent host only** (`--tags=usm_agent`), broker and Connect reporter settings added by hand | Medium | Medium; reporter properties are not documented in the pages I read **(not verified)** | Unclear; ask Confluent |
| **C. Fully manual Agent and broker config** | Medium to high | High; no vendor procedure, no upgrade path | No |
| **D. Podman container for the Agent (Agent 1.0.x/1.1.x on RHEL 8)** | Medium | Unknown; the docs mention it but I found no procedure | Mentioned only; no steps found |

**Constraints that make option A harder than it sounds**
- **Ansible Discovery cannot discover KRaft clusters**, and it doesn't support the Community edition. The client is on KRaft, so Discovery won't generate the inventory. You'd write it by hand, and encrypted passwords have to be filled in manually.
- **Custom service names are not supported** by cp-ansible; it would recreate the cluster with default names.
- **RHEL 8 control node**: Ansible 9.x only.
- The cp-ansible **7.9.x branch defaults to Agent 1.2.1** (`confluent_usm_agent_package_version`), which is native on RHEL 8. The USM networking page's "installs 1.0.0 by default" is stale. Still pin the version explicitly.

**Recommendation.** Do not hand-roll it. Ask Confluent Support/SE two questions first, and get the answers in writing:
1. Is there a supported manual procedure for the Agent and the broker, controller and Connect reporter settings?
2. If not, can cp-ansible be run scoped to the Agent host without redeploying the brokers?

If the answer to both is no, adopt cp-ansible, but stage it: build the inventory from a non-production replica, run `--check --diff` to compare what it would change against the live configs, rehearse a full run in non-prod, then roll prod node by node under change control. For an FSI client that hand-manages brokers, that is a real project. If the only goal is monitoring, weigh it against Control Center before committing.

**What the toolset pages reveal about the moving parts (CFK quick start and CFK USM page, Ansible USM page)**

| Piece | What it is | Where documented |
|---|---|---|
| Agent artifact | Container image `confluentinc/cp-usm-agent:<ver>` (CFK) or a package from `packages.confluent.io` pinned by `confluent_usm_agent_package_version` (Ansible) | CFK quick start, Ansible/networking pages |
| Agent to Cloud | `FRONTDOOR_URL` (+ `:443`), `ENVIRONMENT_ID`, API key/secret as basic auth (CFK secret holds `username=` / `password=`) | CFK quick start, Ansible page |
| Brokers, controllers, Connect to Agent | One client-side "usmAgentClient" setting per component: Agent URL (`http://<agent>:10000`, the dataplane port), auth (basic, basic+TLS, or mTLS, never basic+mTLS), optional `clientMetricsEnabled` | CFK USM page; Ansible vars `usm_agent_*`, `kafka_broker_usm_agent_username/password`, `kafka_controller_...`, `kafka_connect_...` |
| Client metrics (KIP-714) | Opt-in; CFK 3.2.x with CP **7.9.6+, 8.1.2+ or 8.2.0+**; Ansible `usm_client_metrics_enabled` (default off) | CFK USM page, Ansible page |
| Agent tuning | `USM_AGENT_CUSTOM_ARGS` env var (CFK example `-l trace`), `usm_agent_custom_properties` (Ansible) | CFK quick start, networking page |
| Verification | `usm-agent-validz` (VM) / `kubectl confluent cluster usmagent usm-agent-validz` | Deploy page |

**The docs pages give only abstractions, but the cp-ansible source gives the raw properties.** The README (`docs/sample_inventories/usm_agent/README_USM_AGENT.md`, 8.1.x) documents Agent-side variables only: the auth toggles, `ssl_*` cert paths, `ccloud_*`, `usm_client_metrics_enabled`, and four sample inventories (`usm_agent_no_auth.yml`, `usm_agent_basic_auth.yml`, `usm_agent_basic_auth_tls.yml`, `usm_agent_mtls.yml`). It has no broker or Connect properties. Those are in `roles/variables/vars/main.yml` on the **7.9.x branch** (section 3b). The CFK quick start also sets Kafka `metricReporter.enabled: false` when wiring in USM; I don't know whether that is required **(not verified)**.

### 3b. What cp-ansible actually writes (7.9.x branch source)

Read from `github.com/confluentinc/cp-ansible`, branch `7.9.x` (branch head, not the 7.9.10 tag), via WebFetch. A summarising model returned the text, so **diff it against the repo at the exact tag before using it**. License is Apache 2.0.

This confirms cp-ansible 7.9.x carries full USM wiring for brokers, controllers and Connect (including a ZooKeeper-events variant), and that its default Agent package is **1.2.1** (`confluent_usm_agent_package_version: 1.2.1`), not 1.0.0 as the USM networking page says. That page is stale.

**Brokers** (`kafka_broker_properties`, enabled when a `usm_agent` host group exists):
```properties
confluent.telemetry.exporter._usm.enabled=true
confluent.telemetry.exporter._usm.type=http
confluent.telemetry.exporter._usm.client.base.url=<usm_agent_url>          # http(s)://<agent-host>:10000, comma-joined for several agents
confluent.telemetry.exporter._usm.client.request.timeout.ms=60000
confluent.telemetry.exporter._usm.buffer.batch.items.max=4000
confluent.telemetry.exporter._usm.buffer.inflight.submissions.max=10
confluent.telemetry.exporter._usm.buffer.pending.batches.max=80
confluent.client.topic.metrics.manager=org.apache.kafka.server.metrics.PlatformClientTopicMetricsManager
confluent.consumer.lag.emitter.enabled=true
confluent.consumer.lag.calculator.enabled=true
confluent.consumer.group.status.enabled=true
confluent.consumer.lag.calculator.empty.lag.retention.ms=86400000
# auth: basic -> ..._usm.api.key / ..._usm.api.secret = client user/password; no basic -> both set to the literal "dummy"
# TLS: ..._usm.https.ssl.protocol=TLSv1.2, ssl.truststore.location/password
# mTLS adds: ..._usm.https.ssl.keystore.location/password, ssl.key.password
# ZooKeeper-mode or KRaft-migration brokers also get the ..._usm.events.* and confluent.catalog.collector.* keys
```

**KRaft controllers** (`kafka_controller_properties`) get the same `_usm` exporter keys plus the events and catalog collector set:
```properties
confluent.telemetry.exporter._usm.events.enabled=true
confluent.telemetry.exporter._usm.events.client.base.url=<usm_agent_url>
confluent.telemetry.exporter._usm.events.client.request.timeout.ms=60000
confluent.telemetry.exporter._usm.events.filtering.enabled=true
confluent.telemetry.exporter._usm.events.filtering.routes.allowed=catalog-events
confluent.catalog.collector.enable=true
confluent.catalog.collector.destination.topic=catalog-events
confluent.catalog.collector.full.configs.enable=true
confluent.catalog.collector.multitenant.topics.enable=false
confluent.catalog.collector.max.bytes.per.snapshot=52428800
# events.api.key/secret and events.https.ssl.* mirror the non-events keys
```

**Connect** (`kafka_connect_properties`):
```properties
metric.reporters=io.confluent.telemetry.reporter.TelemetryReporter
confluent.telemetry.exporter._usm.enabled=true
confluent.telemetry.exporter._usm.type=http
confluent.telemetry.exporter._usm.client.base.url=<usm_agent_url>
confluent.connect.metadata.events.enabled=true
confluent.connect.metadata.events.emitter.type=cloud.events.http
confluent.connect.metadata.events.client.base.url=<usm_agent_url>
# auth: confluent.telemetry.exporter._usm.api.key/secret and confluent.connect.metadata.events.api.key/secret (or "dummy")
# TLS/mTLS: ..._usm.https.ssl.* and confluent.connect.metadata.events.ssl.* (protocol, truststore, keystore, key.password)
```

**Client metrics (KIP-714)**, only when `usm_client_metrics_enabled: true`, on brokers and controllers:
`confluent.telemetry.external.client.metrics.usm.push.enabled=true`, `...external.client.metrics.push.enabled=true`, `...delta.temporality=true`, `...subscription.interval.ms.list=60000`, plus a long `...subscription.metrics.list` of consumer and producer metrics (not reproduced).

**Schema Registry** (hybrid setup only; these match the USM docs): `usm.schema.registry.remote.endpoint`, `.api.key`, `.api.secret`, optional `.context.prefix`, and the `UsmSchemaRegistryExtension` in the resource extensions.

**The Agent itself** (`usm_agent_properties`, rendered to `usm-agent.properties`):
```properties
confluent.usm-agent.listener.admin.port=9901
confluent.usm-agent.listener.controlplane.port=9999
confluent.usm-agent.listener.dataplane.port=10000
confluent.usm-agent.listener.monitoring.port=9910
confluent.usm-agent.listener.dataplane.basic.auth.enabled=<true|false>
confluent.usm-agent.listener.dataplane.ssl.enabled=<true|false>
confluent.usm-agent.listener.dataplane.ssl.client.auth.enabled=<true|false>
confluent.usm-agent.ccloud.environment-id=<env-id>
confluent.usm-agent.ccloud.host=<frontdoor host>
confluent.usm-agent.ccloud.port=443
confluent.usm-agent.ccloud.ssl.enabled=true
confluent.usm-agent.ccloud.ssl.trusted.ca.location=<CA bundle path>      # RHEL: /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
confluent.usm-agent.ccloud.basic.auth.credential.location=<ccloud_credential.yaml path>
# basic: confluent.usm-agent.listener.dataplane.basic.auth.credential.location=<cp_credential.yaml path>
# TLS: ...dataplane.ssl.server.certificate.location / .server.key.location / .server.key.password.location
# mTLS: ...dataplane.ssl.client.auth.trusted.ca.location
```
The Cloud credential file is an Envoy secret (`type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.Secret`, secret name `credential`) whose `inline_string` is `Basic <base64(apikey:apisecret)>`. Extra Agent settings go in `usm_agent_custom_properties`. The role also templates a systemd override, logging config and logrotate. The package is `confluent-usm-agent`. The ExecStart and the exact `cp_credential.yaml.j2` contents were **not** seen.

**What this changes:** a manual deployment is mechanically small (one package, one properties file, two credential files, a systemd unit, and about a dozen `confluent.telemetry.*` keys per component). That makes the **sandbox-renderer** approach below realistic: capture the real rendered output from a throwaway cluster instead of trusting this transcription. It does not make a hand-built install supported.

**Realistic ways to avoid adopting cp-ansible on the brokers**
1. **Ask Confluent for the supported manual procedure** (best; gets you a supported config).
2. **Use cp-ansible as a config renderer in a sandbox, not on client hosts.** Stand up a throwaway local or Docker 7.9.x KRaft cluster, run the USM playbook with `--check --diff` or a real run, and capture the exact properties it writes to brokers, controllers and Connect. Then apply those by hand or through the client's own config management. Never point it at client infrastructure. Supportability still needs Confluent's blessing **(inference)**.
3. **Agent on a separate host or Podman container** (`cp-usm-agent` image; the docs mention Podman for Agent 1.0.x/1.1.x on RHEL 8 but give no procedure), brokers wired by hand per option 2. CFK is not an option for this client (strictly VM-based CP, no Kubernetes), so there is no second documented toolset to fall back on.

**Also from the metrics page:** USM collects topic metadata only from **KRaft-based** clusters (this client qualifies), and it collects **connector configurations** as key-value pairs. Have the client's security team check what ends up in Connect configs before registering Connect clusters. The Connect credential masking added in 7.9.3 / 8.1.0 is on by default, but I haven't checked whether it applies to what the Agent collects **(not verified)**.

## 4. Implementation: shared steps (both lines)

Prerequisites (Confluent Cloud): `OrgAdmin` user, **Advanced Governance** package, payment method, AWS PrivateLink or Azure Private Link (no public, no GCP). Service account with `USMAgent` and `DataSteward` roles plus Schema Registry and Cloud-resource-management API keys, one service account per CP environment.

1. **Patch CP** to the target (section 5 or 6). Check the installed package version on every broker, controller and Connect node. On an unsupported CP version the Agent fails to connect without an error.
2. **Start registration** in Cloud Console, then Environment, Clusters, *Start Unified Stream Manager setup*.
3. **Private networking:** ingress PrivateLink Gateway, VPC interface endpoint (DNS name disabled, ports 80/443/9092, DNS hostnames and resolution enabled), access point, Route 53 private hosted zone with a `*` CNAME. Gateway states `CREATED`, `READY`, `EXPIRED`. Clients still need public DNS resolution of the `*.glb.confluent.cloud` name.
4. **Service account** with the roles and keys above.
5. **Generate the config JSON** (up to 20 minutes). Treat as a secret.
6. **Deploy the Agent**, then redeploy KRaft controllers, brokers and Connect so they report to it.
7. **Validate** (`validate_usm_agent_configs` tag before, `usm-agent-validz` after).
8. **Complete registration** with the Kafka cluster ID (`cluster.id` in `meta.properties`) and Connect cluster ID (`group.id` in `connect-distributed.properties`).
9. **Optional hybrid Schema Registry:** `UsmSchemaRegistryExtension`, `FORWARD` mode, importer, contexts per CP environment. RBAC and ACLs do not sync.

Agent host: minimum 2 vCPU / 2 GB RAM; HA via load balancer or VIP; ports 9901 (admin, unauthenticated, never expose), 9999, 10000, 9910 (`/stats/prometheus`). Use mTLS (not the default unauthenticated mode) between brokers/Connect and the Agent; the Agent to Cloud leg is basic auth only.

## 5. Implementation: Path A, CP 7.9.10

```yaml
# cp-ansible 7.9.10 inventory fragment. Placeholder values only.
all:
  vars:
    # Mandatory from cp-ansible 7.9.10; the playbook fails early without it.
    confluent_package_version: 7.9.10
    # The cp-ansible 7.9.x branch defaults to Agent 1.2.1 (native on RHEL 8). Pin it anyway.
    confluent_usm_agent_package_version: "1.2.1"

    ccloud_endpoint: https://api-<ap-id>.<region>.aws.accesspoint.glb.confluent.cloud:443
    ccloud_environment_id: env-xxxxx
    ccloud_credential:
      username: "{{ vault_usm_api_key }}"       # from the downloaded config JSON, kept in Ansible Vault
      password: "{{ vault_usm_api_secret }}"

    usm_agent_ssl_enabled: true                  # mTLS between CP components and the Agent
    usm_agent_ssl_mutual_auth_enabled: true
    usm_agent_basic_auth_enabled: false

usm_agent:
  hosts:
    usm-agent1.example.internal:
```

- RHEL 8 control node: Ansible 9.x (ansible-core 2.16) is the only version compatible with RHEL 8.
- Rolling patch upgrade inside 7.9.x from 7.9.4. Take the Agent from Agent 1.2.x if cp-ansible allows it on RHEL 8 (open question above); otherwise Podman on 1.0.x/1.1.x or a RHEL 9 Agent host.
- Runway: standard support ends **Feb 19, 2027**; Platinum **Feb 19, 2028**. Plan the next upgrade now.

## 6. Implementation: Path B, CP 8.1.6

```yaml
# cp-ansible 8.1.6 inventory fragment. Placeholder values only.
all:
  vars:
    confluent_package_version: 8.1.6             # mandatory from cp-ansible 8.1.6
    confluent_usm_agent_package_version: "1.2.1" # 8.1.x branch default not checked; pin explicitly
    # ccloud_* and usm_agent_* variables are the same as the 7.9.10 fragment.
```

- 7.9.x to 8.1.x is a **minor-version upgrade**. Follow the Upgrade Confluent Platform page and the Kafka 4.1 upgrade guide; I did not read either, so rolling-upgrade steps, the IBP/metadata-version sequencing and the 7.9-to-8.1 direct-path rules are **(not verified)**. The client's ZK-to-KRaft migration is already done, which removes the largest 8.x blocker.
- 8.1.0 licensing change: Confluent Enterprise Connect workers (`cp-server-connect`) fail to start without a valid license key after upgrading to 8.1.0.
- 8.1.0 MDS change: if `confluent.metadata.server.user.store=FILE`, the password file must not be world-readable and its directory must not be world-writable (unless sticky bit), or MDS will not start. cp-ansible fixes this; manual installs must correct it before upgrading.
- Connect credential masking is on by default (since 7.9.3 / 8.1.0): scripts that read connector secrets from the REST API are affected.
- Runway: Enterprise Standard to **Oct 15, 2027**, Platinum to **Oct 15, 2028**; Community ended **Oct 15, 2026** (two days from today).
- **Next hop** (8.2/8.3) needs RHEL 9+. Budget the OS upgrade into the 2027 plan either way.

## 7. Decision guide

| Situation | Choose |
|---|---|
| Needs USM fast, change window is small, Platinum contract | **7.9.10** |
| Wants standard-support runway beyond Feb 2027 without a RHEL 9 move | **8.1.6** |
| Wants dual-stack Agent networking | Neither; needs 8.2+ and RHEL 9+ |
| cp-ansible cannot deploy Agent 1.2.x on RHEL 8 | Either line, with the Agent on a RHEL 9 host or Podman |
| Not already on cp-ansible | Adopting cp-ansible is the largest piece of work on both lines; it is the only documented VM deployment path besides Confluent for Kubernetes |

## 8. Not verified

- The Upgrade Confluent Platform procedure and any 7.9-to-8.1 direct-upgrade restrictions.
- Java versions for CP 7.9 vs 8.1 (8.0 to 8.2 list Java 21 default, 17 supported on the versions page; 7.9 not checked).
- The USM Metrics and Metadata Reference (exact telemetry fields), USM troubleshooting page, and networking page.
- CONFSA advisory content and severity; third-party CVEs in bundled libraries.
- USM and Advanced Governance pricing.
- Whether the "7.9.6+" and "8.1.x" ranges in the support policy were tested against 7.9.10 and 8.1.6 specifically.

## Sources

- Versions and interoperability: https://docs.confluent.io/platform/current/installation/versions-interoperability.md
- CP 7.9.x release notes: https://docs.confluent.io/platform/7.9/release-notes/index.md
- CP 8.1 release notes: https://docs.confluent.io/platform/8.1/release-notes/index.md
- USM Agent support policy: https://docs.confluent.io/usm/current/support-policy.html
- USM Agent release notes: https://docs.confluent.io/usm/current/release-notes.html
- USM Get Started: https://docs.confluent.io/usm/current/get-started.html
- USM Sizing, HA and Monitoring: https://docs.confluent.io/usm/current/manage/sizing.html
- Confluent Ansible USM: https://docs.confluent.io/ansible/current/ansible-usm.html
- Confluent Ansible prerequisites: https://docs.confluent.io/ansible/current/ansible-requirements.html
- Confluent Ansible release notes: https://docs.confluent.io/ansible/current/ansible-release-notes.html
- Register your CP cluster: https://docs.confluent.io/cloud/current/usm/register/overview.md
- Deploy the USM Agent: https://docs.confluent.io/cloud/current/usm/register/deploy-agent.md
