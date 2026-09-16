# Cash Flow & Investment Capacity — Decision Cockpit

A static, dependency-free web app presenting the Target Corporation cash-
flow and investment-capacity model for a non-technical decision-maker or
recruiter. Built entirely from public SEC filings, with an explicit
FY2025 10-K information cutoff (2026-03-11).

**Not investment advice.** Every FY2026–FY2030 figure is a labeled
scenario forecast, not a prediction — see the "About / Limitations"
section on the page itself.

## What's in this folder

| Path | Purpose |
|---|---|
| `index.html` | The single-page app (10 sections — see below). |
| `css/style.css` | All styling. Responsive, no external stylesheet dependency. |
| `js/formulas.js` | A manually-maintained port of the Python forecast formula chain, used only by the client-side What-If Sandbox. |
| `js/charts.js` | Minimal hand-rolled SVG chart helpers (line, bar, waterfall) — zero charting-library dependency. |
| `js/app.js` | Fetches `data/model_data.json` and renders every section. |
| `data/model_data.json` | The single source of truth: historical facts, all 3 scenario forecasts, investment capacity, capital allocation waterfalls, DCF valuation, sensitivities, validation totals, source filings — all computed once by the real Python model (never recomputed by hand in this JSON). |
| `screenshots/` | Verified local-preview screenshots (desktop and mobile). |

## The 10 required interface areas

1. **Executive Snapshot** — answers the "30-second" requirement: headline KPIs, revenue/FCF trend, deployable capacity by scenario, scenario narrative.
2. **Historical Financial Trends** — FY2021–FY2025 actuals only.
3. **Cash-Flow Definitions** — the CFO / CapEx / CFI / FCF distinction, with the exact FY2025 reference values, so CapEx is never confused with total investing cash flow.
4. **Scenario Forecast Explorer** — FY2026–FY2030, selector-driven.
5. **Cash-Flow Bridge & Investment Capacity** — CFO → CapEx → FCF → Dividends → Deployable Capacity, plus the corrected (non-double-counted) cumulative capacity series.
6. **Capital Allocation Waterfall** — with a live no-double-counting proof banner.
7. **DCF Valuation & Sensitivities** — with a mandatory not-investment-advice disclaimer.
8. **What-If Assumption Sandbox** — editable assumptions with a "Reset to scenario defaults" button.
9. **Evidence & Sources** — every source filing, the filing-vintage (restatement) comparison, and the independent quarterly cash proof.
10. **About / Limitations** — recruiter-friendly project explanation and a documented limitations list.

## Regenerating the data

```
.venv/bin/python scripts/build_web_cockpit_data.py
```

This re-exports `data/model_data.json` from the live
`data/curated/target_cash.db` plus a live run of
`target_cash.forecast`/`target_cash.valuation` — never from cached or
hand-edited numbers.

## Local preview

No build step and no server-side code — this is a static site. It must
be served over HTTP (not opened via `file://`), because the page
`fetch()`es `data/model_data.json`, which browsers block under
`file://` for security reasons.

```
cd deliverables/web_cockpit
python3 -m http.server 8080
# then open http://localhost:8080/index.html
```

### Automated verification

```
.venv/bin/python scripts/verify_web_cockpit.py
```

This starts a local server, loads the page in headless Chromium
(Playwright), and checks: zero console/page errors; the Snapshot's KPIs
match the Python model exactly for all 3 scenarios; the CFO/CapEx/CFI/FCF
reference values render correctly and distinctly; the What-If sandbox
reproduces exact scenario defaults at zero delta and updates when a
slider moves, and its Reset button restores the exact original values;
the capital-allocation no-double-counting proof reads "OK"; 10 nav links
are present; and the page has no horizontal overflow at a 390px mobile
width. All 20 checks pass — see `docs/decisions.md`'s Milestone 7 entry
for the full run, including one real responsive-layout bug this check
found and fixed (a CSS grid-item min-width issue causing horizontal
overflow at mobile width, fixed by adding `min-width: 0` to `.chart-card`).

## Deployment (not done — requires explicit authorization)

This is a static site and can be deployed to any static host (GitHub
Pages, Netlify, Vercel, S3+CloudFront) with no server-side component:

1. Copy the contents of this folder (`index.html`, `css/`, `js/`,
   `data/`) to the host's publish directory.
2. No build step, no environment variables, no secrets are required.
3. To refresh the data after a new filing is ingested, re-run
   `scripts/build_web_cockpit_data.py` and redeploy the updated
   `data/model_data.json`.

**This project has not been deployed publicly.** Per the project's
governing rules, it will not be published externally without the
project owner's explicit authorization.

## What this is not

- Not a live-data application — there is no server, no database
  connection from the browser, and no real-time market data of any
  kind. `data/model_data.json` is a point-in-time export.
- Not an AI chatbot — there is no conversational interface here by
  design; every number is sourced and citable, not generated on demand.
- Not investment advice — see the disclaimer in the DCF section and the
  "About / Limitations" section on the page itself.
