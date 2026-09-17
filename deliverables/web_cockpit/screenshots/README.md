# Web Cockpit Screenshot Package

Generated exclusively by `scripts/build_web_cockpit_screenshots.py` --
never hand-edited. Re-running that script is the only supported way to
update this package; it deletes and regenerates every PNG here, so a
stale screenshot never lingers alongside a fresh one. Prior versions
remain fully recoverable from git history
(`git log -- deliverables/web_cockpit/screenshots/`).

Verified: 2026-09-17 (UTC).
Financial baseline commit (last commit to touch `data/model_data.json` -- the numbers shown are unchanged since this commit): `fff9b9c5cedb8ec485d1720b74d896adae65089d`.
UI build source commit (the presentation-layer code rendered when these screenshots were captured): `4e383ef8d3c8df03f0d38e86bf712a5a8f320101`.

Note on self-reference: this README ships inside a later commit than the
one recorded above as the "UI build source" -- a file cannot cite the
hash of the commit that first contains it, since that hash does not
exist yet at generation time. Run `git log -1 --format=%H -- deliverables/web_cockpit/screenshots/README.md` for the exact commit
this file itself ships in.

| # | Filename | Viewport | Scenario | Purpose |
|---|---|---|---|---|
| 1 | `01_executive_overview_base.png` | 1440x1000 desktop | Base | Hero, 30-second tour, and executive KPI row on first load. |
| 2 | `02_scenario_comparison.png` | 1440x1000 desktop | Base (comparison mode) | Compact Base/Upside/Downside comparison table for the key decision metrics. |
| 3 | `03_historical_evidence.png` | 1440x1000 desktop | Base | Historical Evidence section: actuals-only chart, cash-flow definitions, and filing-vintage comparison. |
| 4 | `03b_scenario_forecast.png` | 1440x1000 desktop | Base | Scenario Forecast section: margins on a percent axis and diluted EPS on a $/share axis -- the corrected chart-unit formatters, no longer mislabeled in millions. |
| 5 | `04_corrected_capacity_waterfall.png` | 1440x1000 desktop | Base | Investment Capacity section: stock/flow/source/use/reserve badges and the FY2030 source/use waterfall. |
| 6 | `05_gross_vs_net_horizon_reconciliation.png` | 1440x1000 desktop | Base | The corrected Cumulative Capacity Reconciliation table: gross (pre-reserve) vs. net (decision KPI), both visible and labeled. |
| 7 | `06_dcf_valuation_sensitivity.png` | 1440x1000 desktop | Base | DCF Valuation section: WACC build, valuation bridge, and the two sensitivity heatmaps. |
| 8 | `07_whatif_lab.png` | 1440x1000 desktop | Base | Illustrative What-If Lab: dashed-border treatment, baseline-vs-output side by side, changed-input indicator. |
| 9 | `07b_whatif_presets.png` | 1440x1000 desktop | Base | Illustrative What-If presets (Cash Preservation, Automation Reinvestment, Downside Liquidity Stress) with the sandbox-only badge and per-preset delta explanations. |
| 10 | `08_audit_evidence_panel.png` | 1440x1000 desktop | Base | Audit & Methodology section with the validation/correction-timeline table and an expanded evidence panel. |
| 11 | `08b_powerbi_implementation_preview.png` | 1440x1000 desktop | Base | Power BI Implementation Preview: accessible tab list over the offline wireframes, explicitly labeled as not a live embedded .pbix report. |
| 12 | `09_mobile_executive_view.png` | 390x844 mobile | Base | Mobile hero and top of the Overview section -- zero horizontal overflow. |
| 13 | `10_mobile_capacity_view.png` | 390x844 mobile | Base | Mobile Investment Capacity section: horizon reconciliation table stacks label-then-value per row below 480px, so both the label and its dollar value are simultaneously visible with zero horizontal scrolling. |
| 14 | `11_mobile_360_capacity_reconciliation.png` | 360x800 mobile | Base | 360px-wide Investment Capacity reconciliation: the narrowest required viewport, confirming both the gross ($9,304M) and net ($9,175M) value cells stay visible with zero horizontal overflow. |

Any prior version of this package (including any screenshot dated or hashed earlier than the UI build source commit above) is stale and must not be treated as representative of the current build -- see `docs/ui_ux_audit.md` §1 for a documented example of exactly this failure mode.
