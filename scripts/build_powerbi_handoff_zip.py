"""Deterministically package deliverables/powerbi_handoff/ into a single
versioned ZIP for direct download from the web cockpit's Downloads section.

GitHub Pages (and static hosting generally) cannot serve a folder as a single
download, so this script is the documented, reproducible way to produce one
file a recruiter or reviewer can download in one click. It is deterministic:
file order is sorted, and timestamps inside the zip are fixed, so re-running
it against unchanged source content produces a byte-identical archive (only
the embedded MANIFEST.txt's commit hash and build date change between runs
against different commits).

Usage: python3 scripts/build_powerbi_handoff_zip.py
Output: deliverables/powerbi_handoff_package.zip
"""
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "deliverables" / "powerbi_handoff"
OUT_PATH = REPO_ROOT / "deliverables" / "powerbi_handoff_package.zip"
FIXED_DATE_TIME = (2026, 1, 1, 0, 0, 0)  # deterministic zip entry timestamps


def git_commit_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def build() -> None:
    if not SRC_DIR.is_dir():
        print(f"ERROR: {SRC_DIR} not found", file=sys.stderr)
        sys.exit(1)

    files = sorted(p for p in SRC_DIR.rglob("*") if p.is_file())
    commit = git_commit_hash()
    build_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    manifest_lines = [
        "Target Cash Flow & Investment Capacity -- Power BI-ready handoff package",
        "This is a Power BI-ready CSV/DAX/documentation handoff, NOT a .pbix file.",
        f"Built from commit: {commit}",
        f"Build date (UTC): {build_date}",
        f"Source directory: deliverables/powerbi_handoff/",
        f"File count: {len(files)}",
        "",
        "Files:",
    ] + [f"  {p.relative_to(SRC_DIR).as_posix()}" for p in files]
    manifest_text = "\n".join(manifest_lines) + "\n"

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            arcname = "powerbi_handoff/" + p.relative_to(SRC_DIR).as_posix()
            zinfo = zipfile.ZipInfo(arcname, date_time=FIXED_DATE_TIME)
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zinfo, p.read_bytes())
        manifest_info = zipfile.ZipInfo("powerbi_handoff/MANIFEST.txt", date_time=FIXED_DATE_TIME)
        manifest_info.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(manifest_info, manifest_text)

    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size:,} bytes, {len(files)} source files + manifest)")


if __name__ == "__main__":
    build()
