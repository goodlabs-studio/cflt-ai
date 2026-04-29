"""Unit tests for check-canon-parity.py (ACT-08)."""
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.check_canon_parity import check_parity, MODULE_TO_CANON_KEY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_yaml(path: Path, data: dict) -> Path:
    """Write a YAML file and return its path."""
    path.write_text(yaml.dump(data))
    return path


def _make_manifest(modules: list) -> dict:
    """Build a minimal MANIFEST.yaml structure with given terraform-module capability IDs."""
    capabilities = []
    for mod_id in modules:
        capabilities.append({
            "id": mod_id,
            "type": "terraform-module",
            "name": mod_id.split("/")[-1],
            "path": f"modules/{mod_id.split('/')[-1]}",
            "description": f"Test module {mod_id}",
        })
    return {"version": "1.0.0", "capabilities": capabilities}


def _make_defaults(keys: list) -> dict:
    """Build a minimal defaults.yaml with the given top-level keys."""
    return {k: {"_placeholder": True} for k in keys}


# ---------------------------------------------------------------------------
# TestCheckParity
# ---------------------------------------------------------------------------

class TestCheckParity:
    """Tests for the check_parity() function."""

    def test_no_drift_on_current_state(self):
        """Current MANIFEST and defaults should be in parity — no drift expected."""
        manifest_path = PROJECT_ROOT / "raw" / "repos" / "fsi-dsp" / "MANIFEST.yaml"
        defaults_path = PROJECT_ROOT / "canon" / "base" / "defaults.yaml"

        drift = check_parity(manifest_path, defaults_path)
        assert drift == [], (
            f"Expected no drift on current state, but got:\n" +
            "\n".join(drift)
        )

    def test_detects_missing_canon_key(self):
        """Drift detected when defaults.yaml is missing a key required by a terraform-module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            # MANIFEST has module/topic (which requires topic_design) and module/flink
            manifest_path = _write_yaml(
                tmp / "MANIFEST.yaml",
                _make_manifest(["module/topic", "module/flink"]),
            )

            # defaults.yaml only has flink_sql — topic_design is missing
            defaults_path = _write_yaml(
                tmp / "defaults.yaml",
                _make_defaults(["flink_sql", "schema_registry", "producer", "consumer"]),
            )

            drift = check_parity(manifest_path, defaults_path)

            # Must report drift for module/topic -> topic_design
            assert len(drift) >= 1
            drift_text = "\n".join(drift)
            assert "module/topic" in drift_text
            assert "[DRIFT-1]" in drift_text

    def test_parity_function_returns_list(self):
        """check_parity() always returns a list (never None or other type)."""
        manifest_path = PROJECT_ROOT / "raw" / "repos" / "fsi-dsp" / "MANIFEST.yaml"
        defaults_path = PROJECT_ROOT / "canon" / "base" / "defaults.yaml"

        result = check_parity(manifest_path, defaults_path)
        assert isinstance(result, list)

    def test_parity_with_empty_manifest(self):
        """Empty capabilities list returns no drift — no terraform-modules to check."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            # MANIFEST with no capabilities
            manifest_path = _write_yaml(
                tmp / "MANIFEST.yaml",
                {"version": "1.0.0", "capabilities": []},
            )

            defaults_path = _write_yaml(
                tmp / "defaults.yaml",
                _make_defaults(["topic_design", "flink_sql", "schema_registry"]),
            )

            drift = check_parity(manifest_path, defaults_path)

            # No terraform-modules -> no DRIFT-1 violations
            drift_1_items = [d for d in drift if "[DRIFT-1]" in d]
            assert drift_1_items == [], (
                "Empty capabilities should produce no DRIFT-1 violations"
            )

    def test_detects_both_modules_missing_canon_keys(self):
        """Both module/topic and module/flink missing from defaults.yaml are both reported."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            manifest_path = _write_yaml(
                tmp / "MANIFEST.yaml",
                _make_manifest(["module/topic", "module/flink"]),
            )

            # defaults.yaml has neither topic_design nor flink_sql
            defaults_path = _write_yaml(
                tmp / "defaults.yaml",
                _make_defaults(["schema_registry", "producer", "consumer", "security"]),
            )

            drift = check_parity(manifest_path, defaults_path)
            drift_text = "\n".join(drift)

            # Both modules should be flagged
            assert "module/topic" in drift_text
            assert "module/flink" in drift_text

    def test_missing_manifest_file_returns_drift(self):
        """Missing MANIFEST.yaml produces a drift item (not an unhandled exception)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            defaults_path = _write_yaml(
                tmp / "defaults.yaml",
                _make_defaults(["topic_design"]),
            )
            missing_manifest = tmp / "NONEXISTENT.yaml"

            drift = check_parity(missing_manifest, defaults_path)
            assert len(drift) >= 1
            assert any("not found" in d or "MANIFEST" in d for d in drift)


# ---------------------------------------------------------------------------
# TestParityScript
# ---------------------------------------------------------------------------

class TestParityScript:
    """Tests for the check-canon-parity.py script importability and module constants."""

    def test_script_importable(self):
        """from tools.check_canon_parity import check_parity works (underscore alias)."""
        # This import was already done at the top of this file — if we got here, it works.
        assert callable(check_parity)

    def test_module_to_canon_key_mapping_present(self):
        """MODULE_TO_CANON_KEY mapping exists and covers the two terraform-modules."""
        assert "module/topic" in MODULE_TO_CANON_KEY
        assert "module/flink" in MODULE_TO_CANON_KEY
        assert MODULE_TO_CANON_KEY["module/topic"] == "topic_design"
        assert MODULE_TO_CANON_KEY["module/flink"] == "flink_sql"

    def test_module_to_canon_key_values_present_in_defaults(self):
        """Every value in MODULE_TO_CANON_KEY exists as a top-level key in defaults.yaml."""
        defaults_path = PROJECT_ROOT / "canon" / "base" / "defaults.yaml"
        defaults_data = yaml.safe_load(defaults_path.read_text())
        canon_keys = set(defaults_data.keys())

        for module_id, canon_key in MODULE_TO_CANON_KEY.items():
            assert canon_key in canon_keys, (
                f"MODULE_TO_CANON_KEY['{module_id}'] = '{canon_key}' "
                f"but '{canon_key}' is not in defaults.yaml"
            )
