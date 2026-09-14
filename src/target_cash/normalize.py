"""Normalization: raw filed facts -> quarterly_facts rows.

Implements the rules in docs/accounting_policies.md. Every function here
either returns a value with an explicit basis and unit, or raises — it never
silently substitutes a default.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

UNIT_DIVISORS = {
    "USD": Decimal("1000000"),
    "USD_millions": Decimal("1"),
}


class NormalizationError(ValueError):
    """Raised when facts cannot be safely combined or converted."""


@dataclass(frozen=True)
class PeriodSpec:
    fiscal_year: int
    scope: str  # 'Q1' | 'six_month_YTD' | 'nine_month_YTD' | 'annual'
    unit: str
    accounting_basis: str  # e.g. 'US-GAAP-2024'
    start_date: str
    end_date: str
    value: Decimal


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
    if a.fiscal_year != b.fiscal_year:
        raise NormalizationError(
            f"Fiscal year mismatch: {a.fiscal_year} vs {b.fiscal_year}; cannot combine periods across fiscal years."
        )
    if a.unit != b.unit:
        raise NormalizationError(f"Unit mismatch: {a.unit} vs {b.unit}; cannot combine without explicit conversion.")
    if a.accounting_basis != b.accounting_basis:
        raise NormalizationError(
            f"Accounting basis mismatch: {a.accounting_basis} vs {b.accounting_basis}; "
            "likely a restatement or standard adoption between the two periods. Stop and review."
        )


def derive_q2(six_month_ytd: PeriodSpec, q1: PeriodSpec) -> Decimal:
    if six_month_ytd.scope != "six_month_YTD" or q1.scope != "Q1":
        raise NormalizationError("derive_q2 requires a six_month_YTD period and a Q1 period.")
    _assert_compatible(six_month_ytd, q1)
    if q1.start_date != six_month_ytd.start_date:
        raise NormalizationError(
            "Q2 derivation requires Q1 and the 6-month YTD period to share the same start date."
        )
    return six_month_ytd.value - q1.value


def derive_q3(nine_month_ytd: PeriodSpec, six_month_ytd: PeriodSpec) -> Decimal:
    if nine_month_ytd.scope != "nine_month_YTD" or six_month_ytd.scope != "six_month_YTD":
        raise NormalizationError("derive_q3 requires a nine_month_YTD period and a six_month_YTD period.")
    _assert_compatible(nine_month_ytd, six_month_ytd)
    if nine_month_ytd.start_date != six_month_ytd.start_date:
        raise NormalizationError("Q3 derivation requires both YTD periods to share the same start date.")
    return nine_month_ytd.value - six_month_ytd.value


def derive_q4(annual: PeriodSpec, nine_month_ytd: PeriodSpec) -> Decimal:
    if annual.scope != "annual" or nine_month_ytd.scope != "nine_month_YTD":
        raise NormalizationError("derive_q4 requires an annual period and a nine_month_YTD period.")
    _assert_compatible(annual, nine_month_ytd)
    if annual.start_date != nine_month_ytd.start_date:
        raise NormalizationError("Q4 derivation requires the annual and 9-month YTD periods to share the same start date.")
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
