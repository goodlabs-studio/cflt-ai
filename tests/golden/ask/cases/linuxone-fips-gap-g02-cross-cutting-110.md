---
id: linuxone-fips-gap-g02-cross-cutting-110
query: "Why is FIPS-at-install required for the LinuxONE accelerator's TLS layer?"
expected_route: wiki+mcp
floor_model: haiku
tags: [fips, ocp, linuxone, gap-g02, trip-wire, cross-cutting, wiki-05]
required_claims:
  - "G-02"
  - "fips-at-install-ocp-requirement"
  - "install-config.yaml"
forbidden_claims:
  - "I cannot help"
  - "no information"
---

## Case: FIPS-at-install gap G-02 — cross-cutting (WIKI-05)

**What the answer MUST contain:**
- Reference to KNOWN-GAPS G-02 trip-wire
- Citation of wiki/concepts/fips-at-install-ocp-requirement.md
- `fips: true` in install-config.yaml required at install time
- `spec.tls.fips.enabled` on CFK CRs is silently no-op on a non-FIPS OCP cluster

**What the answer MUST NOT contain:**
- Refusal to answer the FIPS question
- Suggestion that post-install FIPS conversion is a supported Red Hat path

**Negative-space trigger:** NO
