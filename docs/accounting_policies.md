# Accounting and Normalization Policies

These rules govern how raw SEC facts become `quarterly_facts` rows. They are
binding on `src/target_cash/normalize.py` and `reconcile.py`; a change here
requires a new entry in `docs/decisions.md`.

## Point-in-time vs. flow values

- Balance-sheet facts (cash, inventory, accounts payable, debt) are **stocks**
  measured at an instant. They are stored with `basis = 'point_in_time'` and
  are **never differenced** across periods to manufacture a quarterly flow.
- Income-statement and cash-flow-statement facts are **flows** over a period
  and may be reported as quarterly, six-month year-to-date (YTD), nine-month
  YTD, or annual, depending on which filing they come from.

## Deriving quarters from YTD filings

When a flow metric is not directly reported for a quarter, it is derived only
from compatible periods of the **same fiscal year, scope, unit, and accounting
basis**:

- `Q2 = six_month_YTD - Q1`
- `Q3 = nine_month_YTD - six_month_YTD`
- `Q4 = annual - nine_month_YTD`

Overlapping quarterly and YTD facts for the same period are never summed.
Every derived value is stored with `basis = 'derived_ytd_subtraction'` and a
`lineage` row for each input fact it used.

## Units and sign

- Values are normalized to **USD millions** (`normalized_unit`), with the
  original filed unit and value preserved alongside the normalized one.
- Costs and capital expenditure are stored as **positive** inputs; cash-flow
  effects (inflow vs. outflow) are made explicit by the metric definition, not
  inferred from a bare sign. `config/metrics.csv` records the intended sign
  convention per metric, but every mapped tag must still be checked against
  the actual filing statement — SEC XBRL sign conventions are not uniform
  across companies or tags, and a similarly-named tag is not assumed to carry
  the same convention without inspection.
- All financial arithmetic uses `decimal.Decimal`, never binary floating point,
  wherever rounding could affect a reported result.

## Fiscal calendar

Target uses a 52/53-week fiscal year ending on the Saturday nearest January 31,
not the calendar year. Actual period start dates, end dates, and day counts are
preserved from the filing and used for any per-day normalization (e.g. in the
seasonal baseline). Calendar-quarter assumptions are never substituted for
fiscal-quarter facts.

## Missing and conflicting data

- A missing metric is recorded as missing, not defaulted to zero. Any
  calculation depending on it fails visibly rather than silently substituting
  a value.
- Conflicting facts (e.g. two candidate tags for the same metric/period that
  disagree) remain visible in `raw_facts` until a mapping decision resolves
  them; the resolution and its rationale are logged in `docs/decisions.md`.
- Later restatements may update the **current reconciled view**
  (`is_current_view = 1`). They must never be substituted into a historical
  forecast origin's information set — see "Two views of history" below.

## Two views of history

1. **Current reconciled view** — may incorporate later restatements, always
   clearly labeled as such.
2. **Information-available-at-the-time view** — for backtesting, selects only
   facts that were publicly available as of a given forecast origin's
   information cutoff. This view is not implemented in Milestone 1 (no
   forecasting yet), but the schema's `as_of_date` / `is_current_view` fields
   exist from the start so it does not require a later migration.

## Reconciliation gate (Milestone 1)

The first data gate passes only when, for one complete fiscal year:

- Quarterly income-statement flows sum to the reported annual total within the
  documented tolerance (`config/model.yml: reconciliation_tolerance`).
- Quarterly cash-flow flows sum to the reported annual total within the same
  tolerance.
- Opening cash rolls forward to ending cash via CFO + CFI + CFF (+ FX/restricted-
  cash effects where applicable) within tolerance.
- Every derived quarterly fact has at least one `lineage` row.
- No missing or conflicting fact has been silently resolved.
