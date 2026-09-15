import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest

from target_cash.derive import (
    DerivationOutcome,
    RawFactRow,
    derive_flow_metric,
    derive_point_in_time_metric,
    derive_reviewed_metrics,
    persist_all_outcomes,
    persist_instant_facts,
    select_authoritative_fact,
)
from target_cash.lineage import LineageLink
from target_cash.migrations import apply_safe_migrations
from target_cash.normalize import QuarterlyFact, SelectionError

REPO_ROOT = Path(__file__).resolve().parents[2]


def make_fact(fact_id, start, end, value, dim=None, concept="us-gaap:TestConcept", accession="acc-1"):
    return RawFactRow(
        fact_id=fact_id, accession_number=accession, cik="0000027419", unit="USD",
        start_date=start, end_date=end, dimensional_context=dim, value=Decimal(value),
        scale=6, sign_as_reported=1, is_superseded=False, concept=concept,
    )


def make_quarterly_fact(metric, fiscal_quarter, basis="direct_quarterly", value=Decimal("100.00")):
    return QuarterlyFact(
        metric=metric, fiscal_year=2025, fiscal_quarter=fiscal_quarter,
        period_start="2025-02-02", period_end="2025-05-03", days_in_period=90,
        value_original=value, original_unit="USD_millions",
        value_normalized=value, normalized_unit="USD_millions", basis=basis,
    )


@pytest.fixture
def db_conn():
    """A real in-memory database built from the project's actual sql/schema.sql
    plus every safe migration (including instant_facts), so persistence is
    tested against real constraints (PRIMARY KEY, CHECK, FOREIGN KEY) -- not
    a hand-rolled stand-in schema, and matching exactly what a real
    connection via cli._connect_db has.
    """
    conn = sqlite3.connect(":memory:")
    conn.executescript((REPO_ROOT / "sql" / "schema.sql").read_text())
    apply_safe_migrations(conn)
    yield conn
    conn.close()


# --- Point-in-time metrics -----------------------------------------------------

def test_derive_point_in_time_metric_covers_all_five_instants():
    facts = [
        make_fact("rf_opening", None, "2025-02-01", "4762000000"),
        make_fact("rf_q1", None, "2025-05-03", "2887000000"),
        make_fact("rf_q2", None, "2025-08-02", "4341000000"),
        make_fact("rf_q3", None, "2025-11-01", "3822000000"),
        make_fact("rf_q4", None, "2026-01-31", "5488000000"),
    ]
    outcome = derive_point_in_time_metric("cash_and_equivalents_balance_sheet", facts, filing_period_ends={})
    assert outcome.errors == []
    assert len(outcome.quarterly_facts) == 5
    by_fq = {(qf.fiscal_year, qf.fiscal_quarter): qf for qf in outcome.quarterly_facts}
    assert by_fq[(2024, 4)].value_normalized == Decimal("4762.00")
    assert by_fq[(2025, 1)].value_normalized == Decimal("2887.00")
    assert by_fq[(2025, 4)].value_normalized == Decimal("5488.00")
    assert all(qf.basis == "point_in_time" for qf in outcome.quarterly_facts)


def test_derive_point_in_time_metric_records_lineage_for_every_fact():
    facts = [make_fact("rf_q1", None, "2025-05-03", "2887000000")]
    outcome = derive_point_in_time_metric("cash_and_equivalents_balance_sheet", facts, filing_period_ends={})
    assert len(outcome.lineage_links) == 1
    link = outcome.lineage_links[0]
    assert link.input_fact_id == "rf_q1"
    assert link.derived_fact_id == outcome.quarterly_facts[0].quarterly_fact_id


def test_derive_point_in_time_metric_reports_missing_instant_as_error_not_silent_gap():
    facts = [make_fact("rf_q1", None, "2025-05-03", "2887000000")]  # only Q1 present
    outcome = derive_point_in_time_metric("cash_and_equivalents_balance_sheet", facts, filing_period_ends={})
    assert len(outcome.quarterly_facts) == 1
    assert len(outcome.errors) == 4  # the other four instants are missing


def test_derive_point_in_time_metric_propagates_ambiguity_as_an_error_not_a_crash():
    facts = [
        make_fact("rf_a", None, "2025-05-03", "100000000"),
        make_fact("rf_b", None, "2025-05-03", "105000000"),  # two consolidated candidates, same instant
    ]
    outcome = derive_point_in_time_metric("cash_and_equivalents_balance_sheet", facts, filing_period_ends={})
    assert len(outcome.quarterly_facts) == 0
    assert any("Ambiguous" in e for e in outcome.errors)


def test_derive_point_in_time_metric_excludes_dimensional_candidates():
    facts = [
        make_fact("rf_consolidated", None, "2025-05-03", "2887000000", dim=None),
        make_fact("rf_segment", None, "2025-05-03", "2887000000", dim="tgt:ReportableSegmentMember"),
    ]
    outcome = derive_point_in_time_metric("cash_and_equivalents_balance_sheet", facts, filing_period_ends={})
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


# --- Dry-run / persistence control (item 3, 2026-09-15 corrective action) ---------


def test_a_deriving_without_persisting_writes_zero_rows(db_conn):
    """derive_reviewed_metrics computes outcomes in memory only. Nothing in this
    module writes to quarterly_facts/lineage unless persist_all_outcomes is
    separately, explicitly invoked -- this is the entire mechanism behind the
    CLI's default dry-run behavior (normalize with no --persist-derived).
    """
    db_conn.execute(
        "INSERT INTO filings (accession_number, cik, company_name, form_type, filed_at, "
        "period_of_report, primary_document_url, ingestion_method) VALUES "
        "('acc-1', '0000027419', 'Target Corporation', '10-Q', '2025-05-30', '2025-05-03', "
        "'https://example.invalid/acc-1', 'manual_upload')"
    )
    db_conn.execute(
        "INSERT INTO raw_facts (fact_id, accession_number, taxonomy, tag, unit, start_date, "
        "end_date, value, scale, sign_as_reported, is_superseded, retrieved_at) VALUES "
        "('rf_q1', 'acc-1', 'us-gaap', 'TestConcept', 'USD', NULL, '2025-05-03', "
        "'2887000000', 6, 1, 0, '2025-05-30T00:00:00Z')"
    )
    db_conn.commit()

    metrics_rows = [{
        "metric": "cash_and_equivalents_balance_sheet", "category": "point_in_time",
        "candidate_xbrl_tag": "TestConcept", "mapping_status": "reviewed",
    }]
    outcomes = derive_reviewed_metrics(db_conn, metrics_rows)
    assert len(outcomes["cash_and_equivalents_balance_sheet"].quarterly_facts) == 1  # computed...

    # ...but never written, because persist_all_outcomes was never called.
    assert db_conn.execute("SELECT COUNT(*) FROM quarterly_facts").fetchone()[0] == 0
    assert db_conn.execute("SELECT COUNT(*) FROM lineage").fetchone()[0] == 0


def test_b_persist_all_outcomes_writes_the_expected_rows(db_conn):
    outcome = DerivationOutcome("metric_a")
    outcome.quarterly_facts.append(make_quarterly_fact("metric_a", fiscal_quarter=1))
    outcome.quarterly_facts.append(make_quarterly_fact("metric_a", fiscal_quarter=2))

    written = persist_all_outcomes(db_conn, {"metric_a": outcome})

    assert written == {"metric_a": 2}
    assert db_conn.execute("SELECT COUNT(*) FROM quarterly_facts").fetchone()[0] == 2
    rows = db_conn.execute("SELECT fiscal_quarter, basis FROM quarterly_facts ORDER BY fiscal_quarter").fetchall()
    assert rows == [(1, "direct_quarterly"), (2, "direct_quarterly")]


def test_c_persist_all_outcomes_rolls_back_the_entire_batch_on_failure(db_conn):
    """One metric's write violates a real schema constraint (CHECK on `basis`).
    Even though an earlier metric in the same call would have succeeded on its
    own, persist_all_outcomes wraps the whole batch in one transaction, so
    that earlier metric's insert must not survive either.
    """
    good = DerivationOutcome("metric_good")
    good.quarterly_facts.append(make_quarterly_fact("metric_good", fiscal_quarter=1))

    bad = DerivationOutcome("metric_bad")
    bad.quarterly_facts.append(make_quarterly_fact("metric_bad", fiscal_quarter=1, basis="not_a_real_basis"))

    with pytest.raises(sqlite3.IntegrityError):
        persist_all_outcomes(db_conn, {"metric_good": good, "metric_bad": bad})

    # Neither metric's row survived -- the successful insert was rolled back
    # along with the failed one, not left half-committed.
    assert db_conn.execute("SELECT COUNT(*) FROM quarterly_facts").fetchone()[0] == 0


def test_d_persist_all_outcomes_is_idempotent_on_repeated_calls(db_conn):
    """Re-running persistence with the same computed outcome must not accumulate
    duplicate rows: each metric's prior quarterly_facts/lineage are cleared and
    rewritten fresh every call.
    """
    outcome = DerivationOutcome("metric_a")
    outcome.quarterly_facts.append(make_quarterly_fact("metric_a", fiscal_quarter=1))

    persist_all_outcomes(db_conn, {"metric_a": outcome})
    persist_all_outcomes(db_conn, {"metric_a": outcome})
    persist_all_outcomes(db_conn, {"metric_a": outcome})

    assert db_conn.execute("SELECT COUNT(*) FROM quarterly_facts").fetchone()[0] == 1


# --- Authoritative-source-filing policy (2026-09-15, item 2) ----------------------


def test_select_authoritative_fact_prefers_the_filing_whose_own_period_this_is():
    facts = [
        make_fact("rf_fy24_10k", None, "2025-02-01", "4762000000", accession="acc-fy2024-10k"),
        make_fact("rf_q1_10q", None, "2025-02-01", "4762000000", accession="acc-q1-10q"),
        make_fact("rf_q2_10q", None, "2025-02-01", "4762000000", accession="acc-q2-10q"),
    ]
    filing_period_ends = {
        "acc-fy2024-10k": "2025-02-01",  # this filing's OWN primary period is 2025-02-01
        "acc-q1-10q": "2025-05-03",      # reports 2025-02-01 only as a comparative
        "acc-q2-10q": "2025-08-02",      # reports 2025-02-01 only as a comparative
    }
    resolution = select_authoritative_fact(facts, filing_period_ends)
    assert resolution.selected.fact_id == "rf_fy24_10k"
    assert {f.fact_id for f in resolution.corroborating} == {"rf_q1_10q", "rf_q2_10q"}


def test_select_authoritative_fact_raises_when_no_filing_claims_primary_authority():
    facts = [
        make_fact("rf_q1_10q", None, "2025-02-01", "4762000000", accession="acc-q1-10q"),
        make_fact("rf_q2_10q", None, "2025-02-01", "4762000000", accession="acc-q2-10q"),
    ]
    filing_period_ends = {"acc-q1-10q": "2025-05-03", "acc-q2-10q": "2025-08-02"}
    with pytest.raises(SelectionError, match="none is from a filing whose own primary reporting period"):
        select_authoritative_fact(facts, filing_period_ends)


def test_select_authoritative_fact_raises_on_disagreement_rather_than_overwriting():
    facts = [
        make_fact("rf_fy24_10k", None, "2025-02-01", "4762000000", accession="acc-fy2024-10k"),
        make_fact("rf_q1_10q", None, "2025-02-01", "4700000000", accession="acc-q1-10q"),  # disagrees
    ]
    filing_period_ends = {"acc-fy2024-10k": "2025-02-01", "acc-q1-10q": "2025-05-03"}
    with pytest.raises(SelectionError, match="disagrees with corroborating fact"):
        select_authoritative_fact(facts, filing_period_ends)


def test_select_authoritative_fact_raises_when_two_filings_both_claim_authority():
    facts = [
        make_fact("rf_a", None, "2025-02-01", "4762000000", accession="acc-a"),
        make_fact("rf_b", None, "2025-02-01", "4762000000", accession="acc-b"),
    ]
    filing_period_ends = {"acc-a": "2025-02-01", "acc-b": "2025-02-01"}
    with pytest.raises(SelectionError, match="each claim this exact date as their own primary reporting period"):
        select_authoritative_fact(facts, filing_period_ends)


def test_derive_point_in_time_metric_resolves_cross_filing_ambiguity_via_authority_and_records_corroboration():
    facts = [
        make_fact("rf_fy24_10k", None, "2025-02-01", "4762000000", accession="acc-fy2024-10k"),
        make_fact("rf_q1_10q", None, "2025-02-01", "4762000000", accession="acc-q1-10q"),
        make_fact("rf_q1", None, "2025-05-03", "2887000000", accession="acc-q1-10q"),
        make_fact("rf_q2", None, "2025-08-02", "4341000000", accession="acc-q2-10q"),
        make_fact("rf_q3", None, "2025-11-01", "3822000000", accession="acc-q3-10q"),
        make_fact("rf_q4", None, "2026-01-31", "5488000000", accession="acc-fy2025-10k"),
    ]
    filing_period_ends = {
        "acc-fy2024-10k": "2025-02-01",
        "acc-q1-10q": "2025-05-03",
        "acc-q2-10q": "2025-08-02",
        "acc-q3-10q": "2025-11-01",
        "acc-fy2025-10k": "2026-01-31",
    }
    outcome = derive_point_in_time_metric("cash_and_equivalents_balance_sheet", facts, filing_period_ends)
    assert outcome.errors == []
    assert len(outcome.quarterly_facts) == 5

    opening_qf = next(qf for qf in outcome.quarterly_facts if qf.fiscal_year == 2024 and qf.fiscal_quarter == 4)
    links = [l for l in outcome.lineage_links if l.derived_fact_id == opening_qf.quarterly_fact_id]
    direct_links = [l for l in links if l.operation == "direct"]
    corroborating_links = [l for l in links if l.operation == "corroborating"]
    assert [l.input_fact_id for l in direct_links] == ["rf_fy24_10k"]
    assert {l.input_fact_id for l in corroborating_links} == {"rf_q1_10q"}


# --- persist_instant_facts (2026-09-15, item 5/6) ---------------------------------


def _insert_filing_and_raw_fact(conn, accession, fact_id, value, filed_at="2025-05-30"):
    conn.execute(
        "INSERT OR IGNORE INTO filings (accession_number, cik, company_name, form_type, filed_at, "
        "period_of_report, primary_document_url, ingestion_method) VALUES "
        "(?, '0000027419', 'Target Corporation', '10-Q', ?, '2025-05-03', 'https://example.invalid', 'manual_upload')",
        (accession, filed_at),
    )
    conn.execute(
        "INSERT OR IGNORE INTO raw_facts (fact_id, accession_number, taxonomy, tag, unit, start_date, "
        "end_date, value, scale, sign_as_reported, is_superseded, retrieved_at) VALUES "
        "(?, ?, 'us-gaap', 'TestConcept', 'USD', NULL, '2025-05-03', ?, 6, 1, 0, '2025-05-30T00:00:00Z')",
        (fact_id, accession, value),
    )


def _build_instant_outcome_with_corroboration():
    qf = make_quarterly_fact("cash_and_equivalents_balance_sheet", fiscal_quarter=1, basis="point_in_time")
    outcome = DerivationOutcome("cash_and_equivalents_balance_sheet")
    outcome.quarterly_facts.append(qf)
    outcome.lineage_links.append(LineageLink(qf.quarterly_fact_id, "rf_selected", "direct"))
    outcome.lineage_links.append(LineageLink(qf.quarterly_fact_id, "rf_corroborating", "corroborating"))
    return outcome, qf


def test_persist_instant_facts_writes_selected_and_corroborating_observations(db_conn):
    _insert_filing_and_raw_fact(db_conn, "acc-selected", "rf_selected", "2887000000")
    _insert_filing_and_raw_fact(db_conn, "acc-corroborating", "rf_corroborating", "2887000000")
    db_conn.commit()
    outcome, qf = _build_instant_outcome_with_corroboration()

    written = persist_instant_facts(db_conn, {"cash_and_equivalents_balance_sheet": outcome})

    assert written == {"cash_and_equivalents_balance_sheet": 1}
    row = db_conn.execute(
        "SELECT metric, as_of_date, selected_raw_fact_id, selection_status FROM instant_facts"
    ).fetchone()
    assert row == ("cash_and_equivalents_balance_sheet", "2025-05-03", "rf_selected", "corroborated")

    obs = db_conn.execute(
        "SELECT raw_fact_id, relationship, difference_from_selected FROM instant_fact_observations ORDER BY relationship"
    ).fetchall()
    assert obs == [
        ("rf_corroborating", "corroborating", 0),
        ("rf_selected", "selected", None),
    ]


def test_persist_instant_facts_is_idempotent_on_repeated_calls(db_conn):
    _insert_filing_and_raw_fact(db_conn, "acc-selected", "rf_selected", "2887000000")
    _insert_filing_and_raw_fact(db_conn, "acc-corroborating", "rf_corroborating", "2887000000")
    db_conn.commit()
    outcome, _ = _build_instant_outcome_with_corroboration()

    persist_instant_facts(db_conn, {"cash_and_equivalents_balance_sheet": outcome})
    persist_instant_facts(db_conn, {"cash_and_equivalents_balance_sheet": outcome})
    persist_instant_facts(db_conn, {"cash_and_equivalents_balance_sheet": outcome})

    assert db_conn.execute("SELECT COUNT(*) FROM instant_facts").fetchone()[0] == 1
    assert db_conn.execute("SELECT COUNT(*) FROM instant_fact_observations").fetchone()[0] == 2


def test_persist_instant_facts_rolls_back_entire_batch_on_failure(db_conn):
    _insert_filing_and_raw_fact(db_conn, "acc-selected", "rf_selected", "2887000000")
    _insert_filing_and_raw_fact(db_conn, "acc-corroborating", "rf_corroborating", "2887000000")
    db_conn.commit()
    good_outcome, _ = _build_instant_outcome_with_corroboration()

    bad_qf = make_quarterly_fact("cash_and_equivalents_rollforward", fiscal_quarter=1, basis="point_in_time")
    bad_outcome = DerivationOutcome("cash_and_equivalents_rollforward")
    bad_outcome.quarterly_facts.append(bad_qf)
    # No raw_facts row exists for "rf_missing" -- persist_instant_facts refuses
    # to persist an instant fact with no real source fact backing it.
    bad_outcome.lineage_links.append(LineageLink(bad_qf.quarterly_fact_id, "rf_missing", "direct"))

    with pytest.raises(ValueError, match="rf_missing"):
        persist_instant_facts(
            db_conn,
            {"cash_and_equivalents_balance_sheet": good_outcome, "cash_and_equivalents_rollforward": bad_outcome},
        )

    # Neither metric's row survived -- the successful insert was rolled back too.
    assert db_conn.execute("SELECT COUNT(*) FROM instant_facts").fetchone()[0] == 0
    assert db_conn.execute("SELECT COUNT(*) FROM instant_fact_observations").fetchone()[0] == 0
