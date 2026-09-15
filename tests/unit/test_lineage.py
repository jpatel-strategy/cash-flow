from decimal import Decimal

from target_cash.lineage import find_facts_missing_lineage, link_direct, link_ytd_subtraction
from target_cash.reconcile import (
    check_arithmetic_invariant,
    check_cash_rollforward,
    check_independent_quarter_validation,
    compute_rounding_bound,
)
from target_cash.validation import run_validation


def test_link_direct_creates_single_link():
    link = link_direct("qf_1", "rf_1")
    assert link.derived_fact_id == "qf_1"
    assert link.input_fact_id == "rf_1"
    assert link.operation == "direct"


def test_link_ytd_subtraction_creates_two_links():
    links = link_ytd_subtraction("qf_q2", "rf_ytd6", "rf_q1", operation="ytd6_minus_q1")
    assert len(links) == 2
    assert {l.input_fact_id for l in links} == {"rf_ytd6", "rf_q1"}
    assert all(l.derived_fact_id == "qf_q2" for l in links)


def test_find_facts_missing_lineage_flags_unlinked_fact():
    links = [link_direct("qf_1", "rf_1")]
    missing = find_facts_missing_lineage(["qf_1", "qf_2"], links)
    assert missing == ["qf_2"]


def test_find_facts_missing_lineage_empty_when_all_linked():
    links = link_ytd_subtraction("qf_q2", "rf_ytd6", "rf_q1", operation="ytd6_minus_q1")
    missing = find_facts_missing_lineage(["qf_q2"], links)
    assert missing == []


def test_validation_gate_fails_when_a_derived_fact_has_no_lineage_even_if_checks_pass():
    links = [link_direct("qf_1", "rf_1")]
    passing_check = check_arithmetic_invariant("some_check", Decimal("1"), Decimal("1"))
    summary = run_validation(
        derived_fact_ids=["qf_1", "qf_2"],
        lineage_links=links,
        arithmetic_invariant_results=[passing_check],
    )
    assert not summary.passed  # missing lineage on qf_2 fails the gate despite the passing check
    assert summary.facts_missing_lineage == ["qf_2"]


def test_validation_gate_fails_with_zero_checks_run():
    # An empty validation run must not report success by default, even with no missing lineage.
    summary = run_validation(derived_fact_ids=[], lineage_links=[])
    assert not summary.passed
    assert summary.to_dict()["checks_run"] == 0


def test_validation_gate_fails_when_independent_validation_is_not_actually_independent():
    not_independent_check = check_independent_quarter_validation(
        metric="revenue", fiscal_year=2025, fiscal_quarter=2,
        derived_value=Decimal("25211"), derived_source="6moYTD - Q1",
        independent_value=Decimal("25211"), independent_source="mislabeled",
        tolerance_absolute=Decimal("1.5"),
        derived_input_fact_ids=frozenset({"rf_q1"}),
        independent_fact_ids=frozenset({"rf_q1"}),
    )
    summary = run_validation(
        derived_fact_ids=[], lineage_links=[],
        independent_validation_results=[not_independent_check],
    )
    assert not summary.passed  # a "not_independent" result must never pass the gate, even though values agree


# --- Validation status classification (2026-09-15 correction) --------------------


def test_missing_required_input_is_classified_blocked_not_failed():
    bound = compute_rounding_bound(2, 0)
    blocked_check = check_cash_rollforward(
        fiscal_year=2025, fiscal_quarter=1,
        beginning_cash=None, cfo=None, cfi=None, cff=None, fx_effect=None,
        ending_cash=Decimal("2887"), rounding_bound=bound,
    )
    summary = run_validation(derived_fact_ids=[], lineage_links=[], cash_rollforward_results=[blocked_check])
    counts = summary.to_dict()
    assert counts["checks_blocked"] == 1
    assert counts["checks_failed"] == 0  # an unexecuted check must never be counted as a numerical failure


def test_calculated_out_of_tolerance_result_is_classified_failed():
    bound = compute_rounding_bound(2, 0)
    failing_check = check_cash_rollforward(
        fiscal_year=2025, fiscal_quarter=1,
        beginning_cash=Decimal("100"), cfo=Decimal("10"), cfi=Decimal("0"), cff=Decimal("0"),
        fx_effect=Decimal("0"), ending_cash=Decimal("500"),  # wildly off vs. computed 110
        rounding_bound=bound,
    )
    summary = run_validation(derived_fact_ids=[], lineage_links=[], cash_rollforward_results=[failing_check])
    counts = summary.to_dict()
    assert counts["checks_failed"] == 1
    assert counts["checks_blocked"] == 0


def test_unavailable_independent_evidence_does_not_erase_a_passed_arithmetic_invariant():
    holding_invariant = check_arithmetic_invariant("da_q4", Decimal("681"), Decimal("681"))
    unavailable_independent = check_independent_quarter_validation(
        metric="depreciation_amortization_opex", fiscal_year=2025, fiscal_quarter=4,
        derived_value=Decimal("681"), derived_source="annual minus nine_month_YTD",
        independent_value=None, independent_source="no discrete fact filed for this quarter",
        tolerance_absolute=Decimal("1.5"),
    )
    summary = run_validation(
        derived_fact_ids=[], lineage_links=[],
        arithmetic_invariant_results=[holding_invariant],
        independent_validation_results=[unavailable_independent],
    )
    counts = summary.to_dict()
    assert counts["checks_passed"] == 1  # the arithmetic invariant still counts as passed
    assert counts["checks_unavailable"] == 1  # tracked separately, never folded into failed or dropped
    assert counts["checks_failed"] == 0
    assert summary.passed  # "unavailable" independent evidence alone must not hold the gate open


def test_a_required_blocked_check_keeps_the_overall_gate_false():
    bound = compute_rounding_bound(2, 0)
    blocked_check = check_cash_rollforward(
        fiscal_year=2025, fiscal_quarter=1,
        beginning_cash=None, cfo=None, cfi=None, cff=None, fx_effect=None,
        ending_cash=Decimal("2887"), rounding_bound=bound,
    )
    holding_invariant = check_arithmetic_invariant("unrelated_check", Decimal("1"), Decimal("1"))
    summary = run_validation(
        derived_fact_ids=[], lineage_links=[],
        arithmetic_invariant_results=[holding_invariant],
        cash_rollforward_results=[blocked_check],
    )
    counts = summary.to_dict()
    assert counts["checks_failed"] == 0  # no numerical failure anywhere
    assert counts["checks_blocked"] == 1
    assert not summary.passed  # a blocked required check still holds the gate open
