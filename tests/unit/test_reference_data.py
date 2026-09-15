import sqlite3

import pytest

from target_cash.migrations import apply_safe_migrations
from target_cash.reference_data import (
    CONCEPT_EQUIVALENCE_RULES,
    FISCAL_CALENDAR_ROWS,
    find_period_overlaps,
    seed_concept_equivalence_rules,
    seed_fiscal_calendar,
)


def make_migrated_db():
    conn = sqlite3.connect(":memory:")
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
    return conn


def test_seed_fiscal_calendar_inserts_all_rows_idempotently():
    conn = make_migrated_db()
    first = seed_fiscal_calendar(conn)
    assert first == len(FISCAL_CALENDAR_ROWS)
    second = seed_fiscal_calendar(conn)
    assert second == 0  # idempotent -- nothing new on rerun
    count = conn.execute("SELECT COUNT(*) FROM fiscal_calendar").fetchone()[0]
    assert count == len(FISCAL_CALENDAR_ROWS)


def test_seed_fiscal_calendar_fy2023_is_53_weeks():
    conn = make_migrated_db()
    seed_fiscal_calendar(conn)
    row = conn.execute(
        "SELECT week_count, is_53_week_year, authority_accession FROM fiscal_calendar "
        "WHERE fiscal_year = 2023 AND fiscal_quarter = 0"
    ).fetchone()
    assert row == (53, 1, "0000027419-24-000032")


def test_seed_fiscal_calendar_fy2019_fy2020_have_no_authority_accession():
    conn = make_migrated_db()
    seed_fiscal_calendar(conn)
    for fy in (2019, 2020):
        accession = conn.execute(
            "SELECT authority_accession FROM fiscal_calendar WHERE fiscal_year = ? AND fiscal_quarter = 0", (fy,)
        ).fetchone()[0]
        assert accession is None  # comparative-only years, no filing held for their own primary period


def test_find_period_overlaps_detects_a_genuine_overlap():
    rows = [
        dict(fiscal_year=2021, fiscal_quarter=0, period_start="2021-01-31", period_end="2022-01-29"),
        dict(fiscal_year=2022, fiscal_quarter=0, period_start="2022-01-01", period_end="2023-01-28"),  # overlaps 2021
    ]
    overlaps = find_period_overlaps(rows)
    assert len(overlaps) == 1


def test_find_period_overlaps_does_not_flag_annual_containing_its_own_quarters():
    rows = [
        dict(fiscal_year=2025, fiscal_quarter=0, period_start="2025-02-02", period_end="2026-01-31"),
        dict(fiscal_year=2025, fiscal_quarter=1, period_start="2025-02-02", period_end="2025-05-03"),
    ]
    assert find_period_overlaps(rows) == []


def test_seed_fiscal_calendar_refuses_overlapping_rows():
    conn = make_migrated_db()
    bad_rows = FISCAL_CALENDAR_ROWS + (
        dict(fiscal_year=2021, fiscal_quarter=0, period_start="2021-06-01", period_end="2022-06-01",
             week_count=52, is_53_week_year=0, authority_accession=None),
    )
    with pytest.raises(ValueError, match="overlap"):
        seed_fiscal_calendar(conn, bad_rows)
    # Nothing partially seeded.
    assert conn.execute("SELECT COUNT(*) FROM fiscal_calendar").fetchone()[0] == 0


def test_seed_concept_equivalence_rules_inserts_both_rules_idempotently():
    conn = make_migrated_db()
    first = seed_concept_equivalence_rules(conn)
    assert first == len(CONCEPT_EQUIVALENCE_RULES)
    second = seed_concept_equivalence_rules(conn)
    assert second == 0
    rule_ids = {r[0] for r in conn.execute("SELECT rule_id FROM concept_equivalence_rules")}
    assert rule_ids == {"rule_interest_expense_v1", "rule_net_income_fy2021_v1"}


def test_net_income_equivalence_rule_is_scoped_to_fy2021_only():
    conn = make_migrated_db()
    seed_concept_equivalence_rules(conn)
    scope = conn.execute(
        "SELECT effective_fiscal_years FROM concept_equivalence_rules WHERE rule_id = 'rule_net_income_fy2021_v1'"
    ).fetchone()[0]
    assert scope == "FY2021 only"


def test_seeding_reference_data_leaves_annual_tables_empty():
    conn = make_migrated_db()
    seed_fiscal_calendar(conn)
    seed_concept_equivalence_rules(conn)
    for table in ("annual_facts", "annual_lineage", "annual_fact_observations"):
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


# --- period_facts_unified: the required fiscal-year-mapping proof (2026-09-15) ------


def test_period_facts_unified_maps_instant_to_authoritative_fiscal_year_not_calendar_year():
    """An instant dated 2025-02-01 is Target's FY2024 year-end, not calendar-year
    FY2025 -- exactly the inference the reviewer required period_facts_unified to
    avoid. This seeds one instant_facts row at that date and asserts the view
    reports fiscal_year=2024 via the fiscal_calendar join, not 2025."""
    conn = make_migrated_db()
    seed_fiscal_calendar(conn)
    conn.execute(
        """
        INSERT INTO instant_facts
            (instant_fact_id, metric, as_of_date, accounting_basis, consolidated_scope, analytical_view,
             selected_raw_fact_id, authoritative_source_reason, value_original, original_unit, scale,
             value_normalized, normalized_unit, accession_number, filed_at, restatement_status,
             mapping_version, selection_status, information_cutoff, is_current_view)
        VALUES
            ('if_1', 'cash_and_equivalents_balance_sheet', '2025-02-01', 'US-GAAP-FY2024-Workiva',
             'consolidated', 'as_originally_filed', 'rf_1', 'own primary period', 4762000000.0, 'USD',
             6, 4762.0, 'USD_millions', '0000027419-25-000018', '2025-03-12', 'as_originally_filed',
             'v0', 'safe', '2026-09-15T00:00:00Z', 1)
        """
    )
    conn.commit()

    row = conn.execute(
        "SELECT fiscal_year, fiscal_quarter, frequency, end_date, value FROM period_facts_unified "
        "WHERE metric = 'cash_and_equivalents_balance_sheet' AND end_date = '2025-02-01'"
    ).fetchone()
    assert row is not None
    fiscal_year, fiscal_quarter, frequency, end_date, value = row
    assert frequency == "instant"
    assert end_date == "2025-02-01"
    assert value == 4762.0
    assert fiscal_year == 2024, (
        f"instant 2025-02-01 must map to FY2024 (Target's own fiscal year-end label), "
        f"not calendar year 2025 -- got fiscal_year={fiscal_year}"
    )
    assert fiscal_quarter is None  # annual-grain fiscal_calendar row -> NULLIF(0, 0) -> NULL


def test_period_facts_unified_instant_without_calendar_row_returns_null_fiscal_year_not_a_guess():
    """An as_of_date with no matching fiscal_calendar row must surface as NULL,
    never a calendar-year-derived guess."""
    conn = make_migrated_db()
    seed_fiscal_calendar(conn)
    conn.execute(
        """
        INSERT INTO instant_facts
            (instant_fact_id, metric, as_of_date, accounting_basis, consolidated_scope, analytical_view,
             selected_raw_fact_id, authoritative_source_reason, value_original, original_unit, scale,
             value_normalized, normalized_unit, accession_number, filed_at, restatement_status,
             mapping_version, selection_status, information_cutoff, is_current_view)
        VALUES
            ('if_2', 'inventory', '2018-02-03', 'US-GAAP-FY2017-Workiva', 'consolidated',
             'as_originally_filed', 'rf_2', 'own primary period', 1.0, 'USD', 6, 1.0, 'USD_millions',
             '0000000000-00-000000', '2018-03-01', 'as_originally_filed', 'v0', 'safe',
             '2026-09-15T00:00:00Z', 1)
        """
    )
    conn.commit()
    row = conn.execute(
        "SELECT fiscal_year FROM period_facts_unified WHERE metric = 'inventory' AND end_date = '2018-02-03'"
    ).fetchone()
    assert row == (None,)


def test_period_facts_unified_does_not_duplicate_an_instant_at_a_fiscal_year_end():
    """A fiscal year-end date (e.g. 2026-01-31) is simultaneously that year's own
    annual period_end AND its Q4 period_end -- fiscal_calendar deliberately has a
    row for each. One instant_facts row at that date must produce exactly one
    period_facts_unified row (the annual grain, fiscal_quarter NULL), never two."""
    conn = make_migrated_db()
    seed_fiscal_calendar(conn)
    conn.execute(
        """
        INSERT INTO instant_facts
            (instant_fact_id, metric, as_of_date, accounting_basis, consolidated_scope, analytical_view,
             selected_raw_fact_id, authoritative_source_reason, value_original, original_unit, scale,
             value_normalized, normalized_unit, accession_number, filed_at, restatement_status,
             mapping_version, selection_status, information_cutoff, is_current_view)
        VALUES
            ('if_3', 'cash_and_equivalents_balance_sheet', '2026-01-31', 'US-GAAP-FY2025-Workiva',
             'consolidated', 'as_originally_filed', 'rf_3', 'own primary period', 5488000000.0, 'USD',
             6, 5488.0, 'USD_millions', '0000027419-26-000016', '2026-03-11', 'as_originally_filed',
             'v0', 'safe', '2026-09-15T00:00:00Z', 1)
        """
    )
    conn.commit()

    rows = conn.execute(
        "SELECT fiscal_year, fiscal_quarter FROM period_facts_unified "
        "WHERE metric = 'cash_and_equivalents_balance_sheet' AND end_date = '2026-01-31'"
    ).fetchall()
    assert len(rows) == 1, f"expected exactly one row, got {len(rows)}: {rows}"
    assert rows[0] == (2025, None)  # annual grain (fiscal_quarter sentinel 0 -> NULLIF -> NULL), not Q4


def test_period_facts_unified_never_duplicates_any_instant_fact():
    """General-purpose guard: with the real fiscal_calendar seeded, every
    as_of_date shared between an annual and a quarterly fiscal_calendar row
    (i.e. every fiscal year-end) must still resolve to exactly one row per
    instant fact -- not just the FY2025 case spelled out above."""
    conn = make_migrated_db()
    seed_fiscal_calendar(conn)
    for i, as_of_date in enumerate(["2025-02-01", "2026-01-31", "2025-05-03"]):
        conn.execute(
            """
            INSERT INTO instant_facts
                (instant_fact_id, metric, as_of_date, accounting_basis, consolidated_scope, analytical_view,
                 selected_raw_fact_id, authoritative_source_reason, value_original, original_unit, scale,
                 value_normalized, normalized_unit, accession_number, filed_at, restatement_status,
                 mapping_version, selection_status, information_cutoff, is_current_view)
            VALUES (?, 'inventory', ?, 'basis', 'consolidated', 'as_originally_filed', ?, 'reason', 1.0, 'USD',
                    6, 1.0, 'USD_millions', '0000027419-26-000016', '2026-03-11', 'as_originally_filed',
                    'v0', 'safe', '2026-09-15T00:00:00Z', 1)
            """,
            (f"if_dup_{i}", as_of_date, f"rf_dup_{i}"),
        )
    conn.commit()
    rows = conn.execute(
        "SELECT end_date, COUNT(*) FROM period_facts_unified WHERE metric = 'inventory' GROUP BY end_date"
    ).fetchall()
    assert all(count == 1 for _, count in rows), f"a date produced more than one row: {rows}"
    assert len(rows) == 3
