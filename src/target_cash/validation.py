"""Orchestrates the Milestone 1 validation gate.

Combines reconciliation checks and lineage-completeness checks into one
machine-readable summary. Used by both `cli.py validate` and pytest — pytest
must observe the same pass/fail logic the CLI reports, not a separate
reimplementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from target_cash.lineage import LineageLink, find_facts_missing_lineage
from target_cash.reconcile import ReconciliationResult


@dataclass
class ValidationSummary:
    reconciliation_results: list[ReconciliationResult] = field(default_factory=list)
    facts_missing_lineage: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        all_reconciliations_passed = all(r.passed for r in self.reconciliation_results)
        no_missing_lineage = len(self.facts_missing_lineage) == 0
        has_at_least_one_check = len(self.reconciliation_results) > 0
        return has_at_least_one_check and all_reconciliations_passed and no_missing_lineage

    def to_dict(self) -> dict:
        return {
            "gate_passed": self.passed,
            "reconciliation_checks": [r.to_dict() for r in self.reconciliation_results],
            "facts_missing_lineage": self.facts_missing_lineage,
            "checks_run": len(self.reconciliation_results),
            "checks_failed": sum(1 for r in self.reconciliation_results if not r.passed),
        }


def run_validation(
    reconciliation_results: list[ReconciliationResult],
    derived_fact_ids: list[str],
    lineage_links: list[LineageLink],
) -> ValidationSummary:
    facts_missing_lineage = find_facts_missing_lineage(derived_fact_ids, lineage_links)
    return ValidationSummary(
        reconciliation_results=reconciliation_results,
        facts_missing_lineage=facts_missing_lineage,
    )
