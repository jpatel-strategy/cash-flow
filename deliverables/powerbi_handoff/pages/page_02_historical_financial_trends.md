# Page 2: Historical Financial Trends

**Wireframe**: `wireframes/page_02_historical_financial_trends.svg`

## Purpose
Show FY2021-FY2025 actual results only — no forecast series appear
anywhere on this page, so it can stand alone as "what actually
happened" evidence.

## Filters / slicers
- Fiscal Year range slider (FY2021-FY2025, cannot be extended past
  FY2025 — do not add forecast years to this page's date table
  visual-level filter).
- Metric category slicer on `dim_metric[category]`.

## Visuals

| Visual | Type | Fields |
|---|---|---|
| Revenue / Gross Profit / Operating Income / Net Income | Line or area chart | X: `dim_fiscal_year[fiscal_year]` (filtered ≤2025); Y: `fact_annual_historical[value_normalized]` split by `metric`, `analytical_view = "latest_restated"` |
| CFO / CapEx / FCF | Line chart | Same X; Y: `CFO (Historical)`, `CapEx (Historical)`, `FCF (Historical)` measures |
| Capital Allocation: Dividends vs Buybacks vs Debt Repayment | Stacked column | X: fiscal year; Y: `dividends_paid`, `share_repurchases`, `debt_repayments` metrics |
| Full historical fact table | Table/Matrix | Rows: `dim_metric[metric_label]`; Columns: `dim_fiscal_year[year_label]`; Values: `fact_annual_historical[value_normalized]` (latest_restated) |

## Notes
- This is the page a reviewer checks first to confirm "nothing on the
  forecast pages contradicts the filed numbers." Every number here
  should be traceable, cell by cell, back to a specific
  `accession_number` via `fact_annual_historical`.
- Do not round the underlying values in the table visual — use Power
  BI's display-unit formatting ($M) rather than pre-rounding data.
