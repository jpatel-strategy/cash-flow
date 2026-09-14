# Known Limitations

This file is updated as limitations are discovered, not just at release. It is
part of every milestone report, not a one-time disclaimer.

## Scope boundaries (fixed by the governing roadmap)

This project is an **external, public-data case study**. It is not, and must
never be represented as:

- Target's internal forecast, budget, or consulting work performed for Target
- A recommendation to buy or sell Target securities
- Evidence that Target adopted or uses this model
- A store-level or SKU-level operating plan, or a daily treasury forecast
- A claim that a proposed investment would generate returns

## Environment limitation (Milestone 1)

This Claude Code remote execution environment cannot reach `data.sec.gov`,
`www.sec.gov`, or `investors.target.com` (blocked by network egress policy).
Historical data acquisition for Milestone 1 therefore relies on the project
owner manually downloading specific SEC URLs and uploading them into this
session, rather than this session fetching them directly. `fetch.py` still
implements a genuine HTTP client for environments where SEC access is open.

## Data coverage (Milestone 1)

- Only one complete fiscal year (4 quarters) is targeted for the first data
  gate — not yet the ~16 quarters the full project calls for.
- CIK `0000027419` is **verified** as Target Corporation (see
  docs/decisions.md, 2026-09-14 entry) via the SEC submissions file.
- XBRL tag mappings in `config/metrics.csv` are candidates from general
  US-GAAP taxonomy knowledge, marked `candidate_unverified`. Company Facts
  reconnaissance (docs/decisions.md) found real gaps a name-based guess would
  have missed — e.g. `CashAndCashEquivalentsAtCarryingValue` has zero entries
  for Target; the balance-sheet cash line is tagged differently, and multiple
  candidate cash tags currently produce identical values for reasons not yet
  confirmed from the actual statement. None of these candidates is active
  until checked against Target's actual filing statements, contexts, and sign
  conventions, per the project owner's explicit standing instruction.

## Not yet built

Forecasting, seasonal baseline, driver model, scenarios, investment-capacity
calculation, backtesting, Excel workbook, Power BI exports, and the public
Investment Decision Room are all out of scope until their respective
milestones are authorized and their upstream gates pass.
