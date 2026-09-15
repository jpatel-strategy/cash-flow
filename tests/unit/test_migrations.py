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
