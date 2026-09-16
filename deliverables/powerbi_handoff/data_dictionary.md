# Data Dictionary — Power BI Handoff

Star schema: 5 dimension tables, 9 fact tables. All facts trace back to
`data/curated/target_cash.db`, itself built only from the 8 SEC filings
registered in `docs/sources.csv`, under the project's FY2025 10-K
information cutoff (2026-03-11).

## Dimension tables

### `dim_scenario.csv` (3 rows, key: `scenario_id`)
| Column | Description |
|---|---|
| `scenario_id` | `base` / `upside` / `downside`. |
| `scenario_name` | Display name ("Base", "Upside", "Downside"). |
| `description` | One-line scenario description. |
| `version` | Assumption-set version tag (`v1`). |
| `information_cutoff` | The filing-date cutoff this scenario's assumptions were built under. |

### `dim_fiscal_year.csv` (10 rows, key: `fiscal_year`)
FY2021–FY2030. `period_type`/`is_historical`/`is_forecast` flag FY2021–
FY2025 as Historical (actual, filed results) and FY2026–FY2030 as
Forecast (scenario projections) — this distinction must be visually
obvious on every chart per the Milestone 5/6/7 "clear actual-vs-forecast
distinction" requirement.

### `dim_metric.csv` (91 rows, key: `metric_key`)
Every metric key that appears in any fact table (historical, forecast,
assumption, or quarterly), with a heuristic `metric_label` (title-cased
for display) and a `category` (Income Statement / Balance Sheet / Cash
Flow / Investment Capacity / Ratio-Driver / Other). Labels and
categories are presentation-only classifications of existing metric
keys — no values are invented.

### `dim_filing.csv` (8 rows, key: `accession_number`)
The full source-filing register: every 10-K/10-Q this project is built
from, with SEC accession number, filed date, period of report, and
source URL. Mirrors `docs/sources.csv`.

### `dim_date_quarterly.csv` (5 rows, key: `as_of_date`)
The 5 real balance-sheet dates used in the quarterly cash proof
(FY2024 year-end through FY2025 year-end).

## Fact tables

### `fact_annual_historical.csv` (488 rows)
**Grain**: one row per (`metric`, `fiscal_year`, `analytical_view`).
Historical (FY2021–FY2025) annual facts in both the `as_originally_filed`
and `latest_restated` analytical views, so filing-vintage differences
are queryable directly. Carries `direct_or_derived`, `fact_status`,
`validation_status`, and the source `accession_number`/`filed_at` for
full lineage back to a specific filing.

### `fact_forecast.csv` (765 rows)
**Grain**: one row per (`scenario_id`, `fiscal_year`, `metric`,
`assumption_version`). FY2026–FY2030 projected values for all 51
persisted forecast metrics across all 3 scenarios, each with its
`formula` string (so a Power BI user can see exactly how a cell was
computed, not just the resulting number).

### `fact_investment_capacity.csv` (15 rows)
**Grain**: one row per (`scenario_id`, `fiscal_year`). The 9 capacity
waterfall stages (gross FCF capacity → post-dividend capacity →
pre-discretionary ending cash → minimum-cash buffer → near-term debt
reserve → deployable capacity → cumulative deployable capacity), plus
`funding_warning` and a mandatory `methodology_note` disclosing exactly
how each row's numbers were derived.

### `fact_valuation_results.csv` (3 rows)
**Grain**: one row per `scenario_id`. The full DCF bridge: PV of explicit
period, terminal value (undiscounted and discounted), enterprise value,
valuation-date net debt, equity value, valuation-date diluted shares,
and implied value per share — plus the WACC and terminal-growth
assumptions used.

### `fact_valuation_ufcf.csv` (15 rows)
**Grain**: one row per (`scenario_id`, `fiscal_year`). Per-year
unlevered free cash flow and its discounted present value, feeding the
DCF explicit-period sum.

### `fact_validation_forecast.csv` (229 rows) / `fact_validation_valuation.csv` (28 rows)
**Grain**: one row per (`check_name`, `scenario_id`, [`fiscal_year`]).
Every automated validation check this project runs (arithmetic
invariants, structural completeness checks, the one genuinely
independent capital-allocation-waterfall reasonableness test, and
scenario-comparative checks), with its PASS/FAIL/WARNING status and a
human-readable `detail` string. All 257 checks currently PASS — see
`validation_totals.md`.

### `fact_quarterly_cash.csv` (10 rows)
**Grain**: one row per (`metric`, `as_of_date`). The real FY2025
quarterly cash-and-equivalents balances (from each 10-Q/10-K balance
sheet) proving Target's seasonal cash trough, independent of the
forecast model.

### `fact_filing_vintage_comparison.csv` (20 rows)
**Grain**: one row per (`metric`, `fiscal_year`), for revenue,
cost_of_sales, gross_profit, and operating_expenses across FY2021–
FY2025. Computed (not a raw table) by pivoting
`fact_annual_historical` to compare `as_originally_filed` against
`latest_restated` and flagging any line where FY2024's segment/expense
reclassification changed a reported figure.

## Core measures required for this handoff

These are implemented as DAX in `dax_measures.md`, each sourced from
the fact tables above (never hardcoded):

Revenue Growth %, Gross Margin %, Operating Margin %, CFO, FCF, FCF
Margin %, Post-Dividend Capacity, Minimum Cash Requirement, Debt
Reserve, Deployable Capacity, Net Debt, Scenario Variance, Validation
Status.
