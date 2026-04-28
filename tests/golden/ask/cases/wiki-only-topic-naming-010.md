---
id: wiki-only-topic-naming-010
query: "What is the recommended topic naming convention?"
expected_route: wiki-only
floor_model: haiku
tags: [kafka, naming, governance]
required_claims:
  - "domain"
  - "entity"
  - "event"
forbidden_claims:
  - "no standard"
---

## Case: Topic naming convention

**What the answer MUST contain:**
- The domain.entity.event pattern (or domain.application.version.entity variant)
- Dot separator convention

**What the answer MUST NOT contain:**
- Claims that no standard exists

**Negative-space trigger:** NO
