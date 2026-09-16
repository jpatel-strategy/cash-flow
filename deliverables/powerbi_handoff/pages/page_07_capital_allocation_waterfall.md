# Page 7: Capital Allocation Waterfall

**Wireframe**: `wireframes/page_07_capital_allocation_waterfall.svg`

## Purpose
Show exactly where every dollar of generated cash went — and prove,
visibly, that no dollar is double-counted across repurchases, debt
repayment, management-selected deployment, deployable capacity, and
ending cash (the explicit no-double-counting requirement from
Milestone 3A).

## Filters / slicers
- Scenario selector.
- Fiscal Year slicer.

## Visuals

| Visual | Type | Fields |
|---|---|---|
| 8-step waterfall | Waterfall chart | Beginning Cash → + CFO → + CFI → + Debt Proceeds → − Debt Repayments → − Dividends → − Share Repurchases → − Management-Selected Deployment → = Ending Cash |
| No-Double-Counting Proof | Card, conditional formatting (green "OK" / red "MISMATCH") | Compares the waterfall's computed ending cash to `fact_forecast[metric="ending_cash"]` for the same scenario/year — should always read "OK" against this project's data |
| Full comparison table | Table | All waterfall steps vs Cash-Flow Bridge ending cash, every scenario × year, side by side |

## Notes
- This page's entire reason for existing is the proof visual — every
  scenario/year combination must show "OK". If a future data refresh
  ever shows "MISMATCH" here, that is a real integrity failure to
  investigate before trusting anything else on the report, not a
  cosmetic issue to filter out of view.
- "Management-selected deployment" is $0 in the current model (no
  discretionary M&A/special-project spending assumed) — the waterfall
  step should still appear, at $0, rather than being omitted, so the
  waterfall's structural completeness is visible even when a step is
  currently unused.
