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
    ArithmeticInvariantResult,
    CompatibilityCheckResult,
    IndependentQuarterValidationResult,
    ReconciliationResult,
    check_arithmetic_invariant,
    check_independent_quarter_validation,
    check_source_compatibility,
    check_ytd_consistency,
    compute_rounding_bound,
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
    compatibility_results: list[CompatibilityCheckResult] = field(default_factory=list)
    arithmetic_invariant_results: list[ArithmeticInvariantResult] = field(default_factory=list)
    ytd_consistency_results: list[ReconciliationResult] = field(default_factory=list)
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


@dataclass(frozen=True)
class AuthoritativeSelection:
    selected: RawFactRow
    corroborating: tuple[RawFactRow, ...]


def select_authoritative_fact(
    facts: list[RawFactRow],
    filing_period_ends: dict[str, str],
) -> AuthoritativeSelection:
    """Resolve more than one consolidated candidate for one exact period using
    the authoritative-source-filing policy (docs/decisions.md, 2026-09-15,
    "Authoritative-source policy"): the candidate from the filing whose own
    primary reporting period (`filings.period_of_report`) equals this exact
    period is authoritative. Every other agreeing candidate is a
    corroborating observation, never a second selection. `facts` must
    already be narrowed to one concept, one exact period, and consolidated
    (non-dimensional, non-superseded) candidates only.

    Never silently picks: if no filing claims this period as its own
    primary period, if more than one does, or if the authoritative fact
    disagrees with any corroborating one, this raises for human review.
    """
    primary = [f for f in facts if filing_period_ends.get(f.accession_number) == f.end_date]
    if len(primary) == 0:
        raise SelectionError(
            f"Ambiguous: {len(facts)} consolidated candidate facts found "
            f"({[f.fact_id for f in facts]}), but none is from a filing whose own primary "
            "reporting period is this exact date -- cannot assign authority without human "
            "review, even though the values may agree."
        )
    if len(primary) > 1:
        raise SelectionError(
            f"Ambiguous: {len(primary)} filings each claim this exact date as their own "
            f"primary reporting period ({[f.fact_id for f in primary]}) -- this should not "
            "happen under the SEC filing calendar and needs human review."
        )
    selected = primary[0]
    corroborating = tuple(f for f in facts if f.fact_id != selected.fact_id)
    disagreeing = [f for f in corroborating if f.value != selected.value]
    if disagreeing:
        raise SelectionError(
            f"Authoritative fact {selected.fact_id} (value {selected.value}) disagrees with "
            f"corroborating fact(s) {[(f.fact_id, str(f.value)) for f in disagreeing]} -- "
            "flagged for human review, not silently overwritten either way."
        )
    return AuthoritativeSelection(selected=selected, corroborating=corroborating)


def _select(
    facts: list[RawFactRow], start_date: Optional[str], end_date: str,
    filing_period_ends: Optional[dict[str, str]] = None,
) -> Optional[RawFactRow]:
    """select_consolidated_fact over the subset of facts matching this exact period,
    excluding any superseded (restated) fact. Propagates SelectionError.

    When `filing_period_ends` is given and more than one consolidated candidate
    exists, resolves via select_authoritative_fact instead of raising outright
    -- this is currently wired only for point-in-time metrics (see
    derive_point_in_time_metric); flow metrics still raise on ambiguity,
    pending a reliable statement-location detection method (docs/decisions.md,
    2026-09-15 net-income entry).
    """
    matching = [f for f in facts if f.start_date == start_date and f.end_date == end_date and not f.is_superseded]
    if not matching:
        return None
    consolidated = [f for f in matching if f.dimensional_context is None]
    if filing_period_ends is not None and len(consolidated) > 1:
        return select_authoritative_fact(consolidated, filing_period_ends).selected
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


def derive_point_in_time_metric(
    metric: str, facts: list[RawFactRow], filing_period_ends: dict[str, str],
) -> DerivationOutcome:
    """`filing_period_ends` maps accession_number -> that filing's own primary
    reporting period end date (filings.period_of_report), and drives the
    authoritative-source-filing policy (docs/decisions.md, 2026-09-15) when
    more than one filing independently reports the same instant.
    """
    outcome = DerivationOutcome(metric)
    for instant, (fiscal_year, fiscal_quarter) in INSTANT_QUARTER_MAP.items():
        try:
            fact = _select(facts, None, instant, filing_period_ends=filing_period_ends)
        except SelectionError as exc:
            outcome.errors.append(f"{metric} @ {instant}: {exc}")
            continue
        if fact is None:
            outcome.errors.append(f"{metric}: no raw fact found for instant {instant}")
            continue

        qf = _make_quarterly_fact(metric, fiscal_year, fiscal_quarter, None, instant, fact.value, fact.unit, "point_in_time")
        outcome.quarterly_facts.append(qf)
        outcome.lineage_links.append(LineageLink(qf.quarterly_fact_id, fact.fact_id, "direct"))

        # Corroborating observations: other filings independently reporting the same
        # instant, agreeing with the authoritative fact (select_authoritative_fact
        # already raised, rather than reaching here, had any of them disagreed).
        # Recorded as lineage so the corroboration is preserved, not silently dropped.
        corroborating = [
            f for f in facts
            if f.start_date is None and f.end_date == instant and not f.is_superseded
            and f.dimensional_context is None and f.fact_id != fact.fact_id
        ]
        for corroborator in corroborating:
            outcome.lineage_links.append(LineageLink(qf.quarterly_fact_id, corroborator.fact_id, "corroborating"))
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

    # YTD consistency: only meaningful when EVERY input is itself a directly-filed
    # fact (never a derived one) -- comparing a directly-reported YTD figure
    # against the sum of directly-reported discrete quarters. Deliberately never
    # attempted at the annual level: annual == Q1+Q2+Q3+Q4 is tautological once
    # Q4 is defined as annual-minus-nine_month_YTD (see reconcile.py docstring).
    # Every value compared here must be normalized to the same unit
    # (USD_millions) before comparison, same as independent_quarter_validation
    # already does -- raw_facts.value is unscaled USD, and compute_rounding_bound
    # returns its bound in USD_millions, so comparing raw values against it
    # would silently compare mismatched units.
    if direct_q2 is not None:
        outcome.ytd_consistency_results.append(
            check_ytd_consistency(
                metric=metric, fiscal_year=2025, ytd_label="six_month_YTD",
                directly_reported_ytd=(normalize_unit(ytd6.value, ytd6.unit) if ytd6 is not None else None),
                sum_of_directly_reported_quarters=(
                    normalize_unit(direct_q1.value, direct_q1.unit) + normalize_unit(direct_q2.value, direct_q2.unit)
                ),
                tolerance_absolute=compute_rounding_bound(num_directly_reported_components=3, num_ytd_derived_components=0),
                ytd_fact_ids=frozenset({ytd6.fact_id}) if ytd6 is not None else frozenset(),
                quarter_fact_ids=frozenset({direct_q1.fact_id, direct_q2.fact_id}),
            )
        )
    if direct_q2 is not None and direct_q3 is not None:
        outcome.ytd_consistency_results.append(
            check_ytd_consistency(
                metric=metric, fiscal_year=2025, ytd_label="nine_month_YTD",
                directly_reported_ytd=(normalize_unit(ytd9.value, ytd9.unit) if ytd9 is not None else None),
                sum_of_directly_reported_quarters=(
                    normalize_unit(direct_q1.value, direct_q1.unit)
                    + normalize_unit(direct_q2.value, direct_q2.unit)
                    + normalize_unit(direct_q3.value, direct_q3.unit)
                ),
                tolerance_absolute=compute_rounding_bound(num_directly_reported_components=4, num_ytd_derived_components=0),
                ytd_fact_ids=frozenset({ytd9.fact_id}) if ytd9 is not None else frozenset(),
                quarter_fact_ids=frozenset({direct_q1.fact_id, direct_q2.fact_id, direct_q3.fact_id}),
            )
        )
    return outcome


def _try_select(outcome: DerivationOutcome, metric: str, facts: list[RawFactRow], start_date: Optional[str], end_date: str) -> Optional[RawFactRow]:
    try:
        return _select(facts, start_date, end_date)
    except SelectionError as exc:
        outcome.errors.append(f"{metric} @ {start_date}..{end_date}: {exc}")
        return None


def persist_all_outcomes(conn, outcomes: dict[str, DerivationOutcome]) -> dict[str, int]:
    """Atomically clear and rewrite quarterly_facts/lineage for every metric in
    `outcomes`, in ONE transaction covering the whole batch.

    Derivation defaults to dry-run everywhere in this module and in the CLI;
    this is the only function that writes analytical rows, and only when a
    caller explicitly invokes it (e.g. `normalize --persist-derived`). If
    anything raises partway through, the entire transaction rolls back --
    no metric is left partially written, and no earlier metric's successful
    write in this same call survives a later one's failure. Never touches
    `raw_facts` or `filings`. Idempotent: re-running with the same inputs
    clears each metric's prior rows first, so row counts never accumulate.
    """
    written: dict[str, int] = {}
    with conn:
        for metric, outcome in outcomes.items():
            conn.execute(
                "DELETE FROM lineage WHERE derived_fact_id IN "
                "(SELECT quarterly_fact_id FROM quarterly_facts WHERE metric = ?)",
                (metric,),
            )
            conn.execute("DELETE FROM quarterly_facts WHERE metric = ?", (metric,))
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
            for link in outcome.lineage_links:
                conn.execute(
                    "INSERT INTO lineage (lineage_id, derived_fact_id, input_fact_id, operation) VALUES (?, ?, ?, ?)",
                    (f"lin_{link.derived_fact_id}_{link.input_fact_id}", link.derived_fact_id, link.input_fact_id, link.operation),
                )
            written[metric] = len(outcome.quarterly_facts)
    return written


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
        check_name = f"{metric}:Q{fiscal_quarter}:{derivation_label}"
        # Recompute the same source-compatibility precondition derive_fn enforces
        # internally (it raises rather than returning a result object), purely to
        # capture a real CompatibilityCheckResult for the validation report --
        # this is the same deterministic check, not a second source of truth.
        outcome.compatibility_results.append(
            check_source_compatibility(
                f"source_compatibility:{check_name}",
                cik_a=minuend.cik, cik_b=subtrahend.cik,
                fiscal_year_a=2025, fiscal_year_b=2025,
                concept_a=minuend.concept, concept_b=subtrahend.concept,
                unit_a=minuend.unit, unit_b=subtrahend.unit,
                scale_a=minuend.scale, scale_b=subtrahend.scale,
                accounting_basis_a=ACCOUNTING_BASIS, accounting_basis_b=ACCOUNTING_BASIS,
                dimensional_context_a=minuend.dimensional_context, dimensional_context_b=subtrahend.dimensional_context,
                start_date_a=minuend.start_date, start_date_b=subtrahend.start_date,
                end_date_a=minuend.end_date, end_date_b=subtrahend.end_date,
                scope_a=minuend_scope, scope_b=subtrahend_scope,
                accession_a=minuend.accession_number, accession_b=subtrahend.accession_number,
                is_superseded_a=minuend.is_superseded, is_superseded_b=subtrahend.is_superseded,
                sign_as_reported_a=minuend.sign_as_reported, sign_as_reported_b=subtrahend.sign_as_reported,
            )
        )
        try:
            derived_value = derive_fn(
                _period_spec(minuend, 2025, minuend_scope),
                _period_spec(subtrahend, 2025, subtrahend_scope),
            )
        except NormalizationError as exc:
            outcome.errors.append(f"{metric}: Q{fiscal_quarter} derivation ({derivation_label}) failed: {exc}")
        else:
            # Code-correctness check only (see reconcile.check_arithmetic_invariant):
            # holds by construction whenever derive_fn's own subtraction is correct.
            outcome.arithmetic_invariant_results.append(
                check_arithmetic_invariant(
                    f"arithmetic_invariant:{check_name}",
                    stored_value=derived_value,
                    recomputed_value=(minuend.value - subtrahend.value),
                )
            )

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


def load_filing_period_ends(conn) -> dict[str, str]:
    """accession_number -> that filing's own primary reporting period end date
    (filings.period_of_report), used by the authoritative-source-filing policy.
    """
    return {
        r[0]: r[1]
        for r in conn.execute("SELECT accession_number, period_of_report FROM filings").fetchall()
    }


def derive_reviewed_metrics(conn, metrics_rows: list[dict]) -> dict[str, DerivationOutcome]:
    """Derive every metric marked `reviewed` in config/metrics.csv.

    `metrics_rows` is the parsed CSV (list of row dicts with at least
    `metric`, `category`, `candidate_xbrl_tag`, `mapping_status`). Returns
    one DerivationOutcome per reviewed metric; callers decide whether/how to
    persist them (see `persist_all_outcomes`) after inspecting `errors` and
    `independent_validations`.
    """
    filing_period_ends = load_filing_period_ends(conn)
    outcomes: dict[str, DerivationOutcome] = {}
    for row in metrics_rows:
        if row.get("mapping_status") != "reviewed":
            continue
        metric = row["metric"]
        tag = row["candidate_xbrl_tag"]
        facts = load_raw_facts(conn, tag)
        if row.get("category") == "point_in_time":
            outcomes[metric] = derive_point_in_time_metric(metric, facts, filing_period_ends)
        else:
            outcomes[metric] = derive_flow_metric(metric, facts)
    return outcomes
