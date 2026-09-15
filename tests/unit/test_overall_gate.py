"""Unit tests for target_cash.validation.compute_overall_gate_passed --
the composite gate `cli.py`'s `validate` command actually calls (2026-09-16
'overall-gate enforcement' round). Exercises the exact function the CLI
uses, per validation.py's own stated principle: pytest must observe the
same pass/fail logic the CLI reports, not a separate reimplementation.
"""
import itertools

from target_cash.validation import compute_overall_gate_passed


def test_milestone_1_pass_mapping_fail_annual_pass_is_overall_fail():
    assert compute_overall_gate_passed(True, False, True) is False


def test_milestone_1_pass_mapping_pass_annual_fail_is_overall_fail():
    assert compute_overall_gate_passed(True, True, False) is False


def test_milestone_1_fail_mapping_pass_annual_pass_is_overall_fail():
    assert compute_overall_gate_passed(False, True, True) is False


def test_all_three_pass_is_overall_pass():
    assert compute_overall_gate_passed(True, True, True) is True


def test_full_truth_table_is_a_pure_and():
    """Every one of the 8 combinations matches a plain boolean AND -- no
    exceptions, no partial credit, no gate silently overridden."""
    for m1, mapping, annual in itertools.product([True, False], repeat=3):
        expected = m1 and mapping and annual
        assert compute_overall_gate_passed(m1, mapping, annual) is expected, (m1, mapping, annual)
