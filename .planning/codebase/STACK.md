# Technology Stack

**Analysis Date:** 2026-04-28

## Languages

**Primary:**
- Python 3.9+ - CLI tools and infrastructure automation (wiki linting, searching, compilation)
- Bash - Setup scripts, environment orchestration, Shell integration
- Markdown - Wiki content and documentation (core knowledge base format)
- YAML - Configuration files, article frontmatter, variable definitions in fsi-dsp submodule
- JSON - Configuration files (.mcp.json), settings files, data interchange

**Secondary:**
- HCL/Terraform - Infrastructure as Code in fsi-dsp submodule (`raw/repos/fsi-dsp/environments/prod/`)
- Ansible YAML - Configuration management and automation in fsi-dsp submodule (`raw/repos/fsi-dsp/ansible/`)
- Java - Reference implementations in fsi-dsp submodule
- SQL/Flink SQL - Stream processing patterns documented in wiki

## Runtime

**Environment:**
- Python 3.9.6 (managed by Flox)
- Node.js v24.5.0 (managed by Flox)
- Bash/Zsh shell
- macOS (Darwin 25.3.0) - development platform

**Package Manager:**
- pip - Python dependencies
- npm/npx - Node.js packages (MCP servers)
- Flox - Unified dev environment and dependency management (primary)
- Lockfile: `.flox/` directory and Flox manifest (location not found in current scan)

## Frameworks

**Core:**
- Claude Code - Agent framework for interactive skills and commands
- MCP (Model Context Protocol) - Server specification for tool integration

**CLI Tools (Python-based):**
- `wiki-lint.py` - Wiki health checking (stubs, broken links, orphans, stale articles)
- `wiki-search.py` - Full-text search over wiki articles
- `wiki-stats.py` - Coverage and statistics reporting
- `wiki-compile.py` - Incremental compiler from raw sources to wiki articles

**Build/Dev:**
- Flox - Reproducible development environment (primary)

## Key Dependencies

**Critical:**
- PyYAML - YAML parsing for wiki frontmatter and configuration (>= 6.0)
- @upstash/context7-mcp - Architecture patterns and Confluent canon patterns MCP server
- @langchain/mcpdoc-server - Live documentation indexing MCP server (Confluent docs via llms.txt)
- @confluentinc/mcp-confluent - Confluent Cloud control plane MCP server (optional, requires API credentials)

**Infrastructure:**
- Confluent Platform / Confluent Cloud - Subject of knowledge base (not a runtime dependency)
- Apache Kafka - Subject of knowledge base
- Apache Flink / Confluent Cloud Flink - Subject of knowledge base
- Confluent Schema Registry - Subject of knowledge base

## Configuration

**Environment:**
- `.mcp.json` - MCP server declarations and configuration (context7, confluent-docs, mcp-confluent)
- `.claude/settings.json` - Claude Code permissions and MCP auto-approve settings
- `.claude/commands/` - Command definitions for `/ask`, `/review`, and wiki skills
- `requirements.txt` - Python dependencies (currently: PyYAML >= 6.0)
- `CLAUDE.md` - Confluent Canon defaults and FSI overlay (auto-loaded by Claude Code)

**Build:**
- `bin/setup` - First-run initialization script (Claude Code auth, fsi-dsp submodule, Confluent Cloud credentials, MCP settings)
- `.github/workflows/wiki-lint.yml` - CI pipeline for wiki structure validation

## Platform Requirements

**Development:**
- Flox environment manager
- Claude Code (npm install -g @anthropic-ai/claude-code or Homebrew)
- Claude authentication (either Claude Max/Pro subscription or Anthropic API key)
- Python 3.9+ (managed by Flox)
- Node.js 20+ (managed by Flox)
- Git with submodule support (for fsi-dsp reference repo)
- Bash or Zsh shell

**Production:**
- Claude Code host (no separate backend deployment)
- Optional: Confluent Cloud credentials for mcp-confluent server (`~/.config/confluent/mcp.env`)
- Optional: SSH access to github.com/goodlabs-studio/fsi-dsp (for reference implementations)

## Deployment Model

This is a **knowledge base and agent application**, not a traditional application:

- **Distributed:** As Claude Code workspaces (no central backend)
- **Version Control:** Wiki articles, commands, and tools tracked in git
- **CI/CD:** GitHub Actions for wiki structure validation (`.github/workflows/wiki-lint.yml`)
- **Secrets:** Confluent Cloud API credentials in `~/.config/confluent/mcp.env` (local, gitignored)

---

*Stack analysis: 2026-04-28*
