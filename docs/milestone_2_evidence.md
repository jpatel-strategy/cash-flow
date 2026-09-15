# Milestone 2 Evidence -- Five-Year Annual Model, Persisted

Consolidated final evidence for Milestone 2 ("Five-Year Historical Financial Model and Driver Architecture"), covering the 2026-09-15 mapping-approval round and the 2026-09-16 overall-gate-enforcement / conditional-persistence round. Generated 2026-09-16 from live data -- the persisted curated database, the real `validate`/`persist-annual` command outputs, and the clean-room reproduction run -- never hand-transcribed. Regeneration: `.venv/bin/python scripts/build_milestone_2_evidence.py`.

## 1. Authoritative Source Set

8 SEC filings, each hash-verified against its own registered record (docs/sources.csv) before every clean-room rebuild:

| Accession | Form | Period of Report | Filed At |
|---|---|---|---|
| 0000027419-22-000007 | 10-K | 2022-01-29 | 2022-03-09 |
| 0000027419-23-000015 | 10-K | 2023-01-28 | 2023-03-08 |
| 0000027419-24-000032 | 10-K | 2024-02-03 | 2024-03-13 |
| 0000027419-25-000018 | 10-K | 2025-02-01 | 2025-03-12 |
| 0000027419-25-000101 | 10-Q | 2025-05-03 | 2025-05-30 |
| 0000027419-25-000118 | 10-Q | 2025-08-02 | 2025-08-29 |
| 0000027419-25-000126 | 10-Q | 2025-11-01 | 2025-11-26 |
| 0000027419-26-000016 | 10-K | 2026-01-31 | 2026-03-11 |

## 2. Mapping Gate

- **checks_run:** 49
- **passed_count:** 49
- **blocked_count:** 0
- **gate_passed:** True

Full per-metric evidence rows: see `docs/milestone_2_mapping_approval_matrix.md` (regenerated from the same live data via `scripts/build_mapping_approval_matrix.py`).

## 3. Historical Tables -- Both Analytical Views (Persisted)

### AS_ORIGINALLY_FILED

| Metric | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| revenue | 106,005.0 | 109,120.0 | 107,412.0 | 106,566.0 | 104,780.0 |
| cost_of_sales | 74,963.0 | 82,229.0 | 77,736.0 | 76,502.0 | 75,511.0 |
| gross_profit | 31,042.0 | 26,891.0 | 29,676.0 | 30,064.0 | 29,269.0 |
| operating_expenses | 19,752.0 | 20,658.0 | 21,554.0 | 21,969.0 | 21,535.0 |
| operating_income | 8,946.0 | 3,848.0 | 5,707.0 | 5,566.0 | 5,117.0 |
| interest_expense | 421.0 | 478.0 | 502.0 | 411.0 | 445.0 |
| net_other_income | 382.0 | 48.0 | 92.0 | 106.0 | 95.0 |
| pretax_income | 8,907.0 | 3,418.0 | 5,297.0 | 5,261.0 | 4,767.0 |
| income_tax_expense | 1,961.0 | 638.0 | 1,159.0 | 1,170.0 | 1,062.0 |
| net_income | 6,946.0 | 2,780.0 | 4,138.0 | 4,091.0 | 3,705.0 |
| diluted_eps | 14.1 | 5.98 | 8.94 | 8.86 | 8.13 |
| diluted_shares | 492.7 | 464.7 | 462.8 | 461.8 | 455.6 |
| operating_cash_flow | 8,625.0 | 4,018.0 | 8,621.0 | 7,367.0 | 6,562.0 |
| capital_expenditure | 3,544.0 | 5,528.0 | 4,806.0 | 2,891.0 | 3,727.0 |
| free_cash_flow | 5,081.0 | -1,510.0 | 3,815.0 | 4,476.0 | 2,835.0 |
| investing_cash_flow | -3,154.0 | -5,504.0 | -4,760.0 | -2,860.0 | -3,649.0 |
| financing_cash_flow | -8,071.0 | -2,196.0 | -2,285.0 | -3,550.0 | -2,187.0 |
| net_change_in_cash | -2,600.0 | -3,682.0 | 1,576.0 | 957.0 | 726.0 |
| dividends_paid | 1,548.0 | 1,836.0 | 2,011.0 | 2,046.0 | 2,053.0 |
| share_repurchases | 7,356.0 | 2,826.0 | 0.0 | 1,007.0 | 408.0 |
| total_debt_gaap | 11,645.0 | 14,067.0 | 14,025.0 | 13,779.0 | 14,343.0 |
| valuation_net_debt_excluding_leases | 5,734.0 | 11,838.0 | 10,220.0 | 9,017.0 | 8,855.0 |
| adjusted_net_debt_including_finance_leases | 7,809.0 | 13,910.0 | 12,233.0 | 11,178.0 | 10,968.0 |

### LATEST_RESTATED

| Metric | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| revenue | 106,005.0 | 109,120.0 | 107,412.0 | 106,566.0 | 104,780.0 |
| cost_of_sales | 74,963.0 | 82,306.0 | 77,828.0 | 76,502.0 | 75,511.0 |
| gross_profit | 31,042.0 | 26,814.0 | 29,584.0 | 30,064.0 | 29,269.0 |
| operating_expenses | 19,752.0 | 20,581.0 | 21,462.0 | 21,969.0 | 21,535.0 |
| operating_income | 8,946.0 | 3,848.0 | 5,707.0 | 5,566.0 | 5,117.0 |
| interest_expense | 421.0 | 478.0 | 502.0 | 411.0 | 445.0 |
| net_other_income | 382.0 | 48.0 | 92.0 | 106.0 | 95.0 |
| pretax_income | 8,907.0 | 3,418.0 | 5,297.0 | 5,261.0 | 4,767.0 |
| income_tax_expense | 1,961.0 | 638.0 | 1,159.0 | 1,170.0 | 1,062.0 |
| net_income | 6,946.0 | 2,780.0 | 4,138.0 | 4,091.0 | 3,705.0 |
| diluted_eps | 14.1 | 5.98 | 8.94 | 8.86 | 8.13 |
| diluted_shares | 492.7 | 464.7 | 462.8 | 461.8 | 455.6 |
| operating_cash_flow | 8,625.0 | 4,018.0 | 8,621.0 | 7,367.0 | 6,562.0 |
| capital_expenditure | 3,544.0 | 5,528.0 | 4,806.0 | 2,891.0 | 3,727.0 |
| free_cash_flow | 5,081.0 | -1,510.0 | 3,815.0 | 4,476.0 | 2,835.0 |
| investing_cash_flow | -3,154.0 | -5,504.0 | -4,760.0 | -2,860.0 | -3,649.0 |
| financing_cash_flow | -8,071.0 | -2,196.0 | -2,285.0 | -3,550.0 | -2,187.0 |
| net_change_in_cash | -2,600.0 | -3,682.0 | 1,576.0 | 957.0 | 726.0 |
| dividends_paid | 1,548.0 | 1,836.0 | 2,011.0 | 2,046.0 | 2,053.0 |
| share_repurchases | 7,188.0 | 2,646.0 | 0.0 | 1,007.0 | 408.0 |
| total_debt_gaap | 11,645.0 | 14,067.0 | 14,025.0 | 13,779.0 | 14,343.0 |
| valuation_net_debt_excluding_leases | 5,734.0 | 11,838.0 | 10,220.0 | 9,017.0 | 8,855.0 |
| adjusted_net_debt_including_finance_leases | 7,809.0 | 13,910.0 | 12,233.0 | 11,178.0 | 10,968.0 |

## 4. Metric Definitions

19 derived-metric definitions, all `reviewed`. Full formulas, sign/denominator policies, and lineage requirements: see `docs/milestone_2_mapping_approval_matrix.md` Section B.

| Metric | Formula | review_status |
|---|---|---|
| gross_profit | revenue - cost_of_sales | reviewed |
| gross_margin | gross_profit / revenue | reviewed |
| operating_margin | operating_income / revenue | reviewed |
| effective_tax_rate | income_tax_expense / pretax_income | reviewed |
| net_margin | net_income / revenue | reviewed |
| free_cash_flow | operating_cash_flow - capital_expenditure | reviewed |
| fcf_margin | free_cash_flow / revenue | reviewed |
| cash_conversion | operating_cash_flow / net_income | reviewed |
| capex_intensity | capital_expenditure / revenue | reviewed |
| total_debt_gaap | long_term_debt_gaap_carrying_value - finance_lease_liabilities (= debt_principal_schedule + debt_fair_value_hedge_adjustment, per the exact bridge) | reviewed |
| valuation_net_debt_excluding_leases | total_debt_gaap - cash_and_equivalents_balance_sheet | reviewed |
| adjusted_net_debt_including_finance_leases | valuation_net_debt_excluding_leases + finance_lease_liabilities (equivalently long_term_debt_gaap_carrying_value - cash_and_equivalents_balance_sheet -- NEVER long_term_debt_gaap_carrying_value + finance_lease_liabilities, which double-counts) | reviewed |
| inventory_to_revenue | inventory / revenue | reviewed |
| accounts_payable_to_cogs | accounts_payable / cost_of_sales | reviewed |
| debt_to_cfo | total_debt_gaap / operating_cash_flow | reviewed |
| net_debt_to_cfo | valuation_net_debt_excluding_leases / operating_cash_flow | reviewed |
| shareholder_distributions_to_fcf | (dividends_paid + share_repurchases) / free_cash_flow | reviewed |
| long_term_debt_gaap_carrying_value | long_term_debt_gaap_carrying_value_noncurrent + long_term_debt_gaap_carrying_value_current | reviewed |
| finance_lease_liabilities | finance_lease_liability_current + finance_lease_liability_noncurrent | reviewed |

## 5. CapEx / CFI Distinction

FY2025 (persisted, as-originally-filed): CFO = $6,562M, CapEx = $3,727M, CFI = -$3,649M, FCF = $2,835M (= CFO - CapEx = 6,562 - 3,727 = 2,835).

**Capital expenditure is not equal to total investing cash flow**: CapEx ($3,727M) != |CFI| ($3,649M) -- CFI includes CapEx plus other investing activity. FCF = CFO - CapEx, never CFO + CFI or CFO - |CFI|. Regression tests: `test_fy2025_capex_is_not_investing_cash_flow`, `test_derive_never_reads_investing_cash_flow_for_fcf` (`tests/unit/test_annual_dry_run.py`), and post-persistence integrity check `capex_remains_distinct_from_cfi` (confirmed `passed=True` against the actual persisted rows).

## 6. Reclassification Bridges

Metrics whose AS_ORIGINALLY_FILED and LATEST_RESTATED values genuinely differ (both persisted, both retained):

| Metric | Fiscal Year | AS_ORIGINALLY_FILED | LATEST_RESTATED | Difference |
|---|---:|---:|---:|---:|
| accounts_payable_to_cogs | 2022 | 16.40 | 16.39 | 0.01 |
| accounts_payable_to_cogs | 2023 | 15.56 | 15.54 | 0.02 |
| cost_of_sales | 2022 | 82,229.00 | 82,306.00 | -77.00 |
| cost_of_sales | 2023 | 77,736.00 | 77,828.00 | -92.00 |
| gross_margin | 2022 | 24.64 | 24.57 | 0.07 |
| gross_margin | 2023 | 27.63 | 27.54 | 0.09 |
| gross_profit | 2022 | 26,891.00 | 26,814.00 | 77.00 |
| gross_profit | 2023 | 29,676.00 | 29,584.00 | 92.00 |
| operating_expenses | 2022 | 20,658.00 | 20,581.00 | 77.00 |
| operating_expenses | 2023 | 21,554.00 | 21,462.00 | 92.00 |
| share_repurchases | 2021 | 7,356.00 | 7,188.00 | 168.00 |
| share_repurchases | 2022 | 2,826.00 | 2,646.00 | 180.00 |
| shareholder_distributions_to_fcf | 2021 | 175.24 | 171.93 | 3.31 |

13 genuinely differing (metric, fiscal_year) pairs, all within target_cash.annual.KNOWN_RECLASSIFIED_METRICS -- confirmed by the post-persistence integrity check `reclassifications_remain_distinct` and by `analytical_view_selection` in annual_analytical_validation (0 unexpected divergences across all 5 fiscal years).

## 7. Debt Bridge

Reconciles exactly (0 residual) in all 5 fiscal years: `debt_principal_schedule + debt_fair_value_hedge_adjustment (signed) + finance_lease_liabilities - current_portion = long_term_debt_gaap_carrying_value` (noncurrent). See `docs/decisions.md`, 2026-09-15 "Debt bridge correction" entry for the full worked table and source citations; proven by 21 tests in `tests/unit/test_annual_dry_run.py` and by `debt_bridge` in annual_analytical_validation (PASS in all 5 fiscal years, both views).

Finance leases are not double-counted: `adjusted_net_debt_including_finance_leases` = `long_term_debt_gaap_carrying_value - cash_and_equivalents_balance_sheet` (never `long_term_debt_gaap_carrying_value + finance_lease_liabilities`, since finance leases are already included in `long_term_debt_gaap_carrying_value`). Confirmed by the post-persistence integrity check `finance_leases_not_double_counted` (`passed=True`) against the actual persisted rows in all fiscal years.

## 8. Fiscal-Calendar Treatment

| Fiscal Year | Quarter | Period Start | Period End | Weeks | 53-Week Year |
|---:|---:|---|---|---:|---|
| 2019 | annual | 2019-02-03 | 2020-02-01 | 52 | no |
| 2020 | annual | 2020-02-02 | 2021-01-30 | 52 | no |
| 2021 | annual | 2021-01-31 | 2022-01-29 | 52 | no |
| 2022 | annual | 2022-01-30 | 2023-01-28 | 52 | no |
| 2023 | annual | 2023-01-29 | 2024-02-03 | 53 | YES |
| 2024 | annual | 2024-02-04 | 2025-02-01 | 52 | no |
| 2025 | annual | 2025-02-02 | 2026-01-31 | 52 | no |
| 2025 | 1 | 2025-02-02 | 2025-05-03 | 13 | no |
| 2025 | 2 | 2025-05-04 | 2025-08-02 | 13 | no |
| 2025 | 3 | 2025-08-03 | 2025-11-01 | 13 | no |
| 2025 | 4 | 2025-11-02 | 2026-01-31 | 13 | no |

FY2023 is the 53-week year (period_end 2024-02-03, 53 weeks) -- confirmed by `fifty_three_week_disclosure` (PASS) and the post-persistence integrity check `fy2023_retains_53_week_indicator` (`passed=True`).

`period_facts_unified`'s instant facts carry `frequency='instant'` always (never reclassified to 'annual'/'quarterly'), plus a separate `reporting_period_role` field (`YEAR_END`/`QUARTER_END`) from migration `0013_period_facts_unified_reporting_role`. A date that is simultaneously a fiscal year-end and its own Q4 end is emitted exactly once, labeled `YEAR_END` (the documented canonical role), never duplicated.

## 9. Persistence Counts

- **annual_facts:** 488 (300 direct + 188 derived)
- **annual_fact_observations:** 686, by relationship: selected=300, corroborating=368, restated=9, original_historical=9, conflicting=0
- **annual_lineage:** 384

Exact match with the preflight plan produced by `target_cash.annual_persistence.compute_persistence_preflight` before any write occurred -- see `docs/decisions.md`, 2026-09-16 entries, for the preflight/post-persistence count reconciliation, the finance_lease_liabilities gap self-caught and fixed (478 -> 488 total facts), and the observation-completeness enrichment (300 -> 686 observations) with its own reconciliation.

### Reclassification evidence rows (restated / original_historical observations)

| Metric | Fiscal Year | View (anchor) | Relationship | Accession | Value | Diff from selected |
|---|---:|---|---|---|---:|---:|
| cost_of_sales | 2022 | as_originally_filed | restated | 0000027419-25-000018 | 82,306.0 | 77.0 |
| cost_of_sales | 2022 | latest_restated | original_historical | 0000027419-23-000015 | 82,229.0 | -77.0 |
| cost_of_sales | 2022 | latest_restated | original_historical | 0000027419-24-000032 | 82,229.0 | -77.0 |
| cost_of_sales | 2023 | as_originally_filed | restated | 0000027419-25-000018 | 77,828.0 | 92.0 |
| cost_of_sales | 2023 | as_originally_filed | restated | 0000027419-26-000016 | 77,828.0 | 92.0 |
| cost_of_sales | 2023 | latest_restated | original_historical | 0000027419-24-000032 | 77,736.0 | -92.0 |
| operating_expenses | 2022 | as_originally_filed | restated | 0000027419-25-000018 | 20,581.0 | -77.0 |
| operating_expenses | 2022 | latest_restated | original_historical | 0000027419-23-000015 | 20,658.0 | 77.0 |
| operating_expenses | 2022 | latest_restated | original_historical | 0000027419-24-000032 | 20,658.0 | 77.0 |
| operating_expenses | 2023 | as_originally_filed | restated | 0000027419-25-000018 | 21,462.0 | -92.0 |
| operating_expenses | 2023 | as_originally_filed | restated | 0000027419-26-000016 | 21,462.0 | -92.0 |
| operating_expenses | 2023 | latest_restated | original_historical | 0000027419-24-000032 | 21,554.0 | 92.0 |
| share_repurchases | 2021 | as_originally_filed | restated | 0000027419-24-000032 | 7,188.0 | -168.0 |
| share_repurchases | 2021 | latest_restated | original_historical | 0000027419-22-000007 | 7,356.0 | 168.0 |
| share_repurchases | 2021 | latest_restated | original_historical | 0000027419-23-000015 | 7,356.0 | 168.0 |
| share_repurchases | 2022 | as_originally_filed | restated | 0000027419-24-000032 | 2,646.0 | -180.0 |
| share_repurchases | 2022 | as_originally_filed | restated | 0000027419-25-000018 | 2,646.0 | -180.0 |
| share_repurchases | 2022 | latest_restated | original_historical | 0000027419-23-000015 | 2,826.0 | 180.0 |

## 10. Lineage Integrity

Post-persistence integrity report (`target_cash.annual_persistence.verify_persistence_integrity`, an independent read-only re-check against the database, never the in-memory preflight plan). Every check name and result below is read live from that function's own current output, never a hand-copied list:

| Check | Result |
|---|---|
| every_direct_fact_has_selected_source_evidence | PASS |
| every_derived_fact_has_complete_input_lineage | PASS |
| all_facts_have_required_evidence | PASS |
| zero_orphan_observations | PASS |
| zero_orphan_lineage | PASS |
| zero_orphan_facts | PASS |
| zero_duplicate_canonical_keys | PASS |
| both_analytical_views_complete | PASS |
| reclassifications_remain_distinct | PASS |
| fy2023_retains_53_week_indicator | PASS |
| finance_leases_not_double_counted | PASS |
| capex_remains_distinct_from_cfi | PASS |
| no_unavailable_metric_persisted | PASS |
| target_defined_net_debt_never_persisted | PASS |
| every_direct_fact_has_exactly_one_selected_observation | PASS |
| zero_duplicate_observation_keys | PASS |
| every_reclassification_has_original_and_later_evidence | PASS |
| conflicting_observations_reported_explicitly | PASS |

All 18 checks pass (`all_passed`: True). Conflicting-observation detail: 0 conflicting observation(s): []

## 11. Validation Results

- **milestone_1_validation.gate_passed:** True (62/79 passed, 0 failed)
- **mapping_evidence_gate.gate_passed:** True (49 passed, 0 blocked)
- **annual_analytical_validation.gate_passed:** True (checks_run=130, by_status={'PASS': 120, 'FAIL': 0, 'BLOCKED': 0, 'UNAVAILABLE': 10, 'NOT_APPLICABLE': 0})
- **overall_gate_passed:** True

`lineage_readiness`: {'PASS': 5} (5 fiscal years, all PASS post-persistence -- was 5 NOT_APPLICABLE before persistence).

The 10 UNAVAILABLE results are exclusively `target_defined_net_debt_policy` (['target_defined_net_debt_policy']) -- the one explicitly allowed permanently-unavailable metric, never persisted (Target discloses no net-debt measure of its own).

## 12. Clean-Room Reproduction

Full rebuild from the 8 registered source filings alone (fetch -> normalize -> validate -> persist quarterly/instant -> seed reference data -> `persist-annual` through the real, conditionally-authorized CLI command -- never a one-off script -> validate), then compared against the active database via `scripts/compare_databases.py`:

```
Read 8 registered sources from /home/user/cash-flow/docs/sources.csv
Clean-room directory: /tmp/target_cash_clean_room_b1n03is9
All 8 source documents present and hash-verified against the manifest.

=== Clean-room result ===
filings_cached: 8
raw_facts_stored: 1293
quarterly_facts (persisted): 28
instant_facts (persisted): 10
fiscal_calendar_rows_total: 11
concept_equivalence_rules_total: 2
persist_annual.written: {'annual_facts': 488, 'annual_fact_observations': 686, 'annual_lineage': 384}
persist_annual.integrity.all_passed: True
validate.milestone_1_validation.gate_passed: True
validate.milestone_1_validation.checks_run: 79
validate.milestone_1_validation.checks_passed: 62
validate.milestone_1_validation.checks_failed: 0
validate.milestone_1_validation.checks_blocked: 0
validate.milestone_1_validation.checks_unavailable: 17
validate.annual_analytical_validation.checks_run: 130
validate.annual_analytical_validation.gate_passed: True
validate.annual_analytical_validation.by_status: {'PASS': 120, 'FAIL': 0, 'BLOCKED': 0, 'UNAVAILABLE': 10, 'NOT_APPLICABLE': 0}
validate.mapping_evidence_gate.checks_run: 49
validate.mapping_evidence_gate.passed_count: 49
validate.mapping_evidence_gate.blocked_count: 0
validate.mapping_evidence_gate.gate_passed: True
validate.overall_gate_passed: True
database: /tmp/target_cash_clean_room_b1n03is9/data/curated/target_cash.db

=== Comparing clean-room database against the active database ===
export                        a_rows  b_rows  match  sha256
quarterly_facts                   28      28  YES    4c45df7ae95479b13d6152e87a94508154ec391ed2be6fe846698554cdd071d5
lineage                           45      45  YES    7813dbae698b64ada3719bcbdbd851f7efb978ca0216fe1a0bd4df652b1885d4
instant_facts                     10      10  YES    399c7bffdf1f0f81f83800fcbbc06e75ce7c7c3983a8347249e5589c52e5861d
instant_fact_observations         18      18  YES    12c83c77e22af78c27334f1ba3373c423a20d33b8718338f10776f29bc2dd76f
annual_facts                     488     488  YES    234c7997b58b3e7f9eeb510a4945d0831b8d0335a0b3f71d82884bb360e6d49a
annual_fact_observations         686     686  YES    68bd42d25504874550a6e6f8d96e5c30fa99d3defb91d9ac4edf5635bcad411d
annual_lineage                   384     384  YES    b6f73358be34fb21f6675b153bdee1af3c1cf9148b0856222dbd9e7965a0ee3f
period_facts_unified             526     526  YES    41ff487191d5849dd075ed8f143f7dd25c63827fd46fb633cb71d5c8a6123ed3
validation_results                            YES    feb15103d10bd4c62084ff8b66e4620982b45ed43baceb499b41b8721e86be47

ALL EXPORTS MATCH
```

## 13. Deterministic Export Hashes

**Canonical normalized exports are hash-identical after documented exclusion of nondeterministic fields.** Every one of the 8 canonical table exports (quarterly_facts, lineage, instant_facts, instant_fact_observations, annual_facts, annual_fact_observations, annual_lineage, period_facts_unified) plus the validation_results comparison matched exactly between the clean-room rebuild and the active database -- see Section 12's output above for the actual hashes from the most recent run. Exclusions are documented in `scripts/compare_databases.py`'s own module docstring: uuid4()-derived quarterly/instant IDs and wall-clock insertion timestamps are excluded (they carry no analytical information beyond identifying "this specific fact", which metric+period already provides); annual_facts/annual_fact_observations/annual_lineage's own IDs need NO exclusion, since target_cash.annual_persistence builds them deterministically.

## 14. Remaining Limitations

- `annual_fact_observations` currently records only `selected` (authoritative) observations -- `corroborating`/`restated`/`conflicting` relationships are not yet catalogued at annual grain (the persistence preflight documents this as a floor, not a ceiling; see `docs/milestone_2_mapping_approval_matrix.md` Section C).
- `current_portion_of_debt` (a metrics.csv row distinct from `long_term_debt_gaap_carrying_value_current`) remains `candidate_unverified` and unimplemented in `target_cash.annual.derive()` -- excluded from this round's approved and persisted set.
- `target_defined_net_debt` remains permanently UNAVAILABLE by design; Target discloses no net-debt measure of its own.
- No forecast, DCF, Excel, Power BI, or website work has been started, per this round's explicit instruction to stop after persistence verification.

## 15. Reproducibility Commands

```bash
.venv/bin/python -m pytest tests/ -q
.venv/bin/python -m target_cash.cli validate --config config/model.yml
.venv/bin/python -m target_cash.cli persist-annual --config config/model.yml
.venv/bin/python scripts/build_mapping_approval_matrix.py
.venv/bin/python scripts/clean_room_rebuild.py
.venv/bin/python scripts/build_milestone_2_evidence.py
```
