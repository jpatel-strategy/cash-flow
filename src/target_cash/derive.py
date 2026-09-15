"""Derives quarterly_facts from raw_facts, for reviewed metrics only.

This is the raw-to-analytical boundary described throughout
docs/accounting_policies.md and docs/decisions.md: a metric is eligible
only when its `config/metrics.csv` row is `mapping_status == 'reviewed'`.
Every derivation runs through machinery built and tested in prior milestone
steps -- nothing here re-implements or bypasses it:

- `normalize.select_consolidated_fact` picks the one dimensionless
  candidate for a (concept, period), refusing ambiguity.
- `normalize.derive_q2/q3/q4` perform the YTD subtraction, gated by
  `reconcile.check_source_compatibility` (entity, concept, unit, scale,
  accounting basis, consolidated scope, dates, period adjacency and
  classification, filing version, sign convention).
- `reconcile.check_independent_quarter_validation` compares a YTD-derived
  quarter against a genuinely independent discrete-quarter fact when one
  exists, and is explicitly labeled "unavailable" when none does (always
  true for Q4, since Target never files a discrete fourth quarter).

FY2025 period boundaries are hardcoded here as plain data, not inferred --
inferring fiscal period boundaries from arbitrary dates is exactly the kind
of silent judgment call this project avoids. See docs/decisions.md's filing
matrix for where these dates come from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from target_cash.lineage import LineageLink
from target_cash.normalize import (
    NormalizationError,
    PeriodSpec,
    QuarterlyFact,
    RawFactCandidate,
    SelectionError,
    derive_q2,
    derive_q3,
    derive_q4,
    normalize_unit,
    select_consolidated_fact,
)
from target_cash.reconcile import (
    IndependentQuarterValidationResult,
    check_independent_quarter_validation,
)

ACCOUNTING_BASIS = "US-GAAP-FY2025-Workiva"  # uniform across all facts ingested so far; no restatement observed

# FY2025 period boundaries, from the filing matrix (docs/decisions.md).
Q1_DATES = ("2025-02-02", "2025-05-03")
Q2_DATES = ("2025-05-04", "2025-08-02")
Q3_DATES = ("2025-08-03", "2025-11-01")
Q4_DATES = ("2025-11-02", "2026-01-31")
YTD6_DATES = ("2025-02-02", "2025-08-02")
YTD9_DATES = ("2025-02-02", "2025-11-01")
ANNUAL_DATES = ("2025-02-02", "2026-01-31")

# Balance-sheet instant dates -> (fiscal_year, fiscal_quarter) they represent.
INSTANT_QUARTER_MAP: dict[str, tuple[int, int]] = {
    "2025-02-01": (2024, 4),  # FY2024 year-end = opening balance for FY2025
    "2025-05-03": (2025, 1),
    "2025-08-02": (2025, 2),
    "2025-11-01": (2025, 3),
    "2026-01-31": (2025, 4),
}

# compute_rounding_bound(num_directly_reported_components=1, num_ytd_derived_components=1) -- see config/model.yml
INDEPENDENT_QUARTER_VALIDATION_BOUND = Decimal("1.5")


@dataclass(frozen=True)
class RawFactRow:
    fact_id: str
    accession_number: str
    cik: str
    unit: str
    start_date: Optional[str]
    end_date: str
    dimensional_context: Optional[str]
    value: Decimal
    scale: int
    sign_as_reported: int
    is_superseded: bool
    concept: str  # 'taxonomy:tag'


@dataclass
class DerivationOutcome:
    metric: str
    quarterly_facts: list[QuarterlyFact] = field(default_factory=list)
    lineage_links: list[LineageLink] = field(default_factory=list)
    independent_validations: list[IndependentQuarterValidationResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def load_raw_facts(conn, tag: str) -> list[RawFactRow]:
    rows = conn.execute(
        """
        SELECT rf.fact_id, rf.accession_number, f.cik, rf.unit, rf.start_date, rf.end_date,
               rf.dimensional_context, rf.value, rf.scale, rf.sign_as_reported,
               rf.is_superseded, rf.taxonomy, rf.tag
        FROM raw_facts rf
        JOIN filings f ON f.accession_number = rf.accession_number
        WHERE rf.tag = ?
        """,
        (tag,),
    ).fetchall()
    return [
        RawFactRow(
            fact_id=r[0], accession_number=r[1], cik=r[2], unit=r[3], start_date=r[4], end_date=r[5],
            dimensional_context=r[6], value=Decimal(r[7]), scale=r[8], sign_as_reported=r[9],
            is_superseded=bool(r[10]), concept=f"{r[11]}:{r[12]}",
        )
        for r in rows
    ]


def _select(facts: list[RawFactRow], start_date: Optional[str], end_date: str) -> Optional[RawFactRow]:
    """select_consolidated_fact over the subset of facts matching this exact period. Propagates SelectionError."""
    matching = [f for f in facts if f.start_date == start_date and f.end_date == end_date]
    if not matching:
        return None
    candidates = [RawFactCandidate(f.fact_id, f.dimensional_context, f.value) for f in matching]
    selected = select_consolidated_fact(candidates)
    return next(f for f in matching if f.fact_id == selected.fact_id)


def _period_spec(fact: RawFactRow, fiscal_year: int, scope: str) -> PeriodSpec:
    return PeriodSpec(
        fiscal_year=fiscal_year,
        scope=scope,
        unit=fact.unit,
        accounting_basis=ACCOUNTING_BASIS,
        start_date=fact.start_date,
        end_date=fact.end_date,
        value=fact.value,
        cik=fact.cik,
        concept=fact.concept,
        scale=fact.scale,
        dimensional_context=fact.dimensional_context,
        accession_number=fact.accession_number,
        is_superseded=fact.is_superseded,
        sign_as_reported=fact.sign_as_reported,
    )


def _make_quarterly_fact(
    metric: str, fiscal_year: int, fiscal_quarter: int,
    period_start: Optional[str], period_end: str,
    value: Decimal, unit: str, basis: str,
) -> QuarterlyFact:
    return QuarterlyFact(
        metric=metric, fiscal_year=fiscal_year, fiscal_quarter=fiscal_quarter,
        period_start=period_start, period_end=period_end, days_in_period=None,
        value_original=value, original_unit=unit,
        value_normalized=normalize_unit(value, unit), normalized_unit="USD_millions",
        basis=basis,
    )


def derive_point_in_time_metric(metric: str, facts: list[RawFactRow]) -> DerivationOutcome:
    outcome = DerivationOutcome(metric)
    for instant, (fiscal_year, fiscal_quarter) in INSTANT_QUARTER_MAP.items():
        try:
            fact = _select(facts, None, instant)
        except SelectionError as exc:
            outcome.errors.append(f"{metric} @ {instant}: {exc}")
            continue
        if fact is None:
            outcome.errors.append(f"{metric}: no raw fact found for instant {instant}")
            continue

        qf = _make_quarterly_fact(metric, fiscal_year, fiscal_quarter, None, instant, fact.value, fact.unit, "point_in_time")
        outcome.quarterly_facts.append(qf)
        outcome.lineage_links.append(LineageLink(qf.quarterly_fact_id, fact.fact_id, "direct"))
    return outcome


def derive_flow_metric(metric: str, facts: list[RawFactRow]) -> DerivationOutcome:
    outcome = DerivationOutcome(metric)

    direct_q1 = _try_select(outcome, metric, facts, *Q1_DATES)
    direct_q2 = _try_select(outcome, metric, facts, *Q2_DATES)
    direct_q3 = _try_select(outcome, metric, facts, *Q3_DATES)
    ytd6 = _try_select(outcome, metric, facts, *YTD6_DATES)
    ytd9 = _try_select(outcome, metric, facts, *YTD9_DATES)
    annual = _try_select(outcome, metric, facts, *ANNUAL_DATES)

    if direct_q1 is None:
        outcome.errors.append(f"{metric}: no direct Q1 fact found; cannot proceed without a Q1 anchor.")
        return outcome
    q1_qf = _make_quarterly_fact(metric, 2025, 1, *Q1_DATES, direct_q1.value, direct_q1.unit, "direct_quarterly")
    outcome.quarterly_facts.append(q1_qf)
    outcome.lineage_links.append(LineageLink(q1_qf.quarterly_fact_id, direct_q1.fact_id, "direct"))

    _derive_quarter(
        outcome, metric, fiscal_quarter=2, dates=Q2_DATES,
        direct_fact=direct_q2, minuend=ytd6, minuend_scope="six_month_YTD",
        subtrahend=direct_q1, subtrahend_scope="Q1", derive_fn=derive_q2,
        derivation_label="six_month_YTD minus Q1",
    )
    _derive_quarter(
        outcome, metric, fiscal_quarter=3, dates=Q3_DATES,
        direct_fact=direct_q3, minuend=ytd9, minuend_scope="nine_month_YTD",
        subtrahend=ytd6, subtrahend_scope="six_month_YTD", derive_fn=derive_q3,
        derivation_label="nine_month_YTD minus six_month_YTD",
    )
    _derive_quarter(
        outcome, metric, fiscal_quarter=4, dates=Q4_DATES,
        direct_fact=None,  # Target never files a discrete Q4 statement
        minuend=annual, minuend_scope="annual",
        subtrahend=ytd9, subtrahend_scope="nine_month_YTD", derive_fn=derive_q4,
        derivation_label="annual minus nine_month_YTD",
    )
    return outcome


def _try_select(outcome: DerivationOutcome, metric: str, facts: list[RawFactRow], start_date: Optional[str], end_date: str) -> Optional[RawFactRow]:
    try:
        return _select(facts, start_date, end_date)
    except SelectionError as exc:
        outcome.errors.append(f"{metric} @ {start_date}..{end_date}: {exc}")
        return None


def persist_outcome(conn, outcome: DerivationOutcome) -> int:
    """Write a DerivationOutcome's quarterly_facts and lineage into the database.

    Idempotent per quarterly_fact_id (each QuarterlyFact gets a fresh id per
    Python-process run, so re-running this against an already-populated
    database intentionally raises on the primary-key collision from a
    *different* fact_id representing the same metric/period, rather than
    silently duplicating analytical rows -- callers should clear the prior
    run's rows for a metric before re-deriving it, not double-insert.)
    """
    inserted = 0
    with conn:
        for qf in outcome.quarterly_facts:
            conn.execute(
                """
                INSERT INTO quarterly_facts
                    (quarterly_fact_id, metric, fiscal_year, fiscal_quarter, period_start, period_end,
                     days_in_period, value_original, original_unit, value_normalized, normalized_unit,
                     basis, as_of_date, mapping_version, is_current_view)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    qf.quarterly_fact_id, qf.metric, qf.fiscal_year, qf.fiscal_quarter,
                    qf.period_start, qf.period_end, qf.days_in_period,
                    str(qf.value_original), qf.original_unit, str(qf.value_normalized), qf.normalized_unit,
                    qf.basis, _today_iso(), "v0-pending-verification",
                ),
            )
            inserted += 1
        for link in outcome.lineage_links:
            conn.execute(
                "INSERT INTO lineage (lineage_id, derived_fact_id, input_fact_id, operation) VALUES (?, ?, ?, ?)",
                (f"lin_{link.derived_fact_id}_{link.input_fact_id}", link.derived_fact_id, link.input_fact_id, link.operation),
            )
    return inserted


def _today_iso() -> str:
    import time

    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _derive_quarter(
    outcome: DerivationOutcome, metric: str, fiscal_quarter: int, dates: tuple[str, str],
    direct_fact: Optional[RawFactRow],
    minuend: Optional[RawFactRow], minuend_scope: str,
    subtrahend: Optional[RawFactRow], subtrahend_scope: str,
    derive_fn, derivation_label: str,
) -> None:
    """Prefer a direct fact when one exists; always also attempt the YTD-subtraction
    derivation so it can be cross-checked against the direct fact (or, when no direct
    fact exists, so the derived value becomes the analytical quarterly_fact itself).
    """
    derived_value = None
    if minuend is not None and subtrahend is not None:
        try:
            derived_value = derive_fn(
                _period_spec(minuend, 2025, minuend_scope),
                _period_spec(subtrahend, 2025, subtrahend_scope),
            )
        except NormalizationError as exc:
            outcome.errors.append(f"{metric}: Q{fiscal_quarter} derivation ({derivation_label}) failed: {exc}")

    if direct_fact is not None:
        qf = _make_quarterly_fact(metric, 2025, fiscal_quarter, *dates, direct_fact.value, direct_fact.unit, "direct_quarterly")
        outcome.quarterly_facts.append(qf)
        outcome.lineage_links.append(LineageLink(qf.quarterly_fact_id, direct_fact.fact_id, "direct"))

        if derived_value is not None:
            outcome.independent_validations.append(
                check_independent_quarter_validation(
                    metric=metric, fiscal_year=2025, fiscal_quarter=fiscal_quarter,
                    derived_value=normalize_unit(derived_value, direct_fact.unit), derived_source=derivation_label,
                    independent_value=normalize_unit(direct_fact.value, direct_fact.unit), independent_source=direct_fact.fact_id,
                    tolerance_absolute=INDEPENDENT_QUARTER_VALIDATION_BOUND,
                    derived_input_fact_ids=frozenset({minuend.fact_id, subtrahend.fact_id}),
                    independent_fact_ids=frozenset({direct_fact.fact_id}),
                )
            )
        return

    if derived_value is not None:
        qf = _make_quarterly_fact(metric, 2025, fiscal_quarter, *dates, derived_value, minuend.unit, "derived_ytd_subtraction")
        outcome.quarterly_facts.append(qf)
        outcome.lineage_links.append(LineageLink(qf.quarterly_fact_id, minuend.fact_id, derivation_label))
        outcome.lineage_links.append(LineageLink(qf.quarterly_fact_id, subtrahend.fact_id, derivation_label))
        outcome.independent_validations.append(
            check_independent_quarter_validation(
                metric=metric, fiscal_year=2025, fiscal_quarter=fiscal_quarter,
                derived_value=normalize_unit(derived_value, minuend.unit), derived_source=derivation_label,
                independent_value=None, independent_source="no discrete fact filed for this quarter",
                tolerance_absolute=INDEPENDENT_QUARTER_VALIDATION_BOUND,
            )
        )
    else:
        outcome.errors.append(f"{metric}: Q{fiscal_quarter} has neither a direct fact nor the inputs to derive one.")


def derive_reviewed_metrics(conn, metrics_rows: list[dict]) -> dict[str, DerivationOutcome]:
    """Derive every metric marked `reviewed` in config/metrics.csv.

    `metrics_rows` is the parsed CSV (list of row dicts with at least
    `metric`, `category`, `candidate_xbrl_tag`, `mapping_status`). Returns
    one DerivationOutcome per reviewed metric; callers decide whether/how to
    persist each (see `persist_outcome`) after inspecting `errors` and
    `independent_validations`.
    """
    outcomes: dict[str, DerivationOutcome] = {}
    for row in metrics_rows:
        if row.get("mapping_status") != "reviewed":
            continue
        metric = row["metric"]
        tag = row["candidate_xbrl_tag"]
        facts = load_raw_facts(conn, tag)
        if row.get("category") == "point_in_time":
            outcomes[metric] = derive_point_in_time_metric(metric, facts)
        else:
            outcomes[metric] = derive_flow_metric(metric, facts)
    return outcomes
