"""Milestone 9 correction: transactional, idempotent persistence of the
corrected investment-capacity taxonomy (src/target_cash/capacity_taxonomy.py)
into the additive schema added by migrations 0025-0028 (v1 tables) and
0029-0036 (v2 finance-semantics correction columns).

Mirrors forecast_persistence.py's design discipline exactly: a preflight
plan computed from pure in-memory target_cash.capacity_taxonomy functions,
a hard authorization gate (zero FAIL among the persisted capacity
validation checks -- WARNING is allowed), one atomic transaction,
deterministic IDs for true idempotency, and a post-write integrity check.

Requires forecast_scenarios to already be populated (via
`persist-forecast`) -- every new table here has a foreign key to it.
Nothing here touches annual_facts, forecast_facts, valuation_results, or
any other existing table; nothing here reads or writes the legacy
`investment_capacity_results` table at all.
"""
from __future__ import annotations

import hashlib
import sqlite3
import time
from dataclasses import dataclass, field

from target_cash import forecast as f
from target_cash import capacity_taxonomy as ct

CAPACITY_MODEL_VERSION = ct.CAPACITY_TAXONOMY_VERSION


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class CapacityPersistencePreflight:
    version: str
    capacity_results: list[dict] = field(default_factory=list)
    horizon_results: list[dict] = field(default_factory=list)
    lineage: list[dict] = field(default_factory=list)
    validation_results: list[dict] = field(default_factory=list)
    validation_failures: list = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "capacity_taxonomy_results": len(self.capacity_results),
            "capacity_horizon_results": len(self.horizon_results),
            "capacity_taxonomy_lineage": len(self.lineage),
            "capacity_validation_results": len(self.validation_results),
            "validation_failures": len(self.validation_failures),
        }

    def is_authorized(self) -> bool:
        return len(self.validation_failures) == 0


def compute_capacity_preflight(version: str = CAPACITY_MODEL_VERSION) -> CapacityPersistencePreflight:
    """Builds the complete, deterministic persistence plan from pure
    in-memory computation -- never a partial recomputation, never reads
    or writes the database itself.
    """
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    taxonomies = ct.build_capacity_taxonomy_all_scenarios(forecasts)
    summaries = ct.build_capacity_horizon_summaries(forecasts, taxonomies)
    validation_results = ct.validate_capacity_taxonomy_all(forecasts, taxonomies, summaries)
    validation_failures = [r for r in validation_results if r.status == "FAIL"]

    now = _now()
    pre = CapacityPersistencePreflight(version=version)

    for scenario, taxonomy_years in taxonomies.items():
        for ty in taxonomy_years:
            pre.capacity_results.append({
                "capacity_taxonomy_result_id": ct.capacity_taxonomy_result_id(scenario, ty.fiscal_year, version),
                "scenario_id": scenario, "fiscal_year": ty.fiscal_year,
                "operating_fcf": ty.operating_fcf,
                "post_dividend_internal_generation": ty.post_dividend_internal_generation,
                "opening_excess_liquidity": ty.opening_excess_liquidity,
                "mandatory_debt_uses": ty.mandatory_debt_uses,
                "self_funded_gross_capacity": ty.self_funded_gross_capacity,
                "gross_debt_proceeds": ty.gross_debt_proceeds,
                "gross_debt_repayments": ty.gross_debt_repayments,
                "net_mandatory_debt_service": ty.net_mandatory_debt_service,
                "self_funded_capacity_generated": ty.self_funded_capacity_generated,
                "debt_funded_incremental_capacity": ty.debt_funded_incremental_capacity,
                "total_gross_funding_capacity": ty.total_gross_funding_capacity,
                "share_repurchases": ty.share_repurchases,
                "strategic_investment": ty.strategic_investment,
                "voluntary_debt_reduction": ty.voluntary_debt_reduction,
                "other_discretionary_uses": ty.other_discretionary_uses,
                "total_discretionary_deployment": ty.total_discretionary_deployment,
                "forward_debt_repayment_reserve": ty.forward_debt_repayment_reserve,
                "forward_reserve_is_proxied": int(ty.forward_reserve_is_proxied),
                "remaining_deployable_headroom": ty.remaining_deployable_headroom,
                "ending_excess_liquidity": ty.ending_excess_liquidity,
                "version": version, "information_cutoff": ty.information_cutoff,
            })

    for scenario, summary in summaries.items():
        pre.horizon_results.append({
            "capacity_horizon_result_id": ct.capacity_horizon_result_id(scenario, version),
            "scenario_id": scenario,
            "cumulative_self_funded_generation": summary.cumulative_self_funded_generation,
            "cumulative_debt_funded_capacity": summary.cumulative_debt_funded_capacity,
            "opening_excess_liquidity_at_horizon_start": summary.opening_excess_liquidity_at_horizon_start,
            "cumulative_discretionary_deployment": summary.cumulative_discretionary_deployment,
            "terminal_remaining_headroom": summary.terminal_remaining_headroom,
            "ending_reserve_movement": summary.ending_reserve_movement,
            "terminal_forward_debt_repayment_reserve": summary.terminal_forward_debt_repayment_reserve,
            "terminal_forward_reserve_is_proxied": int(summary.terminal_forward_reserve_is_proxied),
            # Persisted under the legacy column name (backward-compatible, additive-only migration
            # framework cannot safely rename a column) -- display layers relabel this
            # "Gross Horizon Funding (Before Reserve Adjustments)", never "net accessible capacity".
            "total_horizon_capacity_accessible": summary.gross_horizon_funding_before_reserve_adjustments,
            "net_horizon_deployable_capacity": summary.net_horizon_deployable_capacity,
            "version": version, "information_cutoff": summary.information_cutoff,
        })

    for scenario, taxonomy_years in taxonomies.items():
        for row in ct.build_capacity_taxonomy_lineage(scenario, taxonomy_years, version):
            pre.lineage.append(row)
        for row in ct.build_capacity_horizon_lineage(scenario, version):
            pre.lineage.append(row)

    for r in validation_results:
        pre.validation_results.append({
            "capacity_validation_result_id": ct.capacity_validation_result_id(r.check_name, r.scenario, r.fiscal_year, version),
            "check_name": r.check_name, "scenario_id": r.scenario, "fiscal_year": r.fiscal_year,
            "status": r.status, "detail": r.detail, "capacity_version": version, "run_at": now,
        })

    pre.validation_failures = validation_failures
    return pre


class CapacityPersistenceNotAuthorizedError(RuntimeError):
    pass


class CapacityPersistencePrerequisiteError(RuntimeError):
    pass


def persist_capacity_taxonomy(conn: sqlite3.Connection, preflight: CapacityPersistencePreflight) -> dict:
    """Writes preflight's exact plan into the 4 capacity_* tables as ONE
    atomic transaction. Refuses if any capacity validation check failed,
    or if forecast_scenarios is not yet populated (this schema's foreign-
    key prerequisite). Idempotent: deterministic IDs + ON CONFLICT DO
    UPDATE mean a repeated call with the same preflight plan converges to
    the identical final state.
    """
    if not preflight.is_authorized():
        raise CapacityPersistenceNotAuthorizedError(
            f"Capacity taxonomy persistence refused: {len(preflight.validation_failures)} validation "
            f"check(s) failed: {[r.check_name for r in preflight.validation_failures]}. Fix the "
            "underlying problem before persisting -- do not bypass this gate."
        )

    scenario_count = conn.execute("SELECT COUNT(*) FROM forecast_scenarios").fetchone()[0]
    if scenario_count == 0:
        raise CapacityPersistencePrerequisiteError(
            "forecast_scenarios is empty -- run `persist-forecast` before `persist-capacity-taxonomy` "
            "(every capacity_* table has a foreign key to forecast_scenarios)."
        )

    written = {k: 0 for k in (
        "capacity_taxonomy_results", "capacity_horizon_results",
        "capacity_taxonomy_lineage", "capacity_validation_results",
    )}
    try:
        conn.execute("BEGIN")

        for row in preflight.capacity_results:
            conn.execute(
                """
                INSERT INTO capacity_taxonomy_results
                    (capacity_taxonomy_result_id, scenario_id, fiscal_year, operating_fcf,
                     post_dividend_internal_generation, opening_excess_liquidity, mandatory_debt_uses,
                     self_funded_gross_capacity, gross_debt_proceeds, gross_debt_repayments,
                     net_mandatory_debt_service, self_funded_capacity_generated,
                     debt_funded_incremental_capacity, total_gross_funding_capacity,
                     share_repurchases, strategic_investment, voluntary_debt_reduction, other_discretionary_uses,
                     total_discretionary_deployment, forward_debt_repayment_reserve, forward_reserve_is_proxied,
                     remaining_deployable_headroom, ending_excess_liquidity,
                     version, information_cutoff)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(capacity_taxonomy_result_id) DO UPDATE SET
                    operating_fcf=excluded.operating_fcf,
                    post_dividend_internal_generation=excluded.post_dividend_internal_generation,
                    opening_excess_liquidity=excluded.opening_excess_liquidity,
                    mandatory_debt_uses=excluded.mandatory_debt_uses,
                    self_funded_gross_capacity=excluded.self_funded_gross_capacity,
                    gross_debt_proceeds=excluded.gross_debt_proceeds,
                    gross_debt_repayments=excluded.gross_debt_repayments,
                    net_mandatory_debt_service=excluded.net_mandatory_debt_service,
                    self_funded_capacity_generated=excluded.self_funded_capacity_generated,
                    debt_funded_incremental_capacity=excluded.debt_funded_incremental_capacity,
                    total_gross_funding_capacity=excluded.total_gross_funding_capacity,
                    share_repurchases=excluded.share_repurchases,
                    strategic_investment=excluded.strategic_investment,
                    voluntary_debt_reduction=excluded.voluntary_debt_reduction,
                    other_discretionary_uses=excluded.other_discretionary_uses,
                    total_discretionary_deployment=excluded.total_discretionary_deployment,
                    forward_debt_repayment_reserve=excluded.forward_debt_repayment_reserve,
                    forward_reserve_is_proxied=excluded.forward_reserve_is_proxied,
                    remaining_deployable_headroom=excluded.remaining_deployable_headroom,
                    ending_excess_liquidity=excluded.ending_excess_liquidity
                """,
                (row["capacity_taxonomy_result_id"], row["scenario_id"], row["fiscal_year"], row["operating_fcf"],
                 row["post_dividend_internal_generation"], row["opening_excess_liquidity"], row["mandatory_debt_uses"],
                 row["self_funded_gross_capacity"], row["gross_debt_proceeds"], row["gross_debt_repayments"],
                 row["net_mandatory_debt_service"], row["self_funded_capacity_generated"],
                 row["debt_funded_incremental_capacity"],
                 row["total_gross_funding_capacity"], row["share_repurchases"], row["strategic_investment"],
                 row["voluntary_debt_reduction"], row["other_discretionary_uses"],
                 row["total_discretionary_deployment"], row["forward_debt_repayment_reserve"],
                 row["forward_reserve_is_proxied"], row["remaining_deployable_headroom"],
                 row["ending_excess_liquidity"], row["version"], row["information_cutoff"]),
            )
            written["capacity_taxonomy_results"] += 1

        for row in preflight.horizon_results:
            conn.execute(
                """
                INSERT INTO capacity_horizon_results
                    (capacity_horizon_result_id, scenario_id, cumulative_self_funded_generation,
                     cumulative_debt_funded_capacity, opening_excess_liquidity_at_horizon_start,
                     cumulative_discretionary_deployment, terminal_remaining_headroom, ending_reserve_movement,
                     terminal_forward_debt_repayment_reserve, terminal_forward_reserve_is_proxied,
                     total_horizon_capacity_accessible, net_horizon_deployable_capacity, version, information_cutoff)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(capacity_horizon_result_id) DO UPDATE SET
                    cumulative_self_funded_generation=excluded.cumulative_self_funded_generation,
                    cumulative_debt_funded_capacity=excluded.cumulative_debt_funded_capacity,
                    opening_excess_liquidity_at_horizon_start=excluded.opening_excess_liquidity_at_horizon_start,
                    cumulative_discretionary_deployment=excluded.cumulative_discretionary_deployment,
                    terminal_remaining_headroom=excluded.terminal_remaining_headroom,
                    ending_reserve_movement=excluded.ending_reserve_movement,
                    terminal_forward_debt_repayment_reserve=excluded.terminal_forward_debt_repayment_reserve,
                    terminal_forward_reserve_is_proxied=excluded.terminal_forward_reserve_is_proxied,
                    total_horizon_capacity_accessible=excluded.total_horizon_capacity_accessible,
                    net_horizon_deployable_capacity=excluded.net_horizon_deployable_capacity
                """,
                (row["capacity_horizon_result_id"], row["scenario_id"], row["cumulative_self_funded_generation"],
                 row["cumulative_debt_funded_capacity"], row["opening_excess_liquidity_at_horizon_start"],
                 row["cumulative_discretionary_deployment"], row["terminal_remaining_headroom"],
                 row["ending_reserve_movement"], row["terminal_forward_debt_repayment_reserve"],
                 row["terminal_forward_reserve_is_proxied"], row["total_horizon_capacity_accessible"],
                 row["net_horizon_deployable_capacity"], row["version"], row["information_cutoff"]),
            )
            written["capacity_horizon_results"] += 1

        written_lineage_ids = []
        for row in preflight.lineage:
            conn.execute(
                """
                INSERT INTO capacity_taxonomy_lineage
                    (capacity_lineage_id, scenario_id, fiscal_year, target_field, formula,
                     same_year_forecast_inputs, same_year_capacity_inputs, information_cutoff, version,
                     dependency_timing, input_fiscal_year, next_year_debt_proceeds_fact_id,
                     next_year_debt_repayments_fact_id, proxy_note)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(capacity_lineage_id) DO UPDATE SET
                    formula=excluded.formula,
                    dependency_timing=excluded.dependency_timing,
                    input_fiscal_year=excluded.input_fiscal_year,
                    next_year_debt_proceeds_fact_id=excluded.next_year_debt_proceeds_fact_id,
                    next_year_debt_repayments_fact_id=excluded.next_year_debt_repayments_fact_id,
                    proxy_note=excluded.proxy_note
                """,
                (row["capacity_lineage_id"], row["scenario_id"], row["fiscal_year"], row["target_field"],
                 row["formula"], row["same_year_forecast_inputs"], row["same_year_capacity_inputs"],
                 row["information_cutoff"], row["version"],
                 row["dependency_timing"], row["input_fiscal_year"], row["next_year_debt_proceeds_fact_id"],
                 row["next_year_debt_repayments_fact_id"], row["proxy_note"]),
            )
            written["capacity_taxonomy_lineage"] += 1
            written_lineage_ids.append(row["capacity_lineage_id"])

        # Prune stale lineage rows for the CURRENT version only (e.g. a field
        # renamed within the same version, like total_horizon_capacity_accessible
        # -> gross_horizon_funding_before_reserve_adjustments, leaves behind a row
        # under a target_field this version's code no longer emits). Every OTHER
        # version (e.g. 'v1', frozen historical evidence) is never touched --
        # this only removes rows whose own version matches preflight.version and
        # whose ID isn't among what was just written for that same version.
        if written_lineage_ids:
            placeholders = ",".join("?" for _ in written_lineage_ids)
            conn.execute(
                f"DELETE FROM capacity_taxonomy_lineage WHERE version = ? AND capacity_lineage_id NOT IN ({placeholders})",
                (preflight.version, *written_lineage_ids),
            )

        for row in preflight.validation_results:
            conn.execute(
                """
                INSERT INTO capacity_validation_results
                    (capacity_validation_result_id, check_name, scenario_id, fiscal_year, status, detail,
                     capacity_version, run_at)
                VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(capacity_validation_result_id) DO UPDATE SET
                    status=excluded.status, detail=excluded.detail, run_at=excluded.run_at
                """,
                (row["capacity_validation_result_id"], row["check_name"], row["scenario_id"], row["fiscal_year"],
                 row["status"], row["detail"], row["capacity_version"], row["run_at"]),
            )
            written["capacity_validation_results"] += 1

        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise

    return {"status": "ok", "written": written}


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_capacity_persistence_integrity(conn: sqlite3.Connection) -> dict:
    """Post-write checks: zero orphan lineage, zero duplicates, scenario/
    cutoff lineage completeness, and legacy-table non-interference."""
    checks = {}

    def scalar(sql, params=()):
        return conn.execute(sql, params).fetchone()[0]

    # Final independent-audit closeout: the EXISTS match must require an EXACT
    # (scenario_id, fiscal_year, version) match -- previously this omitted
    # `version`, so a v2 lineage row could pass merely because a v1 result row
    # existed for the same scenario/fiscal_year, even with no matching v2
    # result at all. See test_v2_lineage_cannot_pass_via_matching_v1_result.
    orphans = scalar("""
        SELECT COUNT(*) FROM capacity_taxonomy_lineage ctl
        WHERE ctl.fiscal_year IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM capacity_taxonomy_results ctr
            WHERE ctr.scenario_id = ctl.scenario_id AND ctr.fiscal_year = ctl.fiscal_year
              AND ctr.version = ctl.version
          )
    """)
    checks["zero_orphan_lineage_exact_version"] = orphans == 0

    # Separate exact-version integrity check for HORIZON lineage (the
    # fiscal_year IS NULL rows written by build_capacity_horizon_lineage) --
    # previously these were never checked for orphans at all (the check above
    # explicitly excludes fiscal_year IS NULL rows).
    orphan_horizon_lineage = scalar("""
        SELECT COUNT(*) FROM capacity_taxonomy_lineage ctl
        WHERE ctl.fiscal_year IS NULL
          AND NOT EXISTS (
            SELECT 1 FROM capacity_horizon_results chr
            WHERE chr.scenario_id = ctl.scenario_id AND chr.version = ctl.version
          )
    """)
    checks["zero_orphan_horizon_lineage_exact_version"] = orphan_horizon_lineage == 0

    dup_results = scalar("""
        SELECT COUNT(*) FROM (
            SELECT scenario_id, fiscal_year, version, COUNT(*) c
            FROM capacity_taxonomy_results GROUP BY 1,2,3 HAVING c > 1
        )
    """)
    dup_horizon = scalar("""
        SELECT COUNT(*) FROM (
            SELECT scenario_id, version, COUNT(*) c FROM capacity_horizon_results GROUP BY 1,2 HAVING c > 1
        )
    """)
    checks["zero_duplicate_capacity_results"] = dup_results == 0
    checks["zero_duplicate_horizon_results"] = dup_horizon == 0

    missing_scenario_or_cutoff = scalar("""
        SELECT COUNT(*) FROM capacity_taxonomy_results
        WHERE scenario_id IS NULL OR information_cutoff IS NULL OR information_cutoff = ''
    """)
    checks["zero_missing_scenario_or_cutoff"] = missing_scenario_or_cutoff == 0

    # Legacy table non-interference: this persistence layer must never write
    # to, or depend on the row count of, investment_capacity_results.
    legacy_count = scalar("SELECT COUNT(*) FROM investment_capacity_results")
    checks["legacy_investment_capacity_results_untouched_count"] = legacy_count

    # Every fiscal year present must be a real forecast year (2026-2030).
    bad_years = scalar("SELECT COUNT(*) FROM capacity_taxonomy_results WHERE fiscal_year < 2026")
    checks["zero_pre_2026_capacity_rows"] = bad_years == 0

    checks["all_passed"] = all(
        v for k, v in checks.items() if isinstance(v, bool)
    )
    return checks
