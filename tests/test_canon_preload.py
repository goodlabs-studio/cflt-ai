"""Unit tests for tools/canon_preload.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.canon_preload import (  # noqa: E402
    BUNDLES,
    SKILL_SLUGS,
    bundle_canon,
    bundle_full,
    bundle_navigation,
)


class TestBundleCanon:
    """The floor bundle: canon yaml + CLAUDE.md + MANIFEST."""

    def test_includes_claude_md(self):
        entries = bundle_canon()
        paths = [e.path for e in entries]
        assert "CLAUDE.md" in paths

    def test_includes_manifest(self):
        entries = bundle_canon()
        paths = [e.path for e in entries]
        assert "raw/repos/fsi-dsp/MANIFEST.yaml" in paths

    def test_includes_canon_base_defaults(self):
        entries = bundle_canon()
        paths = [e.path for e in entries]
        assert any("canon/base/defaults.yaml" in p for p in paths)

    def test_includes_canon_fsi_overrides(self):
        entries = bundle_canon()
        paths = [e.path for e in entries]
        assert any("canon/industry/fsi/overrides.yaml" in p for p in paths)


class TestBundleNavigation:
    """The mid bundle: canon + wiki TOC + skill SKILL.md headers."""

    def test_extends_canon(self):
        nav = bundle_navigation()
        canon = bundle_canon()
        nav_paths = {e.path for e in nav}
        for entry in canon:
            assert entry.path in nav_paths

    def test_includes_wiki_index(self):
        entries = bundle_navigation()
        paths = {e.path for e in entries}
        assert "wiki/_index.md" in paths

    def test_includes_wiki_graph(self):
        entries = bundle_navigation()
        paths = {e.path for e in entries}
        assert "wiki/_graph.md" in paths

    def test_includes_all_four_skill_md(self):
        entries = bundle_navigation()
        paths = [e.path for e in entries]
        for slug in SKILL_SLUGS:
            assert any(
                f"skills/{slug}/SKILL.md" in p for p in paths
            ), f"missing SKILL.md for {slug}"

    def test_excludes_skill_references(self):
        """Navigation is headers-only; references load on demand."""
        entries = bundle_navigation()
        paths = [e.path for e in entries]
        assert not any("/references/" in p for p in paths), \
            "navigation bundle should not include skill references/"

    def test_excludes_wiki_article_bodies(self):
        """Navigation is TOC-only; article bodies load on demand."""
        entries = bundle_navigation()
        paths = [e.path for e in entries]
        # Allow the canon-overlay article since it's part of canon resolution,
        # but no other wiki/concepts or wiki/patterns articles
        body_paths = [
            p for p in paths
            if p.startswith(("wiki/concepts/", "wiki/patterns/"))
        ]
        assert body_paths == [], (
            f"navigation bundle leaked wiki article bodies: {body_paths}"
        )


class TestBundleFull:
    """The max bundle: navigation + entire wiki + skill references."""

    def test_extends_navigation(self):
        full = bundle_full()
        nav = bundle_navigation()
        full_paths = {e.path for e in full}
        for entry in nav:
            assert entry.path in full_paths

    def test_includes_wiki_articles(self):
        entries = bundle_full()
        paths = [e.path for e in entries]
        assert any(p.startswith("wiki/concepts/") for p in paths)
        assert any(p.startswith("wiki/patterns/") for p in paths)

    def test_includes_skill_references(self):
        entries = bundle_full()
        paths = [e.path for e in entries]
        for slug in SKILL_SLUGS:
            assert any(
                f"skills/{slug}/references" in p for p in paths
            ), f"missing references/ for {slug}"

    def test_no_duplicate_paths(self):
        """Dedup logic prevents the same file from appearing twice."""
        entries = bundle_full()
        paths = [e.path for e in entries]
        assert len(paths) == len(set(paths)), "duplicate paths in full bundle"


class TestSizeOrdering:
    """canon < navigation < full strictly, with margin."""

    def test_canon_smallest(self):
        canon_total = sum(e.bytes for e in bundle_canon())
        nav_total = sum(e.bytes for e in bundle_navigation())
        assert canon_total < nav_total

    def test_navigation_smaller_than_full(self):
        nav_total = sum(e.bytes for e in bundle_navigation())
        full_total = sum(e.bytes for e in bundle_full())
        assert nav_total < full_total

    def test_canon_fits_easily_anywhere(self):
        """Floor bundle should be under 20k tokens (well under any model window)."""
        canon_tokens = sum(e.tokens for e in bundle_canon())
        assert canon_tokens < 20_000, (
            f"canon bundle is {canon_tokens} tokens — should stay under 20k for cheap caching"
        )

    def test_navigation_fits_sonnet_200k(self):
        """Navigation bundle should fit Sonnet 4.6's 200k window with headroom."""
        nav_tokens = sum(e.tokens for e in bundle_navigation())
        assert nav_tokens < 150_000, (
            f"navigation bundle is {nav_tokens} tokens — exceeds Sonnet safe zone"
        )


class TestBundleRegistry:
    """The BUNDLES dict exposes all three named bundles."""

    def test_three_bundles_registered(self):
        assert set(BUNDLES.keys()) == {"canon", "navigation", "full"}

    @pytest.mark.parametrize("name", ["canon", "navigation", "full"])
    def test_each_bundle_callable(self, name):
        entries = BUNDLES[name]()
        assert isinstance(entries, list)
        assert len(entries) > 0


class TestJSONEmission:
    """JSON output is a path → content mapping suitable for programmatic use."""

    def test_json_format_round_trips(self):
        from tools.canon_preload import _format_json
        entries = bundle_canon()
        rendered = _format_json(entries)
        parsed = json.loads(rendered)
        assert isinstance(parsed, dict)
        assert len(parsed) == len(entries)
        for entry in entries:
            assert entry.path in parsed
            assert parsed[entry.path] == entry.content
