"""Milestone 5: builds the Excel executive model as a real, openpyxl-written
workbook with genuine cross-sheet formulas for the core forecast/DCF chain
(Forecast Assumptions -> Scenario Forecast -> Cash-Flow Bridge ->
Investment Capacity -> Capital Allocation -> DCF Valuation), driven by one
scenario-selector dropdown cell, plus reference/appendix sheets for
historical data, sensitivities, lineage, validation, and limitations.

Design choice, stated once here: rather than building three fully redundant
live-formula blocks (one per scenario) in every sheet, the "Scenario
Forecast" family of sheets computes ONE live, fully-linked column set for
whichever scenario is selected via the dropdown on the Forecast Assumptions
sheet -- standard professional Excel-modeling practice. Static, clearly-
labeled "All-Scenario Comparison" tables (Python-computed, from the same
target_cash.forecast/valuation engine) sit alongside for side-by-side
reference. This keeps the live formula chain traceable and verifiable
(every live cell can be inspected back to its inputs) without a 3x
duplication of formulas that would not add analytical value.

Usage: .venv/bin/python scripts/build_excel_model.py
"""
import sys
from datetime import date

sys.path.insert(0, "src")

import openpyxl
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from target_cash import forecast as f
from target_cash import valuation as v
from target_cash import capacity_taxonomy as ct

OUT_PATH = "deliverables/Target_Cash_Flow_Investment_Capacity_Model.xlsx"

# --- Styles ------------------------------------------------------------

NAVY = "1F3864"
LIGHT_BLUE = "D9E2F3"
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")     # yellow -- editable input cells
FORMULA_FILL = PatternFill("solid", fgColor="FFFFFF")   # white -- computed
HEADER_FILL = PatternFill("solid", fgColor=NAVY)
SUBHEADER_FILL = PatternFill("solid", fgColor=LIGHT_BLUE)
TITLE_FONT = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
SUBHEADER_FONT = Font(name="Calibri", size=10, bold=True, color="1F3864")
LABEL_FONT = Font(name="Calibri", size=10, bold=False)
BOLD_FONT = Font(name="Calibri", size=10, bold=True)
INPUT_FONT = Font(name="Calibri", size=10, color="7F6000")
NOTE_FONT = Font(name="Calibri", size=9, italic=True, color="808080")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

NUM_FMT = "#,##0.0"
PCT_FMT = "0.00%"
USD_FMT = '#,##0.0;(#,##0.0)'
EPS_FMT = "0.00"


def style_title(ws, cell_range, text):
    ws.merge_cells(cell_range)
    top_left = cell_range.split(":")[0]
    ws[top_left] = text
    ws[top_left].font = TITLE_FONT
    ws[top_left].fill = HEADER_FILL
    ws[top_left].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    row = int("".join(ch for ch in top_left if ch.isdigit()))
    ws.row_dimensions[row].height = 28


def style_header_row(ws, row, first_col, last_col):
    for c in range(first_col, last_col + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER


def style_subheader(ws, row, first_col, last_col):
    for c in range(first_col, last_col + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = SUBHEADER_FILL
        cell.font = SUBHEADER_FONT
        cell.border = BORDER


def set_col_widths(ws, widths: dict):
    for col, width in widths.items():
        ws.column_dimensions[col].width = width


def write_row(ws, row, col, values, number_format=None, bold=False, input_cell=False):
    for i, val in enumerate(values):
        cell = ws.cell(row=row, column=col + i, value=val)
        if number_format:
            cell.number_format = number_format
        cell.font = INPUT_FONT if input_cell else (BOLD_FONT if bold else LABEL_FONT)
        if input_cell:
            cell.fill = INPUT_FILL
        cell.border = BORDER
    return row


wb = openpyxl.Workbook()
wb.remove(wb.active)

assumptions = f.build_assumptions()
by_scenario = f.assumptions_by_scenario(assumptions)
forecasts = f.run_all_scenarios(assumptions)
lineage = {s: f.build_lineage(y, assumptions) for s, y in forecasts.items()}
validation_results = f.validate_all(forecasts, assumptions, lineage)
sensitivity = f.build_sensitivity_tables(assumptions=assumptions)
two_var = f.two_variable_sensitivity("revenue_growth_pct", [-1.0, -0.5, 0.0, 0.5, 1.0],
                                      "gross_margin_pct", [-0.5, -0.25, 0.0, 0.25, 0.5], assumptions=assumptions)
val_assumptions = v.build_valuation_assumptions()
val_m = v.valuation_assumptions_by_metric(val_assumptions)
dcf_results = v.run_dcf_all_scenarios(forecasts, val_assumptions)
capacity_taxonomies = ct.build_capacity_taxonomy_all_scenarios(forecasts)
capacity_summaries = ct.build_capacity_horizon_summaries(forecasts, capacity_taxonomies)
val_checks = v.run_all_valuation_checks(forecasts, dcf_results)
wacc_grid = v.wacc_terminal_growth_sensitivity(forecasts["base"], [-1.0, -0.5, 0.0, 0.5, 1.0],
                                                [-1.0, -0.5, 0.0, 0.5, 1.0], val_assumptions)
margin_growth_grid = v.operating_margin_revenue_growth_sensitivity("base", [-0.5, 0.0, 0.5], [-1.0, 0.0, 1.0])

print(f"Loaded: {len(assumptions)} assumptions, {len(validation_results)} forecast checks, "
      f"{len(val_checks)} valuation checks")

# ============================================================================
# Sheet 1: Cover & Instructions
# ============================================================================
ws = wb.create_sheet("Cover & Instructions")
set_col_widths(ws, {"A": 4, "B": 34, "C": 90})
style_title(ws, "A1:C1", "Target Corporation -- Cash Flow & Investment Capacity Decision Cockpit")
ws["B3"] = "Prepared"
ws["C3"] = date.today().isoformat()
ws["B4"] = "Information cutoff"
ws["C4"] = f"{f.FORECAST_INFORMATION_CUTOFF} (FY2025 10-K, accession {f.FORECAST_INFORMATION_CUTOFF_ACCESSION})"
ws["B5"] = "Scope"
ws["C5"] = "Independent, public-data model built entirely from SEC XBRL filings -- no analyst estimates, no information after the cutoff."
for r in (3, 4, 5):
    ws[f"B{r}"].font = BOLD_FONT
    ws[f"C{r}"].font = LABEL_FONT
    ws[f"C{r}"].alignment = Alignment(wrap_text=True)

ws["B7"] = "IMPORTANT DISCLAIMER"
ws["B7"].font = Font(bold=True, size=12, color="C00000")
ws.merge_cells("B8:C8")
ws["B8"] = ("This workbook is a scenario-based analytical model, NOT investment advice, NOT a price "
            "target, and NOT a prediction of Target's actual future results or stock price. DCF outputs "
            "(Sheet 11) use illustrative WACC/terminal-growth inputs -- see Sheet 15 (Limitations).")
ws["B8"].alignment = Alignment(wrap_text=True, vertical="top")
ws.row_dimensions[8].height = 48
ws["B8"].font = Font(italic=True, size=10)

ws["B10"] = "How to use this workbook"
ws["B10"].font = BOLD_FONT
instructions = [
    "1. Sheet 6 (Forecast Assumptions) has a Scenario Selector dropdown (cell C2) -- choose Base, "
    "Upside, or Downside.",
    "2. Sheets 7-11 (Scenario Forecast through DCF Valuation) recalculate LIVE from that selection -- "
    "every number is a real Excel formula traceable back to Sheet 6's input cells.",
    "3. Yellow-filled cells are editable inputs (assumptions). White cells are formulas -- do not "
    "overtype them, or traceability is lost.",
    "4. Sheets 3-5, 12-15 are reference/appendix data (historical facts, sensitivity dry-runs, "
    "source lineage, validation results, limitations) -- static, regenerated by the project's Python "
    "pipeline, not live Excel formulas.",
    "5. A static 'All-Scenario Comparison' table appears below the live forecast on Sheets 7 and 11 "
    "for side-by-side reference across all 3 scenarios at once.",
]
r = 11
for line in instructions:
    ws.merge_cells(f"B{r}:C{r}")
    ws[f"B{r}"] = line
    ws[f"B{r}"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[r].height = 28
    r += 1

ws["B" + str(r + 1)] = "Sheet index"
ws["B" + str(r + 1)].font = BOLD_FONT
sheet_index = [
    "1. Cover & Instructions", "2. Executive Summary", "3. Historical Financials",
    "4. Filing-Vintage Comparison", "5. Quarterly Cash Proof", "6. Forecast Assumptions",
    "7. Scenario Forecast", "8. Cash-Flow Bridge", "9. Investment Capacity", "10. Capital Allocation",
    "11. DCF Valuation", "12. Sensitivities", "13. Source & Lineage", "14. Validation Summary",
    "15. Limitations",
]
r += 2
for name in sheet_index:
    ws[f"B{r}"] = name
    ws[f"B{r}"].font = LABEL_FONT
    r += 1
ws.sheet_view.showGridLines = False


# ============================================================================
# Sheet 6: Forecast Assumptions (built before 2/7 since other sheets reference it)
# ============================================================================
ws_asm = wb.create_sheet("Forecast Assumptions")
set_col_widths(ws_asm, {"A": 40, "B": 24, "C": 10})
for col in "DEFGHIJKLMNOPQRST":
    ws_asm.column_dimensions[col].width = 11
style_title(ws_asm, "A1:T1", "Forecast Assumptions (FY2026-FY2030)")

ws_asm["A2"] = "Scenario Selector"
ws_asm["A2"].font = BOLD_FONT
ws_asm["C2"] = "Base"
ws_asm["C2"].fill = INPUT_FILL
ws_asm["C2"].font = Font(bold=True, size=12, color="7F6000")
ws_asm["C2"].border = BORDER
ws_asm["C2"].alignment = Alignment(horizontal="center")
dv = DataValidation(type="list", formula1='"Base,Upside,Downside"', allow_blank=False)
ws_asm.add_data_validation(dv)
dv.add(ws_asm["C2"])
ws_asm["D2"] = "<- choose Base / Upside / Downside; drives Sheets 7-11 live"
ws_asm["D2"].font = NOTE_FONT

header_row = 4
ws_asm.cell(row=header_row, column=1, value="Assumption")
ws_asm.cell(row=header_row, column=2, value="Area")
ws_asm.cell(row=header_row, column=3, value="Unit")
BASE_COLS = ["D", "E", "F", "G", "H"]
UPSIDE_COLS = ["J", "K", "L", "M", "N"]
DOWNSIDE_COLS = ["P", "Q", "R", "S", "T"]
for i, fy in enumerate(f.FORECAST_YEARS):
    ws_asm.cell(row=header_row, column=openpyxl.utils.column_index_from_string(BASE_COLS[i]), value=f"Base FY{fy}")
    ws_asm.cell(row=header_row, column=openpyxl.utils.column_index_from_string(UPSIDE_COLS[i]), value=f"Upside FY{fy}")
    ws_asm.cell(row=header_row, column=openpyxl.utils.column_index_from_string(DOWNSIDE_COLS[i]), value=f"Downside FY{fy}")
style_header_row(ws_asm, header_row, 1, 20)

ASSUMPTION_ROWS = [
    ("revenue_growth_pct", "Revenue", "Revenue growth %/yr", "percent"),
    ("gross_margin_pct", "Gross Profit", "Gross margin %", "percent"),
    ("sga_pct_of_revenue", "Operating Expenses", "SG&A % of revenue", "percent"),
    ("da_pct_of_revenue", "Operating Expenses", "D&A in opex, % of revenue", "percent"),
    ("effective_tax_rate_pct", "Income Tax", "Effective tax rate %", "percent"),
    ("net_other_income_musd", "Other Income", "Net other income ($M)", "usd"),
    ("diluted_share_change_pct", "Shares", "Diluted share count change %/yr", "percent"),
    ("interest_rate_pct", "Interest", "Interest rate on avg debt %", "percent"),
    ("capex_pct_of_revenue", "CapEx", "CapEx % of revenue", "percent"),
    ("da_cfo_addback_pct_of_revenue", "Cash Flow", "D&A CFO add-back % of revenue", "percent"),
    ("inventory_pct_of_revenue", "Working Capital", "Inventory % of revenue", "percent"),
    ("ap_pct_of_cogs", "Working Capital", "Accounts payable % of COGS", "percent"),
    ("other_operating_cf_musd", "Cash Flow", "Other operating cash adjustments ($M)", "usd"),
    ("dividend_per_share_growth_pct", "Financing", "Dividend per share growth %/yr", "percent"),
    ("buyback_payout_pct_of_post_dividend_fcf", "Financing", "Buyback payout % of post-dividend FCF", "percent"),
    ("debt_proceeds_musd", "Financing", "Debt proceeds ($M/yr)", "usd"),
    ("debt_repayments_musd", "Financing", "Debt repayments ($M/yr)", "usd"),
    ("finance_lease_liabilities_musd", "Balance Sheet", "Finance lease liabilities ($M)", "usd"),
    ("min_cash_buffer_pct_of_revenue", "Liquidity Policy", "Minimum cash buffer % of revenue", "percent"),
]

ASSUMPTION_CELL = {}  # (scenario, metric, fy) -> "D5" etc, filled below
ASSUMPTION_ROW = {}  # metric -> row number
row = header_row + 1
for metric, area, label, kind in ASSUMPTION_ROWS:
    ASSUMPTION_ROW[metric] = row
    ws_asm.cell(row=row, column=1, value=label).font = LABEL_FONT
    ws_asm.cell(row=row, column=2, value=area).font = LABEL_FONT
    unit_label = "%" if kind == "percent" else "$M"
    ws_asm.cell(row=row, column=3, value=unit_label).font = LABEL_FONT
    for scenario, cols in (("base", BASE_COLS), ("upside", UPSIDE_COLS), ("downside", DOWNSIDE_COLS)):
        for i, fy in enumerate(f.FORECAST_YEARS):
            val = f._lookup(by_scenario[scenario][metric], fy)
            display_val = val / 100 if kind == "percent" else val
            col_letter = cols[i]
            cell = ws_asm[f"{col_letter}{row}"]
            cell.value = display_val
            cell.number_format = PCT_FMT if kind == "percent" else USD_FMT
            cell.fill = INPUT_FILL
            cell.font = INPUT_FONT
            cell.border = BORDER
            ASSUMPTION_CELL[(scenario, metric, fy)] = f"{col_letter}{row}"
    row += 1

ws_asm.freeze_panes = "D5"
ws_asm.sheet_view.showGridLines = False
last_asm_row = row - 1
print(f"Forecast Assumptions sheet: {last_asm_row - header_row} metrics, cells mapped through row {last_asm_row}")

ASM = "'Forecast Assumptions'"
SELECTOR = f"{ASM}!$C$2"


def asm_pick(metric: str, fy_index: int) -> str:
    """Excel formula picking the currently-selected scenario's assumption
    value for `metric` at forecast-year index fy_index (0=FY2026)."""
    r = ASSUMPTION_ROW[metric]
    base_cell = f"{ASM}!{BASE_COLS[fy_index]}{r}"
    upside_cell = f"{ASM}!{UPSIDE_COLS[fy_index]}{r}"
    downside_cell = f"{ASM}!{DOWNSIDE_COLS[fy_index]}{r}"
    return f'=IF({SELECTOR}="Base",{base_cell},IF({SELECTOR}="Upside",{upside_cell},{downside_cell}))'


FY_COLS = ["D", "E", "F", "G", "H"]  # FY2026-FY2030 columns on every live-formula sheet


# ============================================================================
# Sheet 7: Scenario Forecast (LIVE formulas, driven by the selector)
# ============================================================================
ws_fc = wb.create_sheet("Scenario Forecast")
set_col_widths(ws_fc, {"A": 34, "B": 10})
for col in FY_COLS:
    ws_fc.column_dimensions[col].width = 13
style_title(ws_fc, "A1:H1", "Scenario Forecast -- Income Statement (LIVE, driven by Sheet 6 selector)")
ws_fc["A2"] = "Selected scenario:"
ws_fc["A2"].font = BOLD_FONT
ws_fc["B2"] = f"={SELECTOR}"
ws_fc["B2"].font = Font(bold=True, color="7F6000")

hdr = 4
ws_fc.cell(row=hdr, column=1, value="Line Item")
for i, fy in enumerate(f.FORECAST_YEARS):
    ws_fc.cell(row=hdr, column=4 + i, value=f"FY{fy}")
style_header_row(ws_fc, hdr, 1, 8)

# Row layout (each a (label, kind) pair); kind drives number format and
# whether it's a formula this script writes, vs. an assumption echo.
IS_ROWS = [
    "revenue", "cost_of_sales", "gross_profit", "gross_margin_pct", "sga_expense", "da_opex",
    "operating_income", "operating_margin_pct", "total_debt_beg", "total_debt_end", "interest_expense",
    "net_other_income", "pretax_income", "income_tax_expense", "net_income", "diluted_shares", "diluted_eps",
]
IS_LABELS = {
    "revenue": "Revenue", "cost_of_sales": "Cost of Sales", "gross_profit": "Gross Profit",
    "gross_margin_pct": "  Gross Margin %", "sga_expense": "SG&A", "da_opex": "D&A (in Opex)",
    "operating_income": "Operating Income", "operating_margin_pct": "  Operating Margin %",
    "total_debt_beg": "Total Debt, Beginning", "total_debt_end": "Total Debt, Ending",
    "interest_expense": "Interest Expense", "net_other_income": "Net Other Income",
    "pretax_income": "Pretax Income", "income_tax_expense": "Income Tax Expense",
    "net_income": "Net Income", "diluted_shares": "Diluted Shares (M)", "diluted_eps": "Diluted EPS ($)",
}
FC_ROW = {}
r = hdr + 1
for key in IS_ROWS:
    ws_fc.cell(row=r, column=1, value=IS_LABELS[key]).font = (
        BOLD_FONT if key in ("gross_profit", "operating_income", "net_income") else LABEL_FONT
    )
    FC_ROW[key] = r
    r += 1

HIST = f.HISTORICAL
for i, fy in enumerate(f.FORECAST_YEARS):
    col = FY_COLS[i]
    prev_col = FY_COLS[i - 1] if i > 0 else None

    # revenue
    growth_formula = asm_pick("revenue_growth_pct", i)
    prev_revenue_ref = f"{prev_col}{FC_ROW['revenue']}" if prev_col else HIST["revenue"][2025]
    ws_fc[f"{col}{FC_ROW['revenue']}"] = f"={prev_revenue_ref}*(1+({growth_formula[1:]}))"

    # gross margin % (echo) and gross profit / COGS
    ws_fc[f"{col}{FC_ROW['gross_margin_pct']}"] = asm_pick("gross_margin_pct", i)
    ws_fc[f"{col}{FC_ROW['gross_profit']}"] = f"={col}{FC_ROW['revenue']}*{col}{FC_ROW['gross_margin_pct']}"
    ws_fc[f"{col}{FC_ROW['cost_of_sales']}"] = f"={col}{FC_ROW['revenue']}-{col}{FC_ROW['gross_profit']}"

    # SG&A and D&A opex
    sga_pct_formula = asm_pick("sga_pct_of_revenue", i)
    ws_fc[f"{col}{FC_ROW['sga_expense']}"] = f"={col}{FC_ROW['revenue']}*({sga_pct_formula[1:]})"
    da_pct_formula = asm_pick("da_pct_of_revenue", i)
    ws_fc[f"{col}{FC_ROW['da_opex']}"] = f"={col}{FC_ROW['revenue']}*({da_pct_formula[1:]})"

    # operating income / margin
    ws_fc[f"{col}{FC_ROW['operating_income']}"] = (
        f"={col}{FC_ROW['gross_profit']}-{col}{FC_ROW['sga_expense']}-{col}{FC_ROW['da_opex']}"
    )
    ws_fc[f"{col}{FC_ROW['operating_margin_pct']}"] = f"={col}{FC_ROW['operating_income']}/{col}{FC_ROW['revenue']}"

    # debt roll-forward
    prev_debt_ref = f"{prev_col}{FC_ROW['total_debt_end']}" if prev_col else HIST["total_debt_gaap"][2025]
    ws_fc[f"{col}{FC_ROW['total_debt_beg']}"] = f"={prev_debt_ref}"
    proceeds_formula = asm_pick("debt_proceeds_musd", i)
    repay_formula = asm_pick("debt_repayments_musd", i)
    ws_fc[f"{col}{FC_ROW['total_debt_end']}"] = (
        f"={col}{FC_ROW['total_debt_beg']}+({proceeds_formula[1:]})-({repay_formula[1:]})"
    )

    # interest expense on average debt
    rate_formula = asm_pick("interest_rate_pct", i)
    ws_fc[f"{col}{FC_ROW['interest_expense']}"] = (
        f"=({rate_formula[1:]})*AVERAGE({col}{FC_ROW['total_debt_beg']},{col}{FC_ROW['total_debt_end']})"
    )

    # net other income
    ws_fc[f"{col}{FC_ROW['net_other_income']}"] = asm_pick("net_other_income_musd", i)

    # pretax / tax / net income
    ws_fc[f"{col}{FC_ROW['pretax_income']}"] = (
        f"={col}{FC_ROW['operating_income']}-{col}{FC_ROW['interest_expense']}+{col}{FC_ROW['net_other_income']}"
    )
    tax_rate_formula = asm_pick("effective_tax_rate_pct", i)
    ws_fc[f"{col}{FC_ROW['income_tax_expense']}"] = f"={col}{FC_ROW['pretax_income']}*({tax_rate_formula[1:]})"
    ws_fc[f"{col}{FC_ROW['net_income']}"] = f"={col}{FC_ROW['pretax_income']}-{col}{FC_ROW['income_tax_expense']}"

    # diluted shares / EPS
    share_chg_formula = asm_pick("diluted_share_change_pct", i)
    prev_shares_ref = f"{prev_col}{FC_ROW['diluted_shares']}" if prev_col else HIST["diluted_shares"][2025]
    ws_fc[f"{col}{FC_ROW['diluted_shares']}"] = f"={prev_shares_ref}*(1+({share_chg_formula[1:]}))"
    ws_fc[f"{col}{FC_ROW['diluted_eps']}"] = f"={col}{FC_ROW['net_income']}/{col}{FC_ROW['diluted_shares']}"

# Formatting pass
for key in IS_ROWS:
    rr = FC_ROW[key]
    fmt = PCT_FMT if key.endswith("_pct") else (EPS_FMT if key == "diluted_eps" else USD_FMT)
    for col in FY_COLS:
        cell = ws_fc[f"{col}{rr}"]
        cell.number_format = fmt
        cell.border = BORDER
ws_fc.freeze_panes = "D5"
ws_fc.sheet_view.showGridLines = False
print("Scenario Forecast sheet: income-statement formulas written")

FC = "'Scenario Forecast'"


def fc(key, col):
    return f"{FC}!{col}{FC_ROW[key]}"


# ============================================================================
# Sheet 8: Cash-Flow Bridge (LIVE, continues from Sheet 7)
# ============================================================================
ws_cf = wb.create_sheet("Cash-Flow Bridge")
set_col_widths(ws_cf, {"A": 34, "B": 10})
for col in FY_COLS:
    ws_cf.column_dimensions[col].width = 13
style_title(ws_cf, "A1:H1", "Cash-Flow Bridge (LIVE, driven by Sheet 6 selector)")
ws_cf["A2"] = "Selected scenario:"
ws_cf["A2"].font = BOLD_FONT
ws_cf["B2"] = f"={SELECTOR}"
ws_cf["B2"].font = Font(bold=True, color="7F6000")

hdr = 4
ws_cf.cell(row=hdr, column=1, value="Line Item")
for i, fy in enumerate(f.FORECAST_YEARS):
    ws_cf.cell(row=hdr, column=4 + i, value=f"FY{fy}")
style_header_row(ws_cf, hdr, 1, 8)

CF_ROWS = [
    "inventory_balance", "inventory_cash_impact", "ap_balance", "ap_cash_impact", "da_cfo_addback",
    "other_operating_cf", "cfo", "capex", "fcf", "investing_cf", "dividend_per_share", "dividends_paid",
    "post_dividend_fcf", "share_repurchases", "debt_proceeds", "debt_repayments", "financing_cf",
    "beginning_cash", "net_change_in_cash", "ending_cash",
]
CF_LABELS = {
    "inventory_balance": "Inventory Balance", "inventory_cash_impact": "  Inventory Cash Impact",
    "ap_balance": "Accounts Payable Balance", "ap_cash_impact": "  AP Cash Impact",
    "da_cfo_addback": "D&A Cash-Flow Add-back", "other_operating_cf": "Other Operating Cash Adjustments",
    "cfo": "Cash Flow from Operations (CFO)", "capex": "Capital Expenditures (CapEx)",
    "fcf": "Free Cash Flow (CFO - CapEx)", "investing_cf": "Total Investing Cash Flow (=-CapEx here)",
    "dividend_per_share": "Dividend per Share ($)", "dividends_paid": "Dividends Paid",
    "post_dividend_fcf": "Post-Dividend FCF", "share_repurchases": "Share Repurchases",
    "debt_proceeds": "Debt Proceeds", "debt_repayments": "Debt Repayments",
    "financing_cf": "Financing Cash Flow", "beginning_cash": "Beginning Cash",
    "net_change_in_cash": "Net Change in Cash", "ending_cash": "Ending Cash",
}
CF_ROW = {}
r = hdr + 1
for key in CF_ROWS:
    ws_cf.cell(row=r, column=1, value=CF_LABELS[key]).font = (
        BOLD_FONT if key in ("cfo", "fcf", "ending_cash") else LABEL_FONT
    )
    CF_ROW[key] = r
    r += 1


def cfr(key, col):
    return f"{col}{CF_ROW[key]}"


for i, fy in enumerate(f.FORECAST_YEARS):
    col = FY_COLS[i]
    prev_col = FY_COLS[i - 1] if i > 0 else None

    inv_pct_formula = asm_pick("inventory_pct_of_revenue", i)
    ws_cf[cfr("inventory_balance", col)] = f"={fc('revenue', col)}*({inv_pct_formula[1:]})"
    prev_inv_ref = f"{cfr('inventory_balance', prev_col)}" if prev_col else HIST["inventory"][2025]
    ws_cf[cfr("inventory_cash_impact", col)] = f"=-({cfr('inventory_balance', col)}-{prev_inv_ref})"

    ap_pct_formula = asm_pick("ap_pct_of_cogs", i)
    ws_cf[cfr("ap_balance", col)] = f"={fc('cost_of_sales', col)}*({ap_pct_formula[1:]})"
    prev_ap_ref = f"{cfr('ap_balance', prev_col)}" if prev_col else HIST["accounts_payable"][2025]
    ws_cf[cfr("ap_cash_impact", col)] = f"={cfr('ap_balance', col)}-{prev_ap_ref}"

    da_addback_formula = asm_pick("da_cfo_addback_pct_of_revenue", i)
    ws_cf[cfr("da_cfo_addback", col)] = f"={fc('revenue', col)}*({da_addback_formula[1:]})"
    ws_cf[cfr("other_operating_cf", col)] = asm_pick("other_operating_cf_musd", i)

    ws_cf[cfr("cfo", col)] = (
        f"={fc('net_income', col)}+{cfr('da_cfo_addback', col)}+{cfr('inventory_cash_impact', col)}"
        f"+{cfr('ap_cash_impact', col)}+{cfr('other_operating_cf', col)}"
    )

    capex_pct_formula = asm_pick("capex_pct_of_revenue", i)
    ws_cf[cfr("capex", col)] = f"={fc('revenue', col)}*({capex_pct_formula[1:]})"
    ws_cf[cfr("fcf", col)] = f"={cfr('cfo', col)}-{cfr('capex', col)}"
    ws_cf[cfr("investing_cf", col)] = f"=-{cfr('capex', col)}"

    div_growth_formula = asm_pick("dividend_per_share_growth_pct", i)
    prev_dps_ref = f"{cfr('dividend_per_share', prev_col)}" if prev_col else (
        HIST["dividends_paid"][2025] / HIST["diluted_shares"][2025]
    )
    ws_cf[cfr("dividend_per_share", col)] = f"={prev_dps_ref}*(1+({div_growth_formula[1:]}))"
    ws_cf[cfr("dividends_paid", col)] = f"={cfr('dividend_per_share', col)}*{fc('diluted_shares', col)}"

    ws_cf[cfr("post_dividend_fcf", col)] = f"={cfr('fcf', col)}-{cfr('dividends_paid', col)}"
    payout_formula = asm_pick("buyback_payout_pct_of_post_dividend_fcf", i)
    ws_cf[cfr("share_repurchases", col)] = f"=MAX(0,{cfr('post_dividend_fcf', col)}*({payout_formula[1:]}))"

    ws_cf[cfr("debt_proceeds", col)] = asm_pick("debt_proceeds_musd", i)
    ws_cf[cfr("debt_repayments", col)] = asm_pick("debt_repayments_musd", i)
    ws_cf[cfr("financing_cf", col)] = (
        f"=-{cfr('dividends_paid', col)}-{cfr('share_repurchases', col)}+{cfr('debt_proceeds', col)}"
        f"-{cfr('debt_repayments', col)}"
    )

    prev_cash_ref = f"{cfr('ending_cash', prev_col)}" if prev_col else HIST["cash_and_equivalents_balance_sheet"][2025]
    ws_cf[cfr("beginning_cash", col)] = f"={prev_cash_ref}"
    ws_cf[cfr("net_change_in_cash", col)] = f"={cfr('cfo', col)}+{cfr('investing_cf', col)}+{cfr('financing_cf', col)}"
    ws_cf[cfr("ending_cash", col)] = f"={cfr('beginning_cash', col)}+{cfr('net_change_in_cash', col)}"

for key in CF_ROWS:
    rr = CF_ROW[key]
    fmt = EPS_FMT if key == "dividend_per_share" else USD_FMT
    for col in FY_COLS:
        cell = ws_cf[f"{col}{rr}"]
        cell.number_format = fmt
        cell.border = BORDER
ws_cf.freeze_panes = "D5"
ws_cf.sheet_view.showGridLines = False
print("Cash-Flow Bridge sheet: formulas written")

CF = "'Cash-Flow Bridge'"


def cff(key, col):
    return f"{CF}!{col}{CF_ROW[key]}"


# ============================================================================
# Sheet 9: Investment Capacity (LIVE, continues from Sheets 7-8)
# ============================================================================
ws_ic = wb.create_sheet("Investment Capacity")
set_col_widths(ws_ic, {"A": 38, "B": 10})
for col in FY_COLS:
    ws_ic.column_dimensions[col].width = 13
style_title(ws_ic, "A1:H1", "Investment Capacity (LIVE, driven by Sheet 6 selector)")
ws_ic["A2"] = "Selected scenario:"
ws_ic["A2"].font = BOLD_FONT
ws_ic["B2"] = f"={SELECTOR}"
ws_ic["B2"].font = Font(bold=True, color="7F6000")

hdr = 4
ws_ic.cell(row=hdr, column=1, value="Line Item")
for i, fy in enumerate(f.FORECAST_YEARS):
    ws_ic.cell(row=hdr, column=4 + i, value=f"FY{fy}")
style_header_row(ws_ic, hdr, 1, 8)

IC_ROWS = [
    "gross_fcf_capacity", "post_dividend_capacity", "mandatory_financing_flows",
    "pre_discretionary_ending_cash", "min_cash_buffer", "near_term_debt_reserve", "deployable_capacity",
    "cumulative_deployable_capacity", "funding_warning",
]
IC_LABELS = {
    "gross_fcf_capacity": "Gross FCF Capacity (=CFO-CapEx)", "post_dividend_capacity": "Post-Dividend Capacity",
    "mandatory_financing_flows": "Mandatory Financing Flows (div + debt sched.)",
    "pre_discretionary_ending_cash": "Pre-Discretionary Ending Cash", "min_cash_buffer": "Minimum Cash Buffer",
    "near_term_debt_reserve": "Near-Term Debt Repayment Reserve",
    "deployable_capacity": "Legacy Gross Pre-Discretionary Ceiling (DEPRECATED -- see note below; not an executive KPI)",
    "cumulative_deployable_capacity": "Legacy Cumulative (DEPRECATED -- see Corrected Capacity Taxonomy below)",
    "funding_warning": "Funding Warning? (1=YES)",
}
IC_ROW = {}
r = hdr + 1
for key in IC_ROWS:
    ws_ic.cell(row=r, column=1, value=IC_LABELS[key]).font = BOLD_FONT if key == "deployable_capacity" else LABEL_FONT
    IC_ROW[key] = r
    r += 1


def icr(key, col):
    return f"{col}{IC_ROW[key]}"


cumulative_running_cell = None
for i, fy in enumerate(f.FORECAST_YEARS):
    col = FY_COLS[i]
    ws_ic[icr("gross_fcf_capacity", col)] = f"={cff('fcf', col)}"
    ws_ic[icr("post_dividend_capacity", col)] = f"={cff('fcf', col)}-{cff('dividends_paid', col)}"
    ws_ic[icr("mandatory_financing_flows", col)] = (
        f"=-{cff('dividends_paid', col)}+{cff('debt_proceeds', col)}-{cff('debt_repayments', col)}"
    )
    ws_ic[icr("pre_discretionary_ending_cash", col)] = (
        f"={cff('beginning_cash', col)}+{cff('cfo', col)}+{cff('investing_cf', col)}+{icr('mandatory_financing_flows', col)}"
    )
    min_buf_formula = asm_pick("min_cash_buffer_pct_of_revenue", i)
    ws_ic[icr("min_cash_buffer", col)] = f"={fc('revenue', col)}*({min_buf_formula[1:]})"
    ws_ic[icr("near_term_debt_reserve", col)] = f"={cff('debt_repayments', col)}"
    ws_ic[icr("deployable_capacity", col)] = (
        f"=MAX(0,{icr('pre_discretionary_ending_cash', col)}-{icr('min_cash_buffer', col)}-{icr('near_term_debt_reserve', col)})"
    )
    # Cumulative deployable capacity = terminal deployable capacity + total actually deployed
    # (always $0 deployed this round -- see Sheet 10) -- NEVER a naive sum of every year's own
    # balance, which would double-count unused cash carried forward via the cash roll-forward
    # (Milestone 3A's corrected definition, replicated here in Excel).
    if i == len(f.FORECAST_YEARS) - 1:
        ws_ic[icr("cumulative_deployable_capacity", col)] = f"={icr('deployable_capacity', col)}+0"
    else:
        ws_ic[icr("cumulative_deployable_capacity", col)] = "=\"see terminal year (FY2030)\""
    ws_ic[icr("funding_warning", col)] = f"=IF({cff('ending_cash', col)}<{icr('min_cash_buffer', col)},1,0)"

for key in IC_ROWS:
    rr = IC_ROW[key]
    fmt = USD_FMT if key != "funding_warning" else "0"
    for col in FY_COLS:
        cell = ws_ic[f"{col}{rr}"]
        if key != "cumulative_deployable_capacity" or col == FY_COLS[-1]:
            cell.number_format = fmt
        cell.border = BORDER
ws_ic.freeze_panes = "D5"
ws_ic.sheet_view.showGridLines = False

# ----------------------------------------------------------------------
# Corrected Capacity Taxonomy (Milestone 9 correction), live formulas,
# same selector, added BELOW the legacy (now deprecated, relabeled) block.
# Per docs/investment_capacity_semantic_audit.md: the legacy
# "deployable_capacity" above is a GROSS, pre-discretionary ceiling that
# never subtracts that year's own repurchases -- it is preserved verbatim
# above for backward compatibility, but is no longer the executive KPI.
# ----------------------------------------------------------------------
note_row = r + 1
ws_ic.merge_cells(f"A{note_row}:H{note_row}")
ws_ic.cell(row=note_row, column=1,
           value="NOTE: the legacy row above is DEPRECATED -- it is a gross, pre-discretionary ceiling "
                 "(includes carried-forward cash and new borrowing; never subtracts this year's own "
                 "repurchases). It is preserved, unmodified, for backward compatibility only. The "
                 "corrected taxonomy below is the executive-facing figure. See "
                 "docs/investment_capacity_correction_evidence.md.")
ws_ic.cell(row=note_row, column=1).font = Font(italic=True, size=9, color="C00000")
ws_ic.cell(row=note_row, column=1).alignment = Alignment(wrap_text=True)
ws_ic.row_dimensions[note_row].height = 30

ct_hdr = note_row + 2
ws_ic.merge_cells(f"A{ct_hdr}:H{ct_hdr}")
ws_ic.cell(row=ct_hdr, column=1, value="CORRECTED CAPACITY TAXONOMY (live, selected scenario)").font = Font(bold=True, size=12, color="1F3864")
ct_hdr2 = ct_hdr + 1
ws_ic.cell(row=ct_hdr2, column=1, value="Line Item")
for i, fy in enumerate(f.FORECAST_YEARS):
    ws_ic.cell(row=ct_hdr2, column=4 + i, value=f"FY{fy}")
style_header_row(ws_ic, ct_hdr2, 1, 8)

CT_ROWS = [
    "operating_fcf", "post_dividend_internal_generation", "opening_excess_liquidity",
    "gross_debt_proceeds", "gross_debt_repayments", "net_mandatory_debt_service",
    "self_funded_capacity_generated", "debt_funded_incremental_capacity", "total_gross_funding_capacity",
    "share_repurchases", "strategic_investment", "voluntary_debt_reduction", "other_discretionary_uses",
    "total_discretionary_deployment", "forward_debt_repayment_reserve", "remaining_deployable_headroom",
    "ending_excess_liquidity", "mandatory_debt_uses_deprecated", "self_funded_gross_capacity_deprecated",
]
CT_LABELS = {
    "operating_fcf": "A. Operating FCF (= CFO - CapEx)",
    "post_dividend_internal_generation": "B. Post-Dividend Internal Generation",
    "opening_excess_liquidity": "Opening Excess Liquidity (STOCK, = MAX(0, beg. cash - buffer)) -- never labeled 'generated'",
    "gross_debt_proceeds": "  Gross Debt Proceeds (supporting, transparent)",
    "gross_debt_repayments": "  Gross Debt Repayments (supporting, transparent)",
    "net_mandatory_debt_service": "Net Mandatory Debt Service (= MAX(0, gross repayments - gross proceeds))",
    "self_funded_capacity_generated": "C. Self-Funded Capacity Generated (FLOW, excludes opening liquidity)",
    "debt_funded_incremental_capacity": "D. Debt-Funded Incremental Capacity (= MAX(0, proceeds - repayments); never gross issuance)",
    "total_gross_funding_capacity": "E. TOTAL GROSS FUNDING CAPACITY (Opening Liquidity + C + D)",
    "share_repurchases": "  Share Repurchases",
    "strategic_investment": "  Strategic Investment (none modeled this round)",
    "voluntary_debt_reduction": "  Voluntary Debt Reduction (none modeled this round)",
    "other_discretionary_uses": "  Other Discretionary Uses (none modeled this round)",
    "total_discretionary_deployment": "F. TOTAL DISCRETIONARY DEPLOYMENT",
    "forward_debt_repayment_reserve": "Forward Debt-Repayment Reserve (next year's net debt service; FY2030 is a documented FY2031 proxy)",
    "remaining_deployable_headroom": "G. REMAINING DEPLOYABLE HEADROOM (stock, = MAX(0, E - F - forward reserve))",
    "ending_excess_liquidity": "Ending Excess Liquidity (independent cross-check: = G + forward reserve)",
    "mandatory_debt_uses_deprecated": "DEPRECATED: Mandatory Debt Uses (v1, = gross repayments, double-subtracted -- see evidence doc)",
    "self_funded_gross_capacity_deprecated": "DEPRECATED: Self-Funded Gross Capacity (v1-style, includes opening liquidity -- never labeled 'generated')",
}
CT_ROW = {}
rr = ct_hdr2 + 1
for key in CT_ROWS:
    bold_keys = ("self_funded_capacity_generated", "debt_funded_incremental_capacity",
                 "total_gross_funding_capacity", "total_discretionary_deployment", "remaining_deployable_headroom")
    deprecated_keys = ("mandatory_debt_uses_deprecated", "self_funded_gross_capacity_deprecated")
    if key in deprecated_keys:
        cell_font = Font(italic=True, size=10, color="C00000")
    elif key in bold_keys:
        cell_font = BOLD_FONT
    else:
        cell_font = LABEL_FONT
    ws_ic.cell(row=rr, column=1, value=CT_LABELS[key]).font = cell_font
    CT_ROW[key] = rr
    rr += 1


def ctr(key, col):
    return f"{col}{CT_ROW[key]}"


NEXT_FY_COL = {"D": "E", "E": "F", "F": "G", "G": "H"}  # FY2030 (H) has no next column -- proxy uses its own column

for i, fy in enumerate(f.FORECAST_YEARS):
    col = FY_COLS[i]
    ws_ic[ctr("operating_fcf", col)] = f"={cff('fcf', col)}"
    ws_ic[ctr("post_dividend_internal_generation", col)] = f"={ctr('operating_fcf', col)}-{cff('dividends_paid', col)}"
    ws_ic[ctr("opening_excess_liquidity", col)] = f"=MAX(0,{cff('beginning_cash', col)}-{icr('min_cash_buffer', col)})"
    ws_ic[ctr("gross_debt_proceeds", col)] = f"={cff('debt_proceeds', col)}"
    ws_ic[ctr("gross_debt_repayments", col)] = f"={cff('debt_repayments', col)}"
    ws_ic[ctr("net_mandatory_debt_service", col)] = (
        f"=MAX(0,{ctr('gross_debt_repayments', col)}-{ctr('gross_debt_proceeds', col)})"
    )
    ws_ic[ctr("self_funded_capacity_generated", col)] = (
        f"={ctr('post_dividend_internal_generation', col)}-{ctr('net_mandatory_debt_service', col)}"
    )
    ws_ic[ctr("debt_funded_incremental_capacity", col)] = (
        f"=MAX(0,{ctr('gross_debt_proceeds', col)}-{ctr('gross_debt_repayments', col)})"
    )
    ws_ic[ctr("total_gross_funding_capacity", col)] = (
        f"={ctr('opening_excess_liquidity', col)}+{ctr('self_funded_capacity_generated', col)}"
        f"+{ctr('debt_funded_incremental_capacity', col)}"
    )
    ws_ic[ctr("share_repurchases", col)] = f"={cff('share_repurchases', col)}"
    ws_ic[ctr("strategic_investment", col)] = 0
    ws_ic[ctr("voluntary_debt_reduction", col)] = 0
    ws_ic[ctr("other_discretionary_uses", col)] = 0
    ws_ic[ctr("total_discretionary_deployment", col)] = (
        f"={ctr('share_repurchases', col)}+{ctr('strategic_investment', col)}"
        f"+{ctr('voluntary_debt_reduction', col)}+{ctr('other_discretionary_uses', col)}"
    )
    next_col = NEXT_FY_COL.get(col)
    if next_col is not None:
        ws_ic[ctr("forward_debt_repayment_reserve", col)] = f"={ctr('net_mandatory_debt_service', next_col)}"
    else:
        # Terminal year (FY2030): documented proxy -- FY2031 is outside the forecast horizon.
        ws_ic[ctr("forward_debt_repayment_reserve", col)] = f"={ctr('net_mandatory_debt_service', col)}"
    ws_ic[ctr("remaining_deployable_headroom", col)] = (
        f"=MAX(0,{ctr('total_gross_funding_capacity', col)}-{ctr('total_discretionary_deployment', col)}"
        f"-{ctr('forward_debt_repayment_reserve', col)})"
    )
    ws_ic[ctr("ending_excess_liquidity", col)] = f"=MAX(0,{cff('ending_cash', col)}-{icr('min_cash_buffer', col)})"
    # DEPRECATED-BY-v2 rows, kept only for backward-compatible reference (never the headline KPI).
    ws_ic[ctr("mandatory_debt_uses_deprecated", col)] = f"={ctr('net_mandatory_debt_service', col)}"
    ws_ic[ctr("self_funded_gross_capacity_deprecated", col)] = (
        f"={ctr('opening_excess_liquidity', col)}+{ctr('self_funded_capacity_generated', col)}"
    )

for key in CT_ROWS:
    row_num = CT_ROW[key]
    for col in FY_COLS:
        cell = ws_ic[f"{col}{row_num}"]
        cell.number_format = USD_FMT
        cell.border = BORDER

proof_row = rr + 1
ws_ic.merge_cells(f"A{proof_row}:H{proof_row}")
ws_ic.cell(row=proof_row, column=1,
           value="Independent proof: Ending Excess Liquidity (from ending cash) equals Remaining "
                 "Deployable Headroom PLUS the Forward Debt-Repayment Reserve, for every year -- "
                 "confirming no dollar is counted in both headroom and deployment/reserve.").font = Font(italic=True, size=9)
ws_ic.row_dimensions[proof_row].height = 20

# Static, all-scenario cumulative-capacity reconciliation (A-G), computed
# from target_cash.capacity_taxonomy -- deliberately NEVER a sum of
# per-year ending-headroom balances (see that module's own docstrings).
cum_hdr = proof_row + 2
ws_ic.merge_cells(f"A{cum_hdr}:H{cum_hdr}")
ws_ic.cell(row=cum_hdr, column=1,
           value="CUMULATIVE CAPACITY RECONCILIATION, FY2026-FY2030 (STATIC reference, all scenarios -- "
                 "from target_cash.capacity_taxonomy; NEVER a sum of per-year ending balances)"
           ).font = Font(bold=True, size=11, color="1F3864")
cum_hdr2 = cum_hdr + 1
cum_labels = [
    "Scenario", "A. Cumulative Self-Funded Generation", "B. Cumulative Debt-Funded Capacity",
    "C. Opening Excess Liquidity (horizon start)", "D. Cumulative Discretionary Deployment",
    "E. Terminal Remaining Headroom", "Ending Reserve Movement",
    "Terminal Forward Debt-Repayment Reserve (FY2031 proxy)",
    "Total Horizon Capacity Accessible (C+A+B)", "Reconciles To (D+E+Reserve Mvmt+Forward Reserve)",
]
for j, label in enumerate(cum_labels):
    ws_ic.cell(row=cum_hdr2, column=1 + j, value=label)
style_header_row(ws_ic, cum_hdr2, 1, len(cum_labels))
rr2 = cum_hdr2 + 1
for scenario in f.SCENARIOS:
    summary = capacity_summaries[scenario]
    reconciles_to = (summary.cumulative_discretionary_deployment + summary.terminal_remaining_headroom
                      + summary.ending_reserve_movement + summary.terminal_forward_debt_repayment_reserve)
    values = [
        scenario.capitalize(), summary.cumulative_self_funded_generation, summary.cumulative_debt_funded_capacity,
        summary.opening_excess_liquidity_at_horizon_start, summary.cumulative_discretionary_deployment,
        summary.terminal_remaining_headroom, summary.ending_reserve_movement,
        summary.terminal_forward_debt_repayment_reserve,
        summary.total_horizon_capacity_accessible, reconciles_to,
    ]
    for j, val in enumerate(values):
        cell = ws_ic.cell(row=rr2, column=1 + j, value=val if j == 0 else round(val, 1))
        if j > 0:
            cell.number_format = USD_FMT
        cell.border = BORDER
    rr2 += 1

ws_ic.sheet_view.showGridLines = False
print("Investment Capacity sheet: legacy + corrected-taxonomy formulas written")

IC = "'Investment Capacity'"


def icf(key, col):
    return f"{IC}!{col}{IC_ROW[key]}"


def ctf(key, col):
    return f"{IC}!{col}{CT_ROW[key]}"


# ============================================================================
# Sheet 10: Capital Allocation (LIVE waterfall + no-double-counting proof)
# ============================================================================
ws_ca = wb.create_sheet("Capital Allocation")
set_col_widths(ws_ca, {"A": 46, "B": 10})
for col in FY_COLS:
    ws_ca.column_dimensions[col].width = 13
style_title(ws_ca, "A1:H1", "Capital Allocation Waterfall (LIVE, driven by Sheet 6 selector)")
ws_ca["A2"] = "Selected scenario:"
ws_ca["A2"].font = BOLD_FONT
ws_ca["B2"] = f"={SELECTOR}"
ws_ca["B2"].font = Font(bold=True, color="7F6000")
ws_ca["A3"] = ("Order of operations: 1) Operating cash generation 2) CapEx 3) Dividends "
               "4) Minimum cash preservation 5) Scheduled debt 6) Incremental financing (always $0) "
               "7) Discretionary repurchases 8) Ending cash.")
ws_ca["A3"].font = NOTE_FONT
ws_ca.merge_cells("A3:H3")
ws_ca["A3"].alignment = Alignment(wrap_text=True)
ws_ca.row_dimensions[3].height = 28

hdr = 5
ws_ca.cell(row=hdr, column=1, value="Waterfall Step")
for i, fy in enumerate(f.FORECAST_YEARS):
    ws_ca.cell(row=hdr, column=4 + i, value=f"FY{fy}")
style_header_row(ws_ca, hdr, 1, 8)

WF_ROWS = [
    "beginning_cash", "step1_cfo", "step2_capex", "step3_dividends", "checkpoint_above_buffer",
    "step5_debt", "checkpoint_deployable", "step6_incremental", "step7_repurchases", "step7b_deployment",
    "step8_ending_cash",
]
WF_LABELS = {
    "beginning_cash": "Beginning Cash", "step1_cfo": "1. + Operating Cash Generation (CFO)",
    "step2_capex": "2. + Capital Expenditures (CFI)", "step3_dividends": "3. - Dividends",
    "checkpoint_above_buffer": "4. Checkpoint: Cash Above Min. Buffer (no movement)",
    "step5_debt": "5. +/- Scheduled Debt (proceeds - repayments)",
    "checkpoint_deployable": "5b. Checkpoint: DEPLOYABLE CAPACITY",
    "step6_incremental": "6. + Incremental Financing (always $0)",
    "step7_repurchases": "7. - Discretionary Repurchases", "step7b_deployment": "7b. - Mgmt-Selected Deployment (always $0)",
    "step8_ending_cash": "8. = Ending Cash",
}
WF_ROW = {}
r = hdr + 1
for key in WF_ROWS:
    ws_ca.cell(row=r, column=1, value=WF_LABELS[key]).font = (
        BOLD_FONT if key in ("checkpoint_deployable", "step8_ending_cash") else LABEL_FONT
    )
    WF_ROW[key] = r
    r += 1


def wfr(key, col):
    return f"{col}{WF_ROW[key]}"


for i, fy in enumerate(f.FORECAST_YEARS):
    col = FY_COLS[i]
    ws_ca[wfr("beginning_cash", col)] = f"={cff('beginning_cash', col)}"
    ws_ca[wfr("step1_cfo", col)] = f"={cff('cfo', col)}"
    ws_ca[wfr("step2_capex", col)] = f"={cff('investing_cf', col)}"
    ws_ca[wfr("step3_dividends", col)] = f"=-{cff('dividends_paid', col)}"
    running = (
        f"{wfr('beginning_cash', col)}+{wfr('step1_cfo', col)}+{wfr('step2_capex', col)}+{wfr('step3_dividends', col)}"
    )
    ws_ca[wfr("checkpoint_above_buffer", col)] = f"=({running})-{icf('min_cash_buffer', col)}"
    ws_ca[wfr("step5_debt", col)] = f"={cff('debt_proceeds', col)}-{cff('debt_repayments', col)}"
    running2 = f"({running})+{wfr('step5_debt', col)}"
    ws_ca[wfr("checkpoint_deployable", col)] = (
        f"=MAX(0,({running2})-{icf('min_cash_buffer', col)}-{icf('near_term_debt_reserve', col)})"
    )
    ws_ca[wfr("step6_incremental", col)] = 0
    ws_ca[wfr("step7_repurchases", col)] = f"=-{cff('share_repurchases', col)}"
    ws_ca[wfr("step7b_deployment", col)] = 0
    ws_ca[wfr("step8_ending_cash", col)] = (
        f"=({running2})+{wfr('step6_incremental', col)}+{wfr('step7_repurchases', col)}+{wfr('step7b_deployment', col)}"
    )

for key in WF_ROWS:
    rr = WF_ROW[key]
    for col in FY_COLS:
        cell = ws_ca[f"{col}{rr}"]
        cell.number_format = USD_FMT
        cell.border = BORDER

# No-double-counting proof, live
proof_row = r + 1
ws_ca.cell(row=proof_row, column=1, value="No-Double-Counting Proof").font = BOLD_FONT
proof_row += 1
ws_ca.cell(row=proof_row, column=1, value="Ending Cash (Sheet 8) matches Step 8 above?")
for i, fy in enumerate(f.FORECAST_YEARS):
    col = FY_COLS[i]
    ws_ca.cell(row=proof_row, column=4 + i,
               value=f'=IF(ROUND({cff("ending_cash", col)}-{wfr("step8_ending_cash", col)},2)=0,"OK","MISMATCH")')
ws_ca.freeze_panes = "D6"
ws_ca.sheet_view.showGridLines = False
print("Capital Allocation sheet: waterfall formulas + proof written")

# ============================================================================
# Sheet 11: DCF Valuation (LIVE, scenario-invariant WACC/growth, scenario-
# dependent UFCF via the same selector)
# ============================================================================
ws_dcf = wb.create_sheet("DCF Valuation")
set_col_widths(ws_dcf, {"A": 40, "B": 14, "C": 4})
for col in FY_COLS:
    ws_dcf.column_dimensions[col].width = 13
style_title(ws_dcf, "A1:H1", "DCF Valuation -- Scenario-Based Model (NOT Investment Advice)")
ws_dcf["A2"] = "Selected scenario:"
ws_dcf["A2"].font = BOLD_FONT
ws_dcf["B2"] = f"={SELECTOR}"
ws_dcf["B2"].font = Font(bold=True, color="7F6000")
ws_dcf.merge_cells("A3:H3")
ws_dcf["A3"] = ("Illustrative WACC inputs below (yellow) -- no live market-data source is available "
                "to this project (SEC filings only); see Sheet 15 (Limitations).")
ws_dcf["A3"].font = NOTE_FONT

ws_dcf["A5"] = "WACC Components (scenario-invariant)"
ws_dcf["A5"].font = BOLD_FONT
WACC_INPUT_ROWS = [
    ("risk_free_rate_pct", "Risk-Free Rate", True), ("equity_risk_premium_pct", "Equity Risk Premium", True),
    ("beta", "Beta", False), ("target_equity_weight_pct", "Target Equity Weight", True),
    ("target_debt_weight_pct", "Target Debt Weight", True), ("cost_of_debt_pct", "Pre-Tax Cost of Debt", True),
    ("tax_rate_for_wacc_pct", "Tax Rate (for WACC)", True), ("terminal_growth_pct", "Terminal Growth Rate", True),
]
WACC_ROW = {}
r = 6
for metric, label, is_pct in WACC_INPUT_ROWS:
    ws_dcf.cell(row=r, column=1, value=label).font = LABEL_FONT
    cell = ws_dcf.cell(row=r, column=2, value=val_m[metric] / 100 if is_pct else val_m[metric])
    cell.number_format = PCT_FMT if is_pct else "0.00"
    cell.fill = INPUT_FILL
    cell.font = INPUT_FONT
    cell.border = BORDER
    WACC_ROW[metric] = r
    r += 1

wacc_calc_row = r + 1
ws_dcf.cell(row=wacc_calc_row, column=1, value="Cost of Equity (CAPM)").font = BOLD_FONT
ws_dcf.cell(row=wacc_calc_row, column=2,
            value=f"=B{WACC_ROW['risk_free_rate_pct']}+B{WACC_ROW['beta']}*B{WACC_ROW['equity_risk_premium_pct']}"
            ).number_format = PCT_FMT
ws_dcf.cell(row=wacc_calc_row + 1, column=1, value="After-Tax Cost of Debt").font = BOLD_FONT
ws_dcf.cell(row=wacc_calc_row + 1, column=2,
            value=f"=B{WACC_ROW['cost_of_debt_pct']}*(1-B{WACC_ROW['tax_rate_for_wacc_pct']})"
            ).number_format = PCT_FMT
wacc_row_final = wacc_calc_row + 2
ws_dcf.cell(row=wacc_row_final, column=1, value="WACC").font = BOLD_FONT
ws_dcf.cell(row=wacc_row_final, column=2,
            value=(f"=B{wacc_calc_row}*B{WACC_ROW['target_equity_weight_pct']}"
                   f"+B{wacc_calc_row + 1}*B{WACC_ROW['target_debt_weight_pct']}")
            ).number_format = PCT_FMT
for rr in (wacc_calc_row, wacc_calc_row + 1, wacc_row_final):
    ws_dcf.cell(row=rr, column=2).border = BORDER

hdr = wacc_row_final + 2
ws_dcf.cell(row=hdr, column=1, value="Unlevered Free Cash Flow")
for i, fy in enumerate(f.FORECAST_YEARS):
    ws_dcf.cell(row=hdr, column=4 + i, value=f"FY{fy}")
style_header_row(ws_dcf, hdr, 1, 8)

DCF_ROWS = ["nopat", "da_addback", "other_opcf", "capex", "wc_change", "ufcf", "discount_factor", "pv_ufcf"]
DCF_LABELS = {
    "nopat": "NOPAT (EBIT x (1-tax))", "da_addback": "+ D&A Add-back", "other_opcf": "+ Other Operating CF",
    "capex": "- CapEx", "wc_change": "+/- Working Capital Cash Impact", "ufcf": "Unlevered FCF (Total)",
    "discount_factor": "Discount Factor", "pv_ufcf": "PV of UFCF",
}
DCF_ROW = {}
r = hdr + 1
for key in DCF_ROWS:
    ws_dcf.cell(row=r, column=1, value=DCF_LABELS[key]).font = BOLD_FONT if key in ("ufcf", "pv_ufcf") else LABEL_FONT
    DCF_ROW[key] = r
    r += 1


def dcfr(key, col):
    return f"{col}{DCF_ROW[key]}"


for i, fy in enumerate(f.FORECAST_YEARS):
    col = FY_COLS[i]
    tax_rate_formula = asm_pick("effective_tax_rate_pct", i)
    ws_dcf[dcfr("nopat", col)] = f"={fc('operating_income', col)}*(1-({tax_rate_formula[1:]}))"
    ws_dcf[dcfr("da_addback", col)] = f"={cff('da_cfo_addback', col)}"
    ws_dcf[dcfr("other_opcf", col)] = f"={cff('other_operating_cf', col)}"
    ws_dcf[dcfr("capex", col)] = f"=-{cff('capex', col)}"
    ws_dcf[dcfr("wc_change", col)] = f"={cff('inventory_cash_impact', col)}+{cff('ap_cash_impact', col)}"
    ws_dcf[dcfr("ufcf", col)] = (
        f"={dcfr('nopat', col)}+{dcfr('da_addback', col)}+{dcfr('other_opcf', col)}"
        f"+{dcfr('capex', col)}+{dcfr('wc_change', col)}"
    )
    ws_dcf[dcfr("discount_factor", col)] = f"=1/(1+$B${wacc_row_final})^{i + 1}"
    ws_dcf[dcfr("pv_ufcf", col)] = f"={dcfr('ufcf', col)}*{dcfr('discount_factor', col)}"

for key in DCF_ROWS:
    rr = DCF_ROW[key]
    fmt = "0.0000" if key == "discount_factor" else USD_FMT
    for col in FY_COLS:
        cell = ws_dcf[f"{col}{rr}"]
        cell.number_format = fmt
        cell.border = BORDER

bridge_hdr = r + 1
ws_dcf.cell(row=bridge_hdr, column=1, value="Valuation Bridge").font = BOLD_FONT
br = bridge_hdr + 1
ws_dcf.cell(row=br, column=1, value="PV of Explicit-Period UFCF (FY2026-FY2030)")
ws_dcf.cell(row=br, column=2, value=f"=SUM({dcfr('pv_ufcf', FY_COLS[0])}:{dcfr('pv_ufcf', FY_COLS[-1])})")
row_pv_explicit = br
br += 1
ws_dcf.cell(row=br, column=1, value="Terminal-Year UFCF (FY2030)")
ws_dcf.cell(row=br, column=2, value=f"={dcfr('ufcf', FY_COLS[-1])}")
row_terminal_ufcf = br
br += 1
ws_dcf.cell(row=br, column=1, value="Terminal Value (undiscounted, Gordon Growth)")
ws_dcf.cell(row=br, column=2,
            value=f"=B{row_terminal_ufcf}*(1+B{WACC_ROW['terminal_growth_pct']})/($B${wacc_row_final}-B{WACC_ROW['terminal_growth_pct']})")
row_tv_undisc = br
br += 1
ws_dcf.cell(row=br, column=1, value="PV of Terminal Value")
ws_dcf.cell(row=br, column=2, value=f"=B{row_tv_undisc}/(1+$B${wacc_row_final})^{len(f.FORECAST_YEARS)}")
row_pv_tv = br
br += 1
ws_dcf.cell(row=br, column=1, value="Enterprise Value").font = BOLD_FONT
ws_dcf.cell(row=br, column=2, value=f"=B{row_pv_explicit}+B{row_pv_tv}").font = BOLD_FONT
row_ev = br
br += 1
ws_dcf.cell(row=br, column=1, value="Net Debt (FY2025 actual: total_debt_gaap - cash)")
ws_dcf.cell(row=br, column=2, value=round(f.HISTORICAL["total_debt_gaap"][2025] - f.HISTORICAL["cash_and_equivalents_balance_sheet"][2025], 1))
ws_dcf.cell(row=br, column=2).fill = INPUT_FILL
ws_dcf.cell(row=br, column=2).font = INPUT_FONT
row_net_debt = br
br += 1
ws_dcf.cell(row=br, column=1, value="Equity Value").font = BOLD_FONT
ws_dcf.cell(row=br, column=2, value=f"=B{row_ev}-B{row_net_debt}").font = BOLD_FONT
row_equity = br
br += 1
ws_dcf.cell(row=br, column=1, value="Diluted Shares (FY2025 actual, millions)")
ws_dcf.cell(row=br, column=2, value=f.HISTORICAL["diluted_shares"][2025])
ws_dcf.cell(row=br, column=2).fill = INPUT_FILL
ws_dcf.cell(row=br, column=2).font = INPUT_FONT
row_shares = br
br += 1
ws_dcf.cell(row=br, column=1, value="IMPLIED VALUE PER SHARE").font = Font(bold=True, size=12)
ws_dcf.cell(row=br, column=2, value=f"=B{row_equity}/B{row_shares}").font = Font(bold=True, size=12, color="1F3864")
row_per_share = br

for rr in range(bridge_hdr + 1, row_per_share + 1):
    c = ws_dcf.cell(row=rr, column=2)
    c.number_format = USD_FMT if rr != row_per_share else "$0.00"
    c.border = BORDER

# Static all-scenario DCF comparison (Python-computed, clearly labeled)
comp_hdr = row_per_share + 3
ws_dcf.cell(row=comp_hdr, column=1,
            value="All-Scenario DCF Comparison (STATIC reference -- from target_cash.valuation, same WACC/growth)"
            ).font = BOLD_FONT
comp_hdr2 = comp_hdr + 1
for j, label in enumerate(["Scenario", "Enterprise Value", "Equity Value", "Implied Value/Share"]):
    ws_dcf.cell(row=comp_hdr2, column=1 + j, value=label)
style_header_row(ws_dcf, comp_hdr2, 1, 4)
rr = comp_hdr2 + 1
for scenario in f.SCENARIOS:
    result = dcf_results[scenario]
    ws_dcf.cell(row=rr, column=1, value=scenario.capitalize())
    ws_dcf.cell(row=rr, column=2, value=round(result.enterprise_value, 1)).number_format = USD_FMT
    ws_dcf.cell(row=rr, column=3, value=round(result.equity_value, 1)).number_format = USD_FMT
    ws_dcf.cell(row=rr, column=4, value=round(result.implied_value_per_share, 2)).number_format = "$0.00"
    for cc in range(1, 5):
        ws_dcf.cell(row=rr, column=cc).border = BORDER
    rr += 1

ws_dcf.freeze_panes = "D" + str(hdr + 1)
ws_dcf.sheet_view.showGridLines = False
print("DCF Valuation sheet: formulas + static comparison written")

# ============================================================================
# Sheet 3: Historical Financials (static, from HISTORICAL literals)
# ============================================================================
ws_h = wb.create_sheet("Historical Financials")
set_col_widths(ws_h, {"A": 34})
for col in "BCDEF":
    ws_h.column_dimensions[col].width = 13
style_title(ws_h, "A1:F1", "Historical Financials, FY2021-FY2025 (latest_restated, ACTUAL)")
hdr = 3
ws_h.cell(row=hdr, column=1, value="Line Item")
for i, hy in enumerate(f.HISTORICAL_YEARS):
    ws_h.cell(row=hdr, column=2 + i, value=f"FY{hy}")
style_header_row(ws_h, hdr, 1, 6)
HIST_ROWS = [
    ("revenue", "Revenue"), ("cost_of_sales", "Cost of Sales"), ("gross_profit", "Gross Profit"),
    ("operating_expenses", "SG&A"), ("depreciation_amortization_opex", "D&A (Opex)"),
    ("operating_income", "Operating Income"), ("interest_expense", "Interest Expense"),
    ("net_other_income", "Net Other Income"), ("pretax_income", "Pretax Income"),
    ("income_tax_expense", "Income Tax Expense"), ("net_income", "Net Income"),
    ("diluted_eps", "Diluted EPS ($)"), ("diluted_shares", "Diluted Shares (M)"),
    ("operating_cash_flow", "CFO"), ("capital_expenditure", "CapEx (PP&E acquisitions)"),
    ("free_cash_flow", "FCF (CFO - CapEx)"), ("investing_cash_flow", "Total Investing Cash Flow"),
    ("financing_cash_flow", "Financing Cash Flow"), ("dividends_paid", "Dividends Paid"),
    ("share_repurchases", "Share Repurchases"), ("cash_and_equivalents_balance_sheet", "Cash & Equivalents"),
    ("total_debt_gaap", "Total Debt (GAAP, excl. finance leases)"),
]
r = hdr + 1
for key, label in HIST_ROWS:
    ws_h.cell(row=r, column=1, value=label).font = LABEL_FONT
    for i, hy in enumerate(f.HISTORICAL_YEARS):
        cell = ws_h.cell(row=r, column=2 + i, value=f.HISTORICAL[key][hy])
        cell.number_format = EPS_FMT if key == "diluted_eps" else USD_FMT
        cell.border = BORDER
    r += 1
ws_h.merge_cells(f"A{r + 1}:F{r + 1}")
ws_h.cell(row=r + 1, column=1,
          value="Note: FY2023 was a 53-week fiscal year. All figures are the LATEST-RESTATED analytical "
                "view -- see Sheet 4 for the as-originally-filed vs. restated comparison.").font = NOTE_FONT
ws_h.freeze_panes = "B4"
ws_h.sheet_view.showGridLines = False
print("Historical Financials sheet written")

# ============================================================================
# Sheet 4: Filing-Vintage Comparison (as_originally_filed vs latest_restated)
# ============================================================================
import sqlite3
conn = sqlite3.connect("data/curated/target_cash.db")
vintage_rows = conn.execute(
    """
    SELECT metric, fiscal_year, analytical_view, value_normalized
    FROM annual_facts
    WHERE metric IN ('revenue','cost_of_sales','operating_expenses','gross_profit')
    ORDER BY metric, fiscal_year, analytical_view
    """
).fetchall()
conn.close()

ws_v = wb.create_sheet("Filing-Vintage Comparison")
set_col_widths(ws_v, {"A": 20, "B": 12})
for col in "CDEFG":
    ws_v.column_dimensions[col].width = 16
style_title(ws_v, "A1:G1", "Filing-Vintage Comparison: As-Originally-Filed vs. Latest-Restated")
ws_v.merge_cells("A2:G2")
ws_v["A2"] = ("Target reclassified certain distribution-center costs between Cost of Sales and SG&A in "
              "later filings (disclosed reclassification, FY2022-FY2023 restated views differ from the "
              "originally-filed views). Revenue is identical in both views every year -- only the COGS/SG&A "
              "split moved.")
ws_v["A2"].font = NOTE_FONT
ws_v["A2"].alignment = Alignment(wrap_text=True)
ws_v.row_dimensions[2].height = 30

by_metric_fy = {}
for metric, fy, view, val in vintage_rows:
    by_metric_fy.setdefault((metric, fy), {})[view] = val

hdr = 4
headers = ["Metric", "FY", "As-Originally-Filed", "Latest-Restated", "Difference", "% Change", "Reclassified?"]
for j, h in enumerate(headers):
    ws_v.cell(row=hdr, column=1 + j, value=h)
style_header_row(ws_v, hdr, 1, 7)
r = hdr + 1
metric_labels = {"revenue": "Revenue", "cost_of_sales": "Cost of Sales", "gross_profit": "Gross Profit",
                  "operating_expenses": "SG&A"}
for metric in ["revenue", "cost_of_sales", "gross_profit", "operating_expenses"]:
    for fy in f.HISTORICAL_YEARS:
        views = by_metric_fy.get((metric, fy), {})
        orig = views.get("as_originally_filed")
        restated = views.get("latest_restated")
        if orig is None or restated is None:
            continue
        diff = restated - orig
        pct = (diff / orig * 100) if orig else 0
        ws_v.cell(row=r, column=1, value=metric_labels[metric]).font = LABEL_FONT
        ws_v.cell(row=r, column=2, value=fy).font = LABEL_FONT
        ws_v.cell(row=r, column=3, value=orig).number_format = USD_FMT
        ws_v.cell(row=r, column=4, value=restated).number_format = USD_FMT
        ws_v.cell(row=r, column=5, value=diff).number_format = USD_FMT
        ws_v.cell(row=r, column=6, value=pct / 100).number_format = "0.00%"
        ws_v.cell(row=r, column=7, value="YES" if abs(diff) > 0.01 else "no")
        for cc in range(1, 8):
            ws_v.cell(row=r, column=cc).border = BORDER
        r += 1
ws_v.freeze_panes = "A5"
ws_v.sheet_view.showGridLines = False
print("Filing-Vintage Comparison sheet written")

# ============================================================================
# Sheet 5: Quarterly Cash Proof (real FY2025 quarterly instant_facts data)
# ============================================================================
conn = sqlite3.connect("data/curated/target_cash.db")
quarterly_cash = conn.execute(
    """
    SELECT as_of_date, value_normalized, accession_number
    FROM instant_facts WHERE metric='cash_and_equivalents_balance_sheet'
    ORDER BY as_of_date
    """
).fetchall()
conn.close()

ws_q = wb.create_sheet("Quarterly Cash Proof")
set_col_widths(ws_q, {"A": 16, "B": 18, "C": 20, "D": 16})
style_title(ws_q, "A1:D1", "Quarterly Cash Proof -- FY2025 Seasonality Evidence")
ws_q.merge_cells("A2:D2")
ws_q["A2"] = ("The only year of quarterly granularity in the registered source set. Grounds the "
              "seasonal-liquidity-stress overlay's 50% haircut (Q1 trough vs. Q4/year-end = 52.6%).")
ws_q["A2"].font = NOTE_FONT
ws_q["A2"].alignment = Alignment(wrap_text=True)
hdr = 4
for j, h in enumerate(["As-Of Date", "Cash & Equivalents ($M)", "Accession", "Period"]):
    ws_q.cell(row=hdr, column=1 + j, value=h)
style_header_row(ws_q, hdr, 1, 4)
period_labels = {0: "FY2024 Year-End", 1: "FY2025 Q1 (trough)", 2: "FY2025 Q2", 3: "FY2025 Q3", 4: "FY2025 Q4/Year-End"}
r = hdr + 1
for i, (as_of, val, accession) in enumerate(quarterly_cash):
    ws_q.cell(row=r, column=1, value=as_of).font = LABEL_FONT
    ws_q.cell(row=r, column=2, value=val).number_format = USD_FMT
    ws_q.cell(row=r, column=3, value=accession).font = LABEL_FONT
    ws_q.cell(row=r, column=4, value=period_labels.get(i, "")).font = LABEL_FONT
    for cc in range(1, 5):
        ws_q.cell(row=r, column=cc).border = BORDER
    r += 1
trough = min(v for _, v, _ in quarterly_cash[1:])
year_end = quarterly_cash[-1][1]
ws_q.cell(row=r + 1, column=1, value="Trough / Year-End Ratio").font = BOLD_FONT
ws_q.cell(row=r + 1, column=2, value=trough / year_end).number_format = "0.0%"
ws_q.freeze_panes = "A5"
ws_q.sheet_view.showGridLines = False
print("Quarterly Cash Proof sheet written")

# ============================================================================
# Sheet 2: Executive Summary (built after 3/4/5 so it can be moved to
# position 2 in the final reorder; content only depends on Python objects)
# ============================================================================
ws_es = wb.create_sheet("Executive Summary")
set_col_widths(ws_es, {"A": 30, "B": 16, "C": 16, "D": 16})
style_title(ws_es, "A1:D1", "Executive Summary")
ws_es.merge_cells("A2:D2")
ws_es["A2"] = ("Scenario-based model. NOT investment advice, a price target, or a prediction. "
               "See Sheet 15 for limitations.")
ws_es["A2"].font = Font(italic=True, size=10, color="C00000")

hdr = 4
for j, h in enumerate(["Metric (FY2030 unless noted)", "Base", "Upside", "Downside"]):
    ws_es.cell(row=hdr, column=1 + j, value=h)
style_header_row(ws_es, hdr, 1, 4)

EXEC_ROWS = [
    ("Revenue ($M)", lambda y, ty: y.revenue, USD_FMT),
    ("Net Income ($M)", lambda y, ty: y.net_income, USD_FMT),
    ("Diluted EPS ($)", lambda y, ty: y.diluted_eps, "$0.00"),
    ("CFO ($M)", lambda y, ty: y.operating_cash_flow, USD_FMT),
    ("FCF ($M)", lambda y, ty: y.free_cash_flow, USD_FMT),
]
r = hdr + 1
for label, getter, fmt in EXEC_ROWS:
    ws_es.cell(row=r, column=1, value=label).font = LABEL_FONT
    for j, scenario in enumerate(f.SCENARIOS):
        val = getter(forecasts[scenario][-1], capacity_taxonomies[scenario][-1])
        cell = ws_es.cell(row=r, column=2 + j, value=round(val, 2))
        cell.number_format = fmt
        cell.border = BORDER
    r += 1

r += 1
ws_es.cell(row=r, column=1, value="Corrected Capacity Taxonomy (FY2030) -- see Sheet 9 for full detail").font = Font(bold=True, color="1F3864")
r += 1
CAPACITY_EXEC_ROWS = [
    ("Opening Excess Liquidity ($M, a STOCK -- never 'generated')", lambda ty: ty.opening_excess_liquidity, USD_FMT),
    ("Self-Funded Capacity Generated ($M)", lambda ty: ty.self_funded_capacity_generated, USD_FMT),
    ("Debt-Funded Capacity ($M, net of repayment)", lambda ty: ty.debt_funded_incremental_capacity, USD_FMT),
    ("Discretionary Deployment ($M)", lambda ty: ty.total_discretionary_deployment, USD_FMT),
    ("Remaining Deployable Headroom ($M)", lambda ty: ty.remaining_deployable_headroom, USD_FMT),
]
for label, getter, fmt in CAPACITY_EXEC_ROWS:
    ws_es.cell(row=r, column=1, value=label).font = BOLD_FONT
    for j, scenario in enumerate(f.SCENARIOS):
        val = getter(capacity_taxonomies[scenario][-1])
        cell = ws_es.cell(row=r, column=2 + j, value=round(val, 2))
        cell.number_format = fmt
        cell.font = BOLD_FONT
        cell.border = BORDER
    r += 1
r += 1
ws_es.merge_cells(f"A{r}:D{r}")
ws_es.cell(row=r, column=1,
           value="Note: a higher-revenue scenario can show LOWER remaining headroom -- it may be "
                 "deploying far more into buybacks/deleveraging (Upside), not generating less. See the "
                 "FY2030 scenario bridges in docs/investment_capacity_correction_evidence.md and Sheet 9.")
ws_es.cell(row=r, column=1).font = Font(italic=True, size=9, color="C00000")
ws_es.cell(row=r, column=1).alignment = Alignment(wrap_text=True)
ws_es.row_dimensions[r].height = 28
r += 1
ws_es.cell(row=r, column=1, value="Implied DCF Value/Share ($)").font = BOLD_FONT
for j, scenario in enumerate(f.SCENARIOS):
    cell = ws_es.cell(row=r, column=2 + j, value=round(dcf_results[scenario].implied_value_per_share, 2))
    cell.number_format = "$0.00"
    cell.font = BOLD_FONT
    cell.border = BORDER
r += 2

ws_es.cell(row=r, column=1, value="Key question answered:").font = BOLD_FONT
r += 1
ws_es.merge_cells(f"A{r}:D{r}")
ws_es.cell(row=r, column=1,
           value="How much capital can Target safely deploy after funding operations, CapEx, dividends, "
                 "minimum liquidity, and debt obligations? -- see Sheet 9 (Investment Capacity) for the "
                 "full FY2026-FY2030 build for the selected scenario.")
ws_es.cell(row=r, column=1).alignment = Alignment(wrap_text=True)
ws_es.row_dimensions[r].height = 30

# Chart: remaining deployable headroom by scenario (FY2030) -- corrected metric
chart_data_row = r + 2
ws_es.cell(row=chart_data_row, column=1, value="Scenario")
ws_es.cell(row=chart_data_row, column=2, value="Remaining Deployable Headroom, FY2030 ($M)")
for j, scenario in enumerate(f.SCENARIOS):
    ws_es.cell(row=chart_data_row + 1 + j, column=1, value=scenario.capitalize())
    ws_es.cell(row=chart_data_row + 1 + j, column=2, value=round(capacity_taxonomies[scenario][-1].remaining_deployable_headroom, 1))
chart = BarChart()
chart.title = "FY2030 Remaining Deployable Headroom by Scenario"
chart.y_axis.title = "$M"
data = Reference(ws_es, min_col=2, min_row=chart_data_row, max_row=chart_data_row + 3)
cats = Reference(ws_es, min_col=1, min_row=chart_data_row + 1, max_row=chart_data_row + 3)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
chart.width, chart.height = 14, 8
ws_es.add_chart(chart, f"F{hdr}")
ws_es.sheet_view.showGridLines = False
ws_es.print_area = "A1:D" + str(r)
print("Executive Summary sheet written")

# ============================================================================
# Sheet 12: Sensitivities (static dry-run tables)
# ============================================================================
ws_s = wb.create_sheet("Sensitivities")
set_col_widths(ws_s, {"A": 30})
for col in "BCDEFG":
    ws_s.column_dimensions[col].width = 14
style_title(ws_s, "A1:G1", "Sensitivities (Static Dry-Run Output)")
r = 3
for driver, rows in sensitivity.items():
    ws_s.cell(row=r, column=1, value=f"Driver: {driver} (Base scenario, FY2030 impact)").font = BOLD_FONT
    r += 1
    headers = ["Delta", "CFO", "FCF", "Ending Cash", "Legacy Gross Capacity (DEPRECATED)", "Legacy Cumulative (DEPRECATED)"]
    for j, h in enumerate(headers):
        ws_s.cell(row=r, column=1 + j, value=h)
    style_header_row(ws_s, r, 1, 6)
    r += 1
    for row in rows:
        ws_s.cell(row=r, column=1, value=row["delta"])
        ws_s.cell(row=r, column=2, value=row["operating_cash_flow"]).number_format = USD_FMT
        ws_s.cell(row=r, column=3, value=row["free_cash_flow"]).number_format = USD_FMT
        ws_s.cell(row=r, column=4, value=row["ending_cash"]).number_format = USD_FMT
        ws_s.cell(row=r, column=5, value=row["deployable_capacity"]).number_format = USD_FMT
        ws_s.cell(row=r, column=6, value=row["cumulative_deployable_capacity_2026_2030"]).number_format = USD_FMT
        for cc in range(1, 7):
            ws_s.cell(row=r, column=cc).border = BORDER
        r += 1
    r += 1

ws_s.cell(row=r, column=1, value="Two-Variable: Revenue Growth x Gross Margin (FY2030 Legacy Gross Capacity, DEPRECATED)").font = BOLD_FONT
r += 1
ws_s.cell(row=r, column=1, value="Growth\\Margin")
for j, cell_ in enumerate(two_var["grid"][0]["cells"]):
    ws_s.cell(row=r, column=2 + j, value=cell_["driver2_delta"])
style_header_row(ws_s, r, 1, 1 + len(two_var["grid"][0]["cells"]))
r += 1
for row in two_var["grid"]:
    ws_s.cell(row=r, column=1, value=row["driver1_delta"])
    for j, cell_ in enumerate(row["cells"]):
        ws_s.cell(row=r, column=2 + j, value=cell_["fy2030_deployable_capacity"]).number_format = USD_FMT
        ws_s.cell(row=r, column=2 + j).border = BORDER
    r += 1
r += 2

ws_s.cell(row=r, column=1, value="DCF: WACC x Terminal Growth (Implied Value/Share)").font = BOLD_FONT
r += 1
ws_s.cell(row=r, column=1, value="WACC\\Growth")
for j, cell_ in enumerate(wacc_grid["grid"][0]["cells"]):
    ws_s.cell(row=r, column=2 + j, value=cell_["growth_delta"])
style_header_row(ws_s, r, 1, 1 + len(wacc_grid["grid"][0]["cells"]))
r += 1
for row in wacc_grid["grid"]:
    ws_s.cell(row=r, column=1, value=round(row["wacc_pct"], 2))
    for j, cell_ in enumerate(row["cells"]):
        val = cell_["implied_value_per_share"]
        ws_s.cell(row=r, column=2 + j, value=round(val, 2) if val is not None else "n/a").number_format = "$0.00"
        ws_s.cell(row=r, column=2 + j).border = BORDER
    r += 1
r += 2

ws_s.cell(row=r, column=1, value="DCF: Gross Margin x Revenue Growth (Implied Value/Share)").font = BOLD_FONT
r += 1
ws_s.cell(row=r, column=1, value="Margin\\Growth")
for j, cell_ in enumerate(margin_growth_grid["grid"][0]["cells"]):
    ws_s.cell(row=r, column=2 + j, value=cell_["revenue_growth_delta"])
style_header_row(ws_s, r, 1, 1 + len(margin_growth_grid["grid"][0]["cells"]))
r += 1
for row in margin_growth_grid["grid"]:
    ws_s.cell(row=r, column=1, value=row["gross_margin_delta"])
    for j, cell_ in enumerate(row["cells"]):
        ws_s.cell(row=r, column=2 + j, value=round(cell_["implied_value_per_share"], 2)).number_format = "$0.00"
        ws_s.cell(row=r, column=2 + j).border = BORDER
    r += 1
ws_s.sheet_view.showGridLines = False
print("Sensitivities sheet written")

# ============================================================================
# Sheet 13: Source & Lineage
# ============================================================================
import csv
with open("docs/sources.csv", newline="") as fh:
    sources = list(csv.DictReader(fh))
ws_src = wb.create_sheet("Source & Lineage")
set_col_widths(ws_src, {"A": 22, "B": 10, "C": 16, "D": 14})
style_title(ws_src, "A1:D1", "Source & Lineage")
ws_src["A3"] = f"Forecast information cutoff: {f.FORECAST_INFORMATION_CUTOFF} (accession {f.FORECAST_INFORMATION_CUTOFF_ACCESSION})"
ws_src["A3"].font = BOLD_FONT
hdr = 5
for j, h in enumerate(["Accession", "Form", "Period of Report", "Filed At"]):
    ws_src.cell(row=hdr, column=1 + j, value=h)
style_header_row(ws_src, hdr, 1, 4)
r = hdr + 1
for s in sorted(sources, key=lambda x: x["filed_at"]):
    ws_src.cell(row=r, column=1, value=s["accession_number"]).font = LABEL_FONT
    ws_src.cell(row=r, column=2, value=s["form_type"]).font = LABEL_FONT
    ws_src.cell(row=r, column=3, value=s["period_of_report"]).font = LABEL_FONT
    ws_src.cell(row=r, column=4, value=s["filed_at"]).font = LABEL_FONT
    for cc in range(1, 5):
        ws_src.cell(row=r, column=cc).border = BORDER
    r += 1
r += 2
ws_src.merge_cells(f"A{r}:D{r}")
ws_src.cell(row=r, column=1,
            value="Lineage: every forecast fact traces to a historical annual_facts anchor, a prior "
                  "forecast fact, or a forecast_assumptions row (1,533 forecast_lineage rows persisted; "
                  "see docs/milestone_3_forecast_schema_proposal.md and the forecast_lineage table).")
ws_src.cell(row=r, column=1).font = NOTE_FONT
ws_src.cell(row=r, column=1).alignment = Alignment(wrap_text=True)
ws_src.sheet_view.showGridLines = False
print("Source & Lineage sheet written")

# ============================================================================
# Sheet 14: Validation Summary
# ============================================================================
ws_val = wb.create_sheet("Validation Summary")
set_col_widths(ws_val, {"A": 40, "B": 10, "C": 10, "D": 10, "E": 10})
style_title(ws_val, "A1:E1", "Validation Summary")
ws_val["A3"] = "Forecast Engine: 21 named checks"
ws_val["A3"].font = BOLD_FONT
hdr = 4
for j, h in enumerate(["Check", "Rows", "PASS", "FAIL", "WARNING"]):
    ws_val.cell(row=hdr, column=1 + j, value=h)
style_header_row(ws_val, hdr, 1, 5)
from collections import Counter, defaultdict
by_check = defaultdict(list)
for res in validation_results:
    by_check[res.check_name].append(res)
r = hdr + 1
for name in sorted(f.VALIDATION_CHECK_METADATA.keys()):
    rows = by_check.get(name, [])
    c = Counter(x.status for x in rows)
    ws_val.cell(row=r, column=1, value=name).font = LABEL_FONT
    ws_val.cell(row=r, column=2, value=len(rows))
    ws_val.cell(row=r, column=3, value=c.get("PASS", 0))
    ws_val.cell(row=r, column=4, value=c.get("FAIL", 0))
    ws_val.cell(row=r, column=5, value=c.get("WARNING", 0))
    for cc in range(1, 6):
        ws_val.cell(row=r, column=cc).border = BORDER
    r += 1
total_fails = sum(1 for x in validation_results if x.status == "FAIL")
ws_val.cell(row=r + 1, column=1, value=f"TOTAL: {len(validation_results)} results, {total_fails} failures").font = BOLD_FONT

r += 3
ws_val.cell(row=r, column=1, value="DCF Valuation: 6 named checks").font = BOLD_FONT
r += 1
for j, h in enumerate(["Check", "Rows", "PASS", "FAIL"]):
    ws_val.cell(row=r, column=1 + j, value=h)
style_header_row(ws_val, r, 1, 4)
r += 1
by_vcheck = defaultdict(list)
for c in val_checks:
    by_vcheck[c.check_name].append(c)
for name, rows in by_vcheck.items():
    cnt = Counter(x.status for x in rows)
    ws_val.cell(row=r, column=1, value=name).font = LABEL_FONT
    ws_val.cell(row=r, column=2, value=len(rows))
    ws_val.cell(row=r, column=3, value=cnt.get("PASS", 0))
    ws_val.cell(row=r, column=4, value=cnt.get("FAIL", 0))
    for cc in range(1, 5):
        ws_val.cell(row=r, column=cc).border = BORDER
    r += 1
val_fails = sum(1 for x in val_checks if x.status == "FAIL")
ws_val.cell(row=r + 1, column=1, value=f"TOTAL: {len(val_checks)} results, {val_fails} failures").font = BOLD_FONT

r += 3
ws_val.cell(row=r, column=1, value=f"Corrected Capacity Taxonomy (Milestone 9 v2 correction): {len(ct.CAPACITY_CHECK_METADATA)} named checks").font = BOLD_FONT
r += 1
for j, h in enumerate(["Check", "Rows", "PASS", "FAIL", "WARNING"]):
    ws_val.cell(row=r, column=1 + j, value=h)
style_header_row(ws_val, r, 1, 5)
r += 1
capacity_validation_results = ct.validate_capacity_taxonomy_all(forecasts, capacity_taxonomies, capacity_summaries)
by_cap_check = defaultdict(list)
for res in capacity_validation_results:
    by_cap_check[res.check_name].append(res)
for name in sorted(ct.CAPACITY_CHECK_METADATA.keys()):
    rows = by_cap_check.get(name, [])
    c = Counter(x.status for x in rows)
    ws_val.cell(row=r, column=1, value=name).font = LABEL_FONT
    ws_val.cell(row=r, column=2, value=len(rows))
    ws_val.cell(row=r, column=3, value=c.get("PASS", 0))
    ws_val.cell(row=r, column=4, value=c.get("FAIL", 0))
    ws_val.cell(row=r, column=5, value=c.get("WARNING", 0))
    for cc in range(1, 6):
        ws_val.cell(row=r, column=cc).border = BORDER
    r += 1
cap_fails = sum(1 for x in capacity_validation_results if x.status == "FAIL")
ws_val.cell(row=r + 1, column=1,
            value=f"TOTAL: {len(capacity_validation_results)} results, {cap_fails} failures "
                  "(7 further structural/definitional proofs live in tests/unit/test_capacity_taxonomy.py)"
            ).font = BOLD_FONT

ws_val.sheet_view.showGridLines = False
print("Validation Summary sheet written")

# ============================================================================
# Sheet 15: Limitations
# ============================================================================
ws_lim = wb.create_sheet("Limitations")
set_col_widths(ws_lim, {"A": 100})
style_title(ws_lim, "A1:A1", "Limitations")
LIMITATIONS = [
    "investing_cash_flow is modeled as exactly -CapEx; no driver exists for other historical investing items.",
    "No FX translation effect is modeled (implicitly zero).",
    "The near-term debt repayment reserve is proxied by each year's own fixed repayment assumption -- no "
    "disclosed maturity ladder exists.",
    "'Other operating cash adjustments' is a single flat scenario assumption, not decomposed into "
    "stock-comp/deferred-tax/other sub-components.",
    "The seasonality stress overlay is grounded in exactly ONE year of real quarterly evidence (FY2025).",
    "The minimum-cash-buffer comparison evaluates 5 policies but endorses none as final.",
    "DCF WACC components (risk-free rate, equity risk premium, beta) are illustrative, general-market "
    "inputs -- no live market-data source is in the registered source set.",
    "DCF capital-structure weights are a target/policy split, not a market-value weight (which would "
    "require the market value of equity -- circular with the equity value being estimated).",
    "This workbook is a scenario-based model, NOT investment advice, a price target, or a prediction of "
    "Target's actual future results or stock price.",
    "CapEx is modeled as a % of revenue with no maintenance-vs-growth split, since Target discloses no "
    "such split.",
    "Dividends are modeled via a $/share growth proxy, not a disclosed per-share dividend policy statement.",
    "No information after the FY2025 10-K cutoff (2026-03-11) is used anywhere in this workbook.",
    "Milestone 9 correction: the original 'DEPLOYABLE CAPACITY' headline (Sheet 9) was found to be "
    "arithmetically correct but economically ambiguous -- a gross, pre-discretionary ceiling that never "
    "subtracted that year's own repurchases. It is preserved, relabeled and deprecated, on Sheet 9 for "
    "backward compatibility; the corrected taxonomy (Self-Funded / Debt-Funded / Discretionary Deployment "
    "/ Remaining Deployable Headroom) on Sheets 2 and 9 is now the executive-facing figure. See "
    "docs/investment_capacity_semantic_audit.md and docs/investment_capacity_correction_evidence.md.",
    "strategic_investment, voluntary_debt_reduction, and other_discretionary_uses in the corrected "
    "taxonomy are structural $0 placeholders -- no policy lever for them has been modeled this round, "
    "following the same convention already established for management_selected_deployment.",
    "v2 finance-semantics correction: debt_funded_incremental_capacity previously equaled gross debt "
    "proceeds, mislabeling capacity even when the same cash was simultaneously repaid. It is now the NET "
    "of proceeds over repayments; the offsetting net_mandatory_debt_service is subtracted from "
    "self_funded_capacity_generated, which now excludes opening_excess_liquidity entirely (a stock is "
    "never labeled 'generated'). Remaining Deployable Headroom now also deducts a forward "
    "debt-repayment reserve, proxied for the terminal FY2030 year since FY2031 is outside the forecast "
    "horizon. See docs/investment_capacity_correction_evidence.md.",
]
r = 3
for lim in LIMITATIONS:
    ws_lim.cell(row=r, column=1, value=f"- {lim}").alignment = Alignment(wrap_text=True)
    ws_lim.row_dimensions[r].height = 30
    r += 1
ws_lim.sheet_view.showGridLines = False
print("Limitations sheet written")

# ============================================================================
# Final: reorder sheets, freeze panes already set, save
# ============================================================================
DESIRED_ORDER = [
    "Cover & Instructions", "Executive Summary", "Historical Financials", "Filing-Vintage Comparison",
    "Quarterly Cash Proof", "Forecast Assumptions", "Scenario Forecast", "Cash-Flow Bridge",
    "Investment Capacity", "Capital Allocation", "DCF Valuation", "Sensitivities", "Source & Lineage",
    "Validation Summary", "Limitations",
]
wb._sheets = [wb[name] for name in DESIRED_ORDER]
for name in DESIRED_ORDER:
    wb[name].sheet_properties.tabColor = NAVY
wb.active = 0

import os
os.makedirs("deliverables", exist_ok=True)
wb.save(OUT_PATH)
print("Saved:", OUT_PATH)
print("Sheet order:", wb.sheetnames)
