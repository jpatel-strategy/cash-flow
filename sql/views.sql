-- Analytical views over the reconciled schema. Kept minimal for Milestone 1;
-- expanded as forecast/scenario tables are populated in later milestones.

-- Every quarterly_facts row that is missing at least one lineage link back to a
-- raw_fact. A non-empty result means a derived value has broken provenance and
-- must not be treated as validated.
CREATE VIEW IF NOT EXISTS v_quarterly_facts_missing_lineage AS
SELECT qf.*
FROM quarterly_facts qf
LEFT JOIN lineage l ON l.derived_fact_id = qf.quarterly_fact_id
WHERE l.lineage_id IS NULL;

-- Four constituent quarters per (metric, fiscal_year), for annual reconciliation checks.
CREATE VIEW IF NOT EXISTS v_quarterly_facts_by_year AS
SELECT
    metric,
    fiscal_year,
    MAX(CASE WHEN fiscal_quarter = 1 THEN value_normalized END) AS q1,
    MAX(CASE WHEN fiscal_quarter = 2 THEN value_normalized END) AS q2,
    MAX(CASE WHEN fiscal_quarter = 3 THEN value_normalized END) AS q3,
    MAX(CASE WHEN fiscal_quarter = 4 THEN value_normalized END) AS q4,
    COUNT(DISTINCT fiscal_quarter) AS quarters_present
FROM quarterly_facts
WHERE basis != 'point_in_time'
  AND is_current_view = 1
GROUP BY metric, fiscal_year;
