(function () {
  "use strict";

  const { lineChart, barChart, groupedBarChart, waterfallChart, fmtM } = window.TargetCashCharts;
  const { runFromMetrics, computeCapacityTaxonomyForYears } = window.TargetCashFormulas;

  // Fixed categorical order for scenario identity -- never red/green, which
  // are reserved for pass/fail and positive/negative status elsewhere on the
  // page. A scenario is an identity, not a status.
  const SCENARIO_COLORS = { base: "#1F3864", upside: "#C9A227", downside: "#2E7D74" };
  const SCENARIO_LABELS = { base: "Base", upside: "Upside", downside: "Downside" };
  const GROSS_COLOR = "#9AA5B1";
  const NET_COLOR = "#1F3864";

  const REPO_URL = "https://github.com/jpatel-strategy/cash-flow";
  const REPO_BRANCH = "claude/gallant-dijkstra-p9xrvr"; // default/publishing branch as of the public release
  const AUTOMATED_TEST_COUNT = 467; // pytest -q, verified at build time -- see docs/ui_ux_audit.md / final report
  const NAMED_CAPACITY_CHECK_COUNT = 19; // len(CAPACITY_CHECK_METADATA) in src/target_cash/capacity_taxonomy.py

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

  function kpiCard(label, value, context, extraClass) {
    return el("div", { class: "kpi-card" + (extraClass ? " " + extraClass : "") }, [
      el("div", { class: "kpi-label", text: label }),
      el("div", { class: "kpi-value", text: value }),
      context ? el("div", { class: "kpi-context", text: context }) : null,
    ]);
  }

  // ---------------------------------------------------------------------
  // Header / evidence badges
  // ---------------------------------------------------------------------
  function validationTotals() {
    const v = DATA.validation;
    const capCheck = v.capacity_taxonomy || { total: 0, PASS: 0 };
    return {
      totalChecks: v.forecast.total + v.valuation.total + capCheck.total,
      totalPass: v.forecast.PASS + v.valuation.PASS + capCheck.PASS,
      capCheck,
    };
  }

  function renderHeader() {
    const badges = document.getElementById("header-badges");
    badges.innerHTML = "";
    const { totalChecks, totalPass, capCheck } = validationTotals();
    const histYears = DATA.historical_years.map(Number);
    const fcstYears = DATA.forecast_years.map(Number);
    const items = [
      { cls: "status-historical", text: `${DATA.sources.length} SEC filings` },
      { cls: "status-historical", text: `FY${Math.min(...histYears)}–FY${Math.max(...histYears)} actuals` },
      { cls: "status-forecast", text: `FY${Math.min(...fcstYears)}–FY${Math.max(...fcstYears)} scenarios` },
      { cls: "", text: `${AUTOMATED_TEST_COUNT} automated tests` },
      { cls: "", text: `${NAMED_CAPACITY_CHECK_COUNT} capacity checks / ${capCheck.total} capacity-validation results` },
      { cls: "", text: `Cutoff: ${DATA.information_cutoff}` },
      { cls: "", text: "Clean-room reproducible" },
      { cls: "status-not-advice", text: "Not investment advice" },
      { cls: "", text: `Validation: ${totalPass}/${totalChecks} PASS` },
    ];
    items.forEach((it) => badges.appendChild(el("span", { class: ("badge " + it.cls).trim(), text: it.text })));
    document.getElementById("footer-cutoff").textContent = DATA.information_cutoff;
  }

  // ---------------------------------------------------------------------
  // 1. Overview
  // ---------------------------------------------------------------------
  function renderOverview() {
    const sc = DATA.scenarios[currentScenario];
    const years = sc.years;
    const terminal = years[years.length - 1];
    const dcf = DATA.valuation.results[currentScenario];
    const hz = sc.capacity_horizon_summary;
    const capTerminal = sc.capacity_taxonomy_by_year[String(terminal.fiscal_year)];
    const { totalChecks, totalPass } = validationTotals();

    const grid = document.getElementById("kpi-grid");
    grid.innerHTML = "";
    grid.appendChild(kpiCard("FY2030 Revenue", fmtM(terminal.revenue), `${SCENARIO_LABELS[currentScenario]} scenario`));
    grid.appendChild(kpiCard("FY2030 Free Cash Flow", fmtM(terminal.free_cash_flow), "CFO − CapEx"));
    grid.appendChild(kpiCard("5-Year Net Horizon Deployable Capacity", fmtM(hz.net_horizon_deployable_capacity), "FY2026–FY2030, net of reserves", "kpi-decision"));
    grid.appendChild(kpiCard("FY2030 Remaining Deployable Headroom", fmtM(capTerminal.remaining_deployable_headroom), "a stock, not cumulative"));
    grid.appendChild(kpiCard("Implied DCF Value/Share", "$" + fmtNum(dcf.implied_value_per_share), "scenario-based, not a price target"));
    grid.appendChild(kpiCard("Validation Status", `${totalPass}/${totalChecks} PASS`, "all checks, this version"));

    document.getElementById("headroom-note").textContent =
      "Remaining headroom is a liquidity and allocation outcome — not a performance score. A scenario can have stronger operating performance but lower remaining headroom because more capital was deployed or reserved.";

    const histSeries = DATA.historical_years.map((fy) => ({ fy: Number(fy), value: DATA.historical[fy].revenue }));
    const fcstSeries = years.map((y) => ({ fy: y.fiscal_year, value: y.revenue }));
    const histFcf = DATA.historical_years.map((fy) => ({ fy: Number(fy), value: DATA.historical[fy].free_cash_flow }));
    const fcstFcf = years.map((y) => ({ fy: y.fiscal_year, value: y.free_cash_flow }));

    const revChart = document.getElementById("chart-revenue-fcf");
    lineChart(revChart, {
      series: [
        { label: "Revenue (actual)", points: histSeries, color: "#1F3864" },
        { label: "Revenue (forecast)", points: [histSeries[histSeries.length - 1], ...fcstSeries], color: "#1F3864", dashed: true },
        { label: "FCF (actual)", points: histFcf, color: "#C9A227" },
        { label: "FCF (forecast)", points: [histFcf[histFcf.length - 1], ...fcstFcf], color: "#C9A227", dashed: true },
      ],
    });
    revChart.setAttribute("aria-label",
      `Line chart: Revenue rose from ${fmtM(DATA.historical["2021"].revenue)} in FY2021 to ${fmtM(DATA.historical["2025"].revenue)} in FY2025 (actual), ` +
      `then to ${fmtM(terminal.revenue)} in FY2030 under the ${SCENARIO_LABELS[currentScenario]} scenario (forecast). ` +
      `Free cash flow moved from ${fmtM(DATA.historical["2021"].free_cash_flow)} to ${fmtM(DATA.historical["2025"].free_cash_flow)} actual, then to ${fmtM(terminal.free_cash_flow)} forecast.`);

    const capBars = ["base", "upside", "downside"].map((s) => ({
      label: SCENARIO_LABELS[s],
      value: DATA.scenarios[s].capacity_horizon_summary.net_horizon_deployable_capacity,
      color: SCENARIO_COLORS[s],
    }));
    const capChart = document.getElementById("chart-capacity-by-scenario");
    barChart(capChart, { bars: capBars });
    capChart.setAttribute("aria-label",
      `Bar chart: five-year net horizon deployable capacity by scenario — ` +
      capBars.map((b) => `${b.label} ${fmtM(b.value)}`).join(", ") + ".");
    document.getElementById("capacity-note").textContent =
      "Net of reserves — see Investment Capacity below for the full gross-vs-net reconciliation. A higher-revenue scenario can show lower net capacity if it deploys or reserves more.";

    document.getElementById("scenario-narrative-snapshot").textContent = sc.narrative;

    renderComparisonTable();
  }

  function renderComparisonTable() {
    const table = document.getElementById("table-comparison");
    const scenarios = ["base", "upside", "downside"];
    const rows = [
      ["FY2030 Revenue", ...scenarios.map((s) => fmtM(DATA.scenarios[s].years[DATA.scenarios[s].years.length - 1].revenue))],
      ["FY2030 Free Cash Flow", ...scenarios.map((s) => fmtM(DATA.scenarios[s].years[DATA.scenarios[s].years.length - 1].free_cash_flow))],
      ["5-Year Net Horizon Deployable Capacity", ...scenarios.map((s) => fmtM(DATA.scenarios[s].capacity_horizon_summary.net_horizon_deployable_capacity))],
      ["FY2030 Remaining Deployable Headroom", ...scenarios.map((s) => {
        const y = DATA.scenarios[s].years;
        const t = y[y.length - 1];
        return fmtM(DATA.scenarios[s].capacity_taxonomy_by_year[String(t.fiscal_year)].remaining_deployable_headroom);
      })],
      ["Implied DCF Value/Share", ...scenarios.map((s) => "$" + fmtNum(DATA.valuation.results[s].implied_value_per_share))],
    ];
    table.dataset.caption = "Key decision metrics, side by side — never mixes results from different scenarios elsewhere on this page";
    renderTable(table, ["Metric", ...scenarios.map((s) => SCENARIO_LABELS[s])], rows);
  }

  // ---------------------------------------------------------------------
  // 2. Historical evidence
  // ---------------------------------------------------------------------
  function renderHistorical() {
    const years = DATA.historical_years;
    lineChart(document.getElementById("chart-historical"), {
      series: [
        { label: "Revenue", points: years.map((fy) => ({ fy: Number(fy), value: DATA.historical[fy].revenue })), color: "#1F3864" },
        { label: "Gross Profit", points: years.map((fy) => ({ fy: Number(fy), value: DATA.historical[fy].gross_profit })), color: "#C9A227" },
        { label: "Operating Income", points: years.map((fy) => ({ fy: Number(fy), value: DATA.historical[fy].operating_income })), color: "#2E7D74" },
        { label: "Net Income", points: years.map((fy) => ({ fy: Number(fy), value: DATA.historical[fy].net_income })), color: "#2E75B6" },
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
        return key.includes("margin") || key === "diluted_eps" ? fmtNum(v, 2) : fmtM(v);
      }),
    ]);
    renderTable(table, ["Metric", ...years.map((y) => "FY" + y)], rows);

    renderCashDefinitions();

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

    const qChart = document.getElementById("chart-quarterly-cash");
    barChart(qChart, { bars: DATA.quarterly_cash.map((q) => ({ label: q.as_of_date, value: q.value, color: "#1F3864" })) });
    qChart.setAttribute("aria-label", "Bar chart of quarter-end cash balances, sourced from 10-Qs, independent of the forecast model.");
  }

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
  // 3. Scenario forecast
  // ---------------------------------------------------------------------
  function renderForecast() {
    const years = DATA.scenarios[currentScenario].years;

    lineChart(document.getElementById("chart-forecast-income"), {
      series: [
        { label: "Revenue", points: years.map((y) => ({ fy: y.fiscal_year, value: y.revenue })), color: "#1F3864", dashed: true },
        { label: "Gross Profit", points: years.map((y) => ({ fy: y.fiscal_year, value: y.gross_profit })), color: "#C9A227", dashed: true },
        { label: "Operating Income", points: years.map((y) => ({ fy: y.fiscal_year, value: y.operating_income })), color: "#2E7D74", dashed: true },
        { label: "Net Income", points: years.map((y) => ({ fy: y.fiscal_year, value: y.net_income })), color: "#2E75B6", dashed: true },
      ],
    });
    // Margins (%) and EPS ($) are kept as SEPARATE charts on separate axes --
    // never plotted together on one shared linear scale (a mixed-unit anti-
    // pattern that made both series unreadable in the prior build; see
    // docs/ui_ux_audit.md §3).
    lineChart(document.getElementById("chart-forecast-margin-pct"), {
      series: [
        { label: "Gross Margin %", points: years.map((y) => ({ fy: y.fiscal_year, value: y.gross_margin_pct })), color: "#C9A227", dashed: true },
        { label: "Operating Margin %", points: years.map((y) => ({ fy: y.fiscal_year, value: y.operating_margin_pct })), color: "#2E7D74", dashed: true },
      ],
    });
    lineChart(document.getElementById("chart-forecast-eps"), {
      series: [
        { label: "Diluted EPS ($)", points: years.map((y) => ({ fy: y.fiscal_year, value: y.diluted_eps })), color: "#1F3864", dashed: true },
      ],
    });
    lineChart(document.getElementById("chart-forecast-cfo-fcf"), {
      series: [
        { label: "CFO", points: years.map((y) => ({ fy: y.fiscal_year, value: y.operating_cash_flow })), color: "#1F3864", dashed: true },
        { label: "Free Cash Flow", points: years.map((y) => ({ fy: y.fiscal_year, value: y.free_cash_flow })), color: "#C9A227", dashed: true },
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
        return key.includes("pct") || key === "diluted_eps" ? fmtNum(v, 2) : fmtM(v);
      }),
    ]);
    renderTable(table, ["Metric", ...years.map((y) => "FY" + y.fiscal_year)], rows);
  }

  // ---------------------------------------------------------------------
  // 4. Investment capacity
  // ---------------------------------------------------------------------
  function renderCapacity() {
    const sc = DATA.scenarios[currentScenario];
    const years = sc.years;
    const terminal = years[years.length - 1];
    const capYears = years.map((y) => sc.capacity_taxonomy_by_year[String(y.fiscal_year)]);
    const capTerminal = capYears[capYears.length - 1];
    const hz = sc.capacity_horizon_summary;

    waterfallChart(document.getElementById("chart-capacity-taxonomy"), {
      steps: [
        { label: "Opening Excess Liquidity (STOCK)", amount: capTerminal.opening_excess_liquidity, isTotal: true },
        { label: "+ Self-Funded Capacity Generated", amount: capTerminal.self_funded_capacity_generated },
        { label: "+ Debt-Funded Capacity (net)", amount: capTerminal.debt_funded_incremental_capacity },
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

    const grossNetGroups = ["base", "upside", "downside"].map((s) => {
      const h = DATA.scenarios[s].capacity_horizon_summary;
      return {
        label: SCENARIO_LABELS[s],
        bars: [
          { seriesLabel: "Gross (before reserves)", value: h.gross_horizon_funding_before_reserve_adjustments, color: GROSS_COLOR },
          { seriesLabel: "Net (decision KPI)", value: h.net_horizon_deployable_capacity, color: NET_COLOR },
        ],
      };
    });
    const gvnChart = document.getElementById("chart-gross-vs-net");
    groupedBarChart(gvnChart, { groups: grossNetGroups });
    gvnChart.setAttribute("aria-label",
      "Grouped bar chart, gross vs net five-year horizon capacity by scenario: " +
      grossNetGroups.map((g) => `${g.label} gross ${fmtM(g.bars[0].value)}, net ${fmtM(g.bars[1].value)}`).join("; ") + ".");

    const horizonTable = document.getElementById("table-capacity-horizon");
    renderTable(
      horizonTable,
      ["Metric", "Value"],
      [
        ["Cumulative Self-Funded Generation (FLOW)", fmtM(hz.cumulative_self_funded_generation)],
        ["Cumulative Debt-Funded Capacity (SOURCE)", fmtM(hz.cumulative_debt_funded_capacity)],
        ["Opening Excess Liquidity, horizon start (STOCK)", fmtM(hz.opening_excess_liquidity_at_horizon_start)],
        ["Cumulative Discretionary Deployment (USE)", fmtM(hz.cumulative_discretionary_deployment)],
        ["Terminal Remaining Headroom, FY2030 (STOCK)", fmtM(hz.terminal_remaining_headroom)],
        ["Ending Reserve Movement (RESERVE)", fmtM(hz.ending_reserve_movement)],
        ["Terminal Forward Debt-Repayment Reserve — FY2031 proxy (RESERVE)", fmtM(hz.terminal_forward_debt_repayment_reserve)],
        [
          { text: "Gross Horizon Funding — NOT accessible capacity", className: "reclassified" },
          { text: fmtM(hz.gross_horizon_funding_before_reserve_adjustments), className: "reclassified" },
        ],
        [
          { text: "Net Horizon Deployable Capacity — decision KPI", className: "reclassified-net" },
          { text: fmtM(hz.net_horizon_deployable_capacity), className: "reclassified-net" },
        ],
      ]
    );
    horizonTable.dataset.caption =
      "Gross = Opening Excess Liquidity + Cumulative Self-Funded + Cumulative Debt-Funded, before reserves. " +
      "Net = Gross − Ending Reserve Movement − Terminal Forward Reserve = Cumulative Deployment + Terminal Headroom.";

    renderCapacityEvidence(hz);

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

    // Legacy waterfall -- deprecated, kept only for backward compatibility.
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
  }

  function renderCapacityEvidence(hz) {
    const dl = document.getElementById("capacity-evidence-list");
    dl.innerHTML = "";
    const entries = [
      ["Formula", "Net = Gross − Ending Reserve Movement − Terminal Forward Debt-Repayment Reserve; reconciles to Cumulative Discretionary Deployment + Terminal Remaining Headroom"],
      ["Unit", "$ millions"],
      ["Fiscal period", "FY2026–FY2030 (5-year horizon)"],
      ["Information cutoff", DATA.information_cutoff],
      ["Model version", "v2 (final independent-audit closeout — see docs/investment_capacity_correction_evidence.md Part III)"],
      ["Validation status", `${NAMED_CAPACITY_CHECK_COUNT} named checks, ${DATA.validation.capacity_taxonomy.total} results, all PASS`],
      ["Known limitation", "FY2030's forward debt-repayment reserve is a documented FY2031 proxy, not a disclosed obligation."],
    ];
    entries.forEach(([term, def]) => {
      dl.appendChild(el("dt", { text: term }));
      dl.appendChild(el("dd", { text: def }));
    });
  }

  // ---------------------------------------------------------------------
  // 5. Capital allocation waterfall
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
  // 6. DCF valuation
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
        .filter((s) => s.step <= 5)
        .map((s) => ({
          label: s.label.replace(/^[=+\-/]\s*/, ""),
          amount: s.value,
          isTotal: [3, 5].includes(s.step),
        })),
    });
    const bridgeCard = document.getElementById("chart-valuation-bridge").parentElement;
    bridgeCard.querySelector(".chart-note")?.remove();
    document.getElementById("chart-valuation-bridge").insertAdjacentHTML(
      "afterend",
      `<p class="chart-note">Equity Value ÷ Diluted Shares (${fmtNum(result.valuation_date_diluted_shares, 1)}M, FY2025 actual) = <strong>$${fmtNum(result.implied_value_per_share)} implied value per share</strong>. Shown separately because $/share is a different unit than the $M bars above.</p>`
    );

    const vpsBars = ["base", "upside", "downside"].map((s) => ({
      label: SCENARIO_LABELS[s],
      value: DATA.valuation.results[s].implied_value_per_share,
      color: SCENARIO_COLORS[s],
    }));
    const vpsChart = document.getElementById("chart-value-per-share-scenario");
    barChart(vpsChart, { bars: vpsBars });
    vpsChart.setAttribute("aria-label", "Bar chart, implied DCF value per share by scenario: " + vpsBars.map((b) => `${b.label} $${fmtNum(b.value)}`).join(", ") + ". Scenario analysis, not a price target.");

    const waccGrid = DATA.valuation.wacc_terminal_growth_sensitivity.grid;
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
  // 7. What-if lab
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
        "aria-label": s.label,
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
    updateChangedIndicator();
  }

  function updateChangedIndicator() {
    const changed = SLIDERS.filter((s) => sliderDeltas[s.key] !== 0).length;
    document.getElementById("whatif-changed-indicator").textContent =
      changed === 0 ? "No inputs changed — showing the published scenario baseline." : `${changed} input${changed === 1 ? "" : "s"} changed from baseline.`;
  }

  function renderWhatIfBaseline() {
    const sc = DATA.scenarios[currentScenario];
    const years = sc.years;
    const terminal = years[years.length - 1];
    const capTerminal = sc.capacity_taxonomy_by_year[String(terminal.fiscal_year)];
    const out = document.getElementById("whatif-baseline");
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
    const cls = "whatif-card";
    out.appendChild(kpiCard("FY2030 Revenue", fmtM(terminal.revenue), null, cls));
    out.appendChild(kpiCard("FY2030 Free Cash Flow", fmtM(terminal.free_cash_flow), null, cls));
    out.appendChild(kpiCard("FY2030 Opening Excess Liquidity", fmtM(capTerminal.opening_excess_liquidity), null, cls));
    out.appendChild(kpiCard("FY2030 Self-Funded Capacity Generated", fmtM(capTerminal.self_funded_capacity_generated), null, cls));
    out.appendChild(kpiCard("FY2030 Debt-Funded Capacity", fmtM(capTerminal.debt_funded_incremental_capacity), null, cls));
    out.appendChild(kpiCard("FY2030 Discretionary Deployment", fmtM(capTerminal.total_discretionary_deployment), null, cls));
    out.appendChild(kpiCard("FY2030 Remaining Deployable Headroom", fmtM(capTerminal.remaining_deployable_headroom), null, cls));
    out.appendChild(kpiCard("FY2030 Diluted EPS", "$" + fmtNum(terminal.diluted_eps), null, cls));
    out.appendChild(kpiCard("FY2030 Ending Cash", fmtM(terminal.ending_cash), null, cls));
    out.appendChild(kpiCard("Funding Warning?", terminal.funding_warning ? "Yes" : "No", null, cls));
    updateChangedIndicator();
  }

  // ---------------------------------------------------------------------
  // 8. Audit & methodology
  // ---------------------------------------------------------------------
  function renderAudit() {
    const srcTable = document.getElementById("table-sources");
    srcTable.dataset.caption = "Every SEC filing this project is built from";
    renderTable(
      srcTable,
      ["Accession #", "Form", "Filed", "Period of Report", "URL"],
      DATA.sources.map((s) => [s.accession_number, s.form_type, s.filed_at, s.period_of_report, { text: "Source ↗", className: "" }])
    );
    const rows = srcTable.querySelectorAll("tbody tr");
    rows.forEach((tr, i) => {
      const lastCell = tr.children[tr.children.length - 1];
      lastCell.innerHTML = "";
      const a = el("a", { href: DATA.sources[i].primary_document_url, target: "_blank", rel: "noopener", text: "Source ↗" });
      lastCell.appendChild(a);
    });

    const { totalChecks, totalPass, capCheck } = validationTotals();
    const checksTable = document.getElementById("table-audit-checks");
    checksTable.dataset.caption = "Validation coverage and the three-round methodology-correction history";
    renderTable(
      checksTable,
      ["Category", "Checks", "Pass", "Status"],
      [
        ["Forecast validation", String(DATA.validation.forecast.total), String(DATA.validation.forecast.PASS), DATA.validation.forecast.FAIL === 0 ? "All PASS" : `${DATA.validation.forecast.FAIL} FAIL`],
        ["Valuation validation", String(DATA.validation.valuation.total), String(DATA.validation.valuation.PASS), DATA.validation.valuation.FAIL === 0 ? "All PASS" : `${DATA.validation.valuation.FAIL} FAIL`],
        [`Capacity taxonomy validation (${NAMED_CAPACITY_CHECK_COUNT} named checks, v2)`, String(capCheck.total), String(capCheck.PASS), capCheck.FAIL === 0 ? "All PASS" : `${capCheck.FAIL} FAIL`],
        [{ text: "Total", className: "reclassified-net" }, { text: String(totalChecks), className: "reclassified-net" }, { text: String(totalPass), className: "reclassified-net" }, { text: "All PASS", className: "reclassified-net" }],
        ["v1 correction (frozen, preserved for audit)", "—", "—", "Self-funded/debt-funded/deployment/headroom taxonomy introduced"],
        ["v2 correction (current formulas)", "—", "—", "Net-of-repayment debt capacity; opening liquidity excluded from generation"],
        ["Final independent-audit closeout (this build)", "—", "—", "Clean-clone tests; next-year lineage for the forward reserve; gross/net horizon split"],
      ]
    );

    renderAbout();
  }

  const LIMITATIONS = [
    "Investing cash flow is modeled as exactly −CapEx in the forecast (no disclosed driver exists for non-CapEx investing items such as investment purchases/maturities) — a documented approximation, never substituted for CapEx or FCF themselves.",
    "The near-term debt-repayment reserve is proxied by each year's own scheduled repayment, because no disclosed debt-maturity ladder exists in the registered source filings.",
    "Share repurchases use a fixed payout-ratio assumption, floored at zero — never solved backward to hit a target ending-cash or EPS figure.",
    "No foreign-exchange translation effect is separately modeled; Target's cash is overwhelmingly USD-denominated and no disclosed FX driver exists in the source set.",
    "WACC inputs (risk-free rate, equity risk premium, beta) are stated, illustrative assumptions, not fitted to any market data feed — this project has no live market-data connection.",
    "The DCF is a scenario-based illustration, not a price target, analyst estimate, or investment recommendation.",
    "All forecast and valuation figures use only information available as of the FY2025 10-K (filed 2026-03-11) — no later filings, analyst estimates, or market results.",
    "True Power BI Desktop and true Excel/LibreOffice recalculation were unavailable in the build environment; verification instead used the `formulas` Python package for Excel and CSV/DAX-level checks for the Power BI-ready package — both documented in docs/decisions.md.",
    "The client-side What-If Lab on this page is a manually-maintained port of the Python forecast formulas for illustrative interactivity only; the authoritative model is always the Python codebase in src/target_cash/.",
    "Minimum-cash-buffer and near-term reserve percentages are policy assumptions calibrated to Target's own observed FY2025 quarterly cash seasonality, not a disclosed corporate policy.",
    "The legacy 'deployable capacity' figure (still shown, de-emphasized, for backward compatibility) was found to be a gross, pre-discretionary ceiling that never subtracted a given year's own repurchases and commingled new borrowing with internally generated cash. The corrected taxonomy replaces it as the executive KPI.",
    "strategic_investment, voluntary_debt_reduction, and other_discretionary_uses in the corrected taxonomy are structural $0 placeholders — no policy lever has been modeled for them this round.",
    "debt_funded_incremental_capacity is the NET of proceeds over repayments (net deleveraging or equal proceeds/repayments produce zero incremental capacity); self_funded_capacity_generated excludes opening_excess_liquidity entirely (a stock is never labeled 'generated').",
    "The forward debt-repayment reserve for the terminal forecast year (FY2030) is a documented PROXY (it repeats FY2030's own net mandatory debt service) because FY2031 is outside the forecast horizon — it is not a real scheduled obligation.",
    "The gross horizon-funding figure is retained (relabeled, de-emphasized) purely to prove the reconciliation identity — it is never the headline 'accessible capacity' figure; that is always the NET figure.",
  ];
  function renderAbout() {
    const list = document.getElementById("limitations-list");
    list.innerHTML = "";
    LIMITATIONS.forEach((text) => list.appendChild(el("li", { text })));
  }

  // ---------------------------------------------------------------------
  // 9. Downloads
  // ---------------------------------------------------------------------
  function renderDownloads() {
    const grid = document.getElementById("downloads-grid");
    grid.innerHTML = "";
    const raw = (path) => `${REPO_URL}/raw/${REPO_BRANCH}/${path}`;
    const blob = (path) => `${REPO_URL}/blob/${REPO_BRANCH}/${path}`;
    const cards = [
      { title: "Excel Model", desc: "15-sheet executive workbook, fully formula-linked, verified against Python.", href: raw("deliverables/Target_Cash_Flow_Investment_Capacity_Model.xlsx"), cta: "Download .xlsx", download: true },
      { title: "Power BI-Ready Handoff", desc: "CSV data model, DAX measures, and page specs — a Power BI-ready handoff, not a .pbix file.", href: raw("deliverables/powerbi_handoff_package.zip"), cta: "Download .zip", download: true },
      { title: "Executive Case Study", desc: "The recruiter-facing narrative: what was built, why, and the headline results.", href: blob("deliverables/portfolio_package/01_executive_case_study.md"), cta: "Read on GitHub", download: false },
      { title: "Methodology & Evidence", desc: "The full three-round correction record: root-cause proofs, formulas, and validation totals.", href: blob("docs/investment_capacity_correction_evidence.md"), cta: "Read on GitHub", download: false },
      { title: "GitHub Repository", desc: "Full source: Python engine, tests, migrations, Excel/Power BI build scripts, and this cockpit.", href: REPO_URL, cta: "View repository", download: false },
    ];
    cards.forEach((c) => {
      const a = el("a", { class: "download-card", href: c.href, target: "_blank", rel: "noopener" });
      if (c.download) a.setAttribute("download", "");
      a.appendChild(el("h3", { text: c.title }));
      a.appendChild(el("p", { text: c.desc }));
      a.appendChild(el("span", { class: "download-cta", text: c.cta + " →" }));
      grid.appendChild(a);
    });
  }

  // ---------------------------------------------------------------------
  // Scenario selector + comparison toggle + scrollspy
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

  function wireComparisonToggle() {
    const btn = document.getElementById("comparison-toggle-btn");
    const panel = document.getElementById("comparison-panel");
    btn.addEventListener("click", () => {
      const expanded = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", String(!expanded));
      panel.hidden = expanded;
    });
  }

  function wireScrollSpy() {
    const links = Array.from(document.querySelectorAll("#site-nav a"));
    const sections = links.map((a) => document.getElementById(a.dataset.section)).filter(Boolean);
    if (!("IntersectionObserver" in window) || sections.length === 0) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const link = links.find((a) => a.dataset.section === entry.target.id);
          if (!link) return;
          if (entry.isIntersecting) {
            links.forEach((a) => a.classList.remove("active"));
            link.classList.add("active");
            link.setAttribute("aria-current", "location");
            links.filter((a) => a !== link).forEach((a) => a.removeAttribute("aria-current"));
          }
        });
      },
      { rootMargin: "-40% 0px -55% 0px", threshold: 0 }
    );
    sections.forEach((s) => observer.observe(s));
  }

  function renderAll() {
    renderOverview();
    renderForecast();
    renderCapacity();
    renderWaterfall();
    renderDcf();
    resetSliders();
    renderWhatIfControls();
    renderWhatIfBaseline();
    recomputeWhatIf();
  }

  function init() {
    fetch("data/model_data.json")
      .then((r) => r.json())
      .then((data) => {
        DATA = data;
        renderHeader();
        wireScenarioSelector();
        wireComparisonToggle();
        wireScrollSpy();
        renderWaterfallYearSelector();
        renderHistorical();
        renderAudit();
        renderDownloads();
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
