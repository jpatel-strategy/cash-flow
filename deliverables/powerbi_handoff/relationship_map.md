# Relationship Map

Set these in Power BI's *Model view* exactly as listed. All
relationships are one-to-many (dimension "1" side → fact "many" side),
single cross-filter direction (dimension filters fact) unless noted.

| From (dimension, "1" side) | To (fact, "many" side) | Key |
|---|---|---|
| `dim_scenario[scenario_id]` | `fact_forecast[scenario_id]` | scenario_id |
| `dim_scenario[scenario_id]` | `fact_investment_capacity[scenario_id]` | scenario_id |
| `dim_scenario[scenario_id]` | `fact_capacity_taxonomy[scenario_id]` | scenario_id |
| `dim_scenario[scenario_id]` | `fact_capacity_horizon[scenario_id]` | scenario_id |
| `dim_scenario[scenario_id]` | `fact_valuation_results[scenario_id]` | scenario_id |
| `dim_scenario[scenario_id]` | `fact_valuation_ufcf[scenario_id]` | scenario_id |
| `dim_scenario[scenario_id]` | `fact_validation_forecast[scenario_id]` | scenario_id (some rows null — cross-scenario checks) |
| `dim_scenario[scenario_id]` | `fact_validation_valuation[scenario_id]` | scenario_id (some rows null) |
| `dim_fiscal_year[fiscal_year]` | `fact_annual_historical[fiscal_year]` | fiscal_year |
| `dim_fiscal_year[fiscal_year]` | `fact_forecast[fiscal_year]` | fiscal_year |
| `dim_fiscal_year[fiscal_year]` | `fact_investment_capacity[fiscal_year]` | fiscal_year |
| `dim_fiscal_year[fiscal_year]` | `fact_capacity_taxonomy[fiscal_year]` | fiscal_year |
| `dim_fiscal_year[fiscal_year]` | `fact_valuation_ufcf[fiscal_year]` | fiscal_year |
| `dim_fiscal_year[fiscal_year]` | `fact_validation_forecast[fiscal_year]` | fiscal_year (some rows null) |
| `dim_fiscal_year[fiscal_year]` | `fact_filing_vintage_comparison[fiscal_year]` | fiscal_year |
| `dim_metric[metric_key]` | `fact_annual_historical[metric]` | metric |
| `dim_metric[metric_key]` | `fact_forecast[metric]` | metric |
| `dim_metric[metric_key]` | `fact_quarterly_cash[metric]` | metric |
| `dim_metric[metric_key]` | `fact_filing_vintage_comparison[metric]` | metric |
| `dim_filing[accession_number]` | `fact_annual_historical[accession_number]` | accession_number |
| `dim_filing[accession_number]` | `fact_quarterly_cash[accession_number]` | accession_number |
| `dim_date_quarterly[as_of_date]` | `fact_quarterly_cash[as_of_date]` | as_of_date |

## Notes

- **Milestone 9 correction**: `fact_investment_capacity` (and its
  `deployable_capacity`/`cumulative_deployable_capacity` columns) is
  preserved verbatim for backward compatibility and is DEPRECATED --
  never relate it into a new visual or measure. `fact_capacity_taxonomy`
  (per scenario-year) and `fact_capacity_horizon` (per-scenario
  cumulative) are the corrected tables; every new capacity measure in
  `dax_measures.md` reads from these two instead.
- `fact_annual_historical` carries BOTH `as_originally_filed` and
  `latest_restated` rows for the same (metric, fiscal_year) — when
  building a "headline" visual (Executive Overview, Scenario Forecast
  Explorer), filter to `analytical_view = "latest_restated"` unless the
  visual is specifically the Filing-Vintage Comparison page, which
  needs both.
- `fact_validation_forecast`/`fact_validation_valuation` rows for
  scenario-invariant or structural checks legitimately have a null
  `scenario_id` and/or `fiscal_year` — do not inner-join these away;
  use a one-to-many relationship (Power BI handles blanks correctly by
  default) rather than filtering nulls out at import.
- No fact table relates directly to another fact table. This keeps the
  model a true star (not a snowflake bridging fact-to-fact), which is
  what makes the DAX in `dax_measures.md` behave predictably under
  cross-filtering from any dimension.
- Mark `dim_fiscal_year` as a **Date table is not required** here since
  `fiscal_year` is a whole-number fiscal year, not a calendar date —
  do not mark it as a Power BI "Date table."
