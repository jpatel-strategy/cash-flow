# Known Limitations

This file is updated as limitations are discovered, not just at release. It is
part of every milestone report, not a one-time disclaimer.

## Scope boundaries (fixed by the governing roadmap)

This project is an **external, public-data case study**. It is not, and must
never be represented as:

- Target's internal forecast, budget, or consulting work performed for Target
- A recommendation to buy or sell Target securities
- Evidence that Target adopted or uses this model
- A store-level or SKU-level operating plan, or a daily treasury forecast
- A claim that a proposed investment would generate returns

## Environment limitation (Milestone 1)

This Claude Code remote execution environment cannot reach `data.sec.gov`,
`www.sec.gov`, or `investors.target.com` (blocked by network egress policy).
Historical data acquisition for Milestone 1 therefore relies on the project
owner manually downloading specific SEC URLs and uploading them into this
session, rather than this session fetching them directly. `fetch.py` still
implements a genuine HTTP client for environments where SEC access is open.

## Data coverage (Milestone 1)

- Only one complete fiscal year (4 quarters) is targeted for the first data
  gate — not yet the ~16 quarters the full project calls for.
- CIK `0000027419` is **verified** as Target Corporation (see
  docs/decisions.md, 2026-09-14 entry) via the SEC submissions file.
- XBRL tag mappings in `config/metrics.csv` are candidates from general
  US-GAAP taxonomy knowledge, marked `candidate_unverified`. Company Facts
  reconnaissance (docs/decisions.md) found real gaps a name-based guess would
  have missed — e.g. `CashAndCashEquivalentsAtCarryingValue` has zero entries
  for Target; the balance-sheet cash line is tagged differently, and multiple
  candidate cash tags currently produce identical values for reasons not yet
  confirmed from the actual statement. None of these candidates is active
  until checked against Target's actual filing statements, contexts, and sign
  conventions, per the project owner's explicit standing instruction.

## Data coverage (Milestone 2)

**Correction, 2026-09-15:** an earlier version of this section stated that
FY2021/FY2022 balance-sheet items were blocked pending the FY2022 10-K, and
that FY2023 would *permanently* lack a filing with its own primary-period
authority, including the chronologically impossible claim that FY2023 would
appear as a comparative in the FY2022 10-K (a filing that predates FY2023
and cannot contain it). Both statements were methodology errors, corrected
in `docs/decisions.md`'s 2026-09-15 methodology-correction entry. The actual
five-year authoritative filing set (FY2021-FY2025 10-Ks) is now fully
ingested; see below for what remains open.

- The full five-year authoritative filing set (FY2021 through FY2025
  10-Ks) is now ingested and hash-verified — see `docs/sources.csv` and
  `docs/milestone_2_proposal.md` §1 for the complete inventory.
- Two `config/metrics.csv` candidate tags were found to be incorrect and
  corrected in this milestone's first pass (`operating_expenses`,
  `long_term_debt`); neither is marked `reviewed`. `gross_profit` has no
  direct XBRL tag in any of the five cached filings and must always be
  derived.
- **Genuine restatements/reclassifications found** (not tag errors —
  real changes in how Target's own comparatives are presented across filing
  vintages): a COGS/SG&A reclassification affecting FY2022 ($77M) and
  FY2023 ($92M), and a share-repurchase reclassification affecting FY2022
  ($180M). Operating income, pretax income, and net income are unaffected
  in every case; derived `gross_profit` for FY2022/FY2023 depends on which
  filing vintage's split is used. Both the as-originally-filed and
  latest-restated values are retained — see `docs/decisions.md` and
  `docs/milestone_2_proposal.md` §5 for the full detail and exact figures.
- **Tag migrations found** (value continuous, no restatement): `interest_expense`
  is tagged `us-gaap:InterestExpense` in the FY2021-FY2023 10-Ks and
  `us-gaap:InterestExpenseNonoperating` from the FY2024 10-K onward;
  `net_income` is tagged `us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic`
  in the FY2021 10-K only and `us-gaap:NetIncomeLoss` from the FY2022 10-K
  onward. `config/metrics.csv`'s single-tag-per-metric column cannot express
  this; the vintage-dependent tag is documented in the mapping matrix
  instead.
- **Debt reconciliation gap, unresolved:** subtracting Target's disclosed
  finance-lease liability from the balance-sheet long-term-debt-and-capital-lease
  line does not exactly equal the separate note-schedule debt total in any
  year, and the residual's sign flips across years (not explainable as a
  simple unamortized-discount/issuance-cost effect). No tag exists in any
  filing to resolve this directly. See `docs/milestone_2_proposal.md` §6.
  Confirmed separately: Target discloses no "net debt" measure of its own
  anywhere in any of the five filings — this project's `net_debt` is
  entirely this project's own construction.

## Not yet built

Forecasting, seasonal baseline, driver model, scenarios, investment-capacity
calculation, backtesting, Excel workbook, Power BI exports, and the public
Investment Decision Room are all out of scope until their respective
milestones are authorized and their upstream gates pass.
