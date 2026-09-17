# Final Project Evidence

> **⚠️ Superseded record — read this banner before relying on any figure below.**
> This document is the original Milestone 8 closeout record. Its capacity
> results, test totals, web-verification totals, and deployment status were
> **superseded** by later semantic-audit and UI-release work:
> - Current investment-capacity evidence: [`docs/investment_capacity_correction_evidence.md`](investment_capacity_correction_evidence.md)
> - Current UI/release evidence: [`docs/ui_ux_audit.md`](ui_ux_audit.md)
> - Current public entry point: the root [`README.md`](../README.md)
>
> This file is kept as a historical record and is **not rewritten** to match
> current figures — its numbers reflect the state of the project on
> 2026-09-16, before the capacity-taxonomy corrections and the recruiter-facing
> UI rebuild.

Produced 2026-09-16, at the close of Milestone 8, as the required final
system audit before the consolidated final report. Every figure in this
document was re-verified against the live repository, database, and
test/verification-script output on this date — none is recalled from
memory or from an earlier milestone's write-up without re-checking.

## 1. Objective

Build a complete, auditable, independent FP&A case study for Target
Corporation — historical fact validation, a 3-scenario 5-year cash-flow
and investment-capacity forecast, a restrained DCF valuation, and four
presentation layers (Excel, Power BI handoff, web cockpit, recruiter
package) — entirely from public SEC filings, under a hard FY2025 10-K
information cutoff (2026-03-11), with no fabricated values, no silent
plugs, and provable (not merely asserted) absence of double counting.

## 2. Architecture

```
SEC filings (docs/sources.csv, 8 filings)
  -> raw_facts -> annual_facts/instant_facts/quarterly_facts (historical)
  -> forecast_scenarios/forecast_assumptions/forecast_facts/forecast_lineage (3B)
  -> valuation_assumptions/valuation_ufcf_facts/valuation_results (4)
  -> Excel workbook (5) | Power BI handoff (6) | web cockpit (7) | portfolio package (8)
```

SQLite (`data/curated/target_cash.db`) is the system of record. Python
3.10+, `pandas`/`pydantic`/`openpyxl` for the pipeline; vanilla HTML/CSS/
JS for the web cockpit; `formulas` (Python) and Playwright/Chromium for
independent, non-native verification of Excel and the web cockpit
respectively, since neither LibreOffice nor Power BI Desktop is
available in this build environment. See
`deliverables/portfolio_package/02_technical_architecture_summary.md`
for the full narrative.

## 3. Source inventory

8 SEC filings registered in `docs/sources.csv`, each with accession
number, filed date, period of report, source URL, and file hash:

| Accession # | Form | Period of Report |
|---|---|---|
| 0000027419-26-000016 | 10-K | 2026-01-31 (FY2025) |
| 0000027419-25-000018 | 10-K | 2025-02-01 (FY2024) |
| 0000027419-24-000032 | 10-K | 2024-02-03 (FY2023) |
| 0000027419-23-000015 | 10-K | 2023-01-28 (FY2022) |
| 0000027419-22-000007 | 10-K | 2022-01-29 (FY2021) |
| 0000027419-25-000101 | 10-Q | 2025-05-03 (FY2025 Q1) |
| 0000027419-25-000118 | 10-Q | 2025-08-02 (FY2025 Q2) |
| 0000027419-25-000126 | 10-Q | 2025-11-01 (FY2025 Q3) |

Re-verified present and hash-matched against the manifest by the
2026-09-16 clean-room rebuild (§13 below).

## 4. Historical results (unchanged from Milestones 1-2)

FY2025 reference values (latest-restated view), re-queried live from
`data/curated/target_cash.db` on 2026-09-16:

| Metric | Value |
|---|---|
| CFO | $6,562M |
| CapEx (property & equipment acquisitions only) | $3,727M |
| CFI (total investing cash flow) | $(3,649)M |
| FCF (CFO − CapEx) | $2,835M |

CapEx ($3,727M) and \|CFI\| ($3,649M) are confirmed numerically distinct
(difference $78M) — CapEx was never substituted for total investing
cash flow anywhere in this project.

**Filing-vintage reclassification** (FY2022/FY2023 cost-of-sales vs.
SG&A): confirmed present and correctly flagged in
`fact_annual_historical`/`fact_filing_vintage_comparison` exports —
FY2022 cost of sales +$77M, FY2023 +$92M, both fully offset in
operating expenses, $0 revenue impact.

488 `annual_facts` rows (FY2021-FY2025 x both analytical views x 49
metrics) are byte-identical to the clean-room rebuild (§13).

## 5. Forecast assumptions (unchanged from Milestone 3A)

19 named assumption metrics x 3 scenarios x 5 forecast years = 105
persisted `forecast_assumptions` rows (re-confirmed count, unchanged
since Milestone 3B). Each assumption carries a rationale, a historical
reference, and a source-evidence citation. Information cutoff
(2026-03-11) is present and identical on every row — no assumption cites
information beyond the FY2025 10-K.

## 6. Scenario outputs (unchanged from Milestone 3A/3B, re-verified 2026-09-16)

FY2030 terminal-year results, re-queried live:

| Scenario | Revenue | Diluted EPS | Deployable Capacity (FY2030) | Cumulative Deployable Capacity |
|---|---|---|---|---|
| Base | $110,124.8M | $8.18 | $6,315.0M | $6,315.0M |
| Upside | $121,468.7M | $13.15 | $3,241.9M | $3,241.9M |
| Downside | $92,321.2M | $2.71 | $6,087.5M | $6,087.5M |

**Scenario separation confirmed**: WACC is identical across all 3
scenarios (8.86177%, `check_wacc_scenario_invariant` PASS); operating
assumptions differ meaningfully and are never mixed across scenarios
(`zero_scenario_mixing` integrity check PASS in the forecast persistence
layer).

## 7. Investment-capacity results (Milestone 3A fix, re-verified)

The corrected formula — `cumulative_deployable_capacity(years) =
years[-1].deployable_capacity + sum(deployed)` — is confirmed still in
use (no regression): for all 3 scenarios in the current run, cumulative
capacity equals the terminal year's own balance exactly, because
`management_selected_deployment` remains $0 throughout (no discretionary
deployment has been selected this round) — consistent with, not a
contradiction of, the corrected formula. The naive (defective) `sum()`
of all 5 years' balances would instead produce a materially larger,
double-counted figure for every scenario, as already documented in the
Milestone 3A decision-log entry.

**Full source/use conservation** (identity c) and **waterfall no-
double-counting proof**: re-confirmed PASS for all 15 scenario-year
combinations via the forecast validation suite (`cumulative_capacity_no_double_counting`
and `verify_no_double_counting` checks) and via the web cockpit's live
proof banner (Milestone 7 verification, check "Capital allocation
no-double-counting proof reads OK").

## 8. Valuation results (Milestone 4, re-verified 2026-09-16)

| Scenario | WACC | Enterprise Value | Equity Value | Implied Value/Share |
|---|---|---|---|---|
| Base | 8.86% | $57,736.3M | $48,881.3M | $107.29 |
| Upside | 8.86% | $71,873.7M | $63,018.7M | $138.32 |
| Downside | 8.86% | $36,898.6M | $28,043.6M | $61.55 |

Valuation-date consistency confirmed: net debt ($8,855.0M =
$14,343.0M total debt − $5,488.0M cash) and diluted shares (455.6M) used
in every scenario's bridge are FY2025 actuals, never a forecast-year
projection (`check_valuation_date_consistency` PASS, all 3 scenarios).
No finance-lease double counting (`check_no_debt_or_lease_double_counting`
PASS, all 3 scenarios). Labeled throughout as scenario analysis, not
investment advice.

## 9. Validation totals

| Suite | Total Checks | PASS | FAIL | WARNING/UNAVAILABLE |
|---|---|---|---|---|
| Forecast (`forecast_validation_results`) | 229 | 229 | 0 | 0 |
| Valuation (`valuation_validation_results`) | 28 | 28 | 0 | 0 |
| Milestone 1 historical validation | 79 | 62 | 0 | 17 (UNAVAILABLE, not FAIL) |
| Annual analytical validation | 130 | 120 | 0 | 10 (UNAVAILABLE, not FAIL) |
| Mapping evidence gate | 49 | 49 | 0 | 0 |

**PASS, FAIL, BLOCKED, UNAVAILABLE, and NOT_APPLICABLE remain
distinct classifications throughout** — an UNAVAILABLE check (e.g. a
comparison requiring a filing vintage that doesn't exist for a given
year) is never silently counted as a PASS or hidden from the totals.

**Validation-check classification** (21 named forecast checks, by
honest type, re-confirmed from `forecast.VALIDATION_CHECK_METADATA`):
12 arithmetic invariants, 7 structural completeness checks, 1 scenario-
comparative check, and exactly **1** independent reasonableness test
(the capital-allocation waterfall reconciliation) — arithmetic
consistency is never described as independent validation anywhere in
this project.

## 10. Database integrity and counts

`data/curated/target_cash.db`: 24 tables. Re-counted 2026-09-16:

| Table | Rows |
|---|---|
| annual_facts | 488 |
| annual_fact_observations | 686 |
| annual_lineage | 384 |
| forecast_scenarios | 3 |
| forecast_assumptions | 105 |
| forecast_facts | 765 |
| forecast_lineage | 1,533 |
| forecast_validation_results | 229 |
| investment_capacity_results | 15 |
| valuation_assumptions | 8 |
| valuation_ufcf_facts | 15 |
| valuation_results | 3 |
| valuation_validation_results | 28 |
| instant_facts | 10 |
| instant_fact_observations | 18 |
| quarterly_facts | 28 |
| filings | 8 |

Backups on file from every persistence milestone:
`data/curated/target_cash.db.backup-20260915T220628Z` (Milestone 2),
`...backup-20260916T010849Z` (pre-Milestone-3B),
`...backup-20260916T012100Z` (pre-Milestone-4).

## 11. Excel workbook verification (Milestone 5, re-run 2026-09-16)

`scripts/verify_excel_model.py`: **all checks pass** — zero formula
errors across 1,769 recalculated cells; exact Python match for all 5
forecast years on Scenario Forecast/Cash-Flow Bridge/Investment
Capacity/Capital Allocation (Base scenario, as saved); exact DCF match
(WACC, EV, equity value, value/share); all 15 sheets present in the
required order; scenario-selector dropdown present; frozen panes set;
and the scenario selector genuinely recalculates to match Python exactly
after switching to Upside and to Downside.

## 12. Power BI handoff status

**No `.pbix` file exists, and none is claimed to exist** — Power BI
Desktop and the Power BI API are both unavailable in this build
environment. `scripts/verify_powerbi_handoff.py`, re-run 2026-09-16:
**all 57 checks pass** — every exported CSV's row count matches the live
database exactly; zero orphan foreign keys across the star schema (5
dimension + 9 fact tables); documented validation totals (229/229,
28/28, the 4 FY2025 reference figures) reproduce exactly from the
exported data; all required files, 8 page specs, and 8 well-formed SVG
wireframes are present; explicitly, no `.pbix` file exists anywhere in
the package.

## 13. Website (web cockpit) verification

`scripts/verify_web_cockpit.py`, re-run 2026-09-16 via Playwright against
the pre-installed Chromium: **all 20 checks pass** — zero console/page
errors; Snapshot KPIs match Python exactly for Base/Upside/Downside; the
FY2025 CFO/CapEx/CFI/FCF reference values render and are numerically
distinct; the What-If sandbox matches Python at zero delta, updates when
a slider moves, and Reset restores the exact original output; the
no-double-counting proof reads "OK"; 10 nav links (all 10 required
interface areas) are present; no horizontal overflow at 390px mobile
width (the one real bug found during Milestone 7 — a CSS Grid
`min-width: auto` overflow trap — remains fixed). Not deployed publicly.

## 14. Clean-room reproducibility (re-run 2026-09-16)

`scripts/clean_room_rebuild.py`, run fresh against only the 8 registered
source filings, in a temporary directory, through the complete
`ingest -> persist-annual -> persist-forecast -> persist-valuation`
pipeline:

- All 8 source documents present and hash-verified against the manifest.
- `persist_annual.integrity.all_passed`: **True**
- `persist_forecast.integrity.all_passed`: **True**
- `persist_valuation.integrity.all_passed`: **True**
- `validate.overall_gate_passed`: **True**

## 15. Canonical export comparison (clean-room vs. active database)

`scripts/compare_databases.py`, comparing the fresh clean-room database
against the active `data/curated/target_cash.db` on sorted, deterministic,
hash-stable canonical exports (wall-clock columns excluded):

| Export | Rows (both) | Match | SHA-256 |
|---|---|---|---|
| quarterly_facts | 28 | YES | `4c45df7ae95479b13d6152e87a94508154ec391ed2be6fe846698554cdd071d5` |
| lineage | 45 | YES | `7813dbae698b64ada3719bcbdbd851f7efb978ca0216fe1a0bd4df652b1885d4` |
| instant_facts | 10 | YES | `399c7bffdf1f0f81f83800fcbbc06e75ce7c7c3983a8347249e5589c52e5861d` |
| instant_fact_observations | 18 | YES | `12c83c77e22af78c27334f1ba3373c423a20d33b8718338f10776f29bc2dd76f` |
| annual_facts | 488 | YES | `234c7997b58b3e7f9eeb510a4945d0831b8d0335a0b3f71d82884bb360e6d49a` |
| annual_fact_observations | 686 | YES | `68bd42d25504874550a6e6f8d96e5c30fa99d3defb91d9ac4edf5635bcad411d` |
| annual_lineage | 384 | YES | `b6f73358be34fb21f6675b153bdee1af3c1cf9148b0856222dbd9e7965a0ee3f` |
| period_facts_unified | 526 | YES | `41ff487191d5849dd075ed8f143f7dd25c63827fd46fb633cb71d5c8a6123ed3` |
| forecast_scenarios | 3 | YES | `f19450c1df313b446f0f98cd833ef988bfbaf503eff18bf58d81da9e480e4bd8` |
| forecast_assumptions | 105 | YES | `d6adde8e91eec49d355852e2cc02808fb423ec460214b455786f06baf2f60e40` |
| forecast_facts | 765 | YES | `c929314db293d31bb7279ff4d3410a1742de2a0f201245f1f514eb38f9451342` |
| forecast_lineage | 1,533 | YES | `d313cf54dc2793d368705c3ed3efbf0f0e16177f0bbda672069f350a8aad8c7d` |
| forecast_validation_results | 229 | YES | `8705ef10b2890dfb871ec1ed0b9c261a58327287bfbc1433a65f5ba7ee2edd4d` |
| investment_capacity_results | 15 | YES | `1697475c98825ce19dbeab103d784e479fc9e16834989603eb369cb66a7a8b67` |
| valuation_assumptions | 8 | YES | `18d14863001f150a6a387bf2d73d33dfd3c4c86c5c305e493ba0de6037d8376f` |
| valuation_ufcf_facts | 15 | YES | `f4cca3382338b11444b45422e22d43bd5e39e22a456022e8819dce48b3228dd1` |
| valuation_results | 3 | YES | `c8e13ae4d522a128d788b4fdc5dfcb7a30a906876ca3e2ea4d302102ff85a075` |
| valuation_validation_results | 28 | YES | `c5c675972884b14e5644c2d2e13625395fb044af1033c767eb36153e8ce5c769` |
| validation_results | — | YES | `feb15103d10bd4c62084ff8b66e4620982b45ed43baceb499b41b8721e86be47` |

**ALL 19 EXPORTS MATCH.**

## 16. Lineage completeness

`forecast.build_full_lineage()` covers all 51 persistable forecast
fields (not just a representative subset), producing 1,533
`forecast_lineage` rows — confirmed zero orphans, zero duplicates
(`zero_orphan_lineage`, `zero_duplicate_facts` integrity checks PASS).
Every FY2026 field with a cross-year dependency resolves to a real
historical `annual_facts` citation; every later year resolves to the
prior year's own `forecast_fact_id`.

## 17. Tests

**401 automated unit/integration tests, all passing** (re-run
2026-09-16, `pytest -q`, 1.75-1.97s). Covers: mapping gate, annual
persistence, the forecast engine (all 21 named validation checks, the
cumulative-capacity fix, scenario narratives), forecast persistence,
the valuation engine, and valuation persistence. Plus 3 non-pytest,
script-driven verification suites (Excel: 20 checks; Power BI: 57
checks; web cockpit: 20 checks) — all passing, all re-run today.

## 18. Known limitations (consolidated; full detail in `deliverables/portfolio_package/05_model_risk_and_limitations.md`)

- Forecast CFI modeled as exactly `-CapEx` (no disclosed non-CapEx
  investing driver).
- Near-term debt-repayment reserve proxied by each year's own scheduled
  repayment (no disclosed maturity ladder).
- No FX translation effect modeled.
- WACC/beta/ERP are stated illustrative assumptions, not live market
  data.
- True LibreOffice and Power BI Desktop recalculation were unavailable
  in this build environment; `formulas` (Python) and CSV/DAX-level
  checks were used as documented, disclosed substitutes.
- The web cockpit's What-If sandbox is a hand-maintained JS port of the
  Python formula chain, verified to match exactly at defaults, with a
  documented (not hidden) drift risk if the Python source changes
  without a corresponding JS update.
- This is a case study built by an outside party from public filings —
  it cannot and does not claim knowledge of Target's actual internal
  capital-allocation policy or plans.

## 19. Reproduction commands

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -q                              # 401 passed
.venv/bin/python scripts/clean_room_rebuild.py              # full rebuild + comparison
.venv/bin/python scripts/build_excel_model.py && .venv/bin/python scripts/verify_excel_model.py
.venv/bin/python scripts/build_powerbi_handoff.py && .venv/bin/python scripts/verify_powerbi_handoff.py
.venv/bin/python scripts/build_web_cockpit_data.py && .venv/bin/python scripts/verify_web_cockpit.py
```

Full detail in `deliverables/portfolio_package/13_reproduction_instructions.md`.

## 20. Commit list (42 commits through this document's own milestone; a 43rd commit follows carrying this file)

See `deliverables/portfolio_package/12_final_project_inventory.md` §Commits
for the full, verified 41-commit history from repository scaffolding
(`cd2c288`) through Milestone 7 (`db84f17`), plus Milestone 8
(`0e5eabf`, the 42nd commit, added after that inventory was written).

## 21. Exact unfinished items

- **No native Power BI `.pbix` file** — Power BI Desktop/API is
  unavailable in this environment. The handoff package is complete and
  verified at the level this environment allows; opening it in real
  Power BI Desktop to confirm final rendering is the one remaining step,
  and requires a machine with Power BI Desktop installed.
- **The web cockpit is not deployed publicly** — pending the project
  owner's explicit authorization, per the project's governing rules.
- **No independent human review has occurred.** This entire project,
  across all 8 milestones, was executed by an AI agent under a
  standing no-pause instruction, with self-verification (tests, clean-
  room rebuilds, script-based checks) at every stage but no second
  human or independent reviewer sign-off. This final document, and the
  consolidated report that follows it, are offered as the evidence base
  for that independent review — not a substitute for it.
- **Excel workbook and Power BI wireframes have not been visually
  inspected in their native applications** (Excel/Power BI Desktop) in
  this environment — only programmatic recalculation/structural
  verification was possible here, as documented in §11-12 above.
