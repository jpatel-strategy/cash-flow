from decimal import Decimal

from target_cash.derive import (
    RawFactRow,
    derive_flow_metric,
    derive_point_in_time_metric,
)


def make_fact(fact_id, start, end, value, dim=None, concept="us-gaap:TestConcept", accession="acc-1"):
    return RawFactRow(
        fact_id=fact_id, accession_number=accession, cik="0000027419", unit="USD",
        start_date=start, end_date=end, dimensional_context=dim, value=Decimal(value),
        scale=6, sign_as_reported=1, is_superseded=False, concept=concept,
    )


# --- Point-in-time metrics -----------------------------------------------------

def test_derive_point_in_time_metric_covers_all_five_instants():
    facts = [
        make_fact("rf_opening", None, "2025-02-01", "4762000000"),
        make_fact("rf_q1", None, "2025-05-03", "2887000000"),
        make_fact("rf_q2", None, "2025-08-02", "4341000000"),
        make_fact("rf_q3", None, "2025-11-01", "3822000000"),
        make_fact("rf_q4", None, "2026-01-31", "5488000000"),
    ]
    outcome = derive_point_in_time_metric("cash_and_equivalents_balance_sheet", facts)
    assert outcome.errors == []
    assert len(outcome.quarterly_facts) == 5
    by_fq = {(qf.fiscal_year, qf.fiscal_quarter): qf for qf in outcome.quarterly_facts}
    assert by_fq[(2024, 4)].value_normalized == Decimal("4762.00")
    assert by_fq[(2025, 1)].value_normalized == Decimal("2887.00")
    assert by_fq[(2025, 4)].value_normalized == Decimal("5488.00")
    assert all(qf.basis == "point_in_time" for qf in outcome.quarterly_facts)


def test_derive_point_in_time_metric_records_lineage_for_every_fact():
    facts = [make_fact("rf_q1", None, "2025-05-03", "2887000000")]
    outcome = derive_point_in_time_metric("cash_and_equivalents_balance_sheet", facts)
    assert len(outcome.lineage_links) == 1
    link = outcome.lineage_links[0]
    assert link.input_fact_id == "rf_q1"
    assert link.derived_fact_id == outcome.quarterly_facts[0].quarterly_fact_id


def test_derive_point_in_time_metric_reports_missing_instant_as_error_not_silent_gap():
    facts = [make_fact("rf_q1", None, "2025-05-03", "2887000000")]  # only Q1 present
    outcome = derive_point_in_time_metric("cash_and_equivalents_balance_sheet", facts)
    assert len(outcome.quarterly_facts) == 1
    assert len(outcome.errors) == 4  # the other four instants are missing


def test_derive_point_in_time_metric_propagates_ambiguity_as_an_error_not_a_crash():
    facts = [
        make_fact("rf_a", None, "2025-05-03", "100000000"),
        make_fact("rf_b", None, "2025-05-03", "105000000"),  # two consolidated candidates, same instant
    ]
    outcome = derive_point_in_time_metric("cash_and_equivalents_balance_sheet", facts)
    assert len(outcome.quarterly_facts) == 0
    assert any("Ambiguous" in e for e in outcome.errors)


def test_derive_point_in_time_metric_excludes_dimensional_candidates():
    facts = [
        make_fact("rf_consolidated", None, "2025-05-03", "2887000000", dim=None),
        make_fact("rf_segment", None, "2025-05-03", "2887000000", dim="tgt:ReportableSegmentMember"),
    ]
    outcome = derive_point_in_time_metric("cash_and_equivalents_balance_sheet", facts)
    assert len(outcome.quarterly_facts) == 1
    assert outcome.lineage_links[0].input_fact_id == "rf_consolidated"


# --- Flow metrics: direct Q1-Q3 + derived Q4 (D&A opex / net_other_income pattern) --

def test_derive_flow_metric_with_direct_quarters_and_ytd_cross_check():
    facts = [
        make_fact("rf_q1", "2025-02-02", "2025-05-03", "655000000"),
        make_fact("rf_q2_direct", "2025-05-04", "2025-08-02", "632000000"),
        make_fact("rf_ytd6", "2025-02-02", "2025-08-02", "1287000000"),  # 655 + 632 = 1287, agrees exactly
        make_fact("rf_q3_direct", "2025-08-03", "2025-11-01", "649000000"),
        make_fact("rf_ytd9", "2025-02-02", "2025-11-01", "1936000000"),  # 1287 + 649 = 1936, agrees exactly
        make_fact("rf_annual", "2025-02-02", "2026-01-31", "2617000000"),
    ]
    outcome = derive_flow_metric("depreciation_amortization_opex", facts)
    assert outcome.errors == []

    by_fq = {qf.fiscal_quarter: qf for qf in outcome.quarterly_facts}
    assert len(by_fq) == 4
    assert by_fq[1].basis == "direct_quarterly"
    assert by_fq[2].basis == "direct_quarterly"
    assert by_fq[3].basis == "direct_quarterly"
    assert by_fq[4].basis == "derived_ytd_subtraction"
    assert by_fq[4].value_normalized == Decimal("681.00")  # 2617 - 1936

    # Independent validations exist for Q2 and Q3 (direct vs. YTD-derived) and are "validated"
    # since the direct facts agree exactly with the YTD-subtraction cross-check.
    by_quarter_validation = {v.check_name.split(":")[-1]: v for v in outcome.independent_validations}
    assert by_quarter_validation["Q2"].status == "validated"
    assert by_quarter_validation["Q3"].status == "validated"
    # Q4 has no discrete fact filed -- always "unavailable", never silently a pass.
    assert by_quarter_validation["Q4"].status == "unavailable"
    assert by_quarter_validation["Q4"].detail == "arithmetic invariant passed; independent quarter validation unavailable"


def test_derive_flow_metric_flags_disagreement_between_direct_and_ytd_derived():
    facts = [
        make_fact("rf_q1", "2025-02-02", "2025-05-03", "655000000"),
        make_fact("rf_q2_direct", "2025-05-04", "2025-08-02", "999000000"),  # deliberately wrong
        make_fact("rf_ytd6", "2025-02-02", "2025-08-02", "1287000000"),
        make_fact("rf_annual", "2025-02-02", "2026-01-31", "2617000000"),
        make_fact("rf_ytd9", "2025-02-02", "2025-11-01", "1936000000"),
    ]
    outcome = derive_flow_metric("depreciation_amortization_opex", facts)
    q2_validation = next(v for v in outcome.independent_validations if v.check_name.endswith("Q2"))
    assert q2_validation.status == "failed"
    # The direct (reported) fact is still what's stored analytically, per accounting policy
    # preference for direct facts -- the disagreement is flagged, not silently overridden.
    q2_fact = next(qf for qf in outcome.quarterly_facts if qf.fiscal_quarter == 2)
    assert q2_fact.value_normalized == Decimal("999.00")
    assert q2_fact.basis == "direct_quarterly"


# --- Flow metrics: YTD-only (D&A cash-flow add-back pattern) -----------------------

def test_derive_flow_metric_ytd_only_derives_q2_q3_q4():
    facts = [
        make_fact("rf_q1", "2025-02-02", "2025-05-03", "787000000"),
        make_fact("rf_ytd6", "2025-02-02", "2025-08-02", "1558000000"),
        make_fact("rf_ytd9", "2025-02-02", "2025-11-01", "2331000000"),
        make_fact("rf_annual", "2025-02-02", "2026-01-31", "3134000000"),
    ]
    outcome = derive_flow_metric("depreciation_amortization_cfo_addback", facts)
    assert outcome.errors == []

    by_fq = {qf.fiscal_quarter: qf for qf in outcome.quarterly_facts}
    assert by_fq[1].basis == "direct_quarterly"
    assert by_fq[2].basis == "derived_ytd_subtraction"
    assert by_fq[2].value_normalized == Decimal("771.00")  # 1558 - 787
    assert by_fq[3].basis == "derived_ytd_subtraction"
    assert by_fq[3].value_normalized == Decimal("773.00")  # 2331 - 1558
    assert by_fq[4].basis == "derived_ytd_subtraction"
    assert by_fq[4].value_normalized == Decimal("803.00")  # 3134 - 2331

    # No discrete quarter fact exists anywhere for this metric -> every derived quarter's
    # independent validation is "unavailable", never silently treated as a pass.
    assert all(v.status == "unavailable" for v in outcome.independent_validations)
    assert len(outcome.independent_validations) == 3  # Q2, Q3, Q4


def test_derive_flow_metric_records_two_lineage_links_per_derived_quarter():
    facts = [
        make_fact("rf_q1", "2025-02-02", "2025-05-03", "787000000"),
        make_fact("rf_ytd6", "2025-02-02", "2025-08-02", "1558000000"),
    ]
    outcome = derive_flow_metric("depreciation_amortization_cfo_addback", facts)
    q2_fact = next(qf for qf in outcome.quarterly_facts if qf.fiscal_quarter == 2)
    q2_links = [l for l in outcome.lineage_links if l.derived_fact_id == q2_fact.quarterly_fact_id]
    assert len(q2_links) == 2
    assert {l.input_fact_id for l in q2_links} == {"rf_ytd6", "rf_q1"}


def test_derive_flow_metric_missing_q1_anchor_is_a_fatal_error_for_that_metric():
    facts = [make_fact("rf_ytd6", "2025-02-02", "2025-08-02", "1558000000")]
    outcome = derive_flow_metric("depreciation_amortization_cfo_addback", facts)
    assert outcome.quarterly_facts == []
    assert any("Q1 anchor" in e for e in outcome.errors)
