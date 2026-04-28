# Golden Test Harness — /ask Skill Cases

## Overview

This directory contains the golden test harness for the `/ask` skill. Each `.md` file in `cases/` defines a single evaluation case: the query to ask, the expected routing decision, the floor model required to pass, and the claims the answer must (and must not) contain.

Phase 1 tests are **structural only** — they verify that case files are well-formed and meet distribution requirements. LLM-evaluated rubric scoring (actually running the skill against a model and grading output) is deferred to Phase 4.

Run with:

```bash
python3 -m pytest tests/golden/ask/test_golden_ask.py -v
```

---

## Case File Format

Each case file is a `.md` file with YAML front matter followed by a markdown body. The YAML block contains machine-readable fields; the body documents human-readable expected behavior.

```yaml
---
id: wiki-only-acks-001               # Unique identifier — must match filename prefix
query: "What is the difference..."   # Exact query string passed to /ask
expected_route: wiki-only            # One of: wiki-only | wiki+mcp | deep | refuse | redirect_to_mcp
floor_model: haiku                   # Minimum model to pass: haiku | sonnet
tags: [kafka, producers, durability] # Topic tags for filtering
required_claims:                     # Strings that MUST appear in the answer
  - "acks=all"
  - "min.insync.replicas"
forbidden_claims:                    # Strings that MUST NOT appear in the answer
  - "I don't know"
  - "cannot answer"
expected_sources_pattern: "wiki/"    # Optional: expected source path pattern
---

## Case: <Human-readable title>

**What the answer MUST contain:**
- ...

**What the answer MUST NOT contain:**
- ...

**Negative-space trigger:** YES | NO
```

### Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique case identifier. Use `<route-prefix>-<topic>-<NNN>` format. |
| `query` | Yes | The exact query string to submit to `/ask`. |
| `expected_route` | Yes | Which route the classifier should select. |
| `floor_model` | Yes | Minimum Claude model that should pass this case. |
| `tags` | Yes | List of topic tags (YAML list format). |
| `required_claims` | Yes | List of strings that must appear in the answer. |
| `forbidden_claims` | Yes | List of strings that must NOT appear in the answer. |
| `expected_sources_pattern` | No | Optional path pattern for expected wiki sources cited. |

---

## Distribution Requirements

The structural test runner (`test_golden_ask.py`) enforces:

| Requirement | Minimum | Test |
|-------------|---------|------|
| Total case files | 30 | `test_minimum_case_count` |
| Negative-space cases (refuse / redirect_to_mcp) | 5 | `test_minimum_negative_space_cases` |
| Routes covered | wiki-only, wiki+mcp, deep all present | `test_all_three_routes_covered` |
| Haiku-floor cases | 10 | `test_haiku_cases_exist` |
| Sonnet-floor cases | 10 | `test_sonnet_cases_exist` |
| Unique IDs | All unique | `test_case_id_unique` |

---

## Floor Model Guidelines

### `floor_model: haiku`

Use for simple, single-topic factual lookups where a smaller model can answer correctly:
- 2-3 required claims (key terms only)
- Straightforward in-domain questions
- No multi-source synthesis required
- Example: "What is the default replication factor for production clusters?"

### `floor_model: sonnet`

Use for complex questions requiring reasoning, synthesis, or trade-off analysis:
- 3+ required claims with substantive content
- Multi-topic or architecture-design questions
- Negative-space cases that require recognizing hallucination bait
- Example: "Design a DR architecture for multi-region FSI deployment with RPO < 10 seconds"

---

## Route Reference

| Route | When Used | Example Query |
|-------|-----------|---------------|
| `wiki-only` | 3+ wiki articles match, no version/config specifics | "What is acks=all?" |
| `wiki+mcp` | Version numbers, config keys, API names, or "does X support Y" | "What is the default acks in Kafka 3.x?" |
| `deep` | Multi-topic, architecture design, trade-off analysis | "Compare EOS vs ALO for regulatory reporting" |
| `refuse` | Out-of-domain, hallucination bait, non-Confluent topics | "How do I train a PyTorch model?" |
| `redirect_to_mcp` | Competitor comparison needing balanced sourcing | "Why is Redpanda better than Confluent?" |

---

## Running Tests

```bash
# Structural validation only (fast, no model calls)
python3 -m pytest tests/golden/ask/test_golden_ask.py -v

# Specific test class
python3 -m pytest tests/golden/ask/test_golden_ask.py::TestGoldenHarnessStructure -v
python3 -m pytest tests/golden/ask/test_golden_ask.py::TestFloorModelDistribution -v

# Full suite including golden harness
python3 -m pytest tests/ -x -q
```

---

## Adding Cases

1. Copy an existing case file from `cases/` as a template.
2. Name the file: `<route>-<topic>-<NNN>.md` (e.g., `wiki-only-compaction-011.md`).
3. Fill in all required YAML fields.
4. Write a descriptive markdown body explaining expected behavior.
5. Validate: `python3 -m pytest tests/golden/ask/test_golden_ask.py -v`

Naming conventions:
- `wiki-only-*.md` — cases that should route to wiki-only
- `mcp-*.md` — cases that should route to wiki+mcp
- `deep-*.md` — cases that should route to deep reasoning
- `negative-*.md` — cases that should refuse or redirect_to_mcp
