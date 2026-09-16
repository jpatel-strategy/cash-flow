# Demo Script (~8-10 minutes)

For a live portfolio walkthrough or a technical/finance interview.
Assumes the web cockpit is running locally (`cd deliverables/web_cockpit
&& python3 -m http.server 8080`).

## 0:00-0:45 — Open on the Executive Snapshot

"This is a full cash-flow and investment-capacity model for Target
Corporation, built entirely from their public SEC filings — no
proprietary data, no analyst estimates. This first screen is designed
to answer, in under 30 seconds: what happened historically, what's
expected under each scenario, how much cash the business generates, and
how much of it can safely be deployed."

*Point to the KPI cards, the revenue/FCF chart (call out the solid-vs-
dashed actual/forecast distinction), and the scenario narrative.*

## 0:45-2:00 — Scenario selector

"Watch what happens when I switch to Upside." *Click Upside.* "Notice
remaining deployable headroom actually goes *down* in Upside versus
Base, even though revenue and FCF are higher — that's not a bug. Upside
deploys more of its cash into buybacks and faster deleveraging, so less
sits idle. The narrative underneath explains exactly why — this isn't
three scenarios that are just the same forecast multiplied by a number."

## 2:00-3:30 — Cash-flow definitions

Scroll to the Cash-Flow Definitions section.

"This section exists because of a specific, common mistake: confusing
CapEx with total investing cash flow. They're never the same number.
For FY2025: CFO is $6,562 million, CapEx — property and equipment
purchases only — is $3,727 million, but total investing cash flow is
$(3,649) million, and free cash flow is CFO minus CapEx: $2,835 million.
Getting this wrong is a real, common analyst error, and this project is
explicit about avoiding it everywhere, not just on this one page."

## 3:30-5:00 — The double-counting proof

Scroll to Capital Allocation Waterfall.

"This is the hardest problem in the whole project. An early version of
this model calculated cumulative deployable capacity by summing every
year's ending balance — which double- and triple-counts the same
unused cash as it carries forward. I found that bug, and fixed it, and
then built an explicit proof: every dollar of cash generated has to be
exactly one of five uses — debt repayment, dividends, buybacks,
management-selected deployment, or ending cash — never zero, never two.
This banner right here is that proof, live, for whatever scenario and
year you pick." *Click through a couple of years.*

"There's actually a second correction on top of that one, right up in
the Snapshot cards you saw earlier. The single-year figure was also
double-subtracting mandatory debt repayments and blending internally
generated cash with new borrowing into one ambiguous number. So the
headline now shows four things instead of one: self-funded capacity
generated, debt-funded capacity — always shown separately, never
counted as internally generated cash — discretionary deployment, and
remaining deployable headroom. The old field is still in the data,
relabeled as a deprecated legacy figure, purely for audit trail."

## 5:00-6:30 — DCF and the disclaimer

Scroll to DCF Valuation.

"A restrained, scenario-based DCF — explicit WACC build, a full
valuation bridge, and sensitivity tables. And it's labeled, right here,
as scenario analysis, not a price target — because it isn't one."

## 6:30-8:00 — What-If sandbox

Scroll to the What-If Assumption Sandbox.

"This lets you actually change assumptions and see the model
recompute, live, in the browser — using the exact same formulas as the
published model. At the defaults it reproduces the published numbers to
the dollar; move a slider and it recalculates; hit reset and you're back
to the exact original. It's a small illustration of the bigger point:
every number in this project is reproducible, not just displayed."

## 8:00-9:00 — Close with the evidence

Scroll to Evidence & Sources, then mention (don't need to open)
`docs/decisions.md`.

"Every fact traces to one of 8 SEC filings, cited by accession number.
And separately, there's a decision log — `docs/decisions.md` — that
records every material judgment call and every bug I found and fixed
across the whole project, dated. That log is probably the single best
piece of evidence for how I actually work."

## If asked "what would you change with more time"

Point to `05_model_risk_and_limitations.md`: real debt-maturity data
instead of the current-year-repayment proxy, a live market-data feed for
WACC inputs, and review by someone with direct knowledge of Target's
actual capital-allocation policy.
