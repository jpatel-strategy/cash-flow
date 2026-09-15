from decimal import Decimal

from target_cash.reconcile import (
    check_arithmetic_invariant,
    check_cash_flow_composition,
    check_cash_movement,
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
        concept_directionality_a="signed_bidirectional", concept_directionality_b="signed_bidirectional",
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


def test_source_compatibility_flags_normalization_policy_mismatch():
    result = check_source_compatibility(
        "test", **compat_kwargs(concept_directionality_b="positive_magnitude_expense")
    )
    assert not result.passed
    assert "normalization_policy" in result.failed_dimensions


def test_source_compatibility_accepts_opposite_raw_signs_under_the_same_directionality():
    """The 2026-09-15 fix: two signed_bidirectional facts with opposite economic
    signs (e.g. a positive annual figure and a negative nine-month figure) are
    compatible -- differing raw sign is never itself an incompatibility."""
    result = check_source_compatibility(
        "test", **compat_kwargs(
            concept_directionality_a="signed_bidirectional", concept_directionality_b="signed_bidirectional",
        )
    )
    assert result.passed


def test_source_compatibility_flags_concept_mismatch():
    result = check_source_compatibility(
        "test",
        **compat_kwargs(
            concept_a="us-gaap:NetCashProvidedByUsedInOperatingActivities",
            concept_b="us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        ),
    )
    assert not result.passed
    assert "concept_identity" in result.failed_dimensions


def test_source_compatibility_allows_approved_concept_equivalence():
    result = check_source_compatibility(
        "test",
        **compat_kwargs(
            concept_a="us-gaap:LegacyTag",
            concept_b="us-gaap:NewTag",
            approved_equivalent_concepts=frozenset({("us-gaap:LegacyTag", "us-gaap:NewTag")}),
        ),
    )
    assert result.passed


def test_source_compatibility_flags_scale_mismatch():
    result = check_source_compatibility("test", **compat_kwargs(scale_a=6, scale_b=3))
    assert not result.passed
    assert "scale" in result.failed_dimensions


def test_source_compatibility_period_adjacency_passes_when_b_ends_before_a():
    result = check_source_compatibility(
        "test", **compat_kwargs(end_date_a="2025-08-02", end_date_b="2025-05-03")
    )
    assert result.passed


def test_source_compatibility_period_adjacency_fails_when_not_strictly_ordered():
    # b (subtrahend) must end strictly before a (minuend) — equal end dates mean no real period to subtract.
    result = check_source_compatibility(
        "test", **compat_kwargs(end_date_a="2025-05-03", end_date_b="2025-05-03")
    )
    assert not result.passed
    assert "period_adjacency" in result.failed_dimensions


def test_source_compatibility_period_adjacency_fails_when_reversed():
    result = check_source_compatibility(
        "test", **compat_kwargs(end_date_a="2025-05-03", end_date_b="2025-08-02")
    )
    assert not result.passed
    assert "period_adjacency" in result.failed_dimensions


def test_source_compatibility_period_classification_passes_for_correctly_labeled_quarter():
    # Q1 FY2025: 2025-02-02 to 2025-05-03 is 91 days, within the Q1 range.
    result = check_source_compatibility(
        "test",
        **compat_kwargs(
            start_date_a="2025-02-02", end_date_a="2025-08-02", scope_a="six_month_YTD",
            start_date_b="2025-02-02", end_date_b="2025-05-03", scope_b="Q1",
        ),
    )
    assert result.passed


def test_source_compatibility_period_classification_fails_when_label_does_not_match_dates():
    # Labeled 'Q1' but actually spans six months' worth of days.
    result = check_source_compatibility(
        "test",
        **compat_kwargs(
            start_date_a="2025-02-02", end_date_a="2025-11-01", scope_a="nine_month_YTD",
            start_date_b="2025-02-02", end_date_b="2025-08-02", scope_b="Q1",
        ),
    )
    assert not result.passed
    assert "period_classification" in result.failed_dimensions


def test_source_compatibility_period_classification_skipped_when_scope_not_given():
    # No scope_a/scope_b passed at all (e.g. point-in-time facts) -> not checked, not a failure.
    result = check_source_compatibility(
        "test", **compat_kwargs(end_date_a="2025-08-02", end_date_b="2025-02-02")
    )
    assert "period_classification" not in result.failed_dimensions


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


def test_independent_quarter_validation_rejects_overlapping_source_facts():
    # The "independent" fact must not be one of the facts that produced the derived value.
    result = check_independent_quarter_validation(
        metric="revenue", fiscal_year=2025, fiscal_quarter=2,
        derived_value=Decimal("25211"), derived_source="6moYTD - Q1",
        independent_value=Decimal("25211"), independent_source="mislabeled discrete Q2 fact",
        tolerance_absolute=Decimal("1.5"),
        derived_input_fact_ids=frozenset({"rf_6moYTD", "rf_Q1"}),
        independent_fact_ids=frozenset({"rf_Q1"}),  # reuses an input fact — not actually independent
    )
    assert result.status == "not_independent"
    assert "rf_Q1" in result.fact_overlap


def test_independent_quarter_validation_passes_with_disjoint_fact_ids():
    result = check_independent_quarter_validation(
        metric="revenue", fiscal_year=2025, fiscal_quarter=2,
        derived_value=Decimal("25211"), derived_source="6moYTD - Q1",
        independent_value=Decimal("25211"), independent_source="discrete Q2 fact",
        tolerance_absolute=Decimal("1.5"),
        derived_input_fact_ids=frozenset({"rf_6moYTD", "rf_Q1"}),
        independent_fact_ids=frozenset({"rf_discreteQ2"}),
    )
    assert result.status == "validated"


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


def test_ytd_consistency_rejects_overlapping_source_facts():
    result = check_ytd_consistency(
        metric="revenue", fiscal_year=2025, ytd_label="nine_month_YTD",
        directly_reported_ytd=Decimal("74327"),
        sum_of_directly_reported_quarters=Decimal("74327"),
        tolerance_absolute=Decimal("2.0"),
        ytd_fact_ids=frozenset({"rf_9moYTD"}),
        quarter_fact_ids=frozenset({"rf_9moYTD", "rf_q3"}),  # bug: reused the YTD fact as if it were a quarter
    )
    assert not result.passed
    assert "Not an independent comparison" in result.detail


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


# --- Cash roll-forward: two layers (2026-09-15 redesign) ----------------------
# Layer A (check_cash_movement): beginning + reported net change = ending.
# Layer B (check_cash_flow_composition): CFO + CFI + CFF [+ reported FX] = reported net change.

def test_cash_movement_passes_within_tolerance():
    bound = compute_rounding_bound(2, 0)
    result = check_cash_movement(
        fiscal_year=2025, fiscal_quarter=0,
        beginning_cash=Decimal("4762"), reported_net_change=Decimal("726"), ending_cash=Decimal("5488"),
        tolerance_absolute=bound,
    )
    assert result.passed
    assert result.difference == Decimal("0")


def test_cash_movement_reports_residual_even_when_within_bound():
    bound = compute_rounding_bound(2, 0)
    result = check_cash_movement(
        fiscal_year=2025, fiscal_quarter=0,
        beginning_cash=Decimal("4762"), reported_net_change=Decimal("725"), ending_cash=Decimal("5488"),
        tolerance_absolute=bound,
    )
    assert result.passed
    assert result.difference == Decimal("1")  # residual reported, not hidden by the pass


def test_cash_movement_fails_when_out_of_tolerance():
    bound = compute_rounding_bound(2, 0)
    result = check_cash_movement(
        fiscal_year=2025, fiscal_quarter=0,
        beginning_cash=Decimal("4762"), reported_net_change=Decimal("0"),  # wildly wrong
        ending_cash=Decimal("5488"), tolerance_absolute=bound,
    )
    assert not result.passed
    assert result.status == "failed"


def test_cash_movement_missing_value_is_blocked_not_failed():
    """A missing required input means the check never executed -- this must be
    reported as BLOCKED, not as a numerical FAIL of Target's cash movement.
    """
    bound = compute_rounding_bound(2, 0)
    result = check_cash_movement(
        fiscal_year=2025, fiscal_quarter=0,
        beginning_cash=None, reported_net_change=Decimal("726"), ending_cash=Decimal("5488"),
        tolerance_absolute=bound,
    )
    assert not result.passed
    assert result.status == "blocked"
    assert "REQUIRED_INPUTS_UNAVAILABLE" in result.detail


def test_cash_flow_composition_passes_within_tolerance():
    bound = compute_rounding_bound(4, 0)
    result = check_cash_flow_composition(
        fiscal_year=2025, fiscal_quarter=0,
        cfo=Decimal("6562"), cfi=Decimal("-3649"), cff=Decimal("-2187"),
        reported_fx=None, reported_net_change=Decimal("726"),
        tolerance_absolute=bound,
    )
    assert result.passed
    assert result.difference == Decimal("0")


def test_cash_flow_composition_never_claims_fx_reported_when_absent():
    """The defining fix (2026-09-15): no separate FX fact/line must never be
    silently treated as a verified zero. It is reported as an explicit
    'unavailable' evidence status, with the gap surfaced as an arithmetic
    implication, never as an independently reported or verified FX fact.
    """
    bound = compute_rounding_bound(4, 0)
    result = check_cash_flow_composition(
        fiscal_year=2025, fiscal_quarter=0,
        cfo=Decimal("6562"), cfi=Decimal("-3649"), cff=Decimal("-2187"),
        reported_fx=None, reported_net_change=Decimal("726"),
        tolerance_absolute=bound,
    )
    assert result.fx_evidence_status == "unavailable"
    assert result.implied_fx_residual == Decimal("0")
    assert "not an independently reported or verified fx fact" in result.detail.lower()
    assert "verified as zero" not in result.detail.lower()
    assert "reported as zero" not in result.detail.lower()


def test_cash_flow_composition_uses_reported_fx_when_available():
    bound = compute_rounding_bound(5, 0)
    result = check_cash_flow_composition(
        fiscal_year=2025, fiscal_quarter=0,
        cfo=Decimal("6562"), cfi=Decimal("-3649"), cff=Decimal("-2187"),
        reported_fx=Decimal("-5"), reported_net_change=Decimal("721"),
        tolerance_absolute=bound,
    )
    assert result.fx_evidence_status == "reported"
    assert result.implied_fx_residual is None  # not needed -- FX was directly reported
    assert result.passed


def test_cash_flow_composition_fails_when_out_of_tolerance():
    bound = compute_rounding_bound(4, 0)
    result = check_cash_flow_composition(
        fiscal_year=2025, fiscal_quarter=0,
        cfo=Decimal("6562"), cfi=Decimal("0"),  # should have been -3649
        cff=Decimal("-2187"), reported_fx=None, reported_net_change=Decimal("726"),
        tolerance_absolute=bound,
    )
    assert not result.passed
    assert result.status == "failed"


def test_cash_flow_composition_missing_value_is_blocked_not_failed():
    bound = compute_rounding_bound(4, 0)
    result = check_cash_flow_composition(
        fiscal_year=2025, fiscal_quarter=0,
        cfo=None, cfi=Decimal("-3649"), cff=Decimal("-2187"),
        reported_fx=None, reported_net_change=Decimal("726"),
        tolerance_absolute=bound,
    )
    assert not result.passed
    assert result.status == "blocked"
    assert "REQUIRED_INPUTS_UNAVAILABLE" in result.detail
