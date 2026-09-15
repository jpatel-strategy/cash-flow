# Milestone 2: Schema Implementation and Complete Five-Year Annual Dry Run

**Status: Schema implemented. Reference metadata seeded. No annual analytical
fact has been persisted — confirmed by direct count below.** No forecasting,
DCF, Excel, Power BI, or website work has begun.

This document is the record for the round that: (1) corrected the debt-metric
inventory miscount from `docs/milestone_2_proposal.md`, (2) built the
lease-inclusion component matrix, (3) implemented the previously-proposed
schema as real, tested migrations, (4) seeded `fiscal_calendar` and
`concept_equivalence_rules` only, and (5) ran the complete five-year annual
dry run under both analytical views via a real script against the real
database — which in turn found and corrected two real bugs and one real
mapping gap, described below.

---

## 1. Corrected debt-metric inventory

The prior document said "nine" debt metrics but listed eight. Corrected:
**eight constructed debt metrics, plus a ninth row that is a definition
placeholder, not a constructed metric.**

| # | Metric | Role |
|---|---|---|
| 1 | `debt_principal_schedule` | Note-schedule debt principal ("Total notes and debentures") |
| 2 | `long_term_debt_gaap_carrying_value` | Balance-sheet GAAP carrying value, current+noncurrent, **including** finance leases |
| 3 | `current_portion_of_debt` | Current portion **excluding** finance leases |
| 4 | `finance_lease_liability_current` | Finance lease liability, current |
| 5 | `finance_lease_liability_noncurrent` | Finance lease liability, noncurrent |
| 6 | `total_debt_gaap_excluding_separately_reported_leases` | GAAP carrying value, debt instruments only, **excluding** finance leases |
| 7 | `valuation_net_debt_excluding_leases` | Measure 6 minus cash |
| 8 | `adjusted_net_debt_including_finance_leases` | Measure 7 plus finance lease liabilities |
| **9** | **`target_defined_net_debt`** | **Definition placeholder only. Status: `UNAVAILABLE`/`NOT_REPORTED`.** Target discloses no net-debt measure of its own anywhere in any of the 5 filings. **No annual fact for this metric will ever carry a value of zero, an inferred value, or a value copied from `valuation_net_debt_excluding_leases` or any other metric** — its permanent absence of a value is the correct, honest state. |

`config/metrics.csv` corrected accordingly (see Git diff, §12).

---

## 2. Lease-inclusion component matrix

Built by reading Target's own debt-maturity-schedule note table directly
(not by tag-name pattern search — see §7 for why that distinction mattered).
The note reads, in order, for every fiscal year-end:

> "Total notes and debentures" → "Swap valuation adjustments" → "Finance
> lease liabilities" → "Less: Amounts due within one year" → "Long-term
> debt and other borrowings"

| XBRL tag | Statement label | Current/Noncurrent | Includes finance leases? | Includes operating leases? | Carrying value or principal? | Selected use |
|---|---|---|---|---|---|---|
| `us-gaap:LongTermDebt` | "Total notes and debentures" (debt note) | Combined only (no split exists) | **NO** | NO | Principal/face amount | `debt_principal_schedule` |
| `tgt:SwapValuationAdjustments` (company-extension tag) | "Swap valuation adjustments" (debt note) | Combined | N/A (not a lease item) | N/A | Fair-value-hedge carrying-value adjustment | `debt_fair_value_hedge_adjustment` |
| `us-gaap:FinanceLeaseLiabilityCurrent` / `...Noncurrent` | "Finance lease liabilities" (debt note); rolled into the combined BS caption on the face of the balance sheet | Split | **YES** (is itself the finance-lease figure) | NO | Carrying value | `finance_lease_liability_current` / `_noncurrent` |
| `us-gaap:LongTermDebtAndCapitalLeaseObligations` / `...Current` | "Long-term debt and other borrowings" / "Current portion of long-term debt and other borrowings" (face of balance sheet) | Split | **YES — confirmed** by the exact bridge in §7 | NO | GAAP carrying value | `long_term_debt_gaap_carrying_value` |
| `us-gaap:OperatingLeaseLiability` / `...Current` / `...Noncurrent` | "Operating lease liabilities" (separate balance-sheet line, never combined with the debt caption) | Split | N/A | **YES** (is itself the operating-lease figure) | Carrying value (discounted lease payments) | `operating_lease_liabilities` — held separate, **not used in any debt total this round**, per instruction |

### Measures A-E, explicitly defined

| Measure | Formula | Double-counting check |
|---|---|---|
| **A.** `total_debt_gaap_excluding_separately_reported_leases` | `long_term_debt_gaap_carrying_value − finance_lease_liabilities` | Correct because the GAAP line already includes finance leases (confirmed, §7) — subtracting removes them once, not zero, not twice. |
| **B.** `finance_lease_liabilities` | `finance_lease_liability_current + finance_lease_liability_noncurrent` | — |
| **C.** `operating_lease_liabilities` | `OperatingLeaseLiabilityCurrent + OperatingLeaseLiabilityNoncurrent` | Never added to any debt measure this round. |
| **D.** `valuation_net_debt_excluding_leases` | `A − cash_and_equivalents_balance_sheet` | — |
| **E.** `adjusted_net_debt_including_finance_leases` | `D + B` (equivalently `long_term_debt_gaap_carrying_value − cash`, since the GAAP line already contains B — **never** `long_term_debt_gaap_carrying_value + B`, which would double-count) | Verified: both formulas for E produce identical values in all 5 years (§9 table). |

---

## 3. Valuation convention

- `valuation_net_debt_excluding_leases` = interest-bearing GAAP debt
  (excluding finance and operating leases) − cash and cash equivalents −
  eligible short-term investments. (Target's balance-sheet cash line
  already includes any short-term investments; no separate line exists.)
- `adjusted_net_debt_including_finance_leases` = `valuation_net_debt_excluding_leases`
  + finance lease liabilities not already included in the excluding-leases
  measure (i.e., added exactly once).
- **The DCF enterprise-to-equity bridge (a later milestone) will use
  `valuation_net_debt_excluding_leases` by default**, unless the
  enterprise-value and cash-flow conventions are modified consistently to
  match a different net-debt definition. **No DCF is implemented this
  milestone.**

---

## 4. Schema implementation — applied DDL and migration results

All 7 migrations proposed in the prior round were implemented as real,
tested `ColumnMigration`/`TableMigration` entries in
`src/target_cash/migrations.py` (`0006` through `0012`), applied via a new
`target_cash.cli seed-reference-data` command
(`src/target_cash/reference_data.py`).

| Migration ID | Object | Kind |
|---|---|---|
| `0006_fiscal_calendar` | `fiscal_calendar` table | `TableMigration` |
| `0007_concept_equivalence_rules` | `concept_equivalence_rules` table | `TableMigration` |
| `0008_annual_facts` | `annual_facts` table | `TableMigration` |
| `0009_annual_lineage` | `annual_lineage` table | `TableMigration` |
| `0010_annual_fact_observations` | `annual_fact_observations` table | `TableMigration` |
| `0011_quarterly_facts_analytical_view` | `quarterly_facts.analytical_view` column | `ColumnMigration` |
| `0012_period_facts_unified` | `period_facts_unified` view | `TableMigration` (view) |

**Applied to the real database** (backed up first to
`db_backups/target_cash.db.before-milestone2-schema.<timestamp>`, hash
`daea2792...` matching the live database exactly before any change).
Confirmed in `_schema_migrations`: all 12 migration IDs present (the
original 5 from Milestones 1-2 plus these 7). **Idempotency confirmed**: a
second `seed-reference-data` run reports 0 newly-inserted rows for both
`fiscal_calendar` and `concept_equivalence_rules`.

**No destructive migration was used or needed** — every statement is
`CREATE TABLE IF NOT EXISTS` / `ALTER TABLE ADD COLUMN` / `CREATE VIEW IF
NOT EXISTS`.

### A real bug, found and fixed before it reached a committed state

The first draft of `period_facts_unified` joined `instant_facts` to
`fiscal_calendar` on `period_end` alone. A fiscal year-end date (e.g.
2026-01-31) is *simultaneously* that year's own annual `period_end` **and**
its Q4 `period_end` (Target's fiscal Q4 always ends exactly at fiscal
year-end) — the naive join fanned one instant fact out into **two** output
rows, violating "avoid duplicate canonical facts." Fixed by preferring the
lowest `fiscal_quarter` match (the annual sentinel `0` beats `1`-`4`).
Verified against the real database: **10 `instant_facts` rows → exactly 10
`period_facts_unified` instant rows** (not 12, the pre-fix count). Two
regression tests guard this:
`test_period_facts_unified_does_not_duplicate_an_instant_at_a_fiscal_year_end`,
`test_period_facts_unified_never_duplicates_any_instant_fact`.

### The required fiscal-year-mapping test

`test_period_facts_unified_maps_instant_to_authoritative_fiscal_year_not_calendar_year`
seeds an instant fact dated 2025-02-01 and asserts the view reports
`fiscal_year = 2024` (Target's own FY2024 year-end label), not calendar-year
2025 — passing. A companion test confirms a date with no `fiscal_calendar`
row returns `NULL`, never a guessed year.

---

## 5. Populated fiscal calendar

11 rows, all from confirmed period boundaries (7 annual, FY2019-FY2025; 4
quarterly, FY2025 only — from the already-ingested 10-Qs):

| fiscal_year | fiscal_quarter | period_start | period_end | week_count | is_53_week_year | authority_accession |
|---|---|---|---|---:|---|---|
| 2019 | annual | 2019-02-03 | 2020-02-01 | 52 | no | *(not held — comparative only)* |
| 2020 | annual | 2020-02-02 | 2021-01-30 | 52 | no | *(not held — comparative only)* |
| 2021 | annual | 2021-01-31 | 2022-01-29 | 52 | no | `0000027419-22-000007` |
| 2022 | annual | 2022-01-30 | 2023-01-28 | 52 | no | `0000027419-23-000015` |
| 2023 | annual | 2023-01-29 | 2024-02-03 | **53** | **yes** | `0000027419-24-000032` |
| 2024 | annual | 2024-02-04 | 2025-02-01 | 52 | no | `0000027419-25-000018` |
| 2025 | annual | 2025-02-02 | 2026-01-31 | 52 | no | `0000027419-26-000016` |
| 2025 | Q1 | 2025-02-02 | 2025-05-03 | 13 | no | `0000027419-25-000101` |
| 2025 | Q2 | 2025-05-04 | 2025-08-02 | 13 | no | `0000027419-25-000118` |
| 2025 | Q3 | 2025-08-03 | 2025-11-01 | 13 | no | `0000027419-25-000126` |
| 2025 | Q4 | 2025-11-02 | 2026-01-31 | 13 | no | `0000027419-26-000016` |

Non-overlap enforced by `find_period_overlaps` (checked within the annual
track and the quarterly track separately, so an annual row correctly
containing its own quarters is never flagged) — tested, and a deliberately
overlapping row is rejected before any row is written (`seed_fiscal_calendar`
raises `ValueError`, nothing partially seeds).

---

## 6. Concept-equivalence rules seeded

2 rows, both entity-scoped to Target (CIK `0000027419`) only:

| rule_id | canonical_metric | source_concept | canonical_concept | effective_fiscal_years | review_status |
|---|---|---|---|---|---|
| `rule_interest_expense_v1` | `interest_expense` | `us-gaap:InterestExpense` | `us-gaap:InterestExpenseNonoperating` | FY2021-FY2023 (source); FY2024-FY2025 (canonical) | `reviewed` |
| `rule_net_income_fy2021_v1` | `net_income` | `us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic` | `us-gaap:NetIncomeLoss` | **FY2021 only** | `reviewed` |

Full accounting rationale for each is in the seeded `accounting_rationale`
column (see `src/target_cash/reference_data.py`) and in
`docs/decisions.md`'s 2026-09-15 entries.

---

## 7. Debt bridge — corrected from `BLOCKED` to `PASS`

**The prior `BLOCKED` classification was itself a search-completeness
error, not a property of Target's disclosures.** Building the literal
bridge template required reading Target's own debt-maturity-schedule note
table directly, rather than repeating the same tag-name pattern search.
That note's middle line, "Swap valuation adjustments," is tagged
`tgt:SwapValuationAdjustments` — a **company-extension taxonomy tag**, not
`us-gaap:*`, which is exactly why the earlier scan (checking only
`us-gaap:DebtInstrumentUnamortized*`/`UnamortizedDebt*` and the word
"unamortized") never found it. It is a fair-value-hedge accounting
adjustment from interest-rate swaps on the debt — a real, different bridge
component than originally hypothesized, but the one Target actually
discloses.

**The bridge reconciles exactly in all 5 years:**

| FY | `debt_principal_schedule` | + `debt_fair_value_hedge_adjustment` | + `finance_lease_liabilities` | − current portion | = `long_term_debt_gaap_carrying_value` (noncurrent) | Reported |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | 11,568 | +77 | 2,075 | −171 | 13,549 | 13,549 ✓ |
| 2022 | 14,141 | −74 | 2,072 | −130 | 16,009 | 16,009 ✓ |
| 2023 | 14,151 | −126 | 2,013 | −1,116 | 14,922 | 14,922 ✓ |
| 2024 | 13,904 | −125 | 2,161 | −1,636 | 14,304 | 14,304 ✓ |
| 2025 | 14,398 | −55 | 2,113 | −2,130 | 14,326 | 14,326 ✓ |

Every one of these five values exactly matches the residual this project
had earlier called "unexplained." **FY2021 is the only year the adjustment
is positive** (no `sign="-"` attribute) — a fair-value hedge adjustment can
genuinely flip sign with interest-rate movements between years; reported as
a real, disclosed fact, not treated as an anomaly.

**Debt bridge validation status: `PASS` in all 5 years, in both analytical
views** (the reclassifications found this milestone never touched the debt
schedule). Direct equality between `debt_principal_schedule` and
`long_term_debt_gaap_carrying_value` **remains `NOT_APPLICABLE`** — they
are still different definitions by design; it is the *bridge*, not direct
equality, that is now proven.

---

## 8. Reclassification bridges

### FY2021 share repurchases: $7,356M → $7,188M

| View | Filing | Fact ID | Value |
|---|---|---|---:|
| AS_ORIGINALLY_FILED | FY2021 10-K (own) | `0000027419-22-000007:us-gaap:PaymentsForRepurchaseOfCommonStock:ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 7,356 |
| (corroborating, unchanged) | FY2022 10-K's own FY2021 comparative | `0000027419-23-000015:us-gaap:PaymentsForRepurchaseOfCommonStock:id439a75c04fa41f683ffed29c2a159fb_D20210131-20220129` | 7,356 |
| LATEST_RESTATED | FY2023 10-K's FY2021 comparative | `0000027419-24-000032:us-gaap:PaymentsForRepurchaseOfCommonStock:c-11` | 7,188 |

Invariant confirmed: this line feeds only `financing_cash_flow`
(unaffected — CFF is directly reported, not summed from its components in
this model) and `distributions_pct_fcf` (both values shown in §9).

### FY2022 share repurchases: $2,826M → $2,646M

| View | Filing | Fact ID | Value |
|---|---|---|---:|
| AS_ORIGINALLY_FILED | FY2022 10-K (own) | `0000027419-23-000015:us-gaap:PaymentsForRepurchaseOfCommonStock:icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 2,826 |
| LATEST_RESTATED | FY2023 10-K's FY2022 comparative (unchanged into FY2024 10-K) | `0000027419-24-000032:us-gaap:PaymentsForRepurchaseOfCommonStock:c-10` | 2,646 |

### FY2022 COGS/SG&A: $77M shift

| View | Filing | Cost of sales fact ID | SG&A fact ID | COGS | SG&A | Combined |
|---|---|---|---|---:|---:|---:|
| AS_ORIGINALLY_FILED | FY2022 10-K | `...23-000015:us-gaap:CostOfGoodsAndServicesSold:icce5194...` | `...23-000015:us-gaap:SellingGeneralAndAdministrativeExpense:icce5194...` | 82,229 | 20,658 | 102,887 |
| LATEST_RESTATED | FY2024 10-K comparative | `...25-000018:us-gaap:CostOfGoodsAndServicesSold:c-5` | `...25-000018:us-gaap:SellingGeneralAndAdministrativeExpense:c-5` | 82,306 | 20,581 | 102,887 |

Invariant confirmed: combined total unchanged (102,887 both ways);
`operating_income` unchanged (3,848 both ways, §9).

### FY2023 COGS/SG&A: $92M shift

| View | Filing | COGS | SG&A | Combined |
|---|---|---:|---:|---:|
| AS_ORIGINALLY_FILED | FY2023 10-K (own) | 77,736 | 21,554 | 99,290 |
| LATEST_RESTATED | FY2024/FY2025 10-K comparative | 77,828 | 21,462 | 99,290 |

Invariant confirmed: combined total unchanged; `operating_income` unchanged
(5,707 both ways, §9).

**Reason label for all four reclassifications, per explicit instruction:
"filing-vintage reclassification; specific cause undisclosed."** No
mechanism is asserted for any of the four — none is labeled an error.

---

## 9. Complete five-year annual dry run, both analytical views

Generated by `scripts/annual_dry_run.py`, which reads only `raw_facts` and
`fiscal_calendar` from the real database and writes nothing. All figures
USD millions unless noted (`_pct` = percent, `diluted_eps` = dollars/share,
`diluted_shares` = millions of shares). Status in parentheses.

### AS_ORIGINALLY_FILED

| Line | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---:|---:|---:|---:|---:|
| Revenue | 106,005 (DIRECT) | 109,120 (DIRECT) | 107,412 (DIRECT) | 106,566 (DIRECT) | 104,780 (DIRECT) |
| Cost of sales | 74,963 (DIRECT) | 82,229 (DIRECT) | 77,736 (DIRECT) | 76,502 (DIRECT) | 75,511 (DIRECT) |
| Gross profit | 31,042 (DERIVED) | 26,891 (DERIVED) | 29,676 (DERIVED) | 30,064 (DERIVED) | 29,269 (DERIVED) |
| Gross margin % | 29.28 (DERIVED) | 24.64 (DERIVED) | 27.63 (DERIVED) | 28.21 (DERIVED) | 27.93 (DERIVED) |
| SG&A | 19,752 (DIRECT) | 20,658 (DIRECT) | 21,554 (DIRECT) | 21,969 (DIRECT) | 21,535 (DIRECT) |
| D&A (opex) | 2,344 (DIRECT) | 2,385 (DIRECT) | 2,415 (DIRECT) | 2,529 (DIRECT) | 2,617 (DIRECT) |
| Operating income | 8,946 (DIRECT) | 3,848 (DIRECT) | 5,707 (DIRECT) | 5,566 (DIRECT) | 5,117 (DIRECT) |
| Operating margin % | 8.44 (DERIVED) | 3.53 (DERIVED) | 5.31 (DERIVED) | 5.22 (DERIVED) | 4.88 (DERIVED) |
| Interest expense | 421 (DIRECT) | 478 (DIRECT) | 502 (DIRECT) | 411 (DIRECT) | 445 (DIRECT) |
| Net other income | 382 (DIRECT) | 48 (DIRECT) | 92 (DIRECT) | 106 (DIRECT) | 95 (DIRECT) |
| Pretax income | 8,907 (DIRECT) | 3,418 (DIRECT) | 5,297 (DIRECT) | 5,261 (DIRECT) | 4,767 (DIRECT) |
| Income tax expense | 1,961 (DIRECT) | 638 (DIRECT) | 1,159 (DIRECT) | 1,170 (DIRECT) | 1,062 (DIRECT) |
| Effective tax rate % | 22.02 (DERIVED) | 18.67 (DERIVED) | 21.88 (DERIVED) | 22.24 (DERIVED) | 22.28 (DERIVED) |
| Net income | 6,946 (DIRECT) | 2,780 (DIRECT) | 4,138 (DIRECT) | 4,091 (DIRECT) | 3,705 (DIRECT) |
| Net margin % | 6.55 (DERIVED) | 2.55 (DERIVED) | 3.85 (DERIVED) | 3.84 (DERIVED) | 3.54 (DERIVED) |
| Diluted shares | 492.7 (DIRECT) | 464.7 (DIRECT) | 462.8 (DIRECT) | 461.8 (DIRECT) | 455.6 (DIRECT) |
| Diluted EPS | 14.10 (DIRECT) | 5.98 (DIRECT) | 8.94 (DIRECT) | 8.86 (DIRECT) | 8.13 (DIRECT) |
| CFO | 8,625 (DIRECT) | 4,018 (DIRECT) | 8,621 (DIRECT) | 7,367 (DIRECT) | 6,562 (DIRECT) |
| CapEx | 3,544 (DIRECT) | 5,528 (DIRECT) | 4,806 (DIRECT) | 2,891 (DIRECT) | 3,727 (DIRECT) |
| FCF | 5,081 (DERIVED) | (1,510) (DERIVED) | 3,815 (DERIVED) | 4,476 (DERIVED) | 2,835 (DERIVED) |
| FCF margin % | 4.79 (DERIVED) | (1.38) (DERIVED) | 3.55 (DERIVED) | 4.20 (DERIVED) | 2.71 (DERIVED) |
| CFI | (3,154) (DIRECT) | (5,504) (DIRECT) | (4,760) (DIRECT) | (2,860) (DIRECT) | (3,649) (DIRECT) |
| CFF | (8,071) (DIRECT) | (2,196) (DIRECT) | (2,285) (DIRECT) | (3,550) (DIRECT) | (2,187) (DIRECT) |
| Dividends | 1,548 (DIRECT) | 1,836 (DIRECT) | 2,011 (DIRECT) | 2,046 (DIRECT) | 2,053 (DIRECT) |
| Repurchases | 7,356 (DIRECT) | 2,826 (DIRECT) | 0 (DIRECT) | 1,007 (DIRECT) | 408 (DIRECT) |
| Debt issuance | 1,972 (DIRECT) | 2,625 (DIRECT) | 0 (DIRECT) | 741 (DIRECT) | 1,984 (DIRECT) |
| Debt repayments | 1,147 (DIRECT) | 163 (DIRECT) | 147 (DIRECT) | 1,139 (DIRECT) | 1,643 (DIRECT) |
| Cash | 5,911 (DIRECT) | 2,229 (DIRECT) | 3,805 (DIRECT) | 4,762 (DIRECT) | 5,488 (DIRECT) |
| Inventory | 13,902 (DIRECT) | 13,499 (DIRECT) | 11,886 (DIRECT) | 12,740 (DIRECT) | 12,304 (DIRECT) |
| Accounts payable | 15,478 (DIRECT) | 13,487 (DIRECT) | 12,098 (DIRECT) | 13,053 (DIRECT) | 12,622 (DIRECT) |
| `debt_principal_schedule` | 11,568 (DIRECT) | 14,141 (DIRECT) | 14,151 (DIRECT) | 13,904 (DIRECT) | 14,398 (DIRECT) |
| `long_term_debt_gaap_carrying_value` | 13,720 (DERIVED) | 16,139 (DERIVED) | 16,038 (DERIVED) | 15,940 (DERIVED) | 16,456 (DERIVED) |
| `total_debt_gaap_excluding_separately_reported_leases` | 11,645 (DERIVED) | 14,067 (DERIVED) | 14,025 (DERIVED) | 13,779 (DERIVED) | 14,343 (DERIVED) |
| `valuation_net_debt_excluding_leases` | 5,734 (DERIVED) | 11,838 (DERIVED) | 10,220 (DERIVED) | 9,017 (DERIVED) | 8,855 (DERIVED) |
| `adjusted_net_debt_including_finance_leases` | 7,809 (DERIVED) | 13,910 (DERIVED) | 12,233 (DERIVED) | 11,178 (DERIVED) | 10,968 (DERIVED) |
| `target_defined_net_debt` | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE |
| Debt bridge check | PASS | PASS | PASS | PASS | PASS |
| Distributions % FCF | 175.24 (DERIVED) | NOT_APPLICABLE | 52.71 (DERIVED) | 68.21 (DERIVED) | 86.81 (DERIVED) |

### LATEST_RESTATED (the default comparison view, per this round's instruction)

Identical to the table above **except**:

| Line | FY2021 | FY2022 | FY2023 |
|---|---:|---:|---:|
| Cost of sales | 74,963 (unchanged) | 82,306 (DIRECT) | 77,828 (DIRECT) |
| Gross profit | 31,042 (unchanged) | 26,814 (DERIVED) | 29,584 (DERIVED) |
| Gross margin % | 29.28 (unchanged) | 24.57 (DERIVED) | 27.54 (DERIVED) |
| SG&A | 19,752 (unchanged) | 20,581 (DIRECT) | 21,462 (DIRECT) |
| Repurchases | 7,188 (DIRECT) | 2,646 (DIRECT) | 0 (unchanged) |
| Distributions % FCF | 171.98 (DERIVED) | NOT_APPLICABLE (unchanged) | 52.71 (unchanged) |

Every other line (operating income through debt figures, and all of
FY2024/FY2025) is byte-identical between the two views — confirming the
reclassifications' invariants (§8) and that FY2024/FY2025 have no later
filing to restate against yet.

---

## 10. Validation totals

| Check | Result |
|---|---|
| Gross-profit derivation (both views, all 5 years) | PASS (10/10) |
| Operating-income bridge | PASS (5/5) |
| Pretax-income bridge | PASS (5/5) |
| Net-income bridge | PASS (5/5) |
| EPS consistency (NI/shares reproduces reported EPS) | PASS (5/5) |
| CFO/CapEx/FCF | PASS (5/5), FCF negative in FY2022 (correct, not an error) |
| Cash composition (CFO+CFI+CFF=reported net change) | PASS (5/5, exact) |
| Debt metric construction (bridge) | PASS (5/5) — see §7 |
| Fiscal-year authority | PASS (5/5 — every year has a held authority filing) |
| Analytical-view selection (as-filed vs. restated correctly diverge only where a real reclassification exists) | PASS |
| Equivalence-rule scope (interest_expense entity-wide; net_income FY2021-only, not over-applied) | PASS |
| Lineage completeness | N/A — nothing persisted yet |
| 53-week-year disclosure | PASS (FY2023, verbatim, from its own primary filing) |

## 11. Blocked / unavailable metrics

**None remain `BLOCKED`** after this round's mapping-gap fixes (§12).
**One remains `UNAVAILABLE` by design**: `target_defined_net_debt`
(Target discloses no such measure — see §1).

---

## 12. Real bugs and mapping gaps found and fixed while building this dry run

Building a real, re-runnable script against real ingested data (rather than
hand-transcribing verified numbers into markdown) surfaced four gaps in
`config/metrics.csv` that every prior round's narrative analysis had walked
around via direct HTML re-extraction, never by querying `raw_facts` itself:

1. `dividends_paid`'s `candidate_xbrl_tag` was still `PaymentsOfDividends`
   (0 occurrences in any filing) — never corrected in earlier rounds even
   though every dry-run table already used the correct
   `PaymentsOfDividendsCommonStock` value. Fixed.
2. `LongTermDebtAndCapitalLeaseObligationsCurrent` (the current-portion
   companion to the noncurrent debt tag) was only ever mentioned in another
   row's notes text, never scanned as its own concept. Added as
   `long_term_debt_gaap_carrying_value_current`.
3. `pretax_income`, `diluted_eps`, and `diluted_shares` — discussed
   extensively in every prior round's income-statement bridge tables, but
   **never actually added as `config/metrics.csv` rows** at all. Added all
   three.
4. The two legacy tags approved via `concept_equivalence_rules`
   (`InterestExpense`, `NetIncomeLossAvailableToCommonStockholdersBasic`)
   were cited by fact ID throughout prior documentation, but — because the
   versioned-equivalence design deliberately does not edit
   `interest_expense`/`net_income`'s own `candidate_xbrl_tag` cell — those
   legacy tags were never actually scanned into `raw_facts`. Added two
   scan-only rows (`interest_expense_legacy_tag`,
   `net_income_legacy_tag`) so the fact IDs already cited in
   `docs/decisions.md` are real, queryable rows, not just re-derived
   citations.

A fifth bug was in the dry-run script itself, not `config/metrics.csv`:
`diluted_eps` was being divided by 1,000,000 like every dollar-denominated
metric, producing `1.41e-05` instead of `14.10` (EPS facts are tagged
`scale=0`/unscaled, unlike every other duration metric here). Fixed with an
explicit unscaled-metric exception; caught immediately because the dry run
was actually run and its output actually inspected, not assumed correct.

`raw_facts_stored` grew from 1,147 (start of this round) to **1,293**
across these fixes — every addition is a `raw_facts` row (broad,
unreviewed evidence, per this project's Milestone 1 design), never an
`annual_facts` row.

---

## 13. Database counts — annual analytical tables confirmed empty

```
filings                     8
raw_facts                1,293
quarterly_facts             28
lineage                      45
instant_facts                10
instant_fact_observations    18
fiscal_calendar              11
concept_equivalence_rules     2
annual_facts                  0
annual_lineage                0
annual_fact_observations      0
```

Every pre-existing table's row count is unchanged except `raw_facts`
(grew only from newly-scanned concepts, per §12) — no `quarterly_facts`,
`lineage`, `instant_facts`, or `instant_fact_observations` row was added,
changed, or removed. **`annual_facts`, `annual_lineage`, and
`annual_fact_observations` are confirmed empty** — no annual analytical
fact has been persisted.

---

## 14. Tests

```
python -m pytest tests/ -q
```

**176 passed**, 0 failed. New this round: 6 migration tests (`0006`-`0012`
existence, idempotency, `fiscal_calendar` primary-key uniqueness,
`annual_facts` canonical uniqueness, `annual_lineage`'s
exactly-one-input-kind `CHECK`), 13 `reference_data` tests (seeding,
idempotency, overlap rejection, and — critically — the required
fiscal-year-mapping proof plus the two duplicate-prevention regression
tests for the bug found in §4), 1 CLI integration smoke test
(`seed-reference-data`), and 8 `annual_dry_run.py` logic tests (tag
resolution, unscaled-metric handling, derived-metric computation, the
`target_defined_net_debt` never-copied guarantee).

---

## 15. Git diff and commit

Files changed this round:

- `src/target_cash/migrations.py` — 7 new migrations (`0006`-`0012`).
- `src/target_cash/reference_data.py` — new module: `fiscal_calendar` and
  `concept_equivalence_rules` data + idempotent seed functions + period-
  overlap validation.
- `src/target_cash/cli.py` — new `seed-reference-data` subcommand.
- `scripts/annual_dry_run.py` — new: the two-view, all-metric dry-run
  script (read-only, writes nothing).
- `config/metrics.csv` — debt-metric inventory corrected (§1); lease
  component rows added (§2); `dividends_paid` tag corrected;
  `long_term_debt_gaap_carrying_value_current`, `pretax_income`,
  `diluted_eps`, `diluted_shares`, `interest_expense_legacy_tag`,
  `net_income_legacy_tag`, `debt_fair_value_hedge_adjustment` added; the
  `unamortized_discount_premium_and_issuance_cost` row's note corrected to
  reflect the real bridge component found. All rows remain
  `candidate_unverified`.
- `tests/unit/test_migrations.py` — `make_stale_db` extended with a
  `quarterly_facts` table (needed for the new `ColumnMigration`); 6 new
  tests.
- `tests/unit/test_reference_data.py` — new file, 13 tests.
- `tests/unit/test_annual_dry_run.py` — new file, 8 tests.
- `tests/integration/test_cli_smoke.py` — 1 new test
  (`seed-reference-data`).
- `docs/decisions.md` — two new entries: the accounting-policy formalization
  round, and this schema-implementation-plus-debt-bridge-correction round.
- `docs/milestone_2_proposal.md` — targeted correction to the debt-metric
  count claim, pointing here for the full corrected inventory and the
  `BLOCKED`→`PASS` debt-bridge correction.
- `docs/milestone_2_schema_and_dry_run.md` — this document.

Database (`data/curated/target_cash.db`, gitignored, not committed):
migrations applied, `fiscal_calendar`/`concept_equivalence_rules` seeded,
`raw_facts` grew to 1,293. `annual_facts`/`annual_lineage`/
`annual_fact_observations` remain empty. Backed up before migration to
`db_backups/target_cash.db.before-milestone2-schema.<timestamp>` (not
committed — gitignored, matching this project's existing backup
convention).

---

## Stop point

**No annual analytical fact has been persisted** (§13). **No forecasting,
DCF, Excel, Power BI, or website work has begun.** Outstanding decisions
for the next round: whether to authorize persistence of `annual_facts`
using the now-implemented schema, and whether the `AS_ORIGINALLY_FILED` /
`LATEST_RESTATED` default-view choice for the FY2022/FY2023 gross-profit
split should be recorded anywhere beyond this document (both values are
retained regardless of which is treated as the "headline" figure).
