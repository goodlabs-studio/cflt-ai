---
id: role-dr-mirrormaker-011
request: "configure MirrorMaker 2 for cross-DC replication"
expected_artifact: "role/cp_dr_mm2"
floor_model: sonnet
tags: [dr, ansible, mirrormaker]
required_claims:
  - "role/cp_dr_mm2"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: MirrorMaker 2 cross-DC replication via Ansible

**What the answer MUST contain:**
- Reference to the role/cp_dr_mm2 fsi-dsp Ansible role
- Cross-DC replication context (MirrorMaker 2 on Confluent Platform)

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks

**Negative-space trigger:** NO

**Note:** Cluster Linking is preferred for Confluent-to-Confluent topologies; MirrorMaker 2 applies when one endpoint is non-Confluent or on-prem CP.

**MANIFEST link:** fsi-dsp://role/cp_dr_mm2 — "Configure MirrorMaker 2 for cross-cluster replication"
