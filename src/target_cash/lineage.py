"""Lineage: linking every derived quarterly fact back to its raw inputs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LineageLink:
    derived_fact_id: str
    input_fact_id: str
    operation: str  # e.g. 'direct', 'ytd6_minus_q1', 'unit_conversion', 'point_in_time'


def link_direct(derived_fact_id: str, input_fact_id: str) -> LineageLink:
    return LineageLink(derived_fact_id, input_fact_id, operation="direct")


def link_ytd_subtraction(derived_fact_id: str, minuend_fact_id: str, subtrahend_fact_id: str, operation: str) -> list[LineageLink]:
    """A YTD-minus-YTD derivation depends on both input facts."""
    return [
        LineageLink(derived_fact_id, minuend_fact_id, operation=operation),
        LineageLink(derived_fact_id, subtrahend_fact_id, operation=operation),
    ]


def find_facts_missing_lineage(derived_fact_ids: list[str], links: list[LineageLink]) -> list[str]:
    """Return every derived fact id with zero lineage links.

    A non-empty result means a derived value has broken provenance and the
    validation gate must fail.
    """
    linked_ids = {link.derived_fact_id for link in links}
    return [fact_id for fact_id in derived_fact_ids if fact_id not in linked_ids]
