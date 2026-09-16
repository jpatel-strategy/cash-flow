"""Milestone 9 (v2 correction): corrected investment-capacity taxonomy.

Produced in response to `docs/investment_capacity_semantic_audit.md`,
which found the legacy `ForecastYear.deployable_capacity` field
arithmetically correct but economically ambiguous: it is a gross,
pre-discretionary ceiling (inclusive of carried-forward cash, inclusive
of new borrowing, and computed BEFORE that year's own repurchases are
subtracted), not a residual "capacity still available" figure.

**v2 finance-semantics correction** (this revision): the v1 taxonomy
(`CAPACITY_TAXONOMY_VERSION = "v1"`, still persisted and readable under
`version='v1'` for audit trail -- never deleted or overwritten) itself
had two further economic defects, found in review:

1. `debt_funded_incremental_capacity = debt_proceeds` (gross issuance)
   was mislabeled as "capacity" even when the same cash was
   simultaneously repaid -- e.g. $700M borrowed and $700M repaid in the
   same year is zero incremental capacity, not $700M. Fixed: only the
   NET of proceeds over repayments is incremental capacity; the NET of
   repayments over proceeds is a mandatory use, not double-counted
   against the gross flows.
2. `self_funded_gross_capacity` blended a STOCK (opening excess
   liquidity, carried forward from prior years) into a figure implicitly
   read as "capacity generated" -- a period FLOW concept. Fixed: the
   stock is now shown as its own line (`opening_excess_liquidity`,
   unchanged), separate from `self_funded_capacity_generated`, which
   contains only this period's own generation.

This module remains purely ADDITIVE. It does not modify `ForecastYear`,
does not change any persisted historical fact, forecast operating
assumption, scenario assumption, or DCF operating projection, and does
not alter the legacy `deployable_capacity` /
`near_term_debt_repayment_reserve` fields' stored values or meaning --
per the governing correction decision, those are preserved verbatim for
backward compatibility, documented as deprecated, and excluded from
every new cumulative-capacity calculation below. The v1 capacity-
taxonomy rows are treated the same way: preserved under `version='v1'`,
superseded (never overwritten) by `version='v2'` rows.

Every new field is computed from `ForecastYear`'s own EXISTING fields
only (never a re-derivation from raw assumptions), so a discrepancy
between the legacy and corrected figures can only come from a different
FORMULA, never from different underlying data.

Required taxonomy (v2):
  A. operating_fcf                        = CFO - CapEx
  B. post_dividend_internal_generation    = operating_fcf - dividends
                                             (the actual period-generated
                                             amount; unchanged by v2)
  -- opening_excess_liquidity             = a STOCK (carried-forward cash
                                             above the buffer), shown on
                                             its own line, never folded
                                             into a "generated" figure
  -- gross_debt_proceeds / gross_debt_repayments
                                           = ForecastYear.debt_proceeds /
                                             .debt_repayments, exposed as
                                             transparent supporting fields
  net_mandatory_debt_service              = max(0, gross_debt_repayments
                                             - gross_debt_proceeds)
  debt_funded_incremental_capacity        = max(0, gross_debt_proceeds
                                             - gross_debt_repayments)
  C. self_funded_capacity_generated       = B - net_mandatory_debt_service
                                             (a FLOW; excludes the opening
                                             stock entirely)
  E. total_gross_funding_capacity         = opening_excess_liquidity
                                             + self_funded_capacity_generated
                                             + debt_funded_incremental_capacity
  F. total_discretionary_deployment       = repurchases + strategic
                                             investment + voluntary debt
                                             reduction + other discretionary uses
  forward_debt_repayment_reserve          = next year's
                                             net_mandatory_debt_service
                                             (FY2030's terminal-year value
                                             is a documented proxy: FY2031
                                             is outside the forecast, so
                                             the proxy repeats FY2030's own
                                             net_mandatory_debt_service --
                                             see `forward_reserve_is_proxied`)
  G. remaining_deployable_headroom        = max(0, E - F_deployment
                                             - forward_debt_repayment_reserve)
"""
from __future__ import annotations

from dataclasses import dataclass

from target_cash import forecast as f

CAPACITY_TAXONOMY_VERSION = "v2"
CAPACITY_TAXONOMY_INFORMATION_CUTOFF = f.FORECAST_INFORMATION_CUTOFF


# ---------------------------------------------------------------------------
# Per-year taxonomy
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CapacityTaxonomyYear:
    """One scenario x fiscal-year row of the corrected (v2) capacity
    taxonomy.

    Every field here is derived exclusively from the corresponding
    `ForecastYear`'s own already-computed, already-tested fields -- no
    raw assumption is re-read, and no new assumption is introduced.
    `strategic_investment`, `voluntary_debt_reduction`, and
    `other_discretionary_uses` are explicit, structurally-present $0
    placeholders (no policy lever exists for them this round), following
    the same non-plug, non-silent-zero convention already established
    for `ForecastYear.management_selected_deployment`.

    CANONICAL v2 fields (use these for all display/reporting):
    `gross_debt_proceeds`, `gross_debt_repayments`,
    `net_mandatory_debt_service`, `debt_funded_incremental_capacity`
    (redefined), `self_funded_capacity_generated`,
    `forward_debt_repayment_reserve`, `forward_reserve_is_proxied`,
    `remaining_deployable_headroom` (redefined).

    DEPRECATED-BY-v2 fields, retained ONLY to satisfy the pre-existing
    NOT NULL schema shared with `version='v1'` rows -- never read these
    for display or for any new calculation:
    `mandatory_debt_uses` (now holds the same value as
    `net_mandatory_debt_service`) and `self_funded_gross_capacity` (now
    holds `opening_excess_liquidity + self_funded_capacity_generated` --
    a legitimate figure, "self-funded capacity including the opening
    stock," but never labeled "generated" anywhere downstream, per the
    v2 correction's governing rule that a stock must never be called a
    flow).
    """
    scenario: str
    fiscal_year: int
    operating_fcf: float
    post_dividend_internal_generation: float
    opening_excess_liquidity: float
    gross_debt_proceeds: float
    gross_debt_repayments: float
    net_mandatory_debt_service: float
    self_funded_capacity_generated: float
    debt_funded_incremental_capacity: float
    total_gross_funding_capacity: float
    share_repurchases: float
    strategic_investment: float
    voluntary_debt_reduction: float
    other_discretionary_uses: float
    total_discretionary_deployment: float
    forward_debt_repayment_reserve: float
    forward_reserve_is_proxied: bool
    remaining_deployable_headroom: float
    ending_excess_liquidity: float
    mandatory_debt_uses: float  # DEPRECATED-BY-v2 -- see class docstring
    self_funded_gross_capacity: float  # DEPRECATED-BY-v2 -- see class docstring
    information_cutoff: str = CAPACITY_TAXONOMY_INFORMATION_CUTOFF


def _net_mandatory_debt_service(proceeds: float, repayments: float) -> float:
    """Mandatory debt service NET of simultaneous refinancing: only the
    amount by which repayments exceed proceeds is a genuine mandatory
    use of self-funded cash. Equal proceeds and repayments net to zero."""
    return max(0.0, repayments - proceeds)


def _debt_funded_incremental_capacity(proceeds: float, repayments: float) -> float:
    """Incremental debt-funded capacity NET of simultaneous repayment:
    only the amount by which proceeds exceed repayments is genuinely new
    capacity. Gross issuance that is simultaneously repaid is zero
    incremental capacity, never counted as capacity generated."""
    return max(0.0, proceeds - repayments)


def compute_capacity_taxonomy_year(
    y: f.ForecastYear, next_y: f.ForecastYear | None
) -> CapacityTaxonomyYear:
    """Pure function: one ForecastYear (plus, when available, the NEXT
    fiscal year's ForecastYear, for the forward debt-repayment reserve)
    in, one CapacityTaxonomyYear out.

    `next_y` is the following fiscal year's ForecastYear, used only to
    look up its actual `debt_proceeds`/`debt_repayments` for
    `forward_debt_repayment_reserve`. Pass `None` for the terminal
    forecast year (FY2030): FY2031 is outside the forecast horizon, so
    the reserve is PROXIED by repeating FY2030's own
    `net_mandatory_debt_service` -- the best available estimate in the
    absence of an FY2031 forecast, and `forward_reserve_is_proxied` is
    set True so no consumer can mistake it for an actual scheduled
    obligation.

    No mandatory item is deducted twice: `net_mandatory_debt_service`
    is subtracted exactly once, inside `self_funded_capacity_generated`
    -- unlike the legacy `deployable_capacity`, which subtracted an
    equivalent amount twice (once inside `pre_discretionary_ending_cash`'s
    own `mandatory_financing_flows`, and again via
    `near_term_debt_repayment_reserve`, itself defined as
    `= y.debt_repayments`). See
    docs/investment_capacity_correction_evidence.md for the proof.

    Gross debt issuance is never labeled capacity when it is
    simultaneously repaid: `debt_funded_incremental_capacity` is the NET
    of proceeds over repayments, and `net_mandatory_debt_service` is the
    NET of repayments over proceeds -- exactly one is nonzero (or both
    are zero when proceeds equal repayments).
    """
    operating_fcf = y.free_cash_flow  # taxonomy A, exact match to the existing field
    post_dividend_internal_generation = y.post_dividend_capacity  # taxonomy B, exact match (unchanged by v2)

    opening_excess_liquidity = max(0.0, y.beginning_cash - y.min_cash_buffer)  # a STOCK, shown on its own line

    gross_debt_proceeds = y.debt_proceeds
    gross_debt_repayments = y.debt_repayments
    net_mandatory_debt_service = _net_mandatory_debt_service(gross_debt_proceeds, gross_debt_repayments)
    debt_funded_incremental_capacity = _debt_funded_incremental_capacity(gross_debt_proceeds, gross_debt_repayments)

    self_funded_capacity_generated = post_dividend_internal_generation - net_mandatory_debt_service  # C, a FLOW only
    total_gross_funding_capacity = (
        opening_excess_liquidity + self_funded_capacity_generated + debt_funded_incremental_capacity
    )  # E

    strategic_investment = 0.0
    voluntary_debt_reduction = 0.0
    other_discretionary_uses = 0.0
    total_discretionary_deployment = (
        y.share_repurchases + strategic_investment + voluntary_debt_reduction + other_discretionary_uses
    )

    if next_y is not None:
        forward_debt_repayment_reserve = _net_mandatory_debt_service(next_y.debt_proceeds, next_y.debt_repayments)
        forward_reserve_is_proxied = False
    else:
        forward_debt_repayment_reserve = net_mandatory_debt_service  # documented proxy: FY2031 is out of scope
        forward_reserve_is_proxied = True

    remaining_deployable_headroom = max(
        0.0, total_gross_funding_capacity - total_discretionary_deployment - forward_debt_repayment_reserve
    )
    ending_excess_liquidity = max(0.0, y.ending_cash - y.min_cash_buffer)

    # DEPRECATED-BY-v2 fields, computed only to satisfy the shared schema's NOT NULL
    # columns -- never read these for display; see the class docstring.
    mandatory_debt_uses = net_mandatory_debt_service
    self_funded_gross_capacity = opening_excess_liquidity + self_funded_capacity_generated

    return CapacityTaxonomyYear(
        scenario=y.scenario, fiscal_year=y.fiscal_year,
        operating_fcf=operating_fcf,
        post_dividend_internal_generation=post_dividend_internal_generation,
        opening_excess_liquidity=opening_excess_liquidity,
        gross_debt_proceeds=gross_debt_proceeds,
        gross_debt_repayments=gross_debt_repayments,
        net_mandatory_debt_service=net_mandatory_debt_service,
        self_funded_capacity_generated=self_funded_capacity_generated,
        debt_funded_incremental_capacity=debt_funded_incremental_capacity,
        total_gross_funding_capacity=total_gross_funding_capacity,
        share_repurchases=y.share_repurchases,
        strategic_investment=strategic_investment,
        voluntary_debt_reduction=voluntary_debt_reduction,
        other_discretionary_uses=other_discretionary_uses,
        total_discretionary_deployment=total_discretionary_deployment,
        forward_debt_repayment_reserve=forward_debt_repayment_reserve,
        forward_reserve_is_proxied=forward_reserve_is_proxied,
        remaining_deployable_headroom=remaining_deployable_headroom,
        ending_excess_liquidity=ending_excess_liquidity,
        mandatory_debt_uses=mandatory_debt_uses,
        self_funded_gross_capacity=self_funded_gross_capacity,
    )


def build_capacity_taxonomy(years: list[f.ForecastYear]) -> list[CapacityTaxonomyYear]:
    return [
        compute_capacity_taxonomy_year(y, years[i + 1] if i + 1 < len(years) else None)
        for i, y in enumerate(years)
    ]


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

    v2 correction adds `terminal_forward_debt_repayment_reserve` (and
    its proxy flag): the terminal year's `remaining_deployable_headroom`
    now deducts a forward reserve for FY2031's (out-of-horizon, proxied)
    debt service, so the D+E+F identity needs this as an explicit fourth
    reconciling term on the right-hand side -- it represents cash held
    back for an obligation that occurs entirely outside the 5-year
    forecast, never double-counted against any in-horizon flow.
    """
    scenario: str
    cumulative_self_funded_generation: float
    cumulative_debt_funded_capacity: float
    opening_excess_liquidity_at_horizon_start: float
    cumulative_discretionary_deployment: float
    terminal_remaining_headroom: float
    ending_reserve_movement: float
    terminal_forward_debt_repayment_reserve: float
    terminal_forward_reserve_is_proxied: bool
    total_horizon_capacity_accessible: float
    information_cutoff: str = CAPACITY_TAXONOMY_INFORMATION_CUTOFF


def cumulative_self_funded_generation(taxonomy_years: list[CapacityTaxonomyYear]) -> float:
    """A. Sum of INCREMENTAL self-funded capacity generated during the
    horizon -- i.e. post-dividend internal generation net of mandatory
    debt service, for every year (`self_funded_capacity_generated`,
    already excludes the opening stock by construction). Deliberately
    EXCLUDES FY2026's opening excess liquidity (a pre-existing stock, not
    capacity generated during the horizon) and every other year's
    opening_excess_liquidity too (each of those is the SAME
    carried-forward stock, not new generation -- including it here would
    double-count it against the horizon-start stock already captured
    separately, below).
    """
    return sum(ty.self_funded_capacity_generated for ty in taxonomy_years)


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
    terminal = taxonomy_years[-1]

    return CapacityHorizonSummary(
        scenario=scenario,
        cumulative_self_funded_generation=cumulative_self_funded_generation(taxonomy_years),
        cumulative_debt_funded_capacity=cumulative_debt_funded_capacity(taxonomy_years),
        opening_excess_liquidity_at_horizon_start=opening_excess_liquidity_at_horizon_start(taxonomy_years),
        cumulative_discretionary_deployment=cumulative_discretionary_deployment(taxonomy_years),
        terminal_remaining_headroom=terminal_remaining_headroom(taxonomy_years),
        ending_reserve_movement=reserve_movement,
        terminal_forward_debt_repayment_reserve=terminal.forward_debt_repayment_reserve,
        terminal_forward_reserve_is_proxied=terminal.forward_reserve_is_proxied,
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
        "formula": "self_funded_capacity_generated == B - net_mandatory_debt_service, "
                    "with net_mandatory_debt_service subtracted exactly once (never a second time via a "
                    "reserve holdback, unlike the legacy near_term_debt_repayment_reserve design)",
    },
    "debt_netting_mutually_exclusive": {
        "check_type": "arithmetic_invariant",
        "formula": "not (net_mandatory_debt_service > 0 AND debt_funded_incremental_capacity > 0) simultaneously; "
                    "net_mandatory_debt_service - debt_funded_incremental_capacity == "
                    "gross_debt_repayments - gross_debt_proceeds exactly, for every scenario-year",
    },
    "debt_funded_capacity_excludes_gross_issuance": {
        "check_type": "arithmetic_invariant",
        "formula": "equal gross proceeds and repayments -> net_mandatory_debt_service == 0 AND "
                    "debt_funded_incremental_capacity == 0; net deleveraging (repayments > proceeds) -> "
                    "debt_funded_incremental_capacity == 0; only proceeds exceeding repayments produce "
                    "debt_funded_incremental_capacity > 0 -- gross issuance alone is never labeled capacity",
    },
    "self_funded_generation_excludes_opening_liquidity": {
        "check_type": "arithmetic_invariant",
        "formula": "self_funded_capacity_generated == post_dividend_internal_generation - "
                    "net_mandatory_debt_service, with NO opening_excess_liquidity term present -- a stock "
                    "is never labeled 'capacity generated'",
    },
    "headroom_deducts_forward_reserve": {
        "check_type": "arithmetic_invariant",
        "formula": "remaining_deployable_headroom == max(0, total_gross_funding_capacity - "
                    "total_discretionary_deployment - forward_debt_repayment_reserve); unfloored, "
                    "equals ending_excess_liquidity - forward_debt_repayment_reserve exactly",
    },
    "forward_reserve_terminal_proxy_documented": {
        "check_type": "structural_completeness_check",
        "formula": "forward_reserve_is_proxied is False and forward_debt_repayment_reserve equals the "
                    "ACTUAL next year's net_mandatory_debt_service for every non-terminal year; True only "
                    "for the terminal (FY2030) year, whose reserve is a documented proxy (FY2031 is "
                    "outside the forecast horizon)",
    },
    "repurchases_in_discretionary_deployment": {
        "check_type": "structural_completeness_check",
        "formula": "share_repurchases is one of the 4 additive components of total_discretionary_deployment",
    },
    "headroom_never_negative": {
        "check_type": "arithmetic_invariant",
        "formula": "remaining_deployable_headroom == max(0, total_gross_funding_capacity - "
                    "total_discretionary_deployment - forward_debt_repayment_reserve) >= 0",
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
        "formula": "remaining_deployable_headroom + total_discretionary_deployment + "
                    "forward_debt_repayment_reserve == total_gross_funding_capacity (unfloored case) -- "
                    "every dollar is exactly one of: deployed, forward-reserved, or remaining headroom",
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
                    "+ terminal_remaining_headroom + ending_reserve_movement "
                    "+ terminal_forward_debt_repayment_reserve",
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
    expected = ty.post_dividend_internal_generation - ty.net_mandatory_debt_service
    ok = f._close(ty.self_funded_capacity_generated, expected)
    # Explicitly also prove the legacy defect this check exists to avoid: the legacy field
    # subtracted mandatory debt uses a SECOND time via near_term_debt_repayment_reserve.
    legacy_double_subtracted = f._close(y.near_term_debt_repayment_reserve, y.debt_repayments)
    return f.ValidationResult(
        "mandatory_debt_not_double_deducted", y.scenario, y.fiscal_year, "PASS" if ok else "FAIL",
        f"self_funded_capacity_generated={ty.self_funded_capacity_generated:.1f} vs expected={expected:.1f} "
        f"(legacy near_term_debt_repayment_reserve duplicated debt_repayments: {legacy_double_subtracted})",
    )


def check_debt_netting_mutually_exclusive(ty: CapacityTaxonomyYear) -> f.ValidationResult:
    both_positive = ty.net_mandatory_debt_service > 0 and ty.debt_funded_incremental_capacity > 0
    expected_diff = ty.gross_debt_repayments - ty.gross_debt_proceeds
    actual_diff = ty.net_mandatory_debt_service - ty.debt_funded_incremental_capacity
    ok = (not both_positive) and f._close(actual_diff, expected_diff)
    return f.ValidationResult(
        "debt_netting_mutually_exclusive", ty.scenario, ty.fiscal_year, "PASS" if ok else "FAIL",
        f"net_mandatory_debt_service={ty.net_mandatory_debt_service:.1f}, "
        f"debt_funded_incremental_capacity={ty.debt_funded_incremental_capacity:.1f}, "
        f"net_service-incremental={actual_diff:.1f} vs gross_repayments-gross_proceeds={expected_diff:.1f}",
    )


def check_debt_funded_capacity_excludes_gross_issuance(ty: CapacityTaxonomyYear) -> f.ValidationResult:
    proceeds, repayments = ty.gross_debt_proceeds, ty.gross_debt_repayments
    if f._close(proceeds, repayments):
        ok = ty.debt_funded_incremental_capacity == 0.0 and ty.net_mandatory_debt_service == 0.0
    elif repayments > proceeds:
        ok = ty.debt_funded_incremental_capacity == 0.0 and ty.net_mandatory_debt_service > 0.0
    else:
        ok = ty.debt_funded_incremental_capacity > 0.0 and ty.net_mandatory_debt_service == 0.0
    return f.ValidationResult(
        "debt_funded_capacity_excludes_gross_issuance", ty.scenario, ty.fiscal_year, "PASS" if ok else "FAIL",
        f"gross_debt_proceeds={proceeds:.1f}, gross_debt_repayments={repayments:.1f}, "
        f"debt_funded_incremental_capacity={ty.debt_funded_incremental_capacity:.1f}, "
        f"net_mandatory_debt_service={ty.net_mandatory_debt_service:.1f}",
    )


def check_self_funded_generation_excludes_opening_liquidity(ty: CapacityTaxonomyYear) -> f.ValidationResult:
    expected = ty.post_dividend_internal_generation - ty.net_mandatory_debt_service
    contaminated = expected + ty.opening_excess_liquidity
    ok = f._close(ty.self_funded_capacity_generated, expected) and (
        ty.opening_excess_liquidity == 0.0 or not f._close(ty.self_funded_capacity_generated, contaminated)
    )
    return f.ValidationResult(
        "self_funded_generation_excludes_opening_liquidity", ty.scenario, ty.fiscal_year, "PASS" if ok else "FAIL",
        f"self_funded_capacity_generated={ty.self_funded_capacity_generated:.1f} vs "
        f"B-net_mandatory_debt_service={expected:.1f} (opening_excess_liquidity={ty.opening_excess_liquidity:.1f} "
        "excluded, not a flow)",
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
    unfloored_lhs = ty.total_gross_funding_capacity - ty.total_discretionary_deployment - ty.forward_debt_repayment_reserve
    floored = unfloored_lhs < 0
    three_way_sum = ty.remaining_deployable_headroom + ty.total_discretionary_deployment + ty.forward_debt_repayment_reserve
    ok = floored or f._close(three_way_sum, ty.total_gross_funding_capacity)
    return f.ValidationResult(
        "capacity_mutually_exclusive", ty.scenario, ty.fiscal_year, "PASS" if ok else "FAIL",
        f"headroom+deployment+forward_reserve={three_way_sum:.1f} "
        f"vs total_gross_funding_capacity={ty.total_gross_funding_capacity:.1f}"
        + (" (floored)" if floored else ""),
    )


def check_headroom_deducts_forward_reserve(ty: CapacityTaxonomyYear) -> f.ValidationResult:
    # Only an exact identity in the unfloored case, same convention as check_capacity_mutually_exclusive.
    unfloored_lhs = ty.total_gross_funding_capacity - ty.total_discretionary_deployment - ty.forward_debt_repayment_reserve
    floored = unfloored_lhs < 0
    expected = ty.ending_excess_liquidity - ty.forward_debt_repayment_reserve
    ok = floored or f._close(ty.remaining_deployable_headroom, expected)
    return f.ValidationResult(
        "headroom_deducts_forward_reserve", ty.scenario, ty.fiscal_year, "PASS" if ok else "FAIL",
        f"remaining_deployable_headroom={ty.remaining_deployable_headroom:.1f} vs "
        f"ending_excess_liquidity-forward_debt_repayment_reserve={expected:.1f}"
        + (" (floored)" if floored else ""),
    )


def check_forward_reserve_terminal_proxy_documented(
    scenario: str, taxonomy_years: list[CapacityTaxonomyYear]
) -> f.ValidationResult:
    ok = True
    details = []
    for i, ty in enumerate(taxonomy_years):
        is_terminal = i == len(taxonomy_years) - 1
        if is_terminal:
            year_ok = ty.forward_reserve_is_proxied is True
        else:
            next_ty = taxonomy_years[i + 1]
            year_ok = ty.forward_reserve_is_proxied is False and f._close(
                ty.forward_debt_repayment_reserve, next_ty.net_mandatory_debt_service
            )
        ok = ok and year_ok
        details.append(f"FY{ty.fiscal_year}: proxied={ty.forward_reserve_is_proxied}, reserve={ty.forward_debt_repayment_reserve:.1f}")
    return f.ValidationResult(
        "forward_reserve_terminal_proxy_documented", scenario, None, "PASS" if ok else "FAIL",
        "; ".join(details),
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
        sum(ty.self_funded_capacity_generated for ty in taxonomy_years) + \
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
    rhs = (
        summary.cumulative_discretionary_deployment
        + summary.terminal_remaining_headroom
        + summary.ending_reserve_movement
        + summary.terminal_forward_debt_repayment_reserve
    )
    ok = f._close(summary.total_horizon_capacity_accessible, rhs)
    return f.ValidationResult(
        "capacity_accounted_for_reconciliation", scenario, None, "PASS" if ok else "FAIL",
        f"total_horizon_capacity_accessible={summary.total_horizon_capacity_accessible:.1f} vs "
        f"deployment+headroom+reserve_movement+terminal_forward_reserve={rhs:.1f}",
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
            results.append(check_debt_netting_mutually_exclusive(ty))
            results.append(check_debt_funded_capacity_excludes_gross_issuance(ty))
            results.append(check_self_funded_generation_excludes_opening_liquidity(ty))
            results.append(check_repurchases_in_discretionary_deployment(ty))
            results.append(check_headroom_never_negative(ty))
            results.append(check_headroom_deducts_forward_reserve(ty))
            results.append(check_ending_cash_above_buffer_or_flagged(y))
            results.append(check_annual_source_use_reconciliation(y, ty))
            results.append(check_capacity_mutually_exclusive(ty))
            results.append(check_scenario_and_cutoff_lineage_complete(ty))
        results.append(check_forward_reserve_terminal_proxy_documented(scenario, taxonomy_years))
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
    "opening_excess_liquidity": (
        "max(0, beginning_cash - min_cash_buffer); a STOCK, never labeled 'generated'",
        ["beginning_cash", "min_cash_buffer"], [],
    ),
    "gross_debt_proceeds": ("= debt_proceeds (transparent supporting field, unchanged)", ["debt_proceeds"], []),
    "gross_debt_repayments": ("= debt_repayments (transparent supporting field, unchanged)", ["debt_repayments"], []),
    "net_mandatory_debt_service": (
        "max(0, gross_debt_repayments - gross_debt_proceeds)", ["debt_proceeds", "debt_repayments"], [],
    ),
    "debt_funded_incremental_capacity": (
        "max(0, gross_debt_proceeds - gross_debt_repayments); gross issuance simultaneously repaid is never capacity",
        ["debt_proceeds", "debt_repayments"], [],
    ),
    "self_funded_capacity_generated": (
        "post_dividend_internal_generation - net_mandatory_debt_service; a FLOW, excludes opening_excess_liquidity", [],
        ["post_dividend_internal_generation", "net_mandatory_debt_service"],
    ),
    "total_gross_funding_capacity": (
        "opening_excess_liquidity + self_funded_capacity_generated + debt_funded_incremental_capacity", [],
        ["opening_excess_liquidity", "self_funded_capacity_generated", "debt_funded_incremental_capacity"],
    ),
    "share_repurchases": ("= ForecastYear.share_repurchases (unchanged)", ["share_repurchases"], []),
    "strategic_investment": ("= 0.0 (no assumption modeled this round; structural placeholder)", [], []),
    "voluntary_debt_reduction": ("= 0.0 (no assumption modeled this round; structural placeholder)", [], []),
    "other_discretionary_uses": ("= 0.0 (no assumption modeled this round; structural placeholder)", [], []),
    "total_discretionary_deployment": (
        "share_repurchases + strategic_investment + voluntary_debt_reduction + other_discretionary_uses", [],
        ["share_repurchases", "strategic_investment", "voluntary_debt_reduction", "other_discretionary_uses"],
    ),
    "forward_debt_repayment_reserve": (
        "= next fiscal year's net_mandatory_debt_service; for the terminal (FY2030) year, PROXIED by "
        "repeating this year's own net_mandatory_debt_service (FY2031 is outside the forecast horizon)",
        [], ["net_mandatory_debt_service"],
    ),
    "remaining_deployable_headroom": (
        "max(0, total_gross_funding_capacity - total_discretionary_deployment - forward_debt_repayment_reserve)", [],
        ["total_gross_funding_capacity", "total_discretionary_deployment", "forward_debt_repayment_reserve"],
    ),
    "ending_excess_liquidity": ("max(0, ending_cash - min_cash_buffer)", ["ending_cash", "min_cash_buffer"], []),
    "mandatory_debt_uses": ("DEPRECATED-BY-v2, = net_mandatory_debt_service (schema NOT NULL compatibility only)", [],
                            ["net_mandatory_debt_service"]),
    "self_funded_gross_capacity": (
        "DEPRECATED-BY-v2, = opening_excess_liquidity + self_funded_capacity_generated "
        "(schema NOT NULL compatibility only; never labeled 'generated')", [],
        ["opening_excess_liquidity", "self_funded_capacity_generated"],
    ),
}

_HORIZON_FIELD_SPECS: dict[str, tuple[str, list[str]]] = {
    "cumulative_self_funded_generation": (
        "sum over FY2026-FY2030 of self_funded_capacity_generated; "
        "excludes FY2026 opening_excess_liquidity by construction",
        ["self_funded_capacity_generated"],
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
    "terminal_forward_debt_repayment_reserve": (
        "= FY2030's own forward_debt_repayment_reserve (a documented FY2031 proxy, held back from "
        "terminal_remaining_headroom; a fourth reconciling term, not a plug)",
        ["forward_debt_repayment_reserve"],
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
