"""Milestone 4: transactional, idempotent persistence of DCF valuation
results into the additive schema (migrations 0021-0024). Mirrors
forecast_persistence.py's discipline exactly: a preflight plan from pure
in-memory target_cash.valuation computation, a hard authorization gate
(zero FAIL across every valuation check), one atomic transaction,
deterministic IDs with ON CONFLICT DO UPDATE for idempotency, and a
post-write integrity report.
"""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field

from target_cash import forecast as f
from target_cash import valuation as v

VALUATION_MODEL_VERSION = "v1"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class ValuationPersistencePreflight:
    version: str
    assumptions: list[dict] = field(default_factory=list)
    ufcf_facts: list[dict] = field(default_factory=list)
    results: list[dict] = field(default_factory=list)
    validation_results: list[dict] = field(default_factory=list)
    validation_failures: list = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "valuation_assumptions": len(self.assumptions),
            "valuation_ufcf_facts": len(self.ufcf_facts),
            "valuation_results": len(self.results),
            "valuation_validation_results": len(self.validation_results),
            "validation_failures": len(self.validation_failures),
        }

    def is_authorized(self) -> bool:
        return len(self.validation_failures) == 0


def compute_valuation_preflight(
    forecasts: dict[str, list[f.ForecastYear]] | None = None, version: str = VALUATION_MODEL_VERSION,
) -> ValuationPersistencePreflight:
    forecasts = forecasts if forecasts is not None else f.run_all_scenarios()
    val_assumptions = v.build_valuation_assumptions()
    dcf_results = v.run_dcf_all_scenarios(forecasts, val_assumptions)
    checks = v.run_all_valuation_checks(forecasts, dcf_results)
    failures = [c for c in checks if c.status == "FAIL"]

    now = _now()
    pre = ValuationPersistencePreflight(version=version)

    for a in val_assumptions:
        pre.assumptions.append({
            "assumption_id": a.assumption_id, "metric": a.metric, "value": a.value, "unit": a.unit,
            "rationale": a.rationale, "source_evidence": a.source_evidence,
            "information_cutoff": a.information_cutoff, "review_status": a.review_status,
            "version": a.version, "created_at": now,
        })

    for scenario, result in dcf_results.items():
        for i, (fy, ufcf) in enumerate(result.ufcf_by_year.items(), start=1):
            pre.ufcf_facts.append({
                "valuation_ufcf_fact_id": f"vufcf_{scenario}_{fy}_{version}",
                "scenario_id": scenario, "fiscal_year": fy, "ufcf": ufcf,
                "pv_ufcf": result.pv_ufcf_by_year[fy], "discount_period": i,
                "information_cutoff": v.VALUATION_INFORMATION_CUTOFF,
            })
        pre.results.append({
            "valuation_result_id": f"vres_{scenario}_{version}", "scenario_id": scenario,
            "wacc_pct": result.wacc_pct, "terminal_growth_pct": result.terminal_growth_pct,
            "pv_explicit_period": result.pv_explicit_period, "terminal_year_ufcf": result.terminal_year_ufcf,
            "terminal_value_undiscounted": result.terminal_value_undiscounted,
            "pv_terminal_value": result.pv_terminal_value, "enterprise_value": result.enterprise_value,
            "valuation_date_net_debt": result.valuation_date_net_debt, "equity_value": result.equity_value,
            "valuation_date_diluted_shares": result.valuation_date_diluted_shares,
            "implied_value_per_share": result.implied_value_per_share,
            "information_cutoff": v.VALUATION_INFORMATION_CUTOFF, "created_at": now,
        })

    for c in checks:
        fy_suffix = f"_{c.fiscal_year}" if c.fiscal_year else ""
        vid = f"vval_{c.check_name}_{c.scenario or 'all'}{fy_suffix}_{version}"
        pre.validation_results.append({
            "validation_result_id": vid, "check_name": c.check_name, "scenario_id": c.scenario,
            "status": c.status, "detail": c.detail, "valuation_version": version, "run_at": now,
        })

    pre.validation_failures = failures
    return pre


class ValuationPersistenceNotAuthorizedError(RuntimeError):
    pass


def persist_valuation(conn: sqlite3.Connection, preflight: ValuationPersistencePreflight) -> dict:
    if not preflight.is_authorized():
        raise ValuationPersistenceNotAuthorizedError(
            f"Valuation persistence refused: {len(preflight.validation_failures)} check(s) failed: "
            f"{[c.check_name for c in preflight.validation_failures]}. Fix the underlying problem "
            "before persisting -- do not bypass this gate."
        )

    written = {k: 0 for k in ("valuation_assumptions", "valuation_ufcf_facts", "valuation_results",
                               "valuation_validation_results")}
    try:
        conn.execute("BEGIN")

        for row in preflight.assumptions:
            conn.execute(
                """
                INSERT INTO valuation_assumptions
                    (assumption_id, metric, value, unit, rationale, source_evidence, information_cutoff,
                     review_status, version, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(assumption_id) DO UPDATE SET
                    value=excluded.value, rationale=excluded.rationale, review_status=excluded.review_status
                """,
                (row["assumption_id"], row["metric"], row["value"], row["unit"], row["rationale"],
                 row["source_evidence"], row["information_cutoff"], row["review_status"], row["version"],
                 row["created_at"]),
            )
            written["valuation_assumptions"] += 1

        for row in preflight.ufcf_facts:
            conn.execute(
                """
                INSERT INTO valuation_ufcf_facts
                    (valuation_ufcf_fact_id, scenario_id, fiscal_year, ufcf, pv_ufcf, discount_period,
                     information_cutoff)
                VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(valuation_ufcf_fact_id) DO UPDATE SET ufcf=excluded.ufcf, pv_ufcf=excluded.pv_ufcf
                """,
                (row["valuation_ufcf_fact_id"], row["scenario_id"], row["fiscal_year"], row["ufcf"],
                 row["pv_ufcf"], row["discount_period"], row["information_cutoff"]),
            )
            written["valuation_ufcf_facts"] += 1

        for row in preflight.results:
            conn.execute(
                """
                INSERT INTO valuation_results
                    (valuation_result_id, scenario_id, wacc_pct, terminal_growth_pct, pv_explicit_period,
                     terminal_year_ufcf, terminal_value_undiscounted, pv_terminal_value, enterprise_value,
                     valuation_date_net_debt, equity_value, valuation_date_diluted_shares,
                     implied_value_per_share, information_cutoff, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(valuation_result_id) DO UPDATE SET
                    enterprise_value=excluded.enterprise_value, equity_value=excluded.equity_value,
                    implied_value_per_share=excluded.implied_value_per_share
                """,
                (row["valuation_result_id"], row["scenario_id"], row["wacc_pct"], row["terminal_growth_pct"],
                 row["pv_explicit_period"], row["terminal_year_ufcf"], row["terminal_value_undiscounted"],
                 row["pv_terminal_value"], row["enterprise_value"], row["valuation_date_net_debt"],
                 row["equity_value"], row["valuation_date_diluted_shares"], row["implied_value_per_share"],
                 row["information_cutoff"], row["created_at"]),
            )
            written["valuation_results"] += 1

        for row in preflight.validation_results:
            conn.execute(
                """
                INSERT INTO valuation_validation_results
                    (validation_result_id, check_name, scenario_id, status, detail, valuation_version, run_at)
                VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(validation_result_id) DO UPDATE SET
                    status=excluded.status, detail=excluded.detail, run_at=excluded.run_at
                """,
                (row["validation_result_id"], row["check_name"], row["scenario_id"], row["status"],
                 row["detail"], row["valuation_version"], row["run_at"]),
            )
            written["valuation_validation_results"] += 1

        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise

    return {"status": "ok", "written": written}


def verify_valuation_persistence_integrity(conn: sqlite3.Connection) -> dict:
    checks = {}

    def scalar(sql, params=()):
        return conn.execute(sql, params).fetchone()[0]

    orphans = scalar("""
        SELECT COUNT(*) FROM valuation_ufcf_facts vf
        WHERE NOT EXISTS (SELECT 1 FROM forecast_scenarios fs WHERE fs.scenario_id = vf.scenario_id)
    """)
    checks["zero_orphan_ufcf_facts"] = orphans == 0

    orphan_results = scalar("""
        SELECT COUNT(*) FROM valuation_results vr
        WHERE NOT EXISTS (SELECT 1 FROM forecast_scenarios fs WHERE fs.scenario_id = vr.scenario_id)
    """)
    checks["zero_orphan_results"] = orphan_results == 0

    dup_results = scalar("""
        SELECT COUNT(*) FROM (SELECT scenario_id, COUNT(*) c FROM valuation_results GROUP BY 1 HAVING c > 1)
    """)
    checks["zero_duplicate_results"] = dup_results == 0

    missing_scenarios = scalar("""
        SELECT COUNT(*) FROM forecast_scenarios fs
        WHERE NOT EXISTS (SELECT 1 FROM valuation_results vr WHERE vr.scenario_id = fs.scenario_id)
    """)
    checks["every_scenario_has_a_valuation_result"] = missing_scenarios == 0

    # WACC/terminal growth invariance re-verified at the DB level.
    distinct_wacc = scalar("SELECT COUNT(DISTINCT wacc_pct) FROM valuation_results")
    distinct_growth = scalar("SELECT COUNT(DISTINCT terminal_growth_pct) FROM valuation_results")
    checks["wacc_and_growth_scenario_invariant"] = distinct_wacc <= 1 and distinct_growth <= 1

    checks["all_passed"] = all(v for v in checks.values() if isinstance(v, bool))
    return checks
