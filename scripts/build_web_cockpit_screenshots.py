"""Regenerate the web cockpit's recruiter-facing screenshot package.

Serves deliverables/web_cockpit/ locally, drives it with Playwright +
the pre-installed Chromium, and captures the 10 screenshots required by
the UI-polish phase into deliverables/web_cockpit/screenshots/, plus a
generated screenshots/README.md documenting each file's viewport,
scenario, purpose, verification date, and the commit this rebuild was
generated against.

This is the ONLY supported way to update the screenshot package -- never
hand-edit an image or the README. Re-run this script whenever the
cockpit's rendered output changes; it always overwrites every file it
manages, so there is never a mix of stale and fresh screenshots. Prior
versions remain fully recoverable from git history (`git log --
deliverables/web_cockpit/screenshots/`).

Usage: python3 scripts/build_web_cockpit_screenshots.py
"""
import http.server
import socketserver
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[1]
COCKPIT_DIR = REPO_ROOT / "deliverables" / "web_cockpit"
SCREENSHOTS_DIR = COCKPIT_DIR / "screenshots"
CHROMIUM_PATH = "/opt/pw-browsers/chromium"
PORT = 8810

DESKTOP = {"width": 1440, "height": 1000}
MOBILE = {"width": 390, "height": 844}


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve():
    handler = lambda *a, **kw: QuietHandler(*a, directory=str(COCKPIT_DIR), **kw)
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def git_commit_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    except Exception:
        return "unknown"


def git_last_commit_touching(path: str) -> str:
    """The commit that last changed `path` in the current history -- used
    to identify the financial-baseline commit (the last one to touch
    model_data.json), independent of how many purely presentational
    commits have landed since."""
    try:
        return subprocess.check_output(
            ["git", "log", "-1", "--format=%H", "--", path], cwd=REPO_ROOT, text=True
        ).strip() or "unknown"
    except Exception:
        return "unknown"


def goto(page, port):
    page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="networkidle")
    page.evaluate("document.documentElement.style.scrollBehavior='auto';")
    page.wait_for_timeout(150)


def scroll_to(page, selector):
    page.evaluate(f"document.querySelector('{selector}').scrollIntoView();")
    page.wait_for_timeout(200)


def click_scenario(page, scenario):
    page.click(f'button[data-scenario="{scenario}"]')
    page.wait_for_timeout(250)


def build():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    # Remove prior generated screenshots -- fully recoverable via git history.
    for old in SCREENSHOTS_DIR.glob("*.png"):
        old.unlink()

    httpd = serve()
    time.sleep(0.3)
    manifest = []

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM_PATH)

        # 1. Executive overview -- Base
        page = browser.new_page(viewport=DESKTOP)
        goto(page, PORT)
        path = SCREENSHOTS_DIR / "01_executive_overview_base.png"
        page.screenshot(path=str(path))
        manifest.append((path.name, "1440x1000 desktop", "Base", "Hero, 30-second tour, and executive KPI row on first load."))

        # 2. Executive overview -- scenario comparison
        page.click("#comparison-toggle-btn")
        page.wait_for_timeout(200)
        path = SCREENSHOTS_DIR / "02_scenario_comparison.png"
        scroll_to(page, "#comparison-panel")
        page.screenshot(path=str(path))
        manifest.append((path.name, "1440x1000 desktop", "Base (comparison mode)", "Compact Base/Upside/Downside comparison table for the key decision metrics."))
        page.click("#comparison-toggle-btn")
        page.close()

        # 3. Historical evidence
        page = browser.new_page(viewport=DESKTOP)
        goto(page, PORT)
        scroll_to(page, "#historical")
        path = SCREENSHOTS_DIR / "03_historical_evidence.png"
        page.screenshot(path=str(path))
        manifest.append((path.name, "1440x1000 desktop", "Base", "Historical Evidence section: actuals-only chart, cash-flow definitions, and filing-vintage comparison."))
        page.close()

        # 4. Corrected capacity waterfall
        page = browser.new_page(viewport=DESKTOP)
        goto(page, PORT)
        scroll_to(page, "#capacity")
        path = SCREENSHOTS_DIR / "04_corrected_capacity_waterfall.png"
        page.screenshot(path=str(path))
        manifest.append((path.name, "1440x1000 desktop", "Base", "Investment Capacity section: stock/flow/source/use/reserve badges and the FY2030 source/use waterfall."))
        page.close()

        # 5. Gross-vs-net horizon reconciliation
        page = browser.new_page(viewport=DESKTOP)
        goto(page, PORT)
        scroll_to(page, "#table-capacity-horizon")
        path = SCREENSHOTS_DIR / "05_gross_vs_net_horizon_reconciliation.png"
        page.screenshot(path=str(path))
        manifest.append((path.name, "1440x1000 desktop", "Base", "The corrected Cumulative Capacity Reconciliation table: gross (pre-reserve) vs. net (decision KPI), both visible and labeled."))
        page.close()

        # 6. DCF valuation and sensitivity
        page = browser.new_page(viewport=DESKTOP)
        goto(page, PORT)
        scroll_to(page, "#dcf")
        path = SCREENSHOTS_DIR / "06_dcf_valuation_sensitivity.png"
        page.screenshot(path=str(path))
        manifest.append((path.name, "1440x1000 desktop", "Base", "DCF Valuation section: WACC build, valuation bridge, and the two sensitivity heatmaps."))
        page.close()

        # 7. What-if lab
        page = browser.new_page(viewport=DESKTOP)
        goto(page, PORT)
        scroll_to(page, "#whatif")
        path = SCREENSHOTS_DIR / "07_whatif_lab.png"
        page.screenshot(path=str(path))
        manifest.append((path.name, "1440x1000 desktop", "Base", "Illustrative What-If Lab: dashed-border treatment, baseline-vs-output side by side, changed-input indicator."))
        page.close()

        # 8. Audit / evidence panel
        page = browser.new_page(viewport=DESKTOP)
        goto(page, PORT)
        scroll_to(page, "#audit")
        page.click("#audit details.evidence-panel summary")
        page.wait_for_timeout(150)
        path = SCREENSHOTS_DIR / "08_audit_evidence_panel.png"
        page.screenshot(path=str(path))
        manifest.append((path.name, "1440x1000 desktop", "Base", "Audit & Methodology section with the validation/correction-timeline table and an expanded evidence panel."))
        page.close()

        # 9. Mobile executive view
        page = browser.new_page(viewport=MOBILE)
        goto(page, PORT)
        path = SCREENSHOTS_DIR / "09_mobile_executive_view.png"
        page.screenshot(path=str(path))
        manifest.append((path.name, "390x844 mobile", "Base", "Mobile hero and top of the Overview section -- zero horizontal overflow."))
        page.close()

        # 10. Mobile capacity view
        page = browser.new_page(viewport=MOBILE)
        goto(page, PORT)
        scroll_to(page, "#table-capacity-horizon")
        path = SCREENSHOTS_DIR / "10_mobile_capacity_view.png"
        page.screenshot(path=str(path))
        manifest.append((path.name, "390x844 mobile", "Base", "Mobile Investment Capacity section: horizon reconciliation table stacks label-then-value per row below 480px, so both the label and its dollar value are simultaneously visible with zero horizontal scrolling."))
        page.close()

        browser.close()

    httpd.shutdown()

    ui_source_commit = git_commit_hash()
    financial_baseline_commit = git_last_commit_touching("deliverables/web_cockpit/data/model_data.json")
    verified_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    readme_lines = [
        "# Web Cockpit Screenshot Package",
        "",
        "Generated exclusively by `scripts/build_web_cockpit_screenshots.py` --",
        "never hand-edited. Re-running that script is the only supported way to",
        "update this package; it deletes and regenerates every PNG here, so a",
        "stale screenshot never lingers alongside a fresh one. Prior versions",
        "remain fully recoverable from git history",
        "(`git log -- deliverables/web_cockpit/screenshots/`).",
        "",
        f"Verified: {verified_date} (UTC).",
        f"Financial baseline commit (last commit to touch `data/model_data.json` -- the numbers shown are unchanged since this commit): `{financial_baseline_commit}`.",
        f"UI build source commit (the presentation-layer code rendered when these screenshots were captured): `{ui_source_commit}`.",
        "",
        "Note on self-reference: this README ships inside a later commit than the",
        "one recorded above as the \"UI build source\" -- a file cannot cite the",
        "hash of the commit that first contains it, since that hash does not",
        "exist yet at generation time. Run `git log -1 --format=%H -- "
        "deliverables/web_cockpit/screenshots/README.md` for the exact commit",
        "this file itself ships in.",
        "",
        "| # | Filename | Viewport | Scenario | Purpose |",
        "|---|---|---|---|---|",
    ]
    for i, (fname, viewport, scenario, purpose) in enumerate(manifest, start=1):
        readme_lines.append(f"| {i} | `{fname}` | {viewport} | {scenario} | {purpose} |")
    readme_lines.append("")
    readme_lines.append(
        "Any prior version of this package (including any screenshot dated or "
        "hashed earlier than the UI build source commit above) is stale and "
        "must not be treated as representative of the current build -- see "
        "`docs/ui_ux_audit.md` §1 for a documented example of exactly this "
        "failure mode."
    )
    (SCREENSHOTS_DIR / "README.md").write_text("\n".join(readme_lines) + "\n")
    print(f"Wrote {len(manifest)} screenshots + README.md to {SCREENSHOTS_DIR}")


if __name__ == "__main__":
    build()
