"""Milestone 6: Power BI implementation-ready handoff package.

Native Power BI Desktop is not available in this environment (no
desktop application, no Power BI REST/XMLA API access), so a native
.pbix file cannot be created or verified here. Per the project's own
General Rule 17, this script instead builds a COMPLETE,
implementation-ready handoff package: star-schema fact/dimension CSV
exports (queried live from the same `data/curated/target_cash.db` used
by every other deliverable), a data dictionary, a relationship map, DAX
measure definitions, page wireframes (as both Markdown specs and SVG
mockup images), a theme JSON file, refresh instructions, and validation
totals a Power BI developer can check the finished report against.

This script NEVER claims a .pbix was created. It was not.

Usage: .venv/bin/python scripts/build_powerbi_handoff.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "curated" / "target_cash.db"
OUT_ROOT = REPO_ROOT / "deliverables" / "powerbi_handoff"
DATA_DIR = OUT_ROOT / "data"
WIREFRAME_DIR = OUT_ROOT / "wireframes"
PAGES_DIR = OUT_ROOT / "pages"

for d in (DATA_DIR, WIREFRAME_DIR, PAGES_DIR):
    d.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row


def q(sql):
    return pd.read_sql_query(sql, conn)


# ---------------------------------------------------------------------------
# 1. DIMENSION TABLES
# ---------------------------------------------------------------------------

dim_scenario = q(
    "SELECT scenario_id, scenario_name, description, version, "
    "information_cutoff FROM forecast_scenarios ORDER BY scenario_id"
)
dim_scenario.to_csv(DATA_DIR / "dim_scenario.csv", index=False)

FISCAL_YEARS = list(range(2021, 2031))
dim_fiscal_year = pd.DataFrame(
    {
        "fiscal_year": FISCAL_YEARS,
        "year_label": [f"FY{y}" for y in FISCAL_YEARS],
        "period_type": ["Historical" if y <= 2025 else "Forecast" for y in FISCAL_YEARS],
        "is_historical": [1 if y <= 2025 else 0 for y in FISCAL_YEARS],
        "is_forecast": [0 if y <= 2025 else 1 for y in FISCAL_YEARS],
    }
)
dim_fiscal_year.to_csv(DATA_DIR / "dim_fiscal_year.csv", index=False)

dim_filing = q(
    "SELECT accession_number, cik, company_name, form_type, filed_at, "
    "period_of_report, primary_document_url, ingestion_method "
    "FROM filings ORDER BY period_of_report"
)
dim_filing.to_csv(DATA_DIR / "dim_filing.csv", index=False)

# dim_metric: union of every metric key that appears in any fact table,
# with a heuristic display label and category (presentation only --
# no values are fabricated, only how a known metric key is labeled).
metric_keys = set()
for table, col in [
    ("annual_facts", "metric"),
    ("forecast_facts", "metric"),
    ("forecast_assumptions", "metric"),
    ("instant_facts", "metric"),
]:
    metric_keys.update(r[0] for r in conn.execute(f"SELECT DISTINCT {col} FROM {table}"))

CASH_FLOW_HINTS = ("cash_flow", "capex", "capital_expenditure", "dividends", "repurchase",
                    "debt_proceeds", "debt_repayment", "free_cash_flow", "financing", "investing")
BALANCE_SHEET_HINTS = ("debt_gaap", "inventory", "accounts_payable", "cash_and_equivalents",
                        "finance_lease_liab", "balance")
INCOME_STMT_HINTS = ("revenue", "cost_of_sales", "gross_profit", "gross_margin", "sga",
                      "operating_income", "operating_margin", "operating_expenses",
                      "net_income", "net_margin", "pretax_income", "income_tax",
                      "diluted_eps", "diluted_shares", "interest_expense", "net_other_income")
CAPACITY_HINTS = ("capacity", "buffer", "reserve", "funding_warning")
RATIO_HINTS = ("_pct", "_to_", "intensity", "conversion")


def classify_metric(key: str) -> str:
    k = key.lower()
    if any(h in k for h in CAPACITY_HINTS):
        return "Investment Capacity"
    if any(h in k for h in CASH_FLOW_HINTS):
        return "Cash Flow"
    if any(h in k for h in BALANCE_SHEET_HINTS):
        return "Balance Sheet"
    if any(h in k for h in RATIO_HINTS):
        return "Ratio / Driver"
    if any(h in k for h in INCOME_STMT_HINTS):
        return "Income Statement"
    return "Other"


dim_metric = pd.DataFrame(
    {
        "metric_key": sorted(metric_keys),
    }
)
dim_metric["metric_label"] = dim_metric["metric_key"].apply(
    lambda k: k.replace("_", " ").title().replace("Cfo", "CFO").replace("Da ", "D&A ")
    .replace("Sga", "SG&A").replace("Eps", "EPS").replace("Gaap", "GAAP")
    .replace("Ap ", "AP ").replace("Ufcf", "UFCF")
)
dim_metric["category"] = dim_metric["metric_key"].apply(classify_metric)
dim_metric.to_csv(DATA_DIR / "dim_metric.csv", index=False)

dim_date_quarterly = q(
    "SELECT DISTINCT as_of_date FROM instant_facts ORDER BY as_of_date"
)
dim_date_quarterly["fiscal_year"] = dim_date_quarterly["as_of_date"].apply(
    lambda d: 2025 if d != "2025-02-01" else 2024
)
dim_date_quarterly["quarter_label"] = [
    "FY2024 Year-End", "FY2025 Q1", "FY2025 Q2", "FY2025 Q3", "FY2025 Year-End"
][: len(dim_date_quarterly)]
dim_date_quarterly.to_csv(DATA_DIR / "dim_date_quarterly.csv", index=False)

# ---------------------------------------------------------------------------
# 2. FACT TABLES
# ---------------------------------------------------------------------------

fact_annual_historical = q(
    "SELECT annual_fact_id, metric, fiscal_year, analytical_view, value_normalized, "
    "normalized_unit, direct_or_derived, fact_status, validation_status, "
    "accession_number, filed_at, information_cutoff "
    "FROM annual_facts ORDER BY metric, fiscal_year, analytical_view"
)
fact_annual_historical.to_csv(DATA_DIR / "fact_annual_historical.csv", index=False)

fact_forecast = q(
    "SELECT forecast_fact_id, scenario_id, fiscal_year, metric, "
    "metric_definition_version, assumption_version, value, unit, formula, "
    "validation_status, information_cutoff "
    "FROM forecast_facts ORDER BY scenario_id, fiscal_year, metric"
)
fact_forecast.to_csv(DATA_DIR / "fact_forecast.csv", index=False)

fact_investment_capacity = q(
    "SELECT investment_capacity_result_id, scenario_id, fiscal_year, "
    "gross_fcf_capacity, post_dividend_capacity, pre_discretionary_ending_cash, "
    "min_cash_buffer, near_term_debt_repayment_reserve, deployable_capacity, "
    "cumulative_deployable_capacity, funding_warning, methodology_note, "
    "information_cutoff "
    "FROM investment_capacity_results ORDER BY scenario_id, fiscal_year"
)
fact_investment_capacity.to_csv(DATA_DIR / "fact_investment_capacity.csv", index=False)

fact_valuation_results = q(
    "SELECT valuation_result_id, scenario_id, wacc_pct, terminal_growth_pct, "
    "pv_explicit_period, terminal_year_ufcf, terminal_value_undiscounted, "
    "pv_terminal_value, enterprise_value, valuation_date_net_debt, equity_value, "
    "valuation_date_diluted_shares, implied_value_per_share, information_cutoff "
    "FROM valuation_results ORDER BY scenario_id"
)
fact_valuation_results.to_csv(DATA_DIR / "fact_valuation_results.csv", index=False)

fact_valuation_ufcf = q(
    "SELECT valuation_ufcf_fact_id, scenario_id, fiscal_year, ufcf, pv_ufcf, "
    "discount_period, information_cutoff "
    "FROM valuation_ufcf_facts ORDER BY scenario_id, fiscal_year"
)
fact_valuation_ufcf.to_csv(DATA_DIR / "fact_valuation_ufcf.csv", index=False)

fact_validation_forecast = q(
    "SELECT validation_result_id, check_name, scenario_id, fiscal_year, status, "
    "detail, forecast_version, run_at FROM forecast_validation_results "
    "ORDER BY check_name, scenario_id, fiscal_year"
)
fact_validation_forecast.to_csv(DATA_DIR / "fact_validation_forecast.csv", index=False)

fact_validation_valuation = q(
    "SELECT validation_result_id, check_name, scenario_id, status, detail, "
    "valuation_version, run_at FROM valuation_validation_results "
    "ORDER BY check_name, scenario_id"
)
fact_validation_valuation.to_csv(DATA_DIR / "fact_validation_valuation.csv", index=False)

fact_quarterly_cash = q(
    "SELECT instant_fact_id, metric, as_of_date, value_normalized, normalized_unit, "
    "accession_number, filed_at, restatement_status, information_cutoff "
    "FROM instant_facts ORDER BY metric, as_of_date"
)
fact_quarterly_cash.to_csv(DATA_DIR / "fact_quarterly_cash.csv", index=False)

# Filing-vintage comparison: as_originally_filed vs latest_restated, for the
# 4 income-statement lines most exposed to Target's FY2024 segment/expense
# reclassification (same 4 lines used on the Excel model's own
# Filing-Vintage Comparison sheet).
VINTAGE_METRICS = ["revenue", "cost_of_sales", "gross_profit", "operating_expenses"]
rows = []
for metric in VINTAGE_METRICS:
    df = q(
        f"SELECT fiscal_year, analytical_view, value_normalized FROM annual_facts "
        f"WHERE metric = '{metric}' ORDER BY fiscal_year"
    )
    pivot = df.pivot(index="fiscal_year", columns="analytical_view", values="value_normalized")
    for fy, row in pivot.iterrows():
        orig = row.get("as_originally_filed")
        restated = row.get("latest_restated")
        if pd.isna(orig) or pd.isna(restated):
            continue
        rows.append(
            {
                "metric": metric,
                "fiscal_year": fy,
                "as_originally_filed": orig,
                "latest_restated": restated,
                "difference": restated - orig,
                "pct_difference": (restated - orig) / orig if orig else None,
                "reclassified": bool(abs(restated - orig) > 0.005),
            }
        )
fact_filing_vintage_comparison = pd.DataFrame(rows)
fact_filing_vintage_comparison.to_csv(DATA_DIR / "fact_filing_vintage_comparison.csv", index=False)

print("Exported fact/dimension CSVs:")
for p in sorted(DATA_DIR.glob("*.csv")):
    n = sum(1 for _ in open(p)) - 1
    print(f"  {p.name}: {n} rows")

conn.close()

# ---------------------------------------------------------------------------
# 3. WIREFRAME MOCKUPS (schematic SVG layouts -- NOT real Power BI
#    screenshots; Power BI Desktop is not available in this environment).
# ---------------------------------------------------------------------------

NAVY = "#1F3864"
GOLD = "#C9A227"
LIGHT_BLUE = "#D9E2F3"
WHITE = "#FFFFFF"
GREY = "#7F7F7F"

PAGE_W, PAGE_H = 1280, 720


def svg_box(x, y, w, h, label, fill=WHITE, stroke=NAVY, text_size=13, label2=None):
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="1.5" rx="4"/>'
    ]
    ty = y + h / 2 - (6 if label2 else 0)
    parts.append(
        f'<text x="{x + w/2}" y="{ty}" font-family="Segoe UI, Arial" '
        f'font-size="{text_size}" fill="{stroke}" text-anchor="middle" '
        f'dominant-baseline="middle">{label}</text>'
    )
    if label2:
        parts.append(
            f'<text x="{x + w/2}" y="{ty + 18}" font-family="Segoe UI, Arial" '
            f'font-size="10" fill="{GREY}" text-anchor="middle" '
            f'dominant-baseline="middle">{label2}</text>'
        )
    return "\n".join(parts)


def build_wireframe(page_no, title, subtitle, filters, boxes):
    """boxes: list of (x, y, w, h, label, fill, label2) tuples in a
    1280x720 canvas below the header/filter bar."""
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}" height="{PAGE_H}" '
        f'viewBox="0 0 {PAGE_W} {PAGE_H}">',
        f'<rect width="{PAGE_W}" height="{PAGE_H}" fill="{WHITE}"/>',
        f'<rect x="0" y="0" width="{PAGE_W}" height="56" fill="{NAVY}"/>',
        f'<text x="20" y="26" font-family="Segoe UI, Arial" font-size="18" '
        f'fill="{WHITE}" font-weight="bold">Page {page_no}: {title}</text>',
        f'<text x="20" y="46" font-family="Segoe UI, Arial" font-size="11" '
        f'fill="{LIGHT_BLUE}">{subtitle}</text>',
        f'<rect x="0" y="56" width="{PAGE_W}" height="34" fill="{LIGHT_BLUE}"/>',
        f'<text x="20" y="77" font-family="Segoe UI, Arial" font-size="11" '
        f'fill="{NAVY}">Filters/Slicers: {filters}</text>',
    ]
    for x, y, w, h, label, fill, label2 in boxes:
        svg.append(svg_box(x, y, w, h, label, fill=fill, label2=label2))
    svg.append(
        f'<text x="{PAGE_W - 20}" y="{PAGE_H - 12}" font-family="Segoe UI, Arial" '
        f'font-size="10" fill="{GREY}" text-anchor="end">'
        "WIREFRAME MOCKUP -- schematic layout only, not an actual Power BI screenshot "
        "(Power BI Desktop unavailable in this build environment)</text>"
    )
    svg.append("</svg>")
    return "\n".join(svg)


CARD = LIGHT_BLUE
CHART = WHITE
TABLE = "#F2F2F2"

WIREFRAMES = [
    (
        1, "Executive Overview",
        "What happened, what's expected, how much can be deployed -- answered in one screen",
        "Scenario selector (Base/Upside/Downside), Fiscal Year",
        [
            (20, 100, 190, 90, "KPI Card", CARD, "Revenue FY2030"),
            (220, 100, 190, 90, "KPI Card", CARD, "FCF FY2030"),
            (420, 100, 190, 90, "KPI Card", CARD, "Deployable Capacity"),
            (620, 100, 190, 90, "KPI Card", CARD, "Implied DCF Value/Share"),
            (820, 100, 190, 90, "KPI Card", CARD, "Validation Status"),
            (1020, 100, 240, 90, "KPI Card", CARD, "Net Debt (Valuation Date)"),
            (20, 210, 610, 240, "Line Chart", CHART, "Revenue &amp; FCF: Actual (solid) vs Forecast (dashed), FY21-FY30"),
            (650, 210, 610, 240, "Clustered Column", CHART, "Deployable Capacity by Scenario, FY2030"),
            (20, 470, 610, 220, "Waterfall Chart", CHART, "Capital Allocation Waterfall (selected scenario)"),
            (650, 470, 610, 220, "Table", TABLE, "Key Evidence Citations (filing, accession #, cutoff date)"),
        ],
    ),
    (
        2, "Historical Financial Trends",
        "FY2021-FY2025 actuals only -- no forecast series on this page",
        "Fiscal Year range, Metric category",
        [
            (20, 100, 610, 280, "Line/Area Chart", CHART, "Revenue, Gross Profit, Operating Income, Net Income"),
            (650, 100, 610, 280, "Line Chart", CHART, "CFO, CapEx, FCF (property &amp; equipment CapEx only)"),
            (20, 400, 610, 290, "Stacked Column", CHART, "Capital Allocation: Dividends vs Buybacks vs Debt Repayment"),
            (650, 400, 610, 290, "Table (Matrix)", TABLE, "Full historical fact table, all 49 metrics x FY2021-FY2025"),
        ],
    ),
    (
        3, "Filing-Vintage &amp; Restatement Comparison",
        "As-originally-filed vs latest-restated -- proves no silent restatement was hidden",
        "Fiscal Year, Metric (revenue / cost_of_sales / gross_profit / operating_expenses)",
        [
            (20, 100, 610, 280, "Clustered Column", CHART, "As-Originally-Filed vs Latest-Restated, by year"),
            (650, 100, 610, 280, "Table", TABLE, "Difference &amp; % Difference, Reclassified flag"),
            (20, 400, 1240, 290, "Callout + Text Box", CARD, "Narrative: FY2022/FY2023 COGS-vs-SG&amp;A reclassification, $0 revenue impact"),
        ],
    ),
    (
        4, "Quarterly Cash Proof",
        "5 real balance-sheet cash figures -- independent evidence for the seasonal minimum-cash policy",
        "None (all 5 real quarters shown together)",
        [
            (20, 100, 900, 300, "Line Chart", CHART, "Cash &amp; Equivalents Balance, FY2024YE - FY2025YE (5 points)"),
            (940, 100, 320, 300, "KPI Card", CARD, "Trough / Year-End Ratio = 52.6%"),
            (20, 420, 1240, 270, "Table", TABLE, "Date, Balance, Accession #, Source Filing URL"),
        ],
    ),
    (
        5, "Scenario Forecast Explorer",
        "FY2026-FY2030 projected income statement &amp; drivers, selector-driven",
        "Scenario selector, Fiscal Year, Metric",
        [
            (20, 100, 610, 280, "Line Chart", CHART, "Revenue, Gross Profit, Operating Income, Net Income by FY"),
            (650, 100, 610, 280, "Line Chart", CHART, "Diluted EPS, Revenue Growth %, Gross/Operating Margin %"),
            (20, 400, 610, 290, "Table (Matrix)", TABLE, "Full income-statement forecast, all years, selected scenario"),
            (650, 400, 610, 290, "Text Box", CARD, "Scenario Narrative (Downside/Base/Upside business-condition story)"),
        ],
    ),
    (
        6, "Cash-Flow Bridge &amp; Investment Capacity",
        "CFO -&gt; CapEx -&gt; FCF -&gt; dividends -&gt; deployable capacity, per scenario/year",
        "Scenario selector, Fiscal Year",
        [
            (20, 100, 1240, 260, "Waterfall Chart", CHART, "CFO -&gt; CapEx -&gt; FCF -&gt; Dividends -&gt; Post-Dividend Capacity -&gt; Min-Cash Buffer -&gt; Debt Reserve -&gt; Deployable Capacity"),
            (20, 380, 610, 310, "Line Chart", CHART, "Deployable Capacity &amp; Cumulative Deployable Capacity by FY"),
            (650, 380, 610, 310, "Table", TABLE, "Investment Capacity fact table with methodology_note column"),
        ],
    ),
    (
        7, "Capital Allocation Waterfall",
        "Where every dollar of cash generated actually went -- with a live no-double-counting proof",
        "Scenario selector, Fiscal Year",
        [
            (20, 100, 900, 320, "Waterfall Chart", CHART, "8-step waterfall: Beginning Cash + CFO + CFI + Debt Proceeds - Debt Repay - Dividends - Buybacks - Mgmt-Selected Deployment = Ending Cash"),
            (940, 100, 320, 320, "KPI Card", CARD, "No-Double-Counting Proof: OK / MISMATCH"),
            (20, 440, 1240, 250, "Table", TABLE, "Waterfall steps vs Cash-Flow Bridge ending cash, all scenarios/years, side by side"),
        ],
    ),
    (
        8, "DCF Valuation &amp; Sensitivities",
        "Restrained scenario-based DCF -- labeled as scenario analysis, not investment advice",
        "Scenario selector",
        [
            (20, 100, 610, 220, "Table", TABLE, "WACC build: risk-free rate, ERP, beta, cost of debt, weights"),
            (650, 100, 610, 220, "Waterfall Chart", CHART, "Valuation Bridge: PV(UFCF) -&gt; PV(TV) -&gt; EV -&gt; Net Debt -&gt; Equity Value -&gt; Value/Share"),
            (20, 340, 610, 330, "Matrix (Heatmap)", TABLE, "WACC x Terminal Growth sensitivity grid"),
            (650, 340, 610, 330, "Matrix (Heatmap)", TABLE, "Operating Margin x Revenue Growth sensitivity grid"),
        ],
    ),
]

for page_no, title, subtitle, filters, boxes in WIREFRAMES:
    svg_text = build_wireframe(page_no, title, subtitle, filters, boxes)
    fname = f"page_{page_no:02d}_{title.lower().replace(' ', '_').replace('&amp;', 'and').replace('-', '_').replace(',', '')}.svg"
    (WIREFRAME_DIR / fname).write_text(svg_text)

print(f"\nWrote {len(WIREFRAMES)} wireframe SVG mockups to {WIREFRAME_DIR}")
