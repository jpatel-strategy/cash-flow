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

    def _counts(self) -> dict[str, int]:
        """Five mutually-exclusive buckets, per the 2026-09-15 status-classification
        correction: a check that never executed because a required input was
        unavailable is BLOCKED, never FAILED -- only a check that actually
        computed an out-of-tolerance result is FAILED. `checks_run` is the sum
        of all five and is the only backward-compatible aggregate kept.
        """
        passed = failed = blocked = unavailable = not_applicable = 0

        for r in self.compatibility_results:
            passed, failed = (passed + 1, failed) if r.passed else (passed, failed + 1)
        for r in self.arithmetic_invariant_results:
            passed, failed = (passed + 1, failed) if r.holds else (passed, failed + 1)
        for r in self.independent_validation_results:
            if r.status == "validated":
                passed += 1
            elif r.status == "unavailable":
                unavailable += 1
            elif r.status in ("failed", "not_independent"):
                failed += 1
            else:
                not_applicable += 1  # defensive: a status this module doesn't yet know about
        for r in self.ytd_consistency_results:
            if r.status == "passed":
                passed += 1
            elif r.status == "blocked":
                blocked += 1
            else:
                failed += 1
        for r in self.cash_rollforward_results:
            if r.status == "passed":
                passed += 1
            elif r.status == "blocked":
                blocked += 1
            else:
                failed += 1

        return {
            "checks_run": passed + failed + blocked + unavailable + not_applicable,
            "checks_passed": passed,
            "checks_failed": failed,
            "checks_blocked": blocked,
            "checks_unavailable": unavailable,
            "checks_not_applicable": not_applicable,
        }

    @property
    def passed(self) -> bool:
        counts = self._counts()
        if counts["checks_run"] == 0:
            return False  # an empty validation run must never report success by default
        # A BLOCKED check is not a numerical failure, but the gate still cannot pass
        # while a required check never ran -- "blocked" and "failed" both hold the
        # gate open; only "unavailable" (structurally no independent evidence can
        # exist, e.g. Q4) and "not_applicable" are non-blocking.
        return (
            counts["checks_failed"] == 0
            and counts["checks_blocked"] == 0
            and len(self.facts_missing_lineage) == 0
        )

    def to_dict(self) -> dict:
        counts = self._counts()
        return {
            "gate_passed": self.passed,
            "source_compatibility_checks": [r.to_dict() for r in self.compatibility_results],
            "arithmetic_invariant_checks": [r.to_dict() for r in self.arithmetic_invariant_results],
            "independent_quarter_validations": [r.to_dict() for r in self.independent_validation_results],
            "ytd_consistency_checks": [r.to_dict() for r in self.ytd_consistency_results],
            "cash_rollforward_checks": [r.to_dict() for r in self.cash_rollforward_results],
            "facts_missing_lineage": self.facts_missing_lineage,
            **counts,
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
