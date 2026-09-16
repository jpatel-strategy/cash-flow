# Page 4: Quarterly Cash Proof

**Wireframe**: `wireframes/page_04_quarterly_cash_proof.svg`

## Purpose
Independently evidence the seasonal minimum-cash-buffer policy used in
the forecast, using Target's actual quarterly balance-sheet cash — data
that exists completely outside the forecast model.

## Filters / slicers
None required — all 5 real data points display together so the
seasonal pattern (trough at Q1, peak at year-end) is visible in one
view.

## Visuals

| Visual | Type | Fields |
|---|---|---|
| Cash & Equivalents Balance over time | Line chart | X: `dim_date_quarterly[as_of_date]`; Y: `fact_quarterly_cash[value_normalized]` where `metric = "cash_and_equivalents_balance_sheet"` |
| Trough/Year-End Ratio | Card | Computed measure: MIN balance / balance at FY2025 year-end (2026-01-31) — should read ≈52.6% |
| Source table | Table | `fact_quarterly_cash[as_of_date, value_normalized, accession_number]` joined to `dim_filing[primary_document_url]` |

## Notes
- This page is the single strongest piece of "evidence" content on the
  report — every number on it is a raw balance-sheet figure from a
  10-Q/10-K, with zero forecast-model computation involved. Label it
  explicitly as such.
- The 5 points are FY2024 year-end (2025-02-01), FY2025 Q1/Q2/Q3, and
  FY2025 year-end (2026-01-31) — do not connect them with a smoothed
  curve that implies continuous daily data; use a straight-segment line
  or a column chart to keep the discrete, quarterly nature honest.
