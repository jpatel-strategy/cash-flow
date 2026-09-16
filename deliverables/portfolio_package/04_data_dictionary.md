# Data Dictionary (Project-Wide)

A high-level map of the whole database. For the full column-by-column
detail of the forecast/valuation export used by Excel, Power BI, and the
web cockpit, see `deliverables/powerbi_handoff/data_dictionary.md` —
this file gives the whole-database picture that sits behind it.

`data/curated/target_cash.db` (SQLite), 28 tables, 6,646 rows as of the
last full pipeline run (2026-09-16), including both the original
capacity-taxonomy correction round (`version='v1'`, preserved for audit
trail) and its v2 finance-semantics follow-up correction
(`version='v2'`, current).

## Source and lineage layer

| Table | Grain | Purpose |
|---|---|---|
| `filings` | one row per SEC filing | The 8 registered 10-K/10-Q filings this entire project is built from — accession number, filed date, period of report, source URL, ingestion notes. |
| `raw_facts` | one row per as-extracted XBRL fact | The unmapped, as-filed data, before any classification or validation. |
| `concept_equivalence_rules` | one row per XBRL-tag-to-metric mapping | The approved mapping from SEC XBRL concepts to this project's internal metric names, with an approval/evidence trail. |
| `lineage` / `annual_lineage` | one row per derived value's inputs | Which raw facts and formulas produced each historical derived metric. |

## Historical facts layer

| Table | Grain | Purpose |
|---|---|---|
| `annual_facts` | (metric, fiscal_year, analytical_view) | The core historical dataset — FY2021-FY2025, in both `as_originally_filed` and `latest_restated` views, with full validation status and source citation per row. |
| `annual_fact_observations` | one row per fact per relationship type | The enriched classification layer (e.g. "original_historical", "restated") proving completeness of the historical record. |
| `instant_facts` / `instant_fact_observations` | one row per balance-sheet date | Point-in-time facts (e.g. quarterly cash balances) rather than period facts. |
| `quarterly_facts` | one row per quarterly metric | The 5-metric quarterly analytical view used for the seasonal cash-proof evidence. |
| `fiscal_calendar` | one row per fiscal period | Target's non-calendar fiscal year definitions, including the FY2023 53-week year. |

## Forecast layer (Milestone 3B)

| Table | Grain | Purpose |
|---|---|---|
| `forecast_scenarios` | one row per scenario | Base/Upside/Downside definitions, versioned, with an information cutoff. |
| `forecast_assumptions` | (scenario, metric, forecast_year) | The 19 x 3 x 5 = 285 named assumption values driving the forecast, each with a rationale and source-evidence citation. |
| `forecast_facts` | (scenario, fiscal_year, metric) | The 51-metric x 3-scenario x 5-year = 765 computed forecast results. |
| `forecast_lineage` | one row per field-level dependency | Full formula-and-input lineage for every one of the 51 forecast fields — the "why is this number what it is" answer for any cell. |
| `forecast_validation_results` | one row per check per scenario/year | 229 automated validation results (all PASS as of the last run). |
| `investment_capacity_results` | (scenario, fiscal_year) | The capital-allocation waterfall's 9 stages, plus the corrected cumulative-deployable-capacity figure and a mandatory methodology disclosure per row. **Superseded for headline use** by the capacity-taxonomy tables below; preserved unmodified for backward compatibility and historical/methodology reference only. |

## Capacity taxonomy layer (correction round)

| Table | Grain | Purpose |
|---|---|---|
| `capacity_taxonomy_results` | (scenario, fiscal_year, version) | The corrected capacity taxonomy, versioned: `v1` fixed the legacy field's double-subtraction of mandatory debt repayments; `v2` (current) additionally corrects the economic mislabeling of gross debt issuance as capacity — debt-funded capacity is now the NET of proceeds over repayments (gross issuance that is simultaneously repaid is $0 capacity, never the gross amount), and self-funded capacity generated now excludes opening excess liquidity (a stock) entirely. Both versions preserved permanently for audit trail; only `v2` is used by any current KPI, formula, or downstream export. |
| `capacity_horizon_results` | one row per (scenario, version) | Five-year cumulative reconciliation: total horizon capacity accessible, cumulative self-funded/debt-funded generation, cumulative discretionary deployment, terminal remaining headroom, ending reserve-movement, and (v2 only) a terminal forward debt-repayment reserve term — the identity reconciles exactly across all four/five terms. |
| `capacity_taxonomy_lineage` | one row per field-level dependency | Formula-and-input lineage for every new derived capacity-taxonomy field. |
| `capacity_validation_results` | one row per check per scenario/year | 147 automated validation results proving the 13 named capacity-taxonomy identities (conservation, non-negativity, cross-checks against `ending_excess_liquidity`, and the horizon reconciliation identity). |

## Valuation layer (Milestone 4)

| Table | Grain | Purpose |
|---|---|---|
| `valuation_assumptions` | one row per assumption | WACC components and terminal growth, kept structurally separate from the operating-forecast assumptions. |
| `valuation_ufcf_facts` | (scenario, fiscal_year) | Unlevered free cash flow and its present value, per year. |
| `valuation_results` | one row per scenario | The full DCF bridge output — enterprise value, net debt, equity value, implied value per share. |
| `valuation_validation_results` | one row per check | 28 automated validation results (all PASS), including UFCF reconciliation and valuation-date consistency. |

## Housekeeping

| Table | Purpose |
|---|---|
| `_schema_migrations` | Tracks every additive migration applied, so the schema's own evolution is itself auditable. |
| `assumptions` / `forecasts` | Legacy/staging tables from early scaffolding — superseded by the `forecast_*` tables above; retained rather than dropped, per the project's non-destructive migration policy. |

## Presentation-layer exports (derived, not source-of-truth)

- `deliverables/powerbi_handoff/data/*.csv` — a full star-schema export
  (5 dimension + 9 fact tables) of the above, with its own detailed
  data dictionary.
- `deliverables/web_cockpit/data/model_data.json` — a single JSON
  export covering historical, forecast, valuation, validation, and
  source data, consumed by the web cockpit.
- `deliverables/Target_Cash_Flow_Investment_Capacity_Model.xlsx` — the
  same data, live-formula-driven, in spreadsheet form.

None of these exports is an independent data source — all three are
generated, reproducibly, from `data/curated/target_cash.db` by their
respective `scripts/build_*.py` generators, and can be regenerated at
any time (see `13_reproduction_instructions.md`).
