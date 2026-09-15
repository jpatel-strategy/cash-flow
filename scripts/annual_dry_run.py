#!/usr/bin/env python3
"""Milestone 2 complete five-year annual dry run, both analytical views.

Reads ONLY raw_facts (already ingested, real data) and fiscal_calendar
(already seeded reference data) from the real curated database. Computes
every requested line item for FY2021-FY2025 under both AS_ORIGINALLY_FILED
and LATEST_RESTATED, classifies each cell DIRECT/DERIVED/BLOCKED/
UNAVAILABLE/NOT_APPLICABLE, and prints the result as JSON.

Writes NOTHING to the database -- no annual_facts/annual_lineage/
annual_fact_observations row is created. This is a pure read+compute dry
run, exactly like `target_cash.cli normalize` without --persist-derived.

Usage (from the repository root):
    .venv/bin/python scripts/annual_dry_run.py [--config config/model.yml]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from decimal import Decimal

TARGET_CIK = "0000027419"
FISCAL_YEARS = [2021, 2022, 2023, 2024, 2025]

# Concept mapping per metric. A value can be a fixed (taxonomy, tag) pair,
# or a callable(fiscal_year) -> (taxonomy, tag) for a tag that migrated
# across filing vintages (see docs/decisions.md, interest_expense /
# net_income tag-migration entries).
DURATION_METRICS: dict[str, object] = {
    "revenue": ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
    "cost_of_sales": ("us-gaap", "CostOfGoodsAndServicesSold"),
    "operating_expenses": ("us-gaap", "SellingGeneralAndAdministrativeExpense"),
    "depreciation_amortization_opex": ("us-gaap", "DepreciationAndAmortization"),
    "operating_income": ("us-gaap", "OperatingIncomeLoss"),
    "interest_expense": lambda fy: ("us-gaap", "InterestExpense") if fy <= 2023 else ("us-gaap", "InterestExpenseNonoperating"),
    "net_other_income": ("us-gaap", "OtherNonoperatingIncomeExpense"),
    "pretax_income": ("us-gaap", "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"),
    "income_tax_expense": ("us-gaap", "IncomeTaxExpenseBenefit"),
    "net_income": lambda fy: ("us-gaap", "NetIncomeLossAvailableToCommonStockholdersBasic") if fy == 2021 else ("us-gaap", "NetIncomeLoss"),
    "diluted_eps": ("us-gaap", "EarningsPerShareDiluted"),
    "diluted_shares": ("us-gaap", "WeightedAverageNumberOfDilutedSharesOutstanding"),
    "operating_cash_flow": ("us-gaap", "NetCashProvidedByUsedInOperatingActivities"),
    "investing_cash_flow": ("us-gaap", "NetCashProvidedByUsedInInvestingActivities"),
    "financing_cash_flow": ("us-gaap", "NetCashProvidedByUsedInFinancingActivities"),
    "capital_expenditure": ("us-gaap", "PaymentsToAcquirePropertyPlantAndEquipment"),
    "dividends_paid": ("us-gaap", "PaymentsOfDividendsCommonStock"),
    "share_repurchases": ("us-gaap", "PaymentsForRepurchaseOfCommonStock"),
    "debt_proceeds": ("us-gaap", "ProceedsFromIssuanceOfLongTermDebt"),
    "debt_repayments": ("us-gaap", "RepaymentsOfLongTermDebt"),
}

INSTANT_METRICS: dict[str, object] = {
    "cash_and_equivalents_balance_sheet": ("us-gaap", "CashCashEquivalentsAndShortTermInvestments"),
    "inventory": ("us-gaap", "InventoryNet"),
    "accounts_payable": ("us-gaap", "AccountsPayableCurrent"),
    "long_term_debt_gaap_carrying_value_noncurrent": ("us-gaap", "LongTermDebtAndCapitalLeaseObligations"),
    "long_term_debt_gaap_carrying_value_current": ("us-gaap", "LongTermDebtAndCapitalLeaseObligationsCurrent"),
    "debt_principal_schedule": ("us-gaap", "LongTermDebt"),
    "finance_lease_liability_current": ("us-gaap", "FinanceLeaseLiabilityCurrent"),
    "finance_lease_liability_noncurrent": ("us-gaap", "FinanceLeaseLiabilityNoncurrent"),
    "debt_fair_value_hedge_adjustment": ("tgt", "SwapValuationAdjustments"),
}


# Metrics whose raw_facts.value is already a true per-share/count figure
# (scale=0 or NULL), never in whole dollars -- must not be divided by 1e6.
UNSCALED_METRICS = {"diluted_eps"}


def q6(metric: str, x) -> float:
    if metric in UNSCALED_METRICS:
        return float(Decimal(x))
    return float(Decimal(x) / Decimal(1_000_000))


def fiscal_period(conn, fiscal_year: int) -> dict:
    row = conn.execute(
        "SELECT period_start, period_end, authority_accession, week_count, is_53_week_year "
        "FROM fiscal_calendar WHERE cik = ? AND fiscal_year = ? AND fiscal_quarter = 0",
        (TARGET_CIK, fiscal_year),
    ).fetchone()
    return dict(zip(("period_start", "period_end", "authority_accession", "week_count", "is_53_week_year"), row))


def duration_value(conn, taxonomy: str, tag: str, start_date: str, end_date: str, accession: str):
    row = conn.execute(
        "SELECT value, fact_id FROM raw_facts WHERE taxonomy=? AND tag=? AND start_date=? AND end_date=? "
        "AND accession_number=? AND dimensional_context IS NULL",
        (taxonomy, tag, start_date, end_date, accession),
    ).fetchone()
    return row


def instant_value(conn, taxonomy: str, tag: str, end_date: str, accession: str):
    row = conn.execute(
        "SELECT value, fact_id FROM raw_facts WHERE taxonomy=? AND tag=? AND end_date=? "
        "AND accession_number=? AND dimensional_context IS NULL AND start_date IS NULL",
        (taxonomy, tag, end_date, accession),
    ).fetchone()
    return row


def latest_restated_duration(conn, taxonomy: str, tag: str, start_date: str, end_date: str):
    """The value + accession from the most-recently-filed filing that reports
    this exact duration for this tag, among ALL filings (own primary period or
    a later comparative) -- picked by filed_at, not accession-number sort."""
    rows = conn.execute(
        """
        SELECT rf.value, rf.fact_id, rf.accession_number, f.filed_at
        FROM raw_facts rf JOIN filings f ON f.accession_number = rf.accession_number
        WHERE rf.taxonomy=? AND rf.tag=? AND rf.start_date=? AND rf.end_date=?
          AND rf.dimensional_context IS NULL
        ORDER BY f.filed_at DESC
        """,
        (taxonomy, tag, start_date, end_date),
    ).fetchall()
    return rows[0] if rows else None


def latest_restated_instant(conn, taxonomy: str, tag: str, end_date: str):
    rows = conn.execute(
        """
        SELECT rf.value, rf.fact_id, rf.accession_number, f.filed_at
        FROM raw_facts rf JOIN filings f ON f.accession_number = rf.accession_number
        WHERE rf.taxonomy=? AND rf.tag=? AND rf.end_date=?
          AND rf.dimensional_context IS NULL AND rf.start_date IS NULL
        ORDER BY f.filed_at DESC
        """,
        (taxonomy, tag, end_date),
    ).fetchall()
    return rows[0] if rows else None


def resolve_tag(spec, fiscal_year: int):
    return spec(fiscal_year) if callable(spec) else spec


def build_year(conn, fiscal_year: int) -> dict:
    period = fiscal_period(conn, fiscal_year)
    accession = period["authority_accession"]
    out = {"fiscal_year": fiscal_year, "period": period, "as_filed": {}, "restated": {}}

    for metric, spec in {**DURATION_METRICS}.items():
        taxonomy, tag = resolve_tag(spec, fiscal_year)
        as_filed_status, as_filed_value_ = "BLOCKED", None
        if accession:
            row = duration_value(conn, taxonomy, tag, period["period_start"], period["period_end"], accession)
            if row:
                as_filed_status, as_filed_value_ = "DIRECT", q6(metric, row[0])
        restated_status, restated_value_ = "UNAVAILABLE", None
        row = latest_restated_duration(conn, taxonomy, tag, period["period_start"], period["period_end"])
        if row:
            restated_status, restated_value_ = "DIRECT", q6(metric, row[0])
        out["as_filed"][metric] = {"status": as_filed_status, "value": as_filed_value_}
        out["restated"][metric] = {"status": restated_status, "value": restated_value_}

    for metric, spec in INSTANT_METRICS.items():
        taxonomy, tag = resolve_tag(spec, fiscal_year)
        as_filed_status, as_filed_value_ = "BLOCKED", None
        if accession:
            row = instant_value(conn, taxonomy, tag, period["period_end"], accession)
            if row:
                as_filed_status, as_filed_value_ = "DIRECT", q6(metric, row[0])
        restated_status, restated_value_ = "UNAVAILABLE", None
        row = latest_restated_instant(conn, taxonomy, tag, period["period_end"])
        if row:
            restated_status, restated_value_ = "DIRECT", q6(metric, row[0])
        out["as_filed"][metric] = {"status": as_filed_status, "value": as_filed_value_}
        out["restated"][metric] = {"status": restated_status, "value": restated_value_}

    return out


def derive(view: dict) -> dict:
    """Compute every DERIVED cell for one view (as_filed or restated) of one
    fiscal year, from the DIRECT cells already resolved in `view`."""
    def val(metric):
        cell = view.get(metric)
        return cell["value"] if cell and cell["status"] in ("DIRECT", "DERIVED") else None

    def set_derived(metric, value, status="DERIVED"):
        view[metric] = {"status": status if value is not None else "BLOCKED", "value": value}

    revenue, cogs = val("revenue"), val("cost_of_sales")
    gross_profit = None if None in (revenue, cogs) else revenue - cogs
    set_derived("gross_profit", gross_profit)
    set_derived("gross_margin_pct", None if None in (gross_profit, revenue) or revenue == 0 else round(100 * gross_profit / revenue, 2))

    oi, rev = val("operating_income"), val("revenue")
    set_derived("operating_margin_pct", None if None in (oi, rev) or rev == 0 else round(100 * oi / rev, 2))

    ni, rev2 = val("net_income"), val("revenue")
    set_derived("net_margin_pct", None if None in (ni, rev2) or rev2 == 0 else round(100 * ni / rev2, 2))

    tax, pretax = val("income_tax_expense"), val("pretax_income")
    set_derived("effective_tax_rate_pct", None if None in (tax, pretax) or pretax == 0 else round(100 * tax / pretax, 2))

    cfo, capex = val("operating_cash_flow"), val("capital_expenditure")
    fcf = None if None in (cfo, capex) else cfo - capex
    set_derived("fcf", fcf)
    set_derived("fcf_margin_pct", None if None in (fcf, rev) or rev == 0 else round(100 * fcf / rev, 2))

    cash = val("cash_and_equivalents_balance_sheet")
    ltd_nc = val("long_term_debt_gaap_carrying_value_noncurrent")
    cur_combined = val("long_term_debt_gaap_carrying_value_current")
    fl_cur = val("finance_lease_liability_current")
    fl_nc = val("finance_lease_liability_noncurrent")
    fin_leases = None if None in (fl_cur, fl_nc) else fl_cur + fl_nc
    set_derived("finance_lease_liabilities", fin_leases)

    ltd_carrying_total = None if None in (ltd_nc, cur_combined) else ltd_nc + cur_combined
    set_derived("long_term_debt_gaap_carrying_value", ltd_carrying_total)

    total_debt_excl = None if None in (ltd_carrying_total, fin_leases) else ltd_carrying_total - fin_leases
    set_derived("total_debt_gaap_excluding_separately_reported_leases", total_debt_excl)

    valuation_net_debt = None if None in (total_debt_excl, cash) else total_debt_excl - cash
    set_derived("valuation_net_debt_excluding_leases", valuation_net_debt)

    adjusted_net_debt = None if None in (ltd_carrying_total, cash) else ltd_carrying_total - cash
    set_derived("adjusted_net_debt_including_finance_leases", adjusted_net_debt)

    # target_defined_net_debt: NEVER derived, NEVER copied, NEVER zero -- permanently UNAVAILABLE/NOT_REPORTED.
    view["target_defined_net_debt"] = {"status": "UNAVAILABLE", "value": None,
                                        "note": "Target discloses no net-debt measure of its own; never populated."}

    # Debt bridge check (principal + hedge adj + finance leases - current = noncurrent carrying value).
    principal = val("debt_principal_schedule")
    hedge_adj = val("debt_fair_value_hedge_adjustment")
    bridge_result = None
    if None not in (principal, hedge_adj, fin_leases, cur_combined, ltd_nc):
        bridge_computed = principal + hedge_adj + fin_leases - cur_combined
        bridge_result = "PASS" if abs(bridge_computed - ltd_nc) < 0.5 else "FAIL"
    view["debt_bridge_check"] = {"status": bridge_result or "BLOCKED", "value": None}

    # Distributions % FCF.
    dividends, repurch = val("dividends_paid"), val("share_repurchases")
    if fcf is not None and fcf > 0 and None not in (dividends, repurch):
        set_derived("distributions_pct_fcf", round(100 * (dividends + repurch) / fcf, 2))
    elif fcf is not None and fcf <= 0:
        view["distributions_pct_fcf"] = {"status": "NOT_APPLICABLE", "value": None}
    else:
        view["distributions_pct_fcf"] = {"status": "UNAVAILABLE", "value": None}

    return view


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/curated/target_cash.db")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    result = {}
    for fy in FISCAL_YEARS:
        year_data = build_year(conn, fy)
        year_data["as_filed"] = derive(year_data["as_filed"])
        year_data["restated"] = derive(year_data["restated"])
        result[fy] = year_data
    conn.close()

    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
