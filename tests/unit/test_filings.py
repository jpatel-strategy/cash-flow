import json
from pathlib import Path

from target_cash.filings import (
    build_primary_document_url,
    filter_by_form_type,
    filter_filed_by_cutoff,
    parse_recent_filings,
    verify_entity_identity,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def load_fixture():
    return json.loads((FIXTURES / "synthetic_submissions.json").read_text())


def test_verify_entity_identity_matches():
    payload = load_fixture()
    assert verify_entity_identity(payload, "SYNTHETIC TEST CORP")


def test_verify_entity_identity_rejects_wrong_name():
    payload = load_fixture()
    assert not verify_entity_identity(payload, "TARGET CORP")


def test_build_primary_document_url_strips_leading_zeros_and_dashes():
    url = build_primary_document_url("0000009999999", "0000000000-24-000004", "synth-10k-2024.htm")
    assert url == "https://www.sec.gov/Archives/edgar/data/9999999/000000000024000004/synth-10k-2024.htm"


def test_parse_recent_filings_returns_all_rows():
    payload = load_fixture()
    records = parse_recent_filings(payload, cik="9999999", company_name="SYNTHETIC TEST CORP")
    assert len(records) == 3
    assert records[0].form_type == "10-K"
    assert records[0].period_of_report == "2024-02-03"


def test_filter_by_form_type():
    payload = load_fixture()
    records = parse_recent_filings(payload, cik="9999999", company_name="SYNTHETIC TEST CORP")
    tens_q = filter_by_form_type(records, ("10-Q",))
    assert len(tens_q) == 2
    assert all(r.form_type == "10-Q" for r in tens_q)


def test_filter_filed_by_cutoff_excludes_later_filings():
    payload = load_fixture()
    records = parse_recent_filings(payload, cik="9999999", company_name="SYNTHETIC TEST CORP")
    cutoff_records = filter_filed_by_cutoff(records, "2023-12-31")
    filed_dates = {r.filed_at for r in cutoff_records}
    assert "2024-03-15" not in filed_dates
    assert "2023-11-15" in filed_dates
