---
phase: 03A-act-rail-plan
plan: 03
type: execute
wave: 3
depends_on: ["03A-01", "03A-02"]
files_modified:
  - tests/golden/act/__init__.py
  - tests/golden/act/test_golden_act.py
  - tests/golden/act/cases/topic-trade-events-001.md
  - tests/golden/act/cases/negative-mongodb-019.md
autonomous: true
requirements:
  - ACT-05
  - ACT-07

must_haves:
  truths:
    - "Golden harness directory exists with >= 20 case files including >= 3 negative-space"
    - "Structural pytest runner validates all case files have required fields"
    - "Negative-space cases enforce no inline Terraform in expected output"
    - "All golden cases pass structural validation at >= 95% rate"
  artifacts:
    - path: "tests/golden/act/test_golden_act.py"
      provides: "Structural golden harness runner mirroring test_golden_ask.py"
      contains: "TestGoldenActHarnessStructure"
      min_lines: 60
    - path: "tests/golden/act/__init__.py"
      provides: "Package marker"
    - path: "tests/golden/act/cases/"
      provides: ">= 20 golden case .md files with YAML frontmatter"
  key_links:
    - from: "tests/golden/act/test_golden_act.py"
      to: "tests/golden/act/cases/"
      via: "glob for *.md case files"
      pattern: "CASES_DIR.glob"
    - from: "tests/golden/act/cases/*.md"
      to: "raw/repos/fsi-dsp/MANIFEST.yaml"
      via: "expected_artifact references MANIFEST capability IDs"
      pattern: "module/topic"
---

<objective>
Build the golden test harness for the act rail with >= 20 structural cases (including negative-space cases) and a parametrized pytest runner that validates case file structure and distribution.

Purpose: Provides the structural correctness measurement (ACT-07 >= 95%) and ensures comprehensive coverage of artifact selection, gate validation, and negative-space scenarios (ACT-05).
Output: tests/golden/act/ directory with runner, __init__.py, and 20+ case files.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/03A-act-rail-plan/03A-CONTEXT.md
@.planning/phases/03A-act-rail-plan/03A-RESEARCH.md
@.planning/phases/03A-act-rail-plan/03A-01-SUMMARY.md
@.planning/phases/03A-act-rail-plan/03A-02-SUMMARY.md

<interfaces>
<!-- From Plan 01 gate chain -->
From tools/act_gates.py:
```python
GATE_NAMES = ["canon_compliance", "fsi_dsp_coverage", "confluent_docs_schema", "mcp_confluent_state"]
# GateResult: {gate: str, status: pass|fail|skipped, detail: str, evidence: list}
```

<!-- Golden harness pattern from existing harnesses -->
From tests/golden/ask/test_golden_ask.py:
```python
CASES_DIR = Path(__file__).parent / "cases"
REQUIRED_FIELDS = {"id", "query", "expected_route", "floor_model", "tags", "required_claims", "forbidden_claims"}

def load_case(path: Path) -> dict:
    content = path.read_text()
    if not content.startswith("---"): return {}
    end = content.find("---", 3)
    if end == -1: return {}
    return yaml.safe_load(content[3:end]) or {}

ALL_CASES = sorted(CASES_DIR.glob("*.md")) if CASES_DIR.exists() else []

class TestGoldenHarnessStructure:
    def test_minimum_case_count(self): assert len(ALL_CASES) >= 30
    def test_minimum_negative_space_cases(self): ...
    @pytest.mark.parametrize("case_path", ALL_CASES, ids=lambda p: p.stem)
    def test_case_has_required_fields(self, case_path): ...
```

<!-- MANIFEST artifact IDs for case authoring -->
Terraform modules: module/topic, module/flink
Ansible roles: role/cp_topic, role/cp_schema, role/cp_rbac, role/cp_connect, role/cp_dr_mm2, role/cp_dr_mrc, role/cp_observability, role/cfk_operator, role/cfk_topic
Scenarios: scenario/cc-aws, scenario/cc-azure, scenario/cc-gcp, scenario/cfk-openshift, scenario/cp-rhel, scenario/private-cloud
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create golden harness runner and package marker</name>
  <files>tests/golden/act/__init__.py, tests/golden/act/test_golden_act.py</files>
  <read_first>
    - tests/golden/ask/test_golden_ask.py (exact pattern to mirror -- load_case, ALL_CASES, REQUIRED_FIELDS, parametrize, TestGoldenHarnessStructure, TestFloorModelDistribution)
    - tests/golden/review/test_golden_review.py (second example of same pattern -- different REQUIRED_FIELDS)
  </read_first>
  <action>
1. Create tests/golden/act/__init__.py as empty file (package marker).

2. Create tests/golden/act/test_golden_act.py mirroring test_golden_ask.py structure exactly.

Module-level constants:
- CASES_DIR = Path(__file__).parent / "cases"
- REQUIRED_FIELDS = {"id", "request", "expected_artifact", "floor_model", "tags", "required_claims", "forbidden_claims", "negative_space"}
- VALID_FLOOR_MODELS = {"haiku", "sonnet"}
- VALID_ARTIFACT_TYPES = {"module/topic", "module/flink", "role/cp_topic", "role/cp_schema", "role/cp_rbac", "role/cp_connect", "role/cp_dr_mm2", "role/cp_dr_mrc", "role/cp_observability", "role/cfk_operator", "role/cfk_topic", "scenario/cc-aws", "scenario/cc-azure", "scenario/cc-gcp", "scenario/cfk-openshift", "scenario/cp-rhel", "scenario/private-cloud", None}

load_case function: identical to test_golden_ask.py -- parse YAML front matter between first two "---" delimiters.

ALL_CASES = sorted(CASES_DIR.glob("*.md")) if CASES_DIR.exists() else []

class TestGoldenActHarnessStructure (ACT-05):
- test_cases_directory_exists: CASES_DIR.exists()
- test_minimum_case_count: len(ALL_CASES) >= 20
- test_minimum_negative_space_cases: cases with negative_space=true >= 3
- test_terraform_module_cases_exist: at least 2 cases with expected_artifact starting with "module/"
- test_ansible_role_cases_exist: at least 2 cases with expected_artifact starting with "role/"
- test_case_id_unique: no duplicate IDs across all cases
- @parametrize test_case_has_required_fields: each case has all REQUIRED_FIELDS
- @parametrize test_case_has_valid_floor_model: floor_model in VALID_FLOOR_MODELS
- @parametrize test_required_claims_is_list: required_claims is a list
- @parametrize test_forbidden_claims_is_list: forbidden_claims is a list
- @parametrize test_negative_space_has_null_artifact: if negative_space is true, expected_artifact must be null (None)
- @parametrize test_positive_case_has_valid_artifact: if negative_space is false, expected_artifact in VALID_ARTIFACT_TYPES

class TestNegativeSpaceCoverage (ACT-06):
- test_negative_cases_forbid_inline_terraform: all negative_space=true cases include a string containing 'resource "confluent_' in their forbidden_claims list
- test_negative_cases_require_no_match_response: all negative_space=true cases include "no matching artifact" in their required_claims list

class TestFloorModelDistribution (ACT-07):
- test_haiku_cases_exist: >= 5 haiku-floor cases
- test_sonnet_cases_exist: >= 5 sonnet-floor cases
  </action>
  <verify>
    <automated>python3 -c "import ast; tree=ast.parse(open('tests/golden/act/test_golden_act.py').read()); classes=[n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]; assert 'TestGoldenActHarnessStructure' in classes; print('OK: harness runner valid')"</automated>
  </verify>
  <acceptance_criteria>
    - tests/golden/act/__init__.py exists (can be empty)
    - tests/golden/act/test_golden_act.py contains class TestGoldenActHarnessStructure
    - tests/golden/act/test_golden_act.py contains class TestNegativeSpaceCoverage
    - tests/golden/act/test_golden_act.py contains class TestFloorModelDistribution
    - tests/golden/act/test_golden_act.py contains REQUIRED_FIELDS with all 8 field names
    - tests/golden/act/test_golden_act.py contains def load_case function
    - tests/golden/act/test_golden_act.py contains ALL_CASES = sorted(CASES_DIR.glob("*.md"))
    - test_minimum_case_count asserts >= 20
    - test_minimum_negative_space_cases asserts >= 3
  </acceptance_criteria>
  <done>Golden harness runner mirrors ask/review harness exactly. Structural tests cover case count, field validation, negative-space enforcement, artifact type validation, and floor model distribution.</done>
</task>

<task type="auto">
  <name>Task 2: Author 22 golden cases (including 4 negative-space)</name>
  <files>tests/golden/act/cases/</files>
  <read_first>
    - tests/golden/ask/cases/deep-dr-architecture-001.md (example golden case file format -- YAML frontmatter between triple-dash delimiters, then body)
    - raw/repos/fsi-dsp/MANIFEST.yaml (all capability IDs and descriptions -- needed for expected_artifact values)
    - canon/base/defaults.yaml (canon config keys -- needed for compliance-related cases)
    - canon/industry/fsi/overrides.yaml (FSI overrides -- needed for overlay cases)
    - tests/golden/act/test_golden_act.py (REQUIRED_FIELDS -- case frontmatter must match exactly)
  </read_first>
  <action>
Create 22 golden case files in tests/golden/act/cases/ directory. Each case is a .md file with YAML frontmatter (between triple-dash delimiters) matching REQUIRED_FIELDS: id, request, expected_artifact, floor_model, tags, required_claims, forbidden_claims, negative_space. After the closing triple-dash, include a "## Context" section with a brief description.

Case naming convention: {category}-{slug}-{NNN}.md

TERRAFORM MODULE CASES (6 cases targeting module/* artifacts):

1. topic-trade-events-001.md -- request: "create a topic for trade events with replication and DR", expected_artifact: "module/topic", floor_model: sonnet, tags: [topic, terraform, dr, fsi], required_claims: ["module/topic", "confluent_kafka_topic"], forbidden_claims: ['resource "confluent_kafka_topic"'], negative_space: false
2. topic-market-data-002.md -- request: "provision a high-throughput topic for market data feed", expected_artifact: "module/topic", floor_model: sonnet, tags: [topic, terraform, market-data], required_claims: ["module/topic"], forbidden_claims: ['resource "confluent_'], negative_space: false
3. topic-compliance-audit-003.md -- request: "create a compliance audit topic with 7-year retention", expected_artifact: "module/topic", floor_model: haiku, tags: [topic, terraform, compliance], required_claims: ["module/topic", "retention"], forbidden_claims: ['resource "confluent_'], negative_space: false
4. flink-stream-processing-004.md -- request: "set up a Flink compute pool for trade enrichment", expected_artifact: "module/flink", floor_model: sonnet, tags: [flink, terraform, processing], required_claims: ["module/flink"], forbidden_claims: ['resource "confluent_flink'], negative_space: false
5. flink-cdc-pipeline-005.md -- request: "provision Flink SQL for CDC processing from Oracle", expected_artifact: "module/flink", floor_model: haiku, tags: [flink, terraform, cdc], required_claims: ["module/flink", "CDC"], forbidden_claims: ['resource "confluent_'], negative_space: false
6. topic-with-schema-006.md -- request: "create a governed topic with Avro schema and RBAC bindings", expected_artifact: "module/topic", floor_model: sonnet, tags: [topic, terraform, schema, rbac], required_claims: ["module/topic", "schema", "RBAC"], forbidden_claims: ['resource "confluent_'], negative_space: false

ANSIBLE ROLE CASES (5 cases targeting role/* artifacts):

7. role-cp-topic-007.md -- request: "configure a topic on Confluent Platform on RHEL", expected_artifact: "role/cp_topic", floor_model: haiku, tags: [topic, ansible, cp], required_claims: ["role/cp_topic"], forbidden_claims: ['resource "confluent_'], negative_space: false
8. role-schema-registry-008.md -- request: "register Avro schemas in Schema Registry on-prem", expected_artifact: "role/cp_schema", floor_model: haiku, tags: [schema, ansible, cp], required_claims: ["role/cp_schema"], forbidden_claims: ['resource "confluent_'], negative_space: false
9. role-rbac-bindings-009.md -- request: "provision RBAC role bindings for the trading team", expected_artifact: "role/cp_rbac", floor_model: haiku, tags: [rbac, ansible, security], required_claims: ["role/cp_rbac"], forbidden_claims: ['resource "confluent_'], negative_space: false
10. role-connect-workers-010.md -- request: "deploy Kafka Connect distributed workers", expected_artifact: "role/cp_connect", floor_model: sonnet, tags: [connect, ansible, cp], required_claims: ["role/cp_connect"], forbidden_claims: ['resource "confluent_'], negative_space: false
11. role-dr-mirrormaker-011.md -- request: "configure MirrorMaker 2 for cross-DC replication", expected_artifact: "role/cp_dr_mm2", floor_model: sonnet, tags: [dr, ansible, mirrormaker], required_claims: ["role/cp_dr_mm2"], forbidden_claims: ['resource "confluent_'], negative_space: false

SCENARIO CASES (3 cases targeting scenario/* artifacts):

12. scenario-cc-aws-012.md -- request: "stand up a Confluent Cloud starter kit on AWS", expected_artifact: "scenario/cc-aws", floor_model: haiku, tags: [scenario, aws, cloud], required_claims: ["scenario/cc-aws"], forbidden_claims: ['resource "confluent_'], negative_space: false
13. scenario-cfk-openshift-013.md -- request: "deploy Confluent for Kubernetes on OpenShift", expected_artifact: "scenario/cfk-openshift", floor_model: sonnet, tags: [scenario, kubernetes, openshift], required_claims: ["scenario/cfk-openshift"], forbidden_claims: ['resource "confluent_'], negative_space: false
14. scenario-cp-rhel-014.md -- request: "set up Confluent Platform on RHEL bare metal", expected_artifact: "scenario/cp-rhel", floor_model: haiku, tags: [scenario, rhel, on-prem], required_claims: ["scenario/cp-rhel"], forbidden_claims: ['resource "confluent_'], negative_space: false

OVERLAY CASES (2 cases testing --overlay behavior):

15. overlay-acme-topic-015.md -- request: "create a topic for trade events --overlay acme-bank", expected_artifact: "module/topic", floor_model: sonnet, tags: [topic, overlay, fsi], required_claims: ["module/topic", "acme-bank"], forbidden_claims: ['resource "confluent_'], negative_space: false
16. overlay-fsi-latency-016.md -- request: "provision a market data topic meeting sub-millisecond SLA", expected_artifact: "module/topic", floor_model: sonnet, tags: [topic, fsi, latency], required_claims: ["module/topic", "sub-millisecond"], forbidden_claims: ['resource "confluent_'], negative_space: false

GATE BYPASS CASES (2 cases testing --gate-bypass behavior):

17. bypass-gate4-017.md -- request: "create a topic --gate-bypass mcp_confluent_state", expected_artifact: "module/topic", floor_model: haiku, tags: [topic, bypass, dev-mode], required_claims: ["module/topic", "skipped"], forbidden_claims: ['resource "confluent_'], negative_space: false
18. bypass-gate3-018.md -- request: "set up Flink pool --gate-bypass confluent_docs_schema", expected_artifact: "module/flink", floor_model: haiku, tags: [flink, bypass, dev-mode], required_claims: ["module/flink", "skipped"], forbidden_claims: ['resource "confluent_'], negative_space: false

NEGATIVE-SPACE CASES (4 cases -- no artifact match, negative_space: true):

19. negative-mongodb-019.md -- request: "provision a MongoDB Atlas cluster with Kafka CDC", expected_artifact: null, floor_model: haiku, tags: [negative-space, out-of-scope], required_claims: ["no matching artifact", "PR proposal"], forbidden_claims: ['resource "confluent_', 'module "confluent_'], negative_space: true
20. negative-inline-terraform-020.md -- request: "write me a Terraform resource block for a Kafka topic", expected_artifact: null, floor_model: haiku, tags: [negative-space, inline-terraform], required_claims: ["no matching artifact"], forbidden_claims: ['resource "confluent_kafka_topic"', 'resource "confluent_'], negative_space: true
21. negative-write-tool-021.md -- request: "create a new Kafka cluster using mcp-confluent", expected_artifact: null, floor_model: sonnet, tags: [negative-space, write-tool], required_claims: ["no matching artifact"], forbidden_claims: ["create_kafka_cluster", 'resource "confluent_'], negative_space: true
22. negative-redis-cache-022.md -- request: "set up a Redis cache cluster with Kafka Streams state store", expected_artifact: null, floor_model: haiku, tags: [negative-space, out-of-scope], required_claims: ["no matching artifact", "PR proposal"], forbidden_claims: ['resource "confluent_'], negative_space: true

VALIDATION CHECKLIST:
- All 22 files have all 8 REQUIRED_FIELDS
- IDs are globally unique
- 4 negative_space: true cases (>= 3 required)
- All negative_space cases have expected_artifact: null
- All negative_space cases include a string containing 'resource "confluent_' in forbidden_claims
- All negative_space cases include "no matching artifact" in required_claims
- Floor model distribution: 10 haiku, 12 sonnet (both >= 5)
  </action>
  <verify>
    <automated>python3 -m pytest tests/golden/act/test_golden_act.py -v --tb=short -q</automated>
  </verify>
  <acceptance_criteria>
    - tests/golden/act/cases/ directory contains >= 20 .md files
    - Each .md file starts with YAML frontmatter delimiters
    - All REQUIRED_FIELDS present in every case (verified by parametrize test)
    - At least 4 cases have negative_space: true
    - At least 2 cases have expected_artifact starting with "module/"
    - At least 2 cases have expected_artifact starting with "role/"
    - All negative_space cases have expected_artifact: null
    - python3 -m pytest tests/golden/act/test_golden_act.py -v --tb=short exits 0 with all tests passing
    - No duplicate case IDs
  </acceptance_criteria>
  <done>Golden harness contains 22 cases (4 negative-space), all passing structural validation. Structural correctness baseline >= 95% (ACT-07). Negative-space cases enforce ACT-06 no-inline-Terraform constraint. Distribution covers terraform-modules, ansible-roles, scenarios, overlays, gate-bypass, and out-of-scope requests.</done>
</task>

</tasks>

<verification>
- `python3 -m pytest tests/golden/act/ -v --tb=short -q` all green
- `python3 -m pytest tests/golden/act/test_golden_act.py::TestGoldenActHarnessStructure::test_minimum_case_count` passes
- `python3 -m pytest tests/golden/act/test_golden_act.py::TestGoldenActHarnessStructure::test_minimum_negative_space_cases` passes
- `python3 -m pytest tests/golden/act/test_golden_act.py::TestNegativeSpaceCoverage` passes
</verification>

<success_criteria>
- >= 20 golden cases exist with valid structure (ACT-05)
- >= 3 negative-space cases enforce no inline Terraform (ACT-05, ACT-06)
- All structural tests pass (ACT-07 >= 95% baseline)
- Floor model distribution covers both haiku and sonnet (ACT-07)
</success_criteria>

<output>
After completion, create `.planning/phases/03A-act-rail-plan/03A-03-SUMMARY.md`
</output>
