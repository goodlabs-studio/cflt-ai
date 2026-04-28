# Codebase Structure

**Analysis Date:** 2026-04-28

## Directory Layout

```
cflt-ai/
├── .claude/                         # Claude Code configuration
│   ├── CLAUDE.md                    # Confluent Canon (auto-read every session)
│   ├── settings.json                # Shared MCP allowlist
│   ├── settings.local.json          # Personal overrides (gitignored)
│   └── commands/
│       ├── ask.md                   # /ask skill: validate configs + answer questions
│       ├── review.md                # /review skill: evaluate documents
│       └── wiki/                    # Wiki reconsolidation skills
│           ├── ingest.md            # /wiki:ingest: compile raw sources into articles
│           ├── validate.md          # /wiki:validate: check articles against live MCP
│           ├── recommend.md         # /wiki:recommend: answer + write discoveries
│           ├── lint.md              # /wiki:lint: health check
│           ├── evaluate.md          # /wiki:evaluate: full document evaluation
│           └── references/          # Helper docs for wiki skills
│               ├── article-format.md
│               └── quality-standards.md
├── .mcp.json                        # MCP server declarations (context7, confluent-docs, mcp-confluent)
├── .flox/                           # Flox environment cache
├── bin/
│   └── setup                        # First-run setup script (auth, credentials, MCP config)
├── wiki/                            # Authoritative knowledge base
│   ├── _index.md                    # Master article index (LLM-maintained)
│   ├── _graph.md                    # Backlink registry (LLM-maintained)
│   ├── _queue.md                    # Work queue: stubs, gaps, stale articles
│   ├── concepts/                    # Foundational topics
│   │   ├── exactly-once-semantics.md
│   │   ├── flink-checkpointing.md
│   │   ├── consumer-lag-monitoring.md
│   │   ├── producer-batching-config.md
│   │   ├── cluster-linking-topology.md
│   │   ├── consumer-group-rebalancing.md
│   │   ├── fsi-data-streaming-platform.md
│   │   ├── fsi-compliance.md
│   │   ├── schema-evolution-strategies.md
│   │   └── sla-tiers.md
│   ├── patterns/                    # Operational patterns
│   │   ├── fsi-governance-automation.md
│   │   ├── topic-naming.md
│   │   ├── dr-cluster-linking.md
│   │   ├── dr-mirrormaker2.md
│   │   ├── dr-multi-region-cluster.md
│   │   ├── fsi-exactly-once.md
│   │   ├── dead-letter-queue-design.md
│   │   └── aks-kafka-tuning.md
│   ├── synthesis/                   # Derived artifacts
│   │   └── adr-index.md             # Cross-referenced ADRs
│   ├── incidents/                   # Incident postmortems (future)
│   ├── releases/                    # Release notes (future)
│   └── activity/                    # Activity log (monthly)
│       └── YYYY-MM.md               # Immutable skill invocation audit trail
├── tools/                           # CLI utilities
│   ├── wiki-lint.py                 # Health check: stubs, broken links, orphans, stale articles
│   ├── wiki-search.py               # Full-text search
│   ├── wiki-stats.py                # Coverage metrics
│   └── wiki-compile.py              # Process ingest queue
├── raw/                             # Input staging area
│   ├── _ingest.md                   # Queue of sources to compile into wiki
│   ├── articles/                    # External articles (URL refs, markdown)
│   ├── papers/                      # Academic/technical papers
│   ├── images/                      # Diagrams and reference images
│   ├── incidents/                   # Raw incident reports
│   └── repos/
│       └── fsi-dsp/                 # Reference Ansible/Terraform/ADRs (submodule)
│           ├── MANIFEST.yaml        # Stable IDs for ansible roles, modules, ADRs
│           ├── ansible/             # Operational playbooks
│           │   ├── roles/           # Reusable roles (cfk_operator, cp_topic, cp_schema, etc.)
│           │   └── inventories/     # Environment vars (prod, staging, dev, dr)
│           ├── modules/             # Terraform modules (topic, flink)
│           ├── docs/adr/            # Architecture decision records
│           ├── environments/        # Prod environment definitions
│           ├── scenarios/           # Deployment templates (cc-aws, cfk-openshift, cp-rhel)
│           ├── reference/           # Example implementations (Java, Python, .NET)
│           ├── schemas/             # Avro/Protobuf examples
│           ├── tests/               # Ansible molecule tests
│           ├── observability/       # Datadog, Dynatrace, Grafana configs
│           └── scripts/             # CI and utilities
├── outputs/                         # Skill-generated artifacts
│   ├── reports/                     # Review reports from /review skill
│   │   └── <slug>-review-YYYY-MM-DD.md
│   ├── slides/                      # Generated presentation decks (future)
│   └── charts/                      # Generated diagrams (future)
├── .planning/
│   └── codebase/                    # Codebase mapping documents (this directory)
│       ├── ARCHITECTURE.md          # Architecture, layers, data flow
│       ├── STRUCTURE.md             # Directory layout, entry points, naming
│       ├── STACK.md                 # Technology stack (planned)
│       ├── INTEGRATIONS.md          # External integrations (planned)
│       ├── CONVENTIONS.md           # Coding conventions (planned)
│       ├── TESTING.md               # Testing patterns (planned)
│       └── CONCERNS.md              # Technical debt (planned)
├── .github/
│   └── workflows/                   # CI/CD pipelines
├── CLAUDE.md                        # Confluent Canon (global, shared, git-tracked)
├── .claude.local.md                 # Personal overrides (gitignored)
├── PROJECT.md                       # Project vision, phases, constraints
├── CONTRIBUTING.md                  # Contribution guidelines
├── README.md                        # Quick start guide
└── .gitignore                       # Excludes .claude.local.md, .env*, credentials
```

## Directory Purposes

**`.claude/` — Claude Code Configuration:**
- **Purpose:** Skill definitions, MCP server config, shared settings
- **Contains:** Command implementations (markdown-based instruction sets), MCP server declarations
- **Key files:**
  - `CLAUDE.md`: Confluent Canon (defaults, FSI overlay, competitive context)
  - `commands/ask.md`: Query skill with 5-step validation process
  - `commands/review.md`: Document evaluation with claim extraction
  - `commands/wiki/*`: Wiki maintenance skills (ingest, validate, lint, etc.)

**`wiki/` — Authoritative Knowledge Base:**
- **Purpose:** Validated, indexed Kafka/Flink/Schema Registry knowledge
- **Contains:** Markdown articles organized by topic (concepts, patterns)
- **Key files:**
  - `_index.md`: Master registry of all articles (title, summary, tags) — LLM-maintained
  - `_graph.md`: Backlink registry — LLM-maintained
  - `_queue.md`: Work queue (discovered gaps, stale content, stubs)
- **Growth:** Articles are written by `/wiki:ingest` (from raw sources), `/wiki:recommend` (from discovered questions), and manual contributions
- **Maintenance:** `/wiki:lint` scans for health issues; `/wiki:validate` checks against live MCP sources

**`tools/` — CLI Utilities:**
- **Purpose:** Command-line access to wiki operations (no Claude Code needed)
- **Contains:** Python scripts with argparse
  - `wiki-lint.py`: Scan for stubs, broken links, orphans, stale articles (>90 days)
  - `wiki-search.py`: Full-text search across articles
  - `wiki-stats.py`: Coverage metrics (article count, backlink graph, confidence distribution)
  - `wiki-compile.py`: Process ingest queue from `raw/`
- **Invocation:** `wiki-lint --full`, `wiki-search "cluster linking"`, `wiki-stats`

**`raw/` — Input Staging Area:**
- **Purpose:** Collect unprocessed sources before compilation into wiki
- **Contains:**
  - `_ingest.md`: Queue of sources to process
  - `articles/`: External Markdown or text articles
  - `papers/`: Academic/technical papers for reference
  - `images/`: Diagrams, architecture images
  - `incidents/`: Raw incident reports (to be synthesized)
  - `repos/fsi-dsp/`: Reference implementations (Ansible, Terraform, ADRs) as a submodule
- **Flow:** Sources added → `/wiki:ingest` reads queue → compiles into articles with MCP validation → articles moved to `wiki/`

**`raw/repos/fsi-dsp/` — Reference Implementation Repository:**
- **Purpose:** Published opinions-as-code: Ansible playbooks, Terraform modules, ADRs, scenario templates
- **Contains:**
  - `MANIFEST.yaml`: Stable identifiers (adr/009, module/topic, role/cp_topic, etc.)
  - `ansible/roles/`: Reusable roles (cfk_operator, cp_topic, cp_schema, cp_dr_mm2, cp_rbac, cp_observability)
  - `modules/`: Terraform modules (topic, flink)
  - `docs/adr/`: Architecture decision records (008: Avro, 009: LinuxONE, etc.)
  - `scenarios/`: Deployment templates (Confluent Cloud on AWS/GCP/Azure, CFK on OpenShift, CP on RHEL)
  - `reference/`: Example code (Java producer/consumer, Python, .NET)
  - `environments/`: Prod/staging/dev inventory and group vars
- **Contract:** MANIFEST.yaml IDs never change without a major bump; cflt-ai cites by ID

**`outputs/` — Skill-Generated Artifacts:**
- **Purpose:** Persistent output from skill invocations
- **Contains:**
  - `reports/`: Review reports from `/review` skill (markdown, later `.docx`)
  - `slides/`: Generated presentation decks (planned)
  - `charts/`: Generated architecture diagrams (planned)
- **Naming:** `<slug>-review-YYYY-MM-DD.md` for review reports

**`bin/` — Setup & Admin Scripts:**
- **Purpose:** One-time initialization and admin utilities
- **Contains:**
  - `setup`: First-run script (checks Claude Code, prompts for auth, fsi-dsp submodule, CC credentials, MCP config)

**`.planning/codebase/` — Codebase Mapping Documents:**
- **Purpose:** Structured documentation for `/gsd:map-codebase` and `/gsd:plan-phase` consumers
- **Contains:** ARCHITECTURE.md, STRUCTURE.md, STACK.md, INTEGRATIONS.md, CONVENTIONS.md, TESTING.md, CONCERNS.md

## Key File Locations

**Entry Points:**

- `bin/setup`: First-run initialization (auth, credentials, MCP, fsi-dsp submodule)
- `.claude/commands/ask.md`: `/ask` skill entry point (user-facing query)
- `.claude/commands/review.md`: `/review` skill entry point (document evaluation)
- `.claude/commands/wiki/*.md`: Wiki maintenance skills (`/wiki:ingest`, `/wiki:validate`, `/wiki:lint`, etc.)

**Configuration:**

- `CLAUDE.md`: Confluent Canon (base defaults, FSI overlay, competitive context) — auto-read by Claude Code every session
- `.claude.local.md`: Personal overrides for canon (gitignored)
- `.mcp.json`: MCP server declarations (context7, confluent-docs, mcp-confluent)
- `~/.claude/settings.json`: Claude Code global settings (MCP auto-approve flag)
- `~/.config/confluent/mcp.env`: Confluent Cloud credentials (optional, for mcp-confluent)

**Core Logic:**

- `wiki/concepts/*.md`: Foundational knowledge articles
- `wiki/patterns/*.md`: Operational pattern articles
- `wiki/_index.md`: Master article index (LLM-maintains)
- `wiki/_graph.md`: Backlink registry (LLM-maintains)
- `wiki/_queue.md`: Work queue (auto-populated by `/wiki:lint`)

**Testing:**

- `tests/golden/ask/`: Golden test cases for `/ask` skill (planned Phase 1)
- `tests/golden/review/`: Golden test cases for `/review` skill (planned Phase 2)
- `tests/golden/act/`: Golden test cases for act rail (planned Phase 3a)

**Utilities:**

- `tools/wiki-lint.py`: Health check CLI
- `tools/wiki-search.py`: Search CLI
- `tools/wiki-stats.py`: Coverage metrics CLI

## Naming Conventions

**Files:**

- Wiki articles: `kebab-case.md` (e.g., `exactly-once-semantics.md`, `dr-cluster-linking.md`)
- Python scripts: `kebab-case.py` (e.g., `wiki-lint.py`)
- Bash scripts: No extension or `.sh` (e.g., `bin/setup`)
- Reports: `<slug>-review-YYYY-MM-DD.md` (e.g., `kafka-dr-framework-review-2026-04-28.md`)
- Activity logs: `YYYY-MM.md` (e.g., `2026-04.md`)

**Directories:**

- Concept groups: `wiki/concepts/` (no subdirs; flat structure)
- Patterns: `wiki/patterns/` (flat structure)
- Raw sources: `raw/<type>/` (articles, papers, incidents, images)
- Reference implementations: `raw/repos/` (git submodules)
- Generated artifacts: `outputs/<type>/` (reports, slides, charts)
- Environment-specific: `<repo>/inventories/<env>/` (dev, staging, prod, dr)

**Topics in Wiki:**

- Domain: `{domain}.{topic}` (e.g., `fsi-compliance`, `fsi-governance`)
- Kafka: `consumer-lag-monitoring`, `producer-batching-config`
- Flink: `flink-checkpointing`
- DR patterns: `dr-cluster-linking`, `dr-mirrormaker2`

## Where to Add New Code

**New Wiki Article:**
- Primary: `wiki/concepts/` for foundational topics OR `wiki/patterns/` for operational patterns
- Naming: `kebab-case.md` (e.g., `ack-strategy-for-transactions.md`)
- Frontmatter: Title, confidence, tags, sources, last_validated
- Register: Add entry to `wiki/_index.md` under appropriate section
- Backlinks: Update `wiki/_graph.md` with forward/reverse links
- Validation: Run `wiki-lint --full` to check for issues

**New Skill (/command):**
- Primary: `.claude/commands/<name>.md` (e.g., `.claude/commands/dsp:plan.md`)
- Pattern: Follow structure in `ask.md` or `review.md` (input section, process steps, output format)
- References: Link to existing wiki articles and MCP sources
- Testing: Add cases to `tests/golden/<skill>/` once testing harness is live

**New fsi-dsp Reference Implementation:**
- Primary: `raw/repos/fsi-dsp/` (submodule)
- Ansible role: `raw/repos/fsi-dsp/ansible/roles/cp_<domain>_<feature>/`
- Terraform module: `raw/repos/fsi-dsp/modules/<domain>/`
- Scenario: `raw/repos/fsi-dsp/scenarios/<deployment>-<provider>/`
- ADR: `raw/repos/fsi-dsp/docs/adr/NNN-<title>.md`
- Register: Update `raw/repos/fsi-dsp/MANIFEST.yaml` with stable ID

**Utilities:**
- CLI tools: `tools/wiki-*.py` (Python with argparse)
- Admin scripts: `bin/<name>` (Bash)

## Special Directories

**`.flox/` — Flox Environment Cache:**
- Purpose: Caches for Node.js, Python, and other dependencies
- Generated: Yes (automatically by Flox)
- Committed: No (gitignored)

**`.github/workflows/` — CI/CD Pipelines:**
- Purpose: Automated checks on PRs (wiki-lint, link validation, etc.)
- Generated: No
- Committed: Yes

**`wiki/activity/` — Activity Log:**
- Purpose: Immutable audit trail of skill invocations
- Generated: Yes (by skills)
- Committed: Yes
- Format: One file per month (`YYYY-MM.md`); append-only

**`outputs/` — Skill-Generated Reports:**
- Purpose: Persistent deliverables from `/review` and future skills
- Generated: Yes (by skills)
- Committed: No (can be committed selectively)
- Naming: `<slug>-<skill>-YYYY-MM-DD.<ext>`

---

*Structure analysis: 2026-04-28*
