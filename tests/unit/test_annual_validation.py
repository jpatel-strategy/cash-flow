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
