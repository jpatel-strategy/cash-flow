# Executive Case Study: Target Corporation Cash Flow & Investment Capacity Model

## The problem

Corporate finance teams routinely need to answer a deceptively hard
question: **how much cash can we safely deploy toward buybacks, debt
paydown, or new investment — without threatening the minimum cash the
business needs to run, and without double-counting the same dollar
across two different "uses"?** Getting this wrong in either direction is
costly: too conservative, and capital sits idle; too aggressive, and a
seasonal cash trough (a real and material feature of Target's business)
creates funding risk.

This project builds that answer for Target Corporation (NYSE: TGT), from
public data only, with the same rigor a real strategic-finance function
would demand: an explicit information cutoff, an auditable chain from
SEC filing to final number, and provable — not asserted — absence of
double counting.

## Scope and constraints (deliberately, not accidentally, tight)

- **Public data only.** Every fact traces to one of 8 registered SEC
  filings (5 10-Ks, 3 10-Qs), listed with accession numbers in
  `docs/sources.csv`.
- **A hard information cutoff** at the FY2025 10-K (filed 2026-03-11).
  No later filings, no analyst estimates, no hindsight — enforced
  programmatically, not just by intention.
- **No fabricated values.** Where a driver isn't disclosed (e.g. a debt
  maturity ladder, or non-CapEx investing detail), the model says so
  explicitly and uses a documented, conservative proxy — never a
  plausible-looking guess presented as fact.

## What was built

1. **Historical fact extraction and validation** (Milestones 1-2): every
   FY2021-FY2025 financial fact ingested from source filings, validated
   against internal arithmetic identities, and reconciled across filing
   vintages. This step caught a **real finding**: Target's FY2024 10-K
   reclassified roughly $77-92M between cost of sales and SG&A for
   FY2022 and FY2023, with zero revenue or net-income impact. The model
   flags this explicitly rather than silently absorbing it — most
   simplified financial models would never surface this at all.
2. **A 3-scenario, 5-year operating forecast** (Milestone 3): Base,
   Upside, and Downside cases, each built from named, sourced
   assumptions (not a single blanket growth rate), each with a coherent
   business narrative (e.g. Downside is a continued discretionary-
   spending slowdown with a dividend freeze, not a cut — not a
   mechanical "everything gets worse" toggle).
3. **A provably non-double-counted investment-capacity framework**
   (Milestone 3A/3B): the project's hardest problem. An early version of
   the cumulative deployable-capacity calculation summed each year's
   ending capacity balance — which silently re-counts the same unused
   cash carried forward year after year, overstating true deployable
   capacity by **roughly 2.6x-3.8x** depending on scenario. Caught,
   diagnosed, and fixed, with an explicit conservation-identity proof
   (`beginning cash + CFO + CFI + debt proceeds = debt repayments +
   dividends + repurchases + deployment + ending cash`) that every
   scenario/year satisfies exactly. A second, independent review later
   found that the same single-year figure was also conflating internally
   generated (self-funded) capacity with new borrowing, and was silently
   double-subtracting mandatory debt repayments — corrected by splitting
   the metric into **self-funded capacity generated**, **debt-funded
   capacity** (shown separately, never as internally generated cash), and
   **remaining deployable headroom**. A third review found even that
   correction still labeled *gross* debt issuance as capacity even when
   the same cash was simultaneously repaid — fixed by netting debt-funded
   capacity to proceeds *in excess of* repayments (zero when they're
   equal or repayments are larger), excluding opening liquidity entirely
   from "capacity generated," and reserving a forward year's known debt
   service before calling the residual "headroom"; see
   `docs/investment_capacity_correction_evidence.md`.
4. **A restrained DCF valuation** (Milestone 4): explicit WACC build,
   Gordon Growth terminal value, and a valuation bridge to per-share
   value — with checks preventing the two most common DCF errors
   (terminal-value period mismatch, and net-debt/finance-lease double
   counting), and an explicit label as scenario analysis, never a price
   target.
5. **Four presentation layers**: a 15-sheet Excel executive workbook
   with a live, formula-driven scenario selector (Milestone 5); a
   Power-BI-ready star-schema handoff package (Milestone 6); a
   responsive web decision cockpit with an editable what-if sandbox
   (Milestone 7); and this recruiter package (Milestone 8).

## Key results (Base / Upside / Downside, FY2030)

| Metric | Base | Upside | Downside |
|---|---|---|---|
| Revenue | $110,125M | $121,469M | $92,321M |
| Diluted EPS | $8.18 | $13.15 | $2.71 |
| Opening Excess Liquidity (stock, separate) | $5,424M | $2,218M | $6,158M |
| Self-Funded Capacity Generated | $1,591M | $2,024M | $30M |
| Debt-Funded Capacity (net of repayment) | $0M | $0M | $200M |
| Discretionary Deployment | $636M | $1,498M | $0M |
| Forward Debt-Repayment Reserve | $0M | $700M | $0M |
| Remaining Deployable Headroom | $6,379M | $2,044M | $6,388M |
| Implied DCF Value/Share | $107.29 | $138.32 | $61.55 |

Note the counterintuitive result: Upside shows *lower* remaining
headroom than Base, despite generating more self-funded capacity —
because Upside deploys far more of it (higher buyback payout, faster
deleveraging) rather than letting it sit idle, *and* it carries a real
$700M forward reserve for a known FY2031 debt repayment that exceeds
that year's expected proceeds. A model that only showed "capacity went
up" without this context would mislead a decision-maker; this one shows
the full waterfall, with debt-funded capacity always net of simultaneous
repayment (Base and Upside both show $0 here despite $700M/$300M of
gross issuance, because each is fully offset by an equal-or-larger
repayment in the same year) and opening liquidity always broken out as
a separate stock, so the tradeoff is visible. (Legacy `Deployable
Capacity` figure, kept only as deprecated methodology evidence: $6,315M
/ $3,242M / $6,088M — see the correction evidence doc for the full
before/after derivation.)

## Why this matters for a finance role, not a software role

The hard parts of this project were never the code — they were the
finance judgment calls: what counts as CapEx versus total investing
cash flow (never the same number, and conflating them is a real error
this project explicitly avoids); how to define investment capacity
without double-counting and without conflating internally generated
cash with new borrowing; how to keep a DCF's valuation date consistent
with its balance-sheet inputs; how to write a scenario narrative that
reads as a coherent business story rather than a mechanical dial-turn.
Those are FP&A and strategic-finance skills. The code is the vehicle,
not the point.

## Full evidence trail

Every material decision, every bug found and fixed, and every
limitation accepted along the way is recorded, dated, in
`docs/decisions.md` — an unusually complete audit trail for a portfolio
project, and itself evidence of the auditability this project is meant
to demonstrate.
