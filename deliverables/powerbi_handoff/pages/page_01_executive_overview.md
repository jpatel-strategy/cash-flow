# Page 1: Executive Overview

**Wireframe**: `wireframes/page_01_executive_overview.svg`

## Purpose
Answer, within 30 seconds of opening the report: what happened
historically, what's expected under the selected scenario, how much
cash was/will be generated, how much can safely be deployed, and what
evidence backs all of it.

## Filters / slicers
- Scenario selector (slicer on `dim_scenario[scenario_name]`,
  single-select, defaults to "Base").
- Fiscal Year slicer (defaults to FY2030, the terminal forecast year).

## Visuals

| Visual | Type | Fields | Measure(s) |
|---|---|---|---|
| Revenue FY2030 | Card | `dim_fiscal_year`, `dim_scenario` | `Revenue (Actual + Forecast, Combined)` |
| FCF FY2030 | Card | same | `FCF (Forecast)` |
| Deployable Capacity | Card | same | `Deployable Capacity` |
| Implied DCF Value/Share | Card | `dim_scenario` | `Implied Value Per Share` |
| Validation Status | Card (conditional formatting: green if 100%) | — | `Validation Status (Combined Label)` |
| Net Debt (Valuation Date) | Card | `dim_scenario` | `Net Debt (DCF Valuation Date, FY2025 Actual)` |
| Revenue & FCF, Actual vs Forecast | Line chart, dual series | X: `dim_fiscal_year[fiscal_year]`; Y: `Historical Revenue`/`Forecast Revenue` as two distinctly colored+dashed series | See "Formatting conventions" in `dax_measures.md` |
| Deployable Capacity by Scenario | Clustered column | X: `dim_scenario[scenario_name]`; Y: `Cumulative Deployable Capacity (Terminal Year)` | — |
| Capital Allocation Waterfall (mini) | Waterfall chart | Category: waterfall step label; Y: dollar amount | From `fact_investment_capacity` |
| Key Evidence Citations | Table | `dim_filing[accession_number, form_type, filed_at, primary_document_url]` | — |

## Data-status badge
A small text visual reading "Historical: SEC-filed, FY2021-FY2025 ·
Forecast: scenario-based, FY2026-FY2030 · Not investment advice" should
sit directly under the page title, always visible regardless of filter
state.

## Notes
- The Revenue & FCF chart line must render with a visually distinct
  style (dashed vs solid, or a shaded background band) for the forecast
  years — never a single continuous solid line spanning both.
- No visual on this page should silently mix `as_originally_filed` and
  `latest_restated` — filter `fact_annual_historical` to
  `analytical_view = "latest_restated"` everywhere on this page.
