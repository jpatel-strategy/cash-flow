# Target Cash Flow & Investment Capacity Decision Cockpit — Recruiter Package

**Independent portfolio case study. Not affiliated with Target Corporation.**
Forecasts and valuation outputs are scenario-based analytical assumptions,
not investment advice or price targets. The primary recruiter entry point
is the live web decision cockpit:
**https://jpatel-strategy.github.io/cash-flow/**
(source in `deliverables/web_cockpit/`; deploy status and audit history in
`docs/ui_ux_audit.md`).

**What this is**: an independent, public-data FP&A / strategic-finance
case study built entirely from Target Corporation's SEC filings — no
proprietary data, no non-public information, no analyst estimates. It
covers the full lifecycle a corporate finance or strategic-finance team
would run: historical fact extraction and validation, a scenario-based
operating forecast, an investment-capacity and capital-allocation
framework, a restrained DCF valuation, and four presentation layers
(Excel, Power BI handoff, a web decision cockpit, and this recruiter
package) — all built on a reproducible, auditable data pipeline.

**Who this is for**: hiring teams evaluating candidates for **FP&A,
strategic finance, finance transformation, business operations, retail
operations, supply-chain finance, or operations analytics** roles. This
project is a demonstration of financial and operational judgment
supported by technical execution — not a software-engineering portfolio
piece. See `06_positioning_note.md` for why that distinction matters and
how this package is deliberately framed around it.

## Start here, in this order

| # | File | What it's for |
|---|---|---|
| 1 | `01_executive_case_study.md` | The full story: problem, approach, findings, results. Read this first. |
| 2 | `02_technical_architecture_summary.md` | How the pipeline is built, for a technical reviewer or interviewer who asks "how does it actually work." |
| 3 | `03_finance_methodology_summary.md` | The accounting and finance judgment calls — the substance a finance hiring manager will actually probe. |
| 4 | `04_data_dictionary.md` | Every table, every metric, every source. |
| 5 | `05_model_risk_and_limitations.md` | What this model does NOT claim, and why — a model-risk statement, not a disclaimer buried in fine print. |
| 6 | `06_positioning_note.md` | How to talk about this project in an FP&A/strategic-finance context (and how not to). |
| 7 | `07_demo_script.md` | A live-walkthrough script (~8-10 minutes) for an interview or portfolio review. |
| 8 | `08_interview_explanations.md` | A 30-second and a 2-minute verbal explanation, written out. |
| 9 | `09_resume_bullets.md` | Ready-to-use resume bullet points. |
| 10 | `10_linkedin_draft.md` | A draft LinkedIn post announcing the project. |
| 11 | `11_screenshot_plan.md` | Which screenshots to take, from where, for a portfolio site or LinkedIn carousel. |
| 12 | `12_final_project_inventory.md` | Every deliverable, every file, every commit — the complete manifest. |
| 13 | `13_reproduction_instructions.md` | Exact commands to rebuild the entire project from source filings, from scratch. |
| 14 | `14_linkedin_launch_package.md` | Public-release launch package: final LinkedIn post, 6-slide carousel plan, 5-minute recruiter demo order, and three role-targeted resume bullet sets. Prepared, not published. |

## The one-sentence version

Built a full-stack FP&A model for Target Corporation from public SEC
filings only — historical validation (catching a real, undisclosed
segment-expense reclassification), a 3-scenario 5-year forecast with a
provably non-double-counted capital-allocation framework, a restrained
DCF, and four decision-support deliverables (Excel, Power BI, a web
cockpit, and this package) — all backed by 467 automated tests, a
reproducible clean-room rebuild, and full source-to-output lineage.

## What to actually look at, if short on time

1. The web decision cockpit (`deliverables/web_cockpit/`) — open
   `index.html` via a local HTTP server for the fastest, most visual
   overview of the whole project.
2. `01_executive_case_study.md` in this folder — the written narrative.
3. `docs/decisions.md` — the full, honest record of every material
   decision, every bug found and fixed, and every limitation, across
   all 8 milestones. This is the strongest evidence of judgment and
   rigor in the whole project — most portfolio pieces do not have an
   equivalent document.
