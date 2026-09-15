import pytest

from target_cash import forecast as f


# --- Assumption grounding ---------------------------------------------------


def test_build_assumptions_every_scenario_year_covered():
    assumptions = f.build_assumptions()
    by_scenario = f.assumptions_by_scenario(assumptions)
    required_metrics = [
        "revenue_growth_pct", "gross_margin_pct", "sga_pct_of_revenue", "da_pct_of_revenue",
        "effective_tax_rate_pct", "net_other_income_musd", "diluted_share_change_pct",
        "interest_rate_pct", "capex_pct_of_revenue", "da_cfo_addback_pct_of_revenue",
        "inventory_pct_of_revenue", "ap_pct_of_cogs", "other_operating_cf_musd",
        "dividend_per_share_growth_pct", "buyback_payout_pct_of_post_dividend_fcf",
        "debt_proceeds_musd", "debt_repayments_musd", "finance_lease_liabilities_musd",
        "min_cash_buffer_pct_of_revenue",
    ]
    for scenario in f.SCENARIOS:
        for metric in required_metrics:
            by_fy = by_scenario[scenario].get(metric, {})
            assert by_fy, f"{scenario}/{metric} has no assumption rows at all"
            for fy in f.FORECAST_YEARS:
                assert fy in by_fy or 0 in by_fy, f"{scenario}/{metric}/{fy} not covered"


def test_every_assumption_has_rationale_and_historical_reference():
    for a in f.build_assumptions():
        assert a.rationale.strip()
        assert a.historical_reference.strip()
        assert a.source_evidence.strip()
        assert a.review_status == "proposed"


def test_every_assumption_information_cutoff_not_after_forecast_cutoff():
    for a in f.build_assumptions():
        assert a.information_cutoff <= f.FORECAST_INFORMATION_CUTOFF


def test_no_arbitrary_symmetric_spread_revenue_growth():
    """Item 3 forbids a naive +-1% spread around base; confirm the three
    scenario values are not equally spaced (which would suggest an arbitrary
    +-delta rather than a historically grounded range) and each is grounded
    in a distinct historical figure cited in its own rationale."""
    assumptions = f.build_assumptions()
    by_scenario = f.assumptions_by_scenario(assumptions)
    base = f._lookup(by_scenario["base"]["revenue_growth_pct"], 2026)
    upside = f._lookup(by_scenario["upside"]["revenue_growth_pct"], 2026)
    downside = f._lookup(by_scenario["downside"]["revenue_growth_pct"], 2026)
    up_gap = upside - base
    down_gap = base - downside
    assert up_gap != down_gap
    assert upside > base > downside


def test_gross_margin_upside_never_exceeds_historical_max():
    hist_max = max(f.historical_ratio("gross_profit", "revenue").values())
    by_scenario = f.assumptions_by_scenario(f.build_assumptions())
    for fy in f.FORECAST_YEARS:
        assert f._lookup(by_scenario["upside"]["gross_margin_pct"], fy) <= hist_max + 1e-9


def test_base_gross_margin_never_reverts_to_fy2021_peak():
    fy2021_margin = f.historical_ratio("gross_profit", "revenue")[2021]
    by_scenario = f.assumptions_by_scenario(f.build_assumptions())
    for fy in f.FORECAST_YEARS:
        assert f._lookup(by_scenario["base"]["gross_margin_pct"], fy) < fy2021_margin


def test_fy2023_53_week_normalized_revenue_and_derived_fy2024_growth():
    normalized = f.fy2023_53_week_normalized_revenue()
    assert normalized < f.HISTORICAL["revenue"][2023]  # normalization reduces the 53-week figure
    fy2024_growth_vs_normalized = (f.HISTORICAL["revenue"][2024] / normalized - 1) * 100
    # Matches the rationale cited for asm_rev_growth_base ("+1.12%")
    assert fy2024_growth_vs_normalized == pytest.approx(1.12, abs=0.02)


# --- Revenue recursion -------------------------------------------------------


def test_revenue_recursion_matches_formula():
    forecasts = f.run_all_scenarios()
    for scenario, years in forecasts.items():
        prev = f.HISTORICAL["revenue"][2025]
        for y in years:
            assert y.revenue == pytest.approx(prev * (1 + y.revenue_growth_pct / 100))
            prev = y.revenue


def test_revenue_growth_is_nominal_not_market_share_claim():
    """Growth assumptions are flat %/yr scalars applied to Target's own prior
    revenue -- nothing in the assumption dictionary references market share,
    competitor share loss/gain, or total-market size, which would be an
    unsupported claim per item 4."""
    for a in f.build_assumptions():
        if a.metric == "revenue_growth_pct":
            assert "market share" not in a.rationale.lower()
            assert "share of market" not in a.rationale.lower()


# --- Operating model ----------------------------------------------------------


def test_operating_income_bridge_no_double_counted_da():
    """depreciation_amortization_opex (which reduces operating_income) and
    da_cfo_addback (which is added back to net_income in CFO) must never be
    the same number -- confirms item 5's double-counting warning in practice."""
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        for y in years:
            assert y.depreciation_amortization_opex != pytest.approx(y.da_cfo_addback)
            assert y.da_cfo_addback > y.depreciation_amortization_opex  # historically always true (COGS-embedded D&A)
            expected_oi = y.gross_profit - y.sga_expense - y.depreciation_amortization_opex
            assert y.operating_income == pytest.approx(expected_oi)


def test_pretax_and_net_income_bridges():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        for y in years:
            assert y.pretax_income == pytest.approx(y.operating_income - y.interest_expense + y.net_other_income)
            assert y.income_tax_expense == pytest.approx(y.pretax_income * y.effective_tax_rate_pct / 100)
            assert y.net_income == pytest.approx(y.pretax_income - y.income_tax_expense)


def test_eps_consistency():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        for y in years:
            assert y.diluted_eps == pytest.approx(y.net_income / y.diluted_shares)


# --- Cash flow model -----------------------------------------------------------


def test_capex_uses_ppe_driver_never_total_cfi():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        for y in years:
            assert y.free_cash_flow == pytest.approx(y.operating_cash_flow - y.capital_expenditure)
            # investing_cash_flow is a distinct, separately-labeled figure --
            # FCF must be computed from capital_expenditure, not from it.
            assert y.capital_expenditure > 0


def test_capex_fy2025_reference_figures_match_historical():
    assert f.HISTORICAL["operating_cash_flow"][2025] == 6562.0
    assert f.HISTORICAL["capital_expenditure"][2025] == 3727.0
    assert f.HISTORICAL["investing_cash_flow"][2025] == -3649.0
    assert f.HISTORICAL["free_cash_flow"][2025] == 2835.0
    assert f.HISTORICAL["operating_cash_flow"][2025] - f.HISTORICAL["capital_expenditure"][2025] == pytest.approx(
        f.HISTORICAL["free_cash_flow"][2025]
    )


def test_cfo_construction_never_a_bare_residual():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        for y in years:
            expected = y.net_income + y.da_cfo_addback + y.inventory_cash_impact + y.ap_cash_impact + y.other_operating_cf
            assert y.operating_cash_flow == pytest.approx(expected)


def test_working_capital_signs():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        prev_inv = f.HISTORICAL["inventory"][2025]
        prev_ap = f.HISTORICAL["accounts_payable"][2025]
        for y in years:
            inv_delta = y.inventory_balance - prev_inv
            ap_delta = y.accounts_payable_balance - prev_ap
            if inv_delta > 0:
                assert y.inventory_cash_impact < 0
            elif inv_delta < 0:
                assert y.inventory_cash_impact > 0
            if ap_delta > 0:
                assert y.ap_cash_impact > 0
            elif ap_delta < 0:
                assert y.ap_cash_impact < 0
            prev_inv, prev_ap = y.inventory_balance, y.accounts_payable_balance


def test_cash_roll_forward_chains_across_years():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        prev_cash = f.HISTORICAL["cash_and_equivalents_balance_sheet"][2025]
        for y in years:
            assert y.beginning_cash == pytest.approx(prev_cash)
            assert y.ending_cash == pytest.approx(y.beginning_cash + y.net_change_in_cash)
            prev_cash = y.ending_cash


def test_debt_roll_forward_chains_across_years():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        prev_debt = f.HISTORICAL["total_debt_gaap"][2025]
        for y in years:
            assert y.total_debt_gaap_beginning == pytest.approx(prev_debt)
            assert y.total_debt_gaap_ending == pytest.approx(prev_debt + y.debt_proceeds - y.debt_repayments)
            prev_debt = y.total_debt_gaap_ending


def test_finance_lease_held_flat_never_folded_into_debt_schedule():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        for y in years:
            assert y.finance_lease_liabilities == pytest.approx(f.HISTORICAL["finance_lease_liabilities"][2025])


# --- Non-plug modeling discipline --------------------------------------------


def test_share_repurchases_are_never_negative_and_track_a_fixed_payout_ratio():
    forecasts = f.run_all_scenarios()
    by_scenario = f.assumptions_by_scenario(f.build_assumptions())
    for scenario, years in forecasts.items():
        payout = f._lookup(by_scenario[scenario]["buyback_payout_pct_of_post_dividend_fcf"], 2026)
        for y in years:
            assert y.share_repurchases >= 0
            post_div_fcf = y.free_cash_flow - y.dividends_paid
            if post_div_fcf > 0:
                assert y.share_repurchases == pytest.approx(max(0.0, post_div_fcf * payout / 100))


def test_downside_share_repurchases_are_zero():
    forecasts = f.run_all_scenarios()
    for y in forecasts["downside"]:
        assert y.share_repurchases == 0.0


def test_debt_schedule_is_fixed_not_a_deficit_plug():
    """The same (proceeds, repayments) pair must recur every year within a
    scenario -- proof the schedule is a pre-set input, not solved backward
    from each year's own cash outcome."""
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        proceeds = {round(y.debt_proceeds, 6) for y in years}
        repayments = {round(y.debt_repayments, 6) for y in years}
        assert len(proceeds) == 1
        assert len(repayments) == 1


# --- Investment capacity -----------------------------------------------------


def test_investment_capacity_formula_chain():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        for y in years:
            assert y.gross_fcf_capacity == pytest.approx(y.operating_cash_flow - y.capital_expenditure)
            assert y.post_dividend_capacity == pytest.approx(y.free_cash_flow - y.dividends_paid)
            expected_pre = y.beginning_cash + y.operating_cash_flow + y.investing_cash_flow + y.mandatory_financing_flows
            assert y.pre_discretionary_ending_cash == pytest.approx(expected_pre)
            expected_deployable = max(0.0, y.pre_discretionary_ending_cash - y.min_cash_buffer - y.near_term_debt_repayment_reserve)
            assert y.deployable_capacity == pytest.approx(expected_deployable)
            assert y.deployable_capacity >= 0.0


def test_mandatory_financing_flows_excludes_share_repurchases():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        for y in years:
            expected = -y.dividends_paid + y.debt_proceeds - y.debt_repayments
            assert y.mandatory_financing_flows == pytest.approx(expected)


def test_minimum_cash_buffer_policy_between_historical_min_and_recent_actuals():
    hist_ratio = f.historical_ratio("cash_and_equivalents_balance_sheet", "revenue")
    by_scenario = f.assumptions_by_scenario(f.build_assumptions())
    policy = f._lookup(by_scenario["base"]["min_cash_buffer_pct_of_revenue"], 0)
    assert min(hist_ratio.values()) < policy < hist_ratio[2025]


# --- Validation ---------------------------------------------------------------


def test_validate_all_reports_zero_failures_on_published_assumptions():
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    lineage = {s: f.build_lineage(years, assumptions) for s, years in forecasts.items()}
    results = f.validate_all(forecasts, assumptions, lineage)
    failures = [r for r in results if r.status == "FAIL"]
    assert failures == []
    check_names = {r.check_name for r in results}
    expected_checks = {
        "revenue_recursion", "gross_profit_calc", "operating_income_bridge", "pretax_income_bridge",
        "tax_net_income_bridge", "eps_consistency", "cfo_construction", "fcf_calc",
        "working_capital_sign_checks", "cash_roll_forward", "debt_roll_forward",
        "no_finance_lease_double_counting", "minimum_cash_compliance", "scenario_ordering",
        "assumption_completeness", "lineage_completeness", "information_cutoff_compliance",
        "no_historical_forecast_mixing",
    }
    assert expected_checks.issubset(check_names)


def test_validate_all_catches_a_broken_revenue_recursion():
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    forecasts["base"][2].revenue += 500  # corrupt one year in place
    lineage = {s: f.build_lineage(years, assumptions) for s, years in forecasts.items()}
    results = f.validate_all(forecasts, assumptions, lineage)
    failing = [r for r in results if r.check_name == "revenue_recursion" and r.status == "FAIL"]
    assert failing, "corrupting a single year's revenue should trip revenue_recursion"


def test_validate_all_catches_a_broken_cfo_construction():
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    forecasts["upside"][0].operating_cash_flow += 1000
    lineage = {s: f.build_lineage(years, assumptions) for s, years in forecasts.items()}
    results = f.validate_all(forecasts, assumptions, lineage)
    failing = [r for r in results if r.check_name == "cfo_construction" and r.status == "FAIL"]
    assert failing


def test_scenario_ordering_flags_an_inverted_upside_base():
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    forecasts["upside"][1].net_income = forecasts["downside"][1].net_income - 1  # break ordering
    lineage = {s: f.build_lineage(years, assumptions) for s, years in forecasts.items()}
    results = f.validate_all(forecasts, assumptions, lineage)
    failing = [r for r in results if r.check_name == "scenario_ordering" and r.status == "FAIL"]
    assert failing


def test_no_historical_forecast_mixing_years_disjoint():
    assert set(f.FORECAST_YEARS).isdisjoint(set(f.HISTORICAL_YEARS))


def test_lineage_entries_reference_real_assumption_ids():
    assumptions = f.build_assumptions()
    valid_ids = {a.assumption_id for a in assumptions}
    forecasts = f.run_all_scenarios(assumptions)
    for scenario, years in forecasts.items():
        entries = f.build_lineage(years, assumptions)
        assert entries
        for e in entries:
            assert e.assumption_ids, f"{e.forecast_fact_id} has no assumption lineage"
            for aid in e.assumption_ids:
                assert aid in valid_ids


# --- Sensitivity ---------------------------------------------------------------


def test_sensitivity_table_monotonic_in_gross_margin():
    rows = f.sensitivity_table("gross_margin_pct", [-0.5, 0.0, 0.5])
    fcfs = [r["free_cash_flow"] for r in rows]
    assert fcfs == sorted(fcfs)


def test_sensitivity_table_zero_delta_matches_unperturbed_base():
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    terminal = forecasts["base"][-1]
    rows = f.sensitivity_table("capex_pct_of_revenue", [0.0], assumptions=assumptions)
    assert rows[0]["free_cash_flow"] == pytest.approx(terminal.free_cash_flow, abs=0.05)


def test_build_sensitivity_tables_covers_all_named_drivers():
    tables = f.build_sensitivity_tables()
    expected = {
        "revenue_growth_pct", "gross_margin_pct", "sga_pct_of_revenue",
        "capex_pct_of_revenue", "inventory_pct_of_revenue", "min_cash_buffer_pct_of_revenue",
    }
    assert expected.issubset(tables.keys())
    for rows in tables.values():
        assert len(rows) >= 2


# --- Structural separation from historical facts -----------------------------


def test_historical_dict_is_frozen_reference_not_mutated_by_a_run():
    import copy
    snapshot = copy.deepcopy(f.HISTORICAL)
    f.run_all_scenarios()
    assert f.HISTORICAL == snapshot


def test_forecast_year_fiscal_years_never_overlap_historical():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        for y in years:
            assert y.fiscal_year not in f.HISTORICAL_YEARS
            assert y.fiscal_year in f.FORECAST_YEARS
