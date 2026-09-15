# Milestone 2 Proposal: Five-Year Historical Financial Model and Driver Architecture

**Status: SECOND REVISION after reviewer-directed corrections.** Nothing in
this milestone has been persisted as an annual analytical fact. No schema
has been implemented. No mapping below is marked `reviewed`. No
forecasting, DCF, Excel, Power BI, or website work has begun.

## What changed in this revision

The reviewer accepted the five-year ingestion and the four reclassification/
tag-migration findings from the previous revision, then directed six
corrections, all applied here:

1. **Analytical-view policy formalized** (`AS_ORIGINALLY_FILED` /
   `LATEST_RESTATED`), with the COGS/SG&A reclassification demonstrated
   under both views explicitly (§1).
2. **Share-repurchase reclassification re-examined with exact fact IDs** —
   this found a **third instance** the first pass missed: FY2021 is also
   reclassified, not just FY2022 (§2).
3. **Interest-expense equivalence investigated with full evidence**, then
   approved as a **versioned concept-equivalence rule**, not a tag
   overwrite (§3).
4. **Net-income equivalence investigated, not assumed** — approved only for
   FY2021, with a documented, evidence-backed limitation (§4).
5. **Debt classification corrected**: the prior blanket `FAIL` is wrong.
   Direct note-schedule-vs-carrying-value equality is `NOT_APPLICABLE`; the
   real bridge is `BLOCKED` (a required disclosure doesn't exist), not
   `FAIL` (§5). Nine explicitly-named debt metrics replace the prior
   ambiguous ones.
6. **Net-debt relabeled** — no formula here is called "Target-reported,"
   since Target discloses no net-debt measure of its own (§6).
7. **Schema refined**: `instant_facts.fiscal_year` withdrawn per the
   reviewer's objection to inferring fiscal years from calendar dates even
   via a stored column; replaced with a proposed `fiscal_calendar`
   reference table joined by the unified view (§7).

---

## Table of contents

1. [Analytical-view policy and the COGS/SG&A demonstration](#1-analytical-view-policy)
2. [Share-repurchase reclassification — full evidence](#2-share-repurchase-reclassification)
3. [Interest-expense concept equivalence](#3-interest-expense-equivalence)
4. [Net-income concept equivalence](#4-net-income-equivalence)
5. [Debt classification, corrected](#5-debt-classification)
6. [Net-debt naming](#6-net-debt-naming)
7. [Schema: final DDL and migration order](#7-schema)
8. [Five-year mapping matrix](#8-mapping-matrix)
9. [Annual historical dry-run table, both views](#9-dry-run-table)
10. [Driver dictionary](#10-driver-dictionary)
11. [Validation plan and results](#11-validation-plan)
12. [Tests executed](#tests-executed)
13. [Git diff summary](#git-diff-summary)

---

## 1. Analytical-view policy

Two views, formally defined and both retained permanently — neither ever
overwrites the other:

| View | Definition |
|---|---|
| **`AS_ORIGINALLY_FILED`** | The metric value in the filing for which that fiscal year was the primary reporting period. Preserves management's original classification at that information date. |
| **`LATEST_RESTATED`** | The value from the most recent verified later filing that presents the same prior year under a revised classification. Becomes the default comparison/forecast-training view once a later milestone needs one. |

Every annual canonical fact retains `selected` (the view's own value),
`corroborating` (an agreeing observation from another filing),
`restated`/`conflicting` (a disagreeing observation from a later filing),
and full source lineage — this is exactly what the proposed
`annual_fact_observations.relationship` column (§7) is for.

### COGS/SG&A demonstration, both years, both views

**FY2022:**

| | Cost of sales | SG&A | Combined (unchanged) |
|---|---:|---:|---:|
| AS_ORIGINALLY_FILED (FY2022 10-K, its own primary year) | 82,229 | 20,658 | 102,887 |
| LATEST_RESTATED (FY2024 10-K's FY2022 comparative) | 82,306 | 20,581 | 102,887 |
| **Reclassification** | **+77** | **-77** | **0** |

**FY2023:**

| | Cost of sales | SG&A | Combined (unchanged) |
|---|---:|---:|---:|
| AS_ORIGINALLY_FILED (FY2023 10-K, its own primary year) | 77,736 | 21,554 | 99,290 |
| LATEST_RESTATED (FY2024/FY2025 10-K's FY2023 comparative) | 77,828 | 21,462 | 99,290 |
| **Reclassification** | **+92** | **-92** | **0** |

**Operating income is unchanged in both years, under both views** (Revenue
and D&A are also unchanged; the combined COGS+SG&A total is invariant):

| | FY2022 | FY2023 |
|---|---:|---:|
| Operating income, AS_ORIGINALLY_FILED | 109,120 − 82,229 − 20,658 − 2,385 = **3,848** | 107,412 − 77,736 − 21,554 − 2,415 = **5,707** |
| Operating income, LATEST_RESTATED | 109,120 − 82,306 − 20,581 − 2,385 = **3,848** | 107,412 − 77,828 − 21,462 − 2,415 = **5,707** |

**Gross profit and gross margin, calculated separately under both views**
(this is the one line the reclassification *does* change):

| | FY2022 as-filed | FY2022 restated | FY2023 as-filed | FY2023 restated |
|---|---:|---:|---:|---:|
| Gross profit (Revenue − COGS) | 109,120 − 82,229 = **26,891** | 109,120 − 82,306 = **26,814** | 107,412 − 77,736 = **29,676** | 107,412 − 77,828 = **29,584** |
| Gross margin | **24.64%** | **24.58%** | **27.63%** | **27.55%** |

---

## 2. Share-repurchase reclassification — full evidence

Re-examining this with exact fact IDs (rather than just the aggregate
figures used in the first pass) found a **third reclassification instance**
the first pass missed: **FY2021 is also reclassified**, not only FY2022.

| Year | View | Filing | Exact fact ID | Value |
|---|---|---|---|---:|
| FY2021 | AS_ORIGINALLY_FILED | FY2021 10-K (own primary year) | `0000027419-22-000007:us-gaap:PaymentsForRepurchaseOfCommonStock:ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 7,356 |
| FY2021 | (corroborating, unchanged) | FY2022 10-K's own FY2021 comparative | `0000027419-23-000015:us-gaap:PaymentsForRepurchaseOfCommonStock:id439a75c04fa41f683ffed29c2a159fb_D20210131-20220129` | 7,356 |
| FY2021 | LATEST_RESTATED | FY2023 10-K's FY2021 comparative | `0000027419-24-000032:us-gaap:PaymentsForRepurchaseOfCommonStock:c-11` | **7,188** |
| FY2022 | AS_ORIGINALLY_FILED | FY2022 10-K (own primary year) | `0000027419-23-000015:us-gaap:PaymentsForRepurchaseOfCommonStock:icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 2,826 |
| FY2022 | LATEST_RESTATED | FY2023 10-K's FY2022 comparative (carried unchanged into FY2024 10-K) | `0000027419-24-000032:us-gaap:PaymentsForRepurchaseOfCommonStock:c-10` | **2,646** |

**Differences:** FY2021 = $168M, FY2022 = $180M. **Both reclassifications
first appear in the same filing** (the FY2023 10-K), applied to both open
comparative years simultaneously.

**Classification/presentation/correction/scope determination:** searched
both the FY2022 10-K and FY2023 10-K in full for "excise tax" and
"accelerated share repurchase" — both phrases appear (Target does disclose
using ASR arrangements as a repurchase method generally), but **no text
ties a specific dollar figure to this reclassification**. The pattern —
both prior years reclassified at once, in the filing immediately following
the fiscal year (2023) when the federal 1% excise tax on share buybacks
(Inflation Reduction Act) first applied — is *consistent with* a
retrospective classification-methodology change (e.g., separating an
excise-tax accrual or an ASR forward-contract equity component out of the
cash-paid repurchase line), but this is a plausible hypothesis, not
evidence. **Per the explicit instruction, this is not labeled an error.**
It is classified as: **an unexplained reclassification, both years'
as-originally-filed and latest-restated values retained, mechanism
undetermined.**

---

## 3. Interest-expense concept equivalence

| Year | Filing | Fact ID | Value | Context | Statement location |
|---|---|---|---|---:|---|---|
| FY2021 | FY2021 10-K (own) | `0000027419-22-000007:us-gaap:InterestExpense:ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 421 | duration 2021-01-31..2022-01-29 | Statement of Operations, "Net interest expense" |
| FY2022 | FY2022 10-K (own) | `0000027419-23-000015:us-gaap:InterestExpense:icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 478 | duration 2022-01-30..2023-01-28 | same |
| FY2023 | FY2023 10-K (own) | `0000027419-24-000032:us-gaap:InterestExpense:c-1` | 502 | duration 2023-01-29..2024-02-03 | same |
| FY2024 | FY2024 10-K (own) | `0000027419-25-000018:us-gaap:InterestExpenseNonoperating:c-1` | 411 | duration 2024-02-04..2025-02-01 | same |
| FY2025 | FY2025 10-K (own) | `0000027419-26-000016:us-gaap:InterestExpenseNonoperating:c-1` | 445 | duration 2025-02-02..2026-01-31 | same |

**Accounting definition** (identical statement label in every filing, "Net
interest expense"): interest expense on outstanding debt, net of
capitalized interest and interest income, presented as one line between
Operating income and Net other income.

**Competing concepts checked and rejected in every filing:**
`us-gaap:FinanceLeaseInterestExpense` (a narrower sub-component: interest
on finance leases only, not the aggregate net interest line — present
separately in the filings, never a candidate for the aggregate) and
`us-gaap:InterestPaidNet` (a cash-paid supplemental disclosure figure, an
accrual-vs-cash difference from the income-statement expense, not a
competing concept for the same line).

**Arithmetic role in the pretax-income bridge, verified exact in all 5
years:** Operating income − [this concept] + Net other income = Pretax
income (zero residual: 8,946−421+382=8,907; 3,848−478+48=3,418;
5,707−502+92=5,297; 5,566−411+106=5,261; 5,117−445+95=4,767).

**Equivalence approved**: same statement label, same accounting definition,
same competing-concept rejections, same arithmetic role, continuous values
across the rename. This is stored as a **versioned concept-equivalence
rule** (§7's `concept_equivalence_rules` table proposal), not by silently
overwriting `interest_expense`'s `candidate_xbrl_tag` cell to prefer one
tag — the underlying `config/metrics.csv` row is unchanged from the prior
revision.

---

## 4. Net-income concept equivalence

**Not automatically equated.** `us-gaap:NetIncomeLoss` has zero occurrences
in the FY2021 10-K; that filing tags "Net earnings" as
`us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic` (fact ID
`0000027419-22-000007:us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic:ia69484dcd4e4439791020018d198f9dd_D20210131-20220129`,
value 6,946M). This tag is, by definition, net income after four possible
adjustments. Each was checked against the FY2021 10-K's own tagged facts:

| Possible adjustment | Evidence found | Conclusion |
|---|---|---|
| Preferred dividends | `us-gaap:PreferredStockSharesOutstanding` and `us-gaap:PreferredStockSharesIssued`, both tagged `format="ixt:fixed-zero"` as of 2022-01-29 | Zero preferred shares outstanding → zero preferred dividends possible |
| Noncontrolling interests | "noncontrolling" occurs exactly once in the whole filing, only as a substring inside the pretax-income concept's own standard US-GAAP taxonomy name — no separate NCI value or line item anywhere | No NCI in Target's structure this period |
| Discontinued operations | `us-gaap:IncomeLossFromDiscontinuedOperationsNetOfTaxAttributableToReportingEntity` reported for FY2021 as `—` (zero); the *same tag* reports a genuine $12M for FY2019 (outside this project's window), proving the concept is actively used, not boilerplate | Confirmed real, reported zero for FY2021 |
| Participating securities | No tag or text match for "participating securit*" anywhere in the filing | None found |

**All four possible adjustments are independently confirmed zero for
FY2021.** Equivalence between `NetIncomeLossAvailableToCommonStockholdersBasic`
and the headline net-income concept is **approved for FY2021 only**, as a
Target-specific, evidence-backed exception. **This is not a general rule**
that the two XBRL concepts are interchangeable — a company with preferred
stock or NCI would show a real, material difference between them. The
limitation is stated explicitly wherever this equivalence is used: it holds
because of Target's own capital structure in FY2021, verified fact-by-fact,
not because the two concepts share a definition in general.

---

## 5. Debt classification, corrected

**The prior version's blanket `FAIL` between the note-schedule debt total
and the GAAP balance-sheet carrying value was wrong and is withdrawn.**
Direct equality between two different definitions is not a meaningful
validation target.

### Corrected metric taxonomy (supersedes the three ambiguous rows added in the prior revision, which are retained in `config/metrics.csv` marked SUPERSEDED, not deleted)

| Metric | Tag(s) | FY2025 | FY2024 | FY2023 | FY2022 | FY2021 |
|---|---|---:|---:|---:|---:|---:|
| `debt_principal_schedule` | `LongTermDebt` (note schedule, single combined value, no current/noncurrent split exists for this tag) | 14,398 | 13,904 | 14,151 | 14,141 | 11,568 |
| `long_term_debt_gaap_carrying_value` | `LongTermDebtAndCapitalLeaseObligations` (+`...Current`) | 16,456 | 15,940 | 16,038 | 16,139 | 13,720 |
| `current_portion_of_debt` (derived, excludes finance leases) | = BS current − finance lease current | 1,999 | 1,500 | 997 | **1** | 63 |
| `finance_lease_liability_current` | `FinanceLeaseLiabilityCurrent` | 131 | 136 | 119 | 129 | 108 |
| `finance_lease_liability_noncurrent` | `FinanceLeaseLiabilityNoncurrent` | 1,982 | 2,025 | 1,894 | 1,943 | 1,967 |
| `finance_lease_obligations` (= sum of the two above) | — | 2,113 | 2,161 | 2,013 | 2,072 | 2,075 |
| `unamortized_discount_premium_and_issuance_cost` | *(no tag exists — see below)* | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| `total_debt_gaap` (= `long_term_debt_gaap_carrying_value` − `finance_lease_obligations`) | — | 14,343 | 13,779 | 14,025 | 14,067 | 11,645 |
| `valuation_net_debt` (= `total_debt_gaap` − cash) | — | 8,855 | 9,017 | 10,220 | 11,838 | 5,734 |
| `adjusted_net_debt_including_finance_leases` (= `long_term_debt_gaap_carrying_value` − cash) | — | 10,968 | 11,178 | 12,233 | 13,910 | 7,809 |

**FY2022's `current_portion_of_debt` of just $1M is a genuine, notable data
point** (130 total current BS line, 129 of which is finance leases that
year) — not a computation error.

### The bridge, and why it is BLOCKED, not FAIL

Requested bridge:

```
Debt principal (debt_principal_schedule)
  ± unamortized premium or discount
  − unamortized issuance costs
  ± other disclosed carrying adjustments
= GAAP debt carrying value before separately presented lease liabilities (total_debt_gaap)
```

| Fiscal year-end | `debt_principal_schedule` | `total_debt_gaap` | Unexplained gap |
|---|---:|---:|---:|
| FY2021 | 11,568 | 11,645 | **-77** |
| FY2022 | 14,141 | 14,067 | **+74** |
| FY2023 | 14,151 | 14,025 | **+126** |
| FY2024 | 13,904 | 13,779 | **+125** |
| FY2025 | 14,398 | 14,343 | **+55** |

An exhaustive tag scan of all 5 filings for every `DebtInstrumentUnamortized*`
and `UnamortizedDebt*` concept, plus a text search for "unamortized"
anywhere near the debt disclosures, returned **zero occurrences in every
filing**. The middle two bridge lines have no disclosed value to plug in —
not a zero, an absence. **The bridge is therefore `BLOCKED`** (a required
adjustment is unavailable), not `FAIL` (which requires every component to
exist and the arithmetic to still disagree). **The residual is reported
above, not plugged, forced to zero, or explained away.**

### Status summary for this section

| Check | Status |
|---|---|
| Direct equality, `debt_principal_schedule` = `long_term_debt_gaap_carrying_value` | **NOT_APPLICABLE** (different definitions by design) |
| Full bridge, principal → GAAP carrying value | **BLOCKED** (required disclosure absent in all 5 filings) |
| Current + noncurrent reconciliation, finance leases | **PASS** (exact in all 5 years) |
| Current + noncurrent reconciliation, BS carrying-value line | **PASS** (exact in all 5 years, by construction) |

---

## 6. Net-debt naming

No formula in this project is labeled "Target-reported Net Debt" or
similar — Target discloses no net-debt measure of its own anywhere in any
of the 5 filings (confirmed again this round by exhaustive text search).

| Label | Definition | Supports |
|---|---|---|
| `valuation_net_debt` | `total_debt_gaap` (debt excluding finance leases) − cash and cash equivalents (Target's balance-sheet cash line already includes any short-term investments; no separate short-term-investments line exists) | DCF enterprise-to-equity bridge (a later milestone): the standard "debt-like obligations, excluding operating items like leases, net of cash" input |
| `target_defined_net_debt` | **Structurally empty** — there is nothing to populate this with; documented here only to make explicit that this project never invents a "Target-defined" figure Target itself does not disclose | N/A |
| `adjusted_net_debt_including_finance_leases` | `valuation_net_debt` + `finance_lease_obligations` (equivalently, `long_term_debt_gaap_carrying_value` − cash) | Leverage analysis and investment-capacity analysis (a later milestone): a ratings-agency-style adjusted view that folds lease obligations back into leverage |

---

## 7. Schema: final DDL and migration order

**None of the following is implemented.** Presented for review, in the
order it would be applied if approved.

### Migration 1 (`TableMigration`): `annual_facts` / `annual_lineage` / `annual_fact_observations`

Unchanged from the prior revision — approved by the reviewer this round.

```sql
CREATE TABLE IF NOT EXISTS annual_facts (
    annual_fact_id     TEXT PRIMARY KEY,
    metric             TEXT NOT NULL,
    fiscal_year        INTEGER NOT NULL,
    period_start       TEXT NOT NULL,
    period_end         TEXT NOT NULL,
    days_in_period     INTEGER NOT NULL,
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
    relationship                TEXT NOT NULL CHECK (relationship IN ('selected', 'corroborating', 'restated', 'conflicting')),
    value_original              REAL NOT NULL,
    difference_from_selected    REAL,
    note                        TEXT
);
```

(`relationship` gains `'restated'` alongside the existing
`instant_fact_observations` vocabulary's `'selected'`/`'corroborating'`/
`'conflicting'`, to distinguish a same-value-different-vintage corroboration
from an actually-different-value restatement like the COGS/SG&A case.)

### Migration 2 (`ColumnMigration`): `quarterly_facts.analytical_view`

Unchanged from the prior revision, approved this round:

```sql
ALTER TABLE quarterly_facts
    ADD COLUMN analytical_view TEXT NOT NULL DEFAULT 'as_originally_filed';
```

### Migration 3 (`TableMigration`): `fiscal_calendar` — replaces the withdrawn `instant_facts.fiscal_year` proposal

The reviewer correctly rejected inferring Target's fiscal year from a
calendar date even via a stored column, since the mapping is genuinely
irregular (52 vs. 53 weeks) and this project already solves the same
problem elsewhere via an explicit, curated table
(`INSTANT_QUARTER_MAP` in `src/target_cash/derive.py`), not a formula.
`fiscal_calendar` generalizes that same approach into a reusable reference
table other tables and views can join against:

```sql
CREATE TABLE IF NOT EXISTS fiscal_calendar (
    fiscal_year          INTEGER NOT NULL,
    fiscal_quarter        INTEGER,                    -- NULL = annual-grain row
    period_start           TEXT NOT NULL,
    period_end              TEXT NOT NULL,
    week_count               INTEGER NOT NULL,
    is_53_week_year           INTEGER NOT NULL DEFAULT 0,
    authority_accession       TEXT REFERENCES filings(accession_number),  -- NULL if not yet held
    PRIMARY KEY (fiscal_year, fiscal_quarter)
);
```

**Populated with real, confirmed data** (annual grain, all verified this
milestone and the last):

| fiscal_year | fiscal_quarter | period_start | period_end | week_count | is_53_week_year | authority_accession |
|---|---|---|---|---:|---|---|
| 2019 | NULL | 2019-02-03 | 2020-02-01 | 52 | 0 | *(not held — comparative only)* |
| 2020 | NULL | 2020-02-02 | 2021-01-30 | 52 | 0 | *(not held — comparative only)* |
| 2021 | NULL | 2021-01-31 | 2022-01-29 | 52 | 0 | `0000027419-22-000007` |
| 2022 | NULL | 2022-01-30 | 2023-01-28 | 52 | 0 | `0000027419-23-000015` |
| 2023 | NULL | 2023-01-29 | 2024-02-03 | **53** | **1** | `0000027419-24-000032` |
| 2024 | NULL | 2024-02-04 | 2025-02-01 | 52 | 0 | `0000027419-25-000018` |
| 2025 | NULL | 2025-02-02 | 2026-01-31 | 52 | 0 | `0000027419-26-000016` |

Quarterly-grain rows are populated only for FY2025 (from the already-
ingested 10-Qs, reusing the exact dates already in `quarterly_facts`);
FY2021-FY2024 quarterly rows are **left absent, not fabricated** — those
years' 10-Qs are not yet ingested, so their exact quarter boundaries are
not confirmed from a primary source. A query against `fiscal_calendar` for
those quarters returns nothing, which is the correct, honest behavior
(BLOCKED via absence, not a guessed date).

### Migration 4 (`TableMigration`): `concept_equivalence_rules`

New this revision — the versioned-equivalence mechanism §3 and §4 require,
so a tag equivalence is never expressed as a silent, destructive edit to
`config/metrics.csv`'s single `candidate_xbrl_tag` cell:

```sql
CREATE TABLE IF NOT EXISTS concept_equivalence_rules (
    rule_id                TEXT PRIMARY KEY,
    rule_version           TEXT NOT NULL,
    canonical_metric       TEXT NOT NULL,               -- e.g. 'interest_expense'
    taxonomy               TEXT NOT NULL DEFAULT 'us-gaap',
    tag_a                  TEXT NOT NULL,
    tag_b                  TEXT NOT NULL,
    equivalence_scope       TEXT NOT NULL,                -- e.g. 'entity-wide' or 'fiscal_year=2021'
    evidence_summary         TEXT NOT NULL,
    limitation                TEXT,                          -- required if scope is narrower than entity-wide
    approved_by                TEXT,
    approved_at                TEXT,
    superseded_by_rule_id       TEXT REFERENCES concept_equivalence_rules(rule_id)
);
```

Rows this milestone would insert if approved (not inserted — schema not
implemented):

| rule_id | canonical_metric | tag_a | tag_b | scope | limitation |
|---|---|---|---|---|---|
| `rule_interest_expense_v1` | `interest_expense` | `InterestExpense` | `InterestExpenseNonoperating` | entity-wide | none — full equivalence, all years verified |
| `rule_net_income_v1` | `net_income` | `NetIncomeLossAvailableToCommonStockholdersBasic` | `NetIncomeLoss` | `fiscal_year=2021` only | Holds only because Target had zero preferred shares, no NCI, zero discontinued-ops for FY2021 specifically — not a general equivalence |

### Migration 5 (read-only view): `period_facts_unified`

```sql
CREATE VIEW IF NOT EXISTS period_facts_unified AS
SELECT
    qf.metric,
    'quarterly'                                    AS frequency,
    qf.fiscal_year,
    qf.fiscal_quarter,
    qf.period_start                                AS start_date,
    qf.period_end                                   AS end_date,
    qf.value_normalized                             AS value,
    qf.normalized_unit                              AS unit,
    CASE qf.basis WHEN 'point_in_time' THEN 'direct'
                  WHEN 'direct_quarterly' THEN 'direct'
                  ELSE 'derived' END                AS direct_or_derived,
    qf.analytical_view,
    NULL                                            AS validation_status
FROM quarterly_facts qf
WHERE qf.is_current_view = 1

UNION ALL

SELECT
    af.metric,
    'annual'                                        AS frequency,
    af.fiscal_year,
    NULL                                             AS fiscal_quarter,
    af.period_start                                  AS start_date,
    af.period_end                                     AS end_date,
    af.value_normalized                               AS value,
    af.normalized_unit                                 AS unit,
    CASE af.basis WHEN 'direct_annual' THEN 'direct' ELSE 'derived' END AS direct_or_derived,
    af.analytical_view,
    af.fact_status                                     AS validation_status
FROM annual_facts af
WHERE af.is_current_view = 1

UNION ALL

SELECT
    inf.metric,
    'instant'                                         AS frequency,
    fc.fiscal_year,                                    -- from the explicit fiscal_calendar join, never inferred
    fc.fiscal_quarter,
    NULL                                                AS start_date,
    inf.as_of_date                                       AS end_date,
    inf.value_normalized                                  AS value,
    inf.normalized_unit                                    AS unit,
    'direct'                                                AS direct_or_derived,
    inf.analytical_view,
    inf.selection_status                                     AS validation_status
FROM instant_facts inf
LEFT JOIN fiscal_calendar fc ON fc.period_end = inf.as_of_date
WHERE inf.is_current_view = 1;
```

**Honest limitation carried forward:** the `LEFT JOIN` means an
`instant_facts` row whose `as_of_date` is not yet in `fiscal_calendar`
(e.g. a future balance-sheet date not yet added) returns `NULL` for
`fiscal_year`/`fiscal_quarter` rather than a guessed value — visibly
absent, not silently wrong. `validation_status` still repurposes
`fact_status`/`selection_status` as the closest existing per-fact status
columns, as noted in the prior revision; a true per-fact validation-status
column remains a deferred design question.

**Migration order, if approved:** 1 → 2 → 3 → 4 → 5 (the view in migration
5 depends on `annual_facts`, `quarterly_facts.analytical_view`, and
`fiscal_calendar` all existing first; `concept_equivalence_rules` has no
dependency and could run at any point but is grouped fourth for narrative
clarity). All five are additive (`CREATE TABLE IF NOT EXISTS` / `ALTER
TABLE ADD COLUMN` / `CREATE VIEW IF NOT EXISTS`) — no existing table's
rows are touched, consistent with every migration applied in this project
so far.

---

## 8. Five-year mapping matrix

| Metric | FY2021 tag (own 10-K) | FY2022 tag (own 10-K) | FY2023 tag (own 10-K) | FY2024/FY2025 tag | Consistency finding |
|---|---|---|---|---|---|
| `revenue` | `RevenueFromContractWithCustomerExcludingAssessedTax` | same | same | same | Fully consistent across all 5 filings. |
| `cost_of_sales` | `CostOfGoodsAndServicesSold` | same | same | same | Tag consistent; **value for FY2022/FY2023 differs by vintage** — see §1. |
| `gross_profit` | *(none — derived)* | *(none)* | *(none)* | *(none)* | Confirmed absent in all 5 filings. Always derived; two values (as-filed/restated) for FY2022/FY2023. |
| `operating_expenses` (SG&A) | `SellingGeneralAndAdministrativeExpense` | same | same | same | Tag consistent; **value for FY2022/FY2023 differs by vintage** — see §1. |
| `depreciation_amortization_opex` | `DepreciationAndAmortization` | same | same | same | Fully consistent. |
| `operating_income` | `OperatingIncomeLoss` | same | same | same | Fully consistent; unaffected by the COGS/SG&A reclassification. |
| `interest_expense` | `InterestExpense` | `InterestExpense` | `InterestExpense` | `InterestExpenseNonoperating` | **Tag migration**, investigated and approved as a versioned equivalence — see §3. |
| `net_other_income` | `OtherNonoperatingIncomeExpense` | same | same | same | Fully consistent. |
| `pretax_income` | `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | same | same | same | Fully consistent; bridge exact in all 5 years. |
| `income_tax_expense` | `IncomeTaxExpenseBenefit` | same | same | same | Fully consistent. |
| `net_income` | `NetIncomeLossAvailableToCommonStockholdersBasic` | `NetIncomeLoss` | `NetIncomeLoss` | `NetIncomeLoss` | **Tag migration**, investigated and approved for FY2021 only with a documented limitation — see §4. |
| `diluted_eps`, `diluted_shares` | `EarningsPerShareDiluted`, `WeightedAverageNumberOfDilutedSharesOutstanding` | same | same | same | Fully consistent; EPS reproduces to the cent in all 5 years. |
| `operating_cash_flow`, `investing_cash_flow`, `financing_cash_flow` | `NetCashProvidedByUsedIn{Operating,Investing,Financing}Activities` | same | same | same | Fully consistent; composition check exact in every year. |
| `net_change_in_cash` | `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect` | same | same | same | Fully consistent. |
| `capital_expenditure` | `PaymentsToAcquirePropertyPlantAndEquipment` | same | same | same | Fully consistent. |
| `depreciation_amortization_cfo_addback` | `DepreciationDepletionAndAmortization` | same | same | same | Fully consistent. |
| `dividends_paid` | `PaymentsOfDividendsCommonStock` | same | same | same | Fully consistent. |
| `share_repurchases` | `PaymentsForRepurchaseOfCommonStock` | same | same | same | Tag consistent; **FY2021 and FY2022 values reclassified** — see §2. FY2023's reported value is a genuine zero, not missing. |
| `debt_proceeds`, `debt_repayments` | `ProceedsFromIssuanceOfLongTermDebt`, `RepaymentsOfLongTermDebt` | same | same | same | Fully consistent. FY2023's `debt_proceeds` is a genuine reported zero. |
| `cash_and_equivalents_balance_sheet` | `CashCashEquivalentsAndShortTermInvestments` | same | same | same | Fully consistent; every year authoritative. |
| `inventory`, `accounts_payable` | `InventoryNet`, `AccountsPayableCurrent` | same | same | same | Fully consistent; every year authoritative. |
| `debt_principal_schedule` | `LongTermDebt` | same | same | same | Tag consistent; single combined value, no current/noncurrent split — see §5. |
| `long_term_debt_gaap_carrying_value` | `LongTermDebtAndCapitalLeaseObligations` (+`...Current`) | same | same | same | Tag consistent; see full debt bridge in §5. |
| `finance_lease_liability_current`, `finance_lease_liability_noncurrent` | `FinanceLeaseLiabilityCurrent`, `FinanceLeaseLiabilityNoncurrent` | same | same | same | Fully consistent in all 5 filings; sums exactly to `finance_lease_obligations`. |
| `unamortized_discount_premium_and_issuance_cost` | *(no tag exists)* | *(none)* | *(none)* | *(none)* | Confirmed absent in all 5 filings — see §5. |

---

## 9. Annual historical dry-run table, both views

All figures USD millions, from each year's own authoritative filing unless
noted. PROVISIONAL pending reviewer approval of §7's schema and §3/§4's
concept-equivalence rules.

### Income statement

| Line | FY2021 | FY2022 (as-filed) | FY2023 (as-filed) | FY2024 | FY2025 |
|---|---:|---:|---:|---:|---:|
| Revenue | 106,005 | 109,120 | 107,412 | 106,566 | 104,780 |
| Cost of sales | 74,963 | 82,229 | 77,736 | 76,502 | 75,511 |
| SG&A | 19,752 | 20,658 | 21,554 | 21,969 | 21,535 |
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

### Gross profit and margin, both views (supersedes the prior revision's single-column presentation)

| | FY2021 | FY2022 as-filed | FY2022 restated | FY2023 as-filed | FY2023 restated | FY2024 | FY2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gross profit | 31,042 | 26,891 | 26,814 | 29,676 | 29,584 | 30,064 | 29,269 |
| Gross margin | 29.28% | 24.64% | 24.58% | 27.63% | 27.55% | 28.21% | 27.94% |

### Debt and net-debt, corrected metrics (supersedes the prior revision's single "Total debt"/"Net debt" rows)

| | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---:|---:|---:|---:|---:|
| `debt_principal_schedule` | 11,568 | 14,141 | 14,151 | 13,904 | 14,398 |
| `long_term_debt_gaap_carrying_value` | 13,720 | 16,139 | 16,038 | 15,940 | 16,456 |
| `total_debt_gaap` (excl. finance leases) | 11,645 | 14,067 | 14,025 | 13,779 | 14,343 |
| `valuation_net_debt` | 5,734 | 11,838 | 10,220 | 9,017 | 8,855 |
| `adjusted_net_debt_including_finance_leases` | 7,809 | 13,910 | 12,233 | 11,178 | 10,968 |

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
| **Free cash flow (CFO−CapEx)** | **5,081** | **(1,510)** | **3,815** | **4,476** | **2,835** |
| D&A (CFO add-back) | 2,642 | 2,700 | 2,801 | 2,981 | 3,134 |
| Dividends paid | 1,548 | 1,836 | 2,011 | 2,046 | 2,053 |
| Share repurchases, as-filed | 7,356 | 2,826 | 0 (reported) | 1,007 | 408 |
| Share repurchases, latest-restated | 7,188 | 2,646 | 0 | 1,007 | 408 |
| Debt proceeds | 1,972 | 2,625 | 0 (reported) | 741 | 1,984 |
| Debt repayments | 1,147 | 163 | 147 | 1,139 | 1,643 |

### Balance sheet / working capital

Every year is an **authoritative** primary-filing instant.

| Line (fiscal year-end) | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---:|---:|---:|---:|---:|
| Cash and equivalents | 5,911 | 2,229 | 3,805 | 4,762 | 5,488 |
| Inventory | 13,902 | 13,499 | 11,886 | 12,740 | 12,304 |
| Accounts payable | 15,478 | 13,487 | 12,098 | 13,053 | 12,622 |

(Debt lines shown in the corrected table above, superseding a single
"Total debt"/"Net debt" pair.)

### Operational drivers

| Driver | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---:|---:|---:|---:|---:|
| CapEx % revenue | 3.34% | 5.07% | 4.47% | 2.71% | 3.56% |
| CFO margin | 8.14% | 3.68% | 8.03% | 6.91% | 6.26% |
| FCF margin | 4.79% | (1.38%) | 3.55% | 4.20% | 2.71% |
| Cash conversion (CFO/NI) | 1.24x | 1.45x | 2.08x | 1.80x | 1.77x |
| Inventory % revenue | 13.12% | 12.37% | 11.07% | 11.96% | 11.74% |
| AP % cost of sales (as-filed COGS) | 20.65% | 16.40% | 15.56% | 17.06% | 16.72% |
| Distributions % FCF | **174.98%** | **NOT_APPLICABLE** (FCF negative) | 52.72% | 68.16% | 86.81% |

FY2021's ~175% distributions/FCF ratio is a genuine, notable data point
(heavy buybacks funded partly from the prior year's cash balance), not an
error. FY2022 remains `NOT_APPLICABLE` under either share-repurchase
vintage, since FY2022's FCF is negative regardless.

---

## 10. Driver dictionary

Unchanged in structure. **Debt-based drivers now presented under both
definitions**, per the two-metric split in §5/§6:

| Driver | Basis | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---|---:|---:|---:|---:|---:|
| Debt-to-CFO | excl. finance leases (`total_debt_gaap`/CFO) | 1.35x | 3.50x | 1.63x | 1.87x | 2.19x |
| Debt-to-CFO | incl. finance leases (`long_term_debt_gaap_carrying_value`/CFO) | 1.59x | 4.02x | 1.86x | 2.16x | 2.51x |
| Net-debt-to-CFO | excl. finance leases (`valuation_net_debt`/CFO) | 0.66x | 2.95x | 1.19x | 1.22x | 1.35x |
| Net-debt-to-CFO | incl. finance leases (`adjusted_net_debt_including_finance_leases`/CFO) | 0.91x | 3.46x | 1.42x | 1.52x | 1.67x |

All other drivers (CapEx%Revenue, CFO margin, FCF margin, cash conversion,
inventory%Revenue, AP%COGS, distributions%FCF) are unchanged from the prior
revision. **`AP % cost of sales` for FY2022/FY2023 now has an explicit
as-filed-vs-restated note**: using as-filed COGS, FY2022 = 16.40%, FY2023 =
15.56%; using restated COGS, FY2022 = 16.39%, FY2023 = 15.54% — a
negligible difference either way, noted for completeness since COGS is the
denominator and is itself reclassification-affected.

---

## 11. Validation plan and results

Fully reassessed debt-related rows; all other rows unchanged from the prior
revision.

| # | Validation | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---|---|---|---|---|---|
| 1-4, 6, 7a-b, 9-13 | (unchanged from prior revision — income-statement/cash-flow/balance-sheet arithmetic, all PASS; CFO reconciliation UNAVAILABLE; 53-week disclosure PASS) | — | — | — | — | — |
| 8 (debt bridge, direct comparison) | **NOT_APPLICABLE** | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE |
| 8b (debt bridge, full reconciliation) | **BLOCKED** | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| 8c (finance-lease current+noncurrent reconciliation) | **PASS** | PASS | PASS | PASS | PASS |
| 8d (BS carrying-value current+noncurrent reconciliation) | **PASS** | PASS | PASS | PASS | PASS |
| 14 (reclassifications identified, both values retained) | PASS (repurchases) | PASS (repurchases, COGS/SG&A) | PASS (COGS/SG&A) | N/A | N/A |
| 15 (authority correctly attributed) | PASS | PASS | PASS | PASS | PASS |
| 16 (concept equivalence: investigated before approval, not assumed) | PASS (net_income, scoped) | — | — | PASS (interest_expense, entity-wide) | PASS (interest_expense, entity-wide) |

**Item 8's split into 8a (withdrawn — was the erroneous blanket FAIL), 8b,
8c, 8d is this revision's core correction**: no single check can capture
"does the note schedule equal the balance sheet" (`NOT_APPLICABLE`, wrong
question), "can the difference be explained" (`BLOCKED`, missing
disclosure), and "does the disclosed portion reconcile internally" (`PASS`,
it does) as one status.

---

## Tests executed

```
python -m pytest tests/ -q
```

**148 passed**, 0 failed — before and after this revision's
`config/metrics.csv` restructuring (three ambiguous rows marked SUPERSEDED,
nine explicitly-named debt rows added, share-repurchase note updated).
`normalize` (dry-run) re-run after every change:
`quarterly_facts_in_db`/`instant_facts_in_db` unchanged at 28/10 throughout
— nothing persisted. `raw_facts_stored` grew from 1113 to 1133 (the two
new granular finance-lease tags, `FinanceLeaseLiabilityCurrent`/
`...Noncurrent`, now in the scanned concept list).

---

## Git diff summary

- `config/metrics.csv` — `finance_lease_obligations`,
  `debt_principal_or_note_schedule`, `total_interest_bearing_debt` marked
  SUPERSEDED (retained, not deleted); nine new explicitly-named rows added
  (`debt_principal_schedule`, `long_term_debt_gaap_carrying_value`,
  `current_portion_of_debt`, `finance_lease_liability_current`,
  `finance_lease_liability_noncurrent`,
  `unamortized_discount_premium_and_issuance_cost`, `total_debt_gaap`,
  `valuation_net_debt`, `adjusted_net_debt_including_finance_leases`);
  `share_repurchases` note updated with the FY2021 finding and both fact
  IDs; `long_term_debt` note updated to record the NOT_APPLICABLE/BLOCKED
  correction. All rows remain `candidate_unverified`.
- `docs/decisions.md` — new entry recording the analytical-view policy,
  the FY2021 share-repurchase finding, the interest-expense and net-income
  equivalence investigations and their approval scope, and the debt/net-debt
  corrections.
- `docs/milestone_2_proposal.md` — this document, revised.

No schema was implemented. No annual analytical fact was persisted.

---

## Summary and stop point

All six reviewer-directed corrections are applied. Outstanding decisions
before implementation:

1. Whether `AS_ORIGINALLY_FILED` or `LATEST_RESTATED` is the project's
   default *display* view where only one figure fits (both are always
   retained regardless).
2. The two `concept_equivalence_rules` rows proposed in §7 (interest-expense
   entity-wide; net-income FY2021-scoped) — approve, amend, or reject.
3. The full schema (5 migrations, §7) — approve for implementation, or
   request further changes.

**Nothing has been persisted. No schema has been implemented. No mapping
has been marked reviewed. No forecasting, DCF, Excel, Power BI, or website
work has begun.**
