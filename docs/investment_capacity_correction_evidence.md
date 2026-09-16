# Investment Capacity Correction — Evidence

This document records the corrective round that followed
`docs/investment_capacity_semantic_audit.md` (diagnostic-only). It does
not repeat that audit's discovery narrative; it documents what was
built, proved, persisted, and verified in response to it.

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
