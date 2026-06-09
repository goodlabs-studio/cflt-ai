"""Tests for the promote/scrub tool (tools/promote-canon.py).

Verifies that promoting a client overlay into a shareable layer strips client
identifiers, rewrites source citations to TODO placeholders, generalizes guard
patterns, and never writes into canon/.
"""
import importlib.util

import pytest
import yaml


@pytest.fixture
def promote(project_root):
    """Load the hyphenated tool module by path."""
    path = project_root / "tools" / "promote-canon.py"
    spec = importlib.util.spec_from_file_location("promote_canon", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_client_name_inferred(promote):
    assert promote._client_name("customer/citi") == "citi"
    assert promote._client_name("engagement/citi-2026-payments") == "citi-2026-payments"


def test_source_keys_become_todo(promote):
    out = promote._scrub_string("override_source", "customer/citi/adr-001", ["citi"], "customer/citi")
    assert out.startswith("TODO: ADR-xxx")
    assert "citi" not in out  # placeholder is client-free


def test_scrub_redacts_client_terms_and_generalizes_guards(promote):
    source = {
        "producer": {
            "compression_type": "zstd",
            "override_source": "customer/citi/adr-001",
        },
        "environment_guard": {"pattern": "citi-prod-sandbox", "enforcement": "advisory"},
        "note": "Tuned for Citi market-data desk",
    }
    terms = ["citi", promote._client_name("customer/citi")]
    scrubbed = promote._scrub(source, terms, "customer/citi")
    dumped = yaml.safe_dump(scrubbed)

    # No client identifier survives anywhere in the promoted content.
    assert "citi" not in dumped.lower()
    # Source citation rewritten to a placeholder.
    assert scrubbed["producer"]["override_source"].startswith("TODO: ADR-xxx")
    # Guard pattern generalized: citi-*-sandbox -> <owner>-*-sandbox.
    assert scrubbed["environment_guard"]["pattern"] == "<owner>-prod-sandbox"


def test_ensure_source_flags_keys_without_adr(promote):
    fragment = {"producer": {"compression_type": "zstd"}}  # no source
    missing = promote._ensure_source(fragment, "customer/citi")
    assert "producer" in missing
    assert fragment["producer"]["override_source"].startswith("TODO: ADR-xxx")


def test_end_to_end_writes_only_to_outputs(promote, project_root, tmp_path, monkeypatch, capsys):
    """A full run writes a paste-safe candidate to outputs/promote and never to canon/."""
    client = tmp_path / "customer" / "citi"
    client.mkdir(parents=True)
    (client / "overrides.yaml").write_text(
        "producer:\n"
        '  compression_type: "zstd"\n'
        '  override_source: "customer/citi/adr-001"\n'
    )
    monkeypatch.setenv("CFLT_CANON_EXTERNAL_PATH", str(tmp_path))
    monkeypatch.setattr(
        promote.sys, "argv",
        ["promote-canon.py", "--from", "customer/citi", "--to", "industry/fsi", "--scrub", "citi"],
    )

    canon_before = sorted((project_root / "canon").rglob("*.yaml"))
    rc = promote.main()
    canon_after = sorted((project_root / "canon").rglob("*.yaml"))

    assert rc == 0
    assert canon_before == canon_after  # canon/ untouched
    candidate = project_root / "outputs" / "promote" / "customer__citi-candidate.yaml"
    assert candidate.exists()
    assert "citi" not in candidate.read_text().lower()  # whole file paste-safe
    assert "NOT READY" in capsys.readouterr().out  # TODO ADR remains
