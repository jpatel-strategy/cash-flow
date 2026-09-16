"""Milestone 3B: transactional, idempotent persistence of Milestone 3
forecast facts into the additive schema proposed in
docs/milestone_3_forecast_schema_proposal.md and implemented in
migrations 0015-0020.

Mirrors annual_persistence.py's design discipline: a preflight plan
computed from pure in-memory target_cash.forecast functions (never a
partial or ad hoc recomputation), a hard authorization gate (every
forecast validation check must show zero FAIL -- WARNING is allowed,
since e.g. minimum_cash_compliance's funding-warning rows are disclosed
findings, not computation errors), one atomic transaction, deterministic
IDs so a repeated call converges to the identical final state, and a
post-write integrity check covering orphan lineage, duplicates, missing
assumptions, and scenario mixing.

Nothing here touches annual_facts, annual_lineage,
annual_fact_observations, raw_facts, filings, or metric_definitions --
purely additive to the new forecast_* / investment_capacity_results
tables.
"""
from __future__ import annotations

import hashlib
import sqlite3
import time
from dataclasses import dataclass, field

from target_cash import forecast as f

FORECAST_MODEL_VERSION = "v1"

# Forecast output metrics (revenue, gross_profit, ...) are NOT XBRL-tag
# mappings like config/metric_definitions.csv's historical metrics -- they
# are derived driver-based computations defined entirely within
# forecast.py's own ForecastYear/FIELD_SPECS. metric_definition_version
# therefore pins to a forecast-specific version tag, not to
# metric_definitions.csv, which has no rows for metrics like
# deployable_capacity or valuation_net_debt.
FORECAST_METRIC_DEFINITION_VERSION = "forecast_v1"

DEPLOYABLE_CAPACITY_METHODOLOGY_NOTE = (
    "Deployable capacity = max(0, pre_discretionary_ending_cash - min_cash_buffer - "
    "near_term_debt_repayment_reserve), where pre_discretionary_ending_cash excludes "
    "discretionary share repurchases but includes dividends and the fixed debt schedule. "
    "This is NOT 'actual cash available for acquisition' without also accounting for: "
    "intra-year (seasonal) liquidity swings -- see the seasonality stress overlay, which "
    "found a materially lower intra-year trough is plausible; credit-rating considerations "
    "that could require preserving additional headroom beyond this buffer; operating-lease "
    "commitments, which are not part of any debt or cash measure here; and management's "
    "ongoing discretion to redirect dividends, buybacks, or the debt schedule. "
    "cumulative_deployable_capacity is the terminal-year figure plus any amount actually "
    "deployed along the way -- never a sum of each year's own balance, which would double-"
    "count unused cash carried forward via the ordinary cash roll-forward."
)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class ForecastPersistencePreflight:
    version: str
    scenarios: list[dict] = field(default_factory=list)
    assumptions: list[dict] = field(default_factory=list)
    facts: list[dict] = field(default_factory=list)
    lineage: list[dict] = field(default_factory=list)
    validation_results: list[dict] = field(default_factory=list)
    investment_capacity: list[dict] = field(default_factory=list)
    validation_failures: list = field(default_factory=list)
    # Kept for downstream inspection / clean-room comparison -- not persisted directly.
    forecasts_by_scenario: dict = field(default_factory=dict)
    assumption_objects: list = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "forecast_scenarios": len(self.scenarios),
            "forecast_assumptions": len(self.assumptions),
            "forecast_facts": len(self.facts),
            "forecast_lineage": len(self.lineage),
            "forecast_validation_results": len(self.validation_results),
            "investment_capacity_results": len(self.investment_capacity),
            "validation_failures": len(self.validation_failures),
        }

    def is_authorized(self) -> bool:
        return len(self.validation_failures) == 0


def compute_forecast_preflight(version: str = FORECAST_MODEL_VERSION) -> ForecastPersistencePreflight:
    """Builds the complete, deterministic persistence plan from pure
    in-memory target_cash.forecast computation -- never a partial
    recomputation, and never reads or writes the database itself.
    """
    assumptions = f.build_assumptions()
    forecasts = f.run_all_scenarios(assumptions)
    representative_lineage = {s: f.build_lineage(y, assumptions) for s, y in forecasts.items()}
    validation_results = f.validate_all(forecasts, assumptions, representative_lineage)
    validation_failures = [r for r in validation_results if r.status == "FAIL"]

    now = _now()
    pre = ForecastPersistencePreflight(version=version, forecasts_by_scenario=forecasts, assumption_objects=assumptions)

    # 1. forecast_scenarios
    scenario_names = {"base": "Base", "upside": "Upside", "downside": "Downside"}
    for s in f.SCENARIOS:
        pre.scenarios.append({
            "scenario_id": s, "scenario_name": scenario_names[s],
            "description": f.scenario_narrative(s),
            "information_cutoff": f.FORECAST_INFORMATION_CUTOFF,
            "information_cutoff_accession": f.FORECAST_INFORMATION_CUTOFF_ACCESSION,
            "version": version, "created_at": now,
        })

    # 2. forecast_assumptions -- directly from build_assumptions(), unchanged.
    for a in assumptions:
        pre.assumptions.append({
            "assumption_id": a.assumption_id, "scenario_id": a.scenario, "forecast_year": a.forecast_year,
            "metric": a.metric, "value": a.value, "unit": a.unit, "rationale": a.rationale,
            "historical_reference": a.historical_reference, "source_evidence": a.source_evidence,
            "information_cutoff": a.information_cutoff, "review_status": a.review_status,
            "version": a.version, "created_at": now,
        })

    # 3. forecast_facts -- one row per (scenario, fiscal_year, metric) for
    # every FIELD_SPECS-covered metric with a non-None value. Values shared
    # across an assumption-echo (e.g. gross_margin_pct is both a ForecastYear
    # field and the raw assumption value) still get their own forecast_facts
    # row: the ROW records "the value actually applied this year", the
    # forecast_assumptions row records "the assumption as authored" -- the
    # same number, two different provenance questions.
    for s, years in forecasts.items():
        for y in years:
            for metric, (formula, _same, _cross, _asm) in f.FIELD_SPECS.items():
                value = getattr(y, metric)
                if value is None:
                    continue
                if isinstance(value, bool):
                    value = 1.0 if value else 0.0
                pre.facts.append({
                    "forecast_fact_id": f.forecast_fact_id(s, metric, y.fiscal_year, version),
                    "scenario_id": s, "fiscal_year": y.fiscal_year, "metric": metric,
                    "metric_definition_version": FORECAST_METRIC_DEFINITION_VERSION,
                    "assumption_version": version, "value": float(value),
                    "unit": "percent" if metric.endswith("_pct") else (
                        "USD_per_share" if metric in ("diluted_eps", "dividend_per_share") else
                        "boolean" if metric == "funding_warning" else "USD_millions"),
                    "formula": formula, "validation_status": "unvalidated",
                    "information_cutoff": f.FORECAST_INFORMATION_CUTOFF, "created_at": now,
                })

    # 4. forecast_lineage -- full grain, via build_full_lineage.
    for s, years in forecasts.items():
        full_lineage = f.build_full_lineage(years, assumptions, version)
        for i, row in enumerate(full_lineage):
            pre.lineage.append({
                "forecast_lineage_id": f"{row['forecast_fact_id']}_lin_{row['sequence']}",
                "forecast_fact_id": row["forecast_fact_id"],
                "input_historical_fact_id": row["input_historical_fact_id"],
                "input_forecast_fact_id": row["input_forecast_fact_id"],
                "input_assumption_id": row["input_assumption_id"],
                "operation": row["operation"], "sequence": row["sequence"],
            })

    # 5. forecast_validation_results -- every check, exactly as validate_all() returned it.
    for r in validation_results:
        vid = f"val_{r.check_name}_{r.scenario or 'all'}_{r.fiscal_year or 0}_{version}"
        pre.validation_results.append({
            "validation_result_id": vid, "check_name": r.check_name,
            "scenario_id": r.scenario, "fiscal_year": r.fiscal_year,
            "status": r.status, "detail": r.detail, "forecast_version": version, "run_at": now,
        })

    # 6. investment_capacity_results -- one row per (scenario, fiscal_year).
    for s, years in forecasts.items():
        cumulative_series = f.cumulative_deployable_capacity_through_each_year(years)
        for y, cumulative in zip(years, cumulative_series):
            pre.investment_capacity.append({
                "investment_capacity_result_id": f"icr_{s}_{y.fiscal_year}_{version}",
                "scenario_id": s, "fiscal_year": y.fiscal_year,
                "gross_fcf_capacity": y.gross_fcf_capacity, "post_dividend_capacity": y.post_dividend_capacity,
                "pre_discretionary_ending_cash": y.pre_discretionary_ending_cash,
                "min_cash_buffer": y.min_cash_buffer,
                "near_term_debt_repayment_reserve": y.near_term_debt_repayment_reserve,
                "deployable_capacity": y.deployable_capacity, "cumulative_deployable_capacity": cumulative,
                "funding_warning": 1 if y.funding_warning else 0,
                "methodology_note": DEPLOYABLE_CAPACITY_METHODOLOGY_NOTE,
                "information_cutoff": f.FORECAST_INFORMATION_CUTOFF,
            })

    pre.validation_failures = validation_failures
    return pre


class ForecastPersistenceNotAuthorizedError(RuntimeError):
    pass


def persist_forecast(conn: sqlite3.Connection, preflight: ForecastPersistencePreflight) -> dict:
    """Writes preflight's exact plan into the 6 forecast_*/investment_capacity_results
    tables as ONE atomic transaction. Refuses if any validation check failed
    (WARNING is fine). Idempotent: deterministic IDs + ON CONFLICT DO UPDATE
    mean a repeated call with the same preflight plan converges to the
    identical final state.
    """
    if not preflight.is_authorized():
        raise ForecastPersistenceNotAuthorizedError(
            f"Forecast persistence refused: {len(preflight.validation_failures)} validation check(s) "
            f"failed: {[r.check_name for r in preflight.validation_failures]}. Fix the underlying "
            "problem before persisting -- do not bypass this gate."
        )

    written = {k: 0 for k in ("forecast_scenarios", "forecast_assumptions", "forecast_facts",
                               "forecast_lineage", "forecast_validation_results", "investment_capacity_results")}
    try:
        conn.execute("BEGIN")

        for row in preflight.scenarios:
            conn.execute(
                """
                INSERT INTO forecast_scenarios
                    (scenario_id, scenario_name, description, information_cutoff,
                     information_cutoff_accession, version, created_at)
                VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(scenario_id) DO UPDATE SET
                    scenario_name=excluded.scenario_name, description=excluded.description,
                    information_cutoff=excluded.information_cutoff,
                    information_cutoff_accession=excluded.information_cutoff_accession,
                    version=excluded.version
                """,
                (row["scenario_id"], row["scenario_name"], row["description"], row["information_cutoff"],
                 row["information_cutoff_accession"], row["version"], row["created_at"]),
            )
            written["forecast_scenarios"] += 1

        for row in preflight.assumptions:
            conn.execute(
                """
                INSERT INTO forecast_assumptions
                    (assumption_id, scenario_id, forecast_year, metric, value, unit, rationale,
                     historical_reference, source_evidence, information_cutoff, review_status,
                     version, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(assumption_id) DO UPDATE SET
                    value=excluded.value, rationale=excluded.rationale,
                    historical_reference=excluded.historical_reference,
                    source_evidence=excluded.source_evidence, review_status=excluded.review_status
                """,
                (row["assumption_id"], row["scenario_id"], row["forecast_year"], row["metric"], row["value"],
                 row["unit"], row["rationale"], row["historical_reference"], row["source_evidence"],
                 row["information_cutoff"], row["review_status"], row["version"], row["created_at"]),
            )
            written["forecast_assumptions"] += 1

        for row in preflight.facts:
            conn.execute(
                """
                INSERT INTO forecast_facts
                    (forecast_fact_id, scenario_id, fiscal_year, metric, metric_definition_version,
                     assumption_version, value, unit, formula, validation_status, information_cutoff, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(forecast_fact_id) DO UPDATE SET
                    value=excluded.value, formula=excluded.formula
                """,
                (row["forecast_fact_id"], row["scenario_id"], row["fiscal_year"], row["metric"],
                 row["metric_definition_version"], row["assumption_version"], row["value"], row["unit"],
                 row["formula"], row["validation_status"], row["information_cutoff"], row["created_at"]),
            )
            written["forecast_facts"] += 1

        for row in preflight.lineage:
            conn.execute(
                """
                INSERT INTO forecast_lineage
                    (forecast_lineage_id, forecast_fact_id, input_historical_fact_id,
                     input_forecast_fact_id, input_assumption_id, operation, sequence)
                VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(forecast_lineage_id) DO UPDATE SET operation=excluded.operation
                """,
                (row["forecast_lineage_id"], row["forecast_fact_id"], row["input_historical_fact_id"],
                 row["input_forecast_fact_id"], row["input_assumption_id"], row["operation"], row["sequence"]),
            )
            written["forecast_lineage"] += 1

        for row in preflight.validation_results:
            conn.execute(
                """
                INSERT INTO forecast_validation_results
                    (validation_result_id, check_name, scenario_id, fiscal_year, status, detail,
                     forecast_version, run_at)
                VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(validation_result_id) DO UPDATE SET
                    status=excluded.status, detail=excluded.detail, run_at=excluded.run_at
                """,
                (row["validation_result_id"], row["check_name"], row["scenario_id"], row["fiscal_year"],
                 row["status"], row["detail"], row["forecast_version"], row["run_at"]),
            )
            written["forecast_validation_results"] += 1

        for row in preflight.investment_capacity:
            conn.execute(
                """
                INSERT INTO investment_capacity_results
                    (investment_capacity_result_id, scenario_id, fiscal_year, gross_fcf_capacity,
                     post_dividend_capacity, pre_discretionary_ending_cash, min_cash_buffer,
                     near_term_debt_repayment_reserve, deployable_capacity, cumulative_deployable_capacity,
                     funding_warning, methodology_note, information_cutoff)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(investment_capacity_result_id) DO UPDATE SET
                    deployable_capacity=excluded.deployable_capacity,
                    cumulative_deployable_capacity=excluded.cumulative_deployable_capacity,
                    funding_warning=excluded.funding_warning
                """,
                (row["investment_capacity_result_id"], row["scenario_id"], row["fiscal_year"],
                 row["gross_fcf_capacity"], row["post_dividend_capacity"], row["pre_discretionary_ending_cash"],
                 row["min_cash_buffer"], row["near_term_debt_repayment_reserve"], row["deployable_capacity"],
                 row["cumulative_deployable_capacity"], row["funding_warning"], row["methodology_note"],
                 row["information_cutoff"]),
            )
            written["investment_capacity_results"] += 1

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


def verify_forecast_persistence_integrity(conn: sqlite3.Connection) -> dict:
    """Post-write checks: zero orphan lineage, zero duplicates, zero missing
    assumptions, zero scenario mixing -- named exactly as the governing
    instructions list them.
    """
    checks = {}

    def scalar(sql, params=()):
        return conn.execute(sql, params).fetchone()[0]

    # zero orphan lineage: every forecast_lineage row's forecast_fact_id must
    # exist in forecast_facts, and every non-null input_* must exist in its
    # own target table.
    orphans = scalar("""
        SELECT COUNT(*) FROM forecast_lineage fl
        WHERE NOT EXISTS (SELECT 1 FROM forecast_facts ff WHERE ff.forecast_fact_id = fl.forecast_fact_id)
           OR (fl.input_forecast_fact_id IS NOT NULL
               AND NOT EXISTS (SELECT 1 FROM forecast_facts ff2 WHERE ff2.forecast_fact_id = fl.input_forecast_fact_id))
           OR (fl.input_assumption_id IS NOT NULL
               AND NOT EXISTS (SELECT 1 FROM forecast_assumptions fa WHERE fa.assumption_id = fl.input_assumption_id))
           OR (fl.input_historical_fact_id IS NOT NULL
               AND NOT EXISTS (SELECT 1 FROM annual_facts af WHERE af.annual_fact_id = fl.input_historical_fact_id))
    """)
    checks["zero_orphan_lineage"] = orphans == 0

    # zero duplicates: every declared UNIQUE/PRIMARY KEY grain has no
    # duplicate rows (defense in depth beyond the schema's own constraints).
    dup_facts = scalar("""
        SELECT COUNT(*) FROM (
            SELECT scenario_id, metric, fiscal_year, assumption_version, COUNT(*) c
            FROM forecast_facts GROUP BY 1,2,3,4 HAVING c > 1
        )
    """)
    dup_assumptions = scalar("""
        SELECT COUNT(*) FROM (
            SELECT scenario_id, metric, forecast_year, version, COUNT(*) c
            FROM forecast_assumptions GROUP BY 1,2,3,4 HAVING c > 1
        )
    """)
    dup_icr = scalar("""
        SELECT COUNT(*) FROM (
            SELECT scenario_id, fiscal_year, COUNT(*) c FROM investment_capacity_results GROUP BY 1,2 HAVING c > 1
        )
    """)
    checks["zero_duplicate_facts"] = dup_facts == 0
    checks["zero_duplicate_assumptions"] = dup_assumptions == 0
    checks["zero_duplicate_investment_capacity_rows"] = dup_icr == 0

    # zero missing assumptions: every scenario has at least one assumption
    # row for every required driver metric (mirrors forecast.py's own
    # assumption_completeness check, re-verified independently at the DB level).
    required_metrics = [
        "revenue_growth_pct", "gross_margin_pct", "sga_pct_of_revenue", "da_pct_of_revenue",
        "effective_tax_rate_pct", "net_other_income_musd", "diluted_share_change_pct",
        "interest_rate_pct", "capex_pct_of_revenue", "da_cfo_addback_pct_of_revenue",
        "inventory_pct_of_revenue", "ap_pct_of_cogs", "other_operating_cf_musd",
        "dividend_per_share_growth_pct", "buyback_payout_pct_of_post_dividend_fcf",
        "debt_proceeds_musd", "debt_repayments_musd", "finance_lease_liabilities_musd",
        "min_cash_buffer_pct_of_revenue",
    ]
    missing = []
    for s in f.SCENARIOS:
        for metric in required_metrics:
            count = scalar(
                "SELECT COUNT(*) FROM forecast_assumptions WHERE scenario_id=? AND metric=?", (s, metric)
            )
            if count == 0:
                missing.append((s, metric))
    checks["zero_missing_assumptions"] = len(missing) == 0
    checks["missing_assumptions_detail"] = missing

    # zero scenario mixing: a forecast_facts row's scenario must match every
    # assumption/forecast-fact input its lineage cites -- a fact for 'base'
    # must never be derived from an 'upside' assumption or fact.
    mixing = scalar("""
        SELECT COUNT(*) FROM forecast_lineage fl
        JOIN forecast_facts ff ON ff.forecast_fact_id = fl.forecast_fact_id
        LEFT JOIN forecast_assumptions fa ON fa.assumption_id = fl.input_assumption_id
        LEFT JOIN forecast_facts ff2 ON ff2.forecast_fact_id = fl.input_forecast_fact_id
        WHERE (fa.scenario_id IS NOT NULL AND fa.scenario_id != ff.scenario_id)
           OR (ff2.scenario_id IS NOT NULL AND ff2.scenario_id != ff.scenario_id)
    """)
    checks["zero_scenario_mixing"] = mixing == 0

    # Structural historical/forecast separation, re-verified at the DB level.
    hist_overlap = scalar("SELECT COUNT(*) FROM forecast_facts WHERE fiscal_year < 2026")
    checks["zero_historical_forecast_year_overlap"] = hist_overlap == 0

    checks["all_passed"] = all(
        v for k, v in checks.items() if isinstance(v, bool)
    )
    return checks
