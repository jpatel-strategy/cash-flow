# Technical Architecture Summary

Written for a technical interviewer or reviewer who wants the "how,"
having already read the "what" in `01_executive_case_study.md`. Kept
deliberately concise — the code itself, and `docs/decisions.md`, are the
full record.

## Stack

- **Python 3.10+**, `pandas`, `pydantic`, `openpyxl`, standard-library
  `sqlite3` — no heavyweight framework. This is a data-pipeline and
  modeling project, not a web-service project, so the toolchain is kept
  boring and inspectable on purpose.
- **SQLite** as the system of record (`data/curated/target_cash.db`),
  chosen for zero-infrastructure reproducibility — anyone can clone the
  repo and get an identical, queryable database with no server to stand
  up.
- **openpyxl** for the Excel workbook, and the `formulas` Python package
  as an independent formula-recalculation engine for verification (see
  below — LibreOffice could not load any `.xlsx` in the build sandbox).
- **Vanilla HTML/CSS/JS** for the web cockpit — zero build step, zero
  CDN dependency, hand-rolled SVG charts. A deliberate choice: the point
  was a decision-support tool, not a demonstration of frontend
  framework skill.
- **Playwright + headless Chromium** for automated, real-browser
  verification of the web cockpit (console errors, rendered-value
  correctness, responsive layout).

## Pipeline stages

```
SEC filings (docs/sources.csv)
      |
      v
raw_facts (as-extracted, per filing, per XBRL tag)
      |
      v  [mapping + validation gates]
annual_facts / instant_facts / quarterly_facts
      |          (historical, both as-originally-filed and
      |           latest-restated analytical views)
      v
forecast_scenarios / forecast_assumptions / forecast_facts / forecast_lineage
      |          (3 scenarios x 5 years x 51 metrics, each with a
      |           full field-to-formula-to-source lineage trail)
      v
valuation_assumptions / valuation_ufcf_facts / valuation_results
      |
      v
Excel workbook  |  Power BI handoff  |  Web cockpit  |  Recruiter package
```

Every arrow is a real, tested, idempotent function — not a diagram of
aspiration. `scripts/clean_room_rebuild.py` runs the entire left-to-
right chain from scratch in a temp directory using only the registered
source filings, and `scripts/compare_databases.py` proves the result is
byte-identical (on deterministic, sorted, hash-stable canonical exports)
to the production database.

## Design decisions worth calling out

- **Deterministic, content-addressed IDs** everywhere persistence
  happens (e.g. `forecast_fact_id = f"fct_{scenario}_{metric}_{fy}_{version}"`).
  This makes every persistence operation genuinely idempotent — re-
  running it twice produces identical row counts, not duplicates — and
  makes `ON CONFLICT DO UPDATE` upserts safe rather than a source of
  silent drift.
- **Additive-only schema migrations.** New tables and columns are added
  via a small migration framework (`src/target_cash/migrations.py`)
  that never alters or drops existing structure — a real production
  discipline, applied here even though this is a solo project, because
  it's the discipline that matters for the finance-auditability point
  being demonstrated.
- **Full field-level lineage**, not just headline-metric lineage. Every
  one of the 51 persisted forecast fields has a `build_full_lineage()`
  entry citing its exact formula and every same-year, cross-year, and
  assumption input it depends on — traceable all the way back to a
  historical SEC fact ID where the chain bottoms out.
- **Two genuinely different formula-verification tools**, because
  neither environment tool worked out of the box: LibreOffice could not
  load *any* `.xlsx` file in this sandbox (confirmed with a trivial one-
  cell test file), so the Excel workbook is verified with the
  `formulas` Python package instead; Power BI Desktop and the Power BI
  API are both unavailable in this environment, so that package is
  verified at the CSV/DAX/referential-integrity level, and is candid,
  in its own README, that no `.pbix` was created.
- **A hand-rolled but faithful client-side formula port** for the web
  cockpit's What-If sandbox (`js/formulas.js`), rather than pulling in a
  full JS numerical stack for one interactive feature — verified against
  Python output to the dollar.

## Test coverage

467 automated unit/integration tests (`pytest`), covering the mapping
gate, the annual persistence pipeline, the forecast engine (including
every validation check and the cumulative-capacity fix), the forecast
persistence layer, the valuation engine, the valuation persistence
layer, and the corrected capacity-taxonomy engine and its persistence
layer. Plus three independent, script-driven verification passes for
the three presentation layers (Excel, Power BI handoff, web cockpit),
none of which are pytest tests but all of which are automated and
re-runnable.
