"""Milestone 6: verification of the Power BI handoff package.

No .pbix exists to open, so this checks what CAN be verified
programmatically: the exported CSVs match the live database exactly,
the star schema has zero orphan foreign keys (every fact row's
scenario/fiscal-year/metric/filing/date key exists in its dimension
table), documented validation totals reproduce from the data, and every
required file in the package is present and well-formed.

Usage: .venv/bin/python scripts/verify_powerbi_handoff.py
"""
import json
import re
import sqlite3
import sys
import xml.dom.minidom as minidom
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "curated" / "target_cash.db"
PKG = REPO_ROOT / "deliverables" / "powerbi_handoff"
DATA_DIR = PKG / "data"

errors_found = []


def check(condition, message):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {message}")
    if not condition:
        errors_found.append(message)


conn = sqlite3.connect(str(DB_PATH))

# --- 1. Exported CSV row counts match the live database exactly ------------
DB_COUNT_QUERIES = {
    "fact_annual_historical.csv": "SELECT COUNT(*) FROM annual_facts",
    "fact_forecast.csv": "SELECT COUNT(*) FROM forecast_facts",
    "fact_investment_capacity.csv": "SELECT COUNT(*) FROM investment_capacity_results",
    "fact_capacity_taxonomy.csv": "SELECT COUNT(*) FROM capacity_taxonomy_results",
    "fact_capacity_horizon.csv": "SELECT COUNT(*) FROM capacity_horizon_results",
    "fact_valuation_results.csv": "SELECT COUNT(*) FROM valuation_results",
    "fact_valuation_ufcf.csv": "SELECT COUNT(*) FROM valuation_ufcf_facts",
    "fact_validation_forecast.csv": "SELECT COUNT(*) FROM forecast_validation_results",
    "fact_validation_valuation.csv": "SELECT COUNT(*) FROM valuation_validation_results",
    "fact_quarterly_cash.csv": "SELECT COUNT(*) FROM instant_facts",
    "dim_scenario.csv": "SELECT COUNT(*) FROM forecast_scenarios",
    "dim_filing.csv": "SELECT COUNT(*) FROM filings",
}
for fname, sql in DB_COUNT_QUERIES.items():
    db_count = conn.execute(sql).fetchone()[0]
    csv_count = len(pd.read_csv(DATA_DIR / fname))
    check(db_count == csv_count, f"{fname}: {csv_count} rows matches database ({db_count})")

# --- 2. Star-schema referential integrity: zero orphan fact keys -----------
dim_scenario = pd.read_csv(DATA_DIR / "dim_scenario.csv")
dim_fiscal_year = pd.read_csv(DATA_DIR / "dim_fiscal_year.csv")
dim_metric = pd.read_csv(DATA_DIR / "dim_metric.csv")
dim_filing = pd.read_csv(DATA_DIR / "dim_filing.csv")
dim_date_quarterly = pd.read_csv(DATA_DIR / "dim_date_quarterly.csv")

scenario_ids = set(dim_scenario["scenario_id"])
fiscal_years = set(dim_fiscal_year["fiscal_year"])
metric_keys = set(dim_metric["metric_key"])
accession_numbers = set(dim_filing["accession_number"])
quarterly_dates = set(dim_date_quarterly["as_of_date"])

fact_forecast = pd.read_csv(DATA_DIR / "fact_forecast.csv")
check(
    set(fact_forecast["scenario_id"]).issubset(scenario_ids),
    "fact_forecast: every scenario_id exists in dim_scenario (zero orphans)",
)
check(
    set(fact_forecast["fiscal_year"]).issubset(fiscal_years),
    "fact_forecast: every fiscal_year exists in dim_fiscal_year (zero orphans)",
)
check(
    set(fact_forecast["metric"]).issubset(metric_keys),
    "fact_forecast: every metric exists in dim_metric (zero orphans)",
)

fact_annual = pd.read_csv(DATA_DIR / "fact_annual_historical.csv")
check(
    set(fact_annual["fiscal_year"]).issubset(fiscal_years),
    "fact_annual_historical: every fiscal_year exists in dim_fiscal_year (zero orphans)",
)
check(
    set(fact_annual["metric"]).issubset(metric_keys),
    "fact_annual_historical: every metric exists in dim_metric (zero orphans)",
)
check(
    set(fact_annual["accession_number"].dropna()).issubset(accession_numbers),
    "fact_annual_historical: every accession_number exists in dim_filing (zero orphans)",
)

fact_ic = pd.read_csv(DATA_DIR / "fact_investment_capacity.csv")
check(
    set(fact_ic["scenario_id"]).issubset(scenario_ids)
    and set(fact_ic["fiscal_year"]).issubset(fiscal_years),
    "fact_investment_capacity: every scenario_id/fiscal_year exists in dimensions",
)

fact_captax = pd.read_csv(DATA_DIR / "fact_capacity_taxonomy.csv")
check(
    set(fact_captax["scenario_id"]).issubset(scenario_ids)
    and set(fact_captax["fiscal_year"]).issubset(fiscal_years),
    "fact_capacity_taxonomy: every scenario_id/fiscal_year exists in dimensions",
)
fact_caphrz = pd.read_csv(DATA_DIR / "fact_capacity_horizon.csv")
check(
    set(fact_caphrz["scenario_id"]).issubset(scenario_ids),
    "fact_capacity_horizon: every scenario_id exists in dim_scenario",
)

fact_val = pd.read_csv(DATA_DIR / "fact_valuation_results.csv")
check(
    set(fact_val["scenario_id"]).issubset(scenario_ids),
    "fact_valuation_results: every scenario_id exists in dim_scenario",
)

fact_ufcf = pd.read_csv(DATA_DIR / "fact_valuation_ufcf.csv")
check(
    set(fact_ufcf["scenario_id"]).issubset(scenario_ids)
    and set(fact_ufcf["fiscal_year"]).issubset(fiscal_years),
    "fact_valuation_ufcf: every scenario_id/fiscal_year exists in dimensions",
)

fact_qc = pd.read_csv(DATA_DIR / "fact_quarterly_cash.csv")
check(
    set(fact_qc["as_of_date"]).issubset(quarterly_dates),
    "fact_quarterly_cash: every as_of_date exists in dim_date_quarterly",
)
check(
    set(fact_qc["accession_number"].dropna()).issubset(accession_numbers),
    "fact_quarterly_cash: every accession_number exists in dim_filing",
)

fact_fv = pd.read_csv(DATA_DIR / "fact_filing_vintage_comparison.csv")
check(
    set(fact_fv["fiscal_year"]).issubset(fiscal_years)
    and set(fact_fv["metric"]).issubset(metric_keys),
    "fact_filing_vintage_comparison: every fiscal_year/metric exists in dimensions",
)

# validation fact tables: scenario_id may legitimately be null (scenario-
# invariant checks); every non-null value must still exist in dim_scenario.
fact_vf = pd.read_csv(DATA_DIR / "fact_validation_forecast.csv")
check(
    set(fact_vf["scenario_id"].dropna()).issubset(scenario_ids),
    "fact_validation_forecast: every non-null scenario_id exists in dim_scenario",
)
fact_vv = pd.read_csv(DATA_DIR / "fact_validation_valuation.csv")
check(
    set(fact_vv["scenario_id"].dropna()).issubset(scenario_ids),
    "fact_validation_valuation: every non-null scenario_id exists in dim_scenario",
)

# --- 3. Documented validation totals reproduce from the data ---------------
check(
    (fact_vf["status"] == "PASS").sum() == 229 and len(fact_vf) == 229,
    "Forecast validation: 229/229 PASS reproduces from fact_validation_forecast.csv",
)
check(
    (fact_vv["status"] == "PASS").sum() == 28 and len(fact_vv) == 28,
    "Valuation validation: 28/28 PASS reproduces from fact_validation_valuation.csv",
)

fy2025_hist = fact_annual[
    (fact_annual["fiscal_year"] == 2025) & (fact_annual["analytical_view"] == "latest_restated")
]


def hist_val(metric):
    row = fy2025_hist[fy2025_hist["metric"] == metric]
    return float(row["value_normalized"].iloc[0])


check(abs(hist_val("operating_cash_flow") - 6562.0) < 0.01, "FY2025 CFO = $6,562M reproduces from the export")
check(abs(hist_val("capital_expenditure") - 3727.0) < 0.01, "FY2025 CapEx = $3,727M reproduces from the export")
check(abs(hist_val("investing_cash_flow") - (-3649.0)) < 0.01, "FY2025 CFI = $(3,649)M reproduces from the export")
check(abs(hist_val("free_cash_flow") - 2835.0) < 0.01, "FY2025 FCF = $2,835M reproduces from the export")
check(
    abs(hist_val("capital_expenditure") - abs(hist_val("investing_cash_flow"))) > 1.0,
    "CapEx is NOT equal to |CFI| in the export -- the two are correctly distinct measures",
)

# --- 3b. Milestone 9 correction: capacity taxonomy reconciles exactly ------
check(len(fact_captax) == 15, f"fact_capacity_taxonomy has 15 rows (found {len(fact_captax)})")
check(len(fact_caphrz) == 3, f"fact_capacity_horizon has 3 rows (found {len(fact_caphrz)})")

for _, row in fact_captax.iterrows():
    lhs = row["self_funded_gross_capacity"] + row["debt_funded_incremental_capacity"]
    check(
        abs(lhs - row["total_gross_funding_capacity"]) < 0.1,
        f"{row['scenario_id']} FY{row['fiscal_year']}: self-funded + debt-funded == total gross funding capacity",
    )
    deployment = (row["share_repurchases"] + row["strategic_investment"]
                  + row["voluntary_debt_reduction"] + row["other_discretionary_uses"])
    check(
        abs(deployment - row["total_discretionary_deployment"]) < 0.1,
        f"{row['scenario_id']} FY{row['fiscal_year']}: 4 discretionary components sum to total_discretionary_deployment",
    )
    check(row["remaining_deployable_headroom"] >= 0, f"{row['scenario_id']} FY{row['fiscal_year']}: headroom is non-negative")
    check(
        abs(row["remaining_deployable_headroom"] - row["ending_excess_liquidity"]) < 0.1,
        f"{row['scenario_id']} FY{row['fiscal_year']}: remaining headroom equals its independent ending-excess-liquidity cross-check",
    )

for _, row in fact_caphrz.iterrows():
    rhs = row["cumulative_discretionary_deployment"] + row["terminal_remaining_headroom"] + row["ending_reserve_movement"]
    check(
        abs(row["total_horizon_capacity_accessible"] - rhs) < 0.5,
        f"{row['scenario_id']}: total horizon capacity accessible reconciles exactly to "
        "deployment + terminal headroom + ending reserve movement",
    )

# Legacy vs. corrected: Upside's corrected total horizon capacity must trail
# Base's by a MUCH smaller margin than the deprecated cumulative measure
# implied -- proving the correction materially changes the comparative picture,
# not just relabels it.
base_legacy = fact_ic[fact_ic["scenario_id"] == "base"]["cumulative_deployable_capacity"].dropna().iloc[-1]
upside_legacy = fact_ic[fact_ic["scenario_id"] == "upside"]["cumulative_deployable_capacity"].dropna().iloc[-1]
legacy_gap_pct = (base_legacy - upside_legacy) / base_legacy
base_corrected = fact_caphrz[fact_caphrz["scenario_id"] == "base"]["total_horizon_capacity_accessible"].iloc[0]
upside_corrected = fact_caphrz[fact_caphrz["scenario_id"] == "upside"]["total_horizon_capacity_accessible"].iloc[0]
corrected_gap_pct = (base_corrected - upside_corrected) / base_corrected
check(
    corrected_gap_pct < legacy_gap_pct - 0.1,
    f"Corrected Base-vs-Upside horizon-capacity gap ({corrected_gap_pct:.1%}) is materially smaller than "
    f"the deprecated legacy gap ({legacy_gap_pct:.1%})",
)

# --- 3c. No bare, unqualified "deployable capacity" label in DAX/dictionary -
dax_text = (PKG / "dax_measures.md").read_text()
dict_text = (PKG / "data_dictionary.md").read_text()
bare_legacy_mentions = [
    m for m in re.finditer(r"(?i)deployable capacity", dax_text)
    if not any(
        q in dax_text[max(0, m.start() - 80):m.end() + 80].lower()
        for q in ("legacy", "deprecated")
    )
]
check(
    len(bare_legacy_mentions) == 0,
    f"dax_measures.md: no bare 'deployable capacity' mention lacking a legacy/deprecated qualifier "
    f"nearby (found {len(bare_legacy_mentions)})",
)
check(
    "fact_capacity_taxonomy" in dict_text and "DEPRECATED" in dict_text,
    "data_dictionary.md: documents both the new fact_capacity_taxonomy table and the legacy deprecation",
)

# --- 4. Required package files are all present and well-formed -------------
REQUIRED_FILES = [
    "README.md", "data_dictionary.md", "relationship_map.md", "dax_measures.md",
    "theme.json", "refresh_instructions.md", "validation_totals.md",
]
for fname in REQUIRED_FILES:
    check((PKG / fname).is_file(), f"Required file present: {fname}")

try:
    json.loads((PKG / "theme.json").read_text())
    check(True, "theme.json is valid JSON")
except Exception as exc:  # noqa: BLE001
    check(False, f"theme.json is valid JSON ({exc})")

EXPECTED_PAGES = [
    "page_01_executive_overview.md",
    "page_02_historical_financial_trends.md",
    "page_03_filing_vintage_comparison.md",
    "page_04_quarterly_cash_proof.md",
    "page_05_scenario_forecast_explorer.md",
    "page_06_cashflow_bridge_investment_capacity.md",
    "page_07_capital_allocation_waterfall.md",
    "page_08_dcf_valuation_sensitivities.md",
]
for fname in EXPECTED_PAGES:
    check((PKG / "pages" / fname).is_file(), f"Page spec present: pages/{fname}")

wireframes = sorted((PKG / "wireframes").glob("*.svg"))
check(len(wireframes) == 8, f"Exactly 8 wireframe SVGs present (found {len(wireframes)})")
for svg_path in wireframes:
    try:
        minidom.parse(str(svg_path))
        ok = True
    except Exception:  # noqa: BLE001
        ok = False
    check(ok, f"Wireframe is well-formed XML/SVG: {svg_path.name}")

# --- 5. No .pbix falsely present or claimed --------------------------------
pbix_files = list(PKG.rglob("*.pbix"))
check(len(pbix_files) == 0, "No .pbix file present in the package (none is claimed to exist)")

print()
if errors_found:
    print(f"VERIFICATION FAILED: {len(errors_found)} issue(s) found.")
    sys.exit(1)
else:
    print("ALL VERIFICATION CHECKS PASSED.")
