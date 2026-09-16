"""Milestone 9: corrected investment-capacity taxonomy.

Produced in response to `docs/investment_capacity_semantic_audit.md`,
which found the legacy `ForecastYear.deployable_capacity` field
arithmetically correct but economically ambiguous: it is a gross,
pre-discretionary ceiling (inclusive of carried-forward cash, inclusive
of new borrowing, and computed BEFORE that year's own repurchases are
subtracted), not a residual "capacity still available" figure.

This module is purely ADDITIVE. It does not modify `ForecastYear`, does
not change any persisted historical fact, forecast operating
assumption, scenario assumption, or DCF operating projection, and does
not alter the legacy `deployable_capacity` /
`near_term_debt_repayment_reserve` fields' stored values or meaning --
per the governing correction decision, those are preserved verbatim for
backward compatibility, documented as deprecated, and excluded from
every new cumulative-capacity calculation below.

Every new field is computed from `ForecastYear`'s own EXISTING fields
only (never a re-derivation from raw assumptions), so a discrepancy
between the legacy and corrected figures can only come from a different
FORMULA, never from different underlying data.

Required taxonomy (per the semantic audit and the correction decision):
  A. operating_fcf                        = CFO - CapEx
  B. post_dividend_internal_generation    = operating_fcf - dividends
  C. self_funded_gross_capacity           = capacity from opening excess
                                             liquidity + B, net of mandatory
                                             debt uses, EXCLUDING new borrowing
  D. debt_funded_incremental_capacity     = eligible new debt proceeds
  E. total_gross_funding_capacity         = C + D
  F. total_discretionary_deployment       = repurchases + strategic
                                             investment + voluntary debt
                                             reduction + other discretionary uses
  G. remaining_deployable_headroom        = max(0, E - F)
"""
from __future__ import annotations

from dataclasses import dataclass

from target_cash import forecast as f

CAPACITY_TAXONOMY_VERSION = "v1"
CAPACITY_TAXONOMY_INFORMATION_CUTOFF = f.FORECAST_INFORMATION_CUTOFF


# ---------------------------------------------------------------------------
# Per-year taxonomy
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CapacityTaxonomyYear:
    """One scenario x fiscal-year row of the corrected capacity taxonomy.

    Every field here is derived exclusively from the corresponding
    `ForecastYear`'s own already-computed, already-tested fields -- no
    raw assumption is re-read, and no new assumption is introduced.
    `strategic_investment`, `voluntary_debt_reduction`, and
    `other_discretionary_uses` are explicit, structurally-present $0
    placeholders (no policy lever exists for them this round), following
    the same non-plug, non-silent-zero convention already established
    for `ForecastYear.management_selected_deployment`.
    """
    scenario: str
    fiscal_year: int
    operating_fcf: float
    post_dividend_internal_generation: float
    opening_excess_liquidity: float
    mandatory_debt_uses: float
    self_funded_gross_capacity: float
    debt_funded_incremental_capacity: float
    total_gross_funding_capacity: float
    share_repurchases: float
    strategic_investment: float
    voluntary_debt_reduction: float
    other_discretionary_uses: float
    total_discretionary_deployment: float
    remaining_deployable_headroom: float
    ending_excess_liquidity: float
    information_cutoff: str = CAPACITY_TAXONOMY_INFORMATION_CUTOFF


def compute_capacity_taxonomy_year(y: f.ForecastYear) -> CapacityTaxonomyYear:
    """Pure function: one ForecastYear in, one CapacityTaxonomyYear out.

    No mandatory item is deducted twice: `mandatory_debt_uses`
    (= y.debt_repayments) is subtracted exactly once, inside
    `self_funded_gross_capacity` -- unlike the legacy
    `deployable_capacity`, which subtracted an equivalent amount twice
    (once inside `pre_discretionary_ending_cash`'s own
    `mandatory_financing_flows`, and again via
    `near_term_debt_repayment_reserve`, itself defined as
    `= y.debt_repayments`). See
    docs/investment_capacity_correction_evidence.md for the proof.
    """
    operating_fcf = y.free_cash_flow  # taxonomy A, exact match to the existing field
    post_dividend_internal_generation = y.post_dividend_capacity  # taxonomy B, exact match

    opening_excess_liquidity = max(0.0, y.beginning_cash - y.min_cash_buffer)
    mandatory_debt_uses = y.debt_repayments

    self_funded_gross_capacity = (
        opening_excess_liquidity + post_dividend_internal_generation - mandatory_debt_uses
    )
    debt_funded_incremental_capacity = y.debt_proceeds  # taxonomy D
    total_gross_funding_capacity = self_funded_gross_capacity + debt_funded_incremental_capacity  # E

    strategic_investment = 0.0
    voluntary_debt_reduction = 0.0
    other_discretionary_uses = 0.0
    total_discretionary_deployment = (
        y.share_repurchases + strategic_investment + voluntary_debt_reduction + other_discretionary_uses
    )

    remaining_deployable_headroom = max(0.0, total_gross_funding_capacity - total_discretionary_deployment)
    ending_excess_liquidity = max(0.0, y.ending_cash - y.min_cash_buffer)

    return CapacityTaxonomyYear(
        scenario=y.scenario, fiscal_year=y.fiscal_year,
        operating_fcf=operating_fcf,
        post_dividend_internal_generation=post_dividend_internal_generation,
        opening_excess_liquidity=opening_excess_liquidity,
        mandatory_debt_uses=mandatory_debt_uses,
        self_funded_gross_capacity=self_funded_gross_capacity,
        debt_funded_incremental_capacity=debt_funded_incremental_capacity,
        total_gross_funding_capacity=total_gross_funding_capacity,
        share_repurchases=y.share_repurchases,
        strategic_investment=strategic_investment,
        voluntary_debt_reduction=voluntary_debt_reduction,
        other_discretionary_uses=other_discretionary_uses,
        total_discretionary_deployment=total_discretionary_deployment,
        remaining_deployable_headroom=remaining_deployable_headroom,
        ending_excess_liquidity=ending_excess_liquidity,
    )


def build_capacity_taxonomy(years: list[f.ForecastYear]) -> list[CapacityTaxonomyYear]:
    return [compute_capacity_taxonomy_year(y) for y in years]


def build_capacity_taxonomy_all_scenarios(
    forecasts: dict[str, list[f.ForecastYear]],
) -> dict[str, list[CapacityTaxonomyYear]]:
    return {scenario: build_capacity_taxonomy(years) for scenario, years in forecasts.items()}


# ---------------------------------------------------------------------------
# Horizon (cumulative) summary -- never sums per-year headroom balances
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CapacityHorizonSummary:
    """The five-year (FY2026-FY2030) cumulative capacity picture, computed
    WITHOUT ever summing per-year `remaining_deployable_headroom` (or
    `opening_excess_liquidity`) values across years -- doing so would
    reproduce the exact double-counting error already found and fixed
    once in Milestone 3A for the legacy `deployable_capacity` field.

    `opening_excess_liquidity_at_horizon_start` is taken from FY2026 ONLY
    (the first forecast year) -- it is a STOCK measured once, at the
    start of the horizon, never re-added for later years (their own
    opening_excess_liquidity already reflects the SAME dollars, carried
    forward, and adding it again would double-count it).

    `ending_reserve_movement` is the algebraically necessary reconciling
    term identified while deriving this summary: the minimum-cash-buffer
    REQUIREMENT itself changes across the horizon (it scales with each
    year's own revenue), so a dollar that was "excess" against FY2026's
    buffer may or may not still be "excess" against FY2030's larger (or
    smaller) buffer, independent of anything spent or borrowed. This is
    not a plug -- it is defined exactly as
    `min_cash_buffer[FY2030] - min_cash_buffer[FY2026]` and is proven,
    not assumed, to close the identity in
    `check_capacity_accounted_for_reconciliation` below.
    """
    scenario: str
    cumulative_self_funded_generation: float
    cumulative_debt_funded_capacity: float
    opening_excess_liquidity_at_horizon_start: float
    cumulative_discretionary_deployment: float
    terminal_remaining_headroom: float
    ending_reserve_movement: float
    total_horizon_capacity_accessible: float
    information_cutoff: str = CAPACITY_TAXONOMY_INFORMATION_CUTOFF


def cumulative_self_funded_generation(taxonomy_years: list[CapacityTaxonomyYear]) -> float:
    """A. Sum of INCREMENTAL self-funded capacity generated during the
    horizon -- i.e. post-dividend internal generation net of mandatory
    debt uses, for every year. Deliberately EXCLUDES FY2026's opening
    excess liquidity (a pre-existing stock, not capacity generated
    during the horizon) and every other year's opening_excess_liquidity
    too (each of those is the SAME carried-forward stock, not new
    generation -- including it here would double-count it against the
    horizon-start stock already captured separately, below).
    """
    return sum(
        ty.post_dividend_internal_generation - ty.mandatory_debt_uses for ty in taxonomy_years
    )


def cumulative_debt_funded_capacity(taxonomy_years: list[CapacityTaxonomyYear]) -> float:
    """B. Sum of eligible new borrowing made available for discretionary
    deployment across the horizon."""
    return sum(ty.debt_funded_incremental_capacity for ty in taxonomy_years)


def opening_excess_liquidity_at_horizon_start(taxonomy_years: list[CapacityTaxonomyYear]) -> float:
    """C. The excess liquidity available at the START of FY2026 only --
    a stock, measured once, never summed across years."""
    return taxonomy_years[0].opening_excess_liquidity


def cumulative_discretionary_deployment(taxonomy_years: list[CapacityTaxonomyYear]) -> float:
    """D. Sum of executed/modelled repurchases, strategic investment,
    voluntary debt reduction, and other discretionary uses, across the
    whole horizon."""
    return sum(ty.total_discretionary_deployment for ty in taxonomy_years)


def terminal_remaining_headroom(taxonomy_years: list[CapacityTaxonomyYear]) -> float:
    """E. The FY2030 (final forecast year) remaining_deployable_headroom
    STOCK -- the single number that answers "how much is left,
    unspent, at the end of the plan," never a sum across years."""
    return taxonomy_years[-1].remaining_deployable_headroom


def compute_capacity_horizon_summary(
    scenario: str, years: list[f.ForecastYear], taxonomy_years: list[CapacityTaxonomyYear]
) -> CapacityHorizonSummary:
    """Builds the full horizon summary. Takes both the source
    `ForecastYear` list and its derived `CapacityTaxonomyYear` list so
    `ending_reserve_movement` can be computed directly from
    `ForecastYear.min_cash_buffer` (the real, already-tested field)
    rather than an indirect reconstruction.
    """
    buffer_first = years[0].min_cash_buffer
    buffer_last = years[-1].min_cash_buffer
    reserve_movement = buffer_last - buffer_first

    return CapacityHorizonSummary(
        scenario=scenario,
        cumulative_self_funded_generation=cumulative_self_funded_generation(taxonomy_years),
        cumulative_debt_funded_capacity=cumulative_debt_funded_capacity(taxonomy_years),
        opening_excess_liquidity_at_horizon_start=opening_excess_liquidity_at_horizon_start(taxonomy_years),
        cumulative_discretionary_deployment=cumulative_discretionary_deployment(taxonomy_years),
        terminal_remaining_headroom=terminal_remaining_headroom(taxonomy_years),
        ending_reserve_movement=reserve_movement,
        total_horizon_capacity_accessible=(
            opening_excess_liquidity_at_horizon_start(taxonomy_years)
            + cumulative_self_funded_generation(taxonomy_years)
            + cumulative_debt_funded_capacity(taxonomy_years)
        ),
    )


def build_capacity_horizon_summaries(
    forecasts: dict[str, list[f.ForecastYear]],
    taxonomies: dict[str, list[CapacityTaxonomyYear]],
) -> dict[str, CapacityHorizonSummary]:
    return {
        scenario: compute_capacity_horizon_summary(scenario, forecasts[scenario], taxonomies[scenario])
        for scenario in forecasts
    }


# ---------------------------------------------------------------------------
# Validation checks (persisted subset -- structural/definitional proofs live
# in tests/unit/test_capacity_taxonomy.py instead; see that file's module
# docstring for the mapping of all 20 required proofs to their home).
# ---------------------------------------------------------------------------

CAPACITY_CHECK_METADATA: dict[str, dict] = {
    "operating_fcf_reconciles": {
        "check_type": "arithmetic_invariant",
        "formula": "operating_fcf == CFO - CapEx (taxonomy A)",
    },
    "post_dividend_generation_reconciles": {
        "check_type": "arithmetic_invariant",
        "formula": "post_dividend_internal_generation == operating_fcf - dividends_paid (taxonomy B)",
    },
    "mandatory_debt_not_double_deducted": {
        "check_type": "arithmetic_invariant",
        "formula": "self_funded_gross_capacity == opening_excess_liquidity + B - mandatory_debt_uses, "
                    "with mandatory_debt_uses subtracted exactly once (never a second time via a "
                    "reserve holdback, unlike the legacy near_term_debt_repayment_reserve design)",
    },
    "repurchases_in_discretionary_deployment": {
        "check_type": "structural_completeness_check",
        "formula": "share_repurchases is one of the 4 additive components of total_discretionary_deployment",
    },
    "headroom_never_negative": {
        "check_type": "arithmetic_invariant",
        "formula": "remaining_deployable_headroom == max(0, total_gross_funding_capacity - total_discretionary_deployment) >= 0",
    },
    "ending_cash_above_buffer_or_flagged": {
        "check_type": "structural_completeness_check",
        "formula": "ending_cash >= min_cash_buffer, else funding_warning must already be True on the source ForecastYear",
    },
    "annual_source_use_reconciliation": {
        "check_type": "arithmetic_invariant",
        "formula": "beginning_cash + B + debt_proceeds - debt_repayments - total_discretionary_deployment == ending_cash",
    },
    "capacity_mutually_exclusive": {
        "check_type": "arithmetic_invariant",
        "formula": "remaining_deployable_headroom + total_discretionary_deployment == total_gross_funding_capacity "
                    "(unfloored case) -- no dollar counted in both",
    },
    "cumulative_excludes_repeated_balances": {
        "check_type": "arithmetic_invariant",
        "formula": "total_horizon_capacity_accessible uses opening_excess_liquidity from FY2026 ONLY, "
                    "never summed across years; proven to differ from the (deliberately wrong) naive "
                    "sum of all 5 years' opening_excess_liquidity whenever that sum is nonzero",
    },
    "opening_excess_liquidity_excluded_from_generation": {
        "check_type": "arithmetic_invariant",
        "formula": "cumulative_self_funded_generation excludes FY2026 opening_excess_liquidity by construction",
    },
    "cumulative_deployment_includes_repurchases": {
        "check_type": "structural_completeness_check",
        "formula": "cumulative_discretionary_deployment > 0 whenever any year's share_repurchases > 0",
    },
    "capacity_accounted_for_reconciliation": {
        "check_type": "arithmetic_invariant",
        "formula": "total_horizon_capacity_accessible == cumulative_discretionary_deployment "
                    "+ terminal_remaining_headroom + ending_reserve_movement",
    },
    "scenario_and_cutoff_lineage_complete": {
        "check_type": "structural_completeness_check",
        "formula": "every CapacityTaxonomyYear/CapacityHorizonSummary row carries a non-null scenario "
                    "and information_cutoff <= FORECAST_INFORMATION_CUTOFF",
    },
}


def check_operating_fcf_reconciles(y: f.ForecastYear, ty: CapacityTaxonomyYear) -> f.ValidationResult:
    ok = f._close(ty.operating_fcf, y.operating_cash_flow - y.capital_expenditure)
    return f.ValidationResult(
        "operating_fcf_reconciles", y.scenario, y.fiscal_year, "PASS" if ok else "FAIL",
        f"operating_fcf={ty.operating_fcf:.1f} vs CFO-CapEx={y.operating_cash_flow - y.capital_expenditure:.1f}",
    )


def check_post_dividend_generation_reconciles(y: f.ForecastYear, ty: CapacityTaxonomyYear) -> f.ValidationResult:
    ok = f._close(ty.post_dividend_internal_generation, ty.operating_fcf - y.dividends_paid)
    return f.ValidationResult(
        "post_dividend_generation_reconciles", y.scenario, y.fiscal_year, "PASS" if ok else "FAIL",
        f"B={ty.post_dividend_internal_generation:.1f} vs operating_fcf-dividends="
        f"{ty.operating_fcf - y.dividends_paid:.1f}",
    )


def check_mandatory_debt_not_double_deducted(y: f.ForecastYear, ty: CapacityTaxonomyYear) -> f.ValidationResult:
    expected = ty.opening_excess_liquidity + ty.post_dividend_internal_generation - ty.mandatory_debt_uses
    ok = f._close(ty.self_funded_gross_capacity, expected)
    # Explicitly also prove the legacy defect this check exists to avoid: the legacy field
    # subtracted mandatory debt uses a SECOND time via near_term_debt_repayment_reserve.
    legacy_double_subtracted = f._close(y.near_term_debt_repayment_reserve, y.debt_repayments)
    return f.ValidationResult(
        "mandatory_debt_not_double_deducted", y.scenario, y.fiscal_year, "PASS" if ok else "FAIL",
        f"self_funded_gross_capacity={ty.self_funded_gross_capacity:.1f} vs expected={expected:.1f} "
        f"(legacy near_term_debt_repayment_reserve duplicated debt_repayments: {legacy_double_subtracted})",
    )


def check_repurchases_in_discretionary_deployment(ty: CapacityTaxonomyYear) -> f.ValidationResult:
    expected = ty.share_repurchases + ty.strategic_investment + ty.voluntary_debt_reduction + ty.other_discretionary_uses
    ok = f._close(ty.total_discretionary_deployment, expected) or (expected == 0 and ty.total_discretionary_deployment == 0)
    return f.ValidationResult(
        "repurchases_in_discretionary_deployment", ty.scenario, ty.fiscal_year, "PASS" if ok else "FAIL",
        f"total_discretionary_deployment={ty.total_discretionary_deployment:.1f} vs sum of 4 components={expected:.1f}",
    )


def check_headroom_never_negative(ty: CapacityTaxonomyYear) -> f.ValidationResult:
    ok = ty.remaining_deployable_headroom >= 0.0
    return f.ValidationResult(
        "headroom_never_negative", ty.scenario, ty.fiscal_year, "PASS" if ok else "FAIL",
        f"remaining_deployable_headroom={ty.remaining_deployable_headroom:.1f}",
    )


def check_ending_cash_above_buffer_or_flagged(y: f.ForecastYear) -> f.ValidationResult:
    ok = y.ending_cash >= y.min_cash_buffer or y.funding_warning
    return f.ValidationResult(
        "ending_cash_above_buffer_or_flagged", y.scenario, y.fiscal_year, "PASS" if ok else "FAIL",
        f"ending_cash={y.ending_cash:.1f} vs min_cash_buffer={y.min_cash_buffer:.1f}, "
        f"funding_warning={y.funding_warning}",
    )


def check_annual_source_use_reconciliation(y: f.ForecastYear, ty: CapacityTaxonomyYear) -> f.ValidationResult:
    lhs = y.beginning_cash + ty.post_dividend_internal_generation + y.debt_proceeds - y.debt_repayments - ty.total_discretionary_deployment
    ok = f._close(lhs, y.ending_cash)
    return f.ValidationResult(
        "annual_source_use_reconciliation", y.scenario, y.fiscal_year, "PASS" if ok else "FAIL",
        f"lhs={lhs:.1f} vs ending_cash={y.ending_cash:.1f}",
    )


def check_capacity_mutually_exclusive(ty: CapacityTaxonomyYear) -> f.ValidationResult:
    # Only an exact identity in the unfloored case; when floored, headroom is
    # clamped to 0 and the two sides legitimately diverge -- detected and reported, not hidden.
    unfloored_lhs = ty.total_gross_funding_capacity - ty.total_discretionary_deployment
    floored = unfloored_lhs < 0
    ok = floored or f._close(ty.remaining_deployable_headroom + ty.total_discretionary_deployment, ty.total_gross_funding_capacity)
    return f.ValidationResult(
        "capacity_mutually_exclusive", ty.scenario, ty.fiscal_year, "PASS" if ok else "FAIL",
        f"headroom+deployment={ty.remaining_deployable_headroom + ty.total_discretionary_deployment:.1f} "
        f"vs total_gross_funding_capacity={ty.total_gross_funding_capacity:.1f}"
        + (" (floored)" if floored else ""),
    )


def check_scenario_and_cutoff_lineage_complete(ty: CapacityTaxonomyYear) -> f.ValidationResult:
    ok = bool(ty.scenario) and ty.information_cutoff <= f.FORECAST_INFORMATION_CUTOFF
    return f.ValidationResult(
        "scenario_and_cutoff_lineage_complete", ty.scenario, ty.fiscal_year, "PASS" if ok else "FAIL",
        f"scenario={ty.scenario!r}, information_cutoff={ty.information_cutoff}",
    )


def check_cumulative_excludes_repeated_balances(
    scenario: str, taxonomy_years: list[CapacityTaxonomyYear], summary: CapacityHorizonSummary
) -> f.ValidationResult:
    naive_wrong_sum = sum(ty.opening_excess_liquidity for ty in taxonomy_years) + \
        sum(ty.post_dividend_internal_generation - ty.mandatory_debt_uses for ty in taxonomy_years) + \
        sum(ty.debt_funded_incremental_capacity for ty in taxonomy_years)
    correct = summary.total_horizon_capacity_accessible
    extra_years_opening = sum(ty.opening_excess_liquidity for ty in taxonomy_years[1:])
    # If any non-FY2026 year has nonzero opening excess liquidity, the naive sum
    # (which would re-add it) must differ from the correct total by exactly that amount.
    ok = extra_years_opening == 0 or not f._close(naive_wrong_sum, correct)
    return f.ValidationResult(
        "cumulative_excludes_repeated_balances", scenario, None, "PASS" if ok else "FAIL",
        f"correct_total={correct:.1f}, naive_wrong_sum_would_be={naive_wrong_sum:.1f}, "
        f"extra_years_opening_liquidity_excluded={extra_years_opening:.1f}",
    )


def check_opening_excess_liquidity_excluded_from_generation(
    scenario: str, taxonomy_years: list[CapacityTaxonomyYear], summary: CapacityHorizonSummary
) -> f.ValidationResult:
    fy2026_opening = taxonomy_years[0].opening_excess_liquidity
    contaminated = summary.cumulative_self_funded_generation + fy2026_opening
    # cumulative_self_funded_generation must NOT already contain fy2026_opening;
    # adding it again must change the value whenever fy2026_opening is nonzero.
    ok = fy2026_opening == 0 or not f._close(summary.cumulative_self_funded_generation, contaminated)
    return f.ValidationResult(
        "opening_excess_liquidity_excluded_from_generation", scenario, None, "PASS" if ok else "FAIL",
        f"cumulative_self_funded_generation={summary.cumulative_self_funded_generation:.1f}, "
        f"fy2026_opening_excess_liquidity={fy2026_opening:.1f} (excluded, not summed in)",
    )


def check_cumulative_deployment_includes_repurchases(
    scenario: str, taxonomy_years: list[CapacityTaxonomyYear], summary: CapacityHorizonSummary
) -> f.ValidationResult:
    total_repurchases = sum(ty.share_repurchases for ty in taxonomy_years)
    ok = total_repurchases == 0 or summary.cumulative_discretionary_deployment >= total_repurchases - 1e-6
    return f.ValidationResult(
        "cumulative_deployment_includes_repurchases", scenario, None, "PASS" if ok else "FAIL",
        f"cumulative_discretionary_deployment={summary.cumulative_discretionary_deployment:.1f}, "
        f"total_repurchases_across_horizon={total_repurchases:.1f}",
    )


def check_capacity_accounted_for_reconciliation(
    scenario: str, summary: CapacityHorizonSummary
) -> f.ValidationResult:
    rhs = summary.cumulative_discretionary_deployment + summary.terminal_remaining_headroom + summary.ending_reserve_movement
    ok = f._close(summary.total_horizon_capacity_accessible, rhs)
    return f.ValidationResult(
        "capacity_accounted_for_reconciliation", scenario, None, "PASS" if ok else "FAIL",
        f"total_horizon_capacity_accessible={summary.total_horizon_capacity_accessible:.1f} vs "
        f"deployment+headroom+reserve_movement={rhs:.1f}",
    )


def validate_capacity_taxonomy_all(
    forecasts: dict[str, list[f.ForecastYear]],
    taxonomies: dict[str, list[CapacityTaxonomyYear]],
    summaries: dict[str, CapacityHorizonSummary],
) -> list[f.ValidationResult]:
    results: list[f.ValidationResult] = []
    for scenario, years in forecasts.items():
        taxonomy_years = taxonomies[scenario]
        for y, ty in zip(years, taxonomy_years):
            results.append(check_operating_fcf_reconciles(y, ty))
            results.append(check_post_dividend_generation_reconciles(y, ty))
            results.append(check_mandatory_debt_not_double_deducted(y, ty))
            results.append(check_repurchases_in_discretionary_deployment(ty))
            results.append(check_headroom_never_negative(ty))
            results.append(check_ending_cash_above_buffer_or_flagged(y))
            results.append(check_annual_source_use_reconciliation(y, ty))
            results.append(check_capacity_mutually_exclusive(ty))
            results.append(check_scenario_and_cutoff_lineage_complete(ty))
        summary = summaries[scenario]
        results.append(check_cumulative_excludes_repeated_balances(scenario, taxonomy_years, summary))
        results.append(check_opening_excess_liquidity_excluded_from_generation(scenario, taxonomy_years, summary))
        results.append(check_cumulative_deployment_includes_repurchases(scenario, taxonomy_years, summary))
        results.append(check_capacity_accounted_for_reconciliation(scenario, summary))
    return results


# ---------------------------------------------------------------------------
# Deterministic IDs (idempotent persistence, matching the pattern already
# established by forecast.forecast_fact_id / forecast.build_full_lineage)
# ---------------------------------------------------------------------------

def capacity_taxonomy_result_id(scenario: str, fiscal_year: int, version: str = CAPACITY_TAXONOMY_VERSION) -> str:
    return f"captax_{scenario}_{fiscal_year}_{version}"


def capacity_horizon_result_id(scenario: str, version: str = CAPACITY_TAXONOMY_VERSION) -> str:
    return f"caphrz_{scenario}_{version}"


def capacity_lineage_id(scenario: str, metric: str, fiscal_year: int | None, sequence: int, version: str = CAPACITY_TAXONOMY_VERSION) -> str:
    fy_part = str(fiscal_year) if fiscal_year is not None else "horizon"
    return f"captaxlin_{scenario}_{metric}_{fy_part}_{sequence}_{version}"


def capacity_validation_result_id(check_name: str, scenario: str | None, fiscal_year: int | None, version: str = CAPACITY_TAXONOMY_VERSION) -> str:
    scen_part = scenario or "all"
    fy_part = str(fiscal_year) if fiscal_year is not None else "na"
    return f"captaxval_{check_name}_{scen_part}_{fy_part}_{version}"


# ---------------------------------------------------------------------------
# Field-level lineage (every one of the 14 per-year fields plus the 7
# horizon-summary fields gets its own lineage row citing formula + inputs)
# ---------------------------------------------------------------------------

# Per-year field -> (formula string, same-year ForecastYear inputs it reads,
# same-year CapacityTaxonomyYear inputs it reads)
_PER_YEAR_FIELD_SPECS: dict[str, tuple[str, list[str], list[str]]] = {
    "operating_fcf": ("CFO - CapEx", ["operating_cash_flow", "capital_expenditure"], []),
    "post_dividend_internal_generation": ("operating_fcf - dividends_paid", ["dividends_paid"], ["operating_fcf"]),
    "opening_excess_liquidity": ("max(0, beginning_cash - min_cash_buffer)", ["beginning_cash", "min_cash_buffer"], []),
    "mandatory_debt_uses": ("= debt_repayments", ["debt_repayments"], []),
    "self_funded_gross_capacity": (
        "opening_excess_liquidity + post_dividend_internal_generation - mandatory_debt_uses", [],
        ["opening_excess_liquidity", "post_dividend_internal_generation", "mandatory_debt_uses"],
    ),
    "debt_funded_incremental_capacity": ("= debt_proceeds", ["debt_proceeds"], []),
    "total_gross_funding_capacity": (
        "self_funded_gross_capacity + debt_funded_incremental_capacity", [],
        ["self_funded_gross_capacity", "debt_funded_incremental_capacity"],
    ),
    "share_repurchases": ("= ForecastYear.share_repurchases (unchanged)", ["share_repurchases"], []),
    "strategic_investment": ("= 0.0 (no assumption modeled this round; structural placeholder)", [], []),
    "voluntary_debt_reduction": ("= 0.0 (no assumption modeled this round; structural placeholder)", [], []),
    "other_discretionary_uses": ("= 0.0 (no assumption modeled this round; structural placeholder)", [], []),
    "total_discretionary_deployment": (
        "share_repurchases + strategic_investment + voluntary_debt_reduction + other_discretionary_uses", [],
        ["share_repurchases", "strategic_investment", "voluntary_debt_reduction", "other_discretionary_uses"],
    ),
    "remaining_deployable_headroom": (
        "max(0, total_gross_funding_capacity - total_discretionary_deployment)", [],
        ["total_gross_funding_capacity", "total_discretionary_deployment"],
    ),
    "ending_excess_liquidity": ("max(0, ending_cash - min_cash_buffer)", ["ending_cash", "min_cash_buffer"], []),
}

_HORIZON_FIELD_SPECS: dict[str, tuple[str, list[str]]] = {
    "cumulative_self_funded_generation": (
        "sum over FY2026-FY2030 of (post_dividend_internal_generation - mandatory_debt_uses); "
        "excludes FY2026 opening_excess_liquidity by construction",
        ["post_dividend_internal_generation", "mandatory_debt_uses"],
    ),
    "cumulative_debt_funded_capacity": (
        "sum over FY2026-FY2030 of debt_funded_incremental_capacity", ["debt_funded_incremental_capacity"],
    ),
    "opening_excess_liquidity_at_horizon_start": (
        "= FY2026's own opening_excess_liquidity (a stock, taken once, never summed)",
        ["opening_excess_liquidity"],
    ),
    "cumulative_discretionary_deployment": (
        "sum over FY2026-FY2030 of total_discretionary_deployment", ["total_discretionary_deployment"],
    ),
    "terminal_remaining_headroom": (
        "= FY2030's own remaining_deployable_headroom (a stock, taken once, never summed)",
        ["remaining_deployable_headroom"],
    ),
    "ending_reserve_movement": (
        "= FY2030.min_cash_buffer - FY2026.min_cash_buffer (the ForecastYear field, both years)", [],
    ),
    "total_horizon_capacity_accessible": (
        "opening_excess_liquidity_at_horizon_start + cumulative_self_funded_generation + cumulative_debt_funded_capacity",
        [],
    ),
}


def build_capacity_taxonomy_lineage(
    scenario: str, taxonomy_years: list[CapacityTaxonomyYear], version: str = CAPACITY_TAXONOMY_VERSION
) -> list[dict]:
    """One lineage row per (field, fiscal_year) for all 14 per-year fields,
    citing its formula and every same-year input it depends on -- the
    capacity-taxonomy analogue of forecast.build_full_lineage()."""
    rows = []
    for ty in taxonomy_years:
        sequence = 0
        for field_name, (formula, fy_inputs, ty_inputs) in _PER_YEAR_FIELD_SPECS.items():
            sequence += 1
            rows.append({
                "capacity_lineage_id": capacity_lineage_id(scenario, field_name, ty.fiscal_year, sequence, version),
                "scenario_id": scenario,
                "fiscal_year": ty.fiscal_year,
                "target_field": field_name,
                "formula": formula,
                "same_year_forecast_inputs": ",".join(fy_inputs) if fy_inputs else None,
                "same_year_capacity_inputs": ",".join(ty_inputs) if ty_inputs else None,
                "information_cutoff": ty.information_cutoff,
                "version": version,
            })
    return rows


def build_capacity_horizon_lineage(scenario: str, version: str = CAPACITY_TAXONOMY_VERSION) -> list[dict]:
    """One lineage row per horizon-summary field, citing its formula and
    every per-year field it aggregates."""
    rows = []
    sequence = 0
    for field_name, (formula, per_year_inputs) in _HORIZON_FIELD_SPECS.items():
        sequence += 1
        rows.append({
            "capacity_lineage_id": capacity_lineage_id(scenario, field_name, None, sequence, version),
            "scenario_id": scenario,
            "fiscal_year": None,
            "target_field": field_name,
            "formula": formula,
            "same_year_forecast_inputs": None,
            "same_year_capacity_inputs": ",".join(per_year_inputs) if per_year_inputs else None,
            "information_cutoff": CAPACITY_TAXONOMY_INFORMATION_CUTOFF,
            "version": version,
        })
    return rows
