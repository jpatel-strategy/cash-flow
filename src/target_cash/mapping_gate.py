"""The mapping_evidence_gate: whether a metric's SOURCE MAPPING has been
reviewed (source concept, statement location, context, unit, sign, authority,
equivalence, competing tags) -- a curation/review status, never inferable
from arithmetic. Kept structurally separate from the analytical_validation_gate
in target_cash.annual (which only proves the numbers are internally
consistent given whatever mapping is currently configured).

Passing analytical_validation_gate with a candidate_unverified mapping proves
nothing about whether the mapping itself is correct -- it only proves the
formula was applied consistently to whatever tag was picked. Annual
persistence requires BOTH gates to pass for a metric, per the reviewer's
explicit instruction (see docs/decisions.md, 2026-09-15 "Two-gate persistence
policy").
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MappingEvidenceResult:
    metric: str
    kind: str  # 'direct' (config/metrics.csv) or 'derived' (config/metric_definitions.csv)
    status: str  # PASS | BLOCKED
    mapping_status: str  # the raw status string found (e.g. 'reviewed', 'candidate_unverified', 'pending_debt_tests')
    detail: str


def load_metrics_csv(metrics_csv_path: str | Path) -> dict[str, dict]:
    with open(metrics_csv_path, newline="") as f:
        return {row["metric"]: row for row in csv.DictReader(f)}


def load_metric_definitions_csv(metric_definitions_csv_path: str | Path) -> dict[str, dict]:
    with open(metric_definitions_csv_path, newline="") as f:
        return {row["metric"]: row for row in csv.DictReader(f)}


def mapping_evidence_gate(
    direct_metrics: list[str],
    derived_metrics: list[str],
    metrics_csv_path: str | Path,
    metric_definitions_csv_path: str | Path,
) -> list[MappingEvidenceResult]:
    """PASS only for a metric whose config row status is exactly 'reviewed'.
    Any other status (candidate_unverified, pending_debt_tests, or the
    metric simply not existing in the config file) is BLOCKED -- a mapping
    evidence gap, never silently treated as passing.
    """
    metrics = load_metrics_csv(metrics_csv_path)
    definitions = load_metric_definitions_csv(metric_definitions_csv_path)
    results: list[MappingEvidenceResult] = []

    for metric in direct_metrics:
        row = metrics.get(metric)
        if row is None:
            results.append(MappingEvidenceResult(metric, "direct", "BLOCKED", "missing", f"{metric} has no config/metrics.csv row at all"))
            continue
        status = row["annual_mapping_status"]
        if status == "reviewed":
            results.append(MappingEvidenceResult(metric, "direct", "PASS", status, "config/metrics.csv annual_mapping_status=reviewed"))
        else:
            results.append(MappingEvidenceResult(metric, "direct", "BLOCKED", status, f"config/metrics.csv annual_mapping_status={status!r}, not 'reviewed'"))

    for metric in derived_metrics:
        row = definitions.get(metric)
        if row is None:
            results.append(MappingEvidenceResult(metric, "derived", "BLOCKED", "missing", f"{metric} has no config/metric_definitions.csv row at all"))
            continue
        status = row["review_status"]
        if status == "reviewed":
            results.append(MappingEvidenceResult(metric, "derived", "PASS", status, "config/metric_definitions.csv review_status=reviewed"))
        else:
            results.append(MappingEvidenceResult(metric, "derived", "BLOCKED", status, f"config/metric_definitions.csv review_status={status!r}, not 'reviewed'"))

    return results


def summarize_mapping_evidence_gate(results: list[MappingEvidenceResult]) -> dict:
    passed = [r.metric for r in results if r.status == "PASS"]
    blocked = [r.metric for r in results if r.status == "BLOCKED"]
    return {
        "checks_run": len(results),
        "passed_count": len(passed),
        "blocked_count": len(blocked),
        "passed_metrics": sorted(passed),
        "blocked_metrics": sorted(blocked),
        "gate_passed_metrics": sorted(passed),  # eligible for persistence per this gate alone
        "detail": [
            {"metric": r.metric, "kind": r.kind, "status": r.status, "mapping_status": r.mapping_status, "detail": r.detail}
            for r in results
        ],
    }


def persistence_eligible_metrics(mapping_results: list[MappingEvidenceResult], analytical_gate_passed: bool) -> list[str]:
    """A metric is eligible for annual persistence only if BOTH gates pass:
    its own mapping_evidence_gate result is PASS, AND the overall
    analytical_validation_gate (target_cash.annual.summarize_annual_validation)
    did not FAIL. analytical_validation_gate is evaluated as a whole (not
    per-metric) since its checks are cross-metric bridges, not single-metric
    facts -- a FAIL anywhere in the arithmetic makes every metric's
    computed value suspect, not just the one nominally "in" that check.
    """
    if not analytical_gate_passed:
        return []
    return sorted(r.metric for r in mapping_results if r.status == "PASS")
