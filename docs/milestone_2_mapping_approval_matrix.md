# Milestone 2 -- Mapping-Approval Matrix and Persistence Manifest

Generated 2026-09-15 from config/metrics.csv, config/metric_definitions.csv, and the live curated database (data/curated/target_cash.db), using target_cash.annual's own resolve_tag/duration_value/instant_value functions -- the exact code path the annual model itself reads. Every accession number, context ID, and value below is queried live, never hand-typed. Regeneration: `.venv/bin/python scripts/build_mapping_approval_matrix.py`.

This document satisfies items 3 and 5 of the 2026-09-15 approval round: item 3's complete mapping-approval matrix for every direct annual metric, and item 5's persistence manifest with expected counts. Item 2's two distinct gates (mapping_evidence_gate, analytical_validation_gate) are kept structurally separate throughout -- a metric's row here records its MAPPING evidence; arithmetic/derivation validation is reported separately by `target_cash validate` (annual_analytical_validation section) and is NOT restated here.

## A. Mapping-Approval Matrix -- Direct Annual Metrics (item 3)

30 metrics: target_cash.annual's own canonical DURATION_METRICS + INSTANT_METRICS sets -- never "every row in config/metrics.csv" (that file also carries legacy/candidate/quarterly-only rows that are not part of the annual model; see docs/decisions.md 'Mapping-approval self-caught gaps').

### `accounts_payable`

- **Statement / location:** balance_sheet (point_in_time)
- **Unit / sign convention:** USD / point_in_time_unsigned
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** instant (point-in-time)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** Point-in-time only.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:AccountsPayableCurrent | 0000027419-22-000007 | `i508a56acdf244287a036fd2e0574e883_I20220129` | 15478.0 |
| 2022 | us-gaap:AccountsPayableCurrent | 0000027419-23-000015 | `i34dc0125b4af4d3f9dbc50b5ed530854_I20230128` | 13487.0 |
| 2023 | us-gaap:AccountsPayableCurrent | 0000027419-24-000032 | `c-12` | 12098.0 |
| 2024 | us-gaap:AccountsPayableCurrent | 0000027419-25-000018 | `c-6` | 13053.0 |
| 2025 | us-gaap:AccountsPayableCurrent | 0000027419-26-000016 | `c-6` | 12622.0 |

### `capital_expenditure`

- **Statement / location:** cash_flow_statement (flow)
- **Unit / sign convention:** USD / positive_magnitude_outflow
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** 

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:PaymentsToAcquirePropertyPlantAndEquipment | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 3544.0 |
| 2022 | us-gaap:PaymentsToAcquirePropertyPlantAndEquipment | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 5528.0 |
| 2023 | us-gaap:PaymentsToAcquirePropertyPlantAndEquipment | 0000027419-24-000032 | `c-1` | 4806.0 |
| 2024 | us-gaap:PaymentsToAcquirePropertyPlantAndEquipment | 0000027419-25-000018 | `c-1` | 2891.0 |
| 2025 | us-gaap:PaymentsToAcquirePropertyPlantAndEquipment | 0000027419-26-000016 | `c-1` | 3727.0 |

### `cash_and_equivalents_balance_sheet`

- **Statement / location:** balance_sheet (point_in_time)
- **Unit / sign convention:** USD / point_in_time_unsigned
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** instant (point-in-time)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** Point-in-time only. Never differenced to create a quarterly flow. Confirmed 2026-09-15 against the actual <ix:nonFraction> markup in accession 0000027419-26-000016 (contexts c-6=2026-01-31 val 5488M, c-7=2025-02-01 val 4762M), Consolidated Statements of Financial Position, 'Cash and cash equivalents' line. Kept a distinct metric from cash_and_equivalents_rollforward even though they currently agree numerically — see that row's notes. See docs/decisions.md 2026-09-15 entries.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:CashCashEquivalentsAndShortTermInvestments | 0000027419-22-000007 | `i508a56acdf244287a036fd2e0574e883_I20220129` | 5911.0 |
| 2022 | us-gaap:CashCashEquivalentsAndShortTermInvestments | 0000027419-23-000015 | `i34dc0125b4af4d3f9dbc50b5ed530854_I20230128` | 2229.0 |
| 2023 | us-gaap:CashCashEquivalentsAndShortTermInvestments | 0000027419-24-000032 | `c-12` | 3805.0 |
| 2024 | us-gaap:CashCashEquivalentsAndShortTermInvestments | 0000027419-25-000018 | `c-6` | 4762.0 |
| 2025 | us-gaap:CashCashEquivalentsAndShortTermInvestments | 0000027419-26-000016 | `c-6` | 5488.0 |

### `cost_of_sales`

- **Statement / location:** income_statement (flow)
- **Unit / sign convention:** USD / positive_magnitude_expense
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** differs between AS_ORIGINALLY_FILED and LATEST_RESTATED (known reclassification)
- **Limitation / evidence notes:** Verify whether D&A is embedded here per Target's presentation before adding it elsewhere.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:CostOfGoodsAndServicesSold | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 74963.0 |
| 2022 | us-gaap:CostOfGoodsAndServicesSold | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 82229.0 |
| 2023 | us-gaap:CostOfGoodsAndServicesSold | 0000027419-24-000032 | `c-1` | 77736.0 |
| 2024 | us-gaap:CostOfGoodsAndServicesSold | 0000027419-25-000018 | `c-1` | 76502.0 |
| 2025 | us-gaap:CostOfGoodsAndServicesSold | 0000027419-26-000016 | `c-1` | 75511.0 |

### `debt_fair_value_hedge_adjustment`

- **Statement / location:** balance_sheet (point_in_time)
- **Unit / sign convention:** USD / signed_bidirectional
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** instant (point-in-time)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** NEW 2026-09-15 (third debt-classification review). Company-extension-taxonomy tag (tgt:SwapValuationAdjustments, not us-gaap), found by reading Target's own debt-maturity-schedule note table directly rather than by tag-name pattern search -- explains why the earlier exhaustive us-gaap tag scan missed it. Statement location: the debt-maturity-schedule note, between 'Total notes and debentures' (debt_principal_schedule) and 'Finance lease liabilities' (finance_lease_liabilities), immediately before 'Less: Amounts due within one year'. Confirmed present in all 5 filings: FY2025=(55) [sign='-'], FY2024=(125), FY2023=(126), FY2022=(74), FY2021=77 [no sign attribute -- positive, the only year this adjustment is additive rather than subtractive; a fair-value hedge adjustment can genuinely flip sign with interest-rate movements, so this is not treated as an anomaly]. EXACT bridge verified in all 5 years: debt_principal_schedule + debt_fair_value_hedge_adjustment (signed) + finance_lease_liabilities - [current portion of the combined BS line] = long_term_debt_gaap_carrying_value (noncurrent portion) -- e.g. FY2025: 14,398-55+2,113-2,130=14,326, exactly the reported noncurrent balance. See docs/milestone_2_proposal.md Section 2 for the full 5-year table. Not marked reviewed.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | tgt:SwapValuationAdjustments | 0000027419-22-000007 | `i508a56acdf244287a036fd2e0574e883_I20220129` | 77.0 |
| 2022 | tgt:SwapValuationAdjustments | 0000027419-23-000015 | `i34dc0125b4af4d3f9dbc50b5ed530854_I20230128` | -74.0 |
| 2023 | tgt:SwapValuationAdjustments | 0000027419-24-000032 | `c-12` | -126.0 |
| 2024 | tgt:SwapValuationAdjustments | 0000027419-25-000018 | `c-6` | -125.0 |
| 2025 | tgt:SwapValuationAdjustments | 0000027419-26-000016 | `c-6` | -55.0 |

### `debt_principal_schedule`

- **Statement / location:** balance_sheet (point_in_time)
- **Unit / sign convention:** USD / point_in_time_unsigned
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** instant (point-in-time)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** NEW 2026-09-15 (Milestone 2 debt-classification correction, item 5). Debt-maturity-schedule note total. Confirmed present in all 5 filings as a single combined instant value (not split current/noncurrent -- no such split exists for this tag in any filing): FY2025=14,398M, FY2024=13,904M, FY2023=14,151M, FY2022=14,141M, FY2021=11,568M. Direct comparison to long_term_debt_gaap_carrying_value is NOT_APPLICABLE (different definitions: contractual/note-schedule principal vs. GAAP balance-sheet carrying value) -- see the debt bridge in docs/milestone_2_proposal.md Section 7. Not marked reviewed.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:LongTermDebt | 0000027419-22-000007 | `i508a56acdf244287a036fd2e0574e883_I20220129` | 11568.0 |
| 2022 | us-gaap:LongTermDebt | 0000027419-23-000015 | `i34dc0125b4af4d3f9dbc50b5ed530854_I20230128` | 14141.0 |
| 2023 | us-gaap:LongTermDebt | 0000027419-24-000032 | `c-12` | 14151.0 |
| 2024 | us-gaap:LongTermDebt | 0000027419-25-000018 | `c-6` | 13904.0 |
| 2025 | us-gaap:LongTermDebt | 0000027419-26-000016 | `c-6` | 14398.0 |

### `debt_proceeds`

- **Statement / location:** cash_flow_statement (flow)
- **Unit / sign convention:** USD / positive_magnitude_inflow
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** 

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:ProceedsFromIssuanceOfLongTermDebt | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 1972.0 |
| 2022 | us-gaap:ProceedsFromIssuanceOfLongTermDebt | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 2625.0 |
| 2023 | us-gaap:ProceedsFromIssuanceOfLongTermDebt | 0000027419-24-000032 | `c-1` | 0.0 |
| 2024 | us-gaap:ProceedsFromIssuanceOfLongTermDebt | 0000027419-25-000018 | `c-1` | 741.0 |
| 2025 | us-gaap:ProceedsFromIssuanceOfLongTermDebt | 0000027419-26-000016 | `c-1` | 1984.0 |

### `debt_repayments`

- **Statement / location:** cash_flow_statement (flow)
- **Unit / sign convention:** USD / positive_magnitude_outflow
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** 

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:RepaymentsOfLongTermDebt | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 1147.0 |
| 2022 | us-gaap:RepaymentsOfLongTermDebt | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 163.0 |
| 2023 | us-gaap:RepaymentsOfLongTermDebt | 0000027419-24-000032 | `c-1` | 147.0 |
| 2024 | us-gaap:RepaymentsOfLongTermDebt | 0000027419-25-000018 | `c-1` | 1139.0 |
| 2025 | us-gaap:RepaymentsOfLongTermDebt | 0000027419-26-000016 | `c-1` | 1643.0 |

### `depreciation_amortization_opex`

- **Statement / location:** income_statement (flow)
- **Unit / sign convention:** USD / positive_magnitude_expense
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** Statement of Operations line, titled by Target itself 'Depreciation and amortization (exclusive of depreciation included in cost of sales)' -- the label itself confirms part of D&A is embedded in cost_of_sales. Confirmed 2026-09-15 against accession 0000027419-26-000016 (context c-1, FY2025=2617M; c-4, FY2024=2529M; c-5, FY2023=2415M). Kept distinct from depreciation_amortization_cfo_addback: this is the smaller, exclusive-of-COGS operating-expense figure only, never the total. See docs/decisions.md 2026-09-15 entries.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:DepreciationAndAmortization | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 2344.0 |
| 2022 | us-gaap:DepreciationAndAmortization | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 2385.0 |
| 2023 | us-gaap:DepreciationAndAmortization | 0000027419-24-000032 | `c-1` | 2415.0 |
| 2024 | us-gaap:DepreciationAndAmortization | 0000027419-25-000018 | `c-1` | 2529.0 |
| 2025 | us-gaap:DepreciationAndAmortization | 0000027419-26-000016 | `c-1` | 2617.0 |

### `diluted_eps`

- **Statement / location:** income_statement (flow)
- **Unit / sign convention:** USD / signed_bidirectional
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** NEW 2026-09-15 (found while building the annual dry-run script, item 8/9), same gap as pretax_income above -- discussed in prior rounds' tables but never added as a metrics.csv row until now. Statement of Operations line 'Diluted'. Not marked reviewed.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:EarningsPerShareDiluted | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 14.1 |
| 2022 | us-gaap:EarningsPerShareDiluted | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 5.98 |
| 2023 | us-gaap:EarningsPerShareDiluted | 0000027419-24-000032 | `c-1` | 8.94 |
| 2024 | us-gaap:EarningsPerShareDiluted | 0000027419-25-000018 | `c-1` | 8.86 |
| 2025 | us-gaap:EarningsPerShareDiluted | 0000027419-26-000016 | `c-1` | 8.13 |

### `diluted_shares`

- **Statement / location:** income_statement (flow)
- **Unit / sign convention:** USD / point_in_time_unsigned
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** NEW 2026-09-15 (found while building the annual dry-run script, item 8/9), same gap as pretax_income above. Statement of Operations line 'Weighted average diluted shares outstanding'. Not marked reviewed.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 492.7 |
| 2022 | us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 464.7 |
| 2023 | us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding | 0000027419-24-000032 | `c-1` | 462.8 |
| 2024 | us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding | 0000027419-25-000018 | `c-1` | 461.8 |
| 2025 | us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding | 0000027419-26-000016 | `c-1` | 455.6 |

### `dividends_paid`

- **Statement / location:** cash_flow_statement (flow)
- **Unit / sign convention:** USD / positive_magnitude_outflow
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** CORRECTED 2026-09-15 (found while building the annual dry-run script, item 8): candidate_xbrl_tag changed from PaymentsOfDividends to PaymentsOfDividendsCommonStock -- us-gaap:PaymentsOfDividends has 0 occurrences in any of the 5 cached filings (confirmed by tag scan); PaymentsOfDividendsCommonStock is the actual Statement of Cash Flows 'Dividends paid' line, already used throughout this project's own analysis (e.g. docs/milestone_2_proposal.md's cash-flow tables) but never corrected here until this dry run's raw_facts query came back empty and exposed the mismatch. Not marked reviewed.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:PaymentsOfDividendsCommonStock | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 1548.0 |
| 2022 | us-gaap:PaymentsOfDividendsCommonStock | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 1836.0 |
| 2023 | us-gaap:PaymentsOfDividendsCommonStock | 0000027419-24-000032 | `c-1` | 2011.0 |
| 2024 | us-gaap:PaymentsOfDividendsCommonStock | 0000027419-25-000018 | `c-1` | 2046.0 |
| 2025 | us-gaap:PaymentsOfDividendsCommonStock | 0000027419-26-000016 | `c-1` | 2053.0 |

### `finance_lease_liability_current`

- **Statement / location:** balance_sheet (point_in_time)
- **Unit / sign convention:** USD / point_in_time_unsigned
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** instant (point-in-time)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** NEW 2026-09-15 (Milestone 2 debt-classification correction, item 5). Confirmed present in all 5 filings: FY2025=131M, FY2024=136M, FY2023=119M, FY2022=129M, FY2021=108M. Sums exactly with finance_lease_liability_noncurrent to finance_lease_obligations in every year. Not marked reviewed.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:FinanceLeaseLiabilityCurrent | 0000027419-22-000007 | `i508a56acdf244287a036fd2e0574e883_I20220129` | 108.0 |
| 2022 | us-gaap:FinanceLeaseLiabilityCurrent | 0000027419-23-000015 | `i34dc0125b4af4d3f9dbc50b5ed530854_I20230128` | 129.0 |
| 2023 | us-gaap:FinanceLeaseLiabilityCurrent | 0000027419-24-000032 | `c-12` | 119.0 |
| 2024 | us-gaap:FinanceLeaseLiabilityCurrent | 0000027419-25-000018 | `c-6` | 136.0 |
| 2025 | us-gaap:FinanceLeaseLiabilityCurrent | 0000027419-26-000016 | `c-6` | 131.0 |

### `finance_lease_liability_noncurrent`

- **Statement / location:** balance_sheet (point_in_time)
- **Unit / sign convention:** USD / point_in_time_unsigned
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** instant (point-in-time)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** NEW 2026-09-15 (Milestone 2 debt-classification correction, item 5). Confirmed present in all 5 filings: FY2025=1,982M, FY2024=2,025M, FY2023=1,894M, FY2022=1,943M, FY2021=1,967M. Not marked reviewed.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:FinanceLeaseLiabilityNoncurrent | 0000027419-22-000007 | `i508a56acdf244287a036fd2e0574e883_I20220129` | 1967.0 |
| 2022 | us-gaap:FinanceLeaseLiabilityNoncurrent | 0000027419-23-000015 | `i34dc0125b4af4d3f9dbc50b5ed530854_I20230128` | 1943.0 |
| 2023 | us-gaap:FinanceLeaseLiabilityNoncurrent | 0000027419-24-000032 | `c-12` | 1894.0 |
| 2024 | us-gaap:FinanceLeaseLiabilityNoncurrent | 0000027419-25-000018 | `c-6` | 2025.0 |
| 2025 | us-gaap:FinanceLeaseLiabilityNoncurrent | 0000027419-26-000016 | `c-6` | 1982.0 |

### `financing_cash_flow`

- **Statement / location:** cash_flow_statement (flow)
- **Unit / sign convention:** USD / signed_bidirectional
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** REVIEWED 2026-09-15, same criteria and evidence as operating_cash_flow. CORRECTED 2026-09-15 (sign-policy fix): concept_directionality is signed_bidirectional -- CFF has always been negative (net use of cash: dividends + share repurchases + debt repayments exceeding any debt proceeds) in the periods examined, but the concept permits either sign (e.g. a large debt issuance could make a period net-positive), so raw sign is never a compatibility gate. No competing candidate found. YTD-only pattern, same as operating_cash_flow. See docs/decisions.md 2026-09-15 cash-flow-mapping entries.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:NetCashProvidedByUsedInFinancingActivities | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | -8071.0 |
| 2022 | us-gaap:NetCashProvidedByUsedInFinancingActivities | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | -2196.0 |
| 2023 | us-gaap:NetCashProvidedByUsedInFinancingActivities | 0000027419-24-000032 | `c-1` | -2285.0 |
| 2024 | us-gaap:NetCashProvidedByUsedInFinancingActivities | 0000027419-25-000018 | `c-1` | -3550.0 |
| 2025 | us-gaap:NetCashProvidedByUsedInFinancingActivities | 0000027419-26-000016 | `c-1` | -2187.0 |

### `income_tax_expense`

- **Statement / location:** income_statement (flow)
- **Unit / sign convention:** USD / positive_magnitude_expense
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** Only modeled explicitly if the explicit-tax net-income method is chosen.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:IncomeTaxExpenseBenefit | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 1961.0 |
| 2022 | us-gaap:IncomeTaxExpenseBenefit | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 638.0 |
| 2023 | us-gaap:IncomeTaxExpenseBenefit | 0000027419-24-000032 | `c-1` | 1159.0 |
| 2024 | us-gaap:IncomeTaxExpenseBenefit | 0000027419-25-000018 | `c-1` | 1170.0 |
| 2025 | us-gaap:IncomeTaxExpenseBenefit | 0000027419-26-000016 | `c-1` | 1062.0 |

### `interest_expense`

- **Statement / location:** income_statement (flow)
- **Unit / sign convention:** USD / positive_magnitude_expense
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** Only modeled explicitly if the explicit-interest net-income method is chosen. CORRECTED 2026-09-15: candidate_xbrl_tag changed from InterestExpense to InterestExpenseNonoperating -- us-gaap:InterestExpense does not appear anywhere in accession 0000027419-26-000016 (confirmed by exhaustive tag scan), so it cannot be the source of the reported figure. us-gaap:InterestExpenseNonoperating is the Statement of Operations 'Net interest expense' line: context c-1 (FY2025, no dimensional segment), value 445,000,000; c-4 (FY2024)=411M; c-5 (FY2023)=502M. Also present at c-216/c-217/c-218 under tgt:ReportableSegmentMember (dimensional duplicate, excluded from selection). Competing candidates considered and rejected: us-gaap:FinanceLeaseInterestExpense (present in the document but a narrower, lease-specific interest concept, not the aggregate net interest expense line) and us-gaap:InterestPaidNet (a cash-paid supplemental-disclosure figure, not the accrual-basis income-statement expense). NOT marked reviewed -- verification against the FY2025 10-K alone is insufficient per instruction; still needs cross-check against the three FY2025 10-Q primary statements before review. TAG MIGRATION FOUND 2026-09-15 (Milestone 2, authoritative-filing reassessment): us-gaap:InterestExpenseNonoperating is correct for FY2024/FY2025 only. The FY2021, FY2022, and FY2023 10-Ks (each authoritative for its own year) use the plain us-gaap:InterestExpense tag instead (0 InterestExpenseNonoperating occurrences in any of those three filings); values are continuous across the rename (FY2021=421M, FY2022=478M, FY2023=502M, reproducing the pretax-income bridge exactly in every year) -- a tag rename, not a restatement. This metrics.csv schema cannot express a vintage-dependent tag in one column; see docs/milestone_2_proposal.md's mapping matrix for the full per-filing tag record. See docs/decisions.md 2026-09-15 entries.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:InterestExpense | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 421.0 |
| 2022 | us-gaap:InterestExpense | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 478.0 |
| 2023 | us-gaap:InterestExpense | 0000027419-24-000032 | `c-1` | 502.0 |
| 2024 | us-gaap:InterestExpenseNonoperating | 0000027419-25-000018 | `c-1` | 411.0 |
| 2025 | us-gaap:InterestExpenseNonoperating | 0000027419-26-000016 | `c-1` | 445.0 |

### `inventory`

- **Statement / location:** balance_sheet (point_in_time)
- **Unit / sign convention:** USD / point_in_time_unsigned
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** instant (point-in-time)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** Point-in-time only.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:InventoryNet | 0000027419-22-000007 | `i508a56acdf244287a036fd2e0574e883_I20220129` | 13902.0 |
| 2022 | us-gaap:InventoryNet | 0000027419-23-000015 | `i34dc0125b4af4d3f9dbc50b5ed530854_I20230128` | 13499.0 |
| 2023 | us-gaap:InventoryNet | 0000027419-24-000032 | `c-12` | 11886.0 |
| 2024 | us-gaap:InventoryNet | 0000027419-25-000018 | `c-6` | 12740.0 |
| 2025 | us-gaap:InventoryNet | 0000027419-26-000016 | `c-6` | 12304.0 |

### `investing_cash_flow`

- **Statement / location:** cash_flow_statement (flow)
- **Unit / sign convention:** USD / signed_bidirectional
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** REVIEWED 2026-09-15, same criteria and evidence as operating_cash_flow. CORRECTED 2026-09-15 (sign-policy fix): concept_directionality is signed_bidirectional -- CFI has always been negative (net use of cash) in the periods examined, but the concept permits either sign (e.g. a large divestiture could make a period net-positive), so raw sign is never a compatibility gate, only matching directionality policy is. Competing candidate us-gaap:PaymentsForProceedsFromOtherInvestingActivities considered and rejected -- it is a sub-component within investing activities (a single line item), not the net investing-activities total. YTD-only pattern, same as operating_cash_flow. See docs/decisions.md 2026-09-15 cash-flow-mapping entries.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:NetCashProvidedByUsedInInvestingActivities | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | -3154.0 |
| 2022 | us-gaap:NetCashProvidedByUsedInInvestingActivities | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | -5504.0 |
| 2023 | us-gaap:NetCashProvidedByUsedInInvestingActivities | 0000027419-24-000032 | `c-1` | -4760.0 |
| 2024 | us-gaap:NetCashProvidedByUsedInInvestingActivities | 0000027419-25-000018 | `c-1` | -2860.0 |
| 2025 | us-gaap:NetCashProvidedByUsedInInvestingActivities | 0000027419-26-000016 | `c-1` | -3649.0 |

### `long_term_debt_gaap_carrying_value_current`

- **Statement / location:** balance_sheet (point_in_time)
- **Unit / sign convention:** USD / point_in_time_unsigned
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** instant (point-in-time)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** NEW 2026-09-15 (found while building the annual dry-run script, item 8): the current-portion companion tag to long_term_debt_gaap_carrying_value, needed as its own metrics.csv row so normalize's concept scan actually extracts it into raw_facts -- previously only mentioned in another row's notes text, never scanned. Confirmed present in all 5 filings: FY2025=2,130M, FY2024=1,636M, FY2023=1,116M, FY2022=130M, FY2021=171M. Not marked reviewed.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:LongTermDebtAndCapitalLeaseObligationsCurrent | 0000027419-22-000007 | `i508a56acdf244287a036fd2e0574e883_I20220129` | 171.0 |
| 2022 | us-gaap:LongTermDebtAndCapitalLeaseObligationsCurrent | 0000027419-23-000015 | `i34dc0125b4af4d3f9dbc50b5ed530854_I20230128` | 130.0 |
| 2023 | us-gaap:LongTermDebtAndCapitalLeaseObligationsCurrent | 0000027419-24-000032 | `c-12` | 1116.0 |
| 2024 | us-gaap:LongTermDebtAndCapitalLeaseObligationsCurrent | 0000027419-25-000018 | `c-6` | 1636.0 |
| 2025 | us-gaap:LongTermDebtAndCapitalLeaseObligationsCurrent | 0000027419-26-000016 | `c-6` | 2130.0 |

### `long_term_debt_gaap_carrying_value_noncurrent`

- **Statement / location:** balance_sheet (point_in_time)
- **Unit / sign convention:** USD / point_in_time_unsigned
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** instant (point-in-time)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** ADDED 2026-09-15 (Milestone 2 mapping-approval round, self-caught gap): this row did not previously exist even though target_cash.annual.INSTANT_METRICS already resolves and uses this exact tag for the annual model's debt bridge (all 5 fiscal years reconcile to zero difference -- see test_all_five_years_debt_bridges_reconcile_to_zero_difference in tests/unit/test_annual_dry_run.py). Confirmed present in all 5 filings: FY2025=14,326M, FY2024=14,304M, FY2023=14,922M, FY2022=16,009M, FY2021=13,549M. Companion to long_term_debt_gaap_carrying_value_current. Not marked reviewed under the quarterly mapping_status (not a quarterly-derivation input).

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:LongTermDebtAndCapitalLeaseObligations | 0000027419-22-000007 | `i508a56acdf244287a036fd2e0574e883_I20220129` | 13549.0 |
| 2022 | us-gaap:LongTermDebtAndCapitalLeaseObligations | 0000027419-23-000015 | `i34dc0125b4af4d3f9dbc50b5ed530854_I20230128` | 16009.0 |
| 2023 | us-gaap:LongTermDebtAndCapitalLeaseObligations | 0000027419-24-000032 | `c-12` | 14922.0 |
| 2024 | us-gaap:LongTermDebtAndCapitalLeaseObligations | 0000027419-25-000018 | `c-6` | 14304.0 |
| 2025 | us-gaap:LongTermDebtAndCapitalLeaseObligations | 0000027419-26-000016 | `c-6` | 14326.0 |

### `net_change_in_cash`

- **Statement / location:** cash_flow_statement (flow)
- **Unit / sign convention:** USD / signed_bidirectional
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** REVIEWED 2026-09-15. This is Target's own reported net-change-in-cash line, used for the cash_movement (Layer A) and cash_flow_composition (Layer B) validation checks -- NOT the same concept as cash_and_equivalents_rollforward (which is the point-in-time beginning/ending balance). No separate FX line or fact exists anywhere in any of the 5 filings (exhaustive tag scan for any *ExchangeRate* concept found none) -- Target's own tag name explicitly says "...IncludingExchangeRateEffect", meaning FX (if any) is definitionally folded into this one reported figure, never a separate addend. Exact reconciliation confirmed: CFO+CFI+CFF equals this reported figure exactly (zero residual) in all 5 periods examined -- see docs/decisions.md 2026-09-15 cash-flow-mapping entries for the full table. Sign is the true net change (can be positive or negative); do not confuse with cash_and_equivalents_rollforward's point-in-time instant values.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | -2600.0 |
| 2022 | us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | -3682.0 |
| 2023 | us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect | 0000027419-24-000032 | `c-1` | 1576.0 |
| 2024 | us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect | 0000027419-25-000018 | `c-1` | 957.0 |
| 2025 | us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect | 0000027419-26-000016 | `c-1` | 726.0 |

### `net_income`

- **Statement / location:** income_statement (flow)
- **Unit / sign convention:** USD / positive_magnitude_inflow
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** TAG MIGRATION FOUND 2026-09-15 (Milestone 2, authoritative-filing reassessment): us-gaap:NetIncomeLoss is correct for FY2022-FY2025 (all three filings covering those years use it). The FY2021 10-K (authoritative for FY2021) has zero NetIncomeLoss occurrences; it tags the 'Net earnings' statement line as us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic instead (value 6,946M, exactly reproducing the pretax-income bridge -- Target has no preferred stock or noncontrolling interest in this period, so this basic-EPS-numerator tag and the headline net-income concept are identical here). This metrics.csv schema cannot express a vintage-dependent tag in one column; see docs/milestone_2_proposal.md's mapping matrix for the full per-filing tag record. See docs/decisions.md 2026-09-15 entries.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 6946.0 |
| 2022 | us-gaap:NetIncomeLoss | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 2780.0 |
| 2023 | us-gaap:NetIncomeLoss | 0000027419-24-000032 | `c-1` | 4138.0 |
| 2024 | us-gaap:NetIncomeLoss | 0000027419-25-000018 | `c-1` | 4091.0 |
| 2025 | us-gaap:NetIncomeLoss | 0000027419-26-000016 | `c-1` | 3705.0 |

### `net_other_income`

- **Statement / location:** income_statement (flow)
- **Unit / sign convention:** USD / positive_magnitude_inflow
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** REVIEWED 2026-09-15 per project owner confirmation that raw-fact 0000027419-26-000016:us-gaap:OtherNonoperatingIncomeExpense:c-1 is the consolidated FY2025 Statement of Operations fact with no dimensional members. Statement of Operations line 'Net other income', between 'Net interest expense' and 'Earnings before income taxes'. Confirmed via raw ix:nonFraction markup at accession 0000027419-26-000016: taxonomy=us-gaap, tag=OtherNonoperatingIncomeExpense, contextRef=c-1 (entity 0000027419, duration 2025-02-02 to 2026-01-31, no dimensional segment), unitRef=usd, scale=6, raw tagged value=95 (no sign='-' attribute present, unlike IncreaseDecreaseInAccountsPayable's explicit sign='-'), true value=95,000,000. Presentation sign: displayed in parentheses '(95)' on the rendered statement. Internal normalized sign: POSITIVE/additive -- confirmed by exact reproduction of the reported bridge: Operating income 5,117 - Net interest expense 445 + Net other income 95 - Provision for income taxes 1,062 = Net earnings 3,705 (exact, no residual). Competing candidates checked: only us-gaap:InterestExpenseNonoperating (already the separate Net interest expense line) and us-gaap:RentalIncomeNonoperating (a narrower, unrelated note-level concept) appear anywhere in the document; neither is a genuine competitor for this line. Also present at c-216/c-217/c-218 under tgt:ReportableSegmentMember -- dimensional duplicate, excluded from selection. See docs/decisions.md 2026-09-15 entries for the full evidence record.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:OtherNonoperatingIncomeExpense | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 382.0 |
| 2022 | us-gaap:OtherNonoperatingIncomeExpense | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 48.0 |
| 2023 | us-gaap:OtherNonoperatingIncomeExpense | 0000027419-24-000032 | `c-1` | 92.0 |
| 2024 | us-gaap:OtherNonoperatingIncomeExpense | 0000027419-25-000018 | `c-1` | 106.0 |
| 2025 | us-gaap:OtherNonoperatingIncomeExpense | 0000027419-26-000016 | `c-1` | 95.0 |

### `operating_cash_flow`

- **Statement / location:** cash_flow_statement (flow)
- **Unit / sign convention:** USD / signed_bidirectional
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** REVIEWED 2026-09-15 per mapping-approval criteria: exact tag us-gaap:NetCashProvidedByUsedInOperatingActivities appears on the primary Consolidated Statements of Cash Flows in all 5 cached filings (FY2024 10-K, FY2025 Q1/Q2/Q3 10-Qs, FY2025 10-K), consolidated context (no dimensional/segment duplicate found anywhere), no competing candidate tag found (only the standard NetCashProvidedByUsedInOperatingActivities exists). CORRECTED 2026-09-15 (sign-policy fix): concept_directionality is signed_bidirectional, not a fixed-sign magnitude -- CFO has always been positive in the periods examined, but the concept itself permits either sign (a period of net operating cash use is not a mapping error), so combining periods must never be gated on raw sign, only on all four sharing this same directionality policy. Reported only as YTD-cumulative in the 10-Qs (context c-1 = that filing's own YTD period) -- no discrete-quarter figure is ever separately filed, so this follows the same YTD-only derivation pattern as depreciation_amortization_cfo_addback (Q1 direct since YTD1=Q1; Q2-Q4 derived by subtraction). Exact reconciliation confirmed against reported net-change-in-cash and beginning/ending cash for all 5 periods (Q1, 6mo, 9mo, FY2025 annual, FY2024 annual) -- see docs/decisions.md 2026-09-15 cash-flow-mapping entries.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:NetCashProvidedByUsedInOperatingActivities | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 8625.0 |
| 2022 | us-gaap:NetCashProvidedByUsedInOperatingActivities | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 4018.0 |
| 2023 | us-gaap:NetCashProvidedByUsedInOperatingActivities | 0000027419-24-000032 | `c-1` | 8621.0 |
| 2024 | us-gaap:NetCashProvidedByUsedInOperatingActivities | 0000027419-25-000018 | `c-1` | 7367.0 |
| 2025 | us-gaap:NetCashProvidedByUsedInOperatingActivities | 0000027419-26-000016 | `c-1` | 6562.0 |

### `operating_expenses`

- **Statement / location:** income_statement (flow)
- **Unit / sign convention:** USD / positive_magnitude_expense
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** differs between AS_ORIGINALLY_FILED and LATEST_RESTATED (known reclassification)
- **Limitation / evidence notes:** CORRECTED 2026-09-15 (Milestone 2 mapping review): candidate_xbrl_tag changed from OperatingExpenses to SellingGeneralAndAdministrativeExpense -- us-gaap:OperatingExpenses does not appear anywhere in accession 0000027419-25-000018 (FY2024 10-K) or accession 0000027419-26-000016 (FY2025 10-K), confirmed by exhaustive tag scan of both documents. us-gaap:SellingGeneralAndAdministrativeExpense is Target's actual Statement of Operations 'Selling, general and administrative expenses' line: FY2025 10-K context c-1 (FY2025)=21,535M, c-4 (FY2024)=21,969M, c-5 (FY2023)=21,462M; FY2024 10-K context c-5 (FY2022, comparative-only)=20,581M. No competing candidate tag found. This line excludes depreciation_amortization_opex (a separate reported line) -- confirmed by the income-statement bridge Gross profit - SG&A - D&A(opex) = Operating income reproducing the reported Operating income exactly (zero residual) for FY2022-FY2025. Not marked reviewed -- statement-location and D&A-embedding confirmation still needs reviewer sign-off per Milestone 2 item 5. See docs/decisions.md 2026-09-15 Milestone 2 entries.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:SellingGeneralAndAdministrativeExpense | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 19752.0 |
| 2022 | us-gaap:SellingGeneralAndAdministrativeExpense | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 20658.0 |
| 2023 | us-gaap:SellingGeneralAndAdministrativeExpense | 0000027419-24-000032 | `c-1` | 21554.0 |
| 2024 | us-gaap:SellingGeneralAndAdministrativeExpense | 0000027419-25-000018 | `c-1` | 21969.0 |
| 2025 | us-gaap:SellingGeneralAndAdministrativeExpense | 0000027419-26-000016 | `c-1` | 21535.0 |

### `operating_income`

- **Statement / location:** income_statement (flow)
- **Unit / sign convention:** USD / positive_magnitude_inflow
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** 

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:OperatingIncomeLoss | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 8946.0 |
| 2022 | us-gaap:OperatingIncomeLoss | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 3848.0 |
| 2023 | us-gaap:OperatingIncomeLoss | 0000027419-24-000032 | `c-1` | 5707.0 |
| 2024 | us-gaap:OperatingIncomeLoss | 0000027419-25-000018 | `c-1` | 5566.0 |
| 2025 | us-gaap:OperatingIncomeLoss | 0000027419-26-000016 | `c-1` | 5117.0 |

### `pretax_income`

- **Statement / location:** income_statement (flow)
- **Unit / sign convention:** USD / signed_bidirectional
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** NEW 2026-09-15 (found while building the annual dry-run script, item 8/9): this metric was discussed extensively in docs/milestone_2_proposal.md's income-statement bridge (Operating income - interest_expense + net_other_income = Pretax income, verified exact in all 5 years) but was never actually added as its own config/metrics.csv row until the dry-run script's raw_facts query came back empty for every accession and exposed the gap -- the bridge verification in prior rounds was done by direct HTML re-extraction, not by querying raw_facts, so the omission was not caught until this round tried to query the real ingested data. Statement of Operations line 'Earnings before income taxes'. Not marked reviewed.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 8907.0 |
| 2022 | us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 3418.0 |
| 2023 | us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest | 0000027419-24-000032 | `c-1` | 5297.0 |
| 2024 | us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest | 0000027419-25-000018 | `c-1` | 5261.0 |
| 2025 | us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest | 0000027419-26-000016 | `c-1` | 4767.0 |

### `revenue`

- **Statement / location:** income_statement (flow)
- **Unit / sign convention:** USD / positive_magnitude_inflow
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** identical under both analytical views (no reclassification observed)
- **Limitation / evidence notes:** Confirm vs. legacy Revenues/SalesRevenueNet tags used before ASC 606 adoption; check for a Net sales-only line if Target separates credit card revenue.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 106005.0 |
| 2022 | us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 109120.0 |
| 2023 | us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax | 0000027419-24-000032 | `c-1` | 107412.0 |
| 2024 | us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax | 0000027419-25-000018 | `c-1` | 106566.0 |
| 2025 | us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax | 0000027419-26-000016 | `c-1` | 104780.0 |

### `share_repurchases`

- **Statement / location:** cash_flow_statement (flow)
- **Unit / sign convention:** USD / positive_magnitude_outflow
- **mapping_evidence_gate status:** `reviewed`
- **Fact kind:** duration (flow)
- **View treatment:** differs between AS_ORIGINALLY_FILED and LATEST_RESTATED (known reclassification)
- **Limitation / evidence notes:** RECLASSIFICATION FOUND 2026-09-15 (Milestone 2, authoritative-filing reassessment), UPDATED 2026-09-15 (second review round -- FY2021 also affected, not just FY2022): the FY2023 10-K reclassifies BOTH FY2021 and FY2022 relative to the filings that originally reported them as their own primary year. FY2022: fact_id 0000027419-23-000015:us-gaap:PaymentsForRepurchaseOfCommonStock:icce5194b17ef459680012472bdec4a34_D20220130-20230128 = 2,826M (as-originally-filed) vs. fact_id 0000027419-24-000032:us-gaap:PaymentsForRepurchaseOfCommonStock:c-10 = 2,646M (latest-restated, carried unchanged into the FY2024 10-K's FY2022 comparative), a $180M difference. FY2021: fact_id 0000027419-22-000007:us-gaap:PaymentsForRepurchaseOfCommonStock:ia69484dcd4e4439791020018d198f9dd_D20210131-20220129 = 7,356M (as-originally-filed, corroborated unchanged by the FY2022 10-K's own FY2021 comparative) vs. fact_id 0000027419-24-000032:us-gaap:PaymentsForRepurchaseOfCommonStock:c-11 = 7,188M (latest-restated), a $168M difference. Both reclassifications first appear in the FY2023 10-K, applied retrospectively to both open comparative years at once -- this timing pattern is consistent with (but does not prove) a systematic classification-methodology change rather than a one-off correction of an error; searched both filings' text for 'excise tax' and 'accelerated share repurchase' disclosures and found no explanatory text tying a specific dollar amount to this shift. NOT LABELED AN ERROR -- classified as an unexplained reclassification pending further evidence. All values retained; FY2023, FY2024, FY2025 repurchase figures agree exactly across every filing vintage that reports them. See docs/decisions.md 2026-09-15 entries.

| FY | Tag | Accession | Context ID | Value (raw) |
|---|---|---|---|---|
| 2021 | us-gaap:PaymentsForRepurchaseOfCommonStock | 0000027419-22-000007 | `ia69484dcd4e4439791020018d198f9dd_D20210131-20220129` | 7356.0 |
| 2022 | us-gaap:PaymentsForRepurchaseOfCommonStock | 0000027419-23-000015 | `icce5194b17ef459680012472bdec4a34_D20220130-20230128` | 2826.0 |
| 2023 | us-gaap:PaymentsForRepurchaseOfCommonStock | 0000027419-24-000032 | `c-1` | 0.0 |
| 2024 | us-gaap:PaymentsForRepurchaseOfCommonStock | 0000027419-25-000018 | `c-1` | 1007.0 |
| 2025 | us-gaap:PaymentsForRepurchaseOfCommonStock | 0000027419-26-000016 | `c-1` | 408.0 |

## B. Derived Metric Definitions (item 4)

19 definitions from config/metric_definitions.csv, each cross-checked against a real computed FY2025 value from target_cash.annual.derive() (as_filed view) to confirm the definition is not just documented but actually implemented and produces a value.

### `gross_profit` (def_gross_profit_v1, v1)

- **Formula:** revenue - cost_of_sales
- **Unit / sign policy:** USD_millions / signed_bidirectional (positive in every observed year)
- **Zero-denominator policy:** N/A (revenue never zero for an operating retailer)
- **Negative-denominator policy:** N/A (revenue never negative)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=29269.0
- **Limitation:** FY2022/FY2023 differ materially by view (see reclassification bridges) -- both values must be computed and retained, never only one.

### `gross_margin` (def_gross_margin_v1, v1)

- **Formula:** gross_profit / revenue
- **Unit / sign policy:** percent / positive in every observed year
- **Zero-denominator policy:** BLOCKED if revenue=0 (not expected for Target but not assumed away)
- **Negative-denominator policy:** N/A (revenue never negative)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=27.93
- **Limitation:** Inherits gross_profit's view-dependence for FY2022/FY2023.

### `operating_margin` (def_operating_margin_v1, v1)

- **Formula:** operating_income / revenue
- **Unit / sign policy:** percent / signed_bidirectional (positive in every observed year)
- **Zero-denominator policy:** BLOCKED if revenue=0
- **Negative-denominator policy:** N/A (revenue never negative)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=4.88
- **Limitation:** operating_income itself is view-invariant (unaffected by the COGS/SG&A reclassification) -- this ratio does not differ between views in practice, even though it is computed under both.

### `effective_tax_rate` (def_effective_tax_rate_v1, v1)

- **Formula:** income_tax_expense / pretax_income
- **Unit / sign policy:** percent / positive in every observed year (0-40% reasonableness band per the validation gate)
- **Zero-denominator policy:** BLOCKED if pretax_income=0
- **Negative-denominator policy:** NOT_APPLICABLE if pretax_income<0 (a tax rate on a pretax loss is not a meaningful percentage without further disclosure of the loss's tax character) -- not observed in FY2021-FY2025 but the policy is stated for completeness
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=22.28
- **Limitation:** View-invariant in practice (neither input is reclassification-affected).

### `net_margin` (def_net_margin_v1, v1)

- **Formula:** net_income / revenue
- **Unit / sign policy:** percent / positive in every observed year
- **Zero-denominator policy:** BLOCKED if revenue=0
- **Negative-denominator policy:** N/A (revenue never negative)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=3.54
- **Limitation:** View-invariant in practice.

### `free_cash_flow` (def_free_cash_flow_v1, v1)

- **Formula:** operating_cash_flow - capital_expenditure
- **Unit / sign policy:** USD_millions / signed_bidirectional (negative in FY2022)
- **Zero-denominator policy:** N/A (CFO can legitimately be zero; formula still computes)
- **Negative-denominator policy:** N/A (CapEx is a magnitude, never negative by this project's sign convention)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=2835.0
- **Limitation:** View-invariant in practice (neither CFO nor CapEx is reclassification-affected).

### `fcf_margin` (def_fcf_margin_v1, v1)

- **Formula:** free_cash_flow / revenue
- **Unit / sign policy:** percent / signed_bidirectional (negative in FY2022)
- **Zero-denominator policy:** BLOCKED if revenue=0
- **Negative-denominator policy:** N/A (revenue never negative)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=2.71
- **Limitation:** View-invariant in practice.

### `cash_conversion` (def_cash_conversion_v1, v1)

- **Formula:** operating_cash_flow / net_income
- **Unit / sign policy:** ratio (x) / positive in every observed year
- **Zero-denominator policy:** BLOCKED if net_income=0
- **Negative-denominator policy:** NOT_APPLICABLE if net_income<0 (a conversion ratio against a net loss is not economically meaningful) -- not observed in FY2021-FY2025
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=1.7711
- **Limitation:** View-invariant in practice.

### `capex_intensity` (def_capex_intensity_v1, v1)

- **Formula:** capital_expenditure / revenue
- **Unit / sign policy:** percent / positive in every observed year
- **Zero-denominator policy:** BLOCKED if revenue=0
- **Negative-denominator policy:** N/A (revenue never negative)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=3.56
- **Limitation:** View-invariant in practice.

### `total_debt_gaap` (def_total_debt_gaap_v1, v1)

- **Formula:** long_term_debt_gaap_carrying_value - finance_lease_liabilities (= debt_principal_schedule + debt_fair_value_hedge_adjustment, per the exact bridge)
- **Unit / sign policy:** USD_millions / positive magnitude
- **Zero-denominator policy:** N/A (not a ratio)
- **Negative-denominator policy:** N/A (not a ratio)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=14343.0
- **Limitation:** Gated on the debt-construction tests required in item 6 of the 2026-09-15 approval round before review_status can become 'reviewed'; the bridge itself is proven exact, this row records the definition, not yet the review sign-off. REVIEWED 2026-09-15 (item 6 debt-construction tests now exist and pass in tests/unit/test_annual_dry_run.py: test_finance_leases_are_not_counted_twice_in_total_debt_gaap, test_adjusted_net_debt_does_not_double_count_finance_leases, test_swap_valuation_adjustment_retains_actual_sign_both_directions, test_current_portion_is_subtracted_exactly_once_in_the_bridge, test_all_five_years_debt_bridges_reconcile_to_zero_difference (all 5 fiscal years), test_valuation_net_debt_excludes_finance_leases_consistently, test_target_defined_net_debt_remains_unavailable_even_with_full_debt_data -- 21/21 debt+CapEx tests passing. Promoted from pending_debt_tests to reviewed.

### `valuation_net_debt_excluding_leases` (def_valuation_net_debt_excluding_leases_v1, v1)

- **Formula:** total_debt_gaap - cash_and_equivalents_balance_sheet
- **Unit / sign policy:** USD_millions / signed_bidirectional (could be negative if cash exceeds debt; positive in every observed year)
- **Zero-denominator policy:** N/A (not a ratio)
- **Negative-denominator policy:** N/A (not a ratio)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=8855.0
- **Limitation:** Same gating as total_debt_gaap. This project's own construction -- never labeled a Target-reported figure (Target discloses no net-debt measure). REVIEWED 2026-09-15 (item 6 debt-construction tests now exist and pass in tests/unit/test_annual_dry_run.py: test_finance_leases_are_not_counted_twice_in_total_debt_gaap, test_adjusted_net_debt_does_not_double_count_finance_leases, test_swap_valuation_adjustment_retains_actual_sign_both_directions, test_current_portion_is_subtracted_exactly_once_in_the_bridge, test_all_five_years_debt_bridges_reconcile_to_zero_difference (all 5 fiscal years), test_valuation_net_debt_excludes_finance_leases_consistently, test_target_defined_net_debt_remains_unavailable_even_with_full_debt_data -- 21/21 debt+CapEx tests passing. Promoted from pending_debt_tests to reviewed.

### `adjusted_net_debt_including_finance_leases` (def_adjusted_net_debt_including_finance_leases_v1, v1)

- **Formula:** valuation_net_debt_excluding_leases + finance_lease_liabilities (equivalently long_term_debt_gaap_carrying_value - cash_and_equivalents_balance_sheet -- NEVER long_term_debt_gaap_carrying_value + finance_lease_liabilities, which double-counts)
- **Unit / sign policy:** USD_millions / positive in every observed year
- **Zero-denominator policy:** N/A (not a ratio)
- **Negative-denominator policy:** N/A (not a ratio)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=10968.0
- **Limitation:** Same gating as total_debt_gaap. Double-counting is prevented by construction and by the dedicated test required in item 6; see docs/milestone_2_schema_and_dry_run.md Section 2 for the lease-inclusion component matrix this definition depends on. REVIEWED 2026-09-15 (item 6 debt-construction tests now exist and pass in tests/unit/test_annual_dry_run.py: test_finance_leases_are_not_counted_twice_in_total_debt_gaap, test_adjusted_net_debt_does_not_double_count_finance_leases, test_swap_valuation_adjustment_retains_actual_sign_both_directions, test_current_portion_is_subtracted_exactly_once_in_the_bridge, test_all_five_years_debt_bridges_reconcile_to_zero_difference (all 5 fiscal years), test_valuation_net_debt_excludes_finance_leases_consistently, test_target_defined_net_debt_remains_unavailable_even_with_full_debt_data -- 21/21 debt+CapEx tests passing. Promoted from pending_debt_tests to reviewed.

### `inventory_to_revenue` (def_inventory_to_revenue_v1, v1)

- **Formula:** inventory / revenue
- **Unit / sign policy:** percent / positive in every observed year
- **Zero-denominator policy:** BLOCKED if revenue=0
- **Negative-denominator policy:** N/A (revenue never negative)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=11.74
- **Limitation:** Mixes a point-in-time stock (inventory) with an annual flow (revenue) -- an average-vs-year-end-inventory convention choice, using year-end per the existing quarterly-model precedent; flagged, not changed, this round.

### `accounts_payable_to_cogs` (def_accounts_payable_to_cogs_v1, v1)

- **Formula:** accounts_payable / cost_of_sales
- **Unit / sign policy:** percent / positive in every observed year
- **Zero-denominator policy:** BLOCKED if cost_of_sales=0
- **Negative-denominator policy:** N/A (cost_of_sales never negative)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=16.72
- **Limitation:** View-dependent for FY2022/FY2023 through cost_of_sales (see reclassification bridges) -- both values computed and retained. Same point-in-time/flow convention caveat as inventory_to_revenue.

### `debt_to_cfo` (def_debt_to_cfo_v1, v1)

- **Formula:** total_debt_gaap / operating_cash_flow
- **Unit / sign policy:** ratio (x) / positive in every observed year
- **Zero-denominator policy:** BLOCKED if operating_cash_flow=0
- **Negative-denominator policy:** NOT_APPLICABLE if operating_cash_flow<0 (not observed FY2021-FY2025, but a negative-CFO leverage ratio is not economically meaningful without qualification)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=2.1858
- **Limitation:** Gated on total_debt_gaap's own gating (item 6 debt tests). REVIEWED 2026-09-15 (item 6 debt-construction tests now exist and pass in tests/unit/test_annual_dry_run.py: test_finance_leases_are_not_counted_twice_in_total_debt_gaap, test_adjusted_net_debt_does_not_double_count_finance_leases, test_swap_valuation_adjustment_retains_actual_sign_both_directions, test_current_portion_is_subtracted_exactly_once_in_the_bridge, test_all_five_years_debt_bridges_reconcile_to_zero_difference (all 5 fiscal years), test_valuation_net_debt_excludes_finance_leases_consistently, test_target_defined_net_debt_remains_unavailable_even_with_full_debt_data -- 21/21 debt+CapEx tests passing. Promoted from pending_debt_tests to reviewed.

### `net_debt_to_cfo` (def_net_debt_to_cfo_v1, v1)

- **Formula:** valuation_net_debt_excluding_leases / operating_cash_flow
- **Unit / sign policy:** ratio (x) / positive in every observed year
- **Zero-denominator policy:** BLOCKED if operating_cash_flow=0
- **Negative-denominator policy:** NOT_APPLICABLE if operating_cash_flow<0 (not observed)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=1.3494
- **Limitation:** Gated on valuation_net_debt_excluding_leases' own gating (item 6 debt tests). REVIEWED 2026-09-15 (item 6 debt-construction tests now exist and pass in tests/unit/test_annual_dry_run.py: test_finance_leases_are_not_counted_twice_in_total_debt_gaap, test_adjusted_net_debt_does_not_double_count_finance_leases, test_swap_valuation_adjustment_retains_actual_sign_both_directions, test_current_portion_is_subtracted_exactly_once_in_the_bridge, test_all_five_years_debt_bridges_reconcile_to_zero_difference (all 5 fiscal years), test_valuation_net_debt_excludes_finance_leases_consistently, test_target_defined_net_debt_remains_unavailable_even_with_full_debt_data -- 21/21 debt+CapEx tests passing. Promoted from pending_debt_tests to reviewed.

### `shareholder_distributions_to_fcf` (def_shareholder_distributions_to_fcf_v1, v1)

- **Formula:** (dividends_paid + share_repurchases) / free_cash_flow
- **Unit / sign policy:** percent / positive when FCF>0 (can exceed 100% -- e.g. FY2021 = 175.24%, a genuine, disclosed data point, not an error)
- **Zero-denominator policy:** BLOCKED if free_cash_flow=0
- **Negative-denominator policy:** NOT_APPLICABLE if free_cash_flow<0 -- REQUIRED: FY2022 must be NOT_APPLICABLE under this policy, since FY2022 FCF = -1,510M in both analytical views. This is a hard requirement, not a default -- see the dedicated test enforcing it.
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=86.81
- **Limitation:** share_repurchases is reclassification-affected for FY2021/FY2022 -- this ratio differs by view in those two years; both computed and retained. FY2022 is NOT_APPLICABLE under EITHER view's repurchase figure, since the denominator (FCF) is negative regardless of which repurchase value is used.

### `long_term_debt_gaap_carrying_value` (def_long_term_debt_gaap_carrying_value_v1, v1)

- **Formula:** long_term_debt_gaap_carrying_value_noncurrent + long_term_debt_gaap_carrying_value_current
- **Unit / sign policy:** USD_millions / positive magnitude in every observed year
- **Zero-denominator policy:** N/A (not a ratio)
- **Negative-denominator policy:** N/A (not a ratio)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=16456.0
- **Limitation:** Trivial exact sum with zero additional judgment beyond its two components, both independently reviewed (see mapping-approval matrix rows for long_term_debt_gaap_carrying_value_noncurrent and _current). Reconciliation proven in tests/unit/test_annual_dry_run.py's debt-bridge tests, which depend on this exact sum being correct in all 5 fiscal years.

### `finance_lease_liabilities` (def_finance_lease_liabilities_v1, v1)

- **Formula:** finance_lease_liability_current + finance_lease_liability_noncurrent
- **Unit / sign policy:** USD_millions / positive magnitude in every observed year
- **Zero-denominator policy:** N/A (not a ratio)
- **Negative-denominator policy:** N/A (not a ratio)
- **Valid analytical views:** as_originally_filed;latest_restated
- **review_status:** `reviewed`
- **FY2025 as-filed computed value:** status=DERIVED, value=2113.0
- **Limitation:** Trivial exact sum with zero additional judgment beyond its two components, both independently reviewed (see mapping-approval matrix rows for finance_lease_liability_current and finance_lease_liability_noncurrent). Reconciliation proven in tests/unit/test_annual_dry_run.py's debt-bridge tests, which depend on this exact sum being correct in all 5 fiscal years.

## C. Persistence Manifest -- Expected Counts (item 5)

Materialized dual-view design: every approved metric x 5 fiscal years x both analytical views (AS_ORIGINALLY_FILED, LATEST_RESTATED) -- never a sparse override. An unchanged value between views still gets two distinct annual_facts rows (the table's UNIQUE(metric, fiscal_year, analytical_view) constraint requires it), but those two rows share the same underlying evidence (the same raw_fact_id in annual_fact_observations); a changed (reclassified) value gets two rows with genuinely different values and, where applicable, different lineage. Counts below are computed live from target_cash.annual.compute_all_years() against the real database -- not estimated.

### By analytical view

| View | Direct annual_facts rows | Derived annual_facts rows | Total |
|---|---:|---:|---:|
| AS_ORIGINALLY_FILED | 150 | 94 | 244 |
| LATEST_RESTATED | 150 | 94 | 244 |
| **Total (both views)** | **300** | **188** | **488** |

### By direct vs. derived, and overall table-row expectations

- **Direct annual_facts rows expected:** 300 of 300 possible slots (30 metrics x 5 fiscal years x 2 views). 0 non-persistable slots.
- **Derived annual_facts rows expected:** 188 of 190 possible slots (19 metrics x 5 fiscal years x 2 views). 2 non-persistable slots (the FY2022 shareholder_distributions_to_fcf NOT_APPLICABLE cells under both views -- the hard requirement from item 4, confirmed here as an actual exclusion, not just documentation).
- **Total annual_facts rows expected: 488**
- **annual_fact_observations rows expected (minimum):** 300 -- one 'selected' observation per persisted DIRECT annual_facts row (the direct metrics' own raw_facts evidence). This is a floor, not a ceiling: a metric with a genuinely corroborating discrete fact (as already modeled for quarterly_facts) would add further 'corroborating' rows; none are counted here since annual-grain corroboration has not yet been catalogued metric-by-metric.
- **annual_lineage rows expected:** 384 -- one row per (derived annual_facts row) x (input metric it depends on), computed from config/metric_definitions.csv's own numerator_metrics/denominator_metrics fields, restricted to the persistable derived slots above.

### By metric (non-persistable exceptions only; all other metric x FY x view slots are persistable)

| Metric | Fiscal year | View | Status | Reason |
|---|---|---|---|---|
| shareholder_distributions_to_fcf | 2022 | as_filed | NOT_APPLICABLE | FCF negative under the approved shareholder_distributions_to_fcf policy |
| shareholder_distributions_to_fcf | 2022 | restated | NOT_APPLICABLE | FCF negative under the approved shareholder_distributions_to_fcf policy |

### Reclassification-affected metrics (view content genuinely differs, not just row count)

- **Direct:** cost_of_sales, operating_expenses, share_repurchases
- **Derived:** gross_margin, gross_profit, shareholder_distributions_to_fcf
Every other metric's two view-rows carry identical values, sharing the same underlying annual_fact_observations evidence -- per item 5's explicit instruction, this is still two distinct materialized rows (never a sparse override collapsing them into one).

### By fiscal year

| Fiscal year | Direct rows (both views) | Derived rows (both views) |
|---|---:|---:|
| 2021 | 60 | 38 |
| 2022 | 60 | 36 |
| 2023 | 60 | 38 |
| 2024 | 60 | 38 |
| 2025 | 60 | 38 |

### Observation and lineage type summary

- **selected:** the one annual_fact_observations row establishing a direct annual_facts row's own evidence -- exactly 1 per persisted direct row, as counted above.
- **corroborating / restated / conflicting:** not yet catalogued at annual grain; none assumed present or absent by this manifest -- a future persistence implementation must enumerate these explicitly per metric rather than default to zero.
- **source lineage (annual_lineage.input_raw_fact_id):** used when a derived fact's input is itself a raw XBRL fact rather than another annual_facts row -- not used by any of the 18 approved derived definitions today (every one lineages to other annual_facts rows via input_annual_fact_id), so 0 expected.
- **derivation lineage (annual_lineage.input_annual_fact_id):** 384 rows, as counted above.

---

**This document does not authorize persistence.** Per the 2026-09-15 approval round's explicit instruction: 'Do not persist annual facts yet.' scripts/clean_room_rebuild.py's annual-persistence step remains a documented TODO, and `data/curated/target_cash.db`'s annual_facts/annual_lineage/annual_fact_observations tables remain empty (verified by `target_cash seed-reference-data`'s own reported counts).
