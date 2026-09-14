"""Helpers for inspecting SEC XBRL Company Facts JSON.

Company Facts is treated only as a *candidate*-fact source (per the governing
roadmap): every candidate here still needs its definition, period, unit,
consolidated scope, dimensional context, sign, and restatement status checked
against the actual filing statement before it is accepted into `raw_facts`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class CandidateFact:
    """One reported value for a taxonomy/tag/unit, as found in Company Facts."""

    taxonomy: str
    tag: str
    unit: str
    start_date: Optional[str]  # None for point-in-time (instant) facts
    end_date: str
    value: Any  # kept as the raw JSON value; caller parses with Decimal
    accession_number: str
    form_type: str
    filed_at: str
    fiscal_year: Optional[int]
    fiscal_period: Optional[str]  # e.g. 'Q1', 'FY'
    frame: Optional[str]


def load_candidate_facts(company_facts_json: dict, taxonomy: str, tag: str) -> list[CandidateFact]:
    """Return every reported value for one taxonomy/tag, across every unit.

    Does not filter by dimensional context or pick a "best" value — that
    judgment belongs to a human reviewing the actual filing statement, per
    the roadmap's explicit prohibition on substituting similarly-named tags
    without review.
    """
    facts_by_taxonomy = company_facts_json.get("facts", {})
    tag_block = facts_by_taxonomy.get(taxonomy, {}).get(tag)
    if tag_block is None:
        return []

    candidates: list[CandidateFact] = []
    units = tag_block.get("units", {})
    for unit, entries in units.items():
        for entry in entries:
            candidates.append(
                CandidateFact(
                    taxonomy=taxonomy,
                    tag=tag,
                    unit=unit,
                    start_date=entry.get("start"),
                    end_date=entry["end"],
                    value=entry["val"],
                    accession_number=entry.get("accn", ""),
                    form_type=entry.get("form", ""),
                    filed_at=entry.get("filed", ""),
                    fiscal_year=entry.get("fy"),
                    fiscal_period=entry.get("fp"),
                    frame=entry.get("frame"),
                )
            )
    return candidates


def filter_by_form(candidates: list[CandidateFact], form_types: tuple[str, ...]) -> list[CandidateFact]:
    return [c for c in candidates if c.form_type in form_types]


def filter_by_accession(candidates: list[CandidateFact], accession_number: str) -> list[CandidateFact]:
    return [c for c in candidates if c.accession_number == accession_number]


def verify_entity_identity(company_facts_json: dict, expected_name_substring: str) -> bool:
    """Confirm the Company Facts payload actually identifies the expected entity.

    This is the check that turns a candidate CIK into a verified one — see
    docs/decisions.md.
    """
    name = company_facts_json.get("entityName", "")
    return expected_name_substring.upper() in name.upper()
