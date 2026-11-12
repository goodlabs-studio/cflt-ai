# Getting started with cflt-ai

GoodLabs Studio · v1.0 · 2026-11-12 · Living document

## 1. Purpose and summary

cflt-ai is the shared Confluent knowledge base and Claude Code workspace for GoodLabs Studio consultants working as Confluent Professional Services. You ask questions, review client documents and write runbooks here, and Claude answers from the validated wiki plus live Confluent docs.

One rule matters more than the rest: **no client organization is ever named in this repo.** Technology vendors, products and tools are fine. Client names, client hostnames and engagement narrative are not. Local guards block them at commit, at push and whenever Claude edits a file, and each consultant keeps their own client list that never leaves their machine.

Setup takes about 15 minutes on a machine that already has Python, Node and Claude Code.

| Section | What it covers |
|---|---|
| 2 | Setting up a new machine, credentials, and what stays local |
| 3 | The client-name guards: what they block and how to clear a blocked push |
| 4 | Daily workflow: asking, writing documents, runbooks in engagement folders, pushing |
| 5 | Troubleshooting |
| 6 | Open questions and next steps |

## 2. Set up a new machine

### 2.1 Prerequisites

| Tool | Needed for | Required |
|---|---|---|
| Git and SSH access to `goodlabs-studio` | Cloning this repo and the `fsi-dsp` submodule | Yes |
| Claude Code (`npm install -g @anthropic-ai/claude-code`) and a login | Everything | Yes |
| Python 3.11+ | Wiki tools, canon tooling, the client-name guards | Yes |
| Node.js 22 and `uv` | MCP servers in `.mcp.json` | Yes for MCP |
| pandoc (`brew install pandoc`) | Building `.docx` from `.md` with `tools/md2docx` | Only for Word output |
| Flox | Pinning the toolchain | No |

### 2.2 Clone and run setup

```bash
git clone --recurse-submodules git@github.com:goodlabs-studio/cflt-ai.git
cd cflt-ai
bin/setup            # auth, MCP prerequisites, fsi-dsp, credentials, MCP approval, client-name guards
bin/setup-guards --claude-hook   # if you skipped step 8, or to add the Claude Code edit hook
bin/setup-guards --check         # confirm everything is green
claude
```

`bin/setup` is safe to re-run. Step 8 calls `bin/setup-guards`, which sets `core.hooksPath=.githooks`, adds the `git org-audit` alias and creates your `.client-terms` from the template. The `--claude-hook` flag also adds a PostToolUse hook to your own `~/.claude/settings.json` so Claude is checked on every edit it makes in this repo. It backs up the settings file first.

If you can't clone `fsi-dsp` over SSH, use HTTPS after `gh auth login`:

```bash
git -c url."https://github.com/".insteadOf="git@github.com:" submodule update --init raw/repos/fsi-dsp
```

Without `fsi-dsp` the wiki and knowledge skills still work. `/dsp:plan` and `/dsp:apply` need it.

### 2.3 Credentials for live MCP servers

The docs servers (`confluent-docs`, `context7`, `shadowtraffic-docs`, `headroom-docs`, `terraform`) need no credentials. The live ones read yours from your environment or a local file, never from the repo.

| Server | What it reads | Where |
|---|---|---|
| `mcp-confluent` | `CONFLUENT_CLOUD_API_KEY`, `CONFLUENT_CLOUD_API_SECRET` | `~/.config/confluent/mcp.env` (chmod 600), or `$CONFLUENT_MCP_ENV_FILE` |
| `dynatrace` | `DT_ENVIRONMENT`, `DT_PLATFORM_TOKEN` | Shell environment. Grail queries bill by GB and are capped at 50 GB |
| `grafana` | `GRAFANA_URL`, `GRAFANA_API_KEY` | Shell environment. Runs read-only |

`shadowtraffic-docs` and `headroom-docs` stay disabled until you enable them with `/mcp`.

### 2.4 What stays on your machine

These pieces are per-person and never committed. A teammate's clone works without yours.

| Piece | Location | Notes |
|---|---|---|
| Client list | `.client-terms` at the repo root | Gitignored, chmod 600. The commit and push gates refuse it by name if it is ever force-added |
| "Not a client" decisions | `.org-audit-reviewed` at the repo root | Gitignored. Written by `org_audit.py --accept` |
| Git hook wiring and alias | `.git/config` | `core.hooksPath=.githooks`, `alias.org-audit` |
| Claude Code edit hook | `~/.claude/settings.json` | Points at this clone's `tools/org_audit.py` |
| Haiku verdict cache | `~/.cache/org-audit/` | Only used by `--explain` |
| MCP credentials and MCP approval | `~/.config/confluent/`, `.claude/settings.local.json` | Gitignored |
| Generated `.docx` files | `outputs/**` | Gitignored. Rebuild from the `.md` (section 4.2) |

## 3. Client-name guards

### 3.1 What is blocked and where

`tools/org_audit.py` finds two kinds of names. A **CLIENT** is anything on your `.client-terms` list. A **REVIEW** is an org-like name the local patterns pick up: a company suffix ("Holdings", "Credit Union", "Payments"), party wording ("for the `<Name>` platform team", "`<Name>`'s prod cluster") or an acronym used as a party ("the `<ACRONYM>` BU requirement"). Names on `tools/org-audit-allowlist.txt` always pass: GoodLabs, Confluent, IBM, cloud and tooling vendors, open-source projects, regulators and placeholder names such as Acme.

| Gate | CLIENT | REVIEW | Runs |
|---|---|---|---|
| `.githooks/pre-commit` | Blocks | Warns | Locally, no network |
| `.githooks/pre-push` | Blocks | Blocks | Locally, after the canon guard |
| Claude Code edit hook | Stops Claude and asks for a rewrite | Same | Locally, on every Edit or Write that resolves into this repo, including edits through a symlink in an engagement folder |
| `git org-audit` | Reports | Reports | On demand |

The push gate also runs `.githooks/canon-guard`, which refuses client or engagement canon under `canon/customer/` and `canon/engagement/`. The `canon-silo-guard.yml` CI job backs that up on the server side.

### 3.2 Your client list

Add every organization you consult for to `.client-terms`, one per line, the day an engagement starts. Plain entries match regardless of case, extra spaces, hyphens, underscores, dots, line wraps or no space at all, so "Example Clearing" also catches "EXAMPLE  CLEARING", "example-clearing" and "exampleclearing.com". Add short forms and acronyms too. For hostnames and patterns, use a regex entry: `re:\bexcl-?corp\.internal\b` or `/prd-kafka-\d+\.example\.net/`. A bad regex is reported and skipped, so it never blocks a commit by accident.

`.client-terms.example` documents the format. Never put a real client name in the template or in the allowlist.

### 3.3 Commands

```bash
git org-audit                       # whole repo, local, about 2 seconds
git org-audit outputs/runbooks      # specific files or folders
git org-audit --explain             # adds a Claude Haiku verdict and reason for each REVIEW name
git org-audit --fix [paths]         # walk each finding: accept a neutral rewrite, edit, skip, or mark not-a-client
git org-audit --accept "Name"       # a REVIEW name that is not a client
git org-audit --add-client "Name"   # append a client to .client-terms
```

`--explain` is the only mode that sends anything off the machine. It sends a REVIEW name plus its one line of context to Claude Haiku through your own `claude` login, with no tools, no MCP servers and no saved session. Names from your client list are never sent. Without a login it falls back to local results.

### 3.4 When a push is blocked

1. Read the report. It lists each file, line, name and the reason it was flagged.
2. Run `git org-audit --fix <files>` and accept or edit each rewrite. Prefer wording that keeps the technical point: "a financial services client", "the platform team".
3. If a REVIEW name is a vendor or product, run `git org-audit --accept "Name"`. If it should be shared with the team, add it to `tools/org-audit-allowlist.txt` instead.
4. Review `git diff`, commit, and push again.

> **Recommendation for every consultant:** the patterns can't recognize a client named by a bare word with no company suffix or party wording ("Meridian runs three clusters"). Only your `.client-terms` list catches that. To test: after adding a new client, run `git org-audit` on a scratch file that mentions the client in three spellings and confirm three CLIENT findings.

## 4. Daily workflow

### 4.1 Asking and reviewing

Start `claude` in the repo root. `/ask` answers a question or a pasted config against the wiki and live docs. `/review` evaluates a document. `/wiki:recommend` answers and writes discoveries back to the wiki. `/wiki:validate` and `/wiki:lint` keep the wiki honest. `CLAUDE.md` holds the Confluent defaults Claude applies to every answer, and the README describes every skill.

### 4.2 Writing documents

Read `WRITING.md` before writing anything. A document starts as one `.md` file in the senior-architect voice. Build Word output from the reviewed `.md`, never by hand:

```bash
python3 tools/md2docx/md2docx.py outputs/runbooks/<name>.md
for f in outputs/runbooks/*.md; do python3 tools/md2docx/md2docx.py "$f"; done   # rebuild all
```

`.docx` files under `outputs/` are gitignored. A fresh clone has none until you run the converter. Edit the `.md`, then convert again, so the two never drift.

### 4.3 Runbooks and engagement folders

`outputs/runbooks/` is the source of truth for general runbooks, and every runbook there stays universally applicable. Engagement folders (`~/GoodLabs/<Client>/`) reach a runbook through a symlink, so one edit shows up everywhere:

```bash
ln -s "$PWD/outputs/runbooks/<name>.md" ~/GoodLabs/<Client>/<name>.md
```

An edit made through that symlink lands in this repo, and the guards check it. Client-specific detail (hostnames, environment names, decisions specific to one client) goes in a separate real file in the engagement folder, never through the symlink.

### 4.4 Committing and pushing

Work on your own branch and open a PR to `main`. Never push to `main` directly. The pre-commit and pre-push gates run on every commit and push. If Claude commits for you, it states the repo, branch, files and purpose first and waits for your approval.

## 5. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `bin/setup-guards --check` shows a warning | A guard isn't installed | Run `bin/setup-guards`, then `--check` again |
| Hooks in `.git/hooks` stopped running | `core.hooksPath=.githooks` replaces `.git/hooks` | Move anything you still need into `.githooks/` |
| Claude edits aren't being checked | Settings change not loaded yet | Open `/hooks` in Claude Code once, or restart it |
| `--explain` prints "Haiku unavailable" | No `claude` login, or it expired | `claude auth login`; local results still work |
| `fsi-dsp` submodule won't clone | No SSH access | HTTPS fallback in section 2.2, or ask for org access |
| `mcp-confluent` fails to start | No credentials file | Create `~/.config/confluent/mcp.env` or re-run `bin/setup` |
| A `.docx` link in an engagement folder is broken | `.docx` files aren't committed | Rebuild with `tools/md2docx` (section 4.2) |
| A vendor or tool keeps getting flagged | Missing from the allowlist | `git org-audit --accept "Name"` for you, or add it to `tools/org-audit-allowlist.txt` for everyone |

## 6. Open questions and next steps

### 6.1 Open questions

| Question | Who answers | Why it matters |
|---|---|---|
| Should CI run `org_audit.py` in pattern-only mode on every PR? | Repo maintainers | Today only local hooks enforce it. CI can't see personal client lists, but it would catch REVIEW names from anyone who skipped setup. |
| Should `git push` to `main` be blocked locally as well as by branch protection? | Repo maintainers | Belt and braces for the "branch and PR" rule. |

### 6.2 Next steps for a new consultant

1. Run section 2 end to end and confirm `bin/setup-guards --check` is all green.
2. Fill `.client-terms` with every current client, then run `git org-audit`.
3. Read `CLAUDE.md`, `WRITING.md` and `CONTRIBUTING.md`.
4. Ask one real question with `/ask` to confirm the MCP servers answer.
