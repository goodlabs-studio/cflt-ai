#!/usr/bin/env python3
"""Scan Headroom's per-request event log for full-prefix cache rewrites.

A "rewrite" is a request that writes a large block of tokens to the prompt
cache in one go (default >= 100K). In a healthy loop the cache read dominates
and each turn writes only the new tail; a rewrite means the earlier part of the
conversation changed, so the whole history was paid for again at write price.

Read-only: opens ~/.headroom/savings_events.jsonl and nothing else. Stdlib only.

Usage:
    python3 -I headroom_rewrite_scan.py [--since 2026-10-13] [--threshold 100000] [--top 10]

Costs are recomputed from the cache token counts (cr/cw5/cw1h/un) at the list
prices below, NOT from the event's own `cost_usd`, which is not usable.
Events without a `cache` breakdown (older records, some models) are skipped and
counted in the footer.
"""

import argparse
import collections
import json
from datetime import datetime
from pathlib import Path

EVENTS = Path.home() / ".headroom" / "savings_events.jsonl"

# $/MTok: cache read, 5m write, 1h write, uncached input.
# Source: Anthropic Pricing page, fetched 2026-10-21. Haiku 5.5 uses the <=100K tier.
PRICES = {
    "claude-sonnet-5-5": {"cr": 0.10, "cw5": 2.50, "cw1h": 4.00, "un": 2.00},
    "claude-sonnet-5": {"cr": 0.20, "cw5": 2.50, "cw1h": 4.00, "un": 2.00},
    "claude-opus-5-5": {"cr": 0.20, "cw5": 5.00, "cw1h": 8.00, "un": 4.00},
    "claude-opus-5": {"cr": 0.50, "cw5": 6.25, "cw1h": 10.00, "un": 5.00},
    "claude-haiku-5-5": {"cr": 0.01, "cw5": 0.125, "cw1h": 0.20, "un": 0.10},
    "claude-haiku-4-5": {"cr": 0.10, "cw5": 1.25, "cw1h": 2.00, "un": 1.00},
}


def price_for(model):
    for name, p in PRICES.items():
        if model.startswith(name):
            return p
    return None


def cost(cache, p):
    return sum(cache.get(k, 0) * p[k] for k in p) / 1e6


def written(cache):
    return cache.get("cw5", 0) + cache.get("cw1h", 0)


def load(since):
    rows, skipped = [], collections.Counter()
    for line in EVENTS.read_text().splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        if since and e["ts"][:10] < since:
            continue
        p = price_for(e["model"])
        if not e.get("cache") or p is None:
            skipped[e["model"]] += 1
            continue
        e["_t"] = datetime.fromisoformat(e["ts"])
        e["_cost"] = cost(e["cache"], p)
        rows.append(e)
    rows.sort(key=lambda e: e["_t"])
    return rows, skipped


def gap_label(gap):
    # 5m / 1h are the two cache lifetimes; a rewrite inside them is not a TTL expiry.
    if gap is None:
        return "first"
    if gap <= 300:
        return "within 5m TTL"
    if gap <= 3600:
        return "5m-1h"
    return "past 1h TTL"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--since", help="YYYY-MM-DD (UTC)")
    ap.add_argument("--threshold", type=int, default=100_000, help="tokens written in one request")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    rows, skipped = load(args.since)
    last_by_model, days = {}, collections.defaultdict(lambda: [0, 0.0, 0, 0.0])
    rewrites = []
    for e in rows:
        prev = last_by_model.get(e["model"])
        e["_gap"] = (e["_t"] - prev).total_seconds() if prev else None
        last_by_model[e["model"]] = e["_t"]
        d = days[e["ts"][:10]]
        d[0] += 1
        d[1] += e["_cost"]
        if written(e["cache"]) >= args.threshold:
            d[2] += 1
            d[3] += e["_cost"]
            rewrites.append(e)

    print(f"{'day':10}  {'reqs':>5}  {'est input $':>11}  {'rewrites':>8}  {'rewrite $':>9}  {'share':>5}")
    for day, (n, c, rn, rc) in sorted(days.items()):
        print(f"{day:10}  {n:5d}  {c:11.2f}  {rn:8d}  {rc:9.2f}  {rc / c if c else 0:5.0%}")
    tot, rtot = sum(d[1] for d in days.values()), sum(d[3] for d in days.values())
    print(f"{'total':10}  {len(rows):5d}  {tot:11.2f}  {len(rewrites):8d}  {rtot:9.2f}  {rtot / tot if tot else 0:5.0%}")

    print(f"\nlargest rewrites (>= {args.threshold:,} tokens written):")
    print(f"{'time (UTC)':16}  {'model':18}  {'written':>9}  {'read':>8}  {'$':>5}  gap")
    for e in sorted(rewrites, key=lambda e: -written(e["cache"]))[: args.top]:
        gap = e["_gap"]
        gap_s = "-" if gap is None else f"{gap / 60:.1f}m"
        print(
            f"{e['ts'][:16]:16}  {e['model']:18}  {written(e['cache']):9,}  "
            f"{e['cache'].get('cr', 0):8,}  {e['_cost']:5.2f}  {gap_s} ({gap_label(gap)})"
        )

    labels = collections.Counter(gap_label(e["_gap"]) for e in rewrites)
    print(f"\nrewrite gap since previous request on the same model: {dict(labels)}")
    if skipped:
        print(f"skipped (no cache breakdown or unpriced model): {dict(skipped)}")


if __name__ == "__main__":
    main()
