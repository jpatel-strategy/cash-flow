"""Unit tests for target_cash.annual.validate_annual / summarize_annual_validation.

Builds a minimal in-memory database seeded with just enough raw_facts and
fiscal_calendar rows to exercise each check category, rather than depending
on the real curated database (which is exercised separately by running
`target_cash.cli validate` against it).
"""
import sqlite3

import pytest

from target_cash.annual import (
    ALLOWED_PERMANENTLY_UNAVAILABLE_METRICS,
    FISCAL_YEARS,
    summarize_annual_validation,
    validate_annual,
)


def _empty_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE filings (
            accession_number TEXT PRIMARY KEY, cik TEXT, company_name TEXT, form_type TEXT,
            filed_at TEXT, period_of_report TEXT, primary_document_url TEXT,
            downloaded_at TEXT, file_hash TEXT, ingestion_method TEXT, notes TEXT
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
        CREATE TABLE fiscal_calendar (
            cik TEXT, company_name TEXT, fiscal_year INTEGER, fiscal_quarter INTEGER,
            period_start TEXT, period_end TEXT, week_count INTEGER, is_53_week_year INTEGER,
            authority_accession TEXT, PRIMARY KEY (cik, fiscal_year, fiscal_quarter)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE concept_equivalence_rules (
            rule_id TEXT PRIMARY KEY, rule_version TEXT, company_scope TEXT, canonical_metric TEXT,
            source_concept TEXT, canonical_concept TEXT, effective_fiscal_years TEXT,
            accounting_rationale TEXT, evidence_reference TEXT, review_status TEXT,
            mapping_version TEXT, superseded_by_rule_id TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE annual_facts (
            annual_fact_id TEXT PRIMARY KEY, metric TEXT, fiscal_year INTEGER, period_start TEXT,
            period_end TEXT, days_in_period INTEGER, analytical_view TEXT, value_original REAL,
            original_unit TEXT, value_normalized REAL, normalized_unit TEXT, direct_or_derived TEXT,
            fact_status TEXT, validation_status TEXT, accession_number TEXT, filed_at TEXT,
            mapping_version TEXT, information_cutoff TEXT, is_current_view INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE annual_lineage (
            annual_lineage_id TEXT PRIMARY KEY, derived_fact_id TEXT, input_raw_fact_id TEXT,
            input_annual_fact_id TEXT, operation TEXT, sequence INTEGER, coefficient REAL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE annual_fact_observations (
            observation_id TEXT PRIMARY KEY, annual_fact_id TEXT, raw_fact_id TEXT,
            accession_number TEXT, filed_at TEXT, relationship TEXT, value_original REAL,
            difference_from_selected REAL, classification_rationale TEXT
        )
        """
    )
    return conn


def test_validate_annual_on_empty_database_blocks_never_fails():
    """With no fiscal_calendar and no raw_facts seeded, every year-level check
    must come back BLOCKED/UNAVAILABLE/NOT_APPLICABLE, never FAIL -- an
    unseeded database is a missing-input state, not a disagreement."""
    conn = _empty_conn()
    results = validate_annual(conn)
    summary = summarize_annual_validation(results)
    assert summary["by_status"]["FAIL"] == 0
    assert summary["gate_passed"] is True
    assert summary["checks_run"] > 0


def test_summarize_annual_validation_fails_gate_on_any_fail():
    from target_cash.annual import AnnualCheckResult
    results = [
        AnnualCheckResult("gross_profit_derivation", 2025, "as_filed", "PASS", ""),
        AnnualCheckResult("operating_income_bridge", 2025, "as_filed", "FAIL", "arithmetic disagreement"),
    ]
    summary = summarize_annual_validation(results)
    assert summary["gate_passed"] is False
    assert summary["by_status"]["FAIL"] == 1


def test_summarize_annual_validation_never_fails_gate_on_blocked_or_unavailable():
    from target_cash.annual import AnnualCheckResult
    results = [
        AnnualCheckResult("gross_profit_derivation", 2025, "as_filed", "BLOCKED", ""),
        AnnualCheckResult("target_defined_net_debt_policy", 2025, "as_filed", "UNAVAILABLE", ""),
        AnnualCheckResult("lineage_readiness", 2025, "as_filed", "NOT_APPLICABLE", ""),
    ]
    summary = summarize_annual_validation(results)
    assert summary["gate_passed"] is True


def test_target_defined_net_debt_is_the_only_allowed_permanently_unavailable_metric():
    assert ALLOWED_PERMANENTLY_UNAVAILABLE_METRICS == {"target_defined_net_debt"}


def test_validate_annual_covers_every_required_category():
    conn = _empty_conn()
    results = validate_annual(conn)
    categories = {r.category for r in results}
    required = {
        "income_statement_arithmetic", "gross_profit_derivation", "operating_income_bridge",
        "pretax_income_bridge", "net_income_bridge", "eps_consistency", "cfo_and_fcf",
        "cash_movement_and_composition", "debt_bridge", "authoritative_source_selection",
        "analytical_view_selection", "concept_equivalence_scope", "fiscal_calendar_mapping",
        "lineage_readiness", "fifty_three_week_disclosure", "target_defined_net_debt_policy",
    }
    assert required <= categories


def test_validate_annual_covers_all_five_fiscal_years():
    conn = _empty_conn()
    results = validate_annual(conn)
    years = {r.fiscal_year for r in results}
    assert years == set(FISCAL_YEARS)


def test_fifty_three_week_disclosure_passes_only_for_the_seeded_fy2023_row():
    conn = _empty_conn()
    conn.execute(
        "INSERT INTO fiscal_calendar (cik, company_name, fiscal_year, fiscal_quarter, period_start, "
        "period_end, week_count, is_53_week_year, authority_accession) VALUES "
        "('0000027419', 'Target Corporation', 2023, 0, '2023-01-29', '2024-02-03', 53, 1, 'acc-2023')"
    )
    conn.commit()
    results = validate_annual(conn)
    fy2023_check = next(r for r in results if r.category == "fifty_three_week_disclosure" and r.fiscal_year == 2023)
    assert fy2023_check.status == "PASS"


def test_fifty_three_week_disclosure_fails_if_fy2023_is_not_marked_53_weeks():
    conn = _empty_conn()
    conn.execute(
        "INSERT INTO fiscal_calendar (cik, company_name, fiscal_year, fiscal_quarter, period_start, "
        "period_end, week_count, is_53_week_year, authority_accession) VALUES "
        "('0000027419', 'Target Corporation', 2023, 0, '2023-01-29', '2024-01-27', 52, 0, 'acc-2023')"
    )
    conn.commit()
    results = validate_annual(conn)
    fy2023_check = next(r for r in results if r.category == "fifty_three_week_disclosure" and r.fiscal_year == 2023)
    assert fy2023_check.status == "FAIL"


def _lineage_readiness_check(results, fiscal_year):
    return next(r for r in results if r.category == "lineage_readiness" and r.fiscal_year == fiscal_year)


def test_lineage_readiness_is_not_applicable_when_nothing_persisted():
    """The pre-persistence state required by this milestone: annual_facts is
    empty, so lineage_readiness is NOT_APPLICABLE -- but this is now a real
    query result (COUNT(*) == 0), not a hardcoded literal."""
    conn = _empty_conn()
    results = validate_annual(conn)
    assert _lineage_readiness_check(results, 2025).status == "NOT_APPLICABLE"


def test_lineage_readiness_passes_when_persisted_facts_have_complete_lineage():
    """2026-09-15 item 8: 'After persistence, lineage_readiness must become
    PASS.' A direct fact needs >=1 selected annual_fact_observations row; a
    derived fact needs >=1 annual_lineage row pointing to it."""
    conn = _empty_conn()
    conn.execute(
        "INSERT INTO annual_facts VALUES "
        "('af_revenue_2025_orig', 'revenue', 2025, '2025-02-02', '2026-01-31', 364, "
        "'as_originally_filed', 106566000000, 'USD', 106566.0, 'USD_millions', 'direct', "
        "'authoritative', 'unvalidated', 'acc-2025', '2026-03-15', 'v0', '2026-09-15', 1)"
    )
    conn.execute(
        "INSERT INTO annual_fact_observations VALUES "
        "('obs_1', 'af_revenue_2025_orig', 'rf_revenue_2025', 'acc-2025', '2026-03-15', "
        "'selected', 106566000000, NULL, 'authoritative 10-K value')"
    )
    conn.execute(
        "INSERT INTO annual_facts VALUES "
        "('af_gross_profit_2025_orig', 'gross_profit', 2025, '2025-02-02', '2026-01-31', 364, "
        "'as_originally_filed', 33000000000, 'USD', 33000.0, 'USD_millions', 'derived', "
        "'authoritative', 'unvalidated', 'acc-2025', '2026-03-15', 'v0', '2026-09-15', 1)"
    )
    conn.execute(
        "INSERT INTO annual_lineage VALUES "
        "('lin_1', 'af_gross_profit_2025_orig', NULL, 'af_revenue_2025_orig', 'subtract', 1, NULL)"
    )
    conn.commit()
    results = validate_annual(conn)
    check = _lineage_readiness_check(results, 2025)
    assert check.status == "PASS"
    assert "2" in check.detail  # both persisted rows accounted for


def test_lineage_readiness_fails_when_a_persisted_fact_is_missing_its_lineage():
    """A direct fact persisted with no annual_fact_observations row (or a
    derived fact with no annual_lineage row) is a partial/corrupted write --
    must FAIL, never silently pass or stay NOT_APPLICABLE."""
    conn = _empty_conn()
    conn.execute(
        "INSERT INTO annual_facts VALUES "
        "('af_revenue_2025_orig', 'revenue', 2025, '2025-02-02', '2026-01-31', 364, "
        "'as_originally_filed', 106566000000, 'USD', 106566.0, 'USD_millions', 'direct', "
        "'authoritative', 'unvalidated', 'acc-2025', '2026-03-15', 'v0', '2026-09-15', 1)"
    )
    # No annual_fact_observations row inserted for it -- the gap.
    conn.commit()
    results = validate_annual(conn)
    check = _lineage_readiness_check(results, 2025)
    assert check.status == "FAIL"
    assert "revenue" in check.detail


def test_analytical_view_selection_treats_canonical_aliases_as_reclassified_too():
    """Regression guard: config/metric_definitions.csv canonical-name aliases
    of an already-known-reclassified metric (e.g. shareholder_distributions_to_fcf
    aliasing distributions_pct_fcf) must not trip analytical_view_selection just
    because the alias's own name isn't separately registered in
    KNOWN_RECLASSIFIED_METRICS -- this exact gap shipped and was caught by
    running `validate` against the real database (FY2021 FAIL) before being
    fixed by adding the alias names alongside their legacy counterparts.
    """
    from target_cash.annual import KNOWN_RECLASSIFIED_METRICS
    assert "gross_margin_pct" in KNOWN_RECLASSIFIED_METRICS
    assert "gross_margin" in KNOWN_RECLASSIFIED_METRICS
    assert "distributions_pct_fcf" in KNOWN_RECLASSIFIED_METRICS
    assert "shareholder_distributions_to_fcf" in KNOWN_RECLASSIFIED_METRICS

    conn = _empty_conn()
    conn.execute(
        "INSERT INTO fiscal_calendar (cik, company_name, fiscal_year, fiscal_quarter, period_start, "
        "period_end, week_count, is_53_week_year, authority_accession) VALUES "
        "('0000027419', 'Target Corporation', 2021, 0, '2021-02-03', '2022-01-29', 52, 0, 'acc-2021')"
    )
    conn.commit()
    results = validate_annual(conn)
    view_selection_2021 = [r for r in results if r.category == "analytical_view_selection" and r.fiscal_year == 2021]
    assert all(r.status != "FAIL" for r in view_selection_2021)
