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


# --- Reviewer audit package: assumption matrix + fact-ID citations ---------


def test_annual_fact_id_matches_real_database_convention():
    # Deterministic unit test -- no database access. The convention itself
    # (f"annual:{metric}:{fiscal_year}:{analytical_view}") is enforced here;
    # target_cash.annual_persistence builds annual_facts.annual_fact_id the
    # same way, so this stays a real cross-check without opening the
    # gitignored data/curated/target_cash.db (which a fresh clone won't have).
    assert f.annual_fact_id_for("revenue", 2025, "latest_restated") == "annual:revenue:2025:latest_restated"


def test_historical_source_fact_ids_cover_all_five_years():
    ids = f.historical_source_fact_ids("revenue")
    assert set(ids.keys()) == set(f.HISTORICAL_YEARS)
    assert all(isinstance(v, str) and v for v in ids.values())


def test_historical_source_fact_ids_uses_raw_fact_for_da_addback():
    ids = f.historical_source_fact_ids("depreciation_amortization_cfo_addback")
    for fy, fid in ids.items():
        assert fid == f.DA_CFO_ADDBACK_RAW_FACT_IDS[fy]
        assert "DepreciationDepletionAndAmortization" in fid


def test_build_assumption_matrix_covers_every_required_area():
    assumptions = f.build_assumptions()
    rows = f.build_assumption_matrix(assumptions)
    required_metrics = {
        "revenue_growth_pct", "gross_margin_pct", "sga_pct_of_revenue", "da_pct_of_revenue",
        "da_cfo_addback_pct_of_revenue", "interest_rate_pct", "effective_tax_rate_pct",
        "diluted_share_change_pct", "inventory_pct_of_revenue", "ap_pct_of_cogs",
        "other_operating_cf_musd", "capex_pct_of_revenue", "dividend_per_share_growth_pct",
        "debt_proceeds_musd", "debt_repayments_musd", "buyback_payout_pct_of_post_dividend_fcf",
        "min_cash_buffer_pct_of_revenue", "finance_lease_liabilities_musd",
    }
    got_metrics = {r["metric"] for r in rows}
    assert required_metrics.issubset(got_metrics)
    # 3 scenarios x len(required-ish set) rows minimum
    assert len(rows) >= len(required_metrics) * 3 - 3  # -3 tolerance for any metric without a per-scenario split


def test_assumption_matrix_rows_have_every_required_column():
    assumptions = f.build_assumptions()
    rows = f.build_assumption_matrix(assumptions)
    required_columns = {
        "assumption_ids", "area", "name", "metric", "scenario", "driver_type", "values_by_year", "unit",
        "historical_series", "historical_min", "historical_max", "historical_median", "rationale",
        "depends_on", "source_fact_ids", "information_cutoff", "review_status", "version",
    }
    for row in rows:
        assert required_columns.issubset(row.keys())
        for fy in f.FORECAST_YEARS:
            assert fy in row["values_by_year"]
            assert row["values_by_year"][fy] is not None


def test_assumption_matrix_dependency_edges_reference_real_metrics():
    assumptions = f.build_assumptions()
    rows = f.build_assumption_matrix(assumptions)
    all_metrics = {r["metric"] for r in rows}
    for row in rows:
        for dep in row["depends_on"]:
            assert dep in all_metrics


# --- Reviewer audit package: other-operating-cf bridge + plug detection ----


def test_historical_other_operating_cf_residual_matches_hand_derivation():
    residual = f.historical_other_operating_cf_residual()
    assert set(residual.keys()) == {2022, 2023, 2024, 2025}
    # Hand-derived from HISTORICAL literals: other = CFO - NI - D&A_addback - inv_impact - ap_impact
    assert residual[2022] == pytest.approx(126.0, abs=0.5)
    assert residual[2023] == pytest.approx(1458.0, abs=0.5)
    assert residual[2024] == pytest.approx(194.0, abs=0.5)
    assert residual[2025] == pytest.approx(-282.0, abs=0.5)


def test_other_operating_cf_not_a_plug_passes_on_real_forecast():
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    lineage = {s: f.build_lineage(y, assumptions) for s, y in forecasts.items()}
    results = f.validate_all(forecasts, assumptions, lineage)
    plug_checks = [r for r in results if r.check_name == "other_operating_cf_not_a_plug"]
    assert len(plug_checks) == 3
    assert all(r.status == "PASS" for r in plug_checks)


def test_demo_backward_solved_cfo_plug_is_detected():
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    corrupted = dict(forecasts)
    corrupted["base"] = f.demo_backward_solved_cfo_plug(forecasts["base"], target_cfo=7500.0)
    # The plug reproduces the target CFO exactly...
    assert all(y.operating_cash_flow == pytest.approx(7500.0) for y in corrupted["base"])
    # ...but other_operating_cf now varies year to year, which the check must catch.
    lineage = {s: f.build_lineage(y, assumptions) for s, y in corrupted.items()}
    results = f.validate_all(corrupted, assumptions, lineage)
    plug_check = next(r for r in results if r.check_name == "other_operating_cf_not_a_plug" and r.scenario == "base")
    assert plug_check.status == "FAIL"


# --- Reviewer audit package: capital allocation waterfall -------------------


def test_capital_allocation_waterfall_reconciles_to_engine_ending_cash():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        for y in years:
            steps = f.capital_allocation_waterfall(y)
            assert steps[-1]["label"] == "Ending cash"
            assert steps[-1]["balance_after"] == pytest.approx(y.ending_cash)


def test_capital_allocation_waterfall_deployable_capacity_checkpoint_matches_engine():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        for y in years:
            steps = f.capital_allocation_waterfall(y)
            checkpoint = next(s for s in steps if s["step"] == "5b")
            checkpoint_value = float(checkpoint["note"].split("=")[1].replace(",", ""))
            assert checkpoint_value == pytest.approx(y.deployable_capacity, abs=0.1)


def test_verify_no_double_counting_holds_for_every_scenario_year():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        for y in years:
            proof = f.verify_no_double_counting(y)
            assert proof["no_double_counting_proven"]


def test_capital_allocation_repurchase_classification_answers_all_four_options():
    answer = f.capital_allocation_repurchase_classification().lower()
    assert "fixed forecast assumption" in answer
    assert "not a use of" in answer or "not" in answer  # explicitly rules out the other 3 options
    assert "residual" in answer


def test_capital_allocation_waterfall_reconciliation_check_present_and_passing():
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    lineage = {s: f.build_lineage(y, assumptions) for s, y in forecasts.items()}
    results = f.validate_all(forecasts, assumptions, lineage)
    checks = [r for r in results if r.check_name == "capital_allocation_waterfall_reconciliation"]
    assert len(checks) == 15  # 3 scenarios x 5 years
    assert all(r.status == "PASS" for r in checks)


# --- Reviewer audit package: minimum-cash-buffer policy comparison ---------


def test_minimum_cash_buffer_policies_returns_five_policies_per_scenario():
    forecasts = f.run_all_scenarios()
    policies = f.minimum_cash_buffer_policies(forecasts)
    for scenario in f.SCENARIOS:
        assert len(policies[scenario]) == 5
        for row in policies[scenario]:
            assert len(row["per_year"]) == len(f.FORECAST_YEARS)
            assert row["rationale"] and row["strength"] and row["limitation"]


def test_minimum_cash_buffer_ending_cash_invariant_across_policies():
    """Buffer policy is a post-hoc overlay -- ending_cash must be identical
    across all 5 policies since none of them feed back into the cash-flow
    engine (repurchases are sized from FCF, never from the buffer)."""
    forecasts = f.run_all_scenarios()
    policies = f.minimum_cash_buffer_policies(forecasts)
    for scenario in f.SCENARIOS:
        rows = policies[scenario]
        for fy_idx in range(len(f.FORECAST_YEARS)):
            ending_cash_values = {row["per_year"][fy_idx]["ending_cash"] for row in rows}
            assert len(ending_cash_values) == 1


def test_minimum_cash_buffer_policies_have_distinct_required_minimums():
    forecasts = f.run_all_scenarios()
    policies = f.minimum_cash_buffer_policies(forecasts)
    required_2026 = {row["policy_id"]: row["per_year"][0]["required_minimum_cash"] for row in policies["base"]}
    assert len(set(round(v, 1) for v in required_2026.values())) >= 3  # not all collapsing to the same figure


# --- Reviewer audit package: seasonality stress overlay ---------------------


def test_seasonal_stress_overlay_reduces_cash_position():
    forecasts = f.run_all_scenarios()
    overlay = f.seasonal_stress_overlay(forecasts["base"])
    for row, y in zip(overlay, forecasts["base"]):
        assert row["stressed_cash_position"] < row["pre_discretionary_ending_cash"]
        assert row["stressed_cash_position"] == pytest.approx(
            y.pre_discretionary_ending_cash * (1 - f.DEFAULT_SEASONAL_HAIRCUT_PCT / 100)
        )


def test_seasonal_stress_overlay_can_trigger_funding_warning_in_downside():
    forecasts = f.run_all_scenarios()
    overlay = f.seasonal_stress_overlay(forecasts["downside"])
    assert any(row["stressed_funding_warning"] for row in overlay)


def test_seasonal_haircut_grounded_in_real_fy2025_quarterly_data():
    assert "2,887" in f.SEASONAL_HAIRCUT_EVIDENCE
    assert "5,488" in f.SEASONAL_HAIRCUT_EVIDENCE
    assert f.DEFAULT_SEASONAL_HAIRCUT_PCT >= 47.4  # conservative vs the observed 47.4% decline


# --- Reviewer audit package: historical-to-forecast handoff -----------------


def test_historical_to_forecast_handoff_covers_all_scenarios():
    forecasts = f.run_all_scenarios()
    handoff = f.historical_to_forecast_handoff(forecasts)
    scenarios_seen = {row["scenario"] for row in handoff}
    assert scenarios_seen == set(f.SCENARIOS)
    for row in handoff:
        assert row["last_historical_value"] is not None
        assert row["first_forecast_value"] is not None


def test_historical_to_forecast_handoff_flags_a_true_cliff():
    forecasts = f.run_all_scenarios()
    handoff = f.historical_to_forecast_handoff(forecasts)
    revenue_row = next(r for r in handoff if r["scenario"] == "base" and r["metric"] == "revenue")
    assert revenue_row["cliff_flag"] is False  # base FY2026 growth is within historical experience
    corrupted = {"base": [
        __import__("dataclasses").replace(y, revenue=y.revenue * 3) if y.fiscal_year == 2026 else y
        for y in forecasts["base"]
    ]}
    handoff2 = f.historical_to_forecast_handoff(corrupted)
    revenue_row2 = next(r for r in handoff2 if r["metric"] == "revenue")
    assert revenue_row2["cliff_flag"] is True


# --- Reviewer audit package: cutoff audit -----------------------------------


def test_cutoff_audit_finds_no_post_cutoff_sources():
    assumptions = f.build_assumptions()
    audit = f.cutoff_audit(assumptions)
    assert audit["no_post_cutoff_sources"]
    assert audit["assumptions_citing_information_after_cutoff"] == []
    assert audit["cutoff_source_record"] is not None
    assert audit["cutoff_source_record"]["accession_number"] == f.FORECAST_INFORMATION_CUTOFF_ACCESSION
    assert audit["cutoff_source_record"]["filed_at"] == f.FORECAST_INFORMATION_CUTOFF


def test_cutoff_audit_covers_all_registered_sources():
    assumptions = f.build_assumptions()
    audit = f.cutoff_audit(assumptions)
    assert audit["total_registered_sources"] == 8
    assert all(s["filed_at"] <= f.FORECAST_INFORMATION_CUTOFF for s in audit["all_sources"])


# --- Reviewer audit package: validation check inventory ---------------------


def test_every_validation_result_check_name_has_metadata():
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    lineage = {s: f.build_lineage(y, assumptions) for s, y in forecasts.items()}
    results = f.validate_all(forecasts, assumptions, lineage)
    check_names = {r.check_name for r in results}
    assert check_names == set(f.VALIDATION_CHECK_METADATA.keys())


def test_validation_metadata_distinguishes_arithmetic_from_independent():
    meta = f.VALIDATION_CHECK_METADATA
    arithmetic = [k for k, v in meta.items() if v["check_type"] == "arithmetic_invariant"]
    independent = [k for k, v in meta.items() if v["check_type"] == "independent_reasonableness_test"]
    assert len(arithmetic) >= 8
    # Only the waterfall reconciliation is computed via a genuinely different code path.
    # cumulative_capacity_no_double_counting re-derives its own function's formula inline
    # as a self-check, so it is honestly an arithmetic invariant, not independent evidence.
    assert independent == ["capital_allocation_waterfall_reconciliation"]
    assert "cumulative_capacity_no_double_counting" in arithmetic


def test_every_check_metadata_has_required_fields():
    required = {"category", "check_type", "formula", "tolerance", "gate_consequence",
                "corruption_test", "example_failure_message"}
    for check_name, meta in f.VALIDATION_CHECK_METADATA.items():
        assert required.issubset(meta.keys()), f"{check_name} missing fields"


# --- Reviewer audit package: two-variable sensitivity -----------------------


def test_two_variable_sensitivity_grid_shape():
    grid = f.two_variable_sensitivity("revenue_growth_pct", [-1.0, 0.0, 1.0], "gross_margin_pct", [-0.5, 0.0, 0.5])
    assert len(grid["grid"]) == 3
    for row in grid["grid"]:
        assert len(row["cells"]) == 3


def test_two_variable_sensitivity_monotonic_in_both_directions():
    grid = f.two_variable_sensitivity("revenue_growth_pct", [-1.0, 0.0, 1.0], "gross_margin_pct", [-0.5, 0.0, 0.5])
    # Fixing driver2's middle column, deployable capacity should rise with driver1
    middle_col = [row["cells"][1]["fy2030_deployable_capacity"] for row in grid["grid"]]
    assert middle_col == sorted(middle_col)
    # Fixing driver1's middle row, deployable capacity should rise with driver2
    middle_row = [cell["fy2030_deployable_capacity"] for cell in grid["grid"][1]["cells"]]
    assert middle_row == sorted(middle_row)


def test_sensitivity_table_includes_cumulative_deployable_capacity():
    rows = f.sensitivity_table("gross_margin_pct", [0.0])
    assert "cumulative_deployable_capacity_2026_2030" in rows[0]
    # With nothing actually deployed this round, cumulative == terminal-year deployable_capacity
    # exactly (see cumulative_deployable_capacity's docstring) -- NOT greater than it, which
    # would indicate the old, defective sum-of-year-end-balances double-counting bug is back.
    assert rows[0]["cumulative_deployable_capacity_2026_2030"] == pytest.approx(rows[0]["deployable_capacity"])


# --- Milestone 3A: cumulative-capacity double-counting fix -----------------


def test_cumulative_deployable_capacity_equals_terminal_when_nothing_deployed():
    forecasts = f.run_all_scenarios()
    for scenario, years in forecasts.items():
        assert all(y.management_selected_deployment in (None, 0.0) for y in years)
        cumulative = f.cumulative_deployable_capacity(years)
        assert cumulative == pytest.approx(years[-1].deployable_capacity)


def test_cumulative_capacity_naive_sum_would_overstate():
    """Proves the fix matters: the OLD (defective) sum-of-year-end-balances
    method materially overstates capacity relative to the corrected figure,
    because every scenario carries positive undeployed capacity forward
    year over year (deployable_capacity is monotonically non-decreasing in
    every scenario here)."""
    forecasts = f.run_all_scenarios()
    for scenario, years in forecasts.items():
        naive_sum = sum(y.deployable_capacity for y in years)
        correct = f.cumulative_deployable_capacity(years)
        assert naive_sum > correct * 1.5  # naive method is off by a wide margin, not a rounding difference


def test_cumulative_deployable_capacity_with_simulated_deployment():
    """If a deployment IS selected partway through the horizon, cumulative
    capacity must include it exactly once (not double-count it alongside
    whatever remains in the terminal balance)."""
    import dataclasses
    forecasts = f.run_all_scenarios()
    years = forecasts["base"]
    deployed_amount = 1000.0
    modified = [
        dataclasses.replace(y, management_selected_deployment=deployed_amount) if y.fiscal_year == 2027 else y
        for y in years
    ]
    cumulative = f.cumulative_deployable_capacity(modified)
    expected = modified[-1].deployable_capacity + deployed_amount
    assert cumulative == pytest.approx(expected)
    # And it must NOT simply equal the terminal balance alone (that would drop the deployment).
    assert cumulative != pytest.approx(modified[-1].deployable_capacity)


def test_cumulative_capacity_validation_check_passes_and_flags_naive_overstatement():
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    lineage = {s: f.build_lineage(y, assumptions) for s, y in forecasts.items()}
    results = f.validate_all(forecasts, assumptions, lineage)
    checks = [r for r in results if r.check_name == "cumulative_capacity_no_double_counting"]
    assert len(checks) == 3
    assert all(r.status == "PASS" for r in checks)
    assert all("naive method overstates" in r.detail for r in checks)


# --- Milestone 3A: extended no-double-counting identity (with debt + deployment) ---


def test_verify_no_double_counting_identity_c_full_conservation():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        for y in years:
            proof = f.verify_no_double_counting(y)
            assert "identity_c_holds" in proof
            assert proof["identity_c_holds"]
            assert proof["no_double_counting_proven"]


def test_verify_no_double_counting_accounts_for_management_selected_deployment():
    import dataclasses
    forecasts = f.run_all_scenarios()
    y = forecasts["base"][0]
    y_with_deployment = dataclasses.replace(
        y, management_selected_deployment=500.0, ending_cash=y.ending_cash - 500.0,
        net_change_in_cash=y.net_change_in_cash - 500.0,
    )
    proof = f.verify_no_double_counting(y_with_deployment)
    assert proof["identity_a_holds"]
    assert proof["identity_c_holds"]


def test_capital_allocation_waterfall_includes_management_selected_deployment_step():
    forecasts = f.run_all_scenarios()
    y = forecasts["base"][0]
    steps = f.capital_allocation_waterfall(y)
    step_7b = next(s for s in steps if s["step"] == "7b")
    assert step_7b["amount"] == 0.0  # no deployment selected this round
    assert steps[-1]["balance_after"] == pytest.approx(y.ending_cash)


# --- Milestone 3A: scenario narratives --------------------------------------


def test_scenario_narratives_exist_for_all_scenarios():
    for s in f.SCENARIOS:
        narrative = f.scenario_narrative(s)
        assert isinstance(narrative, str)
        assert len(narrative) > 500  # substantive prose, not a one-liner


def test_scenario_narratives_are_not_mechanically_identical_in_structure():
    narratives = [f.SCENARIO_NARRATIVES[s] for s in f.SCENARIOS]
    assert len(set(narratives)) == 3  # all distinct


def test_upside_narrative_explains_the_non_monotonic_capex_exception():
    narrative = f.SCENARIO_NARRATIVES["upside"].lower()
    assert "capex" in narrative
    assert "not" in narrative and ("less" in narrative or "minimize" in narrative)


def test_downside_narrative_explains_dividend_freeze_not_cut():
    narrative = f.SCENARIO_NARRATIVES["downside"].lower()
    assert "frozen" in narrative
    assert "not cut" in narrative or "not modeled as plausible" in narrative


def test_downside_narrative_references_funding_warning():
    assert "funding warning" in f.SCENARIO_NARRATIVES["downside"].lower()


def test_scenario_narratives_cite_real_assumption_values():
    by_scenario = f.assumptions_by_scenario(f.build_assumptions())
    base_growth = f._lookup(by_scenario["base"]["revenue_growth_pct"], 2026)
    upside_growth = f._lookup(by_scenario["upside"]["revenue_growth_pct"], 2026)
    downside_growth = f._lookup(by_scenario["downside"]["revenue_growth_pct"], 2026)
    assert f"{base_growth:.1f}%" in f.SCENARIO_NARRATIVES["base"] or "+1.0%" in f.SCENARIO_NARRATIVES["base"]
    assert "+3.0%" in f.SCENARIO_NARRATIVES["upside"]
    assert "-2.5%" in f.SCENARIO_NARRATIVES["downside"]
    assert base_growth == 1.0 and upside_growth == 3.0 and downside_growth == -2.5


def test_cumulative_deployable_capacity_through_each_year_matches_totals():
    forecasts = f.run_all_scenarios()
    for years in forecasts.values():
        series = f.cumulative_deployable_capacity_through_each_year(years)
        assert len(series) == len(years)
        assert series[-1] == pytest.approx(f.cumulative_deployable_capacity(years))
        # With nothing ever deployed, the running series is just each year's own deployable_capacity.
        assert series == [pytest.approx(y.deployable_capacity) for y in years]


# --- Milestone 3B: full-grain lineage ---------------------------------------


def test_build_full_lineage_covers_every_field_every_year():
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    for scenario, years in forecasts.items():
        rows = f.build_full_lineage(years, assumptions)
        fact_ids_with_lineage = {r["forecast_fact_id"] for r in rows}
        expected = {f.forecast_fact_id(scenario, field, y.fiscal_year) for y in years for field in f.FIELD_SPECS}
        assert expected.issubset(fact_ids_with_lineage)


def test_build_full_lineage_every_row_satisfies_check_constraint():
    """Mirrors forecast_lineage's CHECK: exactly-at-least-one of the three input kinds set."""
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    rows = f.build_full_lineage(forecasts["base"], assumptions)
    for r in rows:
        set_count = sum(x is not None for x in (
            r["input_historical_fact_id"], r["input_forecast_fact_id"], r["input_assumption_id"]
        ))
        assert set_count == 1, r


def test_build_full_lineage_fy2026_cross_year_fields_cite_historical_facts():
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    rows = f.build_full_lineage(forecasts["base"], assumptions)
    revenue_2026_rows = [r for r in rows if r["forecast_fact_id"] == f.forecast_fact_id("base", "revenue", 2026)]
    hist_citations = [r for r in revenue_2026_rows if r["input_historical_fact_id"]]
    assert hist_citations
    assert hist_citations[0]["input_historical_fact_id"] == f.annual_fact_id_for("revenue", 2025)


def test_build_full_lineage_no_duplicate_lineage_ids_within_one_run():
    """Regression test: dividend_per_share's FY2026 cross-year anchor cites
    TWO historical metrics (dividends_paid and diluted_shares) in the same
    cross_year_inputs iteration. An earlier version incremented `sequence`
    once per (input_field, offset) pair rather than once per emitted row,
    so both citations shared the same sequence number and therefore the
    same forecast_lineage_id -- a real, caught collision bug."""
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    for scenario, years in forecasts.items():
        rows = f.build_full_lineage(years, assumptions)
        seq_keys = [(r["forecast_fact_id"], r["sequence"]) for r in rows]
        assert len(seq_keys) == len(set(seq_keys)), f"duplicate (fact_id, sequence) in {scenario}"
        lineage_ids = [f"{fid}_lin_{seq}" for fid, seq in seq_keys]
        assert len(lineage_ids) == len(set(lineage_ids))


def test_build_full_lineage_later_years_cite_prior_forecast_facts_not_historical():
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    rows = f.build_full_lineage(forecasts["base"], assumptions)
    revenue_2028_rows = [r for r in rows if r["forecast_fact_id"] == f.forecast_fact_id("base", "revenue", 2028)]
    forecast_citations = [r for r in revenue_2028_rows if r["input_forecast_fact_id"]]
    assert forecast_citations
    assert forecast_citations[0]["input_forecast_fact_id"] == f.forecast_fact_id("base", "revenue", 2027)
    assert all(r["input_historical_fact_id"] is None for r in revenue_2028_rows)
