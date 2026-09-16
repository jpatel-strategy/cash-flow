"""Unit tests for target_cash.capacity_persistence: preflight planning,
the transactional writer, idempotency, rollback, and post-write integrity
checks for the Milestone 9 corrected capacity taxonomy.
"""
import sqlite3
from pathlib import Path

import pytest

from target_cash import forecast as f
from target_cash.migrations import apply_safe_migrations
from target_cash.forecast_persistence import compute_forecast_preflight, persist_forecast
from target_cash.capacity_persistence import (
    CAPACITY_MODEL_VERSION,
    CapacityPersistenceNotAuthorizedError,
    CapacityPersistencePrerequisiteError,
    compute_capacity_preflight,
    persist_capacity_taxonomy,
    verify_capacity_persistence_integrity,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seeded_conn(with_forecast=True):
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
    if with_forecast:
        fpre = compute_forecast_preflight()
        persist_forecast(conn, fpre)
    return conn


def test_compute_capacity_preflight_needs_no_database():
    from target_cash import capacity_taxonomy as ct

    pre = compute_capacity_preflight()
    assert pre.is_authorized()
    summary = pre.summary()
    assert summary["capacity_taxonomy_results"] == 3 * 5  # 3 scenarios x 5 years
    assert summary["capacity_horizon_results"] == 3
    per_scenario_lineage = len(ct._PER_YEAR_FIELD_SPECS) * 5 + len(ct._HORIZON_FIELD_SPECS)
    assert summary["capacity_taxonomy_lineage"] == 3 * per_scenario_lineage
    assert summary["validation_failures"] == 0


def test_persist_refuses_without_forecast_scenarios():
    conn = _seeded_conn(with_forecast=False)
    pre = compute_capacity_preflight()
    with pytest.raises(CapacityPersistencePrerequisiteError):
        persist_capacity_taxonomy(conn, pre)


def test_persist_writes_expected_counts():
    from target_cash import capacity_taxonomy as ct

    conn = _seeded_conn()
    pre = compute_capacity_preflight()
    result = persist_capacity_taxonomy(conn, pre)
    expected = pre.summary()
    del expected["validation_failures"]
    assert result["written"] == expected
    per_scenario_lineage = len(ct._PER_YEAR_FIELD_SPECS) * 5 + len(ct._HORIZON_FIELD_SPECS)
    assert conn.execute("SELECT COUNT(*) FROM capacity_taxonomy_results").fetchone()[0] == 15
    assert conn.execute("SELECT COUNT(*) FROM capacity_horizon_results").fetchone()[0] == 3
    assert conn.execute("SELECT COUNT(*) FROM capacity_taxonomy_lineage").fetchone()[0] == 3 * per_scenario_lineage
    assert conn.execute("SELECT COUNT(*) FROM capacity_validation_results").fetchone()[0] == len(pre.validation_results)


def test_persist_is_idempotent():
    conn = _seeded_conn()
    pre = compute_capacity_preflight()
    persist_capacity_taxonomy(conn, pre)
    before = {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in ("capacity_taxonomy_results", "capacity_horizon_results",
                   "capacity_taxonomy_lineage", "capacity_validation_results")
    }
    persist_capacity_taxonomy(conn, pre)
    after = {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in before
    }
    assert before == after


def test_persist_refuses_when_a_check_fails():
    conn = _seeded_conn()
    pre = compute_capacity_preflight()
    fake_failure = f.ValidationResult("fake_check", "base", 2026, "FAIL", "manufactured for this test")
    pre.validation_failures = [fake_failure]
    with pytest.raises(CapacityPersistenceNotAuthorizedError):
        persist_capacity_taxonomy(conn, pre)
    assert conn.execute("SELECT COUNT(*) FROM capacity_taxonomy_results").fetchone()[0] == 0


def test_persist_rolls_back_on_error():
    conn = _seeded_conn()
    pre = compute_capacity_preflight()
    # Corrupt one row so its INSERT raises (violates the fiscal_year >= 2026 CHECK).
    pre.capacity_results[0]["fiscal_year"] = 1999
    with pytest.raises(sqlite3.IntegrityError):
        persist_capacity_taxonomy(conn, pre)
    # Nothing from this failed transaction should be visible -- proves rollback.
    assert conn.execute("SELECT COUNT(*) FROM capacity_taxonomy_results").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM capacity_horizon_results").fetchone()[0] == 0


def test_verify_capacity_persistence_integrity_all_pass():
    conn = _seeded_conn()
    pre = compute_capacity_preflight()
    persist_capacity_taxonomy(conn, pre)
    checks = verify_capacity_persistence_integrity(conn)
    assert checks["all_passed"], checks
    assert checks["zero_orphan_lineage"]
    assert checks["zero_duplicate_capacity_results"]
    assert checks["zero_duplicate_horizon_results"]
    assert checks["zero_missing_scenario_or_cutoff"]
    assert checks["zero_pre_2026_capacity_rows"]


def test_legacy_investment_capacity_results_untouched_by_capacity_persistence():
    conn = _seeded_conn()
    legacy_before = conn.execute("SELECT * FROM investment_capacity_results ORDER BY investment_capacity_result_id").fetchall()
    pre = compute_capacity_preflight()
    persist_capacity_taxonomy(conn, pre)
    legacy_after = conn.execute("SELECT * FROM investment_capacity_results ORDER BY investment_capacity_result_id").fetchall()
    assert legacy_before == legacy_after
    checks = verify_capacity_persistence_integrity(conn)
    assert checks["legacy_investment_capacity_results_untouched_count"] == len(legacy_after) == 15


def test_persisted_v2_rows_carry_corrected_debt_netting_fields():
    conn = _seeded_conn()
    pre = compute_capacity_preflight()
    persist_capacity_taxonomy(conn, pre)
    row = conn.execute(
        "SELECT gross_debt_proceeds, gross_debt_repayments, net_mandatory_debt_service, "
        "self_funded_capacity_generated, debt_funded_incremental_capacity, "
        "forward_debt_repayment_reserve, forward_reserve_is_proxied "
        "FROM capacity_taxonomy_results WHERE scenario_id='base' AND fiscal_year=2030 AND version=?",
        (CAPACITY_MODEL_VERSION,),
    ).fetchone()
    assert row is not None
    proceeds, repayments, net_service, generated, incremental, forward_reserve, proxied = row
    assert proceeds == pytest.approx(700.0)
    assert repayments == pytest.approx(700.0)
    assert net_service == 0.0
    assert incremental == 0.0
    assert proxied == 1


def test_persisted_horizon_v2_rows_carry_terminal_forward_reserve():
    conn = _seeded_conn()
    pre = compute_capacity_preflight()
    persist_capacity_taxonomy(conn, pre)
    row = conn.execute(
        "SELECT terminal_forward_debt_repayment_reserve, terminal_forward_reserve_is_proxied "
        "FROM capacity_horizon_results WHERE scenario_id='upside' AND version=?",
        (CAPACITY_MODEL_VERSION,),
    ).fetchone()
    assert row is not None
    reserve, proxied = row
    assert reserve == pytest.approx(700.0)
    assert proxied == 1
