"""Unit tests for target_cash.mapping_gate -- the mapping_evidence_gate,
kept structurally separate from analytical_validation_gate (target_cash.annual).
These tests use isolated temp CSV fixtures, never the live config/*.csv files,
so they stay stable as the real config evolves.
"""
import csv

import pytest

from target_cash.mapping_gate import (
    mapping_evidence_gate,
    persistence_eligible_metrics,
    summarize_mapping_evidence_gate,
)

METRICS_FIELDS = ["metric", "mapping_status", "annual_mapping_status"]
DEFS_FIELDS = ["metric", "review_status"]


def _write_metrics_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=METRICS_FIELDS)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def _write_defs_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=DEFS_FIELDS)
        w.writeheader()
        for row in rows:
            w.writerow(row)


@pytest.fixture
def metrics_csv(tmp_path):
    p = tmp_path / "metrics.csv"
    _write_metrics_csv(p, [
        # quarterly mapping_status='reviewed' must NOT make the annual gate pass --
        # only annual_mapping_status is read for direct metrics.
        {"metric": "revenue", "mapping_status": "candidate_unverified", "annual_mapping_status": "reviewed"},
        {"metric": "diluted_eps", "mapping_status": "candidate_unverified", "annual_mapping_status": "reviewed"},
        {"metric": "inventory", "mapping_status": "candidate_unverified", "annual_mapping_status": "candidate_unverified"},
        {"metric": "cash_and_equivalents_balance_sheet", "mapping_status": "reviewed", "annual_mapping_status": "reviewed"},
    ])
    return p


@pytest.fixture
def definitions_csv(tmp_path):
    p = tmp_path / "metric_definitions.csv"
    _write_defs_csv(p, [
        {"metric": "gross_profit", "review_status": "reviewed"},
        {"metric": "total_debt_gaap", "review_status": "pending_debt_tests"},
    ])
    return p


def test_direct_metric_reads_annual_mapping_status_not_mapping_status(metrics_csv, definitions_csv):
    """Regression guard: this is exactly the bug that shipped and was caught --
    a metric whose quarterly mapping_status is candidate_unverified but whose
    annual_mapping_status is reviewed must PASS the annual gate.
    """
    results = mapping_evidence_gate(["revenue"], [], metrics_csv, definitions_csv)
    assert results[0].status == "PASS"
    assert results[0].mapping_status == "reviewed"


def test_direct_metric_non_dollar_unit_is_not_special_cased(metrics_csv, definitions_csv):
    """diluted_eps (USDPERSHARE) must be gated purely on annual_mapping_status,
    exactly like a dollar-denominated metric -- no unit-based branching here.
    """
    results = mapping_evidence_gate(["diluted_eps"], [], metrics_csv, definitions_csv)
    assert results[0].status == "PASS"


def test_direct_metric_candidate_unverified_is_blocked(metrics_csv, definitions_csv):
    results = mapping_evidence_gate(["inventory"], [], metrics_csv, definitions_csv)
    assert results[0].status == "BLOCKED"
    assert results[0].mapping_status == "candidate_unverified"


def test_direct_metric_missing_from_csv_is_blocked_not_skipped(metrics_csv, definitions_csv):
    results = mapping_evidence_gate(["nonexistent_metric"], [], metrics_csv, definitions_csv)
    assert results[0].status == "BLOCKED"
    assert results[0].mapping_status == "missing"


def test_derived_metric_reviewed_passes(metrics_csv, definitions_csv):
    results = mapping_evidence_gate([], ["gross_profit"], metrics_csv, definitions_csv)
    assert results[0].status == "PASS"
    assert results[0].kind == "derived"


def test_derived_metric_pending_debt_tests_is_blocked(metrics_csv, definitions_csv):
    results = mapping_evidence_gate([], ["total_debt_gaap"], metrics_csv, definitions_csv)
    assert results[0].status == "BLOCKED"
    assert results[0].mapping_status == "pending_debt_tests"


def test_derived_metric_missing_from_csv_is_blocked_not_skipped(metrics_csv, definitions_csv):
    results = mapping_evidence_gate([], ["nonexistent_derived"], metrics_csv, definitions_csv)
    assert results[0].status == "BLOCKED"
    assert results[0].mapping_status == "missing"


def test_summarize_counts_and_partitions_correctly(metrics_csv, definitions_csv):
    results = mapping_evidence_gate(
        ["revenue", "inventory"], ["gross_profit", "total_debt_gaap"], metrics_csv, definitions_csv,
    )
    summary = summarize_mapping_evidence_gate(results)
    assert summary["checks_run"] == 4
    assert summary["passed_count"] == 2
    assert summary["blocked_count"] == 2
    assert summary["passed_metrics"] == ["gross_profit", "revenue"]
    assert summary["blocked_metrics"] == ["inventory", "total_debt_gaap"]


def test_persistence_eligible_metrics_requires_both_gates(metrics_csv, definitions_csv):
    results = mapping_evidence_gate(
        ["revenue", "inventory"], ["gross_profit"], metrics_csv, definitions_csv,
    )
    # analytical gate failed overall -> nothing is eligible, even metrics
    # whose own mapping_evidence_gate result is PASS.
    assert persistence_eligible_metrics(results, analytical_gate_passed=False) == []
    # analytical gate passed -> only the PASS-status metrics are eligible.
    assert persistence_eligible_metrics(results, analytical_gate_passed=True) == ["gross_profit", "revenue"]
