# Page 6: Cash-Flow Bridge & Investment Capacity

**Wireframe**: `wireframes/page_06_cash_flow_bridge_and_investment_capacity.svg`

## Purpose
Show, step by step, how operating cash flow becomes deployable capital
— CFO → CapEx → FCF → dividends → post-dividend capacity → minimum-cash
buffer → near-term debt reserve → deployable capacity — with the
correct (non-double-counted) cumulative figure.

## Filters / slicers
- Scenario selector.
- Fiscal Year slicer.

## Visuals

| Visual | Type | Fields |
|---|---|---|
| Cash-flow-to-capacity waterfall | Waterfall chart | Category: step name (CFO, − CapEx, = FCF, − Dividends, = Post-Dividend Capacity, − Min-Cash Buffer, − Debt Reserve, = Deployable Capacity); Y: `fact_investment_capacity` columns |
| Deployable Capacity & Cumulative Deployable Capacity | Line chart | X: fiscal year; Y: `deployable_capacity`, `cumulative_deployable_capacity` |
| Investment Capacity fact table | Table | `fact_investment_capacity[*]` including `methodology_note` |

## Notes
- The `cumulative_deployable_capacity` column already carries the
  Milestone 3A-corrected value (terminal-year balance + amounts
  actually deployed) — do NOT recompute it in DAX as a running
  `SUM()` across years, which would silently reintroduce the exact
  double-counting bug this project already found and fixed. Read it
  straight from the fact table, or use the
  `Cumulative Deployable Capacity (Terminal Year)` measure in
  `dax_measures.md`.
- `funding_warning` (from `fact_investment_capacity`) should surface as
  a visible banner/icon whenever true (Downside scenario, later years)
  — this is a real modeled risk, not a bug to hide.
