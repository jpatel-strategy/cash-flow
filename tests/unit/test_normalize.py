from decimal import Decimal

import pytest

from target_cash.normalize import (
    NormalizationError,
    PeriodSpec,
    build_point_in_time_fact,
    derive_q2,
    derive_q3,
    derive_q4,
    normalize_unit,
    to_decimal,
)


def make_period(
    scope, value, start="2024-02-01", end=None, fiscal_year=2024, unit="USD", basis="US-GAAP-2024",
    cik="0000027419", dimensional_context=None, accession="0000027419-24-000001",
    is_superseded=False, sign_as_reported=1,
):
    return PeriodSpec(
        fiscal_year=fiscal_year,
        scope=scope,
        unit=unit,
        accounting_basis=basis,
        start_date=start,
        end_date=end or start,
        value=to_decimal(value),
        cik=cik,
        dimensional_context=dimensional_context,
        accession_number=accession,
        is_superseded=is_superseded,
        sign_as_reported=sign_as_reported,
    )


def test_to_decimal_avoids_binary_float_error():
    # 0.1 + 0.2 != 0.3 in binary float; Decimal must not reproduce that.
    assert to_decimal("100000000.10") + to_decimal("200000000.20") == to_decimal("300000000.30")


def test_normalize_unit_usd_to_millions():
    assert normalize_unit(Decimal("1234500000"), "USD") == Decimal("1234.50")


def test_normalize_unit_rejects_unknown_unit():
    with pytest.raises(NormalizationError):
        normalize_unit(Decimal("100"), "EUR")


def test_derive_q2_subtracts_q1_from_six_month_ytd():
    q1 = make_period("Q1", "100000000", start="2024-02-01", end="2024-05-04")
    ytd6 = make_period("six_month_YTD", "210000000", start="2024-02-01", end="2024-08-03")
    assert derive_q2(ytd6, q1) == Decimal("110000000")


def test_derive_q3_subtracts_six_month_from_nine_month_ytd():
    ytd6 = make_period("six_month_YTD", "210000000", start="2024-02-01", end="2024-08-03")
    ytd9 = make_period("nine_month_YTD", "330000000", start="2024-02-01", end="2024-11-02")
    assert derive_q3(ytd9, ytd6) == Decimal("120000000")


def test_derive_q4_subtracts_nine_month_from_annual():
    ytd9 = make_period("nine_month_YTD", "330000000", start="2024-02-01", end="2024-11-02")
    annual = make_period("annual", "460000000", start="2024-02-01", end="2025-02-01")
    assert derive_q4(annual, ytd9) == Decimal("130000000")


def test_derive_q2_rejects_mismatched_fiscal_year():
    q1 = make_period("Q1", "100", start="2024-02-01", end="2024-05-04", fiscal_year=2024)
    ytd6 = make_period("six_month_YTD", "210", start="2023-02-01", end="2023-08-03", fiscal_year=2023)
    with pytest.raises(NormalizationError):
        derive_q2(ytd6, q1)


def test_derive_q2_rejects_mismatched_unit():
    q1 = make_period("Q1", "100", unit="USD")
    ytd6 = make_period("six_month_YTD", "210", unit="USD_millions")
    with pytest.raises(NormalizationError):
        derive_q2(ytd6, q1)


def test_derive_q2_rejects_mismatched_accounting_basis():
    q1 = make_period("Q1", "100", basis="US-GAAP-2023")
    ytd6 = make_period("six_month_YTD", "210", basis="US-GAAP-2024")
    with pytest.raises(NormalizationError):
        derive_q2(ytd6, q1)


def test_derive_q2_rejects_mismatched_start_date():
    q1 = make_period("Q1", "100", start="2024-02-01", end="2024-05-04")
    ytd6 = make_period("six_month_YTD", "210", start="2024-02-08", end="2024-08-03")
    with pytest.raises(NormalizationError):
        derive_q2(ytd6, q1)


def test_derive_q2_rejects_wrong_scope_labels():
    not_q1 = make_period("annual", "100")
    ytd6 = make_period("six_month_YTD", "210")
    with pytest.raises(NormalizationError):
        derive_q2(ytd6, not_q1)


def test_derive_q2_rejects_mismatched_entity():
    q1 = make_period("Q1", "100", cik="0000027419")
    ytd6 = make_period("six_month_YTD", "210", cik="0000320193")  # a different filer's CIK
    with pytest.raises(NormalizationError, match="entity"):
        derive_q2(ytd6, q1)


def test_derive_q2_rejects_non_consolidated_dimensional_context():
    q1 = make_period("Q1", "100", dimensional_context=None)
    ytd6 = make_period("six_month_YTD", "210", dimensional_context="SegmentMember")
    with pytest.raises(NormalizationError, match="consolidated_scope"):
        derive_q2(ytd6, q1)


def test_derive_q2_rejects_superseded_input_mixed_with_current():
    q1 = make_period("Q1", "100", is_superseded=False)
    ytd6 = make_period("six_month_YTD", "210", is_superseded=True)
    with pytest.raises(NormalizationError, match="filing_version"):
        derive_q2(ytd6, q1)


def test_derive_q2_rejects_mismatched_sign_convention():
    q1 = make_period("Q1", "100", sign_as_reported=1)
    ytd6 = make_period("six_month_YTD", "210", sign_as_reported=-1)
    with pytest.raises(NormalizationError, match="sign_convention"):
        derive_q2(ytd6, q1)


def test_derive_q2_reports_every_failed_dimension_at_once():
    q1 = make_period("Q1", "100", cik="0000027419", fiscal_year=2024, unit="USD")
    ytd6 = make_period("six_month_YTD", "210", cik="0000320193", fiscal_year=2023, unit="USD_millions")
    with pytest.raises(NormalizationError) as excinfo:
        derive_q2(ytd6, q1)
    message = str(excinfo.value)
    assert "entity" in message
    assert "fiscal_year" in message
    assert "unit" in message


def test_point_in_time_fact_is_never_a_difference():
    fact = build_point_in_time_fact(
        metric="cash_and_equivalents",
        fiscal_year=2024,
        fiscal_quarter=1,
        as_of="2024-05-04",
        value=to_decimal("500000000"),
        original_unit="USD",
    )
    assert fact.basis == "point_in_time"
    assert fact.period_start is None
    assert fact.value_normalized == Decimal("500.00")
