---
title: Auditor-Readonly RBAC Payload Isolation
tags: [rbac, mds, audit, fsi, linuxone, compliance, ldap, sox, ffiec, pci-dss]
sources:
  - fsi-dsp://accelerator/confluent-on-linuxone
related:
  - patterns/fsi-canon-overlay-for-confluent-skills
  - concepts/fsi-compliance
  - patterns/linuxone-on-cfk-reference-architecture
  - patterns/topic-naming
  - concepts/fips-at-install-ocp-requirement
confidence: high
last_updated: 2026-05-23
last_validated: 2026-05-23
---

# Auditor-Readonly RBAC Payload Isolation

## Summary

The canonical FSI pattern for binding an `auditor-readonly` role that has access
to audit metadata **without** access to business payloads. **DeveloperRead is
consume-granting at the topic-prefix scope it's bound to** — this is the
load-bearing fact that makes naive auditor RBAC fail compliance. True auditor
payload isolation requires **topic-scoped binding to `confluent-audit-log-events` +
SR subjects ONLY**, **explicitly NOT to `payments.*` business topics**.

Source of truth: `fsi-dsp://accelerator/confluent-on-linuxone` (layer 01 —
`apply_sequence` `01-rbac`) — DESIGN.md "Decisions locked" #2 (D-02) and
DESIGN.md L108–124 (layer-01 detail block).

## The six FSI roles (layer 01)

Layer 01 of the LinuxONE accelerator deploys six `ConfluentRolebinding` CRs that
map FSI-named roles to Confluent's predefined roles:

| FSI role | Confluent role | Scope |
|----------|----------------|-------|
| `platform-admin` | `SystemAdmin` | cluster |
| `topic-admin` | `ResourceOwner` | Topic `PREFIXED` (per domain) |
| `producer-only` | `DeveloperWrite` | Topic `PREFIXED` (per app) |
| `consumer-only` | `DeveloperRead` | Topic + Group `PREFIXED` (per app) |
| `schema-admin` | `ResourceOwner` | Subject `PREFIXED` (`schemaRegistryClusterId` scope) |
| `auditor-readonly` | `DeveloperRead` | **`confluent-audit-log-events` + SR subjects ONLY** |

All bindings target **LDAP groups** (`type: group`), never individuals — the IdP
is the identity boundary.

## DESIGN.md D-02 — verbatim

From `fsi-dsp://accelerator/confluent-on-linuxone` DESIGN.md "Decisions locked"
#2:

> `auditor-readonly` = audit-topic-scoped. Bound to `DeveloperRead` on
> `confluent-audit-log-events` + all SR subjects (metadata) + read-scoped
> cluster metadata. Explicitly **not** bound to `payments.*` business topics —
> true payload isolation, since Confluent `DeveloperRead` always grants consume.

This decision is the canonical correction for the most common auditor-RBAC
mistake: granting `DeveloperRead` at the cluster scope or at a broad PREFIXED
scope and assuming "read-only" means the auditor can't see business payloads.

## Why cluster-scoped DeveloperRead fails

**DeveloperRead is consume-granting at the topic-prefix scope it's bound to.**

A cluster-scoped binding:
```yaml
apiVersion: platform.confluent.io/v1beta1
kind: ConfluentRolebinding
metadata:
  name: auditor-readonly-WRONG
spec:
  principal:
    type: group
    name: kafka-auditor-group
  role: DeveloperRead
  resourcePatterns:
    - resourceType: Cluster
      name: "*"
      patternType: LITERAL
```

…grants the auditor LDAP group **consume access to every topic on the cluster**.
This includes `payments.transactions.v1.account-transaction` and every other
business topic — the auditor can pull customer transaction data, account
numbers, dollar amounts. That's a clean compliance finding: the auditor role
must not have access to business payload.

A PREFIXED binding on `*` or on the cluster scope has the same effect.

## The correct pattern — topic-scoped DeveloperRead

```yaml
apiVersion: platform.confluent.io/v1beta1
kind: ConfluentRolebinding
metadata:
  name: auditor-readonly-audit-topic
spec:
  principal:
    type: group
    name: kafka-auditor-group
  role: DeveloperRead
  resourcePatterns:
    - resourceType: Topic
      name: confluent-audit-log-events
      patternType: LITERAL
---
apiVersion: platform.confluent.io/v1beta1
kind: ConfluentRolebinding
metadata:
  name: auditor-readonly-sr-subjects
spec:
  principal:
    type: group
    name: kafka-auditor-group
  role: DeveloperRead
  resourcePatterns:
    - resourceType: Subject
      name: ""           # all SR subjects (metadata only — schemas, not payloads)
      patternType: PREFIXED
  clustersScope:
    schemaRegistryClusterId: <SR_CLUSTER_ID>
```

Two LITERAL/PREFIXED bindings on **specific** resources. The auditor sees:
- The audit topic itself (every authn/authz/management event)
- The schema metadata (every subject's schemas and versions)
- Cluster-level metadata (broker list, topic list, etc. via read-scoped roles)

The auditor does **not** see:
- `payments.*` business topics
- Customer transaction payloads
- Any topic not explicitly enumerated

## Validation

```bash
# 1. Confirm the bindings exist
confluent iam rbac role-binding list \
  --principal Group:kafka-auditor-group \
  --kafka-cluster-id <CLUSTER_ID>

# 2. Confirm the auditor CAN consume the audit topic
confluent kafka topic consume confluent-audit-log-events \
  --bootstrap <BOOTSTRAP> --from-beginning --timeout-ms 5000 \
  | head -5   # expect events

# 3. Confirm the auditor CANNOT consume a business topic — must 403
confluent kafka topic consume payments.transactions.v1.account-transaction \
  --bootstrap <BOOTSTRAP> --from-beginning --timeout-ms 5000
# Expected: AuthorizationException / 403
```

The `validate-rbac.sh` in `layers/01-rbac/` automates these three checks and
exits non-zero on any compliance violation.

## FSI regulatory framing

- **SOX** — least-privilege over financial reporting data; auditors must not
  read source-of-record financial topics
- **FFIEC** — segregation of duties between auditor and operator roles
- **PCI-DSS §7** — restrict access to cardholder data by business need-to-know;
  audit metadata is need-to-know, cardholder data is not
- **GLBA Safeguards Rule** — restrict access to nonpublic personal information;
  auditor reviewing audit trail is not reviewing customer NPI

The pattern's value is structural: by enumerating the resources the auditor
needs by literal/prefixed name, you make payload-access an explicit grant rather
than a side-effect of a broader role. A reviewer reading the rolebindings can
see immediately that the auditor cannot consume customer data.

## Common misuse patterns to flag

| Anti-pattern | Why it fails |
|--------------|--------------|
| `DeveloperRead` on the cluster scope | grants consume on every topic |
| `DeveloperRead` with PREFIXED `""` (empty prefix) | matches every topic name |
| "Audit role" = `SystemAdmin` (or other admin role) downgraded "just for reads" | DeveloperRead is read but not read-only of the metadata sense an auditor needs |
| Binding `auditor-readonly` to individual principals | violates the LDAP-group-as-IdP-boundary rule |

When reviewing FSI Kafka RBAC, look for any of these and replace with the
topic-scoped pattern above.

## Cross-references

- DESIGN.md L37–41 (D-02 verbatim — committed design record)
- DESIGN.md L108–124 (layer-01 detail — 6 FSI roles, auditor-readonly binding)
- `patterns/fsi-canon-overlay-for-confluent-skills` — RBAC overlay row for upstream skills
- `concepts/fsi-compliance` — SOX/FFIEC/PCI-DSS framing
- `patterns/topic-naming` — how PREFIXED bindings interact with the domain naming convention

## Related

- `patterns/fsi-canon-overlay-for-confluent-skills`
- `concepts/fsi-compliance`
- `patterns/linuxone-on-cfk-reference-architecture`

## Provenance

- DESIGN.md L37–41 (Decisions locked #2 — D-02, committed design record)
- DESIGN.md L108–124 (layer 01 detail — 6 FSI roles, auditor-readonly binding)
- `layers/01-rbac/README.md` (FSI rationale, validation procedure)
