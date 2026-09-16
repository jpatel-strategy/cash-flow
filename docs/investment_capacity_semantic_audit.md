# Investment Capacity Semantic Audit

**Status: DIAGNOSTIC ONLY. No code, assumptions, database records, Excel
workbook, Power BI exports, website files, or portfolio claims were
modified to produce this document.** Every figure below was obtained by
*calling* existing, unmodified functions in `src/target_cash/forecast.py`
and inspecting their output — the source files themselves were only
read, never edited. Git working tree is clean before and after this
document was written (verified: `git status --short` returns nothing
outside this new file).

## 0. Trigger for this audit

Independent review flagged that the label **"deployable capacity"** is
economically ambiguous, given:

| Scenario | FY2030 Revenue | FY2030 Deployable Capacity (as currently displayed) |
|---|---|---|
| Base | $110,125M | $6,315.0M |
| Upside | $121,469M | $3,242.0M |
| Downside | $92,321M | $6,087.5M |

This document verifies whether these numbers are **arithmetically
correct** (they are — see §5) and whether the **label** is economically
correct (it is **not**, without qualification — see §5 and §11). It does
not change any number; it explains what each existing number actually
measures, maps it to a required taxonomy, and quantifies the gap between
what a reader would likely assume "deployable capacity" means and what
the field actually computes.

## 1. Files and formulas inspected

| File | What was inspected |
|---|---|
| `src/target_cash/forecast.py:889-951` | `ForecastYear` dataclass — every field's definition and docstring. |
| `src/target_cash/forecast.py:953-1114` | `_run_from_metrics()` — the complete formula chain that produces every `ForecastYear` field, line by line. |
| `src/target_cash/forecast.py:1889-1977` | `capital_allocation_waterfall()` — the independently-sequenced 8-step waterfall and its docstring, which explicitly states the deployable-capacity checkpoint is measured "BEFORE step 7's repurchase is subtracted." |
| `src/target_cash/forecast.py:1979-2037` | `verify_no_double_counting()` — the three proven conservation identities (a), (b), (c) that this audit's reconciliations reuse and re-verify. |
| `src/target_cash/forecast.py:2039-2063` | `capital_allocation_repurchase_classification()` — confirms repurchases are a fixed forecast assumption (payout ratio), never solved backward. |
| `src/target_cash/forecast.py:2334-2377` | `cumulative_deployable_capacity()` / `cumulative_deployable_capacity_through_each_year()` — the Milestone 3A-corrected cumulative formula and its own documented scope. |
| `src/target_cash/forecast.py:315-680` (`build_assumptions`) | Source assumption values per scenario/year for every driver referenced below. |
| `scripts/build_excel_model.py` (Investment Capacity / Capital Allocation sheets) | Confirms the Excel workbook uses the identical field names and identical (unmodified) semantics. |
| `deliverables/web_cockpit/js/app.js`, `index.html` | Confirms the web cockpit displays the identical field, identically labeled, with the identical semantics. |
| `deliverables/powerbi_handoff/dax_measures.md`, `data_dictionary.md` | Confirms the Power BI handoff's DAX measure `Deployable Capacity` is a straight `SUM()` of the same underlying field, with the identical semantics. |

**Finding**: the ambiguity identified below is not confined to one
deliverable — the same field name, computed the same way, is displayed
identically across the Python model, the database schema
(`investment_capacity_results.deployable_capacity`), the Excel workbook,
the Power BI DAX measure, and the web cockpit. Any correction must be
coordinated across all five surfaces; this document does not attempt
that correction (per the diagnostic-only instruction).

All numbers in this document were produced by running
`target_cash.forecast.build_assumptions()` and
`target_cash.forecast.run_all_scenarios()` (unmodified) and reading the
resulting `ForecastYear` objects — the same functions every other
deliverable in this project already calls.

## 2. Required taxonomy (A–G): definitions and mapping to existing fields

| # | Taxonomy definition | Exact existing-field match? | Mapping |
|---|---|---|---|
| A | Operating FCF = CFO − CapEx | **Yes, exact** | `free_cash_flow` (`fcf = cfo - capex`, `forecast.py:1027`) |
| B | Post-dividend internally generated capacity = FCF − dividends | **Yes, exact** | `post_dividend_capacity` (`post_div_fcf = fcf - dividends_paid`, `forecast.py:1038`) |
| C | Gross pre-discretionary capacity **excluding new borrowing** | **No existing field.** Derivable: `beginning_cash + CFO + CFI − dividends_paid − debt_repayments` | GAP — see §11, defect 1 |
| D | Debt-funded incremental capacity (new borrowing) | **No existing field under this name.** Numerically identical to the existing `debt_proceeds` field — i.e. gross new borrowing, with no separate "incremental" adjustment applied to it. | GAP — see §11, defect 1 |
| E | Total funding capacity = C + D | **Yes, exact, but under a different name.** `pre_discretionary_ending_cash` already equals C + D exactly (verified numerically for all 15 scenario-years in §4, §8) | Mislabeled — see §11, defect 2 |
| F | Management-selected deployment | **Yes, exact** | `management_selected_deployment` (always `None`/$0 in every scenario this round — no discretionary deployment beyond the routine buyback program has been selected) |
| G | Residual unused capacity | **No existing field.** Derivable exactly two equivalent ways: (i) `deployable_capacity − share_repurchases − management_selected_deployment`, or (ii) `ending_cash − min_cash_buffer − near_term_debt_repayment_reserve` (when the capacity is not floored at zero). Both were computed independently for every scenario-year in §4 and matched to the cent. | GAP — this is the metric closest to what a reader intuitively expects "deployable capacity" to mean. See §11, defect 3, and §12 recommendation. |

**The central finding, stated plainly**: the existing field named
`deployable_capacity` does **not** correspond to G (residual unused
capacity — "what's actually still available to deploy"). It corresponds
most closely to **E minus the minimum-cash-buffer and near-term-debt-
reserve holdbacks** — i.e., a **gross ceiling** on how much could be
spent on repurchases and discretionary deployment this year, computed
**before** that year's own repurchase decision is subtracted. Every
dollar of `share_repurchases` executed in a given year is drawn from
this same displayed `deployable_capacity` figure, but the figure itself
never reflects that draw-down. See §5, Q3/Q4/Q8/Q11 for the direct
evidence.

## 3. Full line-item reference (formula, sign, source, classification, stock/flow)

| Line item | Exact formula | Sign convention | Source assumption | Mandatory / Operational / Financing / Discretionary | Stock or Flow |
|---|---|---|---|---|---|
| Beginning cash | `beginning_cash_t = ending_cash_(t-1)`; FY2026 seed = FY2025 actual `cash_and_equivalents_balance_sheet` ($5,488.0M, historical) | Positive balance | n/a (rolled forward; FY2026 seed is a historical fact, not an assumption) | n/a — balance-sheet carryover | **Stock** |
| Revenue | `revenue_t = revenue_(t-1) * (1 + revenue_growth_pct_t/100)` | Positive | `revenue_growth_pct` | Operational | Flow |
| Net income | `pretax_income - income_tax_expense` | Positive (all scenarios, all years) | `effective_tax_rate_pct`, plus operating/interest inputs | Operational | Flow |
| CFO | `net_income + da_cfo_addback + inventory_cash_impact + ap_cash_impact + other_operating_cf` | Positive | `da_cfo_addback_pct_of_revenue`, `inventory_pct_of_revenue`, `ap_pct_of_cogs`, `other_operating_cf_musd` | Operational | Flow |
| CapEx | `revenue * capex_pct_of_revenue/100` | Positive (recorded as a cash **outflow** — `investing_cash_flow = -CapEx`) | `capex_pct_of_revenue` | Operational (investing) | Flow |
| FCF (A) | `CFO − CapEx` | Positive (all scenarios, all years) | Derived (no separate assumption) | Operational | Flow |
| Dividends | `dps_t * diluted_shares_t`; `dps_t = dps_(t-1)*(1+dividend_per_share_growth_pct/100)` | Cash **outflow** | `dividend_per_share_growth_pct` | **Treated as non-discretionary** in this model's own waterfall (`capital_allocation_waterfall` step 3, sequenced before the discretionary step 7) — a policy commitment, not a legal obligation | Flow |
| Post-dividend capacity (B) | `FCF − dividends_paid` | Can be **negative** (Downside FY2026 = −$174.0M) | Derived | Operational | Flow |
| Mandatory debt repayment | `debt_repayments` (scheduled) | Cash outflow | `debt_repayments_musd` | Mandatory / Financing | Flow |
| Near-term debt reserve | `= debt_repayments` (same-year proxy — **not** a real maturity ladder; documented limitation) | Holdback (subtracted from available capacity, not itself a cash movement) | Derived from `debt_repayments_musd` | Mandatory / Financing (requirement, not a payment) | **Requirement, proxied by a flow** — see §9 |
| New debt issuance | `debt_proceeds` (scheduled) | Cash **inflow** | `debt_proceeds_musd` | **Treated as scheduled, not discretionary**, per `capital_allocation_waterfall`'s own docstring ("proceeds and repayments together, since both are equally 'scheduled'") | Flow |
| Net borrowing | `debt_proceeds − debt_repayments` | Can be negative (net deleveraging) or positive (net issuance) | Derived — no existing standalone field; currently folded into `mandatory_financing_flows` together with dividends | Financing | Flow |
| Repurchases | `max(0, post_dividend_capacity * buyback_payout_pct_of_post_dividend_fcf / 100)` | Cash outflow, floored at $0 | `buyback_payout_pct_of_post_dividend_fcf` | **Discretionary** (this model's own `capital_allocation_repurchase_classification()` confirms: a fixed payout-ratio assumption, never solved backward) | Flow |
| Other discretionary deployment (F) | `management_selected_deployment` | Cash outflow when nonzero | None assigned this round — always $0/`None` | Discretionary | Flow |
| Cash before discretionary deployment | `beginning_cash + CFO + CFI + mandatory_financing_flows`, where `mandatory_financing_flows = -dividends_paid + debt_proceeds - debt_repayments` | Positive | Derived | n/a — a checkpoint balance | **Stock** |
| Minimum cash buffer | `revenue * min_cash_buffer_pct_of_revenue/100` | Holdback | `min_cash_buffer_pct_of_revenue` | Policy requirement | **Requirement, proxied by a flow-scaled figure** (scales with current-year revenue, not a fixed stock target) |
| Gross capacity excl. new debt (C) | `beginning_cash + CFO + CFI - dividends_paid - debt_repayments` | Positive | Derived — **no existing field** | Combination of Stock (beginning cash) + Flows | Mixed — see §9 |
| Debt-funded incremental capacity (D) | `= debt_proceeds` | Positive | `debt_proceeds_musd` | Financing (scheduled, per this model) | Flow |
| Total funding capacity (E) | `C + D` — numerically **identical** to the existing `pre_discretionary_ending_cash` field | Positive | Derived | Mixed | Mixed — see §9 |
| Management-selected deployment (F) | Same as "Other discretionary deployment" above | Cash outflow when nonzero | None assigned this round | Discretionary | Flow |
| Residual unused capacity (G) | `deployable_capacity - share_repurchases - management_selected_deployment` ≡ `ending_cash - min_cash_buffer - near_term_debt_repayment_reserve` (unfloored case) | Positive in all 15 scenario-years modeled | Derived — **no existing field** | n/a — a checkpoint balance, net of ALL uses | **Stock** |
| Ending cash | `pre_discretionary_ending_cash - share_repurchases - management_selected_deployment` | Positive | Derived (proven identity a) | n/a | **Stock** |
| Ending debt | `beginning_debt + debt_proceeds - debt_repayments` | Positive | Derived | n/a | **Stock** |
| Valuation net debt (forecast-year) | `total_debt_gaap_ending - ending_cash` | Can be positive or negative in principle (always positive in this run) | Derived | n/a | **Stock** — reference/scenario-comparison only; **the actual DCF valuation deliberately does NOT use this field**, using FY2025 historical net debt instead (`valuation.py`'s `check_valuation_date_consistency`, re-confirmed in `docs/final_project_evidence.md` §8) |
| Annual incremental capacity | **No existing field.** Diagnostic-only derivation used in this document: `deployable_capacity_t - G_(t-1)`, with `G` for FY2025 undefined (treated as $0 baseline, a known limitation — see §11 defect 4) | Positive in all computed cases | Derived, illustrative only | n/a | Flow (by construction) |
| Cumulative capacity | `cumulative_deployable_capacity()` = terminal year's own `deployable_capacity` + total `management_selected_deployment` across the horizon (currently $0) | Positive | Existing function, `forecast.py:2334` | n/a | **Stock** (explicitly, per its own docstring) — see §11 defect 5 for why this still inherits part of the ambiguity |

## 4. Full per-year, per-scenario tables (FY2026–FY2030)

Every figure below is a direct read of `ForecastYear` fields (or a
simple derivation reconciled in §5/§8), computed by calling
`target_cash.forecast.run_all_scenarios()` unmodified. All values $M
unless noted.

### Base scenario

| Line item | FY2026 | FY2027 | FY2028 | FY2029 | FY2030 |
|---|---|---|---|---|---|
| Beginning cash | 5,488.0 | 6,188.4 | 6,981.2 | 7,827.5 | 8,728.0 |
| Revenue | 105,827.8 | 106,886.1 | 107,954.9 | 109,034.5 | 110,124.8 |
| Net income | 3,681.7 | 3,671.3 | 3,661.2 | 3,649.6 | 3,636.6 |
| CFO | 7,060.7 | 7,283.9 | 7,443.1 | 7,604.1 | 7,765.8 |
| CapEx | 3,809.8 | 3,847.9 | 3,886.4 | 3,925.2 | 3,964.5 |
| FCF (A) | 3,250.9 | 3,436.0 | 3,556.7 | 3,678.9 | 3,801.3 |
| Dividends | 2,083.6 | 2,114.6 | 2,146.1 | 2,178.1 | 2,210.6 |
| Post-dividend capacity (B) | 1,167.3 | 1,321.3 | 1,410.6 | 1,500.8 | 1,590.8 |
| Mandatory debt repayment | 700.0 | 700.0 | 700.0 | 700.0 | 700.0 |
| Near-term debt reserve | 700.0 | 700.0 | 700.0 | 700.0 | 700.0 |
| New debt issuance | 700.0 | 700.0 | 700.0 | 700.0 | 700.0 |
| Net borrowing | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Repurchases | 466.9 | 528.5 | 564.2 | 600.3 | 636.3 |
| Other discretionary deployment (F) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Cash before discretionary deployment | 6,655.3 | 7,509.7 | 8,391.8 | 9,328.3 | 10,318.8 |
| Minimum cash buffer | 3,174.8 | 3,206.6 | 3,238.6 | 3,271.0 | 3,303.7 |
| Gross capacity excl. new debt (C) | 5,955.3 | 6,809.7 | 7,691.8 | 8,628.3 | 9,618.8 |
| Debt-funded incremental capacity (D) | 700.0 | 700.0 | 700.0 | 700.0 | 700.0 |
| Total funding capacity (E) | 6,655.3 | 7,509.7 | 8,391.8 | 9,328.3 | 10,318.8 |
| Management-selected deployment (F) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Residual unused capacity (G) | 2,313.5 | 3,074.6 | 3,888.9 | 4,757.0 | 5,678.7 |
| Ending cash | 6,188.4 | 6,981.2 | 7,827.5 | 8,728.0 | 9,682.5 |
| Ending debt | 14,343.0 | 14,343.0 | 14,343.0 | 14,343.0 | 14,343.0 |
| Valuation net debt (forecast-year, reference only) | 8,154.6 | 7,361.8 | 6,515.5 | 5,615.0 | 4,660.5 |
| **Displayed "deployable_capacity" (existing field)** | **2,780.5** | **3,603.1** | **4,453.1** | **5,357.3** | **6,315.0** |
| Annual incremental capacity (diagnostic-derived) | 2,780.5 | 1,289.6 | 1,378.5 | 1,468.4 | 1,558.1 |
| Cumulative capacity (existing fn, running) | 2,780.5 | 3,603.1 | 4,453.1 | 5,357.3 | 6,315.0 |

### Upside scenario

| Line item | FY2026 | FY2027 | FY2028 | FY2029 | FY2030 |
|---|---|---|---|---|---|
| Beginning cash | 5,488.0 | 5,727.8 | 5,544.3 | 5,584.8 | 5,861.6 |
| Revenue | 107,923.4 | 111,161.1 | 114,495.9 | 117,930.8 | 121,468.7 |
| Net income | 3,743.5 | 4,165.1 | 4,606.7 | 5,069.8 | 5,556.3 |
| CFO | 8,832.3 | 8,082.1 | 8,775.7 | 9,502.5 | 10,263.6 |
| CapEx | 4,640.7 | 4,779.9 | 4,923.3 | 5,071.0 | 5,223.2 |
| FCF (A) | 4,191.6 | 3,302.2 | 3,852.4 | 4,431.5 | 5,040.4 |
| Dividends | 2,103.1 | 2,154.4 | 2,207.0 | 2,260.8 | 2,316.0 |
| Post-dividend capacity (B) | 2,088.5 | 1,147.8 | 1,645.4 | 2,170.6 | 2,724.4 |
| Mandatory debt repayment | 1,000.0 | 1,000.0 | 1,000.0 | 1,000.0 | 1,000.0 |
| Near-term debt reserve | 1,000.0 | 1,000.0 | 1,000.0 | 1,000.0 | 1,000.0 |
| New debt issuance | 300.0 | 300.0 | 300.0 | 300.0 | 300.0 |
| Net borrowing | −700.0 | −700.0 | −700.0 | −700.0 | −700.0 |
| Repurchases | 1,148.7 | 631.3 | 905.0 | 1,193.9 | 1,498.4 |
| Other discretionary deployment (F) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Cash before discretionary deployment | 6,876.5 | 6,175.6 | 6,489.7 | 7,055.4 | 7,886.0 |
| Minimum cash buffer | 3,237.7 | 3,334.8 | 3,434.9 | 3,537.9 | 3,644.1 |
| Gross capacity excl. new debt (C) | 6,576.5 | 5,875.6 | 6,189.7 | 6,755.4 | 7,586.0 |
| Debt-funded incremental capacity (D) | 300.0 | 300.0 | 300.0 | 300.0 | 300.0 |
| Total funding capacity (E) | 6,876.5 | 6,175.6 | 6,489.7 | 7,055.4 | 7,886.0 |
| Management-selected deployment (F) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Residual unused capacity (G) | 1,490.1 | 1,209.5 | 1,149.9 | 1,323.6 | 1,743.5 |
| Ending cash | 5,727.8 | 5,544.3 | 5,584.8 | 5,861.6 | 6,387.6 |
| Ending debt | 13,643.0 | 12,943.0 | 12,243.0 | 11,543.0 | 10,843.0 |
| Valuation net debt (forecast-year, reference only) | 7,915.2 | 7,398.7 | 6,658.2 | 5,681.4 | 4,455.4 |
| **Displayed "deployable_capacity" (existing field)** | **2,638.8** | **1,840.8** | **2,054.9** | **2,517.5** | **3,241.9** |
| Annual incremental capacity (diagnostic-derived) | 2,638.8 | 350.7 | 845.4 | 1,367.6 | 1,918.3 |
| Cumulative capacity (existing fn, running) | 2,638.8 | 1,840.8 | 2,054.9 | 2,517.5 | 3,241.9 |

### Downside scenario

| Line item | FY2026 | FY2027 | FY2028 | FY2029 | FY2030 |
|---|---|---|---|---|---|
| Beginning cash | 5,488.0 | 5,514.0 | 7,126.4 | 8,257.6 | 8,927.5 |
| Revenue | 102,160.5 | 99,606.5 | 97,116.3 | 94,688.4 | 92,321.2 |
| Net income | 3,539.6 | 2,922.5 | 2,333.7 | 1,770.5 | 1,235.0 |
| CFO | 4,739.5 | 6,254.4 | 5,703.5 | 5,174.2 | 4,667.6 |
| CapEx | 2,860.5 | 2,789.0 | 2,719.3 | 2,651.3 | 2,585.0 |
| FCF (A) | 1,879.0 | 3,465.4 | 2,984.2 | 2,522.9 | 2,082.6 |
| Dividends | 2,053.0 | 2,053.0 | 2,053.0 | 2,053.0 | 2,053.0 |
| Post-dividend capacity (B) | −174.0 | 1,412.4 | 931.2 | 469.9 | 29.6 |
| Mandatory debt repayment | 300.0 | 300.0 | 300.0 | 300.0 | 300.0 |
| Near-term debt reserve | 300.0 | 300.0 | 300.0 | 300.0 | 300.0 |
| New debt issuance | 500.0 | 500.0 | 500.0 | 500.0 | 500.0 |
| Net borrowing | 200.0 | 200.0 | 200.0 | 200.0 | 200.0 |
| Repurchases | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Other discretionary deployment (F) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Cash before discretionary deployment | 5,514.0 | 7,126.4 | 8,257.6 | 8,927.5 | 9,157.2 |
| Minimum cash buffer | 3,064.8 | 2,988.2 | 2,913.5 | 2,840.7 | 2,769.6 |
| Gross capacity excl. new debt (C) | 5,014.0 | 6,626.4 | 7,757.6 | 8,427.5 | 8,657.2 |
| Debt-funded incremental capacity (D) | 500.0 | 500.0 | 500.0 | 500.0 | 500.0 |
| Total funding capacity (E) | 5,514.0 | 7,126.4 | 8,257.6 | 8,927.5 | 9,157.2 |
| Management-selected deployment (F) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Residual unused capacity (G) | 2,149.2 | 3,838.2 | 5,044.2 | 5,786.9 | 6,087.5 |
| Ending cash | 5,514.0 | 7,126.4 | 8,257.6 | 8,927.5 | 9,157.2 |
| Ending debt | 14,543.0 | 14,743.0 | 14,943.0 | 15,143.0 | 15,343.0 |
| Valuation net debt (forecast-year, reference only) | 9,029.0 | 7,616.6 | 6,685.4 | 6,215.5 | 6,185.8 |
| **Displayed "deployable_capacity" (existing field)** | **2,149.2** | **3,838.2** | **5,044.2** | **5,786.9** | **6,087.5** |
| Annual incremental capacity (diagnostic-derived) | 2,149.2 | 1,689.1 | 1,205.9 | 742.7 | 300.7 |
| Cumulative capacity (existing fn, running) | 2,149.2 | 3,838.2 | 5,044.2 | 5,786.9 | 6,087.5 |

**Note on Downside**: because `buyback_payout_pct_of_post_dividend_fcf =
0%` in every year of this scenario (confirmed in the source assumption
set, §7), `share_repurchases = 0` every year. This makes G (residual
unused capacity) **exactly equal** to the displayed `deployable_capacity`
figure for Downside, in every year — the ambiguity described in this
document happens to be **invisible** for Downside specifically, purely
because Downside never executes a discretionary use of the pool. It is
fully present for Base and Upside, where real dollars are actually
drawn down each year.

## 5. FY2030 reconciliation and the 12 required questions

### Q1. Why is Upside deployable capacity materially below Base?

Because Upside's assumption set drives **much larger discretionary and
mandatory cash outflows relative to its own cash generation**, so far
less unspent cash accumulates as carried-forward stock, even though
Upside generates the most cash of the three scenarios:

- Upside's buyback payout ratio is **55%** of post-dividend FCF vs.
  Base's **40%** — and Upside's post-dividend FCF is also larger in
  most years, so absolute repurchases are far larger (FY2030: $1,498.4M
  vs. Base's $636.3M — a cumulative $5,377.2M spent 2026-2030 vs. Base's
  $2,796.3M).
- Upside pays down debt net **$700M/year** ($1,000M repayment vs. $300M
  new issuance) vs. Base's flat roll ($700M repayment = $700M issuance,
  net $0).
- Upside's minimum cash buffer is larger in dollar terms (3% of a
  bigger revenue base).
- Net effect: Upside's FY2030 beginning cash is only $5,861.6M vs.
  Base's $8,728.0M — **$2,866.4M less carried-forward stock** — which
  is the single largest term in the FY2030 bridge (§6).

The FY2030 bridge (§6) attributes every dollar of the $3,073.1M gap.

### Q2. Why is Downside capacity nearly equal to Base despite much lower revenue?

Because Downside's `buyback_payout_pct_of_post_dividend_fcf = 0%` in
every year — it **spends nothing** on repurchases — so it retains 100%
of whatever (smaller) cash it generates, while Base retains only
roughly 60% of its (larger) cash generation after buybacks. Downside
also has the lowest CapEx-to-revenue ratio (2.8% vs. Base's 3.6%),
which partially offsets its much lower revenue and net income. The
combination (near-zero discretionary spend + lower capital intensity)
lets an accumulating, un-deployed cash stock build up almost as large
as Base's, despite Downside's FY2030 FCF being 45% lower than Base's
($2,082.6M vs. $3,801.3M). The FY2030 bridge (§6) attributes every
dollar of the $227.5M gap.

### Q3. Are repurchases deducted before the displayed capacity figure?

**No.** `deployable_capacity = max(0, pre_discretionary_ending_cash -
min_cash_buffer - near_term_debt_repayment_reserve)`
(`forecast.py:1071`) — `share_repurchases` does not appear anywhere in
this formula. Repurchases are computed independently, from
`post_dividend_capacity` (not from `deployable_capacity`), and are only
subtracted later, in the derivation of `ending_cash`
(`forecast.py:1053`) and in `capital_allocation_waterfall`'s step 7.

### Q4. Is management-selected deployment deducted before the displayed capacity figure?

**No**, for the identical structural reason as Q3 —
`management_selected_deployment` does not appear in the
`deployable_capacity` formula either. It is only applied at step 7b of
`capital_allocation_waterfall` and in the `ending_cash` conservation
identity. (It is currently $0/`None` in every scenario-year, so this has
no numerical effect this round, but the structural gap is identical to
Q3's.)

### Q5. Does new borrowing increase deployable capacity?

**Yes, directly and dollar-for-dollar (before the floor).**
`debt_proceeds` flows into `mandatory_financing_flows`, which flows
directly into `pre_discretionary_ending_cash`, which flows directly into
`deployable_capacity`. A dollar of new (scheduled) borrowing is
indistinguishable, inside the displayed capacity figure, from a dollar
of internally generated operating cash flow. This is exactly the C/D
distinction the required taxonomy calls for and which does not
currently exist as separate fields (§2, §11 defect 1).

### Q6. Does reduced CapEx increase Downside capacity?

**Yes.** `FCF = CFO - CapEx`, and Downside's `capex_pct_of_revenue`
(2.8%) is the lowest of the three scenarios (vs. Base 3.6%, Upside
4.3%). Lower CapEx, holding CFO constant, mechanically increases FCF,
`post_dividend_capacity`, `pre_discretionary_ending_cash`, and therefore
`deployable_capacity`. This is a real, intended, and correctly-computed
scenario design choice (Downside deliberately assumes capital
discipline) — not a bug — but it is a second, independent contributor
to Q2's answer, alongside the zero-buyback assumption.

### Q7. Are dividends scenario-dependent?

**Yes.** `dividend_per_share_growth_pct`: Base = 2.0%/year, Upside =
4.0%/year, Downside = **0.0%/year** (frozen, not cut — matching the
scenario narrative on file in `docs/decisions.md`'s Milestone 3A entry).
Downside's `dividends_paid` is exactly flat at $2,053.0M every year
2026-2030 (confirmed in §4's table); Base and Upside both grow theirs
each year.

### Q8. Is the current headline number gross capacity or residual unused capacity?

**Neither, cleanly — it is a hybrid, which is the core of the ambiguity.**
It is not a pure "residual unused capacity" (G) because repurchases and
management-selected deployment are never subtracted from it (Q3, Q4).
It is not a pure "new capacity generated this year" flow either, because
it embeds `beginning_cash` — a stock of everything carried forward,
undeployed, from every prior year (Q9). The most precise honest
description: **a gross, pre-discretionary, cumulative-stock ceiling** —
the maximum amount that could be spent on repurchases and discretionary
deployment this year while still respecting the minimum-cash and
near-term-debt-reserve holdbacks, computed before this year's own
spending decision is applied.

### Q9. Does cumulative capacity contain beginning excess cash?

**Yes, directly.** `pre_discretionary_ending_cash` (and therefore
`deployable_capacity`) recursively embeds `beginning_cash`, which for
FY2026 is Target's actual, real, FY2025 year-end cash balance —
**$5,488.0M**, a historical fact that predates the entire forecast
horizon, not "capacity generated" by any scenario assumption. That
$5,488.0M (net of the running minimum-cash/debt/dividend/repurchase
adjustments) flows all the way through the 5-year chain into the
FY2030 `deployable_capacity`/`cumulative_deployable_capacity` figures.
A reader told "the model generated $6,315M of cumulative capacity"
would reasonably assume that figure represents value created *by the
forecast*, when a material portion of it is simply the company's
pre-existing cash pile, carried forward and never spent.

### Q10. Can any carried cash be counted in more than one year?

**Not in the dedicated `cumulative_deployable_capacity()` function** —
that was exactly the Milestone 3A bug, and it remains fixed: the
function uses only the terminal year's own balance plus deployment, not
a `sum()` across years (re-verified: `forecast.py:2358-2360`). **But the
risk is not eliminated at the presentation layer.** Every deliverable
(Excel's Investment Capacity sheet, the web cockpit's per-year table,
this document's own §4 tables) displays `deployable_capacity` as a
row with one column per fiscal year, side by side — exactly the layout
that invites a reader to sum the row by eye, which would silently
reproduce the original 2.6x-3.8x overstatement bug. No UI element in any
current deliverable warns against this at the point of display.

### Q11. Is any dollar counted both as capacity and as deployment?

**Not in any additive database total** — `deployable_capacity` and
`share_repurchases` are never summed together anywhere in the schema,
and `verify_no_double_counting()`'s three identities (re-run and
re-confirmed for all 15 scenario-years in §4/§8) prove no dollar is
double-summed. **But the same dollar does appear, unqualified, in two
figures that a reader would reasonably interpret as describing the same
conceptual bucket ("money available to deploy") at two different points
in time within the same reporting year.** Concretely: of Base's FY2030
`deployable_capacity` ($6,315.0M), $636.3M of it (the same year's own
repurchases) was **already spent** by the time that figure is reported
— it is simultaneously presented as "capacity" and, in a separate line
item, as an executed use. The two labels do not contradict each other
mathematically (the identities hold exactly), but a reader who sees
"$6,315.0M deployable capacity" and adds the reported "$636.3M
repurchases" as if it were additional room left on top would overstate
true availability by exactly the repurchase amount.

### Q12. Which metric should be presented as the primary executive KPI?

Per the required taxonomy, **G — residual unused capacity** — is the
economically correct "what is actually still available to deploy right
now" figure, and none of the current deliverables display it as a named,
labeled field today. Recommended (not applied — see §12) as the primary
executive KPI, replacing or sitting alongside the current
`deployable_capacity` display, with the existing field relabeled to make
clear it is a **gross, pre-discretionary ceiling**, not a residual.

## 6. Base-vs-Upside bridge (FY2030 deployable capacity) — reconciles exactly

| Step | Amount |
|---|---|
| **Base FY2030 deployable capacity** | **$6,315.0M** |
| Δ Beginning cash (Upside − Base) | −$2,866.4M |
| Δ CFO | +$2,497.8M |
| Δ CFI (= −ΔCapEx) | −$1,258.7M |
| Δ Dividends (subtracted) | −$105.4M |
| Δ New debt issuance | −$400.0M |
| Δ Mandatory debt repayment (subtracted) | −$300.0M |
| Δ Minimum cash buffer (subtracted) | −$340.3M |
| Δ Near-term debt reserve (subtracted) | −$300.0M |
| **Sum of deltas** | **−$3,073.1M** |
| **Actual difference (Upside − Base)** | **−$3,073.1M** ✓ reconciles exactly |
| **Upside FY2030 deployable capacity** | **$3,242.0M** |

## 7. Base-vs-Downside bridge (FY2030 deployable capacity) — reconciles exactly

| Step | Amount |
|---|---|
| **Base FY2030 deployable capacity** | **$6,315.0M** |
| Δ Beginning cash (Downside − Base) | +$199.5M |
| Δ CFO | −$3,098.2M |
| Δ CFI (= −ΔCapEx) | +$1,379.5M |
| Δ Dividends (subtracted) | +$157.6M |
| Δ New debt issuance | −$200.0M |
| Δ Mandatory debt repayment (subtracted) | +$400.0M |
| Δ Minimum cash buffer (subtracted) | +$534.1M |
| Δ Near-term debt reserve (subtracted) | +$400.0M |
| **Sum of deltas** | **−$227.5M** |
| **Actual difference (Downside − Base)** | **−$227.5M** ✓ reconciles exactly |
| **Downside FY2030 deployable capacity** | **$6,087.5M** |

Both bridges were computed by decomposing the exact `deployable_capacity`
formula term by term and independently summing the deltas; both sums
match the actual reported difference to the cent (rounding to $0.1M for
display).

## 8. Five-year source/use table — reconciles exactly for every scenario-year

Requested identity: *Beginning available liquidity + internally
generated capacity + incremental borrowing − mandatory debt requirements
− discretionary deployment = ending available liquidity.*

Mapped to existing fields (all confirmed exact matches, not
approximations):

```
beginning_cash + post_dividend_capacity(B) + debt_proceeds
    − debt_repayments − share_repurchases − management_selected_deployment
    = ending_cash
```

This is algebraically identical to `verify_no_double_counting()`'s
already-tested identity (c), regrouped — dividends are folded into B
(post-dividend capacity), which is exactly how taxonomy item B is
defined. Verified independently for **all 15 scenario-years** (3
scenarios × 5 years):

| Scenario | FY | LHS (computed) | RHS (`ending_cash`) | Match |
|---|---|---|---|---|
| Base | 2026 | 6,188.38 | 6,188.38 | ✓ |
| Base | 2027 | 6,981.18 | 6,981.18 | ✓ |
| Base | 2028 | 7,827.54 | 7,827.54 | ✓ |
| Base | 2029 | 8,728.00 | 8,728.00 | ✓ |
| Base | 2030 | 9,682.46 | 9,682.46 | ✓ |
| Upside | 2026 | 5,727.84 | 5,727.84 | ✓ |
| Upside | 2027 | 5,544.34 | 5,544.34 | ✓ |
| Upside | 2028 | 5,584.78 | 5,584.78 | ✓ |
| Upside | 2029 | 5,861.56 | 5,861.56 | ✓ |
| Upside | 2030 | 6,387.56 | 6,387.56 | ✓ |
| Downside | 2026 | 5,513.97 | 5,513.97 | ✓ |
| Downside | 2027 | 7,126.41 | 7,126.41 | ✓ |
| Downside | 2028 | 8,257.64 | 8,257.64 | ✓ |
| Downside | 2029 | 8,927.52 | 8,927.52 | ✓ |
| Downside | 2030 | 9,157.16 | 9,157.16 | ✓ |

**All 15 rows reconcile exactly** (differences under $0.01M, i.e.
floating-point rounding only).

## 9. Stock vs. flow separation — explicit warnings

| Classification | Line items |
|---|---|
| **Stock** (a balance at a point in time — never sum across years) | Beginning cash, Cash before discretionary deployment, Ending cash, Ending debt, Valuation net debt (forecast-year), Residual unused capacity (G), and the **existing `deployable_capacity` field itself** |
| **Flow** (a movement during a year — safe to sum across years, with care) | Revenue, Net income, CFO, CapEx, FCF (A), Dividends, Post-dividend capacity (B), Mandatory debt repayment, New debt issuance, Net borrowing, Repurchases, Management-selected deployment (F), Annual incremental capacity (diagnostic-derived) |
| **Requirement / holdback** (neither a stock nor a flow in the ordinary sense — a policy-set minimum, proxied here by a formula) | Minimum cash buffer, Near-term debt reserve |
| **Mixed** (a stock-plus-flow blend — the direct source of this audit's central finding) | Gross capacity excl. new debt (C), Total funding capacity (E), and by extension the existing `deployable_capacity` and `cumulative_deployable_capacity` fields |

**Explicit warning, re-confirmed by this audit**: do **not** add the
per-year `deployable_capacity` values in §4's tables together across
FY2026-FY2030. Doing so reproduces the exact Milestone 3A double-
counting error (a dollar sitting unspent in FY2026 would be counted
again in FY2027, FY2028, FY2029, and FY2030, since it is carried forward
via `beginning_cash` into every subsequent year's own stock figure). The
dedicated `cumulative_deployable_capacity()` function already avoids
this (§1, §11 defect 5 notwithstanding) — always use that function's
output, never a manual sum of the per-year row.

## 10. A diagnostic-only alternative metric (illustrative — not implemented anywhere)

Because `cumulative_deployable_capacity()` adds back only
`management_selected_deployment` (always $0 this round) to the terminal
year's balance, it does **not** add back `share_repurchases` actually
executed in the four non-terminal years — even though those dollars
represent capacity that was genuinely generated by the plan and put to
productive use, not capacity that evaporated. This means the current
"cumulative capacity" headline substantially **understates** total
capacity generated for any scenario with material buybacks (Base,
Upside), while being coincidentally accurate for Downside (which never
buys back).

An alternative, fully-reconciled definition — **"Total Capacity
Generated Over the Horizon" = terminal-year G + total repurchases
executed 2026-2030 + total management-selected deployment** — produces a
materially different comparative picture:

| Scenario | Current "cumulative_deployable_capacity" | Alternative "Total Capacity Generated" (G_terminal + Σ repurchases + Σ deployment) | Change in the Base-vs-scenario gap |
|---|---|---|---|
| Base | $6,315.0M | $5,678.7M + $2,796.3M + $0 = **$8,475.0M** | — |
| Upside | $3,242.0M | $1,743.5M + $5,377.2M + $0 = **$7,120.7M** | Gap narrows from **−48.7%** to **−16.0%** vs. Base |
| Downside | $6,087.5M | $6,087.5M + $0 + $0 = **$6,087.5M** (unchanged — no buybacks) | No change |

Both components of the alternative metric were verified against an
independent full-horizon roll-up of the source/use identity in §8 (sum
of B + net borrowing across all 5 years = change in cash + total
repurchases + total deployment), matching to within $0.02M for Base.

**This alternative metric is presented for diagnostic illustration
only.** It is not implemented in any code, database table, Excel sheet,
Power BI measure, or web page, and this document takes no position on
which of the two definitions (or some third definition) an independent
reviewer should ultimately adopt — only that the choice is **not
neutral**: it flips the qualitative headline from "Upside generates
less than half of Base's cumulative capacity" to "Upside trails Base by
roughly one-sixth once actually-deployed capital is counted as capacity
generated, not capacity lost."

## 11. Findings

### Arithmetic correctness

**Confirmed correct.** Every formula was re-read directly from source,
every value was reproduced by calling the unmodified, already-tested
production functions, all three `verify_no_double_counting()` identities
were re-verified for all 15 scenario-years, the FY2030 Base-vs-Upside
and Base-vs-Downside bridges reconcile exactly to the cent, and the
5-year source/use identity reconciles exactly for all 15 scenario-years.
**No arithmetic defect was found.** The 401-test pytest suite and all
three deliverable-verification scripts (Excel, Power BI, web cockpit)
were not re-run as part of this diagnostic (no code changed, so no
regression is possible), but nothing in this audit contradicts any of
their prior passing results.

### Label / economic correctness

**Confirmed materially misleading, without qualification, as currently
labeled and presented**, for the reasons detailed in §5 (especially Q3,
Q4, Q8, Q9, Q11) and quantified in §10. The underlying computation is
sound; the name attached to it ("deployable capacity," implying "what
remains available to deploy") does not match what the field actually
measures ("a gross ceiling on discretionary spending room, inclusive of
carried-forward stock, before this year's own discretionary spending is
subtracted").

### Confirmed defect list

1. **No field separates "internally generated funding capacity" (C)
   from "debt-funded incremental capacity" (D).** New borrowing
   (`debt_proceeds`) is commingled into the same `mandatory_financing_flows`
   bucket as dividends and mandatory repayments, and flows into
   `deployable_capacity` indistinguishably from organically generated
   cash (Q5).
2. **`pre_discretionary_ending_cash` (which is exactly taxonomy item E,
   "total funding capacity") is not labeled as such anywhere** — it
   reads as a plain checkpoint variable name, obscuring that it is
   already the sum of C and D.
3. **No field represents G ("residual unused capacity")** — the metric
   closest to a reader's likely intuitive understanding of "deployable
   capacity" does not exist as a named, displayed field in any
   deliverable today (Q3, Q4, Q8, Q12).
4. **"Annual incremental capacity" does not exist as a field or
   function anywhere in the codebase.** This document's own diagnostic
   derivation of it required an arbitrary boundary assumption for FY2026
   (no FY2025 baseline "deployable capacity" concept exists), which is
   itself a limitation of the derivation, not a defect this audit can
   resolve without a design decision.
5. **`cumulative_deployable_capacity()` — while free of the original
   Milestone 3A double-counting bug — still inherits part of the same
   ambiguity**: it adds back only `management_selected_deployment`
   (currently always $0) to the terminal year's gross ceiling, never
   `share_repurchases` actually executed along the way, which
   understates "total capacity generated and deployed" for any scenario
   with material buybacks (§10).
6. **The identical ambiguous label and identical (unmodified) semantics
   are propagated, unchanged, across all five surfaces**: the database
   schema (`investment_capacity_results.deployable_capacity`), the
   Python model, the Excel workbook, the Power BI DAX measure, and the
   web cockpit (§1). A correction, if adopted, is not a one-file fix.
7. **Every current deliverable displays `deployable_capacity` as a
   per-year row across FY2026-FY2030**, a layout that visually invites
   the exact double-counting error Milestone 3A already found and fixed
   once, with no on-page warning at the point of display against
   summing the row (Q10).

### No arithmetic defect was found; all defects above are labeling, disclosure, and metric-design gaps, not calculation errors.

## 12. Recommended corrections — NOT APPLIED

Recorded here for independent review and decision; nothing below has
been implemented in code, data, or any deliverable.

1. Add explicit, separately labeled fields for C (self-funded capacity
   excluding new borrowing) and D (debt-funded incremental capacity),
   so E (total funding capacity) is visibly the sum of two economically
   distinct sources rather than one opaque number.
2. Rename or clearly re-badge the existing `deployable_capacity` field
   (e.g. to "Gross Discretionary Capacity Ceiling" or similar) to stop
   implying it is a residual.
3. Add a new field/column for G (residual unused capacity), computed as
   `deployable_capacity − share_repurchases − management_selected_deployment`,
   and consider promoting it — not the current `deployable_capacity`
   field — to the primary executive KPI position across all
   deliverables (Q12).
4. Decide, with independent input, on a defensible FY2026 boundary
   convention before implementing "annual incremental capacity" as a
   persisted field (defect 4).
5. Decide whether `cumulative_deployable_capacity()` should be redefined
   to add back total repurchases executed (not just
   `management_selected_deployment`), given §10's quantified impact on
   the Base-vs-Upside comparison — this is a substantive methodology
   choice, not a mechanical fix, and should not be made without sign-off.
6. If any of the above is adopted, propagate the same fix consistently
   across the database schema, the Python forecast engine, the Excel
   workbook, the Power BI DAX measures, and the web cockpit — a
   partial fix (e.g. Python-only) would leave the deliverables
   internally inconsistent with each other.
7. Add an explicit on-page warning, in any presentation layer that shows
   `deployable_capacity` (or its eventual replacement) per year, against
   summing the column — even after defect 3/5 are addressed, a reader
   unfamiliar with the stock/flow distinction could still make this
   mistake with a superficially similar-looking metric.

## 13. No-change confirmation

- `git status --short` immediately before writing this document: clean.
- `git status --short` immediately after writing this document: shows
  only this new, untracked file (`docs/investment_capacity_semantic_audit.md`).
- No file under `src/`, `sql/`, `config/`, `scripts/`, `data/`,
  `deliverables/`, or `tests/` was opened in write mode during this
  diagnostic.
- No database write operation (`INSERT`, `UPDATE`, `DELETE`, or any
  `persist-*` CLI command) was executed.
- This document itself is committed as a standalone, diagnostic-only
  commit (repository policy requires no untracked files be left
  uncommitted). That commit contains only this file — no source,
  config, database, or deliverable file is included in it, and no
  correction described in §12 has been applied anywhere.
