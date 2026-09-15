"""Reference metadata: Target's fiscal calendar and approved concept-equivalence
rules. Both are curated, explicit, human-verified data -- never inferred from a
formula -- seeded into the tables created by migrations 0006/0007
(src/target_cash/migrations.py).

This module deliberately seeds ONLY reference metadata. It must never write to
annual_facts, annual_lineage, or annual_fact_observations -- persisting an
annual analytical fact is not authorized by this milestone. See
docs/decisions.md, 2026-09-15 schema-implementation entry.
"""
from __future__ import annotations

import sqlite3
from datetime import date

TARGET_CIK = "0000027419"
TARGET_COMPANY_NAME = "Target Corporation"

# Confirmed directly from each fiscal year's own period boundaries (own 10-K
# where held, otherwise a corroborating comparative -- see authority_accession).
# fiscal_quarter=0 is the annual-grain sentinel (see migrations.py 0006 for why
# NULL is not used). Quarterly-grain rows exist only for FY2025, whose 10-Qs are
# already ingested; FY2021-FY2024 quarterly boundaries are deliberately left
# unpopulated rather than guessed from a formula.
FISCAL_CALENDAR_ROWS: tuple[dict, ...] = (
    # Annual-grain rows, FY2019-FY2025.
    dict(fiscal_year=2019, fiscal_quarter=0, period_start="2019-02-03", period_end="2020-02-01",
         week_count=52, is_53_week_year=0, authority_accession=None),
    dict(fiscal_year=2020, fiscal_quarter=0, period_start="2020-02-02", period_end="2021-01-30",
         week_count=52, is_53_week_year=0, authority_accession=None),
    dict(fiscal_year=2021, fiscal_quarter=0, period_start="2021-01-31", period_end="2022-01-29",
         week_count=52, is_53_week_year=0, authority_accession="0000027419-22-000007"),
    dict(fiscal_year=2022, fiscal_quarter=0, period_start="2022-01-30", period_end="2023-01-28",
         week_count=52, is_53_week_year=0, authority_accession="0000027419-23-000015"),
    dict(fiscal_year=2023, fiscal_quarter=0, period_start="2023-01-29", period_end="2024-02-03",
         week_count=53, is_53_week_year=1, authority_accession="0000027419-24-000032"),
    dict(fiscal_year=2024, fiscal_quarter=0, period_start="2024-02-04", period_end="2025-02-01",
         week_count=52, is_53_week_year=0, authority_accession="0000027419-25-000018"),
    dict(fiscal_year=2025, fiscal_quarter=0, period_start="2025-02-02", period_end="2026-01-31",
         week_count=52, is_53_week_year=0, authority_accession="0000027419-26-000016"),
    # Quarterly-grain rows, FY2025 only (from the already-ingested 10-Qs).
    dict(fiscal_year=2025, fiscal_quarter=1, period_start="2025-02-02", period_end="2025-05-03",
         week_count=13, is_53_week_year=0, authority_accession="0000027419-25-000101"),
    dict(fiscal_year=2025, fiscal_quarter=2, period_start="2025-05-04", period_end="2025-08-02",
         week_count=13, is_53_week_year=0, authority_accession="0000027419-25-000118"),
    dict(fiscal_year=2025, fiscal_quarter=3, period_start="2025-08-03", period_end="2025-11-01",
         week_count=13, is_53_week_year=0, authority_accession="0000027419-25-000126"),
    dict(fiscal_year=2025, fiscal_quarter=4, period_start="2025-11-02", period_end="2026-01-31",
         week_count=13, is_53_week_year=0, authority_accession="0000027419-26-000016"),
)


def _as_date(s: str) -> date:
    y, m, d = (int(part) for part in s.split("-"))
    return date(y, m, d)


def find_period_overlaps(rows) -> list[tuple[dict, dict]]:
    """Return every pair of rows whose [period_start, period_end] ranges overlap.

    Rows are compared only within the same fiscal-quarter "track": annual rows
    (fiscal_quarter=0) against other annual rows, and quarterly rows against
    other quarterly rows -- an annual period is *expected* to span its own
    four quarters, that is not an overlap bug. Two ranges [s1,e1] and [s2,e2]
    overlap iff s1 <= e2 and s2 <= e1.
    """
    overlaps: list[tuple[dict, dict]] = []
    annual = [r for r in rows if r["fiscal_quarter"] == 0]
    quarterly = [r for r in rows if r["fiscal_quarter"] != 0]
    for group in (annual, quarterly):
        for i, a in enumerate(group):
            a_start, a_end = _as_date(a["period_start"]), _as_date(a["period_end"])
            for b in group[i + 1:]:
                b_start, b_end = _as_date(b["period_start"]), _as_date(b["period_end"])
                if a_start <= b_end and b_start <= a_end:
                    overlaps.append((a, b))
    return overlaps


def seed_fiscal_calendar(conn: sqlite3.Connection, rows: tuple[dict, ...] = FISCAL_CALENDAR_ROWS) -> int:
    """Insert every row in `rows` into fiscal_calendar, idempotently (INSERT OR
    IGNORE on the (cik, fiscal_year, fiscal_quarter) primary key). Refuses to
    seed anything if any two rows in the same fiscal_quarter track overlap.
    Returns the number of rows newly inserted.
    """
    overlaps = find_period_overlaps(rows)
    if overlaps:
        a, b = overlaps[0]
        raise ValueError(
            f"fiscal_calendar rows overlap: fiscal_year={a['fiscal_year']} "
            f"quarter={a['fiscal_quarter']} ({a['period_start']}..{a['period_end']}) "
            f"overlaps fiscal_year={b['fiscal_year']} quarter={b['fiscal_quarter']} "
            f"({b['period_start']}..{b['period_end']}) -- refusing to seed."
        )
    inserted = 0
    with conn:
        for row in rows:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO fiscal_calendar
                    (cik, company_name, fiscal_year, fiscal_quarter, period_start, period_end,
                     week_count, is_53_week_year, authority_accession)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    TARGET_CIK, TARGET_COMPANY_NAME, row["fiscal_year"], row["fiscal_quarter"],
                    row["period_start"], row["period_end"], row["week_count"],
                    row["is_53_week_year"], row["authority_accession"],
                ),
            )
            inserted += cursor.rowcount
    return inserted


# Approved 2026-09-15 (see docs/decisions.md). Both rules are entity-scoped to
# Target (CIK 0000027419) only -- neither is a general cross-company claim.
CONCEPT_EQUIVALENCE_RULES: tuple[dict, ...] = (
    dict(
        rule_id="rule_interest_expense_v1",
        rule_version="v1",
        canonical_metric="interest_expense",
        source_concept="us-gaap:InterestExpense",
        canonical_concept="us-gaap:InterestExpenseNonoperating",
        effective_fiscal_years="FY2021-FY2023 (source_concept); FY2024-FY2025 (canonical_concept)",
        accounting_rationale=(
            "Identical Statement of Operations label ('Net interest expense') in every filing; "
            "identical competing-concept rejections (FinanceLeaseInterestExpense, InterestPaidNet) "
            "in every filing; identical arithmetic role in the pretax-income bridge "
            "(Operating income - [concept] + Net other income = Pretax income), verified exact "
            "with zero residual in all 5 fiscal years. A pure tag rename introduced with the "
            "FY2024 10-K, not a restatement -- values are continuous across the boundary "
            "(FY2023 = 502M under both tags, corroborated by both the FY2023 10-K and the "
            "FY2024 10-K)."
        ),
        evidence_reference="docs/decisions.md 2026-09-15 'Interest-expense concept equivalence'; "
                            "docs/milestone_2_proposal.md Section 3",
        review_status="reviewed",
        mapping_version="v0-pending-verification",
    ),
    dict(
        rule_id="rule_net_income_fy2021_v1",
        rule_version="v1",
        canonical_metric="net_income",
        source_concept="us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic",
        canonical_concept="us-gaap:NetIncomeLoss",
        effective_fiscal_years="FY2021 only",
        accounting_rationale=(
            "NetIncomeLossAvailableToCommonStockholdersBasic is, by definition, net income after "
            "preferred dividends, noncontrolling interests, discontinued operations, and "
            "participating-securities adjustments. For FY2021 specifically, all four are "
            "independently confirmed zero from Target's own tagged facts: "
            "PreferredStockSharesOutstanding/Issued both tagged fixed-zero; 'noncontrolling' "
            "appears only inside an unrelated tag's standard taxonomy name, no separate NCI "
            "value exists; IncomeLossFromDiscontinuedOperationsNetOfTaxAttributableToReportingEntity "
            "reported as an explicit zero for FY2021 (the same tag reports a genuine $12M for "
            "FY2019, proving it is an active, non-boilerplate concept Target does use when "
            "applicable); no participating-securities tag or text found anywhere in the filing. "
            "THIS IS NOT A GENERAL EQUIVALENCE -- it holds because of Target's specific capital "
            "structure in FY2021 alone, verified fact-by-fact, and must not be extended to any "
            "other fiscal year or entity without the same verification."
        ),
        evidence_reference="docs/decisions.md 2026-09-15 'Net-income concept equivalence'; "
                            "docs/milestone_2_proposal.md Section 4",
        review_status="reviewed",
        mapping_version="v0-pending-verification",
    ),
)


def seed_concept_equivalence_rules(conn: sqlite3.Connection, rules: tuple[dict, ...] = CONCEPT_EQUIVALENCE_RULES) -> int:
    """Insert every rule in `rules` into concept_equivalence_rules, idempotently.
    Returns the number of rows newly inserted."""
    inserted = 0
    with conn:
        for rule in rules:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO concept_equivalence_rules
                    (rule_id, rule_version, company_scope, canonical_metric, source_concept,
                     canonical_concept, effective_fiscal_years, accounting_rationale,
                     evidence_reference, review_status, mapping_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rule["rule_id"], rule["rule_version"], TARGET_CIK, rule["canonical_metric"],
                    rule["source_concept"], rule["canonical_concept"], rule["effective_fiscal_years"],
                    rule["accounting_rationale"], rule["evidence_reference"], rule["review_status"],
                    rule["mapping_version"],
                ),
            )
            inserted += cursor.rowcount
    return inserted
