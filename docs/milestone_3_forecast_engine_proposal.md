# Milestone 3: Forecast and Investment Capacity Engine -- Proposal (Dry Run, Not Persisted)

**Status: pure in-memory dry run. Nothing in this document, or in `src/target_cash/forecast.py`, has been written to `data/curated/target_cash.db`. No `forecast_*` table exists. No DCF, Excel, Power BI, or website work has begun.** Milestone 2's accepted historical facts, mappings, observations, and lineage are unmodified. Generated live by `scripts/build_milestone_3_proposal.py` from `target_cash.forecast` -- every number below is computed by that module, not hand-transcribed.

**Stop point: this document is submitted for reviewer approval before any forecast schema is implemented or any forecast fact is persisted.**

---

## 1. Forecast Information Cutoff Policy

- **`FORECAST_INFORMATION_CUTOFF = '2026-03-11'`** (accession `0000027419-26-000016`, the FY2025 10-K).
- This is deliberately **distinct** from `config/model.yml`'s project-wide `information_cutoff` (2026-09-14), which records when this review session performed its own analysis, not the latest registered filing an assumption may cite.
- The FY2025 10-K is the latest of the 8 filings in `docs/sources.csv` -- every other registered source (FY2025 Q1-Q3 10-Qs) was filed earlier in fiscal 2025, before the 10-K closed the year.
- Every `Assumption` row's `information_cutoff` field defaults to this constant and is validated (`information_cutoff_compliance` check, Section 9) to never exceed it -- no assumption may cite a later 10-Q, analyst estimate, or any post-cutoff information.
- Every `Assumption` also carries `assumption_id`, `scenario`, `forecast_year`, `value`, `unit`, `rationale`, `historical_reference`, `source_evidence`, `review_status` (`'proposed'` for every row this round -- only a human reviewer may advance it), and `version` (`'v1'`), per item 1's explicit field list.

## 2. Forecast Schema Proposal

See `docs/milestone_3_forecast_schema_proposal.md` for the full proposed DDL (`forecast_scenarios`, `forecast_assumptions`, `forecast_facts`, `forecast_lineage`, `forecast_validation_results`, `investment_capacity_results`). **Not implemented** -- no migration exists yet; `src/target_cash/migrations.py` is unchanged this round.

## 3. Scenario Definitions

- **BASE**: continuation of supportable FY2021-FY2025 trends. Explicitly does **not** revert to FY2021's pandemic-driven peak gross margin (29.28%) or growth rate. Holds SG&A leverage flat at the FY2025 level, extrapolates the observed rising D&A/revenue trend, and assumes a representative (non-FY2022-outlier) effective tax rate.
- **UPSIDE**: stronger execution bounded by Target's own historical range -- every upside assumption sits at or below the best value Target has actually reported in the 5-year window (gross margin capped at the FY2021 max, revenue growth capped at the FY2022 max, etc.), so the scenario stays operationally plausible rather than unprecedented. One deliberate exception: CapEx intensity is *higher* in the upside case (funding the stronger growth), which is why the `scenario_ordering` validation check (Section 9) excludes CapEx/FCF/repurchases from its monotonic-ordering expectations per item 12's own instruction.
- **DOWNSIDE**: revenue and margin pressure with working-capital consumption (inventory build, AP tightening), bounded to roughly 1.5x the single worst historical year -- a continued-deterioration case, not a fabricated crisis. Dividends are frozen (0% growth) rather than cut, because Target's dividends_paid has grown in every one of the 5 historical years with no observed cut; share repurchases go to zero; a small, fixed net debt issuance (not a plug -- see item 9) is assumed as a pre-committed liquidity assumption.
- No scenario uses an arbitrary symmetric spread (e.g. base growth +-1%): every value below traces to a specific historical minimum/median/maximum or a documented policy choice (see each rationale in Section 5).

## 4. Historical Range Analysis (FY2021-FY2025, latest_restated)

| Metric | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 | Min | Median | Max |
|---|---|---|---|---|---|---|---|---|
| Gross margin % | 29.28% | 24.57% | 27.54% | 28.21% | 27.93% | 24.57% | 27.93% | 29.28% |
| SG&A % of revenue | 18.63% | 18.86% | 19.98% | 20.62% | 20.55% | 18.63% | 19.98% | 20.62% |
| D&A (opex) % of revenue | 2.21% | 2.19% | 2.25% | 2.37% | 2.50% | 2.19% | 2.25% | 2.50% |
| D&A (CFO addback) % of revenue | 2.49% | 2.47% | 2.61% | 2.80% | 2.99% | 2.47% | 2.61% | 2.99% |
| Effective tax rate % | 22.02% | 18.67% | 21.88% | 22.24% | 22.28% | 18.67% | 22.02% | 22.28% |
| CapEx % of revenue | 3.34% | 5.07% | 4.47% | 2.71% | 3.56% | 2.71% | 3.56% | 5.07% |
| Inventory % of revenue | 13.11% | 12.37% | 11.07% | 11.96% | 11.74% | 11.07% | 11.96% | 13.11% |
| AP % of COGS | 20.65% | 16.39% | 15.54% | 17.06% | 16.72% | 15.54% | 16.72% | 20.65% |
| Cash % of revenue | 5.58% | 2.04% | 3.54% | 4.47% | 5.24% | 2.04% | 4.47% | 5.58% |

| Growth metric | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---|---|---|---|
| Revenue growth % | +2.94% | -1.57% | -0.79% | -1.68% |
| Net income growth % | -59.98% | +48.85% | -1.14% | -9.44% |
| Diluted share count change % | -5.68% | -0.41% | -0.22% | -1.34% |

FY2023 was a 53-week fiscal year (Target's own disclosure). 52-week-normalized FY2023 revenue: **$105,385.4M** (vs. reported $107,412.0M) -- implies FY2024-vs-FY2023 like-for-like growth of **+1.12%**, materially different from the raw reported figure (-0.79%), and is the figure BASE's revenue growth assumption is anchored to.

## 5. Complete Assumption Dictionary

105 assumption rows (35 average per scenario -- driver-year granularity varies by metric). Full table:

| Assumption ID | Scenario | FY | Metric | Value | Unit | Rationale | Historical Reference |
|---|---|---|---|---|---|---|---|
| `asm_ap_pct_base` | base | all | ap_pct_of_cogs | 16.7 | percent | Holds near the FY2025 actual (16.72%), within the 5-year range. | 5yr range: 15.54%-20.65%, FY2025=16.72% |
| `asm_ap_pct_downside` | downside | all | ap_pct_of_cogs | 15.5 | percent | Suppliers tighten terms under pressure, near the 5-year historical minimum (15.54%, FY2023) -- working-capital consumption. | 5yr range: 15.54%-20.65%, FY2025=16.72% |
| `asm_ap_pct_upside` | upside | all | ap_pct_of_cogs | 17.5 | percent | Extended payables terms / improved cash conversion, near the 5-year historical maximum (20.65%, FY2021) but conservatively below it. | 5yr range: 15.54%-20.65%, FY2025=16.72% |
| `asm_buyback_payout_base` | base | all | buyback_payout_pct_of_post_dividend_fcf | 40.0 | percent | A pre-set target payout ratio of (FCF - dividends), applied identically regardless of the resulting cash balance -- an input assumption, never solved backward to hit a cash or deployable-capacity target (the explicit 'not an automatic balancing plug' requirement). Historical repurchases range from $0 to $7,188M with no fixed dollar pattern, making a payout-ratio policy more defensible than a flat dollar figure. | 5yr share_repurchases: $7,188M, $2,646M, $0M, $1,007M, $408M -- no fixed pattern |
| `asm_buyback_payout_downside` | downside | all | buyback_payout_pct_of_post_dividend_fcf | 0.0 | percent | No repurchases -- capital preservation under pressure. | 5yr share_repurchases: $7,188M, $2,646M, $0M, $1,007M, $408M -- no fixed pattern |
| `asm_buyback_payout_upside` | upside | all | buyback_payout_pct_of_post_dividend_fcf | 55.0 | percent | A higher target payout ratio, reflecting stronger FCF generation and capital return capacity in this scenario. | 5yr share_repurchases: $7,188M, $2,646M, $0M, $1,007M, $408M -- no fixed pattern |
| `asm_capex_pct_base` | base | all | capex_pct_of_revenue | 3.6 | percent | Near the FY2025 actual (3.56%) and the 5-year median (3.56%) -- maintenance-plus-modest-growth continuation, using PaymentsToAcquirePropertyPlantAndEquipment, never total investing cash flow. | 5yr range: 2.71%-5.07%, median 3.56%, FY2025=3.56% |
| `asm_capex_pct_downside` | downside | all | capex_pct_of_revenue | 2.8 | percent | Capital discipline / deferred growth investment under pressure, near the 5-year historical minimum (2.71%, FY2024) -- Target does not disclose a maintenance-only CapEx figure, so this is not claimed as 'maintenance CapEx', only as a low-end plausible total CapEx level. | 5yr range: 2.71%-5.07%, min 2.71% (FY2024) |
| `asm_capex_pct_upside` | upside | all | capex_pct_of_revenue | 4.3 | percent | Elevated growth CapEx (new stores/supply chain/digital investment supporting the stronger revenue growth in this scenario) -- higher CapEx in the upside case is economically appropriate here (item 12), staying below the 5-year historical maximum (5.07%, FY2022). | 5yr range: 2.71%-5.07% |
| `asm_da_addback_pct_base_2026` | base | 2026 | da_cfo_addback_pct_of_revenue | 3.116 | percent | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | 5yr CFO-addback D&A % of revenue: 2.49%-2.99%, rising each year |
| `asm_da_addback_pct_base_2027` | base | 2027 | da_cfo_addback_pct_of_revenue | 3.24 | percent | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | 5yr CFO-addback D&A % of revenue: 2.49%-2.99%, rising each year |
| `asm_da_addback_pct_base_2028` | base | 2028 | da_cfo_addback_pct_of_revenue | 3.365 | percent | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | 5yr CFO-addback D&A % of revenue: 2.49%-2.99%, rising each year |
| `asm_da_addback_pct_base_2029` | base | 2029 | da_cfo_addback_pct_of_revenue | 3.49 | percent | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | 5yr CFO-addback D&A % of revenue: 2.49%-2.99%, rising each year |
| `asm_da_addback_pct_base_2030` | base | 2030 | da_cfo_addback_pct_of_revenue | 3.614 | percent | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | 5yr CFO-addback D&A % of revenue: 2.49%-2.99%, rising each year |
| `asm_da_addback_pct_downside_2026` | downside | 2026 | da_cfo_addback_pct_of_revenue | 3.066 | percent | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | 5yr CFO-addback D&A % of revenue: 2.49%-2.99%, rising each year |
| `asm_da_addback_pct_downside_2027` | downside | 2027 | da_cfo_addback_pct_of_revenue | 3.19 | percent | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | 5yr CFO-addback D&A % of revenue: 2.49%-2.99%, rising each year |
| `asm_da_addback_pct_downside_2028` | downside | 2028 | da_cfo_addback_pct_of_revenue | 3.315 | percent | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | 5yr CFO-addback D&A % of revenue: 2.49%-2.99%, rising each year |
| `asm_da_addback_pct_downside_2029` | downside | 2029 | da_cfo_addback_pct_of_revenue | 3.44 | percent | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | 5yr CFO-addback D&A % of revenue: 2.49%-2.99%, rising each year |
| `asm_da_addback_pct_downside_2030` | downside | 2030 | da_cfo_addback_pct_of_revenue | 3.564 | percent | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | 5yr CFO-addback D&A % of revenue: 2.49%-2.99%, rising each year |
| `asm_da_addback_pct_upside_2026` | upside | 2026 | da_cfo_addback_pct_of_revenue | 3.166 | percent | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | 5yr CFO-addback D&A % of revenue: 2.49%-2.99%, rising each year |
| `asm_da_addback_pct_upside_2027` | upside | 2027 | da_cfo_addback_pct_of_revenue | 3.29 | percent | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | 5yr CFO-addback D&A % of revenue: 2.49%-2.99%, rising each year |
| `asm_da_addback_pct_upside_2028` | upside | 2028 | da_cfo_addback_pct_of_revenue | 3.415 | percent | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | 5yr CFO-addback D&A % of revenue: 2.49%-2.99%, rising each year |
| `asm_da_addback_pct_upside_2029` | upside | 2029 | da_cfo_addback_pct_of_revenue | 3.54 | percent | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | 5yr CFO-addback D&A % of revenue: 2.49%-2.99%, rising each year |
| `asm_da_addback_pct_upside_2030` | upside | 2030 | da_cfo_addback_pct_of_revenue | 3.664 | percent | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | 5yr CFO-addback D&A % of revenue: 2.49%-2.99%, rising each year |
| `asm_da_pct_base_2026` | base | 2026 | da_pct_of_revenue | 2.578 | percent | Extrapolates the FY2021-FY2025 average annual increase (~0.078pp/yr) in D&A as a percent of revenue, reflecting continued store/technology investment amortizing -- a documented persistence of an already-observed trend, not a new assumption. | 5yr D&A % of revenue range: 2.19%-2.50%, rising each year |
| `asm_da_pct_base_2027` | base | 2027 | da_pct_of_revenue | 2.655 | percent | Extrapolates the FY2021-FY2025 average annual increase (~0.078pp/yr) in D&A as a percent of revenue, reflecting continued store/technology investment amortizing -- a documented persistence of an already-observed trend, not a new assumption. | 5yr D&A % of revenue range: 2.19%-2.50%, rising each year |
| `asm_da_pct_base_2028` | base | 2028 | da_pct_of_revenue | 2.732 | percent | Extrapolates the FY2021-FY2025 average annual increase (~0.078pp/yr) in D&A as a percent of revenue, reflecting continued store/technology investment amortizing -- a documented persistence of an already-observed trend, not a new assumption. | 5yr D&A % of revenue range: 2.19%-2.50%, rising each year |
| `asm_da_pct_base_2029` | base | 2029 | da_pct_of_revenue | 2.81 | percent | Extrapolates the FY2021-FY2025 average annual increase (~0.078pp/yr) in D&A as a percent of revenue, reflecting continued store/technology investment amortizing -- a documented persistence of an already-observed trend, not a new assumption. | 5yr D&A % of revenue range: 2.19%-2.50%, rising each year |
| `asm_da_pct_base_2030` | base | 2030 | da_pct_of_revenue | 2.888 | percent | Extrapolates the FY2021-FY2025 average annual increase (~0.078pp/yr) in D&A as a percent of revenue, reflecting continued store/technology investment amortizing -- a documented persistence of an already-observed trend, not a new assumption. | 5yr D&A % of revenue range: 2.19%-2.50%, rising each year |
| `asm_da_pct_downside_2026` | downside | 2026 | da_pct_of_revenue | 2.478 | percent | Same trend less -0.10pp, consistent with the downside scenario's reduced CapEx intensity -- D&A is sticky (prior capex keeps depreciating), so only a small offset is applied, not a reversal of the trend. | 5yr D&A % of revenue range: 2.19%-2.50%, rising each year |
| `asm_da_pct_downside_2027` | downside | 2027 | da_pct_of_revenue | 2.555 | percent | Same trend less -0.10pp, consistent with the downside scenario's reduced CapEx intensity -- D&A is sticky (prior capex keeps depreciating), so only a small offset is applied, not a reversal of the trend. | 5yr D&A % of revenue range: 2.19%-2.50%, rising each year |
| `asm_da_pct_downside_2028` | downside | 2028 | da_pct_of_revenue | 2.632 | percent | Same trend less -0.10pp, consistent with the downside scenario's reduced CapEx intensity -- D&A is sticky (prior capex keeps depreciating), so only a small offset is applied, not a reversal of the trend. | 5yr D&A % of revenue range: 2.19%-2.50%, rising each year |
| `asm_da_pct_downside_2029` | downside | 2029 | da_pct_of_revenue | 2.71 | percent | Same trend less -0.10pp, consistent with the downside scenario's reduced CapEx intensity -- D&A is sticky (prior capex keeps depreciating), so only a small offset is applied, not a reversal of the trend. | 5yr D&A % of revenue range: 2.19%-2.50%, rising each year |
| `asm_da_pct_downside_2030` | downside | 2030 | da_pct_of_revenue | 2.788 | percent | Same trend less -0.10pp, consistent with the downside scenario's reduced CapEx intensity -- D&A is sticky (prior capex keeps depreciating), so only a small offset is applied, not a reversal of the trend. | 5yr D&A % of revenue range: 2.19%-2.50%, rising each year |
| `asm_da_pct_upside_2026` | upside | 2026 | da_pct_of_revenue | 2.678 | percent | Same trend plus +0.10pp, consistent with the upside scenario's higher CapEx intensity (more assets in service depreciate more). | 5yr D&A % of revenue range: 2.19%-2.50%, rising each year |
| `asm_da_pct_upside_2027` | upside | 2027 | da_pct_of_revenue | 2.755 | percent | Same trend plus +0.10pp, consistent with the upside scenario's higher CapEx intensity (more assets in service depreciate more). | 5yr D&A % of revenue range: 2.19%-2.50%, rising each year |
| `asm_da_pct_upside_2028` | upside | 2028 | da_pct_of_revenue | 2.833 | percent | Same trend plus +0.10pp, consistent with the upside scenario's higher CapEx intensity (more assets in service depreciate more). | 5yr D&A % of revenue range: 2.19%-2.50%, rising each year |
| `asm_da_pct_upside_2029` | upside | 2029 | da_pct_of_revenue | 2.91 | percent | Same trend plus +0.10pp, consistent with the upside scenario's higher CapEx intensity (more assets in service depreciate more). | 5yr D&A % of revenue range: 2.19%-2.50%, rising each year |
| `asm_da_pct_upside_2030` | upside | 2030 | da_pct_of_revenue | 2.988 | percent | Same trend plus +0.10pp, consistent with the upside scenario's higher CapEx intensity (more assets in service depreciate more). | 5yr D&A % of revenue range: 2.19%-2.50%, rising each year |
| `asm_debt_proceeds_base` | base | all | debt_proceeds_musd | 700.0 | USD_millions | Fixed at a modest, pre-set rolling-refinancing level (proceeds roughly offsetting repayments) -- not derived from, or sized to, the resulting cash balance. | 5yr debt_proceeds: $1,972M, $2,625M, $0M, $741M, $1,984M |
| `asm_debt_proceeds_downside` | downside | all | debt_proceeds_musd | 500.0 | USD_millions | A small, FIXED, pre-committed net issuance assumption. This is deliberately NOT sized to whatever cash shortfall the downside scenario produces -- see the 'minimum_cash_compliance' validation check, which raises an explicit funding warning if ending cash still falls below the minimum buffer after this fixed amount, rather than silently increasing debt further to force compliance. | 5yr debt_proceeds: $1,972M, $2,625M, $0M, $741M, $1,984M |
| `asm_debt_proceeds_upside` | upside | all | debt_proceeds_musd | 300.0 | USD_millions | Fixed net repayment, funded by stronger scenario FCF -- a deleveraging policy choice, not a residual plug. | 5yr debt_proceeds: $1,972M, $2,625M, $0M, $741M, $1,984M |
| `asm_debt_repayments_base` | base | all | debt_repayments_musd | 700.0 | USD_millions | Fixed at a modest, pre-set rolling-refinancing level (proceeds roughly offsetting repayments) -- not derived from, or sized to, the resulting cash balance. | 5yr debt_repayments: $1,147M, $163M, $147M, $1,139M, $1,643M |
| `asm_debt_repayments_downside` | downside | all | debt_repayments_musd | 300.0 | USD_millions | A small, FIXED, pre-committed net issuance assumption. This is deliberately NOT sized to whatever cash shortfall the downside scenario produces -- see the 'minimum_cash_compliance' validation check, which raises an explicit funding warning if ending cash still falls below the minimum buffer after this fixed amount, rather than silently increasing debt further to force compliance. | 5yr debt_repayments: $1,147M, $163M, $147M, $1,139M, $1,643M |
| `asm_debt_repayments_upside` | upside | all | debt_repayments_musd | 1000.0 | USD_millions | Fixed net repayment, funded by stronger scenario FCF -- a deleveraging policy choice, not a residual plug. | 5yr debt_repayments: $1,147M, $163M, $147M, $1,139M, $1,643M |
| `asm_share_chg_base` | base | all | diluted_share_change_pct | -0.5 | percent | Continued modest buyback-driven reduction, below the 5-year average magnitude given lower recent FCF than the FY2021/FY2022 aggressive-repurchase years. | 5yr YoY share change: -5.68%, -0.41%, -0.22%, -1.34% |
| `asm_share_chg_downside` | downside | all | diluted_share_change_pct | 0.0 | percent | No net buybacks assumed; share count held flat -- capital preservation under pressure. | N/A -- a policy choice, not a historical figure |
| `asm_share_chg_upside` | upside | all | diluted_share_change_pct | -1.5 | percent | More aggressive buyback-driven reduction, funded by stronger scenario FCF -- within the historical range observed in FY2022-FY2025 (excluding the FY2022 outlier year), not the unrepeated -5.68% pandemic-era pace. | 5yr YoY share change range (ex-FY2022): -1.34% to -0.22% |
| `asm_dividend_growth_base` | base | all | dividend_per_share_growth_pct | 2.0 | percent | Continues the recent (FY2024-FY2025) decelerated per-share dividend growth pace of ~1.8%/yr, rounded up modestly. | Implied $/share (dividends_paid/diluted_shares) YoY growth: +25.8%, +10.1%, +1.8%, +1.8% |
| `asm_dividend_growth_downside` | downside | all | dividend_per_share_growth_pct | 0.0 | percent | Dividend frozen (0% growth), not cut -- Target's dividends_paid has grown in every one of the 5 historical years in this dataset with no observed cut, so an outright reduction is not modeled as a plausible base case for the downside scenario; freezing (not increasing) is the appropriate downside floor. | Implied $/share (dividends_paid/diluted_shares) YoY growth: +25.8%, +10.1%, +1.8%, +1.8% |
| `asm_dividend_growth_upside` | upside | all | dividend_per_share_growth_pct | 4.0 | percent | Stronger payout growth supported by better earnings, still well below the earlier, one-time large hikes (+25.8% FY2022, +10.1% FY2023) which followed unusually high FY2021 earnings, not treated as repeatable. | Implied $/share (dividends_paid/diluted_shares) YoY growth: +25.8%, +10.1%, +1.8%, +1.8% |
| `asm_tax_rate_base` | base | all | effective_tax_rate_pct | 22.2 | percent | Average of the 3 most recent years excluding the FY2022 outlier (18.67%, a one-time benefit not treated as representative): (21.88+22.24+22.28)/3 = 22.13%, rounded. | 5yr range 18.67%-22.28% (FY2022 excluded as non-representative); recent 3yr avg 22.13% |
| `asm_tax_rate_downside` | downside | all | effective_tax_rate_pct | 23.0 | percent | Modestly unfavorable rate, slightly above the representative historical maximum. | Representative range (ex-FY2022): 21.88%-22.28% |
| `asm_tax_rate_upside` | upside | all | effective_tax_rate_pct | 21.5 | percent | Modestly favorable rate near the low end of the representative (non-FY2022) historical range. | Representative range (ex-FY2022): 21.88%-22.28% |
| `asm_finance_lease_flat_base` | base | all | finance_lease_liabilities_musd | 2113.0 | USD_millions | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | 5yr range: $2,013M-$2,161M, essentially flat |
| `asm_finance_lease_flat_downside` | downside | all | finance_lease_liabilities_musd | 2113.0 | USD_millions | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | 5yr range: $2,013M-$2,161M, essentially flat |
| `asm_finance_lease_flat_upside` | upside | all | finance_lease_liabilities_musd | 2113.0 | USD_millions | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | 5yr range: $2,013M-$2,161M, essentially flat |
| `asm_gross_margin_base_2026` | base | 2026 | gross_margin_pct | 27.93 | percent | Holds near the FY2023-FY2025 recent average (~27.9-28.2%) -- explicitly NOT reverting to the FY2021 peak of 29.28%, which followed a pandemic-driven demand/mix shift item 3 requires treating as non-repeatable. | 5yr gross margin range: 24.57%-29.28%, median 27.93% |
| `asm_gross_margin_base_2027` | base | 2027 | gross_margin_pct | 27.947 | percent | Holds near the FY2023-FY2025 recent average (~27.9-28.2%) -- explicitly NOT reverting to the FY2021 peak of 29.28%, which followed a pandemic-driven demand/mix shift item 3 requires treating as non-repeatable. | 5yr gross margin range: 24.57%-29.28%, median 27.93% |
| `asm_gross_margin_base_2028` | base | 2028 | gross_margin_pct | 27.965 | percent | Holds near the FY2023-FY2025 recent average (~27.9-28.2%) -- explicitly NOT reverting to the FY2021 peak of 29.28%, which followed a pandemic-driven demand/mix shift item 3 requires treating as non-repeatable. | 5yr gross margin range: 24.57%-29.28%, median 27.93% |
| `asm_gross_margin_base_2029` | base | 2029 | gross_margin_pct | 27.983 | percent | Holds near the FY2023-FY2025 recent average (~27.9-28.2%) -- explicitly NOT reverting to the FY2021 peak of 29.28%, which followed a pandemic-driven demand/mix shift item 3 requires treating as non-repeatable. | 5yr gross margin range: 24.57%-29.28%, median 27.93% |
| `asm_gross_margin_base_2030` | base | 2030 | gross_margin_pct | 28.0 | percent | Holds near the FY2023-FY2025 recent average (~27.9-28.2%) -- explicitly NOT reverting to the FY2021 peak of 29.28%, which followed a pandemic-driven demand/mix shift item 3 requires treating as non-repeatable. | 5yr gross margin range: 24.57%-29.28%, median 27.93% |
| `asm_gross_margin_downside_2026` | downside | 2026 | gross_margin_pct | 27.93 | percent | Gradual, partial reversion toward (not matching) the FY2022 trough of 24.57% -- a moderate margin-pressure case, bounded well short of the full historical worst year. | 5yr gross margin range: 24.57%-29.28%, median 27.93% |
| `asm_gross_margin_downside_2027` | downside | 2027 | gross_margin_pct | 27.523 | percent | Gradual, partial reversion toward (not matching) the FY2022 trough of 24.57% -- a moderate margin-pressure case, bounded well short of the full historical worst year. | 5yr gross margin range: 24.57%-29.28%, median 27.93% |
| `asm_gross_margin_downside_2028` | downside | 2028 | gross_margin_pct | 27.115 | percent | Gradual, partial reversion toward (not matching) the FY2022 trough of 24.57% -- a moderate margin-pressure case, bounded well short of the full historical worst year. | 5yr gross margin range: 24.57%-29.28%, median 27.93% |
| `asm_gross_margin_downside_2029` | downside | 2029 | gross_margin_pct | 26.707 | percent | Gradual, partial reversion toward (not matching) the FY2022 trough of 24.57% -- a moderate margin-pressure case, bounded well short of the full historical worst year. | 5yr gross margin range: 24.57%-29.28%, median 27.93% |
| `asm_gross_margin_downside_2030` | downside | 2030 | gross_margin_pct | 26.3 | percent | Gradual, partial reversion toward (not matching) the FY2022 trough of 24.57% -- a moderate margin-pressure case, bounded well short of the full historical worst year. | 5yr gross margin range: 24.57%-29.28%, median 27.93% |
| `asm_gross_margin_upside_2026` | upside | 2026 | gross_margin_pct | 27.93 | percent | Gradual improvement toward, but never exceeding, the 5-year historical maximum (29.28%, FY2021) -- plausible supply-chain/mix execution, bounded by Target's own observed range. | 5yr gross margin range: 24.57%-29.28%, median 27.93% |
| `asm_gross_margin_upside_2027` | upside | 2027 | gross_margin_pct | 28.148 | percent | Gradual improvement toward, but never exceeding, the 5-year historical maximum (29.28%, FY2021) -- plausible supply-chain/mix execution, bounded by Target's own observed range. | 5yr gross margin range: 24.57%-29.28%, median 27.93% |
| `asm_gross_margin_upside_2028` | upside | 2028 | gross_margin_pct | 28.365 | percent | Gradual improvement toward, but never exceeding, the 5-year historical maximum (29.28%, FY2021) -- plausible supply-chain/mix execution, bounded by Target's own observed range. | 5yr gross margin range: 24.57%-29.28%, median 27.93% |
| `asm_gross_margin_upside_2029` | upside | 2029 | gross_margin_pct | 28.582 | percent | Gradual improvement toward, but never exceeding, the 5-year historical maximum (29.28%, FY2021) -- plausible supply-chain/mix execution, bounded by Target's own observed range. | 5yr gross margin range: 24.57%-29.28%, median 27.93% |
| `asm_gross_margin_upside_2030` | upside | 2030 | gross_margin_pct | 28.8 | percent | Gradual improvement toward, but never exceeding, the 5-year historical maximum (29.28%, FY2021) -- plausible supply-chain/mix execution, bounded by Target's own observed range. | 5yr gross margin range: 24.57%-29.28%, median 27.93% |
| `asm_interest_rate_base` | base | all | interest_rate_pct | 3.1 | percent | Matches the recent (FY2024-FY2025) implied rate on average total_debt_gaap. | 5yr implied rate (interest_expense / total_debt_gaap): 2.98%-3.62%, recent 2 yrs ~3.0-3.1% |
| `asm_interest_rate_downside` | downside | all | interest_rate_pct | 3.4 | percent | Higher borrowing cost, near the historical maximum, reflecting greater reliance on debt funding under pressure. | 5yr implied rate range: 2.98%-3.62% |
| `asm_interest_rate_upside` | upside | all | interest_rate_pct | 2.9 | percent | Slightly favorable borrowing cost / lower incremental debt need, within the historical range. | 5yr implied rate range: 2.98%-3.62% |
| `asm_inventory_pct_base` | base | all | inventory_pct_of_revenue | 11.8 | percent | Holds near the FY2025 actual (11.74%), within the 5-year range. | 5yr range: 11.07%-13.11%, FY2025=11.74% |
| `asm_inventory_pct_downside` | downside | all | inventory_pct_of_revenue | 12.8 | percent | Inventory buildup / slower turns under demand pressure, near the 5-year historical maximum (13.11%, FY2021) -- working-capital consumption, per item 3's downside theme. | 5yr range: 11.07%-13.11%, FY2025=11.74% |
| `asm_inventory_pct_upside` | upside | all | inventory_pct_of_revenue | 11.0 | percent | Improved inventory efficiency/turns, near the 5-year historical minimum (11.07%, FY2023). | 5yr range: 11.07%-13.11%, FY2025=11.74% |
| `asm_min_cash_buffer_pct_base` | base | all | min_cash_buffer_pct_of_revenue | 3.0 | percent | Recommended policy (see docs/milestone_3_forecast_engine_proposal.md Section 11 for the 4-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%), providing headroom without assuming the business needs FY2021-level cash intensity. | 5yr cash % of revenue: 2.04%, 5.58%, 3.54%, 4.47%, 5.24% |
| `asm_min_cash_buffer_pct_downside` | downside | all | min_cash_buffer_pct_of_revenue | 3.0 | percent | Recommended policy (see docs/milestone_3_forecast_engine_proposal.md Section 11 for the 4-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%), providing headroom without assuming the business needs FY2021-level cash intensity. | 5yr cash % of revenue: 2.04%, 5.58%, 3.54%, 4.47%, 5.24% |
| `asm_min_cash_buffer_pct_upside` | upside | all | min_cash_buffer_pct_of_revenue | 3.0 | percent | Recommended policy (see docs/milestone_3_forecast_engine_proposal.md Section 11 for the 4-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%), providing headroom without assuming the business needs FY2021-level cash intensity. | 5yr cash % of revenue: 2.04%, 5.58%, 3.54%, 4.47%, 5.24% |
| `asm_other_income_base` | base | all | net_other_income_musd | 95.0 | USD_millions | Flat at the FY2025 actual level -- this line is historically small and volatile ($48M-$382M) with no clear trend; holding flat avoids fabricating a directional assumption without evidence. | 5yr range: $48M-$382M, FY2025=$95M |
| `asm_other_income_downside` | downside | all | net_other_income_musd | 80.0 | USD_millions | Near-flat, marginally unfavorable -- within the historical range. | 5yr range: $48M-$382M |
| `asm_other_income_upside` | upside | all | net_other_income_musd | 100.0 | USD_millions | Near-flat, marginally favorable -- within the historical range, no fabricated upside swing. | 5yr range: $48M-$382M |
| `asm_other_opcf_base` | base | all | other_operating_cf_musd | 150.0 | USD_millions | Near the historical median of the derived 'other operating cash adjustments' residual (stock-based comp, deferred taxes, other non-cash items, other working capital not separately modeled) -- see docs/milestone_3_forecast_engine_proposal.md Section 7 for the full derivation and component discussion. This is NOT solved backward to hit a CFO target. | FY2022-FY2025 derived residual: -$282M, +$126M, +$194M, +$1,458M; median ~$160M |
| `asm_other_opcf_downside` | downside | all | other_operating_cf_musd | 50.0 | USD_millions | Less favorable working-capital/other items, within the observed historical range. | FY2022-FY2025 derived residual range: -$282M to +$1,458M |
| `asm_other_opcf_upside` | upside | all | other_operating_cf_musd | 250.0 | USD_millions | More favorable working-capital/other items, within the observed historical range. | FY2022-FY2025 derived residual range: -$282M to +$1,458M |
| `asm_rev_growth_base` | base | all | revenue_growth_pct | 1.0 | percent | Below FY2022's post-pandemic snap-back (+2.94%) and above the FY2023-FY2025 raw-decline trend; matches the FY2024-vs-FY2023(52-week-normalized) growth of +1.12%, treated as the cleanest recent read once the FY2023 53-week distortion is removed. Continuation of a stabilizing, low-single-digit trend -- explicitly NOT a return to the FY2021/FY2022 growth rates. | 5yr raw growth range: -1.68% to +2.94%; 52wk-normalized FY2024 growth: +1.12% |
| `asm_rev_growth_downside` | downside | all | revenue_growth_pct | -2.5 | percent | Beyond the single worst observed historical decline (-1.68%, FY2025) by roughly 1.5x, reflecting sustained discretionary-spending pressure -- a continued-deterioration case, not a fabricated crisis or extreme event. | 5yr raw growth min: -1.68% (FY2025) |
| `asm_rev_growth_upside` | upside | all | revenue_growth_pct | 3.0 | percent | At the high end of, without exceeding, the 5-year historical maximum (+2.94%, FY2022); reflects improved traffic/comp execution within the range Target has actually achieved, never an unprecedented acceleration. | 5yr raw growth max: +2.94% (FY2022) |
| `asm_sga_pct_base_2026` | base | 2026 | sga_pct_of_revenue | 20.55 | percent | Flat at the FY2025 actual level -- continuation, not reversion to the lower historical range (18.63%-19.98%) achieved only when revenue was growing. | 5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98% |
| `asm_sga_pct_base_2027` | base | 2027 | sga_pct_of_revenue | 20.55 | percent | Flat at the FY2025 actual level -- continuation, not reversion to the lower historical range (18.63%-19.98%) achieved only when revenue was growing. | 5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98% |
| `asm_sga_pct_base_2028` | base | 2028 | sga_pct_of_revenue | 20.55 | percent | Flat at the FY2025 actual level -- continuation, not reversion to the lower historical range (18.63%-19.98%) achieved only when revenue was growing. | 5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98% |
| `asm_sga_pct_base_2029` | base | 2029 | sga_pct_of_revenue | 20.55 | percent | Flat at the FY2025 actual level -- continuation, not reversion to the lower historical range (18.63%-19.98%) achieved only when revenue was growing. | 5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98% |
| `asm_sga_pct_base_2030` | base | 2030 | sga_pct_of_revenue | 20.55 | percent | Flat at the FY2025 actual level -- continuation, not reversion to the lower historical range (18.63%-19.98%) achieved only when revenue was growing. | 5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98% |
| `asm_sga_pct_downside_2026` | downside | 2026 | sga_pct_of_revenue | 20.55 | percent | Continued deleverage as revenue declines faster than fixed SG&A costs, moderately above the 5-year historical maximum (20.62%, FY2024). | 5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98% |
| `asm_sga_pct_downside_2027` | downside | 2027 | sga_pct_of_revenue | 20.738 | percent | Continued deleverage as revenue declines faster than fixed SG&A costs, moderately above the 5-year historical maximum (20.62%, FY2024). | 5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98% |
| `asm_sga_pct_downside_2028` | downside | 2028 | sga_pct_of_revenue | 20.925 | percent | Continued deleverage as revenue declines faster than fixed SG&A costs, moderately above the 5-year historical maximum (20.62%, FY2024). | 5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98% |
| `asm_sga_pct_downside_2029` | downside | 2029 | sga_pct_of_revenue | 21.113 | percent | Continued deleverage as revenue declines faster than fixed SG&A costs, moderately above the 5-year historical maximum (20.62%, FY2024). | 5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98% |
| `asm_sga_pct_downside_2030` | downside | 2030 | sga_pct_of_revenue | 21.3 | percent | Continued deleverage as revenue declines faster than fixed SG&A costs, moderately above the 5-year historical maximum (20.62%, FY2024). | 5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98% |
| `asm_sga_pct_upside_2026` | upside | 2026 | sga_pct_of_revenue | 20.55 | percent | Gradual improvement toward, but not below, the 5-year historical minimum (18.63%, FY2021) -- cost discipline/productivity, bounded by Target's own observed range. | 5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98% |
| `asm_sga_pct_upside_2027` | upside | 2027 | sga_pct_of_revenue | 20.363 | percent | Gradual improvement toward, but not below, the 5-year historical minimum (18.63%, FY2021) -- cost discipline/productivity, bounded by Target's own observed range. | 5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98% |
| `asm_sga_pct_upside_2028` | upside | 2028 | sga_pct_of_revenue | 20.175 | percent | Gradual improvement toward, but not below, the 5-year historical minimum (18.63%, FY2021) -- cost discipline/productivity, bounded by Target's own observed range. | 5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98% |
| `asm_sga_pct_upside_2029` | upside | 2029 | sga_pct_of_revenue | 19.988 | percent | Gradual improvement toward, but not below, the 5-year historical minimum (18.63%, FY2021) -- cost discipline/productivity, bounded by Target's own observed range. | 5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98% |
| `asm_sga_pct_upside_2030` | upside | 2030 | sga_pct_of_revenue | 19.8 | percent | Gradual improvement toward, but not below, the 5-year historical minimum (18.63%, FY2021) -- cost discipline/productivity, bounded by Target's own observed range. | 5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98% |

## 6. Base / Upside / Downside Headline Assumption Summary

| Driver | Base | Upside | Downside |
|---|---|---|---|
| Revenue growth %/yr | 1.00% | 3.00% | -2.50% |
| Gross margin % (FY2030) | 28.00% | 28.80% | 26.30% |
| SG&A % of revenue (FY2030) | 20.55% | 19.80% | 21.30% |
| Effective tax rate % | 22.20% | 21.50% | 23.00% |
| CapEx % of revenue | 3.60% | 4.30% | 2.80% |
| Buyback payout % of post-dividend FCF | 40.00% | 55.00% | 0.00% |
| Minimum cash buffer % of revenue | 3.00% | 3.00% | 3.00% |

## 7. FY2026-FY2030 Dry-Run Forecast (all scenarios)

### 7.1 Scenario: BASE

| FY | Revenue | Gross Margin % | Operating Income | Interest Exp | Pretax Income | Tax | Net Income | Diluted EPS |
|---|---|---|---|---|---|---|---|---|
| 2026 | 105,827.8 | 27.93% | 5,081.9 | 444.6 | 4,732.2 | 1,050.6 | 3,681.7 | 8.12 |
| 2027 | 106,886.1 | 27.95% | 5,068.5 | 444.6 | 4,718.9 | 1,047.6 | 3,671.3 | 8.14 |
| 2028 | 107,954.9 | 27.96% | 5,055.5 | 444.6 | 4,705.9 | 1,044.7 | 3,661.2 | 8.16 |
| 2029 | 109,034.5 | 27.98% | 5,040.7 | 444.6 | 4,691.0 | 1,041.4 | 3,649.6 | 8.17 |
| 2030 | 110,124.8 | 28.00% | 5,023.9 | 444.6 | 4,674.3 | 1,037.7 | 3,636.6 | 8.18 |

### 7.2 Scenario: UPSIDE

| FY | Revenue | Gross Margin % | Operating Income | Interest Exp | Pretax Income | Tax | Net Income | Diluted EPS |
|---|---|---|---|---|---|---|---|---|
| 2026 | 107,923.4 | 27.93% | 5,074.6 | 405.8 | 4,768.8 | 1,025.3 | 3,743.5 | 8.34 |
| 2027 | 111,161.1 | 28.15% | 5,591.4 | 385.5 | 5,305.9 | 1,140.8 | 4,165.1 | 9.42 |
| 2028 | 114,495.9 | 28.36% | 6,133.5 | 365.2 | 5,868.4 | 1,261.7 | 4,606.7 | 10.58 |
| 2029 | 117,930.8 | 28.58% | 6,703.2 | 344.9 | 6,458.3 | 1,388.5 | 5,069.8 | 11.82 |
| 2030 | 121,468.7 | 28.80% | 7,302.7 | 324.6 | 7,078.1 | 1,521.8 | 5,556.3 | 13.15 |

### 7.3 Scenario: DOWNSIDE

| FY | Revenue | Gross Margin % | Operating Income | Interest Exp | Pretax Income | Tax | Net Income | Diluted EPS |
|---|---|---|---|---|---|---|---|---|
| 2026 | 102,160.5 | 27.93% | 5,007.9 | 491.1 | 4,596.8 | 1,057.3 | 3,539.6 | 7.77 |
| 2027 | 99,606.5 | 27.52% | 4,213.4 | 497.9 | 3,795.5 | 873.0 | 2,922.5 | 6.41 |
| 2028 | 97,116.3 | 27.11% | 3,455.4 | 504.7 | 3,030.7 | 697.1 | 2,333.7 | 5.12 |
| 2029 | 94,688.4 | 26.71% | 2,730.8 | 511.5 | 2,299.4 | 528.9 | 1,770.5 | 3.89 |
| 2030 | 92,321.2 | 26.30% | 2,042.1 | 518.3 | 1,603.9 | 368.9 | 1,235.0 | 2.71 |

## 8. Cash-Flow Model and Cash Roll-Forward

### 8.1 Scenario: BASE

| FY | CFO | D&A Addback | Inv Cash Impact | AP Cash Impact | Other OpCF | CapEx | FCF | Div Paid | Buybacks | Debt Proceeds | Debt Repay | Financing CF | Beg Cash | Net Chg Cash | End Cash |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 7,060.7 | 3,297.6 | -183.7 | 115.1 | 150.0 | 3,809.8 | 3,250.9 | 2,083.6 | 466.9 | 700.0 | 700.0 | -2,550.5 | 5,488.0 | 700.4 | 6,188.4 |
| 2027 | 7,283.9 | 3,463.1 | -124.9 | 124.3 | 150.0 | 3,847.9 | 3,436.0 | 2,114.6 | 528.5 | 700.0 | 700.0 | -2,643.2 | 6,188.4 | 792.8 | 6,981.2 |
| 2028 | 7,443.1 | 3,632.7 | -126.1 | 125.4 | 150.0 | 3,886.4 | 3,556.7 | 2,146.1 | 564.2 | 700.0 | 700.0 | -2,710.4 | 6,981.2 | 846.4 | 7,827.5 |
| 2029 | 7,604.1 | 3,805.3 | -127.4 | 126.6 | 150.0 | 3,925.2 | 3,678.9 | 2,178.1 | 600.3 | 700.0 | 700.0 | -2,778.4 | 7,827.5 | 900.5 | 8,728.0 |
| 2030 | 7,765.8 | 3,979.9 | -128.7 | 128.0 | 150.0 | 3,964.5 | 3,801.3 | 2,210.6 | 636.3 | 700.0 | 700.0 | -2,846.9 | 8,728.0 | 954.5 | 9,682.5 |

### 8.2 Scenario: UPSIDE

| FY | CFO | D&A Addback | Inv Cash Impact | AP Cash Impact | Other OpCF | CapEx | FCF | Div Paid | Buybacks | Debt Proceeds | Debt Repay | Financing CF | Beg Cash | Net Chg Cash | End Cash |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 8,832.3 | 3,416.9 | 432.4 | 989.6 | 250.0 | 4,640.7 | 4,191.6 | 2,103.1 | 1,148.7 | 300.0 | 1,000.0 | -3,951.8 | 5,488.0 | 239.8 | 5,727.8 |
| 2027 | 8,082.1 | 3,657.2 | -356.1 | 365.9 | 250.0 | 4,779.9 | 3,302.2 | 2,154.4 | 631.3 | 300.0 | 1,000.0 | -3,485.7 | 5,727.8 | -183.5 | 5,544.3 |
| 2028 | 8,775.7 | 3,910.0 | -366.8 | 375.8 | 250.0 | 4,923.3 | 3,852.4 | 2,207.0 | 905.0 | 300.0 | 1,000.0 | -3,811.9 | 5,544.3 | 40.4 | 5,584.8 |
| 2029 | 9,502.5 | 4,174.8 | -377.8 | 385.8 | 250.0 | 5,071.0 | 4,431.5 | 2,260.8 | 1,193.9 | 300.0 | 1,000.0 | -4,154.7 | 5,584.8 | 276.8 | 5,861.6 |
| 2030 | 10,263.6 | 4,450.6 | -389.2 | 395.8 | 250.0 | 5,223.2 | 5,040.4 | 2,316.0 | 1,498.4 | 300.0 | 1,000.0 | -4,514.4 | 5,861.6 | 526.0 | 6,387.6 |

### 8.3 Scenario: DOWNSIDE

| FY | CFO | D&A Addback | Inv Cash Impact | AP Cash Impact | Other OpCF | CapEx | FCF | Div Paid | Buybacks | Debt Proceeds | Debt Repay | Financing CF | Beg Cash | Net Chg Cash | End Cash |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 4,739.5 | 3,132.2 | -772.5 | -1,209.8 | 50.0 | 2,860.5 | 1,879.0 | 2,053.0 | 0.0 | 500.0 | 300.0 | -1,853.0 | 5,488.0 | 26.0 | 5,514.0 |
| 2027 | 6,254.4 | 3,177.4 | 326.9 | -222.5 | 50.0 | 2,789.0 | 3,465.4 | 2,053.0 | 0.0 | 500.0 | 300.0 | -1,853.0 | 5,514.0 | 1,612.4 | 7,126.4 |
| 2028 | 5,703.5 | 3,219.4 | 318.7 | -218.3 | 50.0 | 2,719.3 | 2,984.2 | 2,053.0 | 0.0 | 500.0 | 300.0 | -1,853.0 | 7,126.4 | 1,131.2 | 8,257.6 |
| 2029 | 5,174.2 | 3,257.3 | 310.8 | -214.4 | 50.0 | 2,651.3 | 2,522.9 | 2,053.0 | 0.0 | 500.0 | 300.0 | -1,853.0 | 8,257.6 | 669.9 | 8,927.5 |
| 2030 | 4,667.6 | 3,290.3 | 303.0 | -210.7 | 50.0 | 2,585.0 | 2,082.6 | 2,053.0 | 0.0 | 500.0 | 300.0 | -1,853.0 | 8,927.5 | 229.6 | 9,157.2 |

**Limitation**: `investing_cash_flow` is modeled as exactly `-capital_expenditure` -- no disclosed driver exists for other historical investing items (e.g. investment purchases/maturities), so they are not separately forecast. This is never used to compute FCF (`FCF = CFO - CapEx` always, per item 6), only to complete the cash roll-forward. No FX translation effect is separately modeled; it is implicitly zero, reported here as an unmodeled item, never asserted as a historical fact.

## 9. Investment Capacity

`GROSS_FCF_CAPACITY = CFO - CapEx`. `POST_DIVIDEND_CAPACITY = FCF - dividends`. `PRE_DISCRETIONARY_ENDING_CASH = beginning cash + CFO + CFI + mandatory financing flows` (mandatory = dividends + the fixed debt schedule, excluding discretionary share repurchases). `DEPLOYABLE_CAPACITY = max(0, pre-discretionary ending cash - minimum cash buffer - near-term debt repayment reserve)`.

**These figures are not "actual cash available for acquisition."** They exclude: working-capital seasonality within the fiscal year (only year-end balances are modeled), credit-rating considerations that could require preserving additional headroom, operating-lease commitments (not part of any debt or cash measure here), and management's own discretion to redirect any of dividends, buybacks, or the debt schedule mid-year. The near-term debt repayment reserve is proxied by the current year's own fixed repayment assumption because no disclosed maturity ladder exists -- a simplification, not a real schedule.

### 9.1 Scenario: BASE

| FY | Gross FCF Capacity | Post-Dividend Capacity | Pre-Discretionary Ending Cash | Min Cash Buffer | Near-Term Debt Reserve | Deployable Capacity | Funding Warning |
|---|---|---|---|---|---|---|---|
| 2026 | 3,250.9 | 1,167.3 | 6,655.3 | 3,174.8 | 700.0 | 2,780.5 | no |
| 2027 | 3,436.0 | 1,321.3 | 7,509.7 | 3,206.6 | 700.0 | 3,603.1 | no |
| 2028 | 3,556.7 | 1,410.6 | 8,391.8 | 3,238.6 | 700.0 | 4,453.1 | no |
| 2029 | 3,678.9 | 1,500.8 | 9,328.3 | 3,271.0 | 700.0 | 5,357.3 | no |
| 2030 | 3,801.3 | 1,590.8 | 10,318.8 | 3,303.7 | 700.0 | 6,315.0 | no |

### 9.2 Scenario: UPSIDE

| FY | Gross FCF Capacity | Post-Dividend Capacity | Pre-Discretionary Ending Cash | Min Cash Buffer | Near-Term Debt Reserve | Deployable Capacity | Funding Warning |
|---|---|---|---|---|---|---|---|
| 2026 | 4,191.6 | 2,088.5 | 6,876.5 | 3,237.7 | 1,000.0 | 2,638.8 | no |
| 2027 | 3,302.2 | 1,147.8 | 6,175.6 | 3,334.8 | 1,000.0 | 1,840.8 | no |
| 2028 | 3,852.4 | 1,645.4 | 6,489.7 | 3,434.9 | 1,000.0 | 2,054.9 | no |
| 2029 | 4,431.5 | 2,170.6 | 7,055.4 | 3,537.9 | 1,000.0 | 2,517.5 | no |
| 2030 | 5,040.4 | 2,724.4 | 7,886.0 | 3,644.1 | 1,000.0 | 3,241.9 | no |

### 9.3 Scenario: DOWNSIDE

| FY | Gross FCF Capacity | Post-Dividend Capacity | Pre-Discretionary Ending Cash | Min Cash Buffer | Near-Term Debt Reserve | Deployable Capacity | Funding Warning |
|---|---|---|---|---|---|---|---|
| 2026 | 1,879.0 | -174.0 | 5,514.0 | 3,064.8 | 300.0 | 2,149.2 | no |
| 2027 | 3,465.4 | 1,412.4 | 7,126.4 | 2,988.2 | 300.0 | 3,838.2 | no |
| 2028 | 2,984.2 | 931.2 | 8,257.6 | 2,913.5 | 300.0 | 5,044.2 | no |
| 2029 | 2,522.9 | 469.9 | 8,927.5 | 2,840.7 | 300.0 | 5,786.9 | no |
| 2030 | 2,082.6 | 29.6 | 9,157.2 | 2,769.6 | 300.0 | 6,087.5 | no |

## 10. Minimum Cash Buffer Policy Comparison

| Policy | Description | FY2026 implied buffer (BASE revenue) | Assessment |
|---|---|---|---|
| Fixed-dollar historical minimum | Hold the lowest historical year-end cash balance ($2,229M, FY2022) flat in dollar terms | $2,229M | Does not scale with revenue growth or decline; becomes a shrinking % of the business over time in BASE/UPSIDE. |
| **% of revenue (recommended, 3.0%)** | Scale the buffer with forecast revenue | $3,175M | Sits above the historical minimum ratio (2.04%, FY2022) and below recent actuals (4.47%-5.24%) -- scales naturally, chosen policy. |
| % of operating expenditures | 3% of (COGS + SG&A) | $2,941M | Similar magnitude to the %-of-revenue policy here since COGS+SG&A is a large share of revenue; adds complexity without a materially different result at Target's cost structure. |
| Downside liquidity requirement | Set the buffer equal to the lowest ending cash the DOWNSIDE scenario itself reaches ($5,514M) | $5,514M | Circular for stress-testing the downside scenario against its own outcome; useful as a cross-check, not as the primary policy. |

**Recommendation: 3.0% of forecast revenue**, applied uniformly across all three scenarios (see Section 5's `min_cash_buffer_pct_of_revenue` assumption).

## 11. Sensitivity Tables (dry run; no valuation sensitivities)

Each table perturbs one BASE-scenario driver in isolation (holding all others fixed) and reports the FY2030 (terminal year) impact. No DCF/valuation sensitivity is included -- explicitly out of scope for this round.

### revenue_growth_pct

| Delta | CFO | FCF | Ending Cash | Deployable Capacity |
|---|---|---|---|---|
| -1.00 | 7,380.6 | 3,608.6 | 9,344.6 | 6,060.4 |
| -0.50 | 7,571.3 | 3,704.0 | 9,512.4 | 6,186.9 |
| +0.00 | 7,765.8 | 3,801.3 | 9,682.5 | 6,315.0 |
| +0.50 | 7,964.3 | 3,900.7 | 9,854.9 | 6,444.6 |
| +1.00 | 8,166.7 | 4,002.0 | 10,029.7 | 6,575.7 |

### gross_margin_pct

| Delta | CFO | FCF | Ending Cash | Deployable Capacity |
|---|---|---|---|---|
| -0.50 | 7,338.4 | 3,373.9 | 8,477.7 | 4,939.2 |
| -0.25 | 7,552.1 | 3,587.6 | 9,080.1 | 5,627.1 |
| +0.00 | 7,765.8 | 3,801.3 | 9,682.5 | 6,315.0 |
| +0.25 | 7,979.6 | 4,015.1 | 10,284.9 | 7,002.9 |
| +0.50 | 8,193.3 | 4,228.8 | 10,887.2 | 7,690.8 |

### sga_pct_of_revenue

| Delta | CFO | FCF | Ending Cash | Deployable Capacity |
|---|---|---|---|---|
| -0.50 | 8,194.2 | 4,229.7 | 10,942.4 | 7,746.3 |
| -0.25 | 7,980.0 | 4,015.5 | 10,312.4 | 7,030.7 |
| +0.00 | 7,765.8 | 3,801.3 | 9,682.5 | 6,315.0 |
| +0.25 | 7,551.6 | 3,587.1 | 9,052.5 | 5,599.4 |
| +0.50 | 7,337.4 | 3,373.0 | 8,422.5 | 4,883.7 |

### capex_pct_of_revenue

| Delta | CFO | FCF | Ending Cash | Deployable Capacity |
|---|---|---|---|---|
| -0.50 | 7,765.8 | 4,352.0 | 11,301.9 | 8,154.8 |
| -0.25 | 7,765.8 | 4,076.7 | 10,492.2 | 7,234.9 |
| +0.00 | 7,765.8 | 3,801.3 | 9,682.5 | 6,315.0 |
| +0.25 | 7,765.8 | 3,526.0 | 8,872.7 | 5,395.2 |
| +0.50 | 7,765.8 | 3,250.7 | 8,063.0 | 4,475.3 |

### inventory_pct_of_revenue

| Delta | CFO | FCF | Ending Cash | Deployable Capacity |
|---|---|---|---|---|
| -1.00 | 7,776.7 | 3,812.2 | 10,343.2 | 6,980.1 |
| -0.50 | 7,771.3 | 3,806.8 | 10,012.8 | 6,647.6 |
| +0.00 | 7,765.8 | 3,801.3 | 9,682.5 | 6,315.0 |
| +0.50 | 7,760.4 | 3,795.9 | 9,352.1 | 5,982.5 |
| +1.00 | 7,754.9 | 3,790.4 | 9,021.7 | 5,649.9 |

### min_cash_buffer_pct_of_revenue

| Delta | CFO | FCF | Ending Cash | Deployable Capacity |
|---|---|---|---|---|
| -1.00 | 7,765.8 | 3,801.3 | 9,682.5 | 7,416.3 |
| -0.50 | 7,765.8 | 3,801.3 | 9,682.5 | 6,865.6 |
| +0.00 | 7,765.8 | 3,801.3 | 9,682.5 | 6,315.0 |
| +0.50 | 7,765.8 | 3,801.3 | 9,682.5 | 5,764.4 |
| +1.00 | 7,765.8 | 3,801.3 | 9,682.5 | 5,213.8 |

## 12. Forecast Validation Plan and Results

18 named checks (item 12's list), executed live against the BASE/UPSIDE/DOWNSIDE dry-run above via `target_cash.forecast.validate_all()`. Total results: 208. Failures: 0. Warnings: 0.

| Check | Rows | PASS | FAIL | WARNING |
|---|---|---|---|---|
| assumption_completeness | 3 | 3 | 0 | 0 |
| cash_roll_forward | 15 | 15 | 0 | 0 |
| cfo_construction | 15 | 15 | 0 | 0 |
| debt_roll_forward | 15 | 15 | 0 | 0 |
| eps_consistency | 15 | 15 | 0 | 0 |
| fcf_calc | 15 | 15 | 0 | 0 |
| gross_profit_calc | 15 | 15 | 0 | 0 |
| information_cutoff_compliance | 1 | 1 | 0 | 0 |
| lineage_completeness | 3 | 3 | 0 | 0 |
| minimum_cash_compliance | 15 | 15 | 0 | 0 |
| no_finance_lease_double_counting | 15 | 15 | 0 | 0 |
| no_historical_forecast_mixing | 1 | 1 | 0 | 0 |
| operating_income_bridge | 15 | 15 | 0 | 0 |
| pretax_income_bridge | 15 | 15 | 0 | 0 |
| revenue_recursion | 15 | 15 | 0 | 0 |
| scenario_ordering | 5 | 5 | 0 | 0 |
| tax_net_income_bridge | 15 | 15 | 0 | 0 |
| working_capital_sign_checks | 15 | 15 | 0 | 0 |

All 18 checks pass with zero failures and zero warnings across the published Base/Upside/Downside assumption set (a broken-revenue-recursion / broken-CFO-construction / inverted-scenario-ordering regression test in `tests/unit/test_forecast.py` confirms each of the corresponding checks does fail when the underlying computation is corrupted, so a PASS here is not merely because the check is unreachable).

## 13. Limitations

- `depreciation_amortization_cfo_addback` (the full cash-flow-statement D&A addback) is sourced directly from `raw_facts` (not `annual_facts`, which Milestone 2 only approved at the opex-line grain) -- frozen as a literal in `HISTORICAL`, not re-queried live.
- `investing_cash_flow` is approximated as `-capital_expenditure`; no driver exists for other historical investing items.
- No FX translation effect is modeled (implicitly zero); Target's cash is overwhelmingly USD-denominated and no disclosed FX driver exists in the registered source set.
- The near-term debt repayment reserve used in `DEPLOYABLE_CAPACITY` is proxied by each year's own fixed repayment assumption -- Target discloses no year-by-year debt maturity ladder in the registered source set.
- "Other operating cash adjustments" is a single flat scenario assumption grounded in the FY2022-FY2025 derived residual (stock-based comp, deferred taxes, and other non-cash/working-capital items not separately modeled); it is not decomposed into its components.
- CapEx is modeled as a % of revenue; Target does not disclose a maintenance-vs-growth CapEx split, so no maintenance-only figure is claimed anywhere in this document.
- Dividends are modeled via a $/share growth proxy applied to forecast diluted shares, not from a disclosed per-share dividend policy statement.
- Lineage (`build_lineage()`) is representative, covering the major derived metrics (revenue through deployable_capacity) rather than every one of the 40+ fields on `ForecastYear` -- a future persistence round must extend it to full grain.

## 14. Expected Persistence Manifest (NOT executed this round)

If/when the schema in `docs/milestone_3_forecast_schema_proposal.md` is approved and implemented, persisting this exact dry-run would be expected to produce:

- `forecast_scenarios`: 3 rows.
- `forecast_assumptions`: 105 rows (as built by `build_assumptions()`).
- `forecast_facts`: up to 3 x 5 x 50 = 750 rows (one per scenario x fiscal year x `ForecastYear` field, excluding the `scenario`/`fiscal_year` key fields themselves and any boolean flags not modeled as a metric row).
- `forecast_lineage`: at least 150 rows at this round's representative grain (10 tracked metrics x 5 years x 3 scenarios); a full-grain implementation would produce substantially more.
- `forecast_validation_results`: 208 rows per validation run.
- `investment_capacity_results`: 15 rows (3 scenarios x 5 years).

**No such persistence has occurred.** `data/curated/target_cash.db` is unchanged by this round -- confirmed by the git diff (Section 16) touching no file under `data/`.

## 15. Tests

`tests/unit/test_forecast.py` (36 tests): assumption grounding (coverage, non-arbitrary spreads, bounded ranges, rationale/evidence presence, cutoff compliance), revenue recursion, operating-model bridges, EPS consistency, CapEx/CFO/FCF construction, working-capital sign checks, cash and debt roll-forwards, non-plug discipline for buybacks and debt, investment-capacity formula chain, validation-check correctness (including 3 regression tests that corrupt a computed value and confirm the relevant check actually fails), sensitivity-table monotonicity and driver coverage, and structural historical/forecast separation (HISTORICAL is never mutated by a run; fiscal years never overlap). Full suite: 298 tests pass (262 pre-existing + 36 new), 0 failures.

## 16. Git Diff Summary

New files this round (all additive, no existing file modified except this generator's own output and the schema-proposal cross-reference):

- `src/target_cash/forecast.py` -- the forecast engine (assumptions, revenue/operating/cash-flow model, investment capacity, validation, sensitivity). Pure in-memory, no DB writes.
- `tests/unit/test_forecast.py` -- 36 unit tests.
- `docs/milestone_3_forecast_schema_proposal.md` -- proposed (not implemented) DDL.
- `docs/milestone_3_forecast_engine_proposal.md` -- this document.
- `scripts/build_milestone_3_proposal.py` -- this document's generator.

No file under `src/target_cash/migrations.py`, `data/`, `config/metric_definitions.csv`, or any Milestone 1/2 module is touched.

---

**Stop for reviewer approval. Do not persist forecast facts. Do not begin DCF, Excel, Power BI, or website development until this proposal (schema + assumptions + engine + validation) is explicitly approved.**
