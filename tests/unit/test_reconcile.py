from decimal import Decimal

from target_cash.reconcile import check_annual_equals_quarters, check_cash_rollforward

TOLERANCE_ABS = Decimal("1.0")
TOLERANCE_PCT = Decimal("0.5")


def test_annual_equals_quarters_passes_within_tolerance():
    result = check_annual_equals_quarters(
        metric="revenue",
        fiscal_year=2024,
        annual_value=Decimal("460.0"),
        q1=Decimal("100.0"),
        q2=Decimal("110.0"),
        q3=Decimal("120.0"),
        q4=Decimal("130.0"),
        tolerance_absolute=TOLERANCE_ABS,
        tolerance_relative_pct=TOLERANCE_PCT,
    )
    assert result.passed
    assert result.difference == Decimal("0.0")


def test_annual_equals_quarters_fails_outside_tolerance():
    result = check_annual_equals_quarters(
        metric="revenue",
        fiscal_year=2024,
        annual_value=Decimal("460.0"),
        q1=Decimal("100.0"),
        q2=Decimal("110.0"),
        q3=Decimal("120.0"),
        q4=Decimal("100.0"),  # off by 30, well outside a $1M / 0.5% tolerance
        tolerance_absolute=TOLERANCE_ABS,
        tolerance_relative_pct=TOLERANCE_PCT,
    )
    assert not result.passed


def test_annual_equals_quarters_fails_visibly_on_missing_quarter():
    result = check_annual_equals_quarters(
        metric="revenue",
        fiscal_year=2024,
        annual_value=Decimal("460.0"),
        q1=Decimal("100.0"),
        q2=None,  # missing is not zero
        q3=Decimal("120.0"),
        q4=Decimal("130.0"),
        tolerance_absolute=TOLERANCE_ABS,
        tolerance_relative_pct=TOLERANCE_PCT,
    )
    assert not result.passed
    assert "Missing" in result.detail


def test_cash_rollforward_passes_within_tolerance():
    result = check_cash_rollforward(
        fiscal_year=2024,
        fiscal_quarter=1,
        beginning_cash=Decimal("500.0"),
        cfo=Decimal("100.0"),
        cfi=Decimal("-40.0"),
        cff=Decimal("-20.0"),
        fx_effect=Decimal("0.0"),
        ending_cash=Decimal("540.0"),
        tolerance_absolute=TOLERANCE_ABS,
        tolerance_relative_pct=TOLERANCE_PCT,
    )
    assert result.passed


def test_cash_rollforward_fails_when_capex_omitted():
    # Simulates the classic bug: capex/investing outflow left out of the roll-forward.
    result = check_cash_rollforward(
        fiscal_year=2024,
        fiscal_quarter=1,
        beginning_cash=Decimal("500.0"),
        cfo=Decimal("100.0"),
        cfi=Decimal("0.0"),  # should have been -40.0
        cff=Decimal("-20.0"),
        fx_effect=Decimal("0.0"),
        ending_cash=Decimal("540.0"),
        tolerance_absolute=TOLERANCE_ABS,
        tolerance_relative_pct=TOLERANCE_PCT,
    )
    assert not result.passed


def test_cash_rollforward_missing_value_fails_visibly():
    result = check_cash_rollforward(
        fiscal_year=2024,
        fiscal_quarter=1,
        beginning_cash=None,
        cfo=Decimal("100.0"),
        cfi=Decimal("-40.0"),
        cff=Decimal("-20.0"),
        fx_effect=Decimal("0.0"),
        ending_cash=Decimal("540.0"),
        tolerance_absolute=TOLERANCE_ABS,
        tolerance_relative_pct=TOLERANCE_PCT,
    )
    assert not result.passed
    assert "Missing" in result.detail


def test_reconciliation_result_serializes_to_dict():
    result = check_annual_equals_quarters(
        metric="revenue",
        fiscal_year=2024,
        annual_value=Decimal("460.0"),
        q1=Decimal("100.0"),
        q2=Decimal("110.0"),
        q3=Decimal("120.0"),
        q4=Decimal("130.0"),
        tolerance_absolute=TOLERANCE_ABS,
        tolerance_relative_pct=TOLERANCE_PCT,
    )
    d = result.to_dict()
    assert d["passed"] is True
    assert d["check_name"] == "annual_equals_quarters:revenue:2024"
