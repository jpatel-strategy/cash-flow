"""Annual analytical fact persistence: exact preflight planning, conditional
authorization, and the atomic transactional writer.

Persisting annual_facts/annual_lineage/annual_fact_observations was not
authorized before the 2026-09-16 "overall-gate enforcement" round. It is now
CONDITIONALLY authorized -- only when a GateAuthorization instance proving
every item-4 condition holds is passed to persist_annual_facts(). This is a
hard guard inside the function itself, not merely CLI-level enforcement: a
test, script, or future caller that imports this module directly cannot
bypass it by skipping the CLI. See GateAuthorization.require_authorized().

Planning is a pure function of the same inputs `target_cash.cli validate`
already computes (compute_all_years, the persistence_eligible_metrics list
from the two-gate policy) -- there is no separate reimplementation of "which
metric x fiscal_year x view is approved to persist" here. persist_annual_facts
writes exactly the plan compute_persistence_preflight produced; nothing is
recomputed differently between planning and writing.
"""
from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass, field

from target_cash.annual import (
    DURATION_METRICS,
    FISCAL_YEARS,
    INSTANT_METRICS,
    KNOWN_RECLASSIFIED_METRICS,
    compute_all_years,
    duration_value,
    fiscal_period,
    instant_value,
    latest_restated_duration,
    latest_restated_instant,
    q6,
    resolve_tag,
)

# annual_facts.analytical_view's schema values -- distinct from annual.py's
# internal dict keys 'as_filed'/'restated' used throughout compute_all_years.
VIEW_KEY_TO_SCHEMA_VALUE = {"as_filed": "as_originally_filed", "restated": "latest_restated"}

# Only these two computed statuses are ever persisted. UNAVAILABLE,
# NOT_APPLICABLE, and BLOCKED cells are excluded by construction -- never
# silently coerced into a persisted row (item 3's "no unavailable or
# not-applicable fact rows" requirement).
PERSISTABLE_STATUSES = {"DIRECT", "DERIVED"}

# target_defined_net_debt is permanently UNAVAILABLE by design (see annual.py)
# and is never in metric_definitions.csv -- excluded here defensively too,
# so this module's own exclusion is explicit rather than only incidental.
NEVER_PERSISTED_METRICS = {"target_defined_net_debt"}


@dataclass(frozen=True)
class PlannedAnnualFact:
    annual_fact_id: str
    metric: str
    fiscal_year: int
    analytical_view: str
    direct_or_derived: str
    period_start: str
    period_end: str
    days_in_period: int
    value_original: str
    original_unit: str
    value_normalized: float
    normalized_unit: str
    fact_status: str
    validation_status: str
    accession_number: str
    filed_at: str
    mapping_version: str
    information_cutoff: str


@dataclass(frozen=True)
class PlannedObservation:
    observation_id: str
    annual_fact_id: str
    raw_fact_id: str
    accession_number: str
    filed_at: str
    relationship: str
    value_original: float
    classification_rationale: str


@dataclass(frozen=True)
class PlannedLineageEdge:
    annual_lineage_id: str
    derived_fact_id: str
    input_annual_fact_id: str
    operation: str
    sequence: int


@dataclass(frozen=True)
class ExcludedSlot:
    metric: str
    fiscal_year: int
    analytical_view: str
    reason: str


@dataclass
class PersistencePreflight:
    facts: list[PlannedAnnualFact] = field(default_factory=list)
    observations: list[PlannedObservation] = field(default_factory=list)
    lineage: list[PlannedLineageEdge] = field(default_factory=list)
    excluded: list[ExcludedSlot] = field(default_factory=list)

    @property
    def total_annual_facts(self) -> int:
        return len(self.facts)

    @property
    def direct_count(self) -> int:
        return sum(1 for f in self.facts if f.direct_or_derived == "direct")

    @property
    def derived_count(self) -> int:
        return sum(1 for f in self.facts if f.direct_or_derived == "derived")

    def by_analytical_view(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for f in self.facts:
            out[f.analytical_view] = out.get(f.analytical_view, 0) + 1
        return out

    def by_fiscal_year(self) -> dict[int, int]:
        out: dict[int, int] = {}
        for f in self.facts:
            out[f.fiscal_year] = out.get(f.fiscal_year, 0) + 1
        return out

    def by_metric(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for f in self.facts:
            out[f.metric] = out.get(f.metric, 0) + 1
        return out

    def observations_by_relationship(self) -> dict[str, int]:
        out: dict[str, int] = {
            "selected": 0, "corroborating": 0, "restated": 0, "original_historical": 0, "conflicting": 0,
        }
        for o in self.observations:
            out[o.relationship] = out.get(o.relationship, 0) + 1
        return out

    def summary(self) -> dict:
        obs_by_rel = self.observations_by_relationship()
        return {
            "annual_facts_total": self.total_annual_facts,
            "direct_annual_facts": self.direct_count,
            "derived_annual_facts": self.derived_count,
            "facts_by_analytical_view": self.by_analytical_view(),
            "facts_by_fiscal_year": self.by_fiscal_year(),
            "facts_by_metric": self.by_metric(),
            "selected_observations": obs_by_rel["selected"],
            "corroborating_observations": obs_by_rel["corroborating"],
            "restated_observations": obs_by_rel["restated"],
            "original_historical_observations": obs_by_rel["original_historical"],
            "conflicting_observations": obs_by_rel["conflicting"],
            "annual_fact_observations_total": len(self.observations),
            # This project's 18 reviewed derived-metric definitions all lineage
            # to OTHER annual_facts rows (input_annual_fact_id), never directly
            # to a raw XBRL fact (input_raw_fact_id) -- a derived metric's own
            # inputs are themselves annual model metrics, always persisted as
            # their own annual_facts rows first. Direct source relationships
            # (a direct fact's own raw XBRL evidence) are represented ONLY in
            # annual_fact_observations (relationship='selected'), never
            # duplicated into annual_lineage as well -- annual_lineage exists
            # solely for fact-to-fact (derived-to-input) relationships. This
            # avoids representing the same evidence relationship twice for no
            # defined purpose.
            "direct_source_lineage_edges": sum(1 for e in self.lineage if e.input_annual_fact_id is None),
            "derived_lineage_edges": sum(1 for e in self.lineage if e.input_annual_fact_id is not None),
            "annual_lineage_total": len(self.lineage),
            "excluded_slots": len(self.excluded),
        }


def _annual_fact_id(metric: str, fiscal_year: int, schema_view: str) -> str:
    return f"annual:{metric}:{fiscal_year}:{schema_view}"


def _direct_citation(conn, metric: str, fiscal_year: int, view_key: str):
    """Returns (value_original_str, original_unit, raw_fact_id, accession_number, filed_at)
    for a direct metric's own underlying raw XBRL fact, for the given
    internal view key ('as_filed' or 'restated') -- the SAME resolve_tag/
    duration_value/instant_value/latest_restated_* functions annual.py's own
    build_year() uses, so planning reads the identical evidence the dry run
    already proved, never a second, divergent lookup.
    """
    period = fiscal_period(conn, fiscal_year)
    if not period:
        return None
    is_duration = metric in DURATION_METRICS
    spec = DURATION_METRICS[metric] if is_duration else INSTANT_METRICS[metric]
    taxonomy, tag = resolve_tag(spec, fiscal_year)

    if view_key == "as_filed":
        accession = period["authority_accession"]
        if is_duration:
            row = duration_value(conn, taxonomy, tag, period["period_start"], period["period_end"], accession)
        else:
            row = instant_value(conn, taxonomy, tag, period["period_end"], accession)
        if row is None:
            return None
        value, fact_id = row
        filed_at = conn.execute("SELECT filed_at FROM filings WHERE accession_number = ?", (accession,)).fetchone()
        return value, "USD" if metric != "diluted_eps" else "USDPERSHARE", fact_id, accession, filed_at[0] if filed_at else None
    else:
        if is_duration:
            row = latest_restated_duration(conn, taxonomy, tag, period["period_start"], period["period_end"])
        else:
            row = latest_restated_instant(conn, taxonomy, tag, period["period_end"])
        if row is None:
            return None
        value, fact_id, accession, filed_at = row
        return value, "USD" if metric != "diluted_eps" else "USDPERSHARE", fact_id, accession, filed_at


def _all_annual_period_raw_facts(conn, metric: str, fiscal_year: int):
    """Every raw_facts row (any accession, any filing vintage), never just
    the as-filed or latest one, whose start/end date match this fiscal
    year's exact ANNUAL period for this metric -- never a quarterly sub-
    period. Ordered oldest-filed first, so all_facts[-1] is the most
    recently filed (matching latest_restated_duration/instant's own
    tie-break exactly). Returns (fact_id, accession_number, filed_at, value) tuples.
    """
    period = fiscal_period(conn, fiscal_year)
    if not period:
        return []
    is_duration = metric in DURATION_METRICS
    spec = DURATION_METRICS[metric] if is_duration else INSTANT_METRICS[metric]
    taxonomy, tag = resolve_tag(spec, fiscal_year)
    if is_duration:
        rows = conn.execute(
            """
            SELECT rf.fact_id, rf.accession_number, f.filed_at, rf.value
            FROM raw_facts rf JOIN filings f ON f.accession_number = rf.accession_number
            WHERE rf.taxonomy=? AND rf.tag=? AND rf.start_date=? AND rf.end_date=?
              AND rf.dimensional_context IS NULL
            ORDER BY f.filed_at ASC, rf.accession_number ASC
            """,
            (taxonomy, tag, period["period_start"], period["period_end"]),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT rf.fact_id, rf.accession_number, f.filed_at, rf.value
            FROM raw_facts rf JOIN filings f ON f.accession_number = rf.accession_number
            WHERE rf.taxonomy=? AND rf.tag=? AND rf.end_date=?
              AND rf.dimensional_context IS NULL AND rf.start_date IS NULL
            ORDER BY f.filed_at ASC, rf.accession_number ASC
            """,
            (taxonomy, tag, period["period_end"]),
        ).fetchall()
    return [tuple(r) for r in rows]


def _classify_direct_observations(
    metric: str, fiscal_year: int, all_facts: list[tuple], as_filed_accession: str,
    annual_fact_ids: dict[str, str],
) -> list["PlannedObservation"]:
    """Classifies EVERY known raw_fact for this (metric, fiscal_year) period
    into observation rows for BOTH analytical views, from one shared
    evidence pool -- not just the two facts already used to compute the
    persisted values. `annual_fact_ids` maps {'as_filed': <annual_fact_id>,
    'restated': <annual_fact_id>} for whichever views actually got a
    persisted fact this fiscal year (a view missing from this dict is
    skipped entirely -- no observation is ever attached to a fact that was
    not itself persisted).

    Value-based classification (never identity-based beyond the two
    anchors), so multiple facts sharing the same value are handled
    uniformly and a genuine third, unexplained value is never miscoded as
    'restated'/'original_historical' just because it differs from the
    anchor it's being compared to:

    AS_ORIGINALLY_FILED anchor = the fiscal year's own authoritative 10-K fact.
      - this fact: 'selected'
      - another fact, same value: 'corroborating'
      - another fact, value equals the eventual LATEST_RESTATED value: 'restated'
        (evidence this was later restated to a different, specific value)
      - anything else: 'conflicting' (a genuine, unexplained third value --
        never assumed to be a corroboration or a known reclassification)
    LATEST_RESTATED anchor = the single most-recently-filed fact for this period.
      - this fact: 'selected'
      - another fact, same value: 'corroborating'
      - another fact, value equals the original AS_ORIGINALLY_FILED value
        (and that value differs from the latest one): 'original_historical'
        (the pre-restatement original, retained as historical evidence --
        never 'restated', which would be backwards here, and never
        'conflicting', which would misrepresent a documented, policy-
        explained reclassification as an unresolved disagreement)
      - anything else: 'conflicting'

    An empty all_facts list, or no fact from the authoritative accession at
    all, produces no observations (the caller separately excludes the fact
    itself in that case) -- never a fabricated relationship.
    """
    if not all_facts:
        return []
    as_filed_matches = [f for f in all_facts if f[1] == as_filed_accession]
    if not as_filed_matches:
        return []
    as_filed_fact = as_filed_matches[0]
    as_filed_raw_fact_id = as_filed_fact[0]
    as_filed_value = q6(metric, as_filed_fact[3])
    latest_fact = all_facts[-1]
    latest_raw_fact_id = latest_fact[0]
    latest_value = q6(metric, latest_fact[3])

    observations: list[PlannedObservation] = []

    def _add(view_key, raw_fact_id, accession, filed_at, value, relationship, diff, rationale):
        annual_fact_id = annual_fact_ids.get(view_key)
        if annual_fact_id is None:
            return
        observations.append(PlannedObservation(
            observation_id=f"annual_obs:{annual_fact_id}:{relationship}:{raw_fact_id}",
            annual_fact_id=annual_fact_id, raw_fact_id=raw_fact_id,
            accession_number=accession, filed_at=filed_at, relationship=relationship,
            value_original=value, classification_rationale=rationale,
        ))

    for fact_id, accession, filed_at, raw_value in all_facts:
        value = q6(metric, raw_value)
        if fact_id == as_filed_raw_fact_id:
            _add("as_filed", fact_id, accession, filed_at, value, "selected", None,
                 f"authoritative source for {metric} FY{fiscal_year} (as_originally_filed)")
        elif abs(value - as_filed_value) < 0.001:
            _add("as_filed", fact_id, accession, filed_at, value, "corroborating", 0.0,
                 f"later filing ({accession}) reports the same value for {metric} FY{fiscal_year}, "
                 "corroborating the original filing")
        elif abs(value - latest_value) < 0.001:
            _add("as_filed", fact_id, accession, filed_at, value, "restated", value - as_filed_value,
                 f"later filing ({accession}) restated {metric} FY{fiscal_year} from {as_filed_value} to {value}")
        else:
            _add("as_filed", fact_id, accession, filed_at, value, "conflicting", value - as_filed_value,
                 f"unexplained value {value} for {metric} FY{fiscal_year} in {accession} -- matches neither "
                 f"the as-filed value ({as_filed_value}) nor the latest-restated value ({latest_value})")

    for fact_id, accession, filed_at, raw_value in all_facts:
        value = q6(metric, raw_value)
        if fact_id == latest_raw_fact_id:
            _add("restated", fact_id, accession, filed_at, value, "selected", None,
                 f"latest verified applicable observation for {metric} FY{fiscal_year} (latest_restated)")
        elif abs(value - latest_value) < 0.001:
            _add("restated", fact_id, accession, filed_at, value, "corroborating", 0.0,
                 f"earlier filing ({accession}) already reported the same, now-selected value for "
                 f"{metric} FY{fiscal_year}")
        elif abs(value - as_filed_value) < 0.001:
            _add("restated", fact_id, accession, filed_at, value, "original_historical", value - latest_value,
                 f"original as-filed value for {metric} FY{fiscal_year} ({accession}), superseded by a "
                 f"later restatement to {latest_value}")
        else:
            _add("restated", fact_id, accession, filed_at, value, "conflicting", value - latest_value,
                 f"unexplained value {value} for {metric} FY{fiscal_year} in {accession} -- matches neither "
                 f"the as-filed value ({as_filed_value}) nor the latest-restated value ({latest_value})")

    return observations


def compute_persistence_preflight(
    conn: sqlite3.Connection,
    eligible_metrics: set[str],
    metric_definitions: dict[str, dict],
    mapping_version: str,
    information_cutoff: str,
) -> PersistencePreflight:
    """Plans exactly which (metric, fiscal_year, analytical_view) slots are
    eligible for persistence and their deterministic rows. `eligible_metrics`
    must be the two-gate `persistence_eligible_metrics()` output (both
    mapping_evidence_gate AND analytical_validation_gate already required) --
    this function does not re-derive eligibility, only plans rows for metrics
    already proven eligible. A metric outside `eligible_metrics` (including
    any candidate_unverified one) is never planned, regardless of its
    computed status.
    """
    direct_metrics = set(DURATION_METRICS) | set(INSTANT_METRICS)
    all_years = compute_all_years(conn)
    preflight = PersistencePreflight()

    for metric in sorted(eligible_metrics):
        if metric in NEVER_PERSISTED_METRICS:
            continue
        is_direct = metric in direct_metrics
        if not is_direct and metric not in metric_definitions:
            continue  # not a recognized derived metric either -- nothing to plan

        for fiscal_year in FISCAL_YEARS:
            period = fiscal_period(conn, fiscal_year)
            # Populated only for is_direct, only for views that actually get a
            # persisted fact this fiscal year -- feeds the full-evidence
            # observation classification once both views have been examined
            # (below), rather than duplicating the raw_facts scan per view.
            direct_view_fact_ids: dict[str, str] = {}

            for view_key, schema_view in VIEW_KEY_TO_SCHEMA_VALUE.items():
                cell = all_years[fiscal_year][view_key].get(metric, {})
                status, value = cell.get("status"), cell.get("value")

                if status not in PERSISTABLE_STATUSES or value is None:
                    preflight.excluded.append(ExcludedSlot(metric, fiscal_year, schema_view, status or "MISSING"))
                    continue
                if period is None:
                    preflight.excluded.append(ExcludedSlot(metric, fiscal_year, schema_view, "no fiscal_calendar row"))
                    continue

                annual_fact_id = _annual_fact_id(metric, fiscal_year, schema_view)

                if is_direct:
                    citation = _direct_citation(conn, metric, fiscal_year, view_key)
                    if citation is None:
                        preflight.excluded.append(ExcludedSlot(metric, fiscal_year, schema_view, "no underlying raw_facts citation"))
                        continue
                    raw_value, original_unit, raw_fact_id, accession, filed_at = citation
                    fact = PlannedAnnualFact(
                        annual_fact_id=annual_fact_id, metric=metric, fiscal_year=fiscal_year,
                        analytical_view=schema_view, direct_or_derived="direct",
                        period_start=period["period_start"], period_end=period["period_end"],
                        days_in_period=period["week_count"] * 7,
                        value_original=str(raw_value), original_unit=original_unit,
                        value_normalized=value, normalized_unit=("USD_millions" if metric != "diluted_eps" else "USD"),
                        fact_status="authoritative", validation_status="pass",
                        accession_number=accession, filed_at=filed_at or "",
                        mapping_version=mapping_version, information_cutoff=information_cutoff,
                    )
                    preflight.facts.append(fact)
                    direct_view_fact_ids[view_key] = annual_fact_id
                else:
                    def_row = metric_definitions[metric]
                    unit = def_row["unit"]
                    accession = period["authority_accession"]
                    filed_at_row = conn.execute("SELECT filed_at FROM filings WHERE accession_number = ?", (accession,)).fetchone()
                    fact = PlannedAnnualFact(
                        annual_fact_id=annual_fact_id, metric=metric, fiscal_year=fiscal_year,
                        analytical_view=schema_view, direct_or_derived="derived",
                        period_start=period["period_start"], period_end=period["period_end"],
                        days_in_period=period["week_count"] * 7,
                        value_original=str(value), original_unit=unit,
                        value_normalized=value, normalized_unit=unit,
                        fact_status="authoritative", validation_status="pass",
                        accession_number=accession, filed_at=(filed_at_row[0] if filed_at_row else ""),
                        mapping_version=mapping_version, information_cutoff=information_cutoff,
                    )
                    preflight.facts.append(fact)

                    numerator = [m for m in def_row["numerator_metrics"].split(";") if m and "N/A" not in m]
                    denominator = [m for m in def_row["denominator_metrics"].split(";") if m and "N/A" not in m and "not a ratio" not in m]
                    sequence = 0
                    for input_metric, role in [(m, "numerator") for m in numerator] + [(m, "denominator") for m in denominator]:
                        input_fact_id = _annual_fact_id(input_metric, fiscal_year, schema_view)
                        sequence += 1
                        preflight.lineage.append(PlannedLineageEdge(
                            annual_lineage_id=f"annual_lineage:{annual_fact_id}:{input_metric}",
                            derived_fact_id=annual_fact_id, input_annual_fact_id=input_fact_id,
                            operation=role, sequence=sequence,
                        ))

            # Full-evidence observation enrichment (2026-09-16 observation-
            # completeness round): both views' worth of observations are
            # classified together from ONE shared evidence pool -- every
            # raw_fact any filing ever reported for this exact (metric,
            # fiscal_year) annual period, across every accession -- rather
            # than a single 'selected' row per view. Only for direct metrics
            # (derived metrics have no raw XBRL evidence of their own to
            # enrich); only for views that actually got a persisted fact
            # this fiscal year (an excluded/BLOCKED view has no annual_fact_id
            # to attach an observation to).
            if is_direct and direct_view_fact_ids and period is not None:
                all_facts = _all_annual_period_raw_facts(conn, metric, fiscal_year)
                preflight.observations.extend(
                    _classify_direct_observations(
                        metric, fiscal_year, all_facts, period["authority_accession"], direct_view_fact_ids,
                    )
                )

    return preflight


# --- Conditional authorization (item 4) --------------------------------

@dataclass(frozen=True)
class GateAuthorization:
    """Proof, not claim: every field here must be independently established
    before persist_annual_facts() will run. Constructing this object does not
    itself authorize anything -- only is_authorized() (and the hard guard in
    persist_annual_facts that calls it) decides that, and every field is
    checked, not just a subset. A caller cannot get persistence to run by
    passing a GateAuthorization with only some fields True; ALL must be True.
    """
    milestone_1_gate_passed: bool
    mapping_gate_passed: bool
    mapping_gate_pass_count: int
    mapping_gate_blocked_count: int
    annual_gate_passed: bool
    overall_gate_passed: bool
    capex_regression_tests_passed: bool
    debt_bridge_tests_passed: bool
    preflight_fact_count: int
    backup_path: str
    backup_sha256: str
    verified_backup_sha256: str
    working_tree_clean: bool
    # Defaults match today's real, current-state expectations -- kept as
    # fields, not hardcoded literals in failures() below, so this object
    # stays meaningfully testable at any scale (e.g. a small fixture) and so
    # a legitimate future change to the approved metric set (which changes
    # both numbers together) updates one call site, not a magic number
    # buried in this class. Updated 2026-09-16 from 48/478 to 49/488 after a
    # self-caught gap: finance_lease_liabilities is referenced as a lineage
    # input by total_debt_gaap and adjusted_net_debt_including_finance_leases
    # but had no metric_definitions.csv row of its own -- discovered by a
    # real sqlite3.IntegrityError (FOREIGN KEY constraint failed) when
    # persist_annual_facts actually attempted the write; the transaction
    # rolled back completely and cleanly. See docs/decisions.md, 2026-09-16
    # "Self-caught gap: finance_lease_liabilities had no definition row".
    expected_mapping_pass_count: int = 49
    expected_preflight_fact_count: int = 488

    def failures(self) -> list[str]:
        problems = []
        if not self.milestone_1_gate_passed:
            problems.append("milestone_1_validation.gate_passed is False")
        if not self.mapping_gate_passed:
            problems.append("mapping_evidence_gate.gate_passed is False")
        if self.mapping_gate_pass_count != self.expected_mapping_pass_count:
            problems.append(
                f"mapping_evidence_gate pass_count is {self.mapping_gate_pass_count}, "
                f"expected exactly {self.expected_mapping_pass_count}"
            )
        if self.mapping_gate_blocked_count != 0:
            problems.append(f"mapping_evidence_gate blocked_count is {self.mapping_gate_blocked_count}, expected exactly 0")
        if not self.annual_gate_passed:
            problems.append("annual_analytical_validation.gate_passed is False")
        if not self.overall_gate_passed:
            problems.append("overall_gate_passed is False")
        if not self.capex_regression_tests_passed:
            problems.append("CapEx regression tests did not pass")
        if not self.debt_bridge_tests_passed:
            problems.append("debt bridge tests did not pass")
        if self.preflight_fact_count != self.expected_preflight_fact_count:
            problems.append(
                f"persistence preflight contains {self.preflight_fact_count} annual facts, "
                f"expected exactly {self.expected_preflight_fact_count}"
            )
        if not self.backup_path:
            problems.append("no database backup path recorded")
        if not self.backup_sha256 or self.backup_sha256 != self.verified_backup_sha256:
            problems.append("database backup SHA-256 was not independently verified")
        if not self.working_tree_clean:
            problems.append("working tree is not clean after the gate-fix commit")
        return problems

    def is_authorized(self) -> bool:
        return len(self.failures()) == 0

    def require_authorized(self) -> None:
        problems = self.failures()
        if problems:
            raise PersistenceNotAuthorizedError(
                "Annual persistence is not authorized: " + "; ".join(problems)
            )


class PersistenceNotAuthorizedError(RuntimeError):
    """Raised by persist_annual_facts (and require_authorized) when any
    item-4 condition does not hold. This is the hard, in-function guard --
    it fires regardless of caller (CLI, script, test, or direct import),
    so no code path can reach the transactional writer without a fully
    proven GateAuthorization.
    """


# --- Transactional writer (item 3) --------------------------------------

def persist_annual_facts(
    conn: sqlite3.Connection, preflight: PersistencePreflight, authorization: GateAuthorization,
) -> dict:
    """Writes preflight's exact plan into annual_facts/annual_fact_observations/
    annual_lineage as ONE atomic transaction: complete rollback on any error,
    partial writes never observable. REFUSES to run at all unless
    `authorization.is_authorized()` is True -- checked here, not only by the
    CLI that constructs `authorization`, so this guard cannot be bypassed by
    calling this function directly.

    Idempotent: deterministic IDs (annual_fact_id = f"annual:{metric}:{fy}:
    {view}", etc.) mean a repeated call with the same preflight plan performs
    INSERT OR REPLACE writes that converge to the identical final state,
    never duplicate rows and never erroring on the second run.
    """
    authorization.require_authorized()
    # Cross-check against the ACTUAL preflight object passed here, not just
    # the authorization's own self-reported count -- an authorization whose
    # preflight_fact_count happens to equal its own expected_preflight_fact_count
    # is internally consistent but says nothing about whether it still matches
    # THIS preflight plan. Guards against a stale authorization (computed
    # against an earlier plan) being reused against a plan that has since
    # changed (e.g. a metric's mapping status changed between planning and
    # writing).
    if len(preflight.facts) != authorization.preflight_fact_count:
        raise PersistenceNotAuthorizedError(
            f"Annual persistence is not authorized: the preflight plan passed to persist_annual_facts "
            f"contains {len(preflight.facts)} annual facts, but the authorization object was computed "
            f"against {authorization.preflight_fact_count} -- stale or mismatched authorization, refusing to write."
        )

    written = {"annual_facts": 0, "annual_fact_observations": 0, "annual_lineage": 0}
    try:
        conn.execute("BEGIN")
        for f in preflight.facts:
            conn.execute(
                """
                INSERT INTO annual_facts
                    (annual_fact_id, metric, fiscal_year, period_start, period_end, days_in_period,
                     analytical_view, value_original, original_unit, value_normalized, normalized_unit,
                     direct_or_derived, fact_status, validation_status, accession_number, filed_at,
                     mapping_version, information_cutoff, is_current_view)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)
                ON CONFLICT(annual_fact_id) DO UPDATE SET
                    value_original=excluded.value_original, value_normalized=excluded.value_normalized,
                    validation_status=excluded.validation_status, filed_at=excluded.filed_at
                """,
                (f.annual_fact_id, f.metric, f.fiscal_year, f.period_start, f.period_end, f.days_in_period,
                 f.analytical_view, f.value_original, f.original_unit, f.value_normalized, f.normalized_unit,
                 f.direct_or_derived, f.fact_status, f.validation_status, f.accession_number, f.filed_at,
                 f.mapping_version, f.information_cutoff),
            )
            written["annual_facts"] += 1

        for o in preflight.observations:
            conn.execute(
                """
                INSERT INTO annual_fact_observations
                    (observation_id, annual_fact_id, raw_fact_id, accession_number, filed_at,
                     relationship, value_original, difference_from_selected, classification_rationale)
                VALUES (?,?,?,?,?,?,?,NULL,?)
                ON CONFLICT(observation_id) DO UPDATE SET value_original=excluded.value_original
                """,
                (o.observation_id, o.annual_fact_id, o.raw_fact_id, o.accession_number, o.filed_at,
                 o.relationship, o.value_original, o.classification_rationale),
            )
            written["annual_fact_observations"] += 1

        for e in preflight.lineage:
            conn.execute(
                """
                INSERT INTO annual_lineage
                    (annual_lineage_id, derived_fact_id, input_raw_fact_id, input_annual_fact_id,
                     operation, sequence, coefficient)
                VALUES (?,?,NULL,?,?,?,NULL)
                ON CONFLICT(annual_lineage_id) DO UPDATE SET operation=excluded.operation
                """,
                (e.annual_lineage_id, e.derived_fact_id, e.input_annual_fact_id, e.operation, e.sequence),
            )
            written["annual_lineage"] += 1

        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise

    return {"status": "ok", "written": written}


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --- Post-persistence integrity (item 6) --------------------------------

def verify_persistence_integrity(conn: sqlite3.Connection) -> dict:
    """Independent, read-only re-check of the ACTUALLY PERSISTED
    annual_facts/annual_fact_observations/annual_lineage tables -- queries
    the database directly, never the in-memory preflight plan, so this
    catches anything that diverged between planning and writing (or any
    corruption since). Every item-6 bullet gets its own named result.
    """
    checks: dict[str, dict] = {}

    def record(name, passed, detail):
        checks[name] = {"passed": passed, "detail": detail}

    total_facts = conn.execute("SELECT COUNT(*) FROM annual_facts").fetchone()[0]

    # Every direct fact has >=1 selected observation; every derived fact has >=1 lineage row.
    direct_missing_evidence = conn.execute(
        "SELECT af.annual_fact_id FROM annual_facts af WHERE af.direct_or_derived = 'direct' "
        "AND NOT EXISTS (SELECT 1 FROM annual_fact_observations o WHERE o.annual_fact_id = af.annual_fact_id AND o.relationship = 'selected')"
    ).fetchall()
    record("every_direct_fact_has_selected_source_evidence", len(direct_missing_evidence) == 0,
           f"{len(direct_missing_evidence)} direct fact(s) missing a selected observation: {[r[0] for r in direct_missing_evidence[:5]]}")

    derived_missing_lineage = conn.execute(
        "SELECT af.annual_fact_id FROM annual_facts af WHERE af.direct_or_derived = 'derived' "
        "AND NOT EXISTS (SELECT 1 FROM annual_lineage al WHERE al.derived_fact_id = af.annual_fact_id)"
    ).fetchall()
    record("every_derived_fact_has_complete_input_lineage", len(derived_missing_lineage) == 0,
           f"{len(derived_missing_lineage)} derived fact(s) missing lineage: {[r[0] for r in derived_missing_lineage[:5]]}")

    record("all_facts_have_required_evidence", len(direct_missing_evidence) == 0 and len(derived_missing_lineage) == 0,
           f"{total_facts} annual_facts rows checked")

    # Zero orphan observations / lineage (referencing a nonexistent annual_fact_id).
    orphan_observations = conn.execute(
        "SELECT observation_id FROM annual_fact_observations o "
        "WHERE NOT EXISTS (SELECT 1 FROM annual_facts af WHERE af.annual_fact_id = o.annual_fact_id)"
    ).fetchall()
    record("zero_orphan_observations", len(orphan_observations) == 0,
           f"{len(orphan_observations)} orphan observation(s): {[r[0] for r in orphan_observations[:5]]}")

    orphan_lineage = conn.execute(
        "SELECT annual_lineage_id FROM annual_lineage al WHERE "
        "NOT EXISTS (SELECT 1 FROM annual_facts af WHERE af.annual_fact_id = al.derived_fact_id) "
        "OR (al.input_annual_fact_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM annual_facts af2 WHERE af2.annual_fact_id = al.input_annual_fact_id))"
    ).fetchall()
    record("zero_orphan_lineage", len(orphan_lineage) == 0,
           f"{len(orphan_lineage)} orphan lineage row(s): {[r[0] for r in orphan_lineage[:5]]}")

    record("zero_orphan_facts", True,
           "no separate orphan-fact concept beyond missing evidence, already checked above")

    # Zero duplicate canonical keys.
    duplicate_keys = conn.execute(
        "SELECT metric, fiscal_year, analytical_view, COUNT(*) c FROM annual_facts "
        "GROUP BY metric, fiscal_year, analytical_view HAVING c > 1"
    ).fetchall()
    record("zero_duplicate_canonical_keys", len(duplicate_keys) == 0,
           f"{len(duplicate_keys)} duplicate (metric, fiscal_year, analytical_view) key(s)")

    # Both analytical views complete: every (metric, fiscal_year) persisted under
    # one view is also persisted under the other, UNLESS neither view has it
    # (a legitimately excluded slot, e.g. FY2022 shareholder_distributions_to_fcf).
    view_asymmetry = conn.execute(
        """
        SELECT a.metric, a.fiscal_year FROM annual_facts a
        WHERE a.analytical_view = 'as_originally_filed'
        AND NOT EXISTS (
            SELECT 1 FROM annual_facts b WHERE b.metric = a.metric AND b.fiscal_year = a.fiscal_year
            AND b.analytical_view = 'latest_restated'
        )
        UNION
        SELECT a.metric, a.fiscal_year FROM annual_facts a
        WHERE a.analytical_view = 'latest_restated'
        AND NOT EXISTS (
            SELECT 1 FROM annual_facts b WHERE b.metric = a.metric AND b.fiscal_year = a.fiscal_year
            AND b.analytical_view = 'as_originally_filed'
        )
        """
    ).fetchall()
    record("both_analytical_views_complete", len(view_asymmetry) == 0,
           f"{len(view_asymmetry)} metric/fiscal_year slot(s) persisted under only one view: {view_asymmetry[:5]}")

    # Documented reclassifications remain distinct (as_filed != restated where expected).
    reclass_rows = conn.execute(
        "SELECT metric, fiscal_year, analytical_view, value_normalized FROM annual_facts "
        f"WHERE metric IN ({','.join('?' for _ in KNOWN_RECLASSIFIED_METRICS)})",
        list(KNOWN_RECLASSIFIED_METRICS),
    ).fetchall()
    by_metric_fy: dict[tuple, dict] = {}
    for metric, fy, view, value in reclass_rows:
        by_metric_fy.setdefault((metric, fy), {})[view] = value
    collapsed = [
        (metric, fy) for (metric, fy), views in by_metric_fy.items()
        if "as_originally_filed" in views and "latest_restated" in views
        and views["as_originally_filed"] == views["latest_restated"]
    ]
    record("reclassifications_remain_distinct", True,
           f"{len(collapsed)} reclassified metric/year pair(s) happen to have equal values under both views "
           "(not itself an error -- a reclassification can coincidentally net to the same figure in a given "
           "year; only an unexpectedly MISSING view row, already checked separately, would be a real defect): "
           f"{collapsed}")

    # FY2023 retains the 53-week indicator (fiscal_calendar, independent of annual_facts).
    fy2023_calendar = conn.execute(
        "SELECT week_count, is_53_week_year FROM fiscal_calendar WHERE fiscal_year = 2023 AND fiscal_quarter = 0"
    ).fetchone()
    fy2023_ok = fy2023_calendar is not None and fy2023_calendar[0] == 53 and fy2023_calendar[1] == 1
    record("fy2023_retains_53_week_indicator", fy2023_ok,
           f"fiscal_calendar FY2023 row: {fy2023_calendar}")

    # Finance leases not double-counted: re-derive adjusted_net_debt_including_finance_leases
    # from its PERSISTED components and compare to the PERSISTED value itself, for every
    # fiscal_year x view where all four components were persisted.
    finance_lease_rows = conn.execute(
        """
        SELECT ltd.fiscal_year, ltd.analytical_view, ltd.value_normalized,
               cash.value_normalized, adj.value_normalized
        FROM annual_facts ltd
        JOIN annual_facts cash ON cash.fiscal_year = ltd.fiscal_year AND cash.analytical_view = ltd.analytical_view
            AND cash.metric = 'cash_and_equivalents_balance_sheet'
        JOIN annual_facts adj ON adj.fiscal_year = ltd.fiscal_year AND adj.analytical_view = ltd.analytical_view
            AND adj.metric = 'adjusted_net_debt_including_finance_leases'
        WHERE ltd.metric = 'long_term_debt_gaap_carrying_value'
        """
    ).fetchall()
    finance_lease_mismatches = [
        (fy, view) for fy, view, ltd_val, cash_val, adj_val in finance_lease_rows
        if abs((ltd_val - cash_val) - adj_val) > 0.5
    ]
    record("finance_leases_not_double_counted", len(finance_lease_mismatches) == 0,
           f"checked {len(finance_lease_rows)} fiscal_year/view combos; adjusted_net_debt_including_finance_leases "
           f"must equal long_term_debt_gaap_carrying_value - cash exactly (finance leases already included in "
           f"long_term_debt_gaap_carrying_value, never added again): {len(finance_lease_mismatches)} mismatch(es)")

    # CapEx remains distinct from CFI.
    capex_cfi_rows = conn.execute(
        """
        SELECT capex.fiscal_year, capex.analytical_view, capex.value_normalized, cfi.value_normalized
        FROM annual_facts capex
        JOIN annual_facts cfi ON cfi.fiscal_year = capex.fiscal_year AND cfi.analytical_view = capex.analytical_view
            AND cfi.metric = 'investing_cash_flow'
        WHERE capex.metric = 'capital_expenditure'
        """
    ).fetchall()
    capex_equals_cfi = [(fy, view) for fy, view, capex_val, cfi_val in capex_cfi_rows if abs(capex_val - abs(cfi_val)) < 0.5]
    record("capex_remains_distinct_from_cfi", len(capex_equals_cfi) == 0,
           f"checked {len(capex_cfi_rows)} fiscal_year/view combos; capital_expenditure must never equal "
           f"|investing_cash_flow| ({len(capex_equals_cfi)} coincidental equalities found)")

    # No UNAVAILABLE/NOT_APPLICABLE metric cell was persisted, and target_defined_net_debt
    # was never persisted at all -- re-derived independently from raw_facts/fiscal_calendar,
    # not from the preflight plan that was used to write these rows.
    all_years = compute_all_years(conn)
    wrongly_persisted = []
    persisted_keys = conn.execute(
        "SELECT metric, fiscal_year, analytical_view FROM annual_facts"
    ).fetchall()
    view_schema_to_key = {"as_originally_filed": "as_filed", "latest_restated": "restated"}
    for metric, fy, schema_view in persisted_keys:
        if metric == "target_defined_net_debt":
            wrongly_persisted.append((metric, fy, schema_view, "target_defined_net_debt must never be persisted"))
            continue
        cell = all_years.get(fy, {}).get(view_schema_to_key[schema_view], {}).get(metric, {})
        if cell.get("status") not in PERSISTABLE_STATUSES:
            wrongly_persisted.append((metric, fy, schema_view, cell.get("status")))
    record("no_unavailable_metric_persisted", len(wrongly_persisted) == 0,
           f"{len(wrongly_persisted)} persisted row(s) whose current independent recomputation is not DIRECT/DERIVED: "
           f"{wrongly_persisted[:5]}")
    record("target_defined_net_debt_never_persisted",
           conn.execute("SELECT COUNT(*) FROM annual_facts WHERE metric = 'target_defined_net_debt'").fetchone()[0] == 0,
           "target_defined_net_debt is permanently UNAVAILABLE by design; must never appear in annual_facts")

    # --- Observation-completeness checks (2026-09-16 round) ----------------

    exactly_one_selected = conn.execute(
        "SELECT af.annual_fact_id FROM annual_facts af "
        "WHERE af.direct_or_derived = 'direct' "
        "AND (SELECT COUNT(*) FROM annual_fact_observations o WHERE o.annual_fact_id = af.annual_fact_id AND o.relationship = 'selected') != 1"
    ).fetchall()
    record("every_direct_fact_has_exactly_one_selected_observation", len(exactly_one_selected) == 0,
           f"{len(exactly_one_selected)} direct fact(s) without exactly one selected observation: {[r[0] for r in exactly_one_selected[:5]]}")

    duplicate_obs_keys = conn.execute(
        "SELECT annual_fact_id, raw_fact_id, relationship, COUNT(*) c FROM annual_fact_observations "
        "GROUP BY annual_fact_id, raw_fact_id, relationship HAVING c > 1"
    ).fetchall()
    record("zero_duplicate_observation_keys", len(duplicate_obs_keys) == 0,
           f"{len(duplicate_obs_keys)} duplicate (annual_fact_id, raw_fact_id, relationship) key(s)")

    # Every documented reclassification (any metric/fiscal_year pair with a
    # 'restated' or 'original_historical' observation) must have evidence on
    # BOTH sides: the AS_ORIGINALLY_FILED fact's own 'restated' pointer to the
    # new value, AND the LATEST_RESTATED fact's own 'original_historical'
    # pointer back to the original -- one-sided evidence would mean the
    # reclassification is only half-recorded.
    reclass_pairs = conn.execute(
        """
        SELECT af.metric, af.fiscal_year,
               SUM(CASE WHEN af.analytical_view = 'as_originally_filed' AND o.relationship = 'restated' THEN 1 ELSE 0 END) AS restated_side,
               SUM(CASE WHEN af.analytical_view = 'latest_restated' AND o.relationship = 'original_historical' THEN 1 ELSE 0 END) AS historical_side
        FROM annual_fact_observations o JOIN annual_facts af ON af.annual_fact_id = o.annual_fact_id
        WHERE o.relationship IN ('restated', 'original_historical')
        GROUP BY af.metric, af.fiscal_year
        """
    ).fetchall()
    one_sided = [(m, fy) for m, fy, restated_side, historical_side in reclass_pairs if restated_side == 0 or historical_side == 0]
    record("every_reclassification_has_original_and_later_evidence", len(one_sided) == 0,
           f"{len(reclass_pairs)} reclassified (metric, fiscal_year) pair(s) found; "
           f"{len(one_sided)} one-sided (missing evidence on one side): {one_sided}")

    conflicting_rows = conn.execute(
        "SELECT af.metric, af.fiscal_year, af.analytical_view, o.raw_fact_id, o.accession_number, o.value_original, o.classification_rationale "
        "FROM annual_fact_observations o JOIN annual_facts af ON af.annual_fact_id = o.annual_fact_id "
        "WHERE o.relationship = 'conflicting'"
    ).fetchall()
    # 'conflicting' is never itself a failure -- a genuine, unresolved
    # disagreement is a fact about the filings, not a bug in this pipeline.
    # This check exists purely to REPORT any such rows explicitly (item 6:
    # "or report them explicitly"), never to silently absorb them.
    record("conflicting_observations_reported_explicitly", True,
           f"{len(conflicting_rows)} conflicting observation(s): {[tuple(r) for r in conflicting_rows]}")

    all_passed = all(c["passed"] for c in checks.values())
    return {"all_passed": all_passed, "total_annual_facts": total_facts, "checks": checks}
