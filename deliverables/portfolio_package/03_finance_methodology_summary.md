# Finance Methodology Summary

The substance a finance hiring manager will actually probe. Written to
be defensible in an interview, not just accurate on paper.

## Historical fact treatment

- Every historical figure is sourced from a specific SEC filing
  (accession number, filed date, and the exact XBRL-derived value are
  all retained). Where Target's own filings show two different values
  for the same fiscal year across filing vintages (a restatement or
  reclassification), **both** are kept — `as_originally_filed` and
  `latest_restated` — rather than silently picking one. This surfaced a
  real reclassification: **~$77M (FY2022) and ~$92M (FY2023)** moved
  between cost of sales and SG&A in the FY2024 10-K, with **zero**
  revenue or net-income impact. That's the kind of finding a careful
  analyst is expected to catch, and a naive model would silently absorb.
- **Capital expenditure is always the property-and-equipment
  acquisition cash outflow, never total investing cash flow.** These are
  frequently and wrongly treated as interchangeable. FY2025 reference
  values, kept distinct everywhere in this project: CFO **$6,562M**,
  CapEx **$3,727M**, total investing cash flow (CFI) **$(3,649)M**, FCF
  (CFO − CapEx) **$2,835M**. CapEx and |CFI| are not equal, which is the
  point — CFI nets in non-CapEx investing items (investment purchases
  and maturities) that CapEx correctly excludes.

## Forecast construction

- Three scenarios (Base, Upside, Downside), each defined by **19 named,
  independently rationalized assumptions per year** (revenue growth,
  gross margin, SG&A leverage, D&A, tax rate, buyback payout ratio,
  dividend growth, minimum-cash policy, etc.) — never a single blended
  growth-rate dial.
- Every scenario is written and defended as a **coherent business
  story**, not a mechanical "increase/decrease everything by X%." The
  Upside case, for example, deliberately has a *non-monotonic* CapEx
  driver — it spends *more* on capital, not less, because funding the
  stronger growth (new stores, supply chain, digital investment) is
  what makes the stronger growth possible. A model that reflexively
  cuts every cost line in every "good" scenario would get this
  backwards.
- **Information cutoff is enforced, not just claimed**: every
  assumption and every forecast fact carries an explicit
  `information_cutoff` field, and a dedicated audit
  (`forecast.cutoff_audit()`) checks that no assumption's rationale
  references anything the FY2025 10-K couldn't have supported.

## Investment capacity and capital allocation — the hardest problem

The project's central finance-methodology contribution is proving,
rather than asserting, that no dollar of cash flow is counted twice.

- **The bug, found and fixed**: an early version of "cumulative
  deployable capacity" summed each year's *ending* capacity balance
  across the forecast horizon. Because unused capacity in one year
  simply carries into the next year's beginning cash, that naive sum
  re-counts the same undeployed dollars every year they remain unspent
  — overstating true cumulative capacity by **roughly 2.6x-3.8x**
  depending on scenario (Base overstated by $16.2B, Upside by $9.1B,
  Downside by $16.8B). The corrected formula is: *cumulative capacity =
  the terminal year's own ending balance (which already reflects every
  prior year's carried-forward unused cash) + the sum of amounts
  actually deployed along the way.*
- **The proof, not just the fix**: a full source-and-use conservation
  identity is checked for every scenario and year: `beginning cash + CFO
  + CFI + debt proceeds = debt repayments + dividends + repurchases +
  management-selected deployment + ending cash`. Every dollar generated
  is exactly one of five mutually exclusive uses — never zero, never
  two.
- **Honest classification of what's actually "independent."** Out of
  more than 20 automated checks, exactly **one** — the capital-
  allocation waterfall, recomputed as a genuinely separate 8-step
  sequence and reconciled to the engine's own ending-cash figure — is
  classified as an independent reasonableness test. Every other check is
  labeled for what it actually is: an arithmetic invariant, a
  structural-completeness check, or a scenario-comparative check. This
  distinction is stated as a governing rule of the project because
  conflating "the math is internally consistent" with "an independent
  check confirms this is right" is a common and material error in
  financial modeling.

## Valuation

- A **restrained DCF**, explicit about every assumption (risk-free
  rate, equity risk premium, beta, cost of debt, capital-structure
  weights, terminal growth) and never blended with the operating-
  forecast assumptions.
- **Valuation-date consistency, enforced by a check**: net debt and
  diluted share count in the enterprise-to-equity bridge are always
  FY2025 *actuals* (the valuation date), never a forecast year's
  projected balance — a subtle but common DCF error when models
  discount future cash flows back to one date but bridge to equity
  value using another.
- **No debt/lease double counting**: net debt uses `total_debt_gaap −
  cash`, which already excludes finance leases (reported and tracked
  separately per Milestone 2's own debt inventory) — never added back
  on top.
- Labeled, explicitly and repeatedly, as **scenario-based illustration,
  not a price target, analyst estimate, or investment recommendation.**

## What this deliberately does not do

- Does not use analyst estimates, later filings, or market results —
  ever, anywhere in the model.
- Does not solve any cash-flow line backward to hit a target (no
  "plugs"). Share repurchases, for example, use a fixed payout-ratio
  assumption floored at zero, never a residual balancing figure.
- Does not claim precision it doesn't have — every disclosed
  approximation (CFI modeled as exactly −CapEx due to no disclosed
  non-CapEx investing driver; the near-term debt reserve proxied by the
  current year's own scheduled repayment due to no disclosed maturity
  ladder) is documented as exactly that, an approximation, in
  `05_model_risk_and_limitations.md` and in `docs/decisions.md`.
