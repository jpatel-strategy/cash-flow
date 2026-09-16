"""Unit tests for target_cash.valuation_persistence: preflight, transactional
writer, idempotency, and post-write integrity for the Milestone 4 DCF layer.
"""
import sqlite3
from pathlib import Path

import pytest

from target_cash import forecast as f
from target_cash.migrations import apply_safe_migrations
from target_cash.forecast_persistence import compute_forecast_preflight, persist_forecast
from target_cash.valuation_persistence import (
    VALUATION_MODEL_VERSION,
    ValuationPersistenceNotAuthorizedError,
    compute_valuation_preflight,
    persist_valuation,
    verify_valuation_persistence_integrity,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seeded_conn():
    """Real schema + migrations, seeded with FY2021-FY2025 annual_facts
    (from forecast.HISTORICAL) AND with forecast_scenarios already persisted
    (valuation_results/valuation_ufcf_facts reference forecast_scenarios)."""
    conn = sqlite3.connect(":memory:")
    conn.executescript((REPO_ROOT / "sql" / "schema.sql").read_text())
    apply_safe_migrations(conn)
    conn.execute(
        "INSERT INTO filings (accession_number, cik, company_name, form_type, filed_at, "
        "period_of_report, primary_document_url, ingestion_method) VALUES (?,?,?,?,?,?,?,?)",
        (f.FORECAST_INFORMATION_CUTOFF_ACCESSION, "0000027419", "TARGET CORP", "10-K",
         f.FORECAST_INFORMATION_CUTOFF, "2026-01-31", "https://example.invalid/10k", "manual_upload"),
    )
    for metric, series in f.HISTORICAL.items():
        if metric in ("is_53_week_year", "depreciation_amortization_cfo_addback"):
            continue
        for fy, value in series.items():
            conn.execute(
                """
                INSERT INTO annual_facts
                    (annual_fact_id, metric, fiscal_year, period_start, period_end, days_in_period,
                     analytical_view, value_original, original_unit, value_normalized, normalized_unit,
                     direct_or_derived, fact_status, validation_status, accession_number, filed_at,
                     mapping_version, information_cutoff)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (f.annual_fact_id_for(metric, fy), metric, fy, f"{fy}-02-01", f"{fy + 1}-01-31", 365,
                 "latest_restated", value, "USD_millions", value, "USD_millions", "direct", "authoritative",
                 "pass", f.FORECAST_INFORMATION_CUTOFF_ACCESSION, f.FORECAST_INFORMATION_CUTOFF, "v1",
                 f.FORECAST_INFORMATION_CUTOFF),
            )
    conn.commit()
    forecast_preflight = compute_forecast_preflight()
    persist_forecast(conn, forecast_preflight)
    return conn


def _table_counts(conn):
    tables = ["valuation_assumptions", "valuation_ufcf_facts", "valuation_results", "valuation_validation_results"]
    return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}


def test_preflight_is_authorized():
    preflight = compute_valuation_preflight()
    assert preflight.is_authorized()
    assert preflight.validation_failures == []


def test_preflight_counts():
    from target_cash import valuation as v
    preflight = compute_valuation_preflight()
    assert len(preflight.assumptions) == len(v.build_valuation_assumptions())
    assert len(preflight.results) == 3
    assert len(preflight.ufcf_facts) == 3 * len(f.FORECAST_YEARS)


def test_persist_valuation_writes_expected_counts():
    conn = _seeded_conn()
    preflight = compute_valuation_preflight()
    result = persist_valuation(conn, preflight)
    assert result["status"] == "ok"
    assert _table_counts(conn) == {
        "valuation_assumptions": len(preflight.assumptions),
        "valuation_ufcf_facts": len(preflight.ufcf_facts),
        "valuation_results": 3,
        "valuation_validation_results": len(preflight.validation_results),
    }


def test_persist_valuation_is_idempotent():
    conn = _seeded_conn()
    preflight = compute_valuation_preflight()
    persist_valuation(conn, preflight)
    before = _table_counts(conn)
    persist_valuation(conn, preflight)
    after = _table_counts(conn)
    assert before == after


def test_persist_valuation_refuses_on_failure():
    conn = _seeded_conn()
    preflight = compute_valuation_preflight()
    from target_cash import valuation as v
    fake_failure = v.ValuationCheckResult("simulated_failure", "base", "FAIL", "injected")
    preflight.validation_failures = [fake_failure]
    with pytest.raises(ValuationPersistenceNotAuthorizedError):
        persist_valuation(conn, preflight)
    assert _table_counts(conn) == {k: 0 for k in _table_counts(conn)}


def test_verify_valuation_persistence_integrity_all_pass():
    conn = _seeded_conn()
    preflight = compute_valuation_preflight()
    persist_valuation(conn, preflight)
    integrity = verify_valuation_persistence_integrity(conn)
    assert integrity["all_passed"]
    assert integrity["zero_orphan_ufcf_facts"]
    assert integrity["zero_orphan_results"]
    assert integrity["zero_duplicate_results"]
    assert integrity["every_scenario_has_a_valuation_result"]
    assert integrity["wacc_and_growth_scenario_invariant"]


def test_verify_valuation_persistence_integrity_catches_missing_scenario():
    conn = _seeded_conn()
    preflight = compute_valuation_preflight()
    persist_valuation(conn, preflight)
    conn.execute("DELETE FROM valuation_results WHERE scenario_id = 'upside'")
    integrity = verify_valuation_persistence_integrity(conn)
    assert not integrity["every_scenario_has_a_valuation_result"]
    assert not integrity["all_passed"]
