"""End-to-end smoke test for the fetch -> normalize -> validate CLI contract.

Runs against an isolated temp directory (never the real project's data/,
docs/sources.csv, or SQLite db) so pytest never mutates real project state.
Uses only synthetic data — see tests/fixtures/README.md.
"""

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
  annual_vs_quarters:
    directly_reported_flow:
      absolute_usd_millions: 0
      relative_pct: 0
    derived_ytd_flow:
      absolute_usd_millions: 1.0
      relative_pct: 0
  cash_rollforward:
    absolute_usd_millions: 1.0
    relative_pct: 0
  derived_quarter_calculation:
    absolute_usd_millions: 0
    relative_pct: 0
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
    assert normalize_output["quarterly_facts_derived"] == 0  # no reviewed mappings yet — correctly does no derivation

    exit_code = main(["validate", "--config", "config/model.yml"])
    validate_output = json.loads(capsys.readouterr().out)
    # No quarterly facts exist yet, so the first data gate must not report a pass.
    assert exit_code == 1
    assert validate_output["gate_passed"] is False
    assert validate_output["checks_run"] == 0


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
