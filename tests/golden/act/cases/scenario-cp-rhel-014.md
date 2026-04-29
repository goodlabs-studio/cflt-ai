---
id: scenario-cp-rhel-014
request: "set up Confluent Platform on RHEL bare metal"
expected_artifact: "scenario/cp-rhel"
floor_model: haiku
tags: [scenario, rhel, on-prem]
required_claims:
  - "scenario/cp-rhel"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: Confluent Platform on RHEL bare metal

**What the answer MUST contain:**
- Reference to the scenario/cp-rhel fsi-dsp scenario
- On-premises RHEL deployment context

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks (scenario artifact, not hand-rolled)

**Negative-space trigger:** NO

**MANIFEST link:** fsi-dsp://scenario/cp-rhel — "Confluent Platform on RHEL starter kit"
