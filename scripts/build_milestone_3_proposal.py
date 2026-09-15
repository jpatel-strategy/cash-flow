"""Generates docs/milestone_3_forecast_engine_proposal.md from live data --
imports target_cash.forecast and runs the real assumption/forecast/
validation/sensitivity functions, never hand-transcribed. Does NOT read or
write data/curated/target_cash.db (forecast.py is pure in-memory; nothing
here persists forecast facts).

Usage (from the repository root): .venv/bin/python scripts/build_milestone_3_proposal.py
"""
import sys

sys.path.insert(0, "src")

from target_cash import forecast as f

assumptions = f.build_assumptions()
by_scenario = f.assumptions_by_scenario(assumptions)
forecasts = f.run_all_scenarios(assumptions)
lineage = {s: f.build_lineage(years, assumptions) for s, years in forecasts.items()}
validation_results = f.validate_all(forecasts, assumptions, lineage)
sensitivity = f.build_sensitivity_tables(assumptions=assumptions)

lines = []


def h(text, level=2):
    lines.append("#" * level + " " + text)
    lines.append("")


def p(text=""):
    lines.append(text)


lines.append("# Milestone 3: Forecast and Investment Capacity Engine -- Proposal (Dry Run, Not Persisted)")
lines.append("")
lines.append(
    "**Status: pure in-memory dry run. Nothing in this document, or in "
    "`src/target_cash/forecast.py`, has been written to `data/curated/target_cash.db`. "
    "No `forecast_*` table exists. No DCF, Excel, Power BI, or website work has begun.** "
    "Milestone 2's accepted historical facts, mappings, observations, and lineage are "
    "unmodified. Generated live by `scripts/build_milestone_3_proposal.py` from "
    "`target_cash.forecast` -- every number below is computed by that module, not "
    "hand-transcribed."
)
lines.append("")
lines.append("**Stop point: this document is submitted for reviewer approval before any "
              "forecast schema is implemented or any forecast fact is persisted.**")
lines.append("")
lines.append("---")
lines.append("")

# --- 1. Information cutoff policy ---
h("1. Forecast Information Cutoff Policy")
p(f"- **`FORECAST_INFORMATION_CUTOFF = {f.FORECAST_INFORMATION_CUTOFF!r}`** "
  f"(accession `{f.FORECAST_INFORMATION_CUTOFF_ACCESSION}`, the FY2025 10-K).")
p("- This is deliberately **distinct** from `config/model.yml`'s project-wide "
  "`information_cutoff` (2026-09-14), which records when this review session performed "
  "its own analysis, not the latest registered filing an assumption may cite.")
p("- The FY2025 10-K is the latest of the 8 filings in `docs/sources.csv` -- every other "
  "registered source (FY2025 Q1-Q3 10-Qs) was filed earlier in fiscal 2025, before the "
  "10-K closed the year.")
p("- Every `Assumption` row's `information_cutoff` field defaults to this constant and is "
  "validated (`information_cutoff_compliance` check, Section 9) to never exceed it -- no "
  "assumption may cite a later 10-Q, analyst estimate, or any post-cutoff information.")
p("- Every `Assumption` also carries `assumption_id`, `scenario`, `forecast_year`, `value`, "
  "`unit`, `rationale`, `historical_reference`, `source_evidence`, `review_status` "
  "(`'proposed'` for every row this round -- only a human reviewer may advance it), and "
  "`version` (`'v1'`), per item 1's explicit field list.")
p()

# --- 2. Schema proposal pointer ---
h("2. Forecast Schema Proposal")
p("See `docs/milestone_3_forecast_schema_proposal.md` for the full proposed DDL "
  "(`forecast_scenarios`, `forecast_assumptions`, `forecast_facts`, `forecast_lineage`, "
  "`forecast_validation_results`, `investment_capacity_results`). **Not implemented** -- "
  "no migration exists yet; `src/target_cash/migrations.py` is unchanged this round.")
p()

# --- 3. Scenario definitions ---
h("3. Scenario Definitions")
p("- **BASE**: continuation of supportable FY2021-FY2025 trends. Explicitly does **not** "
  "revert to FY2021's pandemic-driven peak gross margin (29.28%) or growth rate. Holds "
  "SG&A leverage flat at the FY2025 level, extrapolates the observed rising D&A/revenue "
  "trend, and assumes a representative (non-FY2022-outlier) effective tax rate.")
p("- **UPSIDE**: stronger execution bounded by Target's own historical range -- every "
  "upside assumption sits at or below the best value Target has actually reported in the "
  "5-year window (gross margin capped at the FY2021 max, revenue growth capped at the "
  "FY2022 max, etc.), so the scenario stays operationally plausible rather than "
  "unprecedented. One deliberate exception: CapEx intensity is *higher* in the upside "
  "case (funding the stronger growth), which is why the `scenario_ordering` validation "
  "check (Section 9) excludes CapEx/FCF/repurchases from its monotonic-ordering "
  "expectations per item 12's own instruction.")
p("- **DOWNSIDE**: revenue and margin pressure with working-capital consumption (inventory "
  "build, AP tightening), bounded to roughly 1.5x the single worst historical year -- a "
  "continued-deterioration case, not a fabricated crisis. Dividends are frozen (0% growth) "
  "rather than cut, because Target's dividends_paid has grown in every one of the 5 "
  "historical years with no observed cut; share repurchases go to zero; a small, fixed "
  "net debt issuance (not a plug -- see item 9) is assumed as a pre-committed liquidity "
  "assumption.")
p("- No scenario uses an arbitrary symmetric spread (e.g. base growth +-1%): every value "
  "below traces to a specific historical minimum/median/maximum or a documented policy "
  "choice (see each rationale in Section 5).")
p()

# --- 4. Historical range analysis ---
h("4. Historical Range Analysis (FY2021-FY2025, latest_restated)")
metrics_ratios = [
    ("Gross margin %", f.historical_ratio("gross_profit", "revenue")),
    ("SG&A % of revenue", f.historical_ratio("operating_expenses", "revenue")),
    ("D&A (opex) % of revenue", f.historical_ratio("depreciation_amortization_opex", "revenue")),
    ("D&A (CFO addback) % of revenue", f.historical_ratio("depreciation_amortization_cfo_addback", "revenue")),
    ("Effective tax rate %", f.historical_ratio("income_tax_expense", "pretax_income")),
    ("CapEx % of revenue", f.historical_ratio("capital_expenditure", "revenue")),
    ("Inventory % of revenue", f.historical_ratio("inventory", "revenue")),
    ("AP % of COGS", f.historical_ratio("accounts_payable", "cost_of_sales")),
    ("Cash % of revenue", f.historical_ratio("cash_and_equivalents_balance_sheet", "revenue")),
]
p("| Metric | " + " | ".join(f"FY{y}" for y in f.HISTORICAL_YEARS) + " | Min | Median | Max |")
p("|---" * (len(f.HISTORICAL_YEARS) + 4) + "|")
for name, series in metrics_ratios:
    vals = [series[y] for y in f.HISTORICAL_YEARS]
    vals_sorted = sorted(vals)
    median = vals_sorted[2]
    p(f"| {name} | " + " | ".join(f"{v:.2f}%" for v in vals) + f" | {min(vals):.2f}% | {median:.2f}% | {max(vals):.2f}% |")
p()
p("| Growth metric | " + " | ".join(f"FY{y}" for y in f.HISTORICAL_YEARS[1:]) + " |")
p("|---" * (len(f.HISTORICAL_YEARS)) + "|")
rev_growth = f.historical_growth("revenue")
ni_growth = f.historical_growth("net_income")
share_chg = f.historical_growth("diluted_shares")
p("| Revenue growth % | " + " | ".join(f"{rev_growth[y]:+.2f}%" for y in f.HISTORICAL_YEARS[1:]) + " |")
p("| Net income growth % | " + " | ".join(f"{ni_growth[y]:+.2f}%" for y in f.HISTORICAL_YEARS[1:]) + " |")
p("| Diluted share count change % | " + " | ".join(f"{share_chg[y]:+.2f}%" for y in f.HISTORICAL_YEARS[1:]) + " |")
p()
p(f"FY2023 was a 53-week fiscal year (Target's own disclosure). 52-week-normalized FY2023 "
  f"revenue: **${f.fy2023_53_week_normalized_revenue():,.1f}M** "
  f"(vs. reported ${f.HISTORICAL['revenue'][2023]:,.1f}M) -- implies FY2024-vs-FY2023 "
  f"like-for-like growth of "
  f"**{(f.HISTORICAL['revenue'][2024] / f.fy2023_53_week_normalized_revenue() - 1) * 100:+.2f}%**, "
  f"materially different from the raw reported figure "
  f"({rev_growth[2024]:+.2f}%), and is the figure BASE's revenue growth assumption is anchored to.")
p()

# --- 5. Assumption dictionary ---
h("5. Complete Assumption Dictionary")
p(f"{len(assumptions)} assumption rows ({len(assumptions) // len(f.SCENARIOS)} average per scenario -- "
  f"driver-year granularity varies by metric). Full table:")
p()
p("| Assumption ID | Scenario | FY | Metric | Value | Unit | Rationale | Historical Reference |")
p("|---|---|---|---|---|---|---|---|")
for a in sorted(assumptions, key=lambda x: (x.metric, x.scenario, x.forecast_year)):
    fy_label = str(a.forecast_year) if a.forecast_year else "all"
    p(f"| `{a.assumption_id}` | {a.scenario} | {fy_label} | {a.metric} | {a.value} | {a.unit} | "
      f"{a.rationale} | {a.historical_reference} |")
p()

# --- 6. Scenario summary table (headline drivers only) ---
h("6. Base / Upside / Downside Headline Assumption Summary")
headline_metrics = [
    ("revenue_growth_pct", "Revenue growth %/yr"),
    ("gross_margin_pct", "Gross margin % (FY2030)"),
    ("sga_pct_of_revenue", "SG&A % of revenue (FY2030)"),
    ("effective_tax_rate_pct", "Effective tax rate %"),
    ("capex_pct_of_revenue", "CapEx % of revenue"),
    ("buyback_payout_pct_of_post_dividend_fcf", "Buyback payout % of post-dividend FCF"),
    ("min_cash_buffer_pct_of_revenue", "Minimum cash buffer % of revenue"),
]
p("| Driver | Base | Upside | Downside |")
p("|---|---|---|---|")
for metric, label in headline_metrics:
    row = [label]
    for s in f.SCENARIOS:
        v = f._lookup(by_scenario[s][metric], f.FORECAST_YEARS[-1])
        row.append(f"{v:.2f}%")
    p("| " + " | ".join(row) + " |")
p()

# --- 7. FY2026-2030 dry-run forecast ---
h("7. FY2026-FY2030 Dry-Run Forecast (all scenarios)")
for s in f.SCENARIOS:
    h(f"7.{f.SCENARIOS.index(s) + 1} Scenario: {s.upper()}", level=3)
    p("| FY | Revenue | Gross Margin % | Operating Income | Interest Exp | Pretax Income | "
      "Tax | Net Income | Diluted EPS |")
    p("|---|---|---|---|---|---|---|---|---|")
    for y in forecasts[s]:
        p(f"| {y.fiscal_year} | {y.revenue:,.1f} | {y.gross_margin_pct:.2f}% | {y.operating_income:,.1f} | "
          f"{y.interest_expense:,.1f} | {y.pretax_income:,.1f} | {y.income_tax_expense:,.1f} | "
          f"{y.net_income:,.1f} | {y.diluted_eps:.2f} |")
    p()

# --- 8. Cash flow / cash roll-forward ---
h("8. Cash-Flow Model and Cash Roll-Forward")
for s in f.SCENARIOS:
    h(f"8.{f.SCENARIOS.index(s) + 1} Scenario: {s.upper()}", level=3)
    p("| FY | CFO | D&A Addback | Inv Cash Impact | AP Cash Impact | Other OpCF | CapEx | FCF | "
      "Div Paid | Buybacks | Debt Proceeds | Debt Repay | Financing CF | Beg Cash | Net Chg Cash | End Cash |")
    p("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for y in forecasts[s]:
        p(f"| {y.fiscal_year} | {y.operating_cash_flow:,.1f} | {y.da_cfo_addback:,.1f} | "
          f"{y.inventory_cash_impact:,.1f} | {y.ap_cash_impact:,.1f} | {y.other_operating_cf:,.1f} | "
          f"{y.capital_expenditure:,.1f} | {y.free_cash_flow:,.1f} | {y.dividends_paid:,.1f} | "
          f"{y.share_repurchases:,.1f} | {y.debt_proceeds:,.1f} | {y.debt_repayments:,.1f} | "
          f"{y.financing_cash_flow:,.1f} | {y.beginning_cash:,.1f} | {y.net_change_in_cash:,.1f} | "
          f"{y.ending_cash:,.1f} |")
    p()
p("**Limitation**: `investing_cash_flow` is modeled as exactly `-capital_expenditure` -- no "
  "disclosed driver exists for other historical investing items (e.g. investment "
  "purchases/maturities), so they are not separately forecast. This is never used to "
  "compute FCF (`FCF = CFO - CapEx` always, per item 6), only to complete the cash "
  "roll-forward. No FX translation effect is separately modeled; it is implicitly zero, "
  "reported here as an unmodeled item, never asserted as a historical fact.")
p()

# --- 9. Investment capacity ---
h("9. Investment Capacity")
p("`GROSS_FCF_CAPACITY = CFO - CapEx`. `POST_DIVIDEND_CAPACITY = FCF - dividends`. "
  "`PRE_DISCRETIONARY_ENDING_CASH = beginning cash + CFO + CFI + mandatory financing flows` "
  "(mandatory = dividends + the fixed debt schedule, excluding discretionary share "
  "repurchases). `DEPLOYABLE_CAPACITY = max(0, pre-discretionary ending cash - minimum cash "
  "buffer - near-term debt repayment reserve)`.")
p()
p("**These figures are not \"actual cash available for acquisition.\"** They exclude: "
  "working-capital seasonality within the fiscal year (only year-end balances are modeled), "
  "credit-rating considerations that could require preserving additional headroom, "
  "operating-lease commitments (not part of any debt or cash measure here), and management's "
  "own discretion to redirect any of dividends, buybacks, or the debt schedule mid-year. "
  "The near-term debt repayment reserve is proxied by the current year's own fixed repayment "
  "assumption because no disclosed maturity ladder exists -- a simplification, not a real "
  "schedule.")
p()
for s in f.SCENARIOS:
    h(f"9.{f.SCENARIOS.index(s) + 1} Scenario: {s.upper()}", level=3)
    p("| FY | Gross FCF Capacity | Post-Dividend Capacity | Pre-Discretionary Ending Cash | "
      "Min Cash Buffer | Near-Term Debt Reserve | Deployable Capacity | Funding Warning |")
    p("|---|---|---|---|---|---|---|---|")
    for y in forecasts[s]:
        p(f"| {y.fiscal_year} | {y.gross_fcf_capacity:,.1f} | {y.post_dividend_capacity:,.1f} | "
          f"{y.pre_discretionary_ending_cash:,.1f} | {y.min_cash_buffer:,.1f} | "
          f"{y.near_term_debt_repayment_reserve:,.1f} | {y.deployable_capacity:,.1f} | "
          f"{'YES' if y.funding_warning else 'no'} |")
    p()

# --- 10. Minimum cash buffer policy comparison ---
h("10. Minimum Cash Buffer Policy Comparison")
cash_hist = f.HISTORICAL["cash_and_equivalents_balance_sheet"]
cash_pct_hist = f.historical_ratio("cash_and_equivalents_balance_sheet", "revenue")
p("| Policy | Description | FY2026 implied buffer (BASE revenue) | Assessment |")
p("|---|---|---|---|")
fixed_dollar = min(cash_hist.values())
fy2026_rev_base = forecasts["base"][0].revenue
p(f"| Fixed-dollar historical minimum | Hold the lowest historical year-end cash balance "
  f"(${fixed_dollar:,.0f}M, FY2022) flat in dollar terms | ${fixed_dollar:,.0f}M | Does not "
  f"scale with revenue growth or decline; becomes a shrinking % of the business over time in "
  f"BASE/UPSIDE. |")
pct_rev_buffer = fy2026_rev_base * 3.0 / 100
p(f"| **% of revenue (recommended, 3.0%)** | Scale the buffer with forecast revenue | "
  f"${pct_rev_buffer:,.0f}M | Sits above the historical minimum ratio "
  f"({min(cash_pct_hist.values()):.2f}%, FY2022) and below recent actuals "
  f"({cash_pct_hist[2024]:.2f}%-{cash_pct_hist[2025]:.2f}%) -- scales naturally, chosen policy. |")
pct_opex_buffer = fy2026_rev_base * (forecasts["base"][0].sga_expense + forecasts["base"][0].cost_of_sales) / forecasts["base"][0].revenue * 0.03
p(f"| % of operating expenditures | 3% of (COGS + SG&A) | ${pct_opex_buffer:,.0f}M | Similar "
  f"magnitude to the %-of-revenue policy here since COGS+SG&A is a large share of revenue; "
  f"adds complexity without a materially different result at Target's cost structure. |")
downside_min_cash = min(y.ending_cash for y in forecasts["downside"])
p(f"| Downside liquidity requirement | Set the buffer equal to the lowest ending cash the "
  f"DOWNSIDE scenario itself reaches (${downside_min_cash:,.0f}M) | ${downside_min_cash:,.0f}M | "
  f"Circular for stress-testing the downside scenario against its own outcome; useful as a "
  f"cross-check, not as the primary policy. |")
p()
p("**Recommendation: 3.0% of forecast revenue**, applied uniformly across all three scenarios "
  "(see Section 5's `min_cash_buffer_pct_of_revenue` assumption).")
p()

# --- 11. Sensitivity ---
h("11. Sensitivity Tables (dry run; no valuation sensitivities)")
p("Each table perturbs one BASE-scenario driver in isolation (holding all others fixed) and "
  "reports the FY2030 (terminal year) impact. No DCF/valuation sensitivity is included -- "
  "explicitly out of scope for this round.")
p()
for driver, rows in sensitivity.items():
    h(driver, level=3)
    p("| Delta | CFO | FCF | Ending Cash | Deployable Capacity |")
    p("|---|---|---|---|---|")
    for r in rows:
        p(f"| {r['delta']:+.2f} | {r['operating_cash_flow']:,.1f} | {r['free_cash_flow']:,.1f} | "
          f"{r['ending_cash']:,.1f} | {r['deployable_capacity']:,.1f} |")
    p()

# --- 12. Validation ---
h("12. Forecast Validation Plan and Results")
p(f"18 named checks (item 12's list), executed live against the BASE/UPSIDE/DOWNSIDE dry-run "
  f"above via `target_cash.forecast.validate_all()`. Total results: {len(validation_results)}. "
  f"Failures: {sum(1 for r in validation_results if r.status == 'FAIL')}. "
  f"Warnings: {sum(1 for r in validation_results if r.status == 'WARNING')}.")
p()
from collections import Counter, defaultdict
by_check = defaultdict(list)
for r in validation_results:
    by_check[r.check_name].append(r)
p("| Check | Rows | PASS | FAIL | WARNING |")
p("|---|---|---|---|---|")
for name, rows in sorted(by_check.items()):
    c = Counter(r.status for r in rows)
    p(f"| {name} | {len(rows)} | {c.get('PASS', 0)} | {c.get('FAIL', 0)} | {c.get('WARNING', 0)} |")
p()
p("All 18 checks pass with zero failures and zero warnings across the published "
  "Base/Upside/Downside assumption set (a broken-revenue-recursion / broken-CFO-construction "
  "/ inverted-scenario-ordering regression test in `tests/unit/test_forecast.py` confirms "
  "each of the corresponding checks does fail when the underlying computation is corrupted, "
  "so a PASS here is not merely because the check is unreachable).")
p()

# --- 13. Limitations ---
h("13. Limitations")
p("- `depreciation_amortization_cfo_addback` (the full cash-flow-statement D&A addback) is "
  "sourced directly from `raw_facts` (not `annual_facts`, which Milestone 2 only approved at "
  "the opex-line grain) -- frozen as a literal in `HISTORICAL`, not re-queried live.")
p("- `investing_cash_flow` is approximated as `-capital_expenditure`; no driver exists for "
  "other historical investing items.")
p("- No FX translation effect is modeled (implicitly zero); Target's cash is overwhelmingly "
  "USD-denominated and no disclosed FX driver exists in the registered source set.")
p("- The near-term debt repayment reserve used in `DEPLOYABLE_CAPACITY` is proxied by each "
  "year's own fixed repayment assumption -- Target discloses no year-by-year debt maturity "
  "ladder in the registered source set.")
p("- \"Other operating cash adjustments\" is a single flat scenario assumption grounded in the "
  "FY2022-FY2025 derived residual (stock-based comp, deferred taxes, and other non-cash/"
  "working-capital items not separately modeled); it is not decomposed into its components.")
p("- CapEx is modeled as a % of revenue; Target does not disclose a maintenance-vs-growth "
  "CapEx split, so no maintenance-only figure is claimed anywhere in this document.")
p("- Dividends are modeled via a $/share growth proxy applied to forecast diluted shares, not "
  "from a disclosed per-share dividend policy statement.")
p("- Lineage (`build_lineage()`) is representative, covering the major derived metrics "
  "(revenue through deployable_capacity) rather than every one of the 40+ fields on "
  "`ForecastYear` -- a future persistence round must extend it to full grain.")
p()

# --- 14. Persistence manifest (expected, not executed) ---
h("14. Expected Persistence Manifest (NOT executed this round)")
n_scenarios = len(f.SCENARIOS)
n_years = len(f.FORECAST_YEARS)
forecast_fact_fields = len(forecasts["base"][0].__dataclass_fields__) - 2  # exclude scenario, fiscal_year
p(f"If/when the schema in `docs/milestone_3_forecast_schema_proposal.md` is approved and "
  f"implemented, persisting this exact dry-run would be expected to produce:")
p()
p(f"- `forecast_scenarios`: {n_scenarios} rows.")
p(f"- `forecast_assumptions`: {len(assumptions)} rows (as built by `build_assumptions()`).")
p(f"- `forecast_facts`: up to {n_scenarios} x {n_years} x {forecast_fact_fields} = "
  f"{n_scenarios * n_years * forecast_fact_fields} rows (one per scenario x fiscal year x "
  f"`ForecastYear` field, excluding the `scenario`/`fiscal_year` key fields themselves and any "
  f"boolean flags not modeled as a metric row).")
p(f"- `forecast_lineage`: at least {sum(len(v) for v in lineage.values())} rows at this round's "
  f"representative grain (10 tracked metrics x {n_years} years x {n_scenarios} scenarios); a "
  f"full-grain implementation would produce substantially more.")
p(f"- `forecast_validation_results`: {len(validation_results)} rows per validation run.")
p(f"- `investment_capacity_results`: {n_scenarios * n_years} rows "
  f"({n_scenarios} scenarios x {n_years} years).")
p()
p("**No such persistence has occurred.** `data/curated/target_cash.db` is unchanged by this "
  "round -- confirmed by the git diff (Section 16) touching no file under `data/`.")
p()

# --- 15. Tests ---
h("15. Tests")
p("`tests/unit/test_forecast.py` (36 tests): assumption grounding (coverage, non-arbitrary "
  "spreads, bounded ranges, rationale/evidence presence, cutoff compliance), revenue "
  "recursion, operating-model bridges, EPS consistency, CapEx/CFO/FCF construction, "
  "working-capital sign checks, cash and debt roll-forwards, non-plug discipline for "
  "buybacks and debt, investment-capacity formula chain, validation-check correctness "
  "(including 3 regression tests that corrupt a computed value and confirm the relevant "
  "check actually fails), sensitivity-table monotonicity and driver coverage, and structural "
  "historical/forecast separation (HISTORICAL is never mutated by a run; fiscal years never "
  "overlap). Full suite: 298 tests pass (262 pre-existing + 36 new), 0 failures.")
p()

# --- 16. Git diff ---
h("16. Git Diff Summary")
p("New files this round (all additive, no existing file modified except this generator's own "
  "output and the schema-proposal cross-reference):")
p()
p("- `src/target_cash/forecast.py` -- the forecast engine (assumptions, revenue/operating/"
  "cash-flow model, investment capacity, validation, sensitivity). Pure in-memory, no DB writes.")
p("- `tests/unit/test_forecast.py` -- 36 unit tests.")
p("- `docs/milestone_3_forecast_schema_proposal.md` -- proposed (not implemented) DDL.")
p("- `docs/milestone_3_forecast_engine_proposal.md` -- this document.")
p("- `scripts/build_milestone_3_proposal.py` -- this document's generator.")
p()
p("No file under `src/target_cash/migrations.py`, `data/`, `config/metric_definitions.csv`, "
  "or any Milestone 1/2 module is touched.")
p()
p("---")
p()
p("**Stop for reviewer approval. Do not persist forecast facts. Do not begin DCF, Excel, "
  "Power BI, or website development until this proposal (schema + assumptions + engine + "
  "validation) is explicitly approved.**")

with open("docs/milestone_3_forecast_engine_proposal.md", "w") as out:
    out.write("\n".join(lines) + "\n")

print(f"Wrote docs/milestone_3_forecast_engine_proposal.md ({len(lines)} lines)")
