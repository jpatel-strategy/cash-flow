# Test Fixtures

Every file in this directory contains **synthetic, fabricated numbers** used
only to exercise code mechanics (parsing, unit conversion, YTD subtraction,
reconciliation math, lineage tracking). None of it is Target Corporation's
actual reported data, and none of it should ever be copied into
`data/raw/`, `data/curated/`, or any output that could be mistaken for a
real financial figure.

Real filing data enters the project only through
`src/target_cash/fetch.py` (manual upload or HTTP), with full SEC
provenance recorded in `docs/sources.csv`.
