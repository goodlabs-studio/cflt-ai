"""
Regression tests for wiki tool bug fixes (HYG-01 through HYG-04).
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# HYG-01: wiki-stats.py Unicode syntax error
# ---------------------------------------------------------------------------

def test_wiki_stats_no_syntax_error(project_root):
    """wiki-stats.py must run to completion without crashing."""
    result = subprocess.run(
        [sys.executable, str(project_root / "tools" / "wiki-stats.py")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"wiki-stats.py exited {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "Articles:" in result.stdout, "Expected 'Articles:' in wiki-stats output"


def test_wiki_stats_no_unicode_box_drawing(project_root):
    """wiki-stats.py must not contain invalid Unicode box-drawing multiplication."""
    source = (project_root / "tools" / "wiki-stats.py").read_text()
    # The broken pattern uses U+2500 (─) directly in an f-string expression
    assert "\u2500*50" not in source, "Found invalid Unicode box-drawing pattern {─*50}"
    assert "'-' * 50" in source, "Expected ASCII hyphen pattern {'-' * 50} not found"


# ---------------------------------------------------------------------------
# HYG-02: wiki-lint.py broken-link regex anchor handling
# ---------------------------------------------------------------------------

def test_wiki_lint_anchor_regex():
    """Regex used in wiki-lint.py must correctly handle fragment identifiers."""
    pattern = r"\[.*?\]\((wiki/[^)#]+(?:#[^)]*)?)\)"

    # Plain link — should match
    m = re.findall(pattern, "[link](wiki/concepts/foo.md)")
    assert m == ["wiki/concepts/foo.md"], f"Plain link not matched: {m}"

    # Link with anchor — should match including anchor
    m = re.findall(pattern, "[link](wiki/concepts/foo.md#section-one)")
    assert m == ["wiki/concepts/foo.md#section-one"], f"Anchored link not matched: {m}"

    # External link — must NOT match
    m = re.findall(pattern, "[link](https://example.com)")
    assert m == [], f"External link should not match: {m}"


def test_wiki_lint_source_has_anchor_regex(project_root):
    """wiki-lint.py source must contain the fixed regex with anchor support."""
    source = (project_root / "tools" / "wiki-lint.py").read_text()
    assert "(?:#[^)]*)?)" in source, (
        "wiki-lint.py missing anchor regex fragment '(?:#[^)]*)?)'"
    )


# ---------------------------------------------------------------------------
# HYG-03: evaluate.md ellipsis paths resolved
# ---------------------------------------------------------------------------

def test_evaluate_no_ellipsis_paths(project_root):
    """evaluate.md must not contain ellipsis paths for fsi-dsp references."""
    content = (project_root / ".claude" / "commands" / "wiki" / "evaluate.md").read_text()

    for line in content.splitlines():
        if "fsi-dsp/reference/" in line:
            assert "..." not in line, (
                f"evaluate.md still has ellipsis path on line: {line!r}"
            )

    assert "src/main/java/org/fsi/kafka/producer/FsiProducer.java" in content, (
        "FsiProducer.java full path missing from evaluate.md"
    )
    assert "src/main/java/org/fsi/kafka/consumer/FsiConsumer.java" in content, (
        "FsiConsumer.java full path missing from evaluate.md"
    )


# ---------------------------------------------------------------------------
# HYG-04: Flox environment health
# ---------------------------------------------------------------------------

def test_flox_manifest_exists(project_root):
    """Flox manifest must exist at .flox/env/manifest.toml."""
    manifest = project_root / ".flox" / "env" / "manifest.toml"
    assert manifest.exists(), f"Flox manifest not found at {manifest}"


def test_flox_manifest_has_pyyaml_deps(project_root):
    """Flox manifest must declare pyyaml as a dependency."""
    content = (project_root / ".flox" / "env" / "manifest.toml").read_text()
    assert "pyyaml" in content, "pyyaml not found in .flox/env/manifest.toml"
