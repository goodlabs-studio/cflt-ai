---
title: Unified Stream Manager (USM) Enablement for Self-Managed CP on RHEL 8
tags: [usm, unified-stream-manager, confluent-platform, confluent-cloud, rhel8, ansible, privatelink, schema-registry, governance, upgrade, fsi]
related: [patterns/schema-linking-cp-to-cc-mtls, patterns/cp-mtls-self-signed-setup, patterns/schema-registry-manual-install-permissions, concepts/confluent-on-s390x-support-and-ifl-sizing]
confidence: medium
last_updated: 2026-10-13
last_validated: 2026-10-13
---

# Unified Stream Manager (USM) Enablement for Self-Managed CP on RHEL 8

## Summary

**Read the Fit check below first.** USM needs a Confluent Cloud org, Advanced Governance and AWS/Azure private networking. A client running only self-managed CP has to adopt Cloud to use it, so confirm that is acceptable before spending effort on the upgrade.

USM makes Confluent Cloud the **control plane** (monitoring, governance, global Schema Registry, lineage, catalog) for a self-managed Confluent Platform (CP) cluster that stays the **data plane**. A **USM Agent** (Envoy-based proxy) in the CP environment forwards metrics and metadata to Confluent Cloud over **AWS PrivateLink or Azure Private Link**. Message data never leaves CP, and Cloud cannot send management commands back.

For a CP 7.9.x / RHEL 8 estate there are two valid paths:

| Path | CP version | USM Agent | Standard support ends | Notes |
|---|---|---|---|---|
| **A. Patch only** | **Target 7.9.10** (7.9.6 is only the USM floor; 7.9.7 is the minimum I would accept) | 1.0.0 to 1.2.x | **Feb 19, 2027** (Platinum Feb 19, 2028) | Smallest change; runway is short |
| **B. Upgrade (recommended if staying >Feb 2027)** | **8.1.x** | 1.2.0 on RHEL 8 | Oct 15, 2027 (Platinum Oct 15, 2028) | Only 8.x release supporting both RHEL 8 and USM |

Hard constraints: CP 8.0.x is **not** supported by USM; CP 8.2 and 8.3 do **not** support RHEL 8; USM requires private networking (no public, no GCP).

## Why 7.9.10 and not 7.9.6 (7.9.x release notes)

USM accepts 7.9.6+, but fixes shipped after 7.9.6:
- **7.9.7:** security fixes for the JSON Schema serializer (CONFSA-2026-06) and ksqlDB (CONFSA-2026-03/04/05), and a **deadlock fix in a broker-side telemetry component used by USM**.
- **7.9.9:** opt-in DoS hardening (`confluent.bounded.request.max.bytes`, `transaction.id.max.length`, `max.decompressed.message.bytes`) and Cluster Linking OAuth URL validation (default off).
- **7.9.3:** Connect REST API masks credentials by default (affects scripts that read connector secrets).

Advisories sit on the Confluent support portal; read them for severity before the client's change review. No third-party CVE list was reviewed, so have the client scan installed packages.

Agent versions: 1.2.1 (Aug 24, 2026) is a security and maintenance patch on 1.2.x. Each Agent minor gets at most two patches, so plan Agent upgrades.

## Fit check: USM is not a CP-only feature

USM requires a **Confluent Cloud organization** as the control plane. A client that is entirely self-managed CP with no cloud presence must add all of the following before USM works:

- A Confluent Cloud org (`OrgAdmin`, payment method) and the **Advanced Governance** package.
- An AWS or Azure account and VPC for PrivateLink / Private Link (public networking is unsupported), reachable from the agent hosts over Direct Connect or VPN (inference, not stated in the docs).
- Approval for cluster health metrics, topic states, connector configs and schema metadata to leave the perimeter. Message data stays on-prem.
- Acceptance of Cloud as schema authority if the hybrid Schema Registry is used.

Ask what the client actually wants (single-pane monitoring, central governance, or a staged CC migration). If monitoring is the goal and there is no cloud footprint, Control Center on CP 8.x is the lower-friction option. That comparison is not feature-by-feature verified here.

## Version and OS facts (confluent-docs, versions-interoperability page)

- USM Agent compatibility: 1.2.0 → CP 7.9.6+, 8.1.x, 8.2.x, 8.3.x; 1.1.0 → 7.9.6+, 8.1.x, 8.2.x; 1.0.0 → 7.9.6+, 8.1.x.
- Agent standard support: two years from the `.0` release (1.2.0 released June 19, 2026 → June 19, 2028). No Platinum tier for the agent. Patches limited to two quarterly releases in the first six months, so plan to take minor upgrades.
- CP OS matrix: RHEL 8.x is supported on CP 8.0 and 8.1 and on all 7.x, **not** 8.2/8.3. RHEL 9 is supported everywhere.
- Agent on RHEL 8: native install needs **Agent 1.2.0+**. Agent 1.0.x/1.1.x are not compatible with RHEL 8; run those as a **Podman container** instead.
- Agent host sizing (Ansible/VM): minimum 2 vCPU, 2 GB RAM. Tested: 5 clusters / 105 brokers / ~1.17M partitions per cluster stayed within 300m CPU / 256Mi.
- 7.9.x lifecycle: EOS Feb 19, 2027 for Community and Standard, Feb 19, 2028 for Platinum.

## Doc conflict to resolve before telling the client "RHEL 8 is fine"

The Ansible USM page (`ansible-usm.html`) says "Unified Stream Manager Agent cannot be deployed on RHEL 8. You must deploy to RHEL 9 or later" and lists CP 8.1.x+ / Ansible 8.1.x+ as the prerequisites. The versions page, USM Get Started page and USM Sizing page all say RHEL 8 works with Agent 1.2.0+ (native) or via Podman (1.0.x/1.1.x), and the matrix lists CP 7.9.6+ as supported.

The cp-ansible prerequisites page adds to the conflict. Its USM compatibility matrix lists **Confluent Ansible 7.9.x, 8.1.x, 8.2.x and 8.3.x all supporting USM Agent 1.0.x to 1.1.x only**. Agent 1.2.0 (the first with native RHEL 8) is not listed, even though the same Ansible release notes mention Agent 1.3.0 packages. That suggests the matrix is lagging (inference). Read literally, the matrix only covers Agent 1.0.x/1.1.x, which are not native on RHEL 8, and no page says whether cp-ansible drives the Podman route.

What is now answered (cp-ansible prerequisites, Sep 24, 2026):
- cp-ansible 7.9.x **does** list USM Agent 1.0.x to 1.1.x, and cp-ansible 7.9.10 exists (it is named in the `confluent_package_version` note). So Path A is not blocked on tooling for those agent versions. The Ansible USM page's "8.1.x and later" line contradicts this and looks stale (inference).
- RHEL 8 requires Ansible 9.x (ansible-core 2.16).
- `confluent_package_version` is mandatory from Confluent Ansible 7.9.10 onward (also 7.6.14, 7.7.12, 7.8.11, 8.0.8, 8.1.6, 8.2.4, 8.3.2, 8.4.0). Playbooks fail early without it, so set it explicitly in the inventory.

Still open, **confirm with Confluent Support/SE** before committing:
1. Whether cp-ansible can deploy Agent 1.2.x natively on RHEL 8, or only 1.0.x/1.1.x via Podman.
2. If not, fall back to a RHEL 9 Agent host. The brokers do not have to be RHEL 9.

If either answer is unfavorable, a RHEL 9 Agent host is fine: the Agent is a separate proxy host, and the brokers do not have to be RHEL 9.

## Prerequisites checklist

**Confluent Cloud**
- User doing setup holds `OrgAdmin`.
- **Advanced Governance** Stream Governance package on the environment (Essentials must be upgraded).
- Payment method configured.
- Private networking: AWS ingress **PrivateLink Gateway + Access Point** (replaces PLATT as of June 2026) or Azure Private Link. Not GCP, not public.

**Network (on-prem side)**
- VPC interface endpoint to the gateway's service name, ports 80/443/9092 open from the source CIDR, DNS hostnames and resolution enabled on the VPC, **Enable DNS name unchecked** on the endpoint.
- Route 53 private hosted zone for the access-point domain (strip `api-` and `.glb` from the FrontDoor URL) with a `*` CNAME to the VPC endpoint DNS name.
- Clients must still resolve the public `*.glb.confluent.cloud` name (it CNAMEs into your private zone).
- Inference, not stated in the docs: an on-prem Agent must reach that VPC endpoint over Direct Connect or VPN. Confirm routing and DNS forwarding from the Agent hosts.
- Agent supports IPv4 and dual-stack (dual-stack needs Agent 1.1.0+ and CP 8.2+). IPv6-only is unsupported.

**Service account** (one per logically separate CP environment, for example Dev vs Prod)
- Roles: `USMAgent` and `DataSteward`.
- API keys: one with **Schema Registry** scope, one with **Cloud resource management** scope.
- Existing accounts missing the roles or keys cause registration to fail.

## Enablement steps

1. **Confirm versions.** CP 7.9.6+ or 8.1.0+. On an unsupported version the Agent fails to connect without reporting an error. Check the installed CP package version on every broker, controller and Connect node.
2. **Upgrade CP** (Path A: patch to 7.9.6+; Path B: 8.1.x). The ZK→KRaft migration is already done for this client, so there is no metadata-mode blocker for 8.x.
3. **Start registration** in Cloud Console → Environment → Clusters → *Start Unified Stream Manager setup*. Choose new or existing agent.
4. **Build private networking** (gateway → VPC endpoint → access point → DNS). Gateway states: `CREATED` → `READY`; `EXPIRED` if no valid access point in time.
5. **Create or select the service account** with the roles and keys above.
6. **Generate and download the config JSON** (can take up to 20 minutes). Fields: `ENVIRONMENT_ID`, `SERVICE_ACCOUNT_API_KEY/SECRET`, `SCHEMA_REGISTRY_API_KEY/SECRET`, `FRONTDOOR_URL`, `SCHEMA_REGISTRY_URL`. Treat it as a secret; keep it in Vault or Ansible Vault.
7. **Deploy the Agent with cp-ansible** (inventory sketch below), and **redeploy KRaft controllers, brokers and Connect** so they send telemetry to the Agent. Use the `--tags` run so the Agent starts first.
8. **Validate**: `ansible-playbook -i hosts.yml confluent.platform.all --tags=validate_usm_agent_configs` before deploy, then `usm-agent-validz` on the Agent host after.
9. **Complete registration** in the wizard: Kafka cluster ID from `/var/lib/kafka/data/meta.properties` (`cluster.id`), Connect cluster ID from `group.id` in `connect-distributed.properties`.
10. **Optional: hybrid Schema Registry** (below). Do this last, after the cluster shows up in Cloud.

### cp-ansible inventory sketch

```yaml
# Placeholder values only. Real credentials come from the downloaded USM config file.
usm_agent:
  hosts:
    usm-agent1.example.internal:

all:
  vars:
    # cp-ansible 7.9.x branch defaults to Agent 1.2.1 (native on RHEL 8); pin explicitly.
    # Raw broker/Connect/Agent property names are in patterns/usm-support-matrix-cp-7-9-vs-8-1.md (section 3b).
    confluent_usm_agent_package_version: "1.2.1"

    ccloud_endpoint: https://api-<ap-id>.<region>.aws.accesspoint.glb.confluent.cloud:443   # FRONTDOOR_URL + port
    ccloud_environment_id: env-xxxxx
    ccloud_credential:
      username: <SERVICE_ACCOUNT_API_KEY>
      password: <SERVICE_ACCOUNT_API_SECRET>

    # Broker/Connect -> Agent leg. Basic auth OR mTLS, never both. Default is unauthenticated.
    # Agent -> Confluent Cloud leg supports basic auth only.
    usm_agent_ssl_enabled: true
    usm_agent_ssl_mutual_auth_enabled: true     # mTLS for FSI; set basic_auth false
    usm_agent_basic_auth_enabled: false

    usm_agent_health_check_enabled: true
    usm_client_metrics_enabled: false           # KIP-714 client metrics; opt in deliberately
```

```bash
ansible-playbook -i hosts.yml confluent.platform.all --tags=validate_usm_agent_configs
ansible-playbook -i hosts.yml confluent.platform.all \
  --tags=usm_agent,kafka_controller,kafka_broker,kafka_connect
```

The host running the Agent must be reachable **only** by the CP components that send it data. Ports: admin 9901 (unauthenticated, never expose or scrape), controlplane 9999, dataplane 10000, monitoring 9910 (`/stats/prometheus`).

## High availability and sizing

- Add a second Agent only for HA; otherwise one larger Agent is more resource-efficient.
- VM HA: HTTP load balancer with health checks across two or more Agents, or an active-passive virtual IP.
- Logs: `/var/log/confluent/usm-agent/usm-agent_application.log`, `usm-agent_access.log`, and `tap/` for traffic logs. Default logrotate: 5 files of 10 MB.
- Scrape port 9910 with Prometheus; Grafana dashboard 23239 (Envoy) is the one the docs reference.

## Hybrid Schema Registry (optional, but it is the governance payoff)

Cloud SR becomes primary. CP SR is set to `FORWARD` mode and acts as a read cache, with an importer pulling updates. Important properties:

- CP SR `resource.extension.class=io.confluent.schema.registry.usm.UsmSchemaRegistryExtension` plus `usm.schema.registry.remote.endpoint` (private endpoint), `.api.key`, `.api.secret`, optional `.context.prefix`. Append to any existing extension list.
- Prerequisite: CP SR global mode is `READWRITE` with **no subject or context-level overrides**.
- Choose scenario 1 (mirror, exact replica; Cloud SR must be empty or already identical to avoid ID collisions) or scenario 2 (one **context per CP environment**, the right default for multi-cluster estates).
- Run a one-time exporter, then pause and delete it before creating the long-running importer. Run `schema-compatibility-check` first if Cloud already has schemas.
- **RBAC and ACLs are not synchronized** between CP and Cloud. A schema write is authorized twice (CP, then Cloud). Plan separate permissions and expect separate audit logs.
- DR: secondary CP SRs run in `FORWARD` mode with importers pulling from Cloud. If Cloud is down, promote the primary CP SR to `READWRITE` and export to secondaries.

## FSI and security considerations

- Agent → Cloud authentication is basic (API key) only, so credential hygiene is on you. One service account per environment, secrets in a vault, rotation planned.
- Use mTLS on the broker/Connect → Agent leg; do not leave the default unauthenticated mode.
- Telemetry includes cluster health, topic states, connector configurations and schema metadata. Review the Metrics and Metadata Reference with the client's security team before approving (connector configs can embed hostnames).
- Cloud being the governance control plane means a Cloud-side outage affects schema writes (not reads) unless the DR runbook above is rehearsed.
- No client infrastructure was contacted in producing this article. All validation is from documentation only.

## Not verified

- Whether cp-ansible deploys Agent 1.2.x natively on RHEL 8 (see conflict above).
- Whether the Agent accepts 7.9.10 specifically. The matrix says "7.9.6+", which covers it, but no page names 7.9.10.
- Agent-to-Cloud egress path from an on-prem data center (Direct Connect or VPN specifics).
- USM pricing. Not covered by the fetched docs; Advanced Governance has its own cost.
- Pages not read: USM release notes, support policy, troubleshooting, monitoring and `networking.html`.

## Sources

- Versions and interoperability: https://docs.confluent.io/platform/current/installation/versions-interoperability.md
- USM in Confluent Platform (overview): https://docs.confluent.io/usm/current/overview.html
- USM Get Started: https://docs.confluent.io/usm/current/get-started.html
- USM Sizing, HA and Monitoring: https://docs.confluent.io/usm/current/manage/sizing.html
- USM Schema Registry hybrid setup: https://docs.confluent.io/usm/current/configure/usm-schema.html
- Confluent Ansible USM: https://docs.confluent.io/ansible/current/ansible-usm.html
- USM in Confluent Cloud: https://docs.confluent.io/cloud/current/usm/overview.md
- Register your CP cluster: https://docs.confluent.io/cloud/current/usm/register/overview.md
- AWS private networking for USM: https://docs.confluent.io/cloud/current/usm/register/usm-network.md
- Service account for the USM Agent: https://docs.confluent.io/cloud/current/usm/register/usm-service-account.md
- Deploy the USM Agent: https://docs.confluent.io/cloud/current/usm/register/deploy-agent.md
