# Web Cockpit Screenshot Package

Generated exclusively by `scripts/build_web_cockpit_screenshots.py` --
never hand-edited. Re-running that script is the only supported way to
update this package; it deletes and regenerates every PNG here, so a
stale screenshot never lingers alongside a fresh one. Prior versions
remain fully recoverable from git history
(`git log -- deliverables/web_cockpit/screenshots/`).

Verified: 2026-09-17 (UTC).
Financial baseline commit (last commit to touch `data/model_data.json` -- the numbers shown are unchanged since this commit): `fff9b9c5cedb8ec485d1720b74d896adae65089d`.
UI build source commit (the presentation-layer code rendered when these screenshots were captured): `1ce4a53fe65c7d3f2e45af4087a286f62548cd1d`.

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
| 4 | `04_corrected_capacity_waterfall.png` | 1440x1000 desktop | Base | Investment Capacity section: stock/flow/source/use/reserve badges and the FY2030 source/use waterfall. |
| 5 | `05_gross_vs_net_horizon_reconciliation.png` | 1440x1000 desktop | Base | The corrected Cumulative Capacity Reconciliation table: gross (pre-reserve) vs. net (decision KPI), both visible and labeled. |
| 6 | `06_dcf_valuation_sensitivity.png` | 1440x1000 desktop | Base | DCF Valuation section: WACC build, valuation bridge, and the two sensitivity heatmaps. |
| 7 | `07_whatif_lab.png` | 1440x1000 desktop | Base | Illustrative What-If Lab: dashed-border treatment, baseline-vs-output side by side, changed-input indicator. |
| 8 | `08_audit_evidence_panel.png` | 1440x1000 desktop | Base | Audit & Methodology section with the validation/correction-timeline table and an expanded evidence panel. |
| 9 | `09_mobile_executive_view.png` | 390x844 mobile | Base | Mobile hero and top of the Overview section -- zero horizontal overflow. |
| 10 | `10_mobile_capacity_view.png` | 390x844 mobile | Base | Mobile Investment Capacity section: horizon reconciliation table stacks label-then-value per row below 480px, so both the label and its dollar value are simultaneously visible with zero horizontal scrolling. |

Any prior version of this package (including any screenshot dated or hashed earlier than the UI build source commit above) is stale and must not be treated as representative of the current build -- see `docs/ui_ux_audit.md` §1 for a documented example of exactly this failure mode.
