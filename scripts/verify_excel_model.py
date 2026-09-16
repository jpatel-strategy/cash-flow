"""Milestone 5: programmatic verification of the Excel executive model.

Opens the workbook with a real formula-evaluation engine (the `formulas`
package -- this environment's sandboxed LibreOffice cannot load ANY xlsx
file, confirmed with a trivial one-cell test file, so `formulas` is the
available substitute for "open, recalculate, inspect" here), recalculates
every formula, and checks:

1. No formula error values anywhere (#REF!, #VALUE!, #DIV/0!, etc.)
2. The live Scenario Forecast / Cash-Flow Bridge / Investment Capacity /
   Capital Allocation / DCF Valuation sheets reproduce target_cash.forecast
   and target_cash.valuation's own Python-computed numbers exactly, for
   whichever scenario the selector cell holds at save time (Base).
3. The Capital Allocation sheet's no-double-counting proof row reads "OK"
   for every year.
4. (Milestone 9 correction) The corrected capacity taxonomy on the
   Investment Capacity sheet reproduces target_cash.capacity_taxonomy's
   own Python-computed numbers exactly, and the legacy, now-deprecated
   "deployable_capacity" headline no longer appears anywhere in the
   Executive Summary's headline rows.

Usage: .venv/bin/python scripts/verify_excel_model.py

This checks that the formula OUTPUTS reconcile to Python -- it does not,
and cannot, substitute for opening the workbook in actual Microsoft
Excel and visually inspecting it (LibreOffice cannot load any xlsx file
in this build environment; see the module docstring history in
docs/decisions.md). The correct claim is: "formula outputs
programmatically reconciled to the Python engine," never "verified in
Excel."
"""
import os
import sys

sys.path.insert(0, "src")

import formulas
import openpyxl

from target_cash import forecast as f
from target_cash import valuation as v
from target_cash import capacity_taxonomy as ct

PATH = "deliverables/Target_Cash_Flow_Investment_Capacity_Model.xlsx"
SHEET_PREFIX = "'[Target_Cash_Flow_Investment_Capacity_Model.xlsx]"

errors_found = []


def check(condition, message):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {message}")
    if not condition:
        errors_found.append(message)


print(f"Loading and recalculating {PATH} ...")
xl_model = formulas.ExcelModel().loads(PATH).finish()
solution = xl_model.calculate()
print(f"Recalculated {len(solution)} cells.\n")


def cell(sheet, ref):
    return solution[f"{SHEET_PREFIX}{sheet.upper()}'!{ref}"].value[0][0]


# --- 1. No formula errors anywhere ------------------------------------------
ERROR_TOKENS = ("#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "#NULL!", "#NUM!", "#N/A")
error_cells = []
for key, res in solution.items():
    try:
        val = res.value[0][0]
    except Exception:
        continue
    if isinstance(val, str) and any(tok in val for tok in ERROR_TOKENS):
        error_cells.append((key, val))
check(len(error_cells) == 0, f"No formula errors anywhere in the workbook (found {len(error_cells)})")
for k, v_ in error_cells[:20]:
    print(f"   ERROR CELL: {k} = {v_}")

# --- 2. Live sheets reproduce Python exactly (Base scenario, as saved) ------
assumptions = f.build_assumptions()
forecasts = f.run_all_scenarios(assumptions)
years = forecasts["base"]
FY_COLS = ["D", "E", "F", "G", "H"]

wb_ro = openpyxl.load_workbook(PATH)
ws_fc = wb_ro["Scenario Forecast"]
ws_cf = wb_ro["Cash-Flow Bridge"]
ws_ic = wb_ro["Investment Capacity"]
ws_ca = wb_ro["Capital Allocation"]
ws_dcf = wb_ro["DCF Valuation"]


def row_of(ws, label):
    for row in ws.iter_rows(min_col=1, max_col=1):
        for c in row:
            if c.value == label:
                return c.row
    raise KeyError(label)


rev_row = row_of(ws_fc, "Revenue")
ni_row = row_of(ws_fc, "Net Income")
eps_row = row_of(ws_fc, "Diluted EPS ($)")
cfo_row = row_of(ws_cf, "Cash Flow from Operations (CFO)")
fcf_row = row_of(ws_cf, "Free Cash Flow (CFO - CapEx)")
end_cash_row = row_of(ws_cf, "Ending Cash")
dep_row = row_of(ws_ic, "Legacy Gross Pre-Discretionary Ceiling (DEPRECATED -- see note below; not an executive KPI)")
wf_end_row = row_of(ws_ca, "8. = Ending Cash")
proof_row = row_of(ws_ca, "Ending Cash (Sheet 8) matches Step 8 above?")

# v2 finance-semantics correction: corrected capacity taxonomy row lookups.
opening_liquidity_row = row_of(ws_ic, "Opening Excess Liquidity (STOCK, = MAX(0, beg. cash - buffer)) -- never labeled 'generated'")
gross_proceeds_row = row_of(ws_ic, "  Gross Debt Proceeds (supporting, transparent)")
gross_repayments_row = row_of(ws_ic, "  Gross Debt Repayments (supporting, transparent)")
net_debt_service_row = row_of(ws_ic, "Net Mandatory Debt Service (= MAX(0, gross repayments - gross proceeds))")
self_funded_row = row_of(ws_ic, "C. Self-Funded Capacity Generated (FLOW, excludes opening liquidity)")
debt_funded_row = row_of(ws_ic, "D. Debt-Funded Incremental Capacity (= MAX(0, proceeds - repayments); never gross issuance)")
total_funding_row = row_of(ws_ic, "E. TOTAL GROSS FUNDING CAPACITY (Opening Liquidity + C + D)")
total_deployment_row = row_of(ws_ic, "F. TOTAL DISCRETIONARY DEPLOYMENT")
forward_reserve_row = row_of(ws_ic, "Forward Debt-Repayment Reserve (next year's net debt service; FY2030 is a documented FY2031 proxy)")
headroom_row = row_of(ws_ic, "G. REMAINING DEPLOYABLE HEADROOM (stock, = MAX(0, E - F - forward reserve))")
ending_excess_row = row_of(ws_ic, "Ending Excess Liquidity (independent cross-check: = G + forward reserve)")

capacity_taxonomies = ct.build_capacity_taxonomy_all_scenarios(forecasts)
capacity_years = capacity_taxonomies["base"]

all_match = True
for i, (col, y, ty) in enumerate(zip(FY_COLS, years, capacity_years)):
    excel_rev = cell("SCENARIO FORECAST", f"{col}{rev_row}")
    excel_ni = cell("SCENARIO FORECAST", f"{col}{ni_row}")
    excel_eps = cell("SCENARIO FORECAST", f"{col}{eps_row}")
    excel_cfo = cell("CASH-FLOW BRIDGE", f"{col}{cfo_row}")
    excel_fcf = cell("CASH-FLOW BRIDGE", f"{col}{fcf_row}")
    excel_end_cash = cell("CASH-FLOW BRIDGE", f"{col}{end_cash_row}")
    excel_dep = cell("INVESTMENT CAPACITY", f"{col}{dep_row}")
    excel_wf_end = cell("CAPITAL ALLOCATION", f"{col}{wf_end_row}")
    proof_val = cell("CAPITAL ALLOCATION", f"{col}{proof_row}")

    matches = (
        abs(excel_rev - y.revenue) < 0.01 and abs(excel_ni - y.net_income) < 0.01
        and abs(excel_eps - y.diluted_eps) < 0.001 and abs(excel_cfo - y.operating_cash_flow) < 0.01
        and abs(excel_fcf - y.free_cash_flow) < 0.01 and abs(excel_end_cash - y.ending_cash) < 0.01
        and abs(excel_dep - y.deployable_capacity) < 0.01 and abs(excel_wf_end - y.ending_cash) < 0.01
        and proof_val == "OK"
    )
    all_match &= matches
    check(matches, f"FY{y.fiscal_year} Base scenario: Excel matches Python exactly "
                    f"(revenue, net income, EPS, CFO, FCF, ending cash, legacy deployable capacity, waterfall proof)")

    excel_opening_liquidity = cell("INVESTMENT CAPACITY", f"{col}{opening_liquidity_row}")
    excel_gross_proceeds = cell("INVESTMENT CAPACITY", f"{col}{gross_proceeds_row}")
    excel_gross_repayments = cell("INVESTMENT CAPACITY", f"{col}{gross_repayments_row}")
    excel_net_debt_service = cell("INVESTMENT CAPACITY", f"{col}{net_debt_service_row}")
    excel_self_funded = cell("INVESTMENT CAPACITY", f"{col}{self_funded_row}")
    excel_debt_funded = cell("INVESTMENT CAPACITY", f"{col}{debt_funded_row}")
    excel_total_funding = cell("INVESTMENT CAPACITY", f"{col}{total_funding_row}")
    excel_total_deployment = cell("INVESTMENT CAPACITY", f"{col}{total_deployment_row}")
    excel_forward_reserve = cell("INVESTMENT CAPACITY", f"{col}{forward_reserve_row}")
    excel_headroom = cell("INVESTMENT CAPACITY", f"{col}{headroom_row}")
    excel_ending_excess = cell("INVESTMENT CAPACITY", f"{col}{ending_excess_row}")

    capacity_matches = (
        abs(excel_opening_liquidity - ty.opening_excess_liquidity) < 0.01
        and abs(excel_gross_proceeds - ty.gross_debt_proceeds) < 0.01
        and abs(excel_gross_repayments - ty.gross_debt_repayments) < 0.01
        and abs(excel_net_debt_service - ty.net_mandatory_debt_service) < 0.01
        and abs(excel_self_funded - ty.self_funded_capacity_generated) < 0.01
        and abs(excel_debt_funded - ty.debt_funded_incremental_capacity) < 0.01
        and abs(excel_total_funding - ty.total_gross_funding_capacity) < 0.01
        and abs(excel_total_deployment - ty.total_discretionary_deployment) < 0.01
        and abs(excel_forward_reserve - ty.forward_debt_repayment_reserve) < 0.01
        and abs(excel_headroom - ty.remaining_deployable_headroom) < 0.01
        and abs(excel_ending_excess - ty.ending_excess_liquidity) < 0.01
        and abs(excel_headroom - (excel_ending_excess - excel_forward_reserve)) < 0.01
    )
    check(capacity_matches, f"FY{y.fiscal_year} Base scenario: corrected (v2) capacity taxonomy "
                             "(opening liquidity, gross proceeds/repayments, net debt service, "
                             "self-funded generated, debt-funded, total funding, discretionary deployment, "
                             "forward reserve, remaining headroom) matches target_cash.capacity_taxonomy "
                             "exactly, and headroom equals ending-excess-liquidity minus the forward reserve")

    # v2 finance-semantics correction: gross debt issuance is never labeled capacity when
    # simultaneously repaid -- prove the netting is reflected in Excel, not just Python
    # (net debt service and debt-funded capacity are never both positive at once).
    check(
        min(excel_net_debt_service, excel_debt_funded) < 1e-6,
        f"FY{y.fiscal_year} Base scenario: net debt service and debt-funded capacity are never both positive in Excel",
    )

# --- 3. DCF sheet matches Python -------------------------------------------
val_assumptions = v.build_valuation_assumptions()
dcf_result = v.run_dcf(years, val_assumptions)
wacc_row = row_of(ws_dcf, "WACC")
ev_row = row_of(ws_dcf, "Enterprise Value")
equity_row = row_of(ws_dcf, "Equity Value")
per_share_row = row_of(ws_dcf, "IMPLIED VALUE PER SHARE")

excel_wacc = cell("DCF VALUATION", f"B{wacc_row}")
excel_ev = cell("DCF VALUATION", f"B{ev_row}")
excel_equity = cell("DCF VALUATION", f"B{equity_row}")
excel_per_share = cell("DCF VALUATION", f"B{per_share_row}")

check(abs(excel_wacc * 100 - dcf_result.wacc_pct) < 0.001, "DCF: WACC matches Python")
check(abs(excel_ev - dcf_result.enterprise_value) < 0.1, "DCF: Enterprise Value matches Python")
check(abs(excel_equity - dcf_result.equity_value) < 0.1, "DCF: Equity Value matches Python")
check(abs(excel_per_share - dcf_result.implied_value_per_share) < 0.01, "DCF: Implied Value/Share matches Python")

# --- 4. Structural checks ---------------------------------------------------
EXPECTED_SHEETS = [
    "Cover & Instructions", "Executive Summary", "Historical Financials", "Filing-Vintage Comparison",
    "Quarterly Cash Proof", "Forecast Assumptions", "Scenario Forecast", "Cash-Flow Bridge",
    "Investment Capacity", "Capital Allocation", "DCF Valuation", "Sensitivities", "Source & Lineage",
    "Validation Summary", "Limitations",
]
check(wb_ro.sheetnames == EXPECTED_SHEETS, f"All 15 sheets present in the required order (got {wb_ro.sheetnames})")

ws_asm = wb_ro["Forecast Assumptions"]
dv_found = any(dv.type == "list" for dv in ws_asm.data_validations.dataValidation)
check(dv_found, "Scenario selector dropdown (data validation) present on Forecast Assumptions!C2")

for name in ["Scenario Forecast", "Cash-Flow Bridge", "Investment Capacity", "Forecast Assumptions"]:
    ws = wb_ro[name]
    check(ws.freeze_panes is not None, f"{name}: frozen panes set")

# --- Milestone 9 correction: legacy KPI removed from Executive Summary headline ---
ws_es = wb_ro["Executive Summary"]
es_labels = [c.value for row in ws_es.iter_rows(min_col=1, max_col=1) for c in row if c.value]
check(
    not any("Deployable Capacity" in str(v) and "Legacy" not in str(v) and "Remaining" not in str(v) for v in es_labels),
    "Executive Summary: no bare, unqualified 'Deployable Capacity' headline label remains",
)
for required_label in ["Opening Excess Liquidity", "Self-Funded Capacity Generated", "Debt-Funded Capacity",
                        "Discretionary Deployment", "Remaining Deployable Headroom"]:
    check(
        any(required_label in str(v) for v in es_labels),
        f"Executive Summary: corrected headline label present: {required_label!r}",
    )

# --- Final independent-audit closeout: NET vs. GROSS horizon capacity ------
capacity_summaries_all = ct.build_capacity_horizon_summaries(
    forecasts, ct.build_capacity_taxonomy_all_scenarios(forecasts)
)


def find_cell(ws, value):
    for row in ws.iter_rows():
        for c in row:
            if c.value == value:
                return c.row, c.column
    raise KeyError(value)


gross_header_row, gross_col = find_cell(
    ws_ic, "Gross Horizon Funding, Before Reserve Adjustments (C+A+B) -- NOT net accessible capacity"
)
net_header_row, net_col = find_cell(ws_ic, "NET Horizon Deployable Capacity (Gross - Reserve Mvmt - Terminal Forward Reserve)")
scenario_col = 1
check(gross_header_row == net_header_row, "Investment Capacity: gross and net horizon-capacity headers share one row")

for offset, scenario in enumerate(f.SCENARIOS, start=1):
    row_num = gross_header_row + offset
    excel_scenario = ws_ic.cell(row=row_num, column=scenario_col).value
    excel_gross = ws_ic.cell(row=row_num, column=gross_col).value
    excel_net = ws_ic.cell(row=row_num, column=net_col).value
    summary = capacity_summaries_all[scenario]
    values_match = (
        str(excel_scenario).lower() == scenario
        and abs(excel_gross - summary.gross_horizon_funding_before_reserve_adjustments) < 0.1
        and abs(excel_net - summary.net_horizon_deployable_capacity) < 0.1
    )
    has_reserves = bool(summary.ending_reserve_movement) or bool(summary.terminal_forward_debt_repayment_reserve)
    net_differs_from_gross = abs(excel_net - excel_gross) > 0.1
    check(
        values_match and (net_differs_from_gross if has_reserves else True),
        f"{scenario}: Excel gross/net horizon-capacity figures match Python exactly, and net != gross whenever reserves are nonzero",
    )
    check(
        abs(excel_net - (summary.cumulative_discretionary_deployment + summary.terminal_remaining_headroom)) < 0.1,
        f"{scenario}: Excel NET horizon deployable capacity == cumulative deployment + terminal headroom",
    )

# --- 5. Scenario selector genuinely recalculates (Upside/Downside) --------
import tempfile

for scenario_label, scenario_key in [("Upside", "upside"), ("Downside", "downside")]:
    wb_switch = openpyxl.load_workbook(PATH)
    wb_switch["Forecast Assumptions"]["C2"] = scenario_label
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = tmp.name
    wb_switch.save(tmp_path)
    tmp_name = tmp_path.split("/")[-1]
    xl_model_2 = formulas.ExcelModel().loads(tmp_path).finish()
    solution_2 = xl_model_2.calculate()
    excel_rev_2030 = solution_2[f"'[{tmp_name}]SCENARIO FORECAST'!H{rev_row}"].value[0][0]
    excel_eps_2030 = solution_2[f"'[{tmp_name}]SCENARIO FORECAST'!H{eps_row}"].value[0][0]
    py_years = forecasts[scenario_key]
    check(
        abs(excel_rev_2030 - py_years[-1].revenue) < 0.01 and abs(excel_eps_2030 - py_years[-1].diluted_eps) < 0.001,
        f"Scenario selector -> {scenario_label}: FY2030 revenue and EPS recalculate to match Python exactly",
    )
    os.remove(tmp_path)

print()
if errors_found:
    print(f"VERIFICATION FAILED: {len(errors_found)} issue(s) found.")
    sys.exit(1)
else:
    print("ALL VERIFICATION CHECKS PASSED.")
