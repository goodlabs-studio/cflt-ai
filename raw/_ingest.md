---
title: Ingest Queue
last_updated: 2026-04-17
---

# Ingest Queue

Files listed here are pending compilation into the wiki.
Run: `python tools/wiki-compile.py --delta` to process.

## Pending

<!-- format:
- path: raw/articles/my-article.md
  source_url: https://...
  added: YYYY-MM-DD
  notes: optional context for the compiler
-->

- path: kafka-best-practices.md
  added: 2026-04-17
  notes: C4E wiki stub covering broker, producer, consumer, app-level, AKS, CC ops, and monitoring guidance for fraud detection on CC + Azure AKS. Compile into wiki/concepts/azure-connection-management.md and wiki/patterns/latency-optimized-kafka-client.md.

- path: kafka-recommendations.md
  added: 2026-04-17
  notes: Detailed 4-phase triage/remediation plan for e2e latency on CC Dedicated + Azure AKS. Keep as report in outputs/reports/. Source for wiki stubs on azure-connection-management and latency-optimized-kafka-client.

## Processed

- path: raw/repos/fsi-dsp/README.md
  source_url: https://github.com/goodlabs-studio/fsi-dsp
  notes: Top-level platform overview — compile into wiki/concepts/ and wiki/patterns/
  compiled: 2026-04-11
  wiki_articles:
    - wiki/concepts/fsi-data-streaming-platform.md
    - wiki/patterns/fsi-governance-automation.md

- path: raw/repos/fsi-dsp/docs/dr-runbook.md
  notes: DR procedures for CL, MM2, MRC — compile into wiki/patterns/dr-*
  compiled: 2026-04-11
  wiki_articles:
    - wiki/patterns/dr-cluster-linking.md
    - wiki/patterns/dr-mirrormaker2.md
    - wiki/patterns/dr-multi-region-cluster.md

- path: raw/repos/fsi-dsp/docs/schema-guide.md
  notes: Schema naming, compatibility, evolution — expand wiki/concepts/schema-evolution-strategies.md
  compiled: 2026-04-11
  wiki_articles:
    - wiki/concepts/schema-evolution-strategies.md

- path: raw/repos/fsi-dsp/docs/compliance-guide.md
  notes: FSI regulatory reference — new wiki/concepts/fsi-compliance.md
  compiled: 2026-04-11
  wiki_articles:
    - wiki/concepts/fsi-compliance.md

- path: raw/repos/fsi-dsp/ansible/vars/sla_tiers.yml
  notes: SLA tier definitions — new wiki/concepts/sla-tiers.md
  compiled: 2026-04-11
  wiki_articles:
    - wiki/concepts/sla-tiers.md

- path: raw/repos/fsi-dsp/ansible/vars/naming_rules.yml
  notes: Topic naming rules — expand wiki/concepts/ or new wiki/patterns/topic-naming.md
  compiled: 2026-04-11
  wiki_articles:
    - wiki/patterns/topic-naming.md

- path: raw/repos/fsi-dsp/docs/adr
  notes: Compile all ADRs into wiki/synthesis/adr-index.md with summaries
  compiled: 2026-04-11
  wiki_articles:
    - wiki/synthesis/adr-index.md
