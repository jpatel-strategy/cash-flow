# Interview Explanations

## 30-second version

"I built a full cash-flow forecasting and investment-capacity model for
Target Corporation, entirely from their public SEC filings. It covers
historical validation, a 3-scenario 5-year forecast, and a capital-
allocation framework where I found and fixed a real double-counting bug
that was overstating deployable cash by 2-4x — then built an explicit
proof that it doesn't happen anymore. I packaged it into an Excel model,
a Power BI handoff, and a web dashboard, all backed by automated tests
and a from-scratch reproducible build."

## 2-minute version

"I built an independent FP&A case study for Target Corporation, using
only their public SEC filings — five 10-Ks and three 10-Qs. The goal
was to answer a real strategic-finance question: how much cash can a
business safely deploy toward buybacks, debt paydown, or investment,
without touching the minimum cash it needs to operate, and without
double-counting the same dollar twice?

"I started with historical fact extraction and validation, which
actually caught something real: Target's FY2024 10-K quietly
reclassified about $77 to $92 million between cost of sales and SG&A
for two prior fiscal years, with zero impact on revenue or net income.
Most simplified models would never surface that.

"Then I built a 3-scenario, 5-year forecast — Base, Upside, and
Downside — each with named, sourced assumptions and a coherent business
narrative, not just a multiplied growth rate. The hardest part was the
investment-capacity framework: an early version of my 'cumulative
deployable capacity' calculation was summing each year's ending balance,
which silently re-counts the same unused cash every year it carries
forward. I caught that, it was overstating capacity by roughly 2.6 to
3.8 times depending on scenario, and I fixed it and then built an
explicit conservation-identity proof — every dollar generated has to be
exactly one of five uses, provably, for every scenario and year. A later
review found a second, more subtle issue in the same area: the
single-year capacity figure was double-subtracting mandatory debt
repayments and blending self-funded cash with new borrowing into one
ambiguous number. I split it into self-funded capacity, debt-funded
capacity shown separately, discretionary deployment, and remaining
headroom — and kept the old field in the data, clearly relabeled as
deprecated, so nothing about the historical record silently changed.

"On top of that I built a restrained DCF valuation, clearly labeled as
scenario analysis and not a price target, and then four ways to consume
the whole thing: a 15-sheet Excel model with a live scenario selector, a
Power BI-ready data package, a web dashboard with an interactive what-if
sandbox, and a written case study.

"The whole thing is backed by 401 automated tests and a clean-room
rebuild script that reproduces the entire database from scratch, from
just the source filings — so every number in it is provably
reproducible, not just displayed. And I kept a full decision log the
whole way through, recording every judgment call and every bug I found,
which I think is the strongest evidence of how I actually approach this
kind of work."

## If pressed: "Why does this matter for an FP&A/strategic-finance role
specifically, not a technical role?"

"Because the hard parts were never the code. They were things like:
never letting CapEx get confused with total investing cash flow;
writing a scenario that reads as a real business story instead of a
dial-turn; catching a filing-vintage reclassification instead of
silently averaging over it; and proving — not just asserting — that a
capital-allocation model doesn't double-count cash. Those are the
judgment calls a strategic-finance function is actually paid for. The
software is just how I made those judgment calls checkable."
