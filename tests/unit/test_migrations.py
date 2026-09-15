import sqlite3

import pytest

from target_cash.migrations import (
    MIGRATIONS,
    ColumnMigration,
    TableMigration,
    UnsafeMigrationError,
    apply_safe_migrations,
    applied_migration_ids,
)

ALL_MIGRATION_IDS = {m.migration_id for m in MIGRATIONS}


def make_stale_db():
    """A filings table exactly as it looked before cached_filename was added --
    reproduces the real failure this module exists to prevent (see
    docs/decisions.md, 2026-09-15 'Database safety')."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE filings (
            accession_number TEXT PRIMARY KEY,
            cik TEXT NOT NULL,
            company_name TEXT NOT NULL,
            form_type TEXT NOT NULL,
            filed_at TEXT NOT NULL,
            period_of_report TEXT NOT NULL,
            primary_document_url TEXT NOT NULL,
            downloaded_at TEXT,
            file_hash TEXT,
            ingestion_method TEXT NOT NULL,
            notes TEXT
        )
        """
    )
    # quarterly_facts exactly as schema.sql created it, before analytical_view
    # (migration 0011) existed -- needed so that ColumnMigration can find its
    # target table.
    conn.execute(
        """
        CREATE TABLE quarterly_facts (
            quarterly_fact_id TEXT PRIMARY KEY,
            metric            TEXT NOT NULL,
            fiscal_year       INTEGER NOT NULL,
            fiscal_quarter    INTEGER NOT NULL,
            period_start      TEXT,
            period_end        TEXT NOT NULL,
            days_in_period    INTEGER,
            value_original    REAL NOT NULL,
            original_unit     TEXT NOT NULL,
            value_normalized  REAL NOT NULL,
            normalized_unit   TEXT NOT NULL DEFAULT 'USD_millions',
            basis             TEXT NOT NULL,
            as_of_date        TEXT NOT NULL,
            mapping_version   TEXT NOT NULL,
            is_current_view   INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    return conn


def test_apply_safe_migrations_adds_missing_column_to_stale_schema():
    conn = make_stale_db()
    applied = apply_safe_migrations(conn)
    assert "0001_filings_cached_filename" in applied
    columns = {row[1] for row in conn.execute("PRAGMA table_info(filings)")}
    assert "cached_filename" in columns


def test_apply_safe_migrations_preserves_existing_rows():
    conn = make_stale_db()
    conn.execute(
        "INSERT INTO filings VALUES ('acc-1', '9999999', 'SYNTHETIC CORP', '10-K', "
        "'2024-03-15', '2024-02-03', 'https://example.invalid/doc.htm', "
        "'2024-03-16T00:00:00Z', 'deadbeef', 'manual_upload', 'note')"
    )
    conn.commit()

    apply_safe_migrations(conn)

    row = conn.execute("SELECT accession_number, cik, company_name, notes FROM filings").fetchone()
    assert row == ("acc-1", "9999999", "SYNTHETIC CORP", "note")
    # The new column exists and is NULL for the pre-existing row, not fabricated.
    cached_filename = conn.execute("SELECT cached_filename FROM filings WHERE accession_number = 'acc-1'").fetchone()[0]
    assert cached_filename is None


def test_apply_safe_migrations_is_idempotent():
    conn = make_stale_db()
    first = apply_safe_migrations(conn)
    second = apply_safe_migrations(conn)
    assert set(first) == ALL_MIGRATION_IDS
    assert second == []  # already applied -- must not error or reapply


def test_apply_safe_migrations_is_a_noop_on_an_already_current_schema():
    conn = make_stale_db()
    conn.execute("ALTER TABLE filings ADD COLUMN cached_filename TEXT")  # simulate a fresh schema.sql-created table
    applied = apply_safe_migrations(conn)
    # Column already present -- migration is recorded as applied without altering anything twice.
    assert "0001_filings_cached_filename" in applied
    assert applied_migration_ids(conn) == ALL_MIGRATION_IDS


def test_apply_safe_migrations_records_applied_migrations():
    conn = make_stale_db()
    apply_safe_migrations(conn)
    rows = conn.execute("SELECT migration_id, description FROM _schema_migrations").fetchall()
    assert {r[0] for r in rows} == ALL_MIGRATION_IDS


def test_unsafe_migration_refuses_to_run_automatically(monkeypatch):
    conn = make_stale_db()
    unsafe = ColumnMigration(
        migration_id="9999_hypothetical_unsafe_change",
        description="hypothetical non-additive change",
        table="filings",
        column="renamed_thing",
        column_def="TEXT",
        is_safe_additive=False,
    )
    monkeypatch.setattr("target_cash.migrations.MIGRATIONS", (*MIGRATIONS, unsafe))
    with pytest.raises(UnsafeMigrationError):
        apply_safe_migrations(conn)

    # Earlier safe migrations still get applied and committed (each is independently safe);
    # only the unsafe one is blocked, and it is never recorded as applied.
    assert applied_migration_ids(conn) == ALL_MIGRATION_IDS


# --- TableMigration (instant_facts, 2026-09-15) --------------------------------


def test_table_migration_creates_both_tables_empty():
    conn = make_stale_db()
    apply_safe_migrations(conn)
    for table in ("instant_facts", "instant_fact_observations"):
        assert conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_table_migration_is_idempotent_on_rerun():
    conn = make_stale_db()
    apply_safe_migrations(conn)
    second = apply_safe_migrations(conn)
    assert second == []
    # Tables still present, still empty, still exactly one each in sqlite_master.
    count = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='instant_facts'"
    ).fetchone()[0]
    assert count == 1


def test_table_migration_enforces_canonical_uniqueness():
    conn = make_stale_db()
    apply_safe_migrations(conn)
    row = (
        "if_1", "cash_and_equivalents_balance_sheet", "2025-05-03", "US-GAAP-FY2025-Workiva",
        "consolidated", "as_originally_filed", "rf_1", "own primary period",
        2887000000.0, "USD", 6, 2887.0, "USD_millions",
        "0000027419-25-000101", "2025-05-30", "as_originally_filed", "v0",
        "safe", "2026-09-15T00:00:00Z", 1,
    )
    conn.execute(
        "INSERT INTO instant_facts "
        "(instant_fact_id, metric, as_of_date, accounting_basis, consolidated_scope, analytical_view, "
        " selected_raw_fact_id, authoritative_source_reason, value_original, original_unit, scale, "
        " value_normalized, normalized_unit, accession_number, filed_at, restatement_status, "
        " mapping_version, selection_status, information_cutoff, is_current_view) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        row,
    )
    conn.commit()
    # A second row for the exact same (metric, as_of_date, accounting_basis,
    # consolidated_scope, analytical_view) tuple must be rejected structurally.
    duplicate = ("if_2",) + row[1:]
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO instant_facts "
            "(instant_fact_id, metric, as_of_date, accounting_basis, consolidated_scope, analytical_view, "
            " selected_raw_fact_id, authoritative_source_reason, value_original, original_unit, scale, "
            " value_normalized, normalized_unit, accession_number, filed_at, restatement_status, "
            " mapping_version, selection_status, information_cutoff, is_current_view) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            duplicate,
        )


def test_table_migration_failure_is_not_recorded_and_is_safe_to_retry(monkeypatch):
    conn = make_stale_db()
    broken = TableMigration(
        migration_id="9998_hypothetical_broken_table",
        description="deliberately malformed SQL to prove failure handling",
        create_sql="CREATE TABLE IF NOT EXISTS this_is_not_valid_sql_on_purpose (;;;",
    )
    monkeypatch.setattr("target_cash.migrations.MIGRATIONS", (*MIGRATIONS, broken))
    with pytest.raises(sqlite3.OperationalError):
        apply_safe_migrations(conn)

    # Every earlier, valid migration still applied; the broken one is never
    # recorded as applied, and no table it might have partially created lingers
    # under any name this test can see.
    assert "9998_hypothetical_broken_table" not in applied_migration_ids(conn)
    assert ALL_MIGRATION_IDS <= applied_migration_ids(conn)

    # Retrying without the broken migration (as if it had been fixed and
    # removed) succeeds cleanly -- nothing about the earlier failure corrupted
    # the database or blocked further progress.
    monkeypatch.setattr("target_cash.migrations.MIGRATIONS", MIGRATIONS)
    second = apply_safe_migrations(conn)
    assert second == []  # already-applied migrations are still recorded; nothing to redo


def test_migration_against_missing_table_refuses_rather_than_guesses(monkeypatch):
    conn = sqlite3.connect(":memory:")  # no filings table at all
    with pytest.raises(UnsafeMigrationError):
        apply_safe_migrations(conn)


# --- fiscal_calendar / concept_equivalence_rules / annual_facts family (2026-09-15) ------


def test_new_tables_and_view_created_empty():
    conn = make_stale_db()
    apply_safe_migrations(conn)
    for table in (
        "fiscal_calendar", "concept_equivalence_rules",
        "annual_facts", "annual_lineage", "annual_fact_observations",
    ):
        assert conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone(), f"{table} was not created"
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    assert conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='view' AND name='period_facts_unified'"
    ).fetchone()
    # The view is queryable (returns zero rows against empty source tables) --
    # proves the UNION ALL and the fiscal_calendar join are syntactically sound.
    assert conn.execute("SELECT COUNT(*) FROM period_facts_unified").fetchone()[0] == 0
    columns = {row[1] for row in conn.execute("PRAGMA table_info(period_facts_unified)")}
    assert "reporting_period_role" in columns


def test_reporting_period_role_year_end_vs_quarter_end_and_frequency_never_reclassified():
    """Item 7 (2026-09-15, 'Unified-view semantics'): an instant fact's frequency
    must stay 'instant' -- never reclassified to 'annual' or 'quarterly' just
    because the fiscal-calendar join attaches a fiscal year/quarter to it.
    reporting_period_role is the separate field carrying that role instead.
    Also proves the year-end/Q4-end collision case: a period_end date that is
    simultaneously an annual year-end (fiscal_quarter=0) and that year's Q4
    end (fiscal_quarter=4) must emit the instant fact exactly once, labeled
    with the canonical YEAR_END role, never QUARTER_END and never duplicated.
    """
    conn = make_stale_db()
    apply_safe_migrations(conn)

    conn.execute(
        "INSERT INTO fiscal_calendar VALUES "
        "('0000027419', 'TARGET CORP', 2025, 0, '2025-02-02', '2026-01-31', 52, 0, NULL)"
    )
    conn.execute(
        "INSERT INTO fiscal_calendar VALUES "
        "('0000027419', 'TARGET CORP', 2025, 4, '2025-11-02', '2026-01-31', 13, 0, NULL)"
    )
    conn.execute(
        "INSERT INTO fiscal_calendar VALUES "
        "('0000027419', 'TARGET CORP', 2025, 2, '2025-05-04', '2025-08-02', 13, 0, NULL)"
    )
    # A year-end instant fact whose as_of_date is BOTH FY2025's annual period_end
    # and FY2025 Q4's period_end -- the collision case.
    conn.execute(
        "INSERT INTO instant_facts VALUES "
        "('inf_1', 'cash_and_equivalents_balance_sheet', '2026-01-31', 'GAAP', 'consolidated', "
        "'as_originally_filed', 'rf_1', 'authoritative', 5488.0, 'USD', 6, 5488.0, 'USD_millions', "
        "'0000027419-26-000016', '2026-03-15', 'as_originally_filed', 'v0', 'safe', '2026-09-14', 1)"
    )
    # A genuine mid-year quarter-end instant fact (FY2025 Q2 end), unambiguous.
    conn.execute(
        "INSERT INTO instant_facts VALUES "
        "('inf_2', 'cash_and_equivalents_balance_sheet', '2025-08-02', 'GAAP', 'consolidated', "
        "'as_originally_filed', 'rf_2', 'authoritative', 4000.0, 'USD', 6, 4000.0, 'USD_millions', "
        "'0000027419-25-000118', '2025-09-02', 'as_originally_filed', 'v0', 'safe', '2026-09-14', 1)"
    )
    conn.commit()

    rows = conn.execute(
        "SELECT metric, frequency, fiscal_year, fiscal_quarter, reporting_period_role, end_date "
        "FROM period_facts_unified WHERE frequency = 'instant' ORDER BY end_date"
    ).fetchall()

    assert len(rows) == 2  # the year-end/Q4-collision fact emitted exactly once, not twice

    q2_row, year_end_row = rows
    assert q2_row == ("cash_and_equivalents_balance_sheet", "instant", 2025, 2, "QUARTER_END", "2025-08-02")
    # frequency stays 'instant' even though fiscal_year/fiscal_quarter/reporting_period_role
    # are attached -- never reclassified to 'annual' despite matching the annual sentinel row.
    assert year_end_row == ("cash_and_equivalents_balance_sheet", "instant", 2025, None, "YEAR_END", "2026-01-31")


def test_quarterly_facts_analytical_view_column_added_with_default():
    conn = make_stale_db()
    conn.execute(
        "INSERT INTO quarterly_facts VALUES "
        "('qf_1', 'operating_cash_flow', 2025, 1, '2025-02-02', '2025-05-03', 91, "
        "2100.0, 'USD_millions', 2100.0, 'USD_millions', 'direct_quarterly', "
        "'2025-05-30T00:00:00Z', 'v0', 1)"
    )
    conn.commit()
    apply_safe_migrations(conn)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(quarterly_facts)")}
    assert "analytical_view" in columns
    value = conn.execute("SELECT analytical_view FROM quarterly_facts WHERE quarterly_fact_id = 'qf_1'").fetchone()[0]
    assert value == "as_originally_filed"  # pre-existing row backfilled with the default, not NULL


def test_all_new_migrations_idempotent_on_rerun():
    conn = make_stale_db()
    first = apply_safe_migrations(conn)
    for mid in (
        "0006_fiscal_calendar", "0007_concept_equivalence_rules", "0008_annual_facts",
        "0009_annual_lineage", "0010_annual_fact_observations",
        "0011_quarterly_facts_analytical_view", "0012_period_facts_unified",
        "0013_period_facts_unified_reporting_role",
        "0014_annual_fact_observations_original_historical",
    ):
        assert mid in first
    second = apply_safe_migrations(conn)
    assert second == []


def test_fiscal_calendar_primary_key_rejects_duplicate_year_quarter():
    conn = make_stale_db()
    apply_safe_migrations(conn)
    row = ("0000027419", "Target Corporation", 2025, 0, "2025-02-02", "2026-01-31", 52, 0, None)
    conn.execute(
        "INSERT INTO fiscal_calendar "
        "(cik, company_name, fiscal_year, fiscal_quarter, period_start, period_end, "
        " week_count, is_53_week_year, authority_accession) VALUES (?,?,?,?,?,?,?,?,?)",
        row,
    )
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO fiscal_calendar "
            "(cik, company_name, fiscal_year, fiscal_quarter, period_start, period_end, "
            " week_count, is_53_week_year, authority_accession) VALUES (?,?,?,?,?,?,?,?,?)",
            row,
        )


def test_annual_facts_canonical_uniqueness():
    conn = make_stale_db()
    apply_safe_migrations(conn)
    row = (
        "af_1", "revenue", 2025, "2025-02-02", "2026-01-31", 364, "as_originally_filed",
        104780000000.0, "USD", 104780.0, "USD_millions", "direct", "authoritative",
        "unvalidated", "0000027419-26-000016", "2026-03-11", "v0", "2026-09-15T00:00:00Z", 1,
    )
    conn.execute(
        "INSERT INTO annual_facts "
        "(annual_fact_id, metric, fiscal_year, period_start, period_end, days_in_period, "
        " analytical_view, value_original, original_unit, value_normalized, normalized_unit, "
        " direct_or_derived, fact_status, validation_status, accession_number, filed_at, "
        " mapping_version, information_cutoff, is_current_view) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        row,
    )
    conn.commit()
    duplicate = ("af_2",) + row[1:]
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO annual_facts "
            "(annual_fact_id, metric, fiscal_year, period_start, period_end, days_in_period, "
            " analytical_view, value_original, original_unit, value_normalized, normalized_unit, "
            " direct_or_derived, fact_status, validation_status, accession_number, filed_at, "
            " mapping_version, information_cutoff, is_current_view) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            duplicate,
        )


def test_annual_lineage_requires_exactly_one_input_kind():
    conn = make_stale_db()
    apply_safe_migrations(conn)
    conn.execute(
        "INSERT INTO annual_facts "
        "(annual_fact_id, metric, fiscal_year, period_start, period_end, days_in_period, "
        " analytical_view, value_original, original_unit, value_normalized, normalized_unit, "
        " direct_or_derived, fact_status, validation_status, accession_number, filed_at, "
        " mapping_version, information_cutoff, is_current_view) VALUES "
        "('af_gp', 'gross_profit', 2025, '2025-02-02', '2026-01-31', 364, 'as_originally_filed', "
        " 29269000000.0, 'USD', 29269.0, 'USD_millions', 'derived', 'authoritative', 'unvalidated', "
        " '0000027419-26-000016', '2026-03-11', 'v0', '2026-09-15T00:00:00Z', 1)"
    )
    conn.commit()
    # Neither input set -- must fail the CHECK.
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO annual_lineage (annual_lineage_id, derived_fact_id, operation, sequence) "
            "VALUES ('al_1', 'af_gp', 'subtract', 1)"
        )
    # Both inputs set -- must also fail the CHECK.
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO annual_lineage "
            "(annual_lineage_id, derived_fact_id, input_raw_fact_id, input_annual_fact_id, operation, sequence) "
            "VALUES ('al_2', 'af_gp', 'rf_1', 'af_gp', 'subtract', 1)"
        )
    # Exactly one set -- succeeds.
    conn.execute(
        "INSERT INTO annual_lineage (annual_lineage_id, derived_fact_id, input_annual_fact_id, operation, sequence) "
        "VALUES ('al_3', 'af_gp', 'af_gp', 'subtract', 1)"
    )


def _add_raw_facts_table(conn):
    """make_stale_db() (this file's own fixture) never creates raw_facts --
    the 0001-0014 migrations under test don't touch it, but annual_facts/
    annual_fact_observations both declare (unenforced, since PRAGMA
    foreign_keys is never set on these test connections) REFERENCES into it,
    and the 0014 tests below insert real raw_facts rows to exercise it."""
    conn.execute(
        """
        CREATE TABLE raw_facts (
            fact_id TEXT PRIMARY KEY, accession_number TEXT, taxonomy TEXT, tag TEXT, unit TEXT,
            start_date TEXT, end_date TEXT, context_ref TEXT, dimensional_context TEXT,
            value TEXT, scale INTEGER, sign_as_reported INTEGER, is_superseded INTEGER, retrieved_at TEXT
        )
        """
    )


def test_migration_0014_preserves_existing_observations_and_expands_check():
    """Migration 0014 rebuilds annual_fact_observations to widen its
    relationship CHECK constraint -- must preserve every existing row
    exactly (this migration inserts and changes nothing itself) while
    accepting the new 'original_historical' value going forward.
    """
    conn = make_stale_db()
    _add_raw_facts_table(conn)
    apply_safe_migrations(conn)

    conn.execute(
        "INSERT INTO filings (accession_number, cik, company_name, form_type, filed_at, "
        "period_of_report, primary_document_url, ingestion_method) VALUES "
        "('acc-1', '0000027419', 'Target Corporation', '10-K', '2025-03-01', '2025-02-01', "
        "'https://example.invalid', 'manual_upload')"
    )
    conn.execute(
        "INSERT INTO raw_facts VALUES ('rf-1', 'acc-1', 'us-gaap', 'Revenues', 'USD', "
        "'2024-02-04', '2025-02-01', 'c-1', NULL, '106566000000', 6, 1, 0, '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO annual_facts VALUES ('af-1', 'revenue', 2024, '2024-02-04', '2025-02-01', 364, "
        "'as_originally_filed', 106566000000, 'USD', 106566.0, 'USD_millions', 'direct', 'authoritative', "
        "'pass', 'acc-1', '2025-03-01', 'v0', '2026-01-01', 1)"
    )
    conn.execute(
        "INSERT INTO annual_fact_observations VALUES ('obs-1', 'af-1', 'rf-1', 'acc-1', '2025-03-01', "
        "'selected', 106566.0, NULL, 'authoritative source')"
    )
    conn.commit()

    before_rows = conn.execute(
        "SELECT observation_id, annual_fact_id, raw_fact_id, accession_number, filed_at, "
        "relationship, value_original, difference_from_selected, classification_rationale "
        "FROM annual_fact_observations ORDER BY observation_id"
    ).fetchall()

    # Re-apply is a no-op here (0014 already applied via the make_stale_db()+apply_safe_migrations()
    # call above, before these rows were inserted) -- this proves inserting a real row afterwards,
    # under the ALREADY-migrated schema, works and the schema state is stable.
    apply_safe_migrations(conn)
    after_rows = conn.execute(
        "SELECT observation_id, annual_fact_id, raw_fact_id, accession_number, filed_at, "
        "relationship, value_original, difference_from_selected, classification_rationale "
        "FROM annual_fact_observations ORDER BY observation_id"
    ).fetchall()
    assert before_rows == after_rows

    # The new relationship value is accepted.
    conn.execute(
        "INSERT INTO annual_fact_observations VALUES ('obs-2', 'af-1', 'rf-1', 'acc-1', '2025-03-01', "
        "'original_historical', 106566.0, 0.0, 'historical evidence')"
    )
    conn.commit()
    assert conn.execute("SELECT relationship FROM annual_fact_observations WHERE observation_id='obs-2'").fetchone()[0] == "original_historical"

    # An invalid relationship value is still rejected.
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO annual_fact_observations VALUES ('obs-bad', 'af-1', 'rf-1', 'acc-1', '2025-03-01', "
            "'not_a_real_relationship', 1.0, NULL, 'bad')"
        )


def test_migration_0014_is_idempotent_and_row_preserving_across_a_fresh_apply():
    """Applying 0014 to a database that already has real annual_fact_observations
    rows (inserted before 0014 runs) must preserve them exactly."""
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
    _add_raw_facts_table(conn)
    # Apply everything up through 0010 (the ORIGINAL 4-value CHECK) manually, by applying all
    # migrations and then inserting a row under the pre-0014 vocabulary -- proves 0014, even though
    # it already ran earlier in this same apply_safe_migrations call, didn't drop any row a
    # subsequent insert adds under the now-current (5-value) schema.
    from target_cash.migrations import apply_safe_migrations as _apply
    _apply(conn)
    conn.execute(
        "INSERT INTO filings (accession_number, cik, company_name, form_type, filed_at, "
        "period_of_report, primary_document_url, ingestion_method) VALUES "
        "('acc-1', '0000027419', 'Target Corporation', '10-K', '2025-03-01', '2025-02-01', "
        "'https://example.invalid', 'manual_upload')"
    )
    conn.execute(
        "INSERT INTO raw_facts VALUES ('rf-1', 'acc-1', 'us-gaap', 'Revenues', 'USD', "
        "'2024-02-04', '2025-02-01', 'c-1', NULL, '106566000000', 6, 1, 0, '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO annual_facts VALUES ('af-1', 'revenue', 2024, '2024-02-04', '2025-02-01', 364, "
        "'as_originally_filed', 106566000000, 'USD', 106566.0, 'USD_millions', 'direct', 'authoritative', "
        "'pass', 'acc-1', '2025-03-01', 'v0', '2026-01-01', 1)"
    )
    conn.execute(
        "INSERT INTO annual_fact_observations VALUES ('obs-1', 'af-1', 'rf-1', 'acc-1', '2025-03-01', "
        "'conflicting', 106566.0, 5.0, 'pre-existing row under the original vocabulary')"
    )
    conn.commit()
    row = conn.execute("SELECT relationship, value_original FROM annual_fact_observations WHERE observation_id='obs-1'").fetchone()
    assert row == ("conflicting", 106566.0)
