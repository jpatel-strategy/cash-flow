import sqlite3

import pytest

from target_cash.migrations import (
    MIGRATIONS,
    ColumnMigration,
    UnsafeMigrationError,
    apply_safe_migrations,
    applied_migration_ids,
)


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
    assert first == ["0001_filings_cached_filename"]
    assert second == []  # already applied -- must not error or reapply


def test_apply_safe_migrations_is_a_noop_on_an_already_current_schema():
    conn = make_stale_db()
    conn.execute("ALTER TABLE filings ADD COLUMN cached_filename TEXT")  # simulate a fresh schema.sql-created table
    applied = apply_safe_migrations(conn)
    # Column already present -- migration is recorded as applied without altering anything twice.
    assert applied == ["0001_filings_cached_filename"]
    assert applied_migration_ids(conn) == {"0001_filings_cached_filename"}


def test_apply_safe_migrations_records_applied_migrations():
    conn = make_stale_db()
    apply_safe_migrations(conn)
    rows = conn.execute("SELECT migration_id, description FROM _schema_migrations").fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "0001_filings_cached_filename"


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
    assert applied_migration_ids(conn) == {"0001_filings_cached_filename"}


def test_migration_against_missing_table_refuses_rather_than_guesses(monkeypatch):
    conn = sqlite3.connect(":memory:")  # no filings table at all
    with pytest.raises(UnsafeMigrationError):
        apply_safe_migrations(conn)
