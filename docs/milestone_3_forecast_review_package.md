# Milestone 3 Forecast -- Reviewer Audit Package

No Milestone 1 or Milestone 2 data, mapping, lineage, observation, or migration is modified by this document or by `src/target_cash/forecast.py`. Generated live by `scripts/build_milestone_3_review_package.py` -- every number below is computed by `target_cash.forecast`, not hand-transcribed.

This supersedes the prior round's summary-level `docs/milestone_3_forecast_engine_proposal.md` for reviewer purposes: that document is left in place unmodified as a historical record, but this package is the complete evidence base -- full assumption matrix, full forecast outputs, full validation and sensitivity results.

**Milestone 3A correction round applied.** This version reflects the Milestone 3A internal review and correction pass: (1) fixed the cumulative-deployable-capacity double-counting defect (Section 4c); (2) extended the capital-allocation no-double-counting proof to explicitly cover management-selected deployment and debt repayment (Section 4a, identity c); (3) added scenario narratives establishing each scenario as a coherent business condition (Section 7); (4) added validation check 21, `cumulative_capacity_no_double_counting`. As of this document's generation (the Milestone 3A commit), no forecast schema is implemented and no forecast fact is persisted -- `data/curated/target_cash.db` is unchanged. Milestone 3B (additive schema, backed-up, transactional, idempotency-verified persistence of this exact, now-corrected assumption set) follows as a separate commit; see `docs/decisions.md` for its record once complete.

---

## 1. Complete Assumption Matrix

57 (metric, scenario) rows, expanded below to 285 (metric, scenario, fiscal year) rows -- one row per forecast year, not summarized. Historical FY2021-FY2025 values are shown inline per row, in the assumption's own unit, so the selected value can be compared directly against the range it was drawn from.

**Source-fact-ID compaction**: real annual_fact_id values follow the deterministic, database-verified pattern `annual:{metric}:{fiscal_year}:latest_restated` (`annual_fact_id_for()`, verified against all 488 rows of the live database -- see Section 11). Rather than repeat up to 25 fully-expanded IDs per row, each row cites its source HISTORICAL metric(s); Section 1a below lists the complete, non-compacted fact-ID table for every metric used, so no citation is actually hidden.

| Assumption ID | Area | Name | Scenario | FY | Value | Unit | Driver Type | FY21 | FY22 | FY23 | FY24 | FY25 | Hist Min | Hist Max | Hist Median | Rationale | Depends On | Source Metrics | Cutoff | Status | Version |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| asm_finance_lease_flat_base | Balance Sheet -- Finance Leases | Finance lease liabilities | base | 2026 | 2,113.00 | USD_millions | Held flat at the FY2025 actual balance | 2,075.00 | 2,072.00 | 2,013.00 | 2,161.00 | 2,113.00 | 2,013.00 | 2,161.00 | 2,075.00 | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | (none) | finance_lease_liabilities | 2026-03-11 | proposed | v1 |
| asm_finance_lease_flat_base | Balance Sheet -- Finance Leases | Finance lease liabilities | base | 2027 | 2,113.00 | USD_millions | Held flat at the FY2025 actual balance | 2,075.00 | 2,072.00 | 2,013.00 | 2,161.00 | 2,113.00 | 2,013.00 | 2,161.00 | 2,075.00 | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | (none) | finance_lease_liabilities | 2026-03-11 | proposed | v1 |
| asm_finance_lease_flat_base | Balance Sheet -- Finance Leases | Finance lease liabilities | base | 2028 | 2,113.00 | USD_millions | Held flat at the FY2025 actual balance | 2,075.00 | 2,072.00 | 2,013.00 | 2,161.00 | 2,113.00 | 2,013.00 | 2,161.00 | 2,075.00 | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | (none) | finance_lease_liabilities | 2026-03-11 | proposed | v1 |
| asm_finance_lease_flat_base | Balance Sheet -- Finance Leases | Finance lease liabilities | base | 2029 | 2,113.00 | USD_millions | Held flat at the FY2025 actual balance | 2,075.00 | 2,072.00 | 2,013.00 | 2,161.00 | 2,113.00 | 2,013.00 | 2,161.00 | 2,075.00 | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | (none) | finance_lease_liabilities | 2026-03-11 | proposed | v1 |
| asm_finance_lease_flat_base | Balance Sheet -- Finance Leases | Finance lease liabilities | base | 2030 | 2,113.00 | USD_millions | Held flat at the FY2025 actual balance | 2,075.00 | 2,072.00 | 2,013.00 | 2,161.00 | 2,113.00 | 2,013.00 | 2,161.00 | 2,075.00 | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | (none) | finance_lease_liabilities | 2026-03-11 | proposed | v1 |
| asm_finance_lease_flat_downside | Balance Sheet -- Finance Leases | Finance lease liabilities | downside | 2026 | 2,113.00 | USD_millions | Held flat at the FY2025 actual balance | 2,075.00 | 2,072.00 | 2,013.00 | 2,161.00 | 2,113.00 | 2,013.00 | 2,161.00 | 2,075.00 | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | (none) | finance_lease_liabilities | 2026-03-11 | proposed | v1 |
| asm_finance_lease_flat_downside | Balance Sheet -- Finance Leases | Finance lease liabilities | downside | 2027 | 2,113.00 | USD_millions | Held flat at the FY2025 actual balance | 2,075.00 | 2,072.00 | 2,013.00 | 2,161.00 | 2,113.00 | 2,013.00 | 2,161.00 | 2,075.00 | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | (none) | finance_lease_liabilities | 2026-03-11 | proposed | v1 |
| asm_finance_lease_flat_downside | Balance Sheet -- Finance Leases | Finance lease liabilities | downside | 2028 | 2,113.00 | USD_millions | Held flat at the FY2025 actual balance | 2,075.00 | 2,072.00 | 2,013.00 | 2,161.00 | 2,113.00 | 2,013.00 | 2,161.00 | 2,075.00 | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | (none) | finance_lease_liabilities | 2026-03-11 | proposed | v1 |
| asm_finance_lease_flat_downside | Balance Sheet -- Finance Leases | Finance lease liabilities | downside | 2029 | 2,113.00 | USD_millions | Held flat at the FY2025 actual balance | 2,075.00 | 2,072.00 | 2,013.00 | 2,161.00 | 2,113.00 | 2,013.00 | 2,161.00 | 2,075.00 | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | (none) | finance_lease_liabilities | 2026-03-11 | proposed | v1 |
| asm_finance_lease_flat_downside | Balance Sheet -- Finance Leases | Finance lease liabilities | downside | 2030 | 2,113.00 | USD_millions | Held flat at the FY2025 actual balance | 2,075.00 | 2,072.00 | 2,013.00 | 2,161.00 | 2,113.00 | 2,013.00 | 2,161.00 | 2,075.00 | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | (none) | finance_lease_liabilities | 2026-03-11 | proposed | v1 |
| asm_finance_lease_flat_upside | Balance Sheet -- Finance Leases | Finance lease liabilities | upside | 2026 | 2,113.00 | USD_millions | Held flat at the FY2025 actual balance | 2,075.00 | 2,072.00 | 2,013.00 | 2,161.00 | 2,113.00 | 2,013.00 | 2,161.00 | 2,075.00 | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | (none) | finance_lease_liabilities | 2026-03-11 | proposed | v1 |
| asm_finance_lease_flat_upside | Balance Sheet -- Finance Leases | Finance lease liabilities | upside | 2027 | 2,113.00 | USD_millions | Held flat at the FY2025 actual balance | 2,075.00 | 2,072.00 | 2,013.00 | 2,161.00 | 2,113.00 | 2,013.00 | 2,161.00 | 2,075.00 | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | (none) | finance_lease_liabilities | 2026-03-11 | proposed | v1 |
| asm_finance_lease_flat_upside | Balance Sheet -- Finance Leases | Finance lease liabilities | upside | 2028 | 2,113.00 | USD_millions | Held flat at the FY2025 actual balance | 2,075.00 | 2,072.00 | 2,013.00 | 2,161.00 | 2,113.00 | 2,013.00 | 2,161.00 | 2,075.00 | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | (none) | finance_lease_liabilities | 2026-03-11 | proposed | v1 |
| asm_finance_lease_flat_upside | Balance Sheet -- Finance Leases | Finance lease liabilities | upside | 2029 | 2,113.00 | USD_millions | Held flat at the FY2025 actual balance | 2,075.00 | 2,072.00 | 2,013.00 | 2,161.00 | 2,113.00 | 2,013.00 | 2,161.00 | 2,075.00 | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | (none) | finance_lease_liabilities | 2026-03-11 | proposed | v1 |
| asm_finance_lease_flat_upside | Balance Sheet -- Finance Leases | Finance lease liabilities | upside | 2030 | 2,113.00 | USD_millions | Held flat at the FY2025 actual balance | 2,075.00 | 2,072.00 | 2,013.00 | 2,161.00 | 2,113.00 | 2,013.00 | 2,161.00 | 2,075.00 | Held flat at the FY2025 actual -- Target does not disclose a forward finance-lease schedule in the registered source set; modeling a trend would be unsupported speculation. | (none) | finance_lease_liabilities | 2026-03-11 | proposed | v1 |
| asm_ap_pct_base | Balance Sheet / Cash Flow -- Working Capital (Accounts Payable) | Accounts-payable driver, % of COGS | base | 2026 | 16.70 | percent | Flat %, % of COGS applied to the year-end balance | 20.65 | 16.39 | 15.54 | 17.06 | 16.72 | 15.54 | 20.65 | 16.72 | Holds near the FY2025 actual (16.72%), within the 5-year range. | (none) | accounts_payable, cost_of_sales | 2026-03-11 | proposed | v1 |
| asm_ap_pct_base | Balance Sheet / Cash Flow -- Working Capital (Accounts Payable) | Accounts-payable driver, % of COGS | base | 2027 | 16.70 | percent | Flat %, % of COGS applied to the year-end balance | 20.65 | 16.39 | 15.54 | 17.06 | 16.72 | 15.54 | 20.65 | 16.72 | Holds near the FY2025 actual (16.72%), within the 5-year range. | (none) | accounts_payable, cost_of_sales | 2026-03-11 | proposed | v1 |
| asm_ap_pct_base | Balance Sheet / Cash Flow -- Working Capital (Accounts Payable) | Accounts-payable driver, % of COGS | base | 2028 | 16.70 | percent | Flat %, % of COGS applied to the year-end balance | 20.65 | 16.39 | 15.54 | 17.06 | 16.72 | 15.54 | 20.65 | 16.72 | Holds near the FY2025 actual (16.72%), within the 5-year range. | (none) | accounts_payable, cost_of_sales | 2026-03-11 | proposed | v1 |
| asm_ap_pct_base | Balance Sheet / Cash Flow -- Working Capital (Accounts Payable) | Accounts-payable driver, % of COGS | base | 2029 | 16.70 | percent | Flat %, % of COGS applied to the year-end balance | 20.65 | 16.39 | 15.54 | 17.06 | 16.72 | 15.54 | 20.65 | 16.72 | Holds near the FY2025 actual (16.72%), within the 5-year range. | (none) | accounts_payable, cost_of_sales | 2026-03-11 | proposed | v1 |
| asm_ap_pct_base | Balance Sheet / Cash Flow -- Working Capital (Accounts Payable) | Accounts-payable driver, % of COGS | base | 2030 | 16.70 | percent | Flat %, % of COGS applied to the year-end balance | 20.65 | 16.39 | 15.54 | 17.06 | 16.72 | 15.54 | 20.65 | 16.72 | Holds near the FY2025 actual (16.72%), within the 5-year range. | (none) | accounts_payable, cost_of_sales | 2026-03-11 | proposed | v1 |
| asm_ap_pct_downside | Balance Sheet / Cash Flow -- Working Capital (Accounts Payable) | Accounts-payable driver, % of COGS | downside | 2026 | 15.50 | percent | Flat %, % of COGS applied to the year-end balance | 20.65 | 16.39 | 15.54 | 17.06 | 16.72 | 15.54 | 20.65 | 16.72 | Suppliers tighten terms under pressure, near the 5-year historical minimum (15.54%, FY2023) -- working-capital consumption. | (none) | accounts_payable, cost_of_sales | 2026-03-11 | proposed | v1 |
| asm_ap_pct_downside | Balance Sheet / Cash Flow -- Working Capital (Accounts Payable) | Accounts-payable driver, % of COGS | downside | 2027 | 15.50 | percent | Flat %, % of COGS applied to the year-end balance | 20.65 | 16.39 | 15.54 | 17.06 | 16.72 | 15.54 | 20.65 | 16.72 | Suppliers tighten terms under pressure, near the 5-year historical minimum (15.54%, FY2023) -- working-capital consumption. | (none) | accounts_payable, cost_of_sales | 2026-03-11 | proposed | v1 |
| asm_ap_pct_downside | Balance Sheet / Cash Flow -- Working Capital (Accounts Payable) | Accounts-payable driver, % of COGS | downside | 2028 | 15.50 | percent | Flat %, % of COGS applied to the year-end balance | 20.65 | 16.39 | 15.54 | 17.06 | 16.72 | 15.54 | 20.65 | 16.72 | Suppliers tighten terms under pressure, near the 5-year historical minimum (15.54%, FY2023) -- working-capital consumption. | (none) | accounts_payable, cost_of_sales | 2026-03-11 | proposed | v1 |
| asm_ap_pct_downside | Balance Sheet / Cash Flow -- Working Capital (Accounts Payable) | Accounts-payable driver, % of COGS | downside | 2029 | 15.50 | percent | Flat %, % of COGS applied to the year-end balance | 20.65 | 16.39 | 15.54 | 17.06 | 16.72 | 15.54 | 20.65 | 16.72 | Suppliers tighten terms under pressure, near the 5-year historical minimum (15.54%, FY2023) -- working-capital consumption. | (none) | accounts_payable, cost_of_sales | 2026-03-11 | proposed | v1 |
| asm_ap_pct_downside | Balance Sheet / Cash Flow -- Working Capital (Accounts Payable) | Accounts-payable driver, % of COGS | downside | 2030 | 15.50 | percent | Flat %, % of COGS applied to the year-end balance | 20.65 | 16.39 | 15.54 | 17.06 | 16.72 | 15.54 | 20.65 | 16.72 | Suppliers tighten terms under pressure, near the 5-year historical minimum (15.54%, FY2023) -- working-capital consumption. | (none) | accounts_payable, cost_of_sales | 2026-03-11 | proposed | v1 |
| asm_ap_pct_upside | Balance Sheet / Cash Flow -- Working Capital (Accounts Payable) | Accounts-payable driver, % of COGS | upside | 2026 | 17.50 | percent | Flat %, % of COGS applied to the year-end balance | 20.65 | 16.39 | 15.54 | 17.06 | 16.72 | 15.54 | 20.65 | 16.72 | Extended payables terms / improved cash conversion, near the 5-year historical maximum (20.65%, FY2021) but conservatively below it. | (none) | accounts_payable, cost_of_sales | 2026-03-11 | proposed | v1 |
| asm_ap_pct_upside | Balance Sheet / Cash Flow -- Working Capital (Accounts Payable) | Accounts-payable driver, % of COGS | upside | 2027 | 17.50 | percent | Flat %, % of COGS applied to the year-end balance | 20.65 | 16.39 | 15.54 | 17.06 | 16.72 | 15.54 | 20.65 | 16.72 | Extended payables terms / improved cash conversion, near the 5-year historical maximum (20.65%, FY2021) but conservatively below it. | (none) | accounts_payable, cost_of_sales | 2026-03-11 | proposed | v1 |
| asm_ap_pct_upside | Balance Sheet / Cash Flow -- Working Capital (Accounts Payable) | Accounts-payable driver, % of COGS | upside | 2028 | 17.50 | percent | Flat %, % of COGS applied to the year-end balance | 20.65 | 16.39 | 15.54 | 17.06 | 16.72 | 15.54 | 20.65 | 16.72 | Extended payables terms / improved cash conversion, near the 5-year historical maximum (20.65%, FY2021) but conservatively below it. | (none) | accounts_payable, cost_of_sales | 2026-03-11 | proposed | v1 |
| asm_ap_pct_upside | Balance Sheet / Cash Flow -- Working Capital (Accounts Payable) | Accounts-payable driver, % of COGS | upside | 2029 | 17.50 | percent | Flat %, % of COGS applied to the year-end balance | 20.65 | 16.39 | 15.54 | 17.06 | 16.72 | 15.54 | 20.65 | 16.72 | Extended payables terms / improved cash conversion, near the 5-year historical maximum (20.65%, FY2021) but conservatively below it. | (none) | accounts_payable, cost_of_sales | 2026-03-11 | proposed | v1 |
| asm_ap_pct_upside | Balance Sheet / Cash Flow -- Working Capital (Accounts Payable) | Accounts-payable driver, % of COGS | upside | 2030 | 17.50 | percent | Flat %, % of COGS applied to the year-end balance | 20.65 | 16.39 | 15.54 | 17.06 | 16.72 | 15.54 | 20.65 | 16.72 | Extended payables terms / improved cash conversion, near the 5-year historical maximum (20.65%, FY2021) but conservatively below it. | (none) | accounts_payable, cost_of_sales | 2026-03-11 | proposed | v1 |
| asm_inventory_pct_base | Balance Sheet / Cash Flow -- Working Capital (Inventory) | Inventory driver, % of revenue | base | 2026 | 11.80 | percent | Flat %, % of revenue applied to the year-end balance | 13.11 | 12.37 | 11.07 | 11.96 | 11.74 | 11.07 | 13.11 | 11.96 | Holds near the FY2025 actual (11.74%), within the 5-year range. | (none) | inventory, revenue | 2026-03-11 | proposed | v1 |
| asm_inventory_pct_base | Balance Sheet / Cash Flow -- Working Capital (Inventory) | Inventory driver, % of revenue | base | 2027 | 11.80 | percent | Flat %, % of revenue applied to the year-end balance | 13.11 | 12.37 | 11.07 | 11.96 | 11.74 | 11.07 | 13.11 | 11.96 | Holds near the FY2025 actual (11.74%), within the 5-year range. | (none) | inventory, revenue | 2026-03-11 | proposed | v1 |
| asm_inventory_pct_base | Balance Sheet / Cash Flow -- Working Capital (Inventory) | Inventory driver, % of revenue | base | 2028 | 11.80 | percent | Flat %, % of revenue applied to the year-end balance | 13.11 | 12.37 | 11.07 | 11.96 | 11.74 | 11.07 | 13.11 | 11.96 | Holds near the FY2025 actual (11.74%), within the 5-year range. | (none) | inventory, revenue | 2026-03-11 | proposed | v1 |
| asm_inventory_pct_base | Balance Sheet / Cash Flow -- Working Capital (Inventory) | Inventory driver, % of revenue | base | 2029 | 11.80 | percent | Flat %, % of revenue applied to the year-end balance | 13.11 | 12.37 | 11.07 | 11.96 | 11.74 | 11.07 | 13.11 | 11.96 | Holds near the FY2025 actual (11.74%), within the 5-year range. | (none) | inventory, revenue | 2026-03-11 | proposed | v1 |
| asm_inventory_pct_base | Balance Sheet / Cash Flow -- Working Capital (Inventory) | Inventory driver, % of revenue | base | 2030 | 11.80 | percent | Flat %, % of revenue applied to the year-end balance | 13.11 | 12.37 | 11.07 | 11.96 | 11.74 | 11.07 | 13.11 | 11.96 | Holds near the FY2025 actual (11.74%), within the 5-year range. | (none) | inventory, revenue | 2026-03-11 | proposed | v1 |
| asm_inventory_pct_downside | Balance Sheet / Cash Flow -- Working Capital (Inventory) | Inventory driver, % of revenue | downside | 2026 | 12.80 | percent | Flat %, % of revenue applied to the year-end balance | 13.11 | 12.37 | 11.07 | 11.96 | 11.74 | 11.07 | 13.11 | 11.96 | Inventory buildup / slower turns under demand pressure, near the 5-year historical maximum (13.11%, FY2021) -- working-capital consumption, per item 3's downside theme. | (none) | inventory, revenue | 2026-03-11 | proposed | v1 |
| asm_inventory_pct_downside | Balance Sheet / Cash Flow -- Working Capital (Inventory) | Inventory driver, % of revenue | downside | 2027 | 12.80 | percent | Flat %, % of revenue applied to the year-end balance | 13.11 | 12.37 | 11.07 | 11.96 | 11.74 | 11.07 | 13.11 | 11.96 | Inventory buildup / slower turns under demand pressure, near the 5-year historical maximum (13.11%, FY2021) -- working-capital consumption, per item 3's downside theme. | (none) | inventory, revenue | 2026-03-11 | proposed | v1 |
| asm_inventory_pct_downside | Balance Sheet / Cash Flow -- Working Capital (Inventory) | Inventory driver, % of revenue | downside | 2028 | 12.80 | percent | Flat %, % of revenue applied to the year-end balance | 13.11 | 12.37 | 11.07 | 11.96 | 11.74 | 11.07 | 13.11 | 11.96 | Inventory buildup / slower turns under demand pressure, near the 5-year historical maximum (13.11%, FY2021) -- working-capital consumption, per item 3's downside theme. | (none) | inventory, revenue | 2026-03-11 | proposed | v1 |
| asm_inventory_pct_downside | Balance Sheet / Cash Flow -- Working Capital (Inventory) | Inventory driver, % of revenue | downside | 2029 | 12.80 | percent | Flat %, % of revenue applied to the year-end balance | 13.11 | 12.37 | 11.07 | 11.96 | 11.74 | 11.07 | 13.11 | 11.96 | Inventory buildup / slower turns under demand pressure, near the 5-year historical maximum (13.11%, FY2021) -- working-capital consumption, per item 3's downside theme. | (none) | inventory, revenue | 2026-03-11 | proposed | v1 |
| asm_inventory_pct_downside | Balance Sheet / Cash Flow -- Working Capital (Inventory) | Inventory driver, % of revenue | downside | 2030 | 12.80 | percent | Flat %, % of revenue applied to the year-end balance | 13.11 | 12.37 | 11.07 | 11.96 | 11.74 | 11.07 | 13.11 | 11.96 | Inventory buildup / slower turns under demand pressure, near the 5-year historical maximum (13.11%, FY2021) -- working-capital consumption, per item 3's downside theme. | (none) | inventory, revenue | 2026-03-11 | proposed | v1 |
| asm_inventory_pct_upside | Balance Sheet / Cash Flow -- Working Capital (Inventory) | Inventory driver, % of revenue | upside | 2026 | 11.00 | percent | Flat %, % of revenue applied to the year-end balance | 13.11 | 12.37 | 11.07 | 11.96 | 11.74 | 11.07 | 13.11 | 11.96 | Improved inventory efficiency/turns, near the 5-year historical minimum (11.07%, FY2023). | (none) | inventory, revenue | 2026-03-11 | proposed | v1 |
| asm_inventory_pct_upside | Balance Sheet / Cash Flow -- Working Capital (Inventory) | Inventory driver, % of revenue | upside | 2027 | 11.00 | percent | Flat %, % of revenue applied to the year-end balance | 13.11 | 12.37 | 11.07 | 11.96 | 11.74 | 11.07 | 13.11 | 11.96 | Improved inventory efficiency/turns, near the 5-year historical minimum (11.07%, FY2023). | (none) | inventory, revenue | 2026-03-11 | proposed | v1 |
| asm_inventory_pct_upside | Balance Sheet / Cash Flow -- Working Capital (Inventory) | Inventory driver, % of revenue | upside | 2028 | 11.00 | percent | Flat %, % of revenue applied to the year-end balance | 13.11 | 12.37 | 11.07 | 11.96 | 11.74 | 11.07 | 13.11 | 11.96 | Improved inventory efficiency/turns, near the 5-year historical minimum (11.07%, FY2023). | (none) | inventory, revenue | 2026-03-11 | proposed | v1 |
| asm_inventory_pct_upside | Balance Sheet / Cash Flow -- Working Capital (Inventory) | Inventory driver, % of revenue | upside | 2029 | 11.00 | percent | Flat %, % of revenue applied to the year-end balance | 13.11 | 12.37 | 11.07 | 11.96 | 11.74 | 11.07 | 13.11 | 11.96 | Improved inventory efficiency/turns, near the 5-year historical minimum (11.07%, FY2023). | (none) | inventory, revenue | 2026-03-11 | proposed | v1 |
| asm_inventory_pct_upside | Balance Sheet / Cash Flow -- Working Capital (Inventory) | Inventory driver, % of revenue | upside | 2030 | 11.00 | percent | Flat %, % of revenue applied to the year-end balance | 13.11 | 12.37 | 11.07 | 11.96 | 11.74 | 11.07 | 13.11 | 11.96 | Improved inventory efficiency/turns, near the 5-year historical minimum (11.07%, FY2023). | (none) | inventory, revenue | 2026-03-11 | proposed | v1 |
| asm_debt_proceeds_base | Cash Flow -- Financing (Debt Issuance) | Debt issuance (proceeds) | base | 2026 | 700.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,972.00 | 2,625.00 | 0.00 | 741.00 | 1,984.00 | 0.00 | 2,625.00 | 1,972.00 | Fixed at a modest, pre-set rolling-refinancing level (proceeds roughly offsetting repayments) -- not derived from, or sized to, the resulting cash balance. | (none) | debt_proceeds | 2026-03-11 | proposed | v1 |
| asm_debt_proceeds_base | Cash Flow -- Financing (Debt Issuance) | Debt issuance (proceeds) | base | 2027 | 700.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,972.00 | 2,625.00 | 0.00 | 741.00 | 1,984.00 | 0.00 | 2,625.00 | 1,972.00 | Fixed at a modest, pre-set rolling-refinancing level (proceeds roughly offsetting repayments) -- not derived from, or sized to, the resulting cash balance. | (none) | debt_proceeds | 2026-03-11 | proposed | v1 |
| asm_debt_proceeds_base | Cash Flow -- Financing (Debt Issuance) | Debt issuance (proceeds) | base | 2028 | 700.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,972.00 | 2,625.00 | 0.00 | 741.00 | 1,984.00 | 0.00 | 2,625.00 | 1,972.00 | Fixed at a modest, pre-set rolling-refinancing level (proceeds roughly offsetting repayments) -- not derived from, or sized to, the resulting cash balance. | (none) | debt_proceeds | 2026-03-11 | proposed | v1 |
| asm_debt_proceeds_base | Cash Flow -- Financing (Debt Issuance) | Debt issuance (proceeds) | base | 2029 | 700.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,972.00 | 2,625.00 | 0.00 | 741.00 | 1,984.00 | 0.00 | 2,625.00 | 1,972.00 | Fixed at a modest, pre-set rolling-refinancing level (proceeds roughly offsetting repayments) -- not derived from, or sized to, the resulting cash balance. | (none) | debt_proceeds | 2026-03-11 | proposed | v1 |
| asm_debt_proceeds_base | Cash Flow -- Financing (Debt Issuance) | Debt issuance (proceeds) | base | 2030 | 700.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,972.00 | 2,625.00 | 0.00 | 741.00 | 1,984.00 | 0.00 | 2,625.00 | 1,972.00 | Fixed at a modest, pre-set rolling-refinancing level (proceeds roughly offsetting repayments) -- not derived from, or sized to, the resulting cash balance. | (none) | debt_proceeds | 2026-03-11 | proposed | v1 |
| asm_debt_proceeds_downside | Cash Flow -- Financing (Debt Issuance) | Debt issuance (proceeds) | downside | 2026 | 500.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,972.00 | 2,625.00 | 0.00 | 741.00 | 1,984.00 | 0.00 | 2,625.00 | 1,972.00 | A small, FIXED, pre-committed net issuance assumption. This is deliberately NOT sized to whatever cash shortfall the downside scenario produces -- see the 'minimum_cash_compliance' validation check, which raises an explicit funding warning if ending cash still falls below the minimum buffer after this fixed amount, rather than silently increasing debt further to force compliance. | (none) | debt_proceeds | 2026-03-11 | proposed | v1 |
| asm_debt_proceeds_downside | Cash Flow -- Financing (Debt Issuance) | Debt issuance (proceeds) | downside | 2027 | 500.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,972.00 | 2,625.00 | 0.00 | 741.00 | 1,984.00 | 0.00 | 2,625.00 | 1,972.00 | A small, FIXED, pre-committed net issuance assumption. This is deliberately NOT sized to whatever cash shortfall the downside scenario produces -- see the 'minimum_cash_compliance' validation check, which raises an explicit funding warning if ending cash still falls below the minimum buffer after this fixed amount, rather than silently increasing debt further to force compliance. | (none) | debt_proceeds | 2026-03-11 | proposed | v1 |
| asm_debt_proceeds_downside | Cash Flow -- Financing (Debt Issuance) | Debt issuance (proceeds) | downside | 2028 | 500.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,972.00 | 2,625.00 | 0.00 | 741.00 | 1,984.00 | 0.00 | 2,625.00 | 1,972.00 | A small, FIXED, pre-committed net issuance assumption. This is deliberately NOT sized to whatever cash shortfall the downside scenario produces -- see the 'minimum_cash_compliance' validation check, which raises an explicit funding warning if ending cash still falls below the minimum buffer after this fixed amount, rather than silently increasing debt further to force compliance. | (none) | debt_proceeds | 2026-03-11 | proposed | v1 |
| asm_debt_proceeds_downside | Cash Flow -- Financing (Debt Issuance) | Debt issuance (proceeds) | downside | 2029 | 500.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,972.00 | 2,625.00 | 0.00 | 741.00 | 1,984.00 | 0.00 | 2,625.00 | 1,972.00 | A small, FIXED, pre-committed net issuance assumption. This is deliberately NOT sized to whatever cash shortfall the downside scenario produces -- see the 'minimum_cash_compliance' validation check, which raises an explicit funding warning if ending cash still falls below the minimum buffer after this fixed amount, rather than silently increasing debt further to force compliance. | (none) | debt_proceeds | 2026-03-11 | proposed | v1 |
| asm_debt_proceeds_downside | Cash Flow -- Financing (Debt Issuance) | Debt issuance (proceeds) | downside | 2030 | 500.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,972.00 | 2,625.00 | 0.00 | 741.00 | 1,984.00 | 0.00 | 2,625.00 | 1,972.00 | A small, FIXED, pre-committed net issuance assumption. This is deliberately NOT sized to whatever cash shortfall the downside scenario produces -- see the 'minimum_cash_compliance' validation check, which raises an explicit funding warning if ending cash still falls below the minimum buffer after this fixed amount, rather than silently increasing debt further to force compliance. | (none) | debt_proceeds | 2026-03-11 | proposed | v1 |
| asm_debt_proceeds_upside | Cash Flow -- Financing (Debt Issuance) | Debt issuance (proceeds) | upside | 2026 | 300.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,972.00 | 2,625.00 | 0.00 | 741.00 | 1,984.00 | 0.00 | 2,625.00 | 1,972.00 | Fixed net repayment, funded by stronger scenario FCF -- a deleveraging policy choice, not a residual plug. | (none) | debt_proceeds | 2026-03-11 | proposed | v1 |
| asm_debt_proceeds_upside | Cash Flow -- Financing (Debt Issuance) | Debt issuance (proceeds) | upside | 2027 | 300.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,972.00 | 2,625.00 | 0.00 | 741.00 | 1,984.00 | 0.00 | 2,625.00 | 1,972.00 | Fixed net repayment, funded by stronger scenario FCF -- a deleveraging policy choice, not a residual plug. | (none) | debt_proceeds | 2026-03-11 | proposed | v1 |
| asm_debt_proceeds_upside | Cash Flow -- Financing (Debt Issuance) | Debt issuance (proceeds) | upside | 2028 | 300.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,972.00 | 2,625.00 | 0.00 | 741.00 | 1,984.00 | 0.00 | 2,625.00 | 1,972.00 | Fixed net repayment, funded by stronger scenario FCF -- a deleveraging policy choice, not a residual plug. | (none) | debt_proceeds | 2026-03-11 | proposed | v1 |
| asm_debt_proceeds_upside | Cash Flow -- Financing (Debt Issuance) | Debt issuance (proceeds) | upside | 2029 | 300.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,972.00 | 2,625.00 | 0.00 | 741.00 | 1,984.00 | 0.00 | 2,625.00 | 1,972.00 | Fixed net repayment, funded by stronger scenario FCF -- a deleveraging policy choice, not a residual plug. | (none) | debt_proceeds | 2026-03-11 | proposed | v1 |
| asm_debt_proceeds_upside | Cash Flow -- Financing (Debt Issuance) | Debt issuance (proceeds) | upside | 2030 | 300.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,972.00 | 2,625.00 | 0.00 | 741.00 | 1,984.00 | 0.00 | 2,625.00 | 1,972.00 | Fixed net repayment, funded by stronger scenario FCF -- a deleveraging policy choice, not a residual plug. | (none) | debt_proceeds | 2026-03-11 | proposed | v1 |
| asm_debt_repayments_base | Cash Flow -- Financing (Debt Repayment) | Debt repayments | base | 2026 | 700.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,147.00 | 163.00 | 147.00 | 1,139.00 | 1,643.00 | 147.00 | 1,643.00 | 1,139.00 | Fixed at a modest, pre-set rolling-refinancing level (proceeds roughly offsetting repayments) -- not derived from, or sized to, the resulting cash balance. | (none) | debt_repayments | 2026-03-11 | proposed | v1 |
| asm_debt_repayments_base | Cash Flow -- Financing (Debt Repayment) | Debt repayments | base | 2027 | 700.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,147.00 | 163.00 | 147.00 | 1,139.00 | 1,643.00 | 147.00 | 1,643.00 | 1,139.00 | Fixed at a modest, pre-set rolling-refinancing level (proceeds roughly offsetting repayments) -- not derived from, or sized to, the resulting cash balance. | (none) | debt_repayments | 2026-03-11 | proposed | v1 |
| asm_debt_repayments_base | Cash Flow -- Financing (Debt Repayment) | Debt repayments | base | 2028 | 700.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,147.00 | 163.00 | 147.00 | 1,139.00 | 1,643.00 | 147.00 | 1,643.00 | 1,139.00 | Fixed at a modest, pre-set rolling-refinancing level (proceeds roughly offsetting repayments) -- not derived from, or sized to, the resulting cash balance. | (none) | debt_repayments | 2026-03-11 | proposed | v1 |
| asm_debt_repayments_base | Cash Flow -- Financing (Debt Repayment) | Debt repayments | base | 2029 | 700.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,147.00 | 163.00 | 147.00 | 1,139.00 | 1,643.00 | 147.00 | 1,643.00 | 1,139.00 | Fixed at a modest, pre-set rolling-refinancing level (proceeds roughly offsetting repayments) -- not derived from, or sized to, the resulting cash balance. | (none) | debt_repayments | 2026-03-11 | proposed | v1 |
| asm_debt_repayments_base | Cash Flow -- Financing (Debt Repayment) | Debt repayments | base | 2030 | 700.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,147.00 | 163.00 | 147.00 | 1,139.00 | 1,643.00 | 147.00 | 1,643.00 | 1,139.00 | Fixed at a modest, pre-set rolling-refinancing level (proceeds roughly offsetting repayments) -- not derived from, or sized to, the resulting cash balance. | (none) | debt_repayments | 2026-03-11 | proposed | v1 |
| asm_debt_repayments_downside | Cash Flow -- Financing (Debt Repayment) | Debt repayments | downside | 2026 | 300.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,147.00 | 163.00 | 147.00 | 1,139.00 | 1,643.00 | 147.00 | 1,643.00 | 1,139.00 | A small, FIXED, pre-committed net issuance assumption. This is deliberately NOT sized to whatever cash shortfall the downside scenario produces -- see the 'minimum_cash_compliance' validation check, which raises an explicit funding warning if ending cash still falls below the minimum buffer after this fixed amount, rather than silently increasing debt further to force compliance. | (none) | debt_repayments | 2026-03-11 | proposed | v1 |
| asm_debt_repayments_downside | Cash Flow -- Financing (Debt Repayment) | Debt repayments | downside | 2027 | 300.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,147.00 | 163.00 | 147.00 | 1,139.00 | 1,643.00 | 147.00 | 1,643.00 | 1,139.00 | A small, FIXED, pre-committed net issuance assumption. This is deliberately NOT sized to whatever cash shortfall the downside scenario produces -- see the 'minimum_cash_compliance' validation check, which raises an explicit funding warning if ending cash still falls below the minimum buffer after this fixed amount, rather than silently increasing debt further to force compliance. | (none) | debt_repayments | 2026-03-11 | proposed | v1 |
| asm_debt_repayments_downside | Cash Flow -- Financing (Debt Repayment) | Debt repayments | downside | 2028 | 300.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,147.00 | 163.00 | 147.00 | 1,139.00 | 1,643.00 | 147.00 | 1,643.00 | 1,139.00 | A small, FIXED, pre-committed net issuance assumption. This is deliberately NOT sized to whatever cash shortfall the downside scenario produces -- see the 'minimum_cash_compliance' validation check, which raises an explicit funding warning if ending cash still falls below the minimum buffer after this fixed amount, rather than silently increasing debt further to force compliance. | (none) | debt_repayments | 2026-03-11 | proposed | v1 |
| asm_debt_repayments_downside | Cash Flow -- Financing (Debt Repayment) | Debt repayments | downside | 2029 | 300.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,147.00 | 163.00 | 147.00 | 1,139.00 | 1,643.00 | 147.00 | 1,643.00 | 1,139.00 | A small, FIXED, pre-committed net issuance assumption. This is deliberately NOT sized to whatever cash shortfall the downside scenario produces -- see the 'minimum_cash_compliance' validation check, which raises an explicit funding warning if ending cash still falls below the minimum buffer after this fixed amount, rather than silently increasing debt further to force compliance. | (none) | debt_repayments | 2026-03-11 | proposed | v1 |
| asm_debt_repayments_downside | Cash Flow -- Financing (Debt Repayment) | Debt repayments | downside | 2030 | 300.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,147.00 | 163.00 | 147.00 | 1,139.00 | 1,643.00 | 147.00 | 1,643.00 | 1,139.00 | A small, FIXED, pre-committed net issuance assumption. This is deliberately NOT sized to whatever cash shortfall the downside scenario produces -- see the 'minimum_cash_compliance' validation check, which raises an explicit funding warning if ending cash still falls below the minimum buffer after this fixed amount, rather than silently increasing debt further to force compliance. | (none) | debt_repayments | 2026-03-11 | proposed | v1 |
| asm_debt_repayments_upside | Cash Flow -- Financing (Debt Repayment) | Debt repayments | upside | 2026 | 1,000.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,147.00 | 163.00 | 147.00 | 1,139.00 | 1,643.00 | 147.00 | 1,643.00 | 1,139.00 | Fixed net repayment, funded by stronger scenario FCF -- a deleveraging policy choice, not a residual plug. | (none) | debt_repayments | 2026-03-11 | proposed | v1 |
| asm_debt_repayments_upside | Cash Flow -- Financing (Debt Repayment) | Debt repayments | upside | 2027 | 1,000.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,147.00 | 163.00 | 147.00 | 1,139.00 | 1,643.00 | 147.00 | 1,643.00 | 1,139.00 | Fixed net repayment, funded by stronger scenario FCF -- a deleveraging policy choice, not a residual plug. | (none) | debt_repayments | 2026-03-11 | proposed | v1 |
| asm_debt_repayments_upside | Cash Flow -- Financing (Debt Repayment) | Debt repayments | upside | 2028 | 1,000.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,147.00 | 163.00 | 147.00 | 1,139.00 | 1,643.00 | 147.00 | 1,643.00 | 1,139.00 | Fixed net repayment, funded by stronger scenario FCF -- a deleveraging policy choice, not a residual plug. | (none) | debt_repayments | 2026-03-11 | proposed | v1 |
| asm_debt_repayments_upside | Cash Flow -- Financing (Debt Repayment) | Debt repayments | upside | 2029 | 1,000.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,147.00 | 163.00 | 147.00 | 1,139.00 | 1,643.00 | 147.00 | 1,643.00 | 1,139.00 | Fixed net repayment, funded by stronger scenario FCF -- a deleveraging policy choice, not a residual plug. | (none) | debt_repayments | 2026-03-11 | proposed | v1 |
| asm_debt_repayments_upside | Cash Flow -- Financing (Debt Repayment) | Debt repayments | upside | 2030 | 1,000.00 | USD_millions | Fixed $M/yr, identical every forecast year within a scenario | 1,147.00 | 163.00 | 147.00 | 1,139.00 | 1,643.00 | 147.00 | 1,643.00 | 1,139.00 | Fixed net repayment, funded by stronger scenario FCF -- a deleveraging policy choice, not a residual plug. | (none) | debt_repayments | 2026-03-11 | proposed | v1 |
| asm_dividend_growth_base | Cash Flow -- Financing (Dividends) | Dividend per share growth | base | 2026 | 2.00 | percent | Flat %/yr, applied recursively to a derived $/share proxy | N/A | 25.75 | 9.98 | 1.96 | 1.71 | 1.71 | 25.75 | 9.98 | Continues the recent (FY2024-FY2025) decelerated per-share dividend growth pace of ~1.8%/yr, rounded up modestly. | (none) | dividends_paid, diluted_shares | 2026-03-11 | proposed | v1 |
| asm_dividend_growth_base | Cash Flow -- Financing (Dividends) | Dividend per share growth | base | 2027 | 2.00 | percent | Flat %/yr, applied recursively to a derived $/share proxy | N/A | 25.75 | 9.98 | 1.96 | 1.71 | 1.71 | 25.75 | 9.98 | Continues the recent (FY2024-FY2025) decelerated per-share dividend growth pace of ~1.8%/yr, rounded up modestly. | (none) | dividends_paid, diluted_shares | 2026-03-11 | proposed | v1 |
| asm_dividend_growth_base | Cash Flow -- Financing (Dividends) | Dividend per share growth | base | 2028 | 2.00 | percent | Flat %/yr, applied recursively to a derived $/share proxy | N/A | 25.75 | 9.98 | 1.96 | 1.71 | 1.71 | 25.75 | 9.98 | Continues the recent (FY2024-FY2025) decelerated per-share dividend growth pace of ~1.8%/yr, rounded up modestly. | (none) | dividends_paid, diluted_shares | 2026-03-11 | proposed | v1 |
| asm_dividend_growth_base | Cash Flow -- Financing (Dividends) | Dividend per share growth | base | 2029 | 2.00 | percent | Flat %/yr, applied recursively to a derived $/share proxy | N/A | 25.75 | 9.98 | 1.96 | 1.71 | 1.71 | 25.75 | 9.98 | Continues the recent (FY2024-FY2025) decelerated per-share dividend growth pace of ~1.8%/yr, rounded up modestly. | (none) | dividends_paid, diluted_shares | 2026-03-11 | proposed | v1 |
| asm_dividend_growth_base | Cash Flow -- Financing (Dividends) | Dividend per share growth | base | 2030 | 2.00 | percent | Flat %/yr, applied recursively to a derived $/share proxy | N/A | 25.75 | 9.98 | 1.96 | 1.71 | 1.71 | 25.75 | 9.98 | Continues the recent (FY2024-FY2025) decelerated per-share dividend growth pace of ~1.8%/yr, rounded up modestly. | (none) | dividends_paid, diluted_shares | 2026-03-11 | proposed | v1 |
| asm_dividend_growth_downside | Cash Flow -- Financing (Dividends) | Dividend per share growth | downside | 2026 | 0.00 | percent | Flat %/yr, applied recursively to a derived $/share proxy | N/A | 25.75 | 9.98 | 1.96 | 1.71 | 1.71 | 25.75 | 9.98 | Dividend frozen (0% growth), not cut -- Target's dividends_paid has grown in every one of the 5 historical years in this dataset with no observed cut, so an outright reduction is not modeled as a plausible base case for the downside scenario; freezing (not increasing) is the appropriate downside floor. | (none) | dividends_paid, diluted_shares | 2026-03-11 | proposed | v1 |
| asm_dividend_growth_downside | Cash Flow -- Financing (Dividends) | Dividend per share growth | downside | 2027 | 0.00 | percent | Flat %/yr, applied recursively to a derived $/share proxy | N/A | 25.75 | 9.98 | 1.96 | 1.71 | 1.71 | 25.75 | 9.98 | Dividend frozen (0% growth), not cut -- Target's dividends_paid has grown in every one of the 5 historical years in this dataset with no observed cut, so an outright reduction is not modeled as a plausible base case for the downside scenario; freezing (not increasing) is the appropriate downside floor. | (none) | dividends_paid, diluted_shares | 2026-03-11 | proposed | v1 |
| asm_dividend_growth_downside | Cash Flow -- Financing (Dividends) | Dividend per share growth | downside | 2028 | 0.00 | percent | Flat %/yr, applied recursively to a derived $/share proxy | N/A | 25.75 | 9.98 | 1.96 | 1.71 | 1.71 | 25.75 | 9.98 | Dividend frozen (0% growth), not cut -- Target's dividends_paid has grown in every one of the 5 historical years in this dataset with no observed cut, so an outright reduction is not modeled as a plausible base case for the downside scenario; freezing (not increasing) is the appropriate downside floor. | (none) | dividends_paid, diluted_shares | 2026-03-11 | proposed | v1 |
| asm_dividend_growth_downside | Cash Flow -- Financing (Dividends) | Dividend per share growth | downside | 2029 | 0.00 | percent | Flat %/yr, applied recursively to a derived $/share proxy | N/A | 25.75 | 9.98 | 1.96 | 1.71 | 1.71 | 25.75 | 9.98 | Dividend frozen (0% growth), not cut -- Target's dividends_paid has grown in every one of the 5 historical years in this dataset with no observed cut, so an outright reduction is not modeled as a plausible base case for the downside scenario; freezing (not increasing) is the appropriate downside floor. | (none) | dividends_paid, diluted_shares | 2026-03-11 | proposed | v1 |
| asm_dividend_growth_downside | Cash Flow -- Financing (Dividends) | Dividend per share growth | downside | 2030 | 0.00 | percent | Flat %/yr, applied recursively to a derived $/share proxy | N/A | 25.75 | 9.98 | 1.96 | 1.71 | 1.71 | 25.75 | 9.98 | Dividend frozen (0% growth), not cut -- Target's dividends_paid has grown in every one of the 5 historical years in this dataset with no observed cut, so an outright reduction is not modeled as a plausible base case for the downside scenario; freezing (not increasing) is the appropriate downside floor. | (none) | dividends_paid, diluted_shares | 2026-03-11 | proposed | v1 |
| asm_dividend_growth_upside | Cash Flow -- Financing (Dividends) | Dividend per share growth | upside | 2026 | 4.00 | percent | Flat %/yr, applied recursively to a derived $/share proxy | N/A | 25.75 | 9.98 | 1.96 | 1.71 | 1.71 | 25.75 | 9.98 | Stronger payout growth supported by better earnings, still well below the earlier, one-time large hikes (+25.8% FY2022, +10.1% FY2023) which followed unusually high FY2021 earnings, not treated as repeatable. | (none) | dividends_paid, diluted_shares | 2026-03-11 | proposed | v1 |
| asm_dividend_growth_upside | Cash Flow -- Financing (Dividends) | Dividend per share growth | upside | 2027 | 4.00 | percent | Flat %/yr, applied recursively to a derived $/share proxy | N/A | 25.75 | 9.98 | 1.96 | 1.71 | 1.71 | 25.75 | 9.98 | Stronger payout growth supported by better earnings, still well below the earlier, one-time large hikes (+25.8% FY2022, +10.1% FY2023) which followed unusually high FY2021 earnings, not treated as repeatable. | (none) | dividends_paid, diluted_shares | 2026-03-11 | proposed | v1 |
| asm_dividend_growth_upside | Cash Flow -- Financing (Dividends) | Dividend per share growth | upside | 2028 | 4.00 | percent | Flat %/yr, applied recursively to a derived $/share proxy | N/A | 25.75 | 9.98 | 1.96 | 1.71 | 1.71 | 25.75 | 9.98 | Stronger payout growth supported by better earnings, still well below the earlier, one-time large hikes (+25.8% FY2022, +10.1% FY2023) which followed unusually high FY2021 earnings, not treated as repeatable. | (none) | dividends_paid, diluted_shares | 2026-03-11 | proposed | v1 |
| asm_dividend_growth_upside | Cash Flow -- Financing (Dividends) | Dividend per share growth | upside | 2029 | 4.00 | percent | Flat %/yr, applied recursively to a derived $/share proxy | N/A | 25.75 | 9.98 | 1.96 | 1.71 | 1.71 | 25.75 | 9.98 | Stronger payout growth supported by better earnings, still well below the earlier, one-time large hikes (+25.8% FY2022, +10.1% FY2023) which followed unusually high FY2021 earnings, not treated as repeatable. | (none) | dividends_paid, diluted_shares | 2026-03-11 | proposed | v1 |
| asm_dividend_growth_upside | Cash Flow -- Financing (Dividends) | Dividend per share growth | upside | 2030 | 4.00 | percent | Flat %/yr, applied recursively to a derived $/share proxy | N/A | 25.75 | 9.98 | 1.96 | 1.71 | 1.71 | 25.75 | 9.98 | Stronger payout growth supported by better earnings, still well below the earlier, one-time large hikes (+25.8% FY2022, +10.1% FY2023) which followed unusually high FY2021 earnings, not treated as repeatable. | (none) | dividends_paid, diluted_shares | 2026-03-11 | proposed | v1 |
| asm_buyback_payout_base | Cash Flow -- Financing (Share Repurchases) | Share repurchase payout ratio | base | 2026 | 40.00 | percent | Flat % of (FCF - dividends), floored at $0 -- never negative | 203.45 | N/A | 0.00 | 41.44 | 52.17 | 0.00 | 203.45 | 52.17 | A pre-set target payout ratio of (FCF - dividends), applied identically regardless of the resulting cash balance -- an input assumption, never solved backward to hit a cash or deployable-capacity target (the explicit 'not an automatic balancing plug' requirement). Historical repurchases range from $0 to $7,188M with no fixed dollar pattern, making a payout-ratio policy more defensible than a flat dollar figure. | dividend_per_share_growth_pct | share_repurchases, free_cash_flow, dividends_paid | 2026-03-11 | proposed | v1 |
| asm_buyback_payout_base | Cash Flow -- Financing (Share Repurchases) | Share repurchase payout ratio | base | 2027 | 40.00 | percent | Flat % of (FCF - dividends), floored at $0 -- never negative | 203.45 | N/A | 0.00 | 41.44 | 52.17 | 0.00 | 203.45 | 52.17 | A pre-set target payout ratio of (FCF - dividends), applied identically regardless of the resulting cash balance -- an input assumption, never solved backward to hit a cash or deployable-capacity target (the explicit 'not an automatic balancing plug' requirement). Historical repurchases range from $0 to $7,188M with no fixed dollar pattern, making a payout-ratio policy more defensible than a flat dollar figure. | dividend_per_share_growth_pct | share_repurchases, free_cash_flow, dividends_paid | 2026-03-11 | proposed | v1 |
| asm_buyback_payout_base | Cash Flow -- Financing (Share Repurchases) | Share repurchase payout ratio | base | 2028 | 40.00 | percent | Flat % of (FCF - dividends), floored at $0 -- never negative | 203.45 | N/A | 0.00 | 41.44 | 52.17 | 0.00 | 203.45 | 52.17 | A pre-set target payout ratio of (FCF - dividends), applied identically regardless of the resulting cash balance -- an input assumption, never solved backward to hit a cash or deployable-capacity target (the explicit 'not an automatic balancing plug' requirement). Historical repurchases range from $0 to $7,188M with no fixed dollar pattern, making a payout-ratio policy more defensible than a flat dollar figure. | dividend_per_share_growth_pct | share_repurchases, free_cash_flow, dividends_paid | 2026-03-11 | proposed | v1 |
| asm_buyback_payout_base | Cash Flow -- Financing (Share Repurchases) | Share repurchase payout ratio | base | 2029 | 40.00 | percent | Flat % of (FCF - dividends), floored at $0 -- never negative | 203.45 | N/A | 0.00 | 41.44 | 52.17 | 0.00 | 203.45 | 52.17 | A pre-set target payout ratio of (FCF - dividends), applied identically regardless of the resulting cash balance -- an input assumption, never solved backward to hit a cash or deployable-capacity target (the explicit 'not an automatic balancing plug' requirement). Historical repurchases range from $0 to $7,188M with no fixed dollar pattern, making a payout-ratio policy more defensible than a flat dollar figure. | dividend_per_share_growth_pct | share_repurchases, free_cash_flow, dividends_paid | 2026-03-11 | proposed | v1 |
| asm_buyback_payout_base | Cash Flow -- Financing (Share Repurchases) | Share repurchase payout ratio | base | 2030 | 40.00 | percent | Flat % of (FCF - dividends), floored at $0 -- never negative | 203.45 | N/A | 0.00 | 41.44 | 52.17 | 0.00 | 203.45 | 52.17 | A pre-set target payout ratio of (FCF - dividends), applied identically regardless of the resulting cash balance -- an input assumption, never solved backward to hit a cash or deployable-capacity target (the explicit 'not an automatic balancing plug' requirement). Historical repurchases range from $0 to $7,188M with no fixed dollar pattern, making a payout-ratio policy more defensible than a flat dollar figure. | dividend_per_share_growth_pct | share_repurchases, free_cash_flow, dividends_paid | 2026-03-11 | proposed | v1 |
| asm_buyback_payout_downside | Cash Flow -- Financing (Share Repurchases) | Share repurchase payout ratio | downside | 2026 | 0.00 | percent | Flat % of (FCF - dividends), floored at $0 -- never negative | 203.45 | N/A | 0.00 | 41.44 | 52.17 | 0.00 | 203.45 | 52.17 | No repurchases -- capital preservation under pressure. | dividend_per_share_growth_pct | share_repurchases, free_cash_flow, dividends_paid | 2026-03-11 | proposed | v1 |
| asm_buyback_payout_downside | Cash Flow -- Financing (Share Repurchases) | Share repurchase payout ratio | downside | 2027 | 0.00 | percent | Flat % of (FCF - dividends), floored at $0 -- never negative | 203.45 | N/A | 0.00 | 41.44 | 52.17 | 0.00 | 203.45 | 52.17 | No repurchases -- capital preservation under pressure. | dividend_per_share_growth_pct | share_repurchases, free_cash_flow, dividends_paid | 2026-03-11 | proposed | v1 |
| asm_buyback_payout_downside | Cash Flow -- Financing (Share Repurchases) | Share repurchase payout ratio | downside | 2028 | 0.00 | percent | Flat % of (FCF - dividends), floored at $0 -- never negative | 203.45 | N/A | 0.00 | 41.44 | 52.17 | 0.00 | 203.45 | 52.17 | No repurchases -- capital preservation under pressure. | dividend_per_share_growth_pct | share_repurchases, free_cash_flow, dividends_paid | 2026-03-11 | proposed | v1 |
| asm_buyback_payout_downside | Cash Flow -- Financing (Share Repurchases) | Share repurchase payout ratio | downside | 2029 | 0.00 | percent | Flat % of (FCF - dividends), floored at $0 -- never negative | 203.45 | N/A | 0.00 | 41.44 | 52.17 | 0.00 | 203.45 | 52.17 | No repurchases -- capital preservation under pressure. | dividend_per_share_growth_pct | share_repurchases, free_cash_flow, dividends_paid | 2026-03-11 | proposed | v1 |
| asm_buyback_payout_downside | Cash Flow -- Financing (Share Repurchases) | Share repurchase payout ratio | downside | 2030 | 0.00 | percent | Flat % of (FCF - dividends), floored at $0 -- never negative | 203.45 | N/A | 0.00 | 41.44 | 52.17 | 0.00 | 203.45 | 52.17 | No repurchases -- capital preservation under pressure. | dividend_per_share_growth_pct | share_repurchases, free_cash_flow, dividends_paid | 2026-03-11 | proposed | v1 |
| asm_buyback_payout_upside | Cash Flow -- Financing (Share Repurchases) | Share repurchase payout ratio | upside | 2026 | 55.00 | percent | Flat % of (FCF - dividends), floored at $0 -- never negative | 203.45 | N/A | 0.00 | 41.44 | 52.17 | 0.00 | 203.45 | 52.17 | A higher target payout ratio, reflecting stronger FCF generation and capital return capacity in this scenario. | dividend_per_share_growth_pct | share_repurchases, free_cash_flow, dividends_paid | 2026-03-11 | proposed | v1 |
| asm_buyback_payout_upside | Cash Flow -- Financing (Share Repurchases) | Share repurchase payout ratio | upside | 2027 | 55.00 | percent | Flat % of (FCF - dividends), floored at $0 -- never negative | 203.45 | N/A | 0.00 | 41.44 | 52.17 | 0.00 | 203.45 | 52.17 | A higher target payout ratio, reflecting stronger FCF generation and capital return capacity in this scenario. | dividend_per_share_growth_pct | share_repurchases, free_cash_flow, dividends_paid | 2026-03-11 | proposed | v1 |
| asm_buyback_payout_upside | Cash Flow -- Financing (Share Repurchases) | Share repurchase payout ratio | upside | 2028 | 55.00 | percent | Flat % of (FCF - dividends), floored at $0 -- never negative | 203.45 | N/A | 0.00 | 41.44 | 52.17 | 0.00 | 203.45 | 52.17 | A higher target payout ratio, reflecting stronger FCF generation and capital return capacity in this scenario. | dividend_per_share_growth_pct | share_repurchases, free_cash_flow, dividends_paid | 2026-03-11 | proposed | v1 |
| asm_buyback_payout_upside | Cash Flow -- Financing (Share Repurchases) | Share repurchase payout ratio | upside | 2029 | 55.00 | percent | Flat % of (FCF - dividends), floored at $0 -- never negative | 203.45 | N/A | 0.00 | 41.44 | 52.17 | 0.00 | 203.45 | 52.17 | A higher target payout ratio, reflecting stronger FCF generation and capital return capacity in this scenario. | dividend_per_share_growth_pct | share_repurchases, free_cash_flow, dividends_paid | 2026-03-11 | proposed | v1 |
| asm_buyback_payout_upside | Cash Flow -- Financing (Share Repurchases) | Share repurchase payout ratio | upside | 2030 | 55.00 | percent | Flat % of (FCF - dividends), floored at $0 -- never negative | 203.45 | N/A | 0.00 | 41.44 | 52.17 | 0.00 | 203.45 | 52.17 | A higher target payout ratio, reflecting stronger FCF generation and capital return capacity in this scenario. | dividend_per_share_growth_pct | share_repurchases, free_cash_flow, dividends_paid | 2026-03-11 | proposed | v1 |
| asm_capex_pct_base | Cash Flow -- Investing (CapEx) | Capital expenditures, % of revenue | base | 2026 | 3.60 | percent | Flat %/yr, % of revenue applied directly | 3.34 | 5.07 | 4.47 | 2.71 | 3.56 | 2.71 | 5.07 | 3.56 | Near the FY2025 actual (3.56%) and the 5-year median (3.56%) -- maintenance-plus-modest-growth continuation, using PaymentsToAcquirePropertyPlantAndEquipment, never total investing cash flow. | (none) | capital_expenditure, revenue | 2026-03-11 | proposed | v1 |
| asm_capex_pct_base | Cash Flow -- Investing (CapEx) | Capital expenditures, % of revenue | base | 2027 | 3.60 | percent | Flat %/yr, % of revenue applied directly | 3.34 | 5.07 | 4.47 | 2.71 | 3.56 | 2.71 | 5.07 | 3.56 | Near the FY2025 actual (3.56%) and the 5-year median (3.56%) -- maintenance-plus-modest-growth continuation, using PaymentsToAcquirePropertyPlantAndEquipment, never total investing cash flow. | (none) | capital_expenditure, revenue | 2026-03-11 | proposed | v1 |
| asm_capex_pct_base | Cash Flow -- Investing (CapEx) | Capital expenditures, % of revenue | base | 2028 | 3.60 | percent | Flat %/yr, % of revenue applied directly | 3.34 | 5.07 | 4.47 | 2.71 | 3.56 | 2.71 | 5.07 | 3.56 | Near the FY2025 actual (3.56%) and the 5-year median (3.56%) -- maintenance-plus-modest-growth continuation, using PaymentsToAcquirePropertyPlantAndEquipment, never total investing cash flow. | (none) | capital_expenditure, revenue | 2026-03-11 | proposed | v1 |
| asm_capex_pct_base | Cash Flow -- Investing (CapEx) | Capital expenditures, % of revenue | base | 2029 | 3.60 | percent | Flat %/yr, % of revenue applied directly | 3.34 | 5.07 | 4.47 | 2.71 | 3.56 | 2.71 | 5.07 | 3.56 | Near the FY2025 actual (3.56%) and the 5-year median (3.56%) -- maintenance-plus-modest-growth continuation, using PaymentsToAcquirePropertyPlantAndEquipment, never total investing cash flow. | (none) | capital_expenditure, revenue | 2026-03-11 | proposed | v1 |
| asm_capex_pct_base | Cash Flow -- Investing (CapEx) | Capital expenditures, % of revenue | base | 2030 | 3.60 | percent | Flat %/yr, % of revenue applied directly | 3.34 | 5.07 | 4.47 | 2.71 | 3.56 | 2.71 | 5.07 | 3.56 | Near the FY2025 actual (3.56%) and the 5-year median (3.56%) -- maintenance-plus-modest-growth continuation, using PaymentsToAcquirePropertyPlantAndEquipment, never total investing cash flow. | (none) | capital_expenditure, revenue | 2026-03-11 | proposed | v1 |
| asm_capex_pct_downside | Cash Flow -- Investing (CapEx) | Capital expenditures, % of revenue | downside | 2026 | 2.80 | percent | Flat %/yr, % of revenue applied directly | 3.34 | 5.07 | 4.47 | 2.71 | 3.56 | 2.71 | 5.07 | 3.56 | Capital discipline / deferred growth investment under pressure, near the 5-year historical minimum (2.71%, FY2024) -- Target does not disclose a maintenance-only CapEx figure, so this is not claimed as 'maintenance CapEx', only as a low-end plausible total CapEx level. | (none) | capital_expenditure, revenue | 2026-03-11 | proposed | v1 |
| asm_capex_pct_downside | Cash Flow -- Investing (CapEx) | Capital expenditures, % of revenue | downside | 2027 | 2.80 | percent | Flat %/yr, % of revenue applied directly | 3.34 | 5.07 | 4.47 | 2.71 | 3.56 | 2.71 | 5.07 | 3.56 | Capital discipline / deferred growth investment under pressure, near the 5-year historical minimum (2.71%, FY2024) -- Target does not disclose a maintenance-only CapEx figure, so this is not claimed as 'maintenance CapEx', only as a low-end plausible total CapEx level. | (none) | capital_expenditure, revenue | 2026-03-11 | proposed | v1 |
| asm_capex_pct_downside | Cash Flow -- Investing (CapEx) | Capital expenditures, % of revenue | downside | 2028 | 2.80 | percent | Flat %/yr, % of revenue applied directly | 3.34 | 5.07 | 4.47 | 2.71 | 3.56 | 2.71 | 5.07 | 3.56 | Capital discipline / deferred growth investment under pressure, near the 5-year historical minimum (2.71%, FY2024) -- Target does not disclose a maintenance-only CapEx figure, so this is not claimed as 'maintenance CapEx', only as a low-end plausible total CapEx level. | (none) | capital_expenditure, revenue | 2026-03-11 | proposed | v1 |
| asm_capex_pct_downside | Cash Flow -- Investing (CapEx) | Capital expenditures, % of revenue | downside | 2029 | 2.80 | percent | Flat %/yr, % of revenue applied directly | 3.34 | 5.07 | 4.47 | 2.71 | 3.56 | 2.71 | 5.07 | 3.56 | Capital discipline / deferred growth investment under pressure, near the 5-year historical minimum (2.71%, FY2024) -- Target does not disclose a maintenance-only CapEx figure, so this is not claimed as 'maintenance CapEx', only as a low-end plausible total CapEx level. | (none) | capital_expenditure, revenue | 2026-03-11 | proposed | v1 |
| asm_capex_pct_downside | Cash Flow -- Investing (CapEx) | Capital expenditures, % of revenue | downside | 2030 | 2.80 | percent | Flat %/yr, % of revenue applied directly | 3.34 | 5.07 | 4.47 | 2.71 | 3.56 | 2.71 | 5.07 | 3.56 | Capital discipline / deferred growth investment under pressure, near the 5-year historical minimum (2.71%, FY2024) -- Target does not disclose a maintenance-only CapEx figure, so this is not claimed as 'maintenance CapEx', only as a low-end plausible total CapEx level. | (none) | capital_expenditure, revenue | 2026-03-11 | proposed | v1 |
| asm_capex_pct_upside | Cash Flow -- Investing (CapEx) | Capital expenditures, % of revenue | upside | 2026 | 4.30 | percent | Flat %/yr, % of revenue applied directly | 3.34 | 5.07 | 4.47 | 2.71 | 3.56 | 2.71 | 5.07 | 3.56 | Elevated growth CapEx (new stores/supply chain/digital investment supporting the stronger revenue growth in this scenario) -- higher CapEx in the upside case is economically appropriate here (item 12), staying below the 5-year historical maximum (5.07%, FY2022). | (none) | capital_expenditure, revenue | 2026-03-11 | proposed | v1 |
| asm_capex_pct_upside | Cash Flow -- Investing (CapEx) | Capital expenditures, % of revenue | upside | 2027 | 4.30 | percent | Flat %/yr, % of revenue applied directly | 3.34 | 5.07 | 4.47 | 2.71 | 3.56 | 2.71 | 5.07 | 3.56 | Elevated growth CapEx (new stores/supply chain/digital investment supporting the stronger revenue growth in this scenario) -- higher CapEx in the upside case is economically appropriate here (item 12), staying below the 5-year historical maximum (5.07%, FY2022). | (none) | capital_expenditure, revenue | 2026-03-11 | proposed | v1 |
| asm_capex_pct_upside | Cash Flow -- Investing (CapEx) | Capital expenditures, % of revenue | upside | 2028 | 4.30 | percent | Flat %/yr, % of revenue applied directly | 3.34 | 5.07 | 4.47 | 2.71 | 3.56 | 2.71 | 5.07 | 3.56 | Elevated growth CapEx (new stores/supply chain/digital investment supporting the stronger revenue growth in this scenario) -- higher CapEx in the upside case is economically appropriate here (item 12), staying below the 5-year historical maximum (5.07%, FY2022). | (none) | capital_expenditure, revenue | 2026-03-11 | proposed | v1 |
| asm_capex_pct_upside | Cash Flow -- Investing (CapEx) | Capital expenditures, % of revenue | upside | 2029 | 4.30 | percent | Flat %/yr, % of revenue applied directly | 3.34 | 5.07 | 4.47 | 2.71 | 3.56 | 2.71 | 5.07 | 3.56 | Elevated growth CapEx (new stores/supply chain/digital investment supporting the stronger revenue growth in this scenario) -- higher CapEx in the upside case is economically appropriate here (item 12), staying below the 5-year historical maximum (5.07%, FY2022). | (none) | capital_expenditure, revenue | 2026-03-11 | proposed | v1 |
| asm_capex_pct_upside | Cash Flow -- Investing (CapEx) | Capital expenditures, % of revenue | upside | 2030 | 4.30 | percent | Flat %/yr, % of revenue applied directly | 3.34 | 5.07 | 4.47 | 2.71 | 3.56 | 2.71 | 5.07 | 3.56 | Elevated growth CapEx (new stores/supply chain/digital investment supporting the stronger revenue growth in this scenario) -- higher CapEx in the upside case is economically appropriate here (item 12), staying below the 5-year historical maximum (5.07%, FY2022). | (none) | capital_expenditure, revenue | 2026-03-11 | proposed | v1 |
| asm_da_addback_pct_base_2026..asm_da_addback_pct_base_2030 (5 rows) | Cash Flow -- Operating (D&A Add-back) | D&A cash-flow add-back, % of revenue | base | 2026 | 3.12 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.49 | 2.47 | 2.61 | 2.80 | 2.99 | 2.47 | 2.99 | 2.61 | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | capex_pct_of_revenue | depreciation_amortization_cfo_addback, revenue | 2026-03-11 | proposed | v1 |
| asm_da_addback_pct_base_2026..asm_da_addback_pct_base_2030 (5 rows) | Cash Flow -- Operating (D&A Add-back) | D&A cash-flow add-back, % of revenue | base | 2027 | 3.24 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.49 | 2.47 | 2.61 | 2.80 | 2.99 | 2.47 | 2.99 | 2.61 | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | capex_pct_of_revenue | depreciation_amortization_cfo_addback, revenue | 2026-03-11 | proposed | v1 |
| asm_da_addback_pct_base_2026..asm_da_addback_pct_base_2030 (5 rows) | Cash Flow -- Operating (D&A Add-back) | D&A cash-flow add-back, % of revenue | base | 2028 | 3.37 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.49 | 2.47 | 2.61 | 2.80 | 2.99 | 2.47 | 2.99 | 2.61 | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | capex_pct_of_revenue | depreciation_amortization_cfo_addback, revenue | 2026-03-11 | proposed | v1 |
| asm_da_addback_pct_base_2026..asm_da_addback_pct_base_2030 (5 rows) | Cash Flow -- Operating (D&A Add-back) | D&A cash-flow add-back, % of revenue | base | 2029 | 3.49 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.49 | 2.47 | 2.61 | 2.80 | 2.99 | 2.47 | 2.99 | 2.61 | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | capex_pct_of_revenue | depreciation_amortization_cfo_addback, revenue | 2026-03-11 | proposed | v1 |
| asm_da_addback_pct_base_2026..asm_da_addback_pct_base_2030 (5 rows) | Cash Flow -- Operating (D&A Add-back) | D&A cash-flow add-back, % of revenue | base | 2030 | 3.61 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.49 | 2.47 | 2.61 | 2.80 | 2.99 | 2.47 | 2.99 | 2.61 | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | capex_pct_of_revenue | depreciation_amortization_cfo_addback, revenue | 2026-03-11 | proposed | v1 |
| asm_da_addback_pct_downside_2026..asm_da_addback_pct_downside_2030 (5 rows) | Cash Flow -- Operating (D&A Add-back) | D&A cash-flow add-back, % of revenue | downside | 2026 | 3.07 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.49 | 2.47 | 2.61 | 2.80 | 2.99 | 2.47 | 2.99 | 2.61 | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | capex_pct_of_revenue | depreciation_amortization_cfo_addback, revenue | 2026-03-11 | proposed | v1 |
| asm_da_addback_pct_downside_2026..asm_da_addback_pct_downside_2030 (5 rows) | Cash Flow -- Operating (D&A Add-back) | D&A cash-flow add-back, % of revenue | downside | 2027 | 3.19 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.49 | 2.47 | 2.61 | 2.80 | 2.99 | 2.47 | 2.99 | 2.61 | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | capex_pct_of_revenue | depreciation_amortization_cfo_addback, revenue | 2026-03-11 | proposed | v1 |
| asm_da_addback_pct_downside_2026..asm_da_addback_pct_downside_2030 (5 rows) | Cash Flow -- Operating (D&A Add-back) | D&A cash-flow add-back, % of revenue | downside | 2028 | 3.31 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.49 | 2.47 | 2.61 | 2.80 | 2.99 | 2.47 | 2.99 | 2.61 | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | capex_pct_of_revenue | depreciation_amortization_cfo_addback, revenue | 2026-03-11 | proposed | v1 |
| asm_da_addback_pct_downside_2026..asm_da_addback_pct_downside_2030 (5 rows) | Cash Flow -- Operating (D&A Add-back) | D&A cash-flow add-back, % of revenue | downside | 2029 | 3.44 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.49 | 2.47 | 2.61 | 2.80 | 2.99 | 2.47 | 2.99 | 2.61 | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | capex_pct_of_revenue | depreciation_amortization_cfo_addback, revenue | 2026-03-11 | proposed | v1 |
| asm_da_addback_pct_downside_2026..asm_da_addback_pct_downside_2030 (5 rows) | Cash Flow -- Operating (D&A Add-back) | D&A cash-flow add-back, % of revenue | downside | 2030 | 3.56 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.49 | 2.47 | 2.61 | 2.80 | 2.99 | 2.47 | 2.99 | 2.61 | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | capex_pct_of_revenue | depreciation_amortization_cfo_addback, revenue | 2026-03-11 | proposed | v1 |
| asm_da_addback_pct_upside_2026..asm_da_addback_pct_upside_2030 (5 rows) | Cash Flow -- Operating (D&A Add-back) | D&A cash-flow add-back, % of revenue | upside | 2026 | 3.17 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.49 | 2.47 | 2.61 | 2.80 | 2.99 | 2.47 | 2.99 | 2.61 | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | capex_pct_of_revenue | depreciation_amortization_cfo_addback, revenue | 2026-03-11 | proposed | v1 |
| asm_da_addback_pct_upside_2026..asm_da_addback_pct_upside_2030 (5 rows) | Cash Flow -- Operating (D&A Add-back) | D&A cash-flow add-back, % of revenue | upside | 2027 | 3.29 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.49 | 2.47 | 2.61 | 2.80 | 2.99 | 2.47 | 2.99 | 2.61 | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | capex_pct_of_revenue | depreciation_amortization_cfo_addback, revenue | 2026-03-11 | proposed | v1 |
| asm_da_addback_pct_upside_2026..asm_da_addback_pct_upside_2030 (5 rows) | Cash Flow -- Operating (D&A Add-back) | D&A cash-flow add-back, % of revenue | upside | 2028 | 3.42 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.49 | 2.47 | 2.61 | 2.80 | 2.99 | 2.47 | 2.99 | 2.61 | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | capex_pct_of_revenue | depreciation_amortization_cfo_addback, revenue | 2026-03-11 | proposed | v1 |
| asm_da_addback_pct_upside_2026..asm_da_addback_pct_upside_2030 (5 rows) | Cash Flow -- Operating (D&A Add-back) | D&A cash-flow add-back, % of revenue | upside | 2029 | 3.54 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.49 | 2.47 | 2.61 | 2.80 | 2.99 | 2.47 | 2.99 | 2.61 | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | capex_pct_of_revenue | depreciation_amortization_cfo_addback, revenue | 2026-03-11 | proposed | v1 |
| asm_da_addback_pct_upside_2026..asm_da_addback_pct_upside_2030 (5 rows) | Cash Flow -- Operating (D&A Add-back) | D&A cash-flow add-back, % of revenue | upside | 2030 | 3.66 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.49 | 2.47 | 2.61 | 2.80 | 2.99 | 2.47 | 2.99 | 2.61 | Modeled independently of the opex D&A line (never summed with it -- item 5's double-counting warning) using DepreciationDepletionAndAmortization's own FY2021-FY2025 trend as a percent of revenue, adjusted by scenario CapEx intensity. | capex_pct_of_revenue | depreciation_amortization_cfo_addback, revenue | 2026-03-11 | proposed | v1 |
| asm_other_opcf_base | Cash Flow -- Operating (Other Adjustments) | Other operating cash adjustments | base | 2026 | 150.00 | USD_millions | Flat $M/yr (never solved backward from a CFO target -- see Section 3) | N/A | 126.00 | 1,458.00 | 194.00 | -282.00 | -282.00 | 1,458.00 | 194.00 | Near the historical median of the derived 'other operating cash adjustments' residual (stock-based comp, deferred taxes, other non-cash items, other working capital not separately modeled) -- see docs/milestone_3_forecast_review_package.md Section 3 for the full derivation and component discussion. This is NOT solved backward to hit a CFO target. | (none) | operating_cash_flow, net_income, depreciation_amortization_cfo_addback, inventory, accounts_payable | 2026-03-11 | proposed | v1 |
| asm_other_opcf_base | Cash Flow -- Operating (Other Adjustments) | Other operating cash adjustments | base | 2027 | 150.00 | USD_millions | Flat $M/yr (never solved backward from a CFO target -- see Section 3) | N/A | 126.00 | 1,458.00 | 194.00 | -282.00 | -282.00 | 1,458.00 | 194.00 | Near the historical median of the derived 'other operating cash adjustments' residual (stock-based comp, deferred taxes, other non-cash items, other working capital not separately modeled) -- see docs/milestone_3_forecast_review_package.md Section 3 for the full derivation and component discussion. This is NOT solved backward to hit a CFO target. | (none) | operating_cash_flow, net_income, depreciation_amortization_cfo_addback, inventory, accounts_payable | 2026-03-11 | proposed | v1 |
| asm_other_opcf_base | Cash Flow -- Operating (Other Adjustments) | Other operating cash adjustments | base | 2028 | 150.00 | USD_millions | Flat $M/yr (never solved backward from a CFO target -- see Section 3) | N/A | 126.00 | 1,458.00 | 194.00 | -282.00 | -282.00 | 1,458.00 | 194.00 | Near the historical median of the derived 'other operating cash adjustments' residual (stock-based comp, deferred taxes, other non-cash items, other working capital not separately modeled) -- see docs/milestone_3_forecast_review_package.md Section 3 for the full derivation and component discussion. This is NOT solved backward to hit a CFO target. | (none) | operating_cash_flow, net_income, depreciation_amortization_cfo_addback, inventory, accounts_payable | 2026-03-11 | proposed | v1 |
| asm_other_opcf_base | Cash Flow -- Operating (Other Adjustments) | Other operating cash adjustments | base | 2029 | 150.00 | USD_millions | Flat $M/yr (never solved backward from a CFO target -- see Section 3) | N/A | 126.00 | 1,458.00 | 194.00 | -282.00 | -282.00 | 1,458.00 | 194.00 | Near the historical median of the derived 'other operating cash adjustments' residual (stock-based comp, deferred taxes, other non-cash items, other working capital not separately modeled) -- see docs/milestone_3_forecast_review_package.md Section 3 for the full derivation and component discussion. This is NOT solved backward to hit a CFO target. | (none) | operating_cash_flow, net_income, depreciation_amortization_cfo_addback, inventory, accounts_payable | 2026-03-11 | proposed | v1 |
| asm_other_opcf_base | Cash Flow -- Operating (Other Adjustments) | Other operating cash adjustments | base | 2030 | 150.00 | USD_millions | Flat $M/yr (never solved backward from a CFO target -- see Section 3) | N/A | 126.00 | 1,458.00 | 194.00 | -282.00 | -282.00 | 1,458.00 | 194.00 | Near the historical median of the derived 'other operating cash adjustments' residual (stock-based comp, deferred taxes, other non-cash items, other working capital not separately modeled) -- see docs/milestone_3_forecast_review_package.md Section 3 for the full derivation and component discussion. This is NOT solved backward to hit a CFO target. | (none) | operating_cash_flow, net_income, depreciation_amortization_cfo_addback, inventory, accounts_payable | 2026-03-11 | proposed | v1 |
| asm_other_opcf_downside | Cash Flow -- Operating (Other Adjustments) | Other operating cash adjustments | downside | 2026 | 50.00 | USD_millions | Flat $M/yr (never solved backward from a CFO target -- see Section 3) | N/A | 126.00 | 1,458.00 | 194.00 | -282.00 | -282.00 | 1,458.00 | 194.00 | Less favorable working-capital/other items, within the observed historical range. | (none) | operating_cash_flow, net_income, depreciation_amortization_cfo_addback, inventory, accounts_payable | 2026-03-11 | proposed | v1 |
| asm_other_opcf_downside | Cash Flow -- Operating (Other Adjustments) | Other operating cash adjustments | downside | 2027 | 50.00 | USD_millions | Flat $M/yr (never solved backward from a CFO target -- see Section 3) | N/A | 126.00 | 1,458.00 | 194.00 | -282.00 | -282.00 | 1,458.00 | 194.00 | Less favorable working-capital/other items, within the observed historical range. | (none) | operating_cash_flow, net_income, depreciation_amortization_cfo_addback, inventory, accounts_payable | 2026-03-11 | proposed | v1 |
| asm_other_opcf_downside | Cash Flow -- Operating (Other Adjustments) | Other operating cash adjustments | downside | 2028 | 50.00 | USD_millions | Flat $M/yr (never solved backward from a CFO target -- see Section 3) | N/A | 126.00 | 1,458.00 | 194.00 | -282.00 | -282.00 | 1,458.00 | 194.00 | Less favorable working-capital/other items, within the observed historical range. | (none) | operating_cash_flow, net_income, depreciation_amortization_cfo_addback, inventory, accounts_payable | 2026-03-11 | proposed | v1 |
| asm_other_opcf_downside | Cash Flow -- Operating (Other Adjustments) | Other operating cash adjustments | downside | 2029 | 50.00 | USD_millions | Flat $M/yr (never solved backward from a CFO target -- see Section 3) | N/A | 126.00 | 1,458.00 | 194.00 | -282.00 | -282.00 | 1,458.00 | 194.00 | Less favorable working-capital/other items, within the observed historical range. | (none) | operating_cash_flow, net_income, depreciation_amortization_cfo_addback, inventory, accounts_payable | 2026-03-11 | proposed | v1 |
| asm_other_opcf_downside | Cash Flow -- Operating (Other Adjustments) | Other operating cash adjustments | downside | 2030 | 50.00 | USD_millions | Flat $M/yr (never solved backward from a CFO target -- see Section 3) | N/A | 126.00 | 1,458.00 | 194.00 | -282.00 | -282.00 | 1,458.00 | 194.00 | Less favorable working-capital/other items, within the observed historical range. | (none) | operating_cash_flow, net_income, depreciation_amortization_cfo_addback, inventory, accounts_payable | 2026-03-11 | proposed | v1 |
| asm_other_opcf_upside | Cash Flow -- Operating (Other Adjustments) | Other operating cash adjustments | upside | 2026 | 250.00 | USD_millions | Flat $M/yr (never solved backward from a CFO target -- see Section 3) | N/A | 126.00 | 1,458.00 | 194.00 | -282.00 | -282.00 | 1,458.00 | 194.00 | More favorable working-capital/other items, within the observed historical range. | (none) | operating_cash_flow, net_income, depreciation_amortization_cfo_addback, inventory, accounts_payable | 2026-03-11 | proposed | v1 |
| asm_other_opcf_upside | Cash Flow -- Operating (Other Adjustments) | Other operating cash adjustments | upside | 2027 | 250.00 | USD_millions | Flat $M/yr (never solved backward from a CFO target -- see Section 3) | N/A | 126.00 | 1,458.00 | 194.00 | -282.00 | -282.00 | 1,458.00 | 194.00 | More favorable working-capital/other items, within the observed historical range. | (none) | operating_cash_flow, net_income, depreciation_amortization_cfo_addback, inventory, accounts_payable | 2026-03-11 | proposed | v1 |
| asm_other_opcf_upside | Cash Flow -- Operating (Other Adjustments) | Other operating cash adjustments | upside | 2028 | 250.00 | USD_millions | Flat $M/yr (never solved backward from a CFO target -- see Section 3) | N/A | 126.00 | 1,458.00 | 194.00 | -282.00 | -282.00 | 1,458.00 | 194.00 | More favorable working-capital/other items, within the observed historical range. | (none) | operating_cash_flow, net_income, depreciation_amortization_cfo_addback, inventory, accounts_payable | 2026-03-11 | proposed | v1 |
| asm_other_opcf_upside | Cash Flow -- Operating (Other Adjustments) | Other operating cash adjustments | upside | 2029 | 250.00 | USD_millions | Flat $M/yr (never solved backward from a CFO target -- see Section 3) | N/A | 126.00 | 1,458.00 | 194.00 | -282.00 | -282.00 | 1,458.00 | 194.00 | More favorable working-capital/other items, within the observed historical range. | (none) | operating_cash_flow, net_income, depreciation_amortization_cfo_addback, inventory, accounts_payable | 2026-03-11 | proposed | v1 |
| asm_other_opcf_upside | Cash Flow -- Operating (Other Adjustments) | Other operating cash adjustments | upside | 2030 | 250.00 | USD_millions | Flat $M/yr (never solved backward from a CFO target -- see Section 3) | N/A | 126.00 | 1,458.00 | 194.00 | -282.00 | -282.00 | 1,458.00 | 194.00 | More favorable working-capital/other items, within the observed historical range. | (none) | operating_cash_flow, net_income, depreciation_amortization_cfo_addback, inventory, accounts_payable | 2026-03-11 | proposed | v1 |
| asm_gross_margin_base_2026..asm_gross_margin_base_2030 (5 rows) | Income Statement -- Cost of Sales / Gross Profit | Gross margin (COGS-derived) | base | 2026 | 27.93 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 29.28 | 24.57 | 27.54 | 28.21 | 27.93 | 24.57 | 29.28 | 27.93 | Holds near the FY2023-FY2025 recent average (~27.9-28.2%) -- explicitly NOT reverting to the FY2021 peak of 29.28%, which followed a pandemic-driven demand/mix shift item 3 requires treating as non-repeatable. | (none) | gross_profit, revenue | 2026-03-11 | proposed | v1 |
| asm_gross_margin_base_2026..asm_gross_margin_base_2030 (5 rows) | Income Statement -- Cost of Sales / Gross Profit | Gross margin (COGS-derived) | base | 2027 | 27.95 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 29.28 | 24.57 | 27.54 | 28.21 | 27.93 | 24.57 | 29.28 | 27.93 | Holds near the FY2023-FY2025 recent average (~27.9-28.2%) -- explicitly NOT reverting to the FY2021 peak of 29.28%, which followed a pandemic-driven demand/mix shift item 3 requires treating as non-repeatable. | (none) | gross_profit, revenue | 2026-03-11 | proposed | v1 |
| asm_gross_margin_base_2026..asm_gross_margin_base_2030 (5 rows) | Income Statement -- Cost of Sales / Gross Profit | Gross margin (COGS-derived) | base | 2028 | 27.96 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 29.28 | 24.57 | 27.54 | 28.21 | 27.93 | 24.57 | 29.28 | 27.93 | Holds near the FY2023-FY2025 recent average (~27.9-28.2%) -- explicitly NOT reverting to the FY2021 peak of 29.28%, which followed a pandemic-driven demand/mix shift item 3 requires treating as non-repeatable. | (none) | gross_profit, revenue | 2026-03-11 | proposed | v1 |
| asm_gross_margin_base_2026..asm_gross_margin_base_2030 (5 rows) | Income Statement -- Cost of Sales / Gross Profit | Gross margin (COGS-derived) | base | 2029 | 27.98 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 29.28 | 24.57 | 27.54 | 28.21 | 27.93 | 24.57 | 29.28 | 27.93 | Holds near the FY2023-FY2025 recent average (~27.9-28.2%) -- explicitly NOT reverting to the FY2021 peak of 29.28%, which followed a pandemic-driven demand/mix shift item 3 requires treating as non-repeatable. | (none) | gross_profit, revenue | 2026-03-11 | proposed | v1 |
| asm_gross_margin_base_2026..asm_gross_margin_base_2030 (5 rows) | Income Statement -- Cost of Sales / Gross Profit | Gross margin (COGS-derived) | base | 2030 | 28.00 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 29.28 | 24.57 | 27.54 | 28.21 | 27.93 | 24.57 | 29.28 | 27.93 | Holds near the FY2023-FY2025 recent average (~27.9-28.2%) -- explicitly NOT reverting to the FY2021 peak of 29.28%, which followed a pandemic-driven demand/mix shift item 3 requires treating as non-repeatable. | (none) | gross_profit, revenue | 2026-03-11 | proposed | v1 |
| asm_gross_margin_downside_2026..asm_gross_margin_downside_2030 (5 rows) | Income Statement -- Cost of Sales / Gross Profit | Gross margin (COGS-derived) | downside | 2026 | 27.93 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 29.28 | 24.57 | 27.54 | 28.21 | 27.93 | 24.57 | 29.28 | 27.93 | Gradual, partial reversion toward (not matching) the FY2022 trough of 24.57% -- a moderate margin-pressure case, bounded well short of the full historical worst year. | (none) | gross_profit, revenue | 2026-03-11 | proposed | v1 |
| asm_gross_margin_downside_2026..asm_gross_margin_downside_2030 (5 rows) | Income Statement -- Cost of Sales / Gross Profit | Gross margin (COGS-derived) | downside | 2027 | 27.52 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 29.28 | 24.57 | 27.54 | 28.21 | 27.93 | 24.57 | 29.28 | 27.93 | Gradual, partial reversion toward (not matching) the FY2022 trough of 24.57% -- a moderate margin-pressure case, bounded well short of the full historical worst year. | (none) | gross_profit, revenue | 2026-03-11 | proposed | v1 |
| asm_gross_margin_downside_2026..asm_gross_margin_downside_2030 (5 rows) | Income Statement -- Cost of Sales / Gross Profit | Gross margin (COGS-derived) | downside | 2028 | 27.11 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 29.28 | 24.57 | 27.54 | 28.21 | 27.93 | 24.57 | 29.28 | 27.93 | Gradual, partial reversion toward (not matching) the FY2022 trough of 24.57% -- a moderate margin-pressure case, bounded well short of the full historical worst year. | (none) | gross_profit, revenue | 2026-03-11 | proposed | v1 |
| asm_gross_margin_downside_2026..asm_gross_margin_downside_2030 (5 rows) | Income Statement -- Cost of Sales / Gross Profit | Gross margin (COGS-derived) | downside | 2029 | 26.71 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 29.28 | 24.57 | 27.54 | 28.21 | 27.93 | 24.57 | 29.28 | 27.93 | Gradual, partial reversion toward (not matching) the FY2022 trough of 24.57% -- a moderate margin-pressure case, bounded well short of the full historical worst year. | (none) | gross_profit, revenue | 2026-03-11 | proposed | v1 |
| asm_gross_margin_downside_2026..asm_gross_margin_downside_2030 (5 rows) | Income Statement -- Cost of Sales / Gross Profit | Gross margin (COGS-derived) | downside | 2030 | 26.30 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 29.28 | 24.57 | 27.54 | 28.21 | 27.93 | 24.57 | 29.28 | 27.93 | Gradual, partial reversion toward (not matching) the FY2022 trough of 24.57% -- a moderate margin-pressure case, bounded well short of the full historical worst year. | (none) | gross_profit, revenue | 2026-03-11 | proposed | v1 |
| asm_gross_margin_upside_2026..asm_gross_margin_upside_2030 (5 rows) | Income Statement -- Cost of Sales / Gross Profit | Gross margin (COGS-derived) | upside | 2026 | 27.93 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 29.28 | 24.57 | 27.54 | 28.21 | 27.93 | 24.57 | 29.28 | 27.93 | Gradual improvement toward, but never exceeding, the 5-year historical maximum (29.28%, FY2021) -- plausible supply-chain/mix execution, bounded by Target's own observed range. | (none) | gross_profit, revenue | 2026-03-11 | proposed | v1 |
| asm_gross_margin_upside_2026..asm_gross_margin_upside_2030 (5 rows) | Income Statement -- Cost of Sales / Gross Profit | Gross margin (COGS-derived) | upside | 2027 | 28.15 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 29.28 | 24.57 | 27.54 | 28.21 | 27.93 | 24.57 | 29.28 | 27.93 | Gradual improvement toward, but never exceeding, the 5-year historical maximum (29.28%, FY2021) -- plausible supply-chain/mix execution, bounded by Target's own observed range. | (none) | gross_profit, revenue | 2026-03-11 | proposed | v1 |
| asm_gross_margin_upside_2026..asm_gross_margin_upside_2030 (5 rows) | Income Statement -- Cost of Sales / Gross Profit | Gross margin (COGS-derived) | upside | 2028 | 28.36 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 29.28 | 24.57 | 27.54 | 28.21 | 27.93 | 24.57 | 29.28 | 27.93 | Gradual improvement toward, but never exceeding, the 5-year historical maximum (29.28%, FY2021) -- plausible supply-chain/mix execution, bounded by Target's own observed range. | (none) | gross_profit, revenue | 2026-03-11 | proposed | v1 |
| asm_gross_margin_upside_2026..asm_gross_margin_upside_2030 (5 rows) | Income Statement -- Cost of Sales / Gross Profit | Gross margin (COGS-derived) | upside | 2029 | 28.58 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 29.28 | 24.57 | 27.54 | 28.21 | 27.93 | 24.57 | 29.28 | 27.93 | Gradual improvement toward, but never exceeding, the 5-year historical maximum (29.28%, FY2021) -- plausible supply-chain/mix execution, bounded by Target's own observed range. | (none) | gross_profit, revenue | 2026-03-11 | proposed | v1 |
| asm_gross_margin_upside_2026..asm_gross_margin_upside_2030 (5 rows) | Income Statement -- Cost of Sales / Gross Profit | Gross margin (COGS-derived) | upside | 2030 | 28.80 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 29.28 | 24.57 | 27.54 | 28.21 | 27.93 | 24.57 | 29.28 | 27.93 | Gradual improvement toward, but never exceeding, the 5-year historical maximum (29.28%, FY2021) -- plausible supply-chain/mix execution, bounded by Target's own observed range. | (none) | gross_profit, revenue | 2026-03-11 | proposed | v1 |
| asm_share_chg_base | Income Statement -- Diluted Shares / EPS | Diluted share count change | base | 2026 | -0.50 | percent | Flat %/yr, applied recursively to prior-year diluted shares | N/A | -5.68 | -0.41 | -0.22 | -1.34 | -5.68 | -0.22 | -0.41 | Continued modest buyback-driven reduction, below the 5-year average magnitude given lower recent FCF than the FY2021/FY2022 aggressive-repurchase years. | (none) | diluted_shares | 2026-03-11 | proposed | v1 |
| asm_share_chg_base | Income Statement -- Diluted Shares / EPS | Diluted share count change | base | 2027 | -0.50 | percent | Flat %/yr, applied recursively to prior-year diluted shares | N/A | -5.68 | -0.41 | -0.22 | -1.34 | -5.68 | -0.22 | -0.41 | Continued modest buyback-driven reduction, below the 5-year average magnitude given lower recent FCF than the FY2021/FY2022 aggressive-repurchase years. | (none) | diluted_shares | 2026-03-11 | proposed | v1 |
| asm_share_chg_base | Income Statement -- Diluted Shares / EPS | Diluted share count change | base | 2028 | -0.50 | percent | Flat %/yr, applied recursively to prior-year diluted shares | N/A | -5.68 | -0.41 | -0.22 | -1.34 | -5.68 | -0.22 | -0.41 | Continued modest buyback-driven reduction, below the 5-year average magnitude given lower recent FCF than the FY2021/FY2022 aggressive-repurchase years. | (none) | diluted_shares | 2026-03-11 | proposed | v1 |
| asm_share_chg_base | Income Statement -- Diluted Shares / EPS | Diluted share count change | base | 2029 | -0.50 | percent | Flat %/yr, applied recursively to prior-year diluted shares | N/A | -5.68 | -0.41 | -0.22 | -1.34 | -5.68 | -0.22 | -0.41 | Continued modest buyback-driven reduction, below the 5-year average magnitude given lower recent FCF than the FY2021/FY2022 aggressive-repurchase years. | (none) | diluted_shares | 2026-03-11 | proposed | v1 |
| asm_share_chg_base | Income Statement -- Diluted Shares / EPS | Diluted share count change | base | 2030 | -0.50 | percent | Flat %/yr, applied recursively to prior-year diluted shares | N/A | -5.68 | -0.41 | -0.22 | -1.34 | -5.68 | -0.22 | -0.41 | Continued modest buyback-driven reduction, below the 5-year average magnitude given lower recent FCF than the FY2021/FY2022 aggressive-repurchase years. | (none) | diluted_shares | 2026-03-11 | proposed | v1 |
| asm_share_chg_downside | Income Statement -- Diluted Shares / EPS | Diluted share count change | downside | 2026 | 0.00 | percent | Flat %/yr, applied recursively to prior-year diluted shares | N/A | -5.68 | -0.41 | -0.22 | -1.34 | -5.68 | -0.22 | -0.41 | No net buybacks assumed; share count held flat -- capital preservation under pressure. | (none) | diluted_shares | 2026-03-11 | proposed | v1 |
| asm_share_chg_downside | Income Statement -- Diluted Shares / EPS | Diluted share count change | downside | 2027 | 0.00 | percent | Flat %/yr, applied recursively to prior-year diluted shares | N/A | -5.68 | -0.41 | -0.22 | -1.34 | -5.68 | -0.22 | -0.41 | No net buybacks assumed; share count held flat -- capital preservation under pressure. | (none) | diluted_shares | 2026-03-11 | proposed | v1 |
| asm_share_chg_downside | Income Statement -- Diluted Shares / EPS | Diluted share count change | downside | 2028 | 0.00 | percent | Flat %/yr, applied recursively to prior-year diluted shares | N/A | -5.68 | -0.41 | -0.22 | -1.34 | -5.68 | -0.22 | -0.41 | No net buybacks assumed; share count held flat -- capital preservation under pressure. | (none) | diluted_shares | 2026-03-11 | proposed | v1 |
| asm_share_chg_downside | Income Statement -- Diluted Shares / EPS | Diluted share count change | downside | 2029 | 0.00 | percent | Flat %/yr, applied recursively to prior-year diluted shares | N/A | -5.68 | -0.41 | -0.22 | -1.34 | -5.68 | -0.22 | -0.41 | No net buybacks assumed; share count held flat -- capital preservation under pressure. | (none) | diluted_shares | 2026-03-11 | proposed | v1 |
| asm_share_chg_downside | Income Statement -- Diluted Shares / EPS | Diluted share count change | downside | 2030 | 0.00 | percent | Flat %/yr, applied recursively to prior-year diluted shares | N/A | -5.68 | -0.41 | -0.22 | -1.34 | -5.68 | -0.22 | -0.41 | No net buybacks assumed; share count held flat -- capital preservation under pressure. | (none) | diluted_shares | 2026-03-11 | proposed | v1 |
| asm_share_chg_upside | Income Statement -- Diluted Shares / EPS | Diluted share count change | upside | 2026 | -1.50 | percent | Flat %/yr, applied recursively to prior-year diluted shares | N/A | -5.68 | -0.41 | -0.22 | -1.34 | -5.68 | -0.22 | -0.41 | More aggressive buyback-driven reduction, funded by stronger scenario FCF -- within the historical range observed in FY2022-FY2025 (excluding the FY2022 outlier year), not the unrepeated -5.68% pandemic-era pace. | (none) | diluted_shares | 2026-03-11 | proposed | v1 |
| asm_share_chg_upside | Income Statement -- Diluted Shares / EPS | Diluted share count change | upside | 2027 | -1.50 | percent | Flat %/yr, applied recursively to prior-year diluted shares | N/A | -5.68 | -0.41 | -0.22 | -1.34 | -5.68 | -0.22 | -0.41 | More aggressive buyback-driven reduction, funded by stronger scenario FCF -- within the historical range observed in FY2022-FY2025 (excluding the FY2022 outlier year), not the unrepeated -5.68% pandemic-era pace. | (none) | diluted_shares | 2026-03-11 | proposed | v1 |
| asm_share_chg_upside | Income Statement -- Diluted Shares / EPS | Diluted share count change | upside | 2028 | -1.50 | percent | Flat %/yr, applied recursively to prior-year diluted shares | N/A | -5.68 | -0.41 | -0.22 | -1.34 | -5.68 | -0.22 | -0.41 | More aggressive buyback-driven reduction, funded by stronger scenario FCF -- within the historical range observed in FY2022-FY2025 (excluding the FY2022 outlier year), not the unrepeated -5.68% pandemic-era pace. | (none) | diluted_shares | 2026-03-11 | proposed | v1 |
| asm_share_chg_upside | Income Statement -- Diluted Shares / EPS | Diluted share count change | upside | 2029 | -1.50 | percent | Flat %/yr, applied recursively to prior-year diluted shares | N/A | -5.68 | -0.41 | -0.22 | -1.34 | -5.68 | -0.22 | -0.41 | More aggressive buyback-driven reduction, funded by stronger scenario FCF -- within the historical range observed in FY2022-FY2025 (excluding the FY2022 outlier year), not the unrepeated -5.68% pandemic-era pace. | (none) | diluted_shares | 2026-03-11 | proposed | v1 |
| asm_share_chg_upside | Income Statement -- Diluted Shares / EPS | Diluted share count change | upside | 2030 | -1.50 | percent | Flat %/yr, applied recursively to prior-year diluted shares | N/A | -5.68 | -0.41 | -0.22 | -1.34 | -5.68 | -0.22 | -0.41 | More aggressive buyback-driven reduction, funded by stronger scenario FCF -- within the historical range observed in FY2022-FY2025 (excluding the FY2022 outlier year), not the unrepeated -5.68% pandemic-era pace. | (none) | diluted_shares | 2026-03-11 | proposed | v1 |
| asm_tax_rate_base | Income Statement -- Income Tax | Effective tax rate | base | 2026 | 22.20 | percent | Flat %/yr, applied to pretax income | 22.02 | 18.67 | 21.88 | 22.24 | 22.28 | 18.67 | 22.28 | 22.02 | Average of the 3 most recent years excluding the FY2022 outlier (18.67%, a one-time benefit not treated as representative): (21.88+22.24+22.28)/3 = 22.13%, rounded. | (none) | income_tax_expense, pretax_income | 2026-03-11 | proposed | v1 |
| asm_tax_rate_base | Income Statement -- Income Tax | Effective tax rate | base | 2027 | 22.20 | percent | Flat %/yr, applied to pretax income | 22.02 | 18.67 | 21.88 | 22.24 | 22.28 | 18.67 | 22.28 | 22.02 | Average of the 3 most recent years excluding the FY2022 outlier (18.67%, a one-time benefit not treated as representative): (21.88+22.24+22.28)/3 = 22.13%, rounded. | (none) | income_tax_expense, pretax_income | 2026-03-11 | proposed | v1 |
| asm_tax_rate_base | Income Statement -- Income Tax | Effective tax rate | base | 2028 | 22.20 | percent | Flat %/yr, applied to pretax income | 22.02 | 18.67 | 21.88 | 22.24 | 22.28 | 18.67 | 22.28 | 22.02 | Average of the 3 most recent years excluding the FY2022 outlier (18.67%, a one-time benefit not treated as representative): (21.88+22.24+22.28)/3 = 22.13%, rounded. | (none) | income_tax_expense, pretax_income | 2026-03-11 | proposed | v1 |
| asm_tax_rate_base | Income Statement -- Income Tax | Effective tax rate | base | 2029 | 22.20 | percent | Flat %/yr, applied to pretax income | 22.02 | 18.67 | 21.88 | 22.24 | 22.28 | 18.67 | 22.28 | 22.02 | Average of the 3 most recent years excluding the FY2022 outlier (18.67%, a one-time benefit not treated as representative): (21.88+22.24+22.28)/3 = 22.13%, rounded. | (none) | income_tax_expense, pretax_income | 2026-03-11 | proposed | v1 |
| asm_tax_rate_base | Income Statement -- Income Tax | Effective tax rate | base | 2030 | 22.20 | percent | Flat %/yr, applied to pretax income | 22.02 | 18.67 | 21.88 | 22.24 | 22.28 | 18.67 | 22.28 | 22.02 | Average of the 3 most recent years excluding the FY2022 outlier (18.67%, a one-time benefit not treated as representative): (21.88+22.24+22.28)/3 = 22.13%, rounded. | (none) | income_tax_expense, pretax_income | 2026-03-11 | proposed | v1 |
| asm_tax_rate_downside | Income Statement -- Income Tax | Effective tax rate | downside | 2026 | 23.00 | percent | Flat %/yr, applied to pretax income | 22.02 | 18.67 | 21.88 | 22.24 | 22.28 | 18.67 | 22.28 | 22.02 | Modestly unfavorable rate, slightly above the representative historical maximum. | (none) | income_tax_expense, pretax_income | 2026-03-11 | proposed | v1 |
| asm_tax_rate_downside | Income Statement -- Income Tax | Effective tax rate | downside | 2027 | 23.00 | percent | Flat %/yr, applied to pretax income | 22.02 | 18.67 | 21.88 | 22.24 | 22.28 | 18.67 | 22.28 | 22.02 | Modestly unfavorable rate, slightly above the representative historical maximum. | (none) | income_tax_expense, pretax_income | 2026-03-11 | proposed | v1 |
| asm_tax_rate_downside | Income Statement -- Income Tax | Effective tax rate | downside | 2028 | 23.00 | percent | Flat %/yr, applied to pretax income | 22.02 | 18.67 | 21.88 | 22.24 | 22.28 | 18.67 | 22.28 | 22.02 | Modestly unfavorable rate, slightly above the representative historical maximum. | (none) | income_tax_expense, pretax_income | 2026-03-11 | proposed | v1 |
| asm_tax_rate_downside | Income Statement -- Income Tax | Effective tax rate | downside | 2029 | 23.00 | percent | Flat %/yr, applied to pretax income | 22.02 | 18.67 | 21.88 | 22.24 | 22.28 | 18.67 | 22.28 | 22.02 | Modestly unfavorable rate, slightly above the representative historical maximum. | (none) | income_tax_expense, pretax_income | 2026-03-11 | proposed | v1 |
| asm_tax_rate_downside | Income Statement -- Income Tax | Effective tax rate | downside | 2030 | 23.00 | percent | Flat %/yr, applied to pretax income | 22.02 | 18.67 | 21.88 | 22.24 | 22.28 | 18.67 | 22.28 | 22.02 | Modestly unfavorable rate, slightly above the representative historical maximum. | (none) | income_tax_expense, pretax_income | 2026-03-11 | proposed | v1 |
| asm_tax_rate_upside | Income Statement -- Income Tax | Effective tax rate | upside | 2026 | 21.50 | percent | Flat %/yr, applied to pretax income | 22.02 | 18.67 | 21.88 | 22.24 | 22.28 | 18.67 | 22.28 | 22.02 | Modestly favorable rate near the low end of the representative (non-FY2022) historical range. | (none) | income_tax_expense, pretax_income | 2026-03-11 | proposed | v1 |
| asm_tax_rate_upside | Income Statement -- Income Tax | Effective tax rate | upside | 2027 | 21.50 | percent | Flat %/yr, applied to pretax income | 22.02 | 18.67 | 21.88 | 22.24 | 22.28 | 18.67 | 22.28 | 22.02 | Modestly favorable rate near the low end of the representative (non-FY2022) historical range. | (none) | income_tax_expense, pretax_income | 2026-03-11 | proposed | v1 |
| asm_tax_rate_upside | Income Statement -- Income Tax | Effective tax rate | upside | 2028 | 21.50 | percent | Flat %/yr, applied to pretax income | 22.02 | 18.67 | 21.88 | 22.24 | 22.28 | 18.67 | 22.28 | 22.02 | Modestly favorable rate near the low end of the representative (non-FY2022) historical range. | (none) | income_tax_expense, pretax_income | 2026-03-11 | proposed | v1 |
| asm_tax_rate_upside | Income Statement -- Income Tax | Effective tax rate | upside | 2029 | 21.50 | percent | Flat %/yr, applied to pretax income | 22.02 | 18.67 | 21.88 | 22.24 | 22.28 | 18.67 | 22.28 | 22.02 | Modestly favorable rate near the low end of the representative (non-FY2022) historical range. | (none) | income_tax_expense, pretax_income | 2026-03-11 | proposed | v1 |
| asm_tax_rate_upside | Income Statement -- Income Tax | Effective tax rate | upside | 2030 | 21.50 | percent | Flat %/yr, applied to pretax income | 22.02 | 18.67 | 21.88 | 22.24 | 22.28 | 18.67 | 22.28 | 22.02 | Modestly favorable rate near the low end of the representative (non-FY2022) historical range. | (none) | income_tax_expense, pretax_income | 2026-03-11 | proposed | v1 |
| asm_interest_rate_base | Income Statement -- Interest Expense | Interest rate on average total debt | base | 2026 | 3.10 | percent | Flat %/yr, applied to average(beginning, ending) total debt | 3.62 | 3.40 | 3.58 | 2.98 | 3.10 | 2.98 | 3.62 | 3.40 | Matches the recent (FY2024-FY2025) implied rate on average total_debt_gaap. | (none) | interest_expense, total_debt_gaap | 2026-03-11 | proposed | v1 |
| asm_interest_rate_base | Income Statement -- Interest Expense | Interest rate on average total debt | base | 2027 | 3.10 | percent | Flat %/yr, applied to average(beginning, ending) total debt | 3.62 | 3.40 | 3.58 | 2.98 | 3.10 | 2.98 | 3.62 | 3.40 | Matches the recent (FY2024-FY2025) implied rate on average total_debt_gaap. | (none) | interest_expense, total_debt_gaap | 2026-03-11 | proposed | v1 |
| asm_interest_rate_base | Income Statement -- Interest Expense | Interest rate on average total debt | base | 2028 | 3.10 | percent | Flat %/yr, applied to average(beginning, ending) total debt | 3.62 | 3.40 | 3.58 | 2.98 | 3.10 | 2.98 | 3.62 | 3.40 | Matches the recent (FY2024-FY2025) implied rate on average total_debt_gaap. | (none) | interest_expense, total_debt_gaap | 2026-03-11 | proposed | v1 |
| asm_interest_rate_base | Income Statement -- Interest Expense | Interest rate on average total debt | base | 2029 | 3.10 | percent | Flat %/yr, applied to average(beginning, ending) total debt | 3.62 | 3.40 | 3.58 | 2.98 | 3.10 | 2.98 | 3.62 | 3.40 | Matches the recent (FY2024-FY2025) implied rate on average total_debt_gaap. | (none) | interest_expense, total_debt_gaap | 2026-03-11 | proposed | v1 |
| asm_interest_rate_base | Income Statement -- Interest Expense | Interest rate on average total debt | base | 2030 | 3.10 | percent | Flat %/yr, applied to average(beginning, ending) total debt | 3.62 | 3.40 | 3.58 | 2.98 | 3.10 | 2.98 | 3.62 | 3.40 | Matches the recent (FY2024-FY2025) implied rate on average total_debt_gaap. | (none) | interest_expense, total_debt_gaap | 2026-03-11 | proposed | v1 |
| asm_interest_rate_downside | Income Statement -- Interest Expense | Interest rate on average total debt | downside | 2026 | 3.40 | percent | Flat %/yr, applied to average(beginning, ending) total debt | 3.62 | 3.40 | 3.58 | 2.98 | 3.10 | 2.98 | 3.62 | 3.40 | Higher borrowing cost, near the historical maximum, reflecting greater reliance on debt funding under pressure. | (none) | interest_expense, total_debt_gaap | 2026-03-11 | proposed | v1 |
| asm_interest_rate_downside | Income Statement -- Interest Expense | Interest rate on average total debt | downside | 2027 | 3.40 | percent | Flat %/yr, applied to average(beginning, ending) total debt | 3.62 | 3.40 | 3.58 | 2.98 | 3.10 | 2.98 | 3.62 | 3.40 | Higher borrowing cost, near the historical maximum, reflecting greater reliance on debt funding under pressure. | (none) | interest_expense, total_debt_gaap | 2026-03-11 | proposed | v1 |
| asm_interest_rate_downside | Income Statement -- Interest Expense | Interest rate on average total debt | downside | 2028 | 3.40 | percent | Flat %/yr, applied to average(beginning, ending) total debt | 3.62 | 3.40 | 3.58 | 2.98 | 3.10 | 2.98 | 3.62 | 3.40 | Higher borrowing cost, near the historical maximum, reflecting greater reliance on debt funding under pressure. | (none) | interest_expense, total_debt_gaap | 2026-03-11 | proposed | v1 |
| asm_interest_rate_downside | Income Statement -- Interest Expense | Interest rate on average total debt | downside | 2029 | 3.40 | percent | Flat %/yr, applied to average(beginning, ending) total debt | 3.62 | 3.40 | 3.58 | 2.98 | 3.10 | 2.98 | 3.62 | 3.40 | Higher borrowing cost, near the historical maximum, reflecting greater reliance on debt funding under pressure. | (none) | interest_expense, total_debt_gaap | 2026-03-11 | proposed | v1 |
| asm_interest_rate_downside | Income Statement -- Interest Expense | Interest rate on average total debt | downside | 2030 | 3.40 | percent | Flat %/yr, applied to average(beginning, ending) total debt | 3.62 | 3.40 | 3.58 | 2.98 | 3.10 | 2.98 | 3.62 | 3.40 | Higher borrowing cost, near the historical maximum, reflecting greater reliance on debt funding under pressure. | (none) | interest_expense, total_debt_gaap | 2026-03-11 | proposed | v1 |
| asm_interest_rate_upside | Income Statement -- Interest Expense | Interest rate on average total debt | upside | 2026 | 2.90 | percent | Flat %/yr, applied to average(beginning, ending) total debt | 3.62 | 3.40 | 3.58 | 2.98 | 3.10 | 2.98 | 3.62 | 3.40 | Slightly favorable borrowing cost / lower incremental debt need, within the historical range. | (none) | interest_expense, total_debt_gaap | 2026-03-11 | proposed | v1 |
| asm_interest_rate_upside | Income Statement -- Interest Expense | Interest rate on average total debt | upside | 2027 | 2.90 | percent | Flat %/yr, applied to average(beginning, ending) total debt | 3.62 | 3.40 | 3.58 | 2.98 | 3.10 | 2.98 | 3.62 | 3.40 | Slightly favorable borrowing cost / lower incremental debt need, within the historical range. | (none) | interest_expense, total_debt_gaap | 2026-03-11 | proposed | v1 |
| asm_interest_rate_upside | Income Statement -- Interest Expense | Interest rate on average total debt | upside | 2028 | 2.90 | percent | Flat %/yr, applied to average(beginning, ending) total debt | 3.62 | 3.40 | 3.58 | 2.98 | 3.10 | 2.98 | 3.62 | 3.40 | Slightly favorable borrowing cost / lower incremental debt need, within the historical range. | (none) | interest_expense, total_debt_gaap | 2026-03-11 | proposed | v1 |
| asm_interest_rate_upside | Income Statement -- Interest Expense | Interest rate on average total debt | upside | 2029 | 2.90 | percent | Flat %/yr, applied to average(beginning, ending) total debt | 3.62 | 3.40 | 3.58 | 2.98 | 3.10 | 2.98 | 3.62 | 3.40 | Slightly favorable borrowing cost / lower incremental debt need, within the historical range. | (none) | interest_expense, total_debt_gaap | 2026-03-11 | proposed | v1 |
| asm_interest_rate_upside | Income Statement -- Interest Expense | Interest rate on average total debt | upside | 2030 | 2.90 | percent | Flat %/yr, applied to average(beginning, ending) total debt | 3.62 | 3.40 | 3.58 | 2.98 | 3.10 | 2.98 | 3.62 | 3.40 | Slightly favorable borrowing cost / lower incremental debt need, within the historical range. | (none) | interest_expense, total_debt_gaap | 2026-03-11 | proposed | v1 |
| asm_da_pct_base_2026..asm_da_pct_base_2030 (5 rows) | Income Statement -- Operating Expenses (D&A) | D&A included in operating expenses, % of revenue | base | 2026 | 2.58 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.21 | 2.19 | 2.25 | 2.37 | 2.50 | 2.19 | 2.50 | 2.25 | Extrapolates the FY2021-FY2025 average annual increase (~0.078pp/yr) in D&A as a percent of revenue, reflecting continued store/technology investment amortizing -- a documented persistence of an already-observed trend, not a new assumption. | capex_pct_of_revenue | depreciation_amortization_opex, revenue | 2026-03-11 | proposed | v1 |
| asm_da_pct_base_2026..asm_da_pct_base_2030 (5 rows) | Income Statement -- Operating Expenses (D&A) | D&A included in operating expenses, % of revenue | base | 2027 | 2.65 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.21 | 2.19 | 2.25 | 2.37 | 2.50 | 2.19 | 2.50 | 2.25 | Extrapolates the FY2021-FY2025 average annual increase (~0.078pp/yr) in D&A as a percent of revenue, reflecting continued store/technology investment amortizing -- a documented persistence of an already-observed trend, not a new assumption. | capex_pct_of_revenue | depreciation_amortization_opex, revenue | 2026-03-11 | proposed | v1 |
| asm_da_pct_base_2026..asm_da_pct_base_2030 (5 rows) | Income Statement -- Operating Expenses (D&A) | D&A included in operating expenses, % of revenue | base | 2028 | 2.73 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.21 | 2.19 | 2.25 | 2.37 | 2.50 | 2.19 | 2.50 | 2.25 | Extrapolates the FY2021-FY2025 average annual increase (~0.078pp/yr) in D&A as a percent of revenue, reflecting continued store/technology investment amortizing -- a documented persistence of an already-observed trend, not a new assumption. | capex_pct_of_revenue | depreciation_amortization_opex, revenue | 2026-03-11 | proposed | v1 |
| asm_da_pct_base_2026..asm_da_pct_base_2030 (5 rows) | Income Statement -- Operating Expenses (D&A) | D&A included in operating expenses, % of revenue | base | 2029 | 2.81 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.21 | 2.19 | 2.25 | 2.37 | 2.50 | 2.19 | 2.50 | 2.25 | Extrapolates the FY2021-FY2025 average annual increase (~0.078pp/yr) in D&A as a percent of revenue, reflecting continued store/technology investment amortizing -- a documented persistence of an already-observed trend, not a new assumption. | capex_pct_of_revenue | depreciation_amortization_opex, revenue | 2026-03-11 | proposed | v1 |
| asm_da_pct_base_2026..asm_da_pct_base_2030 (5 rows) | Income Statement -- Operating Expenses (D&A) | D&A included in operating expenses, % of revenue | base | 2030 | 2.89 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.21 | 2.19 | 2.25 | 2.37 | 2.50 | 2.19 | 2.50 | 2.25 | Extrapolates the FY2021-FY2025 average annual increase (~0.078pp/yr) in D&A as a percent of revenue, reflecting continued store/technology investment amortizing -- a documented persistence of an already-observed trend, not a new assumption. | capex_pct_of_revenue | depreciation_amortization_opex, revenue | 2026-03-11 | proposed | v1 |
| asm_da_pct_downside_2026..asm_da_pct_downside_2030 (5 rows) | Income Statement -- Operating Expenses (D&A) | D&A included in operating expenses, % of revenue | downside | 2026 | 2.48 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.21 | 2.19 | 2.25 | 2.37 | 2.50 | 2.19 | 2.50 | 2.25 | Same trend less -0.10pp, consistent with the downside scenario's reduced CapEx intensity -- D&A is sticky (prior capex keeps depreciating), so only a small offset is applied, not a reversal of the trend. | capex_pct_of_revenue | depreciation_amortization_opex, revenue | 2026-03-11 | proposed | v1 |
| asm_da_pct_downside_2026..asm_da_pct_downside_2030 (5 rows) | Income Statement -- Operating Expenses (D&A) | D&A included in operating expenses, % of revenue | downside | 2027 | 2.56 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.21 | 2.19 | 2.25 | 2.37 | 2.50 | 2.19 | 2.50 | 2.25 | Same trend less -0.10pp, consistent with the downside scenario's reduced CapEx intensity -- D&A is sticky (prior capex keeps depreciating), so only a small offset is applied, not a reversal of the trend. | capex_pct_of_revenue | depreciation_amortization_opex, revenue | 2026-03-11 | proposed | v1 |
| asm_da_pct_downside_2026..asm_da_pct_downside_2030 (5 rows) | Income Statement -- Operating Expenses (D&A) | D&A included in operating expenses, % of revenue | downside | 2028 | 2.63 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.21 | 2.19 | 2.25 | 2.37 | 2.50 | 2.19 | 2.50 | 2.25 | Same trend less -0.10pp, consistent with the downside scenario's reduced CapEx intensity -- D&A is sticky (prior capex keeps depreciating), so only a small offset is applied, not a reversal of the trend. | capex_pct_of_revenue | depreciation_amortization_opex, revenue | 2026-03-11 | proposed | v1 |
| asm_da_pct_downside_2026..asm_da_pct_downside_2030 (5 rows) | Income Statement -- Operating Expenses (D&A) | D&A included in operating expenses, % of revenue | downside | 2029 | 2.71 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.21 | 2.19 | 2.25 | 2.37 | 2.50 | 2.19 | 2.50 | 2.25 | Same trend less -0.10pp, consistent with the downside scenario's reduced CapEx intensity -- D&A is sticky (prior capex keeps depreciating), so only a small offset is applied, not a reversal of the trend. | capex_pct_of_revenue | depreciation_amortization_opex, revenue | 2026-03-11 | proposed | v1 |
| asm_da_pct_downside_2026..asm_da_pct_downside_2030 (5 rows) | Income Statement -- Operating Expenses (D&A) | D&A included in operating expenses, % of revenue | downside | 2030 | 2.79 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.21 | 2.19 | 2.25 | 2.37 | 2.50 | 2.19 | 2.50 | 2.25 | Same trend less -0.10pp, consistent with the downside scenario's reduced CapEx intensity -- D&A is sticky (prior capex keeps depreciating), so only a small offset is applied, not a reversal of the trend. | capex_pct_of_revenue | depreciation_amortization_opex, revenue | 2026-03-11 | proposed | v1 |
| asm_da_pct_upside_2026..asm_da_pct_upside_2030 (5 rows) | Income Statement -- Operating Expenses (D&A) | D&A included in operating expenses, % of revenue | upside | 2026 | 2.68 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.21 | 2.19 | 2.25 | 2.37 | 2.50 | 2.19 | 2.50 | 2.25 | Same trend plus +0.10pp, consistent with the upside scenario's higher CapEx intensity (more assets in service depreciate more). | capex_pct_of_revenue | depreciation_amortization_opex, revenue | 2026-03-11 | proposed | v1 |
| asm_da_pct_upside_2026..asm_da_pct_upside_2030 (5 rows) | Income Statement -- Operating Expenses (D&A) | D&A included in operating expenses, % of revenue | upside | 2027 | 2.75 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.21 | 2.19 | 2.25 | 2.37 | 2.50 | 2.19 | 2.50 | 2.25 | Same trend plus +0.10pp, consistent with the upside scenario's higher CapEx intensity (more assets in service depreciate more). | capex_pct_of_revenue | depreciation_amortization_opex, revenue | 2026-03-11 | proposed | v1 |
| asm_da_pct_upside_2026..asm_da_pct_upside_2030 (5 rows) | Income Statement -- Operating Expenses (D&A) | D&A included in operating expenses, % of revenue | upside | 2028 | 2.83 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.21 | 2.19 | 2.25 | 2.37 | 2.50 | 2.19 | 2.50 | 2.25 | Same trend plus +0.10pp, consistent with the upside scenario's higher CapEx intensity (more assets in service depreciate more). | capex_pct_of_revenue | depreciation_amortization_opex, revenue | 2026-03-11 | proposed | v1 |
| asm_da_pct_upside_2026..asm_da_pct_upside_2030 (5 rows) | Income Statement -- Operating Expenses (D&A) | D&A included in operating expenses, % of revenue | upside | 2029 | 2.91 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.21 | 2.19 | 2.25 | 2.37 | 2.50 | 2.19 | 2.50 | 2.25 | Same trend plus +0.10pp, consistent with the upside scenario's higher CapEx intensity (more assets in service depreciate more). | capex_pct_of_revenue | depreciation_amortization_opex, revenue | 2026-03-11 | proposed | v1 |
| asm_da_pct_upside_2026..asm_da_pct_upside_2030 (5 rows) | Income Statement -- Operating Expenses (D&A) | D&A included in operating expenses, % of revenue | upside | 2030 | 2.99 | percent | Historical trend extrapolation (pp/yr) + scenario offset, % of revenue | 2.21 | 2.19 | 2.25 | 2.37 | 2.50 | 2.19 | 2.50 | 2.25 | Same trend plus +0.10pp, consistent with the upside scenario's higher CapEx intensity (more assets in service depreciate more). | capex_pct_of_revenue | depreciation_amortization_opex, revenue | 2026-03-11 | proposed | v1 |
| asm_sga_pct_base_2026..asm_sga_pct_base_2030 (5 rows) | Income Statement -- Operating Expenses (SG&A) | SG&A % of revenue | base | 2026 | 20.55 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 18.63 | 18.86 | 19.98 | 20.62 | 20.55 | 18.63 | 20.62 | 19.98 | Flat at the FY2025 actual level -- continuation, not reversion to the lower historical range (18.63%-19.98%) achieved only when revenue was growing. | (none) | operating_expenses, revenue | 2026-03-11 | proposed | v1 |
| asm_sga_pct_base_2026..asm_sga_pct_base_2030 (5 rows) | Income Statement -- Operating Expenses (SG&A) | SG&A % of revenue | base | 2027 | 20.55 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 18.63 | 18.86 | 19.98 | 20.62 | 20.55 | 18.63 | 20.62 | 19.98 | Flat at the FY2025 actual level -- continuation, not reversion to the lower historical range (18.63%-19.98%) achieved only when revenue was growing. | (none) | operating_expenses, revenue | 2026-03-11 | proposed | v1 |
| asm_sga_pct_base_2026..asm_sga_pct_base_2030 (5 rows) | Income Statement -- Operating Expenses (SG&A) | SG&A % of revenue | base | 2028 | 20.55 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 18.63 | 18.86 | 19.98 | 20.62 | 20.55 | 18.63 | 20.62 | 19.98 | Flat at the FY2025 actual level -- continuation, not reversion to the lower historical range (18.63%-19.98%) achieved only when revenue was growing. | (none) | operating_expenses, revenue | 2026-03-11 | proposed | v1 |
| asm_sga_pct_base_2026..asm_sga_pct_base_2030 (5 rows) | Income Statement -- Operating Expenses (SG&A) | SG&A % of revenue | base | 2029 | 20.55 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 18.63 | 18.86 | 19.98 | 20.62 | 20.55 | 18.63 | 20.62 | 19.98 | Flat at the FY2025 actual level -- continuation, not reversion to the lower historical range (18.63%-19.98%) achieved only when revenue was growing. | (none) | operating_expenses, revenue | 2026-03-11 | proposed | v1 |
| asm_sga_pct_base_2026..asm_sga_pct_base_2030 (5 rows) | Income Statement -- Operating Expenses (SG&A) | SG&A % of revenue | base | 2030 | 20.55 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 18.63 | 18.86 | 19.98 | 20.62 | 20.55 | 18.63 | 20.62 | 19.98 | Flat at the FY2025 actual level -- continuation, not reversion to the lower historical range (18.63%-19.98%) achieved only when revenue was growing. | (none) | operating_expenses, revenue | 2026-03-11 | proposed | v1 |
| asm_sga_pct_downside_2026..asm_sga_pct_downside_2030 (5 rows) | Income Statement -- Operating Expenses (SG&A) | SG&A % of revenue | downside | 2026 | 20.55 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 18.63 | 18.86 | 19.98 | 20.62 | 20.55 | 18.63 | 20.62 | 19.98 | Continued deleverage as revenue declines faster than fixed SG&A costs, moderately above the 5-year historical maximum (20.62%, FY2024). | (none) | operating_expenses, revenue | 2026-03-11 | proposed | v1 |
| asm_sga_pct_downside_2026..asm_sga_pct_downside_2030 (5 rows) | Income Statement -- Operating Expenses (SG&A) | SG&A % of revenue | downside | 2027 | 20.74 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 18.63 | 18.86 | 19.98 | 20.62 | 20.55 | 18.63 | 20.62 | 19.98 | Continued deleverage as revenue declines faster than fixed SG&A costs, moderately above the 5-year historical maximum (20.62%, FY2024). | (none) | operating_expenses, revenue | 2026-03-11 | proposed | v1 |
| asm_sga_pct_downside_2026..asm_sga_pct_downside_2030 (5 rows) | Income Statement -- Operating Expenses (SG&A) | SG&A % of revenue | downside | 2028 | 20.93 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 18.63 | 18.86 | 19.98 | 20.62 | 20.55 | 18.63 | 20.62 | 19.98 | Continued deleverage as revenue declines faster than fixed SG&A costs, moderately above the 5-year historical maximum (20.62%, FY2024). | (none) | operating_expenses, revenue | 2026-03-11 | proposed | v1 |
| asm_sga_pct_downside_2026..asm_sga_pct_downside_2030 (5 rows) | Income Statement -- Operating Expenses (SG&A) | SG&A % of revenue | downside | 2029 | 21.11 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 18.63 | 18.86 | 19.98 | 20.62 | 20.55 | 18.63 | 20.62 | 19.98 | Continued deleverage as revenue declines faster than fixed SG&A costs, moderately above the 5-year historical maximum (20.62%, FY2024). | (none) | operating_expenses, revenue | 2026-03-11 | proposed | v1 |
| asm_sga_pct_downside_2026..asm_sga_pct_downside_2030 (5 rows) | Income Statement -- Operating Expenses (SG&A) | SG&A % of revenue | downside | 2030 | 21.30 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 18.63 | 18.86 | 19.98 | 20.62 | 20.55 | 18.63 | 20.62 | 19.98 | Continued deleverage as revenue declines faster than fixed SG&A costs, moderately above the 5-year historical maximum (20.62%, FY2024). | (none) | operating_expenses, revenue | 2026-03-11 | proposed | v1 |
| asm_sga_pct_upside_2026..asm_sga_pct_upside_2030 (5 rows) | Income Statement -- Operating Expenses (SG&A) | SG&A % of revenue | upside | 2026 | 20.55 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 18.63 | 18.86 | 19.98 | 20.62 | 20.55 | 18.63 | 20.62 | 19.98 | Gradual improvement toward, but not below, the 5-year historical minimum (18.63%, FY2021) -- cost discipline/productivity, bounded by Target's own observed range. | (none) | operating_expenses, revenue | 2026-03-11 | proposed | v1 |
| asm_sga_pct_upside_2026..asm_sga_pct_upside_2030 (5 rows) | Income Statement -- Operating Expenses (SG&A) | SG&A % of revenue | upside | 2027 | 20.36 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 18.63 | 18.86 | 19.98 | 20.62 | 20.55 | 18.63 | 20.62 | 19.98 | Gradual improvement toward, but not below, the 5-year historical minimum (18.63%, FY2021) -- cost discipline/productivity, bounded by Target's own observed range. | (none) | operating_expenses, revenue | 2026-03-11 | proposed | v1 |
| asm_sga_pct_upside_2026..asm_sga_pct_upside_2030 (5 rows) | Income Statement -- Operating Expenses (SG&A) | SG&A % of revenue | upside | 2028 | 20.18 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 18.63 | 18.86 | 19.98 | 20.62 | 20.55 | 18.63 | 20.62 | 19.98 | Gradual improvement toward, but not below, the 5-year historical minimum (18.63%, FY2021) -- cost discipline/productivity, bounded by Target's own observed range. | (none) | operating_expenses, revenue | 2026-03-11 | proposed | v1 |
| asm_sga_pct_upside_2026..asm_sga_pct_upside_2030 (5 rows) | Income Statement -- Operating Expenses (SG&A) | SG&A % of revenue | upside | 2029 | 19.99 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 18.63 | 18.86 | 19.98 | 20.62 | 20.55 | 18.63 | 20.62 | 19.98 | Gradual improvement toward, but not below, the 5-year historical minimum (18.63%, FY2021) -- cost discipline/productivity, bounded by Target's own observed range. | (none) | operating_expenses, revenue | 2026-03-11 | proposed | v1 |
| asm_sga_pct_upside_2026..asm_sga_pct_upside_2030 (5 rows) | Income Statement -- Operating Expenses (SG&A) | SG&A % of revenue | upside | 2030 | 19.80 | percent | Linear drift FY2026->FY2030, % of revenue applied directly | 18.63 | 18.86 | 19.98 | 20.62 | 20.55 | 18.63 | 20.62 | 19.98 | Gradual improvement toward, but not below, the 5-year historical minimum (18.63%, FY2021) -- cost discipline/productivity, bounded by Target's own observed range. | (none) | operating_expenses, revenue | 2026-03-11 | proposed | v1 |
| asm_other_income_base | Income Statement -- Other Income/Expense | Net other income | base | 2026 | 95.00 | USD_millions | Flat $M/yr | 382.00 | 48.00 | 92.00 | 106.00 | 95.00 | 48.00 | 382.00 | 95.00 | Flat at the FY2025 actual level -- this line is historically small and volatile ($48M-$382M) with no clear trend; holding flat avoids fabricating a directional assumption without evidence. | (none) | net_other_income | 2026-03-11 | proposed | v1 |
| asm_other_income_base | Income Statement -- Other Income/Expense | Net other income | base | 2027 | 95.00 | USD_millions | Flat $M/yr | 382.00 | 48.00 | 92.00 | 106.00 | 95.00 | 48.00 | 382.00 | 95.00 | Flat at the FY2025 actual level -- this line is historically small and volatile ($48M-$382M) with no clear trend; holding flat avoids fabricating a directional assumption without evidence. | (none) | net_other_income | 2026-03-11 | proposed | v1 |
| asm_other_income_base | Income Statement -- Other Income/Expense | Net other income | base | 2028 | 95.00 | USD_millions | Flat $M/yr | 382.00 | 48.00 | 92.00 | 106.00 | 95.00 | 48.00 | 382.00 | 95.00 | Flat at the FY2025 actual level -- this line is historically small and volatile ($48M-$382M) with no clear trend; holding flat avoids fabricating a directional assumption without evidence. | (none) | net_other_income | 2026-03-11 | proposed | v1 |
| asm_other_income_base | Income Statement -- Other Income/Expense | Net other income | base | 2029 | 95.00 | USD_millions | Flat $M/yr | 382.00 | 48.00 | 92.00 | 106.00 | 95.00 | 48.00 | 382.00 | 95.00 | Flat at the FY2025 actual level -- this line is historically small and volatile ($48M-$382M) with no clear trend; holding flat avoids fabricating a directional assumption without evidence. | (none) | net_other_income | 2026-03-11 | proposed | v1 |
| asm_other_income_base | Income Statement -- Other Income/Expense | Net other income | base | 2030 | 95.00 | USD_millions | Flat $M/yr | 382.00 | 48.00 | 92.00 | 106.00 | 95.00 | 48.00 | 382.00 | 95.00 | Flat at the FY2025 actual level -- this line is historically small and volatile ($48M-$382M) with no clear trend; holding flat avoids fabricating a directional assumption without evidence. | (none) | net_other_income | 2026-03-11 | proposed | v1 |
| asm_other_income_downside | Income Statement -- Other Income/Expense | Net other income | downside | 2026 | 80.00 | USD_millions | Flat $M/yr | 382.00 | 48.00 | 92.00 | 106.00 | 95.00 | 48.00 | 382.00 | 95.00 | Near-flat, marginally unfavorable -- within the historical range. | (none) | net_other_income | 2026-03-11 | proposed | v1 |
| asm_other_income_downside | Income Statement -- Other Income/Expense | Net other income | downside | 2027 | 80.00 | USD_millions | Flat $M/yr | 382.00 | 48.00 | 92.00 | 106.00 | 95.00 | 48.00 | 382.00 | 95.00 | Near-flat, marginally unfavorable -- within the historical range. | (none) | net_other_income | 2026-03-11 | proposed | v1 |
| asm_other_income_downside | Income Statement -- Other Income/Expense | Net other income | downside | 2028 | 80.00 | USD_millions | Flat $M/yr | 382.00 | 48.00 | 92.00 | 106.00 | 95.00 | 48.00 | 382.00 | 95.00 | Near-flat, marginally unfavorable -- within the historical range. | (none) | net_other_income | 2026-03-11 | proposed | v1 |
| asm_other_income_downside | Income Statement -- Other Income/Expense | Net other income | downside | 2029 | 80.00 | USD_millions | Flat $M/yr | 382.00 | 48.00 | 92.00 | 106.00 | 95.00 | 48.00 | 382.00 | 95.00 | Near-flat, marginally unfavorable -- within the historical range. | (none) | net_other_income | 2026-03-11 | proposed | v1 |
| asm_other_income_downside | Income Statement -- Other Income/Expense | Net other income | downside | 2030 | 80.00 | USD_millions | Flat $M/yr | 382.00 | 48.00 | 92.00 | 106.00 | 95.00 | 48.00 | 382.00 | 95.00 | Near-flat, marginally unfavorable -- within the historical range. | (none) | net_other_income | 2026-03-11 | proposed | v1 |
| asm_other_income_upside | Income Statement -- Other Income/Expense | Net other income | upside | 2026 | 100.00 | USD_millions | Flat $M/yr | 382.00 | 48.00 | 92.00 | 106.00 | 95.00 | 48.00 | 382.00 | 95.00 | Near-flat, marginally favorable -- within the historical range, no fabricated upside swing. | (none) | net_other_income | 2026-03-11 | proposed | v1 |
| asm_other_income_upside | Income Statement -- Other Income/Expense | Net other income | upside | 2027 | 100.00 | USD_millions | Flat $M/yr | 382.00 | 48.00 | 92.00 | 106.00 | 95.00 | 48.00 | 382.00 | 95.00 | Near-flat, marginally favorable -- within the historical range, no fabricated upside swing. | (none) | net_other_income | 2026-03-11 | proposed | v1 |
| asm_other_income_upside | Income Statement -- Other Income/Expense | Net other income | upside | 2028 | 100.00 | USD_millions | Flat $M/yr | 382.00 | 48.00 | 92.00 | 106.00 | 95.00 | 48.00 | 382.00 | 95.00 | Near-flat, marginally favorable -- within the historical range, no fabricated upside swing. | (none) | net_other_income | 2026-03-11 | proposed | v1 |
| asm_other_income_upside | Income Statement -- Other Income/Expense | Net other income | upside | 2029 | 100.00 | USD_millions | Flat $M/yr | 382.00 | 48.00 | 92.00 | 106.00 | 95.00 | 48.00 | 382.00 | 95.00 | Near-flat, marginally favorable -- within the historical range, no fabricated upside swing. | (none) | net_other_income | 2026-03-11 | proposed | v1 |
| asm_other_income_upside | Income Statement -- Other Income/Expense | Net other income | upside | 2030 | 100.00 | USD_millions | Flat $M/yr | 382.00 | 48.00 | 92.00 | 106.00 | 95.00 | 48.00 | 382.00 | 95.00 | Near-flat, marginally favorable -- within the historical range, no fabricated upside swing. | (none) | net_other_income | 2026-03-11 | proposed | v1 |
| asm_rev_growth_base | Income Statement -- Revenue | Revenue growth | base | 2026 | 1.00 | percent | Flat %/yr, applied recursively: revenue_t = revenue_(t-1) * (1 + g) | N/A | 2.94 | -1.57 | -0.79 | -1.68 | -1.68 | 2.94 | -0.79 | Below FY2022's post-pandemic snap-back (+2.94%) and above the FY2023-FY2025 raw-decline trend; matches the FY2024-vs-FY2023(52-week-normalized) growth of +1.12%, treated as the cleanest recent read once the FY2023 53-week distortion is removed. Continuation of a stabilizing, low-single-digit trend -- explicitly NOT a return to the FY2021/FY2022 growth rates. | (none) | revenue | 2026-03-11 | proposed | v1 |
| asm_rev_growth_base | Income Statement -- Revenue | Revenue growth | base | 2027 | 1.00 | percent | Flat %/yr, applied recursively: revenue_t = revenue_(t-1) * (1 + g) | N/A | 2.94 | -1.57 | -0.79 | -1.68 | -1.68 | 2.94 | -0.79 | Below FY2022's post-pandemic snap-back (+2.94%) and above the FY2023-FY2025 raw-decline trend; matches the FY2024-vs-FY2023(52-week-normalized) growth of +1.12%, treated as the cleanest recent read once the FY2023 53-week distortion is removed. Continuation of a stabilizing, low-single-digit trend -- explicitly NOT a return to the FY2021/FY2022 growth rates. | (none) | revenue | 2026-03-11 | proposed | v1 |
| asm_rev_growth_base | Income Statement -- Revenue | Revenue growth | base | 2028 | 1.00 | percent | Flat %/yr, applied recursively: revenue_t = revenue_(t-1) * (1 + g) | N/A | 2.94 | -1.57 | -0.79 | -1.68 | -1.68 | 2.94 | -0.79 | Below FY2022's post-pandemic snap-back (+2.94%) and above the FY2023-FY2025 raw-decline trend; matches the FY2024-vs-FY2023(52-week-normalized) growth of +1.12%, treated as the cleanest recent read once the FY2023 53-week distortion is removed. Continuation of a stabilizing, low-single-digit trend -- explicitly NOT a return to the FY2021/FY2022 growth rates. | (none) | revenue | 2026-03-11 | proposed | v1 |
| asm_rev_growth_base | Income Statement -- Revenue | Revenue growth | base | 2029 | 1.00 | percent | Flat %/yr, applied recursively: revenue_t = revenue_(t-1) * (1 + g) | N/A | 2.94 | -1.57 | -0.79 | -1.68 | -1.68 | 2.94 | -0.79 | Below FY2022's post-pandemic snap-back (+2.94%) and above the FY2023-FY2025 raw-decline trend; matches the FY2024-vs-FY2023(52-week-normalized) growth of +1.12%, treated as the cleanest recent read once the FY2023 53-week distortion is removed. Continuation of a stabilizing, low-single-digit trend -- explicitly NOT a return to the FY2021/FY2022 growth rates. | (none) | revenue | 2026-03-11 | proposed | v1 |
| asm_rev_growth_base | Income Statement -- Revenue | Revenue growth | base | 2030 | 1.00 | percent | Flat %/yr, applied recursively: revenue_t = revenue_(t-1) * (1 + g) | N/A | 2.94 | -1.57 | -0.79 | -1.68 | -1.68 | 2.94 | -0.79 | Below FY2022's post-pandemic snap-back (+2.94%) and above the FY2023-FY2025 raw-decline trend; matches the FY2024-vs-FY2023(52-week-normalized) growth of +1.12%, treated as the cleanest recent read once the FY2023 53-week distortion is removed. Continuation of a stabilizing, low-single-digit trend -- explicitly NOT a return to the FY2021/FY2022 growth rates. | (none) | revenue | 2026-03-11 | proposed | v1 |
| asm_rev_growth_downside | Income Statement -- Revenue | Revenue growth | downside | 2026 | -2.50 | percent | Flat %/yr, applied recursively: revenue_t = revenue_(t-1) * (1 + g) | N/A | 2.94 | -1.57 | -0.79 | -1.68 | -1.68 | 2.94 | -0.79 | Beyond the single worst observed historical decline (-1.68%, FY2025) by roughly 1.5x, reflecting sustained discretionary-spending pressure -- a continued-deterioration case, not a fabricated crisis or extreme event. | (none) | revenue | 2026-03-11 | proposed | v1 |
| asm_rev_growth_downside | Income Statement -- Revenue | Revenue growth | downside | 2027 | -2.50 | percent | Flat %/yr, applied recursively: revenue_t = revenue_(t-1) * (1 + g) | N/A | 2.94 | -1.57 | -0.79 | -1.68 | -1.68 | 2.94 | -0.79 | Beyond the single worst observed historical decline (-1.68%, FY2025) by roughly 1.5x, reflecting sustained discretionary-spending pressure -- a continued-deterioration case, not a fabricated crisis or extreme event. | (none) | revenue | 2026-03-11 | proposed | v1 |
| asm_rev_growth_downside | Income Statement -- Revenue | Revenue growth | downside | 2028 | -2.50 | percent | Flat %/yr, applied recursively: revenue_t = revenue_(t-1) * (1 + g) | N/A | 2.94 | -1.57 | -0.79 | -1.68 | -1.68 | 2.94 | -0.79 | Beyond the single worst observed historical decline (-1.68%, FY2025) by roughly 1.5x, reflecting sustained discretionary-spending pressure -- a continued-deterioration case, not a fabricated crisis or extreme event. | (none) | revenue | 2026-03-11 | proposed | v1 |
| asm_rev_growth_downside | Income Statement -- Revenue | Revenue growth | downside | 2029 | -2.50 | percent | Flat %/yr, applied recursively: revenue_t = revenue_(t-1) * (1 + g) | N/A | 2.94 | -1.57 | -0.79 | -1.68 | -1.68 | 2.94 | -0.79 | Beyond the single worst observed historical decline (-1.68%, FY2025) by roughly 1.5x, reflecting sustained discretionary-spending pressure -- a continued-deterioration case, not a fabricated crisis or extreme event. | (none) | revenue | 2026-03-11 | proposed | v1 |
| asm_rev_growth_downside | Income Statement -- Revenue | Revenue growth | downside | 2030 | -2.50 | percent | Flat %/yr, applied recursively: revenue_t = revenue_(t-1) * (1 + g) | N/A | 2.94 | -1.57 | -0.79 | -1.68 | -1.68 | 2.94 | -0.79 | Beyond the single worst observed historical decline (-1.68%, FY2025) by roughly 1.5x, reflecting sustained discretionary-spending pressure -- a continued-deterioration case, not a fabricated crisis or extreme event. | (none) | revenue | 2026-03-11 | proposed | v1 |
| asm_rev_growth_upside | Income Statement -- Revenue | Revenue growth | upside | 2026 | 3.00 | percent | Flat %/yr, applied recursively: revenue_t = revenue_(t-1) * (1 + g) | N/A | 2.94 | -1.57 | -0.79 | -1.68 | -1.68 | 2.94 | -0.79 | At the high end of, without exceeding, the 5-year historical maximum (+2.94%, FY2022); reflects improved traffic/comp execution within the range Target has actually achieved, never an unprecedented acceleration. | (none) | revenue | 2026-03-11 | proposed | v1 |
| asm_rev_growth_upside | Income Statement -- Revenue | Revenue growth | upside | 2027 | 3.00 | percent | Flat %/yr, applied recursively: revenue_t = revenue_(t-1) * (1 + g) | N/A | 2.94 | -1.57 | -0.79 | -1.68 | -1.68 | 2.94 | -0.79 | At the high end of, without exceeding, the 5-year historical maximum (+2.94%, FY2022); reflects improved traffic/comp execution within the range Target has actually achieved, never an unprecedented acceleration. | (none) | revenue | 2026-03-11 | proposed | v1 |
| asm_rev_growth_upside | Income Statement -- Revenue | Revenue growth | upside | 2028 | 3.00 | percent | Flat %/yr, applied recursively: revenue_t = revenue_(t-1) * (1 + g) | N/A | 2.94 | -1.57 | -0.79 | -1.68 | -1.68 | 2.94 | -0.79 | At the high end of, without exceeding, the 5-year historical maximum (+2.94%, FY2022); reflects improved traffic/comp execution within the range Target has actually achieved, never an unprecedented acceleration. | (none) | revenue | 2026-03-11 | proposed | v1 |
| asm_rev_growth_upside | Income Statement -- Revenue | Revenue growth | upside | 2029 | 3.00 | percent | Flat %/yr, applied recursively: revenue_t = revenue_(t-1) * (1 + g) | N/A | 2.94 | -1.57 | -0.79 | -1.68 | -1.68 | 2.94 | -0.79 | At the high end of, without exceeding, the 5-year historical maximum (+2.94%, FY2022); reflects improved traffic/comp execution within the range Target has actually achieved, never an unprecedented acceleration. | (none) | revenue | 2026-03-11 | proposed | v1 |
| asm_rev_growth_upside | Income Statement -- Revenue | Revenue growth | upside | 2030 | 3.00 | percent | Flat %/yr, applied recursively: revenue_t = revenue_(t-1) * (1 + g) | N/A | 2.94 | -1.57 | -0.79 | -1.68 | -1.68 | 2.94 | -0.79 | At the high end of, without exceeding, the 5-year historical maximum (+2.94%, FY2022); reflects improved traffic/comp execution within the range Target has actually achieved, never an unprecedented acceleration. | (none) | revenue | 2026-03-11 | proposed | v1 |
| asm_min_cash_buffer_pct_base | Liquidity Policy -- Minimum Cash Buffer | Minimum cash buffer | base | 2026 | 3.00 | percent | Flat % of revenue policy (see Section 5 for the 5-policy comparison) | 5.58 | 2.04 | 3.54 | 4.47 | 5.24 | 2.04 | 5.58 | 4.47 | Candidate policy, not yet endorsed (see docs/milestone_3_forecast_review_package.md Section 5 for the full 5-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%) -- used here only to produce one concrete deployable-capacity figure for the base forecast run, pending the reviewer's choice among the 5 compared policies. | (none) | cash_and_equivalents_balance_sheet, revenue | 2026-03-11 | proposed | v1 |
| asm_min_cash_buffer_pct_base | Liquidity Policy -- Minimum Cash Buffer | Minimum cash buffer | base | 2027 | 3.00 | percent | Flat % of revenue policy (see Section 5 for the 5-policy comparison) | 5.58 | 2.04 | 3.54 | 4.47 | 5.24 | 2.04 | 5.58 | 4.47 | Candidate policy, not yet endorsed (see docs/milestone_3_forecast_review_package.md Section 5 for the full 5-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%) -- used here only to produce one concrete deployable-capacity figure for the base forecast run, pending the reviewer's choice among the 5 compared policies. | (none) | cash_and_equivalents_balance_sheet, revenue | 2026-03-11 | proposed | v1 |
| asm_min_cash_buffer_pct_base | Liquidity Policy -- Minimum Cash Buffer | Minimum cash buffer | base | 2028 | 3.00 | percent | Flat % of revenue policy (see Section 5 for the 5-policy comparison) | 5.58 | 2.04 | 3.54 | 4.47 | 5.24 | 2.04 | 5.58 | 4.47 | Candidate policy, not yet endorsed (see docs/milestone_3_forecast_review_package.md Section 5 for the full 5-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%) -- used here only to produce one concrete deployable-capacity figure for the base forecast run, pending the reviewer's choice among the 5 compared policies. | (none) | cash_and_equivalents_balance_sheet, revenue | 2026-03-11 | proposed | v1 |
| asm_min_cash_buffer_pct_base | Liquidity Policy -- Minimum Cash Buffer | Minimum cash buffer | base | 2029 | 3.00 | percent | Flat % of revenue policy (see Section 5 for the 5-policy comparison) | 5.58 | 2.04 | 3.54 | 4.47 | 5.24 | 2.04 | 5.58 | 4.47 | Candidate policy, not yet endorsed (see docs/milestone_3_forecast_review_package.md Section 5 for the full 5-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%) -- used here only to produce one concrete deployable-capacity figure for the base forecast run, pending the reviewer's choice among the 5 compared policies. | (none) | cash_and_equivalents_balance_sheet, revenue | 2026-03-11 | proposed | v1 |
| asm_min_cash_buffer_pct_base | Liquidity Policy -- Minimum Cash Buffer | Minimum cash buffer | base | 2030 | 3.00 | percent | Flat % of revenue policy (see Section 5 for the 5-policy comparison) | 5.58 | 2.04 | 3.54 | 4.47 | 5.24 | 2.04 | 5.58 | 4.47 | Candidate policy, not yet endorsed (see docs/milestone_3_forecast_review_package.md Section 5 for the full 5-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%) -- used here only to produce one concrete deployable-capacity figure for the base forecast run, pending the reviewer's choice among the 5 compared policies. | (none) | cash_and_equivalents_balance_sheet, revenue | 2026-03-11 | proposed | v1 |
| asm_min_cash_buffer_pct_downside | Liquidity Policy -- Minimum Cash Buffer | Minimum cash buffer | downside | 2026 | 3.00 | percent | Flat % of revenue policy (see Section 5 for the 5-policy comparison) | 5.58 | 2.04 | 3.54 | 4.47 | 5.24 | 2.04 | 5.58 | 4.47 | Candidate policy, not yet endorsed (see docs/milestone_3_forecast_review_package.md Section 5 for the full 5-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%) -- used here only to produce one concrete deployable-capacity figure for the base forecast run, pending the reviewer's choice among the 5 compared policies. | (none) | cash_and_equivalents_balance_sheet, revenue | 2026-03-11 | proposed | v1 |
| asm_min_cash_buffer_pct_downside | Liquidity Policy -- Minimum Cash Buffer | Minimum cash buffer | downside | 2027 | 3.00 | percent | Flat % of revenue policy (see Section 5 for the 5-policy comparison) | 5.58 | 2.04 | 3.54 | 4.47 | 5.24 | 2.04 | 5.58 | 4.47 | Candidate policy, not yet endorsed (see docs/milestone_3_forecast_review_package.md Section 5 for the full 5-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%) -- used here only to produce one concrete deployable-capacity figure for the base forecast run, pending the reviewer's choice among the 5 compared policies. | (none) | cash_and_equivalents_balance_sheet, revenue | 2026-03-11 | proposed | v1 |
| asm_min_cash_buffer_pct_downside | Liquidity Policy -- Minimum Cash Buffer | Minimum cash buffer | downside | 2028 | 3.00 | percent | Flat % of revenue policy (see Section 5 for the 5-policy comparison) | 5.58 | 2.04 | 3.54 | 4.47 | 5.24 | 2.04 | 5.58 | 4.47 | Candidate policy, not yet endorsed (see docs/milestone_3_forecast_review_package.md Section 5 for the full 5-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%) -- used here only to produce one concrete deployable-capacity figure for the base forecast run, pending the reviewer's choice among the 5 compared policies. | (none) | cash_and_equivalents_balance_sheet, revenue | 2026-03-11 | proposed | v1 |
| asm_min_cash_buffer_pct_downside | Liquidity Policy -- Minimum Cash Buffer | Minimum cash buffer | downside | 2029 | 3.00 | percent | Flat % of revenue policy (see Section 5 for the 5-policy comparison) | 5.58 | 2.04 | 3.54 | 4.47 | 5.24 | 2.04 | 5.58 | 4.47 | Candidate policy, not yet endorsed (see docs/milestone_3_forecast_review_package.md Section 5 for the full 5-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%) -- used here only to produce one concrete deployable-capacity figure for the base forecast run, pending the reviewer's choice among the 5 compared policies. | (none) | cash_and_equivalents_balance_sheet, revenue | 2026-03-11 | proposed | v1 |
| asm_min_cash_buffer_pct_downside | Liquidity Policy -- Minimum Cash Buffer | Minimum cash buffer | downside | 2030 | 3.00 | percent | Flat % of revenue policy (see Section 5 for the 5-policy comparison) | 5.58 | 2.04 | 3.54 | 4.47 | 5.24 | 2.04 | 5.58 | 4.47 | Candidate policy, not yet endorsed (see docs/milestone_3_forecast_review_package.md Section 5 for the full 5-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%) -- used here only to produce one concrete deployable-capacity figure for the base forecast run, pending the reviewer's choice among the 5 compared policies. | (none) | cash_and_equivalents_balance_sheet, revenue | 2026-03-11 | proposed | v1 |
| asm_min_cash_buffer_pct_upside | Liquidity Policy -- Minimum Cash Buffer | Minimum cash buffer | upside | 2026 | 3.00 | percent | Flat % of revenue policy (see Section 5 for the 5-policy comparison) | 5.58 | 2.04 | 3.54 | 4.47 | 5.24 | 2.04 | 5.58 | 4.47 | Candidate policy, not yet endorsed (see docs/milestone_3_forecast_review_package.md Section 5 for the full 5-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%) -- used here only to produce one concrete deployable-capacity figure for the base forecast run, pending the reviewer's choice among the 5 compared policies. | (none) | cash_and_equivalents_balance_sheet, revenue | 2026-03-11 | proposed | v1 |
| asm_min_cash_buffer_pct_upside | Liquidity Policy -- Minimum Cash Buffer | Minimum cash buffer | upside | 2027 | 3.00 | percent | Flat % of revenue policy (see Section 5 for the 5-policy comparison) | 5.58 | 2.04 | 3.54 | 4.47 | 5.24 | 2.04 | 5.58 | 4.47 | Candidate policy, not yet endorsed (see docs/milestone_3_forecast_review_package.md Section 5 for the full 5-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%) -- used here only to produce one concrete deployable-capacity figure for the base forecast run, pending the reviewer's choice among the 5 compared policies. | (none) | cash_and_equivalents_balance_sheet, revenue | 2026-03-11 | proposed | v1 |
| asm_min_cash_buffer_pct_upside | Liquidity Policy -- Minimum Cash Buffer | Minimum cash buffer | upside | 2028 | 3.00 | percent | Flat % of revenue policy (see Section 5 for the 5-policy comparison) | 5.58 | 2.04 | 3.54 | 4.47 | 5.24 | 2.04 | 5.58 | 4.47 | Candidate policy, not yet endorsed (see docs/milestone_3_forecast_review_package.md Section 5 for the full 5-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%) -- used here only to produce one concrete deployable-capacity figure for the base forecast run, pending the reviewer's choice among the 5 compared policies. | (none) | cash_and_equivalents_balance_sheet, revenue | 2026-03-11 | proposed | v1 |
| asm_min_cash_buffer_pct_upside | Liquidity Policy -- Minimum Cash Buffer | Minimum cash buffer | upside | 2029 | 3.00 | percent | Flat % of revenue policy (see Section 5 for the 5-policy comparison) | 5.58 | 2.04 | 3.54 | 4.47 | 5.24 | 2.04 | 5.58 | 4.47 | Candidate policy, not yet endorsed (see docs/milestone_3_forecast_review_package.md Section 5 for the full 5-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%) -- used here only to produce one concrete deployable-capacity figure for the base forecast run, pending the reviewer's choice among the 5 compared policies. | (none) | cash_and_equivalents_balance_sheet, revenue | 2026-03-11 | proposed | v1 |
| asm_min_cash_buffer_pct_upside | Liquidity Policy -- Minimum Cash Buffer | Minimum cash buffer | upside | 2030 | 3.00 | percent | Flat % of revenue policy (see Section 5 for the 5-policy comparison) | 5.58 | 2.04 | 3.54 | 4.47 | 5.24 | 2.04 | 5.58 | 4.47 | Candidate policy, not yet endorsed (see docs/milestone_3_forecast_review_package.md Section 5 for the full 5-policy comparison): 3% of forecast revenue scales with the business (unlike a fixed dollar figure) and sits above the historical minimum ratio (2.04%, FY2022) while below the recent (FY2024-FY2025) actual ratios (4.47%-5.24%) -- used here only to produce one concrete deployable-capacity figure for the base forecast run, pending the reviewer's choice among the 5 compared policies. | (none) | cash_and_equivalents_balance_sheet, revenue | 2026-03-11 | proposed | v1 |

### 1a. Source Fact-ID Appendix (full, non-compacted)

Every real fact ID actually cited anywhere in Section 1, in full -- annual_facts IDs verified against the live database (`SELECT annual_fact_id FROM annual_facts ...`), and raw_facts IDs for the one metric sourced outside annual_facts.

| Metric | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---|---|---|---|---|
| accounts_payable | `annual:accounts_payable:2021:latest_restated` | `annual:accounts_payable:2022:latest_restated` | `annual:accounts_payable:2023:latest_restated` | `annual:accounts_payable:2024:latest_restated` | `annual:accounts_payable:2025:latest_restated` |
| capital_expenditure | `annual:capital_expenditure:2021:latest_restated` | `annual:capital_expenditure:2022:latest_restated` | `annual:capital_expenditure:2023:latest_restated` | `annual:capital_expenditure:2024:latest_restated` | `annual:capital_expenditure:2025:latest_restated` |
| cash_and_equivalents_balance_sheet | `annual:cash_and_equivalents_balance_sheet:2021:latest_restated` | `annual:cash_and_equivalents_balance_sheet:2022:latest_restated` | `annual:cash_and_equivalents_balance_sheet:2023:latest_restated` | `annual:cash_and_equivalents_balance_sheet:2024:latest_restated` | `annual:cash_and_equivalents_balance_sheet:2025:latest_restated` |
| cost_of_sales | `annual:cost_of_sales:2021:latest_restated` | `annual:cost_of_sales:2022:latest_restated` | `annual:cost_of_sales:2023:latest_restated` | `annual:cost_of_sales:2024:latest_restated` | `annual:cost_of_sales:2025:latest_restated` |
| debt_proceeds | `annual:debt_proceeds:2021:latest_restated` | `annual:debt_proceeds:2022:latest_restated` | `annual:debt_proceeds:2023:latest_restated` | `annual:debt_proceeds:2024:latest_restated` | `annual:debt_proceeds:2025:latest_restated` |
| debt_repayments | `annual:debt_repayments:2021:latest_restated` | `annual:debt_repayments:2022:latest_restated` | `annual:debt_repayments:2023:latest_restated` | `annual:debt_repayments:2024:latest_restated` | `annual:debt_repayments:2025:latest_restated` |
| depreciation_amortization_cfo_addback | `0000027419-24-000032:us-gaap:DepreciationDepletionAndAmortization:c-11` | `0000027419-25-000018:us-gaap:DepreciationDepletionAndAmortization:c-5` | `0000027419-26-000016:us-gaap:DepreciationDepletionAndAmortization:c-5` | `0000027419-26-000016:us-gaap:DepreciationDepletionAndAmortization:c-4` | `0000027419-26-000016:us-gaap:DepreciationDepletionAndAmortization:c-1` |
| depreciation_amortization_opex | `annual:depreciation_amortization_opex:2021:latest_restated` | `annual:depreciation_amortization_opex:2022:latest_restated` | `annual:depreciation_amortization_opex:2023:latest_restated` | `annual:depreciation_amortization_opex:2024:latest_restated` | `annual:depreciation_amortization_opex:2025:latest_restated` |
| diluted_shares | `annual:diluted_shares:2021:latest_restated` | `annual:diluted_shares:2022:latest_restated` | `annual:diluted_shares:2023:latest_restated` | `annual:diluted_shares:2024:latest_restated` | `annual:diluted_shares:2025:latest_restated` |
| dividends_paid | `annual:dividends_paid:2021:latest_restated` | `annual:dividends_paid:2022:latest_restated` | `annual:dividends_paid:2023:latest_restated` | `annual:dividends_paid:2024:latest_restated` | `annual:dividends_paid:2025:latest_restated` |
| finance_lease_liabilities | `annual:finance_lease_liabilities:2021:latest_restated` | `annual:finance_lease_liabilities:2022:latest_restated` | `annual:finance_lease_liabilities:2023:latest_restated` | `annual:finance_lease_liabilities:2024:latest_restated` | `annual:finance_lease_liabilities:2025:latest_restated` |
| free_cash_flow | `annual:free_cash_flow:2021:latest_restated` | `annual:free_cash_flow:2022:latest_restated` | `annual:free_cash_flow:2023:latest_restated` | `annual:free_cash_flow:2024:latest_restated` | `annual:free_cash_flow:2025:latest_restated` |
| gross_profit | `annual:gross_profit:2021:latest_restated` | `annual:gross_profit:2022:latest_restated` | `annual:gross_profit:2023:latest_restated` | `annual:gross_profit:2024:latest_restated` | `annual:gross_profit:2025:latest_restated` |
| income_tax_expense | `annual:income_tax_expense:2021:latest_restated` | `annual:income_tax_expense:2022:latest_restated` | `annual:income_tax_expense:2023:latest_restated` | `annual:income_tax_expense:2024:latest_restated` | `annual:income_tax_expense:2025:latest_restated` |
| interest_expense | `annual:interest_expense:2021:latest_restated` | `annual:interest_expense:2022:latest_restated` | `annual:interest_expense:2023:latest_restated` | `annual:interest_expense:2024:latest_restated` | `annual:interest_expense:2025:latest_restated` |
| inventory | `annual:inventory:2021:latest_restated` | `annual:inventory:2022:latest_restated` | `annual:inventory:2023:latest_restated` | `annual:inventory:2024:latest_restated` | `annual:inventory:2025:latest_restated` |
| net_income | `annual:net_income:2021:latest_restated` | `annual:net_income:2022:latest_restated` | `annual:net_income:2023:latest_restated` | `annual:net_income:2024:latest_restated` | `annual:net_income:2025:latest_restated` |
| net_other_income | `annual:net_other_income:2021:latest_restated` | `annual:net_other_income:2022:latest_restated` | `annual:net_other_income:2023:latest_restated` | `annual:net_other_income:2024:latest_restated` | `annual:net_other_income:2025:latest_restated` |
| operating_cash_flow | `annual:operating_cash_flow:2021:latest_restated` | `annual:operating_cash_flow:2022:latest_restated` | `annual:operating_cash_flow:2023:latest_restated` | `annual:operating_cash_flow:2024:latest_restated` | `annual:operating_cash_flow:2025:latest_restated` |
| operating_expenses | `annual:operating_expenses:2021:latest_restated` | `annual:operating_expenses:2022:latest_restated` | `annual:operating_expenses:2023:latest_restated` | `annual:operating_expenses:2024:latest_restated` | `annual:operating_expenses:2025:latest_restated` |
| pretax_income | `annual:pretax_income:2021:latest_restated` | `annual:pretax_income:2022:latest_restated` | `annual:pretax_income:2023:latest_restated` | `annual:pretax_income:2024:latest_restated` | `annual:pretax_income:2025:latest_restated` |
| revenue | `annual:revenue:2021:latest_restated` | `annual:revenue:2022:latest_restated` | `annual:revenue:2023:latest_restated` | `annual:revenue:2024:latest_restated` | `annual:revenue:2025:latest_restated` |
| share_repurchases | `annual:share_repurchases:2021:latest_restated` | `annual:share_repurchases:2022:latest_restated` | `annual:share_repurchases:2023:latest_restated` | `annual:share_repurchases:2024:latest_restated` | `annual:share_repurchases:2025:latest_restated` |
| total_debt_gaap | `annual:total_debt_gaap:2021:latest_restated` | `annual:total_debt_gaap:2022:latest_restated` | `annual:total_debt_gaap:2023:latest_restated` | `annual:total_debt_gaap:2024:latest_restated` | `annual:total_debt_gaap:2025:latest_restated` |

## 2. Complete Forecast Outputs (all scenarios, FY2026-FY2030)

Three tables per scenario -- income statement, cash flow, and capital position -- covering every column requested. Signs: a negative cash-flow-statement figure is a use of cash; `inventory_cash_impact` negative = inventory build (use of cash); `ap_cash_impact` positive = AP increase (source of cash); `investing_cash_flow` and `financing_cash_flow` are signed as reported (outflow negative). All dollar figures in USD millions except per-share figures.

### 2.1 Scenario: BASE

**Income Statement**
| FY | Revenue | COGS | Gross Profit | Gross Margin % | Opex (SG&A) | D&A in Opex | Operating Income | Op Margin % | Interest Exp | Net Other Income | Pretax Income | Income Tax | Net Income | Diluted Shares | Diluted EPS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 105,827.8 | 76,270.1 | 29,557.7 | 27.93% | 21,747.6 | 2,728.2 | 5,081.9 | 4.80% | 444.6 | 95.0 | 4,732.2 | 1,050.6 | 3,681.7 | 453.3 | 8.12 |
| 2027 | 106,886.1 | 77,014.6 | 29,871.5 | 27.95% | 21,965.1 | 2,837.8 | 5,068.5 | 4.74% | 444.6 | 95.0 | 4,718.9 | 1,047.6 | 3,671.3 | 451.1 | 8.14 |
| 2028 | 107,954.9 | 77,765.3 | 30,189.6 | 27.96% | 22,184.7 | 2,949.3 | 5,055.5 | 4.68% | 444.6 | 95.0 | 4,705.9 | 1,044.7 | 3,661.2 | 448.8 | 8.16 |
| 2029 | 109,034.5 | 78,523.4 | 30,511.1 | 27.98% | 22,406.6 | 3,063.9 | 5,040.7 | 4.62% | 444.6 | 95.0 | 4,691.0 | 1,041.4 | 3,649.6 | 446.6 | 8.17 |
| 2030 | 110,124.8 | 79,289.9 | 30,835.0 | 28.00% | 22,630.7 | 3,180.4 | 5,023.9 | 4.56% | 444.6 | 95.0 | 4,674.3 | 1,037.7 | 3,636.6 | 444.3 | 8.18 |

**Cash Flow**
| FY | D&A Add-back | Inventory Cash Impact | AP Cash Impact | Other Op CF | CFO | CapEx | FCF | Dividends | Post-Dividend Capacity | Debt Issuance | Debt Repayment | Repurchases | Financing CF |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 3,297.6 | -183.7 | 115.1 | 150.0 | 7,060.7 | 3,809.8 | 3,250.9 | 2,083.6 | 1,167.3 | 700.0 | 700.0 | 466.9 | -2,550.5 |
| 2027 | 3,463.1 | -124.9 | 124.3 | 150.0 | 7,283.9 | 3,847.9 | 3,436.0 | 2,114.6 | 1,321.3 | 700.0 | 700.0 | 528.5 | -2,643.2 |
| 2028 | 3,632.7 | -126.1 | 125.4 | 150.0 | 7,443.1 | 3,886.4 | 3,556.7 | 2,146.1 | 1,410.6 | 700.0 | 700.0 | 564.2 | -2,710.4 |
| 2029 | 3,805.3 | -127.4 | 126.6 | 150.0 | 7,604.1 | 3,925.2 | 3,678.9 | 2,178.1 | 1,500.8 | 700.0 | 700.0 | 600.3 | -2,778.4 |
| 2030 | 3,979.9 | -128.7 | 128.0 | 150.0 | 7,765.8 | 3,964.5 | 3,801.3 | 2,210.6 | 1,590.8 | 700.0 | 700.0 | 636.3 | -2,846.9 |

**Capital Position**
| FY | Cash Before Discretionary Deployment | Min Cash Buffer | Debt Reserve | Deployable Capacity | Mgmt-Selected Deployment | Ending Cash | Ending Debt | Valuation Net Debt | Funding Warning |
|---|---|---|---|---|---|---|---|---|---|
| 2026 | 6,655.3 | 3,174.8 | 700.0 | 2,780.5 | N/A -- no deployment selected this round | 6,188.4 | 14,343.0 | 8,154.6 | no |
| 2027 | 7,509.7 | 3,206.6 | 700.0 | 3,603.1 | N/A -- no deployment selected this round | 6,981.2 | 14,343.0 | 7,361.8 | no |
| 2028 | 8,391.8 | 3,238.6 | 700.0 | 4,453.1 | N/A -- no deployment selected this round | 7,827.5 | 14,343.0 | 6,515.5 | no |
| 2029 | 9,328.3 | 3,271.0 | 700.0 | 5,357.3 | N/A -- no deployment selected this round | 8,728.0 | 14,343.0 | 5,615.0 | no |
| 2030 | 10,318.8 | 3,303.7 | 700.0 | 6,315.0 | N/A -- no deployment selected this round | 9,682.5 | 14,343.0 | 4,660.5 | no |

### 2.2 Scenario: UPSIDE

**Income Statement**
| FY | Revenue | COGS | Gross Profit | Gross Margin % | Opex (SG&A) | D&A in Opex | Operating Income | Op Margin % | Interest Exp | Net Other Income | Pretax Income | Income Tax | Net Income | Diluted Shares | Diluted EPS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 107,923.4 | 77,780.4 | 30,143.0 | 27.93% | 22,178.3 | 2,890.2 | 5,074.6 | 4.70% | 405.8 | 100.0 | 4,768.8 | 1,025.3 | 3,743.5 | 448.8 | 8.34 |
| 2027 | 111,161.1 | 79,871.5 | 31,289.6 | 28.15% | 22,635.7 | 3,062.5 | 5,591.4 | 5.03% | 385.5 | 100.0 | 5,305.9 | 1,140.8 | 4,165.1 | 442.0 | 9.42 |
| 2028 | 114,495.9 | 82,019.2 | 32,476.8 | 28.36% | 23,099.6 | 3,243.7 | 6,133.5 | 5.36% | 365.2 | 100.0 | 5,868.4 | 1,261.7 | 4,606.7 | 435.4 | 10.58 |
| 2029 | 117,930.8 | 84,223.8 | 33,707.0 | 28.58% | 23,572.0 | 3,431.8 | 6,703.2 | 5.68% | 344.9 | 100.0 | 6,458.3 | 1,388.5 | 5,069.8 | 428.9 | 11.82 |
| 2030 | 121,468.7 | 86,485.7 | 34,983.0 | 28.80% | 24,050.8 | 3,629.5 | 7,302.7 | 6.01% | 324.6 | 100.0 | 7,078.1 | 1,521.8 | 5,556.3 | 422.4 | 13.15 |

**Cash Flow**
| FY | D&A Add-back | Inventory Cash Impact | AP Cash Impact | Other Op CF | CFO | CapEx | FCF | Dividends | Post-Dividend Capacity | Debt Issuance | Debt Repayment | Repurchases | Financing CF |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 3,416.9 | 432.4 | 989.6 | 250.0 | 8,832.3 | 4,640.7 | 4,191.6 | 2,103.1 | 2,088.5 | 300.0 | 1,000.0 | 1,148.7 | -3,951.8 |
| 2027 | 3,657.2 | -356.1 | 365.9 | 250.0 | 8,082.1 | 4,779.9 | 3,302.2 | 2,154.4 | 1,147.8 | 300.0 | 1,000.0 | 631.3 | -3,485.7 |
| 2028 | 3,910.0 | -366.8 | 375.8 | 250.0 | 8,775.7 | 4,923.3 | 3,852.4 | 2,207.0 | 1,645.4 | 300.0 | 1,000.0 | 905.0 | -3,811.9 |
| 2029 | 4,174.8 | -377.8 | 385.8 | 250.0 | 9,502.5 | 5,071.0 | 4,431.5 | 2,260.8 | 2,170.6 | 300.0 | 1,000.0 | 1,193.9 | -4,154.7 |
| 2030 | 4,450.6 | -389.2 | 395.8 | 250.0 | 10,263.6 | 5,223.2 | 5,040.4 | 2,316.0 | 2,724.4 | 300.0 | 1,000.0 | 1,498.4 | -4,514.4 |

**Capital Position**
| FY | Cash Before Discretionary Deployment | Min Cash Buffer | Debt Reserve | Deployable Capacity | Mgmt-Selected Deployment | Ending Cash | Ending Debt | Valuation Net Debt | Funding Warning |
|---|---|---|---|---|---|---|---|---|---|
| 2026 | 6,876.5 | 3,237.7 | 1,000.0 | 2,638.8 | N/A -- no deployment selected this round | 5,727.8 | 13,643.0 | 7,915.2 | no |
| 2027 | 6,175.6 | 3,334.8 | 1,000.0 | 1,840.8 | N/A -- no deployment selected this round | 5,544.3 | 12,943.0 | 7,398.7 | no |
| 2028 | 6,489.7 | 3,434.9 | 1,000.0 | 2,054.9 | N/A -- no deployment selected this round | 5,584.8 | 12,243.0 | 6,658.2 | no |
| 2029 | 7,055.4 | 3,537.9 | 1,000.0 | 2,517.5 | N/A -- no deployment selected this round | 5,861.6 | 11,543.0 | 5,681.4 | no |
| 2030 | 7,886.0 | 3,644.1 | 1,000.0 | 3,241.9 | N/A -- no deployment selected this round | 6,387.6 | 10,843.0 | 4,455.4 | no |

### 2.3 Scenario: DOWNSIDE

**Income Statement**
| FY | Revenue | COGS | Gross Profit | Gross Margin % | Opex (SG&A) | D&A in Opex | Operating Income | Op Margin % | Interest Exp | Net Other Income | Pretax Income | Income Tax | Net Income | Diluted Shares | Diluted EPS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 102,160.5 | 73,627.1 | 28,533.4 | 27.93% | 20,994.0 | 2,531.5 | 5,007.9 | 4.90% | 491.1 | 80.0 | 4,596.8 | 1,057.3 | 3,539.6 | 455.6 | 7.77 |
| 2027 | 99,606.5 | 72,191.8 | 27,414.7 | 27.52% | 20,656.4 | 2,544.9 | 4,213.4 | 4.23% | 497.9 | 80.0 | 3,795.5 | 873.0 | 2,922.5 | 455.6 | 6.41 |
| 2028 | 97,116.3 | 70,783.2 | 26,333.1 | 27.11% | 20,321.6 | 2,556.1 | 3,455.4 | 3.56% | 504.7 | 80.0 | 3,030.7 | 697.1 | 2,333.7 | 455.6 | 5.12 |
| 2029 | 94,688.4 | 69,400.0 | 25,288.4 | 26.71% | 19,991.6 | 2,566.1 | 2,730.8 | 2.88% | 511.5 | 80.0 | 2,299.4 | 528.9 | 1,770.5 | 455.6 | 3.89 |
| 2030 | 92,321.2 | 68,040.7 | 24,280.5 | 26.30% | 19,664.4 | 2,573.9 | 2,042.1 | 2.21% | 518.3 | 80.0 | 1,603.9 | 368.9 | 1,235.0 | 455.6 | 2.71 |

**Cash Flow**
| FY | D&A Add-back | Inventory Cash Impact | AP Cash Impact | Other Op CF | CFO | CapEx | FCF | Dividends | Post-Dividend Capacity | Debt Issuance | Debt Repayment | Repurchases | Financing CF |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 3,132.2 | -772.5 | -1,209.8 | 50.0 | 4,739.5 | 2,860.5 | 1,879.0 | 2,053.0 | -174.0 | 500.0 | 300.0 | 0.0 | -1,853.0 |
| 2027 | 3,177.4 | 326.9 | -222.5 | 50.0 | 6,254.4 | 2,789.0 | 3,465.4 | 2,053.0 | 1,412.4 | 500.0 | 300.0 | 0.0 | -1,853.0 |
| 2028 | 3,219.4 | 318.7 | -218.3 | 50.0 | 5,703.5 | 2,719.3 | 2,984.2 | 2,053.0 | 931.2 | 500.0 | 300.0 | 0.0 | -1,853.0 |
| 2029 | 3,257.3 | 310.8 | -214.4 | 50.0 | 5,174.2 | 2,651.3 | 2,522.9 | 2,053.0 | 469.9 | 500.0 | 300.0 | 0.0 | -1,853.0 |
| 2030 | 3,290.3 | 303.0 | -210.7 | 50.0 | 4,667.6 | 2,585.0 | 2,082.6 | 2,053.0 | 29.6 | 500.0 | 300.0 | 0.0 | -1,853.0 |

**Capital Position**
| FY | Cash Before Discretionary Deployment | Min Cash Buffer | Debt Reserve | Deployable Capacity | Mgmt-Selected Deployment | Ending Cash | Ending Debt | Valuation Net Debt | Funding Warning |
|---|---|---|---|---|---|---|---|---|---|
| 2026 | 5,514.0 | 3,064.8 | 300.0 | 2,149.2 | N/A -- no deployment selected this round | 5,514.0 | 14,543.0 | 9,029.0 | no |
| 2027 | 7,126.4 | 2,988.2 | 300.0 | 3,838.2 | N/A -- no deployment selected this round | 7,126.4 | 14,743.0 | 7,616.6 | no |
| 2028 | 8,257.6 | 2,913.5 | 300.0 | 5,044.2 | N/A -- no deployment selected this round | 8,257.6 | 14,943.0 | 6,685.4 | no |
| 2029 | 8,927.5 | 2,840.7 | 300.0 | 5,786.9 | N/A -- no deployment selected this round | 8,927.5 | 15,143.0 | 6,215.5 | no |
| 2030 | 9,157.2 | 2,769.6 | 300.0 | 6,087.5 | N/A -- no deployment selected this round | 9,157.2 | 15,343.0 | 6,185.8 | no |

## 3. Other Operating Cash Adjustments -- Standalone Bridge

**Historical bridge, FY2021-FY2025** (`historical_other_operating_cf_residual()`): `other = CFO - net_income - depreciation_amortization_cfo_addback - inventory_cash_impact - ap_cash_impact`, computed directly from the frozen `HISTORICAL` literals. FY2021 has no prior year in this project's 5-year source window to difference inventory/AP against, so its own residual cannot be derived and is reported as unavailable, not zero or estimated.

| FY | CFO | Net Income | D&A Add-back | Inventory Cash Impact | AP Cash Impact | Other (derived residual) |
|---|---|---|---|---|---|---|
| 2021 | 8,625.0 | 6,946.0 | 2,642.0 | N/A (no FY2020 balance) | N/A (no FY2020 balance) | **unavailable -- not derived** |
| 2022 | 4,018.0 | 2,780.0 | 2,700.0 | 403.0 | -1,991.0 | **126.0** |
| 2023 | 8,621.0 | 4,138.0 | 2,801.0 | 1,613.0 | -1,389.0 | **1,458.0** |
| 2024 | 7,367.0 | 4,091.0 | 2,981.0 | -854.0 | 955.0 | **194.0** |
| 2025 | 6,562.0 | 3,705.0 | 3,134.0 | 436.0 | -431.0 | **-282.0** |

Median of the 4 available years: **$160.0M** (sorted: [-282.0, 126.0, 194.0, 1458.0]).

**Forecast methodology (FY2026-FY2030)**: a single **flat $M/year** assumption per scenario (`other_operating_cf_musd`) -- BASE $150M, UPSIDE $250M, DOWNSIDE $50M -- selected near/around the historical median and range shown above. **Components included**: this line represents stock-based compensation, deferred income taxes, and other non-cash items and working-capital changes not separately modeled (i.e. everything in Target's real cash-flow statement between net income + D&A + inventory + AP and total CFO). **Not decomposed further** -- Target's own cash-flow statement does not break this residual into stock-comp/deferred-tax/other lines cleanly enough for this project's registered source set to re-derive each sub-component independently, which is disclosed as a limitation (Section 13's counterpart in the prior engine proposal, carried forward here). **Constant, not percentage-based, not a rolling average, and not independently modeled per component** -- a single flat dollar figure per scenario.

**Evidence this is never a backward-solved CFO plug**: `other_operating_cf_not_a_plug` (validation check 19) verifies the value is IDENTICAL across every one of the 5 forecast years within a scenario -- a residual plug would instead vary year to year, tracking whatever gap the other CFO components leave. Live result against the real forecast:

| Scenario | Status | Detail |
|---|---|---|
| base | PASS | other_operating_cf per year: [150.0, 150.0, 150.0, 150.0, 150.0] -- constant, consistent with a fixed assumption |
| upside | PASS | other_operating_cf per year: [250.0, 250.0, 250.0, 250.0, 250.0] -- constant, consistent with a fixed assumption |
| downside | PASS | other_operating_cf per year: [50.0, 50.0, 50.0, 50.0, 50.0] -- constant, consistent with a fixed assumption |

**Corruption test — proving the check actually detects a plug** (`demo_backward_solved_cfo_plug(years, target_cfo=7500.0)`): recomputes `other_operating_cf` backward so CFO hits a flat $7,500M target every year, then re-runs the same check against the corrupted BASE scenario:

| FY | Plugged other_operating_cf | Resulting CFO (forced) |
|---|---|---|
| 2026 | 589.3 | 7,500.0 |
| 2027 | 366.1 | 7,500.0 |
| 2028 | 206.9 | 7,500.0 |
| 2029 | 45.9 | 7,500.0 |
| 2030 | -115.8 | 7,500.0 |

Check result on the corrupted data: **FAIL** -- other_operating_cf per year: [589.3, 366.1, 206.9, 45.9, -115.8] -- VARIES across years, consistent with a backward-solved plug

## 4. Capital Allocation Waterfall

Exact order of operations (`capital_allocation_waterfall()`), computed as an independently *sequenced* running-balance calculation -- a different code path from `_run_from_metrics`' own block-formula arithmetic, reconciled against it as validation check 20 (`capital_allocation_waterfall_reconciliation`). All 15 scenario-years shown in full below.

### 4.1 Scenario: BASE

**FY2026** (beginning cash 5,488.0)

| Step | Label | Amount | Balance After |
|---|---|---|---|
| 1 | Operating cash generation (CFO) | 7,060.7 | 12,548.7 |
| 2 | Capital expenditures (CFI = -CapEx) | -3,809.8 | 8,738.9 |
| 3 | Dividends | -2,083.6 | 6,655.3 |
| 4 | Minimum cash preservation (checkpoint, no cash movement) (cash above minimum buffer at this checkpoint: 3,480.5) | 0.0 | 6,655.3 |
| 5 | Scheduled debt reserve / repayment (fixed schedule) | 0.0 | 6,655.3 |
| 5b | DEPLOYABLE CAPACITY CHECKPOINT (pre_discretionary_ending_cash - buffer - reserve, before any repurchase is subtracted) (deployable_capacity = 2,780.5) | 0.0 | 6,655.3 |
| 6 | Incremental (non-scheduled) financing -- always $0 (non-plug policy) | 0.0 | 6,655.3 |
| 7 | Discretionary investment / repurchases (fixed payout-ratio assumption) | -466.9 | 6,188.4 |
| 7b | Management-selected deployment (beyond the routine repurchase program; always $0 this round -- no deployment has been selected) | -0.0 | 6,188.4 |
| 8 | Ending cash | 0.0 | 6,188.4 |

**FY2027** (beginning cash 6,188.4)

| Step | Label | Amount | Balance After |
|---|---|---|---|
| 1 | Operating cash generation (CFO) | 7,283.9 | 13,472.3 |
| 2 | Capital expenditures (CFI = -CapEx) | -3,847.9 | 9,624.4 |
| 3 | Dividends | -2,114.6 | 7,509.7 |
| 4 | Minimum cash preservation (checkpoint, no cash movement) (cash above minimum buffer at this checkpoint: 4,303.1) | 0.0 | 7,509.7 |
| 5 | Scheduled debt reserve / repayment (fixed schedule) | 0.0 | 7,509.7 |
| 5b | DEPLOYABLE CAPACITY CHECKPOINT (pre_discretionary_ending_cash - buffer - reserve, before any repurchase is subtracted) (deployable_capacity = 3,603.1) | 0.0 | 7,509.7 |
| 6 | Incremental (non-scheduled) financing -- always $0 (non-plug policy) | 0.0 | 7,509.7 |
| 7 | Discretionary investment / repurchases (fixed payout-ratio assumption) | -528.5 | 6,981.2 |
| 7b | Management-selected deployment (beyond the routine repurchase program; always $0 this round -- no deployment has been selected) | -0.0 | 6,981.2 |
| 8 | Ending cash | 0.0 | 6,981.2 |

**FY2028** (beginning cash 6,981.2)

| Step | Label | Amount | Balance After |
|---|---|---|---|
| 1 | Operating cash generation (CFO) | 7,443.1 | 14,424.3 |
| 2 | Capital expenditures (CFI = -CapEx) | -3,886.4 | 10,537.9 |
| 3 | Dividends | -2,146.1 | 8,391.8 |
| 4 | Minimum cash preservation (checkpoint, no cash movement) (cash above minimum buffer at this checkpoint: 5,153.1) | 0.0 | 8,391.8 |
| 5 | Scheduled debt reserve / repayment (fixed schedule) | 0.0 | 8,391.8 |
| 5b | DEPLOYABLE CAPACITY CHECKPOINT (pre_discretionary_ending_cash - buffer - reserve, before any repurchase is subtracted) (deployable_capacity = 4,453.1) | 0.0 | 8,391.8 |
| 6 | Incremental (non-scheduled) financing -- always $0 (non-plug policy) | 0.0 | 8,391.8 |
| 7 | Discretionary investment / repurchases (fixed payout-ratio assumption) | -564.2 | 7,827.5 |
| 7b | Management-selected deployment (beyond the routine repurchase program; always $0 this round -- no deployment has been selected) | -0.0 | 7,827.5 |
| 8 | Ending cash | 0.0 | 7,827.5 |

**FY2029** (beginning cash 7,827.5)

| Step | Label | Amount | Balance After |
|---|---|---|---|
| 1 | Operating cash generation (CFO) | 7,604.1 | 15,431.7 |
| 2 | Capital expenditures (CFI = -CapEx) | -3,925.2 | 11,506.4 |
| 3 | Dividends | -2,178.1 | 9,328.3 |
| 4 | Minimum cash preservation (checkpoint, no cash movement) (cash above minimum buffer at this checkpoint: 6,057.3) | 0.0 | 9,328.3 |
| 5 | Scheduled debt reserve / repayment (fixed schedule) | 0.0 | 9,328.3 |
| 5b | DEPLOYABLE CAPACITY CHECKPOINT (pre_discretionary_ending_cash - buffer - reserve, before any repurchase is subtracted) (deployable_capacity = 5,357.3) | 0.0 | 9,328.3 |
| 6 | Incremental (non-scheduled) financing -- always $0 (non-plug policy) | 0.0 | 9,328.3 |
| 7 | Discretionary investment / repurchases (fixed payout-ratio assumption) | -600.3 | 8,728.0 |
| 7b | Management-selected deployment (beyond the routine repurchase program; always $0 this round -- no deployment has been selected) | -0.0 | 8,728.0 |
| 8 | Ending cash | 0.0 | 8,728.0 |

**FY2030** (beginning cash 8,728.0)

| Step | Label | Amount | Balance After |
|---|---|---|---|
| 1 | Operating cash generation (CFO) | 7,765.8 | 16,493.8 |
| 2 | Capital expenditures (CFI = -CapEx) | -3,964.5 | 12,529.3 |
| 3 | Dividends | -2,210.6 | 10,318.8 |
| 4 | Minimum cash preservation (checkpoint, no cash movement) (cash above minimum buffer at this checkpoint: 7,015.0) | 0.0 | 10,318.8 |
| 5 | Scheduled debt reserve / repayment (fixed schedule) | 0.0 | 10,318.8 |
| 5b | DEPLOYABLE CAPACITY CHECKPOINT (pre_discretionary_ending_cash - buffer - reserve, before any repurchase is subtracted) (deployable_capacity = 6,315.0) | 0.0 | 10,318.8 |
| 6 | Incremental (non-scheduled) financing -- always $0 (non-plug policy) | 0.0 | 10,318.8 |
| 7 | Discretionary investment / repurchases (fixed payout-ratio assumption) | -636.3 | 9,682.5 |
| 7b | Management-selected deployment (beyond the routine repurchase program; always $0 this round -- no deployment has been selected) | -0.0 | 9,682.5 |
| 8 | Ending cash | 0.0 | 9,682.5 |

### 4.2 Scenario: UPSIDE

**FY2026** (beginning cash 5,488.0)

| Step | Label | Amount | Balance After |
|---|---|---|---|
| 1 | Operating cash generation (CFO) | 8,832.3 | 14,320.3 |
| 2 | Capital expenditures (CFI = -CapEx) | -4,640.7 | 9,679.6 |
| 3 | Dividends | -2,103.1 | 7,576.5 |
| 4 | Minimum cash preservation (checkpoint, no cash movement) (cash above minimum buffer at this checkpoint: 4,338.8) | 0.0 | 7,576.5 |
| 5 | Scheduled debt reserve / repayment (fixed schedule) | -700.0 | 6,876.5 |
| 5b | DEPLOYABLE CAPACITY CHECKPOINT (pre_discretionary_ending_cash - buffer - reserve, before any repurchase is subtracted) (deployable_capacity = 2,638.8) | 0.0 | 6,876.5 |
| 6 | Incremental (non-scheduled) financing -- always $0 (non-plug policy) | 0.0 | 6,876.5 |
| 7 | Discretionary investment / repurchases (fixed payout-ratio assumption) | -1,148.7 | 5,727.8 |
| 7b | Management-selected deployment (beyond the routine repurchase program; always $0 this round -- no deployment has been selected) | -0.0 | 5,727.8 |
| 8 | Ending cash | 0.0 | 5,727.8 |

**FY2027** (beginning cash 5,727.8)

| Step | Label | Amount | Balance After |
|---|---|---|---|
| 1 | Operating cash generation (CFO) | 8,082.1 | 13,810.0 |
| 2 | Capital expenditures (CFI = -CapEx) | -4,779.9 | 9,030.0 |
| 3 | Dividends | -2,154.4 | 6,875.6 |
| 4 | Minimum cash preservation (checkpoint, no cash movement) (cash above minimum buffer at this checkpoint: 3,540.8) | 0.0 | 6,875.6 |
| 5 | Scheduled debt reserve / repayment (fixed schedule) | -700.0 | 6,175.6 |
| 5b | DEPLOYABLE CAPACITY CHECKPOINT (pre_discretionary_ending_cash - buffer - reserve, before any repurchase is subtracted) (deployable_capacity = 1,840.8) | 0.0 | 6,175.6 |
| 6 | Incremental (non-scheduled) financing -- always $0 (non-plug policy) | 0.0 | 6,175.6 |
| 7 | Discretionary investment / repurchases (fixed payout-ratio assumption) | -631.3 | 5,544.3 |
| 7b | Management-selected deployment (beyond the routine repurchase program; always $0 this round -- no deployment has been selected) | -0.0 | 5,544.3 |
| 8 | Ending cash | 0.0 | 5,544.3 |

**FY2028** (beginning cash 5,544.3)

| Step | Label | Amount | Balance After |
|---|---|---|---|
| 1 | Operating cash generation (CFO) | 8,775.7 | 14,320.0 |
| 2 | Capital expenditures (CFI = -CapEx) | -4,923.3 | 9,396.7 |
| 3 | Dividends | -2,207.0 | 7,189.7 |
| 4 | Minimum cash preservation (checkpoint, no cash movement) (cash above minimum buffer at this checkpoint: 3,754.9) | 0.0 | 7,189.7 |
| 5 | Scheduled debt reserve / repayment (fixed schedule) | -700.0 | 6,489.7 |
| 5b | DEPLOYABLE CAPACITY CHECKPOINT (pre_discretionary_ending_cash - buffer - reserve, before any repurchase is subtracted) (deployable_capacity = 2,054.9) | 0.0 | 6,489.7 |
| 6 | Incremental (non-scheduled) financing -- always $0 (non-plug policy) | 0.0 | 6,489.7 |
| 7 | Discretionary investment / repurchases (fixed payout-ratio assumption) | -905.0 | 5,584.8 |
| 7b | Management-selected deployment (beyond the routine repurchase program; always $0 this round -- no deployment has been selected) | -0.0 | 5,584.8 |
| 8 | Ending cash | 0.0 | 5,584.8 |

**FY2029** (beginning cash 5,584.8)

| Step | Label | Amount | Balance After |
|---|---|---|---|
| 1 | Operating cash generation (CFO) | 9,502.5 | 15,087.3 |
| 2 | Capital expenditures (CFI = -CapEx) | -5,071.0 | 10,016.2 |
| 3 | Dividends | -2,260.8 | 7,755.4 |
| 4 | Minimum cash preservation (checkpoint, no cash movement) (cash above minimum buffer at this checkpoint: 4,217.5) | 0.0 | 7,755.4 |
| 5 | Scheduled debt reserve / repayment (fixed schedule) | -700.0 | 7,055.4 |
| 5b | DEPLOYABLE CAPACITY CHECKPOINT (pre_discretionary_ending_cash - buffer - reserve, before any repurchase is subtracted) (deployable_capacity = 2,517.5) | 0.0 | 7,055.4 |
| 6 | Incremental (non-scheduled) financing -- always $0 (non-plug policy) | 0.0 | 7,055.4 |
| 7 | Discretionary investment / repurchases (fixed payout-ratio assumption) | -1,193.9 | 5,861.6 |
| 7b | Management-selected deployment (beyond the routine repurchase program; always $0 this round -- no deployment has been selected) | -0.0 | 5,861.6 |
| 8 | Ending cash | 0.0 | 5,861.6 |

**FY2030** (beginning cash 5,861.6)

| Step | Label | Amount | Balance After |
|---|---|---|---|
| 1 | Operating cash generation (CFO) | 10,263.6 | 16,125.2 |
| 2 | Capital expenditures (CFI = -CapEx) | -5,223.2 | 10,902.0 |
| 3 | Dividends | -2,316.0 | 8,586.0 |
| 4 | Minimum cash preservation (checkpoint, no cash movement) (cash above minimum buffer at this checkpoint: 4,941.9) | 0.0 | 8,586.0 |
| 5 | Scheduled debt reserve / repayment (fixed schedule) | -700.0 | 7,886.0 |
| 5b | DEPLOYABLE CAPACITY CHECKPOINT (pre_discretionary_ending_cash - buffer - reserve, before any repurchase is subtracted) (deployable_capacity = 3,241.9) | 0.0 | 7,886.0 |
| 6 | Incremental (non-scheduled) financing -- always $0 (non-plug policy) | 0.0 | 7,886.0 |
| 7 | Discretionary investment / repurchases (fixed payout-ratio assumption) | -1,498.4 | 6,387.6 |
| 7b | Management-selected deployment (beyond the routine repurchase program; always $0 this round -- no deployment has been selected) | -0.0 | 6,387.6 |
| 8 | Ending cash | 0.0 | 6,387.6 |

### 4.3 Scenario: DOWNSIDE

**FY2026** (beginning cash 5,488.0)

| Step | Label | Amount | Balance After |
|---|---|---|---|
| 1 | Operating cash generation (CFO) | 4,739.5 | 10,227.5 |
| 2 | Capital expenditures (CFI = -CapEx) | -2,860.5 | 7,367.0 |
| 3 | Dividends | -2,053.0 | 5,314.0 |
| 4 | Minimum cash preservation (checkpoint, no cash movement) (cash above minimum buffer at this checkpoint: 2,249.2) | 0.0 | 5,314.0 |
| 5 | Scheduled debt reserve / repayment (fixed schedule) | 200.0 | 5,514.0 |
| 5b | DEPLOYABLE CAPACITY CHECKPOINT (pre_discretionary_ending_cash - buffer - reserve, before any repurchase is subtracted) (deployable_capacity = 2,149.2) | 0.0 | 5,514.0 |
| 6 | Incremental (non-scheduled) financing -- always $0 (non-plug policy) | 0.0 | 5,514.0 |
| 7 | Discretionary investment / repurchases (fixed payout-ratio assumption) | -0.0 | 5,514.0 |
| 7b | Management-selected deployment (beyond the routine repurchase program; always $0 this round -- no deployment has been selected) | -0.0 | 5,514.0 |
| 8 | Ending cash | 0.0 | 5,514.0 |

**FY2027** (beginning cash 5,514.0)

| Step | Label | Amount | Balance After |
|---|---|---|---|
| 1 | Operating cash generation (CFO) | 6,254.4 | 11,768.4 |
| 2 | Capital expenditures (CFI = -CapEx) | -2,789.0 | 8,979.4 |
| 3 | Dividends | -2,053.0 | 6,926.4 |
| 4 | Minimum cash preservation (checkpoint, no cash movement) (cash above minimum buffer at this checkpoint: 3,938.2) | 0.0 | 6,926.4 |
| 5 | Scheduled debt reserve / repayment (fixed schedule) | 200.0 | 7,126.4 |
| 5b | DEPLOYABLE CAPACITY CHECKPOINT (pre_discretionary_ending_cash - buffer - reserve, before any repurchase is subtracted) (deployable_capacity = 3,838.2) | 0.0 | 7,126.4 |
| 6 | Incremental (non-scheduled) financing -- always $0 (non-plug policy) | 0.0 | 7,126.4 |
| 7 | Discretionary investment / repurchases (fixed payout-ratio assumption) | -0.0 | 7,126.4 |
| 7b | Management-selected deployment (beyond the routine repurchase program; always $0 this round -- no deployment has been selected) | -0.0 | 7,126.4 |
| 8 | Ending cash | 0.0 | 7,126.4 |

**FY2028** (beginning cash 7,126.4)

| Step | Label | Amount | Balance After |
|---|---|---|---|
| 1 | Operating cash generation (CFO) | 5,703.5 | 12,829.9 |
| 2 | Capital expenditures (CFI = -CapEx) | -2,719.3 | 10,110.6 |
| 3 | Dividends | -2,053.0 | 8,057.6 |
| 4 | Minimum cash preservation (checkpoint, no cash movement) (cash above minimum buffer at this checkpoint: 5,144.2) | 0.0 | 8,057.6 |
| 5 | Scheduled debt reserve / repayment (fixed schedule) | 200.0 | 8,257.6 |
| 5b | DEPLOYABLE CAPACITY CHECKPOINT (pre_discretionary_ending_cash - buffer - reserve, before any repurchase is subtracted) (deployable_capacity = 5,044.2) | 0.0 | 8,257.6 |
| 6 | Incremental (non-scheduled) financing -- always $0 (non-plug policy) | 0.0 | 8,257.6 |
| 7 | Discretionary investment / repurchases (fixed payout-ratio assumption) | -0.0 | 8,257.6 |
| 7b | Management-selected deployment (beyond the routine repurchase program; always $0 this round -- no deployment has been selected) | -0.0 | 8,257.6 |
| 8 | Ending cash | 0.0 | 8,257.6 |

**FY2029** (beginning cash 8,257.6)

| Step | Label | Amount | Balance After |
|---|---|---|---|
| 1 | Operating cash generation (CFO) | 5,174.2 | 13,431.8 |
| 2 | Capital expenditures (CFI = -CapEx) | -2,651.3 | 10,780.5 |
| 3 | Dividends | -2,053.0 | 8,727.5 |
| 4 | Minimum cash preservation (checkpoint, no cash movement) (cash above minimum buffer at this checkpoint: 5,886.9) | 0.0 | 8,727.5 |
| 5 | Scheduled debt reserve / repayment (fixed schedule) | 200.0 | 8,927.5 |
| 5b | DEPLOYABLE CAPACITY CHECKPOINT (pre_discretionary_ending_cash - buffer - reserve, before any repurchase is subtracted) (deployable_capacity = 5,786.9) | 0.0 | 8,927.5 |
| 6 | Incremental (non-scheduled) financing -- always $0 (non-plug policy) | 0.0 | 8,927.5 |
| 7 | Discretionary investment / repurchases (fixed payout-ratio assumption) | -0.0 | 8,927.5 |
| 7b | Management-selected deployment (beyond the routine repurchase program; always $0 this round -- no deployment has been selected) | -0.0 | 8,927.5 |
| 8 | Ending cash | 0.0 | 8,927.5 |

**FY2030** (beginning cash 8,927.5)

| Step | Label | Amount | Balance After |
|---|---|---|---|
| 1 | Operating cash generation (CFO) | 4,667.6 | 13,595.2 |
| 2 | Capital expenditures (CFI = -CapEx) | -2,585.0 | 11,010.2 |
| 3 | Dividends | -2,053.0 | 8,957.2 |
| 4 | Minimum cash preservation (checkpoint, no cash movement) (cash above minimum buffer at this checkpoint: 6,187.5) | 0.0 | 8,957.2 |
| 5 | Scheduled debt reserve / repayment (fixed schedule) | 200.0 | 9,157.2 |
| 5b | DEPLOYABLE CAPACITY CHECKPOINT (pre_discretionary_ending_cash - buffer - reserve, before any repurchase is subtracted) (deployable_capacity = 6,087.5) | 0.0 | 9,157.2 |
| 6 | Incremental (non-scheduled) financing -- always $0 (non-plug policy) | 0.0 | 9,157.2 |
| 7 | Discretionary investment / repurchases (fixed payout-ratio assumption) | -0.0 | 9,157.2 |
| 7b | Management-selected deployment (beyond the routine repurchase program; always $0 this round -- no deployment has been selected) | -0.0 | 9,157.2 |
| 8 | Ending cash | 0.0 | 9,157.2 |

### 4a. No-Double-Counting Proof (all 15 scenario-years)

Three identities, per `verify_no_double_counting()` (extended in Milestone 3A to explicitly cover management-selected deployment and debt repayment, per the reviewer's critical waterfall rule): **(a)** `ending_cash = pre_discretionary_ending_cash - share_repurchases - management_selected_deployment` (both discretionary uses are subtracted exactly once). **(b)** `pre_discretionary_ending_cash = deployable_capacity + min_cash_buffer + near_term_debt_repayment_reserve` (whenever not floored at zero). **(c)** full source/use conservation: `beginning_cash + CFO + CFI + debt_proceeds = debt_repayments + dividends + repurchases + management_selected_deployment + ending_cash` -- every dollar generated is exactly one of 5 mutually exclusive, additively-combined uses, never two at once. Reading (a)+(b) together: deployable_capacity/buffer/reserve is an allocation of `pre_discretionary_ending_cash` under a hypothetical "discretionary uses not yet executed" view; share_repurchases + management_selected_deployment + ending_cash is an allocation of the SAME total under the actual "already executed" view. They are alternative readings of one total, never additive -- a dollar inside deployable_capacity is, in the actual outcome, inside repurchases, a selected deployment, or ending_cash, never inside more than one of those at once.

| Scenario | FY | ending_cash | pre_disc_end_cash - repurch - deployment | (a) | pre_disc_end_cash | deployable+buffer+reserve | (b) | sources | uses | (c) |
|---|---|---|---|---|---|---|---|---|---|---|
| base | 2026 | 6,188.4 | 6,188.4 | YES | 6,655.3 | 6,655.3 | YES | 9,438.9 | 9,438.9 | YES |
| base | 2027 | 6,981.2 | 6,981.2 | YES | 7,509.7 | 7,509.7 | YES | 10,324.4 | 10,324.4 | YES |
| base | 2028 | 7,827.5 | 7,827.5 | YES | 8,391.8 | 8,391.8 | YES | 11,237.9 | 11,237.9 | YES |
| base | 2029 | 8,728.0 | 8,728.0 | YES | 9,328.3 | 9,328.3 | YES | 12,206.4 | 12,206.4 | YES |
| base | 2030 | 9,682.5 | 9,682.5 | YES | 10,318.8 | 10,318.8 | YES | 13,229.3 | 13,229.3 | YES |
| upside | 2026 | 5,727.8 | 5,727.8 | YES | 6,876.5 | 6,876.5 | YES | 9,979.6 | 9,979.6 | YES |
| upside | 2027 | 5,544.3 | 5,544.3 | YES | 6,175.6 | 6,175.6 | YES | 9,330.0 | 9,330.0 | YES |
| upside | 2028 | 5,584.8 | 5,584.8 | YES | 6,489.7 | 6,489.7 | YES | 9,696.7 | 9,696.7 | YES |
| upside | 2029 | 5,861.6 | 5,861.6 | YES | 7,055.4 | 7,055.4 | YES | 10,316.2 | 10,316.2 | YES |
| upside | 2030 | 6,387.6 | 6,387.6 | YES | 7,886.0 | 7,886.0 | YES | 11,202.0 | 11,202.0 | YES |
| downside | 2026 | 5,514.0 | 5,514.0 | YES | 5,514.0 | 5,514.0 | YES | 7,867.0 | 7,867.0 | YES |
| downside | 2027 | 7,126.4 | 7,126.4 | YES | 7,126.4 | 7,126.4 | YES | 9,479.4 | 9,479.4 | YES |
| downside | 2028 | 8,257.6 | 8,257.6 | YES | 8,257.6 | 8,257.6 | YES | 10,610.6 | 10,610.6 | YES |
| downside | 2029 | 8,927.5 | 8,927.5 | YES | 8,927.5 | 8,927.5 | YES | 11,280.5 | 11,280.5 | YES |
| downside | 2030 | 9,157.2 | 9,157.2 | YES | 9,157.2 | 9,157.2 | YES | 11,510.2 | 11,510.2 | YES |

### 4b. Repurchase Classification

**Fixed forecast assumption (payout ratio of post-dividend FCF). Not a use of deployable capacity, not a residual allocation, not zero-pending-selection (Downside's zero is itself a fixed assumption, not an unselected default).**

### 4c. Cumulative Deployable Capacity -- Double-Counting Fix (Milestone 3A critical rule)

**Corrected this round.** The prior round's `cumulative_deployable_capacity_2026_2030` summed each year's own `deployable_capacity` balance across all 5 forecast years. Because `deployable_capacity` is a STOCK (a year-end headroom balance whose unused dollars flow forward into every later year's cash balance via the ordinary cash roll-forward), that sum counted the same undeployed dollars up to 5 times. The corrected formula (`cumulative_deployable_capacity()`) is: terminal-year `deployable_capacity` (which already reflects the full accumulation of every prior year's unspent capacity) PLUS whatever was ACTUALLY DEPLOYED along the way (`management_selected_deployment`, summed once each, since deployed cash leaves the ending-cash balance and so is not re-counted by adding the terminal figure).

| Scenario | Corrected Cumulative Capacity | Naive (defective) Sum-of-Years | Overstatement |
|---|---|---|---|
| base | 6,315.0 | 22,509.0 | 16,194.0 |
| upside | 3,241.9 | 12,293.9 | 9,052.0 |
| downside | 6,087.5 | 22,905.9 | 16,818.4 |

Since no deployment has been selected this round (`management_selected_deployment` is 0 in every year), the corrected figure reduces to exactly the terminal-year (FY2030) `deployable_capacity` shown in Section 2's Capital Position tables and Section 9's sensitivity tables below.

## 5. Minimum-Cash-Buffer Policy Comparison

**No policy is endorsed as final in this round.** 5 policies compared side by side, computed as a pure post-hoc overlay: none of them feed back into CFO/FCF/ending_cash (share repurchases are sized from FCF/dividends alone -- see Section 4b -- never from the buffer), so `ending_cash` is IDENTICAL across all 5 policies for a given scenario/year; only `required_minimum_cash` and the resulting `deployable_capacity` change.

### 5.1 Scenario: BASE

**Fixed-dollar historical minimum** (lowest coverage ratio over FY2026-FY2030: 2.78x)

- Rationale: Hold the lowest historical year-end cash balance ($2,229M, FY2022) flat in dollar terms for every forecast year.
- Strength: Simple; directly evidenced by an actual historical low, not a modeled estimate.
- Limitation: Does not scale with revenue growth or decline -- shrinks as a % of the business over time in BASE/UPSIDE, and does not tighten further if DOWNSIDE's revenue contracts well below FY2022's level.

| FY | Required Minimum Cash | Deployable Capacity | Ending Cash | Coverage Ratio |
|---|---|---|---|---|
| 2026 | 2,229.0 | 3,726.3 | 6,188.4 | 2.78x |
| 2027 | 2,229.0 | 4,580.7 | 6,981.2 | 3.13x |
| 2028 | 2,229.0 | 5,462.8 | 7,827.5 | 3.51x |
| 2029 | 2,229.0 | 6,399.3 | 8,728.0 | 3.92x |
| 2030 | 2,229.0 | 7,389.8 | 9,682.5 | 4.34x |

**Percentage of revenue (3.0%)** (lowest coverage ratio over FY2026-FY2030: 1.95x)

- Rationale: 3% of forecast revenue -- the figure already wired into this round's base assumption set, used here as one candidate among five, not as a conclusion.
- Strength: Scales automatically with the business; sits between the historical minimum ratio (2.04%, FY2022) and recent actuals (4.47%-5.24%, FY2024-FY2025).
- Limitation: The 3.0% figure is a judgment call within that range, not derived from a formal statistical rule -- a different reviewer could reasonably pick a different point in the same range.

| FY | Required Minimum Cash | Deployable Capacity | Ending Cash | Coverage Ratio |
|---|---|---|---|---|
| 2026 | 3,174.8 | 2,780.5 | 6,188.4 | 1.95x |
| 2027 | 3,206.6 | 3,603.1 | 6,981.2 | 2.18x |
| 2028 | 3,238.6 | 4,453.1 | 7,827.5 | 2.42x |
| 2029 | 3,271.0 | 5,357.3 | 8,728.0 | 2.67x |
| 2030 | 3,303.7 | 6,315.0 | 9,682.5 | 2.93x |

**Operating-cost coverage (2.5% of COGS + SG&A)** (lowest coverage ratio over FY2026-FY2030: 2.53x)

- Rationale: 2.5% of forecast (COGS + SG&A) -- roughly 9 days of operating-cost coverage, ties the buffer to the cost base being funded rather than to top-line revenue.
- Strength: Conceptually distinct grounding (cost coverage, not revenue scale) from the %-of-revenue policy, useful as an independent cross-check.
- Limitation: Produces a dollar figure very close to the %-of-revenue policy at Target's cost structure (COGS+SG&A is roughly 97%-98% of revenue every historical year), so it adds a second formula without a materially different result in practice.

| FY | Required Minimum Cash | Deployable Capacity | Ending Cash | Coverage Ratio |
|---|---|---|---|---|
| 2026 | 2,450.4 | 3,504.9 | 6,188.4 | 2.53x |
| 2027 | 2,474.5 | 4,335.2 | 6,981.2 | 2.82x |
| 2028 | 2,498.8 | 5,193.0 | 7,827.5 | 3.13x |
| 2029 | 2,523.2 | 6,105.1 | 8,728.0 | 3.46x |
| 2030 | 2,548.0 | 7,070.8 | 9,682.5 | 3.80x |

**Historical cash-ratio 25th percentile (3.54% of revenue)** (lowest coverage ratio over FY2026-FY2030: 1.65x)

- Rationale: 25th percentile of the 5 historical cash/revenue ratios (2.04%, 3.54%, 4.47%, 5.24%, 5.58%) = 3.54%, linear-interpolated.
- Strength: Statistically grounded in the full historical distribution rather than a single hand-picked min/max/round number.
- Limitation: Only 5 historical observations exist -- a percentile computed on 5 points is not a robust distributional estimate and is sensitive to which single year is excluded or included.

| FY | Required Minimum Cash | Deployable Capacity | Ending Cash | Coverage Ratio |
|---|---|---|---|---|
| 2026 | 3,748.9 | 2,206.4 | 6,188.4 | 1.65x |
| 2027 | 3,786.4 | 3,023.4 | 6,981.2 | 1.84x |
| 2028 | 3,824.2 | 3,867.5 | 7,827.5 | 2.05x |
| 2029 | 3,862.5 | 4,765.8 | 8,728.0 | 2.26x |
| 2030 | 3,901.1 | 5,717.7 | 9,682.5 | 2.48x |

**Hybrid: max(fixed-dollar, 3%-of-revenue)** (lowest coverage ratio over FY2026-FY2030: 1.95x)

- Rationale: max($2,229M, 3% of forecast revenue) -- the more conservative (larger) of the two measures always governs.
- Strength: Combines a hard historical floor with a scaling component; never falls below the fixed floor even if a downside scenario's revenue shrinks well below FY2022's level.
- Limitation: A two-part policy is harder to communicate and audit than a single formula, and inherits both component policies' individual limitations in the range where either could bind.

| FY | Required Minimum Cash | Deployable Capacity | Ending Cash | Coverage Ratio |
|---|---|---|---|---|
| 2026 | 3,174.8 | 2,780.5 | 6,188.4 | 1.95x |
| 2027 | 3,206.6 | 3,603.1 | 6,981.2 | 2.18x |
| 2028 | 3,238.6 | 4,453.1 | 7,827.5 | 2.42x |
| 2029 | 3,271.0 | 5,357.3 | 8,728.0 | 2.67x |
| 2030 | 3,303.7 | 6,315.0 | 9,682.5 | 2.93x |

### 5.2 Scenario: UPSIDE

**Fixed-dollar historical minimum** (lowest coverage ratio over FY2026-FY2030: 2.49x)

- Rationale: Hold the lowest historical year-end cash balance ($2,229M, FY2022) flat in dollar terms for every forecast year.
- Strength: Simple; directly evidenced by an actual historical low, not a modeled estimate.
- Limitation: Does not scale with revenue growth or decline -- shrinks as a % of the business over time in BASE/UPSIDE, and does not tighten further if DOWNSIDE's revenue contracts well below FY2022's level.

| FY | Required Minimum Cash | Deployable Capacity | Ending Cash | Coverage Ratio |
|---|---|---|---|---|
| 2026 | 2,229.0 | 3,647.5 | 5,727.8 | 2.57x |
| 2027 | 2,229.0 | 2,946.6 | 5,544.3 | 2.49x |
| 2028 | 2,229.0 | 3,260.7 | 5,584.8 | 2.51x |
| 2029 | 2,229.0 | 3,826.4 | 5,861.6 | 2.63x |
| 2030 | 2,229.0 | 4,657.0 | 6,387.6 | 2.87x |

**Percentage of revenue (3.0%)** (lowest coverage ratio over FY2026-FY2030: 1.63x)

- Rationale: 3% of forecast revenue -- the figure already wired into this round's base assumption set, used here as one candidate among five, not as a conclusion.
- Strength: Scales automatically with the business; sits between the historical minimum ratio (2.04%, FY2022) and recent actuals (4.47%-5.24%, FY2024-FY2025).
- Limitation: The 3.0% figure is a judgment call within that range, not derived from a formal statistical rule -- a different reviewer could reasonably pick a different point in the same range.

| FY | Required Minimum Cash | Deployable Capacity | Ending Cash | Coverage Ratio |
|---|---|---|---|---|
| 2026 | 3,237.7 | 2,638.8 | 5,727.8 | 1.77x |
| 2027 | 3,334.8 | 1,840.8 | 5,544.3 | 1.66x |
| 2028 | 3,434.9 | 2,054.9 | 5,584.8 | 1.63x |
| 2029 | 3,537.9 | 2,517.5 | 5,861.6 | 1.66x |
| 2030 | 3,644.1 | 3,241.9 | 6,387.6 | 1.75x |

**Operating-cost coverage (2.5% of COGS + SG&A)** (lowest coverage ratio over FY2026-FY2030: 2.13x)

- Rationale: 2.5% of forecast (COGS + SG&A) -- roughly 9 days of operating-cost coverage, ties the buffer to the cost base being funded rather than to top-line revenue.
- Strength: Conceptually distinct grounding (cost coverage, not revenue scale) from the %-of-revenue policy, useful as an independent cross-check.
- Limitation: Produces a dollar figure very close to the %-of-revenue policy at Target's cost structure (COGS+SG&A is roughly 97%-98% of revenue every historical year), so it adds a second formula without a materially different result in practice.

| FY | Required Minimum Cash | Deployable Capacity | Ending Cash | Coverage Ratio |
|---|---|---|---|---|
| 2026 | 2,499.0 | 3,377.6 | 5,727.8 | 2.29x |
| 2027 | 2,562.7 | 2,613.0 | 5,544.3 | 2.16x |
| 2028 | 2,628.0 | 2,861.8 | 5,584.8 | 2.13x |
| 2029 | 2,694.9 | 3,360.5 | 5,861.6 | 2.18x |
| 2030 | 2,763.4 | 4,122.6 | 6,387.6 | 2.31x |

**Historical cash-ratio 25th percentile (3.54% of revenue)** (lowest coverage ratio over FY2026-FY2030: 1.38x)

- Rationale: 25th percentile of the 5 historical cash/revenue ratios (2.04%, 3.54%, 4.47%, 5.24%, 5.58%) = 3.54%, linear-interpolated.
- Strength: Statistically grounded in the full historical distribution rather than a single hand-picked min/max/round number.
- Limitation: Only 5 historical observations exist -- a percentile computed on 5 points is not a robust distributional estimate and is sensitive to which single year is excluded or included.

| FY | Required Minimum Cash | Deployable Capacity | Ending Cash | Coverage Ratio |
|---|---|---|---|---|
| 2026 | 3,823.1 | 2,053.4 | 5,727.8 | 1.50x |
| 2027 | 3,937.8 | 1,237.8 | 5,544.3 | 1.41x |
| 2028 | 4,055.9 | 1,433.8 | 5,584.8 | 1.38x |
| 2029 | 4,177.6 | 1,877.8 | 5,861.6 | 1.40x |
| 2030 | 4,303.0 | 2,583.1 | 6,387.6 | 1.48x |

**Hybrid: max(fixed-dollar, 3%-of-revenue)** (lowest coverage ratio over FY2026-FY2030: 1.63x)

- Rationale: max($2,229M, 3% of forecast revenue) -- the more conservative (larger) of the two measures always governs.
- Strength: Combines a hard historical floor with a scaling component; never falls below the fixed floor even if a downside scenario's revenue shrinks well below FY2022's level.
- Limitation: A two-part policy is harder to communicate and audit than a single formula, and inherits both component policies' individual limitations in the range where either could bind.

| FY | Required Minimum Cash | Deployable Capacity | Ending Cash | Coverage Ratio |
|---|---|---|---|---|
| 2026 | 3,237.7 | 2,638.8 | 5,727.8 | 1.77x |
| 2027 | 3,334.8 | 1,840.8 | 5,544.3 | 1.66x |
| 2028 | 3,434.9 | 2,054.9 | 5,584.8 | 1.63x |
| 2029 | 3,537.9 | 2,517.5 | 5,861.6 | 1.66x |
| 2030 | 3,644.1 | 3,241.9 | 6,387.6 | 1.75x |

### 5.3 Scenario: DOWNSIDE

**Fixed-dollar historical minimum** (lowest coverage ratio over FY2026-FY2030: 2.47x)

- Rationale: Hold the lowest historical year-end cash balance ($2,229M, FY2022) flat in dollar terms for every forecast year.
- Strength: Simple; directly evidenced by an actual historical low, not a modeled estimate.
- Limitation: Does not scale with revenue growth or decline -- shrinks as a % of the business over time in BASE/UPSIDE, and does not tighten further if DOWNSIDE's revenue contracts well below FY2022's level.

| FY | Required Minimum Cash | Deployable Capacity | Ending Cash | Coverage Ratio |
|---|---|---|---|---|
| 2026 | 2,229.0 | 2,985.0 | 5,514.0 | 2.47x |
| 2027 | 2,229.0 | 4,597.4 | 7,126.4 | 3.20x |
| 2028 | 2,229.0 | 5,728.6 | 8,257.6 | 3.70x |
| 2029 | 2,229.0 | 6,398.5 | 8,927.5 | 4.01x |
| 2030 | 2,229.0 | 6,628.2 | 9,157.2 | 4.11x |

**Percentage of revenue (3.0%)** (lowest coverage ratio over FY2026-FY2030: 1.80x)

- Rationale: 3% of forecast revenue -- the figure already wired into this round's base assumption set, used here as one candidate among five, not as a conclusion.
- Strength: Scales automatically with the business; sits between the historical minimum ratio (2.04%, FY2022) and recent actuals (4.47%-5.24%, FY2024-FY2025).
- Limitation: The 3.0% figure is a judgment call within that range, not derived from a formal statistical rule -- a different reviewer could reasonably pick a different point in the same range.

| FY | Required Minimum Cash | Deployable Capacity | Ending Cash | Coverage Ratio |
|---|---|---|---|---|
| 2026 | 3,064.8 | 2,149.2 | 5,514.0 | 1.80x |
| 2027 | 2,988.2 | 3,838.2 | 7,126.4 | 2.38x |
| 2028 | 2,913.5 | 5,044.2 | 8,257.6 | 2.83x |
| 2029 | 2,840.7 | 5,786.9 | 8,927.5 | 3.14x |
| 2030 | 2,769.6 | 6,087.5 | 9,157.2 | 3.31x |

**Operating-cost coverage (2.5% of COGS + SG&A)** (lowest coverage ratio over FY2026-FY2030: 2.33x)

- Rationale: 2.5% of forecast (COGS + SG&A) -- roughly 9 days of operating-cost coverage, ties the buffer to the cost base being funded rather than to top-line revenue.
- Strength: Conceptually distinct grounding (cost coverage, not revenue scale) from the %-of-revenue policy, useful as an independent cross-check.
- Limitation: Produces a dollar figure very close to the %-of-revenue policy at Target's cost structure (COGS+SG&A is roughly 97%-98% of revenue every historical year), so it adds a second formula without a materially different result in practice.

| FY | Required Minimum Cash | Deployable Capacity | Ending Cash | Coverage Ratio |
|---|---|---|---|---|
| 2026 | 2,365.5 | 2,848.4 | 5,514.0 | 2.33x |
| 2027 | 2,321.2 | 4,505.2 | 7,126.4 | 3.07x |
| 2028 | 2,277.6 | 5,680.0 | 8,257.6 | 3.63x |
| 2029 | 2,234.8 | 6,392.7 | 8,927.5 | 3.99x |
| 2030 | 2,192.6 | 6,664.5 | 9,157.2 | 4.18x |

**Historical cash-ratio 25th percentile (3.54% of revenue)** (lowest coverage ratio over FY2026-FY2030: 1.52x)

- Rationale: 25th percentile of the 5 historical cash/revenue ratios (2.04%, 3.54%, 4.47%, 5.24%, 5.58%) = 3.54%, linear-interpolated.
- Strength: Statistically grounded in the full historical distribution rather than a single hand-picked min/max/round number.
- Limitation: Only 5 historical observations exist -- a percentile computed on 5 points is not a robust distributional estimate and is sensitive to which single year is excluded or included.

| FY | Required Minimum Cash | Deployable Capacity | Ending Cash | Coverage Ratio |
|---|---|---|---|---|
| 2026 | 3,619.0 | 1,595.0 | 5,514.0 | 1.52x |
| 2027 | 3,528.5 | 3,297.9 | 7,126.4 | 2.02x |
| 2028 | 3,440.3 | 4,517.4 | 8,257.6 | 2.40x |
| 2029 | 3,354.3 | 5,273.2 | 8,927.5 | 2.66x |
| 2030 | 3,270.4 | 5,586.7 | 9,157.2 | 2.80x |

**Hybrid: max(fixed-dollar, 3%-of-revenue)** (lowest coverage ratio over FY2026-FY2030: 1.80x)

- Rationale: max($2,229M, 3% of forecast revenue) -- the more conservative (larger) of the two measures always governs.
- Strength: Combines a hard historical floor with a scaling component; never falls below the fixed floor even if a downside scenario's revenue shrinks well below FY2022's level.
- Limitation: A two-part policy is harder to communicate and audit than a single formula, and inherits both component policies' individual limitations in the range where either could bind.

| FY | Required Minimum Cash | Deployable Capacity | Ending Cash | Coverage Ratio |
|---|---|---|---|---|
| 2026 | 3,064.8 | 2,149.2 | 5,514.0 | 1.80x |
| 2027 | 2,988.2 | 3,838.2 | 7,126.4 | 2.38x |
| 2028 | 2,913.5 | 5,044.2 | 8,257.6 | 2.83x |
| 2029 | 2,840.7 | 5,786.9 | 8,927.5 | 3.14x |
| 2030 | 2,769.6 | 6,087.5 | 9,157.2 | 3.31x |

### 5a. Why 3% of Revenue Is Not Unsafe Despite Recent Actuals Being Higher

FY2024-FY2025 ending cash was 4.47%-5.24% of revenue -- materially above the 3.0% candidate floor. This is not a contradiction, because **the policy is a floor, not a target**: nothing in the forecast engine forces ending cash down toward the buffer. The forecast's own actual ending-cash outcome (Section 2's Capital Position tables) stays well above 3.0% of revenue in every scenario and year -- BASE FY2026 ending cash is 5.85% of revenue, for example, not 3.0%. The buffer exists to answer 'how low could cash go before a policy violation is flagged', not 'what cash level should the company target'. FY2022's actual ratio (2.04%) -- BELOW the proposed 3.0% floor -- is itself evidence Target has historically operated with less cash than this floor would allow without disclosing distress, which argues the floor is conservative (i.e. safely above a level Target itself has sustained), not unsafely low. The real test of safety is the seasonality stress overlay in Section 6, which asks whether an *intra-year* trough -- not just the annual point estimate -- could breach this floor; it shows exactly one such breach (DOWNSIDE FY2026), disclosed there, not hidden here.

## 6. Seasonality Limitation and Stress Overlay

**Not a quarterly forecasting engine** -- explicitly out of scope this round, and no quarterly value for FY2026-FY2030 is fabricated anywhere in this module.

**Evidence and method**: FY2025 real quarterly cash (as_originally_filed, instant_facts): Q1 2025-05-03=$2,887M (trough), Q2 2025-08-02=$4,341M, Q3 2025-11-01=$3,822M, Q4/year-end 2026-01-31=$5,488M. Trough/year-end=52.6%, i.e. a 47.4% observed intra-year decline from the fiscal year-end level, rounded up to a 50% haircut for conservatism. Only one year of quarterly evidence exists in the registered source set -- this is a single-year sample, not a multi-year seasonal pattern.

### 6.1 Scenario: BASE

| FY | Annual Ending Cash | Seasonal Haircut % | Stressed Cash Position | Required Buffer | Stressed Deployable Capacity | Stressed Funding Warning |
|---|---|---|---|---|---|---|
| 2026 | 6,188.4 | 50.0% | 3,327.6 | 3,174.8 | 0.0 | no |
| 2027 | 6,981.2 | 50.0% | 3,754.9 | 3,206.6 | 0.0 | no |
| 2028 | 7,827.5 | 50.0% | 4,195.9 | 3,238.6 | 257.2 | no |
| 2029 | 8,728.0 | 50.0% | 4,664.2 | 3,271.0 | 693.1 | no |
| 2030 | 9,682.5 | 50.0% | 5,159.4 | 3,303.7 | 1,155.6 | no |

### 6.2 Scenario: UPSIDE

| FY | Annual Ending Cash | Seasonal Haircut % | Stressed Cash Position | Required Buffer | Stressed Deployable Capacity | Stressed Funding Warning |
|---|---|---|---|---|---|---|
| 2026 | 5,727.8 | 50.0% | 3,438.3 | 3,237.7 | 0.0 | no |
| 2027 | 5,544.3 | 50.0% | 3,087.8 | 3,334.8 | 0.0 | YES |
| 2028 | 5,584.8 | 50.0% | 3,244.9 | 3,434.9 | 0.0 | YES |
| 2029 | 5,861.6 | 50.0% | 3,527.7 | 3,537.9 | 0.0 | YES |
| 2030 | 6,387.6 | 50.0% | 3,943.0 | 3,644.1 | 0.0 | no |

### 6.3 Scenario: DOWNSIDE

| FY | Annual Ending Cash | Seasonal Haircut % | Stressed Cash Position | Required Buffer | Stressed Deployable Capacity | Stressed Funding Warning |
|---|---|---|---|---|---|---|
| 2026 | 5,514.0 | 50.0% | 2,757.0 | 3,064.8 | 0.0 | YES |
| 2027 | 7,126.4 | 50.0% | 3,563.2 | 2,988.2 | 275.0 | no |
| 2028 | 8,257.6 | 50.0% | 4,128.8 | 2,913.5 | 915.3 | no |
| 2029 | 8,927.5 | 50.0% | 4,463.8 | 2,840.7 | 1,323.1 | no |
| 2030 | 9,157.2 | 50.0% | 4,578.6 | 2,769.6 | 1,508.9 | no |

**Limitations**: (1) only ONE year of quarterly evidence exists in the registered source set (FY2025) -- this is a single-year sample, not a multi-year seasonal pattern, and the true worst-case intra-year trough could differ from what FY2025 alone shows. (2) The haircut is applied uniformly to `pre_discretionary_ending_cash`, not to a real quarterly cash-flow trajectory -- it approximates "how much lower could the point-in-time low have been" rather than modeling the actual timing of Target's seasonal buildup and drawdown (inventory build ahead of the holiday season, cash collection afterward). (3) The 50% figure is a deliberately conservative rounding of the one observed ratio (47.4%), not a statistically fitted value.

## 7. Scenario Logic

**Scenario narratives (Milestone 3A)** -- each scenario is a coherent business condition, not a mechanical increase or decrease applied to every input independently. Full text, live from `SCENARIO_NARRATIVES`:

### 7.1 BASE Narrative

BASE is a continuation-of-current-trajectory story, not a blend of the other two. Target has stabilized after the FY2022 margin shock and the FY2023 53-week-distorted year: traffic and comparable sales are flattish-to-slightly-positive, promotional intensity and mix pressure have stopped worsening but have not meaningfully reversed, and cost discipline is holding SG&A leverage flat rather than improving it. Consistent with that single story: revenue growth is modest (+1.0%/yr, matching the cleanest recent 52-week-normalized read); gross margin holds near its FY2023-FY2025 average (27.93% drifting only to 28.00% by FY2030) rather than reverting to FY2021's pandemic-inflated peak; SG&A stays flat at the FY2025 ratio because there is no assumed acceleration in either sales leverage or cost cutting; CapEx continues at the recent maintenance-plus-modest-growth level (3.6% of revenue, in line with the FY2025 actual and 5-year median); and capital return continues at a moderate, sustainable pace (40% of post-dividend FCF to buybacks, dividend growth decelerating to +2.0%/yr matching the recent FY2024-FY2025 pace) because neither an acceleration nor a retrenchment in the business justifies a change in payout policy. Debt is rolled at a flat, refinancing-style schedule ($700M proceeds against $700M repayments every year) because nothing in this story implies either deleveraging urgency or a new borrowing need.

### 7.2 UPSIDE Narrative

UPSIDE is a successful-execution story: Target's own disclosed strategic initiatives (supply-chain and technology investment, assortment/mix improvement, digital fulfillment growth) work better than the base case assumes, translating into both stronger traffic/comps AND better cost absorption -- but bounded by what Target has ACTUALLY achieved historically, never an unprecedented performance level. Every assumption traces to that one story: revenue growth rises to +3.0%/yr (at, not beyond, the FY2022 historical maximum); gross margin recovers toward, but never exceeds, the FY2021 historical peak (28.80% by FY2030, vs. the FY2021 high of 29.28%) because better mix and supply-chain efficiency are exactly the kind of execution that produced that peak before; SG&A leverage improves (toward, not below, the FY2021 low of 18.63%) because stronger sales absorb fixed costs better. The one deliberately NON-monotonic driver is CapEx: UPSIDE spends MORE on capital (4.3% of revenue, above BASE's 3.6%), not less -- because funding the stronger growth (new stores, supply chain, digital investment) is what makes the stronger growth possible, and higher investment is the correct signature of a genuine growth acceleration, not a cost to be minimized. Stronger FCF supports both faster deleveraging (net debt repayment of $700M/yr rather than a flat roll) and a higher buyback payout ratio (55% of post-dividend FCF) and faster dividend growth (+4.0%/yr) -- all consequences of the SAME improved cash generation, not independently chosen 'better' numbers.

### 7.3 DOWNSIDE Narrative

DOWNSIDE is a sustained discretionary-spending-pressure story -- a continued deterioration of the conditions already visible in FY2023-FY2025, not a fabricated crisis or an extreme, unprecedented event. Consumers pull back further on discretionary categories, promotional intensity increases to defend traffic, and the business responds with capital discipline and balance-sheet caution rather than an operational collapse. Every assumption is a consequence of that one story: revenue declines further (-2.5%/yr, roughly 1.5x the worst single historical year, reflecting sustained rather than one-year pressure); gross margin compresses (toward, not to, the FY2022 trough of 24.57%) from continued promotional activity; SG&A deleverages (revenue falls faster than largely-fixed operating costs) rather than being cut in step; inventory BUILDS as a % of revenue (12.8% vs. BASE's 11.8%) because slower sell-through is a direct, coherent consequence of weaker demand, not an independent assumption; accounts payable tightens (suppliers extend less credit at 15.5% of COGS, near the historical minimum) for the same reason -- both are the SAME working-capital-consumption story, not two unrelated pessimistic picks. Management responds exactly as a distressed-but-not-crisis retailer would: CapEx is cut to a capital-discipline level (2.8% of revenue, near the historical minimum, but never below it, since Target discloses no all-out CapEx freeze); buybacks stop entirely (0% payout -- capital preservation); dividends are frozen, not cut, because Target's dividend has grown in every one of the 5 historical years with no observed reduction, so an outright cut is not modeled as plausible even under sustained pressure; and a small, FIXED, pre-committed net debt issuance ($200M) is assumed as a liquidity backstop -- explicitly NOT sized to whatever cash shortfall results, so a genuine liquidity gap surfaces as an explicit funding warning (see the seasonal stress overlay's FY2026 finding) rather than being silently plugged away by an ever-larger, unexplained debt draw.

**Where Downside <= Base <= Upside is economically appropriate** (validation check 14, `scenario_ordering`): revenue growth, gross margin, net income, and diluted EPS should rise from Downside to Upside (better execution/demand improves all four together); SG&A % of revenue and the effective tax rate should FALL from Downside to Upside (lower cost ratios and a more favorable tax rate are both 'better'). Live result:

| FY | Status | Detail |
|---|---|---|
| 2026 | PASS | upside >= base >= downside holds for all economically-unambiguous drivers |
| 2027 | PASS | upside >= base >= downside holds for all economically-unambiguous drivers |
| 2028 | PASS | upside >= base >= downside holds for all economically-unambiguous drivers |
| 2029 | PASS | upside >= base >= downside holds for all economically-unambiguous drivers |
| 2030 | PASS | upside >= base >= downside holds for all economically-unambiguous drivers |

**Where simple ordering does NOT apply, and why** (deliberately excluded from the check above):

| Metric | FY2026 Base | FY2026 Upside | FY2026 Downside | Why naive ordering fails |
|---|---|---|---|---|
| CapEx | 3,809.8 | 4,640.7 | 2,860.5 | Upside CapEx is HIGHER than Base, not lower -- it funds the stronger growth scenario; more investment is the correct direction for a stronger-execution case, the opposite of a 'cost' that should shrink toward Upside. |
| Debt proceeds | 700.0 | 300.0 | 500.0 | Debt issuance is a financing POLICY choice (deleverage in Upside, small pre-set issuance in Downside for liquidity), not a performance outcome -- there is no economically 'better' direction to enforce across scenarios. |
| Debt repayments | 700.0 | 1,000.0 | 300.0 | Same reasoning as debt proceeds -- Upside repays MORE (funded by stronger FCF), which is 'better' capital discipline, not a smaller number in a naive sense. |
| Inventory balance | 12,487.7 | 11,871.6 | 13,076.5 | Downside inventory is HIGHER (a build/working-capital consumption signal of demand weakness), Upside is LOWER (efficient turns) -- inventory dollars move opposite to 'performance' direction, unlike net income or EPS. |
| Share repurchases | 466.9 | 1,148.7 | 0.0 | A downstream USE of stronger FCF, not an independent performance metric -- it is expected to rise with scenario strength, but is not tested directly because it is a policy application of already-tested drivers (payout ratio), not a driver itself. |

## 8. Validation Inventory

21 named checks (the original 18, plus `other_operating_cf_not_a_plug` and `capital_allocation_waterfall_reconciliation` from the prior audit-package round, plus `cumulative_capacity_no_double_counting` added this round for Milestone 3A's critical cumulative-capacity rule), executed live. Total results: 229. Failures: 0. Warnings: 0.

**Honest self-classification** (per the reviewer's instruction not to present a passed arithmetic invariant as if it were independent evidence): of the 21 checks, 12 are **arithmetic invariants** (re-verify the SAME formula the engine used -- valuable for catching corruption/typos/manual overrides, but do not independently prove the underlying economics are sound), 1 is a genuinely **independent reasonableness test** (`capital_allocation_waterfall_reconciliation` -- computed via a differently-sequenced code path, not a restatement of the same formula), 7 are **structural/completeness/policy checks** (no numeric formula to independently re-derive -- they check presence, shape, or a modeling-discipline property instead), and 1 is a **scenario-comparative check** (`scenario_ordering` -- compares across scenarios, not within one scenario's own formula).

| Check ID | Category | Type | Formula | # Results | PASS | FAIL | WARN | Tolerance | Gate Consequence | Corruption Test | Example Failure Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
| assumption_completeness | Assumption Set | structural_completeness_check | For every required metric and FY2026-FY2030, an assumption row exists at that exact year OR a flat (forecast_year=0) row exists. | 3 | 3 | 0 | 0 | Exact presence/absence, no numeric tolerance | Forecast rejected -- a missing assumption means _lookup() would silently return None and crash downstream, or (worse) be masked by a stale default. | Not corrupted directly this round (would require deleting assumption rows); covered structurally by test_build_assumptions_every_scenario_year_covered. | missing: ['capex_pct_of_revenue@2028'] |
| capital_allocation_waterfall_reconciliation | Cash Flow -- Capital Allocation | independent_reasonableness_test | An 8-step running-balance waterfall (capital_allocation_waterfall) must reach the exact same ending_cash as _run_from_metrics' own block-formula computation, AND both no-double-counting identities in verify_no_double_counting must hold. | 15 | 15 | 0 | 0 | 0.1% relative (_close, tol=1e-3) | Forecast rejected -- this is the one check in the whole suite computed via a genuinely different code path than the engine itself, so a failure here would indicate the engine's own arithmetic (not just a corrupted downstream value) is wrong. | Not corrupted directly this round (it would require deliberately breaking the waterfall function itself, a different exercise than corrupting a ForecastYear value); demonstrated passing against all 15 scenario-years in Section 4. | waterfall ending_cash=6100.0 vs engine ending_cash=6188.4 |
| cash_roll_forward | Cash Flow | arithmetic_invariant | beginning_cash_t = ending_cash_(t-1); ending_cash_t = beginning_cash_t + net_change_in_cash_t; net_change_in_cash_t = CFO_t + CFI_t + CFF_t | 15 | 15 | 0 | 0 | 0.1% relative (_close, tol=1e-3) | Forecast rejected -- the cash balance no longer chains correctly across years. | test_cash_roll_forward_chains_across_years | beginning_cash=6000.0 vs prior ending_cash=6188.4 |
| cfo_construction | Cash Flow | arithmetic_invariant | operating_cash_flow_t = net_income_t + da_cfo_addback_t + inventory_cash_impact_t + ap_cash_impact_t + other_operating_cf_t | 15 | 15 | 0 | 0 | 0.1% relative (_close, tol=1e-3) | Forecast rejected -- CFO is not a bare residual and must reconcile to its stated components exactly. | test_validate_all_catches_a_broken_cfo_construction (adds $1,000M to one year in place) | CFO=8060.7 vs NI+D&A+WC+other=7060.7 |
| cumulative_capacity_no_double_counting | Cash Flow -- Capital Allocation | arithmetic_invariant | cumulative_deployable_capacity(years) = terminal_year.deployable_capacity + sum(management_selected_deployment) -- verified to differ from (and never reported as) the naive, defective sum(y.deployable_capacity for y in years), which double-counts unused cash carried forward year over year. | 3 | 3 | 0 | 0 | 0.1% relative (_close, tol=1e-3) against the correct formula; the naive sum is expected to DIFFER, not match | Forecast rejected -- reporting the naive sum would overstate total capacity to a reviewer, exactly the double-counting error Milestone 3A was opened to fix. | test_cumulative_capacity_naive_sum_would_overstate (asserts the naive sum exceeds the correct figure whenever any interior year carries positive undeployed capacity forward, which holds in every scenario this round) | cumulative=6315.0 but a naive sum-of-years-end-balances would report 23730.9 -- overstated by 17415.9 |
| debt_roll_forward | Balance Sheet -- Debt | arithmetic_invariant | total_debt_gaap_beginning_t = total_debt_gaap_ending_(t-1); total_debt_gaap_ending_t = beginning_t + debt_proceeds_t - debt_repayments_t | 15 | 15 | 0 | 0 | 0.1% relative (_close, tol=1e-3) | Forecast rejected -- the debt balance no longer chains correctly across years. | test_debt_roll_forward_chains_across_years | debt_end=14500.0 vs beg+proceeds-repay=14343.0 |
| eps_consistency | Income Statement | arithmetic_invariant | diluted_eps_t = net_income_t / diluted_shares_t | 15 | 15 | 0 | 0 | 0.1% relative (_close, tol=1e-3) | Forecast rejected -- EPS no longer reconciles to net income and share count. | test_eps_consistency | diluted_eps=8.50 vs net_income/shares=8.12 |
| fcf_calc | Cash Flow | arithmetic_invariant | free_cash_flow_t = operating_cash_flow_t - capital_expenditure_t (never total investing cash flow) | 15 | 15 | 0 | 0 | 0.1% relative (_close, tol=1e-3) | Forecast rejected -- also the specific control against CFI-for-CapEx substitution. | test_capex_uses_ppe_driver_never_total_cfi | FCF=4000.0 vs CFO-CapEx=3250.9 (CapEx=3809.8, distinct from total CFI=-3809.8) |
| gross_profit_calc | Income Statement | arithmetic_invariant | gross_profit_t = revenue_t * gross_margin_pct_t / 100 = revenue_t - cost_of_sales_t | 15 | 15 | 0 | 0 | 0.1% relative (_close, tol=1e-3) | Forecast rejected -- gross margin and COGS have diverged from the revenue base. | Not separately regression-tested this round; covered structurally by test_operating_income_bridge_no_double_counted_da's equality assertions. | gross_profit=29450.0, revenue*margin=29565.2, revenue-COGS=29565.2 |
| information_cutoff_compliance | Evidence / Cutoff | structural_completeness_check | Every assumption's information_cutoff <= FORECAST_INFORMATION_CUTOFF (2026-03-11) | 1 | 1 | 0 | 0 | Exact date-string comparison, no numeric tolerance | Forecast rejected -- a post-cutoff assumption would mean information not yet available at the stated cutoff was used to build the forecast. | Not corrupted directly this round; every assumption uses the same default cutoff constant, so this check currently has no live failure path to demonstrate against (see Section 8's note on this specific gap). | assumptions citing information after cutoff: ['asm_rev_growth_base'] |
| lineage_completeness | Lineage | structural_completeness_check | For each scenario, the 10 representatively-tracked metrics each have exactly one lineage row per forecast year, and every lineage row has >=1 assumption_id. | 3 | 3 | 0 | 0 | Exact count/presence, no numeric tolerance | Forecast rejected -- an incomplete lineage graph means a figure's provenance cannot be audited back to its assumptions. | Not corrupted directly this round; covered structurally by test_lineage_entries_reference_real_assumption_ids. | incomplete: missing metrics {'free_cash_flow'}, or entries with no assumption_ids |
| minimum_cash_compliance | Liquidity Policy | structural_completeness_check | funding_warning_t = (ending_cash_t < min_cash_buffer_t) | 15 | 15 | 0 | 0 | Exact boolean comparison, no numeric tolerance | WARNING (not FAIL) when ending cash is genuinely below the policy buffer -- this is a disclosed liquidity finding, not a computation error, and does not block the forecast from being reviewed. | Not corrupted directly; demonstrated organically by the seasonal stress overlay (Section 6), which DOES trip a funding warning in Downside FY2026. | ending_cash=2900.0 below min_cash_buffer=3174.8 -- funding_warning=True |
| no_finance_lease_double_counting | Balance Sheet -- Debt | structural_completeness_check | finance_lease_liabilities_t = finance_lease_liabilities_2025 (held flat) AND held OUTSIDE the total_debt_gaap roll-forward (never added into debt_proceeds/debt_repayments) | 15 | 15 | 0 | 0 | 0.1% relative on the flat-hold; exact structural check on separation | Forecast rejected -- a finance-lease figure appearing inside both the debt roll-forward and its own line would overstate leverage. | test_finance_lease_held_flat_never_folded_into_debt_schedule | finance_lease=2200.0 vs flat FY2025 actual=2113.0 |
| no_historical_forecast_mixing | Structural Separation | structural_completeness_check | set(FORECAST_YEARS) & set(HISTORICAL_YEARS) == {} AND every ForecastYear.fiscal_year in FORECAST_YEARS | 1 | 1 | 0 | 0 | Exact set/membership comparison, no numeric tolerance | Forecast rejected -- this is the last line of defense against a forecast row being mistaken for, or merged with, a historical annual_facts row. | Not corrupted directly this round (would require editing FORECAST_YEARS/HISTORICAL_YEARS themselves); covered structurally by test_forecast_year_fiscal_years_never_overlap_historical. | overlap or mistagged year detected |
| operating_income_bridge | Income Statement | arithmetic_invariant | operating_income_t = gross_profit_t - sga_expense_t - depreciation_amortization_opex_t | 15 | 15 | 0 | 0 | 0.1% relative (_close, tol=1e-3) | Forecast rejected -- the operating-income bridge no longer reconciles. | test_operating_income_bridge_no_double_counted_da (equality assertion each year) | operating_income=5200.0 vs gross_profit-SG&A-D&A=5081.9 |
| other_operating_cf_not_a_plug | Cash Flow -- Modeling Discipline | structural_completeness_check | other_operating_cf_t is IDENTICAL across every FORECAST_YEARS entry within a scenario | 3 | 3 | 0 | 0 | 1e-9 absolute (effectively exact) | Forecast rejected -- a varying other_operating_cf is the signature of a backward-solved CFO plug, exactly what item 9's non-plug policy forbids. | demo_backward_solved_cfo_plug(years, target_cfo=7500.0) -- see Section 3 | other_operating_cf per year: [589.3, 366.1, 206.9, 45.9, -115.8] -- VARIES across years, consistent with a backward-solved plug |
| pretax_income_bridge | Income Statement | arithmetic_invariant | pretax_income_t = operating_income_t - interest_expense_t + net_other_income_t | 15 | 15 | 0 | 0 | 0.1% relative (_close, tol=1e-3) | Forecast rejected -- pretax income no longer reconciles to its own inputs. | test_pretax_and_net_income_bridges | pretax_income=4900.0 vs OI-interest+other=4732.2 |
| revenue_recursion | Income Statement | arithmetic_invariant | revenue_t = revenue_(t-1) * (1 + revenue_growth_pct_t / 100) | 15 | 15 | 0 | 0 | 0.1% relative (_close, tol=1e-3) | Forecast rejected as internally inconsistent -- no downstream figure in the same scenario/year can be trusted if revenue itself does not reconcile. | test_validate_all_catches_a_broken_revenue_recursion (adds $500M to one year in place) | revenue=110327.8 vs prev*(1+g)=109827.8 |
| scenario_ordering | Cross-Scenario | scenario_comparative_check | For revenue_growth_pct, gross_margin_pct, net_income, diluted_eps: upside >= base >= downside. For sga_pct_of_revenue, effective_tax_rate_pct (inverse-direction metrics): upside <= base <= downside. CapEx/FCF/repurchases are DELIBERATELY EXCLUDED (Upside's higher CapEx intensity is economically appropriate, not a modeling error). | 5 | 5 | 0 | 0 | Exact directional (>=/<=) comparison, no numeric tolerance | Forecast rejected -- an inverted scenario would mean Downside outperforms Upside on a driver where that has no economic justification. | test_scenario_ordering_flags_an_inverted_upside_base | violated for: ['net_income'] (upside net_income < downside net_income) |
| tax_net_income_bridge | Income Statement | arithmetic_invariant | income_tax_expense_t = pretax_income_t * effective_tax_rate_pct_t / 100; net_income_t = pretax_income_t - income_tax_expense_t | 15 | 15 | 0 | 0 | 0.1% relative (_close, tol=1e-3) | Forecast rejected -- tax or net income diverges from its stated rate/base. | test_pretax_and_net_income_bridges | tax=1000.0 vs pretax*ETR=1050.6; net_income=3800.0 vs pretax-tax=3681.7 |
| working_capital_sign_checks | Cash Flow / Working Capital | arithmetic_invariant | inventory_cash_impact_t = -(inventory_balance_t - inventory_balance_(t-1)); ap_cash_impact_t = accounts_payable_balance_t - accounts_payable_balance_(t-1) | 15 | 15 | 0 | 0 | Exact sign comparison, no numeric tolerance | Forecast rejected -- a sign flip here means an inventory build is being recorded as a source of cash (or vice versa), a modeling-direction error. | test_working_capital_signs | inventory_delta=+50.0/cash_impact=+50.0 (should be negative for a build) |

## 9. Sensitivity Tables (complete, all six, plus one two-variable table)

Each one-variable table perturbs a single BASE-scenario driver in isolation (holding all others fixed) and reports the FY2030 terminal-year impact AND the cumulative FY2026-FY2030 deployable capacity. No DCF/valuation sensitivity is included -- out of scope.

### revenue_growth_pct

| Delta | FY2030 CFO | FY2030 FCF | FY2030 Ending Cash | FY2030 Deployable Capacity | Cumulative FY2026-FY2030 Deployable Capacity |
|---|---|---|---|---|---|
| -1.00 | 7,380.6 | 3,608.6 | 9,344.6 | 6,060.4 | 6,060.4 |
| -0.50 | 7,571.3 | 3,704.0 | 9,512.4 | 6,186.9 | 6,186.9 |
| +0.00 | 7,765.8 | 3,801.3 | 9,682.5 | 6,315.0 | 6,315.0 |
| +0.50 | 7,964.3 | 3,900.7 | 9,854.9 | 6,444.6 | 6,444.6 |
| +1.00 | 8,166.7 | 4,002.0 | 10,029.7 | 6,575.7 | 6,575.7 |

### gross_margin_pct

| Delta | FY2030 CFO | FY2030 FCF | FY2030 Ending Cash | FY2030 Deployable Capacity | Cumulative FY2026-FY2030 Deployable Capacity |
|---|---|---|---|---|---|
| -0.50 | 7,338.4 | 3,373.9 | 8,477.7 | 4,939.2 | 4,939.2 |
| -0.25 | 7,552.1 | 3,587.6 | 9,080.1 | 5,627.1 | 5,627.1 |
| +0.00 | 7,765.8 | 3,801.3 | 9,682.5 | 6,315.0 | 6,315.0 |
| +0.25 | 7,979.6 | 4,015.1 | 10,284.9 | 7,002.9 | 7,002.9 |
| +0.50 | 8,193.3 | 4,228.8 | 10,887.2 | 7,690.8 | 7,690.8 |

### sga_pct_of_revenue

| Delta | FY2030 CFO | FY2030 FCF | FY2030 Ending Cash | FY2030 Deployable Capacity | Cumulative FY2026-FY2030 Deployable Capacity |
|---|---|---|---|---|---|
| -0.50 | 8,194.2 | 4,229.7 | 10,942.4 | 7,746.3 | 7,746.3 |
| -0.25 | 7,980.0 | 4,015.5 | 10,312.4 | 7,030.7 | 7,030.7 |
| +0.00 | 7,765.8 | 3,801.3 | 9,682.5 | 6,315.0 | 6,315.0 |
| +0.25 | 7,551.6 | 3,587.1 | 9,052.5 | 5,599.4 | 5,599.4 |
| +0.50 | 7,337.4 | 3,373.0 | 8,422.5 | 4,883.7 | 4,883.7 |

### capex_pct_of_revenue

| Delta | FY2030 CFO | FY2030 FCF | FY2030 Ending Cash | FY2030 Deployable Capacity | Cumulative FY2026-FY2030 Deployable Capacity |
|---|---|---|---|---|---|
| -0.50 | 7,765.8 | 4,352.0 | 11,301.9 | 8,154.8 | 8,154.8 |
| -0.25 | 7,765.8 | 4,076.7 | 10,492.2 | 7,234.9 | 7,234.9 |
| +0.00 | 7,765.8 | 3,801.3 | 9,682.5 | 6,315.0 | 6,315.0 |
| +0.25 | 7,765.8 | 3,526.0 | 8,872.7 | 5,395.2 | 5,395.2 |
| +0.50 | 7,765.8 | 3,250.7 | 8,063.0 | 4,475.3 | 4,475.3 |

### inventory_pct_of_revenue

| Delta | FY2030 CFO | FY2030 FCF | FY2030 Ending Cash | FY2030 Deployable Capacity | Cumulative FY2026-FY2030 Deployable Capacity |
|---|---|---|---|---|---|
| -1.00 | 7,776.7 | 3,812.2 | 10,343.2 | 6,980.1 | 6,980.1 |
| -0.50 | 7,771.3 | 3,806.8 | 10,012.8 | 6,647.6 | 6,647.6 |
| +0.00 | 7,765.8 | 3,801.3 | 9,682.5 | 6,315.0 | 6,315.0 |
| +0.50 | 7,760.4 | 3,795.9 | 9,352.1 | 5,982.5 | 5,982.5 |
| +1.00 | 7,754.9 | 3,790.4 | 9,021.7 | 5,649.9 | 5,649.9 |

### min_cash_buffer_pct_of_revenue

| Delta | FY2030 CFO | FY2030 FCF | FY2030 Ending Cash | FY2030 Deployable Capacity | Cumulative FY2026-FY2030 Deployable Capacity |
|---|---|---|---|---|---|
| -1.00 | 7,765.8 | 3,801.3 | 9,682.5 | 7,416.3 | 7,416.3 |
| -0.50 | 7,765.8 | 3,801.3 | 9,682.5 | 6,865.6 | 6,865.6 |
| +0.00 | 7,765.8 | 3,801.3 | 9,682.5 | 6,315.0 | 6,315.0 |
| +0.50 | 7,765.8 | 3,801.3 | 9,682.5 | 5,764.4 | 5,764.4 |
| +1.00 | 7,765.8 | 3,801.3 | 9,682.5 | 5,213.8 | 5,213.8 |

### 9a. Two-Variable Sensitivity: Revenue Growth x Gross Margin (FY2030 Deployable Capacity)

Grid of revenue_growth_pct (rows) x gross_margin_pct (columns) deltas, BASE scenario, FY2030 deployable capacity in each cell.

| Revenue Growth Delta \ Gross Margin Delta | -0.50 | -0.25 | +0.00 | +0.25 | +0.50 |
|---|---|---|---|---|---|
| -1.00 | 4,727.0 | 5,393.7 | 6,060.4 | 6,727.0 | 7,393.7 |
| -0.50 | 4,832.5 | 5,509.7 | 6,186.9 | 6,864.1 | 7,541.3 |
| +0.00 | 4,939.2 | 5,627.1 | 6,315.0 | 7,002.9 | 7,690.8 |
| +0.50 | 5,047.1 | 5,745.9 | 6,444.6 | 7,143.3 | 7,842.0 |
| +1.00 | 5,156.2 | 5,866.0 | 6,575.7 | 7,285.4 | 7,995.1 |

## 10. Historical-to-Forecast Handoff

FY2025 actual -> FY2026 forecast transition for every major metric, per scenario. A metric is flagged as a cliff when its FY2026 step exceeds 1.5x the widest historical YoY swing on record (for a metric with a natural growth-rate series) or a fixed 20-percentage-point/20% threshold otherwise.

| Scenario | Metric | Last Historical (FY2025) | First Forecast (FY2026) | Step Change | % Change | Within Historical Experience | Cliff Flag |
|---|---|---|---|---|---|---|---|
| base | revenue | 104,780.00 | 105,827.80 | +1,047.80 | +1.00% | YES | no |
| base | gross_margin_pct | 27.93 | 27.93 | -0.00 | -0.01% | YES | no |
| base | sga_pct_of_revenue | 20.55 | 20.55 | -0.00 | -0.01% | YES | no |
| base | operating_income | 5,117.00 | 5,081.85 | -35.15 | -0.69% | YES | no |
| base | net_income | 3,705.00 | 3,681.67 | -23.33 | -0.63% | YES | no |
| base | diluted_eps | 8.13 | 8.12 | -0.01 | -0.10% | YES | no |
| base | operating_cash_flow | 6,562.00 | 7,060.69 | +498.69 | +7.60% | YES | no |
| base | capital_expenditure | 3,727.00 | 3,809.80 | +82.80 | +2.22% | YES | no |
| base | free_cash_flow | 2,835.00 | 3,250.88 | +415.88 | +14.67% | YES | no |
| base | ending_cash | 5,488.00 | 6,188.38 | +700.38 | +12.76% | YES | no |
| base | total_debt_gaap_ending | 14,343.00 | 14,343.00 | +0.00 | +0.00% | YES | no |
| upside | revenue | 104,780.00 | 107,923.40 | +3,143.40 | +3.00% | YES | no |
| upside | gross_margin_pct | 27.93 | 27.93 | -0.00 | -0.01% | YES | no |
| upside | sga_pct_of_revenue | 20.55 | 20.55 | -0.00 | -0.01% | YES | no |
| upside | operating_income | 5,117.00 | 5,074.56 | -42.44 | -0.83% | YES | no |
| upside | net_income | 3,705.00 | 3,743.48 | +38.48 | +1.04% | YES | no |
| upside | diluted_eps | 8.13 | 8.34 | +0.21 | +2.60% | YES | no |
| upside | operating_cash_flow | 6,562.00 | 8,832.33 | +2,270.33 | +34.60% | YES | no |
| upside | capital_expenditure | 3,727.00 | 4,640.71 | +913.71 | +24.52% | YES | no |
| upside | free_cash_flow | 2,835.00 | 4,191.62 | +1,356.62 | +47.85% | YES | no |
| upside | ending_cash | 5,488.00 | 5,727.84 | +239.84 | +4.37% | YES | no |
| upside | total_debt_gaap_ending | 14,343.00 | 13,643.00 | -700.00 | -4.88% | YES | no |
| downside | revenue | 104,780.00 | 102,160.50 | -2,619.50 | -2.50% | YES | no |
| downside | gross_margin_pct | 27.93 | 27.93 | -0.00 | -0.01% | YES | no |
| downside | sga_pct_of_revenue | 20.55 | 20.55 | -0.00 | -0.01% | YES | no |
| downside | operating_income | 5,117.00 | 5,007.91 | -109.09 | -2.13% | YES | no |
| downside | net_income | 3,705.00 | 3,539.57 | -165.43 | -4.47% | YES | no |
| downside | diluted_eps | 8.13 | 7.77 | -0.36 | -4.44% | YES | no |
| downside | operating_cash_flow | 6,562.00 | 4,739.46 | -1,822.54 | -27.77% | YES | no |
| downside | capital_expenditure | 3,727.00 | 2,860.49 | -866.51 | -23.25% | YES | no |
| downside | free_cash_flow | 2,835.00 | 1,878.97 | -956.03 | -33.72% | YES | no |
| downside | ending_cash | 5,488.00 | 5,513.97 | +25.97 | +0.47% | YES | no |
| downside | total_debt_gaap_ending | 14,343.00 | 14,543.00 | +200.00 | +1.39% | YES | no |

**0 of 33 handoff transitions flagged as a cliff.** None -- every FY2026 assumption stays within (a conservative multiple of) historical experience for its own metric.

## 11. Cutoff Audit

**Forecast information cutoff: 2026-03-11** (accession `0000027419-26-000016`).

Cutoff source record (from `docs/sources.csv`):

| Field | Value |
|---|---|
| accession_number | 0000027419-26-000016 |
| form_type | 10-K |
| period_of_report | 2026-01-31 |
| filed_at | 2026-03-11 |

**All 8 registered sources** (docs/sources.csv), sorted by filed date -- the cutoff accession is the LAST one, confirming it is genuinely the latest information used:

| Accession | Form | Period of Report | Filed At |
|---|---|---|---|
| 0000027419-22-000007 | 10-K | 2022-01-29 | 2022-03-09 |
| 0000027419-23-000015 | 10-K | 2023-01-28 | 2023-03-08 |
| 0000027419-24-000032 | 10-K | 2024-02-03 | 2024-03-13 |
| 0000027419-25-000018 | 10-K | 2025-02-01 | 2025-03-12 |
| 0000027419-25-000101 | 10-Q | 2025-05-03 | 2025-05-30 |
| 0000027419-25-000118 | 10-Q | 2025-08-02 | 2025-08-29 |
| 0000027419-25-000126 | 10-Q | 2025-11-01 | 2025-11-26 |
| 0000027419-26-000016 | 10-K | 2026-01-31 | 2026-03-11 <- CUTOFF |

**No post-cutoff source found**: YES (post-cutoff sources list: []).
**No assumption cites information after the cutoff**: YES (offending assumption IDs: []).
**Raw-fact (non-annual_facts) citations all trace to accessions at or before cutoff**: YES.

Raw-fact citations for `depreciation_amortization_cfo_addback` (the one metric sourced outside `annual_facts`):

| FY | raw_fact_id | Accession |
|---|---|---|
| 2021 | `0000027419-24-000032:us-gaap:DepreciationDepletionAndAmortization:c-11` | 0000027419-24-000032 |
| 2022 | `0000027419-25-000018:us-gaap:DepreciationDepletionAndAmortization:c-5` | 0000027419-25-000018 |
| 2023 | `0000027419-26-000016:us-gaap:DepreciationDepletionAndAmortization:c-5` | 0000027419-26-000016 |
| 2024 | `0000027419-26-000016:us-gaap:DepreciationDepletionAndAmortization:c-4` | 0000027419-26-000016 |
| 2025 | `0000027419-26-000016:us-gaap:DepreciationDepletionAndAmortization:c-1` | 0000027419-26-000016 |

**All 2 distinct source_evidence strings cited across every assumption**:

- data/curated/target_cash.db annual_facts, analytical_view=latest_restated, FY2021-FY2025 (frozen 2026-03-11 basis; see docs/milestone_2_evidence.md)
- data/curated/target_cash.db raw_facts, us-gaap:DepreciationDepletionAndAmortization, queried via target_cash.annual.latest_restated_duration, frozen 2026-09-16 (not in annual_facts -- Milestone 2 approved only the opex D&A line at annual grain)

## 12. Reviewer Deliverable Metadata

### 12a. Files Created This Round

- `docs/milestone_3_forecast_review_package.md`
- `scripts/build_milestone_3_review_package.py`
- `tests/unit/test_forecast.py (extended, not created -- see 12b)`

### 12b. Files Modified This Round

- `src/target_cash/forecast.py` -- assumption matrix builder, historical fact-ID citations, other-operating-cf bridge + plug-detection check, capital allocation waterfall + no-double-counting proof, minimum-cash-buffer 5-policy comparison, seasonality stress overlay, historical-to-forecast handoff, cutoff audit, validation-check metadata registry, cumulative deployable capacity, two-variable sensitivity, valuation_net_debt field, and 2 corrected rationale strings (other-operating-cf year attribution; minimum-cash-buffer no longer called 'recommended')
- `tests/unit/test_forecast.py` -- 30 new tests covering every function added this round
- `docs/decisions.md` -- this round's decision-log entry (see 12f)

### 12c. Commands Executed

- `.venv/bin/python scripts/build_milestone_3_review_package.py`
- `.venv/bin/python -m pytest -q`
- `git status`
- `git diff --stat`

### 12d. Tests Executed and Exact Results

```
........................................................................ [ 21%]
........................................................................ [ 42%]
........................................................................ [ 63%]
........................................................................ [ 84%]
.....................................................                    [100%]
341 passed in 1.07s
```

`tests/unit/test_forecast.py` alone:
```
........................................................................ [ 91%]
.......                                                                  [100%]
79 passed in 0.09s
```

### 12e. Git Diff Summary

Working-tree diff stat at generation time (uncommitted changes this round):
```
docs/decisions.md                           |  69 +++++++++++
 docs/milestone_3_forecast_review_package.md | 177 +++++++++++++++++----------
 scripts/build_milestone_3_review_package.py | 107 +++++++++++-----
 src/target_cash/forecast.py                 | 181 +++++++++++++++++++++++++++-
 tests/unit/test_forecast.py                 | 139 ++++++++++++++++++++-
 5 files changed, 573 insertions(+), 100 deletions(-)
```
`git status --short`:
```
M docs/decisions.md
 M docs/milestone_3_forecast_review_package.md
 M scripts/build_milestone_3_review_package.py
 M src/target_cash/forecast.py
 M tests/unit/test_forecast.py
```

No file under `data/`, `src/target_cash/migrations.py`, `config/metric_definitions.csv`, or any other Milestone 1/2 module appears in either listing above -- confirming this round did not touch historical facts, mappings, lineage, observations, or migrations.

### 12f. Known Limitations (consolidated)

- `investing_cash_flow` is modeled as exactly `-capital_expenditure`; no driver exists for other historical investing items.
- No FX translation effect is modeled (implicitly zero).
- The near-term debt repayment reserve is proxied by each year's own fixed repayment assumption -- no disclosed maturity ladder exists.
- "Other operating cash adjustments" is a single flat scenario assumption, not decomposed into stock-comp/deferred-tax/other sub-components (Section 3).
- The seasonality stress overlay (Section 6) is grounded in exactly ONE year of real quarterly evidence (FY2025) -- a single-year sample, not a multi-year seasonal pattern.
- The minimum-cash-buffer comparison (Section 5) evaluates 5 policies but endorses none; the 3.0%-of-revenue figure already wired into the base assumption set is a candidate used to produce one concrete number, not a conclusion.
- Lineage (`build_lineage()`) remains representative (10 tracked metrics), not full-grain across every one of the 50+ `ForecastYear` fields.
- Dividends are modeled via a $/share growth proxy applied to forecast diluted shares, not from a disclosed per-share dividend policy statement.
- CapEx is modeled as a % of revenue with no maintenance-vs-growth split, since Target discloses no such split.
- The two-variable sensitivity table (Section 9a) covers one pair (revenue growth x gross margin) as the requested minimum -- other pairs (e.g. gross margin x CapEx) were not also computed this round.

### 12g. Decisions Requiring Reviewer Approval

- Which of the 5 minimum-cash-buffer policies (Section 5) to adopt, if any -- none is endorsed as final in this round.
- Whether the 50% seasonality haircut (Section 6), grounded in a single year of quarterly evidence, is conservative enough, or whether a full quarterly forecasting engine should be built in a future round instead of relying on this annual-model overlay.
- Whether the representative (10-metric) lineage grain in `build_lineage()` is sufficient for reviewer sign-off, or whether full-grain lineage across every ForecastYear field is required before the forecast schema (docs/milestone_3_forecast_schema_proposal.md) can be approved.
- Whether the fixed debt schedule and buyback payout-ratio assumption VALUES themselves (Section 1's matrix) are acceptable, separate from the mechanism (which is confirmed non-plug by Section 4's proof).
- Whether to proceed to forecast schema implementation and persistence now that this audit package is available, or to request further evidence first.

---

**Stop for reviewer approval, per explicit instruction.** No forecast schema migration was written, no forecast fact was persisted, no DCF/Excel/Power BI/website work has begun, and no Milestone 1/2 historical fact, mapping, lineage, or observation was modified.
