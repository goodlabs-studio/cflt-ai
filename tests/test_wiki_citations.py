"""
Tests for wiki citation correctness.

Verifies:
- No wiki article has raw/repos/fsi-dsp paths in its sources frontmatter (CNTR-02)
- All fsi-dsp:// citations resolve against MANIFEST.yaml IDs
- LinuxONE wiki article exists and is properly wired (WIKI-01)
"""
import yaml
from pathlib import Path


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    return yaml.safe_load(content[3:end]) or {}


def _iter_wiki_articles(wiki_root: Path):
    """Yield (path, frontmatter) for all non-underscore wiki markdown files."""
    for md in sorted(wiki_root.rglob("*.md")):
        if md.name.startswith("_"):
            continue
        content = md.read_text(errors="replace")
        fm = _parse_frontmatter(content)
        yield md, fm, content


def _load_manifest_ids(fsi_dsp_root: Path) -> set:
    """Load all stable IDs from MANIFEST.yaml."""
    manifest_path = fsi_dsp_root / "MANIFEST.yaml"
    if not manifest_path.exists():
        return set()
    data = yaml.safe_load(manifest_path.read_text()) or {}
    capabilities = data.get("capabilities", [])
    return {cap["id"] for cap in capabilities if "id" in cap}


class TestNoRawPaths:
    """Verify no wiki article sources frontmatter contains raw/repos/fsi-dsp paths."""

    def test_no_raw_fsi_dsp_paths_in_sources(self, wiki_root):
        """All wiki article sources must use fsi-dsp:// ID form, not raw file paths."""
        violations = []
        for md, fm, _content in _iter_wiki_articles(wiki_root):
            sources = fm.get("sources", [])
            if isinstance(sources, list):
                for source in sources:
                    if isinstance(source, str) and "raw/repos/fsi-dsp" in source:
                        violations.append(f"{md.relative_to(wiki_root.parent)}: {source!r}")
            elif isinstance(sources, str) and "raw/repos/fsi-dsp" in sources:
                violations.append(f"{md.relative_to(wiki_root.parent)}: {sources!r}")

        assert not violations, (
            f"{len(violations)} wiki articles still use raw file paths in sources:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_migrated_articles_have_fsi_dsp_citations(self, wiki_root):
        """Spot-check that key migrated articles now contain fsi-dsp:// citations."""
        expected = {
            "concepts/sla-tiers.md": "fsi-dsp://role/cp_topic",
            "patterns/dr-cluster-linking.md": "fsi-dsp://adr/005",
            "patterns/topic-naming.md": "fsi-dsp://adr/007",
            "synthesis/adr-index.md": "fsi-dsp://adr/001",
        }
        for relative_path, expected_citation in expected.items():
            article_path = wiki_root / relative_path
            assert article_path.exists(), f"Expected article not found: {relative_path}"
            content = article_path.read_text()
            assert expected_citation in content, (
                f"{relative_path} is missing expected citation {expected_citation!r}"
            )


class TestCitationResolution:
    """Verify all fsi-dsp:// citations in wiki articles resolve against MANIFEST.yaml."""

    def test_all_citations_resolve_against_manifest(self, wiki_root, fsi_dsp_root):
        """Every fsi-dsp:// ID cited in wiki frontmatter must exist in MANIFEST.yaml."""
        manifest_ids = _load_manifest_ids(fsi_dsp_root)
        assert manifest_ids, "MANIFEST.yaml loaded no IDs — check fsi-dsp submodule"

        unresolved = []
        for md, fm, _content in _iter_wiki_articles(wiki_root):
            sources = fm.get("sources", [])
            if not isinstance(sources, list):
                sources = [sources] if sources else []
            for source in sources:
                if not isinstance(source, str):
                    continue
                if source.startswith("fsi-dsp://"):
                    # Strip the scheme prefix and check against manifest IDs
                    cited_id = source[len("fsi-dsp://"):]
                    if cited_id not in manifest_ids:
                        unresolved.append(
                            f"{md.relative_to(wiki_root.parent)}: {source!r} not in MANIFEST.yaml"
                        )

        assert not unresolved, (
            f"{len(unresolved)} wiki citations do not resolve against MANIFEST.yaml:\n"
            + "\n".join(f"  - {u}" for u in unresolved)
        )

    def test_manifest_ids_are_not_empty(self, fsi_dsp_root):
        """MANIFEST.yaml must export a non-empty set of IDs."""
        manifest_ids = _load_manifest_ids(fsi_dsp_root)
        assert len(manifest_ids) > 0, "MANIFEST.yaml contains no capability IDs"

    def test_adr_index_cites_all_nine_adrs(self, wiki_root):
        """wiki/synthesis/adr-index.md must cite all ADRs 001-009."""
        adr_index = wiki_root / "synthesis" / "adr-index.md"
        assert adr_index.exists(), "adr-index.md not found"
        content = adr_index.read_text()
        for n in range(1, 10):
            adr_id = f"fsi-dsp://adr/{n:03d}"
            assert adr_id in content, (
                f"adr-index.md missing citation for {adr_id}"
            )


class TestLinuxOneArticle:
    """Verify LinuxONE wiki article exists and is properly structured."""

    def test_article_exists(self, wiki_root):
        """wiki/concepts/linuxone-kafka-integration.md must exist."""
        article = wiki_root / "concepts" / "linuxone-kafka-integration.md"
        assert article.exists(), (
            "wiki/concepts/linuxone-kafka-integration.md not found — "
            "WIKI-01 requires LinuxONE content ingested into wiki"
        )

    def test_article_cites_adr_009(self, wiki_root):
        """linuxone-kafka-integration.md must contain fsi-dsp://adr/009 in sources frontmatter."""
        article = wiki_root / "concepts" / "linuxone-kafka-integration.md"
        assert article.exists()
        content = article.read_text()
        fm = _parse_frontmatter(content)
        sources = fm.get("sources", [])
        assert "fsi-dsp://adr/009" in sources, (
            f"linuxone-kafka-integration.md sources do not include fsi-dsp://adr/009; "
            f"found: {sources!r}"
        )

    def test_article_has_high_confidence(self, wiki_root):
        """linuxone-kafka-integration.md must have confidence: high."""
        article = wiki_root / "concepts" / "linuxone-kafka-integration.md"
        assert article.exists()
        fm = _parse_frontmatter(article.read_text())
        assert fm.get("confidence") == "high", (
            f"Expected confidence: high, got: {fm.get('confidence')!r}"
        )

    def test_article_mentions_mq_source_connector(self, wiki_root):
        """linuxone-kafka-integration.md must describe the IBM MQ Source Connector pattern."""
        article = wiki_root / "concepts" / "linuxone-kafka-integration.md"
        assert article.exists()
        content = article.read_text()
        assert "IBM MQ Source Connector" in content, (
            "linuxone-kafka-integration.md does not mention 'IBM MQ Source Connector'"
        )

    def test_article_in_index(self, wiki_root):
        """wiki/_index.md must list linuxone-kafka-integration."""
        index = wiki_root / "_index.md"
        assert index.exists(), "wiki/_index.md not found"
        content = index.read_text()
        assert "linuxone-kafka-integration" in content, (
            "wiki/_index.md does not reference linuxone-kafka-integration"
        )

    def test_article_in_graph(self, wiki_root):
        """wiki/_graph.md must contain backlinks for linuxone-kafka-integration."""
        graph = wiki_root / "_graph.md"
        assert graph.exists(), "wiki/_graph.md not found"
        content = graph.read_text()
        assert "linuxone-kafka-integration" in content, (
            "wiki/_graph.md does not contain backlinks for linuxone-kafka-integration"
        )

    def test_article_related_frontmatter(self, wiki_root):
        """linuxone-kafka-integration.md related field must link to expected articles."""
        article = wiki_root / "concepts" / "linuxone-kafka-integration.md"
        assert article.exists()
        fm = _parse_frontmatter(article.read_text())
        related = fm.get("related", [])
        expected_related = [
            "concepts/fsi-data-streaming-platform",
            "concepts/sla-tiers",
            "concepts/fsi-compliance",
            "patterns/dr-cluster-linking",
        ]
        for expected in expected_related:
            assert expected in related, (
                f"linuxone-kafka-integration.md related field missing {expected!r}; "
                f"found: {related!r}"
            )
