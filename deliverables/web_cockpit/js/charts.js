/**
 * Minimal, dependency-free SVG chart helpers. No external charting
 * library is used, so the cockpit has zero CDN dependencies and works
 * fully offline -- consistent with "no fake real-time data" and keeping
 * local preview simple and reliable.
 */
(function (global) {
  "use strict";

  const NAVY = "#1F3864";
  const GOLD = "#C9A227";
  const TEAL = "#2E7D74";
  const GREY = "#64748B";
  const GOOD = "#548235";
  const BAD = "#C00000";
  const GRIDLINE = "rgba(226, 232, 240, 0.85)";
  // Fixed categorical order for identity (never cycled, never reused for status).
  // GOOD/BAD are reserved for pass/fail and positive/negative deltas only --
  // never for scenario identity (a scenario is not a "failure").
  const PALETTE = [NAVY, GOLD, TEAL, "#2E75B6", "#8A5A44"];

  function svgEl(tag, attrs) {
    const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const k in attrs) el.setAttribute(k, attrs[k]);
    return el;
  }

  function clear(container) {
    container.innerHTML = "";
  }

  // -----------------------------------------------------------------------
  // Formatter registry -- centralized, immutable. Every chart call must
  // pass the formatter matching its own unit; never left to default to
  // millions for a %, $/share, or plain-number series.
  // -----------------------------------------------------------------------
  function fmtMillions(v) {
    if (v === null || v === undefined || Number.isNaN(v)) return "—";
    return "$" + Math.round(v).toLocaleString() + "M";
  }
  function fmtPercent(v) {
    if (v === null || v === undefined || Number.isNaN(v)) return "—";
    const rounded = Math.round(v * 10) / 10;
    return (Number.isInteger(rounded) ? rounded.toFixed(0) : rounded.toFixed(1)) + "%";
  }
  function fmtPerShare(v) {
    if (v === null || v === undefined || Number.isNaN(v)) return "—";
    return "$" + v.toFixed(2);
  }
  function fmtNumber(v) {
    if (v === null || v === undefined || Number.isNaN(v)) return "—";
    return v.toLocaleString();
  }
  const Formatters = Object.freeze({
    millions: fmtMillions,
    percent: fmtPercent,
    perShare: fmtPerShare,
    number: fmtNumber,
  });
  function resolveFormatter(f) {
    if (typeof f === "function") return f;
    if (typeof f === "string" && Formatters[f]) return Formatters[f];
    return Formatters.millions;
  }
  // Backward-compatible export -- existing app.js code imports fmtM directly.
  const fmtM = fmtMillions;

  // -----------------------------------------------------------------------
  // Shared domain calculation -- one function, used everywhere a linear
  // y-axis is built, so every chart gets the same ~20% top headroom and
  // never clips a value label above the tallest bar/point.
  // -----------------------------------------------------------------------
  function calculateDomain(values, headroom = 0.2) {
    const finite = values.filter(Number.isFinite);
    const minimum = Math.min(0, ...finite);
    const maximum = Math.max(0, ...finite);
    const range = Math.max(maximum - minimum, 1);
    return {
      min: minimum < 0 ? minimum - range * 0.05 : 0,
      max: maximum + range * headroom,
    };
  }

  // Top margin large enough that a bold ~11px value label drawn 6px above
  // a bar/point never intersects the SVG's own top edge, even before
  // headroom is applied.
  const LABEL_TOP_MARGIN = 28;

  // -----------------------------------------------------------------------
  // Accessible tooltip -- one instance per chart-target container ("wrapper"),
  // shown on pointer hover or keyboard focus of an SVG hit target, clamped
  // to the wrapper's own bounds so it can never create page overflow.
  // -----------------------------------------------------------------------
  function ensureTooltip(wrapper) {
    let tip = wrapper.querySelector(":scope > .chart-tooltip");
    if (!tip) {
      tip = document.createElement("div");
      tip.className = "chart-tooltip";
      tip.setAttribute("role", "status");
      tip.setAttribute("aria-live", "polite");
      tip.hidden = true;
      wrapper.appendChild(tip);
    }
    return tip;
  }

  function positionTooltip(tip, wrapper, clientX, clientY) {
    const wrapRect = wrapper.getBoundingClientRect();
    const tipRect = tip.getBoundingClientRect();
    let left = clientX - wrapRect.left + 14;
    let top = clientY - wrapRect.top + 14;
    const maxLeft = Math.max(4, wrapRect.width - tipRect.width - 4);
    const maxTop = Math.max(4, wrapRect.height - tipRect.height - 4);
    left = Math.max(4, Math.min(left, maxLeft));
    top = Math.max(4, Math.min(top, maxTop));
    tip.style.left = left + "px";
    tip.style.top = top + "px";
  }

  function showTooltip(wrapper, html, clientX, clientY) {
    const tip = ensureTooltip(wrapper);
    tip.innerHTML = html;
    tip.hidden = false;
    positionTooltip(tip, wrapper, clientX, clientY);
  }
  function hideTooltip(wrapper) {
    const tip = wrapper.querySelector(":scope > .chart-tooltip");
    if (tip) tip.hidden = true;
  }
  function positionTooltipNearElement(wrapper, el) {
    const r = el.getBoundingClientRect();
    positionTooltip(wrapper.querySelector(":scope > .chart-tooltip"), wrapper, r.left + r.width / 2, r.top);
  }

  /** Wires pointer + keyboard interaction for one focusable hit target
   * that shows `html` in the shared tooltip on hover/focus. */
  function wireHitTarget(hit, wrapper, buildHtml, ariaLabel) {
    hit.setAttribute("tabindex", "0");
    hit.setAttribute("role", "img");
    hit.setAttribute("aria-label", ariaLabel);
    hit.style.cursor = "pointer";
    const open = (evt) => {
      const rect = hit.getBoundingClientRect();
      const x = evt && typeof evt.clientX === "number" ? evt.clientX : rect.left + rect.width / 2;
      const y = evt && typeof evt.clientY === "number" ? evt.clientY : rect.top;
      showTooltip(wrapper, buildHtml(), x, y);
    };
    const close = () => hideTooltip(wrapper);
    hit.addEventListener("mouseenter", open);
    hit.addEventListener("mousemove", open);
    hit.addEventListener("mouseleave", close);
    hit.addEventListener("focus", () => {
      const rect = hit.getBoundingClientRect();
      showTooltip(wrapper, buildHtml(), rect.left + rect.width / 2, rect.top);
    });
    hit.addEventListener("blur", close);
    hit.addEventListener("keydown", (evt) => {
      if (evt.key === "Escape") close();
    });
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  // -----------------------------------------------------------------------
  // Multi-series line chart.
  // series: [{label, points:[{fy, value}], dashed, color}]
  // formatter: registry key or function, applied to axis labels + tooltip values.
  // headroom: fraction of range added above the max (default 0.2).
  // tooltipFields: optional array subset of ["fiscalYear","metric","value","classification"].
  // valueLabel: optional short axis-title text drawn top-left of the plot area.
  // -----------------------------------------------------------------------
  function lineChart(container, { series, width = 560, height = 260, formatter = "millions", headroom = 0.2, tooltipFields, valueLabel }) {
    clear(container);
    const fmt = resolveFormatter(formatter);
    const fields = tooltipFields || ["fiscalYear", "metric", "value", "classification"];
    const margin = { top: LABEL_TOP_MARGIN, right: 16, bottom: 30, left: 60 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;

    const allPoints = series.flatMap((s) => s.points);
    const xs = [...new Set(allPoints.map((p) => p.fy))].sort((a, b) => a - b);
    const domain = calculateDomain(allPoints.map((p) => p.value), headroom);
    const yMin = domain.min;
    const yMax = domain.max;

    const xScale = (fy) => margin.left + ((fy - xs[0]) / (xs[xs.length - 1] - xs[0] || 1)) * w;
    const yScale = (v) => margin.top + h - ((v - yMin) / (yMax - yMin || 1)) * h;

    // Focusable elements must never live inside an aria-hidden ancestor.
    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}` });

    // gridlines + y-axis labels -- dashed, subtle; horizontal only (no vertical gridlines).
    const gridCount = 4;
    for (let i = 0; i <= gridCount; i++) {
      const v = yMin + ((yMax - yMin) * i) / gridCount;
      const y = yScale(v);
      svg.appendChild(svgEl("line", { x1: margin.left, x2: width - margin.right, y1: y, y2: y, stroke: GRIDLINE, "stroke-dasharray": "3,3" }));
      const t = svgEl("text", { x: margin.left - 8, y: y + 4, "font-size": 10, fill: GREY, "text-anchor": "end" });
      t.textContent = fmt(v);
      svg.appendChild(t);
    }

    if (valueLabel) {
      const lbl = svgEl("text", { x: margin.left, y: margin.top - 12, "font-size": 10, fill: GREY, "font-weight": "600" });
      lbl.textContent = valueLabel;
      svg.appendChild(lbl);
    }

    // x-axis labels
    xs.forEach((fy) => {
      const t = svgEl("text", { x: xScale(fy), y: height - 8, "font-size": 10, fill: GREY, "text-anchor": "middle" });
      t.textContent = "FY" + fy;
      svg.appendChild(t);
    });

    const hitTargets = [];
    series.forEach((s, i) => {
      const color = s.color || PALETTE[i % PALETTE.length];
      const pts = s.points.slice().sort((a, b) => a.fy - b.fy);
      const d = pts.map((p, idx) => `${idx === 0 ? "M" : "L"} ${xScale(p.fy)} ${yScale(p.value)}`).join(" ");
      const path = svgEl("path", {
        d, fill: "none", stroke: color, "stroke-width": 2,
        "stroke-dasharray": s.dashed ? "6,4" : "none",
      });
      svg.appendChild(path);
      pts.forEach((p) => {
        const cx = xScale(p.fy);
        const cy = yScale(p.value);
        svg.appendChild(svgEl("circle", { cx, cy, r: 3, fill: color }));
        // Larger transparent hit target, individually focusable.
        const hit = svgEl("circle", { cx, cy, r: 11, fill: "transparent", stroke: "none" });
        hitTargets.push({ hit, series: s, point: p, fy: p.fy, value: p.value, color });
        svg.appendChild(hit);
      });
    });

    container.appendChild(svg);
    container.style.position = "relative";

    // Shared-tooltip-per-fiscal-year: hovering/focusing any point at a
    // given fy shows every series' already-plotted value at that same fy
    // (never a value not already supplied to this chart).
    hitTargets.forEach(({ hit, series: s, point, fy, value, color }) => {
      const classification = s.dashed ? "Forecast" : "Actual";
      const buildHtml = () => {
        const rows = xs.includes(fy)
          ? series
              .map((s2) => {
                const p2 = s2.points.find((pp) => pp.fy === fy);
                if (!p2) return null;
                const cls2 = s2.dashed ? "Forecast" : "Actual";
                const parts = [];
                if (fields.includes("metric")) parts.push(`<strong>${escapeHtml(s2.label)}</strong>`);
                if (fields.includes("value")) parts.push(escapeHtml(fmt(p2.value)));
                if (fields.includes("classification")) parts.push(`<span class="chart-tooltip-tag">${cls2}</span>`);
                return `<div class="chart-tooltip-row">${parts.join(" — ")}</div>`;
              })
              .filter(Boolean)
              .join("")
          : "";
        const header = fields.includes("fiscalYear") ? `<div class="chart-tooltip-header">FY${fy}</div>` : "";
        return header + rows;
      };
      const ariaLabel = `${s.label}, fiscal year ${fy}, ${fmt(value)}, ${classification}`;
      wireHitTarget(hit, container, buildHtml, ariaLabel);
    });

    appendLegend(container, series.map((s, i) => ({ label: s.label, color: s.color || PALETTE[i % PALETTE.length] })));
  }

  function appendLegend(container, items) {
    const legend = document.createElement("div");
    legend.className = "chart-legend";
    legend.style.display = "flex";
    legend.style.flexWrap = "wrap";
    legend.style.gap = "12px";
    legend.style.marginTop = "6px";
    legend.style.fontSize = "0.78rem";
    items.forEach((it) => {
      const span = document.createElement("span");
      span.innerHTML = `<span style="display:inline-block;width:10px;height:10px;background:${it.color};margin-right:4px;border-radius:2px;"></span>${escapeHtml(it.label)}`;
      legend.appendChild(span);
    });
    container.appendChild(legend);
  }

  // -----------------------------------------------------------------------
  // Simple bar chart. bars: [{label, value, color}]
  // -----------------------------------------------------------------------
  function barChart(container, { bars, width = 560, height = 260, formatter = "millions", headroom = 0.2 }) {
    clear(container);
    const fmt = resolveFormatter(formatter);
    const margin = { top: LABEL_TOP_MARGIN, right: 16, bottom: 40, left: 60 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;
    const domain = calculateDomain(bars.map((b) => b.value), headroom);
    const yMin = domain.min;
    const yMax = domain.max;
    const barW = w / bars.length / 1.6;
    const gap = w / bars.length;

    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}` });
    for (let i = 0; i <= 4; i++) {
      const v = yMin + ((yMax - yMin) * i) / 4;
      const y = margin.top + h - ((v - yMin) / (yMax - yMin || 1)) * h;
      svg.appendChild(svgEl("line", { x1: margin.left, x2: width - margin.right, y1: y, y2: y, stroke: GRIDLINE, "stroke-dasharray": "3,3" }));
      const t = svgEl("text", { x: margin.left - 8, y: y + 4, "font-size": 10, fill: GREY, "text-anchor": "end" });
      t.textContent = fmt(v);
      svg.appendChild(t);
    }
    const hitTargets = [];
    bars.forEach((b, i) => {
      const x = margin.left + i * gap + (gap - barW) / 2;
      const barTopY = margin.top + h - ((b.value - yMin) / (yMax - yMin || 1)) * h;
      const zeroY = margin.top + h - ((0 - yMin) / (yMax - yMin || 1)) * h;
      const y = Math.min(barTopY, zeroY);
      const barH = Math.abs(zeroY - barTopY) || 1;
      const color = b.color || PALETTE[i % PALETTE.length];
      svg.appendChild(svgEl("rect", { x, y, width: barW, height: barH, fill: color, rx: 3 }));
      const valLabel = svgEl("text", { x: x + barW / 2, y: y - 6, "font-size": 11, fill: NAVY, "text-anchor": "middle", "font-weight": "bold" });
      valLabel.textContent = fmt(b.value);
      svg.appendChild(valLabel);
      const catLabel = svgEl("text", { x: x + barW / 2, y: height - 12, "font-size": 11, fill: GREY, "text-anchor": "middle" });
      catLabel.textContent = b.label;
      svg.appendChild(catLabel);
      const hit = svgEl("rect", { x, y: margin.top, width: barW, height: h, fill: "transparent" });
      hitTargets.push({ hit, bar: b });
      svg.appendChild(hit);
    });
    container.appendChild(svg);
    container.style.position = "relative";
    hitTargets.forEach(({ hit, bar }) => {
      const buildHtml = () =>
        `<div class="chart-tooltip-header">${escapeHtml(bar.label)}</div><div class="chart-tooltip-row">${escapeHtml(fmt(bar.value))}</div>`;
      wireHitTarget(hit, container, buildHtml, `${bar.label}, ${fmt(bar.value)}`);
    });
  }

  // -----------------------------------------------------------------------
  // Grouped bar chart. groups: [{label, bars:[{seriesLabel, value, color}]}]
  // -----------------------------------------------------------------------
  function groupedBarChart(container, { groups, width = 560, height = 280, formatter = "millions", headroom = 0.2 }) {
    clear(container);
    const fmt = resolveFormatter(formatter);
    const margin = { top: LABEL_TOP_MARGIN, right: 16, bottom: 40, left: 60 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;
    const allVals = groups.flatMap((g) => g.bars.map((b) => b.value));
    const domain = calculateDomain(allVals, headroom);
    const yMin = domain.min;
    const yMax = domain.max;
    const groupGap = w / groups.length;
    const seriesCount = groups[0].bars.length;
    const groupInnerW = groupGap * 0.7;
    const barW = groupInnerW / seriesCount;

    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}` });
    for (let i = 0; i <= 4; i++) {
      const v = yMin + ((yMax - yMin) * i) / 4;
      const y = margin.top + h - ((v - yMin) / (yMax - yMin || 1)) * h;
      svg.appendChild(svgEl("line", { x1: margin.left, x2: width - margin.right, y1: y, y2: y, stroke: GRIDLINE, "stroke-dasharray": "3,3" }));
      const t = svgEl("text", { x: margin.left - 8, y: y + 4, "font-size": 10, fill: GREY, "text-anchor": "end" });
      t.textContent = fmt(v);
      svg.appendChild(t);
    }
    const hitTargets = [];
    groups.forEach((g, gi) => {
      const groupX = margin.left + gi * groupGap + (groupGap - groupInnerW) / 2;
      g.bars.forEach((b, bi) => {
        const x = groupX + bi * barW;
        const barTopY = margin.top + h - ((b.value - yMin) / (yMax - yMin || 1)) * h;
        const zeroY = margin.top + h - ((0 - yMin) / (yMax - yMin || 1)) * h;
        const y = Math.min(barTopY, zeroY);
        const barH = Math.abs(zeroY - barTopY) || 1;
        svg.appendChild(svgEl("rect", { x: x + 2, y, width: Math.max(barW - 4, 1), height: barH, fill: b.color || PALETTE[bi % PALETTE.length], rx: 2 }));
        const valLabel = svgEl("text", { x: x + barW / 2, y: y - 6, "font-size": 9.5, fill: NAVY, "text-anchor": "middle", "font-weight": "bold" });
        valLabel.textContent = fmt(b.value);
        svg.appendChild(valLabel);
        const hit = svgEl("rect", { x: x + 2, y: margin.top, width: Math.max(barW - 4, 1), height: h, fill: "transparent" });
        hitTargets.push({ hit, bar: b, group: g });
        svg.appendChild(hit);
      });
      const catLabel = svgEl("text", { x: groupX + groupInnerW / 2, y: height - 12, "font-size": 11, fill: GREY, "text-anchor": "middle" });
      catLabel.textContent = g.label;
      svg.appendChild(catLabel);
    });
    container.appendChild(svg);
    container.style.position = "relative";
    hitTargets.forEach(({ hit, bar, group }) => {
      const buildHtml = () =>
        `<div class="chart-tooltip-header">${escapeHtml(group.label)}</div><div class="chart-tooltip-row"><strong>${escapeHtml(bar.seriesLabel)}</strong> — ${escapeHtml(fmt(bar.value))}</div>`;
      wireHitTarget(hit, container, buildHtml, `${group.label}, ${bar.seriesLabel}, ${fmt(bar.value)}`);
    });
    const seriesLabels = groups[0].bars.map((b, i) => ({ label: b.seriesLabel, color: b.color || PALETTE[i % PALETTE.length] }));
    appendLegend(container, seriesLabels);
  }

  // -----------------------------------------------------------------------
  // Waterfall chart. steps: [{label, amount, isTotal}] -- isTotal steps
  // draw from 0 to their own value (e.g. Ending Cash); others draw as a
  // floating bar from running total to running total + amount.
  // -----------------------------------------------------------------------
  function waterfallChart(container, { steps, width = 1080, height = 320, formatter = "millions", headroom = 0.2 }) {
    clear(container);
    const fmt = resolveFormatter(formatter);
    const margin = { top: LABEL_TOP_MARGIN, right: 16, bottom: 90, left: 70 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;

    let running = 0;
    const bars = steps.map((s) => {
      const start = s.isTotal ? 0 : running;
      const end = s.isTotal ? s.amount : running + s.amount;
      if (!s.isTotal) running = end;
      else running = s.amount;
      return { ...s, start, end };
    });

    const allVals = bars.flatMap((b) => [b.start, b.end]);
    // Shared domain logic, applied without distorting source/use semantics:
    // the floating-bar start/end positions are unchanged, only the axis
    // range (and therefore top headroom for labels) comes from calculateDomain.
    const domain = calculateDomain(allVals, headroom);
    const yMin = domain.min;
    const yMax = domain.max;
    const yScale = (v) => margin.top + h - ((v - yMin) / (yMax - yMin || 1)) * h;
    const barW = (w / bars.length) * 0.6;
    const gap = w / bars.length;

    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}` });
    svg.appendChild(svgEl("line", { x1: margin.left, x2: width - margin.right, y1: yScale(0), y2: yScale(0), stroke: "#ccc" }));

    const hitTargets = [];
    bars.forEach((b, i) => {
      const x = margin.left + i * gap + (gap - barW) / 2;
      const y = yScale(Math.max(b.start, b.end));
      const barH = Math.abs(yScale(b.start) - yScale(b.end)) || 1;
      const color = b.isTotal ? NAVY : b.amount >= 0 ? GOOD : BAD;
      svg.appendChild(svgEl("rect", { x, y, width: barW, height: barH, fill: color, rx: 2 }));
      const label = svgEl("text", {
        x: x + barW / 2, y: y - 6, "font-size": 10, "text-anchor": "middle", fill: NAVY, "font-weight": "bold",
      });
      label.textContent = fmt(b.isTotal ? b.end : b.amount);
      svg.appendChild(label);

      const catLines = String(b.label).match(/.{1,16}(\s|$)/g) || [b.label];
      catLines.slice(0, 3).forEach((line, li) => {
        const catLabel = svgEl("text", {
          x: x + barW / 2, y: height - margin.bottom + 14 + li * 11, "font-size": 9.5, fill: GREY, "text-anchor": "middle",
        });
        catLabel.textContent = line.trim();
        svg.appendChild(catLabel);
      });

      const hit = svgEl("rect", { x, y: margin.top, width: barW, height: h, fill: "transparent" });
      hitTargets.push({ hit, bar: b });
      svg.appendChild(hit);
    });

    container.appendChild(svg);
    container.style.position = "relative";
    hitTargets.forEach(({ hit, bar }) => {
      const shown = bar.isTotal ? bar.end : bar.amount;
      const buildHtml = () =>
        `<div class="chart-tooltip-header">${escapeHtml(bar.label)}</div><div class="chart-tooltip-row">${escapeHtml(fmt(shown))}</div>`;
      wireHitTarget(hit, container, buildHtml, `${bar.label}, ${fmt(shown)}`);
    });
  }

  global.TargetCashCharts = {
    lineChart, barChart, groupedBarChart, waterfallChart,
    fmtM, Formatters, calculateDomain,
  };
})(window);
