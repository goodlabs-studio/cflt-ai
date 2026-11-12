#!/usr/bin/env python3
"""Compatibility shim: client-name checks now live in tools/org_audit.py.

Kept so existing hooks that call this file (Claude Code PostToolUse --hook,
git pre-commit --staged) keep working. See `python3 tools/org_audit.py --help`.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import org_audit  # noqa: E402

if __name__ == "__main__":
    sys.exit(org_audit.main(sys.argv[1:]))
