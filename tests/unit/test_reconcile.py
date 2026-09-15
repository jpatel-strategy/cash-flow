from decimal import Decimal

from target_cash.reconcile import (
    check_arithmetic_invariant,
    check_cash_rollforward,
    check_independent_quarter_validation,
    check_source_compatibility,
    check_ytd_consistency,
    compute_rounding_bound,
)

TOLERANCE_ABS = Decimal("1.0")


def compat_kwargs(**overrides):
    base = dict(
        cik_a="0000027419", cik_b="0000027419",
        fiscal_year_a=2025, fiscal_year_b=2025,
        unit_a="USD", unit_b="USD",
        accounting_basis_a="US-GAAP-2024", accounting_basis_b="US-GAAP-2024",
        dimensional_context_a=None, dimensional_context_b=None,
        start_date_a="2025-02-02", start_date_b="2025-02-02",
        accession_a="0000027419-25-000101", accession_b="0000027419-25-000101",
        is_superseded_a=False, is_superseded_b=False,
        sign_as_reported_a=1, sign_as_reported_b=1,
    )
    base.update(overrides)
    return base


# --- Source compatibility -----------------------------------------------------

def test_source_compatibility_passes_when_everything_matches():
    result = check_source_compatibility("test", **compat_kwargs())
    assert result.passed
    assert result.failed_dimensions == ()


def test_source_compatibility_flags_entity_mismatch():
    result = check_source_compatibility("test", **compat_kwargs(cik_b="0000320193"))
    assert not result.passed
    assert "entity" in result.failed_dimensions


def test_source_compatibility_flags_dimensional_scope():
    result = check_source_compatibility("test", **compat_kwargs(dimensional_context_a="SegmentMember"))
    assert not result.passed
    assert "consolidated_scope" in result.failed_dimensions


def test_source_compatibility_flags_superseded_filing_version():
    result = check_source_compatibility("test", **compat_kwargs(is_superseded_b=True))
    assert not result.passed
    assert "filing_version" in result.failed_dimensions


def test_source_compatibility_flags_sign_convention():
    result = check_source_compatibility("test", **compat_kwargs(sign_as_reported_b=-1))
    assert not result.passed
    assert "sign_convention" in result.failed_dimensions


def test_source_compatibility_reports_every_failure_not_just_the_first():
    result = check_source_compatibility(
        "test", **compat_kwargs(cik_b="0000320193", unit_b="USD_millions", fiscal_year_b=2024)
    )
    assert set(result.failed_dimensions) == {"entity", "fiscal_year", "unit"}


# --- Arithmetic invariant (code-correctness, not data validation) -------------

def test_arithmetic_invariant_holds_when_recomputation_matches():
    result = check_arithmetic_invariant("q4_check", stored_value=Decimal("130"), recomputed_value=Decimal("130"))
    assert result.holds
    assert "code-correctness" in result.detail


def test_arithmetic_invariant_fails_when_recomputation_differs():
    result = check_arithmetic_invariant("q4_check", stored_value=Decimal("130"), recomputed_value=Decimal("131"))
    assert not result.holds


# --- Independent quarter validation --------------------------------------------

def test_independent_quarter_validation_passes_within_bound():
    result = check_independent_quarter_validation(
        metric="revenue", fiscal_year=2025, fiscal_quarter=2,
        derived_value=Decimal("25211"), derived_source="6moYTD - Q1",
        independent_value=Decimal("25211"), independent_source="discrete Q2 fact",
        tolerance_absolute=Decimal("1.5"),
    )
    assert result.status == "validated"
    assert result.difference == Decimal("0")


def test_independent_quarter_validation_fails_outside_bound():
    result = check_independent_quarter_validation(
        metric="revenue", fiscal_year=2025, fiscal_quarter=2,
        derived_value=Decimal("25211"), derived_source="6moYTD - Q1",
        independent_value=Decimal("25000"), independent_source="discrete Q2 fact",
        tolerance_absolute=Decimal("1.5"),
    )
    assert result.status == "failed"


def test_independent_quarter_validation_unavailable_uses_required_wording():
    result = check_independent_quarter_validation(
        metric="operating_cash_flow", fiscal_year=2025, fiscal_quarter=4,
        derived_value=Decimal("2495"), derived_source="annual - 9moYTD",
        independent_value=None, independent_source="none filed",
        tolerance_absolute=Decimal("1.5"),
    )
    assert result.status == "unavailable"
    assert result.detail == "arithmetic invariant passed; independent quarter validation unavailable"


# --- YTD consistency (genuinely independent, unlike annual = sum of quarters) --

def test_ytd_consistency_passes_within_bound():
    result = check_ytd_consistency(
        metric="revenue", fiscal_year=2025, ytd_label="nine_month_YTD",
        directly_reported_ytd=Decimal("74327"),
        sum_of_directly_reported_quarters=Decimal("74327"),
        tolerance_absolute=Decimal("2.0"),
    )
    assert result.passed


def test_ytd_consistency_fails_outside_bound():
    result = check_ytd_consistency(
        metric="revenue", fiscal_year=2025, ytd_label="nine_month_YTD",
        directly_reported_ytd=Decimal("74327"),
        sum_of_directly_reported_quarters=Decimal("74300"),
        tolerance_absolute=Decimal("2.0"),
    )
    assert not result.passed


def test_ytd_consistency_missing_value_fails_visibly():
    result = check_ytd_consistency(
        metric="revenue", fiscal_year=2025, ytd_label="nine_month_YTD",
        directly_reported_ytd=None,
        sum_of_directly_reported_quarters=Decimal("74300"),
        tolerance_absolute=Decimal("2.0"),
    )
    assert not result.passed
    assert "Missing" in result.detail


# --- Rounding bound -------------------------------------------------------------

def test_rounding_bound_directly_reported_only():
    # Annual cash roll-forward worked example: 6 directly-reported components.
    assert compute_rounding_bound(6, 0) == Decimal("3.0")


def test_rounding_bound_independent_quarter_validation_example():
    # 1 YTD-derived (counts double) + 1 directly-reported.
    assert compute_rounding_bound(1, 1) == Decimal("1.5")


def test_rounding_bound_ytd_consistency_example():
    assert compute_rounding_bound(4, 0) == Decimal("2.0")


def test_rounding_bound_scales_with_reporting_unit():
    assert compute_rounding_bound(2, 0, reporting_unit_usd_millions=Decimal("10")) == Decimal("10.0")


# --- Cash roll-forward (now takes a rounding bound, not a flat guess) ----------

def test_cash_rollforward_passes_within_rounding_bound():
    bound = compute_rounding_bound(6, 0)  # annual: $3.0M
    result = check_cash_rollforward(
        fiscal_year=2025, fiscal_quarter=0,
        beginning_cash=Decimal("4762"), cfo=Decimal("6562"), cfi=Decimal("-3649"),
        cff=Decimal("-2187"), fx_effect=Decimal("0"), ending_cash=Decimal("5488"),
        rounding_bound=bound,
    )
    assert result.passed
    assert result.difference == Decimal("0")


def test_cash_rollforward_reports_residual_even_when_within_bound():
    bound = compute_rounding_bound(6, 0)
    result = check_cash_rollforward(
        fiscal_year=2025, fiscal_quarter=0,
        beginning_cash=Decimal("4762"), cfo=Decimal("6562"), cfi=Decimal("-3649"),
        cff=Decimal("-2186"), fx_effect=Decimal("0"), ending_cash=Decimal("5488"),
        rounding_bound=bound,
    )
    assert result.passed
    assert result.difference == Decimal("-1")  # residual reported, not hidden by the pass


def test_cash_rollforward_fails_when_capex_omitted():
    bound = compute_rounding_bound(6, 0)
    result = check_cash_rollforward(
        fiscal_year=2025, fiscal_quarter=0,
        beginning_cash=Decimal("4762"), cfo=Decimal("6562"), cfi=Decimal("0"),  # should have been -3649
        cff=Decimal("-2187"), fx_effect=Decimal("0"), ending_cash=Decimal("5488"),
        rounding_bound=bound,
    )
    assert not result.passed


def test_cash_rollforward_missing_value_fails_visibly():
    bound = compute_rounding_bound(6, 0)
    result = check_cash_rollforward(
        fiscal_year=2025, fiscal_quarter=0,
        beginning_cash=None, cfo=Decimal("6562"), cfi=Decimal("-3649"),
        cff=Decimal("-2187"), fx_effect=Decimal("0"), ending_cash=Decimal("5488"),
        rounding_bound=bound,
    )
    assert not result.passed
    assert "Missing" in result.detail
