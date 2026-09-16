# Page 3: Filing-Vintage & Restatement Comparison

**Wireframe**: `wireframes/page_03_filing_vintage_and_restatement_comparison.svg`

## Purpose
Prove no historical figure was silently restated without disclosure —
show exactly which lines changed between the as-originally-filed and
latest-restated views, by how much, and why.

## Filters / slicers
- Fiscal Year slicer (FY2021-FY2025).
- Metric slicer (revenue / cost_of_sales / gross_profit /
  operating_expenses — the 4 lines exposed to Target's FY2024
  segment/expense reclassification).

## Visuals

| Visual | Type | Fields |
|---|---|---|
| As-Originally-Filed vs Latest-Restated | Clustered column | X: fiscal year; Y: `fact_filing_vintage_comparison[as_originally_filed, latest_restated]` |
| Difference table | Table | `fact_filing_vintage_comparison[metric, fiscal_year, difference, pct_difference, reclassified]` |
| Narrative callout | Text box | "FY2022 and FY2023: a COGS-vs-SG&A reclassification moved $77M and $92M respectively out of cost_of_sales into operating_expenses, with $0 impact on revenue or net income. FY2021, FY2024, and FY2025 show no reclassification." |

## Notes
- `reclassified = TRUE` rows should be visually flagged (conditional
  formatting, red/amber marker) in the difference table — this page's
  entire purpose is making restatement visible, not burying it in a
  static number.
- This page has no scenario selector — it is purely historical/actual
  data and is scenario-independent.
