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

Deployable Capacity (LEGACY -- DEPRECATED, do not use as a KPI) =
SUM ( fact_investment_capacity[deployable_capacity] )
-- Milestone 9 correction: this measure is a GROSS, pre-discretionary
-- ceiling -- it embeds carried-forward cash and new borrowing, and never
-- subtracts that year's own repurchases. Preserved, unmodified, only for
-- backward compatibility with fact_investment_capacity (also preserved
-- verbatim). NEVER bind this measure to a headline card, KPI visual, or
-- the Executive Overview page -- see the 4 corrected measures below and
-- docs/investment_capacity_correction_evidence.md.

Cumulative Deployable Capacity (LEGACY -- DEPRECATED, terminal year) =
VAR MaxFY = CALCULATE ( MAX ( fact_investment_capacity[fiscal_year] ), ALLSELECTED ( dim_fiscal_year ) )
RETURN
CALCULATE (
    SUM ( fact_investment_capacity[cumulative_deployable_capacity] ),
    fact_investment_capacity[fiscal_year] = MaxFY
)
-- Also deprecated: adds back only management_selected_deployment
-- (always $0 this round), never share_repurchases actually executed --
-- materially understates total capacity generated for Base/Upside. See
-- "Cumulative Self-Funded Generation" and the other corrected cumulative
-- measures below for the replacement.

-- ============================================================================
-- CORRECTED CAPACITY TAXONOMY (Milestone 9 v2 finance-semantics correction)
-- -- these measures are the executive-facing KPIs. Source:
-- fact_capacity_taxonomy (per scenario-year, version = current) and
-- fact_capacity_horizon (per-scenario cumulative, version = current).
--
-- v2 correction: gross debt issuance is never labeled capacity when
-- simultaneously repaid. debt_funded_incremental_capacity is now the NET
-- of proceeds over repayments; net_mandatory_debt_service is the NET of
-- repayments over proceeds (exactly one is nonzero, or both are zero).
-- self_funded_capacity_generated now excludes opening_excess_liquidity
-- entirely -- a stock is never labeled "generated." Remaining Deployable
-- Headroom now also deducts a forward debt-repayment reserve.
-- ============================================================================

Opening Excess Liquidity =
SUM ( fact_capacity_taxonomy[opening_excess_liquidity] )
-- A STOCK carried forward from prior years -- shown on its own line,
-- NEVER folded into or labeled as "capacity generated."

Gross Debt Proceeds (Supporting) =
SUM ( fact_capacity_taxonomy[gross_debt_proceeds] )
-- Transparent supporting field -- the raw, unnetted debt issuance.
-- Never present this alone as "debt-funded capacity."

Gross Debt Repayments (Supporting) =
SUM ( fact_capacity_taxonomy[gross_debt_repayments] )
-- Transparent supporting field -- the raw, unnetted debt repayment.

Net Mandatory Debt Service =
SUM ( fact_capacity_taxonomy[net_mandatory_debt_service] )
-- = MAX(0, Gross Debt Repayments - Gross Debt Proceeds). Zero when
-- proceeds equal or exceed repayments in the same year.

Self-Funded Capacity Generated =
SUM ( fact_capacity_taxonomy[self_funded_capacity_generated] )
-- Post-dividend internally generated cash, net of Net Mandatory Debt
-- Service -- a pure FLOW. Deliberately EXCLUDES Opening Excess
-- Liquidity (a stock) and EXCLUDES new borrowing entirely.

Debt-Funded Capacity =
SUM ( fact_capacity_taxonomy[debt_funded_incremental_capacity] )
-- = MAX(0, Gross Debt Proceeds - Gross Debt Repayments). Gross issuance
-- that is simultaneously repaid is $0 incremental capacity, never the
-- gross amount. Shown SEPARATELY from Self-Funded Capacity Generated --
-- never combine these into one bar/card without labeling both, and
-- never present new borrowing as if it were internally generated
-- operating capacity.

Total Gross Funding Capacity =
SUM ( fact_capacity_taxonomy[total_gross_funding_capacity] )
-- = Opening Excess Liquidity + Self-Funded Capacity Generated +
-- Debt-Funded Capacity.

Discretionary Deployment =
SUM ( fact_capacity_taxonomy[total_discretionary_deployment] )
-- Share repurchases + strategic investment + voluntary debt reduction +
-- other discretionary uses (the latter three are structural $0 this
-- round -- no policy lever has been modeled for them).

Forward Debt-Repayment Reserve =
SUM ( fact_capacity_taxonomy[forward_debt_repayment_reserve] )
-- Next fiscal year's Net Mandatory Debt Service, held back before
-- calling the residual "headroom." For the terminal FY2030 year this is
-- a documented PROXY (repeats FY2030's own net mandatory debt service)
-- because FY2031 is outside the forecast horizon -- see
-- fact_capacity_taxonomy[forward_reserve_is_proxied].

Remaining Deployable Headroom =
SUM ( fact_capacity_taxonomy[remaining_deployable_headroom] )
-- = MAX(0, Total Gross Funding Capacity - Discretionary Deployment -
-- Forward Debt-Repayment Reserve). THIS is the corrected executive KPI
-- -- the actual amount still available to deploy, net of what has
-- already been spent this year AND net of a reserve for next year's
-- known mandatory debt service. Never sum this measure across multiple
-- fiscal years in the same visual (e.g. a table with FY2026-FY2030
-- columns totaled) -- it is a STOCK, and doing so reproduces the exact
-- double-counting error Milestone 3A already found and fixed once for
-- the legacy measure.

Cumulative Self-Funded Generation (FY2026-FY2030) =
SUM ( fact_capacity_horizon[cumulative_self_funded_generation] )
-- Deliberately EXCLUDES FY2026's own opening excess liquidity (a
-- pre-existing stock, not capacity generated during the horizon).

Cumulative Debt-Funded Capacity (FY2026-FY2030) =
SUM ( fact_capacity_horizon[cumulative_debt_funded_capacity] )

Opening Excess Liquidity (Horizon Start) =
SUM ( fact_capacity_horizon[opening_excess_liquidity_at_horizon_start] )
-- A STOCK, measured once at the start of FY2026 -- never re-added for
-- later years.

Cumulative Discretionary Deployment (FY2026-FY2030) =
SUM ( fact_capacity_horizon[cumulative_discretionary_deployment] )
-- Includes executed share repurchases across all 5 years -- unlike the
-- legacy cumulative measure above, which only ever tracked
-- management_selected_deployment (always $0).

Terminal Remaining Headroom (FY2030) =
SUM ( fact_capacity_horizon[terminal_remaining_headroom] )

Terminal Forward Debt-Repayment Reserve =
SUM ( fact_capacity_horizon[terminal_forward_debt_repayment_reserve] )
-- The fourth reconciling term the v2 correction requires: FY2030's own
-- forward reserve (a documented FY2031 proxy), held back from Terminal
-- Remaining Headroom. See fact_capacity_horizon[terminal_forward_reserve_is_proxied].

Gross Horizon Funding, Before Reserve Adjustments =
SUM ( fact_capacity_horizon[total_horizon_capacity_accessible] )
-- Sourced from the legacy/deprecated-label column (still named
-- total_horizon_capacity_accessible in SQL/CSV for backward
-- compatibility) = Opening Excess Liquidity + Cumulative Self-Funded
-- Generation + Cumulative Debt-Funded Capacity. This is a GROSS figure
-- computed BEFORE Ending Reserve Movement and Terminal Forward
-- Debt-Repayment Reserve are deducted -- under this legacy, pre-adjustment
-- definition it is NOT net accessible/deployable capacity and must not be
-- published as such. It reconciles EXACTLY to Cumulative Discretionary
-- Deployment + Terminal Remaining Headroom + Ending Reserve Movement +
-- Terminal Forward Debt-Repayment Reserve -- see fact_capacity_horizon's
-- own ending_reserve_movement and terminal_forward_debt_repayment_reserve
-- columns and docs/investment_capacity_correction_evidence.md for the
-- proof. This DAX measure carries the corrected, non-misleading label
-- (replacing the legacy/deprecated "Total Horizon Capacity Accessible"
-- name) per the final independent-audit closeout.

Net Horizon Deployable Capacity = -- (not the legacy/deprecated gross measure above)
SUM ( fact_capacity_horizon[net_horizon_deployable_capacity] )
-- This is the corrected,
-- non-legacy figure: = Gross Horizon Funding, Before Reserve Adjustments
-- - Ending Reserve Movement - Terminal Forward Debt-Repayment Reserve.
-- This IS net accessible/deployable capacity (unlike the legacy/deprecated
-- gross measure above) and is the correct headline figure -- use this
-- measure, not the legacy/deprecated Gross Horizon Funding one, wherever
-- "accessible capacity" is reported. Reconciles EXACTLY to Cumulative
-- Discretionary Deployment + Terminal Remaining Headroom (a dual identity;
-- see docs/investment_capacity_correction_evidence.md for the proof).
-- Expected values: Base 9,175.0M; Upside 7,420.7M; Downside 6,387.5M.

Net Debt (Forecast) =
CALCULATE ( SUM ( fact_forecast[value] ), fact_forecast[metric] = "valuation_net_debt" )

Net Debt (DCF Valuation Date, FY2025 Actual) =
SUM ( fact_valuation_results[valuation_date_net_debt] )

-- Compares a metric's forecast value across the 3 scenarios for the
-- same fiscal year -- e.g. how much Revenue Growth % varies between
-- Upside and Downside. Use with a metric/fiscal-year filter context.
-- (For capacity specifically, use Remaining Deployable Headroom -- see
-- the Corrected Capacity Taxonomy section below -- never the legacy,
-- deprecated capacity measure.)
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
