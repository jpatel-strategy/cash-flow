# Model Risk & Limitations Statement

Stated up front, not buried — a model-risk statement is itself part of
demonstrating financial judgment.

## What this model is

An independent, public-data illustration of a cash-flow forecasting and
investment-capacity framework for Target Corporation, built entirely
from SEC filings, for a portfolio/case-study purpose.

## What this model is NOT

- **Not investment advice.** Nothing in this project is a
  recommendation to buy, sell, or hold any security.
- **Not a price target or analyst estimate.** The DCF valuation is
  explicitly scenario-based and illustrative.
- **Not based on non-public information.** Every fact traces to one of
  8 registered, publicly filed SEC documents.
- **Not a prediction.** FY2026-FY2030 figures are labeled scenario
  assumptions, built only from information available as of the FY2025
  10-K (2026-03-11) — they will not, and are not intended to, match
  Target's actual future results.

## Known modeling limitations (by category)

### Disclosed-driver gaps
- **Investing cash flow beyond CapEx is not separately modeled.** No
  disclosed driver exists in the source filings for non-CapEx investing
  items (investment purchases/maturities), so forecast CFI is modeled as
  exactly `-CapEx`. This is a documented approximation, never a
  substitution of CFI for CapEx in the FCF calculation itself.
- **No disclosed debt-maturity ladder exists**, so the near-term debt-
  repayment reserve is proxied by each forecast year's own scheduled
  repayment assumption, not a real maturity schedule.
- **The forward debt-repayment reserve for the terminal forecast year
  (FY2030) is a documented proxy**, not a real scheduled obligation — it
  repeats FY2030's own net mandatory debt service because FY2031 is
  outside the 5-year forecast horizon.
- **No foreign-exchange translation effect is modeled.** Target's cash
  is overwhelmingly USD-denominated, and no disclosed FX driver exists
  in the registered source filings.

### Methodology choices, stated as choices
- **Share repurchases use a fixed payout-ratio assumption**, floored at
  zero — never solved backward to hit a target ending-cash or EPS
  figure. This means the model will not automatically "balance" to a
  clean-looking number; it can produce an ending cash balance that
  looks unusual if the assumption doesn't fit a scenario well, and that
  is by design, not a bug to paper over.
- **Minimum-cash-buffer and near-term-reserve percentages are policy
  assumptions**, calibrated to Target's own observed FY2025 quarterly
  cash seasonality (the real ~52.6% trough-to-year-end ratio) — not a
  disclosed corporate treasury policy.
- **WACC inputs (risk-free rate, equity risk premium, beta) are stated,
  illustrative assumptions**, not fitted to a live market-data feed —
  this project has no live market-data connection anywhere.

### Environment limitations (tooling, not finance)
- **True Excel/LibreOffice recalculation was unavailable** in the build
  sandbox (LibreOffice could not load any `.xlsx` file at all, confirmed
  with a trivial test file); the Excel workbook was instead verified
  with the `formulas` Python package, a credible but distinct
  implementation of the Excel formula language.
- **True Power BI Desktop/API access was unavailable**; no `.pbix` file
  was created or is claimed to exist. The Power BI package is a
  complete implementation-ready handoff, verified at the CSV/DAX/
  referential-integrity level, never opened in the real product.
- **The web cockpit's What-If sandbox** uses a hand-maintained
  JavaScript port of the core Python forecast formulas for illustrative
  interactivity. It is verified to match Python exactly at default
  (zero-delta) settings, but is a separate implementation that could in
  principle drift from the Python source of truth if the latter changes
  without a corresponding update — a risk documented rather than hidden.
  The same is true of the corrected capacity-taxonomy formula
  (`computeCapacityTaxonomyYear` in `formulas.js`), a manually-
  synchronized line-for-line port of `capacity_taxonomy.py`, verified
  against Python at page load but not auto-generated from it.

## Validation coverage and its honest limits

467 automated checks currently pass (229 forecast + 28 valuation + 210
capacity taxonomy). Of these, the large majority are **arithmetic
invariants** (the model's own formulas are internally consistent) or
**structural completeness checks** (every required field/relationship
exists) — not independent confirmation that the underlying assumptions
are *correct*. Exactly one check (the capital-allocation waterfall
reconciliation) is classified as a genuinely independent reasonableness
test, and the project is explicit about this distinction rather than
presenting arithmetic self-consistency as if it were independent
validation.

## What would need to change before this could inform a real decision

1. Replace illustrative WACC/beta/ERP inputs with a live, sourced
   market-data feed.
2. Obtain (or disclose the absence of) a real debt-maturity schedule
   rather than the current-year-repayment proxy.
3. Have the assumption set reviewed and stress-tested by someone with
   direct knowledge of Target's actual capital-allocation policy and
   plans, which this project — built entirely from public filings by an
   outside party — cannot claim to have.
4. Extend the information cutoff forward as new filings become
   available, through the same clean-room-rebuild and validation-gate
   process this project already uses, never through an ad hoc edit.
