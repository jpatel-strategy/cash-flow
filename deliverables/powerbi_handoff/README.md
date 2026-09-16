# Power BI Handoff Package — Target Cash Flow & Investment Capacity Model

## What this is, and what it is not

**No native Power BI (.pbix) file was created, because none could be.**
This environment has no Power BI Desktop application and no Power BI
REST/XMLA API access, so there is no way to author or programmatically
verify a real `.pbix` here. Claiming otherwise would violate the
project's own General Rule 17 and the explicit Milestone 6 instruction
to "never claim that a PBIX was created if it was not."

What follows instead is a **complete, implementation-ready handoff
package**: everything a Power BI developer needs to build the report in
under an hour, with no guesswork about data, relationships, measures, or
layout, and with the totals to check their finished report against.

## What's in this package

| Path | Contents |
|---|---|
| `data/*.csv` | Star-schema fact and dimension tables, exported live from `data/curated/target_cash.db` (the same production database every other deliverable reads). |
| `data_dictionary.md` | Every table, its grain, its keys, and its columns. |
| `relationship_map.md` | Every fact-to-dimension relationship, cardinality, and cross-filter direction to set in Power BI's Model view. |
| `dax_measures.md` | Copy-paste-ready DAX for the required core measures plus supporting measures. |
| `theme.json` | A valid Power BI JSON report theme (navy/gold, matching the Excel workbook's palette) — import via *View → Themes → Browse for themes*. |
| `pages/*.md` | A written wireframe spec for each of the 8 required report pages: purpose, visuals, fields, filters/slicers. |
| `wireframes/*.svg` | A schematic layout mockup for each page (box-and-label diagrams, **not** real Power BI screenshots — Power BI Desktop was not available to capture real ones). |
| `refresh_instructions.md` | How to point Power BI at the CSVs (or, later, directly at the SQLite database) and refresh. |
| `validation_totals.md` | Independent totals/counts a developer can check their built report's visuals against, so a wiring mistake is caught immediately. |

## How to build the actual report

1. Open Power BI Desktop → *Get Data → Text/CSV* → import every file
   in `data/`.
2. In *Model view*, wire up the relationships exactly as listed in
   `relationship_map.md`.
3. Paste the measures from `dax_measures.md` into a dedicated
   measures table (create one blank table named `_Measures` and add
   them there, which is standard Power BI practice).
4. Build each of the 8 pages per its spec in `pages/`, using the
   matching wireframe in `wireframes/` as the layout guide.
5. Apply `theme.json`.
6. Cross-check headline numbers against `validation_totals.md`.

## Regenerating this package

`scripts/build_powerbi_handoff.py` regenerates every CSV export (and
the filing-vintage comparison, which is computed, not a raw table) from
the live database. `scripts/verify_powerbi_handoff.py` independently
re-derives key totals from the database and the `target_cash` Python
model and checks them against the exported CSVs and against each
other, and checks star-schema referential integrity (no fact row
references a dimension key that doesn't exist).

## Information cutoff

Every exported fact carries the same FY2025 10-K information cutoff
(2026-03-11) used throughout this project. No analyst estimates, later
filings, or hindsight are present anywhere in this package.
