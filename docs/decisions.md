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

## 2026-09-15 — Validation methodology extended: additional compatibility dimensions and independence checks

The project owner required `check_source_compatibility` to also check exact
start/end dates, period adjacency, duration, concept identity (or an
explicitly approved equivalence), dimensional context, unit, scale,
consolidated scope, accession, and filing version — and required every
independent-validation result to record whether its "independent" side
actually overlaps with the facts that produced the derived value, refusing
to label a comparison independent if it does. Implemented in
`src/target_cash/reconcile.py` and `src/target_cash/normalize.py`:

- `check_source_compatibility` gained `concept_a/b` (the exact XBRL tag,
  checked for identity or membership in a caller-supplied
  `approved_equivalent_concepts` allowlist — empty by default, so no tag
  substitution is permitted without a documented, reviewed exception),
  `scale_a/b` (the XBRL `scale` attribute), and `end_date_a/b` (checked for
  **period adjacency**: by the convention `normalize.py` already uses — `a`
  is the longer/later-ending period, `b` the shorter — `end_date_b` must
  fall strictly before `end_date_a`, given both share the same start date).
  Every failed dimension is still reported together, not just the first.
- `PeriodSpec` gained `concept` and `scale` fields so `_assert_compatible`
  can pass them through to the same shared check.
- `check_independent_quarter_validation` and `check_ytd_consistency` gained
  fact-id parameters (`derived_input_fact_ids`/`independent_fact_ids` and
  `ytd_fact_ids`/`quarter_fact_ids` respectively). Any overlap produces a new
  status, `"not_independent"`, which `ValidationSummary.passed` treats as a
  gate failure exactly like `"failed"` — a comparison that secretly reuses an
  input fact is never allowed to read as a validated pass, whatever the
  values show.
- Test suite grew from 64 to 74 (concept mismatch, approved equivalence,
  scale mismatch, period-adjacency pass/fail/reversed, and overlap-detection
  cases for both independent-validation functions and the gate itself). Full
  observed results below.

"Accession" and "filing version" were already tracked (`accession_number`,
`is_superseded` on `PeriodSpec`) — accession is recorded for lineage/audit on
every fact but is **not** required to be identical between two combined
facts (Q1 and a 6-month YTD figure routinely come from different 10-Q
filings by design); filing version (`is_superseded`) is the dimension that
actually gates on restatement consistency. "Duration" is not a separate
numeric check: it falls out of the start/end-date and period-adjacency
checks together, since a period's duration is fully determined by its own
start and end dates.

## 2026-09-15 — Real FY2025 10-K obtained and verified; findings A–C resolved, D partially resolved

A properly browser-fetched copy of the FY2025 10-K primary document
(`tgt-20260131-10k.htm`, 2,059,294 bytes — the earlier upload was 1,331 bytes
of SEC block-page HTML) was inspected directly, including its inline-XBRL
markup (not just visible text), to avoid selecting a tag by value match
alone.

**Document verification** (all confirmed from the file's own content, not
asserted):
- `dei:EntityRegistrantName` = "TARGET CORPORATION"; `dei:EntityCentralIndexKey`
  = "0000027419"; `dei:TradingSymbol` = "TGT"; `dei:SecurityExchangeName` =
  "New York Stock Exchange"; `dei:EntityFileNumber` = "1-6049" (Target's
  known, long-standing SEC file number); `dei:DocumentType` = "10-K".
- Cover page reads "For the fiscal year ended January 31, 2026."
- No "Undeclared Automated Tool" text anywhere in the file.
- Consolidated Statements of Operations, Financial Position, and Cash Flows
  all present in full, with figures matching this session's earlier Company
  Facts reconnaissance exactly (e.g. net sales $104,780M / $106,566M /
  $107,412M for 2025/2024/2023).
- **Not directly verifiable from the primary document alone**: the accession
  number `0000027419-26-000016` does not appear as literal text inside the
  primary statement document (normal — accession numbers live in the filing
  index/submission wrapper, not the statement body). Identity is instead
  corroborated by every other independently-checkable signal above matching
  exactly what the SEC submissions file already reported for that accession
  (form 10-K, period 2026-01-31, filed 2026-03-11).

**Finding A (cash) — resolved.** Two distinct, both-legitimate XBRL concepts,
identified by inspecting the actual `<ix:nonFraction>` markup, not by value:
- Balance sheet "Cash and cash equivalents" ($5,488M at 2026-01-31; $4,762M
  at 2025-02-01) is tagged `us-gaap:CashCashEquivalentsAndShortTermInvestments`,
  contexts c-6 (instant 2026-01-31) and c-7 (instant 2025-02-01), entity
  0000027419, no dimensional segment.
- Cash-flow statement's beginning/ending-of-period reconciliation line uses
  `us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` at
  the same instants (contexts c-6/c-7/c-8/c-9, chaining year to year).
- These two concepts are numerically **identical** for Target only because
  Target discloses zero restricted cash — not because they are the same tag.
  Note 9 ("Cash and Cash Equivalents") confirms the $250M/$276M figure the
  project owner referenced is the "Cash" sub-line within the note's
  composition table (Cash + card-transaction receivables $627M/$593M +
  short-term investments $4,611M/$3,893M = the $5,488M/$4,762M total) —
  exactly as the project owner stated, now confirmed from the primary
  document rather than accepted on assertion.
- `config/metrics.csv` to be updated to map `cash_and_equivalents` (balance
  sheet) to `CashCashEquivalentsAndShortTermInvestments` and a new
  cash-roll-forward-specific mapping to
  `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents`, once
  ingestion resumes — not yet activated (still Milestone 1 pre-ingestion).

**Finding B (D&A) — resolved.** The Statement of Operations line itself is
titled "Depreciation and amortization (**exclusive of** depreciation
included in cost of sales)" — the statement's own wording confirms D&A is
partially embedded in cost of sales. Tagged `us-gaap:DepreciationAndAmortization`
(context c-1, FY2025 = $2,617M; c-4, FY2024 = $2,529M; c-5, FY2023 = $2,415M).
The cash-flow add-back is a different concept,
`us-gaap:DepreciationDepletionAndAmortization` (same contexts, $3,134M /
$2,981M / $2,801M) — the total, including the cost-of-sales-embedded portion
(~$517M for FY2025). **The $3,134M figure must never be inserted as a second
income-statement operating expense** — $2,617M of D&A is already reflected
across cost of sales and this exclusive-of-COGS line; $3,134M is used only as
the non-cash CFO add-back.

**Finding C (net income bridge) — resolved and confirmed exactly.** From the
Statement of Operations: Operating income $5,117M − Net interest expense
$445M + Net other income $95M (shown in parentheses as a contra-expense,
i.e. added back) − Provision for income taxes $1,062M = Net earnings $3,705M.
Arithmetic: 5,117 − 445 = 4,672; 4,672 + 95 = 4,767 (= Earnings before income
taxes, as reported); 4,767 − 1,062 = 3,705 (= Net earnings, as reported).
Exact match, no residual.

**Finding D (accounts payable) — partially resolved; interim-quarter gaps
remain open.** The 10-K's Note 9 discloses **book overdrafts included in
Accounts Payable**: $221M at 2026-01-31 and $157M at 2025-02-01. Removing
the book-overdraft component from each balance-sheet AP figure narrows the
annual reconciling gap from $70M to $6M (balance-sheet AP delta −$431M;
less the +$64M book-overdraft change = −$495M trade-payables-only delta,
vs. the reported annual `IncreaseDecreaseInAccountsPayable` of −$501M — a
$6M residual, not fully explained, but far smaller). Also disclosed: Note 14
"Supplier Finance Programs" — vendor obligations eligible for early payment
were $3,666M (2025-02-01) and $3,026M (2026-01-31); the note states these
obligations, whether or not a vendor elects early payment, remain in
Accounts Payable at their invoiced amount and payment date — this affects
disclosure/risk framing more than the cash timing itself. **The Q1 and Q3
FY2025 interim gaps identified earlier are still unresolved** — this 10-K
only discloses book-overdraft balances at the two fiscal year-end dates, not
at 2025-05-03 or 2025-11-01, so confirming the interim-period gaps requires
the corresponding 10-Q filings' own Note disclosures, not yet obtained.
`IncreaseDecreaseInAccountsPayable`'s sign is confirmed directly from the
markup: the FY2025 annual fact carries an explicit `sign="-"` attribute on
its `<ix:nonFraction>` element (displayed magnitude 501, true value −501),
confirming the sign-reading approach must use the XBRL `sign` attribute
directly rather than infer polarity from context.

## 2026-09-15 — FY2025 10-K preserved, hashed, registered, and raw-ingested

Per the project owner's explicit, itemized authorization ("Proceed with a
controlled continuation of Milestone 1 under the following authorization").

**Source preservation check performed first**, as required, before any
action: file existence (`data/raw/` held only `.gitkeep` — not yet copied),
`git status` (clean, nothing pending), source manifest (`docs/sources.csv`
header row only, 0 data rows), database (`filings`/`raw_facts`/
`quarterly_facts`/`lineage`/`assumptions`/`forecasts` all 0 rows). Confirmed
the file had genuinely not yet been preserved, matching the prior session's
stated status.

**Preservation**: `data/raw/tgt-20260131.htm` (2,059,294 bytes), SHA-256
`20bc4552dcb1df7c0bbd837f721de931e2ab4cdd2cb2e3c147f335d41eb68a52`,
independently re-verified with `sha256sum` after ingestion (matches the
manifest exactly). Registered once in `docs/sources.csv` and the `filings`
table — `append_source_manifest` and the `fetch` CLI command were both
hardened this session to raise/refuse rather than silently duplicate a
record for an accession already registered (see below). A first `fetch`
attempt partially completed (file copied, CSV manifest row written) before
failing on a stale database schema missing the new `cached_filename` column
(added this session — see "Validation methodology extended" pattern of
schema evolution while `raw_facts`/`quarterly_facts` were still 0 rows, so
no migration was needed, just a clean recreate). Remediated by recreating
the database against the corrected schema and inserting the matching
`filings` row directly from the already-correct CSV manifest — **no second
manifest row or duplicate database record was created**.

**Raw ingestion**: `src/target_cash/xbrl.py` gained `parse_xbrl_contexts`
and `parse_inline_xbrl_facts`, extracting `<ix:nonFraction>` facts and
resolving their `<xbrli:context>` definitions (entity, start/end or instant
date, dimensional segment) directly from the cached HTML — this is what let
this session distinguish the two same-valued cash concepts and confirm the
D&A split by inspecting actual markup rather than Company Facts values.
`cli.py`'s `normalize` command now runs this extraction against every
cached filing with a recorded `cached_filename`, for every concept named in
`config/metrics.csv` (all 24 rows' candidate tags, not only reviewed ones —
raw ingestion is deliberately broad). Result: **115 raw_facts rows** across
19 distinct concepts (5 of the 24 configured candidate tags — `GrossProfit`,
`OperatingExpenses`, `InterestExpense`, `PaymentsOfDividends`,
`LongTermDebtNoncurrent` — have zero matches in this filing, consistent
with this session's earlier finding that Target does not use those exact
tags; `interest_expense`'s row is now annotated that the real tag is
`InterestExpenseNonoperating`, not corrected in this round as it was outside
the authorized scope). Every candidate context and dimension was preserved,
including genuine dimensional facts (e.g. revenue by merchandise category,
D&A/tax/net-income also tagged under Target's formal single-`ReportableSegmentMember`
axis, net income under `RetainedEarningsMember` from the equity roll-forward) —
none discarded. Repeated identical `(accession, concept, context)` triples
from the same fact being rendered in multiple statements collapse to one
`raw_facts` row each (`fact_id = accession:concept:context`, `INSERT OR
IGNORE`) — this is deduplication of the *same* fact appearing verbatim
multiple times in the document, not selection between *competing* candidates,
which remain fully separate rows. **`quarterly_facts` stays at 0 rows** —
not touched, per explicit instruction; a single annual filing has no
quarters to derive.

**Mappings activated** (`config/metrics.csv`, `mapping_status: reviewed`),
split into distinct metrics exactly as instructed, never merged:
- `cash_and_equivalents_balance_sheet` → `us-gaap:CashCashEquivalentsAndShortTermInvestments`
- `cash_and_equivalents_rollforward` → `us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents`
- `depreciation_amortization_opex` → `us-gaap:DepreciationAndAmortization`
- `depreciation_amortization_cfo_addback` → `us-gaap:DepreciationDepletionAndAmortization`

Each row's `notes` field carries the full confirming evidence (context,
values, statement location) inline, cross-referencing this entry.

**Net-other-income evidence** (conditionally approved; **not** marked
reviewed — added to `config/metrics.csv` as a new `candidate_unverified` row
pending the project owner's own confirmation):

| Field | Value |
|---|---|
| Taxonomy | us-gaap |
| Tag | OtherNonoperatingIncomeExpense |
| Context ID | c-1 |
| Start date | 2025-02-02 |
| End date | 2026-01-31 |
| Unit | USD (unitRef="usd") |
| Scale | 6 |
| Fiscal year / period | FY2025 (Target's internal label), full year (364-day, 52-week year) |
| Accession | 0000027419-26-000016 |
| Statement location | Consolidated Statements of Operations, "Net other income" line, between "Net interest expense" and "Earnings before income taxes" |
| Raw tagged value | 95 (true value after scale: 95,000,000) |
| Presentation sign | Displayed in parentheses, "(95)", on the rendered statement |
| Internal normalized sign | **Positive / additive.** The `<ix:nonFraction>` element carries **no** `sign="-"` attribute (unlike `IncreaseDecreaseInAccountsPayable`'s explicit `sign="-"` on this same statement) — the raw tagged value is already +95,000,000. The parentheses are a presentation/typographic convention in Target's rendering, not a sign-attribute-driven negation. Confirmed independently by exact reproduction of the reported bridge: Operating income 5,117 − Net interest expense 445 + Net other income 95 − Provision for income taxes 1,062 = Net earnings 3,705 (exact). |
| Competing candidates | Only `us-gaap:InterestExpenseNonoperating` (already the separate confirmed "Net interest expense" line) and `us-gaap:RentalIncomeNonoperating` (a narrower, unrelated note-level concept) appear anywhere in the document under a similarly-scoped name; neither is a genuine competitor. |
| Selection rationale | (a) tag appears exactly once at the precise statement location, confirmed by direct markup offset; (b) its context matches the FY2025 annual period already confirmed for every neighboring line on the same statement; (c) its value combines with every neighboring confirmed line to reproduce reported Net earnings exactly. |

Confirms explicitly: the tag **is** `us-gaap:OtherNonoperatingIncomeExpense` — no other concept is in contention.

## 2026-09-15 — Pre-10-Q-ingestion corrections (project owner directive)

Four corrections required before ingesting the FY2025 10-Qs:

1. **Net other income → reviewed.** Project owner confirmed raw-fact
   `0000027419-26-000016:us-gaap:OtherNonoperatingIncomeExpense:c-1` is the
   consolidated FY2025 Statement of Operations fact with no dimensional
   members (context c-1, no `dimensional_context`), per the evidence record
   already gathered. `config/metrics.csv`'s `net_other_income` row moved to
   `reviewed`.
2. **Interest expense tag corrected.** `interest_expense`'s
   `candidate_xbrl_tag` changed from `InterestExpense` (confirmed absent
   anywhere in accession 0000027419-26-000016 by exhaustive tag scan) to
   `InterestExpenseNonoperating` (the actual "Net interest expense" line;
   context c-1 = $445M FY2025). Competing candidates considered and
   rejected: `FinanceLeaseInterestExpense` (narrower, lease-specific) and
   `InterestPaidNet` (cash-paid supplemental disclosure, not the
   accrual-basis income-statement expense). Left `candidate_unverified` —
   not reviewed until cross-checked against the FY2025 10-Qs too, as
   instructed. Re-ran `normalize` against the already-cached 10-K afterward
   to backfill the 6 `InterestExpenseNonoperating` raw_facts this correction
   now finds (`raw_facts_stored` 115 → 121); this reran extraction against
   an already-registered filing, not a new fetch, so no manifest or
   `filings` duplication resulted.
3. **Database safety.** New `src/target_cash/migrations.py`:
   `apply_safe_migrations` tracks applied migrations in a
   `_schema_migrations` table and applies only additive `ALTER TABLE ...
   ADD COLUMN` changes, each idempotent and safe against a populated table.
   A migration marked `is_safe_additive=False`, or one whose target table
   doesn't exist, raises `UnsafeMigrationError` with instructions rather
   than guessing. `cli.py: _connect_db` now calls this after running
   `schema.sql`/`views.sql`, on every connection — a stale schema (like the
   one that caused the earlier `fetch` failure) is now fixed automatically
   and safely instead of requiring a manual database recreate. Reproduced
   the exact failure scenario in `tests/unit/test_migrations.py` (a
   `filings` table built without `cached_filename`, populated with a row)
   and confirmed the migration adds the column and preserves the row.
4. **Consolidated fact selection.** New `normalize.select_consolidated_fact`
   (plus `RawFactCandidate`, `SelectionError`): given a pool of same-concept,
   same-period raw facts, returns the one consolidated
   (`dimensional_context is None`) candidate, or raises if zero or more than
   one exist — even when multiple consolidated candidates agree in value,
   since agreement isn't evidence of which is authoritative. Dimensional
   facts (segment, product-category, equity-rollforward member) are
   excluded outright and never summed as a substitute for a missing
   consolidated total. Tested against a fixture modeled on the real FY2025
   revenue-by-category disclosure, deliberately constructed so the
   dimensional facts do NOT sum to the consolidated value — catching a
   summing bug that coincidentally-correct real data wouldn't have caught.
   Not yet wired into any CLI command: there is nothing to derive yet, since
   `quarterly_facts` population remains unauthorized this round.

Test suite after these four changes: 104 passed, 0 failed.

## 2026-09-15 — FY2025 Q1/Q2/Q3 10-Qs preserved and raw-ingested

Three genuine primary 10-Q documents, verified via dei: tags before any
action (EntityRegistrantName=TARGET CORPORATION, EntityCentralIndexKey=
0000027419, DocumentType=10-Q, matching DocumentPeriodEndDate/FiscalYearFocus/
FiscalPeriodFocus for each; no automated-tool block text in any of them):

| Quarter | Accession | File size | SHA-256 |
|---|---|---|---|
| Q1 | 0000027419-25-000101 | 905,500 bytes | `311e843fc262a7581e2cfe74a50462518ee6f730ad261df3029087a126ac285a` |
| Q2 | 0000027419-25-000118 | 1,091,380 bytes | `e7f3042830970f676c97db753117042c49559a9c0b2dfbbabf2d1302bf18b2ce` |
| Q3 | 0000027419-25-000126 | 1,154,612 bytes | `7003df602996b3e3649b5eac3e409e2e0f9b024de9d24a3a7a57c28be9afb43d` |

All three hashes independently re-verified with `sha256sum` after caching,
matching the manifest exactly. Each registered exactly once in
`docs/sources.csv` and the `filings` table (4 total filings now, one per
accession, `append_source_manifest`'s and `fetch`'s duplicate guards held
throughout with no rejections needed — no retries were required this
round).

**Raw ingestion** (`normalize`, run once for all four cached filings
together): `raw_facts` grew from 121 to 528 (+407: 95 from Q1, 155 from Q2,
157 from Q3; the 10-K's own re-scan found 144 facts — up from 138 now that
`InterestExpenseNonoperating` is searched for — but inserted 0 new rows,
correctly idempotent). **Zero ambiguous consolidated-fact groups**: querying
every `(accession, tag, start_date, end_date)` combination among
dimensionless raw facts found exactly one consolidated context in all 237
groups — `select_consolidated_fact` would resolve every one of them
cleanly. Zero-match configured concepts across all four filings:
`GrossProfit`, `LongTermDebtNoncurrent`, `OperatingExpenses`,
`PaymentsOfDividends` (Target does not use these exact tags — consistent
with earlier findings; `InterestExpense` dropped off this list now that the
tag correction above finds real matches).

**Cross-filing consistency confirmed** (a genuine check made possible only
once multiple filings covering the same point-in-time exist): every
comparative balance repeated across filings matches exactly — cash at
2025-02-01 ($4,762M) and at 2024-02-03 ($3,805M) agree across the 10-K and
all three 10-Qs; accounts payable at 2025-02-01 ($13,053M) agrees across all
four. No cross-filing discrepancy found in any of these overlaps.

**Accounts-payable interim gap (finding D) — still open, and now explained
why it can't be closed from these filings.** Searched all three 10-Qs for
"book overdraft" (the disclosure that narrowed the 10-K's own annual gap
from $70M to $6M) — **absent from all three**; Target discloses that
breakdown only in the annual 10-K, not quarterly. Confirmed interim gaps
from the now-ingested raw facts (previously estimated from Company Facts):
Q1 FY2025 balance-sheet AP delta $11,823M − $13,053M = −$1,230M vs. reported
`IncreaseDecreaseInAccountsPayable` −$1,344M (gap $114M); Q3 FY2025 9-month
delta $13,792M − $13,053M = +$739M vs. reported +$658M (gap $81M). Left
`candidate_unverified`; not attributed to the purchases proxy.

**No `quarterly_facts` derivation performed** — 0 rows before and after, as
instructed; a four-filing mapping and context-selection matrix awaits
approval before that step begins.

Test suite after ingesting all three 10-Qs: 104 passed, 0 failed.

## Pending decisions (not yet made — recorded so they aren't quietly defaulted)

- **Findings A, B are activated** (`cash_and_equivalents_balance_sheet`,
  `cash_and_equivalents_rollforward`, `depreciation_amortization_opex`,
  `depreciation_amortization_cfo_addback` all `reviewed` — see "FY2025 10-K
  preserved, hashed, registered, and raw-ingested" above). **Finding C
  (net-other-income) stays `candidate_unverified`** — evidence gathered and
  recorded, but the project owner has not yet confirmed it for review.
- **Accounts payable — explicitly NOT approved for review.** The annual
  FY2025 gap is substantially (not fully) explained by disclosed book
  overdrafts embedded in the Accounts Payable balance (residual narrowed
  from $70M to $6M — see above). The **Q1 and Q3 FY2025 interim gaps remain
  unresolved**: this 10-K only discloses book-overdraft balances at fiscal
  year-end dates, not at 2025-05-03 or 2025-11-01. Confirming the interim
  gaps requires the corresponding 10-Q filings and their own Note
  disclosures — not yet obtained. Still explicitly **not** attributed to
  the purchases-proxy approximation.
- **No quarterly (Q1–Q4) analytical results exist.** `quarterly_facts` is
  and remains empty — a single annual filing has no quarters to derive, and
  populating them from the annual filing alone was explicitly disallowed.
  Deriving real quarters requires the three FY2025 10-Qs (see "Next source
  step" below).
- **The four-quarter proof / first data gate is NOT complete.** Only raw,
  unreviewed-except-for-four-metrics candidate facts from one annual filing
  exist. No reconciliation check has run against real data yet.
- **Net income method** (explicit interest/tax vs. net-margin simplification):
  deferred to the driver-model milestone. Finding C's confirmed bridge
  (operating income − net interest expense + net other income − taxes = net
  earnings, exact) supports using the explicit-interest-and-tax method, but
  the choice itself is still deferred to that milestone, not decided here.

## 2026-09-15 — Next source step: FY2025 interim 10-Q download list

To derive any real Q1–Q3 figures (Q4 remains derivable only as annual minus
9-month YTD) and to resolve the open accounts-payable interim gaps, the
following three filings are needed next — accession numbers and primary
document filenames already confirmed against the SEC submissions inventory
(see the 2026-09-14 filing-matrix entry above):

| Quarter | Accession | Filed | Period end | Primary document URL |
|---|---|---|---|---|
| Q1 FY2025 | 0000027419-25-000101 | 2025-05-30 | 2025-05-03 | `https://www.sec.gov/Archives/edgar/data/27419/000002741925000101/tgt-20250503.htm` |
| Q2 FY2025 | 0000027419-25-000118 | 2025-08-29 | 2025-08-02 | `https://www.sec.gov/Archives/edgar/data/27419/000002741925000118/tgt-20250802.htm` |
| Q3 FY2025 | 0000027419-25-000126 | 2025-11-26 | 2025-11-01 | `https://www.sec.gov/Archives/edgar/data/27419/000002741925000126/tgt-20251101.htm` |

Not yet requested from the project owner as a formal upload ask in this
entry — that request is made in this session's response, not repeated here.
