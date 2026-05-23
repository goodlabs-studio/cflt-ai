---
id: linuxone-s390x-image-build-105
query: "How do I build a Confluent Connect image for s390x / LinuxONE?"
expected_route: wiki+mcp
floor_model: haiku
tags: [s390x, linuxone, docker-buildx, connect, gap-g08, wiki-04]
required_claims:
  - "s390x-custom-image-build-pipeline"
  - "docker buildx"
  - "linux/s390x"
forbidden_claims:
  - "I cannot help"
  - "no information"
---

## Case: s390x custom Connect image build pipeline (WIKI-04, gap G-08)

**What the answer MUST contain:**
- Citation of wiki/concepts/s390x-custom-image-build-pipeline.md
- `docker buildx build --platform linux/s390x` as the canonical build command
- Base image: CP 8.2.0 Connect s390x; connector JARs pre-installed (Splunk Sink / HTTP Sink)

**What the answer MUST NOT contain:**
- Suggestion that the upstream x86 image works as-is on s390x
- Refusal to answer the image build question

**Negative-space trigger:** NO
