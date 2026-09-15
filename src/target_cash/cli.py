"""Command-line entry points: fetch, normalize, validate.

Every command accepts an explicit --config path, prints a machine-readable
JSON summary to stdout, and returns a nonzero exit status when a required
gate fails. Commands never overwrite an existing cached source file or
database row with different content silently (see fetch.ingest_manual_file
and the INSERT OR IGNORE / explicit-hash-check patterns below).
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
import time
from pathlib import Path

import yaml

from target_cash import __version__
from target_cash.fetch import append_source_manifest, fetch_via_http, ingest_manual_file
from target_cash.validation import run_validation

DEFAULT_PATHS = {
    "cache_dir": "data/raw",
    "curated_dir": "data/curated",
    "db_filename": "target_cash.db",
    "manifest_csv": "docs/sources.csv",
    "schema_sql": "sql/schema.sql",
    "views_sql": "sql/views.sql",
    "metrics_csv": "config/metrics.csv",
}


def load_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def _resolve_path(config: dict, key: str) -> Path:
    """Resolve a configured path relative to the current working directory.

    Paths are not hardcoded to this package's install location, so the same
    CLI can run against an isolated directory in tests without touching the
    real project's data/manifest/db.
    """
    raw = config.get("paths", {}).get(key, DEFAULT_PATHS[key])
    p = Path(raw)
    return p if p.is_absolute() else Path.cwd() / p


def _connect_db(config: dict) -> sqlite3.Connection:
    db_path = _resolve_path(config, "curated_dir") / config.get("paths", {}).get("db_filename", DEFAULT_PATHS["db_filename"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(_resolve_path(config, "schema_sql").read_text())
    conn.executescript(_resolve_path(config, "views_sql").read_text())
    return conn


def cmd_fetch(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config))
    cache_dir = _resolve_path(config, "cache_dir")
    manifest_path = _resolve_path(config, "manifest_csv")

    descriptor = json.loads(Path(args.descriptor).read_text())
    required_fields = {
        "accession_number", "cik", "company_name", "form_type",
        "filed_at", "period_of_report", "dest_filename",
    }
    missing = required_fields - descriptor.keys()
    if missing:
        print(json.dumps({"command": "fetch", "status": "error", "detail": f"Descriptor missing fields: {sorted(missing)}"}))
        return 1

    try:
        if args.mode == "manual":
            if "source_path" not in descriptor:
                raise ValueError("manual mode requires descriptor['source_path']")
            cached = ingest_manual_file(Path(descriptor["source_path"]), cache_dir, descriptor["dest_filename"])
            ingestion_method = "manual_upload"
            primary_document_url = descriptor.get("primary_document_url", "")
        elif args.mode == "http":
            if "url" not in descriptor:
                raise ValueError("http mode requires descriptor['url']")
            cached = fetch_via_http(descriptor["url"], cache_dir, descriptor["dest_filename"], config["data_source"]["user_agent_contact"])
            ingestion_method = "http_fetch"
            primary_document_url = descriptor["url"]
        else:
            raise ValueError(f"Unknown mode: {args.mode}")
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        print(json.dumps({"command": "fetch", "status": "error", "detail": str(exc)}))
        return 1

    manifest_row = {
        "accession_number": descriptor["accession_number"],
        "cik": descriptor["cik"],
        "company_name": descriptor["company_name"],
        "form_type": descriptor["form_type"],
        "filed_at": descriptor["filed_at"],
        "period_of_report": descriptor["period_of_report"],
        "primary_document_url": primary_document_url,
        "downloaded_at": cached.downloaded_at,
        "file_hash": cached.file_hash,
        "ingestion_method": ingestion_method,
        "notes": descriptor.get("notes", ""),
    }
    try:
        append_source_manifest(manifest_path, manifest_row)
    except FileExistsError as exc:
        print(json.dumps({"command": "fetch", "status": "error", "detail": str(exc)}))
        return 1

    conn = _connect_db(config)
    with conn:
        existing = conn.execute(
            "SELECT 1 FROM filings WHERE accession_number = ?", (manifest_row["accession_number"],)
        ).fetchone()
        if existing:
            conn.close()
            print(json.dumps({
                "command": "fetch",
                "status": "error",
                "detail": f"Database already has a filings row for accession {manifest_row['accession_number']!r}; refusing to create a duplicate.",
            }))
            return 1
        conn.execute(
            """
            INSERT INTO filings
                (accession_number, cik, company_name, form_type, filed_at, period_of_report,
                 primary_document_url, downloaded_at, file_hash, cached_filename, ingestion_method, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                manifest_row["accession_number"], manifest_row["cik"], manifest_row["company_name"],
                manifest_row["form_type"], manifest_row["filed_at"], manifest_row["period_of_report"],
                manifest_row["primary_document_url"], manifest_row["downloaded_at"], manifest_row["file_hash"],
                descriptor["dest_filename"], ingestion_method, manifest_row["notes"],
            ),
        )
    conn.close()

    print(json.dumps({
        "command": "fetch",
        "status": "ok",
        "cached_path": str(cached.path),
        "file_hash": cached.file_hash,
        "ingestion_method": ingestion_method,
        "manifest_updated": str(manifest_path),
    }))
    return 0


def cmd_normalize(args: argparse.Namespace) -> int:
    """Extract candidate raw facts from cached HTML/inline-XBRL filings.

    Populates only `raw_facts` — the broad, unreviewed candidate layer. Never
    derives or writes `quarterly_facts` (the analytical layer): that
    requires a human-reviewed mapping plus, for any period derived by YTD
    subtraction, more than one filing (this command runs against whatever
    is cached, which may be a single annual filing with no quarters to
    derive at all).
    """
    from target_cash.xbrl import parse_inline_xbrl_facts

    config = load_config(Path(args.config))
    cache_dir = _resolve_path(config, "cache_dir")
    metrics_path = _resolve_path(config, "metrics_csv")

    with open(metrics_path, newline="") as f:
        metrics = list(csv.DictReader(f))
    reviewed = [m["metric"] for m in metrics if m["mapping_status"] == "reviewed"]
    pending = [m["metric"] for m in metrics if m["mapping_status"] != "reviewed"]
    concepts = sorted({
        f"{m['candidate_xbrl_taxonomy']}:{m['candidate_xbrl_tag']}"
        for m in metrics
        if m.get("candidate_xbrl_taxonomy") and m.get("candidate_xbrl_tag")
    })

    conn = _connect_db(config)
    conn.row_factory = sqlite3.Row
    filings_count = conn.execute("SELECT COUNT(*) FROM filings").fetchone()[0]

    facts_extracted_by_concept: dict[str, int] = {}
    facts_inserted = 0
    filings_processed = []
    for filing in conn.execute("SELECT * FROM filings WHERE cached_filename IS NOT NULL").fetchall():
        doc_path = cache_dir / filing["cached_filename"]
        if not doc_path.exists() or doc_path.suffix.lower() not in (".htm", ".html"):
            continue
        html_content = doc_path.read_text(errors="ignore")
        inline_facts = parse_inline_xbrl_facts(html_content, concepts)

        inserted_for_this_filing = 0
        with conn:
            for fact in inline_facts:
                facts_extracted_by_concept[fact.concept] = facts_extracted_by_concept.get(fact.concept, 0) + 1
                taxonomy, tag = fact.concept.split(":", 1)
                fact_id = f"{filing['accession_number']}:{fact.concept}:{fact.context_id}"
                cursor = conn.execute(
                    """
                    INSERT OR IGNORE INTO raw_facts
                        (fact_id, accession_number, taxonomy, tag, unit, start_date, end_date,
                         context_ref, dimensional_context, value, scale, sign_as_reported,
                         is_superseded, retrieved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                    """,
                    (
                        fact_id, filing["accession_number"], taxonomy, tag,
                        fact.unit_ref.upper(), fact.context.start_date, fact.context.end_date,
                        fact.context_id, fact.context.dimensional_context,
                        str(fact.value), fact.scale, fact.sign_as_reported,
                        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    ),
                )
                if cursor.rowcount:
                    inserted_for_this_filing += 1
        facts_inserted += inserted_for_this_filing
        filings_processed.append({
            "accession_number": filing["accession_number"],
            "cached_filename": filing["cached_filename"],
            "facts_found": len(inline_facts),
            "facts_newly_inserted": inserted_for_this_filing,
        })

    raw_facts_count = conn.execute("SELECT COUNT(*) FROM raw_facts").fetchone()[0]
    quarterly_facts_count = conn.execute("SELECT COUNT(*) FROM quarterly_facts").fetchone()[0]
    conn.close()

    summary = {
        "command": "normalize",
        "status": "ok",
        "mapping_version": config.get("mapping_version"),
        "filings_cached": filings_count,
        "filings_processed": filings_processed,
        "concepts_searched": concepts,
        "raw_facts_extracted_by_concept": facts_extracted_by_concept,
        "raw_facts_newly_inserted": facts_inserted,
        "raw_facts_stored": raw_facts_count,
        "quarterly_facts_derived": quarterly_facts_count,
        "metrics_reviewed": reviewed,
        "metrics_pending_review": pending,
        "detail": (
            "quarterly_facts is intentionally untouched by this command: deriving analytical "
            "quarters requires a human-reviewed mapping plus, for YTD-subtraction metrics, more "
            "than one filing's worth of raw_facts. Raw extraction never selects or derives on its own."
        ),
    }
    print(json.dumps(summary))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config))
    conn = _connect_db(config)
    conn.row_factory = sqlite3.Row

    # The tolerance methodology (source compatibility / arithmetic invariant / independent
    # quarter validation / cash-rollforward rounding bound / Excel-vs-Python) lives under
    # config['reconciliation_tolerance'] (see config/model.yml and docs/decisions.md).
    # Each check category is populated once real quarterly_facts and their source raw_facts
    # exist — there is nothing to check yet, so every category below is empty.
    derived_fact_ids = [
        r["quarterly_fact_id"]
        for r in conn.execute(
            "SELECT quarterly_fact_id FROM quarterly_facts WHERE basis = 'derived_ytd_subtraction'"
        ).fetchall()
    ]
    lineage_rows = conn.execute("SELECT derived_fact_id, input_fact_id, operation FROM lineage").fetchall()
    from target_cash.lineage import LineageLink

    lineage_links = [LineageLink(r["derived_fact_id"], r["input_fact_id"], r["operation"]) for r in lineage_rows]
    conn.close()

    summary = run_validation(derived_fact_ids, lineage_links)
    output = summary.to_dict()
    output["command"] = "validate"
    if output["checks_run"] == 0:
        output["detail"] = (
            "No quarterly facts have been ingested yet, so the first data gate cannot pass. "
            "This is the correct state until real filing data is normalized — see docs/limitations.md."
        )
    print(json.dumps(output, default=str))
    return 0 if summary.passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="target-cash", description="Target Cash Flow and Investment Capacity model")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="Cache one filing source file (manual upload or HTTP).")
    fetch_parser.add_argument("--config", required=True)
    fetch_parser.add_argument("--mode", choices=["manual", "http"], required=True)
    fetch_parser.add_argument("--descriptor", required=True, help="Path to a JSON file describing the source to ingest.")
    fetch_parser.set_defaults(func=cmd_fetch)

    normalize_parser = subparsers.add_parser("normalize", help="Report normalization state (raw facts, derived quarters, pending mappings).")
    normalize_parser.add_argument("--config", required=True)
    normalize_parser.set_defaults(func=cmd_normalize)

    validate_parser = subparsers.add_parser("validate", help="Run the reconciliation / lineage validation gate.")
    validate_parser.add_argument("--config", required=True)
    validate_parser.set_defaults(func=cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
