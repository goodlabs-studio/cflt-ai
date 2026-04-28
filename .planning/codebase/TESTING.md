# Testing Patterns

**Analysis Date:** 2026-04-28

## Test Framework

**Runner:**
- pytest (Python test framework)
- Version: No pinned version in pyproject.toml or setup.py (installed via `pip install pytest`)
- Configuration: No pytest.ini or setup.cfg found; defaults apply
- See: `.github/workflows/ansible-ci.yml` line 70

**Assertion Library:**
- pytest built-in assertions (no external library needed)
- Plain `assert` statements with optional messages (see `test_requirements.py` lines 42-43)

**Molecule Framework:**
- Molecule for Ansible role testing (not pure pytest, but uses pytest internally)
- Delegated driver (no Docker provisioning in CI)
- Version: Installed via `pip install molecule` in CI

**Run Commands:**
```bash
# Run all tests for a role via Molecule
molecule test
working-directory: ansible/roles/{role_name}

# Run governance parity tests
pytest tests/ansible/test_governance_parity.py -v

# Run requirements tests
pytest tests/ansible/test_requirements.py -v

# Run role structure tests
pytest tests/ansible/test_cp_topic.py -v

# Install test dependencies
pip install pytest pyyaml
pip install ansible-core molecule
ansible-galaxy collection install -r ansible/requirements.yml
```

## Test File Organization

**Location:**
- Python unit/integration tests: `tests/ansible/test_*.py` (co-located with FSI-DSP root)
- Molecule scenario tests: `ansible/roles/{role}/molecule/default/` (per role)
- Test fixtures: `tests/ansible/fixtures/` (mock responses, sample data)

**Naming:**
- Test files: `test_*.py` (pytest discovery pattern)
- Test classes: `Test*` (e.g., `TestCpTopicRoleStructure`, `TestGovernanceParity`)
- Test methods: `test_*` (e.g., `test_defaults_exist`, `test_sla_tier_compatibility_matches_terraform`)
- Helper functions: `_function_name()` (e.g., `_load_yaml()`, `_read_text()`)

**Structure:**
```
tests/
├── ansible/
│   ├── conftest.py                          # pytest configuration and shared fixtures
│   ├── test_cp_topic.py                     # Tests for cp_topic role structure, molecule config
│   ├── test_cp_schema.py                    # Tests for cp_schema role
│   ├── test_governance_parity.py            # Tests for Ansible/Terraform constant consistency
│   ├── test_requirements.py                 # Tests for ansible/requirements.yml validity
│   ├── test_fsi_governance_filter.py        # Tests for fsi_governance filter plugin
│   └── fixtures/
│       ├── cptopic_samples/                 # Sample topic YAML definitions
│       │   ├── corebanking-account-txn.yml
│       │   └── compliance-screening-result.yml
│       └── mock_responses/                  # Mocked API responses
│           ├── schema_registry/
│           │   ├── schema_registered.json
│           │   └── schema_incompatible.json
│           ├── admin_rest_v3/               # Admin REST v3 API responses
│           └── connect/                     # Kafka Connect API responses
```

## Test Structure

**Suite Organization:**

Test classes group related tests by concern:

```python
# From test_cp_topic.py
class TestCpTopicRoleStructure:
    """Verify cp_topic role directory structure and defaults."""
    def test_defaults_exist(self): ...
    def test_meta_exist(self): ...
    def test_task_files_exist(self): ...

class TestCpTopicMolecule:
    """Verify molecule scenario files."""
    def test_molecule_uses_delegated_driver(self): ...
    def test_molecule_no_managed_hosts(self): ...

class TestCpTopicGovernanceWiring:
    """Verify governance filters and constants are wired in task files."""
    def test_main_loads_sla_tiers(self): ...
    def test_validate_uses_fsi_validate_topic_name(self): ...
    def test_sla_tier_derivation(self): ...
```

**Patterns:**
- No setup/teardown methods; fixtures use `@pytest.fixture(autouse=True)` for shared initialization
- Initialization in fixture `setup()` method (see `test_requirements.py` lines 23-25):
  ```python
  @pytest.fixture(autouse=True)
  def setup(self):
      self.reqs = load_yaml('ansible/requirements.yml')
  ```
- Instance variables set in fixture for use in all test methods (see `test_governance_parity.py` lines 62-67)
- No explicit teardown; files are read-only, no cleanup needed

## Mocking

**Framework:** No external mocking library detected (unittest.mock not imported)

**Patterns:**
- Manual mock module creation via `types.ModuleType()` for missing Ansible modules (see `test_fsi_governance_filter.py` lines 16-43)
- Example: Mock `ansible.errors.AnsibleFilterError` when Ansible not installed:
  ```python
  try:
      from ansible.errors import AnsibleFilterError
  except ImportError:
      ansible_mod = types.ModuleType('ansible')
      errors_mod = types.ModuleType('ansible.errors')
      class AnsibleFilterError(Exception):
          pass
      errors_mod.AnsibleFilterError = AnsibleFilterError
      sys.modules['ansible'] = ansible_mod
      sys.modules['ansible.errors'] = errors_mod
  ```

**Fixture Data:**
- JSON files in `tests/ansible/fixtures/mock_responses/` represent API responses (schema_registered.json, connector_status_running.json, etc.)
- YAML files in `tests/ansible/fixtures/cptopic_samples/` contain sample topic definitions
- Loaded via `_load_yaml()` or `_read_text()` helper functions

**What to Mock:**
- External API responses: Admin REST v3, Schema Registry (in fixture files, not in test code)
- Ansible modules when running tests outside Ansible environment

**What NOT to Mock:**
- File system operations: Tests read actual YAML/JSON files
- Regex patterns: Tests validate actual patterns from source
- Dictionary lookups: Tests use real SLA_TIERS and governance constants

## Fixtures and Factories

**Test Data:**

Loaded via helper functions at module level:

```python
def _load_yaml(path):
    """Load and parse a YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)

def _read_text(path):
    """Read file as raw text."""
    with open(path) as f:
        return f.read()

def load_yaml(relpath):
    """Load a YAML file relative to the repo root."""
    with open(os.path.join(REPO_ROOT, relpath)) as f:
        return yaml.safe_load(f)
```

**Location:**
- Governance constants: `tests/ansible/fixtures/` (but more commonly loaded from actual source files)
- Sample topic definitions: `tests/ansible/fixtures/cptopic_samples/*.yml`
- Mock API responses: `tests/ansible/fixtures/mock_responses/{domain}/*.json`

**Factory Pattern:**
- No factory classes; tests load pre-existing YAML/JSON files
- Example: `test_governance_parity.py` loads `ansible/vars/sla_tiers.yml` and `modules/topic/main.tf` as fixtures

## Coverage

**Requirements:** No explicit coverage target found; coverage not enforced in CI

**View Coverage:**
No coverage reporting configured. Add via:
```bash
pytest --cov=ansible/filter_plugins --cov-report=term-missing tests/ansible/
```

## Test Types

**Unit Tests:**
- Scope: Individual functions and role structure
- Approach: Load YAML/JSON, call function, assert output
- Examples:
  - `test_fsi_topic_name()`: Test topic name assembly from dict
  - `test_defaults_exist()`: Verify role has defaults/main.yml
  - `test_validate_topic_name()`: Test topic name validation regex

**Integration Tests:**
- Scope: Cross-component consistency (Ansible ↔ Terraform)
- Approach: Parse files, extract constants, compare for parity
- Examples:
  - `test_governance_parity.py`: Compare SLA tiers and naming regexes across Ansible YAML and Terraform HCL
  - `test_sla_tier_derivation()`: Load YAML and verify all tiers present with correct values

**End-to-End / Molecule Tests:**
- Scope: Full Ansible role execution in isolated environment
- Framework: Molecule with delegated driver
- Approach: Converge role, verify idempotency, run check mode
- Execution: `molecule test` in `ansible/roles/{role}/`
- Stages:
  1. Lint: yamllint, ansible-lint
  2. Destroy: Clean previous test state
  3. Create: Set up test instance (delegated driver = localhost)
  4. Converge: Run playbook/role
  5. Idempotency: Re-run, verify no changes reported
  6. Verify: Run verify.yml assertions
  7. Destroy: Clean up

## Common Patterns

**File Path Resolution:**

Tests compute `REPO_ROOT` once at module load, use for relative path lookups:

```python
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Assuming test file: tests/ansible/test_x.py
# REPO_ROOT = /path/to/fsi-dsp
```

**Parsing YAML/JSON:**

Use `yaml.safe_load()` to parse files, handle errors gracefully:

```python
def load_yaml(relpath):
    """Load a YAML file relative to the repo root."""
    with open(os.path.join(REPO_ROOT, relpath)) as f:
        return yaml.safe_load(f)
```

**Regex Extraction from Source Files:**

Parse Terraform/YAML source with regex to verify constants match:

```python
def extract_tf_map(text, map_name):
    """Extract a Terraform map block: name = { key = value ... }"""
    pattern = rf'{map_name}\s*=\s*\{{([\s\S]*?)\}}'
    match = re.search(pattern, text)
    if not match:
        return {}
    # ... parse and return dict
```

**Error/Exception Testing:**

Filters raise `AnsibleFilterError` on invalid input. Test by expecting exception:

```python
def test_invalid_topic_def_raises(self):
    with pytest.raises(AnsibleFilterError, match="missing required keys"):
        fsi_topic_name({})  # Missing domain, application, etc.
```

**Async Testing:**

Not applicable — no async code in codebase.

**Fixture-Based Setup:**

Use `@pytest.fixture(autouse=True)` to initialize test data once per class:

```python
@pytest.fixture(autouse=True)
def setup(self):
    self.sla_tiers = load_yaml('ansible/vars/sla_tiers.yml')
    self.naming_rules = load_yaml('ansible/vars/naming_rules.yml')
    self.main_tf = load_text('modules/topic/main.tf')
```

All test methods in the class can then access `self.sla_tiers`, etc.

## CI/CD Integration

**Workflow:** `.github/workflows/ansible-ci.yml`

**Jobs:**
1. **Lint** (runs first, fast feedback):
   - yamllint on `ansible/` directory
   - ansible-lint with shared profile + FQCN enforcement

2. **Molecule** (runs after lint, per-role matrix):
   - Matrix over roles: cp_topic, cp_schema, cp_rbac, cp_connect, cp_observability, cfk_operator, cfk_topic, cp_dr_mm2, cp_dr_mrc
   - Each role: `molecule test` in its directory
   - Dependencies: ansible-core, molecule, pytest, pyyaml, ansible collections

3. **Governance Parity** (independent):
   - Single pytest command: `pytest tests/ansible/test_governance_parity.py -v`
   - Validates Ansible YAML constants match Terraform HCL values
   - Prevents drift between IaC implementations

**Triggers:**
- Pull request with changes to `ansible/**` or `tests/ansible/**` paths

---

*Testing analysis: 2026-04-28*
