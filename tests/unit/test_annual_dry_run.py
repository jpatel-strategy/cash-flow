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
    assert out["fcf"]["value"] == 4018.0 - 5528.0
    assert out["distributions_pct_fcf"]["status"] == "NOT_APPLICABLE"


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
