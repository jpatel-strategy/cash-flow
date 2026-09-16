"""Milestone 7: export the single JSON data file the web decision cockpit
reads. No values are computed in JavaScript that aren't computed here
first by the same target_cash.forecast/valuation modules everything else
in this project uses -- the web app's "ground truth" numbers are never
independently re-derived by hand in JS, only the optional client-side
what-if sandbox re-implements the published formula chain for
illustrative, clearly-labeled interactivity.

Usage: .venv/bin/python scripts/build_web_cockpit_data.py
"""
import dataclasses
import json
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from target_cash import forecast as f  # noqa: E402
from target_cash import valuation as v  # noqa: E402
from target_cash import capacity_taxonomy as ct  # noqa: E402

DB_PATH = REPO_ROOT / "data" / "curated" / "target_cash.db"
OUT_PATH = REPO_ROOT / "deliverables" / "web_cockpit" / "data" / "model_data.json"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

INFORMATION_CUTOFF = "2026-03-11"

# ---------------------------------------------------------------------------
# Historical (FY2021-FY2025, latest_restated only -- the current, correct view)
# ---------------------------------------------------------------------------
HIST_METRICS = [
    "revenue", "cost_of_sales", "gross_profit", "gross_margin", "operating_expenses",
    "operating_income", "operating_margin", "net_income", "net_margin",
    "diluted_eps", "diluted_shares", "operating_cash_flow", "capital_expenditure",
    "investing_cash_flow", "free_cash_flow", "fcf_margin", "dividends_paid",
    "share_repurchases", "debt_proceeds", "debt_repayments", "total_debt_gaap",
    "cash_and_equivalents_balance_sheet", "financing_cash_flow", "net_change_in_cash",
    "inventory", "accounts_payable",
]
historical = {}
for fy in f.HISTORICAL_YEARS:
    row = {}
    for metric in HIST_METRICS:
        r = conn.execute(
            "SELECT value_normalized FROM annual_facts WHERE metric=? AND fiscal_year=? "
            "AND analytical_view='latest_restated'",
            (metric, fy),
        ).fetchone()
        if r is not None:
            row[metric] = r[0]
    historical[fy] = row

# ---------------------------------------------------------------------------
# Quarterly cash proof
# ---------------------------------------------------------------------------
quarterly_cash = [
    dict(r)
    for r in conn.execute(
        "SELECT as_of_date, value_normalized AS value, accession_number "
        "FROM instant_facts WHERE metric='cash_and_equivalents_balance_sheet' "
        "ORDER BY as_of_date"
    )
]

# ---------------------------------------------------------------------------
# Filing-vintage comparison (same computation as the Excel/Power BI exports)
# ---------------------------------------------------------------------------
filing_vintage = []
for metric in ["revenue", "cost_of_sales", "gross_profit", "operating_expenses"]:
    rows = {
        (r["fiscal_year"], r["analytical_view"]): r["value_normalized"]
        for r in conn.execute(
            "SELECT fiscal_year, analytical_view, value_normalized FROM annual_facts WHERE metric=?",
            (metric,),
        )
    }
    for fy in f.HISTORICAL_YEARS:
        orig = rows.get((fy, "as_originally_filed"))
        restated = rows.get((fy, "latest_restated"))
        if orig is None or restated is None:
            continue
        filing_vintage.append(
            {
                "metric": metric, "fiscal_year": fy,
                "as_originally_filed": orig, "latest_restated": restated,
                "difference": restated - orig,
                "reclassified": abs(restated - orig) > 0.005,
            }
        )

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
sources = [
    dict(r)
    for r in conn.execute(
        "SELECT accession_number, form_type, filed_at, period_of_report, primary_document_url "
        "FROM filings ORDER BY period_of_report"
    )
]

conn.close()

# ---------------------------------------------------------------------------
# Scenarios: assumptions (for the what-if sandbox), full forecast years,
# investment capacity, waterfall, narrative
# ---------------------------------------------------------------------------
assumptions = f.build_assumptions()
by_scenario_assumptions = f.assumptions_by_scenario(assumptions)
forecasts = f.run_all_scenarios(assumptions)

scenarios_out = {}
for scenario in ["base", "upside", "downside"]:
    years = forecasts[scenario]
    years_out = [dataclasses.asdict(y) for y in years]

    # assumption values keyed by metric -> {fiscal_year: value}, restricted
    # to the 19 metrics _run_from_metrics() actually consumes, and to
    # FY2026-FY2030 only (no forecast_year=0 scenario-wide defaults leak
    # in as a spurious "year").
    asm_metrics = by_scenario_assumptions[scenario]
    asm_out = {
        metric: {str(fy): asm_metrics[metric].get(fy, asm_metrics[metric].get(0))
                 for fy in f.FORECAST_YEARS}
        for metric in asm_metrics
    }

    cum_series = f.cumulative_deployable_capacity_through_each_year(years)
    cum_terminal = f.cumulative_deployable_capacity(years)

    # Milestone 9 correction: corrected capacity taxonomy, computed purely
    # from these same ForecastYear objects -- never a re-derivation from
    # raw assumptions, and never reading the legacy deployable_capacity
    # field (see capacity_taxonomy.py's own module docstring).
    capacity_years = ct.build_capacity_taxonomy(years)
    capacity_summary = ct.compute_capacity_horizon_summary(scenario, years, capacity_years)

    scenarios_out[scenario] = {
        "name": scenario.capitalize(),
        "narrative": f.scenario_narrative(scenario),
        "assumptions": asm_out,
        "years": years_out,
        "cumulative_deployable_capacity_terminal": cum_terminal,
        "cumulative_deployable_capacity_series": cum_series,
        "waterfall_by_year": {
            str(y.fiscal_year): f.capital_allocation_waterfall(y) for y in years
        },
        "no_double_counting": {
            str(y.fiscal_year): f.verify_no_double_counting(y) for y in years
        },
        "capacity_taxonomy_by_year": {
            str(cy.fiscal_year): dataclasses.asdict(cy) for cy in capacity_years
        },
        "capacity_horizon_summary": dataclasses.asdict(capacity_summary),
    }

# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------
val_assumptions = v.build_valuation_assumptions()
val_assumptions_by_metric = v.valuation_assumptions_by_metric(val_assumptions)
dcf_results = v.run_dcf_all_scenarios(forecasts, val_assumptions)

valuation_out = {
    "assumptions": [dataclasses.asdict(a) for a in val_assumptions],
    "wacc_pct": v.compute_wacc(val_assumptions_by_metric),
    "results": {},
}
for scenario, result in dcf_results.items():
    valuation_out["results"][scenario] = {
        **dataclasses.asdict(result),
        "bridge": v.valuation_bridge(result),
    }

SENSITIVITY_DELTAS = [-1.0, -0.5, 0.0, 0.5, 1.0]
wacc_grid = v.wacc_terminal_growth_sensitivity(
    forecasts["base"], SENSITIVITY_DELTAS, SENSITIVITY_DELTAS, val_assumptions
)
margin_growth_grid = v.operating_margin_revenue_growth_sensitivity(
    "base", [-0.5, -0.25, 0.0, 0.25, 0.5], SENSITIVITY_DELTAS, assumptions
)
valuation_out["wacc_terminal_growth_sensitivity"] = wacc_grid
valuation_out["operating_margin_revenue_growth_sensitivity"] = margin_growth_grid

# ---------------------------------------------------------------------------
# Validation totals
# ---------------------------------------------------------------------------
lineage = {s: f.build_lineage(years, assumptions) for s, years in forecasts.items()}
forecast_checks = f.validate_all(forecasts, assumptions, lineage)
valuation_checks = v.run_all_valuation_checks(forecasts, dcf_results)

capacity_taxonomies_all = ct.build_capacity_taxonomy_all_scenarios(forecasts)
capacity_summaries_all = ct.build_capacity_horizon_summaries(forecasts, capacity_taxonomies_all)
capacity_checks = ct.validate_capacity_taxonomy_all(forecasts, capacity_taxonomies_all, capacity_summaries_all)


def _status_counts(results):
    counts = {"PASS": 0, "FAIL": 0, "WARNING": 0}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    return counts


validation_out = {
    "forecast": {"total": len(forecast_checks), **_status_counts(forecast_checks)},
    "valuation": {"total": len(valuation_checks), **_status_counts(valuation_checks)},
    "capacity_taxonomy": {"total": len(capacity_checks), **_status_counts(capacity_checks)},
}

# ---------------------------------------------------------------------------
# Assemble and write
# ---------------------------------------------------------------------------
payload = {
    "information_cutoff": INFORMATION_CUTOFF,
    "generated_from": "data/curated/target_cash.db + target_cash.forecast/valuation (live computation)",
    "historical_years": f.HISTORICAL_YEARS,
    "forecast_years": f.FORECAST_YEARS,
    "historical": historical,
    "quarterly_cash": quarterly_cash,
    "filing_vintage": filing_vintage,
    "sources": sources,
    "scenarios": scenarios_out,
    "valuation": valuation_out,
    "validation": validation_out,
}

OUT_PATH.write_text(json.dumps(payload, indent=2, default=str))
print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size:,} bytes)")
print(f"Scenarios: {list(scenarios_out.keys())}")
print(f"Validation: forecast {validation_out['forecast']}, valuation {validation_out['valuation']}")
