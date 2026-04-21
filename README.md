# cflt-ai — Confluent Knowledge Base for Claude Code

A shared knowledge base of Kafka, Flink, Schema Registry, and Confluent architecture patterns. Claude Code does the heavy lifting — validating configs, reviewing architecture docs, and answering Kafka/Flink/DR questions against a compiled wiki and live MCP sources.

No custom application code. The "app" is Claude Code itself, configured via committed files.

## Quick Start

```bash
# 1. Clone (--recurse-submodules pulls fsi-dsp if you have access)
git clone --recurse-submodules git@github.com:goodlabs-studio/cflt-ai.git && cd cflt-ai

# 2. Activate the environment (installs Python, Node.js, etc.)
flox activate

# 3. Run first-time setup (auth, credentials, MCP config)
bin/setup

# 4. Start Claude Code
claude
```

That's it. Ask a question, paste a config, or run a skill.

## What You Can Do

### `/ask` — Get a validated answer

Paste a config snippet, error message, or architecture question. Claude searches the wiki, applies Confluent Canon defaults, and validates claims against live MCP sources.

```
/ask What's the right acks setting for a transactional producer writing to a compacted topic?
```

### `/review` — Evaluate a document

Point at a file and get a structured review with claim-by-claim validation.

```
/review kafka-dr-framework-v3.md
```

Output lands in `outputs/reports/<slug>-review-<date>.md`.

### Wiki Skills

| Skill | Purpose |
|-------|---------|
| `/wiki:ingest` | Compile raw sources into wiki articles with MCP validation |
| `/wiki:validate` | Check wiki claims against live Confluent docs, patch drift |
| `/wiki:recommend` | Answer questions using wiki + MCP, write back discoveries |
| `/wiki:lint` | Health check: stubs, broken links, orphans, stale articles |
| `/wiki:evaluate` | Full evaluation of external documents against wiki + MCP |

### CLI Tools

```bash
wiki-search "cluster linking DR"    # full-text search
wiki-lint --full                     # health check
wiki-stats                           # coverage metrics
wiki-compile --delta                 # process raw ingest queue
```

## Project Structure

```
cflt-ai/
├── .mcp.json                        # MCP server declarations
├── CLAUDE.md                        # Confluent Canon (auto-read by Claude Code)
├── .claude/
│   ├── settings.json                # Shared permission allowlist
│   ├── settings.local.json          # Personal overrides (gitignored)
│   └── commands/
│       ├── ask.md                   # /ask skill
│       ├── review.md                # /review skill
│       └── wiki/                    # Wiki reconsolidation skills
├── wiki/
│   ├── _index.md                    # Master article index
│   ├── _graph.md                    # Backlink registry
│   ├── _queue.md                    # Work queue
│   ├── concepts/                    # Foundational knowledge
│   ├── patterns/                    # Reusable architecture patterns
│   └── synthesis/                   # Cross-cutting analysis (ADRs)
├── raw/
│   └── repos/fsi-dsp/              # Git submodule: Ansible, Terraform, ADRs, reference code
├── tools/                           # Python CLI tools
├── outputs/                         # Generated reports
├── bin/
│   └── setup                        # First-run setup script
└── .github/
    ├── PULL_REQUEST_TEMPLATE.md     # PR template for contributions
    └── workflows/wiki-lint.yml      # CI lint for wiki PRs
```

## How It Works

```
                    ┌─────────────────┐
                    │   Claude Code   │
                    │   (the "app")   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──────┐ ┌────▼────┐ ┌───────▼───────┐
     │  Compiled Wiki │ │ Canon   │ │ MCP Servers   │
     │  (wiki/)       │ │(CLAUDE  │ │ - context7    │
     │  19 articles   │ │  .md)   │ │ - cflt-docs   │
     │  concepts +    │ │ defaults│ │ - mcp-cflt    │
     │  patterns +    │ │ + FSI   │ │   (optional)  │
     │  synthesis     │ │ overlay │ │               │
     └───────────────┘ └─────────┘ └───────────────┘
```

Skills combine these three sources: the wiki provides institutional knowledge, CLAUDE.md provides canonical defaults, and MCP servers provide live validation against current Confluent docs and APIs.

## fsi-dsp Reference Repo (Optional)

The [fsi-dsp](https://github.com/goodlabs-studio/fsi-dsp) repo is linked as a git submodule at `raw/repos/fsi-dsp/`. It contains Ansible vars, Terraform configs, ADRs, and reference Java/Python implementations that 10+ wiki articles cite as sources.

`bin/setup` offers to initialize it. You can also do it manually:

```bash
git submodule update --init raw/repos/fsi-dsp
```

Requires SSH access to `goodlabs-studio/fsi-dsp`. Without it, wiki skills still work — `/wiki:evaluate` skips code-delta checks and notes the gap in its report.

## Confluent Cloud Integration (Optional)

The `mcp-confluent` server lets Claude query live Confluent Cloud clusters (topics, schemas, Flink SQL). Setup during `bin/setup`, or manually:

```bash
mkdir -p ~/.config/confluent
cat > ~/.config/confluent/mcp.env << 'EOF'
CONFLUENT_CLOUD_API_KEY=<your-key>
CONFLUENT_CLOUD_API_SECRET=<your-secret>
EOF
export CONFLUENT_MCP_ENV_FILE=~/.config/confluent/mcp.env
```

Without CC credentials, the wiki and skills still work — you just can't query live clusters.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide. The short version:

1. Branch from `main`
2. Add/modify wiki articles, run `/wiki:lint`
3. Open a PR — CI validates wiki structure automatically
4. Note which claims were MCP-validated in the PR description

## Requirements

- **[Flox](https://flox.dev)** — manages the dev environment (Python, Node.js, etc.)
- **Claude Code** — installed separately via `npm install -g @anthropic-ai/claude-code` or Homebrew
- **Claude auth** — either a Claude Max/Pro subscription or an Anthropic API key
