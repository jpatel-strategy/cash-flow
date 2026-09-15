"""Reconciliation and validation checks: the first data gate.

Three distinct validation layers, per the methodology correction recorded in
docs/decisions.md (2026-09-15). They are never conflated:

1. **Source compatibility** (`check_source_compatibility`): a precondition on
   the raw facts feeding a derivation, checked *before* any arithmetic —
   same entity, fiscal year, unit, consolidated (non-dimensional) scope,
   compatible start/end dates, same filing vintage (no superseded input
   mixed with a current one), same sign convention. Failing this means the
   derivation must not be attempted, not that it produced a slightly-off
   number.

2. **Arithmetic invariant** (`check_arithmetic_invariant`): confirms a
   derivation formula was applied correctly by recomputing it. This holds by
   construction whenever the code is correct — it is a code-correctness
   check, not evidence about the underlying data, and must never be reported
   as if it "reconciles" or "validates" historical accuracy. In particular,
   summing four quarters back up to an annual total is tautological whenever
   the fourth quarter was itself derived as annual-minus-the-other-three;
   that class of check belongs here, honestly labeled, not under
   independent validation.

3. **Independent quarter validation** (`check_independent_quarter_validation`,
   `check_ytd_consistency`): the only checks that compare a derived value
   against a genuinely separately-sourced fact that was *not* used to derive
   it. These are the only checks with real diagnostic power over whether a
   derivation matches the company's own independent reporting. When no
   independent fact exists for a quarter (true for every Q4, since Target
   never files a discrete Q4 statement), the result is explicitly labeled
   "arithmetic invariant passed; independent quarter validation unavailable"
   — never silently treated as a pass.

`check_cash_rollforward`'s tolerance is a documented rounding-propagation
bound (`compute_rounding_bound`), not an arbitrary flat figure — see that
function's docstring. The residual is always reported, even when it falls
within the allowed bound.
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


@dataclass(frozen=True)
class CompatibilityCheckResult:
    check_name: str
    passed: bool
    failed_dimensions: tuple[str, ...]
    detail: str

    def to_dict(self) -> dict:
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "failed_dimensions": list(self.failed_dimensions),
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ArithmeticInvariantResult:
    check_name: str
    holds: bool
    stored_value: Decimal
    recomputed_value: Decimal
    detail: str = (
        "Confirms the derivation formula was applied correctly by recomputing it. "
        "This is a code-correctness check, not an independent validation of the "
        "underlying data — it holds by construction whenever the code is correct."
    )

    def to_dict(self) -> dict:
        return {
            "check_name": self.check_name,
            "holds": self.holds,
            "stored_value": str(self.stored_value),
            "recomputed_value": str(self.recomputed_value),
            "detail": self.detail,
        }


@dataclass(frozen=True)
class IndependentQuarterValidationResult:
    check_name: str
    status: str  # "validated" | "failed" | "unavailable"
    derived_value: Optional[Decimal]
    derived_source: str
    independent_value: Optional[Decimal]
    independent_source: str
    difference: Optional[Decimal]
    tolerance_absolute: Optional[Decimal]
    detail: str

    def to_dict(self) -> dict:
        return {
            "check_name": self.check_name,
            "status": self.status,
            "derived_value": str(self.derived_value) if self.derived_value is not None else None,
            "derived_source": self.derived_source,
            "independent_value": str(self.independent_value) if self.independent_value is not None else None,
            "independent_source": self.independent_source,
            "difference": str(self.difference) if self.difference is not None else None,
            "tolerance_absolute": str(self.tolerance_absolute) if self.tolerance_absolute is not None else None,
            "detail": self.detail,
        }


def check_source_compatibility(
    check_name: str,
    *,
    cik_a: str,
    cik_b: str,
    fiscal_year_a: int,
    fiscal_year_b: int,
    unit_a: str,
    unit_b: str,
    accounting_basis_a: str,
    accounting_basis_b: str,
    dimensional_context_a: Optional[str],
    dimensional_context_b: Optional[str],
    start_date_a: Optional[str],
    start_date_b: Optional[str],
    accession_a: str,
    accession_b: str,
    is_superseded_a: bool,
    is_superseded_b: bool,
    sign_as_reported_a: int,
    sign_as_reported_b: int,
) -> CompatibilityCheckResult:
    """Precondition check on two raw facts before any arithmetic combines them.

    Every dimension is checked independently and every failure is reported —
    this never short-circuits on the first mismatch, so a caller sees the
    full picture of why two facts are (or are not) safe to combine.
    """
    failed: list[str] = []
    if cik_a != cik_b:
        failed.append("entity")
    if fiscal_year_a != fiscal_year_b:
        failed.append("fiscal_year")
    if unit_a != unit_b:
        failed.append("unit")
    if accounting_basis_a != accounting_basis_b:
        failed.append("accounting_basis")
    if dimensional_context_a is not None or dimensional_context_b is not None:
        failed.append("consolidated_scope")
    if start_date_a != start_date_b:
        failed.append("start_date")
    if is_superseded_a or is_superseded_b:
        failed.append("filing_version")
    if sign_as_reported_a != sign_as_reported_b:
        failed.append("sign_convention")

    passed = len(failed) == 0
    detail = (
        "All source-compatibility dimensions match."
        if passed
        else f"Incompatible on: {', '.join(failed)}. Facts from accessions {accession_a!r} and {accession_b!r} must not be combined until resolved."
    )
    return CompatibilityCheckResult(check_name=check_name, passed=passed, failed_dimensions=tuple(failed), detail=detail)


def check_arithmetic_invariant(check_name: str, stored_value: Decimal, recomputed_value: Decimal) -> ArithmeticInvariantResult:
    return ArithmeticInvariantResult(
        check_name=check_name,
        holds=(stored_value == recomputed_value),
        stored_value=stored_value,
        recomputed_value=recomputed_value,
    )


def check_independent_quarter_validation(
    metric: str,
    fiscal_year: int,
    fiscal_quarter: int,
    derived_value: Decimal,
    derived_source: str,
    independent_value: Optional[Decimal],
    independent_source: str,
    tolerance_absolute: Decimal,
) -> IndependentQuarterValidationResult:
    """Compare a derived quarter against a separately-filed discrete-quarter fact.

    Pass `independent_value=None` when no such fact exists (always true for
    Q4, since Target never files a discrete fourth quarter) — the result is
    then explicitly labeled "unavailable", per the project owner's required
    wording, rather than silently omitted or treated as a pass.
    """
    check_name = f"independent_quarter_validation:{metric}:{fiscal_year}:Q{fiscal_quarter}"
    if independent_value is None:
        return IndependentQuarterValidationResult(
            check_name=check_name,
            status="unavailable",
            derived_value=derived_value,
            derived_source=derived_source,
            independent_value=None,
            independent_source=independent_source,
            difference=None,
            tolerance_absolute=None,
            detail="arithmetic invariant passed; independent quarter validation unavailable",
        )

    difference = derived_value - independent_value
    status = "validated" if abs(difference) <= tolerance_absolute else "failed"
    return IndependentQuarterValidationResult(
        check_name=check_name,
        status=status,
        derived_value=derived_value,
        derived_source=derived_source,
        independent_value=independent_value,
        independent_source=independent_source,
        difference=difference,
        tolerance_absolute=tolerance_absolute,
        detail=(
            f"Derived value ({derived_source}) vs. independently reported discrete-quarter fact ({independent_source})."
            if status == "validated"
            else f"Derived value ({derived_source}) disagrees with the independently reported discrete-quarter fact ({independent_source}) beyond tolerance."
        ),
    )


def check_ytd_consistency(
    metric: str,
    fiscal_year: int,
    ytd_label: str,
    directly_reported_ytd: Optional[Decimal],
    sum_of_directly_reported_quarters: Optional[Decimal],
    tolerance_absolute: Decimal,
) -> ReconciliationResult:
    """Compare a directly-filed YTD fact against the sum of directly-filed discrete quarters.

    Unlike summing quarters back up to an annual total (tautological when a
    quarter was derived as the residual), both sides here are independently
    filed by the company — this is a genuine consistency check, not a
    restatement of the arithmetic that produced either side.
    """
    check_name = f"ytd_consistency:{metric}:{fiscal_year}:{ytd_label}"
    if directly_reported_ytd is None or sum_of_directly_reported_quarters is None:
        return ReconciliationResult(
            check_name=check_name,
            passed=False,
            expected=directly_reported_ytd,
            actual=sum_of_directly_reported_quarters,
            difference=None,
            tolerance_absolute=tolerance_absolute,
            tolerance_relative_pct=Decimal("0"),
            detail="Missing values, cannot check YTD consistency. Missing is not zero.",
        )
    difference = directly_reported_ytd - sum_of_directly_reported_quarters
    passed = abs(difference) <= tolerance_absolute
    return ReconciliationResult(
        check_name=check_name,
        passed=passed,
        expected=directly_reported_ytd,
        actual=sum_of_directly_reported_quarters,
        difference=difference,
        tolerance_absolute=tolerance_absolute,
        tolerance_relative_pct=Decimal("0"),
        detail=f"Directly-reported {ytd_label} vs. sum of independently-filed discrete quarters."
        if passed
        else f"Directly-reported {ytd_label} disagrees with the sum of independently-filed discrete quarters beyond the rounding bound.",
    )


def compute_rounding_bound(
    num_directly_reported_components: int,
    num_ytd_derived_components: int,
    reporting_unit_usd_millions: Decimal = Decimal("1"),
) -> Decimal:
    """Worst-case propagated-rounding bound for a linear combination of reported values.

    Each directly-reported component is independently rounded by the filer to
    the nearest `reporting_unit_usd_millions` (Target rounds to the nearest
    $1M), so it carries a maximum rounding error of half that unit. A
    YTD-derived component is itself a subtraction of two independently
    rounded reported facts, so it inherits rounding error from both — twice
    the per-component bound.

    This is a worst-case (triangle-inequality) bound: it assumes every
    component's rounding error points the same direction, which is the most
    that could possibly happen, not a statistical expectation. It replaces an
    earlier flat $1M guess with a figure derived from how many independently-
    rounded facts actually feed the specific check being run — see
    docs/accounting_policies.md for worked examples.
    """
    half_unit = reporting_unit_usd_millions / Decimal("2")
    return (Decimal(num_directly_reported_components) + Decimal(2) * Decimal(num_ytd_derived_components)) * half_unit


def check_cash_rollforward(
    fiscal_year: int,
    fiscal_quarter: int,
    beginning_cash: Optional[Decimal],
    cfo: Optional[Decimal],
    cfi: Optional[Decimal],
    cff: Optional[Decimal],
    fx_effect: Optional[Decimal],
    ending_cash: Optional[Decimal],
    rounding_bound: Decimal,
) -> ReconciliationResult:
    """Beginning cash + CFO + CFI + CFF + FX effect vs. reported ending cash.

    `rounding_bound` must come from `compute_rounding_bound`, counting the
    actual independently-rounded and YTD-derived components feeding this
    specific period's roll-forward — never a flat guess. The residual is
    always reported in `difference`, even when it falls inside the bound.
    """
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
            tolerance_absolute=rounding_bound,
            tolerance_relative_pct=Decimal("0"),
            detail=f"Missing values, cannot roll forward: {missing}. Missing is not zero.",
        )

    computed_ending_cash = beginning_cash + cfo + cfi + cff + fx_effect
    residual = ending_cash - computed_ending_cash
    passed = abs(residual) <= rounding_bound
    return ReconciliationResult(
        check_name=check_name,
        passed=passed,
        expected=ending_cash,
        actual=computed_ending_cash,
        difference=residual,
        tolerance_absolute=rounding_bound,
        tolerance_relative_pct=Decimal("0"),
        detail=f"Residual {residual} vs. rounding bound ±{rounding_bound} (see compute_rounding_bound). "
        + ("Within bound." if passed else "Exceeds bound — investigate, do not widen the bound to force a pass."),
    )
