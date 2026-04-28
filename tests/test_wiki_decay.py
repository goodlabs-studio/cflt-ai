"""
Tests for wiki article decay lifecycle (WIKI-03 and WIKI-04).

TestLastValidatedField — verifies all wiki articles carry the last_validated field
TestDecayRule         — verifies check_decay() and apply_decay_fix() logic
"""
import importlib.util
import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Load wiki-lint module (handles hyphen in filename)
# ---------------------------------------------------------------------------
_spec = importlib.util.spec_from_file_location(
    "wiki_lint",
    str(Path(__file__).resolve().parent.parent / "tools" / "wiki-lint.py"),
)
_wiki_lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_wiki_lint)
check_decay = _wiki_lint.check_decay
apply_decay_fix = _wiki_lint.apply_decay_fix
parse_frontmatter = _wiki_lint.parse_frontmatter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_article(confidence: str, last_validated: str, last_updated: str = "2026-01-01") -> str:
    """Return a minimal wiki article string with the given frontmatter values."""
    return (
        "---\n"
        f"title: Test Article\n"
        f"tags: [test]\n"
        f"confidence: {confidence}\n"
        f"last_updated: {last_updated}\n"
        f"last_validated: {last_validated}\n"
        "---\n\n"
        "# Test Article\n\n"
        "Body text with confidence: high mention that should NOT be rewritten.\n"
    )


# ---------------------------------------------------------------------------
# TestLastValidatedField
# ---------------------------------------------------------------------------

class TestLastValidatedField:
    """Verify every wiki article carries a properly formatted last_validated field."""

    def _wiki_articles(self, wiki_root: Path):
        """Yield all non-underscore wiki .md files (concepts, patterns, synthesis)."""
        for subdir in ("concepts", "patterns", "synthesis"):
            d = wiki_root / subdir
            if d.is_dir():
                for md in d.rglob("*.md"):
                    if not md.name.startswith("_"):
                        yield md

    def test_all_articles_have_last_validated(self, wiki_root):
        """Every wiki article must have a last_validated key in its YAML front matter."""
        missing = []
        for md in self._wiki_articles(wiki_root):
            content = md.read_text(errors="replace")
            fm = parse_frontmatter(content)
            if "last_validated" not in fm:
                missing.append(str(md.relative_to(wiki_root.parent)))
        assert missing == [], (
            f"Articles missing last_validated field:\n" + "\n".join(f"  {p}" for p in missing)
        )

    def test_last_validated_is_valid_date(self, wiki_root):
        """The last_validated value in every article must match YYYY-MM-DD format."""
        invalid = []
        for md in self._wiki_articles(wiki_root):
            content = md.read_text(errors="replace")
            fm = parse_frontmatter(content)
            lv = fm.get("last_validated")
            if lv is None:
                continue  # caught by test_all_articles_have_last_validated
            try:
                datetime.strptime(str(lv), "%Y-%m-%d")
            except ValueError:
                invalid.append(f"{md.relative_to(wiki_root.parent)}: {lv!r}")
        assert invalid == [], (
            "Articles with invalid last_validated date format:\n"
            + "\n".join(f"  {e}" for e in invalid)
        )

    def test_article_format_spec_documents_last_validated(self, project_root):
        """article-format.md must contain the literal string 'last_validated: YYYY-MM-DD'."""
        spec_path = (
            project_root
            / ".claude"
            / "commands"
            / "wiki"
            / "references"
            / "article-format.md"
        )
        assert spec_path.exists(), f"Spec file not found: {spec_path}"
        content = spec_path.read_text(errors="replace")
        assert "last_validated: YYYY-MM-DD" in content, (
            "article-format.md does not document last_validated field"
        )


# ---------------------------------------------------------------------------
# TestDecayRule
# ---------------------------------------------------------------------------

class TestDecayRule:
    """Unit tests for the check_decay() and apply_decay_fix() functions."""

    def test_stale_high_confidence_detected(self):
        """confidence:high article with last_validated older than 90 days is stale."""
        stale_date = (datetime.now() - timedelta(days=91)).strftime("%Y-%m-%d")
        article = _make_article(confidence="high", last_validated=stale_date)
        fm = parse_frontmatter(article)
        assert check_decay(fm) is True, (
            f"Expected stale detection for last_validated={stale_date!r}"
        )

    def test_fresh_high_confidence_not_detected(self):
        """confidence:high article with last_validated within 90 days is NOT stale."""
        fresh_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        article = _make_article(confidence="high", last_validated=fresh_date)
        fm = parse_frontmatter(article)
        assert check_decay(fm) is False, (
            f"Expected no stale detection for last_validated={fresh_date!r}"
        )

    def test_medium_confidence_not_affected(self):
        """confidence:medium is never marked stale regardless of last_validated date."""
        stale_date = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d")
        article = _make_article(confidence="medium", last_validated=stale_date)
        fm = parse_frontmatter(article)
        assert check_decay(fm) is False, (
            "Medium confidence articles should never trigger decay"
        )

    def test_fix_rewrites_confidence_in_frontmatter_only(self):
        """apply_decay_fix() replaces 'confidence: high' only in front matter, not body."""
        stale_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
        # Article body deliberately contains "confidence: high" as literal text
        content = (
            "---\n"
            "title: Test\n"
            "confidence: high\n"
            f"last_validated: {stale_date}\n"
            "---\n\n"
            "# Test\n\n"
            "The producer requires confidence: high for exactly-once delivery.\n"
        )
        changed, new_content = apply_decay_fix(content)
        assert changed is True, "apply_decay_fix should report a change"

        # Extract front matter and body
        end_idx = new_content.find("---", 3)
        front = new_content[:end_idx + 3]
        body = new_content[end_idx + 3:]

        assert "confidence: medium" in front, "Front matter should contain confidence: medium"
        assert "confidence: high" not in front, "Front matter should no longer contain confidence: high"
        # Body must be untouched — the original "confidence: high" text survives
        assert "confidence: high" in body, (
            "Body text containing 'confidence: high' must NOT be rewritten"
        )
