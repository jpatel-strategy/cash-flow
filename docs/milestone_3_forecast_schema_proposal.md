# Milestone 3: Forecast Schema Proposal (NOT IMPLEMENTED)

**Status: proposal only.** No migration has been written, no `CREATE TABLE`
statement below has been executed, and `src/target_cash/migrations.py` is
unchanged by this round. This document exists so a reviewer can approve the
shape of the persistence layer *before* any schema code is written, per the
explicit instruction governing this round ("propose ... but do NOT implement
until the DDL is presented"). Once approved, implementing these as real,
tested migrations (in the same additive, `IF NOT EXISTS` style as
`0008_annual_facts` through `0014_annual_fact_observations_original_historical`)
is future work, not part of this round.

Nothing in `src/target_cash/forecast.py` (this round's actual deliverable)
writes to any of these tables, or to any existing table. It is pure in-memory
computation; see that module's docstring.

---

## 1. Design principles carried over from Milestone 2

- **Additive only.** No existing table (`annual_facts`, `annual_lineage`,
  `annual_fact_observations`, `raw_facts`, `filings`, `metric_definitions`) is
  altered. Forecast tables are new, separate tables.
- **Structural historical/forecast separation.** `forecast_facts.fiscal_year`
  carries a `CHECK (fiscal_year >= 2026)` floor, so a forecast row can never
  land in the FY2021-FY2025 historical range, and `annual_facts` never
  contains a forecast year. The two fact tables live in different SQL tables
  with different primary-key prefixes (`fct_...` vs `af_...`, mirroring the
  existing `annual_fact_...` id convention) — there is no way for a query
  joining across them to produce an "indistinguishable" row, because every
  row's table of origin is itself part of its identity.
- **Same lineage discipline.** `forecast_lineage` mirrors `annual_lineage`'s
  input-fact-pointer pattern, generalized to three possible input kinds
  (a historical annual fact, another forecast fact, or an assumption) instead
  of two, with a `CHECK` requiring at least one to be set.
- **Same versioning/review-status discipline as `annual_facts.mapping_version`
  and `validation_status`.** Every assumption and fact carries a version and
  either a review status (assumptions) or a validation status (facts),
  because Milestone 2 established that "the reviewer must be able to tell
  whether a number has been checked" applies to every persisted figure, not
  only historical ones.
- **No plug values persisted as if they were independent facts.** Share
  repurchases and debt proceeds/repayments are still ordinary
  `forecast_assumptions` rows (a payout ratio, a fixed schedule) — the schema
  does not add a special "solved to balance" column, because no such solving
  is permitted (item 9).

## 2. Proposed tables

### 2.1 `forecast_scenarios`

```sql
CREATE TABLE IF NOT EXISTS forecast_scenarios (
    scenario_id                    TEXT PRIMARY KEY,   -- 'base' | 'upside' | 'downside'
    scenario_name                  TEXT NOT NULL,
    description                    TEXT NOT NULL,
    information_cutoff             TEXT NOT NULL,
    information_cutoff_accession   TEXT NOT NULL REFERENCES filings(accession_number),
    version                        TEXT NOT NULL DEFAULT 'v1',
    created_at                     TEXT NOT NULL
);
```

One row per scenario per version. `information_cutoff_accession` points at
`0000027419-26-000016` (the FY2025 10-K) via the existing `filings` table —
the forecast cutoff is registered evidence, not a bare string.

### 2.2 `forecast_assumptions`

```sql
CREATE TABLE IF NOT EXISTS forecast_assumptions (
    assumption_id           TEXT PRIMARY KEY,
    scenario_id              TEXT NOT NULL REFERENCES forecast_scenarios(scenario_id),
    forecast_year            INTEGER NOT NULL,   -- 0 = flat, applies to every forecast year unless overridden
    metric                   TEXT NOT NULL,
    value                    REAL NOT NULL,
    unit                     TEXT NOT NULL,
    rationale                TEXT NOT NULL,
    historical_reference     TEXT NOT NULL,
    source_evidence          TEXT NOT NULL,
    information_cutoff       TEXT NOT NULL,
    review_status            TEXT NOT NULL DEFAULT 'proposed'
                                 CHECK (review_status IN ('proposed', 'reviewed', 'approved', 'rejected')),
    version                  TEXT NOT NULL DEFAULT 'v1',
    created_at                TEXT NOT NULL,
    UNIQUE (scenario_id, metric, forecast_year, version)
);
CREATE INDEX IF NOT EXISTS idx_forecast_assumptions_scenario_metric
    ON forecast_assumptions(scenario_id, metric);
```

Directly persists `forecast.Assumption` (this round's dataclass) unchanged —
every field of that dataclass has a matching column. `review_status` starts
at `'proposed'` for every row this round produces (never `'reviewed'` or
`'approved'` — only a human reviewer may advance that field).

### 2.3 `forecast_facts`

```sql
CREATE TABLE IF NOT EXISTS forecast_facts (
    forecast_fact_id            TEXT PRIMARY KEY,
    scenario_id                  TEXT NOT NULL REFERENCES forecast_scenarios(scenario_id),
    fiscal_year                  INTEGER NOT NULL CHECK (fiscal_year >= 2026),
    metric                       TEXT NOT NULL,
    metric_definition_version    TEXT NOT NULL,   -- pins to config/metric_definitions.csv, same discipline as annual_facts.mapping_version
    assumption_version           TEXT NOT NULL,
    value                        REAL NOT NULL,
    unit                         TEXT NOT NULL DEFAULT 'USD_millions',
    formula                      TEXT NOT NULL,
    validation_status            TEXT NOT NULL DEFAULT 'unvalidated'
                                     CHECK (validation_status IN ('pass', 'fail', 'blocked', 'unvalidated')),
    information_cutoff           TEXT NOT NULL,
    created_at                   TEXT NOT NULL,
    UNIQUE (scenario_id, metric, fiscal_year, assumption_version)
);
CREATE INDEX IF NOT EXISTS idx_forecast_facts_scenario_year ON forecast_facts(scenario_id, fiscal_year);
```

Each field of `forecast.ForecastYear` (revenue, gross_profit, ...,
deployable_capacity — 40+ metrics) becomes one row per
`(scenario_id, fiscal_year)`, matching `annual_facts`' one-row-per-metric
grain rather than one wide row per year. `fiscal_year >= 2026` is the
structural historical/forecast separation described in §1.

### 2.4 `forecast_lineage`

```sql
CREATE TABLE IF NOT EXISTS forecast_lineage (
    forecast_lineage_id         TEXT PRIMARY KEY,
    forecast_fact_id             TEXT NOT NULL REFERENCES forecast_facts(forecast_fact_id),
    input_historical_fact_id     TEXT REFERENCES annual_facts(annual_fact_id),
    input_forecast_fact_id       TEXT REFERENCES forecast_facts(forecast_fact_id),
    input_assumption_id          TEXT REFERENCES forecast_assumptions(assumption_id),
    operation                    TEXT NOT NULL,
    sequence                     INTEGER NOT NULL,
    CHECK (
        (input_historical_fact_id IS NOT NULL)
        + (input_forecast_fact_id IS NOT NULL)
        + (input_assumption_id IS NOT NULL) >= 1
    )
);
CREATE INDEX IF NOT EXISTS idx_forecast_lineage_fact ON forecast_lineage(forecast_fact_id);
```

Generalizes `annual_lineage`'s two-input-kind `CHECK` (exactly one of
raw/annual) to three input kinds with "at least one," because a forecast
fact routinely combines a prior-year forecast fact, a historical anchor
(e.g. FY2025 beginning cash), and an assumption in a single formula (e.g.
`ending_cash_2026` per §2.3 of `forecast.py`'s `_run_from_metrics`).

### 2.5 `forecast_validation_results`

```sql
CREATE TABLE IF NOT EXISTS forecast_validation_results (
    validation_result_id  TEXT PRIMARY KEY,
    check_name              TEXT NOT NULL,
    scenario_id              TEXT REFERENCES forecast_scenarios(scenario_id),  -- NULL for cross-scenario/global checks
    fiscal_year              INTEGER,                                          -- NULL for scenario-level or global checks
    status                   TEXT NOT NULL CHECK (status IN ('PASS', 'FAIL', 'WARNING')),
    detail                   TEXT NOT NULL,
    forecast_version         TEXT NOT NULL,
    run_at                   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_forecast_validation_check ON forecast_validation_results(check_name);
```

One row per `forecast.ValidationResult` (this round's dataclass) per run.
`scenario_id`/`fiscal_year` nullable because 4 of the 18 checks
(`scenario_ordering`, `assumption_completeness` when reported per-scenario
only, `information_cutoff_compliance`, `no_historical_forecast_mixing`) are
not scoped to a single scenario/year.

### 2.6 `investment_capacity_results`

```sql
CREATE TABLE IF NOT EXISTS investment_capacity_results (
    investment_capacity_result_id      TEXT PRIMARY KEY,
    scenario_id                          TEXT NOT NULL REFERENCES forecast_scenarios(scenario_id),
    fiscal_year                          INTEGER NOT NULL,
    gross_fcf_capacity                   REAL NOT NULL,
    post_dividend_capacity               REAL NOT NULL,
    pre_discretionary_ending_cash        REAL NOT NULL,
    min_cash_buffer                      REAL NOT NULL,
    near_term_debt_repayment_reserve     REAL NOT NULL,
    deployable_capacity                  REAL NOT NULL,
    funding_warning                      INTEGER NOT NULL DEFAULT 0 CHECK (funding_warning IN (0, 1)),
    methodology_note                     TEXT NOT NULL,
    information_cutoff                   TEXT NOT NULL,
    UNIQUE (scenario_id, fiscal_year)
);
```

`methodology_note` is mandatory (`NOT NULL`, no default) by design: item 10
requires that `deployable_capacity` never be presented as a bare number
without the liquidity-buffer/seasonality/covenant/discretion caveats, so the
schema makes it structurally impossible to insert the figure without also
storing that explanation alongside it.

## 3. What this schema deliberately does NOT do

- No column anywhere stores a "plug" or "balancing" value computed backward
  from a target cash or capacity figure — every input to `forecast_facts` is
  either a historical fact, a prior forecast fact, or a `forecast_assumptions`
  row set independently of the output it feeds (item 9).
- No table merges historical and forecast rows into one structure with a
  discriminator column; they remain fully separate tables, so a query that
  forgets to filter cannot silently blend them (item 2's "must never share
  indistinguishable rows").
- No `forecast_facts` row is marked `validation_status = 'pass'` by a
  migration or default — only a validation run (querying
  `forecast_validation_results`) may set it, mirroring `annual_facts`'
  existing `'unvalidated'` default discipline.

## 4. Migration numbering (reserved, not written)

If approved, these would be implemented as six additive `TableMigration`
entries following `0014_annual_fact_observations_original_historical`
(`0015_forecast_scenarios` through `0020_investment_capacity_results`), each
independently testable the same way `tests/unit/test_migrations.py` tests
`0008`-`0014` today. No such migration code exists yet.
