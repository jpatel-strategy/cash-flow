-- Target Cash Flow and Investment Capacity model
-- SQLite schema. See docs/accounting_policies.md for the rules these tables enforce.
--
-- Only `filings`, `raw_facts`, `quarterly_facts`, and `lineage` are populated during
-- Milestone 1 (repository setup and four-quarter data proof). `assumptions` and
-- `forecasts` are declared now so downstream milestones don't require a schema
-- migration, but they stay empty until the scenario/forecast milestone is authorized.

PRAGMA foreign_keys = ON;

-- One row per SEC filing (or manually-ingested equivalent) actually used as a source.
CREATE TABLE IF NOT EXISTS filings (
    accession_number      TEXT PRIMARY KEY,
    cik                    TEXT NOT NULL,
    company_name           TEXT NOT NULL,
    form_type              TEXT NOT NULL,               -- e.g. '10-K', '10-Q'
    filed_at               TEXT NOT NULL,                -- ISO date, as filed with SEC
    fiscal_year_end_focus  TEXT,                         -- SEC dei:DocumentFiscalYearFocus if available
    period_of_report       TEXT NOT NULL,                -- ISO date, end of the reporting period
    primary_document_url   TEXT NOT NULL,
    downloaded_at          TEXT,                         -- ISO datetime this session cached it
    file_hash              TEXT,                         -- sha256 of the cached file
    ingestion_method       TEXT NOT NULL CHECK (ingestion_method IN ('http_fetch', 'manual_upload')),
    notes                  TEXT
);

-- Facts at their original filed grain, before any quarterization or unit conversion.
-- Candidate duplicates and prior (superseded) values are retained, never overwritten.
CREATE TABLE IF NOT EXISTS raw_facts (
    fact_id              TEXT PRIMARY KEY,
    accession_number     TEXT NOT NULL REFERENCES filings(accession_number),
    taxonomy             TEXT NOT NULL,                  -- e.g. 'us-gaap', 'dei'
    tag                  TEXT NOT NULL,                  -- e.g. 'Revenues'
    unit                 TEXT NOT NULL,                  -- e.g. 'USD'
    start_date           TEXT,                           -- NULL for point-in-time (balance sheet) facts
    end_date             TEXT NOT NULL,
    context_ref          TEXT,                           -- XBRL context id from the filing
    dimensional_context  TEXT,                           -- segment/member axis, if any; NULL = consolidated
    value                TEXT NOT NULL,                  -- stored as text, parsed with Decimal downstream
    sign_as_reported     INTEGER NOT NULL DEFAULT 1,      -- +1 or -1, as tagged in the filing
    is_superseded        INTEGER NOT NULL DEFAULT 0,      -- 1 if a later filing restated this fact
    retrieved_at          TEXT NOT NULL
);

-- One selected value per (metric, fiscal_year, fiscal_quarter) analytical grain.
-- Balance-sheet metrics are stored as point-in-time stocks (basis='point_in_time')
-- and must never be differenced to manufacture a flow.
CREATE TABLE IF NOT EXISTS quarterly_facts (
    quarterly_fact_id   TEXT PRIMARY KEY,
    metric               TEXT NOT NULL,                  -- key into config/metrics.csv
    fiscal_year          INTEGER NOT NULL,
    fiscal_quarter       INTEGER NOT NULL CHECK (fiscal_quarter BETWEEN 1 AND 4),
    period_start         TEXT,                           -- NULL for point-in-time facts
    period_end           TEXT NOT NULL,
    days_in_period       INTEGER,                        -- NULL for point-in-time facts
    value_original        REAL NOT NULL,
    original_unit         TEXT NOT NULL,
    value_normalized       REAL NOT NULL,
    normalized_unit         TEXT NOT NULL DEFAULT 'USD_millions',
    basis                 TEXT NOT NULL CHECK (
                               basis IN ('direct_quarterly', 'derived_ytd_subtraction', 'point_in_time')
                           ),
    as_of_date            TEXT NOT NULL,                  -- information-cutoff this value was valid under
    mapping_version        TEXT NOT NULL,                  -- config/metrics.csv version used
    is_current_view        INTEGER NOT NULL DEFAULT 1       -- 0 = superseded-at-time-of-forecast-origin snapshot
);

-- Every derived quarterly_fact must point to every raw_fact used to build it.
CREATE TABLE IF NOT EXISTS lineage (
    lineage_id        TEXT PRIMARY KEY,
    derived_fact_id   TEXT NOT NULL REFERENCES quarterly_facts(quarterly_fact_id),
    input_fact_id     TEXT NOT NULL REFERENCES raw_facts(fact_id),
    operation         TEXT NOT NULL                        -- e.g. 'direct', 'ytd6_minus_q1', 'unit_conversion'
);

-- Scenario driver values. Not populated until the scenario/forecast milestone.
CREATE TABLE IF NOT EXISTS assumptions (
    assumption_id   TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    scenario        TEXT NOT NULL,                        -- 'base' | 'downside' | 'recovery'
    quarter         TEXT NOT NULL,
    driver          TEXT NOT NULL,
    value           REAL NOT NULL,
    unit            TEXT NOT NULL,
    rationale       TEXT NOT NULL,
    source_type     TEXT NOT NULL CHECK (
                        source_type IN ('historical_calibration', 'management_disclosure', 'illustrative_assumption')
                    )
);

-- Forecast results and their backtest evaluation against actuals. Not populated
-- until the forecast/backtest milestone.
CREATE TABLE IF NOT EXISTS forecasts (
    forecast_id           TEXT PRIMARY KEY,
    run_id                TEXT NOT NULL,
    information_cutoff    TEXT NOT NULL,
    target_quarter        TEXT NOT NULL,
    horizon               INTEGER NOT NULL,
    metric                TEXT NOT NULL,
    scenario              TEXT NOT NULL,
    forecast_value        REAL,
    baseline_value        REAL,
    actual_value          REAL,                            -- NULL until the target quarter is later reported
    source_versions       TEXT NOT NULL                     -- JSON blob: mapping_version, dataset version, etc.
);

CREATE INDEX IF NOT EXISTS idx_raw_facts_accession ON raw_facts(accession_number);
CREATE INDEX IF NOT EXISTS idx_quarterly_facts_metric_period ON quarterly_facts(metric, fiscal_year, fiscal_quarter);
CREATE INDEX IF NOT EXISTS idx_lineage_derived ON lineage(derived_fact_id);
