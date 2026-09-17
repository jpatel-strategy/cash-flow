# Web Cockpit — UI/UX Audit

**Purpose**: a pre-implementation visual audit of `deliverables/web_cockpit/`, performed by serving the site locally and inspecting it in a real headless browser (Playwright + the pre-installed Chromium) at 1440×1000 (desktop), 1024×768 (tablet), and 390×844 (mobile), plus targeted section screenshots. This is a record of what was found, not a design brief — the fixes are implemented directly afterward per the instruction not to stop for approval on non-financial UI changes.

**Method**: `python3` scripts served `deliverables/web_cockpit/` on a local port and drove Chromium via Playwright to screenshot the full page and each `<section>` at each viewport, then dumped `innerHTML`/computed layout for anything that looked visually wrong, to distinguish a real bug from a screenshot artifact. Static source (`index.html`, `css/style.css`, `js/app.js`, `js/charts.js`) was read alongside every visual finding — no finding below is source-only or screenshot-only.

**Baseline commit audited**: `27bab65` (the frozen, approved financial/data commit).

---

## 1. Stale committed screenshots (confirmed, not assumed)

`deliverables/web_cockpit/screenshots/01_snapshot_base.png` (dated 2026‑09‑16 02:03, **before** the final independent-audit closeout commits) was opened and inspected directly. It shows, as bare, unlabeled headline KPI cards:

- **"DEPLOYABLE CAPACITY, FY2030"** and **"CUMULATIVE DEPLOYABLE CAPACITY"** — the exact legacy, ambiguous labels the closeout explicitly forbids as unlabeled executive KPIs.
- **"257/257 PASS"** — a stale validation total; the current model reports 470/470 (229 forecast + 28 valuation + 213 capacity).
- A bar chart ("Deployable Capacity by Scenario, FY2030") coloring **Upside green and Downside red** — status colors (good/bad) applied to scenario identity, not to an actual pass/fail state.

All 5 committed screenshots predate the closeout and must be treated as **stale and not representative of the current build**. They are superseded in this phase (§21 of the task) after the rebuild is verified, not reused.

## 2. Broken layout: horizon-reconciliation table (desktop, confirmed via DOM inspection)

The "Cumulative Capacity Reconciliation, FY2026–FY2030" table (`#table-capacity-horizon`) sits in a half-width `.chart-card` next to a line chart. Its `innerHTML` confirms every row has a value (e.g. `Net Horizon Deployable Capacity … → $9,175M`), but the **label column text is long enough** (e.g. "Net Horizon Deployable Capacity (corrected headline figure, replaces legacy gross total)") that in the fixed-width half-card the **value column is pushed outside the visible frame**, with no visible scrollbar affordance at rest — a recruiter scanning the page sees a column of labels and no numbers at all unless they know to scroll the card horizontally. Confirmed via screenshot (`desktop_horizon_table.png`) showing only the label column with no visible dollar figures, matching the DOM dump proving the values exist. This is the single most damaging finding: **the differentiating gross/net reconciliation — the strongest evidence of the project's core correction — is effectively invisible on first paint.**

## 3. Misleading chart: mixed units on one linear axis (confirmed via screenshot)

"Diluted EPS & Margins" (`#chart-forecast-margins`) plots **Diluted EPS in dollars (~$8)**, **Gross Margin %  (~28)**, and **Operating Margin % (~5)** as three lines on a single shared linear y-axis scaled to the max value across all three (~$31). Result, confirmed visually: Gross Margin renders near the top of the chart, while EPS and Operating Margin both render as nearly flat lines pinned near zero — none of the three series' actual year-over-year movement is legible. This is a textbook mixed-unit/dual-axis-avoidance violation (per the dataviz skill's non-negotiables: "Two measures of different scale → two charts, small multiples, or indexed to a common base," never one shared linear axis for unlike units).

## 4. Scenario color mapping reuses status colors for identity (confirmed in source + screenshot)

`app.js` line 7: `SCENARIO_COLORS = { base: "#1F3864" (navy), upside: "#548235" (GOOD/green), downside: "#C00000" (BAD/red) }`. Every scenario-colored bar and line in the cockpit (headroom-by-scenario bar chart, etc.) paints Downside red and Upside green. This directly conflates a categorical identity (which scenario) with a status signal (pass/fail, good/bad) — confirmed as an anti-pattern by the dataviz skill ("status colors are reserved... never reused for series identity") and explicitly called out as a requirement to avoid in the task brief ("red for failures or risk, not merely for the Downside scenario").

## 5. Weak hierarchy: deprecated content precedes the corrected content, at equal visual weight

In the Cash-Flow Bridge section, the legacy waterfall (ending in "Legacy Gross Ceiling (DEPRECATED)") and its accompanying table row "Legacy Gross Capacity (deprecated)" / "Deprecated: Self-Funded Gross Capacity… (v1-style, never labeled 'generated')" render **before** the "Corrected Capacity Taxonomy" heading, in the same card style and font weight as everything else. A recruiter scanning top-to-bottom sees deprecated content first, with no visual demotion (muted color, collapsed/expandable state, smaller type) to signal "this is legacy, skip unless you want the before/after."

## 6. Executive KPI row does not match the required decision hierarchy

Current top KPI row (`#kpi-grid`): Revenue, FCF, Implied DCF Value/Share, Validation Status, **Net Debt (Valuation Date)**, **Funding Warning?**. The two required decision metrics — **Net Horizon Deployable Capacity** and **FY2030 Remaining Deployable Headroom** — are absent from this primary row; they only appear one scroll-length down, in the secondary `#capacity-kpi-grid`, and Remaining Headroom only appears inside a taxonomy grid, never as an executive card. Net Debt and Funding Warning are lower-priority context, not top-six material per the required hierarchy.

## 7. Mobile: header + nav consume nearly the entire first viewport

At 390×844, the sticky-less header (brand + 6 badges + 10-item nav, wrapped) measures roughly 640px tall before any page content appears — over 75% of the mobile viewport's height on first load. A recruiter opening the link on a phone sees almost nothing but chrome before scrolling. (Confirmed via screenshot `mobile_390x844_top.png`.) This is compounded by 10 flat nav links with no grouping or collapse behavior on small screens.

## 8. What-if lab is not visually distinguished from authoritative results

The What-If Sandbox result cards use the exact same `.kpi-grid`/`.kpi-card` markup and styling as every authoritative KPI elsewhere on the page. Aside from one sentence of prose above the form and a light-yellow section background, there is no visual language (border treatment, icon, "illustrative" watermark, distinct card style) marking these numbers as browser-only and non-authoritative — a screenshot taken mid-scroll could easily be mistaken for a published result. There is also no baseline-vs-what-if side-by-side comparison and no "changed input" indicator; only a flat reset button.

## 9. No section-aware navigation, no 30-second tour, no scenario comparison mode

The nav bar (`.site-nav`) never indicates which section is currently in view while scrolling (no active-state class, no scrollspy). There is no "30-second tour" scaffold near the top (the three-step "what happened / what could happen / what can safely be deployed" framing the brief requires). There is no compact Base/Upside/Downside comparison view for the key decision metrics — a reviewer must click through each scenario button and rely on memory to compare.

## 10. Accessibility gaps (confirmed in source)

- All charts are inline SVG rendered into a `<div role="img" aria-label="...">`, but the SVG itself is additionally marked `aria-hidden="true"` (`charts.js`), and the `aria-label` on the wrapping `div` is a static, generic string (e.g. "Revenue and free cash flow chart") that does not summarize the actual data — a screen-reader user gets a label but no data.
- No `prefers-reduced-motion` handling exists (moot today since there is no animation, but not future-proofed).
- No `<caption>`-equivalent accessible summary exists for any `.data-table` beyond the plain `<caption>` text already present on 2 of 9 tables.
- Heatmap sensitivity tables (WACC × terminal growth, margin × revenue growth) rely on background color alone to convey magnitude, with no pattern/texture or explicit value-based fallback for a colorblind or color-off context beyond the numeric text itself (numeric text is present, which partially mitigates this — but there's no legend explaining the color ramp).
- No visible focus outline was audited under keyboard-only navigation before this pass (existing `:focus-visible` outline exists in CSS and is a reasonable baseline, but no explicit skip-link target check or landmark-role audit had been done).

## 11. No downloads section

There is no section offering the Excel model, the Power BI handoff package, the executive case study, the methodology/evidence doc, or a link to the GitHub repository — despite all of these existing in the repo already. A recruiter or reviewer who wants to go deeper than the page has no in-page path to do so.

## 12. No deployment metadata

No Open Graph tags, no `robots.txt`, no social-preview image, no favicon beyond an inline data-URI SVG (functional but not ideal for OG previews), and no GitHub Pages / static-hosting workflow exists yet.

## 13. Stale phrasing in the portfolio package (confirmed by direct grep)

`deliverables/portfolio_package/04_data_dictionary.md` still reads **"13 named capacity-taxonomy identities"** in one place (the count was 13 in Part I, then 18, now 19 after the final closeout's `net_horizon_capacity_reconciles` check) — flagged explicitly in this phase's brief as "14 named capacity-taxonomy identities" (the brief's own recollection is slightly off in wording but the defect it points at is real and confirmed); corrected to **"19 named capacity-taxonomy checks."**

## 14. What was checked and found acceptable (no change needed)

- No horizontal page overflow at any of the 3 required viewports on first paint (`document.body.scrollWidth` == viewport width at all three, verified via Playwright `page.evaluate`).
- No bare, unlabeled legacy KPI (`Deployable Capacity`, `Cumulative Deployable Capacity`, `total_horizon_capacity_accessible`) renders anywhere in the **current** build — the existing `scripts/verify_web_cockpit.py` already enforces this and passes (44/44) against the current `model_data.json`. Only the *stale committed screenshots* (§1) show the old, pre-correction labels.
- Gross vs. net horizon figures are present, correctly computed, and reconcile exactly (verified in the previous phase); the defect here is purely presentational (§2), not numerical.
- The scenario selector already updates all cards/charts/tables/narrative consistently (`app.js`'s single `render()` re-entry point keyed off `currentScenario`) and already supports basic keyboard operability as native `<button>` elements.
- Base architecture (static HTML/CSS/JS reading a single generated `model_data.json`, no backend, no build step) already matches the required architecture exactly — no rebuild needed, only refinement.

---

## Disposition

Every finding above is addressed directly in this phase's implementation (see the phase's final report for the corresponding fix, file, and verification). No finding here implicates a financial formula, a historical fact, a scenario assumption, a validation definition, or a capacity-taxonomy methodology — every fix is presentational, structural, or navigational, consistent with the instruction to freeze approved financial logic.
