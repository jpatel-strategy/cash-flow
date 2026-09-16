# Page 6: Cash-Flow Bridge & Investment Capacity

**Wireframe**: `wireframes/page_06_cash_flow_bridge_and_investment_capacity.svg`

## Purpose (Milestone 9 correction)

Show, step by step, how operating cash flow becomes actually-deployable
capital — using the corrected taxonomy from
`docs/investment_capacity_correction_evidence.md`, not the deprecated
single "deployable capacity" figure. The legacy figure was arithmetically
correct but economically ambiguous: it never subtracted that year's own
repurchases, and it commingled internally generated cash with new
borrowing. This page makes both distinctions explicit.

## Filters / slicers
- Scenario selector.
- Fiscal Year slicer.

## Visuals

| Visual | Type | Fields |
|---|---|---|
| Capacity waterfall | Waterfall chart | Opening Excess Liquidity (STOCK, own bar) → + Self-Funded Capacity Generated (FLOW) → + Debt-Funded Capacity (net of repayment; own bar, distinctly colored/patterned from self-funded bars) → − Discretionary Deployment → − Forward Debt-Repayment Reserve → = Remaining Deployable Headroom. From `fact_capacity_taxonomy`. |
| Corrected capacity KPI row | 5 cards | Opening Excess Liquidity, Self-Funded Capacity Generated, Debt-Funded Capacity, Discretionary Deployment, Remaining Deployable Headroom — all from `fact_capacity_taxonomy`, selected scenario/year |
| Supporting detail table | Table, small font | Gross Debt Proceeds, Gross Debt Repayments, Net Mandatory Debt Service, Forward Debt-Repayment Reserve (with a "PROXY" badge when `forward_reserve_is_proxied = 1`) — all from `fact_capacity_taxonomy` |
| Legacy reference table | Table, visually de-emphasized (grey, smaller font) | `fact_investment_capacity[deployable_capacity, cumulative_deployable_capacity]`, clearly labeled "DEPRECATED — reference only, not a KPI" |
| Remaining Deployable Headroom by FY | Line chart | X: fiscal year; Y: `remaining_deployable_headroom` from `fact_capacity_taxonomy` — a STOCK; the chart may show it per year, but the page must not let a viewer sum the points (see Notes) |
| Cumulative reconciliation | Table | From `fact_capacity_horizon`: Opening Excess Liquidity + Cumulative Self-Funded Generation + Cumulative Debt-Funded Capacity = Cumulative Discretionary Deployment + Terminal Remaining Headroom + Ending Reserve Movement + Terminal Forward Debt-Repayment Reserve — both sides shown, with a conditional-formatting check that they match |

## Notes

- **Debt-funded capacity must never be visually merged with self-funded
  capacity.** Use a distinct color/pattern in the waterfall and never
  combine them into a single "capacity generated" bar without the split
  visible — new borrowing is not internally generated operating cash,
  and gross issuance that is simultaneously repaid is $0 incremental
  capacity, never the gross amount.
- **Opening Excess Liquidity must never be folded into "capacity
  generated."** It is a STOCK, always its own bar/card — Self-Funded
  Capacity Generated excludes it by construction.
- **Never sum `remaining_deployable_headroom` (or
  `opening_excess_liquidity`) across FY2026-FY2030 in any table or
  visual-level total.** Both are stocks. The correct FY2026-FY2030
  cumulative figures live in `fact_capacity_horizon` and are computed
  without ever re-summing a carried-forward balance — reproducing that
  error was exactly the Milestone 3A bug this project already found and
  fixed once, and exactly the ambiguity Milestone 9 corrected two further
  instances of (self-funded/debt-funded conflation, and headroom without
  a forward debt-service reserve).
- The legacy `fact_investment_capacity` table (and its
  `deployable_capacity`/`cumulative_deployable_capacity` columns) is
  preserved for backward compatibility only. Display it, if at all, as
  a clearly de-emphasized reference table — never as this page's
  headline.
- `funding_warning` (from `fact_forecast`) should surface as a visible
  banner/icon whenever true — this is a real modeled risk, not a bug to
  hide.
- If asked "why does Upside show lower remaining headroom than Base
  despite higher revenue," point to the Discretionary Deployment card:
  Upside deploys far more into buybacks and faster deleveraging, not
  less capacity generated. Conversely, if asked "why is Downside's
  headroom close to Base's despite far lower revenue," point to
  Discretionary Deployment being $0 for Downside (no buybacks) plus its
  lower CapEx-to-revenue ratio — never present reduced investment or
  higher borrowing as if it were improved operating performance.
