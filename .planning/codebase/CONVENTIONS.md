# Coding Conventions

**Analysis Date:** 2026-04-28

## Naming Patterns

**Files:**
- Python scripts: lowercase with hyphens (e.g., `wiki-lint.py`, `wiki-search.py`, `fsi_governance.py`)
- Ansible task files: lowercase with hyphens (e.g., `create.yml`, `validate.yml`, `delete.yml`)
- YAML configuration: lowercase with hyphens (e.g., `sla_tiers.yml`, `naming_rules.yml`)
- Test files: `test_*.py` prefix (e.g., `test_cp_topic.py`, `test_requirements.py`, `test_governance_parity.py`)

**Functions and Variables:**
- Python: snake_case for functions and variables (e.g., `fsi_topic_name()`, `extract_tf_map()`, `_load_yaml()`)
- Python: UPPER_SNAKE_CASE for module-level constants (e.g., `DOMAIN_RE`, `REPO_ROOT`, `SLA_TIERS`)
- Python: Leading underscore for private/internal functions (e.g., `_load_yaml()`, `_REQUIRED_KEYS`, `_COMPONENT_REGEX`)
- Ansible: lowercase with underscores for variable names (e.g., `cp_admin_rest_url`, `cp_topics_dir`)
- Ansible: PascalCase for role names (e.g., `cp_topic`, `cp_schema`, `cp_rbac`)

**Classes and Modules:**
- Python test classes: PascalCase (e.g., `TestCpTopicRoleStructure`, `TestGovernanceParity`, `TestRequirements`)
- Ansible filter module: lowercase with underscores (e.g., `fsi_governance.py`)
- FilterModule class: `FilterModule` (Ansible standard)

**Type Patterns:**
- Regex patterns: Compiled at module level with `re.compile()` (e.g., `DOMAIN_RE = re.compile(r'^[a-z][a-z0-9-]{1,30}$')`)
- Dict keys: snake_case (e.g., `domain`, `application`, `entity`, `compatibility_mode`)
- Error messages: descriptive with context (e.g., "fsi_topic_name: missing required keys: domain, application")

## Code Style

**Formatting:**
- Python: 4-space indentation (PEP 8 standard)
- YAML: 2-space indentation (Ansible standard)
- No automatic formatter detected (style enforced by review)

**Linting:**
- Python: No explicit linter configuration found; relies on type hints and docstrings
- Ansible: ansible-lint enabled with `shared` profile + FQCN enforcement (see `ansible/.ansible-lint`)
- YAML: yamllint configured in CI/CD pipeline (see `.github/workflows/ansible-ci.yml`)
- Ansible-lint rules: `profile: shared` with explicit `fqcn` rule enabled, `var_naming_pattern: "^[a-z_][a-z0-9_]*$"`

**Comments and Documentation:**
- Module docstrings: Triple-quoted blocks at top of file (see `fsi_governance.py` lines 1-13)
- Function docstrings: Triple-quoted with Args, Returns, Raises sections (see `fsi_governance.py` lines 69-80, 116-128)
- Inline comments: Explain WHY, not WHAT (see `ansible/.ansible-lint` lines 4-8)
- Section separators: Full-width comment blocks with equals signs (see `ansible/vars/naming_rules.yml` lines 1-7)
- Governance markers: "MUST stay in sync" comments flag critical consistency points (see `ansible/vars/naming_rules.yml` line 5)

## Import Organization

**Python:**
- Standard library imports first (e.g., `os`, `sys`, `re`, `types`, `argparse`, `pathlib`)
- Third-party imports second (e.g., `yaml`, `pytest`)
- Local imports last (e.g., filter plugins added to `sys.path`)
- No `from __future__ import` statements detected

**Ansible:**
- Collections referenced via FQCN (Fully Qualified Collection Name): `ansible.builtin.copy`, `community.general.debug`
- Variables sourced via `include_vars` tasks (see `ansible/roles/cp_topic/tasks/main.yml`)
- No implicit imports; all module usage explicit

## Error Handling

**Python:**
- Specific exception catching: catch `AnsibleFilterError` separately from general `Exception` (see `fsi_governance.py` lines 110-113, 145-148)
- Custom errors via `AnsibleFilterError(message)` for Ansible integration (see `fsi_governance.py` line 83)
- Error messages include context: variable name, expected pattern, and actual value (see `fsi_governance.py` lines 99-102)
- Nested try blocks to preserve original exception type before re-raising (see `fsi_governance.py` line 113: `raise AnsibleFilterError("fsi_topic_name: %s" % to_native(e))`)
- Type checking before processing (see `fsi_governance.py` line 82: `isinstance(topic_def, dict)`)

**Test Assertions:**
- pytest-style assertions with descriptive messages (see `test_governance_parity.py` lines 73-74, 124-126)
- Custom extraction helpers handle parsing failures gracefully (see `test_governance_parity.py` lines 29-56)
- Fixture-based setup with `@pytest.fixture(autouse=True)` for data initialization (see `test_requirements.py` lines 23-25, `test_governance_parity.py` lines 62-67)

## Logging

**Framework:** No structured logging framework detected; uses simple stdout/stderr

**Patterns:**
- Python print statements for normal output (see `wiki-search.py` lines 74-76)
- stdout for success messages, stderr for errors (see `wiki-lint.py` line 112: `print("✓ Wiki looks clean.")`)
- Test output: pytest captures and displays assertions automatically
- Ansible: uses standard `debug` module for output (referenced in workflow but not shown in samples)

## Comments

**When to Comment:**
- Explain non-obvious governance constraints (see `ansible/vars/naming_rules.yml` lines 4-6: "Source of truth" and "MUST stay in sync")
- Document regex pattern rationale in YAML (see `ansible/vars/naming_rules.yml` lines 11-21: each pattern has description)
- Mark critical consistency points that are enforced across multiple files (see `ansible/filter_plugins/fsi_governance.py` lines 20-21, 37-38)

**Comment Style:**
- Inline YAML: Use `#` with space (see `ansible/vars/naming_rules.yml`)
- Python: Use `#` with space, or `"""` for docstrings
- Block comments: Full-width separator lines (80 characters) for major sections (see `fsi_governance.py` lines 20-22, 36-38)

**JSDoc/Type Hints:**
- Python docstrings follow NumPy style: Args, Returns, Raises sections (see `fsi_governance.py` lines 69-80)
- Type hints not used in function signatures; validation happens at runtime
- Ansible: No type hints used; type validation in `validate()` blocks within role tasks

## Function Design

**Size:**
- Small focused functions: 30-50 lines preferred (e.g., `fsi_topic_name()` is 30 lines)
- Single responsibility: One function = one validation or one transformation (see `fsi_governance.py`)

**Parameters:**
- Minimal parameters: Usually 1-2 arguments (see `fsi_topic_name(topic_def)`, `fsi_sla_lookup(tier, prop)`)
- Dict-based config: Prefer passing structured dict over multiple parameters (see `fsi_topic_name(topic_def: dict)`)
- Required parameters validated immediately (see `fsi_governance.py` lines 87-92)

**Return Values:**
- Return primitive types when possible: str, int, bool, dict
- Raise exceptions on validation failure rather than returning sentinel values
- Example: `fsi_topic_name()` returns assembled string or raises `AnsibleFilterError`

## Module Design

**Python Script Organization:**
- Utility functions prefixed with underscore (e.g., `_load_yaml()`, `_read_text()`)
- Filter/mapping functions as public module-level functions (e.g., `fsi_topic_name()`)
- Constants at module top level (e.g., `SLA_TIERS`, `REPO_ROOT`, compiled regex patterns)
- Main entry point in `if __name__ == "__main__":` block (see `wiki-lint.py` line 131-132)

**Ansible Filter Module:**
- Single filter module per domain (e.g., `fsi_governance.py` for FSI domain)
- `FilterModule` class required with `filters()` method returning dict mapping filter names to functions (see `fsi_governance.py` near end, not shown in excerpt but standard pattern)
- Constants and helper functions at module level
- No class-based filter logic; functions passed to `FilterModule.filters()`

**Test Module Organization:**
- Group related tests in classes: `TestCpTopicRoleStructure`, `TestCpTopicMolecule`, `TestCpTopicGovernanceWiring`
- Use `@pytest.fixture` for shared setup (see `test_requirements.py` lines 23-25)
- Use module-level helper functions for file I/O (`_load_yaml()`, `_read_text()`, `load_yaml()`, `load_text()`)
- No class inheritance; inherit from `object` implicitly
- One test class per logical domain (role structure, molecule config, governance wiring, API wiring, etc.)

## Shutdown and Lifecycle

**Not applicable** — codebase is primarily Ansible playbooks, Python utilities, and test scripts. No long-running services require graceful shutdown logic.

## Cross-Cutting Concerns

**Validation:**
- Regex-based: Compiled at module level, referenced in validation functions
- Early validation: Check types and required keys before processing (see `fsi_governance.py` lines 82-92)
- Consistent error messages: Include expected pattern and actual value for regex failures
- Re-used patterns: Same regex patterns defined in both `fsi_governance.py` and `ansible/vars/naming_rules.yml` with CI enforcement to keep them in sync (see `test_governance_parity.py`)

**Configuration:**
- Environment variables: `CFLT_WIKI_ROOT` overrides default wiki path (see `wiki-lint.py` lines 15-17)
- Fallback logic: Walk up directory tree to find `wiki/` if env var not set
- Config files: `.ansible-lint`, `ansible.cfg` define Ansible-specific settings
- Default values: `ansible/vars/defaults/` contains role defaults (referenced in tests)

**Secrets/Credentials:**
- Never logged or printed (see `ansible/.ansible-lint` doesn't expose credential vars)
- Passed via environment variables or Ansible vault (referenced in comments but not shown in code)
- Test fixtures use mock/dummy values, not real credentials

**Testing:**
- Unit tests: Validate individual functions in isolation (e.g., `test_fsi_topic_name`, `test_sla_tier_*`)
- Integration/parity tests: Validate consistency across files (e.g., `test_governance_parity.py`)
- Role tests: Molecule framework for full Ansible role validation (see `.github/workflows/ansible-ci.yml` lines 42-75)
- File structure tests: Validate files exist and contain expected keys/sections (see `test_cp_topic.py` lines 35-73)

---

*Convention analysis: 2026-04-28*
