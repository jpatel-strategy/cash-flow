#!/usr/bin/env python3
"""Standalone JSON dump of the Milestone 2 annual dry run (both analytical
views), for ad hoc inspection. The actual computation lives in
target_cash.annual so target_cash.cli validate can share the identical
logic -- this script is a thin wrapper, not a separate reimplementation.

Writes NOTHING to the database.

Usage (from the repository root):
    .venv/bin/python scripts/annual_dry_run.py [--db data/curated/target_cash.db]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from target_cash.annual import compute_all_years  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/curated/target_cash.db")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    result = compute_all_years(conn)
    conn.close()

    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
