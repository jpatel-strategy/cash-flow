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
  const GREY = "#7F7F7F";
  const GOOD = "#548235";
  const BAD = "#C00000";
  // Fixed categorical order for identity (never cycled, never reused for status).
  // GOOD/BAD are reserved for pass/fail and positive/negative deltas only --
  // never for scenario identity (a scenario is not a "failure").
  const PALETTE = [NAVY, GOLD, TEAL, "#2E75B6", "#8A5A44"];

  function svgEl(tag, attrs) {
    const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const k in attrs) el.setAttribute(k, attrs[k]);
    return el;
  }

  function fmtM(v) {
    if (v === null || v === undefined || Number.isNaN(v)) return "—";
    return "$" + Math.round(v).toLocaleString() + "M";
  }

  function clear(container) {
    container.innerHTML = "";
  }

  /** Multi-series line chart. series: [{label, points:[{fy, value}], dashed, color}] */
  function lineChart(container, { series, width = 560, height = 260, yLabel = "" }) {
    clear(container);
    const margin = { top: 16, right: 16, bottom: 30, left: 60 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;

    const allPoints = series.flatMap((s) => s.points);
    const xs = [...new Set(allPoints.map((p) => p.fy))].sort((a, b) => a - b);
    const ys = allPoints.map((p) => p.value);
    const yMin = Math.min(0, ...ys);
    const yMax = Math.max(...ys) * 1.1;

    const xScale = (fy) => margin.left + ((fy - xs[0]) / (xs[xs.length - 1] - xs[0] || 1)) * w;
    const yScale = (v) => margin.top + h - ((v - yMin) / (yMax - yMin || 1)) * h;

    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, "aria-hidden": "true" });

    // gridlines + y-axis labels
    const gridCount = 4;
    for (let i = 0; i <= gridCount; i++) {
      const v = yMin + ((yMax - yMin) * i) / gridCount;
      const y = yScale(v);
      svg.appendChild(svgEl("line", { x1: margin.left, x2: width - margin.right, y1: y, y2: y, stroke: "#eee" }));
      const t = svgEl("text", { x: margin.left - 8, y: y + 4, "font-size": 10, fill: GREY, "text-anchor": "end" });
      t.textContent = fmtM(v);
      svg.appendChild(t);
    }

    // x-axis labels
    xs.forEach((fy) => {
      const t = svgEl("text", { x: xScale(fy), y: height - 8, "font-size": 10, fill: GREY, "text-anchor": "middle" });
      t.textContent = "FY" + fy;
      svg.appendChild(t);
    });

    series.forEach((s, i) => {
      const color = s.color || PALETTE[i % PALETTE.length];
      const pts = s.points.slice().sort((a, b) => a.fy - b.fy);
      const d = pts.map((p, idx) => `${idx === 0 ? "M" : "L"} ${xScale(p.fy)} ${yScale(p.value)}`).join(" ");
      const path = svgEl("path", {
        d, fill: "none", stroke: color, "stroke-width": 2.5,
        "stroke-dasharray": s.dashed ? "6,4" : "none",
      });
      svg.appendChild(path);
      pts.forEach((p) => {
        svg.appendChild(svgEl("circle", { cx: xScale(p.fy), cy: yScale(p.value), r: 3, fill: color }));
      });
    });

    container.appendChild(svg);
    appendLegend(container, series.map((s, i) => ({ label: s.label, color: s.color || PALETTE[i % PALETTE.length] })));
  }

  function appendLegend(container, items) {
    const legend = document.createElement("div");
    legend.style.display = "flex";
    legend.style.flexWrap = "wrap";
    legend.style.gap = "12px";
    legend.style.marginTop = "6px";
    legend.style.fontSize = "0.78rem";
    items.forEach((it) => {
      const span = document.createElement("span");
      span.innerHTML = `<span style="display:inline-block;width:10px;height:10px;background:${it.color};margin-right:4px;border-radius:2px;"></span>${it.label}`;
      legend.appendChild(span);
    });
    container.appendChild(legend);
  }

  /** Simple bar chart. bars: [{label, value, color}] */
  function barChart(container, { bars, width = 560, height = 260 }) {
    clear(container);
    const margin = { top: 16, right: 16, bottom: 40, left: 60 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;
    const maxV = Math.max(...bars.map((b) => b.value), 0);
    const barW = w / bars.length / 1.6;
    const gap = w / bars.length;

    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, "aria-hidden": "true" });
    for (let i = 0; i <= 4; i++) {
      const v = (maxV * i) / 4;
      const y = margin.top + h - (v / maxV) * h;
      svg.appendChild(svgEl("line", { x1: margin.left, x2: width - margin.right, y1: y, y2: y, stroke: "#eee" }));
      const t = svgEl("text", { x: margin.left - 8, y: y + 4, "font-size": 10, fill: GREY, "text-anchor": "end" });
      t.textContent = fmtM(v);
      svg.appendChild(t);
    }
    bars.forEach((b, i) => {
      const x = margin.left + i * gap + (gap - barW) / 2;
      const barH = (b.value / (maxV || 1)) * h;
      const y = margin.top + h - barH;
      svg.appendChild(svgEl("rect", { x, y, width: barW, height: barH, fill: b.color || PALETTE[i % PALETTE.length], rx: 3 }));
      const valLabel = svgEl("text", { x: x + barW / 2, y: y - 6, "font-size": 11, fill: NAVY, "text-anchor": "middle", "font-weight": "bold" });
      valLabel.textContent = fmtM(b.value);
      svg.appendChild(valLabel);
      const catLabel = svgEl("text", { x: x + barW / 2, y: height - 12, "font-size": 11, fill: GREY, "text-anchor": "middle" });
      catLabel.textContent = b.label;
      svg.appendChild(catLabel);
    });
    container.appendChild(svg);
  }

  /** Grouped bar chart. groups: [{label, bars:[{seriesLabel, value, color}]}] */
  function groupedBarChart(container, { groups, width = 560, height = 280 }) {
    clear(container);
    const margin = { top: 24, right: 16, bottom: 40, left: 60 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;
    const allVals = groups.flatMap((g) => g.bars.map((b) => b.value));
    const maxV = Math.max(...allVals, 0);
    const groupGap = w / groups.length;
    const seriesCount = groups[0].bars.length;
    const groupInnerW = groupGap * 0.7;
    const barW = groupInnerW / seriesCount;

    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, "aria-hidden": "true" });
    for (let i = 0; i <= 4; i++) {
      const v = (maxV * i) / 4;
      const y = margin.top + h - (v / (maxV || 1)) * h;
      svg.appendChild(svgEl("line", { x1: margin.left, x2: width - margin.right, y1: y, y2: y, stroke: "#eee" }));
      const t = svgEl("text", { x: margin.left - 8, y: y + 4, "font-size": 10, fill: GREY, "text-anchor": "end" });
      t.textContent = fmtM(v);
      svg.appendChild(t);
    }
    groups.forEach((g, gi) => {
      const groupX = margin.left + gi * groupGap + (groupGap - groupInnerW) / 2;
      g.bars.forEach((b, bi) => {
        const x = groupX + bi * barW;
        const barH = ((b.value || 0) / (maxV || 1)) * h;
        const y = margin.top + h - barH;
        svg.appendChild(svgEl("rect", { x: x + 2, y, width: Math.max(barW - 4, 1), height: barH, fill: b.color || PALETTE[bi % PALETTE.length], rx: 2 }));
        const valLabel = svgEl("text", { x: x + barW / 2, y: y - 6, "font-size": 9.5, fill: NAVY, "text-anchor": "middle", "font-weight": "bold" });
        valLabel.textContent = fmtM(b.value);
        svg.appendChild(valLabel);
      });
      const catLabel = svgEl("text", { x: groupX + groupInnerW / 2, y: height - 12, "font-size": 11, fill: GREY, "text-anchor": "middle" });
      catLabel.textContent = g.label;
      svg.appendChild(catLabel);
    });
    container.appendChild(svg);
    const seriesLabels = groups[0].bars.map((b, i) => ({ label: b.seriesLabel, color: b.color || PALETTE[i % PALETTE.length] }));
    appendLegend(container, seriesLabels);
  }

  /** Waterfall chart. steps: [{label, amount, isTotal}] -- isTotal steps
   * draw from 0 to their own value (e.g. Ending Cash); others draw as a
   * floating bar from running total to running total + amount. */
  function waterfallChart(container, { steps, width = 1080, height = 320 }) {
    clear(container);
    const margin = { top: 24, right: 16, bottom: 90, left: 70 };
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
    const yMin = Math.min(0, ...allVals);
    const yMax = Math.max(...allVals) * 1.15;
    const yScale = (v) => margin.top + h - ((v - yMin) / (yMax - yMin || 1)) * h;
    const barW = (w / bars.length) * 0.6;
    const gap = w / bars.length;

    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, "aria-hidden": "true" });
    svg.appendChild(svgEl("line", { x1: margin.left, x2: width - margin.right, y1: yScale(0), y2: yScale(0), stroke: "#ccc" }));

    bars.forEach((b, i) => {
      const x = margin.left + i * gap + (gap - barW) / 2;
      const y = yScale(Math.max(b.start, b.end));
      const barH = Math.abs(yScale(b.start) - yScale(b.end)) || 1;
      const color = b.isTotal ? NAVY : b.amount >= 0 ? GOOD : BAD;
      svg.appendChild(svgEl("rect", { x, y, width: barW, height: barH, fill: color, rx: 2 }));
      const label = svgEl("text", {
        x: x + barW / 2, y: y - 6, "font-size": 10, "text-anchor": "middle", fill: NAVY, "font-weight": "bold",
      });
      label.textContent = fmtM(b.isTotal ? b.end : b.amount);
      svg.appendChild(label);

      const catLines = String(b.label).match(/.{1,16}(\s|$)/g) || [b.label];
      catLines.slice(0, 3).forEach((line, li) => {
        const catLabel = svgEl("text", {
          x: x + barW / 2, y: height - margin.bottom + 14 + li * 11, "font-size": 9.5, fill: GREY, "text-anchor": "middle",
        });
        catLabel.textContent = line.trim();
        svg.appendChild(catLabel);
      });
    });

    container.appendChild(svg);
  }

  global.TargetCashCharts = { lineChart, barChart, groupedBarChart, waterfallChart, fmtM };
})(window);
