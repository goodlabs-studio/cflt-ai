---
id: scenario-cfk-openshift-013
request: "deploy Confluent for Kubernetes on OpenShift"
expected_artifact: "scenario/cfk-openshift"
floor_model: sonnet
tags: [scenario, kubernetes, openshift]
required_claims:
  - "scenario/cfk-openshift"
forbidden_claims:
  - 'resource "confluent_'
negative_space: false
---

## Case: Confluent for Kubernetes on OpenShift

**What the answer MUST contain:**
- Reference to the scenario/cfk-openshift fsi-dsp scenario
- CFK on OpenShift context (OCP 4.x with operator lifecycle management)

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks

**Negative-space trigger:** NO

**MANIFEST link:** fsi-dsp://scenario/cfk-openshift — "Confluent for Kubernetes on OpenShift starter kit"
