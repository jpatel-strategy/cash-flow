import pytest
"""Unit tests for target_cash.annual's pure logic (tag resolution, value
scaling, derived-metric computation) -- not the database queries, which are
exercised end-to-end by running scripts/annual_dry_run.py (a thin wrapper
around this module) against the real database, and by the validate_annual
integration tests in test_annual_validation.py.
"""
from target_cash.annual import derive, q6, resolve_tag


def test_q6_scales_dollar_metrics_by_one_million():
    assert q6("revenue", "104780000000") == 104780.0


def test_q6_does_not_scale_diluted_eps():
    assert q6("diluted_eps", "8.13") == 8.13


def test_resolve_tag_fixed_pair():
    assert resolve_tag(("us-gaap", "Revenues"), 2025) == ("us-gaap", "Revenues")


def test_resolve_tag_vintage_dependent_interest_expense():
    assert resolve_tag(lambda fy: ("us-gaap", "InterestExpense") if fy <= 2023 else ("us-gaap", "InterestExpenseNonoperating"), 2023) == ("us-gaap", "InterestExpense")
    assert resolve_tag(lambda fy: ("us-gaap", "InterestExpense") if fy <= 2023 else ("us-gaap", "InterestExpenseNonoperating"), 2024) == ("us-gaap", "InterestExpenseNonoperating")


def _direct(value):
    return {"status": "DIRECT", "value": value}


def test_derive_gross_profit_and_margin():
    view = {"revenue": _direct(109120.0), "cost_of_sales": _direct(82229.0)}
    view = {**view, "operating_income": _direct(3848.0), "net_income": _direct(2780.0),
            "income_tax_expense": _direct(638.0), "pretax_income": _direct(3418.0),
            "operating_cash_flow": _direct(4018.0), "capital_expenditure": _direct(5528.0),
            "cash_and_equivalents_balance_sheet": _direct(2229.0),
            "long_term_debt_gaap_carrying_value_noncurrent": _direct(16009.0),
            "long_term_debt_gaap_carrying_value_current": _direct(130.0),
            "finance_lease_liability_current": _direct(129.0),
            "finance_lease_liability_noncurrent": _direct(1943.0),
            "debt_principal_schedule": _direct(14141.0),
            "debt_fair_value_hedge_adjustment": _direct(-74.0),
            "dividends_paid": _direct(1836.0), "share_repurchases": _direct(2826.0)}
    out = derive(view)
    assert out["gross_profit"]["value"] == 26891.0
    assert out["gross_profit"]["status"] == "DERIVED"
    assert out["gross_margin_pct"]["value"] == round(100 * 26891.0 / 109120.0, 2)


def test_derive_fcf_negative_makes_distributions_not_applicable():
    """This IS the dedicated FY2022 test required by the 2026-09-15 approval
    round's item 4: 'FY2022 shareholder_distributions_to_fcf must remain
    NOT_APPLICABLE because FCF is negative, according to the approved policy'
    -- referenced from config/metric_definitions.csv's shareholder_distributions_to_fcf
    negative_denominator_policy field. Uses FY2022's real reported figures
    (revenue $109,120M, CFO $4,018M, CapEx $5,528M -> FCF = -$1,510M, matching
    both analytical views), and asserts NOT_APPLICABLE is a hard status, not
    a computed negative percentage -- this must hold regardless of how large
    dividends_paid/share_repurchases are, since the policy triggers on the
    denominator's sign alone.
    """
    view = {
        "revenue": _direct(109120.0), "operating_cash_flow": _direct(4018.0),
        "capital_expenditure": _direct(5528.0), "dividends_paid": _direct(1836.0),
        "share_repurchases": _direct(2826.0), "operating_income": _direct(3848.0),
        "net_income": _direct(2780.0), "income_tax_expense": _direct(638.0),
        "pretax_income": _direct(3418.0), "cash_and_equivalents_balance_sheet": _direct(2229.0),
        "long_term_debt_gaap_carrying_value_noncurrent": _direct(16009.0),
        "long_term_debt_gaap_carrying_value_current": _direct(130.0),
        "finance_lease_liability_current": _direct(129.0),
        "finance_lease_liability_noncurrent": _direct(1943.0),
        "debt_principal_schedule": _direct(14141.0),
        "debt_fair_value_hedge_adjustment": _direct(-74.0),
    }
    out = derive(view)
    assert out["fcf"]["value"] == 4018.0 - 5528.0 == -1510.0
    assert out["distributions_pct_fcf"]["status"] == "NOT_APPLICABLE"
    # Hard requirement, not a default: NOT_APPLICABLE must hold even though
    # dividends_paid+share_repurchases is a large, real, disclosed number --
    # the policy triggers on FCF's sign alone, never on distribution size.
    assert view["dividends_paid"]["value"] + view["share_repurchases"]["value"] == 4662.0


def test_derive_debt_bridge_pass_when_all_components_present_and_reconciling():
    view = {
        "revenue": _direct(1.0), "operating_cash_flow": _direct(1.0), "capital_expenditure": _direct(1.0),
        "dividends_paid": _direct(0.0), "share_repurchases": _direct(0.0),
        "operating_income": _direct(1.0), "net_income": _direct(1.0), "income_tax_expense": _direct(0.0),
        "pretax_income": _direct(1.0),
        "cash_and_equivalents_balance_sheet": _direct(0.0),
        "long_term_debt_gaap_carrying_value_noncurrent": _direct(16009.0),
        "long_term_debt_gaap_carrying_value_current": _direct(130.0),
        "finance_lease_liability_current": _direct(129.0),
        "finance_lease_liability_noncurrent": _direct(1943.0),
        "debt_principal_schedule": _direct(14141.0),
        "debt_fair_value_hedge_adjustment": _direct(-74.0),
    }
    out = derive(view)
    assert out["debt_bridge_check"]["status"] == "PASS"


def test_derive_target_defined_net_debt_is_always_unavailable_never_zero_or_copied():
    view = {
        "revenue": _direct(1.0), "operating_cash_flow": _direct(1.0), "capital_expenditure": _direct(1.0),
        "dividends_paid": _direct(0.0), "share_repurchases": _direct(0.0),
        "operating_income": _direct(1.0), "net_income": _direct(1.0), "income_tax_expense": _direct(0.0),
        "pretax_income": _direct(1.0), "cash_and_equivalents_balance_sheet": _direct(5.0),
        "long_term_debt_gaap_carrying_value_noncurrent": _direct(10.0),
        "long_term_debt_gaap_carrying_value_current": _direct(1.0),
        "finance_lease_liability_current": _direct(0.0), "finance_lease_liability_noncurrent": _direct(0.0),
        "debt_principal_schedule": _direct(11.0), "debt_fair_value_hedge_adjustment": _direct(0.0),
    }
    out = derive(view)
    assert out["target_defined_net_debt"] == {
        "status": "UNAVAILABLE", "value": None,
        "note": "Target discloses no net-debt measure of its own; never populated.",
    }
    # Never equal to valuation_net_debt_excluding_leases (would indicate an accidental copy).
    assert out["target_defined_net_debt"]["value"] != out["valuation_net_debt_excluding_leases"]["value"]


# --- CapEx / FCF formula lock-in (2026-09-15) ---------------------------------
# FCF must be CFO - PaymentsToAcquirePropertyPlantAndEquipment (capital_expenditure),
# never CFO + investing_cash_flow (CFI) or CFO - investing_cash_flow. CapEx and CFI
# are different concepts (CFI includes CapEx plus every other investing activity --
# e.g. securities purchases/maturities, acquisitions) and must never be conflated.

def test_fy2025_capex_is_not_investing_cash_flow():
    """Locks in the real, distinct FY2025 values so a future edit that
    accidentally aliases capital_expenditure to investing_cash_flow (or
    vice versa) fails immediately: CapEx ($3,727M) != |CFI| ($3,649M) --
    they are close but genuinely different figures, not a typo."""
    view = {
        "revenue": _direct(104780.0), "cost_of_sales": _direct(75511.0),
        "operating_income": _direct(5117.0), "net_income": _direct(3705.0),
        "income_tax_expense": _direct(1062.0), "pretax_income": _direct(4767.0),
        "operating_cash_flow": _direct(6562.0),
        "capital_expenditure": _direct(3727.0),
        "investing_cash_flow": _direct(-3649.0),
        "cash_and_equivalents_balance_sheet": _direct(5488.0),
        "long_term_debt_gaap_carrying_value_noncurrent": _direct(14326.0),
        "long_term_debt_gaap_carrying_value_current": _direct(2130.0),
        "finance_lease_liability_current": _direct(131.0),
        "finance_lease_liability_noncurrent": _direct(1982.0),
        "debt_principal_schedule": _direct(14398.0),
        "debt_fair_value_hedge_adjustment": _direct(-55.0),
        "dividends_paid": _direct(2053.0), "share_repurchases": _direct(408.0),
    }
    out = derive(view)
    assert view["capital_expenditure"]["value"] == 3727.0
    assert view["investing_cash_flow"]["value"] == -3649.0
    assert view["capital_expenditure"]["value"] != abs(view["investing_cash_flow"]["value"])
    # The required formula: FCF = CFO - capital_expenditure (PaymentsToAcquirePropertyPlantAndEquipment).
    assert out["fcf"]["value"] == 6562.0 - 3727.0 == 2835.0
    # A regression that swapped in CFI would produce a materially different, wrong number --
    # assert the wrong formulas explicitly do NOT match what fcf actually is.
    wrong_using_cfi_as_capex = 6562.0 - (-3649.0)  # CFO - CFI, treating CFI as if it were CapEx
    assert out["fcf"]["value"] != wrong_using_cfi_as_capex
    wrong_subtracting_cfi_from_cfo = 6562.0 + (-3649.0)  # CFO + CFI (another plausible-looking mistake)
    assert out["fcf"]["value"] != wrong_subtracting_cfi_from_cfo


def test_derive_never_reads_investing_cash_flow_for_fcf():
    """Structural guard: removing investing_cash_flow from the view entirely
    must not change fcf's value or push it to BLOCKED -- proving derive()
    does not consult investing_cash_flow when computing fcf at all."""
    base = {
        "revenue": _direct(104780.0), "cost_of_sales": _direct(75511.0),
        "operating_income": _direct(5117.0), "net_income": _direct(3705.0),
        "income_tax_expense": _direct(1062.0), "pretax_income": _direct(4767.0),
        "operating_cash_flow": _direct(6562.0), "capital_expenditure": _direct(3727.0),
        "cash_and_equivalents_balance_sheet": _direct(5488.0),
        "long_term_debt_gaap_carrying_value_noncurrent": _direct(14326.0),
        "long_term_debt_gaap_carrying_value_current": _direct(2130.0),
        "finance_lease_liability_current": _direct(131.0),
        "finance_lease_liability_noncurrent": _direct(1982.0),
        "debt_principal_schedule": _direct(14398.0),
        "debt_fair_value_hedge_adjustment": _direct(-55.0),
        "dividends_paid": _direct(2053.0), "share_repurchases": _direct(408.0),
    }
    without_cfi = derive({**base})
    with_cfi = derive({**base, "investing_cash_flow": _direct(-3649.0)})
    assert without_cfi["fcf"]["value"] == with_cfi["fcf"]["value"] == 2835.0


# --- Debt-construction proofs, required before any debt metric is marked
# reviewed (2026-09-15 approval round, item 6) -----------------------------

def _debt_view(**overrides):
    base = {
        "long_term_debt_gaap_carrying_value_noncurrent": _direct(14326.0),
        "long_term_debt_gaap_carrying_value_current": _direct(2130.0),
        "finance_lease_liability_current": _direct(131.0),
        "finance_lease_liability_noncurrent": _direct(1982.0),
        "debt_principal_schedule": _direct(14398.0),
        "debt_fair_value_hedge_adjustment": _direct(-55.0),
        "cash_and_equivalents_balance_sheet": _direct(5488.0),
    }
    base.update(overrides)
    return base


def test_finance_leases_are_not_counted_twice_in_total_debt_gaap():
    """total_debt_gaap_excluding_separately_reported_leases must equal
    long_term_debt_gaap_carrying_value MINUS finance_lease_liabilities exactly
    once -- not zero times (leases left in) and not twice (over-subtracted)."""
    out = derive(_debt_view())
    ltd = out["long_term_debt_gaap_carrying_value"]["value"]  # 14326+2130=16456
    fin_leases = out["finance_lease_liabilities"]["value"]  # 131+1982=2113
    total_excl = out["total_debt_gaap_excluding_separately_reported_leases"]["value"]
    assert ltd == 16456.0
    assert fin_leases == 2113.0
    assert total_excl == ltd - fin_leases == 14343.0
    # Subtracting twice would give a materially different (wrong) number -- assert it doesn't.
    assert total_excl != ltd - 2 * fin_leases


def test_adjusted_net_debt_does_not_double_count_finance_leases():
    """adjusted_net_debt_including_finance_leases must equal
    long_term_debt_gaap_carrying_value - cash exactly -- NOT
    long_term_debt_gaap_carrying_value + finance_lease_liabilities - cash,
    which would double-count (the GAAP carrying value already includes
    finance leases)."""
    out = derive(_debt_view())
    ltd = out["long_term_debt_gaap_carrying_value"]["value"]
    cash = 5488.0
    fin_leases = out["finance_lease_liabilities"]["value"]
    adjusted = out["adjusted_net_debt_including_finance_leases"]["value"]
    correct = ltd - cash
    double_counted = ltd + fin_leases - cash
    assert adjusted == correct == 10968.0
    assert adjusted != double_counted


def test_swap_valuation_adjustment_retains_actual_sign_both_directions():
    """The debt bridge must use the swap adjustment's real signed value --
    positive in the one year it actually is (FY2021: +77), negative in the
    other four (FY2022-FY2025) -- never its absolute value and never a
    hard-coded sign."""
    positive_year = derive(_debt_view(
        long_term_debt_gaap_carrying_value_noncurrent=_direct(13549.0),
        long_term_debt_gaap_carrying_value_current=_direct(171.0),
        finance_lease_liability_current=_direct(108.0),
        finance_lease_liability_noncurrent=_direct(1967.0),
        debt_principal_schedule=_direct(11568.0),
        debt_fair_value_hedge_adjustment=_direct(77.0),  # positive, FY2021
    ))
    negative_year = derive(_debt_view())  # FY2025 fixture: -55
    assert positive_year["debt_bridge_check"]["status"] == "PASS"
    assert negative_year["debt_bridge_check"]["status"] == "PASS"
    # Flipping FY2021's sign to negative must break the bridge -- proves the
    # check actually depends on the sign, not just the magnitude.
    sign_flipped = derive(_debt_view(
        long_term_debt_gaap_carrying_value_noncurrent=_direct(13549.0),
        long_term_debt_gaap_carrying_value_current=_direct(171.0),
        finance_lease_liability_current=_direct(108.0),
        finance_lease_liability_noncurrent=_direct(1967.0),
        debt_principal_schedule=_direct(11568.0),
        debt_fair_value_hedge_adjustment=_direct(-77.0),  # wrong sign
    ))
    assert sign_flipped["debt_bridge_check"]["status"] == "FAIL"


def test_current_portion_is_subtracted_exactly_once_in_the_bridge():
    """The bridge subtracts the current portion once to land on the
    noncurrent carrying value -- subtracting zero times or twice must both
    break it."""
    out = derive(_debt_view())
    assert out["debt_bridge_check"]["status"] == "PASS"
    # Doubling the current-portion input (simulating a double-subtraction bug
    # elsewhere) must break the bridge, proving the check is sensitive to it.
    doubled_current = derive(_debt_view(long_term_debt_gaap_carrying_value_current=_direct(2130.0 * 2)))
    # NOTE: this also changes long_term_debt_gaap_carrying_value itself (since
    # it's current+noncurrent), which is the correct, honest behavior -- the
    # bridge check still must not silently pass with an internally
    # inconsistent set of inputs.
    assert doubled_current["debt_bridge_check"]["status"] == "FAIL"


@pytest.mark.parametrize("fy_fixture", [
    dict(ltd_nc=13549.0, ltd_cur=171.0, fl_cur=108.0, fl_nc=1967.0, principal=11568.0, swap=77.0),   # FY2021
    dict(ltd_nc=16009.0, ltd_cur=130.0, fl_cur=129.0, fl_nc=1943.0, principal=14141.0, swap=-74.0),  # FY2022
    dict(ltd_nc=14922.0, ltd_cur=1116.0, fl_cur=119.0, fl_nc=1894.0, principal=14151.0, swap=-126.0), # FY2023
    dict(ltd_nc=14304.0, ltd_cur=1636.0, fl_cur=136.0, fl_nc=2025.0, principal=13904.0, swap=-125.0), # FY2024
    dict(ltd_nc=14326.0, ltd_cur=2130.0, fl_cur=131.0, fl_nc=1982.0, principal=14398.0, swap=-55.0),  # FY2025
])
def test_all_five_years_debt_bridges_reconcile_to_zero_difference(fy_fixture):
    out = derive(_debt_view(
        long_term_debt_gaap_carrying_value_noncurrent=_direct(fy_fixture["ltd_nc"]),
        long_term_debt_gaap_carrying_value_current=_direct(fy_fixture["ltd_cur"]),
        finance_lease_liability_current=_direct(fy_fixture["fl_cur"]),
        finance_lease_liability_noncurrent=_direct(fy_fixture["fl_nc"]),
        debt_principal_schedule=_direct(fy_fixture["principal"]),
        debt_fair_value_hedge_adjustment=_direct(fy_fixture["swap"]),
    ))
    assert out["debt_bridge_check"]["status"] == "PASS"


def test_valuation_net_debt_excludes_finance_leases_consistently():
    """valuation_net_debt_excluding_leases must be computed from
    total_debt_gaap_excluding_separately_reported_leases (already lease-free),
    not from long_term_debt_gaap_carrying_value (which still includes
    leases) -- otherwise leases would leak into a metric whose name promises
    they're excluded."""
    out = derive(_debt_view())
    valuation = out["valuation_net_debt_excluding_leases"]["value"]
    total_excl = out["total_debt_gaap_excluding_separately_reported_leases"]["value"]
    cash = 5488.0
    assert valuation == total_excl - cash == 8855.0
    # If leases had leaked in, valuation would equal long_term_debt_gaap_carrying_value - cash instead.
    ltd = out["long_term_debt_gaap_carrying_value"]["value"]
    assert valuation != ltd - cash


def test_target_defined_net_debt_remains_unavailable_even_with_full_debt_data():
    """Even when every other debt input is fully populated and the bridge
    passes, target_defined_net_debt must still be UNAVAILABLE -- its
    unavailability is permanent by design, not a side effect of missing data."""
    out = derive(_debt_view())
    assert out["debt_bridge_check"]["status"] == "PASS"
    assert out["target_defined_net_debt"] == {
        "status": "UNAVAILABLE", "value": None,
        "note": "Target discloses no net-debt measure of its own; never populated.",
    }


# --- config/metric_definitions.csv canonical-name coverage (2026-09-15 item 4) ---
# Every metric_definitions.csv row must correspond to an ACTUAL computed value
# in derive()'s output -- a formula marked 'reviewed' with nothing computing it
# is the same class of gap self-caught and fixed elsewhere this round (see
# config/metrics.csv's current_portion_of_debt and long_term_debt_gaap_carrying_value
# corrections, and docs/decisions.md's 'Mapping-approval self-caught gaps' entry).

def _full_fy2025_view():
    return {
        "revenue": _direct(106566.0), "cost_of_sales": _direct(77297.0),
        "operating_income": _direct(5197.0), "net_income": _direct(3770.0),
        "income_tax_expense": _direct(1081.0), "pretax_income": _direct(4851.0),
        "operating_cash_flow": _direct(6562.0), "capital_expenditure": _direct(3727.0),
        "cash_and_equivalents_balance_sheet": _direct(5488.0),
        "long_term_debt_gaap_carrying_value_noncurrent": _direct(14326.0),
        "long_term_debt_gaap_carrying_value_current": _direct(2130.0),
        "finance_lease_liability_current": _direct(131.0),
        "finance_lease_liability_noncurrent": _direct(1982.0),
        "debt_principal_schedule": _direct(14398.0),
        "debt_fair_value_hedge_adjustment": _direct(-55.0),
        "dividends_paid": _direct(2032.0), "share_repurchases": _direct(430.0),
        "inventory": _direct(12518.0), "accounts_payable": _direct(12922.0),
    }


def test_every_metric_definitions_canonical_name_is_actually_computed():
    """Regression guard for the whole metric_definitions.csv file: parses the
    real config CSV (not a hand-copied list) and asserts every row's metric
    name is a DERIVED (or legitimately non-DERIVED, e.g. NOT_APPLICABLE)
    key in derive()'s output -- never simply absent.
    """
    import csv as _csv
    from pathlib import Path as _Path

    out = derive(_full_fy2025_view())
    repo_root = _Path(__file__).resolve().parents[2]
    with open(repo_root / "config" / "metric_definitions.csv", newline="") as f:
        derived_metric_names = [row["metric"] for row in _csv.DictReader(f)]
    assert derived_metric_names, "metric_definitions.csv must not be empty"
    for metric in derived_metric_names:
        assert metric in out, f"{metric} has a metric_definitions.csv row but derive() never computes it"


def test_canonical_names_are_exact_aliases_of_their_legacy_internal_names():
    out = derive(_full_fy2025_view())
    assert out["gross_margin"] == out["gross_margin_pct"]
    assert out["operating_margin"] == out["operating_margin_pct"]
    assert out["effective_tax_rate"] == out["effective_tax_rate_pct"]
    assert out["net_margin"] == out["net_margin_pct"]
    assert out["free_cash_flow"] == out["fcf"]
    assert out["fcf_margin"] == out["fcf_margin_pct"]
    assert out["shareholder_distributions_to_fcf"] == out["distributions_pct_fcf"]
    assert out["total_debt_gaap"] == out["total_debt_gaap_excluding_separately_reported_leases"]
    assert out["free_cash_flow"]["value"] == 2835.0  # FY2025: 6562 - 3727


def test_cash_conversion_and_leverage_ratios_distinguish_blocked_from_not_applicable():
    """config/metric_definitions.csv states these as two DISTINCT policies,
    never collapsed: BLOCKED when the denominator is exactly zero,
    NOT_APPLICABLE when it is negative.
    """
    base = _full_fy2025_view()

    zero_ni = {**base, "net_income": _direct(0.0)}
    assert derive(zero_ni)["cash_conversion"]["status"] == "BLOCKED"

    negative_ni = {**base, "net_income": _direct(-100.0)}
    assert derive(negative_ni)["cash_conversion"]["status"] == "NOT_APPLICABLE"

    positive = derive(base)
    assert positive["cash_conversion"]["status"] == "DERIVED"
    assert positive["cash_conversion"]["value"] == round(6562.0 / 3770.0, 4)

    zero_cfo = {**base, "operating_cash_flow": _direct(0.0)}
    assert derive(zero_cfo)["debt_to_cfo"]["status"] == "BLOCKED"
    assert derive(zero_cfo)["net_debt_to_cfo"]["status"] == "BLOCKED"

    negative_cfo = {**base, "operating_cash_flow": _direct(-500.0)}
    assert derive(negative_cfo)["debt_to_cfo"]["status"] == "NOT_APPLICABLE"
    assert derive(negative_cfo)["net_debt_to_cfo"]["status"] == "NOT_APPLICABLE"


def test_capex_intensity_inventory_and_payables_ratios_computed():
    out = derive(_full_fy2025_view())
    assert out["capex_intensity"]["value"] == round(100 * 3727.0 / 106566.0, 2)
    assert out["inventory_to_revenue"]["value"] == round(100 * 12518.0 / 106566.0, 2)
    assert out["accounts_payable_to_cogs"]["value"] == round(100 * 12922.0 / 77297.0, 2)
