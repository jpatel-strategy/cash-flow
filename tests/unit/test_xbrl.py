import json
from pathlib import Path

from target_cash.xbrl import load_candidate_facts, verify_entity_identity

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def load_fixture():
    return json.loads((FIXTURES / "synthetic_companyfacts.json").read_text())


def test_verify_entity_identity_matches():
    payload = load_fixture()
    assert verify_entity_identity(payload, "SYNTHETIC TEST CORP")


def test_verify_entity_identity_rejects_wrong_name():
    payload = load_fixture()
    assert not verify_entity_identity(payload, "TARGET CORP")


def test_load_candidate_facts_returns_all_units_and_entries():
    payload = load_fixture()
    candidates = load_candidate_facts(payload, "us-gaap", "NetCashProvidedByUsedInOperatingActivities")
    assert len(candidates) == 4
    end_dates = {c.end_date for c in candidates}
    assert end_dates == {"2019-03-31", "2019-06-30", "2019-09-30", "2019-12-31"}


def test_load_candidate_facts_missing_tag_returns_empty():
    payload = load_fixture()
    candidates = load_candidate_facts(payload, "us-gaap", "SomeTagThatDoesNotExist")
    assert candidates == []


def test_load_candidate_facts_preserves_point_in_time_start_date_none():
    payload = load_fixture()
    candidates = load_candidate_facts(payload, "us-gaap", "CashAndCashEquivalentsAtCarryingValue")
    assert all(c.start_date is None for c in candidates)
