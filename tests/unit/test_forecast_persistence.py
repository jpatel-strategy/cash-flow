"""Unit tests for target_cash.forecast_persistence: preflight planning,
the transactional writer, idempotency, and post-write integrity checks.

compute_forecast_preflight() needs no database at all (it is pure
target_cash.forecast computation), so most of this file exercises it
directly. persist_forecast()/verify_forecast_persistence_integrity() need
a real connection with the forecast_* tables (via apply_safe_migrations)
plus a minimal, but REAL-shaped, annual_facts table -- seeded
programmatically from target_cash.forecast.HISTORICAL itself, using the
exact annual_fact_id_for() convention, so the orphan-lineage check has
genuine rows to resolve against, not a simplified mock.
"""
import sqlite3
from pathlib import Path

import pytest

from target_cash import forecast as f
from target_cash.migrations import apply_safe_migrations
from target_cash.forecast_persistence import (
    FORECAST_MODEL_VERSION,
    ForecastPersistenceNotAuthorizedError,
    compute_forecast_preflight,
    persist_forecast,
    verify_forecast_persistence_integrity,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seeded_conn():
    """A real database built from the project's actual sql/schema.sql plus
    every safe migration (exactly test_derive.py's own db_conn pattern),
    with a minimal filings row and a full set of FY2021-FY2025 annual_facts
    rows generated directly from forecast.HISTORICAL, using the real
    annual_facts column set and the exact annual_fact_id_for() convention,
    so every historical fact id build_full_lineage() cites actually exists.
    """
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
    conn.commit()  # close out the fixture-seeding transaction so persist_forecast's own BEGIN succeeds
    return conn


def _table_counts(conn):
    tables = ["forecast_scenarios", "forecast_assumptions", "forecast_facts",
              "forecast_lineage", "forecast_validation_results", "investment_capacity_results"]
    return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}


# --- Preflight (no database needed) -----------------------------------------


def test_preflight_is_authorized_on_real_assumption_set():
    preflight = compute_forecast_preflight()
    assert preflight.is_authorized()
    assert preflight.validation_failures == []


def test_preflight_scenario_count():
    preflight = compute_forecast_preflight()
    assert len(preflight.scenarios) == 3
    assert {s["scenario_id"] for s in preflight.scenarios} == set(f.SCENARIOS)
    for s in preflight.scenarios:
        assert s["description"] == f.scenario_narrative(s["scenario_id"])


def test_preflight_assumption_count_matches_build_assumptions():
    preflight = compute_forecast_preflight()
    assert len(preflight.assumptions) == len(f.build_assumptions())


def test_preflight_fact_count_excludes_none_valued_fields():
    preflight = compute_forecast_preflight()
    expected = 3 * len(f.FORECAST_YEARS) * len(f.FIELD_SPECS)
    assert len(preflight.facts) == expected
    # management_selected_deployment is never in FIELD_SPECS -- confirm no fact row for it.
    assert all(row["metric"] != "management_selected_deployment" for row in preflight.facts)


def test_preflight_lineage_ids_are_all_unique():
    preflight = compute_forecast_preflight()
    ids = [row["forecast_lineage_id"] for row in preflight.lineage]
    assert len(ids) == len(set(ids))


def test_preflight_investment_capacity_count():
    preflight = compute_forecast_preflight()
    assert len(preflight.investment_capacity) == 3 * len(f.FORECAST_YEARS)
    for row in preflight.investment_capacity:
        assert row["methodology_note"]  # never empty -- schema makes this mandatory


def test_preflight_deterministic_ids_stable_across_calls():
    p1 = compute_forecast_preflight()
    p2 = compute_forecast_preflight()
    assert {r["forecast_fact_id"] for r in p1.facts} == {r["forecast_fact_id"] for r in p2.facts}
    assert {r["assumption_id"] for r in p1.assumptions} == {r["assumption_id"] for r in p2.assumptions}


# --- Persist + verify (real in-memory schema) -------------------------------


def test_persist_forecast_writes_expected_counts():
    conn = _seeded_conn()
    preflight = compute_forecast_preflight()
    result = persist_forecast(conn, preflight)
    assert result["status"] == "ok"
    assert _table_counts(conn) == {
        "forecast_scenarios": 3, "forecast_assumptions": len(f.build_assumptions()),
        "forecast_facts": len(preflight.facts), "forecast_lineage": len(preflight.lineage),
        "forecast_validation_results": len(preflight.validation_results),
        "investment_capacity_results": 3 * len(f.FORECAST_YEARS),
    }


def test_persist_forecast_is_idempotent():
    conn = _seeded_conn()
    preflight = compute_forecast_preflight()
    persist_forecast(conn, preflight)
    before = _table_counts(conn)
    persist_forecast(conn, preflight)
    after = _table_counts(conn)
    assert before == after


def test_persist_forecast_refuses_when_a_check_fails():
    conn = _seeded_conn()
    preflight = compute_forecast_preflight()
    fake_failure = f.ValidationResult(
        check_name="simulated_failure_for_test", scenario="base", fiscal_year=2026,
        status="FAIL", detail="injected by test",
    )
    preflight.validation_failures = [fake_failure]  # simulate a failure
    with pytest.raises(ForecastPersistenceNotAuthorizedError):
        persist_forecast(conn, preflight)
    assert _table_counts(conn) == {k: 0 for k in _table_counts(conn)}


def test_persist_forecast_rolls_back_completely_on_error():
    """A mid-transaction failure (simulated by a facts row with a bad
    scenario_id, which the schema doesn't reject via SQLite FK enforcement
    by default -- so instead simulate a raised exception mid-loop) must
    leave zero rows in every table, never a partial write."""
    conn = _seeded_conn()
    preflight = compute_forecast_preflight()
    preflight.investment_capacity[-1]["deployable_capacity"] = float("nan")
    # NaN is a valid SQLite REAL, so instead force a real failure: corrupt a
    # required NOT NULL field to trigger an IntegrityError partway through.
    preflight.assumptions[-1]["rationale"] = None
    with pytest.raises(sqlite3.IntegrityError):
        persist_forecast(conn, preflight)
    assert _table_counts(conn) == {k: 0 for k in _table_counts(conn)}


def test_verify_forecast_persistence_integrity_all_pass_on_real_data():
    conn = _seeded_conn()
    preflight = compute_forecast_preflight()
    persist_forecast(conn, preflight)
    integrity = verify_forecast_persistence_integrity(conn)
    assert integrity["all_passed"]
    assert integrity["zero_orphan_lineage"]
    assert integrity["zero_duplicate_facts"]
    assert integrity["zero_duplicate_assumptions"]
    assert integrity["zero_duplicate_investment_capacity_rows"]
    assert integrity["zero_missing_assumptions"]
    assert integrity["zero_scenario_mixing"]
    assert integrity["zero_historical_forecast_year_overlap"]


def test_verify_forecast_persistence_integrity_catches_orphan_lineage():
    conn = _seeded_conn()
    preflight = compute_forecast_preflight()
    persist_forecast(conn, preflight)
    # schema.sql sets PRAGMA foreign_keys = ON for this connection, which
    # would otherwise correctly block the very corruption this test needs to
    # inject -- toggle it off for this one, deliberate, test-only insert.
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute(
        "INSERT INTO forecast_lineage (forecast_lineage_id, forecast_fact_id, input_assumption_id, "
        "operation, sequence) VALUES ('orphan_row', 'fct_base_revenue_2026_v1', 'nonexistent_assumption', 'x', 99)"
    )
    integrity = verify_forecast_persistence_integrity(conn)
    assert not integrity["zero_orphan_lineage"]
    assert not integrity["all_passed"]


def test_verify_forecast_persistence_integrity_catches_scenario_mixing():
    conn = _seeded_conn()
    preflight = compute_forecast_preflight()
    persist_forecast(conn, preflight)
    # Point a base-scenario fact's lineage at an upside-scenario assumption.
    upside_assumption_id = next(a["assumption_id"] for a in preflight.assumptions if a["scenario_id"] == "upside")
    conn.execute(
        "INSERT INTO forecast_lineage (forecast_lineage_id, forecast_fact_id, input_assumption_id, "
        "operation, sequence) VALUES ('mixed_row', 'fct_base_revenue_2026_v1', ?, 'x', 98)",
        (upside_assumption_id,),
    )
    integrity = verify_forecast_persistence_integrity(conn)
    assert not integrity["zero_scenario_mixing"]
    assert not integrity["all_passed"]


def test_schema_unique_constraint_itself_blocks_a_duplicate_fact():
    """The forecast_facts.UNIQUE(scenario_id, metric, fiscal_year,
    assumption_version) constraint (migration 0017) is the primary defense
    against a duplicate logical fact under two different generated IDs --
    stronger than an application-level check alone, since it is enforced
    even for a caller that bypasses forecast_persistence.py entirely."""
    conn = _seeded_conn()
    preflight = compute_forecast_preflight()
    persist_forecast(conn, preflight)
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed"):
        conn.execute(
            "INSERT INTO forecast_facts (forecast_fact_id, scenario_id, fiscal_year, metric, "
            "metric_definition_version, assumption_version, value, unit, formula, validation_status, "
            "information_cutoff, created_at) VALUES ('dup1', 'base', 2026, 'revenue', 'forecast_v1', 'v1', "
            "999.0, 'USD_millions', 'x', 'unvalidated', '2026-03-11', '2026-09-16T00:00:00Z')"
        )
    conn.rollback()
    # The application-level check in verify_forecast_persistence_integrity is
    # defense in depth on top of that constraint -- confirm it independently
    # reports zero duplicates on the untouched, still-clean data.
    integrity = verify_forecast_persistence_integrity(conn)
    assert integrity["zero_duplicate_facts"]


def test_persist_forecast_second_call_updates_not_duplicates_on_value_change():
    """A re-run with a genuinely changed assumption (e.g. after a defect
    correction) must UPDATE the existing row in place, not insert a
    duplicate -- proving the ON CONFLICT DO UPDATE path, not just the
    no-op path."""
    conn = _seeded_conn()
    preflight = compute_forecast_preflight()
    persist_forecast(conn, preflight)
    preflight2 = compute_forecast_preflight()
    preflight2.assumptions[0]["rationale"] = "CHANGED rationale for idempotency test"
    persist_forecast(conn, preflight2)
    row = conn.execute(
        "SELECT rationale, COUNT(*) FROM forecast_assumptions WHERE assumption_id = ? GROUP BY rationale",
        (preflight2.assumptions[0]["assumption_id"],),
    ).fetchone()
    assert row[0] == "CHANGED rationale for idempotency test"
    assert row[1] == 1  # exactly one row, not a duplicate
    assert _table_counts(conn)["forecast_assumptions"] == len(f.build_assumptions())
