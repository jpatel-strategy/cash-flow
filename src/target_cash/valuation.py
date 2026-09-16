"""Milestone 4: a restrained DCF valuation layer built on top of the
Milestone 3 forecast engine.

**This is a scenario-based model, not investment advice, not a price
target, and not a prediction of Target's actual future stock price.**
Every assumption below is either (a) reused, cited, from the already-
validated Milestone 3 operating forecast (never duplicated or silently
re-derived differently), or (b) a NEW, explicitly-labeled valuation-only
assumption (WACC components, terminal growth) kept in its own
ValuationAssumption dataclass, never mixed into forecast.Assumption.

Data-availability limitation, stated once here and repeated wherever it
matters: this project's registered source set (docs/sources.csv) is SEC
filings only -- no market price feed, no analyst consensus, no live
Treasury-yield or equity-risk-premium data source is available. WACC
components (risk-free rate, equity risk premium, beta) are therefore
ILLUSTRATIVE, GENERAL-MARKET INPUTS, not asserted as verified facts about
Target specifically, and capital-structure weights use a target/policy
split rather than market-value weights (computing market-value weights
would require the market value of equity -- circular with the very
equity value this model is trying to estimate, and no live share price
is available regardless). This is disclosed, not fabricated: every
ValuationAssumption here carries review_status='proposed' and a
rationale explaining exactly this limitation.

No forecast fact is modified. No information after FORECAST_INFORMATION_
CUTOFF (2026-03-11, the FY2025 10-K) is used anywhere in this module.
"""
from __future__ import annotations

from dataclasses import dataclass

from target_cash import forecast as f

VALUATION_INFORMATION_CUTOFF = f.FORECAST_INFORMATION_CUTOFF  # same real-world cutoff as the operating forecast
VALUATION_INFORMATION_CUTOFF_ACCESSION = f.FORECAST_INFORMATION_CUTOFF_ACCESSION


@dataclass(frozen=True)
class ValuationAssumption:
    assumption_id: str
    metric: str
    value: float
    unit: str
    rationale: str
    source_evidence: str
    information_cutoff: str = VALUATION_INFORMATION_CUTOFF
    review_status: str = "proposed"
    version: str = "v1"


def build_valuation_assumptions() -> list[ValuationAssumption]:
    """One shared set of valuation-only assumptions, applied uniformly across
    Base/Upside/Downside -- WACC and terminal growth are properties of the
    market and the long-run economy, not of which operating scenario plays
    out, so they are NOT varied by scenario (a deliberate, documented
    choice: scenario differences in this DCF come entirely from differing
    operating cash flows, never from cherry-picking a friendlier discount
    rate for the friendlier scenario).
    """
    return [
        ValuationAssumption(
            "val_risk_free_rate", "risk_free_rate_pct", 4.5, "percent",
            "Illustrative long-term risk-free-rate proxy. No live Treasury-yield source is in the "
            "registered source set (SEC filings only) -- this is a general, round-number market "
            "input, not a fetched or verified rate as of the cutoff date.",
            "General market convention; not derived from a registered source.",
        ),
        ValuationAssumption(
            "val_equity_risk_premium", "equity_risk_premium_pct", 5.5, "percent",
            "Illustrative long-run US equity risk premium. No live market-data source is in the "
            "registered source set -- a commonly-cited long-run range (roughly 5-6%), not a "
            "verified current figure.",
            "General market convention; not derived from a registered source.",
        ),
        ValuationAssumption(
            "val_beta", "beta", 1.0, "ratio",
            "Illustrative unlevered-market-sensitivity proxy (beta=1.0, i.e. average market "
            "sensitivity). Target's actual regression beta would come from a market-data provider "
            "not in the registered source set -- this is a neutral placeholder, not a measured value.",
            "Not derived from a registered source -- no market price data available.",
        ),
        ValuationAssumption(
            "val_target_equity_weight", "target_equity_weight_pct", 85.0, "percent",
            "Target/policy capital-structure weight, not a market-value weight -- computing a "
            "market-value weight requires the market value of equity, which is circular with the "
            "equity value this DCF estimates, and no live share price is available regardless. "
            "85%/15% approximates a well-capitalized, investment-grade retailer's typical structure.",
            "Policy choice; not derived from a registered source.",
        ),
        ValuationAssumption(
            "val_target_debt_weight", "target_debt_weight_pct", 15.0, "percent",
            "See val_target_equity_weight -- the complementary weight.",
            "Policy choice; not derived from a registered source.",
        ),
        ValuationAssumption(
            "val_cost_of_debt", "cost_of_debt_pct", 3.1, "percent",
            "Pre-tax cost of debt: reuses the BASE scenario's own interest_rate_pct operating "
            "assumption (asm_interest_rate_base, itself grounded in the FY2024-FY2025 implied rate "
            "on average total_debt_gaap) as a single, flat, scenario-invariant proxy for Target's "
            "current borrowing cost -- grounded in real historical data, unlike the equity-side "
            "CAPM inputs above.",
            "Cites asm_interest_rate_base (forecast.py); ultimately grounded in FY2024-FY2025 "
            "interest_expense/total_debt_gaap.",
        ),
        ValuationAssumption(
            "val_tax_rate_for_wacc", "tax_rate_for_wacc_pct", 22.2, "percent",
            "Reuses the BASE scenario's flat effective_tax_rate_pct operating assumption "
            "(asm_tax_rate_base) as WACC's single, flat, scenario-invariant tax shield rate -- "
            "consistent with cost_of_debt_pct's own BASE-scenario sourcing.",
            "Cites asm_tax_rate_base (forecast.py).",
        ),
        ValuationAssumption(
            "val_terminal_growth", "terminal_growth_pct", 2.5, "percent",
            "Perpetuity growth rate for the Gordon Growth terminal value, held conservatively at "
            "roughly long-run nominal GDP growth -- well below WACC (required for a finite, "
            "economically meaningful terminal value) and below every scenario's own explicit-period "
            "revenue growth assumption, so the terminal period does not implicitly assume Target "
            "outgrows the broader economy forever.",
            "General long-run macro convention; not derived from a registered source.",
        ),
    ]


def valuation_assumptions_by_metric(assumptions: list[ValuationAssumption]) -> dict[str, float]:
    return {a.metric: a.value for a in assumptions}


def compute_wacc(assumptions_by_metric: dict[str, float]) -> float:
    m = assumptions_by_metric
    cost_of_equity = m["risk_free_rate_pct"] + m["beta"] * m["equity_risk_premium_pct"]
    after_tax_cost_of_debt = m["cost_of_debt_pct"] * (1 - m["tax_rate_for_wacc_pct"] / 100)
    wacc = (
        cost_of_equity * m["target_equity_weight_pct"] / 100
        + after_tax_cost_of_debt * m["target_debt_weight_pct"] / 100
    )
    return wacc


# --- Unlevered free cash flow ------------------------------------------------

def unlevered_free_cash_flow(y: f.ForecastYear) -> float:
    """UFCF_t = EBIT_t*(1 - tax_rate_t) + D&A_t + other_operating_cf_t - CapEx_t - delta_NWC_t

    EBIT = operating_income (pre-interest, pre-other-income -- genuinely
    unlevered). D&A = da_cfo_addback (the full cash-flow-statement add-back,
    same metric the operating forecast's own CFO construction uses -- never
    the smaller opex-line D&A, which would understate the add-back). Working
    capital investment (delta_NWC, a USE of cash when positive) is the
    negative of the already-computed inventory_cash_impact + ap_cash_impact,
    so this formula uses those two SIGNED cash-impact figures directly
    (adding them, not subtracting) rather than re-deriving balance deltas
    from scratch. See reconcile_ufcf_to_levered_fcf for the exact, tested
    reconciliation back to forecast.ForecastYear.free_cash_flow (item: DCF
    "reconciliation to forecast cash flows").
    """
    tax_rate = y.effective_tax_rate_pct / 100
    nopat = y.operating_income * (1 - tax_rate)
    return nopat + y.da_cfo_addback + y.other_operating_cf - y.capital_expenditure + y.inventory_cash_impact + y.ap_cash_impact


def reconcile_ufcf_to_levered_fcf(y: f.ForecastYear) -> dict:
    """UFCF = levered FCF + after-tax interest expense - after-tax net other
    income. Levering UP again (adding back after-tax interest, since UFCF
    assumes no debt; removing after-tax net other income, since UFCF
    excludes non-operating income) must reproduce the operating forecast's
    OWN free_cash_flow figure exactly -- proves UFCF is not an independently
    invented number disconnected from the already-validated cash-flow model.
    """
    tax_rate = y.effective_tax_rate_pct / 100
    ufcf = unlevered_free_cash_flow(y)
    bridge = y.free_cash_flow + (1 - tax_rate) * (y.interest_expense - y.net_other_income)
    return {
        "scenario": y.scenario, "fiscal_year": y.fiscal_year,
        "ufcf": ufcf, "levered_fcf": y.free_cash_flow,
        "bridge_value": bridge, "reconciles": abs(ufcf - bridge) <= 1e-6 * max(1.0, abs(bridge)),
    }


# --- DCF ----------------------------------------------------------------

@dataclass(frozen=True)
class DCFResult:
    scenario: str
    wacc_pct: float
    terminal_growth_pct: float
    ufcf_by_year: dict  # {fiscal_year: ufcf}
    pv_ufcf_by_year: dict  # {fiscal_year: discounted ufcf}
    pv_explicit_period: float
    terminal_year_ufcf: float
    terminal_value_undiscounted: float
    pv_terminal_value: float
    enterprise_value: float
    valuation_date_net_debt: float
    equity_value: float
    valuation_date_diluted_shares: float
    implied_value_per_share: float


def run_dcf(years: list[f.ForecastYear], assumptions: list[ValuationAssumption] | None = None) -> DCFResult:
    """Discounts the explicit FY2026-FY2030 UFCF stream plus a Gordon Growth
    terminal value back to the valuation date -- the END of FY2025 (the
    start of the forecast horizon), NOT any later date. Net debt and diluted
    shares used in the enterprise-to-equity bridge are FY2025 ACTUALS
    (HISTORICAL, historical facts) -- never a forecast year's projected net
    debt or share count, which would value the company as of some other,
    inconsistent date than the cash flows are discounted to. See
    check_terminal_value_period_consistency and check_no_debt_or_lease_double_counting.
    """
    assumptions = assumptions if assumptions is not None else build_valuation_assumptions()
    m = valuation_assumptions_by_metric(assumptions)
    wacc = compute_wacc(m)
    g = m["terminal_growth_pct"]

    if wacc <= g:
        raise ValueError(f"WACC ({wacc:.2f}%) must exceed terminal growth ({g:.2f}%) for a finite terminal value.")

    ufcf_by_year = {}
    pv_ufcf_by_year = {}
    pv_explicit_period = 0.0
    for i, y in enumerate(years, start=1):
        ufcf = unlevered_free_cash_flow(y)
        pv = ufcf / (1 + wacc / 100) ** i
        ufcf_by_year[y.fiscal_year] = ufcf
        pv_ufcf_by_year[y.fiscal_year] = pv
        pv_explicit_period += pv

    terminal_year_ufcf = ufcf_by_year[years[-1].fiscal_year]
    terminal_value_undiscounted = terminal_year_ufcf * (1 + g / 100) / (wacc / 100 - g / 100)
    n_periods = len(years)
    pv_terminal_value = terminal_value_undiscounted / (1 + wacc / 100) ** n_periods

    enterprise_value = pv_explicit_period + pv_terminal_value

    # Valuation-date (FY2025 actual) net debt -- valuation_net_debt_excluding_leases,
    # the exact measure Milestone 2's own decisions.md entry designated as
    # "The DCF enterprise-to-equity bridge ... will use ... by default."
    # total_debt_gaap already excludes finance leases (Milestone 2 debt
    # inventory), so this is never double-counted with finance_lease_liabilities.
    net_debt = f.HISTORICAL["total_debt_gaap"][2025] - f.HISTORICAL["cash_and_equivalents_balance_sheet"][2025]
    diluted_shares = f.HISTORICAL["diluted_shares"][2025]

    equity_value = enterprise_value - net_debt
    implied_value_per_share = equity_value / diluted_shares

    return DCFResult(
        scenario=years[0].scenario, wacc_pct=wacc, terminal_growth_pct=g,
        ufcf_by_year=ufcf_by_year, pv_ufcf_by_year=pv_ufcf_by_year, pv_explicit_period=pv_explicit_period,
        terminal_year_ufcf=terminal_year_ufcf, terminal_value_undiscounted=terminal_value_undiscounted,
        pv_terminal_value=pv_terminal_value, enterprise_value=enterprise_value,
        valuation_date_net_debt=net_debt, equity_value=equity_value,
        valuation_date_diluted_shares=diluted_shares, implied_value_per_share=implied_value_per_share,
    )


def run_dcf_all_scenarios(
    forecasts: dict[str, list[f.ForecastYear]], assumptions: list[ValuationAssumption] | None = None
) -> dict[str, DCFResult]:
    return {s: run_dcf(years, assumptions) for s, years in forecasts.items()}


# --- Valuation bridge -----------------------------------------------------

def valuation_bridge(result: DCFResult) -> list[dict]:
    """PV of explicit-period UFCF -> + PV of terminal value -> = Enterprise
    Value -> - net debt -> = Equity Value -> / diluted shares -> = implied
    value per share. Every step is a real, already-computed DCFResult field
    -- this function only orders and labels them for presentation.
    """
    return [
        {"step": 1, "label": "PV of explicit-period UFCF (FY2026-FY2030)", "value": result.pv_explicit_period},
        {"step": 2, "label": "+ PV of terminal value", "value": result.pv_terminal_value},
        {"step": 3, "label": "= Enterprise value", "value": result.enterprise_value},
        {"step": 4, "label": "- Net debt (FY2025 actual, valuation_net_debt_excluding_leases)",
         "value": -result.valuation_date_net_debt},
        {"step": 5, "label": "= Equity value", "value": result.equity_value},
        {"step": 6, "label": "/ Diluted shares (FY2025 actual)", "value": result.valuation_date_diluted_shares},
        {"step": 7, "label": "= Implied value per share", "value": result.implied_value_per_share},
    ]


# --- Validation checks ------------------------------------------------------

@dataclass(frozen=True)
class ValuationCheckResult:
    check_name: str
    scenario: str | None
    status: str  # 'PASS' | 'FAIL'
    detail: str
    fiscal_year: int | None = None


def check_ufcf_reconciliation(forecasts: dict[str, list[f.ForecastYear]]) -> list[ValuationCheckResult]:
    results = []
    for scenario, years in forecasts.items():
        for y in years:
            r = reconcile_ufcf_to_levered_fcf(y)
            results.append(ValuationCheckResult(
                "ufcf_reconciles_to_levered_fcf", scenario, "PASS" if r["reconciles"] else "FAIL",
                f"FY{y.fiscal_year}: ufcf={r['ufcf']:.1f}, bridge={r['bridge_value']:.1f}",
                fiscal_year=y.fiscal_year,
            ))
    return results


def check_terminal_value_period_consistency(result: DCFResult, years: list[f.ForecastYear]) -> ValuationCheckResult:
    """Terminal value must be grown from the LAST explicit forecast year's
    UFCF by exactly one period, and discounted back by exactly as many
    periods as there are explicit forecast years -- never a different year's
    UFCF, and never a mismatched discount period count (e.g. discounting the
    terminal value by 4 periods when there are 5 explicit years, which would
    silently double-count or drop a year of value).
    """
    last_year = years[-1].fiscal_year
    expected_terminal_base = result.ufcf_by_year[last_year]
    ok_base = abs(result.terminal_year_ufcf - expected_terminal_base) < 1e-6
    expected_tv = result.terminal_year_ufcf * (1 + result.terminal_growth_pct / 100) / (
        result.wacc_pct / 100 - result.terminal_growth_pct / 100
    )
    ok_tv_formula = abs(result.terminal_value_undiscounted - expected_tv) < 1e-6 * max(1.0, abs(expected_tv))
    expected_pv_tv = result.terminal_value_undiscounted / (1 + result.wacc_pct / 100) ** len(years)
    ok_discount_periods = abs(result.pv_terminal_value - expected_pv_tv) < 1e-6 * max(1.0, abs(expected_pv_tv))
    ok = ok_base and ok_tv_formula and ok_discount_periods
    return ValuationCheckResult(
        "terminal_value_period_consistency", result.scenario, "PASS" if ok else "FAIL",
        f"terminal base year={last_year}, discount periods={len(years)}, "
        f"terminal_year_ufcf matches FY{last_year}={ok_base}, TV formula={ok_tv_formula}, "
        f"discount periods={ok_discount_periods}",
    )


def check_no_debt_or_lease_double_counting(result: DCFResult) -> ValuationCheckResult:
    """Net debt used in the EV-to-equity bridge must equal
    total_debt_gaap - cash EXACTLY (the valuation_net_debt_excluding_leases
    measure) -- proving finance_lease_liabilities was never separately added
    on top (total_debt_gaap already excludes leases per the Milestone 2 debt
    inventory; adding leases again here would double-count them).
    """
    expected = f.HISTORICAL["total_debt_gaap"][2025] - f.HISTORICAL["cash_and_equivalents_balance_sheet"][2025]
    ok = abs(result.valuation_date_net_debt - expected) < 1e-6
    return ValuationCheckResult(
        "no_debt_or_lease_double_counting", result.scenario, "PASS" if ok else "FAIL",
        f"net_debt={result.valuation_date_net_debt:.1f} vs total_debt_gaap-cash={expected:.1f} "
        f"(finance_lease_liabilities={f.HISTORICAL['finance_lease_liabilities'][2025]:.1f} correctly excluded)",
    )


def check_valuation_date_consistency(result: DCFResult) -> ValuationCheckResult:
    """Net debt and diluted shares must both be FY2025 ACTUALS (the
    valuation date), never a forecast year's projected figure -- otherwise
    the enterprise-value-to-per-share bridge would mix cash flows discounted
    to one date with a balance-sheet snapshot from a different date.
    """
    ok_debt = abs(
        result.valuation_date_net_debt
        - (f.HISTORICAL["total_debt_gaap"][2025] - f.HISTORICAL["cash_and_equivalents_balance_sheet"][2025])
    ) < 1e-6
    ok_shares = abs(result.valuation_date_diluted_shares - f.HISTORICAL["diluted_shares"][2025]) < 1e-6
    ok = ok_debt and ok_shares
    return ValuationCheckResult(
        "valuation_date_consistency", result.scenario, "PASS" if ok else "FAIL",
        f"net_debt uses FY2025 actuals={ok_debt}, diluted_shares uses FY2025 actual={ok_shares}",
    )


def check_wacc_exceeds_terminal_growth(result: DCFResult) -> ValuationCheckResult:
    ok = result.wacc_pct > result.terminal_growth_pct
    return ValuationCheckResult(
        "wacc_exceeds_terminal_growth", result.scenario, "PASS" if ok else "FAIL",
        f"WACC={result.wacc_pct:.2f}% vs terminal growth={result.terminal_growth_pct:.2f}%",
    )


def check_wacc_scenario_invariant(results: dict[str, DCFResult]) -> ValuationCheckResult:
    """WACC and terminal growth must be IDENTICAL across all 3 scenarios --
    scenario differences in enterprise value must come entirely from
    differing operating cash flows, never from a friendlier discount rate
    quietly applied to a friendlier scenario."""
    waccs = {r.wacc_pct for r in results.values()}
    growths = {r.terminal_growth_pct for r in results.values()}
    ok = len(waccs) == 1 and len(growths) == 1
    return ValuationCheckResult(
        "wacc_and_terminal_growth_scenario_invariant", None, "PASS" if ok else "FAIL",
        f"distinct WACC values across scenarios: {waccs}; distinct terminal growth values: {growths}",
    )


def run_all_valuation_checks(
    forecasts: dict[str, list[f.ForecastYear]], results: dict[str, DCFResult]
) -> list[ValuationCheckResult]:
    checks = list(check_ufcf_reconciliation(forecasts))
    for scenario, result in results.items():
        checks.append(check_terminal_value_period_consistency(result, forecasts[scenario]))
        checks.append(check_no_debt_or_lease_double_counting(result))
        checks.append(check_valuation_date_consistency(result))
        checks.append(check_wacc_exceeds_terminal_growth(result))
    checks.append(check_wacc_scenario_invariant(results))
    return checks


# --- Sensitivities -----------------------------------------------------

def wacc_terminal_growth_sensitivity(
    years: list[f.ForecastYear], wacc_deltas: list[float], growth_deltas: list[float],
    assumptions: list[ValuationAssumption] | None = None,
) -> dict:
    assumptions = assumptions if assumptions is not None else build_valuation_assumptions()
    base_m = valuation_assumptions_by_metric(assumptions)
    base_wacc = compute_wacc(base_m)
    base_growth = base_m["terminal_growth_pct"]

    grid = []
    for wd in wacc_deltas:
        row = {"wacc_delta": wd, "wacc_pct": base_wacc + wd, "cells": []}
        for gd in growth_deltas:
            growth = base_growth + gd
            if base_wacc + wd <= growth:
                row["cells"].append({"growth_delta": gd, "terminal_growth_pct": growth, "implied_value_per_share": None})
                continue
            m2 = dict(base_m)
            # Directly override the effective WACC by scaling cost/weight inputs is awkward;
            # instead recompute UFCF-independent EV using the overridden wacc/growth directly.
            wacc_pct = base_wacc + wd
            ufcf_by_year = {y.fiscal_year: unlevered_free_cash_flow(y) for y in years}
            pv_explicit = sum(ufcf / (1 + wacc_pct / 100) ** i for i, ufcf in enumerate(ufcf_by_year.values(), start=1))
            terminal_ufcf = list(ufcf_by_year.values())[-1]
            tv = terminal_ufcf * (1 + growth / 100) / (wacc_pct / 100 - growth / 100)
            pv_tv = tv / (1 + wacc_pct / 100) ** len(years)
            ev = pv_explicit + pv_tv
            net_debt = f.HISTORICAL["total_debt_gaap"][2025] - f.HISTORICAL["cash_and_equivalents_balance_sheet"][2025]
            equity_value = ev - net_debt
            per_share = equity_value / f.HISTORICAL["diluted_shares"][2025]
            row["cells"].append({"growth_delta": gd, "terminal_growth_pct": growth, "implied_value_per_share": per_share})
        grid.append(row)
    return {"scenario": years[0].scenario, "base_wacc_pct": base_wacc, "base_terminal_growth_pct": base_growth, "grid": grid}


def operating_margin_revenue_growth_sensitivity(
    scenario: str, gross_margin_deltas: list[float], revenue_growth_deltas: list[float],
    forecast_assumptions: list[f.Assumption] | None = None, valuation_assumptions: list[ValuationAssumption] | None = None,
) -> dict:
    """Perturbs gross_margin_pct and revenue_growth_pct simultaneously (a
    proxy for 'operating margin x revenue growth') and reports the implied
    value per share for each combination -- an operating-side sensitivity,
    distinct from the WACC/terminal-growth (valuation-side) sensitivity
    above.
    """
    forecast_assumptions = forecast_assumptions if forecast_assumptions is not None else f.build_assumptions()
    valuation_assumptions = valuation_assumptions if valuation_assumptions is not None else build_valuation_assumptions()
    by_scenario = f.assumptions_by_scenario(forecast_assumptions)

    grid = []
    for md in gross_margin_deltas:
        row = {"gross_margin_delta": md, "cells": []}
        for gd in revenue_growth_deltas:
            metrics = {k: dict(v) for k, v in by_scenario[scenario].items()}
            metrics["gross_margin_pct"] = {fy: v + md for fy, v in metrics["gross_margin_pct"].items()}
            metrics["revenue_growth_pct"] = {fy: v + gd for fy, v in metrics["revenue_growth_pct"].items()}
            years = f._run_from_metrics(scenario, metrics)
            result = run_dcf(years, valuation_assumptions)
            row["cells"].append({
                "revenue_growth_delta": gd, "implied_value_per_share": result.implied_value_per_share,
                "enterprise_value": result.enterprise_value,
            })
        grid.append(row)
    return {"scenario": scenario, "grid": grid}
