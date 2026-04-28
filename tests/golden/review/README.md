# Golden Test Harness — /review Skill Cases

## Overview

This directory contains the golden test harness for the `/review` skill (REVW-05). Each `.md` file in `cases/` defines a single evaluation case: the fixture document(s) to review, the minimum expected claim count, the floor model required to pass, and the report sections/content the review must (and must not) produce.

Phase 2 tests are **structural only** — they verify that case files are well-formed and meet distribution requirements. LLM-evaluated rubric scoring (actually running the skill against a model and grading output) is deferred to Phase 4.

Run with:

```bash
python3 -m pytest tests/golden/review/test_golden_review.py -v
```

---

## Case File Format

Each case file is a `.md` file with YAML front matter followed by a markdown body. The YAML block contains machine-readable fields; the body documents human-readable expected behavior.

```yaml
---
id: review-bad-acks-001            # Unique identifier
input_files:                       # List of fixture paths relative to repo root
  - tests/golden/review/fixtures/bad-acks-producer.md
expected_claims_min: 3             # Minimum claims the review must extract
floor_model: haiku                 # Minimum model to pass: haiku | sonnet
tags: [kafka, producers, acks]    # Topic tags for filtering
required_report_sections:          # Section headings that MUST appear in report
  - "## Summary"
  - "## Claim Validation"
  - "## Canon Compliance"
  - "## Recommendations"
forbidden_content:                 # Strings that MUST NOT appear in report
  - "I don't know"
  - "cannot answer"
# Optional fields:
expected_verdict_contains:         # Verdict strings the report should contain
  - "Corrected"
premise_challenge_expected: false  # Whether ## Premise Challenge section expected
overlay: null                      # Customer overlay name or null
---

## Case: <Human-readable title>

**What the review MUST find:**
- ...

**What the review MUST NOT contain:**
- ...

**Negative-space trigger:** YES | NO
```

### Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique case identifier. Use `review-<topic>-<NNN>` format. |
| `input_files` | Yes | List of fixture file paths relative to repo root. |
| `expected_claims_min` | Yes | Minimum number of claims the review must extract. |
| `floor_model` | Yes | Minimum Claude model that should pass this case. |
| `tags` | Yes | List of topic tags (YAML list format). |
| `required_report_sections` | Yes | List of section headings that must appear in report. |
| `forbidden_content` | Yes | List of strings that must NOT appear in the report. |
| `expected_verdict_contains` | No | List of verdict strings expected in the report. |
| `premise_challenge_expected` | No | Whether the report should include a Premise Challenge section. |
| `overlay` | No | Customer overlay name (e.g., `acme-bank`) or null. |

---

## Distribution Requirements

The structural test runner (`test_golden_review.py`) enforces:

| Requirement | Minimum | Test |
|-------------|---------|------|
| Total case files | 15 | `test_minimum_case_count` |
| Premise-challenge cases (REVW-02) | 1 | `test_premise_challenge_case_exists` |
| Overlay cases (REVW-06) | 1 | `test_overlay_case_exists` |
| Multi-doc cases (REVW-04) | 1 | `test_multi_doc_case_exists` |
| Correction cases (REVW-01) | 1 | `test_correction_case_exists` |
| Unique IDs | All unique | `test_case_id_unique` |
| Haiku-floor cases | 5 | `test_haiku_cases_exist` |
| Sonnet-floor cases | 5 | `test_sonnet_cases_exist` |

---

## Fixture Documents

Fixture documents in `fixtures/` are **synthetic documents** (15–50 lines) created specifically for testing. They are NOT real customer documents. Each fixture exercises specific review behaviors:

| Fixture | Purpose |
|---------|---------|
| `bad-acks-producer.md` | Producer config recommending acks=1 — triggers corrections |
| `correct-consumer-config.md` | All-canon consumer config — triggers Confirmed verdicts |
| `fsi-latency-assumptions.md` | Architecture doc with market data latency assumptions — triggers FSI premise challenge |
| `multi-doc-deck.md` | Slide content with Schema Registry JSON Schema claim |
| `multi-doc-tfvars.tfvars` | Terraform vars with non-canon values (partition_count, replication_factor) |
| `multi-doc-runbook.md` | Operational runbook referencing deck and tfvars |
| `overlay-compression-doc.md` | Doc recommending lz4 — base Aligned, but Deviates under acme-bank overlay |
| `schema-evolution-review.md` | Schema evolution doc with FULL compatibility and Avro vs Protobuf comparison |

---

## Floor Model Guidelines

### `floor_model: haiku`

Use for simple, single-topic validation cases where a smaller model can correctly:
- Identify 2–3 config value deviations
- Produce a well-formed Claim Validation table
- No premise-challenge or multi-doc synthesis required
- Example: "Verify acks setting in producer config"

### `floor_model: sonnet`

Use for complex cases requiring reasoning or synthesis:
- Premise-challenge cases where implicit assumptions must be identified
- Multi-document cases where claims must be merged and contradictions detected
- Overlay differential cases requiring before/after comparison
- Example: "Review FSI latency doc for premise challenges against sub-millisecond tier"

---

## Requirement Coverage

| Requirement | Coverage |
|-------------|---------|
| REVW-01: Claim extraction >= 95% | Cases with `expected_claims_min` and specific `expected_verdict_contains` |
| REVW-02: Premise-challenge step | Cases with `premise_challenge_expected: true` and `## Premise Challenge` in `required_report_sections` |
| REVW-03: .docx output | (Phase 4 LLM eval — structural harness not tested) |
| REVW-04: Multi-document review | Cases with multiple `input_files` entries |
| REVW-05: Golden test harness >= 15 cases | This harness (16 cases) |
| REVW-06: Customer overlay end-to-end | Cases with non-null `overlay` field |

---

## Running Tests

```bash
# Structural validation only (fast, no model calls)
python3 -m pytest tests/golden/review/test_golden_review.py -v

# Specific test class
python3 -m pytest tests/golden/review/test_golden_review.py::TestGoldenReviewStructure -v
python3 -m pytest tests/golden/review/test_golden_review.py::TestFloorModelDistribution -v

# Full suite including golden harness
python3 -m pytest tests/ -x -q
```

---

## Adding Cases

1. Copy an existing case file from `cases/` as a template.
2. Name the file: `review-<topic>-<NNN>.md` (e.g., `review-bad-acks-017.md`).
3. Fill in all required YAML fields.
4. Write a descriptive markdown body explaining expected behavior.
5. Ensure all fixture paths in `input_files` exist under `fixtures/`.
6. Validate: `python3 -m pytest tests/golden/review/test_golden_review.py -v`

Naming conventions:
- `review-bad-*.md` — cases that test incorrect configurations
- `review-correct-*.md` — cases that should produce all Confirmed verdicts
- `review-fsi-*.md` — cases that exercise FSI-specific behaviors
- `review-multi-doc-*.md` — cases that exercise multi-document review
- `review-overlay-*.md` — cases that exercise customer overlay differential
- `review-schema-*.md` — cases that exercise Schema Registry patterns
