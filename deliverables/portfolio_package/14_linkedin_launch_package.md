# LinkedIn Launch Package (public release)

Prepared for the public release of the decision cockpit. **Nothing in this
file has been published** — it is prepared for the project owner to review
and post manually.

- Live cockpit: https://jpatel-strategy.github.io/cash-flow/
- Repository: https://github.com/jpatel-strategy/cash-flow

---

## A. Final LinkedIn post (ready to post)

Every finance team eventually runs into a version of the same question:
how much cash can we actually deploy without quietly double-counting the
pile already sitting on the balance sheet? I built an independent,
public-data model to answer that for Target Corporation — a 3-scenario,
5-year cash-flow and investment-capacity forecast, built entirely from
SEC filings (10-Ks and 10-Qs, each cited by accession number).

Two findings shaped the project more than I expected. First, cross-
checking the same historical quarters across filing vintages surfaced a
real cost-of-sales/SG&A reclassification the company made to two prior
fiscal years — a reminder that a single filing's numbers aren't always
the final word. Second, my own headline "deployable capacity" metric
failed three separate audits before it was right: it was double-counting
cash carried forward year to year, then blending self-funded cash with
new borrowing, then still counting gross debt issuance as capacity even
when it was repaid in the same year. Each fix is documented, not quietly
overwritten.

One result surprised me. The Upside scenario — the highest revenue and
EPS of the three — ends FY2030 with *less* undeployed headroom than
either Base or Downside, because it puts more of its cash to work rather
than letting it sit idle. Performing best and having the most left over
turned out not to be the same question.

The model, tests, and full decision log are reproducible from source.

Interactive cockpit: https://jpatel-strategy.github.io/cash-flow/
Code and evidence: https://github.com/jpatel-strategy/cash-flow

External case study — not investment advice, not affiliated with or
adopted by Target.

#FPandA #StrategicFinance #FinancialModeling #CorporateFinance #DataDriven

*(Word count: within the 180–300 word target. See `10_linkedin_draft.md`
for an earlier, longer draft with a different narrative framing —
this version is the one written to this release's specific
requirements: leads with the business question, names both the
historical and capacity findings explicitly, and states the
counterintuitive Upside-headroom result plainly.)*

---

## B. LinkedIn carousel plan (6 slides)

Use existing verified screenshots from `deliverables/web_cockpit/screenshots/`
wherever possible; only slide 2 needs a new simple diagram (the mermaid
architecture chart in the root `README.md`, exported as an image, or
recreated as a plain text/box diagram for the carousel).

1. **Business question** — "How much capital can Target deploy without
   double-counting liquidity or compromising its operating cash
   reserve?" Plain text slide, no screenshot — this is the hook.
2. **SEC-to-decision architecture** — the evidence-chain diagram (SEC
   filings → curated database → Python model → Excel / Power BI / web
   cockpit → validation gates). Use the root README's mermaid diagram,
   rendered as an image.
3. **Historical filing-vintage finding** — screenshot
   `03_historical_evidence.png`, captioned with the ~$77–92M cost-of-
   sales/SG&A reclassification finding.
4. **Corrected capacity waterfall** — screenshot
   `04_corrected_capacity_waterfall.png`, captioned with the three-audit
   correction story (2.6x–3.8x overstatement caught and fixed).
5. **Scenario comparison and the counterintuitive Upside result** —
   screenshot `02_scenario_comparison.png`, captioned with the Upside
   headroom finding: highest revenue and EPS, lowest remaining
   deployable headroom, because more cash is put to work rather than
   held idle.
6. **Evidence, limitations, live demo, GitHub** — screenshot
   `08_audit_evidence_panel.png`, captioned with the validation totals
   (467 tests, 41 Excel checks, 114 web-cockpit checks) plus both links
   (live cockpit, GitHub) and the external-case-study / not-investment-
   advice disclaimer.

---

## C. Recruiter demo order (5 minutes)

A tighter version of the full 8–10 minute walkthrough in
`07_demo_script.md`, for a time-constrained recruiter screen or a
LinkedIn video walkthrough:

1. **Executive Snapshot** (~1 min) — the 30-second framing: what
   happened historically, what's expected under each scenario, how much
   cash the business generates.
2. **Historical evidence** (~1 min) — the FY2025 CFO/CapEx/CFI/FCF
   reference values and the filing-vintage cross-check that caught the
   cost-of-sales/SG&A reclassification.
3. **Corrected capacity waterfall** (~1.5 min) — the no-double-counting
   proof and the three-audit correction story (self-funded vs.
   debt-funded capacity, discretionary deployment, remaining headroom).
4. **Scenario comparison** (~1 min) — switch Base → Upside → Downside
   live; land on the counterintuitive Upside-headroom result.
5. **Audit evidence and limitations** (~30 sec) — the Evidence & Sources
   panel, the validation totals, and a direct pointer to
   `05_model_risk_and_limitations.md` — closing on what the model does
   NOT claim.

---

## D. Resume bullets (three role-targeted versions)

Numbers are drawn from this project's own validated output; do not alter
the figures. Pick 2–4 per version depending on space. (See
`09_resume_bullets.md` for the original, differently-grouped bullet set —
this version splits Finance Transformation out from BizOps/Operations
Analytics per the release spec.)

### FP&A / Strategic Finance

- Built an independent 3-scenario (Base/Upside/Downside), 5-year cash-flow
  forecast and investment-capacity model for a Fortune 500 retailer from
  public SEC filings, with a capital-allocation framework proven
  non-double-counted across five mutually exclusive uses of cash.
- Found and corrected a capacity-metric error overstating deployable cash
  by 2.6x–3.8x across scenarios, then caught two further, subtler defects
  in follow-up audits — redesigning the metric into a taxonomy that
  separates self-funded capacity, debt-funded capacity, discretionary
  deployment, and remaining headroom.
- Identified a real SEC filing-vintage reclassification (~$77–92M moved
  between cost of sales and SG&A across two fiscal years) by
  cross-validating historical facts across multiple 10-K filings.
- Built a restrained, scenario-based DCF valuation with an explicit WACC
  build and sensitivity analysis across discount rate, terminal growth,
  margin, and revenue-growth assumptions; delivered across a live-formula
  Excel workbook, a Power BI-ready package, and an interactive web
  cockpit.

### BizOps / Operations Analytics

- Designed and shipped a self-serve decision cockpit translating a
  multi-scenario financial model into an interactive tool a
  non-technical stakeholder can use directly — including a live what-if
  sandbox that is visually and functionally separated from published,
  authoritative figures.
- Built a validated data pipeline (filing ingestion → historical facts →
  scenario forecast → decision-ready exports) with full field-level
  lineage from every displayed number back to its source filing.
- Ran a from-scratch, clean-room reproducibility rebuild, verified
  byte-identical to the production database, backed by 467 automated
  tests and a dated log of every material judgment call and bug fix.
- Established a validation taxonomy distinguishing arithmetic internal-
  consistency checks from genuinely independent reasonableness tests —
  and documented which was which, rather than presenting one as the
  other.

### Finance Transformation

- Replaced a single, ambiguous "deployable capacity" figure with a
  six-concept taxonomy (opening liquidity as a stock, self-funded and
  debt-funded capacity as flows, discretionary deployment as a use, a
  forward reserve, and remaining headroom as the decision KPI) after
  three rounds of self-audit — an additive migration with zero changes
  to historical facts or forecast assumptions.
- Delivered one model across four decision-support formats (Excel,
  Power BI, a web decision cockpit, and a recruiter package) from a
  single source of truth, eliminating the risk of the same number
  drifting across formats.
- Instrumented every downstream artifact to be independently checked
  against the live model rather than against each other: 41 Excel checks
  recalculate the live workbook formula-by-formula, and 114 web-cockpit
  checks drive a real headless browser against the same model.
