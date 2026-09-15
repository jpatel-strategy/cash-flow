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
