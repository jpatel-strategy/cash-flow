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
| Implied DCF Value/Share | Card | `dim_scenario` | `Implied Value Per Share` |
| Validation Status | Card (conditional formatting: green if 100%) | — | `Validation Status (Combined Label)` |
| Net Debt (Valuation Date) | Card | `dim_scenario` | `Net Debt (DCF Valuation Date, FY2025 Actual)` |
| Funding Warning? | Card (red icon if true) | `dim_scenario`, `dim_fiscal_year` | From `fact_forecast[metric="funding_warning"]` |
| **Opening Excess Liquidity** (a STOCK, shown separately, never labeled "generated") | Card | `dim_scenario`, `dim_fiscal_year` | `Opening Excess Liquidity` |
| **Self-Funded Capacity Generated** | Card | same | `Self-Funded Capacity Generated` |
| **Debt-Funded Capacity** (net of simultaneous repayment; shown separately, never combined into the self-funded card) | Card | same | `Debt-Funded Capacity` |
| **Discretionary Deployment** | Card | same | `Discretionary Deployment` |
| **Remaining Deployable Headroom** (the corrected executive KPI; net of deployment AND a forward debt-repayment reserve) | Card, visually the largest/most prominent capacity card | same | `Remaining Deployable Headroom` |
| Revenue & FCF, Actual vs Forecast | Line chart, dual series | X: `dim_fiscal_year[fiscal_year]`; Y: `Historical Revenue`/`Forecast Revenue` as two distinctly colored+dashed series | See "Formatting conventions" in `dax_measures.md` |
| Remaining Deployable Headroom by Scenario | Clustered column, WITH a second series for Discretionary Deployment shown alongside | X: `dim_scenario[scenario_name]`; Y1: `Remaining Deployable Headroom`; Y2: `Discretionary Deployment` | So a viewer can see immediately why a higher-revenue scenario can show lower headroom (it deployed more, or carries a real forward debt-service reserve) |
| Capital Allocation Waterfall (mini) | Waterfall chart | Category: waterfall step label; Y: dollar amount | Opening Excess Liquidity → + Self-Funded Capacity Generated → + Debt-Funded Capacity (net of repayment) → − Discretionary Deployment → − Forward Debt-Repayment Reserve → = Remaining Deployable Headroom; from `fact_capacity_taxonomy` |
| Key Evidence Citations | Table | `dim_filing[accession_number, form_type, filed_at, primary_document_url]` | — |

**Never display the legacy `Deployable Capacity` measure (from
`fact_investment_capacity`) on this page.** It is deprecated — see
`data_dictionary.md` and `dax_measures.md`.

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
- **Milestone 9 v2 finance-semantics correction**: no label on this page
  may say "deployable capacity" without specifying whether it means
  gross capacity or remaining headroom — use the 5 corrected labels
  (Opening Excess Liquidity, Self-Funded, Debt-Funded, Discretionary
  Deployment, Remaining Deployable Headroom) exactly as named in
  `dax_measures.md`, never a bare "Capacity" label. Debt-Funded Capacity
  is always the NET of proceeds over repayments — never gross issuance.
