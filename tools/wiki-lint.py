#!/usr/bin/env python3
"""
wiki-lint.py — health check for the cflt-ai wiki.
Usage: python tools/wiki-lint.py [--full] [--fix]
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


def get_wiki_root() -> Path:
    env_root = os.environ.get("CFLT_WIKI_ROOT")
    if env_root:
        return Path(env_root)
    here = Path(__file__).resolve().parent
    for candidate in [here.parent, here]:
        if (candidate / "wiki").is_dir():
            return candidate
    sys.exit("Could not locate wiki/ directory. Set CFLT_WIKI_ROOT.")


DECAY_DAYS = 90


def parse_frontmatter(content: str) -> dict:
    import yaml
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    try:
        return yaml.safe_load(content[3:end]) or {}
    except Exception:
        return {}


def check_decay(fm: dict, last_validated_fallback_field: str = "last_updated") -> bool:
    """Return True if the article has confidence:high and last_validated is stale (>DECAY_DAYS old)."""
    if fm.get("confidence") != "high":
        return False
    lv_raw = fm.get("last_validated") or fm.get(last_validated_fallback_field)
    if not lv_raw:
        return False
    try:
        lv_date = datetime.strptime(str(lv_raw), "%Y-%m-%d")
    except ValueError:
        return False
    return lv_date < (datetime.now() - timedelta(days=DECAY_DAYS))


def apply_decay_fix(content: str) -> tuple:
    """Demote confidence:high to confidence:medium in front matter only.

    Returns (changed: bool, new_content: str).
    """
    if not content.startswith("---"):
        return (False, content)
    end_idx = content.find("---", 3)
    if end_idx == -1:
        return (False, content)
    front = content[:end_idx + 3]
    body = content[end_idx + 3:]
    new_front = re.sub(r'confidence:\s*high', 'confidence: medium', front, count=1)
    if new_front == front:
        return (False, content)
    return (True, new_front + body)


def load_vendor_pins(repo_root: Path):
    """Return parsed tools/vendor-sources.json or None if missing/malformed.

    Missing file is a soft condition per D-09 (passive drift detection): warn to
    stderr, return None, callers skip the drift check. Exit code stays 0.
    """
    pin_path = repo_root / "tools" / "vendor-sources.json"
    if not pin_path.exists():
        print(
            f"WARNING: MISSING vendor-sources.json at {pin_path} — drift check skipped",
            file=sys.stderr,
        )
        return None
    try:
        return json.loads(pin_path.read_text())
    except json.JSONDecodeError as exc:
        print(
            f"WARNING: MALFORMED vendor-sources.json: {exc} — drift check skipped",
            file=sys.stderr,
        )
        return None


def check_vendor_drift(article_path: Path, fm: dict, vendor_pins) -> list:
    """Return list of drift findings for one article. Empty list = clean.

    D-09 passive drift detection:
    - No source: field → skip (non-vendored article)
    - source: without @ separator → MALFORMED finding
    - Unknown vendor → UNKNOWN VENDOR finding
    - SHA mismatch with pin → DRIFT finding
    - SHA matches pin → no finding (clean)
    """
    if vendor_pins is None:
        return []
    source = fm.get("source")
    if not source:
        return []
    if "@" not in str(source):
        return [
            f"MALFORMED source field in {article_path}: {source!r} (expected '<vendor>@<sha>')"
        ]
    vendor, sha = str(source).split("@", 1)
    pin_entry = vendor_pins.get(vendor)
    if pin_entry is None:
        return [
            f"UNKNOWN VENDOR in {article_path}: {vendor!r} not in vendor-sources.json"
        ]
    pinned_sha = str(pin_entry.get("commit", ""))
    if sha != pinned_sha:
        return [
            f"DRIFT: {article_path}: source={sha[:12]}..., pin={pinned_sha[:12]}..."
        ]
    return []


def check_gap_drift(repo_root: Path, vendor_pins) -> dict:
    """Surface drift between declared trip-wires and upstream KNOWN-GAPS.md.

    Per H.1 D-09 passive posture: findings are surfaced but lint exits 0.
    Returns dict with three keys: gap_drift, missing_gap, malformed_gap (each a list of strings).
    Silently returns empty dict if 'linuxone-accelerator-gaps' key absent (back-compat).

    Findings emitted:
    - DRIFT-GAP {id}: declared={declared!r}, upstream={upstream!r}
    - MISSING-GAP {id}: no matching row in upstream KNOWN-GAPS.md
    - MALFORMED-GAP {id}: missing field(s) {fields}

    Status comparison is case-insensitive and whitespace-stripped.
    """
    findings = {"gap_drift": [], "missing_gap": [], "malformed_gap": []}
    if vendor_pins is None:
        return findings
    gaps_entry = vendor_pins.get("linuxone-accelerator-gaps")
    if not gaps_entry:
        return findings  # back-compat: silent skip when key absent

    known_gaps_path = repo_root / "raw/repos/fsi-dsp/accelerators/confluent-on-linuxone/KNOWN-GAPS.md"
    if not known_gaps_path.exists():
        return findings  # submodule not checked out — passive skip
    upstream_content = known_gaps_path.read_text(errors="replace")

    required_fields = {"id", "title", "status", "workaround", "fsi_impact", "source", "source_id"}
    for tw in gaps_entry.get("trip_wires", []):
        missing = required_fields - set(tw.keys())
        if missing:
            findings["malformed_gap"].append(
                f"MALFORMED-GAP {tw.get('id', '<no-id>')}: missing field(s) {sorted(missing)}"
            )
            continue

        gap_id = tw["id"]
        declared_status = str(tw["status"]).strip().lower()

        # Match the table row: | G-NN | <title> | <impact> | <workaround> | <STATUS> |
        # Anchor on the trailing pipe; capture the final pipe-delimited cell.
        row_re = re.compile(
            rf"^\|\s*{re.escape(gap_id)}\s*\|.*\|\s*([^|]+?)\s*\|\s*$",
            re.MULTILINE,
        )
        match = row_re.search(upstream_content)
        if not match:
            findings["missing_gap"].append(
                f"MISSING-GAP {gap_id}: no matching row in upstream KNOWN-GAPS.md"
            )
            continue

        upstream_status_raw = match.group(1).strip()
        upstream_status = upstream_status_raw.lower()
        if declared_status != upstream_status:
            findings["gap_drift"].append(
                f"DRIFT-GAP {gap_id}: declared={tw['status']!r}, upstream={upstream_status_raw!r}"
            )
    return findings


def _load_manifest_index(repo_root: Path) -> "dict[str, str]":
    """Return {capability_id: path} for every MANIFEST.yaml capability.

    Used by check_source_staleness() to resolve `fsi-dsp://<id>` URIs in wiki
    article frontmatter to on-disk paths in the submodule. Returns empty dict if
    MANIFEST is missing or malformed (passive failure mode — wiki staleness is
    advisory, never blocking lint exit codes).
    """
    import yaml
    manifest_path = repo_root / "raw/repos/fsi-dsp/MANIFEST.yaml"
    if not manifest_path.exists():
        return {}
    try:
        data = yaml.safe_load(manifest_path.read_text())
    except yaml.YAMLError:
        return {}
    if not isinstance(data, dict):
        return {}
    index: dict[str, str] = {}
    for cap in data.get("capabilities", []):
        if isinstance(cap, dict) and "id" in cap and "path" in cap:
            index[cap["id"]] = cap["path"]
    return index


def _file_last_modified_in_submodule(repo_root: Path, rel_path: str) -> "datetime | None":
    """Return the most-recent git commit date for `rel_path` in the fsi-dsp submodule.

    Uses `git log -1 --format=%cI -- <path>` to get the ISO-8601 committer date.
    Returns None if the file is untracked, the submodule is unavailable, or the
    git command fails for any reason (passive failure — silent skip is correct).
    """
    submodule_path = repo_root / "raw/repos/fsi-dsp"
    if not submodule_path.exists():
        return None
    try:
        import subprocess
        result = subprocess.run(
            ["git", "-C", str(submodule_path), "log", "-1", "--format=%cI", "--", rel_path],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        # %cI format is full ISO-8601 with timezone, e.g. 2026-05-26T01:30:00+00:00
        return datetime.fromisoformat(result.stdout.strip().replace("Z", "+00:00"))
    except (subprocess.SubprocessError, ValueError, OSError):
        return None


def check_source_staleness(article_path: Path, fm: dict, repo_root: Path,
                           manifest_index: "dict[str, str] | None" = None) -> list:
    """Return STALE-SOURCE findings for one article. Empty = clean.

    Resolves each `fsi-dsp://<id>` URI in the article's `sources:` list to a
    MANIFEST capability path, gets the file's most-recent commit date in the
    submodule, compares against the article's `last_validated`. If the file
    has been modified since the article was validated, emits STALE-SOURCE-1.

    Findings:
    - STALE-SOURCE-1: file changed since article validation (queue for reconsolidation)
    - STALE-SOURCE-2: file no longer exists in MANIFEST (id was removed upstream)
    - STALE-SOURCE-3: URI is malformed or unresolvable

    Passive posture per H.1 D-09: findings surface but do not fail lint exit.
    """
    sources = fm.get("sources") or []
    if not isinstance(sources, list) or not sources:
        return []
    last_validated_str = fm.get("last_validated") or fm.get("last_updated")
    if not last_validated_str:
        return []
    try:
        last_validated = datetime.strptime(str(last_validated_str), "%Y-%m-%d")
        # Treat the date as midnight UTC so the comparison against tz-aware git dates is sane.
        from datetime import timezone
        last_validated = last_validated.replace(tzinfo=timezone.utc)
    except ValueError:
        return []

    if manifest_index is None:
        manifest_index = _load_manifest_index(repo_root)

    findings: list = []
    for uri in sources:
        uri_str = str(uri)
        if not uri_str.startswith("fsi-dsp://"):
            continue  # other vendor URIs handled by check_vendor_drift
        cap_id = uri_str[len("fsi-dsp://"):]
        cap_path = manifest_index.get(cap_id)
        if cap_path is None:
            # Allow short-form IDs like adr/009 by prefix-matching against the index;
            # if exactly one match, accept it. Multiple matches = ambiguous, skip.
            matches = [p for cid, p in manifest_index.items() if cid.startswith(cap_id + "-") or cid == cap_id]
            if len(matches) == 1:
                cap_path = matches[0]
            elif len(matches) > 1:
                findings.append(
                    f"STALE-SOURCE-3 {article_path}: URI {uri_str!r} is ambiguous "
                    f"({len(matches)} MANIFEST matches) — use full capability ID"
                )
                continue
            else:
                findings.append(
                    f"STALE-SOURCE-2 {article_path}: URI {uri_str!r} resolves to no "
                    f"MANIFEST capability — id removed or never registered"
                )
                continue
        file_mtime = _file_last_modified_in_submodule(repo_root, cap_path)
        if file_mtime is None:
            continue  # silent skip — file untracked or submodule unavailable
        if file_mtime > last_validated:
            findings.append(
                f"STALE-SOURCE-1 {article_path}: cites {uri_str} ({cap_path}); "
                f"validated {last_validated.date()}, file last changed "
                f"{file_mtime.date()} — queue for reconsolidation"
            )
    return findings


def lint_wiki(root: Path, full: bool = False, fix: bool = False) -> dict:
    wiki = root / "wiki"
    findings = {
        "stubs": [],
        "broken_links": [],
        "orphans": [],
        "stale": [],
        "low_confidence": [],
        "unverified": [],
        "missing_diagram": [],
        "decayed": [],
        "drift": [],
        "malformed_source": [],
        "unknown_vendor": [],
        "gap_drift": [],
        "missing_gap": [],
        "malformed_gap": [],
        "stale_source": [],
        "missing_source": [],
        "ambiguous_source": [],
    }
    vendor_pins = load_vendor_pins(root)
    # Build the MANIFEST index once per lint run; reused for every article's
    # source-staleness check. Empty dict if MANIFEST is unavailable (passive skip).
    manifest_index = _load_manifest_index(root)

    all_md = {str(p.relative_to(root)) for p in wiki.rglob("*.md")}
    stale_cutoff = datetime.now() - timedelta(days=90)

    for md in sorted(wiki.rglob("*.md")):
        if md.name.startswith("_"):
            continue
        rel = str(md.relative_to(root))
        content = md.read_text(errors="replace")
        fm = parse_frontmatter(content)

        # Stubs
        if "⚠️ Stub" in content:
            findings["stubs"].append(rel)

        # Low confidence
        if fm.get("confidence") == "low":
            findings["low_confidence"].append(rel)

        # Unverified inline flags
        if "⚠️ unverified" in content:
            findings["unverified"].append(rel)

        # Stale (last_updated > 90 days ago)
        if full and fm.get("last_updated"):
            try:
                lu = datetime.strptime(str(fm["last_updated"]), "%Y-%m-%d")
                if lu < stale_cutoff:
                    findings["stale"].append(rel)
            except ValueError:
                pass

        # Advisory (--full): architectural patterns with no rendered diagram.
        # Heuristic on filename markers (precise, low false-positive); a diagram
        # is either a mermaid block or legacy ASCII box-drawing art.
        if full and rel.startswith("wiki/patterns/"):
            name = md.stem
            archy = any(
                k in name
                for k in ("reference-architecture", "-architecture", "dr-", "migration", "topology")
            )
            has_diagram = "```mermaid" in content or any(
                c in content for c in "┌└├│┐┘┤─┬┴┼"
            )
            if archy and not has_diagram:
                findings["missing_diagram"].append(rel)

        # Decay rule (WIKI-03/04): confidence:high with stale last_validated
        if check_decay(fm):
            findings["decayed"].append(rel)
            if fix:
                changed, new_content = apply_decay_fix(content)
                if changed:
                    md.write_text(new_content)

        # Broken wiki-internal links
        links = re.findall(r"\[.*?\]\((wiki/[^)#]+(?:#[^)]*)?)\)", content)
        for link in links:
            if link not in all_md:
                findings["broken_links"].append(f"{rel} → {link}")

        # D-09: vendor-source drift detection (passive — surfaces but doesn't fail)
        for drift_msg in check_vendor_drift(Path(rel), fm, vendor_pins):
            if drift_msg.startswith("DRIFT:"):
                findings["drift"].append(drift_msg)
            elif drift_msg.startswith("MALFORMED"):
                findings["malformed_source"].append(drift_msg)
            elif drift_msg.startswith("UNKNOWN VENDOR"):
                findings["unknown_vendor"].append(drift_msg)

        # Source-staleness: fsi-dsp:// URIs in `sources:` whose file changed
        # since `last_validated`. Drives the reconsolidation loop — queues
        # affected articles for /wiki:validate review without manual tracking.
        # Only runs in --full mode (git log per article has measurable latency).
        if full:
            for sm in check_source_staleness(Path(rel), fm, root, manifest_index):
                if sm.startswith("STALE-SOURCE-1"):
                    findings["stale_source"].append(sm)
                elif sm.startswith("STALE-SOURCE-2"):
                    findings["missing_source"].append(sm)
                elif sm.startswith("STALE-SOURCE-3"):
                    findings["ambiguous_source"].append(sm)

    # Orphans: articles not referenced in _index.md
    # _index.md uses paths relative to the wiki dir (e.g. "concepts/foo.md"),
    # so compare against wiki-relative paths, not project-root-relative ones.
    if full:
        index = wiki / "_index.md"
        if index.exists():
            index_content = index.read_text()
            for md in sorted(wiki.rglob("*.md")):
                if md.name.startswith("_"):
                    continue
                rel_wiki = str(md.relative_to(wiki))
                if rel_wiki not in index_content:
                    findings["orphans"].append(str(md.relative_to(root)))

        # 12-02: KNOWN-GAPS trip-wire drift (passive surface, non-fatal per H.1 D-09)
        gap_findings = check_gap_drift(root, vendor_pins)
        findings["gap_drift"].extend(gap_findings["gap_drift"])
        findings["missing_gap"].extend(gap_findings["missing_gap"])
        findings["malformed_gap"].extend(gap_findings["malformed_gap"])

    return findings


def main():
    parser = argparse.ArgumentParser(description="Lint the cflt-ai wiki")
    parser.add_argument("--full", action="store_true", help="Full lint including orphans and stale")
    parser.add_argument("--fix", action="store_true", help="Auto-fix: demote stale confidence:high to medium")
    args = parser.parse_args()

    if args.fix:
        args.full = True  # --fix implies --full

    root = get_wiki_root()
    findings = lint_wiki(root, full=args.full, fix=args.fix)

    total = sum(len(v) for v in findings.values())
    if total == 0:
        print("✓ Wiki looks clean.")
        sys.exit(0)

    print(f"Wiki lint findings ({total} total):\n")
    labels = {
        "stubs": "Stubs (need expansion)",
        "broken_links": "Broken internal links",
        "orphans": "Orphaned articles (not in _index.md)",
        "stale": "Stale articles (>90 days)",
        "low_confidence": "Low confidence articles",
        "unverified": "Unverified inline claims",
        "missing_diagram": "Architectural pattern with no diagram (consider adding a mermaid diagram)",
        "decayed": "Decayed articles (confidence demoted)",
        "drift": "Vendor-source DRIFT (article SHA doesn't match tools/vendor-sources.json pin)",
        "malformed_source": "MALFORMED source field (vendor@<sha> shape required)",
        "unknown_vendor": "UNKNOWN VENDOR (source: references a vendor not pinned in vendor-sources.json)",
        "gap_drift": "KNOWN-GAPS DRIFT (declared trip-wire status doesn't match upstream KNOWN-GAPS.md)",
        "missing_gap": "MISSING-GAP (trip-wire ID has no matching row in upstream KNOWN-GAPS.md — gap removed?)",
        "malformed_gap": "MALFORMED-GAP (trip-wire JSON missing required field)",
        "stale_source": "STALE-SOURCE (fsi-dsp:// citation file changed since last_validated — queue for /wiki:validate)",
        "missing_source": "MISSING-SOURCE (fsi-dsp:// citation resolves to no MANIFEST capability — id removed?)",
        "ambiguous_source": "AMBIGUOUS-SOURCE (fsi-dsp:// citation matches multiple MANIFEST capabilities — use full id)",
    }
    for key, items in findings.items():
        if items:
            print(f"  {labels[key]} ({len(items)})")
            for item in items:
                print(f"    - {item}")
            print()


if __name__ == "__main__":
    main()
