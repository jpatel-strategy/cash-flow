# Data Dictionary — Power BI Handoff

Star schema: 5 dimension tables, 11 fact tables (9 original + 2 added by
the Milestone 9 capacity correction). All facts trace back to
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

### `fact_investment_capacity.csv` (15 rows) — **DEPRECATED, Milestone 9**
**Grain**: one row per (`scenario_id`, `fiscal_year`). The 9 capacity
waterfall stages (gross FCF capacity → post-dividend capacity →
pre-discretionary ending cash → minimum-cash buffer → near-term debt
reserve → deployable capacity → cumulative deployable capacity), plus
`funding_warning` and a mandatory `methodology_note` disclosing exactly
how each row's numbers were derived.

**This table is preserved verbatim for backward compatibility and its
`deployable_capacity`/`cumulative_deployable_capacity` columns are
DEPRECATED.** Per
`docs/investment_capacity_semantic_audit.md`, `deployable_capacity` is
arithmetically correct but economically ambiguous: it is a gross,
pre-discretionary ceiling that embeds carried-forward cash and new
borrowing, and never subtracts that year's own repurchases before being
displayed. Do not relate this table into any new visual, measure, or
headline card — use `fact_capacity_taxonomy` and `fact_capacity_horizon`
below instead.

### `fact_capacity_taxonomy.csv` (15 rows) — Milestone 9 correction
**Grain**: one row per (`scenario_id`, `fiscal_year`). The corrected
14-field capacity taxonomy: `operating_fcf` (A) →
`post_dividend_internal_generation` (B) → `opening_excess_liquidity` →
`mandatory_debt_uses` → `self_funded_gross_capacity` (C, excludes new
borrowing) → `debt_funded_incremental_capacity` (D, new borrowing,
always shown separately from C) → `total_gross_funding_capacity` (E = C
+ D) → `share_repurchases` / `strategic_investment` /
`voluntary_debt_reduction` / `other_discretionary_uses` (the latter
three are structural $0 placeholders this round) →
`total_discretionary_deployment` (F) → `remaining_deployable_headroom`
(G = MAX(0, E − F), **the corrected executive KPI**) →
`ending_excess_liquidity` (an independent cross-check of G, computed
from ending cash rather than the discretionary-deployment waterfall —
proven equal to G in every row). **Never sum `remaining_deployable_headroom`
across fiscal years** — it is a stock; see `fact_capacity_horizon` for
the correct cumulative figures.

### `fact_capacity_horizon.csv` (3 rows) — Milestone 9 correction
**Grain**: one row per `scenario_id`. The FY2026–FY2030 cumulative
capacity picture, computed WITHOUT summing per-year ending-headroom
balances: `cumulative_self_funded_generation` (excludes FY2026's own
opening excess liquidity), `cumulative_debt_funded_capacity`,
`opening_excess_liquidity_at_horizon_start` (a stock, taken once, from
FY2026 only), `cumulative_discretionary_deployment` (includes executed
repurchases — unlike the legacy cumulative measure, which never did),
`terminal_remaining_headroom` (FY2030's own headroom, a stock),
`ending_reserve_movement` (the change in the minimum-cash-buffer
requirement from FY2026 to FY2030 — the reconciling term, not a plug),
and `total_horizon_capacity_accessible`, which reconciles EXACTLY to
`cumulative_discretionary_deployment + terminal_remaining_headroom +
ending_reserve_movement` for every scenario (proven in
`docs/investment_capacity_correction_evidence.md`).

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
Reserve, Net Debt, Scenario Variance, Validation Status.

**Deployable Capacity is superseded by the Milestone 9 correction.** The
executive-facing capacity KPIs are now the 4 corrected measures --
Self-Funded Capacity Generated, Debt-Funded Capacity, Discretionary
Deployment, and Remaining Deployable Headroom -- plus the 5 cumulative
horizon measures, all defined in `dax_measures.md`'s "Corrected Capacity
Taxonomy" section. The legacy `Deployable Capacity` / `Cumulative
Deployable Capacity` measures are preserved and explicitly marked
deprecated in that same file; do not use them for any new visual.
