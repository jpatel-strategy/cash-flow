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
    TableMigration(
        migration_id="0013_period_facts_unified_reporting_role",
        description=(
            "Extend period_facts_unified with reporting_period_role, per the "
            "2026-09-15 item 7 ('Unified-view semantics') instruction: an instant "
            "fact's economic frequency must never be reclassified as ANNUAL or "
            "QUARTERLY just because the fiscal-calendar join attaches a fiscal year/ "
            "quarter to it -- frequency stays 'instant' for every point-in-time fact, "
            "exactly as migration 0012 already had it. reporting_period_role is the "
            "new, separate field carrying the fiscal-calendar role instead: "
            "'YEAR_END' or 'QUARTER_END' for instant facts (NULL for quarterly/annual "
            "duration facts, which are not point-in-time and do not have this "
            "ambiguity). migration 0012 already resolves the case where a date is "
            "simultaneously a fiscal year-end AND its Q4 end by picking the lowest "
            "fiscal_quarter match (the annual sentinel fiscal_quarter=0 beats 1-4) -- "
            "this migration reuses that exact same join/tie-break unchanged, so the "
            "fact is still emitted exactly once, and reporting_period_role now simply "
            "labels the already-chosen row as YEAR_END in that case (the documented "
            "canonical reporting role required by item 7), never QUARTER_END.\n"
            "Per the append-only migration rule, 0012 itself is never edited -- this "
            "migration DROPs and recreates the view (safe: a view carries no stored "
            "rows of its own, only a query definition, so dropping and recreating it "
            "can never lose data) with the added column, superseding 0012's view "
            "definition without touching any table."
        ),
        create_sql="""
            DROP VIEW IF EXISTS period_facts_unified;

            CREATE VIEW period_facts_unified AS
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
                NULL                                            AS validation_status,
                NULL                                            AS reporting_period_role
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
                af.validation_status                                 AS validation_status,
                NULL                                                  AS reporting_period_role
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
                inf.selection_status                                      AS validation_status,
                CASE WHEN fc.fiscal_quarter = 0 THEN 'YEAR_END'
                     WHEN fc.fiscal_quarter IS NOT NULL THEN 'QUARTER_END'
                     ELSE NULL END                                         AS reporting_period_role
            FROM instant_facts inf
            LEFT JOIN fiscal_calendar fc
                ON fc.period_end = inf.as_of_date
                AND fc.fiscal_quarter = (
                    SELECT MIN(fc2.fiscal_quarter) FROM fiscal_calendar fc2 WHERE fc2.period_end = inf.as_of_date
                );
        """,
    ),
    TableMigration(
        migration_id="0014_annual_fact_observations_original_historical",
        description=(
            "Add 'original_historical' to annual_fact_observations.relationship's CHECK constraint "
            "(2026-09-16 observation-completeness round). The existing 4-value vocabulary "
            "(selected, corroborating, restated, conflicting) cannot distinguish two genuinely "
            "different relationships that both arise from the SAME reclassification: attached to "
            "the AS_ORIGINALLY_FILED fact, a later, different-valued observation is correctly "
            "'restated' (evidence that this fact was later restated). But attached to the "
            "LATEST_RESTATED fact, the ORIGINAL, now-superseded observation is the OPPOSITE "
            "direction of the same relationship -- reusing 'restated' there would be backwards and "
            "ambiguous, and 'conflicting' would misrepresent a known, documented, policy-explained "
            "reclassification as an unresolved disagreement. 'original_historical' names the "
            "original filing's own value, retained under the restated view as historical evidence, "
            "explicitly distinct from a genuine unexplained 'conflicting' disagreement.\n"
            "SQLite cannot ALTER a CHECK constraint in place, so this migration rebuilds the table: "
            "CREATE the new table with the expanded CHECK, COPY every existing row unchanged, DROP "
            "the old table, RENAME the new one into place -- wrapped in one explicit transaction "
            "(BEGIN...COMMIT) for atomicity, so any failure leaves the original table completely "
            "untouched rather than partially rebuilt. Every existing row's values are preserved "
            "exactly (this migration inserts no new rows and changes no existing value); only the "
            "constraint governing which relationship strings may be inserted going forward changes. "
            "Per the append-only migration rule, migration 0010 itself is never edited."
        ),
        create_sql="""
            BEGIN TRANSACTION;

            CREATE TABLE annual_fact_observations_v2 (
                observation_id            TEXT PRIMARY KEY,
                annual_fact_id            TEXT NOT NULL REFERENCES annual_facts(annual_fact_id),
                raw_fact_id               TEXT NOT NULL REFERENCES raw_facts(fact_id),
                accession_number          TEXT NOT NULL REFERENCES filings(accession_number),
                filed_at                  TEXT NOT NULL,
                relationship              TEXT NOT NULL
                                              CHECK (relationship IN
                                                  ('selected', 'corroborating', 'restated', 'original_historical', 'conflicting')),
                value_original            REAL NOT NULL,
                difference_from_selected  REAL,
                classification_rationale  TEXT NOT NULL
            );

            INSERT INTO annual_fact_observations_v2
                (observation_id, annual_fact_id, raw_fact_id, accession_number, filed_at,
                 relationship, value_original, difference_from_selected, classification_rationale)
            SELECT
                observation_id, annual_fact_id, raw_fact_id, accession_number, filed_at,
                relationship, value_original, difference_from_selected, classification_rationale
            FROM annual_fact_observations;

            DROP TABLE annual_fact_observations;

            ALTER TABLE annual_fact_observations_v2 RENAME TO annual_fact_observations;

            CREATE INDEX IF NOT EXISTS idx_annual_fact_observations_annual
                ON annual_fact_observations(annual_fact_id);

            COMMIT;
        """,
    ),
    TableMigration(
        migration_id="0015_forecast_scenarios",
        description=(
            "Create forecast_scenarios (empty). Milestone 3B: implements, unchanged, the schema "
            "proposed in docs/milestone_3_forecast_schema_proposal.md Section 2.1 (approved as a "
            "proposal 2026-09-16, implemented 2026-09-16 once Milestone 3A's forecast corrections "
            "passed every validation gate). One row per scenario (base/upside/downside). "
            "information_cutoff_accession points at the FY2025 10-K via the existing filings table "
            "-- the forecast cutoff is registered evidence, never a bare string."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS forecast_scenarios (
                scenario_id                  TEXT PRIMARY KEY,
                scenario_name                TEXT NOT NULL,
                description                  TEXT NOT NULL,
                information_cutoff           TEXT NOT NULL,
                information_cutoff_accession TEXT NOT NULL REFERENCES filings(accession_number),
                version                      TEXT NOT NULL DEFAULT 'v1',
                created_at                   TEXT NOT NULL
            );
        """,
    ),
    TableMigration(
        migration_id="0016_forecast_assumptions",
        description=(
            "Create forecast_assumptions (empty). Milestone 3B, per the proposal's Section 2.2. "
            "Directly persists target_cash.forecast.Assumption unchanged -- every field of that "
            "dataclass has a matching column. review_status starts at 'proposed' for every row this "
            "round produces; only a human reviewer may advance it to 'reviewed'/'approved'."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS forecast_assumptions (
                assumption_id         TEXT PRIMARY KEY,
                scenario_id           TEXT NOT NULL REFERENCES forecast_scenarios(scenario_id),
                forecast_year         INTEGER NOT NULL,
                metric                TEXT NOT NULL,
                value                 REAL NOT NULL,
                unit                  TEXT NOT NULL,
                rationale             TEXT NOT NULL,
                historical_reference  TEXT NOT NULL,
                source_evidence       TEXT NOT NULL,
                information_cutoff    TEXT NOT NULL,
                review_status         TEXT NOT NULL DEFAULT 'proposed'
                                          CHECK (review_status IN ('proposed', 'reviewed', 'approved', 'rejected')),
                version               TEXT NOT NULL DEFAULT 'v1',
                created_at            TEXT NOT NULL,
                UNIQUE (scenario_id, metric, forecast_year, version)
            );
            CREATE INDEX IF NOT EXISTS idx_forecast_assumptions_scenario_metric
                ON forecast_assumptions(scenario_id, metric);
        """,
    ),
    TableMigration(
        migration_id="0017_forecast_facts",
        description=(
            "Create forecast_facts (empty). Milestone 3B, per the proposal's Section 2.3. One row "
            "per (scenario, fiscal_year, metric) -- every field of target_cash.forecast.ForecastYear "
            "becomes its own row, matching annual_facts' one-row-per-metric grain. "
            "CHECK (fiscal_year >= 2026) is the structural historical/forecast separation: a forecast "
            "row can never land in the FY2021-FY2025 historical range, and this table is entirely "
            "separate from annual_facts, so no query can accidentally blend the two."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS forecast_facts (
                forecast_fact_id           TEXT PRIMARY KEY,
                scenario_id                TEXT NOT NULL REFERENCES forecast_scenarios(scenario_id),
                fiscal_year                INTEGER NOT NULL CHECK (fiscal_year >= 2026),
                metric                     TEXT NOT NULL,
                metric_definition_version  TEXT NOT NULL,
                assumption_version         TEXT NOT NULL,
                value                      REAL NOT NULL,
                unit                       TEXT NOT NULL DEFAULT 'USD_millions',
                formula                    TEXT NOT NULL,
                validation_status          TEXT NOT NULL DEFAULT 'unvalidated'
                                               CHECK (validation_status IN ('pass', 'fail', 'blocked', 'unvalidated')),
                information_cutoff         TEXT NOT NULL,
                created_at                 TEXT NOT NULL,
                UNIQUE (scenario_id, metric, fiscal_year, assumption_version)
            );
            CREATE INDEX IF NOT EXISTS idx_forecast_facts_scenario_year ON forecast_facts(scenario_id, fiscal_year);
        """,
    ),
    TableMigration(
        migration_id="0018_forecast_lineage",
        description=(
            "Create forecast_lineage (empty). Milestone 3B, per the proposal's Section 2.4. "
            "Generalizes annual_lineage's two-input-kind CHECK (exactly one of raw/annual) to three "
            "input kinds with 'at least one', because a forecast fact routinely combines a prior-year "
            "forecast fact, a historical annual_facts anchor, and an assumption in one formula."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS forecast_lineage (
                forecast_lineage_id       TEXT PRIMARY KEY,
                forecast_fact_id          TEXT NOT NULL REFERENCES forecast_facts(forecast_fact_id),
                input_historical_fact_id  TEXT REFERENCES annual_facts(annual_fact_id),
                input_forecast_fact_id    TEXT REFERENCES forecast_facts(forecast_fact_id),
                input_assumption_id       TEXT REFERENCES forecast_assumptions(assumption_id),
                operation                 TEXT NOT NULL,
                sequence                  INTEGER NOT NULL,
                CHECK (
                    (input_historical_fact_id IS NOT NULL)
                    + (input_forecast_fact_id IS NOT NULL)
                    + (input_assumption_id IS NOT NULL) >= 1
                )
            );
            CREATE INDEX IF NOT EXISTS idx_forecast_lineage_fact ON forecast_lineage(forecast_fact_id);
        """,
    ),
    TableMigration(
        migration_id="0019_forecast_validation_results",
        description=(
            "Create forecast_validation_results (empty). Milestone 3B, per the proposal's Section "
            "2.5. One row per target_cash.forecast.ValidationResult per persistence run. "
            "scenario_id/fiscal_year are nullable because several checks (scenario_ordering, "
            "information_cutoff_compliance, no_historical_forecast_mixing, "
            "cumulative_capacity_no_double_counting when reported per-scenario only) are not scoped "
            "to a single scenario/year."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS forecast_validation_results (
                validation_result_id  TEXT PRIMARY KEY,
                check_name            TEXT NOT NULL,
                scenario_id           TEXT REFERENCES forecast_scenarios(scenario_id),
                fiscal_year           INTEGER,
                status                TEXT NOT NULL CHECK (status IN ('PASS', 'FAIL', 'WARNING')),
                detail                TEXT NOT NULL,
                forecast_version      TEXT NOT NULL,
                run_at                TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_forecast_validation_check ON forecast_validation_results(check_name);
        """,
    ),
    TableMigration(
        migration_id="0020_investment_capacity_results",
        description=(
            "Create investment_capacity_results (empty). Milestone 3B, per the proposal's Section "
            "2.6. methodology_note is NOT NULL with no default by design: deployable_capacity must "
            "never be persisted as a bare number without the liquidity-buffer/seasonality/covenant/"
            "discretion caveats attached, so the schema makes it structurally impossible to insert "
            "the figure without also storing that explanation."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS investment_capacity_results (
                investment_capacity_result_id     TEXT PRIMARY KEY,
                scenario_id                       TEXT NOT NULL REFERENCES forecast_scenarios(scenario_id),
                fiscal_year                        INTEGER NOT NULL,
                gross_fcf_capacity                 REAL NOT NULL,
                post_dividend_capacity             REAL NOT NULL,
                pre_discretionary_ending_cash      REAL NOT NULL,
                min_cash_buffer                    REAL NOT NULL,
                near_term_debt_repayment_reserve   REAL NOT NULL,
                deployable_capacity                REAL NOT NULL,
                cumulative_deployable_capacity     REAL,
                funding_warning                    INTEGER NOT NULL DEFAULT 0 CHECK (funding_warning IN (0, 1)),
                methodology_note                   TEXT NOT NULL,
                information_cutoff                 TEXT NOT NULL,
                UNIQUE (scenario_id, fiscal_year)
            );
        """,
    ),
    TableMigration(
        migration_id="0021_valuation_assumptions",
        description=(
            "Create valuation_assumptions (empty). Milestone 4: DCF valuation layer, kept in its "
            "own tables, additive to (never mixed into) forecast_assumptions -- WACC components and "
            "terminal growth are properties of the market/economy, not of an operating scenario, so "
            "there is deliberately no scenario_id column here (see target_cash.valuation's own "
            "module docstring for why WACC/terminal growth are scenario-invariant by design)."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS valuation_assumptions (
                assumption_id       TEXT PRIMARY KEY,
                metric              TEXT NOT NULL,
                value               REAL NOT NULL,
                unit                TEXT NOT NULL,
                rationale           TEXT NOT NULL,
                source_evidence     TEXT NOT NULL,
                information_cutoff  TEXT NOT NULL,
                review_status       TEXT NOT NULL DEFAULT 'proposed'
                                        CHECK (review_status IN ('proposed', 'reviewed', 'approved', 'rejected')),
                version             TEXT NOT NULL DEFAULT 'v1',
                created_at          TEXT NOT NULL,
                UNIQUE (metric, version)
            );
        """,
    ),
    TableMigration(
        migration_id="0022_valuation_ufcf_facts",
        description=(
            "Create valuation_ufcf_facts (empty). Milestone 4: one row per (scenario, fiscal_year) "
            "unlevered free cash flow and its discounted present value -- the explicit-period detail "
            "behind each valuation_results row's pv_explicit_period total."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS valuation_ufcf_facts (
                valuation_ufcf_fact_id  TEXT PRIMARY KEY,
                scenario_id             TEXT NOT NULL REFERENCES forecast_scenarios(scenario_id),
                fiscal_year             INTEGER NOT NULL CHECK (fiscal_year >= 2026),
                ufcf                    REAL NOT NULL,
                pv_ufcf                 REAL NOT NULL,
                discount_period         INTEGER NOT NULL,
                information_cutoff      TEXT NOT NULL,
                UNIQUE (scenario_id, fiscal_year)
            );
        """,
    ),
    TableMigration(
        migration_id="0023_valuation_results",
        description=(
            "Create valuation_results (empty). Milestone 4: one row per scenario -- the complete DCF "
            "bridge (PV of explicit period, terminal value, enterprise value, net debt, equity value, "
            "implied value per share). valuation_date_net_debt/valuation_date_diluted_shares are "
            "FY2025 actuals (never a forecast year's projected figure -- see "
            "target_cash.valuation.check_valuation_date_consistency)."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS valuation_results (
                valuation_result_id           TEXT PRIMARY KEY,
                scenario_id                   TEXT NOT NULL REFERENCES forecast_scenarios(scenario_id),
                wacc_pct                      REAL NOT NULL,
                terminal_growth_pct           REAL NOT NULL,
                pv_explicit_period            REAL NOT NULL,
                terminal_year_ufcf            REAL NOT NULL,
                terminal_value_undiscounted   REAL NOT NULL,
                pv_terminal_value             REAL NOT NULL,
                enterprise_value              REAL NOT NULL,
                valuation_date_net_debt       REAL NOT NULL,
                equity_value                  REAL NOT NULL,
                valuation_date_diluted_shares REAL NOT NULL,
                implied_value_per_share       REAL NOT NULL,
                information_cutoff            TEXT NOT NULL,
                created_at                    TEXT NOT NULL,
                UNIQUE (scenario_id)
            );
        """,
    ),
    TableMigration(
        migration_id="0024_valuation_validation_results",
        description=(
            "Create valuation_validation_results (empty). Milestone 4: one row per "
            "target_cash.valuation.ValuationCheckResult per persistence run -- UFCF reconciliation, "
            "terminal-value period consistency, no debt/lease double counting, valuation-date "
            "consistency, WACC-exceeds-growth, and WACC/growth scenario invariance."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS valuation_validation_results (
                validation_result_id  TEXT PRIMARY KEY,
                check_name            TEXT NOT NULL,
                scenario_id           TEXT REFERENCES forecast_scenarios(scenario_id),
                status                TEXT NOT NULL CHECK (status IN ('PASS', 'FAIL')),
                detail                TEXT NOT NULL,
                valuation_version     TEXT NOT NULL,
                run_at                TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_valuation_validation_check ON valuation_validation_results(check_name);
        """,
    ),
    TableMigration(
        migration_id="0025_capacity_taxonomy_results",
        description=(
            "Create capacity_taxonomy_results (empty). Milestone 9 correction, per "
            "docs/investment_capacity_semantic_audit.md and "
            "docs/investment_capacity_correction_evidence.md: the corrected, per-scenario-year "
            "capacity taxonomy (operating_fcf through ending_excess_liquidity). Purely additive -- "
            "does not alter or remove investment_capacity_results (Milestone 3B), which is preserved "
            "verbatim, deprecated in documentation only, and never read by any formula here."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS capacity_taxonomy_results (
                capacity_taxonomy_result_id       TEXT PRIMARY KEY,
                scenario_id                        TEXT NOT NULL REFERENCES forecast_scenarios(scenario_id),
                fiscal_year                        INTEGER NOT NULL CHECK (fiscal_year >= 2026),
                operating_fcf                      REAL NOT NULL,
                post_dividend_internal_generation  REAL NOT NULL,
                opening_excess_liquidity           REAL NOT NULL,
                mandatory_debt_uses                REAL NOT NULL,
                self_funded_gross_capacity         REAL NOT NULL,
                debt_funded_incremental_capacity   REAL NOT NULL,
                total_gross_funding_capacity       REAL NOT NULL,
                share_repurchases                  REAL NOT NULL,
                strategic_investment                REAL NOT NULL DEFAULT 0,
                voluntary_debt_reduction            REAL NOT NULL DEFAULT 0,
                other_discretionary_uses            REAL NOT NULL DEFAULT 0,
                total_discretionary_deployment      REAL NOT NULL,
                remaining_deployable_headroom       REAL NOT NULL,
                ending_excess_liquidity             REAL NOT NULL,
                version                             TEXT NOT NULL DEFAULT 'v1',
                information_cutoff                  TEXT NOT NULL,
                UNIQUE (scenario_id, fiscal_year, version)
            );
        """,
    ),
    TableMigration(
        migration_id="0026_capacity_horizon_results",
        description=(
            "Create capacity_horizon_results (empty). Milestone 9 correction: one row per scenario, "
            "the FY2026-FY2030 cumulative capacity picture (cumulative_self_funded_generation through "
            "total_horizon_capacity_accessible), computed WITHOUT summing per-year ending-headroom "
            "balances -- see capacity_taxonomy.compute_capacity_horizon_summary's docstring for the "
            "proof. ending_reserve_movement is NOT NULL with no default: the reconciliation identity "
            "(total_horizon_capacity_accessible = cumulative_discretionary_deployment + "
            "terminal_remaining_headroom + ending_reserve_movement) must never be persisted without "
            "its reconciling term."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS capacity_horizon_results (
                capacity_horizon_result_id                  TEXT PRIMARY KEY,
                scenario_id                                  TEXT NOT NULL REFERENCES forecast_scenarios(scenario_id),
                cumulative_self_funded_generation            REAL NOT NULL,
                cumulative_debt_funded_capacity              REAL NOT NULL,
                opening_excess_liquidity_at_horizon_start    REAL NOT NULL,
                cumulative_discretionary_deployment          REAL NOT NULL,
                terminal_remaining_headroom                  REAL NOT NULL,
                ending_reserve_movement                      REAL NOT NULL,
                total_horizon_capacity_accessible            REAL NOT NULL,
                version                                       TEXT NOT NULL DEFAULT 'v1',
                information_cutoff                           TEXT NOT NULL,
                UNIQUE (scenario_id, version)
            );
        """,
    ),
    TableMigration(
        migration_id="0027_capacity_taxonomy_lineage",
        description=(
            "Create capacity_taxonomy_lineage (empty). Milestone 9 correction: one row per "
            "(field, fiscal_year|horizon) for every one of the 14 per-year and 7 horizon-summary "
            "capacity-taxonomy fields, citing its formula and every same-year/same-scenario input it "
            "depends on -- the capacity-taxonomy analogue of forecast_lineage."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS capacity_taxonomy_lineage (
                capacity_lineage_id           TEXT PRIMARY KEY,
                scenario_id                    TEXT NOT NULL REFERENCES forecast_scenarios(scenario_id),
                fiscal_year                    INTEGER,
                target_field                   TEXT NOT NULL,
                formula                        TEXT NOT NULL,
                same_year_forecast_inputs      TEXT,
                same_year_capacity_inputs      TEXT,
                information_cutoff             TEXT NOT NULL,
                version                        TEXT NOT NULL DEFAULT 'v1'
            );
            CREATE INDEX IF NOT EXISTS idx_capacity_taxonomy_lineage_field ON capacity_taxonomy_lineage(target_field);
        """,
    ),
    TableMigration(
        migration_id="0028_capacity_validation_results",
        description=(
            "Create capacity_validation_results (empty). Milestone 9 correction: one row per "
            "target_cash.capacity_taxonomy validation check per persistence run -- the persisted "
            "subset of the 20 required correction proofs (the remaining, purely structural/"
            "definitional proofs live in tests/unit/test_capacity_taxonomy.py instead, per that "
            "module's own docstring)."
        ),
        create_sql="""
            CREATE TABLE IF NOT EXISTS capacity_validation_results (
                capacity_validation_result_id  TEXT PRIMARY KEY,
                check_name                      TEXT NOT NULL,
                scenario_id                     TEXT REFERENCES forecast_scenarios(scenario_id),
                fiscal_year                     INTEGER,
                status                          TEXT NOT NULL CHECK (status IN ('PASS', 'FAIL', 'WARNING')),
                detail                          TEXT NOT NULL,
                capacity_version                TEXT NOT NULL,
                run_at                          TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_capacity_validation_check ON capacity_validation_results(check_name);
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
