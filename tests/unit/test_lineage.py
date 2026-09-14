from target_cash.lineage import find_facts_missing_lineage, link_direct, link_ytd_subtraction
from target_cash.validation import run_validation


def test_link_direct_creates_single_link():
    link = link_direct("qf_1", "rf_1")
    assert link.derived_fact_id == "qf_1"
    assert link.input_fact_id == "rf_1"
    assert link.operation == "direct"


def test_link_ytd_subtraction_creates_two_links():
    links = link_ytd_subtraction("qf_q2", "rf_ytd6", "rf_q1", operation="ytd6_minus_q1")
    assert len(links) == 2
    assert {l.input_fact_id for l in links} == {"rf_ytd6", "rf_q1"}
    assert all(l.derived_fact_id == "qf_q2" for l in links)


def test_find_facts_missing_lineage_flags_unlinked_fact():
    links = [link_direct("qf_1", "rf_1")]
    missing = find_facts_missing_lineage(["qf_1", "qf_2"], links)
    assert missing == ["qf_2"]


def test_find_facts_missing_lineage_empty_when_all_linked():
    links = link_ytd_subtraction("qf_q2", "rf_ytd6", "rf_q1", operation="ytd6_minus_q1")
    missing = find_facts_missing_lineage(["qf_q2"], links)
    assert missing == []


def test_validation_gate_fails_when_a_derived_fact_has_no_lineage():
    links = [link_direct("qf_1", "rf_1")]
    summary = run_validation(reconciliation_results=[], derived_fact_ids=["qf_1", "qf_2"], lineage_links=links)
    assert not summary.passed
    assert summary.facts_missing_lineage == ["qf_2"]


def test_validation_gate_fails_with_zero_checks_run():
    # An empty validation run must not report success by default.
    summary = run_validation(reconciliation_results=[], derived_fact_ids=[], lineage_links=[])
    assert not summary.passed
    assert summary.to_dict()["checks_run"] == 0
