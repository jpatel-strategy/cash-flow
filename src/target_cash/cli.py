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
from target_cash.migrations import apply_safe_migrations
from target_cash.reference_data import seed_concept_equivalence_rules, seed_fiscal_calendar
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
    """Open (or create) the curated database, safely bringing its schema up to date.

    Never drops or recreates a table: sql/schema.sql only ever CREATEs
    tables that don't yet exist, and apply_safe_migrations only ever ADDs
    columns that don't yet exist. A populated database is never at risk from
    either step — see src/target_cash/migrations.py and docs/decisions.md,
    2026-09-15 "Database safety".
    """
    db_path = _resolve_path(config, "curated_dir") / config.get("paths", {}).get("db_filename", DEFAULT_PATHS["db_filename"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(_resolve_path(config, "schema_sql").read_text())
    conn.executescript(_resolve_path(config, "views_sql").read_text())
    apply_safe_migrations(conn)
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
    """Extract candidate raw facts, then derive analytical quarters for reviewed metrics.

    Two passes, both idempotent:
    1. Extracts every candidate concept named in config/metrics.csv from
       every cached filing into `raw_facts` (broad, unreviewed — every
       competing candidate and dimensional context is kept).
    2. For metrics whose config/metrics.csv row is `mapping_status ==
       'reviewed'`, derives quarterly_facts via target_cash.derive
       (select_consolidated_fact + YTD-subtraction where needed, gated by
       reconcile.check_source_compatibility and cross-checked with
       reconcile.check_independent_quarter_validation). A reviewed metric's
       prior quarterly_facts/lineage rows are cleared and regenerated fresh
       each run. Metrics still `candidate_unverified` are never derived.
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

    # Analytical derivation: only for metrics marked 'reviewed'. Defaults to
    # DRY RUN -- computed and reported, never written -- unless the caller
    # passes --persist-derived. Persistence, when requested, happens as one
    # atomic transaction per table family: flow metrics' outcomes go through
    # derive.persist_all_outcomes (quarterly_facts/lineage), point-in-time
    # metrics' outcomes go through derive.persist_instant_facts (instant_facts/
    # instant_fact_observations) -- never mixed, since a point-in-time balance
    # persisted under a fiscal_quarter label is exactly the mislabeling
    # docs/decisions.md's instant-fact design exists to prevent. raw_facts and
    # filings are never touched by either.
    from target_cash.derive import derive_reviewed_metrics, persist_all_outcomes, persist_instant_facts

    derivation_outcomes = derive_reviewed_metrics(conn, metrics)
    derivation_summary = {
        metric: {
            "quarterly_facts_written": len(outcome.quarterly_facts),
            "errors": outcome.errors,
            "independent_validations": [v.to_dict() for v in outcome.independent_validations],
        }
        for metric, outcome in derivation_outcomes.items()
    }

    category_by_metric = {m["metric"]: m.get("category") for m in metrics}
    flow_outcomes = {
        metric: outcome for metric, outcome in derivation_outcomes.items()
        if category_by_metric.get(metric) != "point_in_time"
    }
    point_in_time_outcomes = {
        metric: outcome for metric, outcome in derivation_outcomes.items()
        if category_by_metric.get(metric) == "point_in_time"
    }

    persisted = bool(getattr(args, "persist_derived", False))
    if persisted:
        persist_all_outcomes(conn, flow_outcomes)
        persist_instant_facts(conn, point_in_time_outcomes)

    quarterly_facts_in_db = conn.execute("SELECT COUNT(*) FROM quarterly_facts").fetchone()[0]
    instant_facts_in_db = conn.execute("SELECT COUNT(*) FROM instant_facts").fetchone()[0]
    conn.close()

    quarterly_facts_computed = sum(v["quarterly_facts_written"] for v in derivation_summary.values())

    summary = {
        "command": "normalize",
        "status": "ok",
        "mapping_version": config.get("mapping_version"),
        "derivation_persisted": persisted,
        "filings_cached": filings_count,
        "filings_processed": filings_processed,
        "concepts_searched": concepts,
        "raw_facts_extracted_by_concept": facts_extracted_by_concept,
        "raw_facts_newly_inserted": facts_inserted,
        "raw_facts_stored": raw_facts_count,
        "quarterly_facts_computed_this_run": quarterly_facts_computed,
        "quarterly_facts_in_db": quarterly_facts_in_db,
        "instant_facts_in_db": instant_facts_in_db,
        "derivation_by_metric": derivation_summary,
        "metrics_reviewed": reviewed,
        "metrics_pending_review": pending,
        "detail": (
            "quarterly_facts is derived only for metrics marked 'reviewed' in config/metrics.csv. "
            "Derivation defaults to dry-run: quarterly_facts_computed_this_run reflects what "
            "derivation produced in memory, quarterly_facts_in_db reflects what is actually "
            "persisted. Pass --persist-derived to write. See derivation_by_metric for per-metric "
            "errors and independent-validation results."
        ),
    }
    print(json.dumps(summary))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Run every applicable validation-check category and fail loudly when
    none apply (see ValidationSummary.passed: checks_run == 0 is never a
    silent pass). Never writes to the database.

    Compatibility/arithmetic-invariant/independent-quarter/YTD-consistency
    checks are recomputed fresh, in memory, from derive.derive_reviewed_metrics
    -- the same dry-run derivation `normalize` reports -- so `validate`
    always reflects the current raw_facts and config/metrics.csv mapping
    state, not a possibly-stale persisted snapshot. Cash roll-forward and
    balance-sheet-vs-roll-forward checks are computed here directly from
    those same in-memory outcomes. Lineage completeness is the one category
    checked against what is ACTUALLY PERSISTED in the database, since its
    purpose is catching a partial or corrupted write.
    """
    from target_cash.derive import derive_reviewed_metrics
    from target_cash.lineage import LineageLink
    from target_cash.reconcile import (
        check_balance_sheet_cash_agreement,
        check_cash_flow_composition,
        check_cash_movement,
        compute_rounding_bound,
    )

    config = load_config(Path(args.config))
    metrics_path = _resolve_path(config, "metrics_csv")
    with open(metrics_path, newline="") as f:
        metrics = list(csv.DictReader(f))

    conn = _connect_db(config)
    conn.row_factory = sqlite3.Row

    outcomes = derive_reviewed_metrics(conn, metrics)

    compatibility_results = []
    arithmetic_invariant_results = []
    independent_validation_results = []
    ytd_consistency_results = []
    for outcome in outcomes.values():
        compatibility_results.extend(outcome.compatibility_results)
        arithmetic_invariant_results.extend(outcome.arithmetic_invariant_results)
        independent_validation_results.extend(outcome.independent_validations)
        ytd_consistency_results.extend(outcome.ytd_consistency_results)

    # Cash roll-forward (two layers, 2026-09-15 redesign) + balance-sheet-vs-
    # roll-forward agreement: computed directly from the in-memory outcomes.
    def _quarterly_facts_by_year_quarter(metric_name: str) -> dict:
        # Keyed by (fiscal_year, fiscal_quarter): the FY2024 Q4 opening instant and
        # the FY2025 Q4 closing instant both have fiscal_quarter == 4, so keying by
        # fiscal_quarter alone would collide the two and silently pick one.
        outcome = outcomes.get(metric_name)
        return {(qf.fiscal_year, qf.fiscal_quarter): qf for qf in outcome.quarterly_facts} if outcome else {}

    def _quarterly_fact_value(metric_name: str, fiscal_quarter: int):
        outcome = outcomes.get(metric_name)
        if outcome is None:
            return None
        qf = next((f for f in outcome.quarterly_facts if f.fiscal_year == 2025 and f.fiscal_quarter == fiscal_quarter), None)
        return qf.value_normalized if qf else None

    cash_rollforward_results = []
    bs_cash = _quarterly_facts_by_year_quarter("cash_and_equivalents_balance_sheet")
    rf_cash = _quarterly_facts_by_year_quarter("cash_and_equivalents_rollforward")
    cash_tolerance = compute_rounding_bound(num_directly_reported_components=2, num_ytd_derived_components=0)

    # Only attempted when cash_and_equivalents_rollforward is itself a reviewed
    # metric this run -- otherwise there is nothing configured to roll forward,
    # and fabricating "missing values" checks out of an unconfigured metric
    # would inflate checks_run without meaning anything.
    for fiscal_quarter in (1, 2, 3, 4) if "cash_and_equivalents_rollforward" in outcomes else ():
        beginning_key = (2024, 4) if fiscal_quarter == 1 else (2025, fiscal_quarter - 1)
        beginning_qf = rf_cash.get(beginning_key)
        ending_qf = rf_cash.get((2025, fiscal_quarter))
        beginning_cash = beginning_qf.value_normalized if beginning_qf else None
        ending_cash = ending_qf.value_normalized if ending_qf else None
        net_change = _quarterly_fact_value("net_change_in_cash", fiscal_quarter)

        # Layer A: beginning + reported net change = ending.
        cash_rollforward_results.append(
            check_cash_movement(
                fiscal_year=2025, fiscal_quarter=fiscal_quarter,
                beginning_cash=beginning_cash, reported_net_change=net_change, ending_cash=ending_cash,
                tolerance_absolute=cash_tolerance,
            )
        )
        # Layer B: CFO + CFI + CFF [+ reported FX, when one exists] = reported net change.
        # No separate FX fact/line exists anywhere in the cached filings (see
        # docs/decisions.md) -- reported_fx=None is passed explicitly, never a
        # synthetic zero, so the check reports fx_evidence_status="unavailable"
        # and discloses the implied residual rather than silently assuming zero.
        cash_rollforward_results.append(
            check_cash_flow_composition(
                fiscal_year=2025, fiscal_quarter=fiscal_quarter,
                cfo=_quarterly_fact_value("operating_cash_flow", fiscal_quarter),
                cfi=_quarterly_fact_value("investing_cash_flow", fiscal_quarter),
                cff=_quarterly_fact_value("financing_cash_flow", fiscal_quarter),
                reported_fx=None,
                reported_net_change=net_change,
                tolerance_absolute=cash_tolerance,
            )
        )
        bs_qf = bs_cash.get((2025, fiscal_quarter))
        cash_rollforward_results.append(
            check_balance_sheet_cash_agreement(
                fiscal_year=2025, fiscal_quarter=fiscal_quarter,
                balance_sheet_cash=(bs_qf.value_normalized if bs_qf else None),
                balance_sheet_source=(bs_qf.quarterly_fact_id if bs_qf else "unavailable"),
                rollforward_cash=ending_cash,
                rollforward_source=(ending_qf.quarterly_fact_id if ending_qf else "unavailable"),
                tolerance_absolute=cash_tolerance,
            )
        )

    # Lineage completeness reflects the database's ACTUAL persisted state, not
    # the outcomes just recomputed above (which are never written here).
    derived_fact_ids = [
        r["quarterly_fact_id"]
        for r in conn.execute(
            "SELECT quarterly_fact_id FROM quarterly_facts WHERE basis = 'derived_ytd_subtraction'"
        ).fetchall()
    ]
    lineage_rows = conn.execute("SELECT derived_fact_id, input_fact_id, operation FROM lineage").fetchall()
    lineage_links = [LineageLink(r["derived_fact_id"], r["input_fact_id"], r["operation"]) for r in lineage_rows]
    conn.close()

    summary = run_validation(
        derived_fact_ids, lineage_links,
        compatibility_results=compatibility_results,
        arithmetic_invariant_results=arithmetic_invariant_results,
        independent_validation_results=independent_validation_results,
        ytd_consistency_results=ytd_consistency_results,
        cash_rollforward_results=cash_rollforward_results,
    )
    output = summary.to_dict()
    output["command"] = "validate"
    output["derivation_errors_by_metric"] = {metric: outcome.errors for metric, outcome in outcomes.items()}
    if output["checks_run"] == 0:
        output["detail"] = (
            "No applicable validation checks were computable from the current raw_facts and "
            "config/metrics.csv reviewed-mapping state, so the first data gate cannot pass. "
            "See derivation_errors_by_metric for why."
        )
    print(json.dumps(output, default=str))
    return 0 if summary.passed else 1


def cmd_seed_reference_data(args: argparse.Namespace) -> int:
    """Apply pending schema migrations, then seed ONLY reference metadata:
    fiscal_calendar and concept_equivalence_rules. Never writes to
    annual_facts/annual_lineage/annual_fact_observations -- persisting an
    annual analytical fact is a separate, not-yet-authorized action. Reports
    before/after counts for every annual-family table so the caller can
    confirm they remain empty.
    """
    config = load_config(Path(args.config))
    conn = _connect_db(config)

    before = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("annual_facts", "annual_lineage", "annual_fact_observations")
    }

    fiscal_calendar_inserted = seed_fiscal_calendar(conn)
    concept_equivalence_rules_inserted = seed_concept_equivalence_rules(conn)

    after = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("annual_facts", "annual_lineage", "annual_fact_observations")
    }
    fiscal_calendar_count = conn.execute("SELECT COUNT(*) FROM fiscal_calendar").fetchone()[0]
    concept_equivalence_rules_count = conn.execute("SELECT COUNT(*) FROM concept_equivalence_rules").fetchone()[0]
    conn.close()

    print(json.dumps({
        "command": "seed-reference-data",
        "status": "ok",
        "fiscal_calendar_rows_inserted": fiscal_calendar_inserted,
        "fiscal_calendar_rows_total": fiscal_calendar_count,
        "concept_equivalence_rules_inserted": concept_equivalence_rules_inserted,
        "concept_equivalence_rules_total": concept_equivalence_rules_count,
        "annual_analytical_tables_before": before,
        "annual_analytical_tables_after": after,
        "annual_analytical_tables_remain_empty": all(v == 0 for v in after.values()),
    }))
    return 0


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
    normalize_parser.add_argument(
        "--persist-derived",
        action="store_true",
        default=False,
        help="Persist derived quarterly_facts/lineage to the database. Default is dry-run: "
             "derivation is computed and reported but nothing is written.",
    )
    normalize_parser.set_defaults(func=cmd_normalize)

    validate_parser = subparsers.add_parser("validate", help="Run the reconciliation / lineage validation gate.")
    validate_parser.add_argument("--config", required=True)
    validate_parser.set_defaults(func=cmd_validate)

    seed_parser = subparsers.add_parser(
        "seed-reference-data",
        help="Apply pending schema migrations and seed fiscal_calendar / concept_equivalence_rules only "
             "(never annual_facts/annual_lineage/annual_fact_observations).",
    )
    seed_parser.add_argument("--config", required=True)
    seed_parser.set_defaults(func=cmd_seed_reference_data)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
