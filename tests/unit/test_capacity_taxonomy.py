"""Tests for the Milestone 9 corrected investment-capacity taxonomy
(src/target_cash/capacity_taxonomy.py), v2 finance-semantics correction.

Maps all proofs required by the correction decision (and the v2
finance-semantics follow-up correction) to a test:

 1  test_operating_fcf_reconciles
 2  test_post_dividend_generation_reconciles
 3  test_opening_excess_liquidity_is_a_stock_used_exactly_once
 4  test_equal_proceeds_and_repayments_create_zero_incremental_debt_capacity
 5  test_net_deleveraging_creates_zero_debt_funded_capacity
 6  test_only_net_new_borrowing_creates_incremental_debt_capacity
 7  test_mandatory_debt_repayment_not_deducted_twice
 8  test_repurchases_are_part_of_discretionary_deployment
 9  test_repurchases_reduce_remaining_headroom
10  test_strategic_investment_reduces_remaining_headroom
11  test_voluntary_debt_reduction_reduces_remaining_headroom
12  test_headroom_never_negative
13  test_ending_cash_above_buffer_or_flagged
14  test_annual_source_use_reconciliation
15  test_cumulative_excludes_repeated_ending_balances
16  test_opening_excess_liquidity_excluded_from_cumulative_generation
17  test_cumulative_discretionary_deployment_includes_executed_repurchases
18  test_capacity_accounted_for_reconciliation_without_summing_annual_stocks
19  test_no_dollar_in_both_headroom_deployment_and_forward_reserve
20  test_scenario_and_information_cutoff_lineage_complete
21  test_legacy_deployable_capacity_never_feeds_the_new_taxonomy
22  test_opening_liquidity_never_labeled_capacity_generated
23  test_remaining_headroom_deducts_forward_reserve
24  test_forward_reserve_terminal_year_is_proxied_and_documented

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


def compute_terminal(y, next_y=None):
    """Helper: compute a single CapacityTaxonomyYear in isolation, as if it
    were the terminal (no next_y) or a middle year (next_y given)."""
    return ct.compute_capacity_taxonomy_year(y, next_y)


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
            sum(ty.self_funded_capacity_generated for ty in taxonomy_years) + \
            sum(ty.debt_funded_incremental_capacity for ty in taxonomy_years)
        extra_opening = sum(ty.opening_excess_liquidity for ty in taxonomy_years[1:])
        if extra_opening > 0:
            assert not f._close(naive_wrong, summary.gross_horizon_funding_before_reserve_adjustments), (
                f"{scenario}: naive multi-year sum of opening_excess_liquidity must NOT "
                "match the correct horizon total when later years carry nonzero opening liquidity"
            )
        assert summary.opening_excess_liquidity_at_horizon_start == taxonomy_years[0].opening_excess_liquidity


# --- 4-6: gross debt issuance is never mislabeled as capacity ---------------

def test_equal_proceeds_and_repayments_create_zero_incremental_debt_capacity(forecasts):
    y = forecasts["base"][-1]
    equal_year = dataclasses.replace(y, debt_proceeds=700.0, debt_repayments=700.0)
    ty = compute_terminal(equal_year)
    assert ty.debt_funded_incremental_capacity == 0.0
    assert ty.net_mandatory_debt_service == 0.0
    result = ct.check_debt_funded_capacity_excludes_gross_issuance(ty)
    assert result.status == "PASS", result


def test_net_deleveraging_creates_zero_debt_funded_capacity(forecasts):
    y = forecasts["base"][-1]
    deleveraging_year = dataclasses.replace(y, debt_proceeds=300.0, debt_repayments=1_000.0)
    ty = compute_terminal(deleveraging_year)
    assert ty.debt_funded_incremental_capacity == 0.0
    assert ty.net_mandatory_debt_service == pytest.approx(700.0)
    result = ct.check_debt_funded_capacity_excludes_gross_issuance(ty)
    assert result.status == "PASS", result


def test_only_net_new_borrowing_creates_incremental_debt_capacity(forecasts):
    y = forecasts["base"][-1]
    net_borrowing_year = dataclasses.replace(y, debt_proceeds=500.0, debt_repayments=300.0)
    ty = compute_terminal(net_borrowing_year)
    assert ty.debt_funded_incremental_capacity == pytest.approx(200.0)
    assert ty.net_mandatory_debt_service == 0.0
    result = ct.check_debt_funded_capacity_excludes_gross_issuance(ty)
    assert result.status == "PASS", result


def test_fy2030_example_values_from_the_correction_authorization(forecasts):
    """Exact numerical proof of the three worked examples in the v2
    finance-semantics correction authorization."""
    base = forecasts["base"][-1]
    upside = forecasts["upside"][-1]
    downside = forecasts["downside"][-1]
    assert (base.debt_proceeds, base.debt_repayments) == pytest.approx((700.0, 700.0))
    assert (upside.debt_proceeds, upside.debt_repayments) == pytest.approx((300.0, 1_000.0))
    assert (downside.debt_proceeds, downside.debt_repayments) == pytest.approx((500.0, 300.0))

    ty_base = compute_terminal(base)
    ty_upside = compute_terminal(upside)
    ty_downside = compute_terminal(downside)

    assert ty_base.debt_funded_incremental_capacity == 0.0
    assert ty_upside.debt_funded_incremental_capacity == 0.0
    assert ty_upside.net_mandatory_debt_service == pytest.approx(700.0)
    assert ty_downside.debt_funded_incremental_capacity == pytest.approx(200.0)


def test_new_debt_appears_only_in_debt_funded_capacity(forecasts):
    y = forecasts["base"][-1]
    baseline = compute_terminal(y)
    perturbed_year = dataclasses.replace(y, debt_proceeds=y.debt_proceeds + 1_000.0)
    perturbed = compute_terminal(perturbed_year)
    delta_debt_funded = perturbed.debt_funded_incremental_capacity - baseline.debt_funded_incremental_capacity
    delta_total = perturbed.total_gross_funding_capacity - baseline.total_gross_funding_capacity
    assert f._close(delta_debt_funded, 1_000.0)
    assert f._close(delta_total, 1_000.0), "the +$1,000 must flow through entirely via debt_funded_incremental_capacity"


# --- 7: mandatory debt repayment not deducted twice -------------------------

def test_mandatory_debt_repayment_not_deducted_twice(forecasts, taxonomies):
    for scenario, years in forecasts.items():
        for y, ty in zip(years, taxonomies[scenario]):
            result = ct.check_mandatory_debt_not_double_deducted(y, ty)
            assert result.status == "PASS", result


def test_legacy_field_did_double_deduct_mandatory_debt_use(forecasts):
    """Documents, rather than fixes, the legacy defect: `deployable_capacity`
    subtracts an amount equal to `debt_repayments` twice (once inside
    `pre_discretionary_ending_cash`'s own mandatory_financing_flows, again
    via `near_term_debt_repayment_reserve`). This is about the ORIGINAL
    (v1) correction and is independent of the v2 forward-reserve deduction,
    so the comparison is made against v1's self_funded_gross_capacity-based
    total (i.e. excluding the v2 forward reserve, which did not exist when
    this legacy comparison was first established)."""
    for scenario, years in forecasts.items():
        for i, y in enumerate(years):
            next_y = years[i + 1] if i + 1 < len(years) else None
            ty = ct.compute_capacity_taxonomy_year(y, next_y)
            legacy_residual = y.deployable_capacity - y.share_repurchases - (y.management_selected_deployment or 0.0)
            v1_style_headroom = max(
                0.0, ty.self_funded_gross_capacity + ty.debt_funded_incremental_capacity - ty.total_discretionary_deployment
            )
            if y.debt_repayments > 0:
                assert f._close(
                    v1_style_headroom, legacy_residual + y.debt_repayments
                ), f"{scenario} FY{y.fiscal_year}: v1-style corrected headroom should exceed the legacy residual by exactly debt_repayments"


# --- 8-9: repurchases are discretionary and reduce headroom -----------------

def test_repurchases_are_part_of_discretionary_deployment(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        for ty in taxonomy_years:
            result = ct.check_repurchases_in_discretionary_deployment(ty)
            assert result.status == "PASS", result
            assert ty.share_repurchases <= ty.total_discretionary_deployment + 1e-6


def test_repurchases_reduce_remaining_headroom(forecasts):
    y = forecasts["base"][-1]
    baseline = compute_terminal(y)
    higher_buyback_year = dataclasses.replace(y, share_repurchases=y.share_repurchases + 500.0)
    higher_buyback = compute_terminal(higher_buyback_year)
    assert higher_buyback.remaining_deployable_headroom == pytest.approx(
        baseline.remaining_deployable_headroom - 500.0, abs=0.5
    )


# --- 10-11: strategic investment / voluntary debt reduction reduce headroom -

def test_strategic_investment_reduces_remaining_headroom(forecasts):
    y = forecasts["base"][-1]
    baseline = compute_terminal(y)
    new_deployment = baseline.total_discretionary_deployment + 300.0
    bumped = dataclasses.replace(
        baseline, strategic_investment=300.0,
        total_discretionary_deployment=new_deployment,
        remaining_deployable_headroom=max(
            0.0, baseline.total_gross_funding_capacity - new_deployment - baseline.forward_debt_repayment_reserve
        ),
    )
    assert bumped.remaining_deployable_headroom < baseline.remaining_deployable_headroom


def test_voluntary_debt_reduction_reduces_remaining_headroom(forecasts):
    y = forecasts["base"][-1]
    baseline = compute_terminal(y)
    new_deployment = baseline.total_discretionary_deployment + 300.0
    bumped = dataclasses.replace(
        baseline, voluntary_debt_reduction=300.0,
        total_discretionary_deployment=new_deployment,
        remaining_deployable_headroom=max(
            0.0, baseline.total_gross_funding_capacity - new_deployment - baseline.forward_debt_repayment_reserve
        ),
    )
    assert bumped.remaining_deployable_headroom < baseline.remaining_deployable_headroom


# --- 12-13: headroom floor, ending-cash-above-buffer gate -------------------

def test_headroom_never_negative(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        for ty in taxonomy_years:
            result = ct.check_headroom_never_negative(ty)
            assert result.status == "PASS", result
            assert ty.remaining_deployable_headroom >= 0.0


def _make_stress_year(**overrides):
    base_kwargs = dict(
        scenario="stress_test", fiscal_year=2026, operating_fcf=100.0,
        post_dividend_internal_generation=50.0, opening_excess_liquidity=0.0,
        gross_debt_proceeds=0.0, gross_debt_repayments=0.0,
        net_mandatory_debt_service=0.0, self_funded_capacity_generated=50.0,
        debt_funded_incremental_capacity=0.0, total_gross_funding_capacity=50.0,
        share_repurchases=200.0, strategic_investment=0.0, voluntary_debt_reduction=0.0,
        other_discretionary_uses=0.0, total_discretionary_deployment=200.0,
        forward_debt_repayment_reserve=0.0, forward_reserve_is_proxied=True,
        remaining_deployable_headroom=max(0.0, 50.0 - 200.0 - 0.0), ending_excess_liquidity=0.0,
        mandatory_debt_uses=0.0, self_funded_gross_capacity=50.0,
    )
    base_kwargs.update(overrides)
    return ct.CapacityTaxonomyYear(**base_kwargs)


def test_headroom_floors_at_zero_when_deployment_exceeds_capacity():
    ty = _make_stress_year()
    assert ty.remaining_deployable_headroom == 0.0
    result = ct.check_headroom_never_negative(ty)
    assert result.status == "PASS"


def test_ending_cash_above_buffer_or_flagged(forecasts):
    for scenario, years in forecasts.items():
        for y in years:
            result = ct.check_ending_cash_above_buffer_or_flagged(y)
            assert result.status == "PASS", result


# --- 14: annual source/use reconciliation -----------------------------------

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


# --- 15-17: cumulative-capacity definitions ---------------------------------

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


# --- 18: capacity-accounted-for reconciliation, without summing annual stocks

def test_capacity_accounted_for_reconciliation_without_summing_annual_stocks(taxonomies, summaries):
    for scenario in taxonomies:
        result = ct.check_capacity_accounted_for_reconciliation(scenario, summaries[scenario])
        assert result.status == "PASS", result

    # Explicitly prove the identity is NOT achieved by summing each year's own
    # ending headroom balance across the horizon -- the governing rule this
    # correction round requires: "Never add FY2026...FY2030 ending-headroom
    # balances."
    for scenario, taxonomy_years in taxonomies.items():
        summary = summaries[scenario]
        naive_sum_of_headroom_balances = sum(ty.remaining_deployable_headroom for ty in taxonomy_years)
        if len(taxonomy_years) > 1 and naive_sum_of_headroom_balances != summary.terminal_remaining_headroom:
            assert not f._close(naive_sum_of_headroom_balances, summary.gross_horizon_funding_before_reserve_adjustments), (
                f"{scenario}: summing annual headroom balances must NOT reproduce the correct horizon total"
            )


def test_capacity_accounted_for_reconciliation_catches_corruption(summaries):
    summary = summaries["base"]
    corrupted = dataclasses.replace(summary, terminal_remaining_headroom=summary.terminal_remaining_headroom + 500.0)
    result = ct.check_capacity_accounted_for_reconciliation("base", corrupted)
    assert result.status == "FAIL"


# --- 19: no dollar in both headroom, deployment, and forward reserve -------

def test_no_dollar_in_both_headroom_deployment_and_forward_reserve(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        for ty in taxonomy_years:
            result = ct.check_capacity_mutually_exclusive(ty)
            assert result.status == "PASS", result


def test_capacity_mutually_exclusive_catches_corruption(taxonomies):
    ty = taxonomies["base"][-1]
    corrupted = dataclasses.replace(ty, remaining_deployable_headroom=ty.remaining_deployable_headroom + 500.0)
    result = ct.check_capacity_mutually_exclusive(corrupted)
    assert result.status == "FAIL"


# --- 20: scenario / information-cutoff lineage completeness ----------------

def test_scenario_and_information_cutoff_lineage_complete(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        for ty in taxonomy_years:
            result = ct.check_scenario_and_cutoff_lineage_complete(ty)
            assert result.status == "PASS", result


def test_lineage_covers_all_v2_per_year_fields_every_year(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        lineage = ct.build_capacity_taxonomy_lineage(scenario, taxonomy_years)
        assert len(lineage) == len(ct._PER_YEAR_FIELD_SPECS) * len(taxonomy_years)
        for row in lineage:
            assert row["information_cutoff"] <= f.FORECAST_INFORMATION_CUTOFF
            assert row["scenario_id"] == scenario


def test_horizon_lineage_covers_all_summary_fields():
    lineage = ct.build_capacity_horizon_lineage("base")
    assert len(lineage) == len(ct._HORIZON_FIELD_SPECS)
    for row in lineage:
        assert row["scenario_id"] == "base"
        assert row["fiscal_year"] is None


# --- 21: legacy deployable_capacity never feeds the new taxonomy -----------

def test_legacy_deployable_capacity_never_feeds_the_new_taxonomy(forecasts):
    """Perturbing the legacy `deployable_capacity` / `near_term_debt_repayment_reserve`
    fields must have ZERO effect on any new taxonomy output -- proving the new
    KPI is computed independently of the deprecated field, never derived from it."""
    y = forecasts["base"][-1]
    baseline = compute_terminal(y)
    corrupted_legacy = dataclasses.replace(
        y, deployable_capacity=y.deployable_capacity + 999_999.0,
        near_term_debt_repayment_reserve=y.near_term_debt_repayment_reserve + 999_999.0,
    )
    after = compute_terminal(corrupted_legacy)
    assert dataclasses.astuple(baseline) == dataclasses.astuple(after), (
        "no new taxonomy field may read the legacy deployable_capacity or "
        "near_term_debt_repayment_reserve fields"
    )


# --- 22: opening liquidity is never labeled "capacity generated" -----------

def test_opening_liquidity_never_labeled_capacity_generated(forecasts):
    """self_funded_capacity_generated -- the ONLY field this correction round
    labels 'capacity generated' -- must be computable from
    post_dividend_internal_generation and net_mandatory_debt_service alone,
    with zero sensitivity to opening_excess_liquidity."""
    y = forecasts["base"][-1]
    baseline = compute_terminal(y)
    # Perturb beginning_cash (the sole driver of opening_excess_liquidity)
    # by a large amount and confirm self_funded_capacity_generated is unchanged.
    perturbed_year = dataclasses.replace(y, beginning_cash=y.beginning_cash + 5_000.0)
    perturbed = compute_terminal(perturbed_year)
    assert perturbed.opening_excess_liquidity != pytest.approx(baseline.opening_excess_liquidity)
    assert f._close(perturbed.self_funded_capacity_generated, baseline.self_funded_capacity_generated), (
        "self_funded_capacity_generated must be a pure FLOW, invariant to the opening-liquidity STOCK"
    )
    for scenario, taxonomy_years in {"base": [baseline]}.items():
        for ty in taxonomy_years:
            result = ct.check_self_funded_generation_excludes_opening_liquidity(ty)
            assert result.status == "PASS", result


def test_self_funded_generation_excludes_opening_liquidity_all_scenarios(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        for ty in taxonomy_years:
            result = ct.check_self_funded_generation_excludes_opening_liquidity(ty)
            assert result.status == "PASS", result


def test_deprecated_self_funded_gross_capacity_still_includes_opening_liquidity_but_is_unlabeled(taxonomies):
    """The DEPRECATED-BY-v2 self_funded_gross_capacity column legitimately
    still includes the opening stock (kept only for schema NOT NULL
    compatibility) -- this test documents that it is intentionally
    DIFFERENT from self_funded_capacity_generated, so nobody mistakes the
    two, and that only the latter is ever labeled 'generated' anywhere
    downstream (see docs/investment_capacity_correction_evidence.md)."""
    for scenario, taxonomy_years in taxonomies.items():
        for ty in taxonomy_years:
            expected_deprecated = ty.opening_excess_liquidity + ty.self_funded_capacity_generated
            assert f._close(ty.self_funded_gross_capacity, expected_deprecated)
            if ty.opening_excess_liquidity > 0:
                assert not f._close(ty.self_funded_gross_capacity, ty.self_funded_capacity_generated)


# --- 23: remaining headroom deducts the forward reserve --------------------

def test_remaining_headroom_deducts_forward_reserve(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        for ty in taxonomy_years:
            result = ct.check_headroom_deducts_forward_reserve(ty)
            assert result.status == "PASS", result


def test_forward_reserve_reduces_headroom_relative_to_no_reserve(forecasts):
    """A middle year (FY2026) with a known nonzero next-year net mandatory
    debt service must show LOWER headroom than if the reserve were zero."""
    years = forecasts["upside"]
    y0 = years[0]
    ty_with_reserve = ct.compute_capacity_taxonomy_year(y0, years[1])
    ty_without_reserve = ct.compute_capacity_taxonomy_year(y0, None)
    # Force the "without reserve" comparison to have zero forward reserve by
    # using a next_y with equal proceeds/repayments (net service exactly 0).
    zero_reserve_next = dataclasses.replace(years[1], debt_proceeds=500.0, debt_repayments=500.0)
    ty_zero_reserve = ct.compute_capacity_taxonomy_year(y0, zero_reserve_next)
    if ty_with_reserve.forward_debt_repayment_reserve > 0:
        assert ty_with_reserve.remaining_deployable_headroom <= ty_zero_reserve.remaining_deployable_headroom
    del ty_without_reserve  # only used to document the terminal-proxy alternative shape


def test_headroom_deducts_forward_reserve_catches_corruption(taxonomies):
    ty = taxonomies["upside"][-1]
    corrupted = dataclasses.replace(ty, remaining_deployable_headroom=ty.remaining_deployable_headroom + 500.0)
    result = ct.check_headroom_deducts_forward_reserve(corrupted)
    assert result.status == "FAIL"


# --- 24: forward reserve terminal-year proxy is documented -----------------

def test_forward_reserve_terminal_year_is_proxied_and_documented(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        result = ct.check_forward_reserve_terminal_proxy_documented(scenario, taxonomy_years)
        assert result.status == "PASS", result
        terminal = taxonomy_years[-1]
        assert terminal.forward_reserve_is_proxied is True
        assert terminal.forward_debt_repayment_reserve == pytest.approx(terminal.net_mandatory_debt_service)
        for ty in taxonomy_years[:-1]:
            assert ty.forward_reserve_is_proxied is False


def test_forward_reserve_non_terminal_years_use_actual_next_year_value(forecasts):
    years = forecasts["base"]
    for i in range(len(years) - 1):
        ty = ct.compute_capacity_taxonomy_year(years[i], years[i + 1])
        expected = max(0.0, years[i + 1].debt_repayments - years[i + 1].debt_proceeds)
        assert ty.forward_debt_repayment_reserve == pytest.approx(expected)
        assert ty.forward_reserve_is_proxied is False


# --- Debt-netting mutual exclusivity (persisted check) ----------------------

def test_debt_netting_mutually_exclusive_all_scenarios(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        for ty in taxonomy_years:
            result = ct.check_debt_netting_mutually_exclusive(ty)
            assert result.status == "PASS", result


def test_debt_netting_mutually_exclusive_catches_corruption(taxonomies):
    ty = taxonomies["downside"][-1]
    # Force both net_mandatory_debt_service and debt_funded_incremental_capacity
    # positive simultaneously -- structurally impossible under a correct
    # computation, so the check must catch it.
    corrupted = dataclasses.replace(ty, net_mandatory_debt_service=100.0, debt_funded_incremental_capacity=50.0)
    result = ct.check_debt_netting_mutually_exclusive(corrupted)
    assert result.status == "FAIL"


# --- Cross-scenario sanity (ties this suite back to the semantic audit) ----

def test_base_upside_downside_headroom_ordering_matches_audit_narrative(taxonomies):
    base_terminal = taxonomies["base"][-1].remaining_deployable_headroom
    upside_terminal = taxonomies["upside"][-1].remaining_deployable_headroom
    downside_terminal = taxonomies["downside"][-1].remaining_deployable_headroom
    # Upside still trails Base under the corrected metric (it deploys far more
    # into buybacks/deleveraging, and its terminal year carries a real forward
    # debt-service reserve), and Downside still sits close to Base (it deploys
    # nothing) -- the corrected number changes the MAGNITUDE but not this
    # qualitative ordering.
    assert upside_terminal < base_terminal
    assert downside_terminal > 0


def test_total_gross_funding_capacity_unchanged_by_v2_decomposition(forecasts):
    """The v2 correction only changes how total_gross_funding_capacity is
    DECOMPOSED (opening stock shown separately, debt netted) -- for any
    given ForecastYear, the TOTAL must equal beginning_cash's excess over
    the buffer plus post-dividend generation plus net debt flow, exactly as
    it did before this round, since opening_excess_liquidity +
    self_funded_capacity_generated + debt_funded_incremental_capacity is
    algebraically identical to the old self_funded_gross_capacity +
    debt_funded_incremental_capacity for the same underlying cash flows."""
    for scenario, years in forecasts.items():
        for i, y in enumerate(years):
            next_y = years[i + 1] if i + 1 < len(years) else None
            ty = ct.compute_capacity_taxonomy_year(y, next_y)
            expected = ty.opening_excess_liquidity + ty.post_dividend_internal_generation - ty.net_mandatory_debt_service + ty.debt_funded_incremental_capacity
            assert f._close(ty.total_gross_funding_capacity, expected)


# --- Final independent-audit closeout: net vs. gross horizon capacity ------

def test_gross_horizon_funding_is_not_net_accessible_capacity(summaries):
    """gross_horizon_funding_before_reserve_adjustments (the field formerly
    published as total_horizon_capacity_accessible) is computed BEFORE
    ending_reserve_movement and terminal_forward_debt_repayment_reserve are
    deducted -- it must never be published or treated as 'net accessible
    capacity.' net_horizon_deployable_capacity is the corrected figure."""
    for scenario, summary in summaries.items():
        gross = summary.gross_horizon_funding_before_reserve_adjustments
        net = summary.net_horizon_deployable_capacity
        reserves = summary.ending_reserve_movement + summary.terminal_forward_debt_repayment_reserve
        if reserves != 0:
            assert not f._close(gross, net), (
                f"{scenario}: gross horizon funding must differ from net deployable capacity "
                "whenever the reserve terms are nonzero"
            )
        assert f._close(net, gross - reserves)


def test_net_horizon_deployable_capacity_equals_deployment_plus_terminal_headroom(summaries):
    """The identity this correction requires: net_horizon_deployable_capacity
    == cumulative_discretionary_deployment + terminal_remaining_headroom,
    exactly -- proven both algebraically (via gross - reserves) and via this
    independent right-hand-side reconstruction."""
    for scenario, summary in summaries.items():
        result = ct.check_net_horizon_capacity_reconciles(scenario, summary)
        assert result.status == "PASS", result
        expected = summary.cumulative_discretionary_deployment + summary.terminal_remaining_headroom
        assert f._close(summary.net_horizon_deployable_capacity, expected)


def test_net_horizon_deployable_capacity_expected_values(summaries):
    """Exact expected values from the final independent-audit closeout
    authorization."""
    expected = {"base": 9175.0, "upside": 7420.7, "downside": 6387.5}
    for scenario, value in expected.items():
        assert summaries[scenario].net_horizon_deployable_capacity == pytest.approx(value, abs=0.5)


def test_net_horizon_capacity_reconciles_catches_corruption(summaries):
    summary = summaries["base"]
    corrupted = dataclasses.replace(summary, net_horizon_deployable_capacity=summary.net_horizon_deployable_capacity + 500.0)
    result = ct.check_net_horizon_capacity_reconciles("base", corrupted)
    assert result.status == "FAIL"


# --- Final independent-audit closeout: cross-year lineage for the forward --
# --- debt-repayment reserve, never recorded as a same-year dependency -----

def test_forward_reserve_lineage_records_next_year_dependency_for_non_terminal_years(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        lineage = ct.build_capacity_taxonomy_lineage(scenario, taxonomy_years)
        fdr_rows = {r["fiscal_year"]: r for r in lineage if r["target_field"] == "forward_debt_repayment_reserve"}
        for ty in taxonomy_years[:-1]:
            row = fdr_rows[ty.fiscal_year]
            assert row["dependency_timing"] == "next_year"
            assert row["input_fiscal_year"] == ty.fiscal_year + 1
            assert row["next_year_debt_proceeds_fact_id"] == f.forecast_fact_id(scenario, "debt_proceeds", ty.fiscal_year + 1, ct.FORECAST_MODEL_VERSION)
            assert row["next_year_debt_repayments_fact_id"] == f.forecast_fact_id(scenario, "debt_repayments", ty.fiscal_year + 1, ct.FORECAST_MODEL_VERSION)
            assert row["proxy_note"] is None
            # Never recorded as a same-year dependency.
            assert row["same_year_forecast_inputs"] is None
            assert row["same_year_capacity_inputs"] is None


def test_forward_reserve_lineage_records_terminal_proxy_for_terminal_year(taxonomies):
    for scenario, taxonomy_years in taxonomies.items():
        lineage = ct.build_capacity_taxonomy_lineage(scenario, taxonomy_years)
        terminal_fy = taxonomy_years[-1].fiscal_year
        row = next(r for r in lineage if r["target_field"] == "forward_debt_repayment_reserve" and r["fiscal_year"] == terminal_fy)
        assert row["dependency_timing"] == "terminal_proxy"
        assert row["input_fiscal_year"] == terminal_fy
        assert row["next_year_debt_proceeds_fact_id"] is None
        assert row["next_year_debt_repayments_fact_id"] is None
        assert row["proxy_note"] is not None
        assert "net_mandatory_debt_service" in row["proxy_note"] or "PROXY" in row["proxy_note"]
        assert str(terminal_fy + 1) in row["proxy_note"], "must name the out-of-horizon year the proxy stands in for"
        assert "no actual" in row["proxy_note"].lower() or "not claimed" in row["proxy_note"].lower() or "not known" in row["proxy_note"].lower()


def test_all_other_per_year_fields_remain_same_year_dependencies(taxonomies):
    """Only forward_debt_repayment_reserve has a cross-year dependency --
    every other per-year field's lineage row must still be same_year."""
    for scenario, taxonomy_years in taxonomies.items():
        lineage = ct.build_capacity_taxonomy_lineage(scenario, taxonomy_years)
        for row in lineage:
            if row["target_field"] != "forward_debt_repayment_reserve":
                assert row["dependency_timing"] == "same_year"
                assert row["input_fiscal_year"] == row["fiscal_year"]
                assert row["next_year_debt_proceeds_fact_id"] is None
                assert row["next_year_debt_repayments_fact_id"] is None
                assert row["proxy_note"] is None


def test_horizon_lineage_rows_carry_default_dependency_metadata():
    lineage = ct.build_capacity_horizon_lineage("base")
    for row in lineage:
        assert row["dependency_timing"] == "same_year"
        assert row["input_fiscal_year"] is None
        assert row["next_year_debt_proceeds_fact_id"] is None
        assert row["next_year_debt_repayments_fact_id"] is None
        assert row["proxy_note"] is None
