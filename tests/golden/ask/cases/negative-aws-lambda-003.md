---
id: negative-aws-lambda-003
query: "What is the best way to deploy a REST API using AWS Lambda?"
expected_route: refuse
floor_model: haiku
tags: [negative-space, out-of-domain, aws]
required_claims:
  - "not within"
forbidden_claims:
  - "Lambda"
  - "API Gateway"
  - "serverless"
---

## Case: Out-of-domain refusal — AWS Lambda REST API

**What the answer MUST contain:**
- Statement that AWS Lambda deployment is not within the Confluent domain

**What the answer MUST NOT contain:**
- Any serverless or Lambda deployment guidance

**Negative-space trigger:** YES — AWS Lambda REST API deployment is out of domain.
