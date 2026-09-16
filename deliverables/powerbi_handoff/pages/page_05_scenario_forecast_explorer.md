# Page 5: Scenario Forecast Explorer

**Wireframe**: `wireframes/page_05_scenario_forecast_explorer.svg`

## Purpose
Let a user explore the full FY2026-FY2030 income-statement and
operating-driver forecast for whichever scenario they select, with the
scenario's business narrative alongside the numbers (not just
mechanical increases/decreases).

## Filters / slicers
- Scenario selector (primary interaction on this page).
- Fiscal Year slicer.
- Metric slicer for the line charts.

## Visuals

| Visual | Type | Fields |
|---|---|---|
| Revenue / Gross Profit / Operating Income / Net Income | Line chart | X: fiscal year (FY2026-FY2030); Y: `fact_forecast[value]` per metric, filtered to selected scenario |
| Diluted EPS / Revenue Growth % / Margins | Line chart (dual axis: $ vs %) | Same X; Y: `diluted_eps`, `revenue_growth_pct`, `gross_margin_pct`, `operating_margin_pct` |
| Full income-statement forecast | Matrix | Rows: `dim_metric[metric_label]` (income-statement category only); Columns: `dim_fiscal_year[year_label]`; Values: `fact_forecast[value]` |
| Scenario Narrative | Text box, dynamically bound | A DAX measure returning the matching narrative string for the selected scenario (source: `docs/decisions.md`'s Milestone 3A scenario narratives — copy the 3 narrative strings into a small `dim_scenario_narrative` table with one row per scenario, `scenario_id` + `narrative_text`, and relate it to `dim_scenario`) |

## Notes
- This page must make the scenario selection change every visual on
  the page — verify by switching scenarios and confirming the matrix
  and both charts update (the same kind of check
  `scripts/verify_excel_model.py` performs for the Excel workbook's
  own scenario selector).
- The scenario narrative text box exists specifically so the report
  doesn't reduce Upside/Base/Downside to "numbers went up/down" — it
  should read as a coherent business story (e.g. Downside: a
  broad-based demand slowdown with a dividend freeze, not a cut;
  Upside: margin expansion with a temporary non-monotonic CapEx step-up).
