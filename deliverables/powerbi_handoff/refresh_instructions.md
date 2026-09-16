# Refresh Instructions

## Current mode: CSV import (no live database connection)

The package ships as static CSV snapshots (`data/*.csv`) because this
environment cannot host a network-reachable database for Power BI
Desktop/Service to connect to live. This is a snapshot, not a
live-refreshing report, until someone deploys the SQLite database (or a
migrated copy of it) somewhere Power BI can reach.

**To refresh with new data today:**
1. Re-run `.venv/bin/python scripts/build_powerbi_handoff.py` to
   regenerate every CSV from the current `data/curated/target_cash.db`.
2. In Power BI Desktop, *Home → Refresh* (with the CSVs re-pointed at
   the same file paths, a plain refresh picks up the new rows —
   no model or measure changes needed, since row-count changes don't
   affect the star schema shape).

## Recommended future mode: live/scheduled refresh

Once this project (or its database) is deployed somewhere reachable:

1. Migrate `data/curated/target_cash.db` (SQLite) to a server database
   Power BI can connect to directly — SQL Server, Azure SQL, or
   PostgreSQL are all straightforward targets given the schema in
   `sql/schema.sql` + `src/target_cash/migrations.py` is portable
   ANSI-ish SQL.
2. Replace each CSV import in Power BI's Power Query with a native
   database connector pointed at the same query used in
   `scripts/build_powerbi_handoff.py` for that fact/dimension.
3. Publish to the Power BI Service and configure a Scheduled Refresh
   (Settings → Datasets → Scheduled refresh) — daily is more than
   sufficient, since the underlying model only changes when a new SEC
   filing is ingested (quarterly at most).
4. If using an on-premises SQLite file directly, install the On-premises
   Data Gateway and use an ODBC connection to SQLite (Power BI has no
   native SQLite connector).

## What must NOT change on refresh

- The FY2025 10-K information cutoff (2026-03-11) that every forecast
  and valuation fact is built under. A refresh that pulls in a later
  filing must go through the same clean-room-rebuild + validation-gate
  process the rest of this project uses (see
  `scripts/clean_room_rebuild.py`), not a silent Power BI-side
  overwrite.
- Deterministic keys (`forecast_fact_id`, `valuation_result_id`, etc.)
  — Power BI's refresh is additive/replace-in-place by nature, so as
  long as the underlying export keeps using the same deterministic IDs,
  refreshed rows update in place rather than duplicating.
