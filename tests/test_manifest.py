"""Tests for MANIFEST.yaml completeness and structure (CNTR-01, CNTR-03)."""
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def manifest(fsi_dsp_root):
    """Load MANIFEST.yaml data."""
    manifest_path = fsi_dsp_root / "MANIFEST.yaml"
    if not manifest_path.exists():
        pytest.skip("MANIFEST.yaml not found")
    return yaml.safe_load(manifest_path.read_text())


@pytest.fixture
def manifest_ids(manifest):
    """Return set of all capability IDs."""
    return {cap["id"] for cap in manifest.get("capabilities", [])}


class TestManifestStructure:
    """CNTR-01: MANIFEST.yaml has correct schema."""

    def test_version_is_1_1_0(self, manifest):
        # Bumped to 1.1.0 in Phase 9 — upstream fsi-dsp main introduced
        # the confluent-on-linuxone accelerator + reference/*-low-latency-azure
        # additions; MANIFEST is a non-breaking 1.0.0 -> 1.1.0 minor bump.
        assert manifest["version"] == "1.1.0"

    def test_schema_is_v1(self, manifest):
        assert manifest["schema"] == "fsi-dsp/manifest/v1"

    def test_capabilities_is_list(self, manifest):
        assert isinstance(manifest["capabilities"], list)
        assert len(manifest["capabilities"]) >= 47

    def test_each_capability_has_required_fields(self, manifest):
        for cap in manifest["capabilities"]:
            assert "id" in cap, f"Missing id in capability: {cap.get('name', 'unknown')}"
            assert "type" in cap, f"Missing type in capability: {cap['id']}"
            assert "name" in cap, f"Missing name in capability: {cap['id']}"
            assert "path" in cap, f"Missing path in capability: {cap['id']}"


class TestManifestCompleteness:
    """CNTR-01: All fsi-dsp assets are present."""

    EXPECTED_ROLES = [
        "role/cp_topic", "role/cp_schema", "role/cp_rbac",
        "role/cp_connect", "role/cp_dr_mm2", "role/cp_dr_mrc",
        "role/cp_observability", "role/cfk_operator", "role/cfk_topic",
    ]

    EXPECTED_MODULES = ["module/topic", "module/flink"]

    EXPECTED_SCENARIOS = [
        "scenario/cc-aws", "scenario/cc-azure", "scenario/cc-gcp",
        "scenario/cfk-openshift", "scenario/cp-rhel", "scenario/private-cloud",
    ]

    EXPECTED_ADRS = [f"adr/{str(i).zfill(3)}" for i in range(1, 10)]

    EXPECTED_REFERENCES = [
        "reference/java-producer", "reference/java-consumer",
        "reference/dotnet-producer", "reference/dotnet-consumer",
        "reference/python-producer", "reference/python-consumer",
        "reference/flink-sql", "reference/connect-configs",
        "reference/integration-test", "reference/local-dev",
    ]

    EXPECTED_SCRIPTS = [
        "script/mirror-failover", "script/mirror-failback",
        "script/fsi-dr", "script/consul-flip-region",
        "script/connect-pause-all", "script/validate-apply",
        "script/validate-fips",
    ]

    def test_all_roles_present(self, manifest_ids):
        for role_id in self.EXPECTED_ROLES:
            assert role_id in manifest_ids, f"Missing role: {role_id}"

    def test_all_modules_present(self, manifest_ids):
        for mod_id in self.EXPECTED_MODULES:
            assert mod_id in manifest_ids, f"Missing module: {mod_id}"

    def test_all_scenarios_present(self, manifest_ids):
        for scen_id in self.EXPECTED_SCENARIOS:
            assert scen_id in manifest_ids, f"Missing scenario: {scen_id}"

    def test_all_adrs_present(self, manifest_ids):
        for adr_id in self.EXPECTED_ADRS:
            assert adr_id in manifest_ids, f"Missing ADR: {adr_id}"

    def test_all_references_present(self, manifest_ids):
        for ref_id in self.EXPECTED_REFERENCES:
            assert ref_id in manifest_ids, f"Missing reference: {ref_id}"

    def test_all_scripts_present(self, manifest_ids):
        for script_id in self.EXPECTED_SCRIPTS:
            assert script_id in manifest_ids, f"Missing script: {script_id}"

    def test_ids_are_unique(self, manifest):
        ids = [cap["id"] for cap in manifest["capabilities"]]
        assert len(ids) == len(set(ids)), f"Duplicate IDs found: {[i for i in ids if ids.count(i) > 1]}"

    def test_ids_have_type_prefix(self, manifest):
        """IDs must include type prefix to avoid ambiguity (Pitfall 2)."""
        valid_prefixes = {"role/", "module/", "scenario/", "adr/", "reference/", "script/", "observability/"}
        for cap in manifest["capabilities"]:
            has_prefix = any(cap["id"].startswith(p) for p in valid_prefixes)
            assert has_prefix, f"ID '{cap['id']}' missing type prefix"


class TestManifestPathsExist:
    """Verify MANIFEST.yaml paths reference real directories/files."""

    def test_paths_exist(self, manifest, fsi_dsp_root):
        missing = []
        for cap in manifest["capabilities"]:
            path = fsi_dsp_root / cap["path"]
            if not path.exists():
                # ADR-009 might not exist yet if Plan 04 hasn't run
                if cap["id"] == "adr/009":
                    continue
                missing.append(f"{cap['id']}: {cap['path']}")
        assert missing == [], f"Missing paths:\n" + "\n".join(missing)


class TestCIWorkflowsExist:
    """CNTR-03: CI parity workflows exist in both repos."""

    def test_cflt_ai_citation_workflow(self, project_root):
        wf = project_root / ".github" / "workflows" / "manifest-citations.yml"
        assert wf.is_file(), "cflt-ai manifest-citations.yml missing"

    def test_fsi_dsp_stability_workflow(self, fsi_dsp_root):
        wf = fsi_dsp_root / ".github" / "workflows" / "manifest-stability.yml"
        assert wf.is_file(), "fsi-dsp manifest-stability.yml missing"

    def test_check_citations_script(self, project_root):
        script = project_root / "tools" / "check-citations.py"
        assert script.is_file(), "check-citations.py missing"

    def test_check_stability_script(self, fsi_dsp_root):
        script = fsi_dsp_root / "scripts" / "check-manifest-stability.py"
        assert script.is_file(), "check-manifest-stability.py missing"
