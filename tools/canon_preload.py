"""Assemble a deterministic, cache-friendly prefix bundle from internal canon sources.

Inspired by Chan et al. 2024 "Don't Do RAG: When Cache-Augmented Generation is All
You Need for Knowledge Tasks" (arXiv:2412.15605). For bounded knowledge bases that
fit in a long-context window, preloading + KV-caching beats retrieval on latency,
retrieval errors, and architectural complexity. Anthropic's prompt-prefix caching
is the practical analog: emit the bundle as the first content block, mark with
`cache_control: {"type": "ephemeral"}`, and per-query input cost drops to ~10% of
base rate when the same prefix repeats inside the 5-minute TTL.

This module produces three named bundles for different cflt-ai surfaces:

- **canon**         Canon overlays + CLAUDE.md + MANIFEST.yaml (~10k tokens).
                    Already implicitly loaded at start of /review and /dsp:plan;
                    serves as the floor.

- **navigation**    canon + wiki/_index + wiki/_graph + 4 skill SKILL.md headers
                    (~40-50k tokens). Gives the model the wiki TOC + skill domain
                    map without article bodies or skill references. Tunable
                    sweet spot for /ask sessions.

- **full**          canon + entire wiki/ + 4 SKILL.md + 4 references/ trees
                    (~330k tokens). True CAG — load everything. Requires Opus
                    4.7 1M context; exceeds Sonnet 4.6 200k window. Only useful
                    for batch sweeps like a full /wiki:validate run.

Usage:

    python tools/canon_preload.py size                  # print size table
    python tools/canon_preload.py emit --bundle canon   # emit bundle to stdout
    python tools/canon_preload.py emit --bundle navigation > prefix.md
    python tools/canon_preload.py emit --bundle full --format json > prefix.json

Output format is plain text by default (concatenated files with separators)
or JSON with `{file_path: content}` mapping when `--format json` is set.

Token estimates use a 4 chars-per-token heuristic — Anthropic-specific tokenizer
yields slightly different counts but the heuristic is within 10% for English
prose + YAML + code mix.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PIN_SHA = "91d1871e"  # streaming-skills-plugin pin per tools/vendor-sources.json
VENDOR_SKILLS = PROJECT_ROOT / "raw" / "vendor" / "confluent-agent-skills" / PIN_SHA / "skills"
SKILL_SLUGS = (
    "kafka-streams-programming",
    "developing-kafka-python-client",
    "kafka-schema-registry",
    "confluent-cloud-cdc-tableflow",
)

# 4 chars/token is a reasonable rough estimate for English prose + YAML + code.
# Anthropic's actual tokenizer is closer to 3.5-4.0 for this content mix.
CHARS_PER_TOKEN = 4


@dataclass
class BundleEntry:
    path: str
    content: str

    @property
    def bytes(self) -> int:
        return len(self.content.encode("utf-8"))

    @property
    def tokens(self) -> int:
        return self.bytes // CHARS_PER_TOKEN


def _read(rel_path: str) -> BundleEntry:
    abs_path = PROJECT_ROOT / rel_path
    return BundleEntry(path=rel_path, content=abs_path.read_text(errors="replace"))


def _read_glob(rel_dir: str, pattern: str) -> Iterable[BundleEntry]:
    abs_dir = PROJECT_ROOT / rel_dir
    if not abs_dir.exists():
        return
    for p in sorted(abs_dir.rglob(pattern)):
        if p.is_file():
            yield BundleEntry(
                path=str(p.relative_to(PROJECT_ROOT)),
                content=p.read_text(errors="replace"),
            )


def bundle_canon() -> list[BundleEntry]:
    """Floor bundle: canon yaml + project CLAUDE.md + MANIFEST.

    Always-on context for any cflt-ai skill invocation. Tiny (~10k tokens).
    """
    entries: list[BundleEntry] = []
    for p in ("CLAUDE.md", "raw/repos/fsi-dsp/MANIFEST.yaml"):
        if (PROJECT_ROOT / p).exists():
            entries.append(_read(p))
    entries.extend(_read_glob("canon", "*.yaml"))
    return entries


def bundle_navigation() -> list[BundleEntry]:
    """Mid bundle: canon + wiki index + graph + 4 skill SKILL.md headers.

    The cflt-ai sweet spot — gives the model the wiki TOC, the canon overlay
    resolution map, and the skill domain coverage without article bodies or
    skill references. Article bodies and skill references load on demand via
    targeted Read calls; this prefix tells the model what's available.
    """
    entries = bundle_canon()
    for p in ("wiki/_index.md", "wiki/_graph.md", "wiki/_queue.md"):
        if (PROJECT_ROOT / p).exists():
            entries.append(_read(p))
    for slug in SKILL_SLUGS:
        skill_md = VENDOR_SKILLS / slug / "SKILL.md"
        if skill_md.exists():
            entries.append(_read(str(skill_md.relative_to(PROJECT_ROOT))))
    return entries


def bundle_full() -> list[BundleEntry]:
    """Max bundle: canon + entire wiki/ + 4 skill SKILL.md + all references/.

    True CAG — preload everything. Exceeds Sonnet 4.6 (200k); fits Opus 4.7
    (1M context). Only useful for batch sweeps like a full /wiki:validate run
    where the amortized cost per article is dominated by repeated reads of
    the same prefix.
    """
    entries = bundle_navigation()
    # Wiki article bodies
    entries.extend(_read_glob("wiki/concepts", "*.md"))
    entries.extend(_read_glob("wiki/patterns", "*.md"))
    # Skill references (SKILL.md already in navigation)
    for slug in SKILL_SLUGS:
        refs_dir = VENDOR_SKILLS / slug / "references"
        if refs_dir.exists():
            entries.extend(_read_glob(
                str(refs_dir.relative_to(PROJECT_ROOT)),
                "*",
            ))
    # Dedupe by path (skill SKILL.md was added in navigation)
    seen: set[str] = set()
    deduped: list[BundleEntry] = []
    for e in entries:
        if e.path not in seen:
            seen.add(e.path)
            deduped.append(e)
    return deduped


BUNDLES = {
    "canon": bundle_canon,
    "navigation": bundle_navigation,
    "full": bundle_full,
}


def _format_text(entries: list[BundleEntry]) -> str:
    """Concatenate entries with a header line per file (cache-friendly fixed format)."""
    parts: list[str] = []
    for e in entries:
        parts.append(f"<!-- cflt-ai canon-preload: {e.path} -->\n{e.content}\n")
    return "\n".join(parts)


def _format_json(entries: list[BundleEntry]) -> str:
    return json.dumps(
        {e.path: e.content for e in entries},
        indent=2,
        ensure_ascii=False,
    )


def _cmd_size(_args: argparse.Namespace) -> int:
    print(f"Bundle sizes (chars/{CHARS_PER_TOKEN} ≈ tokens):")
    print()
    print(f"  {'bundle':<14}{'files':>7}{'bytes':>12}{'~tokens':>12}")
    print(f"  {'-' * 6:<14}{'-' * 5:>7}{'-' * 7:>12}{'-' * 8:>12}")
    for name, fn in BUNDLES.items():
        entries = fn()
        total_bytes = sum(e.bytes for e in entries)
        total_tokens = total_bytes // CHARS_PER_TOKEN
        print(f"  {name:<14}{len(entries):>7}{total_bytes:>12}{total_tokens:>12}")
    print()
    print("Cacheability:")
    print("  - Anthropic prompt-prefix cache: 5 min ephemeral TTL")
    print("  - Minimum prefix size to be cacheable: 1024 tokens")
    print("  - Write cost: ~$0.30/M tokens (Sonnet); $3.75/M (Opus)")
    print("  - Read cost (cache hit): ~$0.03/M tokens (Sonnet); $0.30/M (Opus)")
    print("  - Break-even: cache write paid back after ~10 cache hits at Sonnet rates")
    return 0


def _cmd_emit(args: argparse.Namespace) -> int:
    bundle_fn = BUNDLES.get(args.bundle)
    if bundle_fn is None:
        print(f"ERROR: unknown bundle {args.bundle!r}. Valid: {sorted(BUNDLES)}", file=sys.stderr)
        return 2
    entries = bundle_fn()
    if args.format == "json":
        sys.stdout.write(_format_json(entries))
    else:
        sys.stdout.write(_format_text(entries))
    return 0


def _cmd_files(args: argparse.Namespace) -> int:
    bundle_fn = BUNDLES.get(args.bundle)
    if bundle_fn is None:
        print(f"ERROR: unknown bundle {args.bundle!r}", file=sys.stderr)
        return 2
    for e in bundle_fn():
        print(f"{e.tokens:>7}  {e.path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assemble cache-friendly prefix bundles from cflt-ai canon."
    )
    subs = parser.add_subparsers(dest="cmd", required=True)

    p_size = subs.add_parser("size", help="Print size table for all three bundles.")
    p_size.set_defaults(func=_cmd_size)

    p_emit = subs.add_parser("emit", help="Emit a bundle to stdout.")
    p_emit.add_argument("--bundle", choices=sorted(BUNDLES), default="navigation")
    p_emit.add_argument("--format", choices=("text", "json"), default="text")
    p_emit.set_defaults(func=_cmd_emit)

    p_files = subs.add_parser("files", help="List files in a bundle with per-file token counts.")
    p_files.add_argument("--bundle", choices=sorted(BUNDLES), default="navigation")
    p_files.set_defaults(func=_cmd_files)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
