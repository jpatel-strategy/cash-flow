#!/usr/bin/env python3
"""Clean-room reproducibility proof for Milestone 1 AND Milestone 2.

Builds a brand-new target_cash.db in an isolated temporary directory, from
nothing but: the project's own code (schema.sql, views.sql,
config/metrics.csv, config/metric_definitions.csv, config/model.yml, and
every migration in src/target_cash/migrations.py, applied automatically by
every CLI command's _connect_db call), the registered source manifest
(docs/sources.csv), and the cached source documents (data/raw/*.htm -- the
same files a manual re-upload would produce; this script never reads or
copies the active database at data/curated/target_cash.db).

Usage (from the repository root):
    .venv/bin/python scripts/clean_room_rebuild.py [--keep]

Steps, in order: fetch every registered source -> normalize (dry-run) ->
validate (dry-run, includes the annual_validation and mapping_evidence_gate
sections) -> normalize --persist-derived (Milestone 1: quarterly_facts/
instant_facts) -> seed-reference-data (Milestone 2: fiscal_calendar/
concept_equivalence_rules only) -> validate (final).

**Annual analytical persistence is NOT part of this script yet** --
persisting annual_facts/annual_lineage/annual_fact_observations is not
authorized as of this milestone (see docs/decisions.md, 2026-09-15 later
entry, "Persistence remains not authorized"). Once a `normalize
--persist-annual` (or equivalent) command exists and is authorized, add it
here, immediately after seed-reference-data and before the final validate
call, so this script continues to prove the ENTIRE database -- Milestone
1's quarterly/instant facts and Milestone 2's annual facts alike -- rebuilds
byte-for-byte-equivalent (via canonical export hashing,
scripts/compare_databases.py) from source documents alone. The expected
post-persistence counts that step should reproduce are the persistence
manifest in docs/milestone_2_mapping_approval_matrix.md, Section C: 478
annual_facts (300 direct + 178 derived), >=300 annual_fact_observations,
364 annual_lineage -- regenerate that document (scripts/
build_mapping_approval_matrix.py) if config/metrics.csv or
config/metric_definitions.csv change before persistence is implemented.

Prints the resulting table counts and validate totals, then (unless
--keep is passed) deletes the temporary directory. Exit code is nonzero
if any step fails or a source file's hash doesn't match the manifest.

See docs/milestone_1_evidence.md for the Milestone 1 expected counts and
docs/milestone_2_schema_and_dry_run.md for the Milestone 2 schema/seed
counts, both compared against the active database via
scripts/compare_databases.py.
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
        shutil.copyfile(REPO_ROOT / "config" / "metric_definitions.csv", tmp_dir / "config" / "metric_definitions.csv")
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
        seed_reference = run_cli(tmp_dir, "seed-reference-data", "--config", "config/model.yml")
        # TODO (once authorized and implemented): annual persistence step goes here,
        # e.g. run_cli(tmp_dir, "normalize", "--config", "config/model.yml", "--persist-annual")
        # -- see the module docstring for the expected post-persistence counts.
        validate_final = run_cli(tmp_dir, "validate", "--config", "config/model.yml")

        db_path = tmp_dir / "data" / "curated" / "target_cash.db"
        print()
        print("=== Clean-room result ===")
        print(f"filings_cached: {normalize_dry['filings_cached']}")
        print(f"raw_facts_stored: {normalize_dry['raw_facts_stored']}")
        print(f"quarterly_facts (persisted): {normalize_persisted['quarterly_facts_in_db']}")
        print(f"instant_facts (persisted): {normalize_persisted['instant_facts_in_db']}")
        print(f"fiscal_calendar_rows_total: {seed_reference['fiscal_calendar_rows_total']}")
        print(f"concept_equivalence_rules_total: {seed_reference['concept_equivalence_rules_total']}")
        print(f"annual_analytical_tables_remain_empty: {seed_reference['annual_analytical_tables_remain_empty']}")
        for k in ("gate_passed", "checks_run", "checks_passed", "checks_failed", "checks_blocked", "checks_unavailable"):
            print(f"validate.{k}: {validate_final[k]}")
        annual = validate_final.get("annual_validation", {})
        print(f"validate.annual_validation.checks_run: {annual.get('checks_run')}")
        print(f"validate.annual_validation.gate_passed: {annual.get('gate_passed')}")
        print(f"validate.annual_validation.by_status: {annual.get('by_status')}")
        mapping_gate = validate_final.get("mapping_evidence_gate", {})
        print(f"validate.mapping_evidence_gate.checks_run: {mapping_gate.get('checks_run')}")
        print(f"validate.mapping_evidence_gate.passed_count: {mapping_gate.get('passed_count')}")
        print(f"validate.mapping_evidence_gate.blocked_count: {mapping_gate.get('blocked_count')}")
        print(f"database: {db_path}")
        return 0
    finally:
        if args.keep:
            print(f"--keep passed: leaving {tmp_dir} in place.")
        else:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
