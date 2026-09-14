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

## Pending decisions (not yet made — recorded so they aren't quietly defaulted)

- **Information cutoff date**: cannot be fixed until the SEC filing inventory
  (submissions JSON) is available and we can see what was actually public by a
  candidate cutoff.
- **Proof fiscal year**: which complete fiscal year (4 quarters + opening cash)
  to use for the first data gate — deferred until the filing inventory is seen.
- **Reconciliation tolerance**: placeholder of $1.0M absolute / 0.5% relative in
  `config/model.yml`; to be revisited once real filings show Target's actual
  reporting precision.
- **Net income method** (explicit interest/tax vs. net-margin simplification):
  deferred to the driver-model milestone; must not be decided until the
  income-statement presentation is inspected for embedded D&A.
