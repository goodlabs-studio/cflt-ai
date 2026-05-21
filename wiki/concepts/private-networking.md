---
title: Private Networking — PrivateLink Gateway, PNI, Peering, TGW
tags: [networking, confluent-cloud, privatelink, private-service-connect, pni, peering, transit-gateway, flink, fsi]
sources: []
related: [concepts/network-connectivity-by-tier, concepts/cc-cluster-tiers, patterns/dr-cluster-linking, patterns/low-latency-kafka-azure, concepts/fsi-data-streaming-platform]
confidence: high
last_updated: 2026-05-15
last_validated: 2026-05-15
---

# Private Networking — PrivateLink Gateway, PNI, Peering, TGW

## Summary

Confluent Cloud private networking is undergoing a generational shift: the **PrivateLink Attachment (PLATT)** resource has been replaced by the **ingress PrivateLink Gateway** — AWS on **2026-02-12**, Azure and Google Cloud on **2026-05-04**. The gateway provides the same functionality as PLATT but issues **unique FQDNs per PrivateLink connection**, which lets you route VPC traffic granularly to specific services (Enterprise Kafka, Schema Registry, Flink). Existing PLATTs continue to work but no new ones can be provisioned on these dates' rollout schedules. This article covers the gateway model, the per-tier connectivity matrix, **Flink-to-Kafka internal routing** (Flink traffic never leaves Confluent Cloud), egress PrivateLink for outbound calls (external tables, S3/Blob, SaaS, AI inference), and the Azure ILB idle-timeout consideration that Private Link bypasses. For the tier-by-tier networking matrix see [Network Connectivity by Cluster Tier](network-connectivity-by-tier.md); this article is the **mechanics** layer.

## Detail

### The PLATT → PrivateLink Gateway transition

Validated against `confluent-docs` MCP (`networking/aws-platt.md`, `networking/azure-platt.md`, `networking/gcp-platt.md`, `flink/concepts/flink-private-networking.md`) on 2026-05-15.

| Cloud | PLATT → Gateway cutover | What replaces it |
|---|---|---|
| AWS | **2026-02-12** | Ingress PrivateLink Gateway (`AwsIngressPrivateLinkGatewaySpec`) |
| Azure | **2026-05-04** | Ingress PrivateLink Gateway (`AzureIngressPrivateLinkGatewaySpec`) |
| Google Cloud | **2026-05-04** | Ingress PrivateLink Gateway (`GcpIngressPrivateServiceConnectGatewaySpec`) |

Existing PLATT resources keep working. **No new PLATTs can be provisioned** following a future release after the cutover dates. **Update FSI Terraform modules** to the `confluent_gateway` resource — the v2 governance module ships gateway-by-default.

Why the gateway model matters operationally:
- **Per-connection FQDNs** — each access point gets its own DNS subdomain (`$lkc-id.$accesspointId.$region.$cloud.accesspoint.confluent.cloud`). Routing rules in your VPC can target specific Confluent services without all-or-nothing.
- **Reuse across services** — a single gateway in a region covers Enterprise Kafka, Schema Registry, **and Flink** in that region/environment. For Flink, the same gateway used by Enterprise clusters is reused (Dedicated clusters require a **separate** gateway in the same region — see Flink-to-Kafka below).
- **Up to 10 endpoints per gateway** on AWS (VPC interface endpoints), Azure (private endpoints), and GCP (PSC endpoints).

### Three-resource model (Gateway + Access Point + DNS)

Every PrivateLink Gateway deployment is the same three-step shape regardless of cloud:

1. **Ingress PrivateLink Gateway** — Confluent-side reservation. Provisioned in `CREATED` state; transitions to `READY` after an Access Point is created and accepted; goes `EXPIRED` if no valid access point is provisioned in the allotted time.
2. **VPC/VNet endpoint** — created on the cloud-provider side, associated with the gateway's **PrivateLink Service ID** (AWS) / **Private Link Service ID or Alias** (Azure) / **Service Attachment URI** (GCP).
3. **Ingress PrivateLink Access Point** — Confluent-side registration of the cloud endpoint, binding it to the gateway.

Then **DNS**: two-step CNAME resolution. The Confluent Cloud Global DNS Resolver returns a CNAME stripping the `glb` subdomain (`$lkc-id-$accesspointId.$region.$cloud.accesspoint.glb.confluent.cloud` → `$lkc-id.$accesspointId.$region.$cloud.accesspoint.confluent.cloud`), and your private DNS resolver (Route53 / Azure Private DNS Zone / Cloud DNS) maps that CNAME to your VPC endpoint with a wildcard `*` record.

> Kafka broker names returned in metadata are **not static** — do not hardcode them in DNS records. Always wildcard the access-point zone.

Terraform skeleton (AWS shown — Azure/GCP differ only in the inner block):

```terraform
resource "confluent_gateway" "aws_ingress" {
  display_name = "fsi-prod-us-east-1"
  environment { id = "env-123abc" }
  aws_ingress_private_link_gateway { region = "us-east-1" }
}

resource "confluent_access_point" "aws_ingress_1" {
  display_name = "fsi-vpc-endpoint"
  environment  { id = "env-123abc" }
  gateway      { id = confluent_gateway.aws_ingress.id }
  aws_ingress_private_link_endpoint {
    vpc_endpoint_id = "vpce-1234567890abcdef0"   # created in your AWS account
  }
  depends_on = [confluent_gateway.aws_ingress]
}
```

CLI form: `confluent network gateway create <name> --cloud aws --region us-east-1 --type ingress-privatelink`.

### Cluster-tier requirements

The gateway is for **serverless products** — Enterprise Kafka, Schema Registry, and Flink. Tier-by-tier:

| Cluster | Private connectivity options |
|---|---|
| **Basic / Standard** | Public only |
| **Enterprise** | **AWS**: PrivateLink (Gateway) + PNI. **Azure**: Private Link (Gateway). **GCP**: Private Service Connect (Gateway). No peering, no Transit Gateway. |
| **Dedicated** | AWS: VPC Peering, TGW, PrivateLink (Dedicated — separate from Gateway), PNI for Connect. Azure: VNet Peering, Private Link. GCP: VPC Peering, PSC. |
| **Freight (AWS only)** | PNI only — no PrivateLink, no peering, no TGW |

Cross-cuts:
- **PNI on AWS** raises Enterprise from 10 eCKU PrivateLink cap to 32 eCKU. Required above 10 eCKU on AWS Enterprise.
- **Cluster Linking from Enterprise** to an external cluster uses **egress PrivateLink (Serverless)** on AWS — not the ingress gateway. CC↔CC over private is straightforward; **CC↔CP needs the CP side mutually reachable**.

### Flink-to-Kafka — traffic stays internal

This is the operational subtlety that catches teams: **Flink-to-Kafka traffic routes internally within Confluent Cloud**. The PrivateLink Gateway for Flink only handles the **client→Flink** path — submitting statements, fetching results, Cloud Console, CLI, Terraform, REST API. The Flink compute pool reaches the Kafka cluster over Confluent's internal fabric.

Implications:
- **For Enterprise clusters**: reuse the **same gateway** used for Enterprise Kafka. One gateway, multiple services.
- **For Dedicated clusters**: you **still need a gateway in the same region**, *even if* a Private Link already exists for the Dedicated cluster. The Dedicated cluster's PrivateLink is a separate resource and does not cover Flink's client-side endpoint.
- **A single gateway** enables Flink statements created in that environment/region to access any Flink cluster in the same region, regardless of environment — RBAC governs access.
- **Cluster links and Flink statements** can move data between all private networks in the organization, including CCNs associated with Dedicated Kafka clusters, **through the gateway fabric**.

Flink endpoints with private DNS:
- Enterprise (Gateway): `flink.$region.$cloud.private.confluent.cloud` and `flinkpls.$region.$cloud.private.confluent.cloud` (language service for autocomplete in the SQL shell).
- Dedicated: `flink.dom$id.$region.$cloud.private.confluent.cloud` / `flinkpls.dom$id.$region.$cloud.private.confluent.cloud`.

Don't forget the `flinkpls` endpoint — its absence breaks autocomplete in the Flink SQL shell with no clear error.

### Egress PrivateLink — external services from CC

Confluent Cloud for Apache Flink supports **outbound PrivateLink** on **AWS and Azure** (not GCP) via Egress PrivateLink endpoints. These are:
- AWS Interface VPC Endpoints
- Azure Private Endpoints

Use cases (validated 2026-05-15):
- **AI external tables** — model inference against Bedrock, OpenAI, Azure OpenAI, etc.
- **Cloud storage** — S3, Azure Blob Storage (e.g., Iceberg external tables, Tableflow targets).
- **SaaS services** — any service exposed as an AWS PrivateLink service or Azure Private Link service.
- **Your own services** — internal PrivateLink services you publish.

These endpoints attach to your Confluent Cloud environment and let CC-side workloads reach **your or third-party** private services without traversing public internet. **Not the same** as static egress IPs (which are public IPs used by fully-managed connectors for sources without PrivateLink support).

### Azure ILB idle-timeout and Private Link

Azure Internal Load Balancers (used in front of self-managed Kafka on AKS and in some CC Azure paths) have a TCP idle-timeout (default 4 minutes, max 30 minutes) that silently drops idle connections — clients see `Disconnected during request` style errors and reconnect storms, which look like rebalance events but aren't.

**Azure Private Link bypasses the ILB** for the CC Azure path: the private endpoint connects to the PrivateLink service directly, no ILB in the data path, no idle-timeout class of failure. This is one of the operational reasons Azure FSI deployments default to Private Link on Enterprise rather than public-with-allowlisting. For self-managed AKS Kafka, see the connection-management overlay in [Low-Latency Kafka Clients on Azure](../patterns/low-latency-kafka-azure.md) — different mitigation (TCP keepalive shorter than ILB timeout, periodic metadata refresh).

> ⚠️ unverified — exact Azure ILB idle-timeout defaults and their interaction with the Confluent Cloud Azure fabric vary by SKU and were not re-validated against current Azure docs in this session. The architectural claim (Private Link path does not traverse the ILB) is sound; specific timeout values should be confirmed against current Azure ILB docs if used in a customer-facing recommendation.

### FSI defaults

- **Enterprise + ingress PrivateLink Gateway** is the FSI baseline for new production CC clusters in 2026. Smaller surface area than Dedicated, no peering complexity, gateway covers SR + Flink.
- **One gateway per environment per region.** Up to 10 endpoints; if you outgrow 10, split environments rather than gateways.
- **Terraform-first.** Provision the gateway, access point, and DNS via `confluent_gateway` + `confluent_access_point` + `aws_vpc_endpoint` / `azurerm_private_endpoint` / `google_compute_forwarding_rule`. The fsi-dsp v2 module bundles this.
- **No PLATT in new code.** Existing PLATTs are tolerated; new modules emit gateway resources only.
- **Egress PrivateLink** for any Flink external table / AI inference / cloud-storage call where the alternative is a public route. For FSI compliance, public egress from CC for data plane is a documented exception, not a default.

## Related

- [Network Connectivity by Cluster Tier](network-connectivity-by-tier.md) — tier/connectivity matrix; this article is the deep dive on the gateway mechanics
- [Confluent Cloud Cluster Tiers](cc-cluster-tiers.md) — Basic/Standard/Enterprise/Dedicated/Freight tier definitions
- [DR — Cluster Linking](../patterns/dr-cluster-linking.md) — CL over private (CC↔CC) and CC↔CP reachability planning
- [Low-Latency Kafka Clients on Azure](../patterns/low-latency-kafka-azure.md) — Azure ILB-aware connection management for self-managed paths
- [FSI Data Streaming Platform](fsi-data-streaming-platform.md) — six deployment models and where private networking applies
