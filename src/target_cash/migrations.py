"""Safe, additive schema migrations for the curated SQLite database.

`sql/schema.sql` uses `CREATE TABLE IF NOT EXISTS`, which creates missing
tables but never alters an existing one — so adding a column to that file
does nothing to a database that already has the table (this is exactly how
`filings.cached_filename` went missing against an already-created database
in an earlier session; see docs/decisions.md, 2026-09-15 "Database safety").

This module is the fix: every schema change beyond the original tables is
recorded here as an explicit, additive migration (currently: ADD COLUMN
only, since that is the one kind of change SQLite can apply without ever
touching existing rows). `apply_safe_migrations` is idempotent, records
what it has applied in `_schema_migrations`, and NEVER drops or recreates a
table — a database with existing rows is always safe to pass through it.

If a future change cannot be expressed as a safe additive migration (a
column removal, a type change, a NOT NULL added to a populated column),
add it here as a new `Migration` with `is_safe_additive=False` and
`apply_safe_migrations` will refuse to run automatically, raising
`UnsafeMigrationError` with instructions instead of guessing.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass


class UnsafeMigrationError(RuntimeError):
    """Raised when a pending migration cannot be applied automatically and safely."""


@dataclass(frozen=True)
class ColumnMigration:
    migration_id: str  # stable, never reused once released
    description: str
    table: str
    column: str
    column_def: str  # e.g. 'TEXT', 'INTEGER DEFAULT 0' -- must be nullable or have a default
    is_safe_additive: bool = True


# Append-only: once a migration ships, never edit or remove it here -- add a
# new one instead, even to fix a mistake in an earlier one.
MIGRATIONS: tuple[ColumnMigration, ...] = (
    ColumnMigration(
        migration_id="0001_filings_cached_filename",
        description="Add filings.cached_filename so normalize can locate a filing's cached document.",
        table="filings",
        column="cached_filename",
        column_def="TEXT",
    ),
)


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS _schema_migrations (
            migration_id TEXT PRIMARY KEY,
            applied_at   TEXT NOT NULL,
            description  TEXT NOT NULL
        )
        """
    )


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return (
        conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
        is not None
    )


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(row[1] == column for row in conn.execute(f"PRAGMA table_info({table})"))


def applied_migration_ids(conn: sqlite3.Connection) -> set[str]:
    _ensure_migrations_table(conn)
    return {row[0] for row in conn.execute("SELECT migration_id FROM _schema_migrations")}


def apply_safe_migrations(conn: sqlite3.Connection) -> list[str]:
    """Apply every pending safe additive migration; return the ids applied.

    Safe to call on every connection, including a fresh database (schema.sql
    already creates the column via CREATE TABLE, so the column-exists check
    below makes each migration a no-op there) and a database that already
    has the column (same no-op). Never drops or recreates anything.
    """
    _ensure_migrations_table(conn)
    already_applied = applied_migration_ids(conn)
    newly_applied: list[str] = []

    for migration in MIGRATIONS:
        if migration.migration_id in already_applied:
            continue
        if not migration.is_safe_additive:
            raise UnsafeMigrationError(
                f"Migration {migration.migration_id!r} ({migration.description}) is not a safe additive "
                "change and cannot be applied automatically. Back up data/curated/target_cash.db, then "
                "apply it manually and record it in _schema_migrations yourself."
            )
        if not _table_exists(conn, migration.table):
            raise UnsafeMigrationError(
                f"Migration {migration.migration_id!r} expects table {migration.table!r} to already exist "
                "(created by sql/schema.sql), but it does not. The database may be corrupt or from an "
                "unrelated project -- refusing to guess. Inspect data/curated/target_cash.db manually."
            )
        if not _column_exists(conn, migration.table, migration.column):
            with conn:
                conn.execute(f"ALTER TABLE {migration.table} ADD COLUMN {migration.column} {migration.column_def}")
        with conn:
            conn.execute(
                "INSERT INTO _schema_migrations (migration_id, applied_at, description) VALUES (?, ?, ?)",
                (migration.migration_id, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), migration.description),
            )
        newly_applied.append(migration.migration_id)

    return newly_applied
