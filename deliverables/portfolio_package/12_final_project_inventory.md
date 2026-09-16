# Final Project Inventory

A complete manifest as of 2026-09-16, immediately before the final
system audit (Milestone-list item 9). Numbers here are the actual state
of the repository, not estimates.

## Commits (41 total, chronological)

The full milestone-by-milestone commit history, from repository
scaffolding through Milestone 7:

```
cd2c288  Scaffold repository, schema, and validation pipeline (Milestone 1, part 1)
648770d  Verify Target Corporation entity identity (Milestone 1, part 2)
2536cb5  Activate approved proof year, cutoff, and category-specific tolerances
920a30c  Correct validation methodology: separate arithmetic invariants from independent validation
0b98336  Extend source-compatibility checks and detect non-independent validations
8b584f8  Preserve and raw-ingest the real FY2025 10-K; activate 4 reviewed mappings
eba349f  Pre-10-Q-ingestion corrections: net-other-income review, interest-expense tag fix, ...
50af913  Preserve and raw-ingest the three FY2025 10-Qs (Q1/Q2/Q3)
50842ff  Derive quarterly_facts for the 5 reviewed metrics; surface a real cross-filing ambiguity
1eaa107  Add dry-run persistence control and wire the real validation gate
432eee0  Fix unit-mismatch bug in YTD-consistency validation checks
25ecaad  Classify unexecuted validation checks as BLOCKED, not FAILED
a69fcfc  Correct FX characterization, review CFO/CFI/CFF, add instant-fact schema
8925310  Correct sign-compatibility policy; add persist_instant_facts
5cd45ef  Record Milestone 1 first analytical persistence
879ac2d  Milestone 1 reproducibility closeout: clean-room proof and evidence doc
c9f11ed  Correct imprecise phrasing in Milestone 1 evidence doc
c6ba8ca  Milestone 2 deliverables: five-year mapping matrix, dry-run table, driver dictionary, ...
1c568a0  Correct FY2023 methodology error; ingest full five-year authoritative filing set
c0d4b93  Correct debt classification; approve concept equivalences with evidence; ...
ec2958c  Implement Milestone 2 schema; run complete five-year dry run; correct debt bridge ...
f1bacfa  Integrate annual validation into the standard validate command
534c38e  Milestone 2: two-gate mapping-approval policy, complete evidence matrix ...
9150365  Gate-fix: composite overall_gate_passed enforcement and conditional annual persistence
4aea5c3  Fix self-caught gap: finance_lease_liabilities had no metric_definitions.csv row
3c3e42a  Extend clean-room rebuild to run annual persistence through the real CLI
0819168  Add generator script for docs/milestone_2_evidence.md
432629d  Add Milestone 2 final evidence document
7b14b35  Observation-completeness: full evidence enrichment for annual_fact_observations
d9a2ab8  Fix stale observation rationale/diff on re-persist (found by clean-room mismatch)
226878c  Update evidence-doc generator for the enriched observation set
0e1fe8d  Regenerate Milestone 2 evidence for the enriched observation set
18be5f8  Document observation-completeness closeout round
c0df82f  Milestone 3: forecast and investment capacity engine (dry run, not persisted)
df07bd5  Milestone 3 reviewer audit package: complete evidence, not a summary   <- approved starting point
19fd116  Milestone 3A: forecast correction round -- fix cumulative-capacity double counting
372a58b  Milestone 3B: implement and persist the forecast schema
1133b4f  Milestone 4: restrained DCF valuation layer, persisted
749ae73  Milestone 5: Excel executive workbook (15 sheets), formula-verified
2905d92  Milestone 6: Power BI implementation-ready handoff package
db84f17  Milestone 7: web decision cockpit, verified against Python and previewed
```

(A further commit for this Milestone 8 portfolio package, and a final
commit for the system audit, follow this one.)

## Source code (`src/target_cash/`, ~20,300 lines of Python project-wide)

`annual.py`, `annual_persistence.py`, `cli.py`, `derive.py`, `fetch.py`,
`filings.py`, `forecast.py`, `forecast_persistence.py`, `lineage.py`,
`mapping_gate.py`, `migrations.py`, `normalize.py`, `reconcile.py`,
`reference_data.py`, `validation.py`, `valuation.py`,
`valuation_persistence.py`, `xbrl.py`.

## Tests

401 automated tests across 19 test files in `tests/unit/`, all passing.
Plus 3 script-based, non-pytest verification suites (Excel: 20 checks;
Power BI: 57 checks; web cockpit: 20 checks) — all passing.

## Scripts (`scripts/`)

Data/build: `annual_dry_run.py`, `build_excel_model.py`,
`build_mapping_approval_matrix.py`, `build_milestone_2_evidence.py`,
`build_milestone_3_proposal.py`, `build_milestone_3_review_package.py`,
`build_powerbi_handoff.py`, `build_web_cockpit_data.py`.
Verification: `verify_excel_model.py`, `verify_powerbi_handoff.py`,
`verify_web_cockpit.py`.
Reproducibility: `clean_room_rebuild.py`, `compare_databases.py`.

## Database (`data/curated/target_cash.db`)

24 tables, 5,701 total rows as of the last full pipeline run. Backed up
before every persistence milestone (backups retained under
`data/curated/*.backup-*`).

## Documentation (`docs/`)

`decisions.md` (the full, dated decision log — the single most
important document in the project for demonstrating judgment and
rigor), `accounting_policies.md`, `limitations.md`, `sources.csv` (the
8-filing source register), plus per-milestone evidence/proposal
documents for Milestones 1-3.

## Deliverables (`deliverables/`)

| Path | Milestone | Contents |
|---|---|---|
| `Target_Cash_Flow_Investment_Capacity_Model.xlsx` | 5 | 15-sheet Excel workbook, live-formula scenario selector, verified via the `formulas` package (20 checks). |
| `powerbi_handoff/` | 6 | Star-schema CSV exports (5 dim + 9 fact tables), data dictionary, relationship map, DAX measures, theme, 8 page specs + wireframes, refresh instructions, validation totals. Verified via 57 checks. No `.pbix` — none claimed. |
| `web_cockpit/` | 7 | Static HTML/CSS/JS web app, 10 interface areas, editable what-if sandbox, verified via 20 Playwright-driven checks. Not deployed publicly. |
| `portfolio_package/` | 8 | This folder — 14 recruiter/portfolio deliverables. |

## What is explicitly NOT in this project

- No `.pbix` file (Power BI Desktop unavailable in this environment —
  disclosed, not hidden).
- No live deployment of the web cockpit (requires explicit
  authorization not yet sought).
- No use of any information beyond the FY2025 10-K (filed 2026-03-11)
  anywhere in the model.
- No paid services, no external publishing, no exposed credentials.
