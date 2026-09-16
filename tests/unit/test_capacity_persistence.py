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
    assert checks["zero_orphan_lineage_exact_version"]
    assert checks["zero_orphan_horizon_lineage_exact_version"]
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


def test_persisted_horizon_v2_rows_carry_net_horizon_deployable_capacity():
    conn = _seeded_conn()
    pre = compute_capacity_preflight()
    persist_capacity_taxonomy(conn, pre)
    row = conn.execute(
        "SELECT total_horizon_capacity_accessible, net_horizon_deployable_capacity, "
        "cumulative_discretionary_deployment, terminal_remaining_headroom "
        "FROM capacity_horizon_results WHERE scenario_id='base' AND version=?",
        (CAPACITY_MODEL_VERSION,),
    ).fetchone()
    assert row is not None
    gross, net, deployment, headroom = row
    assert gross == pytest.approx(9303.9, abs=0.5)
    assert net == pytest.approx(9175.0, abs=0.5)
    assert net == pytest.approx(deployment + headroom, abs=0.1)
    assert net != pytest.approx(gross, abs=1.0), "net must differ from gross once reserves are nonzero"


def test_lineage_forward_reserve_rows_carry_cross_year_dependency_metadata():
    conn = _seeded_conn()
    pre = compute_capacity_preflight()
    persist_capacity_taxonomy(conn, pre)
    rows = conn.execute(
        "SELECT fiscal_year, dependency_timing, input_fiscal_year, next_year_debt_proceeds_fact_id, "
        "next_year_debt_repayments_fact_id, proxy_note "
        "FROM capacity_taxonomy_lineage WHERE scenario_id='base' AND version=? "
        "AND target_field='forward_debt_repayment_reserve' ORDER BY fiscal_year",
        (CAPACITY_MODEL_VERSION,),
    ).fetchall()
    assert len(rows) == 5
    for fiscal_year, timing, input_fy, proceeds_id, repayments_id, proxy_note in rows[:-1]:
        assert timing == "next_year"
        assert input_fy == fiscal_year + 1
        assert proceeds_id == f"fct_base_debt_proceeds_{fiscal_year + 1}_v1"
        assert repayments_id == f"fct_base_debt_repayments_{fiscal_year + 1}_v1"
        assert proxy_note is None
    terminal_fy, terminal_timing, terminal_input_fy, terminal_proceeds, terminal_repayments, terminal_note = rows[-1]
    assert terminal_fy == 2030
    assert terminal_timing == "terminal_proxy"
    assert terminal_input_fy == 2030
    assert terminal_proceeds is None
    assert terminal_repayments is None
    assert "PROXY" in terminal_note and "FY2031" in terminal_note


def test_persist_prunes_stale_current_version_lineage_after_field_rename():
    """A field renamed within the SAME version (e.g. total_horizon_capacity_
    accessible -> gross_horizon_funding_before_reserve_adjustments) leaves a
    stale lineage row under the old target_field name, since its
    deterministic ID is derived from the field name. persist_capacity_
    taxonomy must prune stale rows for the CURRENT version only -- a
    frozen historical version (e.g. 'v1') carrying the same target_field
    name legitimately is never touched."""
    conn = _seeded_conn()
    pre = compute_capacity_preflight()
    persist_capacity_taxonomy(conn, pre)

    # Manually insert a fake v1 lineage row under the old field name -- this
    # must survive pruning, since pruning is scoped to the current version only.
    conn.execute(
        "INSERT INTO capacity_taxonomy_lineage (capacity_lineage_id, scenario_id, fiscal_year, "
        "target_field, formula, information_cutoff, version) VALUES (?,?,?,?,?,?,?)",
        ("captaxlin_base_total_horizon_capacity_accessible_horizon_8_v1_fake", "base", None,
         "total_horizon_capacity_accessible", "legacy formula", "2026-03-11", "v1"),
    )
    # And a fake STALE current-version row under a field name the current
    # code no longer emits -- this one MUST be pruned.
    conn.execute(
        "INSERT INTO capacity_taxonomy_lineage (capacity_lineage_id, scenario_id, fiscal_year, "
        "target_field, formula, information_cutoff, version) VALUES (?,?,?,?,?,?,?)",
        (f"captaxlin_base_total_horizon_capacity_accessible_horizon_8_{CAPACITY_MODEL_VERSION}",
         "base", None, "total_horizon_capacity_accessible", "stale formula", "2026-03-11", CAPACITY_MODEL_VERSION),
    )
    conn.commit()

    persist_capacity_taxonomy(conn, pre)
    conn.commit()

    stale_current = conn.execute(
        "SELECT COUNT(*) FROM capacity_taxonomy_lineage WHERE target_field='total_horizon_capacity_accessible' AND version=?",
        (CAPACITY_MODEL_VERSION,),
    ).fetchone()[0]
    assert stale_current == 0, "stale current-version lineage row must be pruned on re-persist"

    v1_survives = conn.execute(
        "SELECT COUNT(*) FROM capacity_taxonomy_lineage WHERE target_field='total_horizon_capacity_accessible' AND version='v1'"
    ).fetchone()[0]
    assert v1_survives == 1, "a frozen historical version's lineage row must never be touched by pruning"


def test_v2_lineage_cannot_pass_via_matching_v1_result():
    """Corruption test: a v2 lineage row must NOT be considered satisfied
    merely because a v1 result row exists for the same scenario_id and
    fiscal_year. Before the exact-version fix, the orphan-lineage check's
    EXISTS clause omitted `version`, so deleting the real v2 result while a
    v1 row remained for the same (scenario_id, fiscal_year) would have
    incorrectly reported zero orphans."""
    conn = _seeded_conn()
    pre = compute_capacity_preflight()
    persist_capacity_taxonomy(conn, pre)

    scenario, fiscal_year = "base", 2026
    v1_columns = (
        "capacity_taxonomy_result_id, scenario_id, fiscal_year, operating_fcf, "
        "post_dividend_internal_generation, opening_excess_liquidity, mandatory_debt_uses, "
        "self_funded_gross_capacity, debt_funded_incremental_capacity, total_gross_funding_capacity, "
        "share_repurchases, strategic_investment, voluntary_debt_reduction, other_discretionary_uses, "
        "total_discretionary_deployment, remaining_deployable_headroom, ending_excess_liquidity, "
        "version, information_cutoff"
    )
    conn.execute(
        f"INSERT INTO capacity_taxonomy_results ({v1_columns}) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (f"captax_{scenario}_{fiscal_year}_v1_fake", scenario, fiscal_year,
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "v1", "2026-03-11"),
    )
    conn.commit()

    # Sanity check: before deleting the real v2 row, everything passes.
    assert verify_capacity_persistence_integrity(conn)["zero_orphan_lineage_exact_version"]

    # Remove the REAL v2 result row for this scenario/fiscal_year. A v1 row
    # (same scenario_id + fiscal_year) still exists.
    conn.execute(
        "DELETE FROM capacity_taxonomy_results WHERE scenario_id=? AND fiscal_year=? AND version=?",
        (scenario, fiscal_year, CAPACITY_MODEL_VERSION),
    )
    conn.commit()

    checks = verify_capacity_persistence_integrity(conn)
    assert not checks["zero_orphan_lineage_exact_version"], (
        "a v2 lineage row must not pass merely because a matching v1 result row exists"
    )
    assert not checks["all_passed"]


def test_horizon_lineage_cannot_pass_via_matching_v1_horizon_result():
    """Same corruption proof as above, for horizon-level lineage rows
    (fiscal_year IS NULL)."""
    conn = _seeded_conn()
    pre = compute_capacity_preflight()
    persist_capacity_taxonomy(conn, pre)

    scenario = "base"
    conn.execute(
        "INSERT INTO capacity_horizon_results (capacity_horizon_result_id, scenario_id, "
        "cumulative_self_funded_generation, cumulative_debt_funded_capacity, "
        "opening_excess_liquidity_at_horizon_start, cumulative_discretionary_deployment, "
        "terminal_remaining_headroom, ending_reserve_movement, total_horizon_capacity_accessible, "
        "version, information_cutoff) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (f"caphrz_{scenario}_v1_fake", scenario, 0, 0, 0, 0, 0, 0, 0, "v1", "2026-03-11"),
    )
    conn.commit()

    assert verify_capacity_persistence_integrity(conn)["zero_orphan_horizon_lineage_exact_version"]

    conn.execute(
        "DELETE FROM capacity_horizon_results WHERE scenario_id=? AND version=?",
        (scenario, CAPACITY_MODEL_VERSION),
    )
    conn.commit()

    checks = verify_capacity_persistence_integrity(conn)
    assert not checks["zero_orphan_horizon_lineage_exact_version"], (
        "a v2 horizon-lineage row must not pass merely because a matching v1 horizon result row exists"
    )
    assert not checks["all_passed"]
