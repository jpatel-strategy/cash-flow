# Validation Totals

Independent numbers to check a finished Power BI report against —
computed directly from `data/curated/target_cash.db` on 2026-09-16, the
same database every CSV in `data/` was exported from. If a built visual
doesn't match one of these, the model/measure wiring has a bug, not the
data.

## FY2025 historical reference values (must never be confused with each other)

| Metric | Value | Source metric key |
|---|---|---|
| CFO | $6,562M | `operating_cash_flow` |
| CapEx (property & equipment acquisitions only) | $3,727M | `capital_expenditure` |
| CFI (total investing cash flow) | $(3,649)M | `investing_cash_flow` |
| FCF (CFO − CapEx) | $2,835M | `free_cash_flow` |

**CapEx ($3,727M) and CFI ($(3,649)M) are two different numbers.** A
Power BI visual that shows CapEx and gets $3,649M has wired CapEx to
`investing_cash_flow` by mistake — the exact error this project was
explicitly warned not to repeat.

## FY2030 scenario headline figures

| Scenario | Revenue | Diluted EPS | Cumulative Deployable Capacity | DCF Value/Share | Enterprise Value | WACC |
|---|---|---|---|---|---|---|
| Base | $110,124.8M | $8.18 | $6,315.0M | $107.29 | $57,736.3M | 8.86% |
| Upside | $121,468.7M | $13.15 | $3,241.9M | $138.32 | $71,873.7M | 8.86% |
| Downside | $92,321.2M | $2.71 | $6,087.5M | $61.55 | $36,898.6M | 8.86% |

Note Upside's cumulative deployable capacity is *lower* than Base's —
this is correct, not a bug: Upside deploys more capital into buybacks
along the way (see `docs/decisions.md`'s Milestone 3A scenario
narratives), leaving less *undeployed* balance at the terminal year,
even though Upside generates more cash overall. A "higher scenario
always wins" assumption baked into a Power BI visual would misread this
— if in doubt, chart deployable capacity alongside cumulative *deployed*
amount so the tradeoff is visible, not just the ending balance.

WACC is scenario-invariant by construction (same capital-structure and
market assumptions applied to all 3 operating scenarios) — a report
where WACC differs by scenario has a bug.

## Row counts (must match `data/*.csv` exactly)

| Table | Rows |
|---|---|
| `fact_annual_historical` | 488 |
| `fact_forecast` | 765 |
| `fact_investment_capacity` | 15 |
| `fact_valuation_results` | 3 |
| `fact_valuation_ufcf` | 15 |
| `fact_validation_forecast` | 229 |
| `fact_validation_valuation` | 28 |
| `fact_quarterly_cash` | 10 |
| `fact_filing_vintage_comparison` | 20 |
| `dim_scenario` | 3 |
| `dim_fiscal_year` | 10 |
| `dim_metric` | 91 |
| `dim_filing` | 8 |
| `dim_date_quarterly` | 5 |

## Validation status (should read 100% in the Validation Summary page)

- Forecast validation checks: **229 / 229 PASS** (0 FAIL, 0 WARNING).
- Valuation validation checks: **28 / 28 PASS** (0 FAIL, 0 WARNING).

If the built report's `Validation Status (Combined Label)` measure ever
reads anything other than "All checks PASS" against this same database,
that is a real finding to investigate — not a display bug to suppress.

## Quarterly cash proof (independent of the forecast model)

| As of | Balance | Context |
|---|---|---|
| 2025-02-01 | $4,762M | FY2024 year-end |
| 2025-05-03 | $2,887M | FY2025 Q1 — seasonal trough |
| 2025-08-02 | $4,341M | FY2025 Q2 |
| 2025-11-01 | $3,822M | FY2025 Q3 |
| 2026-01-31 | $5,488M | FY2025 year-end |

Trough-to-year-end ratio: $2,887M / $5,488M ≈ 52.6% — the real evidence
behind this project's seasonal minimum-cash-buffer policy, independent
of the forecast model itself.
