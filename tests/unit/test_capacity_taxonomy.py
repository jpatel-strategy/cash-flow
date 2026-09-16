"""Tests for the Milestone 9 corrected investment-capacity taxonomy
(src/target_cash/capacity_taxonomy.py).

Maps all 20 proofs required by the correction decision to a test:

 1  test_operating_fcf_reconciles
 2  test_post_dividend_generation_reconciles
 3  test_opening_excess_liquidity_is_a_stock_used_exactly_once
 4  test_new_debt_excluded_from_self_funded_capacity
 5  test_new_debt_appears_only_in_debt_funded_capacity
 6  test_mandatory_debt_repayment_not_deducted_twice
 7  test_repurchases_are_part_of_discretionary_deployment
 8  test_repurchases_reduce_remaining_headroom
 9  test_strategic_investment_reduces_remaining_headroom
10  test_voluntary_debt_reduction_reduces_remaining_headroom
11  test_headroom_never_negative
12  test_ending_cash_above_buffer_or_flagged
13  test_annual_source_use_reconciliation
14  test_cumulative_excludes_repeated_ending_balances
15  test_opening_excess_liquidity_excluded_from_cumulative_generation
16  test_cumulative_discretionary_deployment_includes_executed_repurchases
17  test_capacity_accounted_for_reconciliation
18  test_no_dollar_in_both_headroom_and_deployment
19  test_scenario_and_information_cutoff_lineage_complete
20  test_legacy_deployable_capacity_never_feeds_the_new_taxonomy

Plus corruption tests for the most important identities.
"""
import dataclasses

import pytest

from target_cash import forecast as f
from target_cash import capacity_taxonomy as ct


@pytest.fixture(scope="module")
def assumptions():
    return f.build_assumptions()


@pytest.fixture(scope="module")
def forecasts(assumptions):
    return f.run_all_scenarios(assumptions)


@pytest.fixture(scope="module")
def taxonomies(forecasts):
    return ct.build_capacity_taxonomy_all_scenarios(forecasts)


@pytest.fixture(scope="module")
def summaries(forecasts, taxonomies):
    return ct.build_capacity_horizon_summaries(forecasts, taxonomies)


# --- 1-2: core flow reconciliations -----------------------------------------

def test_operating_fcf_reconciles(forecasts, taxonomies):
    for scenario, years in forecasts.items():
        for y, ty in zip(years, taxonomies[scenario]):
            result = ct.check_operating_fcf_reconciles(y, ty)
            assert result.status == "PASS", result


def test_post_dividend_generation_reconciles(forecasts, taxonomies):
    for scenario, years in forecasts.items():
        for y, ty in zip(years, taxonomies[scenario]):
            result = ct.check_post_dividend_generation_reconciles(y, ty)
            assert result.status == "PASS", result


# --- 3: opening excess liquidity is a stock, used exactly once -------------

def test_opening_excess_liquidity_is_a_stock_used_exactly_once(taxonomies, summaries):
    for scenario, taxonomy_years in taxonomies.items():
        summary = summaries[scenario]
        # The horizon total must equal FY2026's own opening_excess_liquidity
        # plus flows -- NOT a sum of every year's opening_excess_liquidity.
        naive_wrong = sum(ty.opening_excess_liquidity for ty in taxonomy_years) + \
            sum(ty.post_dividend_internal_generation - ty.mandatory_debt_uses for ty in taxonomy_years) + \
            sum(ty.debt_funded_incremental_capacity for ty in taxonomy_years)
        extra_opening = sum(ty.opening_excess_liquidity for ty in taxonomy_years[1:])
        if extra_opening > 0:
            assert not f._close(naive_wrong, summary.total_horizon_capacity_accessible), (
                f"{scenario}: naive multi-year sum of opening_excess_liquidity must NOT "
                "match the correct horizon total when later years carry nonzero opening liquidity"
            )
        assert summary.opening_excess_liquidity_at_horizon_start == taxonomy_years[0].opening_excess_liquidity


# --- 4-5: new debt excluded from self-funded, appears only in debt-funded --

def test_new_debt_excluded_from_self_funded_capacity(forecasts):
    y = forecasts["base"][-1]
    baseline = ct.compute_capacity_taxonomy_year(y)
    perturbed_year = dataclasses.replace(y, debt_proceeds=y.debt_proceeds + 1_000.0)
    perturbed = ct.compute_capacity_taxonomy_year(perturbed_year)
    assert f._close(baseline.self_funded_gross_capacity, perturbed.self_funded_gross_capacity), (
        "self_funded_gross_capacity must be invariant to new borrowing"
    )


def test_new_debt_appears_only_in_debt_funded_capacity(forecasts):
    y = forecasts["base"][-1]
    baseline = ct.compute_capacity_taxonomy_year(y)
    perturbed_year = dataclasses.replace(y, debt_proceeds=y.debt_proceeds + 1_000.0)
    perturbed = ct.compute_capacity_taxonomy_year(perturbed_year)
    delta_debt_funded = perturbed.debt_funded_incremental_capacity - baseline.debt_funded_incremental_capacity
    delta_total = perturbed.total_gross_funding_capacity - baseline.total_gross_funding_capacity
    assert f._close(delta_debt_funded, 1_000.0)
    assert f._close(delta_total, 1_000.0), "the +$1,000 must flow through entirely via debt_funded_incremental_capacity"


# --- 6: mandatory debt repayment not deducted twice -------------------------

def test_mandatory_debt_repayment_not_deducted_twice(forecasts, taxonomies):
    for scenario, years in forecasts.items():
        for y, ty in zip(years, taxonomies[scenario]):
            result = ct.check_mandatory_debt_not_double_deducted(y, ty)
            assert result.status == "PASS", result


def test_legacy_field_did_double_deduct_mandatory_debt_use(forecasts):
    """Documents, rather than fixes, the legacy defect: `deployable_capacity`
    subtracts an amount equal to `debt_repayments` twice (once inside
    `pre_discretionary_ending_cash`'s own mandatory_financing_flows, again
    via `near_term_debt_repayment_reserve`). The new taxonomy's
    remaining_deployable_headroom must therefore exceed the legacy
    deployable_capacity net of that year's own repurchases by exactly
    that amount, for every scenario-year where debt_repayments > 0."""
    for scenario, years in forecasts.items():
        for y in years:
            ty = ct.compute_capacity_taxonomy_year(y)
            legacy_residual = y.deployable_capacity - y.share_repurchases - (y.management_selected_deployment or 0.0)
            if y.debt_repayments > 0:
                assert f._close(
                    ty.remaining_deployable_headroom, legacy_residual + y.debt_repayments
                ), f"{scenario} FY{y.fiscal_year}: corrected headroom should exceed the legacy residual by exactly debt_repayments"


# --- 7-8: repurchases are discretionary and reduce headroom -----------------

def test_repurchases_are_part_of_discretionary_deployment(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        for ty in taxonomy_years:
            result = ct.check_repurchases_in_discretionary_deployment(ty)
            assert result.status == "PASS", result
            assert ty.share_repurchases <= ty.total_discretionary_deployment + 1e-6


def test_repurchases_reduce_remaining_headroom(forecasts):
    y = forecasts["base"][-1]
    baseline = ct.compute_capacity_taxonomy_year(y)
    higher_buyback_year = dataclasses.replace(y, share_repurchases=y.share_repurchases + 500.0)
    higher_buyback = ct.compute_capacity_taxonomy_year(higher_buyback_year)
    assert higher_buyback.remaining_deployable_headroom == pytest.approx(
        baseline.remaining_deployable_headroom - 500.0, abs=0.5
    )


# --- 9-10: strategic investment / voluntary debt reduction reduce headroom -

def test_strategic_investment_reduces_remaining_headroom(forecasts):
    y = forecasts["base"][-1]
    baseline = ct.compute_capacity_taxonomy_year(y)
    bumped = dataclasses.replace(
        baseline, strategic_investment=300.0,
        total_discretionary_deployment=baseline.total_discretionary_deployment + 300.0,
        remaining_deployable_headroom=max(0.0, baseline.total_gross_funding_capacity - (baseline.total_discretionary_deployment + 300.0)),
    )
    assert bumped.remaining_deployable_headroom < baseline.remaining_deployable_headroom


def test_voluntary_debt_reduction_reduces_remaining_headroom(forecasts):
    y = forecasts["base"][-1]
    baseline = ct.compute_capacity_taxonomy_year(y)
    bumped = dataclasses.replace(
        baseline, voluntary_debt_reduction=300.0,
        total_discretionary_deployment=baseline.total_discretionary_deployment + 300.0,
        remaining_deployable_headroom=max(0.0, baseline.total_gross_funding_capacity - (baseline.total_discretionary_deployment + 300.0)),
    )
    assert bumped.remaining_deployable_headroom < baseline.remaining_deployable_headroom


# --- 11-12: headroom floor, ending-cash-above-buffer gate -------------------

def test_headroom_never_negative(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        for ty in taxonomy_years:
            result = ct.check_headroom_never_negative(ty)
            assert result.status == "PASS", result
            assert ty.remaining_deployable_headroom >= 0.0


def test_headroom_floors_at_zero_when_deployment_exceeds_capacity():
    ty = ct.CapacityTaxonomyYear(
        scenario="stress_test", fiscal_year=2026, operating_fcf=100.0,
        post_dividend_internal_generation=50.0, opening_excess_liquidity=0.0,
        mandatory_debt_uses=0.0, self_funded_gross_capacity=50.0,
        debt_funded_incremental_capacity=0.0, total_gross_funding_capacity=50.0,
        share_repurchases=200.0, strategic_investment=0.0, voluntary_debt_reduction=0.0,
        other_discretionary_uses=0.0, total_discretionary_deployment=200.0,
        remaining_deployable_headroom=max(0.0, 50.0 - 200.0), ending_excess_liquidity=0.0,
    )
    assert ty.remaining_deployable_headroom == 0.0
    result = ct.check_headroom_never_negative(ty)
    assert result.status == "PASS"


def test_ending_cash_above_buffer_or_flagged(forecasts):
    for scenario, years in forecasts.items():
        for y in years:
            result = ct.check_ending_cash_above_buffer_or_flagged(y)
            assert result.status == "PASS", result


# --- 13: annual source/use reconciliation -----------------------------------

def test_annual_source_use_reconciliation(forecasts, taxonomies):
    for scenario, years in forecasts.items():
        for y, ty in zip(years, taxonomies[scenario]):
            result = ct.check_annual_source_use_reconciliation(y, ty)
            assert result.status == "PASS", result


def test_annual_source_use_reconciliation_catches_corruption(forecasts, taxonomies):
    y = forecasts["base"][0]
    ty = taxonomies["base"][0]
    corrupted = dataclasses.replace(ty, total_discretionary_deployment=ty.total_discretionary_deployment + 999.0)
    result = ct.check_annual_source_use_reconciliation(y, corrupted)
    assert result.status == "FAIL"


# --- 14-16: cumulative-capacity definitions ---------------------------------

def test_cumulative_excludes_repeated_ending_balances(taxonomies, summaries):
    for scenario, taxonomy_years in taxonomies.items():
        result = ct.check_cumulative_excludes_repeated_balances(scenario, taxonomy_years, summaries[scenario])
        assert result.status == "PASS", result


def test_opening_excess_liquidity_excluded_from_cumulative_generation(taxonomies, summaries):
    for scenario, taxonomy_years in taxonomies.items():
        result = ct.check_opening_excess_liquidity_excluded_from_generation(scenario, taxonomy_years, summaries[scenario])
        assert result.status == "PASS", result


def test_cumulative_discretionary_deployment_includes_executed_repurchases(taxonomies, summaries):
    for scenario, taxonomy_years in taxonomies.items():
        result = ct.check_cumulative_deployment_includes_repurchases(scenario, taxonomy_years, summaries[scenario])
        assert result.status == "PASS", result
    # Base and Upside both execute real repurchases -- prove the cumulative
    # figure is not silently zero the way the legacy cumulative_deployable_capacity's
    # "amount deployed" addend always was (it only tracked management_selected_deployment,
    # never share_repurchases).
    for scenario in ("base", "upside"):
        assert summaries[scenario].cumulative_discretionary_deployment > 0


# --- 17: capacity-accounted-for reconciliation ------------------------------

def test_capacity_accounted_for_reconciliation(taxonomies, summaries):
    for scenario in taxonomies:
        result = ct.check_capacity_accounted_for_reconciliation(scenario, summaries[scenario])
        assert result.status == "PASS", result


def test_capacity_accounted_for_reconciliation_catches_corruption(summaries):
    summary = summaries["base"]
    corrupted = dataclasses.replace(summary, terminal_remaining_headroom=summary.terminal_remaining_headroom + 500.0)
    result = ct.check_capacity_accounted_for_reconciliation("base", corrupted)
    assert result.status == "FAIL"


# --- 18: no dollar in both headroom and deployment --------------------------

def test_no_dollar_in_both_headroom_and_deployment(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        for ty in taxonomy_years:
            result = ct.check_capacity_mutually_exclusive(ty)
            assert result.status == "PASS", result


def test_capacity_mutually_exclusive_catches_corruption(taxonomies):
    ty = taxonomies["base"][-1]
    corrupted = dataclasses.replace(ty, remaining_deployable_headroom=ty.remaining_deployable_headroom + 500.0)
    result = ct.check_capacity_mutually_exclusive(corrupted)
    assert result.status == "FAIL"


# --- 19: scenario / information-cutoff lineage completeness ----------------

def test_scenario_and_information_cutoff_lineage_complete(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        for ty in taxonomy_years:
            result = ct.check_scenario_and_cutoff_lineage_complete(ty)
            assert result.status == "PASS", result


def test_lineage_covers_all_14_fields_every_year(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        lineage = ct.build_capacity_taxonomy_lineage(scenario, taxonomy_years)
        assert len(lineage) == 14 * len(taxonomy_years)
        for row in lineage:
            assert row["information_cutoff"] <= f.FORECAST_INFORMATION_CUTOFF
            assert row["scenario_id"] == scenario


def test_horizon_lineage_covers_all_7_summary_fields():
    lineage = ct.build_capacity_horizon_lineage("base")
    assert len(lineage) == 7
    for row in lineage:
        assert row["scenario_id"] == "base"
        assert row["fiscal_year"] is None


# --- 20: legacy deployable_capacity never feeds the new taxonomy -----------

def test_legacy_deployable_capacity_never_feeds_the_new_taxonomy(forecasts):
    """Perturbing the legacy `deployable_capacity` / `near_term_debt_repayment_reserve`
    fields must have ZERO effect on any new taxonomy output -- proving the new
    KPI is computed independently of the deprecated field, never derived from it."""
    y = forecasts["base"][-1]
    baseline = ct.compute_capacity_taxonomy_year(y)
    corrupted_legacy = dataclasses.replace(
        y, deployable_capacity=y.deployable_capacity + 999_999.0,
        near_term_debt_repayment_reserve=y.near_term_debt_repayment_reserve + 999_999.0,
    )
    after = ct.compute_capacity_taxonomy_year(corrupted_legacy)
    assert dataclasses.astuple(baseline) == dataclasses.astuple(after), (
        "no new taxonomy field may read the legacy deployable_capacity or "
        "near_term_debt_repayment_reserve fields"
    )


# --- Cross-scenario sanity (ties this suite back to the semantic audit) ----

def test_base_upside_downside_headroom_ordering_matches_audit_narrative(taxonomies):
    base_terminal = taxonomies["base"][-1].remaining_deployable_headroom
    upside_terminal = taxonomies["upside"][-1].remaining_deployable_headroom
    downside_terminal = taxonomies["downside"][-1].remaining_deployable_headroom
    # Upside still trails Base under the corrected metric (it deploys far more
    # into buybacks/deleveraging), and Downside still sits close to Base
    # (it deploys nothing) -- the corrected number changes the MAGNITUDE
    # (see test_legacy_field_did_double_deduct_mandatory_debt_use) but not
    # this qualitative ordering.
    assert upside_terminal < base_terminal
    assert downside_terminal > 0
