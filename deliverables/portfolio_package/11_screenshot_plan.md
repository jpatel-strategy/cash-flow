# Screenshot Plan

Which screenshots to use, and where — for a portfolio site, LinkedIn
carousel, or resume-linked project page. All source images already
exist and are verified (see `deliverables/web_cockpit/screenshots/` and
below); this file just says how to use them.

## Already captured (web cockpit)

| File | Use it for |
|---|---|
| `deliverables/web_cockpit/screenshots/01_snapshot_base.png` | **Primary hero image.** The Executive Snapshot at default (Base) scenario — this is the single best image for a portfolio homepage, LinkedIn post, or resume link preview. Shows KPIs, the actual-vs-forecast chart, and the scenario narrative in one frame. |
| `deliverables/web_cockpit/screenshots/02_cash_definitions.png` | Use when the audience is finance-literate and you want to make the CFO/CapEx/CFI/FCF distinction point directly (e.g. in a comment reply or a technical interview follow-up). |
| `deliverables/web_cockpit/screenshots/03_dcf_valuation.png` | Use for a valuation-focused audience or when discussing the DCF/sensitivity methodology. |
| `deliverables/web_cockpit/screenshots/04_whatif_sandbox.png` | Use to demonstrate interactivity — good for a LinkedIn carousel's second slide ("and you can actually play with the assumptions"). |
| `deliverables/web_cockpit/screenshots/05_mobile_snapshot.png` | Use once, to demonstrate responsive design, if the portfolio format allows a second image (e.g. "works on mobile too"). |

## Additional screenshots worth capturing before publishing externally

These require opening the actual Excel workbook and are not yet
captured (Excel itself is not available in this build environment — see
`05_model_risk_and_limitations.md`). If presenting from a machine with
Excel installed:

1. The Excel workbook's **Executive Summary** sheet (Sheet 2) — shows
   the chart and the side-by-side scenario comparison table.
2. The Excel workbook's **Scenario Forecast** sheet (Sheet 7) with the
   scenario-selector dropdown visible at the top, to show the live-
   formula interactivity.
3. The Power BI handoff's **wireframe mockups**
   (`deliverables/powerbi_handoff/wireframes/*.svg`) — these are
   schematic, not real product screenshots, and should be captioned as
   such if used ("wireframe spec, not a live Power BI screenshot").

## Recommended carousel order (LinkedIn / portfolio site, 4-5 slides)

1. `01_snapshot_base.png` — "Here's the whole story in one screen."
2. `04_whatif_sandbox.png` — "And you can actually change the
   assumptions."
3. `02_cash_definitions.png` — "Getting CFO vs. CapEx vs. CFI right,
   explicitly."
4. `03_dcf_valuation.png` — "A restrained, labeled DCF."
5. A cropped section of `docs/decisions.md` (text, not a screenshot of
   the whole file — pick one dated entry, e.g. the cumulative-capacity
   bug fix) — "and here's the bug I found and fixed, documented as I
   found it."

## Captioning rules (apply to every image used externally)

- Never caption a wireframe SVG as a "Power BI screenshot" — caption it
  as a wireframe/mockup, per the project's own honesty rule about the
  Power BI package.
- Always caption DCF-related images with a one-line reminder that it is
  scenario analysis, not investment advice, if the image will be seen
  outside a context that already carries that disclaimer.
- Do not add sensitive-looking data — there is none in this project
  (it's 100% public SEC data), but this rule stands for future updates.
