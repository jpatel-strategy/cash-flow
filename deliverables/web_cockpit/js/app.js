(function () {
  "use strict";

  const { lineChart, barChart, waterfallChart, fmtM } = window.TargetCashCharts;
  const { runFromMetrics, computeCapacityTaxonomyForYears } = window.TargetCashFormulas;

  const SCENARIO_COLORS = { base: "#1F3864", upside: "#548235", downside: "#C00000" };

  let DATA = null;
  let currentScenario = "base";
  let currentWaterfallYear = 2030;

  function fmtPct(v, digits = 1) {
    if (v === null || v === undefined || Number.isNaN(v)) return "—";
    return v.toFixed(digits) + "%";
  }
  function fmtNum(v, digits = 2) {
    if (v === null || v === undefined || Number.isNaN(v)) return "—";
    return v.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
  }

  function el(tag, attrs = {}, children = []) {
    const node = document.createElement(tag);
    for (const k in attrs) {
      if (k === "text") node.textContent = attrs[k];
      else if (k === "html") node.innerHTML = attrs[k];
      else node.setAttribute(k, attrs[k]);
    }
    (Array.isArray(children) ? children : [children]).forEach((c) => c && node.appendChild(c));
    return node;
  }

  function renderTable(table, headers, rows) {
    table.innerHTML = "";
    const caption = table.dataset.caption;
    if (caption) table.appendChild(el("caption", { text: caption }));
    const thead = el("thead", {}, el("tr", {}, headers.map((h) => el("th", { text: h }))));
    table.appendChild(thead);
    const tbody = el("tbody");
    rows.forEach((row) => {
      const tr = el("tr");
      row.forEach((cell) => {
        const text = typeof cell === "object" ? cell.text : cell;
        const cls = typeof cell === "object" ? cell.className : null;
        const style = typeof cell === "object" ? cell.style : null;
        const td = el("td", { text });
        if (cls) td.className = cls;
        if (style) td.setAttribute("style", style);
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
  }

  function kpiCard(label, value, context) {
    return el("div", { class: "kpi-card" }, [
      el("div", { class: "kpi-label", text: label }),
      el("div", { class: "kpi-value", text: value }),
      context ? el("div", { class: "kpi-context", text: context }) : null,
    ]);
  }

  // ---------------------------------------------------------------------
  // Header
  // ---------------------------------------------------------------------
  function renderHeader() {
    const badges = document.getElementById("header-badges");
    badges.innerHTML = "";
    const v = DATA.validation;
    const capCheck = v.capacity_taxonomy || { total: 0, PASS: 0 };
    const totalChecks = v.forecast.total + v.valuation.total + capCheck.total;
    const totalPass = v.forecast.PASS + v.valuation.PASS + capCheck.PASS;
    badges.appendChild(el("span", { class: "badge status-historical", text: "Historical: SEC-filed, FY2021–FY2025" }));
    badges.appendChild(el("span", { class: "badge status-forecast", text: "Forecast: scenario-based, FY2026–FY2030" }));
    badges.appendChild(el("span", { class: "badge status-not-advice", text: "Not investment advice" }));
    badges.appendChild(el("span", { class: "badge", text: `Cutoff: ${DATA.information_cutoff}` }));
    badges.appendChild(el("span", { class: "badge", text: `Validation: ${totalPass}/${totalChecks} PASS` }));
    document.getElementById("footer-cutoff").textContent = DATA.information_cutoff;
  }

  // ---------------------------------------------------------------------
  // 1. Snapshot
  // ---------------------------------------------------------------------
  function renderSnapshot() {
    const sc = DATA.scenarios[currentScenario];
    const years = sc.years;
    const terminal = years[years.length - 1];
    const dcf = DATA.valuation.results[currentScenario];

    const grid = document.getElementById("kpi-grid");
    grid.innerHTML = "";
    const capCheck = DATA.validation.capacity_taxonomy || { total: 0, PASS: 0 };
    const totalPass = DATA.validation.forecast.PASS + DATA.validation.valuation.PASS + capCheck.PASS;
    const totalChecks = DATA.validation.forecast.total + DATA.validation.valuation.total + capCheck.total;
    grid.appendChild(kpiCard("Revenue, FY2030", fmtM(terminal.revenue), `${currentScenario} scenario`));
    grid.appendChild(kpiCard("Free Cash Flow, FY2030", fmtM(terminal.free_cash_flow), "CFO − CapEx"));
    grid.appendChild(kpiCard("Implied DCF Value/Share", "$" + fmtNum(dcf.implied_value_per_share), "scenario-based, not a price target"));
    grid.appendChild(kpiCard("Validation Status", `${totalPass}/${totalChecks} PASS`, "all checks"));
    grid.appendChild(kpiCard("Net Debt (Valuation Date)", fmtM(dcf.valuation_date_net_debt), "FY2025 actual"));
    grid.appendChild(kpiCard("Funding Warning?", terminal.funding_warning ? "Yes" : "No", `${currentScenario}, FY2030`));

    const capGrid = document.getElementById("capacity-kpi-grid");
    capGrid.innerHTML = "";
    const capTerminal = sc.capacity_taxonomy_by_year[String(terminal.fiscal_year)];
    capGrid.appendChild(kpiCard("Opening Excess Liquidity", fmtM(capTerminal.opening_excess_liquidity), "a STOCK carried forward — never labeled 'generated'"));
    capGrid.appendChild(kpiCard("Self-Funded Capacity Generated", fmtM(capTerminal.self_funded_capacity_generated), "this period's flow only, excludes the opening stock and nets mandatory debt service"));
    capGrid.appendChild(kpiCard("Debt-Funded Capacity", fmtM(capTerminal.debt_funded_incremental_capacity), "net of simultaneous repayment — gross issuance that is repaid is never capacity"));
    capGrid.appendChild(kpiCard("Discretionary Deployment", fmtM(capTerminal.total_discretionary_deployment), "repurchases + other discretionary uses"));
    capGrid.appendChild(kpiCard("Remaining Deployable Headroom", fmtM(capTerminal.remaining_deployable_headroom), "net of deployment AND a forward debt-repayment reserve"));

    const histSeries = DATA.historical_years.map((fy) => ({
      fy: Number(fy), value: DATA.historical[fy].revenue,
    }));
    const fcstSeries = years.map((y) => ({ fy: y.fiscal_year, value: y.revenue }));
    const histFcf = DATA.historical_years.map((fy) => ({ fy: Number(fy), value: DATA.historical[fy].free_cash_flow }));
    const fcstFcf = years.map((y) => ({ fy: y.fiscal_year, value: y.free_cash_flow }));

    lineChart(document.getElementById("chart-revenue-fcf"), {
      series: [
        { label: "Revenue (actual)", points: histSeries, color: "#1F3864" },
        { label: "Revenue (forecast)", points: [histSeries[histSeries.length - 1], ...fcstSeries], color: "#1F3864", dashed: true },
        { label: "FCF (actual)", points: histFcf, color: "#C9A227" },
        { label: "FCF (forecast)", points: [histFcf[histFcf.length - 1], ...fcstFcf], color: "#C9A227", dashed: true },
      ],
    });

    const capBars = ["base", "upside", "downside"].map((s) => {
      const sYears = DATA.scenarios[s].years;
      const sTerminalFy = sYears[sYears.length - 1].fiscal_year;
      return {
        label: s.charAt(0).toUpperCase() + s.slice(1),
        value: DATA.scenarios[s].capacity_taxonomy_by_year[String(sTerminalFy)].remaining_deployable_headroom,
        color: SCENARIO_COLORS[s],
      };
    });
    barChart(document.getElementById("chart-capacity-by-scenario"), { bars: capBars });
    document.getElementById("capacity-note").textContent =
      "A higher-revenue scenario can show LOWER headroom if it deploys more (see Upside) — check Discretionary Deployment in the Cash Bridge section before assuming a lower bar means less capacity was generated.";

    document.getElementById("scenario-narrative-snapshot").textContent = sc.narrative;
  }

  // ---------------------------------------------------------------------
  // 2. Historical
  // ---------------------------------------------------------------------
  function renderHistorical() {
    const years = DATA.historical_years;
    lineChart(document.getElementById("chart-historical"), {
      series: [
        { label: "Revenue", points: years.map((fy) => ({ fy: Number(fy), value: DATA.historical[fy].revenue })), color: "#1F3864" },
        { label: "Gross Profit", points: years.map((fy) => ({ fy: Number(fy), value: DATA.historical[fy].gross_profit })), color: "#C9A227" },
        { label: "Operating Income", points: years.map((fy) => ({ fy: Number(fy), value: DATA.historical[fy].operating_income })), color: "#2E75B6" },
        { label: "Net Income", points: years.map((fy) => ({ fy: Number(fy), value: DATA.historical[fy].net_income })), color: "#548235" },
      ],
    });

    const metrics = [
      ["Revenue", "revenue"], ["Cost of Sales", "cost_of_sales"], ["Gross Profit", "gross_profit"],
      ["Gross Margin %", "gross_margin"], ["Operating Income", "operating_income"], ["Operating Margin %", "operating_margin"],
      ["Net Income", "net_income"], ["Diluted EPS ($)", "diluted_eps"], ["CFO", "operating_cash_flow"],
      ["CapEx (property & equipment only)", "capital_expenditure"], ["Investing Cash Flow (total)", "investing_cash_flow"],
      ["Free Cash Flow", "free_cash_flow"], ["Dividends Paid", "dividends_paid"], ["Share Repurchases", "share_repurchases"],
      ["Total Debt (GAAP)", "total_debt_gaap"], ["Cash & Equivalents", "cash_and_equivalents_balance_sheet"],
    ];
    const table = document.getElementById("table-historical");
    table.dataset.caption = "Historical annual facts, latest-restated view, all $ millions unless noted";
    const rows = metrics.map(([label, key]) => [
      label,
      ...years.map((fy) => {
        const v = DATA.historical[fy][key];
        if (v === undefined) return "—";
        return key.includes("margin") || key === "diluted_eps" ? fmtNum(v, key === "diluted_eps" ? 2 : 2) : fmtM(v);
      }),
    ]);
    renderTable(table, ["Metric", ...years.map((y) => "FY" + y)], rows);
  }

  // ---------------------------------------------------------------------
  // 3. Cash-flow definitions
  // ---------------------------------------------------------------------
  function renderCashDefinitions() {
    const h = DATA.historical["2025"];
    const grid = document.getElementById("cash-definitions-grid");
    grid.innerHTML = "";
    const defs = [
      ["CFO", h.operating_cash_flow, "Cash Flow from Operations — the full operating section of the cash-flow statement."],
      ["CapEx", h.capital_expenditure, "Property-and-equipment acquisitions only — never total investing cash flow."],
      ["CFI (Total Investing CF)", h.investing_cash_flow, "All investing activities combined (CapEx plus everything else investing) — always a separate, larger-magnitude figure than CapEx alone."],
      ["FCF (CFO − CapEx)", h.free_cash_flow, "Free cash flow, defined strictly as CFO minus CapEx — not CFO plus CFI."],
    ];
    defs.forEach(([label, value, note]) => {
      grid.appendChild(
        el("div", { class: "definition-card" }, [
          el("h4", { text: label }),
          el("div", { class: "value", text: fmtM(value) }),
          el("p", { text: note }),
        ])
      );
    });
  }

  // ---------------------------------------------------------------------
  // 4. Forecast explorer
  // ---------------------------------------------------------------------
  function renderForecast() {
    const years = DATA.scenarios[currentScenario].years;
    lineChart(document.getElementById("chart-forecast-income"), {
      series: [
        { label: "Revenue", points: years.map((y) => ({ fy: y.fiscal_year, value: y.revenue })), color: "#1F3864", dashed: true },
        { label: "Gross Profit", points: years.map((y) => ({ fy: y.fiscal_year, value: y.gross_profit })), color: "#C9A227", dashed: true },
        { label: "Operating Income", points: years.map((y) => ({ fy: y.fiscal_year, value: y.operating_income })), color: "#2E75B6", dashed: true },
        { label: "Net Income", points: years.map((y) => ({ fy: y.fiscal_year, value: y.net_income })), color: "#548235", dashed: true },
      ],
    });
    lineChart(document.getElementById("chart-forecast-margins"), {
      series: [
        { label: "Diluted EPS ($)", points: years.map((y) => ({ fy: y.fiscal_year, value: y.diluted_eps })), color: "#1F3864", dashed: true },
        { label: "Gross Margin %", points: years.map((y) => ({ fy: y.fiscal_year, value: y.gross_margin_pct })), color: "#C9A227", dashed: true },
        { label: "Operating Margin %", points: years.map((y) => ({ fy: y.fiscal_year, value: y.operating_margin_pct })), color: "#2E75B6", dashed: true },
      ],
    });

    const metrics = [
      ["Revenue", "revenue"], ["Revenue Growth %", "revenue_growth_pct"], ["Gross Profit", "gross_profit"],
      ["Gross Margin %", "gross_margin_pct"], ["Operating Income", "operating_income"], ["Operating Margin %", "operating_margin_pct"],
      ["Net Income", "net_income"], ["Diluted EPS ($)", "diluted_eps"], ["CFO", "operating_cash_flow"],
      ["CapEx", "capital_expenditure"], ["Free Cash Flow", "free_cash_flow"], ["Dividends Paid", "dividends_paid"],
      ["Share Repurchases", "share_repurchases"], ["Ending Cash", "ending_cash"],
      ["Legacy Gross Capacity (deprecated)", "deployable_capacity"],
    ];
    const table = document.getElementById("table-forecast");
    table.dataset.caption = `Full scenario forecast — ${currentScenario} scenario, $ millions unless noted`;
    const rows = metrics.map(([label, key]) => [
      label,
      ...years.map((y) => {
        const v = y[key];
        return key.includes("pct") || key === "diluted_eps" ? fmtNum(v, key === "diluted_eps" ? 2 : 2) : fmtM(v);
      }),
    ]);
    renderTable(table, ["Metric", ...years.map((y) => "FY" + y.fiscal_year)], rows);
  }

  // ---------------------------------------------------------------------
  // 5. Cash bridge & investment capacity
  // ---------------------------------------------------------------------
  function renderBridge() {
    const sc = DATA.scenarios[currentScenario];
    const years = sc.years;
    const terminal = years[years.length - 1];
    const capYears = years.map((y) => sc.capacity_taxonomy_by_year[String(y.fiscal_year)]);
    const capTerminal = capYears[capYears.length - 1];

    // Legacy waterfall (deprecated) -- preserved verbatim for backward compatibility.
    waterfallChart(document.getElementById("chart-bridge"), {
      steps: [
        { label: "CFO", amount: terminal.operating_cash_flow },
        { label: "− CapEx", amount: -terminal.capital_expenditure },
        { label: "= FCF", amount: terminal.free_cash_flow, isTotal: true },
        { label: "− Dividends", amount: -terminal.dividends_paid },
        { label: "= Post-Dividend Capacity", amount: terminal.post_dividend_capacity, isTotal: true },
        { label: "− Min-Cash Buffer", amount: -terminal.min_cash_buffer },
        { label: "− Debt Reserve", amount: -terminal.near_term_debt_repayment_reserve },
        { label: "= Legacy Gross Ceiling (DEPRECATED)", amount: terminal.deployable_capacity, isTotal: true },
      ],
    });

    // Corrected (v2) capacity taxonomy waterfall -- opening liquidity (a STOCK)
    // is its own line, never blended into "capacity generated"; debt is shown
    // NET of simultaneous repayment; the forward debt-repayment reserve is
    // held back before the residual is called "headroom."
    waterfallChart(document.getElementById("chart-capacity-taxonomy"), {
      steps: [
        { label: "Opening Excess Liquidity (STOCK)", amount: capTerminal.opening_excess_liquidity, isTotal: true },
        { label: "+ Self-Funded Capacity Generated (B − net debt service)", amount: capTerminal.self_funded_capacity_generated },
        { label: "+ Debt-Funded Capacity (net of simultaneous repayment)", amount: capTerminal.debt_funded_incremental_capacity },
        { label: "= Total Gross Funding Capacity", amount: capTerminal.total_gross_funding_capacity, isTotal: true },
        { label: "− Discretionary Deployment", amount: -capTerminal.total_discretionary_deployment },
        { label: "− Forward Debt-Repayment Reserve", amount: -capTerminal.forward_debt_repayment_reserve },
        { label: "= Remaining Deployable Headroom", amount: capTerminal.remaining_deployable_headroom, isTotal: true },
      ],
    });

    lineChart(document.getElementById("chart-capacity-series"), {
      series: [
        { label: "Remaining Deployable Headroom", points: capYears.map((cy) => ({ fy: cy.fiscal_year, value: cy.remaining_deployable_headroom })), color: "#1F3864" },
        { label: "Discretionary Deployment (same year)", points: capYears.map((cy) => ({ fy: cy.fiscal_year, value: cy.total_discretionary_deployment })), color: "#C9A227" },
      ],
    });

    const horizonTable = document.getElementById("table-capacity-horizon");
    const hz = sc.capacity_horizon_summary;
    renderTable(
      horizonTable,
      ["Metric", "Value"],
      [
        ["Cumulative Self-Funded Generation", fmtM(hz.cumulative_self_funded_generation)],
        ["Cumulative Debt-Funded Capacity", fmtM(hz.cumulative_debt_funded_capacity)],
        ["Opening Excess Liquidity (horizon start)", fmtM(hz.opening_excess_liquidity_at_horizon_start)],
        ["Cumulative Discretionary Deployment", fmtM(hz.cumulative_discretionary_deployment)],
        ["Terminal Remaining Headroom (FY2030)", fmtM(hz.terminal_remaining_headroom)],
        ["Ending Reserve Movement", fmtM(hz.ending_reserve_movement)],
        ["Terminal Forward Debt-Repayment Reserve (FY2031 proxy)", fmtM(hz.terminal_forward_debt_repayment_reserve)],
        [{ text: "Total Horizon Capacity Accessible", className: "reclassified" }, { text: fmtM(hz.total_horizon_capacity_accessible), className: "reclassified" }],
      ]
    );

    const table = document.getElementById("table-capacity");
    table.dataset.caption = `Corrected (v2) capacity taxonomy detail — ${currentScenario} scenario (legacy/deprecated fields shown at bottom)`;
    const metrics = [
      ["A. Operating FCF", "operating_fcf"], ["B. Post-Dividend Internal Generation", "post_dividend_internal_generation"],
      ["Opening Excess Liquidity (STOCK)", "opening_excess_liquidity"],
      ["Gross Debt Proceeds (supporting)", "gross_debt_proceeds"], ["Gross Debt Repayments (supporting)", "gross_debt_repayments"],
      ["Net Mandatory Debt Service", "net_mandatory_debt_service"],
      ["C. Self-Funded Capacity Generated (excludes opening liquidity)", "self_funded_capacity_generated"],
      ["D. Debt-Funded Incremental Capacity (net of repayment)", "debt_funded_incremental_capacity"],
      ["E. Total Gross Funding Capacity", "total_gross_funding_capacity"], ["Share Repurchases", "share_repurchases"],
      ["F. Total Discretionary Deployment", "total_discretionary_deployment"],
      ["Forward Debt-Repayment Reserve", "forward_debt_repayment_reserve"],
      ["G. Remaining Deployable Headroom", "remaining_deployable_headroom"],
      ["Ending Excess Liquidity (cross-check: G = this − forward reserve)", "ending_excess_liquidity"],
    ];
    const rows = metrics.map(([label, key]) => [label, ...capYears.map((cy) => fmtM(cy[key]))]);
    rows.push([
      { text: "Legacy Gross Pre-Discretionary Ceiling (DEPRECATED, v1)", className: "reclassified" },
      ...years.map((y) => ({ text: fmtM(y.deployable_capacity), className: "reclassified" })),
    ]);
    rows.push([
      { text: "Deprecated: Self-Funded Gross Capacity incl. opening stock (v1-style, never labeled 'generated')", className: "reclassified" },
      ...capYears.map((cy) => ({ text: fmtM(cy.self_funded_gross_capacity), className: "reclassified" })),
    ]);
    renderTable(table, ["Metric", ...years.map((y) => "FY" + y.fiscal_year)], rows);
  }

  // ---------------------------------------------------------------------
  // 6. Capital allocation waterfall
  // ---------------------------------------------------------------------
  function renderWaterfallYearSelector() {
    const container = document.getElementById("waterfall-year-selector");
    container.innerHTML = "";
    DATA.forecast_years.forEach((fy) => {
      const btn = el("button", { type: "button", "aria-pressed": String(fy === currentWaterfallYear), text: "FY" + fy });
      btn.addEventListener("click", () => {
        currentWaterfallYear = fy;
        renderWaterfallYearSelector();
        renderWaterfall();
      });
      container.appendChild(btn);
    });
  }

  function renderWaterfall() {
    const sc = DATA.scenarios[currentScenario];
    const steps = sc.waterfall_by_year[String(currentWaterfallYear)];
    waterfallChart(document.getElementById("chart-waterfall"), {
      steps: steps.map((s) => ({
        label: String(s.label).split("(")[0].trim(),
        amount: s.amount,
        isTotal: s.step === 8,
      })).filter((s) => s.amount !== 0 || s.isTotal),
    });

    const proof = sc.no_double_counting[String(currentWaterfallYear)];
    const banner = document.getElementById("no-double-count-banner");
    const holds = proof.no_double_counting_proven;
    banner.className = "proof-banner " + (holds ? "ok" : "mismatch");
    banner.textContent = holds
      ? `No-Double-Counting Proof: OK — every dollar of ${currentScenario} FY${currentWaterfallYear} cash flow is accounted for exactly once across sources and uses.`
      : `No-Double-Counting Proof: MISMATCH detected for ${currentScenario} FY${currentWaterfallYear} — investigate before trusting this scenario/year.`;
  }

  // ---------------------------------------------------------------------
  // 7. DCF valuation
  // ---------------------------------------------------------------------
  function renderDcf() {
    const result = DATA.valuation.results[currentScenario];
    const asmByMetric = {};
    DATA.valuation.assumptions.forEach((a) => (asmByMetric[a.metric] = a));

    const waccTable = document.getElementById("table-wacc");
    waccTable.dataset.caption = "WACC build (identical across all 3 scenarios)";
    renderTable(
      waccTable,
      ["Component", "Value"],
      [
        ["Risk-Free Rate", fmtPct(asmByMetric.risk_free_rate_pct.value)],
        ["Equity Risk Premium", fmtPct(asmByMetric.equity_risk_premium_pct.value)],
        ["Beta", fmtNum(asmByMetric.beta.value)],
        ["Cost of Debt (pre-tax)", fmtPct(asmByMetric.cost_of_debt_pct.value)],
        ["Tax Rate (for WACC)", fmtPct(asmByMetric.tax_rate_for_wacc_pct.value)],
        ["Equity Weight", fmtPct(asmByMetric.target_equity_weight_pct.value)],
        ["Debt Weight", fmtPct(asmByMetric.target_debt_weight_pct.value)],
        ["Terminal Growth", fmtPct(asmByMetric.terminal_growth_pct.value)],
        ["WACC", { text: fmtPct(DATA.valuation.wacc_pct, 2), className: "reclassified" }],
      ]
    );

    waterfallChart(document.getElementById("chart-valuation-bridge"), {
      steps: result.bridge
        .filter((s) => s.step <= 5) // steps 6-7 are a division into $/share, a different unit than $M -- shown separately below
        .map((s) => ({
          label: s.label.replace(/^[=+\-/]\s*/, ""),
          amount: s.value,
          isTotal: [3, 5].includes(s.step),
        })),
    });
    document.getElementById("chart-valuation-bridge").parentElement.querySelector(".chart-note")?.remove();
    document.getElementById("chart-valuation-bridge").insertAdjacentHTML(
      "afterend",
      `<p class="chart-note">Equity Value ÷ Diluted Shares (${fmtNum(result.valuation_date_diluted_shares, 1)}M, FY2025 actual) = <strong>$${fmtNum(result.implied_value_per_share)} implied value per share</strong>. Shown separately because $/share is a different unit than the $M bars above.</p>`
    );

    const waccGrid = DATA.valuation.wacc_terminal_growth_sensitivity.grid;
    const waccDeltas = DATA.valuation.wacc_terminal_growth_sensitivity.wacc_deltas || waccGrid.map((r) => r.wacc_delta);
    const growthLabels = waccGrid[0].cells.map((c) => c.terminal_growth_delta ?? c.growth_delta ?? "");
    const waccTableEl = document.getElementById("table-wacc-sensitivity");
    waccTableEl.dataset.caption = "Rows: WACC delta (pp); Columns: terminal growth delta (pp)";
    const values = waccGrid.flatMap((r) => r.cells.map((c) => c.implied_value_per_share).filter((v) => v !== null));
    const vMin = Math.min(...values), vMax = Math.max(...values);
    renderTable(
      waccTableEl,
      ["WACC Δ \\ Growth Δ", ...growthLabels.map((g) => (g >= 0 ? "+" : "") + g)],
      waccGrid.map((row) => [
        (row.wacc_delta >= 0 ? "+" : "") + row.wacc_delta,
        ...row.cells.map((c) => heatCell(c.implied_value_per_share, vMin, vMax)),
      ])
    );

    const mgGrid = DATA.valuation.operating_margin_revenue_growth_sensitivity.grid;
    const mgGrowthLabels = mgGrid[0].cells.map((c) => c.revenue_growth_delta ?? "");
    const mgTableEl = document.getElementById("table-margin-sensitivity");
    mgTableEl.dataset.caption = "Rows: gross margin delta (pp); Columns: revenue growth delta (pp)";
    const mgValues = mgGrid.flatMap((r) => r.cells.map((c) => c.implied_value_per_share).filter((v) => v !== null));
    const mgMin = Math.min(...mgValues), mgMax = Math.max(...mgValues);
    renderTable(
      mgTableEl,
      ["Margin Δ \\ Growth Δ", ...mgGrowthLabels.map((g) => (g >= 0 ? "+" : "") + g)],
      mgGrid.map((row) => [
        (row.gross_margin_delta >= 0 ? "+" : "") + row.gross_margin_delta,
        ...row.cells.map((c) => heatCell(c.implied_value_per_share, mgMin, mgMax)),
      ])
    );
  }

  function heatCell(value, min, max) {
    if (value === null || value === undefined) return { text: "n/a (growth ≥ WACC)", className: "cell" };
    const t = (value - min) / (max - min || 1);
    const r = Math.round(255 - t * (255 - 31));
    const g = Math.round(242 - t * (242 - 86));
    const b = Math.round(204 - t * (204 - 128));
    return { text: "$" + fmtNum(value, 0), className: "cell", style: `background: rgb(${r},${g},${b})` };
  }

  // ---------------------------------------------------------------------
  // 8. What-if sandbox
  // ---------------------------------------------------------------------
  const SLIDERS = [
    { key: "revenue_growth_pct", label: "Revenue Growth % (Δ, all forecast years)", range: [-3, 3], step: 0.1 },
    { key: "gross_margin_pct", label: "Gross Margin % (Δ, all forecast years)", range: [-2, 2], step: 0.1 },
    { key: "capex_pct_of_revenue", label: "CapEx % of Revenue (Δ)", range: [-1, 1], step: 0.05 },
    { key: "buyback_payout_pct_of_post_dividend_fcf", label: "Buyback Payout % of Post-Dividend FCF (Δ)", range: [-30, 30], step: 1 },
    { key: "dividend_per_share_growth_pct", label: "Dividend/Share Growth % (Δ)", range: [-5, 5], step: 0.5 },
    { key: "min_cash_buffer_pct_of_revenue", label: "Minimum Cash Buffer % of Revenue (Δ)", range: [-1, 1], step: 0.1 },
  ];
  let sliderDeltas = {};

  function resetSliders() {
    sliderDeltas = {};
    SLIDERS.forEach((s) => (sliderDeltas[s.key] = 0));
  }

  function renderWhatIfControls() {
    const container = document.getElementById("whatif-controls");
    container.innerHTML = "";
    SLIDERS.forEach((s) => {
      const valueSpan = el("span", { class: "whatif-value", text: sliderDeltas[s.key].toFixed(2) });
      const input = el("input", {
        type: "range", min: s.range[0], max: s.range[1], step: s.step, value: sliderDeltas[s.key],
      });
      input.addEventListener("input", () => {
        sliderDeltas[s.key] = parseFloat(input.value);
        valueSpan.textContent = (sliderDeltas[s.key] >= 0 ? "+" : "") + sliderDeltas[s.key].toFixed(2);
        recomputeWhatIf();
      });
      container.appendChild(
        el("div", { class: "whatif-control" }, [
          el("label", {}, [document.createTextNode(s.label + " "), valueSpan]),
          input,
        ])
      );
    });
  }

  function recomputeWhatIf() {
    const sc = DATA.scenarios[currentScenario];
    const seed = {
      revenue: DATA.historical["2025"].revenue,
      diluted_shares: DATA.historical["2025"].diluted_shares,
      total_debt_gaap: DATA.historical["2025"].total_debt_gaap,
      inventory: DATA.historical["2025"].inventory,
      accounts_payable: DATA.historical["2025"].accounts_payable,
      cash_and_equivalents_balance_sheet: DATA.historical["2025"].cash_and_equivalents_balance_sheet,
      dividends_paid: DATA.historical["2025"].dividends_paid,
    };

    const metrics = {};
    for (const key in sc.assumptions) {
      metrics[key] = {};
      for (const fy of DATA.forecast_years) {
        let v = sc.assumptions[key][String(fy)];
        if (sliderDeltas[key] !== undefined) v += sliderDeltas[key];
        metrics[key][fy] = v;
      }
    }

    const result = runFromMetrics(seed, metrics);
    const terminal = result[result.length - 1];
    const capYears = computeCapacityTaxonomyForYears(result);
    const capTerminal = capYears[capYears.length - 1];

    const out = document.getElementById("whatif-results");
    out.innerHTML = "";
    out.appendChild(kpiCard("FY2030 Revenue", fmtM(terminal.revenue)));
    out.appendChild(kpiCard("FY2030 Free Cash Flow", fmtM(terminal.free_cash_flow)));
    out.appendChild(kpiCard("FY2030 Opening Excess Liquidity", fmtM(capTerminal.opening_excess_liquidity)));
    out.appendChild(kpiCard("FY2030 Self-Funded Capacity Generated", fmtM(capTerminal.self_funded_capacity_generated)));
    out.appendChild(kpiCard("FY2030 Debt-Funded Capacity", fmtM(capTerminal.debt_funded_incremental_capacity)));
    out.appendChild(kpiCard("FY2030 Discretionary Deployment", fmtM(capTerminal.total_discretionary_deployment)));
    out.appendChild(kpiCard("FY2030 Remaining Deployable Headroom", fmtM(capTerminal.remaining_deployable_headroom)));
    out.appendChild(kpiCard("FY2030 Diluted EPS", "$" + fmtNum(terminal.diluted_eps)));
    out.appendChild(kpiCard("FY2030 Ending Cash", fmtM(terminal.ending_cash)));
    out.appendChild(kpiCard("Funding Warning?", terminal.funding_warning ? "Yes" : "No"));
  }

  // ---------------------------------------------------------------------
  // 9. Evidence & sources
  // ---------------------------------------------------------------------
  function renderEvidence() {
    const srcTable = document.getElementById("table-sources");
    srcTable.dataset.caption = "Every SEC filing this project is built from";
    renderTable(
      srcTable,
      ["Accession #", "Form", "Filed", "Period of Report", "URL"],
      DATA.sources.map((s) => [
        s.accession_number, s.form_type, s.filed_at, s.period_of_report,
        { text: "Source ↗", className: "" },
      ])
    );
    // wire up links (renderTable doesn't support anchors directly)
    const rows = srcTable.querySelectorAll("tbody tr");
    rows.forEach((tr, i) => {
      const lastCell = tr.children[tr.children.length - 1];
      lastCell.innerHTML = "";
      const a = el("a", { href: DATA.sources[i].primary_document_url, target: "_blank", rel: "noopener", text: "Source ↗" });
      lastCell.appendChild(a);
    });

    const vintageTable = document.getElementById("table-vintage");
    vintageTable.dataset.caption = "As-originally-filed vs. latest-restated (revenue, cost of sales, gross profit, operating expenses)";
    renderTable(
      vintageTable,
      ["Metric", "Fiscal Year", "As Filed", "Restated", "Difference", "Reclassified?"],
      DATA.filing_vintage.map((r) => [
        r.metric, "FY" + r.fiscal_year, fmtM(r.as_originally_filed), fmtM(r.latest_restated),
        fmtM(r.difference),
        { text: r.reclassified ? "Yes" : "No", className: r.reclassified ? "reclassified" : "" },
      ])
    );

    const points = DATA.quarterly_cash.map((q) => ({ fy: new Date(q.as_of_date).getTime(), value: q.value }));
    // Use a bar chart keyed by index since dates aren't fiscal years.
    barChart(document.getElementById("chart-quarterly-cash"), {
      bars: DATA.quarterly_cash.map((q) => ({ label: q.as_of_date, value: q.value, color: "#1F3864" })),
    });
  }

  // ---------------------------------------------------------------------
  // 10. About / limitations
  // ---------------------------------------------------------------------
  const LIMITATIONS = [
    "Investing cash flow is modeled as exactly −CapEx in the forecast (no disclosed driver exists for non-CapEx investing items such as investment purchases/maturities) — a documented approximation, never substituted for CapEx or FCF themselves.",
    "The near-term debt-repayment reserve is proxied by each year's own scheduled repayment, because no disclosed debt-maturity ladder exists in the registered source filings.",
    "Share repurchases use a fixed payout-ratio assumption, floored at zero — never solved backward to hit a target ending-cash or EPS figure.",
    "No foreign-exchange translation effect is separately modeled; Target's cash is overwhelmingly USD-denominated and no disclosed FX driver exists in the source set.",
    "WACC inputs (risk-free rate, equity risk premium, beta) are stated, illustrative assumptions, not fitted to any market data feed — this project has no live market-data connection.",
    "The DCF is a scenario-based illustration, not a price target, analyst estimate, or investment recommendation.",
    "All forecast and valuation figures use only information available as of the FY2025 10-K (filed 2026-03-11) — no later filings, analyst estimates, or market results.",
    "True Power BI Desktop and true Excel/LibreOffice recalculation were unavailable in the build environment; verification instead used the `formulas` Python package for Excel and CSV/DAX-level checks for the Power BI package — both documented in docs/decisions.md.",
    "The client-side What-If Sandbox on this page is a manually-maintained port of the Python forecast formulas for illustrative interactivity only; the authoritative model is always the Python codebase in src/target_cash/.",
    "Minimum-cash-buffer and near-term reserve percentages are policy assumptions calibrated to Target's own observed FY2025 quarterly cash seasonality, not a disclosed corporate policy.",
    "Milestone 9 correction: the legacy 'deployable capacity' figure (still shown, de-emphasized, in the Cash Bridge section for backward compatibility) was found to be a gross, pre-discretionary ceiling that never subtracted a given year's own repurchases and commingled new borrowing with internally generated cash. The corrected taxonomy (Self-Funded Capacity Generated, Debt-Funded Capacity, Discretionary Deployment, Remaining Deployable Headroom) replaces it as the executive KPI — see docs/investment_capacity_correction_evidence.md.",
    "strategic_investment, voluntary_debt_reduction, and other_discretionary_uses in the corrected taxonomy are structural $0 placeholders — no policy lever has been modeled for them this round.",
    "v2 finance-semantics correction: debt_funded_incremental_capacity previously equaled gross debt proceeds, mislabeling capacity even when the same cash was simultaneously repaid. It is now the NET of proceeds over repayments (net deleveraging or equal proceeds/repayments produce zero incremental capacity); the offsetting net_mandatory_debt_service is subtracted from self_funded_capacity_generated, which now excludes opening_excess_liquidity entirely (a stock is never labeled 'generated'). Remaining Deployable Headroom now also deducts a forward debt-repayment reserve.",
    "The forward debt-repayment reserve for the terminal forecast year (FY2030) is a documented PROXY (it repeats FY2030's own net mandatory debt service) because FY2031 is outside the forecast horizon — it is not a real scheduled obligation.",
  ];
  function renderAbout() {
    const list = document.getElementById("limitations-list");
    list.innerHTML = "";
    LIMITATIONS.forEach((text) => list.appendChild(el("li", { text })));
  }

  // ---------------------------------------------------------------------
  // Scenario selector wiring
  // ---------------------------------------------------------------------
  function wireScenarioSelector() {
    document.querySelectorAll(".scenario-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        currentScenario = btn.dataset.scenario;
        document.querySelectorAll(".scenario-btn").forEach((b) => b.setAttribute("aria-checked", String(b === btn)));
        renderAll();
      });
    });
  }

  function renderAll() {
    renderSnapshot();
    renderForecast();
    renderBridge();
    renderWaterfall();
    renderDcf();
    resetSliders();
    renderWhatIfControls();
    recomputeWhatIf();
  }

  function init() {
    fetch("data/model_data.json")
      .then((r) => r.json())
      .then((data) => {
        DATA = data;
        renderHeader();
        wireScenarioSelector();
        renderWaterfallYearSelector();
        renderHistorical();
        renderCashDefinitions();
        renderEvidence();
        renderAbout();
        document.getElementById("whatif-reset").addEventListener("click", () => {
          resetSliders();
          renderWhatIfControls();
          recomputeWhatIf();
        });
        renderAll();
      })
      .catch((err) => {
        document.getElementById("main").innerHTML =
          '<p style="padding:40px;color:#C00000;">Failed to load data/model_data.json — ' +
          "run this page from a local HTTP server (not file://) and confirm the data file was built via " +
          "scripts/build_web_cockpit_data.py. Error: " + err + "</p>";
      });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
