"""Unit tests for target_cash.annual_persistence: preflight planning,
conditional authorization, and the transactional writer.

Uses a small, real-schema (via apply_safe_migrations -- the same migrations
the real database gets, with real CHECK/UNIQUE constraints, not a simplified
mock) in-memory database, seeded with just two direct metrics (revenue,
cost_of_sales -- real target_cash.annual.DURATION_METRICS entries, since
DURATION_METRICS/INSTANT_METRICS are hardcoded and not test-parameterizable)
across two fiscal years, plus one derived metric (gross_profit). This is
enough to exercise every required guarantee without needing all 30 direct
metrics x 5 years of real filing data.
"""
import sqlite3

import pytest

from target_cash.migrations import apply_safe_migrations
from target_cash.annual_persistence import (
    GateAuthorization,
    PersistenceNotAuthorizedError,
    compute_persistence_preflight,
    persist_annual_facts,
)

GROSS_PROFIT_DEF = {
    "gross_profit": {
        "unit": "USD_millions",
        "formula": "revenue - cost_of_sales",
        "numerator_metrics": "revenue",
        "denominator_metrics": "cost_of_sales",
    }
}


def _seeded_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute(
        """
        CREATE TABLE filings (
            accession_number TEXT PRIMARY KEY, cik TEXT NOT NULL, company_name TEXT NOT NULL,
            form_type TEXT NOT NULL, filed_at TEXT NOT NULL, period_of_report TEXT NOT NULL,
            primary_document_url TEXT NOT NULL, downloaded_at TEXT, file_hash TEXT,
            ingestion_method TEXT NOT NULL, notes TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE raw_facts (
            fact_id TEXT PRIMARY KEY, accession_number TEXT, taxonomy TEXT, tag TEXT, unit TEXT,
            start_date TEXT, end_date TEXT, context_ref TEXT, dimensional_context TEXT,
            value TEXT, scale INTEGER, sign_as_reported INTEGER, is_superseded INTEGER, retrieved_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE quarterly_facts (
            quarterly_fact_id TEXT PRIMARY KEY, metric TEXT NOT NULL, fiscal_year INTEGER NOT NULL,
            fiscal_quarter INTEGER NOT NULL, period_start TEXT, period_end TEXT NOT NULL,
            days_in_period INTEGER, value_original REAL NOT NULL, original_unit TEXT NOT NULL,
            value_normalized REAL NOT NULL, normalized_unit TEXT NOT NULL DEFAULT 'USD_millions',
            basis TEXT NOT NULL, as_of_date TEXT NOT NULL, mapping_version TEXT NOT NULL,
            is_current_view INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    apply_safe_migrations(conn)

    filings_cols = (
        "accession_number, cik, company_name, form_type, filed_at, period_of_report, "
        "primary_document_url, ingestion_method"
    )
    conn.execute(
        f"INSERT INTO filings ({filings_cols}) VALUES "
        "('acc-2024', '0000027419', 'Target Corporation', '10-K', "
        "'2024-03-01', '2024-02-03', 'https://example.invalid', 'manual_upload')"
    )
    conn.execute(
        f"INSERT INTO filings ({filings_cols}) VALUES "
        "('acc-2025', '0000027419', 'Target Corporation', '10-K', "
        "'2025-03-01', '2025-02-01', 'https://example.invalid', 'manual_upload')"
    )
    conn.execute(
        "INSERT INTO fiscal_calendar (cik, company_name, fiscal_year, fiscal_quarter, period_start, "
        "period_end, week_count, is_53_week_year, authority_accession) VALUES "
        "('0000027419', 'Target Corporation', 2024, 0, '2023-01-29', '2024-02-03', 53, 1, 'acc-2024')"
    )
    conn.execute(
        "INSERT INTO fiscal_calendar (cik, company_name, fiscal_year, fiscal_quarter, period_start, "
        "period_end, week_count, is_53_week_year, authority_accession) VALUES "
        "('0000027419', 'Target Corporation', 2025, 0, '2024-02-04', '2025-02-01', 52, 0, 'acc-2025')"
    )
    # revenue / cost_of_sales raw facts for both fiscal years (as_filed == latest_restated here,
    # since only one filing per year exists in this fixture).
    for fy, start, end, acc, rev, cogs in (
        (2024, "2023-01-29", "2024-02-03", "acc-2024", "107412000000", "77736000000"),
        (2025, "2024-02-04", "2025-02-01", "acc-2025", "106566000000", "77297000000"),
    ):
        conn.execute(
            "INSERT INTO raw_facts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"rf_rev_{fy}", acc, "us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax", "USD",
             start, end, "c-1", None, rev, 6, 1, 0, "2026-09-16T00:00:00Z"),
        )
        conn.execute(
            "INSERT INTO raw_facts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"rf_cogs_{fy}", acc, "us-gaap", "CostOfGoodsAndServicesSold", "USD",
             start, end, "c-2", None, cogs, 6, 1, 0, "2026-09-16T00:00:00Z"),
        )
    conn.commit()
    return conn


def _full_authorization(preflight_fact_count=8):
    """A GateAuthorization with every field proving authorized -- the
    baseline for tests that need persistence to actually run. Individual
    tests mutate one field via dataclasses.replace to prove that field's
    guard actually matters.
    """
    return GateAuthorization(
        milestone_1_gate_passed=True, mapping_gate_passed=True,
        # 42 is an arbitrary fixture-scale number, deliberately unrelated to
        # the real project's own mapping-gate pass count (whatever it
        # currently is) -- paired with a matching expected_mapping_pass_count
        # override so this helper never silently breaks when the real
        # project's own count changes (as it did 2026-09-16, 48 -> 49).
        mapping_gate_pass_count=42, expected_mapping_pass_count=42, mapping_gate_blocked_count=0,
        annual_gate_passed=True, overall_gate_passed=True,
        capex_regression_tests_passed=True, debt_bridge_tests_passed=True,
        preflight_fact_count=preflight_fact_count, expected_preflight_fact_count=preflight_fact_count,
        backup_path="/tmp/fake-backup.db", backup_sha256="abc123", verified_backup_sha256="abc123",
        working_tree_clean=True,
    )


# --- Preflight planner ----------------------------------------------------

def test_preflight_plans_direct_and_derived_facts_with_deterministic_ids():
    conn = _seeded_conn()
    preflight = compute_persistence_preflight(
        conn, {"revenue", "cost_of_sales", "gross_profit"}, GROSS_PROFIT_DEF,
        mapping_version="v0-test", information_cutoff="2026-09-16",
    )
    # revenue + cost_of_sales: 2 direct metrics x 2 FY x 2 views = 8 direct facts.
    # gross_profit: 1 derived metric x 2 FY x 2 views = 4 derived facts.
    assert preflight.total_annual_facts == 12
    assert preflight.direct_count == 8
    assert preflight.derived_count == 4
    ids = {f.annual_fact_id for f in preflight.facts}
    assert "annual:revenue:2025:as_originally_filed" in ids
    assert "annual:gross_profit:2025:latest_restated" in ids
    # Deterministic: recomputing must produce byte-identical IDs.
    preflight2 = compute_persistence_preflight(
        conn, {"revenue", "cost_of_sales", "gross_profit"}, GROSS_PROFIT_DEF,
        mapping_version="v0-test", information_cutoff="2026-09-16",
    )
    assert {f.annual_fact_id for f in preflight2.facts} == ids


def test_preflight_excludes_metric_not_in_eligible_set():
    conn = _seeded_conn()
    preflight = compute_persistence_preflight(
        conn, {"revenue"}, {}, mapping_version="v0-test", information_cutoff="2026-09-16",
    )
    assert all(f.metric == "revenue" for f in preflight.facts)
    assert preflight.total_annual_facts == 4  # 2 FY x 2 views, cost_of_sales/gross_profit never touched


def test_preflight_direct_facts_get_exactly_one_selected_observation():
    conn = _seeded_conn()
    preflight = compute_persistence_preflight(
        conn, {"revenue", "cost_of_sales"}, {}, mapping_version="v0-test", information_cutoff="2026-09-16",
    )
    # 2 direct metrics x 2 FY x 2 views = 8 direct facts, each with exactly 1 observation.
    assert len(preflight.observations) == 8
    assert all(o.relationship == "selected" for o in preflight.observations)
    assert preflight.observations_by_relationship() == {"selected": 8, "corroborating": 0, "restated": 0, "conflicting": 0}


def test_preflight_derived_facts_get_lineage_edges_never_source_edges():
    conn = _seeded_conn()
    preflight = compute_persistence_preflight(
        conn, {"revenue", "cost_of_sales", "gross_profit"}, GROSS_PROFIT_DEF,
        mapping_version="v0-test", information_cutoff="2026-09-16",
    )
    # 4 gross_profit rows (2 FY x 2 views), each with 2 inputs (revenue, cost_of_sales) = 8 edges.
    assert len(preflight.lineage) == 8
    assert all(e.input_annual_fact_id is not None for e in preflight.lineage)
    summary = preflight.summary()
    assert summary["direct_source_lineage_edges"] == 0
    assert summary["derived_lineage_edges"] == 8


def test_preflight_never_persists_target_defined_net_debt():
    conn = _seeded_conn()
    preflight = compute_persistence_preflight(
        conn, {"revenue", "target_defined_net_debt"}, {}, mapping_version="v0-test", information_cutoff="2026-09-16",
    )
    assert all(f.metric != "target_defined_net_debt" for f in preflight.facts)


# --- Conditional authorization (item 4) -----------------------------------

@pytest.mark.parametrize("field,bad_value", [
    ("milestone_1_gate_passed", False),
    ("mapping_gate_passed", False),
    ("mapping_gate_pass_count", 47),
    ("mapping_gate_blocked_count", 1),
    ("annual_gate_passed", False),
    ("overall_gate_passed", False),
    ("capex_regression_tests_passed", False),
    ("debt_bridge_tests_passed", False),
    ("preflight_fact_count", 477),
    ("backup_path", ""),
    ("working_tree_clean", False),
])
def test_a_single_failed_condition_blocks_authorization(field, bad_value):
    import dataclasses
    auth = dataclasses.replace(_full_authorization(), **{field: bad_value})
    assert auth.is_authorized() is False
    assert field.split("_gate")[0] in " ".join(auth.failures()) or len(auth.failures()) > 0


def test_backup_hash_mismatch_blocks_authorization():
    import dataclasses
    auth = dataclasses.replace(_full_authorization(), verified_backup_sha256="different-hash")
    assert auth.is_authorized() is False


def test_all_conditions_true_authorizes():
    assert _full_authorization().is_authorized() is True
    assert _full_authorization().failures() == []


# --- Persistence cannot bypass a failed component gate --------------------

def test_persist_refuses_without_authorization_object_at_all():
    """direct invocation of the persistence function requires an explicit
    validated authorization object -- passing None (or omitting it) must
    refuse, not silently proceed."""
    conn = _seeded_conn()
    preflight = compute_persistence_preflight(conn, {"revenue"}, {}, "v0-test", "2026-09-16")
    with pytest.raises(TypeError):
        persist_annual_facts(conn, preflight)  # authorization arg omitted entirely


def test_persist_refuses_when_overall_gate_failed():
    import dataclasses
    conn = _seeded_conn()
    preflight = compute_persistence_preflight(
        conn, {"revenue", "cost_of_sales", "gross_profit"}, GROSS_PROFIT_DEF, "v0-test", "2026-09-16",
    )
    bad_auth = dataclasses.replace(
        _full_authorization(preflight_fact_count=preflight.total_annual_facts), overall_gate_passed=False,
    )
    with pytest.raises(PersistenceNotAuthorizedError):
        persist_annual_facts(conn, preflight, bad_auth)
    assert conn.execute("SELECT COUNT(*) FROM annual_facts").fetchone()[0] == 0


def test_persist_refuses_when_mapping_gate_has_any_blocked():
    import dataclasses
    conn = _seeded_conn()
    preflight = compute_persistence_preflight(
        conn, {"revenue", "cost_of_sales", "gross_profit"}, GROSS_PROFIT_DEF, "v0-test", "2026-09-16",
    )
    bad_auth = dataclasses.replace(
        _full_authorization(preflight_fact_count=preflight.total_annual_facts),
        mapping_gate_blocked_count=3,
    )
    with pytest.raises(PersistenceNotAuthorizedError):
        persist_annual_facts(conn, preflight, bad_auth)
    assert conn.execute("SELECT COUNT(*) FROM annual_facts").fetchone()[0] == 0


def test_persist_refuses_when_preflight_count_does_not_match_authorization():
    """Guards against a stale authorization being reused against a
    different (e.g. since-changed) preflight plan."""
    conn = _seeded_conn()
    preflight = compute_persistence_preflight(
        conn, {"revenue", "cost_of_sales", "gross_profit"}, GROSS_PROFIT_DEF, "v0-test", "2026-09-16",
    )
    assert preflight.total_annual_facts == 12
    stale_auth = _full_authorization(preflight_fact_count=488)  # the real-project count, not this fixture's 12
    with pytest.raises(PersistenceNotAuthorizedError):
        persist_annual_facts(conn, preflight, stale_auth)


# --- Transactional writer: success, rollback, idempotency -----------------

def test_persist_writes_all_three_tables_atomically_on_success():
    conn = _seeded_conn()
    preflight = compute_persistence_preflight(
        conn, {"revenue", "cost_of_sales", "gross_profit"}, GROSS_PROFIT_DEF, "v0-test", "2026-09-16",
    )
    auth = _full_authorization(preflight_fact_count=preflight.total_annual_facts)
    result = persist_annual_facts(conn, preflight, auth)
    assert result["status"] == "ok"
    assert conn.execute("SELECT COUNT(*) FROM annual_facts").fetchone()[0] == 12
    assert conn.execute("SELECT COUNT(*) FROM annual_fact_observations").fetchone()[0] == 8
    assert conn.execute("SELECT COUNT(*) FROM annual_lineage").fetchone()[0] == 8


def test_persist_is_idempotent_on_repeated_execution():
    conn = _seeded_conn()
    preflight = compute_persistence_preflight(
        conn, {"revenue", "cost_of_sales", "gross_profit"}, GROSS_PROFIT_DEF, "v0-test", "2026-09-16",
    )
    auth = _full_authorization(preflight_fact_count=preflight.total_annual_facts)
    persist_annual_facts(conn, preflight, auth)
    first_count = conn.execute("SELECT COUNT(*) FROM annual_facts").fetchone()[0]
    result2 = persist_annual_facts(conn, preflight, auth)
    assert result2["status"] == "ok"
    second_count = conn.execute("SELECT COUNT(*) FROM annual_facts").fetchone()[0]
    assert first_count == second_count == 12
    assert conn.execute("SELECT COUNT(*) FROM annual_fact_observations").fetchone()[0] == 8
    assert conn.execute("SELECT COUNT(*) FROM annual_lineage").fetchone()[0] == 8


def test_persist_repeated_execution_does_not_duplicate_rows_for_same_key():
    conn = _seeded_conn()
    preflight = compute_persistence_preflight(
        conn, {"revenue"}, {}, "v0-test", "2026-09-16",
    )
    auth = _full_authorization(preflight_fact_count=preflight.total_annual_facts)
    persist_annual_facts(conn, preflight, auth)
    persist_annual_facts(conn, preflight, auth)
    persist_annual_facts(conn, preflight, auth)
    rows = conn.execute(
        "SELECT metric, fiscal_year, analytical_view, COUNT(*) FROM annual_facts "
        "GROUP BY metric, fiscal_year, analytical_view HAVING COUNT(*) > 1"
    ).fetchall()
    assert rows == []


def test_persist_rolls_back_completely_if_a_row_fails_partway():
    """Injects a bad lineage edge (derived_fact_id referencing a fact that
    was never planned/inserted -- annual_lineage has no FK enforced in this
    fixture, so instead we break the CHECK constraint directly: a lineage
    row with BOTH input_raw_fact_id and input_annual_fact_id NULL violates
    the table's XOR CHECK and must abort the whole transaction, including
    the annual_facts rows already staged earlier in the same call.
    """
    import dataclasses
    conn = _seeded_conn()
    preflight = compute_persistence_preflight(
        conn, {"revenue", "cost_of_sales", "gross_profit"}, GROSS_PROFIT_DEF, "v0-test", "2026-09-16",
    )
    broken_edge = dataclasses.replace(preflight.lineage[0], input_annual_fact_id=None)
    preflight.lineage[0] = broken_edge
    auth = _full_authorization(preflight_fact_count=preflight.total_annual_facts)

    with pytest.raises(sqlite3.IntegrityError):
        persist_annual_facts(conn, preflight, auth)

    # Complete rollback: none of the facts staged before the bad lineage
    # row survive -- no partial write.
    assert conn.execute("SELECT COUNT(*) FROM annual_facts").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM annual_fact_observations").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM annual_lineage").fetchone()[0] == 0


# --- Post-persistence integrity (item 6) -----------------------------------

FULL_METRIC_DEFS = {
    "gross_profit": {
        "unit": "USD_millions", "formula": "revenue - cost_of_sales",
        "numerator_metrics": "revenue", "denominator_metrics": "cost_of_sales",
    },
    "finance_lease_liabilities": {
        "unit": "USD_millions", "formula": "finance_lease_liability_current + finance_lease_liability_noncurrent",
        "numerator_metrics": "finance_lease_liability_current;finance_lease_liability_noncurrent", "denominator_metrics": "N/A",
    },
    "long_term_debt_gaap_carrying_value": {
        "unit": "USD_millions",
        "formula": "long_term_debt_gaap_carrying_value_noncurrent + long_term_debt_gaap_carrying_value_current",
        "numerator_metrics": "long_term_debt_gaap_carrying_value_noncurrent;long_term_debt_gaap_carrying_value_current",
        "denominator_metrics": "N/A",
    },
    "adjusted_net_debt_including_finance_leases": {
        "unit": "USD_millions", "formula": "long_term_debt_gaap_carrying_value - cash_and_equivalents_balance_sheet",
        "numerator_metrics": "long_term_debt_gaap_carrying_value", "denominator_metrics": "cash_and_equivalents_balance_sheet",
    },
    "free_cash_flow": {
        "unit": "USD_millions", "formula": "operating_cash_flow - capital_expenditure",
        "numerator_metrics": "operating_cash_flow", "denominator_metrics": "capital_expenditure",
    },
}


def _seeded_conn_full():
    """Extends _seeded_conn with the additional direct metrics needed to
    exercise verify_persistence_integrity's finance-lease and CapEx/CFI
    checks: cash, debt components, finance lease components, CapEx, CFI, CFO.
    """
    conn = _seeded_conn()
    conn.execute(
        "INSERT INTO fiscal_calendar (cik, company_name, fiscal_year, fiscal_quarter, period_start, "
        "period_end, week_count, is_53_week_year, authority_accession) VALUES "
        "('0000027419', 'Target Corporation', 2023, 0, '2022-01-30', '2023-01-28', 53, 1, 'acc-2024')"
    )
    for fy, acc, start, end, cash, ltd_nc, ltd_cur, fl_cur, fl_nc, capex, cfi, cfo in (
        (2024, "acc-2024", "2023-01-29", "2024-02-03", 4762.0, 14304.0, 1636.0, 136.0, 2025.0, 2891.0, -1234.0, 5978.0),
        (2025, "acc-2025", "2024-02-04", "2025-02-01", 5488.0, 14326.0, 2130.0, 131.0, 1982.0, 3727.0, -3649.0, 6562.0),
    ):
        rows = [
            ("cash_and_equivalents_balance_sheet", "CashCashEquivalentsAndShortTermInvestments", None, end, cash),
            ("long_term_debt_gaap_carrying_value_noncurrent", "LongTermDebtAndCapitalLeaseObligations", None, end, ltd_nc),
            ("long_term_debt_gaap_carrying_value_current", "LongTermDebtAndCapitalLeaseObligationsCurrent", None, end, ltd_cur),
            ("finance_lease_liability_current", "FinanceLeaseLiabilityCurrent", None, end, fl_cur),
            ("finance_lease_liability_noncurrent", "FinanceLeaseLiabilityNoncurrent", None, end, fl_nc),
        ]
        for metric, tag, s, e, val in rows:
            conn.execute(
                "INSERT INTO raw_facts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (f"rf_{metric}_{fy}", acc, "us-gaap", tag, "USD", s, e, "c-x", None,
                 str(val * 1_000_000), 6, 1, 0, "2026-09-16T00:00:00Z"),
            )
        for metric, tag, val in (
            ("capital_expenditure", "PaymentsToAcquirePropertyPlantAndEquipment", capex),
            ("investing_cash_flow", "NetCashProvidedByUsedInInvestingActivities", cfi),
            ("operating_cash_flow", "NetCashProvidedByUsedInOperatingActivities", cfo),
        ):
            conn.execute(
                "INSERT INTO raw_facts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (f"rf_{metric}_{fy}", acc, "us-gaap", tag, "USD", start, end, "c-y", None,
                 str(val * 1_000_000), 6, 1, 0, "2026-09-16T00:00:00Z"),
            )
    conn.commit()
    return conn


FULL_ELIGIBLE = {
    "revenue", "cost_of_sales", "gross_profit",
    "cash_and_equivalents_balance_sheet",
    "long_term_debt_gaap_carrying_value_noncurrent", "long_term_debt_gaap_carrying_value_current",
    "finance_lease_liability_current", "finance_lease_liability_noncurrent",
    "finance_lease_liabilities", "long_term_debt_gaap_carrying_value", "adjusted_net_debt_including_finance_leases",
    "capital_expenditure", "investing_cash_flow", "operating_cash_flow", "free_cash_flow",
}


def test_verify_persistence_integrity_all_checks_pass_on_a_clean_persist():
    from target_cash.annual_persistence import verify_persistence_integrity

    conn = _seeded_conn_full()
    preflight = compute_persistence_preflight(conn, FULL_ELIGIBLE, FULL_METRIC_DEFS, "v0-test", "2026-09-16")
    auth = _full_authorization(preflight_fact_count=preflight.total_annual_facts)
    persist_annual_facts(conn, preflight, auth)

    report = verify_persistence_integrity(conn)
    failed = {name: c for name, c in report["checks"].items() if not c["passed"]}
    assert failed == {}, failed
    assert report["all_passed"] is True


def test_verify_persistence_integrity_detects_orphan_observation():
    from target_cash.annual_persistence import verify_persistence_integrity

    conn = _seeded_conn_full()
    preflight = compute_persistence_preflight(conn, FULL_ELIGIBLE, FULL_METRIC_DEFS, "v0-test", "2026-09-16")
    auth = _full_authorization(preflight_fact_count=preflight.total_annual_facts)
    persist_annual_facts(conn, preflight, auth)

    conn.execute(
        "INSERT INTO annual_fact_observations "
        "(observation_id, annual_fact_id, raw_fact_id, accession_number, filed_at, relationship, value_original, classification_rationale) "
        "VALUES ('orphan_obs', 'annual:nonexistent:2025:as_originally_filed', 'rf_x', 'acc-2025', '2025-03-01', 'selected', 1.0, 'test-injected orphan')"
    )
    conn.commit()

    report = verify_persistence_integrity(conn)
    assert report["checks"]["zero_orphan_observations"]["passed"] is False
    assert report["all_passed"] is False


def test_verify_persistence_integrity_detects_duplicate_canonical_key():
    from target_cash.annual_persistence import verify_persistence_integrity

    conn = _seeded_conn_full()
    preflight = compute_persistence_preflight(conn, FULL_ELIGIBLE, FULL_METRIC_DEFS, "v0-test", "2026-09-16")
    auth = _full_authorization(preflight_fact_count=preflight.total_annual_facts)
    persist_annual_facts(conn, preflight, auth)

    # Bypass the annual_fact_id PRIMARY KEY (different id, same canonical
    # metric/fiscal_year/analytical_view) to exercise the UNIQUE(metric,
    # fiscal_year, analytical_view) constraint's own detection path.
    row = conn.execute("SELECT * FROM annual_facts WHERE metric = 'revenue' AND fiscal_year = 2025 AND analytical_view = 'as_originally_filed'").fetchone()
    cols = [d[0] for d in conn.execute("SELECT * FROM annual_facts LIMIT 1").description]
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            f"INSERT INTO annual_facts ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
            ("annual:revenue:2025:as_originally_filed:duplicate",) + row[1:],
        )


def test_verify_persistence_integrity_capex_distinct_from_cfi_on_real_fy2025_figures():
    from target_cash.annual_persistence import verify_persistence_integrity

    conn = _seeded_conn_full()
    preflight = compute_persistence_preflight(conn, FULL_ELIGIBLE, FULL_METRIC_DEFS, "v0-test", "2026-09-16")
    auth = _full_authorization(preflight_fact_count=preflight.total_annual_facts)
    persist_annual_facts(conn, preflight, auth)

    capex = conn.execute(
        "SELECT value_normalized FROM annual_facts WHERE metric='capital_expenditure' AND fiscal_year=2025 AND analytical_view='as_originally_filed'"
    ).fetchone()[0]
    cfi = conn.execute(
        "SELECT value_normalized FROM annual_facts WHERE metric='investing_cash_flow' AND fiscal_year=2025 AND analytical_view='as_originally_filed'"
    ).fetchone()[0]
    assert capex == 3727.0
    assert cfi == -3649.0
    assert capex != abs(cfi)

    report = verify_persistence_integrity(conn)
    assert report["checks"]["capex_remains_distinct_from_cfi"]["passed"] is True


def test_verify_persistence_integrity_finance_leases_not_double_counted_on_real_figures():
    from target_cash.annual_persistence import verify_persistence_integrity

    conn = _seeded_conn_full()
    preflight = compute_persistence_preflight(conn, FULL_ELIGIBLE, FULL_METRIC_DEFS, "v0-test", "2026-09-16")
    auth = _full_authorization(preflight_fact_count=preflight.total_annual_facts)
    persist_annual_facts(conn, preflight, auth)

    ltd = conn.execute(
        "SELECT value_normalized FROM annual_facts WHERE metric='long_term_debt_gaap_carrying_value' AND fiscal_year=2025 AND analytical_view='as_originally_filed'"
    ).fetchone()[0]
    cash = conn.execute(
        "SELECT value_normalized FROM annual_facts WHERE metric='cash_and_equivalents_balance_sheet' AND fiscal_year=2025 AND analytical_view='as_originally_filed'"
    ).fetchone()[0]
    adjusted = conn.execute(
        "SELECT value_normalized FROM annual_facts WHERE metric='adjusted_net_debt_including_finance_leases' AND fiscal_year=2025 AND analytical_view='as_originally_filed'"
    ).fetchone()[0]
    assert ltd == 14326.0 + 2130.0  # noncurrent + current, both already include finance leases
    assert adjusted == ltd - cash  # never ltd + finance_lease_liabilities again

    report = verify_persistence_integrity(conn)
    assert report["checks"]["finance_leases_not_double_counted"]["passed"] is True
