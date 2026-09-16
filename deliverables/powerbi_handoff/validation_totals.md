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

| Scenario | Revenue | Diluted EPS | DCF Value/Share | Enterprise Value | WACC |
|---|---|---|---|---|---|
| Base | $110,124.8M | $8.18 | $107.29 | $57,736.3M | 8.86% |
| Upside | $121,468.7M | $13.15 | $138.32 | $71,873.7M | 8.86% |
| Downside | $92,321.2M | $2.71 | $61.55 | $36,898.6M | 8.86% |

WACC is scenario-invariant by construction (same capital-structure and
market assumptions applied to all 3 operating scenarios) — a report
where WACC differs by scenario has a bug.

## FY2030 corrected capacity taxonomy (Milestone 9 correction — the executive KPIs)

| Scenario | Self-Funded Capacity | Debt-Funded Capacity | Total Funding Capacity | Discretionary Deployment | Remaining Headroom |
|---|---|---|---|---|---|
| Base | $6,315.0M | $700.0M | $7,015.0M | $636.3M | $6,378.7M |
| Upside | $3,941.9M | $300.0M | $4,241.9M | $1,498.4M | $2,743.5M |
| Downside | $5,887.5M | $500.0M | $6,387.5M | $0.0M | $6,387.5M |

Note Upside's Remaining Deployable Headroom is *lower* than Base's —
this is correct, not a bug: Upside deploys far more capital into
buybacks along the way ($1,498.4M vs. Base's $636.3M in FY2030 alone —
see `docs/decisions.md`'s Milestone 3A scenario narratives), leaving
less headroom unspent at year end, even though Upside generates more
total funding capacity than Base in most years and much more cash
overall. A "higher scenario always wins" assumption baked into a Power
BI visual would misread this — always show Discretionary Deployment
alongside Remaining Deployable Headroom so the tradeoff is visible, not
just the ending balance. **Never present Debt-Funded Capacity as if it
were internally generated operating capacity** — it is shown as a
separate column specifically so a report cannot conflate the two.

## Cumulative capacity reconciliation, FY2026-FY2030 (Milestone 9 correction)

| Scenario | Cum. Self-Funded | Cum. Debt-Funded | Opening Excess Liquidity | Cum. Discretionary Deployment | Terminal Headroom | Ending Reserve Movement | Total Horizon Capacity |
|---|---|---|---|---|---|---|---|
| Base | $3,490.8M | $3,500.0M | $2,313.2M | $2,796.3M | $6,378.7M | $128.9M | $9,303.9M |
| Upside | $4,776.8M | $1,500.0M | $2,250.3M | $5,377.2M | $2,743.5M | $406.4M | $8,527.1M |
| Downside | $1,169.2M | $2,500.0M | $2,423.2M | $0.0M | $6,387.5M | $(295.2)M | $6,092.3M |

For every scenario: **Total Horizon Capacity = Cumulative Discretionary
Deployment + Terminal Remaining Headroom + Ending Reserve Movement**,
exactly (to within $0.1M rounding) — proven in
`docs/investment_capacity_correction_evidence.md`. Under this corrected,
more complete measure, Upside trails Base by roughly 8% ($8,527.1M vs.
$9,303.9M) rather than the ~48% gap the legacy, deprecated
`cumulative_deployable_capacity` measure would have implied — because
the legacy measure never counted capital Upside had already deployed as
capacity the plan generated. **Never sum per-year
`remaining_deployable_headroom` values across FY2026-FY2030** — use
`fact_capacity_horizon`'s own cumulative columns instead.

## Row counts (must match `data/*.csv` exactly)

| Table | Rows |
|---|---|
| `fact_annual_historical` | 488 |
| `fact_forecast` | 765 |
| `fact_investment_capacity` (DEPRECATED, preserved verbatim) | 15 |
| `fact_capacity_taxonomy` | 15 |
| `fact_capacity_horizon` | 3 |
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
- Capacity taxonomy validation checks (Milestone 9): **147 / 147 PASS** (0 FAIL, 0 WARNING) — 9 per-scenario-year checks × 15 scenario-years + 4 per-scenario checks × 3 scenarios.

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
