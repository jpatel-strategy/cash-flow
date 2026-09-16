"""Compares canonical analytical content between two target_cash.db files
(e.g. the active database and a clean-room rebuild) via deterministic,
sorted, hash-stable exports -- never comparing raw SQLite file bytes/hashes,
since file-level layout (page order, vacuum state, etc.) is not a property
of the analytical content.

Excluded fields, and why (each is a randomly-generated identifier or wall-
clock timestamp assigned fresh on each derivation run, carrying no
information beyond identifying "this specific fact" -- which the natural
key of metric + period already provides):
  - quarterly_facts.quarterly_fact_id, instant_facts.instant_fact_id,
    lineage.lineage_id, instant_fact_observations.observation_id:
    uuid.uuid4()-derived, regenerated every run.
  - quarterly_facts.as_of_date, instant_facts.information_cutoff:
    wall-clock insertion timestamps.
  - Any "qf_<12 hex chars>" substring appearing inside a validate check's
    free-text `detail` field (e.g. check_balance_sheet_cash_agreement's
    balance_sheet_source/rollforward_source) -- the same random
    quarterly_fact_id, echoed into prose.

annual_facts.annual_fact_id, annual_fact_observations.observation_id, and
annual_lineage.annual_lineage_id are NOT excluded, and need no normalization
regex: target_cash.annual_persistence builds them deterministically
(f"annual:{metric}:{fiscal_year}:{analytical_view}", etc.), not from
uuid.uuid4(), specifically so a clean-room rebuild produces byte-identical
IDs, not just byte-identical content under a value-only comparison.
annual_facts.information_cutoff is also NOT excluded -- it comes from
config/model.yml's fixed `information_cutoff` field, not a wall-clock
timestamp, so it is identical across any two runs against the same config.

Milestone 3B: forecast_scenarios.created_at, forecast_assumptions.created_at,
forecast_facts.created_at, and forecast_validation_results.run_at are
EXCLUDED for the same reason as quarterly_facts.as_of_date -- wall-clock
insertion timestamps. Every forecast_* primary key (forecast_fact_id,
forecast_lineage_id, validation_result_id, investment_capacity_result_id)
IS included and needs no normalization: target_cash.forecast_persistence
builds them all deterministically (forecast_fact_id = f"fct_{scenario}_
{metric}_{fiscal_year}_{version}", etc.), the same discipline as
annual_facts.annual_fact_id.

Usage: python compare_databases.py <db_a> <db_b> <validate_json_a> <validate_json_b>
"""
import hashlib
import json
import re
import sqlite3
import sys


def export_quarterly_facts(conn):
    rows = conn.execute(
        """
        SELECT metric, fiscal_year, fiscal_quarter, period_start, period_end,
               days_in_period, value_original, original_unit, value_normalized,
               normalized_unit, basis, mapping_version, is_current_view
        FROM quarterly_facts ORDER BY metric, fiscal_year, fiscal_quarter
        """
    ).fetchall()
    return [list(r) for r in rows]


def export_lineage(conn):
    rows = conn.execute(
        """
        SELECT qf.metric, qf.fiscal_year, qf.fiscal_quarter, l.input_fact_id, l.operation
        FROM lineage l JOIN quarterly_facts qf ON qf.quarterly_fact_id = l.derived_fact_id
        ORDER BY qf.metric, qf.fiscal_year, qf.fiscal_quarter, l.input_fact_id, l.operation
        """
    ).fetchall()
    return [list(r) for r in rows]


def export_instant_facts(conn):
    rows = conn.execute(
        """
        SELECT metric, as_of_date, accounting_basis, consolidated_scope, analytical_view,
               selected_raw_fact_id, authoritative_source_reason, value_original, original_unit,
               scale, value_normalized, normalized_unit, accession_number, filed_at,
               restatement_status, mapping_version, selection_status, is_current_view
        FROM instant_facts ORDER BY metric, as_of_date, accounting_basis, consolidated_scope, analytical_view
        """
    ).fetchall()
    return [list(r) for r in rows]


def export_instant_fact_observations(conn):
    rows = conn.execute(
        """
        SELECT i.metric, i.as_of_date, o.raw_fact_id, o.accession_number, o.filed_at,
               o.relationship, o.value_original, o.difference_from_selected, o.note
        FROM instant_fact_observations o JOIN instant_facts i ON i.instant_fact_id = o.instant_fact_id
        ORDER BY i.metric, i.as_of_date, o.relationship, o.raw_fact_id
        """
    ).fetchall()
    return [list(r) for r in rows]


def export_annual_facts(conn):
    rows = conn.execute(
        """
        SELECT annual_fact_id, metric, fiscal_year, period_start, period_end, days_in_period,
               analytical_view, value_original, original_unit, value_normalized, normalized_unit,
               direct_or_derived, fact_status, validation_status, accession_number, filed_at,
               mapping_version, information_cutoff, is_current_view
        FROM annual_facts ORDER BY metric, fiscal_year, analytical_view
        """
    ).fetchall()
    return [list(r) for r in rows]


def export_annual_fact_observations(conn):
    rows = conn.execute(
        """
        SELECT af.metric, af.fiscal_year, af.analytical_view, o.observation_id, o.raw_fact_id,
               o.accession_number, o.filed_at, o.relationship, o.value_original,
               o.difference_from_selected, o.classification_rationale
        FROM annual_fact_observations o JOIN annual_facts af ON af.annual_fact_id = o.annual_fact_id
        ORDER BY af.metric, af.fiscal_year, af.analytical_view, o.observation_id
        """
    ).fetchall()
    return [list(r) for r in rows]


def export_annual_lineage(conn):
    rows = conn.execute(
        """
        SELECT derived.metric, derived.fiscal_year, derived.analytical_view,
               al.annual_lineage_id, al.input_raw_fact_id, input.metric, al.operation, al.sequence
        FROM annual_lineage al
        JOIN annual_facts derived ON derived.annual_fact_id = al.derived_fact_id
        LEFT JOIN annual_facts input ON input.annual_fact_id = al.input_annual_fact_id
        ORDER BY derived.metric, derived.fiscal_year, derived.analytical_view, al.sequence
        """
    ).fetchall()
    return [list(r) for r in rows]


def export_forecast_scenarios(conn):
    # created_at excluded: a wall-clock insertion timestamp, like
    # quarterly_facts.as_of_date above -- not a property of the analytical
    # content, and different between any two independent persistence runs.
    rows = conn.execute(
        """
        SELECT scenario_id, scenario_name, description, information_cutoff,
               information_cutoff_accession, version
        FROM forecast_scenarios ORDER BY scenario_id
        """
    ).fetchall()
    return [list(r) for r in rows]


def export_forecast_assumptions(conn):
    rows = conn.execute(
        """
        SELECT assumption_id, scenario_id, forecast_year, metric, value, unit, rationale,
               historical_reference, source_evidence, information_cutoff, review_status, version
        FROM forecast_assumptions ORDER BY scenario_id, metric, forecast_year
        """
    ).fetchall()
    return [list(r) for r in rows]


def export_forecast_facts(conn):
    rows = conn.execute(
        """
        SELECT forecast_fact_id, scenario_id, fiscal_year, metric, metric_definition_version,
               assumption_version, value, unit, formula, validation_status, information_cutoff
        FROM forecast_facts ORDER BY scenario_id, metric, fiscal_year
        """
    ).fetchall()
    return [list(r) for r in rows]


def export_forecast_lineage(conn):
    rows = conn.execute(
        """
        SELECT ff.scenario_id, ff.metric, ff.fiscal_year, fl.forecast_lineage_id,
               fl.input_historical_fact_id, fl.input_forecast_fact_id, fl.input_assumption_id,
               fl.operation, fl.sequence
        FROM forecast_lineage fl JOIN forecast_facts ff ON ff.forecast_fact_id = fl.forecast_fact_id
        ORDER BY ff.scenario_id, ff.metric, ff.fiscal_year, fl.sequence
        """
    ).fetchall()
    return [list(r) for r in rows]


def export_forecast_validation_results(conn):
    # run_at excluded (wall-clock timestamp); validation_result_id is
    # deterministic (built from check_name/scenario/fiscal_year/version, not
    # a random id) so it IS included, same rationale as annual_fact_id above.
    rows = conn.execute(
        """
        SELECT validation_result_id, check_name, scenario_id, fiscal_year, status, detail, forecast_version
        FROM forecast_validation_results ORDER BY check_name, scenario_id, fiscal_year
        """
    ).fetchall()
    return [list(r) for r in rows]


def export_investment_capacity_results(conn):
    rows = conn.execute(
        """
        SELECT investment_capacity_result_id, scenario_id, fiscal_year, gross_fcf_capacity,
               post_dividend_capacity, pre_discretionary_ending_cash, min_cash_buffer,
               near_term_debt_repayment_reserve, deployable_capacity, cumulative_deployable_capacity,
               funding_warning, methodology_note, information_cutoff
        FROM investment_capacity_results ORDER BY scenario_id, fiscal_year
        """
    ).fetchall()
    return [list(r) for r in rows]


def export_period_facts_unified(conn):
    rows = conn.execute(
        """
        SELECT metric, frequency, fiscal_year, fiscal_quarter, start_date, end_date, value, unit,
               direct_or_derived, analytical_view, validation_status, reporting_period_role
        FROM period_facts_unified
        ORDER BY metric, frequency, fiscal_year, fiscal_quarter, analytical_view
        """
    ).fetchall()
    return [list(r) for r in rows]


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))


def sha256_of(obj) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def export_db(db_path):
    conn = sqlite3.connect(db_path)
    exports = {
        "quarterly_facts": export_quarterly_facts(conn),
        "lineage": export_lineage(conn),
        "instant_facts": export_instant_facts(conn),
        "instant_fact_observations": export_instant_fact_observations(conn),
        "annual_facts": export_annual_facts(conn),
        "annual_fact_observations": export_annual_fact_observations(conn),
        "annual_lineage": export_annual_lineage(conn),
        "period_facts_unified": export_period_facts_unified(conn),
        "forecast_scenarios": export_forecast_scenarios(conn),
        "forecast_assumptions": export_forecast_assumptions(conn),
        "forecast_facts": export_forecast_facts(conn),
        "forecast_lineage": export_forecast_lineage(conn),
        "forecast_validation_results": export_forecast_validation_results(conn),
        "investment_capacity_results": export_investment_capacity_results(conn),
    }
    conn.close()
    return {name: {"row_count": len(rows), "sha256": sha256_of(rows)} for name, rows in exports.items()}


def normalize_validate_output(d):
    d = dict(d)
    d.pop("command", None)
    text = canonical_json(d)
    text = re.sub(r"qf_[0-9a-f]{12}", "qf_<normalized>", text)
    return text


def main():
    db_a, db_b, validate_a_path, validate_b_path = sys.argv[1:5]

    export_a = export_db(db_a)
    export_b = export_db(db_b)

    validate_a = normalize_validate_output(json.load(open(validate_a_path)))
    validate_b = normalize_validate_output(json.load(open(validate_b_path)))
    validate_a_hash = hashlib.sha256(validate_a.encode()).hexdigest()
    validate_b_hash = hashlib.sha256(validate_b.encode()).hexdigest()

    all_match = True
    print(f"{'export':<28} {'a_rows':>7} {'b_rows':>7}  match  sha256")
    for name in export_a:
        a, b = export_a[name], export_b[name]
        match = a == b
        all_match &= match
        print(f"{name:<28} {a['row_count']:>7} {b['row_count']:>7}  {'YES' if match else 'NO ':<5}  {a['sha256']}")
        if not match:
            print(f"  {'':28} {'':7} {'':7}         {b['sha256']}")

    validate_match = validate_a_hash == validate_b_hash
    all_match &= validate_match
    print(f"{'validation_results':<28} {'':>7} {'':>7}  {'YES' if validate_match else 'NO ':<5}  {validate_a_hash}")
    if not validate_match:
        print(f"  {'':28} {'':7} {'':7}         {validate_b_hash}")

    print()
    print("ALL EXPORTS MATCH" if all_match else "MISMATCH DETECTED")
    return 0 if all_match else 1


if __name__ == "__main__":
    sys.exit(main())
