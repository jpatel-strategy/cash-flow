"""Parsing and identity verification for the SEC submissions inventory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FilingRecord:
    accession_number: str
    cik: str
    company_name: str
    form_type: str
    filed_at: str
    period_of_report: str
    primary_document_url: str


def verify_entity_identity(submissions_json: dict, expected_name_substring: str) -> bool:
    """Confirm the submissions payload actually identifies the expected entity."""
    name = submissions_json.get("name", "")
    return expected_name_substring.upper() in name.upper()


def build_primary_document_url(cik: str, accession_number: str, primary_document: str) -> str:
    """Construct the canonical SEC Archives URL for a filing's primary document."""
    cik_int = str(int(cik))  # strip leading zeros, as SEC Archives paths expect
    accession_no_dashes = accession_number.replace("-", "")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{cik_int}/"
        f"{accession_no_dashes}/{primary_document}"
    )


def parse_recent_filings(submissions_json: dict, cik: str, company_name: str) -> list[FilingRecord]:
    """Parse the `filings.recent` block of a submissions JSON into FilingRecords.

    Does not filter by form type — callers select 10-K/10-Q as needed. Older
    filings living in `filings.files[*]` (paginated submission-history files)
    are not handled here; fetch those separately if the target fiscal year
    predates what `recent` covers.
    """
    recent = submissions_json.get("filings", {}).get("recent", {})
    accession_numbers = recent.get("accessionNumber", [])
    form_types = recent.get("form", [])
    filed_dates = recent.get("filingDate", [])
    period_dates = recent.get("reportDate", [])
    primary_documents = recent.get("primaryDocument", [])

    n = len(accession_numbers)
    records: list[FilingRecord] = []
    for i in range(n):
        accession_number = accession_numbers[i]
        primary_document = primary_documents[i] if i < len(primary_documents) else ""
        records.append(
            FilingRecord(
                accession_number=accession_number,
                cik=cik,
                company_name=company_name,
                form_type=form_types[i] if i < len(form_types) else "",
                filed_at=filed_dates[i] if i < len(filed_dates) else "",
                period_of_report=period_dates[i] if i < len(period_dates) else "",
                primary_document_url=build_primary_document_url(cik, accession_number, primary_document)
                if primary_document
                else "",
            )
        )
    return records


def filter_by_form_type(records: list[FilingRecord], form_types: tuple[str, ...]) -> list[FilingRecord]:
    return [r for r in records if r.form_type in form_types]


def filter_filed_by_cutoff(records: list[FilingRecord], cutoff_date: str) -> list[FilingRecord]:
    """Keep only filings whose filed_at date is on or before the information cutoff.

    Dates are compared as ISO strings (YYYY-MM-DD), which sort correctly.
    """
    return [r for r in records if r.filed_at and r.filed_at <= cutoff_date]
