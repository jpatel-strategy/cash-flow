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
from source-compatible periods:

- `Q2 = six_month_YTD - Q1`
- `Q3 = nine_month_YTD - six_month_YTD`
- `Q4 = annual - nine_month_YTD`

"Source-compatible" is a precondition checked on **every** dimension before
the subtraction runs — same entity (CIK), same fiscal year, same XBRL concept
(or an explicitly reviewed and approved equivalence — never a silent
substitution of a similarly-named tag), same unit and scale, same accounting
basis, same consolidated (non-dimensional) scope, exact matching start date,
correct end-date ordering ("period adjacency": the shorter period must end
strictly before the longer one, given both share the same start), same
filing vintage (neither input superseded by a later restatement while the
other is current), and same sign convention. See
`reconcile.check_source_compatibility` — this precondition is a gate, not a
tolerance: any failed dimension blocks the derivation outright rather than
producing a slightly-off number, and every failed dimension is reported at
once rather than stopping at the first one found.

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

## Validation methodology (corrected 2026-09-15)

An earlier design conflated three fundamentally different kinds of check
under one "reconciliation" label. That conflation is wrong and has been
corrected — see `docs/decisions.md` for the full correction and
`src/target_cash/reconcile.py` for the implementation. The three layers are
never conflated in code, config, or reporting:

### 1. Source compatibility (a precondition, not a tolerance)

Before any two facts are combined by subtraction, every dimension listed
above ("Deriving quarters from YTD filings") is checked. This has no numeric
tolerance — it is pass/fail, and a failure blocks the derivation rather than
producing an approximately-right number.

### 2. Arithmetic invariant (a code-correctness check, not a data validation)

Recomputing a derivation formula must reproduce the stored value exactly, or
the derivation code has a bug. **This is never reported as if it validates
the underlying data.** In particular:

> Summing four quarters back up to an annual total is **tautological**
> whenever the fourth quarter was itself derived as `annual - Q1 - Q2 - Q3`
> (equivalently, `annual - nine_month_YTD`). The equality is algebraically
> guaranteed by construction — it proves the subtraction was coded correctly,
> not that the underlying quarters are accurate. The same applies to checking
> `Q1 + Q2 == six_month_YTD` when Q2 was itself defined as
> `six_month_YTD - Q1`. Neither check is an independent reconciliation, and
> neither is ever labeled as one.

### 3. Independent quarter validation (the only genuine data validation)

The only checks with real diagnostic power compare a derived value against a
fact that was **not used to produce it**:

- **`check_independent_quarter_validation`**: Target reports revenue and cost
  of sales as discrete 3-month figures directly in every 10-Q, in addition to
  the YTD figures used for other metrics. Where such a discrete fact exists,
  the YTD-derived quarter is compared against it — a genuine independent
  check, since the discrete fact was filed separately from the YTD figures
  used in the subtraction. **Every quarter without such a fact — always true
  for Q4, since Target never files a discrete fourth quarter — is labeled
  exactly `"arithmetic invariant passed; independent quarter validation
  unavailable"`**, never silently treated as a pass.
- **`check_ytd_consistency`**: compares a directly-filed YTD fact against the
  sum of three directly-filed discrete quarters. Both sides are independently
  filed by the company (neither derived from the other), so this is a
  genuine check — unlike summing quarters to an annual total when one
  quarter was defined as the residual.

Both functions require the two sides' raw-fact identifiers to be disjoint,
and check this explicitly. **A comparison is never labeled independent
merely because it produced two different-looking function calls** — if the
"independent" side secretly draws on a fact that also fed the derived value,
the result is `"not_independent"` (a gate failure), never `"validated"`,
regardless of whether the values happen to agree.

### Rounding-bound tolerances (not an arbitrary flat figure)

Where a numeric tolerance is needed (independent quarter validation, YTD
consistency, cash roll-forward), it is a **documented worst-case bound**
(`reconcile.compute_rounding_bound`), derived from how many independently-
rounded reported facts actually feed that specific check:

- Each **directly-reported** component is rounded by the filer to the
  nearest reporting unit ($1M for Target), so it carries a maximum rounding
  error of half that unit ($0.5M).
- Each **YTD-derived** component is itself a subtraction of two independently
  rounded facts, so it carries twice that ($1.0M) — it inherits rounding
  error from both inputs.
- `bound = (num_directly_reported + 2 × num_ytd_derived) × (reporting_unit / 2)`

This is a worst-case (triangle-inequality) bound, not a statistical estimate
— it assumes every component's rounding error points the same direction,
which is the most that could possibly happen. Worked examples (see
`config/model.yml: reconciliation_tolerance`):

| Check | Components | Bound |
|---|---|---|
| Independent quarter validation | 1 YTD-derived (counts as 2) + 1 directly-reported | (1 + 2×1) × $0.5M = **$1.5M** |
| YTD consistency | 4 directly-reported (3 quarters + 1 YTD fact) | (4 + 0) × $0.5M = **$2.0M** |
| Cash roll-forward, annual | 6 directly-reported (beginning cash, CFO, CFI, CFF, FX, ending cash) | (6 + 0) × $0.5M = **$3.0M** |
| Cash roll-forward, quarterly (Q2/Q3) | fewer directly-reported, more YTD-derived, since Target's cash-flow statement is YTD-only in 10-Qs | computed per period from its actual derivation lineage, not hardcoded |

**The residual is always reported, even when it falls inside the bound** —
never silently absorbed into a bare pass/fail.

### Excel vs. Python

Kept **separate** from the rounding-bound method above: Excel and Python
compute the identical formula on identical inputs, so this is not about
propagated filing-rounding at all. A tolerance of $0.01M (one unit at
2-decimal display precision) catches only binary-float-vs-Decimal noise at
the last digit — any larger difference is a real modeling divergence.

### First data gate (Milestone 1)

The first data gate passes only when, for one complete fiscal year:

- Every source-compatibility precondition passes for every derived fact.
- Every arithmetic invariant holds (recomputation matches the stored value).
- Every independent quarter validation that is *available* passes within its
  rounding bound; those correctly labeled "unavailable" do not block the gate
  but are never miscounted as passes either.
- Every YTD-consistency check passes within its rounding bound.
- Opening cash rolls forward to ending cash within its rounding bound, with
  the residual reported regardless of outcome.
- Every derived quarterly fact has at least one `lineage` row.
- No missing or conflicting fact has been silently resolved.
