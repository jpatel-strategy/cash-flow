/**
 * What-if sandbox formula engine.
 *
 * This is a line-for-line port of target_cash.forecast._run_from_metrics()
 * (src/target_cash/forecast.py), used ONLY by the illustrative What-If
 * Assumption Sandbox on this page. The "ground truth" numbers shown
 * everywhere else on this page (Snapshot, Forecast Explorer, Cash Bridge,
 * Waterfall, DCF) come directly from data/model_data.json, which is
 * computed once by the real Python model and never recomputed here.
 *
 * Keeping this in sync with forecast.py is a documented manual step (see
 * docs/decisions.md, Milestone 7 entry) -- it is not auto-generated.
 */
(function (global) {
  "use strict";

  const FORECAST_YEARS = [2026, 2027, 2028, 2029, 2030];

  function lookup(byYear, fy) {
    if (Object.prototype.hasOwnProperty.call(byYear, fy)) return byYear[fy];
    if (Object.prototype.hasOwnProperty.call(byYear, String(fy))) return byYear[String(fy)];
    throw new Error("No assumption value for fiscal year " + fy);
  }

  /**
   * seed: { revenue, diluted_shares, total_debt_gaap, inventory,
   *         accounts_payable, cash_and_equivalents_balance_sheet,
   *         dividends_paid }  -- all FY2025 actuals.
   * metrics: { metricKey: { fy: value } } for the 19 assumption metrics.
   * Returns an array of per-year result objects, FY2026-FY2030.
   */
  function runFromMetrics(seed, metrics) {
    const years = [];
    let prevRevenue = seed.revenue;
    let prevShares = seed.diluted_shares;
    let prevDebt = seed.total_debt_gaap;
    let prevInventory = seed.inventory;
    let prevAp = seed.accounts_payable;
    let prevCash = seed.cash_and_equivalents_balance_sheet;
    let prevDps = seed.dividends_paid / seed.diluted_shares;

    for (const fy of FORECAST_YEARS) {
      const growth = lookup(metrics.revenue_growth_pct, fy);
      const revenue = prevRevenue * (1 + growth / 100);

      const gm = lookup(metrics.gross_margin_pct, fy);
      const grossProfit = (revenue * gm) / 100;
      const costOfSales = revenue - grossProfit;

      const sgaPct = lookup(metrics.sga_pct_of_revenue, fy);
      const sgaExpense = (revenue * sgaPct) / 100;

      const daPct = lookup(metrics.da_pct_of_revenue, fy);
      const daOpex = (revenue * daPct) / 100;

      const operatingIncome = grossProfit - sgaExpense - daOpex;
      const operatingMarginPct = (operatingIncome / revenue) * 100;

      const debtProceeds = lookup(metrics.debt_proceeds_musd, fy);
      const debtRepayments = lookup(metrics.debt_repayments_musd, fy);
      const debtEnding = prevDebt + debtProceeds - debtRepayments;
      const interestRate = lookup(metrics.interest_rate_pct, fy);
      const interestExpense = ((interestRate / 100) * (prevDebt + debtEnding)) / 2;

      const netOtherIncome = lookup(metrics.net_other_income_musd, fy);
      const pretaxIncome = operatingIncome - interestExpense + netOtherIncome;

      const etr = lookup(metrics.effective_tax_rate_pct, fy);
      const tax = (pretaxIncome * etr) / 100;
      const netIncome = pretaxIncome - tax;

      const shareChg = lookup(metrics.diluted_share_change_pct, fy);
      const dilutedShares = prevShares * (1 + shareChg / 100);
      const dilutedEps = netIncome / dilutedShares;

      const daAddbackPct = lookup(metrics.da_cfo_addback_pct_of_revenue, fy);
      const daAddback = (revenue * daAddbackPct) / 100;

      const invPct = lookup(metrics.inventory_pct_of_revenue, fy);
      const inventoryBalance = (revenue * invPct) / 100;
      const inventoryCashImpact = -(inventoryBalance - prevInventory);

      const apPct = lookup(metrics.ap_pct_of_cogs, fy);
      const apBalance = (costOfSales * apPct) / 100;
      const apCashImpact = apBalance - prevAp;

      const otherOpcf = lookup(metrics.other_operating_cf_musd, fy);

      const cfo = netIncome + daAddback + inventoryCashImpact + apCashImpact + otherOpcf;

      const capexPct = lookup(metrics.capex_pct_of_revenue, fy);
      const capex = (revenue * capexPct) / 100;
      const fcf = cfo - capex;
      const investingCf = -capex;

      const divGrowth = lookup(metrics.dividend_per_share_growth_pct, fy);
      const dps = prevDps * (1 + divGrowth / 100);
      const dividendsPaid = dps * dilutedShares;

      const postDivFcf = fcf - dividendsPaid;
      const buybackPayout = lookup(metrics.buyback_payout_pct_of_post_dividend_fcf, fy);
      const shareRepurchases = Math.max(0, (postDivFcf * buybackPayout) / 100);

      const financingCf = -dividendsPaid - shareRepurchases + debtProceeds - debtRepayments;
      const netChangeCash = cfo + investingCf + financingCf;
      const beginningCash = prevCash;
      const endingCash = beginningCash + netChangeCash;

      const grossFcfCapacity = fcf;
      const postDividendCapacity = postDivFcf;
      const mandatoryFinancingFlows = -dividendsPaid + debtProceeds - debtRepayments;
      const preDiscretionaryEndingCash = beginningCash + cfo + investingCf + mandatoryFinancingFlows;
      const minCashBufferPct = lookup(metrics.min_cash_buffer_pct_of_revenue, fy);
      const minCashBuffer = (revenue * minCashBufferPct) / 100;
      const nearTermReserve = debtRepayments;
      const deployableCapacity = Math.max(
        0,
        preDiscretionaryEndingCash - minCashBuffer - nearTermReserve
      );
      const fundingWarning = endingCash < minCashBuffer;

      years.push({
        fiscal_year: fy,
        revenue, revenue_growth_pct: growth,
        cost_of_sales: costOfSales, gross_profit: grossProfit, gross_margin_pct: gm,
        sga_expense: sgaExpense, operating_income: operatingIncome, operating_margin_pct: operatingMarginPct,
        interest_expense: interestExpense, pretax_income: pretaxIncome, income_tax_expense: tax,
        net_income: netIncome, diluted_shares: dilutedShares, diluted_eps: dilutedEps,
        operating_cash_flow: cfo, capital_expenditure: capex, free_cash_flow: fcf,
        investing_cash_flow: investingCf, dividend_per_share: dps, dividends_paid: dividendsPaid,
        share_repurchases: shareRepurchases, financing_cash_flow: financingCf,
        beginning_cash: beginningCash, ending_cash: endingCash,
        post_dividend_capacity: postDividendCapacity, min_cash_buffer: minCashBuffer,
        deployable_capacity: deployableCapacity, funding_warning: fundingWarning,
        total_debt_gaap_ending: debtEnding,
        debt_proceeds: debtProceeds, debt_repayments: debtRepayments,
      });

      prevRevenue = revenue;
      prevShares = dilutedShares;
      prevDebt = debtEnding;
      prevInventory = inventoryBalance;
      prevAp = apBalance;
      prevCash = endingCash;
      prevDps = dps;
    }

    return years;
  }

  /**
   * Milestone 9 v2 finance-semantics correction: corrected capacity
   * taxonomy, computed from a full array of runFromMetrics() year objects
   * (needs the FOLLOWING year for the forward debt-repayment reserve) --
   * a line-for-line port of capacity_taxonomy.compute_capacity_taxonomy_year()
   * (Python). Never reads deployable_capacity; strategic_investment,
   * voluntary_debt_reduction, and other_discretionary_uses are structural
   * $0 placeholders, matching the Python source of truth.
   *
   * Gross debt issuance is never labeled capacity when simultaneously
   * repaid: debt_funded_incremental_capacity is the NET of proceeds over
   * repayments; net_mandatory_debt_service is the NET of repayments over
   * proceeds. self_funded_capacity_generated is a pure FLOW (excludes
   * opening_excess_liquidity, a STOCK, shown on its own line).
   */
  function calcNetMandatoryDebtService(proceeds, repayments) {
    return Math.max(0, repayments - proceeds);
  }

  function calcDebtFundedIncrementalCapacity(proceeds, repayments) {
    return Math.max(0, proceeds - repayments);
  }

  function computeCapacityTaxonomyYear(y, nextY) {
    const operatingFcf = y.free_cash_flow;
    const postDividendInternalGeneration = y.post_dividend_capacity;
    const openingExcessLiquidity = Math.max(0, y.beginning_cash - y.min_cash_buffer);

    const grossDebtProceeds = y.debt_proceeds;
    const grossDebtRepayments = y.debt_repayments;
    const netMandatoryDebtService = calcNetMandatoryDebtService(grossDebtProceeds, grossDebtRepayments);
    const debtFundedIncrementalCap = calcDebtFundedIncrementalCapacity(grossDebtProceeds, grossDebtRepayments);

    const selfFundedCapacityGenerated = postDividendInternalGeneration - netMandatoryDebtService;
    const totalGrossFundingCapacity = openingExcessLiquidity + selfFundedCapacityGenerated + debtFundedIncrementalCap;

    const strategicInvestment = 0;
    const voluntaryDebtReduction = 0;
    const otherDiscretionaryUses = 0;
    const totalDiscretionaryDeployment = y.share_repurchases + strategicInvestment + voluntaryDebtReduction + otherDiscretionaryUses;

    let forwardDebtRepaymentReserve, forwardReserveIsProxied;
    if (nextY) {
      forwardDebtRepaymentReserve = calcNetMandatoryDebtService(nextY.debt_proceeds, nextY.debt_repayments);
      forwardReserveIsProxied = false;
    } else {
      forwardDebtRepaymentReserve = netMandatoryDebtService; // documented proxy: FY2031 is out of scope
      forwardReserveIsProxied = true;
    }

    const remainingDeployableHeadroom = Math.max(
      0, totalGrossFundingCapacity - totalDiscretionaryDeployment - forwardDebtRepaymentReserve
    );
    const endingExcessLiquidity = Math.max(0, y.ending_cash - y.min_cash_buffer);

    // DEPRECATED-BY-v2 fields, kept only for parity with the Python schema; never displayed as "generated".
    const mandatoryDebtUses = netMandatoryDebtService;
    const selfFundedGrossCapacity = openingExcessLiquidity + selfFundedCapacityGenerated;

    return {
      fiscal_year: y.fiscal_year,
      operating_fcf: operatingFcf,
      post_dividend_internal_generation: postDividendInternalGeneration,
      opening_excess_liquidity: openingExcessLiquidity,
      gross_debt_proceeds: grossDebtProceeds,
      gross_debt_repayments: grossDebtRepayments,
      net_mandatory_debt_service: netMandatoryDebtService,
      self_funded_capacity_generated: selfFundedCapacityGenerated,
      debt_funded_incremental_capacity: debtFundedIncrementalCap,
      total_gross_funding_capacity: totalGrossFundingCapacity,
      share_repurchases: y.share_repurchases,
      strategic_investment: strategicInvestment,
      voluntary_debt_reduction: voluntaryDebtReduction,
      other_discretionary_uses: otherDiscretionaryUses,
      total_discretionary_deployment: totalDiscretionaryDeployment,
      forward_debt_repayment_reserve: forwardDebtRepaymentReserve,
      forward_reserve_is_proxied: forwardReserveIsProxied,
      remaining_deployable_headroom: remainingDeployableHeadroom,
      ending_excess_liquidity: endingExcessLiquidity,
      mandatory_debt_uses: mandatoryDebtUses,
      self_funded_gross_capacity: selfFundedGrossCapacity,
    };
  }

  function computeCapacityTaxonomyForYears(years) {
    return years.map((y, i) => computeCapacityTaxonomyYear(y, i + 1 < years.length ? years[i + 1] : null));
  }

  global.TargetCashFormulas = {
    FORECAST_YEARS, runFromMetrics, computeCapacityTaxonomyYear, computeCapacityTaxonomyForYears,
  };
})(window);
