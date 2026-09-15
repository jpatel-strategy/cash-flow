"""Cached retrieval layer for SEC filing data.

Two ingestion paths land in the same cache directory and the same source
manifest, so downstream code (`normalize.py`) never needs to know which one
was used:

- `fetch_via_http`: a real SEC EDGAR client, for environments with network
  egress to data.sec.gov / www.sec.gov.
- `ingest_manual_file`: registers a file the project owner downloaded by hand
  and uploaded, for environments (like this one, currently) that cannot reach
  SEC directly. See docs/limitations.md.

Neither path ever fabricates a value. If a file can't be retrieved or
ingested, the caller must stop and report the gap rather than substitute
data.
"""

from __future__ import annotations

import csv
import hashlib
import shutil
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

MANIFEST_FIELDS = [
    "accession_number",
    "cik",
    "company_name",
    "form_type",
    "filed_at",
    "period_of_report",
    "primary_document_url",
    "downloaded_at",
    "file_hash",
    "ingestion_method",
    "notes",
]


@dataclass(frozen=True)
class CachedFile:
    path: Path
    file_hash: str
    downloaded_at: str


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def ingest_manual_file(source_path: Path, cache_dir: Path, dest_filename: str) -> CachedFile:
    """Register a manually-downloaded file into the local cache.

    Copies the file (never moves — the project owner's original stays intact),
    hashes it, and returns the cache metadata needed for a manifest row.
    Raises if `source_path` does not exist; never invents a placeholder file.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Manual ingestion source not found: {source_path}")

    cache_dir.mkdir(parents=True, exist_ok=True)
    dest_path = cache_dir / dest_filename
    if dest_path.exists():
        existing_hash = sha256_of_file(dest_path)
        new_hash = sha256_of_file(source_path)
        if existing_hash != new_hash:
            raise FileExistsError(
                f"{dest_path} already exists with a different hash "
                f"({existing_hash} != {new_hash}); refusing to silently overwrite "
                "a cached source file. Remove it explicitly if replacement is intended."
            )
        return CachedFile(path=dest_path, file_hash=existing_hash, downloaded_at=_utc_now_iso())

    shutil.copyfile(source_path, dest_path)
    return CachedFile(path=dest_path, file_hash=sha256_of_file(dest_path), downloaded_at=_utc_now_iso())


def fetch_via_http(url: str, cache_dir: Path, dest_filename: str, user_agent_contact: str) -> CachedFile:
    """Fetch a URL from SEC EDGAR and cache it locally.

    Requires network egress to the target host. Not used in this environment
    (see docs/limitations.md) but implemented so the pipeline is genuinely
    reproducible where SEC access is open, per the roadmap's local-terminal
    workflow.
    """
    import requests  # imported lazily so this module loads even without `requests` installed yet

    cache_dir.mkdir(parents=True, exist_ok=True)
    dest_path = cache_dir / dest_filename
    if dest_path.exists():
        return CachedFile(path=dest_path, file_hash=sha256_of_file(dest_path), downloaded_at=_utc_now_iso())

    headers = {"User-Agent": f"target-cash-model research ({user_agent_contact})"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    dest_path.write_bytes(response.content)
    return CachedFile(path=dest_path, file_hash=sha256_of_file(dest_path), downloaded_at=_utc_now_iso())


def append_source_manifest(manifest_csv_path: Path, record: dict) -> None:
    """Append one filing's provenance to the source manifest, creating the
    header if the file is new. Never rewrites or drops existing rows, and
    never creates a duplicate record for an accession already present.
    """
    accession_number = record.get("accession_number", "")
    if manifest_csv_path.exists():
        with open(manifest_csv_path, newline="") as f:
            existing_accessions = {row.get("accession_number", "") for row in csv.DictReader(f)}
        if accession_number in existing_accessions:
            raise FileExistsError(
                f"Source manifest already has a record for accession {accession_number!r}; "
                f"refusing to create a duplicate row in {manifest_csv_path}."
            )

    row = {field: record.get(field, "") for field in MANIFEST_FIELDS}
    file_exists = manifest_csv_path.exists()
    with open(manifest_csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
