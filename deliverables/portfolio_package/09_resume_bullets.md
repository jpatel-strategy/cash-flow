# Resume Bullets

Pick 2-4 depending on the role and available space. Numbers are real,
drawn from this project's own validated output — do not alter the
figures.

## FP&A / Strategic Finance framing

- Built an independent 3-scenario (Base/Upside/Downside), 5-year cash-
  flow forecast and investment-capacity model for a Fortune 500 retailer
  from public SEC filings, including a capital-allocation framework with
  a proven, non-double-counted conservation identity across five
  mutually exclusive uses of cash.
- Identified and corrected a cumulative-capacity calculation error that
  was overstating deployable cash by 2.6x-3.8x across scenarios;
  designed and implemented an explicit source-and-use reconciliation
  proof to prevent recurrence.
- In a follow-up audit, found and fixed a second capacity-metric defect
  (a single-year figure double-subtracting mandatory debt repayments
  while conflating self-funded cash with new borrowing); redesigned the
  metric into a 14-field taxonomy separating self-funded capacity,
  debt-funded capacity, discretionary deployment, and remaining
  headroom, with an additive database migration and zero changes to
  historical facts or forecast assumptions.
- Discovered and correctly classified a real SEC filing-vintage
  reclassification (~$77-92M moved between cost of sales and SG&A
  across two fiscal years) by cross-validating historical facts across
  multiple 10-K filings rather than relying on a single filing's
  reported figures.
- Built a restrained, scenario-based DCF valuation with an explicit
  WACC build, terminal-value and net-debt consistency checks, and
  sensitivity analysis across discount rate, terminal growth, margin,
  and revenue-growth assumptions.
- Delivered the model across four decision-support formats — a
  15-sheet Excel executive workbook with a live formula-driven scenario
  selector, a Power BI-ready star-schema data package, and an
  interactive web dashboard — for audiences ranging from executives to
  BI developers.

## Finance Transformation / Operations Analytics framing

- Designed and built an end-to-end financial data pipeline (SEC filing
  ingestion → validated historical facts → scenario forecast → DCF
  valuation → executive reporting) with full field-level lineage from
  every output back to its source filing.
- Implemented a reproducibility and audit framework — a clean-room,
  from-scratch rebuild verified byte-identical to production across 28
  database tables and 6,600+ rows, backed by 467 automated tests and a
  dated decision log recording every material judgment call.
- Established a validation taxonomy distinguishing arithmetic
  invariants, structural completeness checks, and genuinely independent
  reasonableness tests — preventing the common modeling error of
  presenting internal consistency as if it were independent validation.

## Shorter, single-line versions (for space-constrained resumes)

- Built and validated a 3-scenario cash-flow/investment-capacity model
  for a Fortune 500 retailer from SEC filings; found and fixed a capacity
  double-counting error overstating deployable cash by up to 3.8x.
- Delivered a scenario-based DCF valuation and capital-allocation
  framework across Excel, Power BI, and web dashboard formats, backed by
  467 automated tests and a reproducible clean-room rebuild.
