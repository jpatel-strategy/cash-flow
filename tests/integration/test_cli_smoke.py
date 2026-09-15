"""End-to-end smoke test for the fetch -> normalize -> validate CLI contract.

Runs against an isolated temp directory (never the real project's data/,
docs/sources.csv, or SQLite db) so pytest never mutates real project state.
Uses only synthetic data — see tests/fixtures/README.md.
"""

import csv
import json
import shutil
from pathlib import Path

import pytest

from target_cash.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def isolated_project(tmp_path, monkeypatch):
    """Build a minimal isolated copy of the repo's schema/config, then chdir into it."""
    (tmp_path / "sql").mkdir()
    (tmp_path / "config").mkdir()
    (tmp_path / "docs").mkdir()
    shutil.copy(REPO_ROOT / "sql" / "schema.sql", tmp_path / "sql" / "schema.sql")
    shutil.copy(REPO_ROOT / "sql" / "views.sql", tmp_path / "sql" / "views.sql")

    metrics_csv = tmp_path / "config" / "metrics.csv"
    metrics_csv.write_text(
        "metric,statement,category,candidate_xbrl_taxonomy,candidate_xbrl_tag,unit,sign_convention,mapping_status,notes\n"
        "revenue,income_statement,flow,us-gaap,Revenues,USD,positive_inflow,candidate_unverified,\n"
    )

    model_yml = tmp_path / "config" / "model.yml"
    model_yml.write_text(
        """
company:
  name: "Synthetic Test Corp"
  cik: "9999999"
information_cutoff: "2024-12-31"
reconciliation_tolerance:
  reporting_unit_usd_millions: 1.0
  source_compatibility:
    tolerance: "n/a - pass/fail precondition"
  arithmetic_invariant:
    tolerance: "n/a - exact equality of a recomputation"
  independent_quarter_validation:
    worked_example_usd_millions: 1.5
  ytd_consistency:
    worked_example_usd_millions: 2.0
  cash_rollforward:
    worked_example_annual_usd_millions: 3.0
  excel_vs_python:
    absolute_usd_millions: 0.01
    relative_pct: 0
data_source:
  mode: "manual_upload"
  user_agent_contact: "test@example.invalid"
mapping_version: "test-v0"
paths:
  cache_dir: "data/raw"
  curated_dir: "data/curated"
  db_filename: "target_cash.db"
  manifest_csv: "docs/sources.csv"
  schema_sql: "sql/schema.sql"
  views_sql: "sql/views.sql"
  metrics_csv: "config/metrics.csv"
"""
    )

    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_fetch_manual_then_normalize_then_validate(isolated_project, capsys, tmp_path):
    # A synthetic "downloaded" source file the project owner supposedly uploaded.
    source_file = tmp_path / "uploaded_synthetic.json"
    source_file.write_text('{"synthetic": true}')

    descriptor = {
        "source_path": str(source_file),
        "dest_filename": "synthetic-10k.json",
        "accession_number": "0000000000-24-000004",
        "cik": "9999999",
        "company_name": "SYNTHETIC TEST CORP",
        "form_type": "10-K",
        "filed_at": "2024-03-15",
        "period_of_report": "2024-02-03",
        "primary_document_url": "https://example.invalid/synthetic-10k.json",
        "notes": "synthetic fixture for CLI smoke test",
    }
    descriptor_path = tmp_path / "descriptor.json"
    descriptor_path.write_text(json.dumps(descriptor))

    exit_code = main(["fetch", "--config", "config/model.yml", "--mode", "manual", "--descriptor", str(descriptor_path)])
    fetch_output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert fetch_output["status"] == "ok"
    assert (tmp_path / "data" / "raw" / "synthetic-10k.json").exists()
    assert (tmp_path / "docs" / "sources.csv").exists()

    exit_code = main(["normalize", "--config", "config/model.yml"])
    normalize_output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert normalize_output["filings_cached"] == 1
    assert normalize_output["quarterly_facts_computed_this_run"] == 0  # no reviewed mappings yet — correctly does no derivation
    assert normalize_output["quarterly_facts_in_db"] == 0

    exit_code = main(["validate", "--config", "config/model.yml"])
    validate_output = json.loads(capsys.readouterr().out)
    # No quarterly facts exist yet, so the first data gate must not report a pass.
    assert exit_code == 1
    assert validate_output["gate_passed"] is False
    assert validate_output["checks_run"] == 0


def test_fetch_manual_then_normalize_extracts_raw_facts_from_real_html(isolated_project, capsys, tmp_path):
    """Exercises the actual inline-XBRL extraction path through the CLI --
    the other normalize test above uses a plain .json fixture, which the
    HTML-suffix guard skips, so it never touches parse_inline_xbrl_facts.
    """
    synthetic_10k_html = """
    <xbrli:context id="c-1">
      <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">9999999</xbrli:identifier></xbrli:entity>
      <xbrli:period><xbrli:startDate>2024-02-04</xbrli:startDate><xbrli:endDate>2025-02-01</xbrli:endDate></xbrli:period>
    </xbrli:context>
    <span><ix:nonFraction unitRef="usd" contextRef="c-1" name="us-gaap:Revenues" scale="6" id="f-1">1,234</ix:nonFraction></span>
    """
    source_file = tmp_path / "uploaded_synthetic.htm"
    source_file.write_text(synthetic_10k_html)

    descriptor = {
        "source_path": str(source_file),
        "dest_filename": "synthetic-10k.htm",
        "accession_number": "0000000000-24-000009",
        "cik": "9999999",
        "company_name": "SYNTHETIC TEST CORP",
        "form_type": "10-K",
        "filed_at": "2024-03-15",
        "period_of_report": "2024-02-03",
    }
    descriptor_path = tmp_path / "descriptor.json"
    descriptor_path.write_text(json.dumps(descriptor))

    main(["fetch", "--config", "config/model.yml", "--mode", "manual", "--descriptor", str(descriptor_path)])
    capsys.readouterr()

    exit_code = main(["normalize", "--config", "config/model.yml"])
    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["raw_facts_newly_inserted"] == 1
    assert output["raw_facts_extracted_by_concept"] == {"us-gaap:Revenues": 1}
    assert output["filings_processed"][0]["accession_number"] == "0000000000-24-000009"

    # Running normalize again must not duplicate the row (same concept+context+accession).
    exit_code_2 = main(["normalize", "--config", "config/model.yml"])
    output_2 = json.loads(capsys.readouterr().out)
    assert exit_code_2 == 0
    assert output_2["raw_facts_newly_inserted"] == 0
    assert output_2["raw_facts_stored"] == 1


def test_fetch_manual_rejects_missing_source_file(isolated_project, capsys, tmp_path):
    descriptor = {
        "source_path": str(tmp_path / "does_not_exist.json"),
        "dest_filename": "x.json",
        "accession_number": "acc",
        "cik": "9999999",
        "company_name": "SYNTHETIC TEST CORP",
        "form_type": "10-K",
        "filed_at": "2024-03-15",
        "period_of_report": "2024-02-03",
    }
    descriptor_path = tmp_path / "descriptor.json"
    descriptor_path.write_text(json.dumps(descriptor))

    exit_code = main(["fetch", "--config", "config/model.yml", "--mode", "manual", "--descriptor", str(descriptor_path)])
    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "error"


def test_fetch_manual_refuses_duplicate_accession_with_different_hash(isolated_project, capsys, tmp_path):
    source_a = tmp_path / "a.json"
    source_a.write_text('{"version": "a"}')
    descriptor_a = {
        "source_path": str(source_a),
        "dest_filename": "same-name.json",
        "accession_number": "acc-1",
        "cik": "9999999",
        "company_name": "SYNTHETIC TEST CORP",
        "form_type": "10-K",
        "filed_at": "2024-03-15",
        "period_of_report": "2024-02-03",
    }
    descriptor_a_path = tmp_path / "descriptor_a.json"
    descriptor_a_path.write_text(json.dumps(descriptor_a))
    main(["fetch", "--config", "config/model.yml", "--mode", "manual", "--descriptor", str(descriptor_a_path)])
    capsys.readouterr()

    source_b = tmp_path / "b.json"
    source_b.write_text('{"version": "b"}')
    descriptor_b = {**descriptor_a, "source_path": str(source_b)}
    descriptor_b_path = tmp_path / "descriptor_b.json"
    descriptor_b_path.write_text(json.dumps(descriptor_b))
    exit_code = main(["fetch", "--config", "config/model.yml", "--mode", "manual", "--descriptor", str(descriptor_b_path)])
    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "error"


def test_fetch_manual_refuses_duplicate_accession_even_with_same_hash(isolated_project, capsys, tmp_path):
    # Same accession, same file content (same hash) -- still must not create a second
    # manifest/database record for an accession that's already registered.
    source = tmp_path / "same.json"
    source.write_text('{"version": "same"}')
    descriptor = {
        "source_path": str(source),
        "dest_filename": "same-name.json",
        "accession_number": "acc-dup",
        "cik": "9999999",
        "company_name": "SYNTHETIC TEST CORP",
        "form_type": "10-K",
        "filed_at": "2024-03-15",
        "period_of_report": "2024-02-03",
    }
    descriptor_path = tmp_path / "descriptor.json"
    descriptor_path.write_text(json.dumps(descriptor))

    exit_code_1 = main(["fetch", "--config", "config/model.yml", "--mode", "manual", "--descriptor", str(descriptor_path)])
    capsys.readouterr()
    assert exit_code_1 == 0

    exit_code_2 = main(["fetch", "--config", "config/model.yml", "--mode", "manual", "--descriptor", str(descriptor_path)])
    output_2 = json.loads(capsys.readouterr().out)
    assert exit_code_2 == 1
    assert output_2["status"] == "error"

    with open(tmp_path / "docs" / "sources.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1


def test_normalize_derives_quarterly_facts_for_a_reviewed_point_in_time_metric(isolated_project, capsys, tmp_path):
    """End-to-end: a reviewed metric's raw facts, once ingested from real HTML,
    get derived into quarterly_facts through the actual CLI command -- not just
    the unit-tested derive.py functions in isolation.
    """
    # Override the fixture's metrics.csv with one reviewed point-in-time metric.
    (tmp_path / "config" / "metrics.csv").write_text(
        "metric,statement,category,candidate_xbrl_taxonomy,candidate_xbrl_tag,unit,sign_convention,mapping_status,notes\n"
        "cash_and_equivalents_balance_sheet,balance_sheet,point_in_time,us-gaap,"
        "CashCashEquivalentsAndShortTermInvestments,USD,stock,reviewed,\n"
    )

    synthetic_html = """
    <xbrli:context id="c-6">
      <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">9999999</xbrli:identifier></xbrli:entity>
      <xbrli:period><xbrli:instant>2025-05-03</xbrli:instant></xbrli:period>
    </xbrli:context>
    <span><ix:nonFraction unitRef="usd" contextRef="c-6" name="us-gaap:CashCashEquivalentsAndShortTermInvestments" scale="6" id="f-1">2,887</ix:nonFraction></span>
    """
    source_file = tmp_path / "uploaded_synthetic.htm"
    source_file.write_text(synthetic_html)
    descriptor = {
        "source_path": str(source_file),
        "dest_filename": "synthetic-10q.htm",
        "accession_number": "0000000000-25-000101",
        "cik": "9999999",
        "company_name": "SYNTHETIC TEST CORP",
        "form_type": "10-Q",
        "filed_at": "2025-05-30",
        "period_of_report": "2025-05-03",
    }
    descriptor_path = tmp_path / "descriptor.json"
    descriptor_path.write_text(json.dumps(descriptor))

    main(["fetch", "--config", "config/model.yml", "--mode", "manual", "--descriptor", str(descriptor_path)])
    capsys.readouterr()

    # Default (no --persist-derived) is dry-run: derivation is computed and reported,
    # but nothing is written to quarterly_facts/lineage.
    exit_code = main(["normalize", "--config", "config/model.yml"])
    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["derivation_persisted"] is False
    assert output["quarterly_facts_computed_this_run"] == 1
    assert output["quarterly_facts_in_db"] == 0
    metric_summary = output["derivation_by_metric"]["cash_and_equivalents_balance_sheet"]
    assert metric_summary["quarterly_facts_written"] == 1
    # The other four FY2025 instants are absent from this synthetic single-fact filing,
    # so they're reported as errors, not silently skipped.
    assert len(metric_summary["errors"]) == 4

    # With --persist-derived, the same computed row is actually written -- into
    # instant_facts, since this is a point-in-time metric, never quarterly_facts
    # (which would mislabel a balance under a fiscal_quarter it doesn't belong to).
    exit_code_p = main(["normalize", "--config", "config/model.yml", "--persist-derived"])
    output_p = json.loads(capsys.readouterr().out)
    assert exit_code_p == 0
    assert output_p["derivation_persisted"] is True
    assert output_p["instant_facts_in_db"] == 1
    assert output_p["quarterly_facts_in_db"] == 0

    # Re-running with --persist-derived must not duplicate the instant_facts row
    # (recompute-and-replace, not accumulate).
    exit_code_2 = main(["normalize", "--config", "config/model.yml", "--persist-derived"])
    output_2 = json.loads(capsys.readouterr().out)
    assert exit_code_2 == 0
    assert output_2["instant_facts_in_db"] == 1


def test_validate_wires_real_checks_for_a_reviewed_flow_metric(isolated_project, capsys, tmp_path):
    """`validate` must actually compute checks from real raw_facts for reviewed
    metrics -- not report checks_run == 0 whenever nothing has been persisted.
    Uses a YTD-only flow metric (Q1 direct + six-month YTD direct, no direct
    Q2) so every derived quarter's independent validation is guaranteed
    'unavailable', with the exact required wording -- never silently a pass.
    """
    (tmp_path / "config" / "metrics.csv").write_text(
        "metric,statement,category,candidate_xbrl_taxonomy,candidate_xbrl_tag,unit,sign_convention,mapping_status,notes\n"
        "da_addback,cash_flow_statement,flow,us-gaap,DepreciationDepletionAndAmortization,USD,"
        "positive_noncash_addback,reviewed,\n"
    )

    synthetic_html = """
    <xbrli:context id="c-1">
      <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">9999999</xbrli:identifier></xbrli:entity>
      <xbrli:period><xbrli:startDate>2025-02-02</xbrli:startDate><xbrli:endDate>2025-05-03</xbrli:endDate></xbrli:period>
    </xbrli:context>
    <xbrli:context id="c-2">
      <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">9999999</xbrli:identifier></xbrli:entity>
      <xbrli:period><xbrli:startDate>2025-02-02</xbrli:startDate><xbrli:endDate>2025-08-02</xbrli:endDate></xbrli:period>
    </xbrli:context>
    <span><ix:nonFraction unitRef="usd" contextRef="c-1" name="us-gaap:DepreciationDepletionAndAmortization" scale="6" id="f-1">787</ix:nonFraction></span>
    <span><ix:nonFraction unitRef="usd" contextRef="c-2" name="us-gaap:DepreciationDepletionAndAmortization" scale="6" id="f-2">1,558</ix:nonFraction></span>
    """
    source_file = tmp_path / "uploaded_synthetic.htm"
    source_file.write_text(synthetic_html)
    descriptor = {
        "source_path": str(source_file),
        "dest_filename": "synthetic-10q.htm",
        "accession_number": "0000000000-25-000101",
        "cik": "9999999",
        "company_name": "SYNTHETIC TEST CORP",
        "form_type": "10-Q",
        "filed_at": "2025-05-30",
        "period_of_report": "2025-05-03",
    }
    descriptor_path = tmp_path / "descriptor.json"
    descriptor_path.write_text(json.dumps(descriptor))

    main(["fetch", "--config", "config/model.yml", "--mode", "manual", "--descriptor", str(descriptor_path)])
    capsys.readouterr()
    main(["normalize", "--config", "config/model.yml"])  # dry-run; derivation is recomputed fresh by validate anyway
    capsys.readouterr()

    exit_code = main(["validate", "--config", "config/model.yml"])
    output = json.loads(capsys.readouterr().out)

    # A real check ran -- this must never read 0 just because nothing was persisted.
    assert output["checks_run"] > 0
    assert len(output["source_compatibility_checks"]) == 1
    assert output["source_compatibility_checks"][0]["passed"] is True
    assert len(output["arithmetic_invariant_checks"]) == 1
    assert output["arithmetic_invariant_checks"][0]["holds"] is True

    q2_validation = next(
        v for v in output["independent_quarter_validations"] if v["check_name"].endswith(":Q2")
    )
    assert q2_validation["status"] == "unavailable"
    assert q2_validation["detail"] == "arithmetic invariant passed; independent quarter validation unavailable"

    # No quarterly_facts/lineage were ever persisted, so the database's own
    # lineage-completeness check (which reads real DB state) trivially holds,
    # and validate must not have written anything either.
    assert output["facts_missing_lineage"] == []
    exit_code_normalize_check = main(["normalize", "--config", "config/model.yml"])
    still_dry = json.loads(capsys.readouterr().out)
    assert still_dry["quarterly_facts_in_db"] == 0


def test_seed_reference_data_populates_calendar_and_rules_but_not_annual_facts(isolated_project, capsys):
    # fiscal_calendar.authority_accession is a real FK into filings -- register
    # minimal synthetic rows for every accession the reference data cites, so
    # this isolated (never-fetched-anything) database's FK enforcement doesn't
    # reject the seed. Mirrors how filings rows are always created via `fetch`
    # in production before anything references them.
    import sqlite3
    (isolated_project / "data" / "curated").mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(isolated_project / "data" / "curated" / "target_cash.db")
    conn.executescript((Path("sql") / "schema.sql").read_text())
    for accession in (
        "0000027419-22-000007", "0000027419-23-000015", "0000027419-24-000032",
        "0000027419-25-000018", "0000027419-25-000101", "0000027419-25-000118",
        "0000027419-25-000126", "0000027419-26-000016",
    ):
        conn.execute(
            "INSERT INTO filings (accession_number, cik, company_name, form_type, filed_at, "
            "period_of_report, primary_document_url, ingestion_method) VALUES (?,?,?,?,?,?,?,?)",
            (accession, "0000027419", "Target Corporation", "10-K", "2024-01-01",
             "2024-01-01", "https://example.invalid", "manual_upload"),
        )
    conn.commit()
    conn.close()

    exit_code = main(["seed-reference-data", "--config", "config/model.yml"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["status"] == "ok"
    assert output["fiscal_calendar_rows_inserted"] > 0
    assert output["concept_equivalence_rules_inserted"] == 2
    assert output["annual_analytical_tables_before"] == {
        "annual_facts": 0, "annual_lineage": 0, "annual_fact_observations": 0,
    }
    assert output["annual_analytical_tables_after"] == {
        "annual_facts": 0, "annual_lineage": 0, "annual_fact_observations": 0,
    }
    assert output["annual_analytical_tables_remain_empty"] is True

    # Idempotent: a second run inserts nothing new and still reports empty annual tables.
    second_exit_code = main(["seed-reference-data", "--config", "config/model.yml"])
    second_output = json.loads(capsys.readouterr().out)
    assert second_exit_code == 0
    assert second_output["fiscal_calendar_rows_inserted"] == 0
    assert second_output["concept_equivalence_rules_inserted"] == 0
    assert second_output["annual_analytical_tables_remain_empty"] is True
