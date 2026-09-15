# Milestone 1 Evidence Summary

Repository setup and four-quarter data proof for Target Corporation's public
cash-flow model. This document consolidates the evidence already recorded,
entry by entry, in `docs/decisions.md` — it does not replace that log, and
where the two differ on a specific number, `docs/decisions.md`'s dated
entries are the primary record.

## 1. Objective

Establish, from Target Corporation's own SEC filings only, a reviewed,
lineage-complete, independently-validated set of FY2025 quarterly cash-flow
and D&A facts, plus point-in-time cash instants — with every mapping
decision, tolerance, and validation result evidenced against the actual
filed documents, and the whole pipeline reproducible from source documents
and code alone. No forecasting, scenario, Excel, Power BI, or website work
is in scope for this milestone.

## 2. Source inventory

All 5 registered filings, verified present and hash-matching their
manifest record (`docs/sources.csv`) as of this document:

| Accession | Form | Fiscal period end | Filed | Primary filename | Byte size | Verification status |
|---|---|---|---|---|---|---|
| 0000027419-25-000018 | 10-K | 2025-02-01 | 2025-03-12 | tgt-20250201.htm | 2,023,702 | Identity/content verified against document `dei:` tags; `filed_at` is `document_derived_candidate` (rests on the document's own signature-page date, not cross-checked against SEC submissions metadata) |
| 0000027419-25-000101 | 10-Q | 2025-05-03 | 2025-05-30 | tgt-20250503.htm | 905,500 | `sec_submissions_verified` (filed_at traced to `CIK0000027419-submissions.json`); identity/content verified against document `dei:` tags |
| 0000027419-25-000118 | 10-Q | 2025-08-02 | 2025-08-29 | tgt-20250802.htm | 1,091,380 | `sec_submissions_verified`; identity/content verified |
| 0000027419-25-000126 | 10-Q | 2025-11-01 | 2025-11-26 | tgt-20251101.htm | 1,154,612 | `sec_submissions_verified`; identity/content verified |
| 0000027419-26-000016 | 10-K | 2026-01-31 | 2026-03-11 | tgt-20260131.htm | 2,059,294 | `sec_submissions_verified`; identity/content verified |

Full SHA-256 (each verified twice: once against `docs/sources.csv`'s
manifest record, once independently recomputed just above):

- `tgt-20250201.htm`: `d079d7c1872d9c96a3752acab6a3b41758b3238f8c4a36a1406473729d632c89`
- `tgt-20250503.htm`: `311e843fc262a7581e2cfe74a50462518ee6f730ad261df3029087a126ac285a`
- `tgt-20250802.htm`: `e7f3042830970f676c97db753117042c49559a9c0b2dfbbabf2d1302bf18b2ce`
- `tgt-20251101.htm`: `7003df602996b3e3649b5eac3e409e2e0f9b024de9d24a3a7a57c28be9afb43d`
- `tgt-20260131.htm`: `20bc4552dcb1df7c0bbd837f721de931e2ab4cdd2cb2e3c147f335d41eb68a52`

Entity for all 5: Target Corporation, CIK 0000027419. Original URLs, full
SHA-256 values, and verification notes are in `docs/sources.csv` (the
manifest) and the corresponding dated entries in `docs/decisions.md`.

**Missing-source report: empty.** All 5 source documents required to
reproduce Milestone 1 are present in `data/raw/` and hash-match their
manifest record exactly (see `scripts/clean_room_rebuild.py`'s own
hash-verification step, which refuses to proceed on any mismatch).

**Recovery method.** The authoritative way to recover this project's
analytical state is **rebuilding from registered sources, configuration,
migrations, and code** (`scripts/clean_room_rebuild.py`) — not restoring
any database backup. A backup made during this session
(`docs/decisions.md`, 2026-09-15 persistence entry) is a temporary,
session-scoped scratch artifact for this session's own safety net; it is
not committed to the repository, not durable, and not the recommended
recovery path.

## 3. Mapping inventory

9 of 24 configured metrics are `reviewed` (see `config/metrics.csv` for the
full per-metric evidence notes):

| Metric | Category | XBRL tag | Concept directionality |
|---|---|---|---|
| net_other_income | flow | `us-gaap:OtherNonoperatingIncomeExpense` | positive_magnitude_inflow |
| depreciation_amortization_opex | flow | `us-gaap:DepreciationAndAmortization` | positive_magnitude_expense |
| depreciation_amortization_cfo_addback | flow | `us-gaap:DepreciationDepletionAndAmortization` | positive_magnitude_inflow |
| operating_cash_flow | flow | `us-gaap:NetCashProvidedByUsedInOperatingActivities` | signed_bidirectional |
| investing_cash_flow | flow | `us-gaap:NetCashProvidedByUsedInInvestingActivities` | signed_bidirectional |
| financing_cash_flow | flow | `us-gaap:NetCashProvidedByUsedInFinancingActivities` | signed_bidirectional |
| net_change_in_cash | flow | `us-gaap:...PeriodIncreaseDecreaseIncludingExchangeRateEffect` | signed_bidirectional |
| cash_and_equivalents_balance_sheet | point_in_time | `us-gaap:CashCashEquivalentsAndShortTermInvestments` | point_in_time_unsigned |
| cash_and_equivalents_rollforward | point_in_time | `us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | point_in_time_unsigned |

The remaining 15 metrics stay `candidate_unverified` (not derived, not
persisted): `revenue`, `cost_of_sales`, `gross_profit`, `operating_expenses`,
`operating_income`, `interest_expense`, `income_tax_expense`, `net_income`,
`inventory`, `accounts_payable`, `long_term_debt`,
`inventory_cash_adjustment`, `accounts_payable_cash_adjustment`,
`capital_expenditure`, `dividends_paid`, `share_repurchases`,
`debt_proceeds`, `debt_repayments`. No FX metric is mapped — no FX concept
exists in any of the 5 filings.

## 4. Quarterly results (FY2025, USD millions)

| Metric | Q1 | Q2 | Q3 | Q4 |
|---|---:|---:|---:|---:|
| net_other_income | 26.00 | 17.00 | 26.00 | 27.00 |
| depreciation_amortization_opex | 655.00 | 632.00 | 649.00 | 681.00 |
| depreciation_amortization_cfo_addback | 787.00 | 771.00 | 773.00 | 803.00 |
| operating_cash_flow | 275.00 | 2,083.00 | 1,127.00 | 3,077.00 |
| investing_cash_flow | -787.00 | -1,066.00 | -937.00 | -859.00 |
| financing_cash_flow | -1,363.00 | 437.00 | -709.00 | -552.00 |
| net_change_in_cash | -1,875.00 | 1,454.00 | -519.00 | 1,666.00 |

Q1 is always `direct_quarterly` (a filed fact); Q2–Q4 are
`derived_ytd_subtraction` except `depreciation_amortization_opex` Q2/Q3,
which are also directly filed. Point-in-time cash (both metrics, identical
in every period since Target discloses zero restricted cash):
2025-02-01 = 4,762.00; 2025-05-03 = 2,887.00; 2025-08-02 = 4,341.00;
2025-11-01 = 3,822.00; 2026-01-31 = 5,488.00.

## 5. Cash reconciliation

Two independent validation layers, both exact in every FY2025 quarter:

| Quarter | Beginning cash | CFO | CFI | CFF | Reported net change | Calculated ending | Reported ending | Difference |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Q1 | 4,762.00 | 275.00 | -787.00 | -1,363.00 | -1,875.00 | 2,887.00 | 2,887.00 | 0.00 |
| Q2 | 2,887.00 | 2,083.00 | -1,066.00 | 437.00 | 1,454.00 | 4,341.00 | 4,341.00 | 0.00 |
| Q3 | 4,341.00 | 1,127.00 | -937.00 | -709.00 | -519.00 | 3,822.00 | 3,822.00 | 0.00 |
| Q4 | 3,822.00 | 3,077.00 | -859.00 | -552.00 | 1,666.00 | 5,488.00 | 5,488.00 | 0.00 |

**FX**: no separate FX fact or line exists in any of the 5 filings
(exhaustive tag scan). Reported FX status: `unavailable`. Implied residual
(an arithmetic implication from already-filed facts, never an
independently reported or verified fact, never persisted as a synthetic
raw fact): **$0.00 in every quarter** — CFO+CFI+CFF reconciles exactly to
the reported net-change line with no unexplained gap.

## 6. Validation totals

`checks_run=79, checks_passed=62, checks_failed=0, checks_blocked=0, checks_unavailable=17, checks_not_applicable=0, gate_passed=true`.

## 7. Unavailable validations, and why

17 `independent_quarter_validation` results are `unavailable` — every one
because **Target never files a discrete fourth quarter, and 4 of the 7 flow
metrics never file any discrete quarter at all** (`operating_cash_flow`,
`investing_cash_flow`, `financing_cash_flow`, `net_change_in_cash` are
YTD-cumulative only in every 10-Q). Each is worded exactly "arithmetic
invariant passed; independent quarter validation unavailable" — never
silently counted as a pass, and never folded into `checks_passed` at the
top level; tracked in its own `checks_unavailable` bucket. This is a
structural property of Target's own filing calendar, not a gap in this
project's evidence.

## 8. Unresolved accounts-payable limitation

`accounts_payable` remains `candidate_unverified` and unpersisted. The
annual FY2025 gap is substantially, not fully, explained by disclosed book
overdrafts (residual narrowed from $70M to $6M at fiscal year-end — see
`docs/decisions.md`, 2026-09-15 entries). The **Q1 and Q3 FY2025 interim
gaps remain unresolved**: the 10-K only discloses book-overdraft balances
at fiscal year-end, not at interim dates, and this has not been separately
investigated against the 10-Qs' own footnotes. Not attributed to the
purchases-proxy approximation. No accounts-payable value of any kind is
persisted.

## 9. Lineage and integrity results

- Every one of the 28 persisted `quarterly_facts` rows has at least one
  `lineage` row (45 total); zero orphaned `lineage` rows (pointing to a
  nonexistent `quarterly_facts` or `raw_facts` row).
- Every one of the 10 persisted `instant_facts` rows has at least one
  `instant_fact_observations` row including exactly one `relationship='selected'`
  observation (18 total observations); zero orphaned observation rows.
- Zero duplicate `(metric, fiscal_year, fiscal_quarter)` in `quarterly_facts`;
  zero duplicate `(metric, as_of_date, accounting_basis, consolidated_scope,
  analytical_view)` in `instant_facts` — 10 rows, 10 distinct canonical keys.
- **Observation-count reconciliation** (correcting an undercount in this
  session's own prior report and one `docs/decisions.md` entry, which said
  "3 corroborating" — the database itself was always correct):

  | Metric | as_of_date | Selected | Corroborating | Conflicting | Total |
  |---|---|---:|---:|---:|---:|
  | cash_and_equivalents_balance_sheet | 2025-02-01 | 1 | 4 | 0 | 5 |
  | cash_and_equivalents_balance_sheet | 2025-05-03 | 1 | 0 | 0 | 1 |
  | cash_and_equivalents_balance_sheet | 2025-08-02 | 1 | 0 | 0 | 1 |
  | cash_and_equivalents_balance_sheet | 2025-11-01 | 1 | 0 | 0 | 1 |
  | cash_and_equivalents_balance_sheet | 2026-01-31 | 1 | 0 | 0 | 1 |
  | cash_and_equivalents_rollforward | 2025-02-01 | 1 | 4 | 0 | 5 |
  | cash_and_equivalents_rollforward | 2025-05-03 | 1 | 0 | 0 | 1 |
  | cash_and_equivalents_rollforward | 2025-08-02 | 1 | 0 | 0 | 1 |
  | cash_and_equivalents_rollforward | 2025-11-01 | 1 | 0 | 0 | 1 |
  | cash_and_equivalents_rollforward | 2026-01-31 | 1 | 0 | 0 | 1 |

  Total: 10 selected + 8 corroborating + 0 conflicting = 18, matching
  `instant_fact_observations` exactly. The opening (2025-02-01) instant's 4
  corroborating observations are the three FY2025 10-Qs plus the FY2025
  10-K's own prior-year comparative — all four, not three; the earlier
  undercount omitted the FY2025 10-K's own comparative disclosure.

## 10. Clean-room rebuild proof

Built via `scripts/clean_room_rebuild.py` in an isolated temporary
directory, from `docs/sources.csv`, `config/metrics.csv`, `config/model.yml`,
`sql/schema.sql`/`views.sql`, and the 5 cached source documents (each
hash-verified against the manifest before use) — the active database was
never read or copied.

| Metric | Expected | Clean-room actual |
|---|---:|---:|
| filings | 5 | 5 |
| raw_facts | 688 | 688 |
| quarterly_facts | 28 | 28 |
| lineage | 45 | 45 |
| instant_facts | 10 | 10 |
| instant_fact_observations | 18 | 18 |
| checks_run | 79 | 79 |
| checks_passed | 62 | 62 |
| checks_failed | 0 | 0 |
| checks_blocked | 0 | 0 |
| checks_unavailable | 17 | 17 |
| gate_passed | true | true |

Every count matches exactly; run twice independently (once via ad hoc
commands, once via the committed script) with identical results both times.

## 11. Deterministic export hashes

Computed by `scripts/compare_databases.py`, which exports each table as a
sorted, canonical-JSON list (excluding only randomly-generated UUID primary
keys and wall-clock insertion timestamps — documented in the script's own
docstring) and SHA-256-hashes the result — never a raw SQLite file hash,
since file-level byte layout is not a property of analytical content.

Deterministic canonical exports are hash-identical after documented
exclusion of nondeterministic identifiers and timestamps (active and
clean-room hash is the same value in every row — printed once):

| Export | SHA-256 (active == clean-room) |
|---|---|
| quarterly_facts | `4c45df7ae95479b13d6152e87a94508154ec391ed2be6fe846698554cdd071d5` |
| lineage | `7813dbae698b64ada3719bcbdbd851f7efb978ca0216fe1a0bd4df652b1885d4` |
| instant_facts | `399c7bffdf1f0f81f83800fcbbc06e75ce7c7c3983a8347249e5589c52e5861d` |
| instant_fact_observations | `12c83c77e22af78c27334f1ba3373c423a20d33b8718338f10776f29bc2dd76f` |
| validation_results (normalized) | `380497fe0227ee992227bd4194d8b26ff40f64a89a3d253318549e0e6d59537b` |

`validation_results` normalization additionally strips the
`qf_<12 hex chars>` random-UUID fragment that `check_balance_sheet_cash_agreement`
embeds in its free-text `detail` field — the only nondeterministic content
found in `validate`'s own JSON output.

## 12. Commands required to reproduce this milestone

```bash
# From a fresh checkout, with the 5 source documents already downloaded
# into data/raw/ (see docs/sources.csv for their original URLs):

.venv/bin/python -m target_cash.cli fetch --config config/model.yml \
    --mode manual --descriptor <descriptor.json>   # once per filing, 5 times

.venv/bin/python -m target_cash.cli normalize --config config/model.yml
.venv/bin/python -m target_cash.cli validate   --config config/model.yml
.venv/bin/python -m target_cash.cli normalize --config config/model.yml --persist-derived
.venv/bin/python -m target_cash.cli validate   --config config/model.yml

# Full reproducibility proof, in one step, from source documents alone:
.venv/bin/python scripts/clean_room_rebuild.py

# Compare any two databases' analytical content (never raw file hashes):
python3 scripts/compare_databases.py <db_a> <db_b> <validate_a.json> <validate_b.json>

# Full test suite:
.venv/bin/python -m pytest -q
```

## 13. Commit IDs

| Commit | Summary |
|---|---|
| `648770d` | Verify Target Corporation entity identity |
| `2536cb5` | Activate approved proof year, cutoff, and category-specific tolerances |
| `920a30c` | Correct validation methodology: separate arithmetic invariants from independent validation |
| `0b98336` | Extend source-compatibility checks and detect non-independent validations |
| `8b584f8` | Preserve and raw-ingest the real FY2025 10-K; activate 4 reviewed mappings |
| `eba349f` | Pre-10-Q-ingestion corrections: net-other-income review, interest-expense tag fix, safe schema migrations, consolidated-fact selection guard |
| `50af913` | Preserve and raw-ingest the three FY2025 10-Qs |
| `50842ff` | Derive quarterly_facts for the 5 reviewed metrics; surface a real cross-filing ambiguity (unauthorized persistence run, later reverted — see `docs/decisions.md`) |
| `1eaa107` | Add dry-run persistence control and wire the real validation gate |
| `432eee0` | Fix unit-mismatch bug in YTD-consistency validation checks |
| `25ecaad` | Classify unexecuted validation checks as BLOCKED, not FAILED |
| `edd5eb4` | Ingest FY2024 10-K raw facts and implement authoritative-source policy |
| `a69fcfc` | Correct FX characterization, review CFO/CFI/CFF, add instant-fact schema |
| `8925310` | Correct sign-compatibility policy; add persist_instant_facts |
| `5cd45ef` | Record Milestone 1 first analytical persistence |

Full narrative and evidence for every decision above is in
`docs/decisions.md`, appended chronologically and never rewritten.
