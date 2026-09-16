# Page 8: DCF Valuation & Sensitivities

**Wireframe**: `wireframes/page_08_dcf_valuation_and_sensitivities.svg`

## Purpose
Present the restrained, scenario-based DCF and its sensitivity to the
two assumptions decision-makers most often ask about (discount rate and
terminal growth; operating margin and revenue growth), clearly labeled
as scenario analysis rather than a price target.

## Filters / slicers
- Scenario selector.

## Visuals

| Visual | Type | Fields |
|---|---|---|
| WACC build | Table | Risk-free rate, ERP, beta, cost of equity, cost of debt (after-tax), equity/debt weights, resulting WACC — from `fact_valuation_results` |
| Valuation Bridge | Waterfall chart | PV(explicit-period UFCF) → + PV(terminal value) → = Enterprise Value → − Net Debt (FY2025 actual) → = Equity Value → ÷ Diluted Shares (FY2025 actual) → = Implied Value/Share |
| WACC × Terminal Growth sensitivity | Matrix with conditional-formatting heatmap | Rows: WACC values; Columns: terminal growth values; Values: implied value/share |
| Operating Margin × Revenue Growth sensitivity | Matrix with conditional-formatting heatmap | Rows: margin values; Columns: growth values; Values: implied value/share or deployable capacity |

## Mandatory disclaimer banner (must appear on this page, not buried in a tooltip)
"This DCF is a scenario-based illustration built entirely from public
FY2025 10-K data and stated assumptions. It is not a price target,
analyst estimate, or investment recommendation."

## Notes
- Net debt and diluted shares in the Valuation Bridge are always the
  FY2025 actual figures (`valuation_date_net_debt`,
  `valuation_date_diluted_shares` from `fact_valuation_results`) —
  never a forecast year's projected balance. This is enforced upstream
  by `check_valuation_date_consistency` in the Python model; the Power
  BI report should not introduce a different net-debt figure by
  accident (e.g. by summing a forecast-year debt metric instead).
- WACC is identical across all 3 scenarios by construction — if a
  visual on this page appears to show WACC varying by scenario, that
  indicates a wiring error, not a real result.
