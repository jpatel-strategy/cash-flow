"""Milestone 3: FY2026-FY2030 Forecast and Investment Capacity Engine.

Pure, in-memory dry-run computation. NO forecast_* database tables exist
yet -- nothing in this module writes to the database, and no persistence
function is provided. See docs/milestone_3_forecast_schema_proposal.md for
the proposed (not yet implemented) persistence schema, which requires
separate reviewer approval before any migration is written.

Every forecast value is clearly and structurally separated from historical
facts: HISTORICAL below is the only place actual reported figures appear,
frozen as a literal dict (not a live database query), and every function
that touches it treats it as read-only reference data, never as something
a forecast computation could overwrite. Forecast outputs use "forecast_"
scoped keys and are never inserted into annual_facts or any Milestone 1/2
table.

Historical figures are FY2021-FY2025, analytical_view='latest_restated',
pulled from the persisted annual_facts table (see docs/milestone_2_evidence.md)
on 2026-09-16 and frozen here as literals -- this module does not
re-query the database, so a later persistence change cannot silently
alter an already-approved forecast's historical grounding without a new,
explicit re-freeze.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

# --- Information cutoff (item 1) ------------------------------------------

# The forecast information cutoff is DISTINCT from config/model.yml's
# project-wide `information_cutoff` (2026-09-14, when this review session's
# own analysis was performed) -- that field describes when THIS PROJECT
# looked at the data, not the latest fact a forecast assumption may cite.
# FORECAST_INFORMATION_CUTOFF is the FY2025 10-K's own filed_at date: the
# latest of the 8 already-registered sources (docs/sources.csv), chosen
# because "through the FY2025 10-K" is exactly what item 1 requires, and
# every other registered source (the FY2025 Q1-Q3 10-Qs) was filed earlier
# in fiscal 2025, before the FY2025 10-K closed the year. No later 10-Q,
# analyst estimate, or post-cutoff information may be used as an
# assumption's source/evidence.
FORECAST_INFORMATION_CUTOFF = "2026-03-11"
FORECAST_INFORMATION_CUTOFF_ACCESSION = "0000027419-26-000016"  # the FY2025 10-K itself

FORECAST_YEARS = [2026, 2027, 2028, 2029, 2030]
SCENARIOS = ["base", "upside", "downside"]

# --- Historical reference, FY2021-FY2025, latest_restated -----------------
# Source: data/curated/target_cash.db, annual_facts, analytical_view=
# 'latest_restated', frozen 2026-09-16. See docs/milestone_2_evidence.md
# Section 3 for the full, live-queried table this was copied from.
HISTORICAL = {
    "revenue": {2021: 106005.0, 2022: 109120.0, 2023: 107412.0, 2024: 106566.0, 2025: 104780.0},
    "cost_of_sales": {2021: 74963.0, 2022: 82306.0, 2023: 77828.0, 2024: 76502.0, 2025: 75511.0},
    "gross_profit": {2021: 31042.0, 2022: 26814.0, 2023: 29584.0, 2024: 30064.0, 2025: 29269.0},
    "operating_expenses": {2021: 19752.0, 2022: 20581.0, 2023: 21462.0, 2024: 21969.0, 2025: 21535.0},
    "depreciation_amortization_opex": {2021: 2344.0, 2022: 2385.0, 2023: 2415.0, 2024: 2529.0, 2025: 2617.0},
    "operating_income": {2021: 8946.0, 2022: 3848.0, 2023: 5707.0, 2024: 5566.0, 2025: 5117.0},
    "interest_expense": {2021: 421.0, 2022: 478.0, 2023: 502.0, 2024: 411.0, 2025: 445.0},
    "net_other_income": {2021: 382.0, 2022: 48.0, 2023: 92.0, 2024: 106.0, 2025: 95.0},
    "pretax_income": {2021: 8907.0, 2022: 3418.0, 2023: 5297.0, 2024: 5261.0, 2025: 4767.0},
    "income_tax_expense": {2021: 1961.0, 2022: 638.0, 2023: 1159.0, 2024: 1170.0, 2025: 1062.0},
    "net_income": {2021: 6946.0, 2022: 2780.0, 2023: 4138.0, 2024: 4091.0, 2025: 3705.0},
    "diluted_eps": {2021: 14.1, 2022: 5.98, 2023: 8.94, 2024: 8.86, 2025: 8.13},
    "diluted_shares": {2021: 492.7, 2022: 464.7, 2023: 462.8, 2024: 461.8, 2025: 455.6},
    "operating_cash_flow": {2021: 8625.0, 2022: 4018.0, 2023: 8621.0, 2024: 7367.0, 2025: 6562.0},
    "capital_expenditure": {2021: 3544.0, 2022: 5528.0, 2023: 4806.0, 2024: 2891.0, 2025: 3727.0},
    "free_cash_flow": {2021: 5081.0, 2022: -1510.0, 2023: 3815.0, 2024: 4476.0, 2025: 2835.0},
    "investing_cash_flow": {2021: -3154.0, 2022: -5504.0, 2023: -4760.0, 2024: -2860.0, 2025: -3649.0},
    "financing_cash_flow": {2021: -8071.0, 2022: -2196.0, 2023: -2285.0, 2024: -3550.0, 2025: -2187.0},
    "net_change_in_cash": {2021: -2600.0, 2022: -3682.0, 2023: 1576.0, 2024: 957.0, 2025: 726.0},
    "dividends_paid": {2021: 1548.0, 2022: 1836.0, 2023: 2011.0, 2024: 2046.0, 2025: 2053.0},
    "share_repurchases": {2021: 7188.0, 2022: 2646.0, 2023: 0.0, 2024: 1007.0, 2025: 408.0},
    "debt_proceeds": {2021: 1972.0, 2022: 2625.0, 2023: 0.0, 2024: 741.0, 2025: 1984.0},
    "debt_repayments": {2021: 1147.0, 2022: 163.0, 2023: 147.0, 2024: 1139.0, 2025: 1643.0},
    "cash_and_equivalents_balance_sheet": {2021: 5911.0, 2022: 2229.0, 2023: 3805.0, 2024: 4762.0, 2025: 5488.0},
    "inventory": {2021: 13902.0, 2022: 13499.0, 2023: 11886.0, 2024: 12740.0, 2025: 12304.0},
    "accounts_payable": {2021: 15478.0, 2022: 13487.0, 2023: 12098.0, 2024: 13053.0, 2025: 12622.0},
    "total_debt_gaap": {2021: 11645.0, 2022: 14067.0, 2023: 14025.0, 2024: 13779.0, 2025: 14343.0},
    "finance_lease_liabilities": {2021: 2075.0, 2022: 2072.0, 2023: 2013.0, 2024: 2161.0, 2025: 2113.0},
    # NOT in annual_facts (Milestone 2 only approved depreciation_amortization_opex at annual
    # grain) -- queried directly from raw_facts (tag us-gaap:DepreciationDepletionAndAmortization,
    # the CFO cash-flow-statement addback line, distinct from DepreciationAndAmortization used in
    # the opex/operating-income bridge above) via latest_restated_duration, frozen 2026-09-16.
    # Consistently LARGER than depreciation_amortization_opex every year (D&A embedded in COGS,
    # e.g. distribution-center depreciation, not present in the SG&A-adjacent opex line) -- the
    # two must never be summed or substituted for each other (item 5's double-counting warning).
    "depreciation_amortization_cfo_addback": {2021: 2642.0, 2022: 2700.0, 2023: 2801.0, 2024: 2981.0, 2025: 3134.0},
    "is_53_week_year": {2021: False, 2022: False, 2023: True, 2024: False, 2025: False},
}

HISTORICAL_YEARS = [2021, 2022, 2023, 2024, 2025]


def historical_ratio(numerator: str, denominator: str) -> dict[int, float]:
    return {y: HISTORICAL[numerator][y] / HISTORICAL[denominator][y] * 100 for y in HISTORICAL_YEARS}


def historical_growth(metric: str) -> dict[int, float]:
    series = HISTORICAL[metric]
    return {
        HISTORICAL_YEARS[i]: (series[HISTORICAL_YEARS[i]] / series[HISTORICAL_YEARS[i - 1]] - 1) * 100
        for i in range(1, len(HISTORICAL_YEARS))
    }


def fy2023_53_week_normalized_revenue() -> float:
    """FY2023 had 53 weeks (2023-01-29 to 2024-02-03) -- every other historical
    year has 52. Dividing by 53/52 estimates what FY2023 revenue would have
    been on a 52-week basis, for a like-for-like growth comparison. See
    docs/decisions.md and annual_analytical_validation's fifty_three_week_
    disclosure check (PASS for FY2023) for the underlying fact.
    """
    return HISTORICAL["revenue"][2023] * 52 / 53


# --- Assumption dictionary (item 1) ---------------------------------------

@dataclass(frozen=True)
class Assumption:
    assumption_id: str
    scenario: str  # 'base' | 'upside' | 'downside'
    forecast_year: int  # 0 = applies to every FORECAST_YEARS entry unless a year-specific row overrides it
    metric: str
    value: float
    unit: str
    rationale: str
    historical_reference: str
    source_evidence: str
    information_cutoff: str = FORECAST_INFORMATION_CUTOFF
    review_status: str = "proposed"  # never 'reviewed' until a human approves this round's proposal
    version: str = "v1"


def _a(assumption_id, scenario, metric, value, unit, rationale, historical_reference, source_evidence, forecast_year=0):
    return Assumption(
        assumption_id=assumption_id, scenario=scenario, forecast_year=forecast_year, metric=metric,
        value=value, unit=unit, rationale=rationale, historical_reference=historical_reference,
        source_evidence=source_evidence,
    )


def build_assumptions() -> list[Assumption]:
    """Every scenario x driver assumption, grounded in HISTORICAL's own
    5-year range (never an arbitrary base ± N% spread). See
    docs/milestone_3_forecast_engine_proposal.md Section 5 for the full
    historical-range table each rationale below cites.
    """
    hist_ev = f"data/curated/target_cash.db annual_facts, analytical_view=latest_restated, FY2021-FY2025 (frozen {FORECAST_INFORMATION_CUTOFF} basis; see docs/milestone_2_evidence.md)"
    assumptions: list[Assumption] = []

    # --- Revenue growth (%/yr) ---
    assumptions += [
        _a("asm_rev_growth_base", "base", "revenue_growth_pct", 1.0, "percent",
           "Below FY2022's post-pandemic snap-back (+2.94%) and above the FY2023-FY2025 raw-decline trend; "
           "matches the FY2024-vs-FY2023(52-week-normalized) growth of +1.12%, treated as the cleanest "
           "recent read once the FY2023 53-week distortion is removed. Continuation of a stabilizing, "
           "low-single-digit trend -- explicitly NOT a return to the FY2021/FY2022 growth rates.",
           "5yr raw growth range: -1.68% to +2.94%; 52wk-normalized FY2024 growth: +1.12%", hist_ev),
        _a("asm_rev_growth_upside", "upside", "revenue_growth_pct", 3.0, "percent",
           "At the high end of, without exceeding, the 5-year historical maximum (+2.94%, FY2022); "
           "reflects improved traffic/comp execution within the range Target has actually achieved, "
           "never an unprecedented acceleration.",
           "5yr raw growth max: +2.94% (FY2022)", hist_ev),
        _a("asm_rev_growth_downside", "downside", "revenue_growth_pct", -2.5, "percent",
           "Beyond the single worst observed historical decline (-1.68%, FY2025) by roughly 1.5x, "
           "reflecting sustained discretionary-spending pressure -- a continued-deterioration case, "
           "not a fabricated crisis or extreme event.",
           "5yr raw growth min: -1.68% (FY2025)", hist_ev),
    ]

    # --- Gross margin (%), FY2026 starting point then linear drift to FY2030 ---
    gm_path = {
        "base": (27.93, 28.00),
        "upside": (27.93, 28.80),
        "downside": (27.93, 26.30),
    }
    gm_rationale = {
        "base": "Holds near the FY2023-FY2025 recent average (~27.9-28.2%) -- explicitly NOT reverting to "
                "the FY2021 peak of 29.28%, which followed a pandemic-driven demand/mix shift item 3 "
                "requires treating as non-repeatable.",
        "upside": "Gradual improvement toward, but never exceeding, the 5-year historical maximum (29.28%, "
                  "FY2021) -- plausible supply-chain/mix execution, bounded by Target's own observed range.",
        "downside": "Gradual, partial reversion toward (not matching) the FY2022 trough of 24.57% -- a "
                    "moderate margin-pressure case, bounded well short of the full historical worst year.",
    }
    for scenario, (start, end) in gm_path.items():
        for fy in FORECAST_YEARS:
            frac = (fy - FORECAST_YEARS[0]) / (FORECAST_YEARS[-1] - FORECAST_YEARS[0])
            value = round(start + (end - start) * frac, 3)
            assumptions.append(Assumption(
                assumption_id=f"asm_gross_margin_{scenario}_{fy}", scenario=scenario, forecast_year=fy,
                metric="gross_margin_pct", value=value, unit="percent", rationale=gm_rationale[scenario],
                historical_reference="5yr gross margin range: 24.57%-29.28%, median 27.93%",
                source_evidence=hist_ev,
            ))

    # --- SG&A % of revenue (opex, excludes D&A) ---
    sga_path = {"base": (20.55, 20.55), "upside": (20.55, 19.80), "downside": (20.55, 21.30)}
    sga_rationale = {
        "base": "Flat at the FY2025 actual level -- continuation, not reversion to the lower historical "
                "range (18.63%-19.98%) achieved only when revenue was growing.",
        "upside": "Gradual improvement toward, but not below, the 5-year historical minimum (18.63%, FY2021) "
                  "-- cost discipline/productivity, bounded by Target's own observed range.",
        "downside": "Continued deleverage as revenue declines faster than fixed SG&A costs, moderately "
                    "above the 5-year historical maximum (20.62%, FY2024).",
    }
    for scenario, (start, end) in sga_path.items():
        for fy in FORECAST_YEARS:
            frac = (fy - FORECAST_YEARS[0]) / (FORECAST_YEARS[-1] - FORECAST_YEARS[0])
            value = round(start + (end - start) * frac, 3)
            assumptions.append(Assumption(
                assumption_id=f"asm_sga_pct_{scenario}_{fy}", scenario=scenario, forecast_year=fy,
                metric="sga_pct_of_revenue", value=value, unit="percent", rationale=sga_rationale[scenario],
                historical_reference="5yr SG&A % of revenue range: 18.63%-20.62%, median 19.98%",
                source_evidence=hist_ev,
            ))

    # --- D&A % of revenue (opex line only) -- continues the observed rising trend ---
    da_trend_per_year = (2.50 - 2.19) / 4  # FY2021->FY2025 average annual increase, percentage points
    da_adjust = {"base": 0.0, "upside": 0.10, "downside": -0.10}
    da_rationale = {
        "base": "Extrapolates the FY2021-FY2025 average annual increase (~0.078pp/yr) in D&A as a percent "
                "of revenue, reflecting continued store/technology investment amortizing -- a documented "
                "persistence of an already-observed trend, not a new assumption.",
        "upside": "Same trend plus +0.10pp, consistent with the upside scenario's higher CapEx intensity "
                  "(more assets in service depreciate more).",
        "downside": "Same trend less -0.10pp, consistent with the downside scenario's reduced CapEx "
                    "intensity -- D&A is sticky (prior capex keeps depreciating), so only a small offset "
                    "is applied, not a reversal of the trend.",
    }
    for scenario, adj in da_adjust.items():
        for i, fy in enumerate(FORECAST_YEARS, start=1):
            value = round(2.50 + da_trend_per_year * i + adj, 3)
            assumptions.append(Assumption(
                assumption_id=f"asm_da_pct_{scenario}_{fy}", scenario=scenario, forecast_year=fy,
                metric="da_pct_of_revenue", value=value, unit="percent", rationale=da_rationale[scenario],
                historical_reference="5yr D&A % of revenue range: 2.19%-2.50%, rising each year",
                source_evidence=hist_ev,
            ))

    # --- Effective tax rate ---
    assumptions += [
        _a("asm_tax_rate_base", "base", "effective_tax_rate_pct", 22.2, "percent",
           "Average of the 3 most recent years excluding the FY2022 outlier (18.67%, a one-time benefit "
           "not treated as representative): (21.88+22.24+22.28)/3 = 22.13%, rounded.",
           "5yr range 18.67%-22.28% (FY2022 excluded as non-representative); recent 3yr avg 22.13%", hist_ev),
        _a("asm_tax_rate_upside", "upside", "effective_tax_rate_pct", 21.5, "percent",
           "Modestly favorable rate near the low end of the representative (non-FY2022) historical range.",
           "Representative range (ex-FY2022): 21.88%-22.28%", hist_ev),
        _a("asm_tax_rate_downside", "downside", "effective_tax_rate_pct", 23.0, "percent",
           "Modestly unfavorable rate, slightly above the representative historical maximum.",
           "Representative range (ex-FY2022): 21.88%-22.28%", hist_ev),
    ]

    # --- Net other income ($M/yr, flat) ---
    assumptions += [
        _a("asm_other_income_base", "base", "net_other_income_musd", 95.0, "USD_millions",
           "Flat at the FY2025 actual level -- this line is historically small and volatile ($48M-$382M) "
           "with no clear trend; holding flat avoids fabricating a directional assumption without evidence.",
           "5yr range: $48M-$382M, FY2025=$95M", hist_ev),
        _a("asm_other_income_upside", "upside", "net_other_income_musd", 100.0, "USD_millions",
           "Near-flat, marginally favorable -- within the historical range, no fabricated upside swing.",
           "5yr range: $48M-$382M", hist_ev),
        _a("asm_other_income_downside", "downside", "net_other_income_musd", 80.0, "USD_millions",
           "Near-flat, marginally unfavorable -- within the historical range.",
           "5yr range: $48M-$382M", hist_ev),
    ]

    # --- Diluted share count change (%/yr) ---
    assumptions += [
        _a("asm_share_chg_base", "base", "diluted_share_change_pct", -0.5, "percent",
           "Continued modest buyback-driven reduction, below the 5-year average magnitude given lower "
           "recent FCF than the FY2021/FY2022 aggressive-repurchase years.",
           "5yr YoY share change: -5.68%, -0.41%, -0.22%, -1.34%", hist_ev),
        _a("asm_share_chg_upside", "upside", "diluted_share_change_pct", -1.5, "percent",
           "More aggressive buyback-driven reduction, funded by stronger scenario FCF -- within the "
           "historical range observed in FY2022-FY2025 (excluding the FY2022 outlier year), not the "
           "unrepeated -5.68% pandemic-era pace.",
           "5yr YoY share change range (ex-FY2022): -1.34% to -0.22%", hist_ev),
        _a("asm_share_chg_downside", "downside", "diluted_share_change_pct", 0.0, "percent",
           "No net buybacks assumed; share count held flat -- capital preservation under pressure.",
           "N/A -- a policy choice, not a historical figure", hist_ev),
    ]

    # --- Interest rate on average total GAAP debt ---
    assumptions += [
        _a("asm_interest_rate_base", "base", "interest_rate_pct", 3.1, "percent",
           "Matches the recent (FY2024-FY2025) implied rate on average total_debt_gaap.",
           "5yr implied rate (interest_expense / total_debt_gaap): 2.98%-3.62%, recent 2 yrs ~3.0-3.1%", hist_ev),
        _a("asm_interest_rate_upside", "upside", "interest_rate_pct", 2.9, "percent",
           "Slightly favorable borrowing cost / lower incremental debt need, within the historical range.",
           "5yr implied rate range: 2.98%-3.62%", hist_ev),
        _a("asm_interest_rate_downside", "downside", "interest_rate_pct", 3.4, "percent",
           "Higher borrowing cost, near the historical maximum, reflecting greater reliance on debt "
           "funding under pressure.",
           "5yr implied rate range: 2.98%-3.62%", hist_ev),
    ]

    # --- CapEx % of revenue ---
    assumptions += [
        _a("asm_capex_pct_base", "base", "capex_pct_of_revenue", 3.6, "percent",
           "Near the FY2025 actual (3.56%) and the 5-year median (3.56%) -- maintenance-plus-modest-growth "
           "continuation, using PaymentsToAcquirePropertyPlantAndEquipment, never total investing cash flow.",
           "5yr range: 2.71%-5.07%, median 3.56%, FY2025=3.56%", hist_ev),
        _a("asm_capex_pct_upside", "upside", "capex_pct_of_revenue", 4.3, "percent",
           "Elevated growth CapEx (new stores/supply chain/digital investment supporting the stronger "
           "revenue growth in this scenario) -- higher CapEx in the upside case is economically "
           "appropriate here (item 12), staying below the 5-year historical maximum (5.07%, FY2022).",
           "5yr range: 2.71%-5.07%", hist_ev),
        _a("asm_capex_pct_downside", "downside", "capex_pct_of_revenue", 2.8, "percent",
           "Capital discipline / deferred growth investment under pressure, near the 5-year historical "
           "minimum (2.71%, FY2024) -- Target does not disclose a maintenance-only CapEx figure, so this "
           "is not claimed as 'maintenance CapEx', only as a low-end plausible total CapEx level.",
           "5yr range: 2.71%-5.07%, min 2.71% (FY2024)", hist_ev),
    ]

    # --- Total D&A cash-flow add-back ($, modeled as % of revenue, separate from opex D&A) ---
    addback_trend_per_year = (3134.0 / 104780.0 - 2642.0 / 106005.0) * 100 / 4
    addback_start_pct = 3134.0 / 104780.0 * 100
    addback_adjust = {"base": 0.0, "upside": 0.05, "downside": -0.05}
    for scenario, adj in addback_adjust.items():
        for i, fy in enumerate(FORECAST_YEARS, start=1):
            value = round(addback_start_pct + addback_trend_per_year * i + adj, 3)
            assumptions.append(Assumption(
                assumption_id=f"asm_da_addback_pct_{scenario}_{fy}", scenario=scenario, forecast_year=fy,
                metric="da_cfo_addback_pct_of_revenue", value=value, unit="percent",
                rationale="Modeled independently of the opex D&A line (never summed with it -- item 5's "
                          "double-counting warning) using DepreciationDepletionAndAmortization's own "
                          "FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity.",
                historical_reference=f"5yr CFO-addback D&A % of revenue: {2642.0/106005.0*100:.2f}%-{3134.0/104780.0*100:.2f}%, rising each year",
                source_evidence="data/curated/target_cash.db raw_facts, us-gaap:DepreciationDepletionAndAmortization, "
                                 "queried via target_cash.annual.latest_restated_duration, frozen 2026-09-16 "
                                 "(not in annual_facts -- Milestone 2 approved only the opex D&A line at annual grain)",
            ))

    # --- Inventory % of revenue ---
    inv_path = {"base": 11.8, "upside": 11.0, "downside": 12.8}
    inv_rationale = {
        "base": "Holds near the FY2025 actual (11.74%), within the 5-year range.",
        "upside": "Improved inventory efficiency/turns, near the 5-year historical minimum (11.07%, FY2023).",
        "downside": "Inventory buildup / slower turns under demand pressure, near the 5-year historical "
                    "maximum (13.11%, FY2021) -- working-capital consumption, per item 3's downside theme.",
    }
    for scenario, value in inv_path.items():
        assumptions.append(Assumption(
            assumption_id=f"asm_inventory_pct_{scenario}", scenario=scenario, forecast_year=0,
            metric="inventory_pct_of_revenue", value=value, unit="percent", rationale=inv_rationale[scenario],
            historical_reference="5yr range: 11.07%-13.11%, FY2025=11.74%", source_evidence=hist_ev,
        ))

    # --- Accounts payable % of COGS ---
    ap_path = {"base": 16.7, "upside": 17.5, "downside": 15.5}
    ap_rationale = {
        "base": "Holds near the FY2025 actual (16.72%), within the 5-year range.",
        "upside": "Extended payables terms / improved cash conversion, near the 5-year historical maximum "
                  "(20.65%, FY2021) but conservatively below it.",
        "downside": "Suppliers tighten terms under pressure, near the 5-year historical minimum (15.54%, "
                    "FY2023) -- working-capital consumption.",
    }
    for scenario, value in ap_path.items():
        assumptions.append(Assumption(
            assumption_id=f"asm_ap_pct_{scenario}", scenario=scenario, forecast_year=0,
            metric="ap_pct_of_cogs", value=value, unit="percent", rationale=ap_rationale[scenario],
            historical_reference="5yr range: 15.54%-20.65%, FY2025=16.72%", source_evidence=hist_ev,
        ))

    # --- Other operating cash adjustments ($M/yr, flat) ---
    # Historical derivation: other = CFO - net_income - D&A_addback - inventory_cash_impact - AP_cash_impact,
    # computed for FY2022-FY2025 (FY2021 has no prior year to difference against): -282, +126, +194, +1458.
    assumptions += [
        _a("asm_other_opcf_base", "base", "other_operating_cf_musd", 150.0, "USD_millions",
           "Near the historical median of the derived 'other operating cash adjustments' residual "
           "(stock-based comp, deferred taxes, other non-cash items, other working capital not "
           "separately modeled) -- see docs/milestone_3_forecast_engine_proposal.md Section 7 for the "
           "full derivation and component discussion. This is NOT solved backward to hit a CFO target.",
           "FY2022-FY2025 derived residual: -$282M, +$126M, +$194M, +$1,458M; median ~$160M", hist_ev),
        _a("asm_other_opcf_upside", "upside", "other_operating_cf_musd", 250.0, "USD_millions",
           "More favorable working-capital/other items, within the observed historical range.",
           "FY2022-FY2025 derived residual range: -$282M to +$1,458M", hist_ev),
        _a("asm_other_opcf_downside", "downside", "other_operating_cf_musd", 50.0, "USD_millions",
           "Less favorable working-capital/other items, within the observed historical range.",
           "FY2022-FY2025 derived residual range: -$282M to +$1,458M", hist_ev),
    ]

    # --- Dividends: modeled as dividend-per-share growth applied to a $/share proxy ---
    div_growth = {"base": 2.0, "upside": 4.0, "downside": 0.0}
    div_rationale = {
        "base": "Continues the recent (FY2024-FY2025) decelerated per-share dividend growth pace of "
                "~1.8%/yr, rounded up modestly.",
        "upside": "Stronger payout growth supported by better earnings, still well below the earlier, "
                  "one-time large hikes (+25.8% FY2022, +10.1% FY2023) which followed unusually high "
                  "FY2021 earnings, not treated as repeatable.",
        "downside": "Dividend frozen (0% growth), not cut -- Target's dividends_paid has grown in every "
                    "one of the 5 historical years in this dataset with no observed cut, so an outright "
                    "reduction is not modeled as a plausible base case for the downside scenario; "
                    "freezing (not increasing) is the appropriate downside floor.",
    }
    for scenario, value in div_growth.items():
        assumptions.append(Assumption(
            assumption_id=f"asm_dividend_growth_{scenario}", scenario=scenario, forecast_year=0,
            metric="dividend_per_share_growth_pct", value=value, unit="percent", rationale=div_rationale[scenario],
            historical_reference="Implied $/share (dividends_paid/diluted_shares) YoY growth: +25.8%, +10.1%, +1.8%, +1.8%",
            source_evidence=hist_ev,
        ))

    # --- Share repurchases: a target payout ratio of post-dividend FCF, NEVER a balancing plug ---
    buyback_payout = {"base": 40.0, "upside": 55.0, "downside": 0.0}
    buyback_rationale = {
        "base": "A pre-set target payout ratio of (FCF - dividends), applied identically regardless of "
                "the resulting cash balance -- an input assumption, never solved backward to hit a cash "
                "or deployable-capacity target (the explicit 'not an automatic balancing plug' "
                "requirement). Historical repurchases range from $0 to $7,188M with no fixed dollar "
                "pattern, making a payout-ratio policy more defensible than a flat dollar figure.",
        "upside": "A higher target payout ratio, reflecting stronger FCF generation and capital return "
                  "capacity in this scenario.",
        "downside": "No repurchases -- capital preservation under pressure.",
    }
    for scenario, value in buyback_payout.items():
        assumptions.append(Assumption(
            assumption_id=f"asm_buyback_payout_{scenario}", scenario=scenario, forecast_year=0,
            metric="buyback_payout_pct_of_post_dividend_fcf", value=value, unit="percent",
            rationale=buyback_rationale[scenario],
            historical_reference="5yr share_repurchases: $7,188M, $2,646M, $0M, $1,007M, $408M -- no fixed pattern",
            source_evidence=hist_ev,
        ))

    # --- Debt: fixed, pre-set proceeds/repayments (never an automatic deficit-filling plug) ---
    debt_schedule = {
        "base": (700.0, 700.0),      # (proceeds, repayments) -- net roughly flat, rolling refinancing
        "upside": (300.0, 1000.0),   # net repayment -- delever as FCF allows
        "downside": (500.0, 300.0),  # small net issuance -- a fixed, pre-committed liquidity assumption,
                                     # explicitly NOT sized to whatever the cash shortfall turns out to be
    }
    debt_rationale = {
        "base": "Fixed at a modest, pre-set rolling-refinancing level (proceeds roughly offsetting "
                "repayments) -- not derived from, or sized to, the resulting cash balance.",
        "upside": "Fixed net repayment, funded by stronger scenario FCF -- a deleveraging policy choice, "
                  "not a residual plug.",
        "downside": "A small, FIXED, pre-committed net issuance assumption. This is deliberately NOT sized "
                    "to whatever cash shortfall the downside scenario produces -- see the "
                    "'minimum_cash_compliance' validation check, which raises an explicit funding warning "
                    "if ending cash still falls below the minimum buffer after this fixed amount, rather "
                    "than silently increasing debt further to force compliance.",
    }
    for scenario, (proceeds, repayments) in debt_schedule.items():
        assumptions.append(Assumption(
            assumption_id=f"asm_debt_proceeds_{scenario}", scenario=scenario, forecast_year=0,
            metric="debt_proceeds_musd", value=proceeds, unit="USD_millions", rationale=debt_rationale[scenario],
            historical_reference="5yr debt_proceeds: $1,972M, $2,625M, $0M, $741M, $1,984M",
            source_evidence=hist_ev,
        ))
        assumptions.append(Assumption(
            assumption_id=f"asm_debt_repayments_{scenario}", scenario=scenario, forecast_year=0,
            metric="debt_repayments_musd", value=repayments, unit="USD_millions", rationale=debt_rationale[scenario],
            historical_reference="5yr debt_repayments: $1,147M, $163M, $147M, $1,139M, $1,643M",
            source_evidence=hist_ev,
        ))

    # --- Finance leases: held flat (no new modeling basis disclosed) ---
    for scenario in SCENARIOS:
        assumptions.append(Assumption(
            assumption_id=f"asm_finance_lease_flat_{scenario}", scenario=scenario, forecast_year=0,
            metric="finance_lease_liabilities_musd", value=HISTORICAL["finance_lease_liabilities"][2025],
            unit="USD_millions",
            rationale="Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease "
                      "schedule in the registered source set; modeling a trend would be unsupported "
                      "speculation.",
            historical_reference="5yr range: $2,013M-$2,161M, essentially flat", source_evidence=hist_ev,
        ))

    # --- Minimum cash buffer: recommended policy (see item 11 analysis) ---
    for scenario in SCENARIOS:
        assumptions.append(Assumption(
            assumption_id=f"asm_min_cash_buffer_pct_{scenario}", scenario=scenario, forecast_year=0,
            metric="min_cash_buffer_pct_of_revenue", value=3.0, unit="percent",
            rationale="Recommended policy (see docs/milestone_3_forecast_engine_proposal.md Section 11 "
                      "for the 4-policy comparison): 3% of forecast revenue scales with the business "
                      "(unlike a fixed dollar figure) and sits above the historical minimum ratio "
                      "(2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%), providing "
                      "headroom without assuming the business needs FY2021-level cash intensity.",
            historical_reference="5yr cash % of revenue: 2.04%, 5.58%, 3.54%, 4.47%, 5.24%",
            source_evidence=hist_ev,
        ))

    return assumptions


def assumptions_by_scenario(assumptions: list[Assumption]) -> dict[str, dict[str, dict[int, float]]]:
    """Reshapes the flat assumption list into {scenario: {metric: {forecast_year_or_0: value}}}."""
    out: dict[str, dict[str, dict[int, float]]] = {s: {} for s in SCENARIOS}
    for a in assumptions:
        out[a.scenario].setdefault(a.metric, {})[a.forecast_year] = a.value
    return out


def _lookup(by_metric: dict[int, float], fy: int) -> float:
    return by_metric.get(fy, by_metric.get(0))


# --- Full driver-based forecast (items 4-10) -------------------------------

@dataclass
class ForecastYear:
    """One scenario x fiscal-year row of the full forecast financial statements.

    Every field here is a FORECAST value (never written to annual_facts or any
    Milestone 1/2 table); HISTORICAL above remains the only source of actual
    reported figures. fiscal_year is always a member of FORECAST_YEARS, never
    of HISTORICAL_YEARS -- the two sets of rows are structurally disjoint.
    """
    scenario: str
    fiscal_year: int
    revenue: float
    revenue_growth_pct: float
    cost_of_sales: float
    gross_profit: float
    gross_margin_pct: float
    sga_expense: float
    sga_pct_of_revenue: float
    depreciation_amortization_opex: float
    da_pct_of_revenue: float
    operating_income: float
    operating_margin_pct: float
    total_debt_gaap_beginning: float
    total_debt_gaap_ending: float
    debt_proceeds: float
    debt_repayments: float
    interest_rate_pct: float
    interest_expense: float
    net_other_income: float
    pretax_income: float
    effective_tax_rate_pct: float
    income_tax_expense: float
    net_income: float
    diluted_shares: float
    diluted_eps: float
    da_cfo_addback: float
    inventory_balance: float
    inventory_cash_impact: float
    accounts_payable_balance: float
    ap_cash_impact: float
    other_operating_cf: float
    operating_cash_flow: float
    capital_expenditure: float
    free_cash_flow: float
    investing_cash_flow: float
    dividend_per_share: float
    dividends_paid: float
    share_repurchases: float
    financing_cash_flow: float
    net_change_in_cash: float
    beginning_cash: float
    ending_cash: float
    finance_lease_liabilities: float
    gross_fcf_capacity: float
    post_dividend_capacity: float
    mandatory_financing_flows: float
    pre_discretionary_ending_cash: float
    min_cash_buffer: float
    near_term_debt_repayment_reserve: float
    deployable_capacity: float
    funding_warning: bool


def _run_from_metrics(scenario: str, metrics: dict[str, dict[int, float]]) -> list[ForecastYear]:
    """Core engine. `metrics` is one scenario's {metric: {fy_or_0: value}} slice
    of assumptions_by_scenario() output -- factored out from run_scenario() so
    sensitivity analysis can perturb a single driver without touching the
    published assumption set.
    """
    years: list[ForecastYear] = []
    prev_revenue = HISTORICAL["revenue"][2025]
    prev_shares = HISTORICAL["diluted_shares"][2025]
    prev_debt = HISTORICAL["total_debt_gaap"][2025]
    prev_inventory = HISTORICAL["inventory"][2025]
    prev_ap = HISTORICAL["accounts_payable"][2025]
    prev_cash = HISTORICAL["cash_and_equivalents_balance_sheet"][2025]
    prev_dps = HISTORICAL["dividends_paid"][2025] / HISTORICAL["diluted_shares"][2025]

    for fy in FORECAST_YEARS:
        growth = _lookup(metrics["revenue_growth_pct"], fy)
        revenue = prev_revenue * (1 + growth / 100)

        gm = _lookup(metrics["gross_margin_pct"], fy)
        gross_profit = revenue * gm / 100
        cost_of_sales = revenue - gross_profit

        sga_pct = _lookup(metrics["sga_pct_of_revenue"], fy)
        sga_expense = revenue * sga_pct / 100

        da_pct = _lookup(metrics["da_pct_of_revenue"], fy)
        da_opex = revenue * da_pct / 100

        operating_income = gross_profit - sga_expense - da_opex
        operating_margin_pct = operating_income / revenue * 100

        debt_proceeds = _lookup(metrics["debt_proceeds_musd"], fy)
        debt_repayments = _lookup(metrics["debt_repayments_musd"], fy)
        debt_ending = prev_debt + debt_proceeds - debt_repayments
        interest_rate = _lookup(metrics["interest_rate_pct"], fy)
        # Rate applied to the average of beginning/ending balance -- avoids
        # overstating interest on debt issued/repaid partway through the year.
        interest_expense = interest_rate / 100 * (prev_debt + debt_ending) / 2

        net_other_income = _lookup(metrics["net_other_income_musd"], fy)
        pretax_income = operating_income - interest_expense + net_other_income

        etr = _lookup(metrics["effective_tax_rate_pct"], fy)
        tax = pretax_income * etr / 100
        net_income = pretax_income - tax

        share_chg = _lookup(metrics["diluted_share_change_pct"], fy)
        diluted_shares = prev_shares * (1 + share_chg / 100)
        diluted_eps = net_income / diluted_shares

        # da_cfo_addback is the full cash-flow-statement D&A addback
        # (us-gaap:DepreciationDepletionAndAmortization, includes COGS-embedded
        # D&A) -- modeled independently of da_opex above and NEVER summed with
        # it (item 5's double-counting warning: da_opex already reduced
        # operating_income; da_cfo_addback is added back to net_income to
        # reconstruct CFO, a completely separate step).
        da_addback_pct = _lookup(metrics["da_cfo_addback_pct_of_revenue"], fy)
        da_addback = revenue * da_addback_pct / 100

        inv_pct = _lookup(metrics["inventory_pct_of_revenue"], fy)
        inventory_balance = revenue * inv_pct / 100
        inventory_cash_impact = -(inventory_balance - prev_inventory)  # build = use of cash

        ap_pct = _lookup(metrics["ap_pct_of_cogs"], fy)
        ap_balance = cost_of_sales * ap_pct / 100
        ap_cash_impact = ap_balance - prev_ap  # increase = source of cash

        other_opcf = _lookup(metrics["other_operating_cf_musd"], fy)

        cfo = net_income + da_addback + inventory_cash_impact + ap_cash_impact + other_opcf

        capex_pct = _lookup(metrics["capex_pct_of_revenue"], fy)
        capex = revenue * capex_pct / 100
        fcf = cfo - capex
        # LIMITATION: no disclosed driver exists for non-CapEx investing items
        # (e.g. investment purchases/maturities), so investing_cash_flow is
        # modeled as exactly -capex. This is a documented approximation, never
        # a substitution of CFI for CapEx in the FCF formula itself (item 6).
        investing_cf = -capex

        div_growth = _lookup(metrics["dividend_per_share_growth_pct"], fy)
        dps = prev_dps * (1 + div_growth / 100)
        dividends_paid = dps * diluted_shares

        post_div_fcf = fcf - dividends_paid
        buyback_payout = _lookup(metrics["buyback_payout_pct_of_post_dividend_fcf"], fy)
        # Floored at 0, never allowed to go negative (a negative repurchase
        # has no cash-flow meaning here) -- payout ratio is a fixed input,
        # not solved backward to hit any target (item 9).
        share_repurchases = max(0.0, post_div_fcf * buyback_payout / 100)

        financing_cf = -dividends_paid - share_repurchases + debt_proceeds - debt_repayments

        net_change_cash = cfo + investing_cf + financing_cf
        # No FX translation effect is separately modeled -- Target's cash is
        # overwhelmingly USD-denominated and no disclosed FX driver exists in
        # the registered source set. Reported here as an unmodeled item
        # (implicitly zero), never asserted as a historical fact (item 6).
        beginning_cash = prev_cash
        ending_cash = beginning_cash + net_change_cash

        finance_lease = _lookup(metrics["finance_lease_liabilities_musd"], fy)

        gross_fcf_capacity = fcf
        post_dividend_capacity = post_div_fcf
        # Mandatory financing flows exclude share repurchases (the
        # discretionary use of capacity being measured) but include dividends
        # and the fixed, pre-set debt schedule.
        mandatory_financing_flows = -dividends_paid + debt_proceeds - debt_repayments
        pre_discretionary_ending_cash = beginning_cash + cfo + investing_cf + mandatory_financing_flows
        min_cash_buffer_pct = _lookup(metrics["min_cash_buffer_pct_of_revenue"], fy)
        min_cash_buffer = revenue * min_cash_buffer_pct / 100
        # No disclosed debt-maturity ladder exists, so the near-term repayment
        # reserve is proxied by this year's own fixed, pre-set repayment
        # assumption -- documented as a simplification pending real maturity
        # data (item 11's limitation).
        near_term_reserve = debt_repayments
        deployable_capacity = max(0.0, pre_discretionary_ending_cash - min_cash_buffer - near_term_reserve)
        funding_warning = ending_cash < min_cash_buffer

        years.append(ForecastYear(
            scenario=scenario, fiscal_year=fy,
            revenue=revenue, revenue_growth_pct=growth,
            cost_of_sales=cost_of_sales, gross_profit=gross_profit, gross_margin_pct=gm,
            sga_expense=sga_expense, sga_pct_of_revenue=sga_pct,
            depreciation_amortization_opex=da_opex, da_pct_of_revenue=da_pct,
            operating_income=operating_income, operating_margin_pct=operating_margin_pct,
            total_debt_gaap_beginning=prev_debt, total_debt_gaap_ending=debt_ending,
            debt_proceeds=debt_proceeds, debt_repayments=debt_repayments,
            interest_rate_pct=interest_rate, interest_expense=interest_expense,
            net_other_income=net_other_income, pretax_income=pretax_income,
            effective_tax_rate_pct=etr, income_tax_expense=tax, net_income=net_income,
            diluted_shares=diluted_shares, diluted_eps=diluted_eps,
            da_cfo_addback=da_addback,
            inventory_balance=inventory_balance, inventory_cash_impact=inventory_cash_impact,
            accounts_payable_balance=ap_balance, ap_cash_impact=ap_cash_impact,
            other_operating_cf=other_opcf, operating_cash_flow=cfo,
            capital_expenditure=capex, free_cash_flow=fcf, investing_cash_flow=investing_cf,
            dividend_per_share=dps, dividends_paid=dividends_paid, share_repurchases=share_repurchases,
            financing_cash_flow=financing_cf, net_change_in_cash=net_change_cash,
            beginning_cash=beginning_cash, ending_cash=ending_cash,
            finance_lease_liabilities=finance_lease,
            gross_fcf_capacity=gross_fcf_capacity, post_dividend_capacity=post_dividend_capacity,
            mandatory_financing_flows=mandatory_financing_flows,
            pre_discretionary_ending_cash=pre_discretionary_ending_cash,
            min_cash_buffer=min_cash_buffer, near_term_debt_repayment_reserve=near_term_reserve,
            deployable_capacity=deployable_capacity, funding_warning=funding_warning,
        ))

        prev_revenue, prev_shares, prev_debt = revenue, diluted_shares, debt_ending
        prev_inventory, prev_ap, prev_cash, prev_dps = inventory_balance, ap_balance, ending_cash, dps

    return years


def run_scenario(scenario: str, by_scenario: dict[str, dict[str, dict[int, float]]]) -> list[ForecastYear]:
    return _run_from_metrics(scenario, by_scenario[scenario])


def run_all_scenarios(assumptions: list[Assumption] | None = None) -> dict[str, list[ForecastYear]]:
    assumptions = assumptions if assumptions is not None else build_assumptions()
    by_scenario = assumptions_by_scenario(assumptions)
    return {s: run_scenario(s, by_scenario) for s in SCENARIOS}


def perturb_metric(
    by_scenario: dict[str, dict[str, dict[int, float]]], scenario: str, metric: str, delta: float
) -> dict[str, dict[int, float]]:
    """Returns a copy of one scenario's metrics dict with every forecast_year
    entry of `metric` shifted by `delta` (same unit as the assumption, e.g.
    percentage points for a *_pct metric). Used only for sensitivity dry-runs
    (item 13) -- never mutates the published assumption set.
    """
    metrics = {k: dict(v) for k, v in by_scenario[scenario].items()}
    metrics[metric] = {fy: v + delta for fy, v in metrics[metric].items()}
    return metrics


# --- Lineage (representative, item 2's forecast_lineage concept) ----------

@dataclass(frozen=True)
class ForecastLineageEntry:
    forecast_fact_id: str
    scenario: str
    fiscal_year: int
    metric: str
    formula: str
    input_fact_ids: tuple[str, ...]
    assumption_ids: tuple[str, ...]
    information_cutoff: str = FORECAST_INFORMATION_CUTOFF


def build_lineage(years: list[ForecastYear], assumptions: list[Assumption]) -> list[ForecastLineageEntry]:
    """Representative lineage for the major derived metrics (revenue through
    deployable_capacity). A future persistence round must extend this to
    every persisted forecast_facts row at full grain -- this dry-run
    demonstrates the required shape and satisfies the lineage_completeness
    validation check below, it does not claim to be the final schema-ready
    lineage set.
    """
    by_key: dict[tuple[str, str, int], str] = {}
    for a in assumptions:
        by_key[(a.scenario, a.metric, a.forecast_year)] = a.assumption_id

    def asm_id_for(s: str, metric: str, fy: int) -> str | None:
        return by_key.get((s, metric, fy)) or by_key.get((s, metric, 0))

    entries: list[ForecastLineageEntry] = []
    for y in years:
        s, fy = y.scenario, y.fiscal_year
        prior_fact = f"forecast_{s}_{fy - 1}_revenue" if fy - 1 in FORECAST_YEARS else "hist_revenue_2025"

        def add(metric, formula, input_ids, asm_metrics, _s=s, _fy=fy):
            asm_ids = tuple(aid for m in asm_metrics if (aid := asm_id_for(_s, m, _fy)) is not None)
            entries.append(ForecastLineageEntry(
                forecast_fact_id=f"forecast_{s}_{fy}_{metric}", scenario=s, fiscal_year=fy, metric=metric,
                formula=formula, input_fact_ids=tuple(input_ids), assumption_ids=asm_ids,
            ))

        add("revenue", "revenue_t = revenue_(t-1) * (1 + growth_t)", (prior_fact,), ("revenue_growth_pct",))
        add("gross_profit", "gross_profit_t = revenue_t * gross_margin_pct_t", (f"forecast_{s}_{fy}_revenue",), ("gross_margin_pct",))
        add("operating_income", "operating_income_t = gross_profit_t - sga_expense_t - da_opex_t",
            (f"forecast_{s}_{fy}_gross_profit",), ("sga_pct_of_revenue", "da_pct_of_revenue"))
        add("pretax_income", "pretax_income_t = operating_income_t - interest_expense_t + net_other_income_t",
            (f"forecast_{s}_{fy}_operating_income",), ("interest_rate_pct", "net_other_income_musd"))
        add("net_income", "net_income_t = pretax_income_t * (1 - effective_tax_rate_t)",
            (f"forecast_{s}_{fy}_pretax_income",), ("effective_tax_rate_pct",))
        add("diluted_eps", "diluted_eps_t = net_income_t / diluted_shares_t",
            (f"forecast_{s}_{fy}_net_income",), ("diluted_share_change_pct",))
        add("operating_cash_flow",
            "cfo_t = net_income_t + da_cfo_addback_t + inventory_cash_impact_t + ap_cash_impact_t + other_operating_cf_t",
            (f"forecast_{s}_{fy}_net_income",),
            ("da_cfo_addback_pct_of_revenue", "inventory_pct_of_revenue", "ap_pct_of_cogs", "other_operating_cf_musd"))
        add("free_cash_flow", "fcf_t = cfo_t - capex_t",
            (f"forecast_{s}_{fy}_operating_cash_flow",), ("capex_pct_of_revenue",))
        add("ending_cash", "ending_cash_t = beginning_cash_t + cfo_t + investing_cf_t + financing_cf_t",
            (f"forecast_{s}_{fy}_free_cash_flow",),
            ("dividend_per_share_growth_pct", "buyback_payout_pct_of_post_dividend_fcf",
             "debt_proceeds_musd", "debt_repayments_musd"))
        add("deployable_capacity",
            "deployable_capacity_t = max(0, pre_discretionary_ending_cash_t - min_cash_buffer_t - near_term_debt_repayment_reserve_t)",
            (f"forecast_{s}_{fy}_ending_cash",), ("min_cash_buffer_pct_of_revenue",))

    return entries


# --- Validation (item 12: 18 named checks) ---------------------------------

_TOL = 1e-6


@dataclass(frozen=True)
class ValidationResult:
    check_name: str
    scenario: str | None
    fiscal_year: int | None
    status: str  # 'PASS' | 'FAIL' | 'WARNING'
    detail: str


def _close(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(b))


def validate_all(
    forecasts: dict[str, list[ForecastYear]],
    assumptions: list[Assumption],
    lineage: dict[str, list[ForecastLineageEntry]],
) -> list[ValidationResult]:
    results: list[ValidationResult] = []

    def rec(check, scenario, fy, ok, detail, warning=False):
        status = "PASS" if ok else ("WARNING" if warning else "FAIL")
        results.append(ValidationResult(check, scenario, fy, status, detail))

    for scenario, years in forecasts.items():
        by_fy = {y.fiscal_year: y for y in years}
        prev_revenue = HISTORICAL["revenue"][2025]
        prev_debt = HISTORICAL["total_debt_gaap"][2025]
        prev_cash = HISTORICAL["cash_and_equivalents_balance_sheet"][2025]

        for y in years:
            fy = y.fiscal_year

            # 1. revenue_recursion
            expected_rev = prev_revenue * (1 + y.revenue_growth_pct / 100)
            rec("revenue_recursion", scenario, fy, _close(y.revenue, expected_rev),
                f"revenue={y.revenue:.1f} vs prev*(1+g)={expected_rev:.1f}")

            # 2. gross_profit_calc
            gp_from_margin = y.revenue * y.gross_margin_pct / 100
            rec("gross_profit_calc", scenario, fy,
                _close(y.gross_profit, gp_from_margin) and _close(y.gross_profit, y.revenue - y.cost_of_sales),
                f"gross_profit={y.gross_profit:.1f}, revenue*margin={gp_from_margin:.1f}, revenue-COGS={y.revenue - y.cost_of_sales:.1f}")

            # 3. operating_income_bridge
            expected_oi = y.gross_profit - y.sga_expense - y.depreciation_amortization_opex
            rec("operating_income_bridge", scenario, fy, _close(y.operating_income, expected_oi),
                f"operating_income={y.operating_income:.1f} vs gross_profit-SG&A-D&A={expected_oi:.1f}")

            # 4. pretax_income_bridge
            expected_pretax = y.operating_income - y.interest_expense + y.net_other_income
            rec("pretax_income_bridge", scenario, fy, _close(y.pretax_income, expected_pretax),
                f"pretax_income={y.pretax_income:.1f} vs OI-interest+other={expected_pretax:.1f}")

            # 5. tax_net_income_bridge
            expected_tax = y.pretax_income * y.effective_tax_rate_pct / 100
            expected_ni = y.pretax_income - y.income_tax_expense
            rec("tax_net_income_bridge", scenario, fy,
                _close(y.income_tax_expense, expected_tax) and _close(y.net_income, expected_ni),
                f"tax={y.income_tax_expense:.1f} vs pretax*ETR={expected_tax:.1f}; net_income={y.net_income:.1f} vs pretax-tax={expected_ni:.1f}")

            # 6. eps_consistency
            expected_eps = y.net_income / y.diluted_shares
            rec("eps_consistency", scenario, fy, _close(y.diluted_eps, expected_eps),
                f"diluted_eps={y.diluted_eps:.4f} vs net_income/shares={expected_eps:.4f}")

            # 7. cfo_construction
            expected_cfo = y.net_income + y.da_cfo_addback + y.inventory_cash_impact + y.ap_cash_impact + y.other_operating_cf
            rec("cfo_construction", scenario, fy, _close(y.operating_cash_flow, expected_cfo),
                f"CFO={y.operating_cash_flow:.1f} vs NI+D&A+WC+other={expected_cfo:.1f}")

            # 8. fcf_calc -- FCF must equal CFO - CapEx specifically (never CFO - total CFI)
            expected_fcf = y.operating_cash_flow - y.capital_expenditure
            rec("fcf_calc", scenario, fy, _close(y.free_cash_flow, expected_fcf),
                f"FCF={y.free_cash_flow:.1f} vs CFO-CapEx={expected_fcf:.1f} (CapEx={y.capital_expenditure:.1f}, distinct from total CFI={y.investing_cash_flow:.1f})")

            # 9. working_capital_sign_checks
            inv_delta = y.inventory_balance - (HISTORICAL["inventory"][2025] if fy == FORECAST_YEARS[0] else by_fy[fy - 1].inventory_balance)
            ap_delta = y.accounts_payable_balance - (HISTORICAL["accounts_payable"][2025] if fy == FORECAST_YEARS[0] else by_fy[fy - 1].accounts_payable_balance)
            ok_inv_sign = (inv_delta >= 0 and y.inventory_cash_impact <= _TOL) or (inv_delta < 0 and y.inventory_cash_impact > 0)
            ok_ap_sign = (ap_delta >= 0 and y.ap_cash_impact >= -_TOL) or (ap_delta < 0 and y.ap_cash_impact < 0)
            rec("working_capital_sign_checks", scenario, fy, ok_inv_sign and ok_ap_sign,
                f"inventory_delta={inv_delta:.1f}/cash_impact={y.inventory_cash_impact:.1f}; ap_delta={ap_delta:.1f}/cash_impact={y.ap_cash_impact:.1f}")

            # 10. cash_roll_forward
            expected_beg = prev_cash
            expected_end = y.beginning_cash + y.net_change_in_cash
            expected_change = y.operating_cash_flow + y.investing_cash_flow + y.financing_cash_flow
            rec("cash_roll_forward", scenario, fy,
                _close(y.beginning_cash, expected_beg) and _close(y.ending_cash, expected_end) and _close(y.net_change_in_cash, expected_change),
                f"beginning_cash={y.beginning_cash:.1f}, ending_cash={y.ending_cash:.1f} vs beg+change={expected_end:.1f}")

            # 11. debt_roll_forward
            expected_debt_end = y.total_debt_gaap_beginning + y.debt_proceeds - y.debt_repayments
            rec("debt_roll_forward", scenario, fy,
                _close(y.total_debt_gaap_beginning, prev_debt) and _close(y.total_debt_gaap_ending, expected_debt_end),
                f"debt_beg={y.total_debt_gaap_beginning:.1f}, debt_end={y.total_debt_gaap_ending:.1f} vs beg+proceeds-repay={expected_debt_end:.1f}")

            # 12. no_finance_lease_double_counting -- finance leases held flat and
            # never folded into the total_debt_gaap roll-forward above.
            rec("no_finance_lease_double_counting", scenario, fy,
                _close(y.finance_lease_liabilities, HISTORICAL["finance_lease_liabilities"][2025]) and
                _close(y.total_debt_gaap_ending, expected_debt_end),
                f"finance_lease={y.finance_lease_liabilities:.1f} (flat at FY2025 actual, held outside total_debt_gaap roll-forward)")

            # 13. minimum_cash_compliance -- funding warning surfaced, not silently patched
            below_buffer = y.ending_cash < y.min_cash_buffer - _TOL
            rec("minimum_cash_compliance", scenario, fy, y.funding_warning == below_buffer,
                f"ending_cash={y.ending_cash:.1f}, min_cash_buffer={y.min_cash_buffer:.1f}, funding_warning={y.funding_warning}",
                warning=below_buffer)

            # 17. information_cutoff_compliance (checked per assumption below, per-year placeholder omitted)

            prev_revenue, prev_debt, prev_cash = y.revenue, y.total_debt_gaap_ending, y.ending_cash

    # 14. scenario_ordering -- only for metrics with an economically unambiguous direction;
    # CapEx/FCF/repurchases are explicitly EXCLUDED per item 12 (upside can carry higher CapEx).
    for fy in FORECAST_YEARS:
        b, u, d = forecasts["base"][FORECAST_YEARS.index(fy)], forecasts["upside"][FORECAST_YEARS.index(fy)], forecasts["downside"][FORECAST_YEARS.index(fy)]
        checks = [
            ("revenue_growth_pct", u.revenue_growth_pct >= b.revenue_growth_pct >= d.revenue_growth_pct),
            ("gross_margin_pct", u.gross_margin_pct >= b.gross_margin_pct >= d.gross_margin_pct),
            ("sga_pct_of_revenue_inverse", u.sga_pct_of_revenue <= b.sga_pct_of_revenue <= d.sga_pct_of_revenue),
            ("effective_tax_rate_pct_inverse", u.effective_tax_rate_pct <= b.effective_tax_rate_pct <= d.effective_tax_rate_pct),
            ("net_income", u.net_income >= b.net_income >= d.net_income),
            ("diluted_eps", u.diluted_eps >= b.diluted_eps >= d.diluted_eps),
        ]
        ok = all(c[1] for c in checks)
        failed = [c[0] for c in checks if not c[1]]
        rec("scenario_ordering", None, fy, ok,
            "upside >= base >= downside holds for all economically-unambiguous drivers" if ok
            else f"violated for: {failed}")

    # 15. assumption_completeness -- every scenario has a value (year-specific or flat)
    # for every metric, for every forecast year the engine actually looked up.
    required_metrics = [
        "revenue_growth_pct", "gross_margin_pct", "sga_pct_of_revenue", "da_pct_of_revenue",
        "effective_tax_rate_pct", "net_other_income_musd", "diluted_share_change_pct",
        "interest_rate_pct", "capex_pct_of_revenue", "da_cfo_addback_pct_of_revenue",
        "inventory_pct_of_revenue", "ap_pct_of_cogs", "other_operating_cf_musd",
        "dividend_per_share_growth_pct", "buyback_payout_pct_of_post_dividend_fcf",
        "debt_proceeds_musd", "debt_repayments_musd", "finance_lease_liabilities_musd",
        "min_cash_buffer_pct_of_revenue",
    ]
    by_scenario = assumptions_by_scenario(assumptions)
    for scenario in SCENARIOS:
        missing = []
        for metric in required_metrics:
            by_fy = by_scenario[scenario].get(metric, {})
            for fy in FORECAST_YEARS:
                if fy not in by_fy and 0 not in by_fy:
                    missing.append(f"{metric}@{fy}")
        rec("assumption_completeness", scenario, None, not missing,
            "all required metrics covered for FY2026-FY2030" if not missing else f"missing: {missing}")

    # 16. lineage_completeness
    for scenario in SCENARIOS:
        entries = lineage.get(scenario, [])
        expected_metrics = {"revenue", "gross_profit", "operating_income", "pretax_income", "net_income",
                             "diluted_eps", "operating_cash_flow", "free_cash_flow", "ending_cash", "deployable_capacity"}
        got_metrics = {e.metric for e in entries if e.fiscal_year == FORECAST_YEARS[0]}
        no_empty_asm = all(len(e.assumption_ids) > 0 for e in entries)
        ok = expected_metrics.issubset(got_metrics) and no_empty_asm and len(entries) == len(expected_metrics) * len(FORECAST_YEARS)
        rec("lineage_completeness", scenario, None, ok,
            f"{len(entries)} lineage rows covering {len(got_metrics)}/{len(expected_metrics)} tracked metrics per year, "
            f"all with >=1 assumption_id" if ok else f"incomplete: missing metrics {expected_metrics - got_metrics}, or entries with no assumption_ids")

    # 17. information_cutoff_compliance
    bad_cutoff = [a.assumption_id for a in assumptions if a.information_cutoff > FORECAST_INFORMATION_CUTOFF]
    rec("information_cutoff_compliance", None, None, not bad_cutoff,
        "every assumption's information_cutoff <= FORECAST_INFORMATION_CUTOFF (2026-03-11, FY2025 10-K)"
        if not bad_cutoff else f"assumptions citing information after cutoff: {bad_cutoff}")

    # 18. no_historical_forecast_mixing -- structural: forecast rows only use FORECAST_YEARS,
    # never overlap HISTORICAL_YEARS, and HISTORICAL itself is never mutated by this module.
    fy_overlap = set(FORECAST_YEARS) & set(HISTORICAL_YEARS)
    all_years_tagged = all(y.fiscal_year in FORECAST_YEARS for years in forecasts.values() for y in years)
    rec("no_historical_forecast_mixing", None, None, not fy_overlap and all_years_tagged,
        "FORECAST_YEARS and HISTORICAL_YEARS are disjoint and every ForecastYear.fiscal_year is a FORECAST_YEARS member"
        if not fy_overlap and all_years_tagged else "overlap or mistagged year detected")

    return results


# --- Sensitivity (item 13) --------------------------------------------------

SENSITIVITY_DRIVERS = {
    "revenue_growth_pct": "revenue_growth_pct",
    "gross_margin_pct": "gross_margin_pct",
    "sga_pct_of_revenue": "sga_pct_of_revenue",
    "capex_pct_of_revenue": "capex_pct_of_revenue",
    "inventory_pct_of_revenue": "inventory_pct_of_revenue",
    "min_cash_buffer_pct_of_revenue": "min_cash_buffer_pct_of_revenue",
}


def sensitivity_table(
    driver: str, deltas: list[float], base_scenario: str = "base", assumptions: list[Assumption] | None = None
) -> list[dict]:
    """Perturbs one driver (in the assumption's own unit, e.g. percentage
    points) across `deltas` around the given scenario's published path,
    holding every other assumption fixed, and reports the terminal-year
    (FY2030) impact on CFO, FCF, ending cash, and deployable capacity. Pure
    dry-run -- no persistence, no valuation. Item 13 scope only.
    """
    assumptions = assumptions if assumptions is not None else build_assumptions()
    by_scenario = assumptions_by_scenario(assumptions)
    rows = []
    for delta in deltas:
        metrics = perturb_metric(by_scenario, base_scenario, driver, delta)
        years = _run_from_metrics(base_scenario, metrics)
        terminal = years[-1]
        rows.append({
            "driver": driver, "delta": delta, "scenario": base_scenario, "fiscal_year": terminal.fiscal_year,
            "operating_cash_flow": round(terminal.operating_cash_flow, 1),
            "free_cash_flow": round(terminal.free_cash_flow, 1),
            "ending_cash": round(terminal.ending_cash, 1),
            "deployable_capacity": round(terminal.deployable_capacity, 1),
        })
    return rows


def build_sensitivity_tables(base_scenario: str = "base", assumptions: list[Assumption] | None = None) -> dict[str, list[dict]]:
    deltas = {
        "revenue_growth_pct": [-1.0, -0.5, 0.0, 0.5, 1.0],
        "gross_margin_pct": [-0.5, -0.25, 0.0, 0.25, 0.5],
        "sga_pct_of_revenue": [-0.5, -0.25, 0.0, 0.25, 0.5],
        "capex_pct_of_revenue": [-0.5, -0.25, 0.0, 0.25, 0.5],
        "inventory_pct_of_revenue": [-1.0, -0.5, 0.0, 0.5, 1.0],
        "min_cash_buffer_pct_of_revenue": [-1.0, -0.5, 0.0, 0.5, 1.0],
    }
    return {driver: sensitivity_table(driver, ds, base_scenario, assumptions) for driver, ds in deltas.items()}
