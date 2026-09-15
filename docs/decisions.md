# Decision Log

Each entry records a project decision, the date, and the rationale. Entries are
appended, never rewritten, so the reasoning behind a later change stays visible.

## 2026-09-14 — Company and scope

- Company: **Target Corporation**. Fixed per the governing roadmap
  (`docs/Target_Cash_Flow_Final_Execution_Roadmap.docx`). Will not be changed
  without the project owner's explicit written approval.
- CIK: `0000027419` (candidate). This is the widely-cited SEC identifier for
  Target Corporation, but it is being treated as **unverified** until the SEC
  submissions JSON for this CIK is inspected and confirmed to echo back
  `"name": "TARGET CORP"`. No downstream figure should be attributed to Target
  before this check passes.
- Milestone authorized: repository setup + four-quarter data proof only.
  Forecasting, scenarios, Excel, Power BI, and the public website are explicitly
  out of scope until their gates are passed.

## 2026-09-14 — Environment constraint and data-acquisition mode

- This Claude Code remote execution environment has no network egress to
  `data.sec.gov`, `www.sec.gov`, or `investors.target.com` (confirmed via direct
  test — `EGRESS_BLOCKED` by network policy, not a transient failure).
- Per the roadmap's own contingency ("If an environment cannot fetch SEC data,
  use manually downloaded source files with recorded provenance. Never generate
  substitute financial values."), Milestone 1 uses **manual file ingestion**:
  the project owner downloads specific SEC URLs and uploads them; this session
  ingests them with the same lineage/hash recording a live fetch would produce.
- `config/model.yml: data_source.mode = "manual_upload"` records this choice.
  `src/target_cash/fetch.py` still implements a real HTTP fetch path so the
  pipeline is genuinely reproducible for a user running it where SEC access is
  open, per the roadmap's local-terminal workflow.

## 2026-09-14 — Entity identity verified

- **Verification source**: `CIK0000027419-submissions.json`, downloaded by the
  project owner from `https://data.sec.gov/submissions/CIK0000027419.json`
  and uploaded into this session (manual ingestion — see the environment
  constraint entry above). Cross-checked against `CIK0000027419-companyfacts.json`
  (`entityName: "Target Corporation"`, `cik: 27419`), which agrees.
- **CIK**: `0000027419` — **verified**.
- **Entity name**: `TARGET CORP` (submissions) / `Target Corporation` (company facts).
- **Ticker**: `TGT`.
- **Exchange**: `NYSE`.
- **Supporting detail**: `formerNames` includes "DAYTON HUDSON CORP" (1994–1999),
  Target's well-documented legal predecessor name — consistent with the
  entity being the real Target Corporation, not a coincidentally similar filer.
  SIC code 5331 ("Retail-Variety Stores"), state of incorporation MN,
  headquartered in Minneapolis, MN — all consistent with public knowledge of
  Target Corporation.
- `config/model.yml: company.status` updated from `pending_verification` to
  `verified`.

## 2026-09-14 — Filing inventory and proposed proof year (PROPOSED, pending approval)

- The submissions file's `filings.recent` block covers filings dated
  2016-04-25 through 2026-08-28 (1,001 filings; older filings back to
  1994-02-10 live in a separate paginated file not yet retrieved — not needed
  for the current ~16-quarter target range).
- 42 `10-K`/`10-Q` filings identified in that range. Full matrix below.
- **Proposed information cutoff**: `2026-09-14` (today). All filings proposed
  for the four-quarter proof were filed by 2026-03-11, comfortably before
  this cutoff.
- **Proposed proof fiscal year**: **fiscal 2025** (Target's internal label),
  period `2025-02-02` to `2026-01-31` — the most recently complete fiscal
  year with a filed 10-K and all three 10-Qs public, and a clean 52-week/
  13-week-per-quarter year (no 53-week complexity). Not yet activated in
  `config/model.yml` — see the filing matrix and blocking questions delivered
  alongside this entry for the approval request.

## 2026-09-14 — Fiscal year, cutoff, and initial tolerance framework approved, then corrected

- Project owner approved fiscal 2025 as the proof year and `2026-09-14` as the
  information cutoff. Activated in `config/model.yml`.
- Project owner approved a first tolerance framework (four categories:
  directly-reported annual-vs-quarters, YTD-derived annual-vs-quarters, cash
  roll-forward, Excel-vs-Python), which was activated in `config/model.yml`.
- **This framework was superseded the same day** — see the next entry. It is
  recorded here, not deleted, so the reasoning that led to the correction
  stays visible.

## 2026-09-15 — Validation methodology corrected: arithmetic invariants vs. independent validation

The project owner identified a substantive flaw in the approach above and
required it be corrected before any tolerance is treated as permanent. Full
correction implemented in `src/target_cash/reconcile.py`,
`src/target_cash/normalize.py`, `src/target_cash/validation.py`,
`config/model.yml`, and `docs/accounting_policies.md` ("Validation
methodology" section). Summary of the correction:

- **The flaw**: the prior "annual equals sum of quarters" check was reported
  as if it were an independent reconciliation. It is not, whenever the fourth
  quarter is derived as `annual - Q1 - Q2 - Q3` (equivalently
  `annual - nine_month_YTD`) — the equality is then algebraically guaranteed
  by construction, proving only that the subtraction was coded correctly, not
  that the underlying data is accurate. The same conflation applied to
  checking `Q1 + Q2 == six_month_YTD` when Q2 was itself defined as
  `six_month_YTD - Q1`.
- **The fix**: three validation layers, kept structurally distinct and never
  conflated in code, config, or reported output:
  1. **Source compatibility** (`check_source_compatibility`) — a precondition
     on entity, fiscal year, unit, accounting basis, consolidated scope,
     start/end dates, filing version, and sign convention, checked before any
     subtraction is attempted. No numeric tolerance; pass/fail.
  2. **Arithmetic invariant** (`check_arithmetic_invariant`) — confirms a
     derivation formula was applied correctly by recomputing it. Explicitly
     documented as a code-correctness check, never reported as data
     validation. This replaces the old "annual equals quarters" /
     "derived_quarter_calculation" categories.
  3. **Independent quarter validation** (`check_independent_quarter_validation`,
     `check_ytd_consistency`) — the only checks that compare a derived value
     against a fact genuinely not used to produce it: a directly-reported
     discrete quarter (Target files these for revenue and cost of sales,
     confirmed via Company Facts reconnaissance) or a directly-reported YTD
     figure compared against the sum of directly-reported discrete quarters.
     When no independent fact exists — always true for Q4 — the result is
     labeled exactly `"arithmetic invariant passed; independent quarter
     validation unavailable"`, per the project owner's required wording,
     never silently counted as a pass.
- **Tolerance redesign**: `compute_rounding_bound` replaces every flat-figure
  guess with a worst-case propagated-rounding bound derived from how many
  independently-rounded reported facts feed the specific check: each
  directly-reported component contributes half of Target's $1M reporting
  unit ($0.5M); each YTD-derived component contributes twice that ($1.0M),
  since it inherits rounding error from both of its inputs. Worked examples
  in `config/model.yml` and `docs/accounting_policies.md`. The residual is
  always reported, even when it falls inside the bound. Excel-vs-Python
  tolerance stays a separate, flat $0.01M figure, per explicit instruction —
  it tests binary-float-vs-Decimal noise on identical inputs, not propagated
  filing-rounding, so the rounding-bound method does not apply to it.
- `config/model.yml: reconciliation_tolerance` rewritten accordingly; the
  approved-then-superseded framework above is no longer active.

## 2026-09-15 — Uploaded "FY2025 10-K" was actually SEC's automated-traffic block page

The file uploaded as Target's FY2025 10-K (`tgt-20260131-10k.htm`) is not the
filing — its content is SEC's `"Your Request Originates from an Undeclared
Automated Tool"` rate-limit/block page, meaning whatever process fetched it
was blocked by SEC before it could retrieve the real document. Per the
project's standing rule that missing data is not zero and unverified claims
are never treated as reported facts: none of the project owner's stated
figures for cash, D&A, the net-income bridge, or accounts payable have been
independently confirmed against the actual statement, even though several
match this session's earlier Company Facts reconnaissance. A properly-fetched
copy (a normal browser session viewing/saving the page, not a script) has
been requested. Findings A–D from the project owner's message remain
**open**, not resolved, until that document is inspected directly.

## Pending decisions (not yet made — recorded so they aren't quietly defaulted)

- **Cash mapping** (finding A): which of `Cash`, `CashCashEquivalentsAndShortTermInvestments`,
  or `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` backs the
  actual balance-sheet "Cash and cash equivalents" line and the cash-flow
  statement's roll-forward line — blocked on inspecting the real 10-K (see
  2026-09-15 entry above); do not select a tag on value-match alone.
  Preserve all candidate tags in `raw_facts` regardless of which is selected.
- **D&A treatment** (finding B): whether/how the $3,134M cash-flow add-back
  and the $2,617M income-statement line (exclusive of D&A in cost of sales)
  are both represented without double-counting D&A as an operating expense —
  blocked on the real 10-K's statement presentation.
- **Net-income bridge** (finding C): whether a ~$95M net-other-income line
  reconciles operating income to net earnings — blocked on the real 10-K.
- **Accounts payable gap** (finding D): cause of the Q1/Q3 FY2025 gaps between
  the reported `IncreaseDecreaseInAccountsPayable` YTD figure and the
  balance-sheet point-in-time delta. Explicitly **not** attributed to the
  purchases-proxy approximation — book overdrafts and supplier-finance
  (payables factoring) arrangements are noted as possible reconciling items,
  to be checked against the relevant 10-Q statements and notes. Left
  unresolved until then.
- **Net income method** (explicit interest/tax vs. net-margin simplification):
  deferred to the driver-model milestone; must not be decided until the
  income-statement presentation is inspected for embedded D&A.
