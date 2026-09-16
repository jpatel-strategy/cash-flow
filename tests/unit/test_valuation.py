"""Unit tests for target_cash.valuation: the Milestone 4 DCF layer.

Every number here is computed live against the real Milestone 3 forecast
engine (target_cash.forecast) -- never a hand-picked or hardcoded
expectation disconnected from the actual formulas, matching this
project's established testing discipline.
"""
import pytest

from target_cash import forecast as f
from target_cash import valuation as v


@pytest.fixture(scope="module")
def forecasts():
    return f.run_all_scenarios()


@pytest.fixture(scope="module")
def val_assumptions():
    return v.build_valuation_assumptions()


@pytest.fixture(scope="module")
def dcf_results(forecasts, val_assumptions):
    return v.run_dcf_all_scenarios(forecasts, val_assumptions)


# --- Assumptions -------------------------------------------------------------


def test_valuation_assumptions_are_separate_from_operating_assumptions():
    val_assumptions = v.build_valuation_assumptions()
    operating_assumptions = f.build_assumptions()
    val_ids = {a.assumption_id for a in val_assumptions}
    op_ids = {a.assumption_id for a in operating_assumptions}
    assert val_ids.isdisjoint(op_ids)
    assert not isinstance(val_assumptions[0], f.Assumption)


def test_valuation_assumptions_never_scenario_specific():
    """Unlike forecast.Assumption, ValuationAssumption has no `scenario`
    field at all -- the type system itself prevents a per-scenario WACC."""
    for a in v.build_valuation_assumptions():
        assert not hasattr(a, "scenario")


def test_valuation_assumptions_all_proposed_status():
    for a in v.build_valuation_assumptions():
        assert a.review_status == "proposed"
        assert a.information_cutoff == v.VALUATION_INFORMATION_CUTOFF


def test_valuation_assumptions_cite_illustrative_limitation_for_market_inputs():
    by_metric = {a.metric: a for a in v.build_valuation_assumptions()}
    for metric in ("risk_free_rate_pct", "equity_risk_premium_pct", "beta"):
        assert "illustrative" in by_metric[metric].rationale.lower() or "not derived from a registered source" in by_metric[metric].source_evidence.lower()


def test_cost_of_debt_and_tax_rate_grounded_in_operating_forecast():
    by_metric = {a.metric: a for a in v.build_valuation_assumptions()}
    assert "asm_interest_rate_base" in by_metric["cost_of_debt_pct"].rationale
    assert "asm_tax_rate_base" in by_metric["tax_rate_for_wacc_pct"].rationale


def test_wacc_is_between_cost_of_debt_and_cost_of_equity():
    m = v.valuation_assumptions_by_metric(v.build_valuation_assumptions())
    wacc = v.compute_wacc(m)
    cost_of_equity = m["risk_free_rate_pct"] + m["beta"] * m["equity_risk_premium_pct"]
    after_tax_cod = m["cost_of_debt_pct"] * (1 - m["tax_rate_for_wacc_pct"] / 100)
    assert after_tax_cod < wacc < cost_of_equity


# --- UFCF and reconciliation -------------------------------------------------


def test_ufcf_reconciles_to_levered_fcf_every_scenario_year(forecasts):
    for years in forecasts.values():
        for y in years:
            r = v.reconcile_ufcf_to_levered_fcf(y)
            assert r["reconciles"], r


def test_ufcf_excludes_interest_and_net_other_income(forecasts):
    """UFCF must differ from levered FCF whenever interest expense or net
    other income is nonzero -- proving it's genuinely unlevered, not just a
    renamed copy of the levered figure."""
    y = forecasts["base"][0]
    assert y.interest_expense != 0
    ufcf = v.unlevered_free_cash_flow(y)
    assert ufcf != pytest.approx(y.free_cash_flow)


def test_ufcf_uses_da_cfo_addback_not_opex_da(forecasts):
    """A regression guard against the item-5 double-counting mistake: UFCF
    must use the full CFO D&A add-back, not the smaller opex-line D&A."""
    y = forecasts["base"][0]
    tax_rate = y.effective_tax_rate_pct / 100
    wrong_ufcf = (
        y.operating_income * (1 - tax_rate) + y.depreciation_amortization_opex + y.other_operating_cf
        - y.capital_expenditure + y.inventory_cash_impact + y.ap_cash_impact
    )
    assert v.unlevered_free_cash_flow(y) != pytest.approx(wrong_ufcf)


def test_check_ufcf_reconciliation_all_pass(forecasts):
    checks = v.check_ufcf_reconciliation(forecasts)
    assert len(checks) == 3 * len(f.FORECAST_YEARS)
    assert all(c.status == "PASS" for c in checks)


def test_check_ufcf_reconciliation_catches_a_broken_ufcf(forecasts, monkeypatch):
    import dataclasses
    y = forecasts["base"][0]
    broken = dataclasses.replace(y, operating_income=y.operating_income + 10000)
    r = v.reconcile_ufcf_to_levered_fcf(broken)
    assert not r["reconciles"]


# --- DCF mechanics ------------------------------------------------------


def test_run_dcf_produces_positive_enterprise_value(dcf_results):
    for result in dcf_results.values():
        assert result.enterprise_value > 0
        assert result.equity_value != 0
        assert result.implied_value_per_share != 0


def test_run_dcf_scenario_ordering_base_upside_downside(dcf_results):
    assert dcf_results["upside"].enterprise_value > dcf_results["base"].enterprise_value > dcf_results["downside"].enterprise_value
    assert dcf_results["upside"].implied_value_per_share > dcf_results["base"].implied_value_per_share > dcf_results["downside"].implied_value_per_share


def test_run_dcf_raises_if_wacc_does_not_exceed_growth(forecasts):
    bad_assumptions = [
        dataclasses_replace(a, value=1.0) if a.metric == "terminal_growth_pct" else a
        for a in v.build_valuation_assumptions()
    ]
    # Force terminal growth above WACC by cranking it very high instead.
    import dataclasses
    bad_assumptions = [
        dataclasses.replace(a, value=50.0) if a.metric == "terminal_growth_pct" else a
        for a in v.build_valuation_assumptions()
    ]
    with pytest.raises(ValueError, match="must exceed"):
        v.run_dcf(forecasts["base"], bad_assumptions)


def dataclasses_replace(a, **kwargs):
    import dataclasses
    return dataclasses.replace(a, **kwargs)


def test_pv_explicit_period_equals_sum_of_pv_by_year(dcf_results):
    for result in dcf_results.values():
        assert result.pv_explicit_period == pytest.approx(sum(result.pv_ufcf_by_year.values()))


def test_terminal_value_formula_gordon_growth(dcf_results):
    for result in dcf_results.values():
        expected = result.terminal_year_ufcf * (1 + result.terminal_growth_pct / 100) / (
            result.wacc_pct / 100 - result.terminal_growth_pct / 100
        )
        assert result.terminal_value_undiscounted == pytest.approx(expected)


def test_valuation_bridge_steps_sum_correctly(dcf_results):
    """Steps 1, 2, and 4 are the genuinely additive components (PV of
    explicit UFCF, PV of terminal value, and negative net debt); steps 3, 5,
    and 7 are running subtotals/labels ("=" rows), not separate contributions
    -- summing all 5 of steps[:5] would double-count the enterprise-value
    subtotal on top of its own components."""
    result = dcf_results["base"]
    steps = {s["step"]: s["value"] for s in v.valuation_bridge(result)}
    additive_total = steps[1] + steps[2] + steps[4]
    assert additive_total == pytest.approx(result.equity_value)
    assert steps[3] == pytest.approx(result.enterprise_value)
    assert steps[5] == pytest.approx(result.equity_value)
    assert steps[7] == pytest.approx(result.equity_value / result.valuation_date_diluted_shares)


# --- Checks: periods, double-counting, consistency --------------------------


def test_check_terminal_value_period_consistency_passes(forecasts, dcf_results):
    for scenario, result in dcf_results.items():
        check = v.check_terminal_value_period_consistency(result, forecasts[scenario])
        assert check.status == "PASS", check.detail


def test_check_terminal_value_period_consistency_catches_wrong_base_year(forecasts, dcf_results):
    import dataclasses
    result = dcf_results["base"]
    corrupted = dataclasses.replace(result, terminal_year_ufcf=result.terminal_year_ufcf + 500)
    check = v.check_terminal_value_period_consistency(corrupted, forecasts["base"])
    assert check.status == "FAIL"


def test_check_no_debt_or_lease_double_counting_passes(dcf_results):
    for result in dcf_results.values():
        check = v.check_no_debt_or_lease_double_counting(result)
        assert check.status == "PASS", check.detail


def test_check_no_debt_or_lease_double_counting_catches_added_leases(dcf_results):
    import dataclasses
    result = dcf_results["base"]
    corrupted = dataclasses.replace(
        result, valuation_date_net_debt=result.valuation_date_net_debt + f.HISTORICAL["finance_lease_liabilities"][2025]
    )
    check = v.check_no_debt_or_lease_double_counting(corrupted)
    assert check.status == "FAIL"


def test_check_valuation_date_consistency_passes(dcf_results):
    for result in dcf_results.values():
        check = v.check_valuation_date_consistency(result)
        assert check.status == "PASS", check.detail


def test_check_valuation_date_consistency_catches_a_future_share_count(dcf_results):
    import dataclasses
    result = dcf_results["base"]
    corrupted = dataclasses.replace(result, valuation_date_diluted_shares=400.0)  # not FY2025's actual 455.6
    check = v.check_valuation_date_consistency(corrupted)
    assert check.status == "FAIL"


def test_check_wacc_exceeds_terminal_growth_passes(dcf_results):
    for result in dcf_results.values():
        assert v.check_wacc_exceeds_terminal_growth(result).status == "PASS"


def test_check_wacc_scenario_invariant_passes(dcf_results):
    check = v.check_wacc_scenario_invariant(dcf_results)
    assert check.status == "PASS"


def test_check_wacc_scenario_invariant_catches_a_per_scenario_wacc(dcf_results):
    import dataclasses
    corrupted = dict(dcf_results)
    corrupted["upside"] = dataclasses.replace(corrupted["upside"], wacc_pct=corrupted["upside"].wacc_pct + 1.0)
    check = v.check_wacc_scenario_invariant(corrupted)
    assert check.status == "FAIL"


def test_run_all_valuation_checks_all_pass(forecasts, dcf_results):
    checks = v.run_all_valuation_checks(forecasts, dcf_results)
    fails = [c for c in checks if c.status == "FAIL"]
    assert fails == []


# --- Sensitivities -----------------------------------------------------


def test_wacc_terminal_growth_sensitivity_monotonic(forecasts, val_assumptions):
    grid = v.wacc_terminal_growth_sensitivity(
        forecasts["base"], [-1.0, -0.5, 0.0, 0.5, 1.0], [-1.0, -0.5, 0.0, 0.5, 1.0], val_assumptions
    )
    # Higher WACC (larger delta) -> lower value per share, holding growth fixed.
    middle_col = [row["cells"][2]["implied_value_per_share"] for row in grid["grid"]]
    assert middle_col == sorted(middle_col, reverse=True)
    # Higher terminal growth -> higher value per share, holding WACC fixed.
    middle_row = [cell["implied_value_per_share"] for cell in grid["grid"][2]["cells"]]
    assert middle_row == sorted(middle_row)


def test_wacc_terminal_growth_sensitivity_handles_growth_exceeding_wacc(forecasts, val_assumptions):
    grid = v.wacc_terminal_growth_sensitivity(forecasts["base"], [-5.0], [10.0], val_assumptions)
    assert grid["grid"][0]["cells"][0]["implied_value_per_share"] is None  # never a fabricated/garbage number


def test_operating_margin_revenue_growth_sensitivity_monotonic():
    grid = v.operating_margin_revenue_growth_sensitivity("base", [-0.5, 0.0, 0.5], [-1.0, 0.0, 1.0])
    middle_row = [c["implied_value_per_share"] for c in grid["grid"][1]["cells"]]
    assert middle_row == sorted(middle_row)
    first_col = [row["cells"][0]["implied_value_per_share"] for row in grid["grid"]]
    assert first_col == sorted(first_col)


def test_operating_margin_revenue_growth_sensitivity_never_uses_persisted_forecast():
    """Confirms the sensitivity re-derives its own scenario run rather than
    reading any persisted database state (pure in-memory, same discipline
    as forecast.py's own sensitivity functions)."""
    import inspect
    src = inspect.getsource(v.operating_margin_revenue_growth_sensitivity)
    assert "sqlite3" not in src and "conn." not in src
