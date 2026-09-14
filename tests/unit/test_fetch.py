import csv

import pytest

from target_cash.fetch import append_source_manifest, ingest_manual_file, sha256_of_file


def test_ingest_manual_file_copies_and_hashes(tmp_path):
    source = tmp_path / "source" / "downloaded.json"
    source.parent.mkdir()
    source.write_text('{"synthetic": true}')

    cache_dir = tmp_path / "cache"
    cached = ingest_manual_file(source, cache_dir, "dest.json")

    assert cached.path == cache_dir / "dest.json"
    assert cached.path.read_text() == '{"synthetic": true}'
    assert cached.file_hash == sha256_of_file(source)
    # Original file must be left untouched (copy, not move).
    assert source.exists()


def test_ingest_manual_file_missing_source_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        ingest_manual_file(tmp_path / "does_not_exist.json", tmp_path / "cache", "dest.json")


def test_ingest_manual_file_is_idempotent_for_identical_content(tmp_path):
    source = tmp_path / "downloaded.json"
    source.write_text('{"synthetic": true}')
    cache_dir = tmp_path / "cache"

    first = ingest_manual_file(source, cache_dir, "dest.json")
    second = ingest_manual_file(source, cache_dir, "dest.json")
    assert first.file_hash == second.file_hash


def test_ingest_manual_file_refuses_silent_overwrite_of_different_content(tmp_path):
    cache_dir = tmp_path / "cache"
    source_a = tmp_path / "a.json"
    source_a.write_text('{"version": "a"}')
    ingest_manual_file(source_a, cache_dir, "dest.json")

    source_b = tmp_path / "b.json"
    source_b.write_text('{"version": "b"}')
    with pytest.raises(FileExistsError):
        ingest_manual_file(source_b, cache_dir, "dest.json")


def test_append_source_manifest_creates_header_once(tmp_path):
    manifest_path = tmp_path / "sources.csv"
    row = {
        "accession_number": "0000000000-24-000004",
        "cik": "9999999",
        "company_name": "SYNTHETIC TEST CORP",
        "form_type": "10-K",
        "filed_at": "2024-03-15",
        "period_of_report": "2024-02-03",
        "primary_document_url": "https://example.invalid/doc.htm",
        "downloaded_at": "2024-03-16T00:00:00Z",
        "file_hash": "deadbeef",
        "ingestion_method": "manual_upload",
        "notes": "",
    }
    append_source_manifest(manifest_path, row)
    append_source_manifest(manifest_path, {**row, "accession_number": "0000000000-24-000005"})

    with open(manifest_path, newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[0]["accession_number"] == "0000000000-24-000004"
    assert rows[1]["accession_number"] == "0000000000-24-000005"
