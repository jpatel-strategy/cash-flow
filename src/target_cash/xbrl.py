"""Helpers for inspecting SEC XBRL Company Facts JSON.

Company Facts is treated only as a *candidate*-fact source (per the governing
roadmap): every candidate here still needs its definition, period, unit,
consolidated scope, dimensional context, sign, and restatement status checked
against the actual filing statement before it is accepted into `raw_facts`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterable, Optional


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


# --- Inline XBRL extraction from a primary filing document -------------------
#
# Company Facts is a convenient candidate-fact index, but it cannot show
# which XBRL context backs a specific rendered statement line, nor whether
# that line carries a dimensional (segment/member) scope. Resolving that
# requires reading the actual <ix:nonFraction> markup and its <xbrli:context>
# definitions in the primary document itself — see docs/decisions.md,
# 2026-09-15 "Real FY2025 10-K obtained and verified" entry, where exactly
# this distinguished two same-valued but differently-scoped cash concepts.


@dataclass(frozen=True)
class XbrlContext:
    context_id: str
    entity_cik: Optional[str]
    start_date: Optional[str]  # None for an instant context
    end_date: Optional[str]  # the instant date, or the duration's end date
    dimensional_context: Optional[str]  # None = consolidated; else a raw description of the segment/member found


@dataclass(frozen=True)
class InlineXbrlFact:
    concept: str  # e.g. 'us-gaap:CashCashEquivalentsAndShortTermInvestments'
    context_id: str
    unit_ref: str
    scale: Optional[int]
    sign_as_reported: int  # +1 unless the element carried sign="-"
    raw_text: str
    element_id: str
    context: XbrlContext

    @property
    def value(self) -> Decimal:
        """The true value after applying `scale` and `sign_as_reported`.

        E.g. raw_text="5,488", scale=6 -> Decimal("5488") * 10**6.
        """
        magnitude = Decimal(self.raw_text.replace(",", "").strip() or "0")
        scaled = magnitude * (Decimal(10) ** self.scale) if self.scale is not None else magnitude
        return scaled * (Decimal(-1) if self.sign_as_reported < 0 else Decimal(1))


_ATTR_PATTERN = re.compile(r'(\w[\w:.-]*)="([^"]*)"')


def _parse_attrs(tag_open: str) -> dict[str, str]:
    return dict(_ATTR_PATTERN.findall(tag_open))


def parse_xbrl_contexts(html_content: str) -> dict[str, XbrlContext]:
    """Parse every <xbrli:context id="..."> block into an XbrlContext.

    Dimensional scope is detected by the presence of an <xbrli:segment>
    element inside the context; the segment's raw inner text is kept as a
    human-readable marker rather than fully modeling the dimension — callers
    only need to know "consolidated vs. not" to gate a derivation, per
    check_source_compatibility's consolidated_scope dimension.
    """
    contexts: dict[str, XbrlContext] = {}
    for match in re.finditer(r'<xbrli:context id="([^"]+)">(.*?)</xbrli:context>', html_content, re.S):
        context_id, block = match.group(1), match.group(2)

        entity_match = re.search(r"<xbrli:identifier[^>]*>([^<]*)</xbrli:identifier>", block)
        entity_cik = entity_match.group(1).strip() if entity_match else None

        segment_match = re.search(r"<xbrli:segment>(.*?)</xbrli:segment>", block, re.S)
        dimensional_context = None
        if segment_match:
            member_match = re.search(r">([^<>]*Member)<", segment_match.group(1))
            dimensional_context = member_match.group(1) if member_match else "segment_present"

        instant_match = re.search(r"<xbrli:instant>([^<]*)</xbrli:instant>", block)
        if instant_match:
            start_date, end_date = None, instant_match.group(1).strip()
        else:
            start_match = re.search(r"<xbrli:startDate>([^<]*)</xbrli:startDate>", block)
            end_match = re.search(r"<xbrli:endDate>([^<]*)</xbrli:endDate>", block)
            start_date = start_match.group(1).strip() if start_match else None
            end_date = end_match.group(1).strip() if end_match else None

        contexts[context_id] = XbrlContext(
            context_id=context_id,
            entity_cik=entity_cik,
            start_date=start_date,
            end_date=end_date,
            dimensional_context=dimensional_context,
        )
    return contexts


def parse_inline_xbrl_facts(html_content: str, concepts: Iterable[str]) -> list[InlineXbrlFact]:
    """Extract every <ix:nonFraction> fact for the given concepts, with its
    context resolved.

    Matches concepts exactly as given (e.g. 'us-gaap:CashCashEquivalentsAnd
    ShortTermInvestments') — no fuzzy or substring matching, since selecting
    a fact by an approximately-matching tag name is exactly what this
    project's standing rule prohibits. Attribute order on the source
    <ix:nonFraction> tag varies across the document (observed both
    name-before-contextRef and contextRef-before-name), so attributes are
    parsed generically rather than assumed to appear in one order.
    """
    contexts = parse_xbrl_contexts(html_content)
    wanted = set(concepts)
    facts: list[InlineXbrlFact] = []

    for match in re.finditer(r"<ix:nonFraction\s+([^>]*?)>([^<]*)</ix:nonFraction>", html_content):
        attrs_text, raw_text = match.group(1), match.group(2)
        attrs = _parse_attrs(attrs_text)
        concept = attrs.get("name", "")
        if concept not in wanted:
            continue
        context_id = attrs.get("contextRef", "")
        context = contexts.get(context_id)
        if context is None:
            continue  # a fact whose context we couldn't resolve is not usable; skip rather than guess
        scale = int(attrs["scale"]) if "scale" in attrs else None
        sign = -1 if attrs.get("sign") == "-" else 1
        facts.append(
            InlineXbrlFact(
                concept=concept,
                context_id=context_id,
                unit_ref=attrs.get("unitRef", ""),
                scale=scale,
                sign_as_reported=sign,
                raw_text=raw_text.strip().replace("&#8212;", "0").replace("—", "0"),  # em-dash marks a reported zero
                element_id=attrs.get("id", ""),
                context=context,
            )
        )
    return facts
