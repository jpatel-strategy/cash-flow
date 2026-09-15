# Milestone 2 Proposal: Five-Year Historical Financial Model and Driver Architecture

**Status: REVISED after a methodology correction. DELIVERABLES FOR REVIEW.**
Nothing in this milestone has been persisted as an annual analytical fact.
No schema in this document has been implemented. No mapping below is marked
`reviewed`. No forecasting, DCF, Excel, Power BI, or website work has begun.

## Correction notice (read first)

The first version of this document contained a methodology error: it
claimed FY2023 could never have primary-filing authority under this
project's filing set, and — chronologically impossible — that FY2023 would
appear as a comparative in the FY2022 10-K (a filing that predates FY2023
and cannot contain it). Both claims were wrong. The actual gap was simply
that this project's source manifest was missing the FY2023 10-K itself.

**Correction applied:** the FY2023 10-K (accession `0000027419-24-000032`),
FY2022 10-K (accession `0000027419-23-000015`), and FY2021 10-K (accession
`0000027419-22-000007`) were supplied by the project owner, verified,
hash-registered, and ingested. **The full five-year authoritative filing
set (FY2021-FY2025) is now in place.** Full detail of the correction is in
`docs/decisions.md`'s 2026-09-15 "Methodology correction" entry.

Re-examining each year through its *own* primary filing — rather than
through a later filing's comparative column, which is what the first pass
had no choice but to do for FY2021/FY2022/FY2023 — surfaced real findings
that the first pass could not have seen: two genuine reclassifications, two
tag migrations across filing vintages, and an unresolved debt-reconciliation
gap. These are documented in full below and in `docs/decisions.md`. **Every
finding from the first version of this document is downgraded to
PROVISIONAL and reassessed here against the newly authoritative sources.**

---

## Table of contents

1. [Source coverage — corrected, complete inventory](#1-source-coverage)
2. [Authority framework](#3-authority-framework)
3. [Financial definitions](#4-financial-definitions)
4. [Accounting consistency — 53-week fiscal year](#5-accounting-consistency)
5. [Five-year mapping matrix — revised](#6-five-year-mapping-matrix)
6. [Annual historical dry-run table (FY2021-FY2025) — provisional](#7-annual-dry-run-table)
7. [Debt reconciliation](#8-debt-reconciliation)
8. [Driver dictionary](#9-driver-dictionary)
9. [Proposed analytical schema, including `period_facts_unified`](#10-proposed-schema)
10. [Validation plan and dry-run results](#11-validation-plan)
11. [Tests executed](#tests-executed)
12. [Git diff summary](#git-diff-summary)

---

## 1. Source coverage

**The complete five-year authoritative filing set is now ingested.**

| Filing | Accession | Period of report | Filed at (signature-page date) | SHA-256 | Status |
|---|---|---|---|---|---|
| FY2025 10-K | `0000027419-26-000016` | 2026-01-31 | 2026-03-11 | `20bc4552...` | Ingested (Milestone 1) |
| FY2024 10-K | `0000027419-25-000018` | 2025-02-01 | 2025-03-12 | `d079d7c1...` | Ingested (Milestone 1) |
| **FY2023 10-K** | `0000027419-24-000032` | 2024-02-03 | 2024-03-13 | `f37f8372...` | **Ingested this milestone** |
| **FY2022 10-K** | `0000027419-23-000015` | 2023-01-28 | 2023-03-08 | `45a94324...` | **Ingested this milestone** |
| **FY2021 10-K** | `0000027419-22-000007` | 2022-01-29 | 2022-03-09 | `487a6f5c...` | **Ingested this milestone** |
| FY2025 Q1/Q2/Q3 10-Qs | see `docs/sources.csv` | — | — | — | Ingested (Milestone 1) |

Each new filing was verified before ingestion (dei:EntityRegistrantName,
dei:EntityCentralIndexKey=`0000027419`, dei:DocumentType=10-K,
dei:DocumentFiscalYearFocus matching the expected year, dei:AmendmentFlag=
FALSE, dei:TradingSymbol=TGT, dei:EntityFileNumber=1-6049,
dei:DocumentPeriodEndDate matching the expected date via its nested
`CurrentFiscalYearEndDate` span — e.g. the FY2023 10-K resolves to "February
3, 2024"), hash-verified, and registered via
`target_cash.cli fetch --mode manual` (the tested manifest-append path, not
a hand-edited CSV). No SEC block-page markers found in any of the three. The
FY2021 10-K's `dei:EntityRegistrantName` reads "TARGET CORP" rather than
"TARGET CORPORATION" — the same CIK (`0000027419`), a legal-name variant,
not a distinct entity.

**Idempotency confirmed:** a repeat `fetch` call for the FY2023 accession
was refused ("already has a record for accession ... refusing to create a
duplicate row"). A repeat `normalize` call after ingestion inserted zero new
raw facts.

**Raw-fact counts** (`normalize`, dry-run, no `--persist-derived`):

| Filing | Facts found (current concept list) | Facts newly inserted |
|---|---:|---:|
| FY2025 10-K | 163 | 8 |
| FY2025 Q1 10-Q | 116 | 7 |
| FY2025 Q2 10-Q | 184 | 11 |
| FY2025 Q3 10-Q | 186 | 11 |
| FY2024 10-K | 162 | 8 |
| **FY2023 10-K** | **129** | **102** |
| **FY2022 10-K** | **130** | **103** |
| **FY2021 10-K** | **114** | **97** |

`raw_facts_stored` after ingesting the three new filings: **1035** (up from
688 at Milestone 1's close). After also adding the three new
debt-reconciliation candidate tags to `config/metrics.csv` (§8) and
re-running `normalize`, `raw_facts_stored` = **1113**. `quarterly_facts_in_db`
(28) and `instant_facts_in_db` (10) are **unchanged** throughout —
`derivation_persisted: false` on every run. Nothing has been persisted.

---

## 2. Authority framework

Per the instruction not to treat comparative availability as authority, the
following four states are used consistently for every fiscal year and
every metric below:

| State | Meaning |
|---|---|
| **Authoritative primary-period filing** | A filing whose own `period_of_report` equals the fact's period. Exists now for **every year FY2021-FY2025** — the five-filing set closes the window completely. |
| **Corroborating comparative** | The same fact reported in a *different* filing's comparative column (one or two years back). Retained, never discarded, but never itself sufficient to call a year authoritative. |
| **Conflicting/restated observation** | A corroborating comparative that disagrees numerically with the authoritative primary-period value (see §6/§7 — genuine cases found this milestone). Both values retained; neither silently overwritten. |
| **Missing authoritative source** | No filing exists (or is held) whose own period matches. **Does not currently apply to any FY2021-FY2025 metric** — this state applied to FY2021/FY2022 before this milestone's ingestion and is now cleared. |

Every year now has an authoritative primary-period filing for income
statement, cash flow statement, *and* balance sheet — the FY2021-FY2025
window is fully closed.

---

## 3. Financial definitions

Unchanged from the first version of this document except where noted below
(the debt/net-debt definitions in §8 supersede the earlier draft language).

| Term | Definition | Notes |
|---|---|---|
| **Gross profit** | Revenue − Cost of sales | Always **derived** — confirmed absent (0 occurrences) in all **five** filings, not just the two examined in the first pass. |
| **Free cash flow (FCF)** | Operating cash flow − Capital expenditures | This project's own working definition. Confirmed again: no `*FreeCashFlow*` XBRL concept exists in any of the five filings, and the text "free cash flow" is never used as a labeled Target measure. Never presented as Target's official non-GAAP FCF. |
| **Net debt** | Total interest-bearing debt − Cash and cash equivalents (and any short-term investments in the same balance-sheet line) | **Confirmed this milestone: the text "net debt" does not appear anywhere in any of the five cached filings.** This is entirely this project's own construction, never a Target-defined figure. "Total interest-bearing debt" itself is an open definitional choice — see §8. |
| **Cash conversion** | Operating cash flow / Net income | A ratio, not a percentage. |

**Caveats carried forward, reaffirmed:** this project's FCF is never labeled
Target's own non-GAAP measure; financing cash flows are never treated as
operating investment capacity.

---

## 4. Accounting consistency — 53-week fiscal year

**Reassessed and strengthened**, now backed directly by the FY2023 10-K's
own primary text (previously this section relied only on the FY2024/FY2025
10-Ks' comparative mentions):

> FY2023 10-K, own primary statement: "2023 consisted of 53 weeks. The
> extra week in 2023 contributed $1.7 billion of sales." … "2023 consisted
> of 53 weeks compared with 52 weeks in 2022 and 2021."

This is now confirmed from the primary source for FY2023 itself, not merely
from later filings' comparatives.

| Fiscal year | Weeks | Period |
|---|---|---|
| FY2021 | 52 | 2021-01-31 to 2022-01-29 |
| FY2022 | 52 | 2022-01-30 to 2023-01-28 |
| FY2023 | **53** | 2023-01-29 to 2024-02-03 |
| FY2024 | 52 | 2024-02-04 to 2025-02-01 |
| FY2025 | 52 | 2025-02-02 to 2026-01-31 |

**Reported growth, with week-count limitation notes, all now backed by
authoritative-filing figures (not comparative-only):**

- FY2022 vs. FY2021 (52wk vs. 52wk, directly comparable): revenue +2.94%.
- FY2023 vs. FY2022 (53wk vs. 52wk): revenue **-1.57% even including** the
  extra week's ~$1.7B contribution — the underlying comparable-week decline
  is larger than the headline number suggests.
- FY2024 vs. FY2023 (52wk vs. 53wk): revenue -0.79% — this headline number
  is **worse** on a comparable-week basis than it looks, since FY2024 had
  one fewer selling week than FY2023.
- FY2025 vs. FY2024 (52wk vs. 52wk, directly comparable): revenue -1.68%.

No 52-week-adjusted figure is invented anywhere in this project.

---

## 5. Five-year mapping matrix

**Revised** to incorporate the tag migrations and reclassifications found
this milestone. Every row stays at its existing `mapping_status`
(`candidate_unverified` unless already `reviewed` in Milestone 1); no
mapping is marked reviewed in this document.

| Metric | FY2021 tag (own 10-K) | FY2022 tag (own 10-K) | FY2023 tag (own 10-K) | FY2024/FY2025 tag | Consistency finding |
|---|---|---|---|---|---|
| `revenue` | `RevenueFromContractWithCustomerExcludingAssessedTax` | same | same | same | Fully consistent across all 5 filings, zero discrepancy. |
| `cost_of_sales` | `CostOfGoodsAndServicesSold` | same | same | same | **Reclassification found** — see below; tag is consistent, the *value* for FY2022/FY2023 differs by filing vintage. |
| `gross_profit` | *(none — derived)* | *(none)* | *(none)* | *(none)* | Confirmed absent in all 5 filings, not just 2. Always derived. |
| `operating_expenses` (SG&A) | `SellingGeneralAndAdministrativeExpense` | same | same | same | Tag consistent across all 5 filings; **value for FY2022/FY2023 differs by vintage** — see reclassification below. |
| `depreciation_amortization_opex` | `DepreciationAndAmortization` | same | same | same | Fully consistent. |
| `operating_income` | `OperatingIncomeLoss` | same | same | same | Fully consistent; unaffected by the COGS/SG&A reclassification (bridge holds exactly under both splits). |
| `interest_expense` | **`InterestExpense`** | **`InterestExpense`** | **`InterestExpense`** | `InterestExpenseNonoperating` | **Tag migration** — the plain `InterestExpense` tag is used through the FY2023 10-K; `InterestExpenseNonoperating` (this project's current candidate) begins with the FY2024 10-K. Values fully continuous across the rename (421→478→502→411→445). |
| `net_other_income` | `OtherNonoperatingIncomeExpense` | same | same | same | Fully consistent (already `reviewed` for FY2024/FY2025; confirmed continuing back through FY2021). |
| `pretax_income` | `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | same | same | same | Fully consistent; bridge exact in all 5 years. |
| `income_tax_expense` | `IncomeTaxExpenseBenefit` | same | same | same | Fully consistent. |
| `net_income` | **`NetIncomeLossAvailableToCommonStockholdersBasic`** | `NetIncomeLoss` | `NetIncomeLoss` | `NetIncomeLoss` | **Tag migration** — `NetIncomeLoss` has zero occurrences in the FY2021 10-K; that filing uses the basic-EPS-numerator tag instead (economically identical here — Target has no preferred stock or NCI in this period). `NetIncomeLoss` begins with the FY2022 10-K. |
| `diluted_eps`, `diluted_shares` | `EarningsPerShareDiluted`, `WeightedAverageNumberOfDilutedSharesOutstanding` | same | same | same | Fully consistent; EPS reproduces to the cent from net_income/shares in all 5 years. |
| `operating_cash_flow`, `investing_cash_flow`, `financing_cash_flow` | `NetCashProvidedByUsedIn{Operating,Investing,Financing}Activities` | same | same | same | Fully consistent across all 5 years; composition check (CFO+CFI+CFF=reported net change) exact in every year. |
| `net_change_in_cash` | `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect` | same | same | same | Fully consistent. |
| `capital_expenditure` | `PaymentsToAcquirePropertyPlantAndEquipment` | same | same | same | Fully consistent. |
| `depreciation_amortization_cfo_addback` | `DepreciationDepletionAndAmortization` | same | same | same | Fully consistent. |
| `dividends_paid` | `PaymentsOfDividendsCommonStock` | same | same | same | Fully consistent. |
| `share_repurchases` | `PaymentsForRepurchaseOfCommonStock` | same | same | same | Tag consistent; **FY2022 value reclassified** — see below. FY2023's reported value is a genuine zero (`—`), not missing. |
| `debt_proceeds`, `debt_repayments` | `ProceedsFromIssuanceOfLongTermDebt`, `RepaymentsOfLongTermDebt` | same | same | same | Fully consistent. FY2023's `debt_proceeds` is a genuine reported zero. |
| `cash_and_equivalents_balance_sheet` | `CashCashEquivalentsAndShortTermInvestments` | same | same | same | Fully consistent; every year now has authoritative primary-filing balance-sheet authority. |
| `inventory`, `accounts_payable` | `InventoryNet`, `AccountsPayableCurrent` | same | same | same | Fully consistent; every year now authoritative. |
| `long_term_debt` | `LongTermDebtAndCapitalLeaseObligations` (+ `...Current`) | same | same | same | Tag consistent across all 5 years. See §8 for the full debt reconciliation and the unresolved note-schedule residual. |

### Reclassifications found (real, not tag or mapping errors)

**COGS/SG&A reclassification.** Comparing each year's own primary filing to
how later filings present the same year as a comparative:

| Year | As-originally-filed (own 10-K) | Latest-restated (later 10-K's comparative) | Shift |
|---|---:|---:|---:|
| FY2022 COGS | 82,229 | 82,306 | +77 |
| FY2022 SG&A | 20,658 | 20,581 | -77 |
| FY2023 COGS | 77,736 | 77,828 | +92 |
| FY2023 SG&A | 21,554 | 21,462 | -92 |

In both years, revenue, D&A, and operating income are byte-identical across
every vintage (the combined COGS+SG&A total is unchanged) — a pure
reclassification between two expense lines with **zero effect on operating
income, pretax income, or net income**. It **does** change derived
`gross_profit` and gross margin depending on which vintage's split is used
(shown both ways in §7). This is exactly the case the `instant_facts`
schema's `analytical_view` (`as_originally_filed` / `latest_restated`)
column was designed for.

**Share-repurchase reclassification.** FY2022's
`PaymentsForRepurchaseOfCommonStock`: 2,826 (FY2022 10-K, as-originally-filed)
vs. 2,646 (FY2023 10-K's comparative onward, latest-restated) — a $180M
difference, first appearing one filing cycle earlier than the COGS/SG&A
shift. No mechanism is asserted; both values are retained.

---

## 6. Annual historical dry-run table (FY2021-FY2025) — provisional

All figures USD millions. Every figure below now comes from an
**authoritative primary-period filing** (no more comparative-only figures
for FY2021/FY2022/FY2023). **Marked PROVISIONAL** pending reviewer
sign-off on the reclassification handling in §5 and the debt-metric
decision in §8.

### Income statement

| Line | FY2021 | FY2022 (as-filed) | FY2023 (as-filed) | FY2024 | FY2025 |
|---|---:|---:|---:|---:|---:|
| Revenue | 106,005 | 109,120 | 107,412 | 106,566 | 104,780 |
| Cost of sales | 74,963 | 82,229 | 77,736 | 76,502 | 75,511 |
| **Gross profit (derived, as-filed split)** | **31,042** | **26,891** | **29,676** | **30,064** | **29,269** |
| Gross margin (as-filed) | 29.28% | 24.64% | 27.63% | 28.21% | 27.94% |
| *Gross profit (derived, latest-restated split)* | *n/a* | *26,814* | *29,584* | *n/a* | *n/a* |
| *Gross margin (latest-restated)* | *n/a* | *24.58%* | *27.55%* | *n/a* | *n/a* |
| SG&A (as-filed) | 19,752 | 20,658 | 21,554 | 21,969 | 21,535 |
| D&A (opex) | 2,344 | 2,385 | 2,415 | 2,529 | 2,617 |
| Operating income (reported) | 8,946 | 3,848 | 5,707 | 5,566 | 5,117 |
| — bridge check | 8,946 ✓ | 3,848 ✓ | 5,707 ✓ | 5,566 ✓ | 5,117 ✓ |
| Operating margin | 8.44% | 3.53% | 5.31% | 5.22% | 4.88% |
| Interest expense | 421 | 478 | 502 | 411 | 445 |
| Net other income | 382 | 48 | 92 | 106 | 95 |
| Pretax income | 8,907 | 3,418 | 5,297 | 5,261 | 4,767 |
| — bridge check | 8,907 ✓ | 3,418 ✓ | 5,297 ✓ | 5,261 ✓ | 4,767 ✓ |
| Income tax expense | 1,961 | 638 | 1,159 | 1,170 | 1,062 |
| Effective tax rate | 22.02% | 18.67% | 21.88% | 22.24% | 22.28% |
| Net income | 6,946 | 2,780 | 4,138 | 4,091 | 3,705 |
| — bridge check | 6,946 ✓ | 2,780 ✓ | 4,138 ✓ | 4,091 ✓ | 3,705 ✓ |
| Net margin | 6.55% | 2.55% | 3.85% | 3.84% | 3.54% |
| Diluted shares (M) | 492.7 | 464.7 | 462.8 | 461.8 | 455.6 |
| Diluted EPS | 14.10 | 5.98 | 8.94 | 8.86 | 8.13 |
| — cross-check | 14.10 ✓ | 5.98 ✓ | 8.94 ✓ | 8.86 ✓ | 8.13 ✓ |

### Cash flow statement

| Line | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---:|---:|---:|---:|---:|
| CFO | 8,625 | 4,018 | 8,621 | 7,367 | 6,562 |
| CFI | (3,154) | (5,504) | (4,760) | (2,860) | (3,649) |
| CFF | (8,071) | (2,196) | (2,285) | (3,550) | (2,187) |
| — composition check | (2,600) | (3,682) | 1,576 | 957 | 726 |
| Net change in cash (reported) | (2,600) | (3,682) | 1,576 | 957 | 726 |
| — check vs. reported | ✓ exact | ✓ exact | ✓ exact | ✓ exact | ✓ exact |
| Capital expenditure | 3,544 | 5,528 | 4,806 | 2,891 | 3,727 |
| **Free cash flow (CFO-CapEx)** | **5,081** | **(1,510)** | **3,815** | **4,476** | **2,835** |
| D&A (CFO add-back) | 2,642 | 2,700 | 2,801 | 2,981 | 3,134 |
| Dividends paid | 1,548 | 1,836 | 2,011 | 2,046 | 2,053 |
| Share repurchases (as-filed) | 7,356 | 2,826 *(restated: 2,646)* | 0 (reported) | 1,007 | 408 |
| Debt proceeds | 1,972 | 2,625 | 0 (reported) | 741 | 1,984 |
| Debt repayments | 1,147 | 163 | 147 | 1,139 | 1,643 |

### Balance sheet / working capital

Every year below is now an **authoritative** primary-filing instant (no
BLOCKED years remain).

| Line (fiscal year-end) | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---:|---:|---:|---:|---:|
| Cash and equivalents | 5,911 | 2,229 | 3,805 | 4,762 | 5,488 |
| Inventory | 13,902 | 13,499 | 11,886 | 12,740 | 12,304 |
| Accounts payable | 15,478 | 13,487 | 12,098 | 13,053 | 12,622 |
| LTD + capital leases, noncurrent | 13,549 | 16,009 | 14,922 | 14,304 | 14,326 |
| LTD + capital leases, current | 171 | 130 | 1,116 | 1,636 | 2,130 |
| **Total debt (BS carrying value)** | **13,720** | **16,139** | **16,038** | **15,940** | **16,456** |
| **Net debt** (total debt − cash) | **7,809** | **13,910** | **12,233** | **11,178** | **10,968** |

### Operational drivers

| Driver | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---:|---:|---:|---:|---:|
| CapEx % revenue | 3.34% | 5.07% | 4.47% | 2.71% | 3.56% |
| CFO margin | 8.14% | 3.68% | 8.03% | 6.91% | 6.26% |
| FCF margin | 4.79% | (1.38%) | 3.55% | 4.20% | 2.71% |
| Cash conversion (CFO/NI) | 1.24x | 1.45x | 2.08x | 1.80x | 1.77x |
| Inventory % revenue | 13.12% | 12.37% | 11.07% | 11.96% | 11.74% |
| AP % cost of sales (as-filed) | 20.65% | 16.40% | 15.56% | 17.06% | 16.72% |
| Debt-to-CFO | 1.59x | 4.02x | 1.86x | 2.16x | 2.51x |
| Net-debt-to-CFO | 0.91x | 3.46x | 1.42x | 1.52x | 1.67x |
| Distributions % FCF | **174.98%** | **NOT_APPLICABLE** (FCF negative) | 52.72% | 68.16% | 86.81% |

**FY2021's distributions/FCF ratio of ~175%** is a genuine, notable data
point, not an error: FY2021 combined $1,548M in dividends with $7,356M in
share repurchases — the year's cash returned to shareholders substantially
exceeded that year's free cash flow (funded from the prior year's large
cash balance: cash fell from $8,511M to $5,911M over FY2021, consistent
with this). **FY2022's ratio remains `NOT_APPLICABLE`** under both the
as-filed and restated repurchase figures, since FY2022's FCF is negative
either way. **FY2022's debt-to-CFO (4.02x) and net-debt-to-CFO (3.46x) are
sharply elevated relative to every other year** — driven by FY2022's
unusually low CFO ($4,018M, the lowest of the five years) combined with
that year's debt issuance, not by a debt increase alone; this is flagged
as a genuine year-specific outlier, not a data error.

---

## 7. Debt reconciliation

Per the explicit instruction not to select the note-schedule total merely
because it is larger or more detailed, here is the full year-by-year
reconciliation now that all five balance sheets are authoritative:

| Fiscal year-end | BS carrying value (LTD+CapLease, total) | Finance lease liability | Debt-only carrying (BS − FinLease) | Note-schedule total (`LongTermDebt`) | Residual (note-schedule − debt-only) |
|---|---:|---:|---:|---:|---:|
| FY2021 (2022-01-29) | 13,720 | 2,075 | 11,645 | 11,568 | **-77** |
| FY2022 (2023-01-28) | 16,139 | 2,072 | 14,067 | 14,141 | **+74** |
| FY2023 (2024-02-03) | 16,038 | 2,013 | 14,025 | 14,151 | **+126** |
| FY2024 (2025-02-01) | 15,940 | 2,161 | 13,779 | 13,904 | **+125** |
| FY2025 (2026-01-31) | 16,456 | 2,113 | 14,343 | 14,398 | **+55** |

**The residual's sign flips (negative in FY2021, positive every year
since) and its magnitude is not stable as a share of debt.** This rules out
a simple, one-directional explanation like "the note schedule states gross
principal and the balance sheet nets out issuance costs" (which would
predict a consistently positive, roughly stable residual). No
`DebtInstrumentUnamortizedDiscount...`/`...IssuanceCosts`-family tag exists
in any of the five filings to resolve this directly. **This reconciliation
gap is reported as `UNAVAILABLE`, not explained away.**

Also confirmed: the text "net debt" does not appear anywhere in any of the
five filings — Target discloses no net-debt measure of its own.

**Proposed metrics (added to `config/metrics.csv` this milestone, all
`candidate_unverified`, none marking a policy decision yet):**

| Metric | Definition | Source |
|---|---|---|
| `debt_balance_sheet_carrying_value` | (documented via the existing `long_term_debt` row) BS "Long-term debt and other borrowings" line, current + noncurrent | `LongTermDebtAndCapitalLeaseObligations` (+`...Current`) |
| `finance_lease_obligations` | Finance lease liability, current + noncurrent | `FinanceLeaseLiability` |
| `debt_principal_or_note_schedule` | Debt-maturity-schedule note total | `LongTermDebt` |
| `total_interest_bearing_debt` | **Derived — definition undecided.** Option (a): `long_term_debt` (full BS carrying value including finance leases). Option (b): `long_term_debt − finance_lease_obligations` (debt excluding finance leases). | — |

The dry-run table in §6 uses **Option (a)** (`long_term_debt` = full BS
carrying value including finance leases) for `net_debt` and the
debt-to-CFO/net-debt-to-CFO drivers, since it is the only option directly
reconcilable to the audited balance sheet without an unresolved residual.
**This is a placeholder choice, not a recommendation** — reviewer decision
requested. Under Option (b), every net-debt and debt-to-CFO figure in §6
would be roughly $2.0-2.2B lower each year (subtracting finance leases);
the DCF/capacity model (a later milestone) must not mix a principal-basis
figure with a GAAP-carrying-value figure silently, whichever option is
chosen.

**Operating lease liabilities** (`OperatingLeaseLiability` /
`...Current` / `...Noncurrent`) exist as separately tagged concepts in
every filing but are **not** included in any debt definition above — GAAP
does not classify operating leases as debt, and no metrics.csv row is
proposed for them in this milestone. Flagged as a possible future
"leverage including operating leases" variant, not built here.

---

## 8. Driver dictionary

Unchanged in structure from the first version; values now extend to all
five years (§6) rather than four. The nine requested operational drivers
and the core margin/rate metrics retain their formulas, units, frequency,
sign interpretation, limitations, and forecast relevance exactly as
originally documented — only the underlying values changed (see §6), plus
two additions:

- **`debt_to_cfo` / `net_debt_to_cfo`** limitation updated: both drivers'
  values now depend on the Option (a)/(b) debt-definition choice in §7,
  not yet finalized.
- **`distributions_pct_fcf`** limitation updated: confirmed to also require
  a NOT_APPLICABLE branch even in a *positive*-FCF year if distributions
  and FCF combine to produce a ratio well above 100% that could otherwise
  read as an error (FY2021 = 175%) — the driver's documentation must state
  explicitly that a distributions/FCF ratio above 100% is a valid,
  meaningful value (funded from cash reserves or prior-year FCF), not a
  computation bug, alongside the existing NOT_APPLICABLE-on-negative-FCF
  rule.

Every driver remains a purely historical, backward-looking observation; no
driver value here is a forecast input or assumption.

---

## 9. Proposed analytical schema, including `period_facts_unified`

**Not implemented.** Presented for review per the instruction.

### Option A (recommended, safe-additive): `annual_facts` / `annual_lineage` / `annual_fact_observations`

Unchanged from the first version's Option A — a parallel table set
mirroring the existing `quarterly_facts`/`lineage`/`instant_facts` pattern,
implemented as `TableMigration`s (`CREATE TABLE IF NOT EXISTS`, no `ALTER`
of any existing table):

```sql
CREATE TABLE IF NOT EXISTS annual_facts (
    annual_fact_id     TEXT PRIMARY KEY,
    metric             TEXT NOT NULL,
    fiscal_year        INTEGER NOT NULL,
    period_start       TEXT NOT NULL,
    period_end         TEXT NOT NULL,
    days_in_period     INTEGER NOT NULL,               -- 364 or 371 (53wk)
    value_original     REAL NOT NULL,
    original_unit      TEXT NOT NULL,
    value_normalized   REAL NOT NULL,
    normalized_unit    TEXT NOT NULL DEFAULT 'USD_millions',
    basis              TEXT NOT NULL CHECK (
                            basis IN ('direct_annual', 'derived_annual', 'derived_from_quarters')
                        ),
    fact_status        TEXT NOT NULL DEFAULT 'authoritative'
                            CHECK (fact_status IN ('authoritative', 'corroborating_only')),
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
    operation          TEXT NOT NULL
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

The `annual_facts.analytical_view` column now has a **concrete, real use
case** confirmed this milestone: FY2022 and FY2023 `gross_profit` (and
their component `cost_of_sales`/`operating_expenses`) each need exactly two
rows — one `as_originally_filed`, one `latest_restated` — per the
reclassification found in §5. `annual_fact_observations.relationship =
'conflicting'` is the natural home for the restated COGS/SG&A/repurchase
values relative to the as-filed `selected` value.

### A companion column migration, newly identified this milestone: `quarterly_facts.analytical_view`

Building the `period_facts_unified` view below (needed to satisfy this
message's schema requirement) exposed a real gap: **`quarterly_facts` has
no `analytical_view` column at all** — it was never needed in Milestone 1
because no restatement had been encountered yet. It is needed now, since a
future quarterly restatement (not yet observed, but the COGS/SG&A case
proves it can happen) would have nowhere to record `as_originally_filed`
vs. `latest_restated` on the quarterly grain. Proposed as a second,
independent `ColumnMigration` (the same safe-additive pattern already used
for `filings.document_signature_date`, etc.):

```sql
ALTER TABLE quarterly_facts
    ADD COLUMN analytical_view TEXT NOT NULL DEFAULT 'as_originally_filed';
```

### A second gap identified while designing `period_facts_unified`: `instant_facts` fiscal-year labeling

`instant_facts` has no `fiscal_year` column — only `as_of_date`. Target's
fiscal year label does **not** equal the calendar year of its January/
February year-end date (e.g. `as_of_date = 2026-01-31` is **FY2025**, not
FY2026), so a naive `strftime('%Y', as_of_date)` in the view would be
**wrong**. This project already solves the same problem for balance-sheet
instants going into `quarterly_facts` via an explicit, curated
`INSTANT_QUARTER_MAP` in `src/target_cash/derive.py` (date → (fiscal_year,
fiscal_quarter), not a date-arithmetic formula, precisely because Target's
52/53-week calendar makes a formula unreliable at the edges). The same
approach is proposed here — not a new invention:

```sql
ALTER TABLE instant_facts ADD COLUMN fiscal_year INTEGER;
```

populated at write time from the same kind of explicit, curated mapping
already used for `quarterly_facts`'s point-in-time rows, extended to
annual-only instants (10-K-only balance-sheet dates that never appear in a
10-Q). **Not implemented** — presented here because the view below cannot
be written correctly without it, and it seemed more honest to surface the
gap than to paper over it with an incorrect date-arithmetic expression.

### `period_facts_unified` (read-only view, depends on the two migrations above)

```sql
CREATE VIEW IF NOT EXISTS period_facts_unified AS
SELECT
    metric,
    'quarterly'                                    AS frequency,
    fiscal_year,
    fiscal_quarter,
    period_start                                   AS start_date,
    period_end                                      AS end_date,
    value_normalized                                AS value,
    normalized_unit                                 AS unit,
    CASE basis WHEN 'point_in_time' THEN 'direct'
               WHEN 'direct_quarterly' THEN 'direct'
               ELSE 'derived' END                   AS direct_or_derived,
    analytical_view,
    NULL                                             AS validation_status  -- see note below
FROM quarterly_facts
WHERE is_current_view = 1

UNION ALL

SELECT
    metric,
    'annual'                                        AS frequency,
    fiscal_year,
    NULL                                             AS fiscal_quarter,
    period_start                                     AS start_date,
    period_end                                       AS end_date,
    value_normalized                                 AS value,
    normalized_unit                                  AS unit,
    CASE basis WHEN 'direct_annual' THEN 'direct' ELSE 'derived' END AS direct_or_derived,
    analytical_view,
    fact_status                                      AS validation_status  -- 'authoritative' | 'corroborating_only'
FROM annual_facts                                    -- proposed in this section, not yet created
WHERE is_current_view = 1

UNION ALL

SELECT
    metric,
    'instant'                                        AS frequency,
    fiscal_year,                                     -- requires the instant_facts.fiscal_year column proposed above
    NULL                                              AS fiscal_quarter,
    NULL                                              AS start_date,
    as_of_date                                        AS end_date,
    value_normalized                                  AS value,
    normalized_unit                                   AS unit,
    'direct'                                          AS direct_or_derived,  -- instant_facts are always direct-selected today
    analytical_view,
    selection_status                                  AS validation_status  -- 'safe' | 'corroborated' | 'conflicted_unresolved'
FROM instant_facts
WHERE is_current_view = 1;
```

**Honest limitation on the `validation_status` column:** neither
`quarterly_facts` nor the proposed `annual_facts` stores a per-fact
validation outcome today — `validate` computes check results at query time
from current facts, it does not write a status back onto the fact row. The
view above returns `NULL` for `quarterly_facts` rows rather than inventing
a column that does not exist; `annual_facts.fact_status` and
`instant_facts.selection_status` are repurposed for this column because
they are the closest existing per-fact status fields, not because they are
a perfect match for "validation status" in the sense item 5 of the original
request meant. Closing this gap properly (a real per-fact validation-status
column, populated by `validate`) is a larger design question deferred to
when this view's actual query patterns are known — not decided here.

**Recommendation, unchanged: Option A** for `annual_facts`, plus the two
companion column migrations above (`quarterly_facts.analytical_view`,
`instant_facts.fiscal_year`) needed to make `period_facts_unified`
correct. Reviewer decision requested before any implementation.

---

## 10. Validation plan and dry-run results

Reassessed against the newly authoritative sources. Classification:
**PASS** / **FAIL** / **BLOCKED** / **UNAVAILABLE** / **NOT_APPLICABLE**.

| # | Validation | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---|---|---|---|---|---|
| 1 | Income-statement arithmetic | PASS | PASS (as-filed) | PASS (as-filed) | PASS | PASS |
| 2 | Pretax-income bridge | PASS | PASS | PASS | PASS | PASS |
| 3 | Effective tax rate reasonableness | PASS (22.02%) | PASS (18.67%) | PASS (21.88%) | PASS (22.24%) | PASS (22.28%) |
| 4 | Gross-profit derivation consistency | PASS | PASS (two valid values, both retained) | PASS (two valid values, both retained) | PASS | PASS |
| 5 | CFO reconciliation (full indirect method) | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE |
| 6 | FCF calculation | PASS | PASS | PASS | PASS | PASS |
| 7a | Cash movement (beginning+net change=ending) | PASS | PASS | PASS | PASS | PASS |
| 7b | Cash-flow composition | PASS (exact) | PASS (exact) | PASS (exact) | PASS (exact) | PASS (exact) |
| 8 | Debt roll-forward (exact) | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE |
| 8b | Debt reconciliation (BS vs. note-schedule vs. finance leases) | **FAIL** (unexplained -77 residual) | **FAIL** (+74) | **FAIL** (+126) | **FAIL** (+125) | **FAIL** (+55) |
| 9 | Annual-vs-quarter agreement, FY2025 | — | — | — | — | PASS (CFO/CFI/CFF/net-change, from Milestone 1) / UNAVAILABLE (IS lines) |
| 10 | Balance-sheet instant authority | PASS (authoritative) | PASS (authoritative) | PASS (authoritative) | PASS | PASS |
| 11 | Direct-vs-derived status recorded | PASS | PASS | PASS | PASS | PASS |
| 12 | Lineage completeness | N/A — nothing persisted | N/A | N/A | N/A | N/A |
| 13 | 53-week-year disclosure, no invented adjustment | N/A | N/A | PASS (verbatim, now from primary source) | N/A | N/A |
| 14 (new) | Restatement/reclassification identified and both values retained | N/A | PASS (COGS/SG&A, repurchases) | PASS (COGS/SG&A) | N/A | N/A |
| 15 (new) | Authority correctly attributed (not comparative-only) | PASS | PASS | PASS | PASS | PASS |

**Item 8b is a new, explicit `FAIL`** — this milestone's most important
validation-plan change. The debt reconciliation does not close in any
year, and unlike the CFO-reconciliation `UNAVAILABLE` items (where the
needed tags simply are not mapped yet), this is a case where **all the
relevant tags are mapped and the numbers still do not reconcile**,
warranting a `FAIL` rather than `UNAVAILABLE` per the validation-status
taxonomy's own distinction (`UNAVAILABLE` = independent evidence doesn't
exist; `FAIL` = it exists and disagrees).

---

## Tests executed

```
python -m pytest tests/ -q
```

Result: **148 passed**, 0 failed — both before and after this milestone's
`config/metrics.csv` additions (three new candidate debt rows) and the
three-filing ingestion. `normalize` (dry-run) re-run after every change;
`quarterly_facts_in_db`/`instant_facts_in_db` unchanged at 28/10 throughout,
confirming nothing was persisted. Idempotency re-confirmed: a second
`fetch` for an already-registered accession is refused; a second
`normalize` inserts zero new raw facts.

---

## Git diff summary

Files changed this correction pass:

- `config/metrics.csv` — tag-migration notes added to `interest_expense`,
  `net_income`; reclassification note added to `share_repurchases`;
  full reconciliation note added to `long_term_debt`; three new candidate
  rows added (`finance_lease_obligations`, `debt_principal_or_note_schedule`,
  `total_interest_bearing_debt`). All rows remain `candidate_unverified`.
- `docs/sources.csv` — three new filing records (FY2023, FY2022, FY2021
  10-Ks), appended via `target_cash.cli fetch --mode manual`, not by hand.
- `data/raw/` — three new cached source files (`tgt-20240203.htm`,
  `tgt-20230128.htm`, `tgt-20220129.htm`). Not committed to git (gitignored,
  same as every other cached filing).
- `data/curated/target_cash.db` (gitignored, not committed) — `raw_facts`
  grew from 688 to 1113; `quarterly_facts`/`instant_facts`/`lineage` are
  **unchanged** (28/10/45 respectively) — nothing new was persisted.
- `docs/decisions.md` — methodology-correction entry (striking the FY2023
  permanence error) and a full findings entry (reclassifications, tag
  migrations, debt reconciliation).
- `docs/limitations.md` — corrected to remove the erroneous FY2023-permanent
  claim; new entries for the reclassifications, tag migrations, and debt
  reconciliation gap.
- `docs/milestone_2_proposal.md` — this document, substantially revised.

No schema was implemented. No annual analytical fact was persisted.

---

## Summary and stop point

The full five-year authoritative filing set is now in hand. This document
corrects the FY2023 chronology error, reclassifies every FY2021-FY2023
finding from "comparative-only" to "authoritative," and surfaces four new,
real findings (two reclassifications, two tag migrations, one unresolved
debt-reconciliation gap) that only became visible once each year was
checked against its own primary filing. **Still nothing has been persisted,
no schema has been implemented, and no mapping has been marked reviewed.**
Awaiting reviewer decisions on:

1. Which COGS/SG&A split (`as_originally_filed` vs. `latest_restated`) is
   the project's default view for FY2022/FY2023 `gross_profit` (both are
   retained either way).
2. The `total_interest_bearing_debt` definition (Option (a) vs. (b), §7).
3. The proposed schema (`annual_facts`/`annual_lineage`/
   `annual_fact_observations`, plus the two companion column migrations
   needed for `period_facts_unified`).

No forecasting, DCF, Excel, Power BI, or website work has begun.
