# Milestone 2 Proposal: Five-Year Historical Financial Model and Driver Architecture

**Status: DELIVERABLES FOR REVIEW. Nothing in this milestone has been persisted
as an analytical fact. No schema in this document has been implemented. No
mapping below is marked `reviewed`. No forecasting, DCF, Excel, Power BI, or
website work has begun.** This document is the complete Milestone 2
deliverable package per the governing instruction and stops for reviewer
approval before any further action.

Milestone 1 (repository setup and four-quarter data proof) is frozen at
commit `879ac2d` (phrasing corrected at `c9f11ed`) — see
`docs/milestone_1_evidence.md`.

## Table of contents

1. [Source coverage](#1-source-coverage)
2. [Financial definitions](#3-financial-definitions)
3. [Accounting consistency — 53-week fiscal year and comparability](#4-accounting-consistency)
4. [Five-year mapping matrix](#5-five-year-mapping-matrix)
5. [Annual historical dry-run table (FY2022-FY2025)](#2-annual-historical-dry-run-table)
6. [Driver dictionary](#7-driver-dictionary)
7. [Proposed historical analytical schema](#6-proposed-analytical-schema)
8. [Validation plan and dry-run results](#8-validation-plan)
9. [Unresolved mappings and accounting limitations](#unresolved-and-limitations)
10. [Tests executed](#tests-executed)
11. [Git diff summary](#git-diff-summary)

---

## 1. Source coverage

| Filing | Accession | Period of report | Status |
|---|---|---|---|
| FY2025 10-K | `0000027419-26-000016` | 2026-01-31 | Cached, verified (Milestone 1) |
| FY2024 10-K | `0000027419-25-000018` | 2025-02-01 | Cached, verified (Milestone 1) |
| FY2025 Q1/Q2/Q3 10-Qs | see `docs/sources.csv` | — | Cached, verified (Milestone 1) |
| **FY2022 10-K** | `0000027419-23-000015` | **2023-01-28** | **NOT PRESENT — requested below** |

### Request

**The FY2022 10-K is not available in this environment.** Per item 1's
instruction, only this one filing is requested — no broader source-vault
project is being opened:

> Accession `0000027419-23-000015`, primary document `tgt-20230128.htm`,
> period end `2023-01-28`, URL
> `https://www.sec.gov/Archives/edgar/data/27419/000002741923000015/tgt-20230128.htm`

Please download this document and upload it into this session (network
egress to `www.sec.gov` remains blocked here, per the environment limitation
already on file in `docs/limitations.md`). Once uploaded, it will be
hash-verified and registered in `docs/sources.csv` before any of its facts
are ingested, exactly as done for the FY2024 and FY2025 10-Ks.

### A second, previously-unstated source-authority gap

Obtaining the FY2022 10-K does **not** fully close the five-year window.
**No filing among current or planned holdings will ever have FY2023 as its
own primary period of report:**

- The FY2024 10-K's own period is FY2024; FY2023 appears there only as a
  comparative (one year back).
- The FY2025 10-K's own period is FY2025; FY2023 appears there only as a
  second comparative (two years back).
- The FY2022 10-K's own period is FY2022 (period end 2023-01-28); its
  comparative reaches back to FY2021, not forward to FY2023.

Under this project's authoritative-source-filing policy (a fact is
authoritative only when the filing's own period of report equals that fact's
period), **FY2023 will structurally remain a corroborating-only period** —
well-evidenced (it appears identically in two independent filings) but never
backed by a filing whose own primary statements are for FY2023. This is
reported as a standing limitation, not a request for a further filing, per
the explicit instruction not to broaden the source-vault project. It is
recorded in `docs/limitations.md` (see the update in this milestone's diff).

---

## 3. Financial definitions

These are fixed before any calculation below uses them, per item 3.

| Term | Definition | Notes |
|---|---|---|
| **Gross profit** | Revenue − Cost of sales | Always **derived** for Target — see §5, no direct XBRL tag exists. |
| **Free cash flow (FCF)** | Operating cash flow − Capital expenditures | **This is this project's own working definition, not a claim about Target's non-GAAP measures.** Target does not define or disclose a "free cash flow" figure identically to this in either cached 10-K (confirmed by tag scan — no `*FreeCashFlow*` concept exists in either filing). This project's FCF must never be presented as Target's official non-GAAP FCF measure. |
| **Net debt** | Interest-bearing debt (current + noncurrent long-term debt and capital/finance lease obligations) − Cash and cash equivalents (and any short-term investments included in the same balance-sheet line) | See §9 for the unresolved `LongTermDebt` vs. `LongTermDebtAndCapitalLeaseObligations` question that affects which "interest-bearing debt" figure is used. |
| **Cash conversion** | Operating cash flow / Net income | A ratio, not a percentage of revenue; values >1.0 mean CFO exceeds reported net income (common when D&A is large relative to working-capital drag). |
| **Operating cash conversion / working capital** | Standard indirect-method components: net income, D&A add-back, and changes in inventory/AP where mapped | See §8, item "CFO reconciliation" — currently **partial**, not a full indirect-method proof, because several CFO line items (stock compensation, deferred taxes, other non-cash items) are not yet mapped. |

**Explicit caveats carried forward from the governing instruction:**

- This project's FCF definition is never labeled as Target's own official
  non-GAAP measure unless Target defines it identically (it does not, per
  above).
- Financing cash flows (debt issuance, dividends, share repurchases) are
  never treated as a source of operating investment capacity. Investment
  capacity, once modeled in a later milestone, will be built from CFO and
  FCF only; CFF is presented purely as a historical use/source of cash for
  shareholder distributions and debt management, never folded into any
  "capacity" figure.

---

## 4. Accounting consistency — 53-week fiscal year and comparability

Target's own verbatim disclosure, found identically in both the FY2024 10-K
and FY2025 10-K:

> "2023 consisted of 53 weeks. The extra week in 2023 contributed $1.7
> billion of Net Sales."

Week-count table (cross-confirmed by both filings' own comparative tables —
FY2024 10-K: "2023 consisted of 53 weeks compared with 52 weeks in 2024 and
2022"; FY2025 10-K: "2023 consisted of 53 weeks compared with 52 weeks in
2025 and 2024"):

| Fiscal year | Weeks | Period |
|---|---|---|
| FY2022 | 52 | 2022-01-30 to 2023-01-28 |
| FY2023 | **53** | 2023-01-29 to 2024-02-03 |
| FY2024 | 52 | 2024-02-04 to 2025-02-01 |
| FY2025 | 52 | 2025-02-02 to 2026-01-31 |

**Both a reported growth figure and a week-count limitation note are carried
side by side wherever FY2023 is compared to an adjacent year** in the dry-run
table below (§5). **No 52-week-adjusted FY2023 figure is invented anywhere
in this project** — Target discloses the extra week's approximate revenue
contribution ($1.7B) but does not disclose a fully adjusted comparable
income statement, so no normalization is computed.

Other accounting-consistency items checked for every metric below (per item
4): authoritative filing selected where more than one candidate period
exists; corroborating comparatives retained, never discarded on agreement;
no restatement found between the two cached filings for any metric in
common years (FY2023 and FY2024 figures agree exactly between the FY2024 and
FY2025 10-Ks in every case checked); direct vs. derived status recorded per
metric (§5); no missing value replaced with zero anywhere (FY2022
balance-sheet items are reported as `BLOCKED`, not `0`).

---

## 5. Five-year mapping matrix

Legend: **Direct** = value taken from a single reported XBRL tag. **Derived**
= computed from other mapped metrics. `mapping_status` is never changed to
`reviewed` in this document — every row below stays `candidate_unverified`
in `config/metrics.csv` (two rows, `net_other_income` and the four cash-flow
totals, were already marked `reviewed` in Milestone 1 and are included here
only for completeness of the annual view).

| Metric | Statement | XBRL concept | Direct/Derived | Sign policy | Statement location | Competing tags considered | Missing years | Notes |
|---|---|---|---|---|---|---|---|---|
| `revenue` | IS | `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax` | Direct | `positive_magnitude_inflow` | Statement of Operations, "Sales" + "Other revenue" combined into "Total revenue" | Legacy `Revenues`/`SalesRevenueNet` not present in either filing (ASC 606 tag used throughout) | FY2021 (blocked) | Annual contexts confirmed exact across both filings for FY2023/FY2024 overlap. |
| `cost_of_sales` | IS | `us-gaap:CostOfGoodsAndServicesSold` | Direct | `positive_magnitude_expense` | Statement of Operations, "Cost of sales" | None found | FY2021 | — |
| `gross_profit` | IS | *(none — derived)* | **Derived** = revenue − cost_of_sales | `positive_magnitude_inflow` | Not a reported line | `us-gaap:GrossProfit`: **0 occurrences**, confirmed absent | FY2021 | See §3; no direct tag exists in either cached filing. |
| `operating_expenses` (SG&A) | IS | `us-gaap:SellingGeneralAndAdministrativeExpense` **(corrected this milestone)** | Direct | `positive_magnitude_expense` | Statement of Operations, "Selling, general and administrative expenses" | Original candidate `us-gaap:OperatingExpenses`: **0 occurrences**, confirmed absent | FY2021 | Tag correction applied to `config/metrics.csv` this milestone (candidate status unchanged). |
| `depreciation_amortization_opex` | IS | `us-gaap:DepreciationAndAmortization` | Direct | `positive_magnitude_expense` | Statement of Operations, "Depreciation and amortization (exclusive of depreciation included in cost of sales)" | — | FY2021 | Already `reviewed` (Milestone 1). Confirmed to also reproduce FY2022-FY2023 in the FY2024 10-K. |
| `operating_income` | IS | `us-gaap:OperatingIncomeLoss` | Direct (cross-checked as derived — see §8) | `positive_magnitude_inflow` | Statement of Operations, "Operating income" | — | FY2021 | Bridge check: gross_profit − operating_expenses − depreciation_amortization_opex reproduces this exactly, zero residual, FY2022-FY2025. |
| `interest_expense` | IS | `us-gaap:InterestExpenseNonoperating` | Direct | `positive_magnitude_expense` | Statement of Operations, "Net interest expense" | `FinanceLeaseInterestExpense` (narrower, rejected), `InterestPaidNet` (cash-paid, rejected) | FY2021 | Already corrected, not yet `reviewed` (Milestone 1 note carried forward). |
| `net_other_income` | IS | `us-gaap:OtherNonoperatingIncomeExpense` | Direct | `positive_magnitude_inflow` | Statement of Operations, "Net other income" | `RentalIncomeNonoperating` (rejected, narrower) | FY2021 | Already `reviewed` (Milestone 1). |
| `pretax_income` | IS | `us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | Direct (cross-checked as derived) | `signed_bidirectional` | Statement of Operations, "Earnings before income taxes" | Narrower `...Foreign` variant present but not competing (a note-level sub-total) | FY2021 | Bridge check: operating_income − interest_expense + net_other_income reproduces this exactly, zero residual, FY2022-FY2025. |
| `income_tax_expense` | IS | `us-gaap:IncomeTaxExpenseBenefit` | Direct | `positive_magnitude_expense` | Statement of Operations, "Provision for income taxes" | — | FY2021 | — |
| `net_income` | IS | `us-gaap:NetIncomeLoss` | Direct (cross-checked as derived) | `signed_bidirectional` | Statement of Operations, "Net earnings" | — | FY2021 | Bridge check: pretax_income − income_tax_expense reproduces this exactly, zero residual, FY2022-FY2025. Statement-location detection ambiguity noted in Milestone 1 remains open (multiple identically-valued contexts; the consolidated no-segment context is used). |
| `diluted_eps` | IS | `us-gaap:EarningsPerShareDiluted` | Direct | `signed_bidirectional` | Statement of Operations, "Diluted" | — | FY2021 | Cross-check: net_income / diluted_shares reproduces reported EPS to the cent, FY2022-FY2025. |
| `diluted_shares` | IS | `us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding` | Direct | `point_in_time_unsigned` (share count) | Statement of Operations, "Weighted average diluted shares outstanding" | — | FY2021 | — |
| `operating_cash_flow`, `investing_cash_flow`, `financing_cash_flow`, `net_change_in_cash` | CF | (see Milestone 1 mapping) | Direct | `signed_bidirectional` | Statement of Cash Flows | Already resolved (Milestone 1) | FY2021 | Already `reviewed`. Annual context confirmed identical pattern in both 10-Ks. |
| `capital_expenditure` | CF | `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment` | Direct | `positive_magnitude_outflow` | Statement of Cash Flows, "Investments in property and equipment" | — | FY2021 | — |
| `depreciation_amortization_cfo_addback` | CF | `us-gaap:DepreciationDepletionAndAmortization` | Direct | `positive_magnitude_inflow` | Statement of Cash Flows, "Depreciation and amortization" | — | FY2021 | Already `reviewed` (Milestone 1). |
| `dividends_paid` | CF | `us-gaap:PaymentsOfDividendsCommonStock` **(tag detail confirmed this milestone)** | Direct | `positive_magnitude_outflow` | Statement of Cash Flows, "Dividends paid" | Generic `PaymentsOfDividends`: **0 occurrences** — the common-stock-specific tag is the one actually used | FY2021 | — |
| `share_repurchases` | CF | `us-gaap:PaymentsForRepurchaseOfCommonStock` | Direct | `positive_magnitude_outflow` | Statement of Cash Flows, "Share repurchases" | — | FY2021 | FY2023 value is a reported zero (`—`), not a missing value — confirmed present in the tagged statement with an explicit em-dash. |
| `debt_proceeds` | CF | `us-gaap:ProceedsFromIssuanceOfLongTermDebt` | Direct | `positive_magnitude_inflow` | Statement of Cash Flows, "Issuance of long-term debt" | — | FY2021 | FY2023 value is a reported zero (`—`), confirmed, not missing. |
| `debt_repayments` | CF | `us-gaap:RepaymentsOfLongTermDebt` | Direct | `positive_magnitude_outflow` | Statement of Cash Flows, "Repayments of long-term debt" | — | FY2021 | — |
| `cash_and_equivalents_balance_sheet` | BS | `us-gaap:CashCashEquivalentsAndShortTermInvestments` | Direct, point-in-time | `point_in_time_unsigned` | Statement of Financial Position, "Cash and cash equivalents" | — | FY2021 (and FY2022 — see below) | Already `reviewed` (Milestone 1). Two-year BS lookback in each 10-K covers FY2024/FY2025 and FY2023/FY2024 only. |
| `inventory` | BS | `us-gaap:InventoryNet` | Direct, point-in-time | `point_in_time_unsigned` | Statement of Financial Position, "Inventory" | — | FY2021, **FY2022** (blocked — see §9) | — |
| `accounts_payable` | BS | `us-gaap:AccountsPayableCurrent` | Direct, point-in-time | `point_in_time_unsigned` | Statement of Financial Position, "Accounts payable" | — | FY2021, **FY2022** | Milestone 1's interim-gap limitation for quarterly AP does not apply to the annual (10-K-only) figure used here. |
| `long_term_debt` | BS | `us-gaap:LongTermDebtAndCapitalLeaseObligations` **(corrected this milestone)** + `...Current` | Direct, point-in-time | `point_in_time_unsigned` | Statement of Financial Position, "Long-term debt and other borrowings" (noncurrent) + current portion | Original candidate `LongTermDebtNoncurrent`: **0 occurrences**. Competing candidate `us-gaap:LongTermDebt` (note-schedule total) **unresolved** — see §9 | FY2021, **FY2022** | Tag correction applied to `config/metrics.csv` this milestone. |

---

## 2. Annual historical dry-run table (FY2022-FY2025)

All figures in USD millions unless noted. **FY2022 column values are sourced
only from the FY2024 10-K's own comparative context (`c-5`) — corroborating,
not authoritative**, pending the FY2022 10-K itself (see §1). No FY2021
column is shown; every FY2021 figure is fully blocked pending that same
filing.

### Income statement

| Line | FY2022 (corroborating only) | FY2023 (53wk; comparative-only, no primary-authority filing) | FY2024 | FY2025 |
|---|---:|---:|---:|---:|
| Revenue | 109,120 | 107,412 | 106,566 | 104,780 |
| Cost of sales | 82,306 | 77,828 | 76,502 | 75,511 |
| **Gross profit (derived)** | **26,814** | **29,584** | **30,064** | **29,269** |
| Gross margin | 24.58% | 27.55% | 28.21% | 27.94% |
| SG&A | 20,581 | 21,462 | 21,969 | 21,535 |
| D&A (opex) | 2,385 | 2,415 | 2,529 | 2,617 |
| Operating income (reported) | 3,848 | 5,707 | 5,566 | 5,117 |
| — bridge check (Gross profit − SG&A − D&A) | 3,848 ✓ | 5,707 ✓ | 5,566 ✓ | 5,117 ✓ |
| Operating margin | 3.53% | 5.31% | 5.22% | 4.88% |
| Net interest expense | 478 | 502 | 411 | 445 |
| Net other income | 48 | 92 | 106 | 95 |
| Pretax income (reported) | 3,418 | 5,297 | 5,261 | 4,767 |
| — bridge check (OpInc − Int + Other) | 3,418 ✓ | 5,297 ✓ | 5,261 ✓ | 4,767 ✓ |
| Income tax expense | 638 | 1,159 | 1,170 | 1,062 |
| Effective tax rate | 18.67% | 21.88% | 22.24% | 22.28% |
| Net income (reported) | 2,780 | 4,138 | 4,091 | 3,705 |
| — bridge check (Pretax − Tax) | 2,780 ✓ | 4,138 ✓ | 4,091 ✓ | 3,705 ✓ |
| Net margin | 2.55% | 3.85% | 3.84% | 3.54% |
| Diluted shares (millions) | 464.7 | 462.8 | 461.8 | 455.6 |
| Diluted EPS (reported) | 5.98 | 8.94 | 8.86 | 8.13 |
| — cross-check (NI / diluted shares) | 5.98 ✓ | 8.94 ✓ | 8.86 ✓ | 8.13 ✓ |

**Reported year-over-year growth (unadjusted) with 53-week limitation note:**
FY2023 revenue declined 1.57% vs. FY2022 on a 53-week vs. 52-week basis
(FY2023 had one extra week); FY2024 revenue declined 0.79% vs. FY2023 on a
52-week vs. 53-week basis (FY2024 had one fewer week — the reported decline
therefore understates the underlying comparable-week trend, since Target
itself attributes ~$1.7B of FY2023 net sales to the extra week alone). No
adjusted 52-week figure is computed or asserted for FY2023.

### Cash flow statement

| Line | FY2022 (corroborating only) | FY2023 | FY2024 | FY2025 |
|---|---:|---:|---:|---:|
| Operating cash flow (CFO) | 4,018 | 8,621 | 7,367 | 6,562 |
| Investing cash flow (CFI) | (5,504) | (4,760) | (2,860) | (3,649) |
| Financing cash flow (CFF) | (2,196) | (2,285) | (3,550) | (2,187) |
| — composition check (CFO+CFI+CFF) | (3,682) | 1,576 | 957 | 726 |
| Net change in cash (reported) | (3,682) | 1,576 | 957 | 726 |
| — composition check vs. reported | ✓ exact | ✓ exact | ✓ exact | ✓ exact |
| Capital expenditure | 5,528 | 4,806 | 2,891 | 3,727 |
| **Free cash flow (CFO − CapEx)** | **(1,510)** | **3,815** | **4,476** | **2,835** |
| D&A (CFO add-back) | 2,700 | 2,801 | 2,981 | 3,134 |
| Dividends paid | 1,836 | 2,011 | 2,046 | 2,053 |
| Share repurchases | 2,646 | 0 (reported) | 1,007 | 408 |
| Debt proceeds | 2,625 | 0 (reported) | 741 | 1,984 |
| Debt repayments | 163 | 147 | 1,139 | 1,643 |

### Balance sheet / working capital

| Line (fiscal year-end instant) | FY2022 | FY2023 (comparative-only) | FY2024 | FY2025 |
|---|---:|---:|---:|---:|
| Cash and equivalents | **BLOCKED** — see §9 | 3,805 | 4,762 | 5,488 |
| Inventory | **BLOCKED** | 11,886 | 12,740 | 12,304 |
| Accounts payable | **BLOCKED** | 12,098 | 13,053 | 12,622 |
| Long-term debt + capital leases (noncurrent) | **BLOCKED** | 14,922 | 14,304 | 14,326 |
| Long-term debt + capital leases (current) | **BLOCKED** | 1,116 | 1,636 | 2,130 |
| **Total debt** | **BLOCKED** | 16,038 | 15,940 | 16,456 |
| **Net debt** (total debt − cash) | **BLOCKED** | 12,233 | 11,178 | 10,968 |

**Note on FY2022 cash:** the cash *rollforward* balance (beginning/ending
instant used only in the cash-movement check, per `cash_and_equivalents_rollforward`)
for 2023-01-28 is available (2,229, corroborating, from both cached 10-Ks'
comparative cash-flow-statement roll-forward lines). The **balance-sheet**
cash line for that same date is not — the two-year balance-sheet lookback in
the FY2024 10-K reaches only to 2024-02-03. This is exactly the distinction
the two separate metrics (`cash_and_equivalents_balance_sheet` vs.
`cash_and_equivalents_rollforward`) were designed to preserve.

### Operational drivers

| Driver | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---:|---:|---:|---:|
| CapEx % revenue | 5.07% | 4.47% | 2.71% | 3.56% |
| CFO margin | 3.68% | 8.03% | 6.91% | 6.26% |
| FCF margin | (1.38%) | 3.55% | 4.20% | 2.71% |
| Cash conversion (CFO/NI) | 1.45x | 2.08x | 1.80x | 1.77x |
| Inventory % revenue | **BLOCKED** | 11.07% | 11.96% | 11.74% |
| AP % cost of sales | **BLOCKED** | 15.55% | 17.06% | 16.72% |
| Debt-to-CFO | **BLOCKED** | 1.86x | 2.16x | 2.51x |
| Net-debt-to-CFO | **BLOCKED** | 1.42x | 1.52x | 1.67x |
| Distributions % FCF ((dividends+repurchases)/FCF) | **NOT_APPLICABLE** (FCF negative) | 52.72% | 68.16% | 86.81% |

FY2022's distributions/FCF ratio is deliberately classified `NOT_APPLICABLE`
rather than reported as a raw negative percentage — dividing a positive
distribution total by a negative FCF produces a mathematically well-defined
but economically misleading negative ratio (it would read as if
distributions were "negative," which is not what happened; FY2022 simply
funded its distributions from sources other than that year's free cash
flow).

---

## 7. Driver dictionary

### Core margin / rate metrics

| ID | Business meaning | Formula | Unit | Frequency | Sign | Limitation | Forecast relevance |
|---|---|---|---|---|---|---|---|
| `gross_margin` | Pricing/COGS efficiency | gross_profit / revenue | % | Annual (quarterly once IS metrics are quarterized) | Positive | Depends on derived gross_profit | Revenue-driver anchor |
| `operating_margin` | Core operating profitability | operating_income / revenue | % | Annual | Positive | — | Margin-bridge anchor |
| `effective_tax_rate` | Effective tax burden | income_tax_expense / pretax_income | % | Annual | Positive, typically 15-30% | Sensitive to one-off tax items not separately identified | Tax-assumption anchor |
| `net_margin` | Bottom-line profitability | net_income / revenue | % | Annual | Positive | — | EPS-bridge anchor |

### The nine requested operational drivers

| Driver ID | Business meaning | Formula | Numerator / Denominator | Unit | Valid frequency | Sign interpretation | Limitation | Forecast relevance | Source-lineage requirement |
|---|---|---|---|---|---|---|---|---|---|
| `capex_pct_revenue` | Capital intensity of the business | capital_expenditure / revenue | capital_expenditure / revenue | % | Annual, quarterly (CFO metrics already quarterized) | Positive; higher = more capital-intensive | CapEx is lumpy year to year (e.g. FY2022/FY2023 store-remodel cycle vs. FY2024 pullback) | Anchors forecast CapEx as % of forecast revenue | Both inputs must trace to `reviewed` mappings before use |
| `cfo_margin` | Cash-generative efficiency of operations | operating_cash_flow / revenue | CFO / revenue | % | Annual, quarterly | Positive in all periods examined; concept itself is `signed_bidirectional` | — | Core driver for CFO forecast | — |
| `fcf_margin` | Cash left after reinvestment, as % of sales | (operating_cash_flow − capital_expenditure) / revenue | FCF / revenue | % | Annual, quarterly | Can be negative (FY2022) | Inherits CapEx lumpiness | Core driver for FCF forecast and, later, investment capacity | — |
| `cash_conversion` | How much of accounting profit becomes cash | operating_cash_flow / net_income | CFO / net_income | ratio (x) | Annual, quarterly | Normally >1x when D&A > working-capital drag; undefined if net_income = 0 | Not meaningful in a net-loss period (none observed FY2022-FY2025) | Diagnostic for earnings quality | — |
| `inventory_pct_revenue` | Inventory intensity | inventory / revenue | inventory (point-in-time) / revenue (annual flow) | % | Annual only (point-in-time vs. flow mismatch makes quarterly less meaningful without average-balance convention) | Positive | Mixes a point-in-time stock with an annual flow — a convention decision (average vs. year-end inventory) is needed before quarterly use | Working-capital forecast anchor | Inventory value must be flagged `point_in_time`, never differenced |
| `ap_pct_cogs` | Trade-payable-funded portion of COGS | accounts_payable / cost_of_sales | AP (point-in-time) / COGS (annual flow) | % | Annual only, same convention caveat as above | Positive | Same point-in-time/flow mismatch | Working-capital forecast anchor | — |
| `debt_to_cfo` | Leverage relative to cash-generating capacity | total_debt / operating_cash_flow | total_debt (point-in-time) / CFO (annual flow) | ratio (x) | Annual | Positive; higher = more leveraged relative to cash flow | Depends on the unresolved `LongTermDebt` vs. `LongTermDebtAndCapitalLeaseObligations` question (§9) | Debt-capacity / covenant-style driver | — |
| `net_debt_to_cfo` | Leverage net of cash reserves | net_debt / operating_cash_flow | (total_debt − cash) / CFO | ratio (x) | Annual | Positive here in every year examined; could be negative if cash > debt | Same debt-definition dependency | Debt-capacity driver | — |
| `distributions_pct_fcf` | Share of free cash flow returned to shareholders | (dividends_paid + share_repurchases) / (operating_cash_flow − capital_expenditure) | distributions / FCF | % | Annual | Positive when FCF > 0; **NOT_APPLICABLE when FCF ≤ 0** (see FY2022) | Capital-allocation / distribution-sustainability driver | Must carry an explicit NOT_APPLICABLE branch, never a raw negative-denominator ratio |

**Separation of historical observation from future assumption (per item 7):**
every driver above is, in this milestone, a purely historical, backward-looking
observation computed from filed facts. **No driver value in this table is a
forecast input, target, or assumption** — that distinction (a separate
`assumptions`/driver-projection layer) is explicitly out of scope until a
forecasting milestone is authorized, consistent with `sql/schema.sql`'s
already-declared-but-unpopulated `assumptions` table.

---

## 6. Proposed analytical schema

**Not implemented.** Two designs are presented for review, per item 6's
requirement to support annual+quarterly frequencies, instant+duration facts,
direct+derived facts, as-originally-filed/latest-restated views,
selected/corroborating observations, metric-definition versions,
source/derivation lineage, and deterministic rebuilds.

### Option A (recommended): parallel `annual_facts` / `annual_lineage`, mirroring the existing quarterly design

This is the same pattern already used successfully for `instant_facts` in
Milestone 1: a new table alongside the existing ones, touching nothing that
already exists. It is a **safe additive migration** — `TableMigration`,
`CREATE TABLE IF NOT EXISTS`, no `ALTER` of any existing table, fully
consistent with every migration applied so far in this project.

```sql
CREATE TABLE IF NOT EXISTS annual_facts (
    annual_fact_id     TEXT PRIMARY KEY,
    metric             TEXT NOT NULL,                  -- key into config/metrics.csv
    fiscal_year        INTEGER NOT NULL,
    period_start       TEXT NOT NULL,
    period_end         TEXT NOT NULL,
    days_in_period     INTEGER NOT NULL,                -- 364 or 371 (53wk) -- makes the week-count explicit and queryable
    value_original     REAL NOT NULL,
    original_unit      TEXT NOT NULL,
    value_normalized   REAL NOT NULL,
    normalized_unit    TEXT NOT NULL DEFAULT 'USD_millions',
    basis              TEXT NOT NULL CHECK (
                            basis IN ('direct_annual', 'derived_annual', 'derived_from_quarters')
                        ),
    fact_status        TEXT NOT NULL DEFAULT 'authoritative'
                            CHECK (fact_status IN ('authoritative', 'corroborating_only')),
                        -- 'corroborating_only' = no filing whose own period_of_report
                        -- equals this fact's period exists yet (e.g. FY2022 today; FY2023 permanently)
    analytical_view    TEXT NOT NULL DEFAULT 'as_originally_filed'
                            CHECK (analytical_view IN ('as_originally_filed', 'latest_restated')),
    accession_number   TEXT NOT NULL REFERENCES filings(accession_number),
    filed_at           TEXT NOT NULL,
    mapping_version    TEXT NOT NULL,
    as_of_date         TEXT NOT NULL,
    is_current_view    INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS annual_lineage (
    annual_lineage_id  TEXT PRIMARY KEY,
    derived_fact_id    TEXT NOT NULL REFERENCES annual_facts(annual_fact_id),
    input_fact_id      TEXT NOT NULL REFERENCES raw_facts(fact_id),
    operation          TEXT NOT NULL                     -- 'direct', 'corroborating', 'derived_subtraction', etc.
);

CREATE TABLE IF NOT EXISTS annual_fact_observations (
    observation_id            TEXT PRIMARY KEY,
    annual_fact_id            TEXT NOT NULL REFERENCES annual_facts(annual_fact_id),
    raw_fact_id                TEXT NOT NULL REFERENCES raw_facts(fact_id),
    accession_number           TEXT NOT NULL REFERENCES filings(accession_number),
    relationship                TEXT NOT NULL CHECK (relationship IN ('selected', 'corroborating', 'conflicting')),
    value_original              REAL NOT NULL,
    difference_from_selected    REAL,
    note                        TEXT
);
```

Point-in-time annual facts (balance-sheet lines as of a 10-K's fiscal
year-end) need **no schema change at all** — `instant_facts` is already
keyed by `as_of_date`, not by fiscal quarter, so it already supports annual
instants; the FY2022/FY2023 balance-sheet gaps in §5 are a *source*
limitation, not a schema limitation.

**Metric-definition versioning:** `mapping_version` (already present on
every fact table) already serves this role — a definition change (e.g. if
`net_debt` were later redefined to include operating lease liabilities) is
captured by minting a new `mapping_version` string, exactly as the existing
`quarterly_facts`/`instant_facts` tables already do.

**Deterministic rebuild:** unaffected — the existing clean-room-rebuild and
canonical-export methodology (`scripts/clean_room_rebuild.py`,
`scripts/compare_databases.py`) extends to `annual_facts`/`annual_lineage`
by adding two more `SELECT ... ORDER BY` export functions following the
exact same pattern already used for `quarterly_facts`/`lineage`.

### Option B: a single unified `period_facts` table

A more literal reading of "unified... architecture" would replace both
`quarterly_facts` and the proposed `annual_facts` with one table carrying a
`frequency` discriminator (`'quarterly' | 'annual'`) and a nullable
`fiscal_quarter`. This is **not recommended**: every migration applied in
this project so far (`ColumnMigration`, `TableMigration`) has been
deliberately restricted to additive, non-breaking changes that never alter
an existing table's constraints or require moving existing rows. Unifying
`quarterly_facts` into a new table would require migrating all 28 existing
`quarterly_facts` rows and their 45 `lineage` rows into a new structure,
relaxing `quarterly_facts.fiscal_quarter`'s `NOT NULL CHECK (BETWEEN 1 AND
4)` constraint, and retiring or aliasing the existing `views.sql` and
`compare_databases.py` exports that key on the current shape — a
non-additive, higher-risk change with no compensating analytical benefit
over Option A, whose two tables can be queried together trivially with a
`UNION ALL` view if a single logical view is ever wanted.

**Recommendation: Option A.** Reviewer decision requested before any
implementation.

---

## 8. Validation plan and dry-run results

Classification per item 8: **PASS** / **FAIL** / **BLOCKED** (required input
unavailable) / **UNAVAILABLE** (independent evidence structurally doesn't
exist) / **NOT_APPLICABLE**.

| # | Validation | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---|---|---|---|---|
| 1 | Income-statement arithmetic (Revenue−COGS−SG&A−D&A=OpInc) | PASS (corroborating-only input) | PASS | PASS | PASS |
| 2 | Pretax-income bridge (OpInc−Interest+Other=Pretax) | PASS (corrob.-only) | PASS | PASS | PASS |
| 3 | Effective tax rate reasonableness (0-40% band) | PASS (18.67%) | PASS (21.88%) | PASS (22.24%) | PASS (22.28%) |
| 4 | Gross-profit derivation consistency (no direct tag ever competes) | PASS | PASS | PASS | PASS |
| 5 | CFO reconciliation (indirect method, full) | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE |
| 6 | FCF calculation (CFO−CapEx) | PASS | PASS | PASS | PASS |
| 7a | Cash movement (beginning+net change=ending) | BLOCKED (BS cash blocked) | PASS | PASS | PASS |
| 7b | Cash-flow composition (CFO+CFI+CFF=net change) | PASS (corrob.-only, exact) | PASS (exact) | PASS (exact) | PASS (exact) |
| 8 | Debt roll-forward (beginning+proceeds−repayments≈ending) | BLOCKED | UNAVAILABLE (reasonableness-only, not exact) | UNAVAILABLE | UNAVAILABLE |
| 9 | Annual-vs-quarter agreement, FY2025 | PASS (CFO/CFI/CFF/net-change, from Milestone 1) / UNAVAILABLE (IS lines, not yet quarterized) | N/A | N/A | see left |
| 10 | Balance-sheet instant authority | BLOCKED (no filing yet) | UNAVAILABLE (permanently comparative-only — see §1) | PASS | PASS |
| 11 | Direct-vs-derived status recorded per metric | PASS (§5 table complete) | PASS | PASS | PASS |
| 12 | Lineage completeness (every fact traces to ≥1 raw fact) | N/A — nothing persisted yet | N/A | N/A | N/A |
| 13 | 53-week-year disclosure present and no invented adjustment | N/A | PASS (verbatim disclosure recorded, §4) | N/A | N/A |

**Notes on the UNAVAILABLE items:**

- **#5 (full CFO reconciliation):** a complete indirect-method proof needs
  every reconciling line item Target reports between net income and CFO
  (stock-based compensation, deferred income taxes, impairments, other
  non-cash items, and the full working-capital line set) — only
  D&A-addback, and (candidate, not yet reviewed) inventory/AP adjustments
  are currently mapped. This becomes a PASS/FAIL check once those additional
  tags are mapped and reviewed in a future pass; until then it is honestly
  UNAVAILABLE, not silently skipped.
- **#8 (debt roll-forward):** `ProceedsFromIssuanceOfLongTermDebt` −
  `RepaymentsOfLongTermDebt` does not exactly bridge the balance-sheet
  long-term-debt change, because the balance-sheet line includes capital/
  finance lease obligations (which have their own non-cash roll-forward not
  reflected in the two cash-flow-statement debt lines) and because of the
  current/noncurrent reclassification each year. A reasonableness check
  (same-order-of-magnitude, same-direction) could be built, but an exact
  roll-forward is not supportable with the currently-mapped tags.
- **#9 IS-line annual-vs-quarter agreement:** the income-statement metrics
  (revenue, COGS, SG&A, etc.) are not part of Milestone 1's quarterized set
  (only the four cash-flow totals and instant cash balances were
  quarterized) — so there is no independent quarterly figure to check the
  FY2025 annual figure against yet for these lines.

---

## Unresolved mappings and accounting limitations

1. **`long_term_debt` competing candidate** (§5): `us-gaap:LongTermDebt`
   (note-schedule total) vs. `us-gaap:LongTermDebtAndCapitalLeaseObligations`
   (statement-of-financial-position line) disagree numerically (FY2025:
   14,398M vs. 14,326M). Needs reviewer decision on which is the correct
   "interest-bearing debt" input to `net_debt` before that mapping can be
   marked `reviewed`.
2. **`net_income` statement-location ambiguity** carried over from
   Milestone 1: multiple identically-valued contexts exist for
   `NetIncomeLoss`; the consolidated no-segment context is used, but this
   was documented as unresolved in Milestone 1 and remains so.
3. **Operating lease liabilities** ("when supportable" per item 2) — not
   evaluated in this milestone; no candidate tag has been checked yet. If
   material to net debt, this is a further mapping-review item for a future
   pass, not resolved here.
4. **Point-in-time vs. annual-flow ratio convention** (`inventory_pct_revenue`,
   `ap_pct_cogs`): using year-end (not average) inventory/AP against a
   full-year flow is a convention choice flagged in the driver dictionary
   (§7), not yet reviewer-confirmed.
5. **FY2023 permanent corroborating-only status** (§1): a structural
   limitation of the available filing set, not fixable by any single
   additional filing request.
6. **FY2022 balance-sheet items and FY2021 in full**: BLOCKED pending the
   requested FY2022 10-K.

---

## Tests executed

The existing 148-test Milestone 1 suite was re-run to confirm this
milestone's read-only research and `config/metrics.csv` tag corrections
introduced no regression (no code in `src/target_cash/` was modified this
milestone — only `config/metrics.csv` candidate tag values, which the test
suite does not hardcode):

```
python -m pytest tests/ -q
```

Result: **148 passed**, 0 failed. (No new tests were added this milestone —
no new code was written; the schema in §6 is a proposal, not an
implementation, so there is nothing new to unit-test yet.)

---

## Git diff summary

Files changed this milestone (all documentation and mapping-config; no
`src/target_cash/` code, no database, no schema migration):

- `config/metrics.csv` — three `candidate_xbrl_tag` corrections
  (`operating_expenses`, `long_term_debt`, `gross_profit` note), all kept at
  `mapping_status=candidate_unverified`.
- `docs/decisions.md` — new append-only entry recording this milestone's
  findings (tag corrections, source-authority gaps, bridge verification,
  53-week disclosure).
- `docs/limitations.md` — new entry recording the FY2022-pending and
  permanent-FY2023-comparative-only limitations.
- `docs/milestone_2_proposal.md` — this document (new file).

No file under `data/raw/`, `data/curated/`, or any database was created,
modified, or committed.

---

## Summary and stop point

Per the governing instruction: **no annual analytical fact has been
persisted, no schema has been implemented, no mapping has been marked
reviewed, and no forecasting/DCF/Excel/Power BI/website work has begun.**
This document, together with the `config/metrics.csv` and `docs/decisions.md`
updates, is the complete Milestone 2 deliverable package. Awaiting:

1. The FY2022 10-K (requested in §1), and
2. Reviewer approval of the mapping matrix (§5), the proposed schema (§6,
   Option A recommended), and the validation plan (§8) — including a
   decision on the unresolved `long_term_debt` competing-candidate question
   (§9) — before any schema implementation or analytical persistence
   proceeds.
