"""Orchestrates the Milestone 1 validation gate.

Keeps the three validation layers from reconcile.py distinct in the reported
summary — a reviewer must be able to tell "the derivation arithmetic is
self-consistent" apart from "an independent fact confirms this value" apart
from "no independent fact exists to check against". Collapsing them into one
undifferentiated pass/fail list is exactly the conflation the 2026-09-15
methodology correction (docs/decisions.md) requires fixing.

Used by both `cli.py validate` and pytest — pytest must observe the same
pass/fail logic the CLI reports, not a separate reimplementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from target_cash.lineage import LineageLink, find_facts_missing_lineage
from target_cash.reconcile import (
    ArithmeticInvariantResult,
    CompatibilityCheckResult,
    IndependentQuarterValidationResult,
    ReconciliationResult,
)


@dataclass
class ValidationSummary:
    compatibility_results: list[CompatibilityCheckResult] = field(default_factory=list)
    arithmetic_invariant_results: list[ArithmeticInvariantResult] = field(default_factory=list)
    independent_validation_results: list[IndependentQuarterValidationResult] = field(default_factory=list)
    ytd_consistency_results: list[ReconciliationResult] = field(default_factory=list)
    cash_rollforward_results: list[ReconciliationResult] = field(default_factory=list)
    facts_missing_lineage: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        checks_run = (
            len(self.compatibility_results)
            + len(self.arithmetic_invariant_results)
            + len(self.independent_validation_results)
            + len(self.ytd_consistency_results)
            + len(self.cash_rollforward_results)
        )
        if checks_run == 0:
            return False  # an empty validation run must never report success by default
        return (
            all(r.passed for r in self.compatibility_results)
            and all(r.holds for r in self.arithmetic_invariant_results)
            and all(r.status != "failed" for r in self.independent_validation_results)
            and all(r.passed for r in self.ytd_consistency_results)
            and all(r.passed for r in self.cash_rollforward_results)
            and len(self.facts_missing_lineage) == 0
        )

    def to_dict(self) -> dict:
        checks_run = (
            len(self.compatibility_results)
            + len(self.arithmetic_invariant_results)
            + len(self.independent_validation_results)
            + len(self.ytd_consistency_results)
            + len(self.cash_rollforward_results)
        )
        checks_failed = (
            sum(1 for r in self.compatibility_results if not r.passed)
            + sum(1 for r in self.arithmetic_invariant_results if not r.holds)
            + sum(1 for r in self.independent_validation_results if r.status == "failed")
            + sum(1 for r in self.ytd_consistency_results if not r.passed)
            + sum(1 for r in self.cash_rollforward_results if not r.passed)
        )
        return {
            "gate_passed": self.passed,
            "source_compatibility_checks": [r.to_dict() for r in self.compatibility_results],
            "arithmetic_invariant_checks": [r.to_dict() for r in self.arithmetic_invariant_results],
            "independent_quarter_validations": [r.to_dict() for r in self.independent_validation_results],
            "ytd_consistency_checks": [r.to_dict() for r in self.ytd_consistency_results],
            "cash_rollforward_checks": [r.to_dict() for r in self.cash_rollforward_results],
            "facts_missing_lineage": self.facts_missing_lineage,
            "checks_run": checks_run,
            "checks_failed": checks_failed,
            "independent_validations_unavailable": sum(
                1 for r in self.independent_validation_results if r.status == "unavailable"
            ),
        }


def run_validation(
    derived_fact_ids: list[str],
    lineage_links: list[LineageLink],
    compatibility_results: list[CompatibilityCheckResult] | None = None,
    arithmetic_invariant_results: list[ArithmeticInvariantResult] | None = None,
    independent_validation_results: list[IndependentQuarterValidationResult] | None = None,
    ytd_consistency_results: list[ReconciliationResult] | None = None,
    cash_rollforward_results: list[ReconciliationResult] | None = None,
) -> ValidationSummary:
    facts_missing_lineage = find_facts_missing_lineage(derived_fact_ids, lineage_links)
    return ValidationSummary(
        compatibility_results=compatibility_results or [],
        arithmetic_invariant_results=arithmetic_invariant_results or [],
        independent_validation_results=independent_validation_results or [],
        ytd_consistency_results=ytd_consistency_results or [],
        cash_rollforward_results=cash_rollforward_results or [],
        facts_missing_lineage=facts_missing_lineage,
    )
