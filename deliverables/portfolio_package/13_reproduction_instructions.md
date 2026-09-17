# Reproduction Instructions

Every number in this project can be rebuilt from scratch, from the 8
registered source filings only. This is not aspirational — it's tested
by `scripts/clean_room_rebuild.py` after every persistence milestone.

## Prerequisites

- Python 3.10+
- The repository cloned, with `data/raw/` containing the 8 cached
  source filings referenced in `docs/sources.csv` (these are the
  original downloaded SEC documents; the clean-room rebuild reads them
  from this local cache rather than re-fetching over the network, since
  the filings themselves don't change).

## 1. Install

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## 2. Run the full test suite

```bash
.venv/bin/python -m pytest -q
# Expect: 467 passed
```

## 3. Rebuild the database from scratch (clean-room proof)

```bash
.venv/bin/python scripts/clean_room_rebuild.py
```

This copies only the registered source filings and schema/config files
into a fresh temporary directory, re-runs the entire CLI pipeline
(`ingest` → `persist-annual` → `persist-forecast` → `persist-valuation`
→ `persist-capacity-taxonomy`) from nothing, and then uses
`scripts/compare_databases.py`'s
deterministic, sorted, hash-stable canonical exports to prove the
result matches the active `data/curated/target_cash.db` exactly (wall-
clock columns like `created_at` excluded, since deterministic primary
keys already prove reproducibility independent of when the rebuild ran).

## 4. Regenerate each deliverable

```bash
# Excel workbook (Milestone 5)
.venv/bin/python scripts/build_excel_model.py
.venv/bin/python scripts/verify_excel_model.py     # 41 checks

# Power BI handoff package (Milestone 6)
.venv/bin/python scripts/build_powerbi_handoff.py
.venv/bin/python scripts/verify_powerbi_handoff.py  # 168 checks

# Web decision cockpit (Milestone 7)
.venv/bin/python scripts/build_web_cockpit_data.py
.venv/bin/python scripts/verify_web_cockpit.py      # 104 checks, needs Playwright + Chromium
```

`verify_web_cockpit.py` needs `playwright` (`pip install playwright`,
included in the `dev` extra) and a Chromium binary. If Playwright's
bundled browser download is blocked in your environment (as it was in
the environment this project was built in), point it at a system
Chromium instead:

```python
# inside verify_web_cockpit.py, already set:
CHROMIUM_PATH = "/opt/pw-browsers/chromium"  # adjust to your machine
```

## 5. Preview the web cockpit locally

```bash
cd deliverables/web_cockpit
python3 -m http.server 8080
# open http://localhost:8080/index.html
```

Must be served over HTTP, not opened via `file://` — the page fetches
`data/model_data.json`, which browsers block under `file://`.

## 6. Inspect the decision log

```bash
less docs/decisions.md
```

Every material decision, every bug found and fixed, and every
limitation accepted is recorded here, in chronological order, with the
date and the milestone it belongs to.

## What "reproducible" means here, precisely

- **Deterministic IDs**: every persisted row's primary key is derived
  from its own content (scenario, metric, fiscal year, version) — never
  an autoincrement or a random UUID — so re-running persistence twice
  produces identical row counts, not duplicates.
- **Idempotent persistence**: `persist-annual`, `persist-forecast`,
  `persist-valuation`, and `persist-capacity-taxonomy` can each be
  re-run any number of times against the
  same inputs with no change in the resulting data.
- **Canonical, hash-stable exports**: `scripts/compare_databases.py`
  exports every table in a sorted, deterministic order with
  wall-clock-only columns excluded, so two independently-built
  databases can be compared byte-for-byte on their actual content.
- **No network dependency for the rebuild**: the clean-room rebuild
  reads only the locally cached source filings and the repository's own
  schema/config files — it does not re-fetch from SEC.gov, so it
  reproduces even if run offline or years later.
