"""Reconciliation checks: the first data gate.

Every check returns a ReconciliationResult rather than raising, so a caller
(validate CLI, pytest) can collect every failure before deciding whether the
gate passes — hiding one failure inside a general success statement is
exactly what this module must not do.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class ReconciliationResult:
    check_name: str
    passed: bool
    expected: Optional[Decimal]
    actual: Optional[Decimal]
    difference: Optional[Decimal]
    tolerance_absolute: Decimal
    tolerance_relative_pct: Decimal
    detail: str

    def to_dict(self) -> dict:
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "expected": str(self.expected) if self.expected is not None else None,
            "actual": str(self.actual) if self.actual is not None else None,
            "difference": str(self.difference) if self.difference is not None else None,
            "tolerance_absolute": str(self.tolerance_absolute),
            "tolerance_relative_pct": str(self.tolerance_relative_pct),
            "detail": self.detail,
        }


def _within_tolerance(expected: Decimal, actual: Decimal, tolerance_absolute: Decimal, tolerance_relative_pct: Decimal) -> bool:
    difference = abs(expected - actual)
    relative_allowance = abs(expected) * (tolerance_relative_pct / Decimal("100"))
    allowance = max(tolerance_absolute, relative_allowance)
    return difference <= allowance


def check_annual_equals_quarters(
    metric: str,
    fiscal_year: int,
    annual_value: Optional[Decimal],
    q1: Optional[Decimal],
    q2: Optional[Decimal],
    q3: Optional[Decimal],
    q4: Optional[Decimal],
    tolerance_absolute: Decimal,
    tolerance_relative_pct: Decimal,
) -> ReconciliationResult:
    check_name = f"annual_equals_quarters:{metric}:{fiscal_year}"
    missing = [name for name, value in [("annual", annual_value), ("q1", q1), ("q2", q2), ("q3", q3), ("q4", q4)] if value is None]
    if missing:
        return ReconciliationResult(
            check_name=check_name,
            passed=False,
            expected=annual_value,
            actual=None,
            difference=None,
            tolerance_absolute=tolerance_absolute,
            tolerance_relative_pct=tolerance_relative_pct,
            detail=f"Missing values, cannot reconcile: {missing}. Missing is not zero.",
        )

    quarter_sum = q1 + q2 + q3 + q4
    passed = _within_tolerance(annual_value, quarter_sum, tolerance_absolute, tolerance_relative_pct)
    return ReconciliationResult(
        check_name=check_name,
        passed=passed,
        expected=annual_value,
        actual=quarter_sum,
        difference=annual_value - quarter_sum,
        tolerance_absolute=tolerance_absolute,
        tolerance_relative_pct=tolerance_relative_pct,
        detail="Sum of Q1-Q4 vs. reported annual total." if passed else "Sum of Q1-Q4 does not match the reported annual total within tolerance.",
    )


def check_cash_rollforward(
    fiscal_year: int,
    fiscal_quarter: int,
    beginning_cash: Optional[Decimal],
    cfo: Optional[Decimal],
    cfi: Optional[Decimal],
    cff: Optional[Decimal],
    fx_effect: Optional[Decimal],
    ending_cash: Optional[Decimal],
    tolerance_absolute: Decimal,
    tolerance_relative_pct: Decimal,
) -> ReconciliationResult:
    check_name = f"cash_rollforward:{fiscal_year}:Q{fiscal_quarter}"
    fx_effect = fx_effect if fx_effect is not None else Decimal("0")
    missing = [
        name
        for name, value in [
            ("beginning_cash", beginning_cash),
            ("cfo", cfo),
            ("cfi", cfi),
            ("cff", cff),
            ("ending_cash", ending_cash),
        ]
        if value is None
    ]
    if missing:
        return ReconciliationResult(
            check_name=check_name,
            passed=False,
            expected=ending_cash,
            actual=None,
            difference=None,
            tolerance_absolute=tolerance_absolute,
            tolerance_relative_pct=tolerance_relative_pct,
            detail=f"Missing values, cannot roll forward: {missing}. Missing is not zero.",
        )

    computed_ending_cash = beginning_cash + cfo + cfi + cff + fx_effect
    passed = _within_tolerance(ending_cash, computed_ending_cash, tolerance_absolute, tolerance_relative_pct)
    return ReconciliationResult(
        check_name=check_name,
        passed=passed,
        expected=ending_cash,
        actual=computed_ending_cash,
        difference=ending_cash - computed_ending_cash,
        tolerance_absolute=tolerance_absolute,
        tolerance_relative_pct=tolerance_relative_pct,
        detail="Beginning cash + CFO + CFI + CFF + FX effect vs. reported ending cash."
        if passed
        else "Cash roll-forward does not match reported ending cash within tolerance.",
    )
