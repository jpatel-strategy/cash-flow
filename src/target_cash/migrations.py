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


@dataclass(frozen=True)
class TableMigration:
    """A CREATE TABLE (+ optional CREATE INDEX) migration -- additive by
    construction as long as every statement in `create_sql` uses
    'IF NOT EXISTS', so it never touches a table or index that already
    exists. Applied via `executescript`, so `create_sql` may contain more
    than one statement; nothing is recorded as applied in
    `_schema_migrations` unless every statement in it succeeds.
    """

    migration_id: str
    description: str
    create_sql: str
    is_safe_additive: bool = True


# Append-only: once a migration ships, never edit or remove it here -- add a
# new one instead, even to fix a mistake in an earlier one.
MIGRATIONS: tuple[ColumnMigration | TableMigration, ...] = (
    ColumnMigration(
        migration_id="0001_filings_cached_filename",
        description="Add filings.cached_filename so normalize can locate a filing's cached document.",
        table="filings",
        column="cached_filename",
        column_def="TEXT",
    ),
    ColumnMigration(
        migration_id="0002_filings_document_signature_date",
        description=(
            "Add filings.document_signature_date: the date found on a filing's own "
            "signature page, distinct from the SEC's actual filed date -- see "
            "docs/decisions.md, 2026-09-15 filing-date metadata correction."
        ),
        table="filings",
        column="document_signature_date",
        column_def="TEXT",
    ),
    ColumnMigration(
        migration_id="0003_filings_sec_acceptance_timestamp",
        description="Add filings.sec_acceptance_timestamp, populated only once verified against SEC submissions metadata.",
        table="filings",
        column="sec_acceptance_timestamp",
        column_def="TEXT",
    ),
    ColumnMigration(
        migration_id="0004_filings_filed_at_source",
        description=(
            "Add filings.filed_at_source, classifying the provenance of the existing "
            "filed_at column: 'sec_submissions_verified' (taken from a downloaded SEC "
            "submissions JSON) vs. 'document_derived_candidate' (inferred from the "
            "filing document itself, e.g. its signature-page date, not yet cross-"
            "checked against SEC submissions metadata)."
        ),
        table="filings",
        column="filed_at_source",
        column_def="TEXT",
    ),
    TableMigration(
        migration_id="0005_instant_facts",
        description=(
            "Create instant_facts and instant_fact_observations (empty; not populated "
            "by this migration) -- the canonical point-in-time-fact design approved "
            "2026-09-15. See docs/decisions.md for the full design rationale."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS instant_facts (
                instant_fact_id              TEXT PRIMARY KEY,
                metric                       TEXT NOT NULL,
                as_of_date                   TEXT NOT NULL,
                accounting_basis             TEXT NOT NULL,
                consolidated_scope           TEXT NOT NULL DEFAULT 'consolidated',
                analytical_view              TEXT NOT NULL DEFAULT 'as_originally_filed'
                                                 CHECK (analytical_view IN ('as_originally_filed', 'latest_restated')),
                selected_raw_fact_id         TEXT NOT NULL REFERENCES raw_facts(fact_id),
                authoritative_source_reason  TEXT NOT NULL,
                value_original               REAL NOT NULL,
                original_unit                TEXT NOT NULL,
                scale                        INTEGER,
                value_normalized             REAL NOT NULL,
                normalized_unit              TEXT NOT NULL DEFAULT 'USD_millions',
                accession_number             TEXT NOT NULL REFERENCES filings(accession_number),
                filed_at                     TEXT NOT NULL,
                restatement_status           TEXT NOT NULL DEFAULT 'as_originally_filed'
                                                 CHECK (restatement_status IN ('as_originally_filed', 'restated')),
                mapping_version              TEXT NOT NULL,
                selection_status             TEXT NOT NULL
                                                 CHECK (selection_status IN ('safe', 'corroborated', 'conflicted_unresolved')),
                information_cutoff           TEXT NOT NULL,
                is_current_view              INTEGER NOT NULL DEFAULT 1,
                UNIQUE (metric, as_of_date, accounting_basis, consolidated_scope, analytical_view)
            );
            CREATE TABLE IF NOT EXISTS instant_fact_observations (
                observation_id            TEXT PRIMARY KEY,
                instant_fact_id           TEXT NOT NULL REFERENCES instant_facts(instant_fact_id),
                raw_fact_id               TEXT NOT NULL REFERENCES raw_facts(fact_id),
                accession_number          TEXT NOT NULL REFERENCES filings(accession_number),
                filed_at                  TEXT NOT NULL,
                relationship              TEXT NOT NULL CHECK (relationship IN ('selected', 'corroborating', 'conflicting')),
                value_original            REAL NOT NULL,
                difference_from_selected  REAL,
                note                      TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_instant_facts_metric_date ON instant_facts(metric, as_of_date);
            CREATE INDEX IF NOT EXISTS idx_instant_fact_observations_instant
                ON instant_fact_observations(instant_fact_id);
        """,
    ),
    TableMigration(
        migration_id="0006_fiscal_calendar",
        description=(
            "Create fiscal_calendar (empty; populated only by "
            "target_cash.reference_data.seed_fiscal_calendar, never by this migration). "
            "An explicit, curated fiscal-year/quarter reference table -- replaces an "
            "earlier, withdrawn proposal to add a fiscal_year column to instant_facts "
            "computed from calendar dates, which the reviewer correctly rejected: "
            "Target's fiscal year-end (52 or 53 weeks, late Jan/early Feb) cannot be "
            "derived from a calendar date by formula. fiscal_quarter=0 is the sentinel "
            "for an annual-grain row (SQLite does not enforce uniqueness across NULLs "
            "in a composite primary key, so NULL is not used here). See "
            "docs/decisions.md, 2026-09-15 schema-implementation entry."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS fiscal_calendar (
                cik                  TEXT NOT NULL,
                company_name         TEXT NOT NULL,
                fiscal_year          INTEGER NOT NULL,
                fiscal_quarter       INTEGER NOT NULL DEFAULT 0
                                         CHECK (fiscal_quarter BETWEEN 0 AND 4),
                period_start         TEXT NOT NULL,
                period_end           TEXT NOT NULL,
                week_count           INTEGER NOT NULL,
                is_53_week_year      INTEGER NOT NULL DEFAULT 0,
                authority_accession  TEXT REFERENCES filings(accession_number),
                PRIMARY KEY (cik, fiscal_year, fiscal_quarter)
            );
            CREATE INDEX IF NOT EXISTS idx_fiscal_calendar_period_end ON fiscal_calendar(period_end);
        """,
    ),
    TableMigration(
        migration_id="0007_concept_equivalence_rules",
        description=(
            "Create concept_equivalence_rules (empty; populated only by "
            "target_cash.reference_data.seed_concept_equivalence_rules). Records a "
            "tag-vintage equivalence (e.g. us-gaap:InterestExpense == "
            "us-gaap:InterestExpenseNonoperating) as a versioned, evidenced rule "
            "instead of a destructive edit to config/metrics.csv's single "
            "candidate_xbrl_tag cell. See docs/decisions.md, 2026-09-15 entries."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS concept_equivalence_rules (
                rule_id                TEXT PRIMARY KEY,
                rule_version           TEXT NOT NULL,
                company_scope          TEXT NOT NULL,
                canonical_metric       TEXT NOT NULL,
                source_concept         TEXT NOT NULL,
                canonical_concept      TEXT NOT NULL,
                effective_fiscal_years TEXT NOT NULL,
                accounting_rationale   TEXT NOT NULL,
                evidence_reference     TEXT NOT NULL,
                review_status          TEXT NOT NULL DEFAULT 'proposed'
                                           CHECK (review_status IN ('proposed', 'reviewed', 'rejected')),
                mapping_version        TEXT NOT NULL,
                superseded_by_rule_id  TEXT REFERENCES concept_equivalence_rules(rule_id)
            );
            CREATE INDEX IF NOT EXISTS idx_concept_equivalence_rules_metric
                ON concept_equivalence_rules(canonical_metric);
        """,
    ),
    TableMigration(
        migration_id="0008_annual_facts",
        description=(
            "Create annual_facts (empty; not populated by this migration or by any "
            "code shipped this milestone -- persistence of annual analytical facts "
            "is not yet authorized). Mirrors the quarterly_facts/instant_facts "
            "pattern for the annual grain, with an explicit validation_status column "
            "(quarterly_facts and instant_facts compute validation status at query "
            "time; this table can store a result once one exists). See "
            "docs/decisions.md, 2026-09-15 entries."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS annual_facts (
                annual_fact_id       TEXT PRIMARY KEY,
                metric               TEXT NOT NULL,
                fiscal_year          INTEGER NOT NULL,
                period_start         TEXT NOT NULL,
                period_end           TEXT NOT NULL,
                days_in_period       INTEGER NOT NULL,
                analytical_view      TEXT NOT NULL DEFAULT 'as_originally_filed'
                                         CHECK (analytical_view IN ('as_originally_filed', 'latest_restated')),
                value_original       REAL NOT NULL,
                original_unit        TEXT NOT NULL,
                value_normalized     REAL NOT NULL,
                normalized_unit      TEXT NOT NULL DEFAULT 'USD_millions',
                direct_or_derived    TEXT NOT NULL CHECK (direct_or_derived IN ('direct', 'derived')),
                fact_status          TEXT NOT NULL DEFAULT 'authoritative'
                                         CHECK (fact_status IN ('authoritative', 'corroborating_only')),
                validation_status    TEXT NOT NULL DEFAULT 'unvalidated'
                                         CHECK (validation_status IN
                                             ('pass', 'fail', 'blocked', 'unavailable', 'not_applicable', 'unvalidated')),
                accession_number     TEXT NOT NULL REFERENCES filings(accession_number),
                filed_at             TEXT NOT NULL,
                mapping_version      TEXT NOT NULL,
                information_cutoff   TEXT NOT NULL,
                is_current_view      INTEGER NOT NULL DEFAULT 1,
                UNIQUE (metric, fiscal_year, analytical_view)
            );
            CREATE INDEX IF NOT EXISTS idx_annual_facts_metric_year ON annual_facts(metric, fiscal_year);
        """,
    ),
    TableMigration(
        migration_id="0009_annual_lineage",
        description=(
            "Create annual_lineage (empty). Generalizes quarterly_facts' lineage "
            "table: an annual fact's input may be a raw_fact OR another annual_fact "
            "(e.g. gross_profit's lineage points at revenue's and cost_of_sales' own "
            "annual_facts rows, not at raw XBRL facts directly), so exactly one of "
            "input_raw_fact_id/input_annual_fact_id is set per row."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS annual_lineage (
                annual_lineage_id     TEXT PRIMARY KEY,
                derived_fact_id       TEXT NOT NULL REFERENCES annual_facts(annual_fact_id),
                input_raw_fact_id     TEXT REFERENCES raw_facts(fact_id),
                input_annual_fact_id  TEXT REFERENCES annual_facts(annual_fact_id),
                operation             TEXT NOT NULL,
                sequence              INTEGER NOT NULL,
                coefficient           REAL,
                CHECK ((input_raw_fact_id IS NOT NULL) <> (input_annual_fact_id IS NOT NULL))
            );
            CREATE INDEX IF NOT EXISTS idx_annual_lineage_derived ON annual_lineage(derived_fact_id);
        """,
    ),
    TableMigration(
        migration_id="0010_annual_fact_observations",
        description="Create annual_fact_observations (empty). Same relationship vocabulary as instant_fact_observations, plus 'restated' for a same-metric-different-value corroboration (e.g. the COGS/SG&A reclassification), distinct from 'conflicting' (a genuine, unresolved disagreement).",
        create_sql="""
            CREATE TABLE IF NOT EXISTS annual_fact_observations (
                observation_id            TEXT PRIMARY KEY,
                annual_fact_id            TEXT NOT NULL REFERENCES annual_facts(annual_fact_id),
                raw_fact_id               TEXT NOT NULL REFERENCES raw_facts(fact_id),
                accession_number          TEXT NOT NULL REFERENCES filings(accession_number),
                filed_at                  TEXT NOT NULL,
                relationship              TEXT NOT NULL
                                              CHECK (relationship IN ('selected', 'corroborating', 'restated', 'conflicting')),
                value_original            REAL NOT NULL,
                difference_from_selected  REAL,
                classification_rationale  TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_annual_fact_observations_annual
                ON annual_fact_observations(annual_fact_id);
        """,
    ),
    ColumnMigration(
        migration_id="0011_quarterly_facts_analytical_view",
        description=(
            "Add quarterly_facts.analytical_view, mirroring instant_facts' column of "
            "the same name. No quarterly restatement has been observed yet (the "
            "COGS/SG&A reclassification found this milestone is annual-grain only), "
            "but the column must exist before one can be recorded."
        ),
        table="quarterly_facts",
        column="analytical_view",
        column_def="TEXT NOT NULL DEFAULT 'as_originally_filed'",
    ),
    TableMigration(
        migration_id="0012_period_facts_unified",
        description=(
            "Create the read-only period_facts_unified view, unioning quarterly_facts, "
            "annual_facts, and instant_facts into one reporting interface. Instant "
            "facts' fiscal year/quarter come from an explicit join to fiscal_calendar "
            "on period_end -- never inferred from as_of_date's calendar year, per the "
            "reviewer's explicit direction. A fiscal year-end date is simultaneously "
            "that year's annual period_end AND its Q4 period_end (Target's fiscal Q4 "
            "ends exactly at fiscal year-end); the join deliberately picks the lowest "
            "fiscal_quarter match (the annual sentinel 0 beats 1-4) so one instant fact "
            "never fans out into two output rows. See docs/decisions.md, 2026-09-15 entries."
        ),
        create_sql="""
            CREATE VIEW IF NOT EXISTS period_facts_unified AS
            SELECT
                qf.metric,
                'quarterly'                                    AS frequency,
                qf.fiscal_year,
                qf.fiscal_quarter,
                qf.period_start                                AS start_date,
                qf.period_end                                   AS end_date,
                qf.value_normalized                             AS value,
                qf.normalized_unit                              AS unit,
                CASE qf.basis WHEN 'point_in_time' THEN 'direct'
                              WHEN 'direct_quarterly' THEN 'direct'
                              ELSE 'derived' END                AS direct_or_derived,
                qf.analytical_view                              AS analytical_view,
                NULL                                            AS validation_status
            FROM quarterly_facts qf
            WHERE qf.is_current_view = 1

            UNION ALL

            SELECT
                af.metric,
                'annual'                                        AS frequency,
                af.fiscal_year,
                NULL                                             AS fiscal_quarter,
                af.period_start                                  AS start_date,
                af.period_end                                     AS end_date,
                af.value_normalized                               AS value,
                af.normalized_unit                                 AS unit,
                af.direct_or_derived                                AS direct_or_derived,
                af.analytical_view                                  AS analytical_view,
                af.validation_status                                 AS validation_status
            FROM annual_facts af
            WHERE af.is_current_view = 1

            UNION ALL

            SELECT
                inf.metric,
                'instant'                                         AS frequency,
                fc.fiscal_year,
                NULLIF(fc.fiscal_quarter, 0)                       AS fiscal_quarter,
                NULL                                                AS start_date,
                inf.as_of_date                                       AS end_date,
                inf.value_normalized                                  AS value,
                inf.normalized_unit                                    AS unit,
                'direct'                                                AS direct_or_derived,
                inf.analytical_view                                      AS analytical_view,
                inf.selection_status                                      AS validation_status
            FROM instant_facts inf
            LEFT JOIN fiscal_calendar fc
                ON fc.period_end = inf.as_of_date
                AND fc.fiscal_quarter = (
                    SELECT MIN(fc2.fiscal_quarter) FROM fiscal_calendar fc2 WHERE fc2.period_end = inf.as_of_date
                );
        """,
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

        if isinstance(migration, TableMigration):
            # executescript may contain more than one statement; if any of them
            # fails, nothing after it runs and this migration is never recorded
            # as applied -- a later call retries the whole script, safely, since
            # every statement in it is IF NOT EXISTS.
            conn.executescript(migration.create_sql)
        else:
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
