# DAX Measures

Create a blank table named `_Measures` (Power BI convention for a
measures-only "table") and paste these in. All reference the star
schema in `relationship_map.md`; none hardcode a value that should be
an assumption or a database fact.

## Helper pattern: value-lookup by metric key

Both `fact_forecast` and `fact_annual_historical` store one row per
metric per period rather than one column per metric, so every measure
below follows the same `CALCULATE(SUM(...), <table>[metric] = "...")`
pattern. This is deliberate — it means a new forecast metric added to
the database in the future needs no DAX or model change to appear in
these measures' surrounding context (only a new explicit measure if the
report wants to chart it specifically).

```DAX
Forecast Revenue =
CALCULATE ( SUM ( fact_forecast[value] ), fact_forecast[metric] = "revenue" )

Historical Revenue =
CALCULATE (
    SUM ( fact_annual_historical[value_normalized] ),
    fact_annual_historical[metric] = "revenue",
    fact_annual_historical[analytical_view] = "latest_restated"
)
```

## Core measures (as required by the Milestone 6 handoff spec)

```DAX
Revenue Growth % =
CALCULATE ( SUM ( fact_forecast[value] ), fact_forecast[metric] = "revenue_growth_pct" ) / 100

Gross Margin % (Forecast) =
CALCULATE ( SUM ( fact_forecast[value] ), fact_forecast[metric] = "gross_margin_pct" ) / 100

Gross Margin % (Historical) =
DIVIDE (
    CALCULATE ( SUM ( fact_annual_historical[value_normalized] ),
        fact_annual_historical[metric] = "gross_profit",
        fact_annual_historical[analytical_view] = "latest_restated" ),
    CALCULATE ( SUM ( fact_annual_historical[value_normalized] ),
        fact_annual_historical[metric] = "revenue",
        fact_annual_historical[analytical_view] = "latest_restated" )
)

Operating Margin % (Forecast) =
CALCULATE ( SUM ( fact_forecast[value] ), fact_forecast[metric] = "operating_margin_pct" ) / 100

Operating Margin % (Historical) =
DIVIDE (
    CALCULATE ( SUM ( fact_annual_historical[value_normalized] ),
        fact_annual_historical[metric] = "operating_income",
        fact_annual_historical[analytical_view] = "latest_restated" ),
    CALCULATE ( SUM ( fact_annual_historical[value_normalized] ),
        fact_annual_historical[metric] = "revenue",
        fact_annual_historical[analytical_view] = "latest_restated" )
)

CFO (Forecast) =
CALCULATE ( SUM ( fact_forecast[value] ), fact_forecast[metric] = "operating_cash_flow" )

CFO (Historical) =
CALCULATE ( SUM ( fact_annual_historical[value_normalized] ),
    fact_annual_historical[metric] = "operating_cash_flow",
    fact_annual_historical[analytical_view] = "latest_restated" )

FCF (Forecast) =
CALCULATE ( SUM ( fact_forecast[value] ), fact_forecast[metric] = "free_cash_flow" )

FCF (Historical) =
CALCULATE ( SUM ( fact_annual_historical[value_normalized] ),
    fact_annual_historical[metric] = "free_cash_flow",
    fact_annual_historical[analytical_view] = "latest_restated" )

-- CapEx is always the property-and-equipment acquisition outflow, never
-- total investing cash flow (General Rule 9). FY2025 reference values
-- (CFO $6,562M, CapEx $3,727M, CFI $(3,649)M, FCF $2,835M) must
-- reproduce exactly from this measure and "CFO (Historical)" above.
CapEx (Historical) =
CALCULATE ( SUM ( fact_annual_historical[value_normalized] ),
    fact_annual_historical[metric] = "capital_expenditure",
    fact_annual_historical[analytical_view] = "latest_restated" )

FCF Margin % (Forecast) =
DIVIDE ( [FCF (Forecast)], [Forecast Revenue] )

FCF Margin % (Historical) =
DIVIDE ( [FCF (Historical)], [Historical Revenue] )

Post-Dividend Capacity =
SUM ( fact_investment_capacity[post_dividend_capacity] )

Minimum Cash Requirement =
SUM ( fact_investment_capacity[min_cash_buffer] )

Debt Reserve =
SUM ( fact_investment_capacity[near_term_debt_repayment_reserve] )

Deployable Capacity =
SUM ( fact_investment_capacity[deployable_capacity] )

-- Milestone 3A's corrected formula: terminal-year balance already
-- reflects every prior year's carried-forward unused capacity, so the
-- cumulative figure is the TERMINAL row plus whatever was actually
-- deployed -- never a naive SUM() of every year's balance.
Cumulative Deployable Capacity (Terminal Year) =
VAR MaxFY = CALCULATE ( MAX ( fact_investment_capacity[fiscal_year] ), ALLSELECTED ( dim_fiscal_year ) )
RETURN
CALCULATE (
    SUM ( fact_investment_capacity[cumulative_deployable_capacity] ),
    fact_investment_capacity[fiscal_year] = MaxFY
)

Net Debt (Forecast) =
CALCULATE ( SUM ( fact_forecast[value] ), fact_forecast[metric] = "valuation_net_debt" )

Net Debt (DCF Valuation Date, FY2025 Actual) =
SUM ( fact_valuation_results[valuation_date_net_debt] )

-- Compares a metric's forecast value across the 3 scenarios for the
-- same fiscal year -- e.g. how much Deployable Capacity varies between
-- Upside and Downside. Use with a metric/fiscal-year filter context.
Scenario Variance (Selected Metric) =
VAR UpsideVal =
    CALCULATE ( SUM ( fact_forecast[value] ), fact_forecast[scenario_id] = "upside" )
VAR DownsideVal =
    CALCULATE ( SUM ( fact_forecast[value] ), fact_forecast[scenario_id] = "downside" )
RETURN
UpsideVal - DownsideVal

Validation Status (Forecast, % Pass) =
DIVIDE (
    CALCULATE ( COUNTROWS ( fact_validation_forecast ), fact_validation_forecast[status] = "PASS" ),
    COUNTROWS ( fact_validation_forecast )
)

Validation Status (Valuation, % Pass) =
DIVIDE (
    CALCULATE ( COUNTROWS ( fact_validation_valuation ), fact_validation_valuation[status] = "PASS" ),
    COUNTROWS ( fact_validation_valuation )
)

Validation Status (Combined Label) =
VAR FailCount =
    CALCULATE ( COUNTROWS ( fact_validation_forecast ), fact_validation_forecast[status] = "FAIL" )
    + CALCULATE ( COUNTROWS ( fact_validation_valuation ), fact_validation_valuation[status] = "FAIL" )
RETURN
IF ( FailCount = 0, "All checks PASS", FORMAT ( FailCount, "0" ) & " check(s) FAILING" )
```

## Supporting measures

```DAX
Implied Value Per Share =
SUM ( fact_valuation_results[implied_value_per_share] )

Enterprise Value =
SUM ( fact_valuation_results[enterprise_value] )

WACC % =
SUM ( fact_valuation_results[wacc_pct] ) / 100

Funding Warning Flag =
MAX ( fact_investment_capacity[funding_warning] )

-- Combined actual + forecast revenue line for a single continuous
-- FY2021-FY2030 chart on the Scenario Forecast Explorer page.
Revenue (Actual + Forecast, Combined) =
VAR HistPart = [Historical Revenue]
VAR FcstPart = [Forecast Revenue]
RETURN
IF ( NOT ISBLANK ( FcstPart ), FcstPart, HistPart )
```

## Formatting conventions

- All `_pct`/`%` measures are stored as ratios (e.g. `0.294` not
  `29.4`) — format as Percentage in the visual, not in the DAX.
- All dollar measures are in $ millions, matching every other
  deliverable in this project (Excel workbook, web cockpit) — do not
  rescale to thousands or whole dollars.
- Historical/forecast pairs (e.g. `CFO (Historical)` / `CFO
  (Forecast)`) are intentionally separate measures, not one
  auto-switching measure, so a chart can show both series distinctly
  colored and distinctly labeled per the "clear actual-vs-forecast
  distinction" requirement.
