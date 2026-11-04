#!/usr/bin/env python3
"""Confluent Cloud cost-by-usage report at topic or topic-group level.

Two stages, because the Metrics API only keeps a short rolling window of data
(retention not confirmed here; check the docs) and the Costs API has no topic detail:

  collect  Pull billing (Costs API) + per-topic usage (Metrics API) for the
           trailing N days into a local SQLite file. Idempotent upsert, so run it
           daily from cron/CI and history accumulates past the Metrics window.
  report   Allocate each day's cluster cost to topics by usage share, optionally
           roll topics up into groups, write CSV + print a table.

Allocation (per day, per cluster):
  network write cost  -> share of received_bytes
  network read cost   -> share of sent_bytes
  storage cost        -> share of retained_bytes (daily mean of hourly samples)
  everything else     -> share of (received+sent) bytes  [--fixed-by equal for even split]
  usage missing for a day -> that cost lands in the "(unattributed)" row, so totals
  always reconcile to the invoice-side number.

Env vars (Cloud API keys, NOT cluster keys):
  CCLOUD_COSTS_KEY / CCLOUD_COSTS_SECRET      OrganizationAdmin or BillingAdmin
  CCLOUD_METRICS_KEY / CCLOUD_METRICS_SECRET  MetricsViewer (dedicated service account)

Topic groups file (JSON, first matching glob wins):
  {"groups": {"payments": ["payments.*", "pay-*"], "risk": ["risk.*"]},
   "default": "(ungrouped)"}

Usage:
  cc_topic_chargeback.py collect --cluster lkc-abc123 --days 7
  cc_topic_chargeback.py report  --cluster lkc-abc123 --from 2026-10-01 --to 2026-11-01 \
      --group-by group --groups groups.json --csv out.csv
  cc_topic_chargeback.py selftest
"""
import argparse
import csv
import fnmatch
import json
import os
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import base64
import urllib.error
import urllib.parse
import urllib.request

COSTS_URL = "https://api.confluent.cloud/billing/v1/costs"
METRICS_URL = "https://api.telemetry.confluent.cloud/v2/metrics/cloud/query"
M_RX = "io.confluent.kafka.server/received_bytes"
M_TX = "io.confluent.kafka.server/sent_bytes"
M_RET = "io.confluent.kafka.server/retained_bytes"
M_REQ = "io.confluent.kafka.server/request_bytes"    # per-principal ingress
M_RESP = "io.confluent.kafka.server/response_bytes"  # per-principal egress
UNATTRIBUTED = "(unattributed)"


# ---------------------------------------------------------------- storage
def db_open(path):
    db = sqlite3.connect(path)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS usage(day TEXT, cluster TEXT, topic TEXT, metric TEXT, value REAL,
        PRIMARY KEY(day, cluster, topic, metric));
    CREATE TABLE IF NOT EXISTS usage_p(day TEXT, cluster TEXT, principal TEXT, name TEXT, metric TEXT, value REAL,
        PRIMARY KEY(day, cluster, principal, metric));
    CREATE TABLE IF NOT EXISTS costs(day TEXT, cluster TEXT, line_type TEXT, amount REAL,
        PRIMARY KEY(day, cluster, line_type));
    """)
    return db


# ---------------------------------------------------------------- HTTP
def _auth(prefix):
    k, s = os.environ.get(f"{prefix}_KEY"), os.environ.get(f"{prefix}_SECRET")
    if not (k and s):
        sys.exit(f"set {prefix}_KEY and {prefix}_SECRET")
    return (k, s)


def _req(method, url, auth, params=None, json_body=None, retries=5):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    hdrs = {"Authorization": "Basic " + base64.b64encode(":".join(auth).encode()).decode(),
            "Content-Type": "application/json"}
    data = json.dumps(json_body).encode() if json_body is not None else None
    for i in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data, hdrs, method=method), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(2 ** i)
                continue
            sys.exit(f"{method} {url} -> {e.code}: {e.read()[:500].decode(errors='replace')}")
    sys.exit(f"{method} {url}: gave up after {retries} retries")


def fetch_costs(cluster, start, end):
    """Yield (day, line_type, amount) for one cluster. end is exclusive (UTC).
    API window is capped at one month, so chunk."""
    auth, cur = _auth("CCLOUD_COSTS"), start
    while cur < end:
        nxt = min(cur + timedelta(days=30), end)
        params = {"start_date": cur.isoformat(), "end_date": nxt.isoformat()}
        url = COSTS_URL
        while url:
            body = _req("GET", url, auth, params=params)
            for row in body.get("data", []):
                if (row.get("resource") or {}).get("id") != cluster:
                    continue
                yield row["start_date"][:10], row.get("line_type", "UNKNOWN"), float(row["amount"])
            url, params = (body.get("metadata") or {}).get("next"), None  # next URL carries page_token
        cur = nxt


def query_metric(cluster, metric, start, end, granularity, label="metric.topic"):
    """Return [(timestamp, label_value, value, name)] grouped by label, following pagination."""
    auth = _auth("CCLOUD_METRICS")
    body = {
        "aggregations": [{"metric": metric}],
        "filter": {"field": "resource.kafka.id", "op": "EQ", "value": cluster},
        "granularity": granularity,
        "group_by": [label],
        "intervals": [f"{start.isoformat()}T00:00:00Z/{end.isoformat()}T00:00:00Z"],
        "limit": 1000,
    }
    out = []
    while True:
        resp = _req("POST", METRICS_URL, auth, json_body=body)
        for d in resp.get("data", []):
            out.append((d["timestamp"], d.get(label, ""), float(d["value"]), d.get("metric.principal_name", "")))
        tok = ((resp.get("meta") or {}).get("pagination") or {}).get("next_page_token")
        if not tok:
            return out
        body["page_token"] = tok


def fetch_usage(cluster, start, end):
    """Yield (day, topic, metric, value). Bytes in/out: daily sum. Retained: mean of hourly samples."""
    for metric in (M_RX, M_TX):
        for ts, topic, v, _ in query_metric(cluster, metric, start, end, "P1D"):
            yield ts[:10], topic, metric, v
    hourly = defaultdict(list)
    for ts, topic, v, _ in query_metric(cluster, M_RET, start, end, "PT1H"):
        hourly[(ts[:10], topic)].append(v)
    for (day, topic), vs in hourly.items():
        yield day, topic, M_RET, sum(vs) / len(vs)


def fetch_principal_usage(cluster, start, end):
    """Yield (day, principal_id, principal_name, metric, value): daily request/response bytes per principal.
    Whether these two metrics accept group_by metric.principal_id is per the Metrics API descriptor;
    verify with the Cloud descriptors page before first live run."""
    for metric in (M_REQ, M_RESP):
        for ts, pid, v, name in query_metric(cluster, metric, start, end, "P1D", "metric.principal_id"):
            yield ts[:10], pid, name, metric, v


# ---------------------------------------------------------------- collect
def cmd_collect(a):
    end = datetime.now(timezone.utc).date() + timedelta(days=1)  # exclusive; today is partial
    start = end - timedelta(days=a.days + 1)
    db = db_open(a.db)
    n = 0
    for day, lt, amt in fetch_costs(a.cluster, start, end):
        db.execute("INSERT OR REPLACE INTO costs VALUES(?,?,?,?)", (day, a.cluster, lt, amt))
        n += 1
    m = 0
    for day, topic, metric, v in fetch_usage(a.cluster, start, end):
        db.execute("INSERT OR REPLACE INTO usage VALUES(?,?,?,?,?)", (day, a.cluster, topic, metric, v))
        m += 1
    pm = 0
    if a.principals:
        for day, pid, name, metric, v in fetch_principal_usage(a.cluster, start, end):
            db.execute("INSERT OR REPLACE INTO usage_p VALUES(?,?,?,?,?,?)", (day, a.cluster, pid, name, metric, v))
            pm += 1
    db.commit()
    print(f"upserted {n} cost rows, {m} usage rows, {pm} principal rows ({start}..{end}). "
          f"Costs lag up to ~72h: recent days are re-pulled on each run, keep the window >= 4 days.")


# ---------------------------------------------------------------- allocation
def line_kind(line_type):
    lt = line_type.upper()
    if "NETWORK_WRITE" in lt:
        return "write"
    if "NETWORK_READ" in lt:
        return "read"
    if "STORAGE" in lt:
        return "storage"
    return "fixed"


def shares(weights):
    tot = sum(weights.values())
    return {k: v / tot for k, v in weights.items()} if tot > 0 else {}


def allocate_day(costs, usage, fixed_by="bytes"):
    """costs: {line_type: amount}; usage: {metric: {topic: value}}.
    Returns ({topic: {kind: amount}}, unattributed_amount)."""
    rx, tx, ret = usage.get(M_RX, {}), usage.get(M_TX, {}), usage.get(M_RET, {})
    topics = set(rx) | set(tx) | set(ret)
    bytes_total = {t: rx.get(t, 0) + tx.get(t, 0) for t in topics}
    basis = {
        "write": shares(rx),
        "read": shares(tx),
        # retained_bytes missing -> fall back to write share rather than losing the cost
        "storage": shares(ret) or shares(rx),
        "fixed": shares({t: 1 for t in topics}) if fixed_by == "equal" else shares(bytes_total),
    }
    out, unattributed = defaultdict(lambda: defaultdict(float)), 0.0
    for lt, amt in costs.items():
        k = line_kind(lt)
        if not basis[k]:
            unattributed += amt
            continue
        for t, s in basis[k].items():
            out[t][k] += amt * s
    return out, unattributed


def build_report(db, cluster, start, end, group_of, fixed_by):
    costs, usage = defaultdict(dict), defaultdict(lambda: defaultdict(dict))
    for day, lt, amt in db.execute(
            "SELECT day,line_type,amount FROM costs WHERE cluster=? AND day>=? AND day<?",
            (cluster, start, end)):
        costs[day][lt] = amt
    for day, topic, metric, v in db.execute(
            "SELECT day,topic,metric,value FROM usage WHERE cluster=? AND day>=? AND day<?",
            (cluster, start, end)):
        usage[day][metric][topic] = v
    rows = defaultdict(lambda: defaultdict(float))  # key -> kind -> amount
    meta = defaultdict(float)                       # key -> bytes in+out (for display)
    missing_usage_days = []
    for day in sorted(costs):
        alloc, un = allocate_day(costs[day], usage.get(day, {}), fixed_by)
        if not usage.get(day):
            missing_usage_days.append(day)
        for t, kinds in alloc.items():
            key = group_of(t)
            for k, v in kinds.items():
                rows[key][k] += v
        if un:
            rows[UNATTRIBUTED]["fixed"] += un
        for metric in (M_RX, M_TX):
            for t, v in usage.get(day, {}).get(metric, {}).items():
                meta[group_of(t)] += v
    return rows, meta, sum(sum(c.values()) for c in costs.values()), missing_usage_days


def make_bu_mapper_from(cfg):
    default = cfg.get("default", "Unassigned")
    pats = [(bu, p) for bu, ps in cfg["bus"].items() for p in ps]
    return lambda pid: next((bu for bu, p in pats if fnmatch.fnmatchcase(pid, p)), default)


def make_bu_mapper(path):
    """bu map JSON: {"bus": {"payments": ["sa-123", "sa-9*"]}, "default": "Unassigned"}.
    Principals are matched by id (glob ok). Unmapped principals -> default, never silently dropped."""
    cfg = json.load(open(path))
    default = cfg.get("default", "Unassigned")
    pats = [(bu, p) for bu, ps in cfg["bus"].items() for p in ps]

    def bu_of(pid):
        for bu, p in pats:
            if fnmatch.fnmatchcase(pid, p):
                return bu
        return default
    return bu_of


def build_report_principal(db, cluster, start, end, bu_of, fixed_by):
    """Same maths as build_report, keyed by principal then rolled up to BU.
    Storage has no per-principal metric, so allocate_day's fallback uses the ingress (writer) share."""
    costs, usage, names = defaultdict(dict), defaultdict(lambda: defaultdict(dict)), {}
    for day, lt, amt in db.execute(
            "SELECT day,line_type,amount FROM costs WHERE cluster=? AND day>=? AND day<?", (cluster, start, end)):
        costs[day][lt] = amt
    alias = {M_REQ: M_RX, M_RESP: M_TX}
    for day, pid, name, metric, v in db.execute(
            "SELECT day,principal,name,metric,value FROM usage_p WHERE cluster=? AND day>=? AND day<?",
            (cluster, start, end)):
        usage[day][alias[metric]][pid or "(unknown-principal)"] = v
        names[pid] = name
    rows, meta, missing = defaultdict(lambda: defaultdict(float)), defaultdict(float), []
    for day in sorted(costs):
        alloc, un = allocate_day(costs[day], usage.get(day, {}), fixed_by)
        if not usage.get(day):
            missing.append(day)
        for pid, kinds in alloc.items():
            for k, v in kinds.items():
                if v:  # zero-byte principals shouldn't create empty rows
                    rows[bu_of(pid)][k] += v
        if un:
            rows[UNATTRIBUTED]["fixed"] += un
        for metric in (M_RX, M_TX):
            for pid, v in usage.get(day, {}).get(metric, {}).items():
                meta[bu_of(pid)] += v
    return rows, meta, sum(sum(c.values()) for c in costs.values()), missing


def make_grouper(a):
    if a.group_by == "topic":
        return lambda t: t or "(cluster-level)"
    cfg = json.load(open(a.groups))
    default = cfg.get("default", "(ungrouped)")
    patterns = [(g, p) for g, ps in cfg["groups"].items() for p in ps]

    def group_of(t):
        for g, p in patterns:
            if fnmatch.fnmatchcase(t, p):
                return g
        return default
    return group_of


def cmd_report(a):
    db = db_open(a.db)
    if a.group_by == "bu":
        rows, meta, total, missing = build_report_principal(
            db, a.cluster, a.start, a.end, make_bu_mapper(a.bu_map), a.fixed_by)
    else:
        rows, meta, total, missing = build_report(db, a.cluster, a.start, a.end, make_grouper(a), a.fixed_by)
    kinds = ["write", "read", "storage", "fixed"]
    hdr = [a.group_by, *[f"{k}_cost" for k in kinds], "total_cost", "pct_of_total", "gb_in_out"]
    out = []
    for key, k in sorted(rows.items(), key=lambda kv: -sum(kv[1].values())):
        t = sum(k.values())
        out.append([key, *[round(k.get(x, 0), 4) for x in kinds], round(t, 4),
                    round(100 * t / total, 2) if total else 0, round(meta.get(key, 0) / 1e9, 3)])
    alloc_sum = sum(r[5] for r in out)
    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(hdr)
            w.writerows(out)
    widths = [max(len(str(x)) for x in col) for col in zip(hdr, *out)]
    for r in [hdr, *out]:
        print("  ".join(str(x).rjust(w) if i else str(x).ljust(w) for i, (x, w) in enumerate(zip(r, widths))))
    print(f"\ncluster cost in window: {total:.2f}  | allocated rows sum: {alloc_sum:.2f}  "
          f"| diff: {total - alloc_sum:+.4f} (should be ~0)")
    if missing:
        print(f"WARNING: no usage data for {len(missing)} day(s) with cost -> "
              f"fully in '{UNATTRIBUTED}': {', '.join(missing[:10])}", file=sys.stderr)


# ---------------------------------------------------------------- selftest
def cmd_selftest(_):
    """Offline check of allocation maths + grouping + reconciliation. No network."""
    db = db_open(":memory:")
    c = "lkc-test"
    costs = {"KAFKA_NETWORK_WRITE": 10.0, "KAFKA_NETWORK_READ": 20.0, "KAFKA_STORAGE": 30.0,
             "KAFKA_BASE": 40.0}
    for lt, amt in costs.items():
        db.execute("INSERT INTO costs VALUES('2026-10-01',?,?,?)", (c, lt, amt))
    db.execute("INSERT INTO costs VALUES('2026-10-02',?,?,?)", (c, "KAFKA_BASE", 5.0))  # no usage that day
    use = {M_RX: {"payments.a": 75, "payments.b": 25, "risk.x": 100},
           M_TX: {"payments.a": 0, "payments.b": 100, "risk.x": 100},
           M_RET: {"payments.a": 50, "payments.b": 50, "risk.x": 100}}
    for m, d in use.items():
        for t, v in d.items():
            db.execute("INSERT INTO usage VALUES('2026-10-01',?,?,?,?)", (c, t, m, v))
    grp = lambda t: "payments" if t.startswith("payments") else "risk"  # noqa: E731
    rows, _, total, missing = build_report(db, c, "2026-10-01", "2026-10-03", grp, "bytes")
    got = {k: round(sum(v.values()), 6) for k, v in rows.items()}
    # write 10: pay 5, risk 5 | read 20: pay 10, risk 10 | storage 30: pay 15, risk 15
    # base 40 by bytes (pay 200 of 400): pay 20, risk 20 | day2 base 5 unattributed
    exp = {"payments": 50.0, "risk": 50.0, UNATTRIBUTED: 5.0}
    assert got == exp, (got, exp)
    assert abs(sum(got.values()) - total) < 1e-9 and missing == ["2026-10-02"]
    # --- principal -> BU path
    for pid, name, rq, rs in [("sa-pay1", "pay-app", 75, 0), ("sa-pay2", "pay-batch", 25, 100),
                              ("u-risk", "risk-user", 100, 100), ("sa-orphan", "", 0, 0)]:
        db.execute("INSERT INTO usage_p VALUES('2026-10-01',?,?,?,?,?)", (c, pid, name, M_REQ, rq))
        db.execute("INSERT INTO usage_p VALUES('2026-10-01',?,?,?,?,?)", (c, pid, name, M_RESP, rs))
    bu = make_bu_mapper_from({"bus": {"payments": ["sa-pay*"], "risk": ["u-risk"]}, "default": "Unassigned"})
    prow, _, ptotal, pmiss = build_report_principal(db, c, "2026-10-01", "2026-10-03", bu, "bytes")
    pgot = {k: round(sum(v.values()), 6) for k, v in prow.items()}
    # same usage shares as topic test, so same split; orphan has zero bytes -> no cost
    assert pgot == exp and abs(sum(pgot.values()) - ptotal) < 1e-9, (pgot, exp)
    db.execute("INSERT INTO usage_p VALUES('2026-10-01',?,?,?,?,?)", (c, "sa-new", "new", M_REQ, 100))
    prow, _, ptotal, _ = build_report_principal(db, c, "2026-10-01", "2026-10-03", bu, "bytes")
    assert "Unassigned" in prow and abs(sum(sum(v.values()) for v in prow.values()) - ptotal) < 1e-9
    print("selftest ok:", got, "| principal path ok:", pgot)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default="cc_chargeback.sqlite")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--cluster", required=True, help="lkc-xxxxx")
    c.add_argument("--days", type=int, default=7, help="trailing days to (re)pull")
    c.add_argument("--principals", action="store_true", help="also pull per-principal request/response bytes")
    c.set_defaults(fn=cmd_collect)
    r = sub.add_parser("report")
    r.add_argument("--cluster", required=True)
    r.add_argument("--from", dest="start", required=True, help="YYYY-MM-DD inclusive")
    r.add_argument("--to", dest="end", required=True, help="YYYY-MM-DD exclusive")
    r.add_argument("--group-by", choices=["topic", "group", "bu"], default="topic")
    r.add_argument("--groups", help="JSON file of topic groups (required for --group-by group)")
    r.add_argument("--fixed-by", choices=["bytes", "equal"], default="bytes")
    r.add_argument("--bu-map", help="JSON principal->BU map (required for --group-by bu)")
    r.add_argument("--csv")
    r.set_defaults(fn=cmd_report)
    sub.add_parser("selftest").set_defaults(fn=cmd_selftest)
    a = p.parse_args()
    if a.cmd == "report" and a.group_by == "bu" and not a.bu_map:
        p.error("--group-by bu needs --bu-map")
    if a.cmd == "report" and a.group_by == "group" and not a.groups:
        p.error("--group-by group needs --groups")
    a.fn(a)


if __name__ == "__main__":
    main()
