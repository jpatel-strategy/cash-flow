# Positioning Note: How to Talk About This Project

## Target roles

FP&A / strategic finance, finance transformation, business operations,
retail operations, supply-chain finance, operations analytics.

## Explicitly NOT the framing

Not a senior ML engineer portfolio piece. Not a software-architecture
portfolio piece. There is no machine learning in this project at all,
and the software architecture (SQLite, a Python pipeline, static HTML/
JS) is deliberately simple, boring, and inspectable — it is a means to
a finance end, not a demonstration of engineering sophistication for its
own sake.

## The correct framing, in one line

"I built the kind of forecasting and capital-allocation model a
strategic-finance or FP&A team would actually build and defend — with
the rigor (validation, lineage, no-double-counting proofs, an honest
limitations statement) that a real finance function is held to — and I
happened to build the supporting tooling myself because I could."

## What to emphasize in an interview or cover letter

- **Financial and operational judgment**: the scenario narratives, the
  CapEx-vs-CFI distinction, the recognition that Upside's lower
  remaining deployable headroom is a feature (more gets deployed) not a
  bug, and never presenting debt-funded capacity as internally
  generated cash.
- **Accounting interpretation**: catching and correctly handling the
  FY2024 10-K's COGS/SG&A reclassification of FY2022-FY2023 figures —
  a real judgment call about what "the same number" means across filing
  vintages.
- **SEC/XBRL evidence discipline**: every fact cites its filing,
  accession number, and XBRL concept — the muscle memory of "where did
  this number come from" that a strong analyst has and a mediocre one
  doesn't.
- **Scenario planning**: three coherent, differently-reasoned business
  narratives, not three multiplied growth rates.
- **Cash and capital-allocation analysis**: the central technical
  contribution of the project (the double-counting bug and its proof-
  based fix) is a finance methodology story, not a coding story — tell
  it that way.
- **Auditability**: the fact that `docs/decisions.md` records every
  material decision and every bug, dated, is itself the strongest single
  piece of evidence for "this person builds things a real finance
  organization could trust."
- **Executive communication**: the four presentation layers (Excel,
  Power BI, web cockpit, this package) exist because a real finance
  deliverable has to reach different audiences — an executive who wants
  30 seconds, an analyst who wants to audit a formula, a BI team that
  needs a handoff spec.

## What to de-emphasize

- The line-count of the codebase, the specific JS charting
  implementation, the database engine choice. None of that is the
  point, and dwelling on it undercuts the FP&A framing.
- Do not present this as "I can code, therefore I can do finance." Flip
  it: "I understand the finance well enough that I could specify exactly
  what needed to be built, and rigorous enough that I built in the
  checks a reviewer would demand."

## One likely pushback, and the answer

**"This is a lot of infrastructure for a case study — why not just use
Excel from the start?"** Because the interesting part of this project —
proving no dollar is double-counted, keeping historical and forecast
data honestly separated, keeping an information cutoff enforceable
rather than just claimed — needed a real, testable pipeline to do
credibly. A single hand-built spreadsheet can *assert* those properties;
this project *proves* them, with 453 automated tests and a from-scratch
clean-room rebuild that reproduces the same numbers. That provability is
the actual deliverable, and it's a finance-rigor argument, not a
software-engineering flex.
