"""Normalization: raw filed facts -> quarterly_facts rows.

Implements the rules in docs/accounting_policies.md. Every function here
either returns a value with an explicit basis and unit, or raises — it never
silently substitutes a default.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

UNIT_DIVISORS = {
    "USD": Decimal("1000000"),
    "USD_millions": Decimal("1"),
}


class NormalizationError(ValueError):
    """Raised when facts cannot be safely combined or converted."""


class SelectionError(ValueError):
    """Raised when raw facts cannot be safely narrowed to one analytical fact."""


@dataclass(frozen=True)
class RawFactCandidate:
    """The minimal shape select_consolidated_fact needs from a raw_facts row."""

    fact_id: str
    dimensional_context: Optional[str]  # None = consolidated
    value: Decimal


def select_consolidated_fact(candidates: list[RawFactCandidate]) -> RawFactCandidate:
    """Narrow a pool of same-concept, same-period raw facts to the one
    consolidated (dimensionless) analytical fact.

    Dimensional facts (segment, product-category, equity-rollforward member,
    etc.) are excluded outright — they are never summed together as a
    substitute for a missing consolidated total, and never silently combined
    with a consolidated fact. If more than one consolidated candidate
    remains — even if their values happen to agree — this raises rather than
    picking one, since "which one is authoritative" is a judgment for a
    human reviewer, not a default. Callers must already have scoped
    `candidates` to one target period (e.g. one fiscal_year + scope); this
    function only resolves the dimensional-vs-consolidated axis within that
    scope.
    """
    consolidated = [c for c in candidates if c.dimensional_context is None]
    if len(consolidated) == 0:
        raise SelectionError(
            "No consolidated (dimensionless) candidate fact found among "
            f"{[c.fact_id for c in candidates]}; refusing to select or sum dimensional "
            "facts as a substitute for a missing consolidated total."
        )
    if len(consolidated) > 1:
        raise SelectionError(
            f"Ambiguous: {len(consolidated)} consolidated candidate facts found "
            f"({[c.fact_id for c in consolidated]}); human resolution required, not "
            "silently selecting one, even where their values agree."
        )
    return consolidated[0]


@dataclass(frozen=True)
class PeriodSpec:
    fiscal_year: int
    scope: str  # 'Q1' | 'six_month_YTD' | 'nine_month_YTD' | 'annual'
    unit: str
    accounting_basis: str  # e.g. 'US-GAAP-2024'
    start_date: str
    end_date: str
    value: Decimal
    cik: str = ""
    concept: str = ""  # exact XBRL tag, e.g. 'us-gaap:NetCashProvidedByUsedInOperatingActivities'
    scale: int = 6  # XBRL scale attribute; 6 = values expressed in millions
    dimensional_context: Optional[str] = None  # None = consolidated; anything else = segment/member scope
    accession_number: str = ""
    is_superseded: bool = False
    sign_as_reported: int = 1


def _new_quarterly_fact_id() -> str:
    return f"qf_{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True)
class QuarterlyFact:
    metric: str
    fiscal_year: int
    fiscal_quarter: int
    period_start: Optional[str]
    period_end: str
    days_in_period: Optional[int]
    value_original: Decimal
    original_unit: str
    value_normalized: Decimal
    normalized_unit: str
    basis: str  # 'direct_quarterly' | 'derived_ytd_subtraction' | 'point_in_time'
    quarterly_fact_id: str = field(default_factory=_new_quarterly_fact_id)


def to_decimal(raw_value) -> Decimal:
    """Parse a raw JSON/text numeric value as Decimal, never as binary float."""
    return Decimal(str(raw_value))


def normalize_unit(value: Decimal, original_unit: str, normalized_unit: str = "USD_millions") -> Decimal:
    if original_unit not in UNIT_DIVISORS:
        raise NormalizationError(f"Unrecognized unit for normalization: {original_unit!r}")
    if normalized_unit != "USD_millions":
        raise NormalizationError(f"Only normalization to USD_millions is implemented, got {normalized_unit!r}")
    divisor = UNIT_DIVISORS[original_unit]
    return (value / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _assert_compatible(a: PeriodSpec, b: PeriodSpec) -> None:
    """Precondition gate on two facts before any subtraction combines them.

    Delegates entirely to reconcile.check_source_compatibility (including the
    start-date dimension) so the derivation path here — which must raise and
    refuse to compute — and the audit/reporting path exposed to callers who
    want a structured pass/fail record share one single definition of
    "compatible". See docs/decisions.md, 2026-09-15 methodology correction.
    """
    from target_cash.reconcile import check_source_compatibility  # local import avoids a module cycle

    result = check_source_compatibility(
        check_name="normalize._assert_compatible",
        cik_a=a.cik, cik_b=b.cik,
        fiscal_year_a=a.fiscal_year, fiscal_year_b=b.fiscal_year,
        concept_a=a.concept, concept_b=b.concept,
        unit_a=a.unit, unit_b=b.unit,
        scale_a=a.scale, scale_b=b.scale,
        accounting_basis_a=a.accounting_basis, accounting_basis_b=b.accounting_basis,
        dimensional_context_a=a.dimensional_context, dimensional_context_b=b.dimensional_context,
        start_date_a=a.start_date, start_date_b=b.start_date,
        end_date_a=a.end_date, end_date_b=b.end_date,  # by convention a=minuend (longer), b=subtrahend (shorter)
        scope_a=a.scope, scope_b=b.scope,
        accession_a=a.accession_number, accession_b=b.accession_number,
        is_superseded_a=a.is_superseded, is_superseded_b=b.is_superseded,
        sign_as_reported_a=a.sign_as_reported, sign_as_reported_b=b.sign_as_reported,
    )
    if not result.passed:
        raise NormalizationError(
            f"Incompatible source facts on: {', '.join(result.failed_dimensions)} "
            f"(accessions {a.accession_number!r} and {b.accession_number!r}). {result.detail}"
        )


def derive_q2(six_month_ytd: PeriodSpec, q1: PeriodSpec) -> Decimal:
    if six_month_ytd.scope != "six_month_YTD" or q1.scope != "Q1":
        raise NormalizationError("derive_q2 requires a six_month_YTD period and a Q1 period.")
    _assert_compatible(six_month_ytd, q1)
    return six_month_ytd.value - q1.value


def derive_q3(nine_month_ytd: PeriodSpec, six_month_ytd: PeriodSpec) -> Decimal:
    if nine_month_ytd.scope != "nine_month_YTD" or six_month_ytd.scope != "six_month_YTD":
        raise NormalizationError("derive_q3 requires a nine_month_YTD period and a six_month_YTD period.")
    _assert_compatible(nine_month_ytd, six_month_ytd)
    return nine_month_ytd.value - six_month_ytd.value


def derive_q4(annual: PeriodSpec, nine_month_ytd: PeriodSpec) -> Decimal:
    if annual.scope != "annual" or nine_month_ytd.scope != "nine_month_YTD":
        raise NormalizationError("derive_q4 requires an annual period and a nine_month_YTD period.")
    _assert_compatible(annual, nine_month_ytd)
    return annual.value - nine_month_ytd.value


def days_between(start_date: str, end_date: str) -> int:
    return (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days + 1


def build_point_in_time_fact(metric: str, fiscal_year: int, fiscal_quarter: int, as_of: str, value: Decimal, original_unit: str) -> QuarterlyFact:
    """Balance-sheet stock value: stored as-is, never differenced."""
    return QuarterlyFact(
        metric=metric,
        fiscal_year=fiscal_year,
        fiscal_quarter=fiscal_quarter,
        period_start=None,
        period_end=as_of,
        days_in_period=None,
        value_original=value,
        original_unit=original_unit,
        value_normalized=normalize_unit(value, original_unit),
        normalized_unit="USD_millions",
        basis="point_in_time",
    )
