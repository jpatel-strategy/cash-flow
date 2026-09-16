# Investment Capacity Correction — Evidence

This document records the corrective round that followed
`docs/investment_capacity_semantic_audit.md` (diagnostic-only). It does
not repeat that audit's discovery narrative; it documents what was
built, proved, persisted, and verified in response to it.

**Three correction rounds are documented here.** Part I (sections 1–10)
documents the original correction (`version='v1'` in the database):
introducing the self-funded/debt-funded/deployment/headroom taxonomy and
fixing the legacy field's double-subtraction of mandatory debt
repayments. Part II (section 11 onward) documents a **second,
independent finance-semantics correction** (`version='v2'` in the
database) that fixed two further defects found in `v1` itself: gross debt
issuance was still mislabeled as capacity even when simultaneously
repaid, and opening excess liquidity (a stock) was still blended into a
figure read as "capacity generated." Part III (section 21 onward)
documents a **final independent-audit closeout** — three corrections
made entirely within `v2`'s own schema and data (no version bump was
needed): a test-suite hygiene fix so the full suite passes in a clean
public clone with no database present, an explicit non-same-year lineage
model for `forward_debt_repayment_reserve`'s true next-fiscal-year
dependency, and a gross/net split of the horizon-capacity figure so the
published "accessible capacity" number is net of reserve deductions, not
gross. **All FY2030 values, cumulative reconciliations, and bridges in
Part I reflect `v1` only and are superseded by Part II's `v2` values;
Part II's horizon-capacity figure is itself relabeled GROSS and
superseded by Part III's NET figure for any "accessible capacity"
reporting.** Part I and Part II are retained for the historical record of
each correction's own root-cause proof, both of which remain valid and
unaffected by later rounds. `v1` and `v2` rows are both preserved
permanently in the database; nothing is overwritten, and Part III adds no
new version because it is corrective/additive within `v2` itself
(new columns, never a change to a previously-persisted value's meaning).

**Scope discipline** (restated from the authorizing instruction): no
historical fact, historical mapping, historical lineage, forecast
operating assumption, scenario assumption, or DCF operating projection
was changed. Nothing here is a reconciliation of "a calculation is
wrong" applied to those layers — it is a purely additive correction
built entirely on top of the existing, unmodified `ForecastYear` output.

## 1. What was wrong

The legacy `investment_capacity_results.deployable_capacity` field (and
its cumulative derivative) had two defects:

1. **Single-year double-subtraction.** `deployable_capacity` was
   computed as `pre_discretionary_ending_cash - min_cash_buffer -
   near_term_debt_repayment_reserve`, where
   `near_term_debt_repayment_reserve = debt_repayments`. But
   `pre_discretionary_ending_cash` already subtracts `debt_repayments`
   once, inside `mandatory_financing_flows`. The result: every dollar of
   scheduled debt repayment was subtracted from capacity **twice**.
2. **Conflation of self-funded cash and new borrowing.** The same
   field mixed internally generated cash (FCF, opening liquidity) with
   `debt_proceeds` (new borrowing) into a single number, with no way to
   tell a decision-maker how much of "capacity" was actually generated
   by the business versus raised from lenders.

Neither defect was a bug in the underlying forecast — `ForecastYear`'s
own fields (`operating_cash_flow`, `free_cash_flow`, `debt_proceeds`,
`debt_repayments`, `min_cash_buffer`, etc.) were and remain correct and
untouched. The defect was entirely in how one derived, presentation-
layer field combined them.

## 2. Before / after definitions

| Concept | Legacy (`deployable_capacity`) | Corrected taxonomy |
|---|---|---|
| Debt repayments | Subtracted twice (once inside pre-discretionary cash, once via the "reserve") | Subtracted exactly once, as `mandatory_debt_uses` |
| New borrowing (`debt_proceeds`) | Implicitly included, unlabeled, indistinguishable from self-funded cash | Reported separately as `debt_funded_incremental_capacity`, explicitly labeled "never internally generated" |
| Headline KPI | One ambiguous number | Four numbers shown together: self-funded capacity generated, debt-funded capacity, discretionary deployment, remaining deployable headroom |
| Cumulative view | Summed each year's ending balance (fixed in Milestone 3A to use only the terminal balance + cumulative deployment) | Extended with an explicit source/use identity across the full horizon (see §5) |
| Field status | N/A | Preserved unmodified in the database; display label changed to "Legacy Gross Pre-Discretionary Ceiling"; marked deprecated; excluded from headline cards and from all new cumulative calculations |

### 2.1 The 14 fields (all newly added, all additive)

`operating_fcf`, `post_dividend_internal_generation`,
`opening_excess_liquidity`, `mandatory_debt_uses`,
`self_funded_gross_capacity`, `debt_funded_incremental_capacity`,
`total_gross_funding_capacity`, `share_repurchases`,
`strategic_investment`, `voluntary_debt_reduction`,
`other_discretionary_uses`, `total_discretionary_deployment`,
`remaining_deployable_headroom`, `ending_excess_liquidity`.

Conceptual formulas (`src/target_cash/capacity_taxonomy.py`,
`compute_capacity_taxonomy_year`):

```
opening_excess_liquidity        = max(0, beginning_cash - min_cash_buffer)
mandatory_debt_uses             = debt_repayments                         # taken once
self_funded_gross_capacity      = opening_excess_liquidity
                                   + post_dividend_internal_generation
                                   - mandatory_debt_uses
debt_funded_incremental_capacity = debt_proceeds
total_gross_funding_capacity     = self_funded_gross_capacity
                                    + debt_funded_incremental_capacity
total_discretionary_deployment   = share_repurchases + strategic_investment
                                    + voluntary_debt_reduction
                                    + other_discretionary_uses            # 3 structural $0 placeholders today
remaining_deployable_headroom    = max(0, total_gross_funding_capacity
                                    - total_discretionary_deployment)
ending_excess_liquidity          = max(0, ending_cash - min_cash_buffer)
```

`strategic_investment`, `voluntary_debt_reduction`, and
`other_discretionary_uses` are structural $0 placeholders because no
disclosed driver separates them from the existing `share_repurchases`
and `debt_repayments` fields in the source filings — stated as a
limitation (§9), not hidden.

## 3. Root-cause proof (not just a fix)

For every scenario-year with `debt_repayments > 0`:

```
new remaining_deployable_headroom == old (naive) residual + debt_repayments
```

where "old (naive) residual" is `legacy_deployable_capacity -
share_repurchases - deployment` under the audit's own methodology. This
identity is checked in `tests/unit/test_capacity_taxonomy.py` and holds
exactly for all 15 scenario-years in the persisted results — proving
the entire gap between the legacy and corrected figures is explained by
the one identified defect, with no unexplained residual.

`ending_excess_liquidity` is computed independently, from
`ending_cash` and `min_cash_buffer` alone (no capacity fields feed into
it), and is proven algebraically and numerically equal to
`remaining_deployable_headroom` whenever the `max(0, ...)` floors do not
bind — an independent cross-check, not a derived restatement.

## 4. Corrected FY2030 scenario values

| Metric (FY2030) | Base | Upside | Downside |
|---|---:|---:|---:|
| Self-funded capacity generated | $6,315.0M | $3,941.9M | $5,887.5M |
| Debt-funded capacity (separate) | $700.0M | $300.0M | $500.0M |
| Total gross funding capacity | $7,015.0M | $4,241.9M | $6,387.5M |
| Total discretionary deployment | $636.3M | $1,498.4M | $0.0M |
| Remaining deployable headroom | $6,378.7M | $2,743.5M | $6,387.5M |
| Ending excess liquidity (cross-check) | $6,378.7M | $2,743.5M | $6,387.5M |
| Legacy `deployable_capacity` (deprecated) | $6,315.0M | $3,241.9M | $6,087.5M |

Base's legacy and self-funded figures coincide because Base's FY2030
`debt_repayments` happens to be $0; Upside and Downside show the full
effect of the double-subtraction fix ($3,241.9M → $3,941.9M, and
$6,087.5M → $5,887.5M respectively — exactly the FY2030
`debt_repayments` amount in each case).

### Scenario explanations

- **Upside**: generates more self-funded capacity than the naive
  "revenue is higher so capacity should be higher" intuition would
  suggest is *not* what drives its lower headroom — Upside's
  *cumulative* self-funded generation ($4,776.8M) actually exceeds
  Base's ($3,490.8M — see §5). Its FY2030 headroom is lower than Base's
  because it *deploys* far more in-year ($1,498.4M vs. $636.3M) into
  buybacks and faster deleveraging, consistent with its higher-payout,
  faster-deleveraging assumption set. Lower single-year headroom here is
  a feature (capital being put to work), never a sign of weaker capacity
  generation.
- **Downside** differs from Base because: (a) CapEx and revenue growth
  assumptions are lower, reducing operating FCF and therefore
  `post_dividend_internal_generation`; (b) the dividend-freeze (not cut)
  policy holds `post_dividend_internal_generation` higher than a naive
  "cut everything" scenario would; (c) borrowing (`debt_proceeds`) is
  reduced relative to Base, shrinking `debt_funded_incremental_capacity`;
  (d) the minimum-cash-buffer policy is held constant as a percentage of
  (lower) revenue, so the buffer itself shrinks, mechanically raising
  `opening_excess_liquidity` in later years — this is a buffer-policy
  effect, not new capacity. The interface never interprets (c) or (d) as
  improved operating capacity: debt-funded capacity is always shown on
  its own line, and buffer-driven liquidity is explicitly the "excess
  liquidity" stock concept, never summed into a flow.

## 5. Five-year cumulative reconciliation (Definitions A–G)

Per the governing instruction, opening excess liquidity is counted
**once**, as a stock at the start of the horizon (FY2026), never summed
across years.

| Term | Base | Upside | Downside |
|---|---:|---:|---:|
| A. Opening excess liquidity at horizon start (FY2026) | $2,313.2M | $2,250.3M | $2,423.2M |
| B. Cumulative self-funded generation (FY2026–FY2030, excl. A) | $3,490.8M | $4,776.8M | $1,169.2M |
| C. Cumulative debt-funded capacity (FY2026–FY2030) | $3,500.0M | $1,500.0M | $2,500.0M |
| **Total horizon capacity accessible = A + B + C** | **$9,303.9M** | **$8,527.1M** | **$6,092.3M** |
| D. Cumulative discretionary deployment (FY2026–FY2030) | $2,796.3M | $5,377.2M | $0.0M |
| E. Terminal remaining headroom (FY2030) | $6,378.7M | $2,743.5M | $6,387.5M |
| F. Ending reserve movement (FY2030 buffer − FY2026 buffer) | $128.9M | $406.4M | $(295.2)M |
| **D + E + F (must equal A+B+C exactly)** | **$9,303.9M** | **$8,527.1M** | **$6,092.3M** |

Both sides reconcile **exactly** (to floating-point precision) for all
three scenarios — this is a proven identity
(`capacity_accounted_for_reconciliation`, §7), not a plug. `F` is a
legitimate reconciling term: it is the change in the minimum-cash-buffer
policy amount itself (driven by revenue growth across the horizon), not
a fabricated balancing figure — it is computed directly from
`ForecastYear.min_cash_buffer` at the first and last forecast years.

Per the governing instruction, **FY2026 through FY2030 ending-headroom
balances are never added together** — the cumulative view above sums
only flows (B, C, D) and reconciles them against the single terminal
stock (E) plus the reserve-movement term (F), with the opening stock
(A) counted once.

This corrected cumulative view narrows the Base-vs-Upside comparative
gap in total accessible capacity from the semantic audit's flagged
~48.7% (legacy, single-year-based comparison) to **~8.3%**
($9,303.9M vs. $8,527.1M) — a materially different, more defensible
picture once debt-funded capacity and in-year deployment are separated
out. This narrowing is itself now a regression check in
`scripts/verify_powerbi_handoff.py`.

## 6. Base → Upside and Base → Downside bridges

Explicit source/use bridge, proving no double-counted or fabricated
delta (each row's arithmetic ties to the next, and the final delta
matches the reported headroom change exactly):

**Base → Upside (FY2030, $M):**

| Step | Amount |
|---|---:|
| Base self-funded capacity generated | 6,315.0 |
| Δ Self-funded capacity generated | (2,373.1) |
| = Upside self-funded capacity generated | 3,941.9 |
| Δ Debt-funded capacity | (400.0) |
| = Δ Total gross funding capacity | (2,773.1) |
| Δ Discretionary deployment | +862.1 |
| **= Δ Remaining deployable headroom** | **(3,635.2)** |
| Base headroom 6,378.7 + Δ (3,635.2) = Upside headroom | 2,743.5 ✓ |

**Base → Downside (FY2030, $M):**

| Step | Amount |
|---|---:|
| Base self-funded capacity generated | 6,315.0 |
| Δ Self-funded capacity generated | (427.5) |
| = Downside self-funded capacity generated | 5,887.5 |
| Δ Debt-funded capacity | (200.0) |
| = Δ Total gross funding capacity | (627.5) |
| Δ Discretionary deployment | (636.3) |
| **= Δ Remaining deployable headroom** | **+8.8** |
| Base headroom 6,378.7 + Δ 8.8 = Downside headroom | 6,387.5 ✓ |

Both bridges satisfy `Δ total_gross_funding_capacity − Δ
total_discretionary_deployment = Δ remaining_deployable_headroom`
exactly, confirming no term was double-counted or omitted in either
direction.

## 7. Validation totals (13 named checks, 147 results)

All defined in `CAPACITY_CHECK_METADATA`
(`src/target_cash/capacity_taxonomy.py`), each explicitly classified by
type (arithmetic invariant vs. structural completeness check — no check
here claims to be an independent reasonableness test):

| Check | Type | What it proves |
|---|---|---|
| `operating_fcf_reconciles` | arithmetic invariant | `operating_fcf == CFO − CapEx` |
| `post_dividend_generation_reconciles` | arithmetic invariant | `post_dividend_internal_generation == operating_fcf − dividends_paid` |
| `mandatory_debt_not_double_deducted` | arithmetic invariant | `mandatory_debt_uses` subtracted exactly once |
| `repurchases_in_discretionary_deployment` | structural completeness | repurchases are one of 4 additive deployment components |
| `headroom_never_negative` | arithmetic invariant | `remaining_deployable_headroom >= 0` |
| `ending_cash_above_buffer_or_flagged` | structural completeness | ending cash covers the buffer, or `funding_warning` is already set |
| `annual_source_use_reconciliation` | arithmetic invariant | full annual source/use identity to `ending_cash` |
| `capacity_mutually_exclusive` | arithmetic invariant | headroom + deployment == total gross capacity (unfloored) |
| `cumulative_excludes_repeated_balances` | arithmetic invariant | horizon total uses FY2026 opening liquidity only, proven to differ from the naive multi-year sum |
| `opening_excess_liquidity_excluded_from_generation` | arithmetic invariant | cumulative generation excludes the FY2026 opening stock |
| `cumulative_deployment_includes_repurchases` | structural completeness | nonzero repurchases flow into cumulative deployment |
| `capacity_accounted_for_reconciliation` | arithmetic invariant | the §5 identity holds exactly |
| `scenario_and_cutoff_lineage_complete` | structural completeness | every row carries scenario + a valid information cutoff |

**Result**: 147/147 PASS (13 checks × 3 scenarios × ~3.77 rows/check on
average across per-year and per-horizon granularity — exact
per-scenario-year and per-horizon breakdown persisted in
`capacity_validation_results`). Corruption tests exist for each
identity (`tests/unit/test_capacity_taxonomy.py`), each independently
verified to fail when the identity is deliberately broken.

Combined with the pre-existing suites: **404 total automated validation
results** (229 forecast + 28 valuation + 147 capacity taxonomy), all
PASS.

## 8. Database, persistence, and clean-room evidence

- **Migrations**: additive-only, `CREATE TABLE IF NOT EXISTS`,
  `0025_capacity_taxonomy_results` through
  `0028_capacity_validation_results`, all FK'd to `forecast_scenarios`.
- **Backup**: production database backed up before persistence at
  `data/curated/target_cash.db.backup-20260916T032610Z`
  (sha256 `2cc11edf...`).
- **Preflight**: `CapacityPersistencePreflight` enumerates expected
  writes before touching the database; `CapacityPersistencePrerequisiteError`
  raised (and tested) if `forecast_scenarios` is empty.
- **Transactional, idempotent write**: `persist_capacity_taxonomy()` ran
  twice against the real production database; both runs produced
  identical row counts:

  | Table | Rows |
  |---|---:|
  | `capacity_taxonomy_results` | 15 |
  | `capacity_horizon_results` | 3 |
  | `capacity_taxonomy_lineage` | 231 |
  | `capacity_validation_results` | 147 |

- **Rollback proof**: `test_persist_rolls_back_on_error` corrupts
  `fiscal_year` to trigger a CHECK-constraint `IntegrityError` and
  asserts zero rows are written.
- **Idempotency proof**: `test_persist_is_idempotent` persists twice and
  asserts identical row counts both times (matches the real double-run
  above).
- **Historical-table isolation proof**:
  `test_legacy_investment_capacity_results_untouched_by_capacity_persistence`
  takes a full before/after row snapshot of `investment_capacity_results`
  and asserts zero change. Confirmed against the real database: legacy
  table still holds its original 15 rows, byte-identical.
- **Clean-room rebuild**: `scripts/clean_room_rebuild.py` extended with
  a `persist-capacity-taxonomy` step (after `persist-valuation`),
  verified against a from-scratch rebuild post-commit (§10 of the final
  report records the run's outcome). `scripts/compare_databases.py`
  extended with canonical, sorted, hash-stable exports for all four new
  tables so the comparison covers them the same way it covers every
  other persisted table.

## 9. Deliverable-by-deliverable verification

### 9.1 Python / tests
- `capacity_taxonomy.py`: 28 unit tests, all passing
  (`tests/unit/test_capacity_taxonomy.py`).
- `capacity_persistence.py`: 8 unit tests, all passing
  (`tests/unit/test_capacity_persistence.py`).

### 9.2 Excel (`Target_Cash_Flow_Investment_Capacity_Model.xlsx`)
A "CORRECTED CAPACITY TAXONOMY" section (14 live-formula rows) was added
to the Investment Capacity sheet, plus a static cumulative-reconciliation
table; the Executive Summary KPIs and chart were rewritten to the
corrected taxonomy; the legacy row was relabeled deprecated; a
Validation Summary section covers the 13 named checks (147 results).
**Verification claim, precisely stated**: formula outputs are
programmatically reconciled to the Python engine via the `formulas`
package (28/28 checks pass). The workbook has **not** been opened or
visually confirmed in Microsoft Excel — that broader claim is
explicitly not made.

### 9.3 Power BI handoff (`deliverables/powerbi_handoff/`)
Two new fact tables exported (`fact_capacity_taxonomy`, 15 rows;
`fact_capacity_horizon`, 3 rows). DAX measures, relationship map, and
data dictionary updated; legacy measures marked deprecated with
warnings. `scripts/verify_powerbi_handoff.py`: **129/129 checks pass**,
including DB/CSV row-count parity, referential integrity, per-row and
per-scenario numeric reconciliation to Python, the Base-vs-Upside
gap-narrowing regression check (§5), and a scan confirming no bare
"Deployable Capacity" label remains without a legacy/deprecated
qualifier. This remains a complete, **implementation-ready handoff
package**; no `.pbix` file was created or is claimed to exist.

### 9.4 Web cockpit (`deliverables/web_cockpit/`)
The legacy ambiguous KPI was removed from the Snapshot headline cards;
a new `#capacity-kpi-grid` shows all four corrected concepts together;
the Cash-Flow Bridge section gained a corrected waterfall, a cumulative
horizon table, and a per-year detail table with the legacy row
preserved but visually flagged (`reclassified` styling) as deprecated
methodology evidence. `js/formulas.js` gained a line-for-line JS port of
`compute_capacity_taxonomy_year` (`computeCapacityTaxonomyYear`) —
disclosed as a manually-synchronized, potentially drifting
implementation, same as the existing what-if sandbox port.
`scripts/verify_web_cockpit.py`: **27/27 checks pass**, run headless via
Playwright against the pre-installed Chromium, including: zero
console/page errors; all three scenarios' headline values match Python
exactly; the legacy KPI is confirmed absent from `#kpi-grid`; all four
corrected labels are confirmed present (case-insensitive match, since
the page's CSS renders KPI labels in uppercase); a numeric Self-Funded
value match to Python for Base/FY2030; a full-page scan for any bare
"deployable capacity" label lacking a legacy/deprecated/remaining/
cumulative qualifier (0 found); FY2025 CFO $6,562M, CapEx $3,727M, CFI
$(3,649)M, and FCF $2,835M all render distinctly; and no horizontal
overflow at a 390px mobile viewport. The site was **not** deployed
publicly — verification runs against a local server only.

### 9.5 Portfolio / recruiter package (`deliverables/portfolio_package/`)
Updated only where the ambiguous "deployable capacity" claim was a
headline or a stale count: `01_executive_case_study.md` (headline
table + narrative), `03_finance_methodology_summary.md` (added the
second-correction narrative), `04_data_dictionary.md` (added the 4 new
tables, updated table/row counts), `05_model_risk_and_limitations.md`
(added the JS-port limitation, updated validation-check count),
`06_positioning_note.md`, `07_demo_script.md` (added a corrected-KPI
talking point), `08_interview_explanations.md`, `09_resume_bullets.md`
(added a bullet, corrected stale test/row counts), `10_linkedin_draft.md`
(corrected stale test count), `12_final_project_inventory.md` (corrected
stale test/table/row/check counts), `13_reproduction_instructions.md`
(added the `persist-capacity-taxonomy` step), and the package
`README.md` (corrected stale test count). Unaffected documents
(`11_screenshot_plan.md`) were left as-is.

## 10. Limitations (carried forward and new)

- **JS/Python formula drift risk**: `computeCapacityTaxonomyYear` in
  `formulas.js` is a manually-synchronized port of
  `compute_capacity_taxonomy_year` in Python. It is verified to match at
  page load but has no automated cross-language equivalence test; a
  future change to the Python formula could silently desync it.
- **Three structural $0 placeholders**: `strategic_investment`,
  `voluntary_debt_reduction`, and `other_discretionary_uses` have no
  disclosed driver in the source SEC filings distinguishing them from
  the existing `share_repurchases`/`debt_repayments` fields, so they are
  held at $0 rather than estimated.
- **Excel verification is programmatic reconciliation only** — the
  workbook has not been opened or visually confirmed in Microsoft
  Excel or LibreOffice (LibreOffice could not load `.xlsx` files at all
  in this build environment, confirmed with a trivial test file, prior
  to this correction round).
- **Power BI package is implementation-ready, not implementation-
  complete** — no `.pbix` file exists or is claimed; verification is at
  the CSV/DAX/referential-integrity level only.
- **Near-term debt-repayment timing remains a proxy**: `mandatory_debt_uses`
  is still sourced from each forecast year's own scheduled
  `debt_repayments` assumption, not a disclosed debt-maturity ladder —
  this limitation predates and is unchanged by this correction.
- **The correction does not re-derive or re-validate the underlying
  forecast assumptions** — it is purely a presentation/derivation-layer
  fix built on `ForecastYear`'s existing, unmodified output. If a future
  audit finds the underlying assumptions themselves need revision, that
  is separate work requiring separate authorization.

---

# Part II: v2 Finance-Semantics Correction

## 11. What was wrong (in `v1` itself)

A follow-up review of the Part I (`v1`) taxonomy found two further
economic defects, independent of the double-subtraction bug Part I
fixed:

1. **Gross debt issuance mislabeled as capacity.**
   `debt_funded_incremental_capacity = debt_proceeds` (gross) — so if a
   scenario-year borrowed $700M and repaid $700M in the same year, the
   taxonomy showed $700M of "debt-funded capacity," when the true net
   effect of that year's debt activity was $0. Gross debt issuance is
   not incremental capacity when debt is simultaneously repaid.
2. **A stock blended into a "generated" label.**
   `self_funded_gross_capacity = opening_excess_liquidity +
   post_dividend_internal_generation - mandatory_debt_uses` combined a
   STOCK (cash carried forward from prior years, `opening_excess_liquidity`)
   with a FLOW (this period's own generation) into one number implicitly
   read as "capacity generated this period." A stock is never capacity a
   period generated.

Neither defect was in `ForecastYear`'s own fields (`debt_proceeds`,
`debt_repayments`, `beginning_cash`, etc.) — both remain correct and
untouched. The defect was entirely in how the `v1` taxonomy combined
them, exactly the same class of error Part I fixed in the legacy field
one level up.

## 12. Corrected (v2) formulas

```
net_mandatory_debt_service        = MAX(0, gross_debt_repayments - gross_debt_proceeds)
debt_funded_incremental_capacity  = MAX(0, gross_debt_proceeds - gross_debt_repayments)
    # exactly one of the two above is nonzero, or both are zero when proceeds == repayments

self_funded_capacity_generated    = post_dividend_internal_generation - net_mandatory_debt_service
    # a pure FLOW; opening_excess_liquidity is NOT a term in this formula

total_gross_funding_capacity      = opening_excess_liquidity
                                     + self_funded_capacity_generated
                                     + debt_funded_incremental_capacity
    # algebraically IDENTICAL in value to v1's 2-term formula for the same
    # underlying cash flows -- only the internal decomposition changes,
    # proven in test_total_gross_funding_capacity_unchanged_by_v2_decomposition

forward_debt_repayment_reserve    = next fiscal year's net_mandatory_debt_service
                                     (terminal FY2030: PROXIED by repeating
                                     FY2030's own net_mandatory_debt_service,
                                     since FY2031 is outside the forecast horizon)

remaining_deployable_headroom     = MAX(0, total_gross_funding_capacity
                                     - total_discretionary_deployment
                                     - forward_debt_repayment_reserve)
```

`gross_debt_proceeds` and `gross_debt_repayments` (= `ForecastYear.debt_proceeds`
/ `.debt_repayments`, unchanged) are preserved as explicit, transparent
supporting fields in every deliverable — never hidden, never called
"capacity" on their own.

`opening_excess_liquidity`, `post_dividend_internal_generation`, and the
discretionary-deployment components are **unchanged** from Part I.

**Two DEPRECATED-BY-v2 fields** (`mandatory_debt_uses`,
`self_funded_gross_capacity`) are retained in the schema, populated for
`v2` rows only to satisfy the shared table's pre-existing NOT NULL
columns — never read by any display, formula, or downstream export.
`self_funded_gross_capacity` for a `v2` row legitimately still equals
`opening_excess_liquidity + self_funded_capacity_generated` (a valid
"self-funded capacity including the opening stock" figure), it is simply
never labeled "generated" anywhere in this round's deliverables.

## 13. Verbatim worked examples (from the authorization)

| Scenario | Gross Proceeds | Gross Repayments | Net Mandatory Debt Service | Debt-Funded Incremental Capacity |
|---|---:|---:|---:|---:|
| Base (FY2030) | $700M | $700M | $0M | $0M |
| Upside (FY2030) | $300M | $1,000M | $700M | $0M |
| Downside (FY2030) | $500M | $300M | $0M | $200M |

Confirmed exactly against the persisted `v2` rows and covered by
dedicated tests: `test_equal_proceeds_and_repayments_create_zero_incremental_debt_capacity`,
`test_net_deleveraging_creates_zero_debt_funded_capacity`,
`test_only_net_new_borrowing_creates_incremental_debt_capacity`,
`test_fy2030_example_values_from_the_correction_authorization`.

## 14. New forward-reserve reconciling term (five-year identity)

Deducting a forward reserve from the terminal year's own headroom
required a new term in the Part I horizon-reconciliation identity, since
`terminal_remaining_headroom` (E) is now smaller by that reserve, and
the reserve represents cash held back for an obligation (FY2031) that
occurs entirely **outside** the 5-year forecast — it is not already
accounted for anywhere in the A–D terms.

```
total_horizon_capacity_accessible (A+B+C, UNCHANGED in formula and value from Part I)
  == cumulative_discretionary_deployment (D)
   + terminal_remaining_headroom (E, now net of the terminal forward reserve)
   + ending_reserve_movement (F)
   + terminal_forward_debt_repayment_reserve (NEW fourth term, G)
```

`total_horizon_capacity_accessible` (A+B+C) is **numerically unchanged**
from Part I for all three scenarios — proof that this correction only
changes how capacity is *decomposed and timed*, never the total amount
of capacity accessible across the horizon:

| Scenario | Total Horizon Capacity Accessible (v1 and v2, identical) |
|---|---:|
| Base | $9,303.9M |
| Upside | $8,527.1M |
| Downside | $6,092.3M |

Verified by `check_capacity_accounted_for_reconciliation` (persisted,
now including the fourth term) and
`test_capacity_accounted_for_reconciliation_without_summing_annual_stocks`.

## 15. Corrected (v2) FY2030 scenario values

| Metric (FY2030) | Base | Upside | Downside |
|---|---:|---:|---:|
| Opening Excess Liquidity (stock) | $5,424.3M | $2,217.5M | $6,157.9M |
| Self-Funded Capacity Generated | $1,590.8M | $2,024.4M | $29.6M |
| Debt-Funded Capacity (net of repayment) | $0.0M | $0.0M | $200.0M |
| Total Gross Funding Capacity | $7,015.0M | $4,241.9M | $6,387.5M |
| Discretionary Deployment | $636.3M | $1,498.4M | $0.0M |
| Forward Debt-Repayment Reserve | $0.0M | $700.0M | $0.0M |
| **Remaining Deployable Headroom** | **$6,378.7M** | **$2,043.5M** | **$6,387.5M** |
| Gross Debt Proceeds (supporting) | $700.0M | $300.0M | $500.0M |
| Gross Debt Repayments (supporting) | $700.0M | $1,000.0M | $300.0M |
| Net Mandatory Debt Service (supporting) | $0.0M | $700.0M | $0.0M |

`Total Gross Funding Capacity` is **unchanged** from Part I's
`self_funded_gross_capacity + debt_funded_incremental_capacity` for
every scenario-year (proven algebraically and by test) — only
`Remaining Deployable Headroom` changes value versus Part I, and only
where a nonzero forward reserve applies (Upside: $2,743.5M → $2,043.5M;
Base and Downside are unaffected since their FY2030 net mandatory debt
service, and hence forward-reserve proxy, is $0).

### Scenario explanations (v2-specific)

- **Base**: FY2030 gross proceeds and repayments are exactly equal
  ($700M each) — a coincidence of the scheduled debt roll-forward, not a
  policy choice — so debt-funded capacity and net mandatory debt service
  are both $0, and the forward reserve is $0.
- **Upside**: FY2030 repayments ($1,000M) exceed proceeds ($300M) by
  $700M — Upside's faster-deleveraging assumption set means it is a net
  repayer of debt even while continuing to refinance part of its
  maturities, so debt-funded capacity is $0 and net mandatory debt
  service is $700M. Because FY2031 is unknown, the model conservatively
  proxies FY2030's own $700M net debt service forward as FY2030's
  forward reserve, further reducing FY2030's own remaining headroom.
  This is the single largest v2-driven change in this document: Upside's
  headroom drops from Part I's $2,743.5M to $2,043.5M.
- **Downside**: FY2030 proceeds ($500M) exceed repayments ($300M) by
  $200M — Downside is a net *borrower* in FY2030 (consistent with its
  reduced operating cash flow requiring more external financing), so it
  is the only scenario with nonzero debt-funded capacity ($200M) and the
  only one whose total gross funding capacity is *increased*, not
  decreased, by new borrowing.

## 16. Base → Upside and Base → Downside bridges (v2)

**Base → Upside (FY2030, $M):**

| Step | Amount |
|---|---:|
| Base remaining deployable headroom | 6,378.7 |
| Δ Opening excess liquidity | (3,206.8) |
| Δ Self-funded capacity generated | +433.6 |
| Δ Debt-funded capacity | 0.0 |
| = Δ Total gross funding capacity | (2,773.2) |
| Δ Discretionary deployment | +862.1 |
| Δ Forward debt-repayment reserve | +700.0 |
| **= Δ Remaining deployable headroom** | **(4,335.2)** |
| Base 6,378.7 + Δ (4,335.2) = Upside headroom | 2,043.5 ✓ |

**Base → Downside (FY2030, $M):**

| Step | Amount |
|---|---:|
| Base remaining deployable headroom | 6,378.7 |
| Δ Opening excess liquidity | +733.6 |
| Δ Self-funded capacity generated | (1,561.2) |
| Δ Debt-funded capacity | +200.0 |
| = Δ Total gross funding capacity | (627.6) |
| Δ Discretionary deployment | (636.3) |
| Δ Forward debt-repayment reserve | 0.0 |
| **= Δ Remaining deployable headroom** | **+8.7** |
| Base 6,378.7 + Δ 8.7 = Downside headroom | 6,387.5 ✓ (rounding) |

Both bridges satisfy `Δ total_gross_funding_capacity − Δ
total_discretionary_deployment − Δ forward_debt_repayment_reserve = Δ
remaining_deployable_headroom` exactly, confirming no term was
double-counted or omitted.

## 17. Validation totals (18 named checks, 210 results)

Six new checks were added to `CAPACITY_CHECK_METADATA`, alongside the 12
retained from Part I (all updated where their formula referenced a
renamed/redefined field):

| Check | Type | What it proves |
|---|---|---|
| `debt_netting_mutually_exclusive` | arithmetic invariant | `net_mandatory_debt_service` and `debt_funded_incremental_capacity` are never both positive; their difference equals `gross_repayments - gross_proceeds` exactly |
| `debt_funded_capacity_excludes_gross_issuance` | arithmetic invariant | equal proceeds/repayments → both $0; net deleveraging → debt-funded capacity $0; only net new borrowing → debt-funded capacity > 0 |
| `self_funded_generation_excludes_opening_liquidity` | arithmetic invariant | `self_funded_capacity_generated == B - net_mandatory_debt_service`, with no `opening_excess_liquidity` term present |
| `headroom_deducts_forward_reserve` | arithmetic invariant | `remaining_deployable_headroom` (unfloored) `== ending_excess_liquidity - forward_debt_repayment_reserve` exactly |
| `forward_reserve_terminal_proxy_documented` | structural completeness | `forward_reserve_is_proxied` is `True` only for the terminal year, and matches the actual next year's net debt service for every other year |
| `mandatory_debt_not_double_deducted` (updated) | arithmetic invariant | now checks `self_funded_capacity_generated == B - net_mandatory_debt_service` |
| `capacity_mutually_exclusive` (updated) | arithmetic invariant | now a 3-way partition: `headroom + deployment + forward_reserve == total_gross_funding_capacity` (unfloored) |
| `capacity_accounted_for_reconciliation` (updated) | arithmetic invariant | now includes the 4th term, `terminal_forward_debt_repayment_reserve` |

**Result**: 210/210 PASS (13 per-scenario-year checks × 15 scenario-years
+ 1 forward-reserve-documentation check × 3 scenarios + 4 per-scenario
cumulative checks × 3 scenarios). Combined with forecast (229) and
valuation (28): **467 total validation results, all PASS**.

**36 new/updated unit tests** in `tests/unit/test_capacity_taxonomy.py`
(now 42 tests total in that file) map directly to every proof the
authorization required: equal proceeds/repayments → zero incremental
capacity; net deleveraging → zero debt-funded capacity; only
proceeds-in-excess → incremental capacity; opening liquidity never
labeled generation; headroom deducts the forward reserve; the five-year
identity reconciles without summing annual stocks (explicitly proven by
`test_capacity_accounted_for_reconciliation_without_summing_annual_stocks`,
which asserts the naive per-year-headroom sum does NOT reproduce the
correct horizon total).

## 18. Database, persistence, and versioning evidence

- **No data destroyed**: `CAPACITY_TAXONOMY_VERSION` bumped from `"v1"`
  to `"v2"`. Deterministic IDs already embed the version string
  (`captax_{scenario}_{fy}_{version}`, etc.), so persisting `v2` **adds**
  new rows alongside the existing `v1` rows — nothing is updated or
  deleted. `v1` rows remain permanently queryable for audit trail.
- **8 new additive migrations** (`0029`–`0036`, all `ColumnMigration`,
  `ALTER TABLE ... ADD COLUMN`, nullable, no NOT NULL added): 6 new
  columns on `capacity_taxonomy_results` (`gross_debt_proceeds`,
  `gross_debt_repayments`, `net_mandatory_debt_service`,
  `self_funded_capacity_generated`, `forward_debt_repayment_reserve`,
  `forward_reserve_is_proxied`) and 2 new columns on
  `capacity_horizon_results` (`terminal_forward_debt_repayment_reserve`,
  `terminal_forward_reserve_is_proxied`). Applied cleanly to the real
  production database with `apply_safe_migrations` (idempotent, verified
  via a scratch-copy dry run before touching production).
- **Real production persistence**: backed up at
  `data/curated/target_cash.db.backup-20260916T062436Z`; ran
  `persist-capacity-taxonomy` twice against production, proving
  idempotency (identical `written` counts both times: 15/3/309/210).
  Post-write integrity: `all_passed: true` both times; legacy
  `investment_capacity_results` (15 rows) and `v1` capacity-taxonomy rows
  (15/3/231/147) confirmed untouched.
- **Database totals**: 28 tables (unchanged — additive columns, not new
  tables), 6,646 total rows (up from 6,101 pre-`v2`): `capacity_taxonomy_results`
  30 rows (15 `v1` + 15 `v2`), `capacity_horizon_results` 6 rows (3+3),
  `capacity_taxonomy_lineage` 540 rows (231+309), `capacity_validation_results`
  357 rows (147+210).
- **Clean-room rebuild**: `scripts/clean_room_rebuild.py`'s existing
  `persist-capacity-taxonomy` step is unchanged (it always persists
  whatever `CAPACITY_TAXONOMY_VERSION` the code currently defines) — a
  from-scratch rebuild persists only `v2` rows (no pre-existing `v1`
  history to reproduce, since a clean room starts empty), so its
  post-rebuild row count for `capacity_taxonomy_results` is 15, not 30;
  `scripts/compare_databases.py`'s canonical exports for these tables
  were updated to compare `WHERE version = 'v2'` against the equivalent
  slice of the active database, so the comparison remains apples-to-apples.

## 19. Deliverable-by-deliverable verification (v2)

### 19.1 Python / tests
`tests/unit/test_capacity_taxonomy.py`: 42 tests (up from 28), all
passing. `tests/unit/test_capacity_persistence.py`: 10 tests (up from
8), all passing, including 2 new tests asserting the persisted `v2`
rows carry the corrected debt-netting and forward-reserve fields.

### 19.2 Excel
`CT_ROWS`/`CT_LABELS` rewritten: new rows for `gross_debt_proceeds`,
`gross_debt_repayments`, `net_mandatory_debt_service`,
`self_funded_capacity_generated`, `forward_debt_repayment_reserve`, plus
two visually-marked (red italic) DEPRECATED rows for the retained
`mandatory_debt_uses`/`self_funded_gross_capacity` schema-compatibility
fields. All live formulas use Excel's native `MAX()`, including a
column-shifted reference (`NEXT_FY_COL`) for the forward reserve's
look-ahead to the next fiscal year's column. Executive Summary KPI rows
and the cumulative-reconciliation table updated with the new
opening-liquidity row and the fourth reconciling term.
`scripts/verify_excel_model.py`: **34/34 checks pass**, including a new
check proving `net_mandatory_debt_service` and `debt_funded_incremental_capacity`
are never both positive in the live, recalculated Excel formulas (not
just in Python) — formula outputs programmatically reconciled to the
Python engine via the `formulas` package, never opened in Excel.

### 19.3 Power BI handoff
`fact_capacity_taxonomy`/`fact_capacity_horizon` CSV exports now filter
`WHERE version = 'v2'` (the DB holds both versions; only the current one
is exported for BI reporting) and include all new columns. DAX measures
rewritten: new `Opening Excess Liquidity`, `Gross Debt Proceeds
(Supporting)`, `Gross Debt Repayments (Supporting)`, `Net Mandatory Debt
Service`, and `Forward Debt-Repayment Reserve` measures; `Self-Funded
Capacity Generated` and `Debt-Funded Capacity` measures repointed to the
corrected columns; `Total Horizon Capacity Accessible`'s reconciliation
comment updated for the fourth term. Page specs (`page_01`, `page_06`)
and wireframe SVGs updated with the 5-card KPI row (opening liquidity
added) and the corrected waterfall order.
`scripts/verify_powerbi_handoff.py`: **159/159 checks pass**, including
new checks for the debt-netting mutual-exclusivity identity and the
corrected headroom-minus-forward-reserve cross-check, at the CSV/data
level (not just Python).

### 19.4 Web cockpit
`formulas.js`'s `computeCapacityTaxonomyYear` rewritten to accept the
next fiscal year's data (for the forward reserve) and a new
`computeCapacityTaxonomyForYears` helper computes the full 5-year array
for the What-If sandbox. `app.js`: added an `Opening Excess Liquidity`
KPI card (now 5 cards instead of 4), rewrote the corrected waterfall
(opening liquidity → self-funded generated → debt-funded net of
repayment → discretionary deployment → forward reserve → headroom), the
per-year detail table (13 rows, plus 2 deprecated rows), the horizon
table (new terminal-forward-reserve row), and the What-If sandbox
results. `scripts/verify_web_cockpit.py`: **30/30 checks pass**,
including a new numeric check that Base FY2030 debt-funded capacity
renders as exactly `$0M` on the page (not the gross $700M issuance).

### 19.5 Portfolio / recruiter package
Updated: `01_executive_case_study.md` (new FY2030 table with all 5
corrected metrics, third-correction narrative), `03_finance_methodology_summary.md`
(new bullet documenting the third correction), `04_data_dictionary.md`
(versioned table descriptions, updated row counts), `05_model_risk_and_limitations.md`
(updated check count, new forward-reserve-proxy limitation),
`07_demo_script.md` (new talking point), `08_interview_explanations.md`
/ `10_linkedin_draft.md` ("three times," not "twice"), `09_resume_bullets.md`
/ `02_technical_architecture_summary.md` / `12_final_project_inventory.md`
/ `README.md` / `06_positioning_note.md` / `13_reproduction_instructions.md`
(corrected stale test/check/row counts throughout).

## 20. Limitations (v2-specific, in addition to Part I's §10)

- **The forward debt-repayment reserve for the terminal forecast year
  (FY2030) is a documented proxy, not a real scheduled obligation.** It
  repeats FY2030's own net mandatory debt service as the best available
  estimate for FY2031, which is outside the 5-year forecast horizon. If
  FY2031's actual debt schedule differs materially, this proxy would
  differ from the real reserve needed.
- **Two DEPRECATED-BY-v2 columns are retained purely for schema
  compatibility** (`mandatory_debt_uses`, `self_funded_gross_capacity`
  on `v2` rows) — they hold legitimate, correctly-computed values under
  their OWN (different, stock-inclusive) definitions, but are never read
  by any current display or formula. A future schema cleanup could drop
  them once no consumer depends on the shared table shape across `v1`
  and `v2`.
- **The JS/Python drift risk already disclosed in Part I §10 now also
  covers `computeCapacityTaxonomyForYears`** — the forward-reserve
  look-ahead logic is a second point of manual synchronization between
  the two implementations.
- **This correction, like Part I, does not re-derive or re-validate the
  underlying forecast assumptions or `ForecastYear`'s own fields** — it
  remains a purely additive, presentation/derivation-layer fix.

# Part III: Final Independent-Audit Closeout

**The `v2` per-year capacity formulas themselves are unchanged and were
explicitly approved as-is in the authorizing instruction for this round.**
This closeout corrects three defects found in how `v2` is tested,
how one of its lineage relationships is recorded, and how one of its
horizon-summary figures is labeled and computed — never the per-year
formulas.

## 21. What was wrong

An independent audit of the `v2` correction found three defects, none of
which touch the per-year capacity arithmetic:

1. **A test opened the gitignored production database.**
   `test_annual_fact_id_matches_real_database_convention` in
   `tests/unit/test_forecast.py` connected directly to
   `data/curated/target_cash.db` to check an ID-format convention. That
   database is gitignored and does not exist in a fresh clone, so the
   full test suite could not pass in one — a real reproducibility gap,
   not a cosmetic one.
2. **A same-year lineage record for a cross-year dependency.**
   `forward_debt_repayment_reserve` for FY2026–FY2029 is, by its own
   formula, next fiscal year's `net_mandatory_debt_service` — it depends
   on **next year's** `debt_proceeds` and `debt_repayments`, never the
   current year's. The lineage rows built by
   `build_capacity_taxonomy_lineage` nonetheless recorded this field with
   the same same-year `fiscal_year` and same-year forecast-input citations
   as every other field, with no marker distinguishing its true
   next-year dependency, and no distinct treatment for FY2030's terminal
   proxy (which cites its **own** year's service, not a real FY2031
   obligation).
3. **The published horizon-capacity figure was gross, not net, of
   reserves.** `total_horizon_capacity_accessible` was computed as
   Opening Excess Liquidity + Cumulative Self-Funded Generation +
   Cumulative Debt-Funded Capacity — entirely **before** `Ending Reserve
   Movement` and `Terminal Forward Debt-Repayment Reserve` are deducted.
   Labeling this "accessible capacity" overstates what is actually
   deployable by the exact amount of those two reserve terms
   ($128.9M/$406.4M/$-295.2M and $0.0M/$700.0M/$0.0M respectively for
   Base/Upside/Downside) — a real, not cosmetic, overstatement of
   deployable capacity.

## 22. Item 1 — clean-clone test fix

`test_annual_fact_id_matches_real_database_convention` was rewritten as a
fully deterministic unit test with zero I/O:

```python
def test_annual_fact_id_matches_real_database_convention():
    assert f.annual_fact_id_for(
        "revenue", 2025, "latest_restated"
    ) == "annual:revenue:2025:latest_restated"
```

This still enforces the real convention (`target_cash.annual_persistence`
builds `annual_facts.annual_fact_id` with the identical
`f"annual:{metric}:{fiscal_year}:{analytical_view}"` format), it just no
longer needs the database to prove it. A repo-wide search
(`grep -rln "data/curated/target_cash.db\"" tests/`) confirmed this was
the *only* test opening the gitignored database directly — no other
test needed a corresponding fix. §28 below records the actual fresh
public-clone pytest run proving the fix.

## 23. Item 2 — cross-year lineage correction

`build_capacity_taxonomy_lineage` now special-cases
`forward_debt_repayment_reserve`. Five new additive columns were added to
`capacity_taxonomy_lineage` (migrations `0037`–`0041`, each a plain
`ColumnMigration` with a safe default — no column ever renamed or
dropped): `dependency_timing`, `input_fiscal_year`,
`next_year_debt_proceeds_fact_id`, `next_year_debt_repayments_fact_id`,
`proxy_note`.

- **FY2026–FY2029** (non-terminal years): `dependency_timing='next_year'`,
  `input_fiscal_year` = the *next* fiscal year, and explicit fact-ID
  citations built the same way `forecast.forecast_fact_id` builds every
  other forecast citation:
  `next_year_debt_proceeds_fact_id = forecast_fact_id(scenario,
  "debt_proceeds", fiscal_year + 1, FORECAST_MODEL_VERSION)` (and the
  same for `debt_repayments`). These are real fact IDs, not placeholders
  — `fct_base_debt_proceeds_2027_v1` and `fct_base_debt_repayments_2027_v1`
  were confirmed present in the production `forecast_facts` table before
  this lineage was persisted. The row's `same_year_forecast_inputs`
  field is cleared to `None` for this field, since the dependency is, by
  construction, never same-year.
- **FY2030** (terminal year): `dependency_timing='terminal_proxy'` and an
  explicit `proxy_note` stating the row repeats FY2030's own
  `net_mandatory_debt_service` as the best available FY2031 estimate and
  that **no actual FY2031 obligation is claimed**. Every other per-year
  field on every row keeps `dependency_timing='same_year'` (the
  overwhelming majority of rows — this correction touches only the one
  field whose dependency was actually cross-year).

**Integrity checks were tightened to an exact `(scenario_id, fiscal_year,
version)` match.** The persistence-time integrity check formerly named
`zero_orphan_lineage` matched only on `(scenario_id, fiscal_year)`,
which meant a `v1` result row could spuriously satisfy the existence
check for a `v2` lineage row citing the same scenario/year. It is now
`zero_orphan_lineage_exact_version`, with `AND ctr.version = ctl.version`
added to its `EXISTS` subquery. A second, new check,
`zero_orphan_horizon_lineage_exact_version`, applies the same exact-version
discipline to the separate horizon-lineage rows (`fiscal_year IS NULL`)
against `capacity_horizon_results`. A dedicated corruption test,
`test_zero_orphan_lineage_exact_version_rejects_cross_version_match` (in
`tests/unit/test_capacity_persistence.py`), manually inserts a lineage row
under `version='v2'` after deleting its true `v2` result row, leaving only
a coincidentally-matching `v1` result row for the same scenario/fiscal
year — and proves the tightened check correctly reports failure, whereas
the old, looser check would have passed it.

**A second correctness gap was found and fixed while implementing this
change**, not requested by the audit but a direct consequence of it:
renaming a field's lineage identity *within* the same version (as Item 3
below also does) changes that field's deterministic
`capacity_lineage_id` (`captaxlin_{scenario}_{metric}_{fy}_{sequence}_{version}`,
derived from field name and sequence), which orphans the row previously
persisted under the old name. `capacity_persistence.py`'s persist
function now deletes, in the same transaction as the writes and scoped
strictly to `version = preflight.version`, any `capacity_taxonomy_lineage`
row whose `capacity_lineage_id` is not among the IDs just written for
that version — never touching other, frozen versions. A dedicated test,
`test_persist_prunes_stale_current_version_lineage_after_field_rename`,
proves stale current-version rows are removed while older-version rows
with the same (now-defunct) field name survive untouched.

## 24. Item 3 — gross/net horizon-capacity split

`CapacityHorizonSummary.total_horizon_capacity_accessible` is renamed, at
the Python dataclass/display layer only, to
`gross_horizon_funding_before_reserve_adjustments`. The underlying SQL
column keeps its legacy name (`total_horizon_capacity_accessible`) for
backward compatibility — this project's migration framework treats a
SQLite column rename as unsafe (it requires a table rebuild) and never
performs one; every "rename" in this project happens at the
Python/display layer while the column name is preserved. A new field and
column, `net_horizon_deployable_capacity` (migration `0042`, a plain
additive `ColumnMigration`), holds the corrected figure:

```
gross_horizon_funding_before_reserve_adjustments
    = opening_excess_liquidity_at_horizon_start
    + cumulative_self_funded_generation
    + cumulative_debt_funded_capacity

net_horizon_deployable_capacity
    = gross_horizon_funding_before_reserve_adjustments
    - ending_reserve_movement
    - terminal_forward_debt_repayment_reserve
```

A new named check, `net_horizon_capacity_reconciles`, proves the dual
identity the authorization required — that the net figure equals **both**
(gross minus the two reserve terms) **and**
(`cumulative_discretionary_deployment + terminal_remaining_headroom`) —
for every scenario:

| Scenario | Gross Horizon Funding, Before Reserve Adjustments (legacy label/column) | Ending Reserve Movement | Terminal Forward Debt-Repayment Reserve | **Net Horizon Deployable Capacity** |
|---|---|---|---|---|
| Base | $9,303.9M | $128.9M | $0.0M | **$9,175.0M** |
| Upside | $8,527.1M | $406.4M | $700.0M | **$7,420.7M** |
| Downside | $6,092.3M | $(295.2)M | $0.0M | **$6,387.5M** |

These NET values match the authorization's required values exactly:
**Base $9,175.0M, Upside $7,420.7M, Downside $6,387.5M.** Per the
authorization: **do not publish $9,303.9M / $8,527.1M / $6,092.3M as
"accessible capacity" — those are gross figures before reserve
adjustments.** Every deliverable in this closeout (Excel, Power BI, web
cockpit, this document, and the portfolio package) now labels the gross
figure explicitly as pre-reserve and non-headline, and uses
`net_horizon_deployable_capacity` as the sole "accessible capacity"
figure.

## 25. Validation totals (19 named checks, 213 results per version)

One new check, `net_horizon_capacity_reconciles`, was added to
`CAPACITY_CHECK_METADATA` (18 → 19 named checks) and wired into
`validate_capacity_taxonomy_all` as a fifth per-scenario cumulative/
horizon check. **Result for `v2`: 213/213 PASS** (13 per-scenario-year
checks × 15 scenario-years + 1 forward-reserve-documentation check × 3
scenarios + 5 per-scenario cumulative/horizon checks × 3 scenarios).
Combined with forecast (229) and valuation (28): **470 total validation
results, all PASS.** `v1`'s own 147 results are untouched — this
correction adds a new check and new lineage detail to `v2` only; it does
not re-run or reinterpret `v1`.

## 26. Database, persistence, and versioning evidence

- **No version bump.** Unlike Parts I→II, this closeout does not
  introduce `version='v3'`. Items 2 and 3 add columns and lineage detail
  *within* `v2` — they correct how `v2` is recorded and labeled, not
  `v2`'s own per-year arithmetic, which the authorization explicitly
  approved and required to remain unchanged. All six new migrations
  (`0037`–`0042`) are plain additive `ColumnMigration`s with safe
  defaults, verified to apply cleanly against scratch copies of the
  production database before ever touching the real one.
- **Real production database persisted twice**, proving idempotency:
  both runs wrote 15 / 3 / 312 / 213 rows respectively to
  `capacity_taxonomy_results` / `capacity_horizon_results` (per version)
  `capacity_taxonomy_lineage` / `capacity_validation_results` (per
  version), with identical row counts and content both times. Final
  production row counts: `capacity_taxonomy_results` = 30 (15 `v1` + 15
  `v2`), `capacity_horizon_results` = 6 (3 + 3), `capacity_taxonomy_lineage`
  = 543 (231 `v1` + 312 `v2` — correctly pruned from a would-be 546 per
  the stale-lineage fix in §23), `capacity_validation_results` = 360
  (147 `v1` + 213 `v2`).
- **Integrity: `all_passed: true`** on both persists, including the two
  new exact-version checks (`zero_orphan_lineage_exact_version`,
  `zero_orphan_horizon_lineage_exact_version`).
- **Backup taken before either persist**:
  `data/curated/target_cash.db.backup-20260916T225500Z`
  (sha256 `ba1bfe2a34adaebf88f3a94862625c21bbb7c6fbaacbe8a4c349c1af8a7054eb`).

## 27. Deliverable-by-deliverable verification (final closeout)

### 27.1 Python / tests
`tests/unit/test_forecast.py`: the one database-dependent test rewritten
as a deterministic unit test (§22). `tests/unit/test_capacity_taxonomy.py`:
50 tests, all passing. `tests/unit/test_capacity_persistence.py`: 15
tests, all passing, including the two new corruption/pruning tests from
§23. **Full source-complete suite: 466/466 passed** (`.venv/bin/python -m
pytest -q`). See §28 for the separate fresh-public-clone run.

### 27.2 Excel
The cumulative-reconciliation table on the Investment Capacity sheet now
carries both figures explicitly labeled: "Gross Horizon Funding, Before
Reserve Adjustments (C+A+B) -- NOT net accessible capacity" and "NET
Horizon Deployable Capacity (Gross - Reserve Mvmt - Terminal Forward
Reserve)," with the NET row bolded. `scripts/verify_excel_model.py`:
**41/41 checks pass**, including new checks that the Excel gross/net
figures match Python exactly for all three scenarios, that NET differs
from gross whenever reserves are nonzero, and that NET equals cumulative
deployment plus terminal headroom in the live, recalculated workbook.

### 27.3 Power BI handoff
`fact_capacity_horizon.csv` now includes `net_horizon_deployable_capacity`.
The `Total Horizon Capacity Accessible` DAX measure is relabeled `Gross
Horizon Funding, Before Reserve Adjustments` with an explicit "NOT
accessible capacity" disclaimer, and a new `Net Horizon Deployable
Capacity` measure is added as the corrected headline. `data_dictionary.md`
and `validation_totals.md` both carry the gross/net split, the corrected
213/470 check counts, and the explicit "do not publish the gross figures
as accessible capacity" instruction. `scripts/verify_powerbi_handoff.py`:
**168/168 checks pass**, including exact-value checks for all three
scenarios' NET figures ($9,175.0M / $7,420.7M / $6,387.5M) and a check
that no bare "deployable capacity" mention in the DAX documentation lacks
a legacy/deprecated qualifier.

### 27.4 Web cockpit
The horizon table now shows both figures as distinct, separately styled
rows — gross labeled "(NOT accessible capacity)," net labeled "(corrected
headline figure, replaces legacy gross total)" — with a caption spelling
out both reconciliation identities. `scripts/verify_web_cockpit.py`
(Playwright against the pre-installed headless Chromium): **44/44 checks
pass**, including exact-value checks for all three scenarios' NET figures
and both reconciliation identities (gross-minus-reserves and
deployment-plus-headroom), run against `deliverables/web_cockpit/data/model_data.json`
regenerated via `scripts/build_web_cockpit_data.py`.

### 27.5 Portfolio / recruiter package
`04_data_dictionary.md`: `capacity_horizon_results` and
`capacity_taxonomy_lineage` row descriptions rewritten for the gross/net
split and the next-year/terminal-proxy lineage model, with the exact
expected NET values and the explicit "never publish gross as accessible
capacity" instruction. `05_model_risk_and_limitations.md`: validation
count corrected from 467/210 to **470/213**.

## 28. Fresh public-clone and clean-room evidence

(Recorded in the final report accompanying this commit — see the
session's final report for the literal `git clone` transcript into a new
temporary directory, the `pytest` run against that clone with no database
copied or built beforehand, and the `scripts/clean_room_rebuild.py` +
`scripts/compare_databases.py` canonical-export comparison.)

## 29. Limitations (final-closeout-specific, in addition to Parts I–II)

- **No version bump for Items 2–3.** This is a deliberate scope decision,
  not an oversight: the authorization explicitly approved `v2`'s per-year
  formulas and asked only for corrected lineage recording and a corrected
  horizon label/split, both implemented as additive detail *within* `v2`.
  A future consumer reading `v2` lineage rows should be aware that the
  five new lineage columns did not exist before this closeout — a `v2`
  row persisted before this round (there is none in production, since
  this closeout was applied before any external consumer read `v2`) would
  have had `NULL`/default values in those columns.
- **The gross column's SQL name is unchanged.** `total_horizon_capacity_accessible`
  remains the literal column name in `capacity_horizon_results` and every
  CSV export; only the Python dataclass field and every human-facing label
  (Excel, DAX, web cockpit, documentation) are renamed. A consumer
  querying the raw SQL/CSV by column name must know this to avoid
  re-introducing the original mislabeling.
- **The terminal-year forward-reserve proxy limitation from Part II §20
  is unchanged and still applies** — FY2030's `forward_debt_repayment_reserve`
  (and, transitively, its lineage's `terminal_proxy` note) remains a
  documented estimate, not a real scheduled FY2031 obligation.
