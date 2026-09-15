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
validate (dry-run, includes annual_analytical_validation and
mapping_evidence_gate) -> normalize --persist-derived (Milestone 1:
quarterly_facts/instant_facts) -> seed-reference-data (Milestone 2:
fiscal_calendar/concept_equivalence_rules only) -> persist-annual (Milestone
2: annual_facts/annual_fact_observations/annual_lineage, through the SAME
conditionally-authorized CLI command a real operator would run -- never a
one-off script) -> validate (final, post-persistence).

`persist-annual`'s own conditional-authorization chain re-checks the git
working tree and re-runs the CapEx/debt-bridge regression tests against
THIS repository (not the clean-room copy -- those checks are about whether
the codebase itself is trustworthy, independent of which database it is
about to write), while everything database-dependent (raw_facts,
annual_facts, the preflight plan) operates entirely on the clean room's own
isolated database. If the working tree is not clean when this script runs,
persist-annual correctly refuses and this script fails loudly rather than
silently proceeding without annual facts.

After the final validate, this script runs scripts/compare_databases.py
between the clean-room database and the ACTIVE database
(data/curated/target_cash.db), covering quarterly_facts, lineage,
instant_facts, instant_fact_observations, annual_facts,
annual_fact_observations, annual_lineage, and period_facts_unified, plus
the two validate JSON outputs -- via deterministic, sorted, canonical
exports (never raw file bytes). Corresponding hashes must match.

Prints the resulting table counts, validate totals, persistence counts, and
the comparison result, then (unless --keep is passed) deletes the temporary
directory. Exit code is nonzero if any step fails, a source file's hash
doesn't match the manifest, or the clean-room and active databases diverge.

See docs/milestone_1_evidence.md for the Milestone 1 expected counts,
docs/milestone_2_mapping_approval_matrix.md for the Milestone 2 mapping
matrix and persistence manifest, and docs/milestone_2_evidence.md for the
consolidated final evidence package.
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
        persist_annual = run_cli(tmp_dir, "persist-annual", "--config", "config/model.yml")
        if persist_annual.get("status") != "ok":
            print("persist-annual did not succeed in the clean room:", file=sys.stderr)
            print(json.dumps(persist_annual, indent=2), file=sys.stderr)
            return 1
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
        print(f"persist_annual.written: {persist_annual.get('written')}")
        print(f"persist_annual.integrity.all_passed: {persist_annual.get('integrity', {}).get('all_passed')}")
        m1 = validate_final.get("milestone_1_validation", {})
        for k in ("gate_passed", "checks_run", "checks_passed", "checks_failed", "checks_blocked", "checks_unavailable"):
            print(f"validate.milestone_1_validation.{k}: {m1.get(k)}")
        annual = validate_final.get("annual_analytical_validation", {})
        print(f"validate.annual_analytical_validation.checks_run: {annual.get('checks_run')}")
        print(f"validate.annual_analytical_validation.gate_passed: {annual.get('gate_passed')}")
        print(f"validate.annual_analytical_validation.by_status: {annual.get('by_status')}")
        mapping_gate = validate_final.get("mapping_evidence_gate", {})
        print(f"validate.mapping_evidence_gate.checks_run: {mapping_gate.get('checks_run')}")
        print(f"validate.mapping_evidence_gate.passed_count: {mapping_gate.get('passed_count')}")
        print(f"validate.mapping_evidence_gate.blocked_count: {mapping_gate.get('blocked_count')}")
        print(f"validate.mapping_evidence_gate.gate_passed: {mapping_gate.get('gate_passed')}")
        print(f"validate.overall_gate_passed: {validate_final.get('overall_gate_passed')}")
        print(f"database: {db_path}")

        active_db_path = REPO_ROOT / "data" / "curated" / "target_cash.db"
        active_validate_path = tmp_dir / "active_validate.json"
        clean_room_validate_path = tmp_dir / "clean_room_validate.json"
        active_validate = run_cli(REPO_ROOT, "validate", "--config", "config/model.yml")
        active_validate_path.write_text(json.dumps(active_validate))
        clean_room_validate_path.write_text(json.dumps(validate_final))

        print()
        print("=== Comparing clean-room database against the active database ===")
        compare_proc = subprocess.run(
            [PYTHON, str(REPO_ROOT / "scripts" / "compare_databases.py"),
             str(db_path), str(active_db_path), str(clean_room_validate_path), str(active_validate_path)],
            capture_output=True, text=True,
        )
        print(compare_proc.stdout)
        if compare_proc.returncode != 0:
            print(compare_proc.stderr, file=sys.stderr)
            print("CLEAN-ROOM COMPARISON FAILED", file=sys.stderr)
            return 1

        return 0
    finally:
        if args.keep:
            print(f"--keep passed: leaving {tmp_dir} in place.")
        else:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
