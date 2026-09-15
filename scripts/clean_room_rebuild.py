#!/usr/bin/env python3
"""Clean-room reproducibility proof for Milestone 1.

Builds a brand-new target_cash.db in an isolated temporary directory, from
nothing but: the project's own code (schema.sql, views.sql,
config/metrics.csv, config/model.yml), the registered source manifest
(docs/sources.csv), and the cached source documents (data/raw/*.htm --
the same files a manual re-upload would produce; this script never reads
or copies the active database at data/curated/target_cash.db).

Usage (from the repository root):
    .venv/bin/python scripts/clean_room_rebuild.py [--keep]

Prints the resulting table counts and validate totals, then (unless
--keep is passed) deletes the temporary directory. Exit code is nonzero
if any step fails or a source file's hash doesn't match the manifest.

See docs/milestone_1_evidence.md for the expected counts and the
independent comparison against the active database
(scripts/compare_databases.py).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_cli(cwd: Path, *args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "-m", "target_cash.cli", *args],
        cwd=str(cwd), capture_output=True, text=True,
        env={"PYTHONPATH": str(REPO_ROOT / "src")},
    )
    if proc.returncode not in (0, 1):  # validate returns 1 when the gate is closed -- not a script failure
        print(proc.stdout, file=sys.stdout)
        print(proc.stderr, file=sys.stderr)
        raise RuntimeError(f"command failed: {args} (exit {proc.returncode})")
    return json.loads(proc.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", action="store_true", help="keep the temporary directory instead of deleting it")
    args = parser.parse_args()

    manifest_path = REPO_ROOT / "docs" / "sources.csv"
    with open(manifest_path, newline="") as f:
        sources = list(csv.DictReader(f))
    print(f"Read {len(sources)} registered sources from {manifest_path}")

    tmp_dir = Path(tempfile.mkdtemp(prefix="target_cash_clean_room_"))
    print(f"Clean-room directory: {tmp_dir}")
    try:
        (tmp_dir / "sql").mkdir()
        (tmp_dir / "config").mkdir()
        (tmp_dir / "docs").mkdir()
        (tmp_dir / "data" / "raw").mkdir(parents=True)
        (tmp_dir / "data" / "curated").mkdir(parents=True)
        (tmp_dir / "source_uploads").mkdir()

        shutil.copyfile(REPO_ROOT / "sql" / "schema.sql", tmp_dir / "sql" / "schema.sql")
        shutil.copyfile(REPO_ROOT / "sql" / "views.sql", tmp_dir / "sql" / "views.sql")
        shutil.copyfile(REPO_ROOT / "config" / "metrics.csv", tmp_dir / "config" / "metrics.csv")
        shutil.copyfile(REPO_ROOT / "config" / "model.yml", tmp_dir / "config" / "model.yml")

        missing_sources = []
        for row in sources:
            cached_name = Path(row["primary_document_url"]).name
            active_cached_path = REPO_ROOT / "data" / "raw" / cached_name
            if not active_cached_path.exists():
                missing_sources.append(row["accession_number"])
                continue
            actual_hash = sha256_of_file(active_cached_path)
            if actual_hash != row["file_hash"]:
                raise RuntimeError(
                    f"{row['accession_number']}: cached file hash {actual_hash} does not match "
                    f"manifest hash {row['file_hash']} -- refusing to build from a source that "
                    "doesn't match its own registered record."
                )
            shutil.copyfile(active_cached_path, tmp_dir / "source_uploads" / cached_name)

        if missing_sources:
            print(f"MISSING SOURCES (cannot rebuild without them): {missing_sources}", file=sys.stderr)
            return 1
        print(f"All {len(sources)} source documents present and hash-verified against the manifest.")

        for row in sources:
            cached_name = Path(row["primary_document_url"]).name
            descriptor = {
                "source_path": str(tmp_dir / "source_uploads" / cached_name),
                "dest_filename": cached_name,
                "accession_number": row["accession_number"],
                "cik": row["cik"],
                "company_name": row["company_name"],
                "form_type": row["form_type"],
                "filed_at": row["filed_at"],
                "period_of_report": row["period_of_report"],
                "primary_document_url": row["primary_document_url"],
                "notes": f"Clean-room rebuild, reconstructed from {manifest_path.name}.",
            }
            descriptor_path = tmp_dir / f"descriptor_{row['accession_number']}.json"
            descriptor_path.write_text(json.dumps(descriptor))
            run_cli(tmp_dir, "fetch", "--config", "config/model.yml", "--mode", "manual",
                    "--descriptor", str(descriptor_path))

        normalize_dry = run_cli(tmp_dir, "normalize", "--config", "config/model.yml")
        validate_dry = run_cli(tmp_dir, "validate", "--config", "config/model.yml")
        normalize_persisted = run_cli(tmp_dir, "normalize", "--config", "config/model.yml", "--persist-derived")
        validate_final = run_cli(tmp_dir, "validate", "--config", "config/model.yml")

        db_path = tmp_dir / "data" / "curated" / "target_cash.db"
        print()
        print("=== Clean-room result ===")
        print(f"filings_cached: {normalize_dry['filings_cached']}")
        print(f"raw_facts_stored: {normalize_dry['raw_facts_stored']}")
        print(f"quarterly_facts (persisted): {normalize_persisted['quarterly_facts_in_db']}")
        print(f"instant_facts (persisted): {normalize_persisted['instant_facts_in_db']}")
        for k in ("gate_passed", "checks_run", "checks_passed", "checks_failed", "checks_blocked", "checks_unavailable"):
            print(f"validate.{k}: {validate_final[k]}")
        print(f"database: {db_path}")
        return 0
    finally:
        if args.keep:
            print(f"--keep passed: leaving {tmp_dir} in place.")
        else:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
