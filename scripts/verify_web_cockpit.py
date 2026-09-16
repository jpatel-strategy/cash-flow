"""Milestone 7: automated verification of the web decision cockpit.

Serves deliverables/web_cockpit/ over a local HTTP server, loads it in a
real headless browser (Playwright + the pre-installed Chromium), and
checks: zero console/page errors, the Executive Snapshot's headline
numbers match the Python model exactly, the scenario selector actually
changes rendered values, the What-If sandbox reproduces the exact
scenario defaults at zero delta and changes when a slider moves, and the
FY2025 CFO/CapEx/CFI/FCF reference values render distinctly (never
collapsing CapEx into CFI).

Usage: .venv/bin/python scripts/verify_web_cockpit.py
"""
import http.server
import json
import re
import socketserver
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[1]
COCKPIT_DIR = REPO_ROOT / "deliverables" / "web_cockpit"
DATA_PATH = COCKPIT_DIR / "data" / "model_data.json"
CHROMIUM_PATH = "/opt/pw-browsers/chromium"
PORT = 8792

errors_found = []


def check(condition, message):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {message}")
    if not condition:
        errors_found.append(message)


def money_to_float(text):
    m = re.search(r"-?\$?[\d,]+(\.\d+)?", text.replace("−", "-"))
    if not m:
        return None
    return float(m.group(0).replace("$", "").replace(",", ""))


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve():
    handler = lambda *a, **kw: QuietHandler(*a, directory=str(COCKPIT_DIR), **kw)
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


httpd = serve()
time.sleep(0.3)

data = json.loads(DATA_PATH.read_text())

console_errors = []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROMIUM_PATH)
    page = browser.new_page(viewport={"width": 1400, "height": 1000})
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: console_errors.append(str(exc)))
    page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="networkidle")
    page.wait_for_timeout(500)

    check(len(console_errors) == 0, f"Zero console/page errors on load (found {len(console_errors)})")
    for e in console_errors[:10]:
        print("   ERROR:", e)

    # --- Snapshot matches Python for Base scenario ---
    kpi_text = page.locator("#kpi-grid").inner_text()
    base_terminal = data["scenarios"]["base"]["years"][-1]
    revenue_shown = money_to_float([l for l in kpi_text.split("\n") if l.startswith("$") and "M" in l][0])
    check(abs(revenue_shown - base_terminal["revenue"]) < 1.0, "Snapshot Revenue KPI matches Python (Base)")

    dcf_base = data["valuation"]["results"]["base"]["implied_value_per_share"]
    check(f"${dcf_base:.2f}" in kpi_text, "Snapshot DCF Value/Share KPI matches Python exactly (Base)")

    cap_v = data["validation"].get("capacity_taxonomy", {"total": 0, "PASS": 0})
    total_checks = data["validation"]["forecast"]["total"] + data["validation"]["valuation"]["total"] + cap_v["total"]
    total_pass = data["validation"]["forecast"]["PASS"] + data["validation"]["valuation"]["PASS"] + cap_v["PASS"]
    check(f"{total_pass}/{total_checks} PASS" in kpi_text, "Validation status KPI matches Python totals (incl. capacity taxonomy)")

    # --- Scenario selector changes rendered values ---
    page.click('button[data-scenario="upside"]')
    page.wait_for_timeout(300)
    kpi_text_upside = page.locator("#kpi-grid").inner_text()
    upside_terminal = data["scenarios"]["upside"]["years"][-1]
    revenue_upside_shown = money_to_float([l for l in kpi_text_upside.split("\n") if l.startswith("$") and "M" in l][0])
    check(
        abs(revenue_upside_shown - upside_terminal["revenue"]) < 1.0
        and abs(revenue_upside_shown - base_terminal["revenue"]) > 1.0,
        "Scenario selector -> Upside: Snapshot Revenue KPI updates to Python's Upside value",
    )

    page.click('button[data-scenario="downside"]')
    page.wait_for_timeout(300)
    kpi_text_downside = page.locator("#kpi-grid").inner_text()
    downside_terminal = data["scenarios"]["downside"]["years"][-1]
    revenue_downside_shown = money_to_float([l for l in kpi_text_downside.split("\n") if l.startswith("$") and "M" in l][0])
    check(
        abs(revenue_downside_shown - downside_terminal["revenue"]) < 1.0,
        "Scenario selector -> Downside: Snapshot Revenue KPI updates to Python's Downside value",
    )

    page.click('button[data-scenario="base"]')
    page.wait_for_timeout(300)

    # --- Cash-flow definitions: CFO/CapEx/CFI/FCF distinct and correct ---
    defs_text = page.locator("#cash-definitions-grid").inner_text()
    hist = data["historical"]["2025"]
    check("$6,562M" in defs_text, "FY2025 CFO reference value ($6,562M) renders on the page")
    check("$3,727M" in defs_text, "FY2025 CapEx reference value ($3,727M) renders on the page")
    check("$3,649M" in defs_text or "-$3,649M" in defs_text or "$-3,649M" in defs_text, "FY2025 CFI reference value ($(3,649)M) renders on the page")
    check("$2,835M" in defs_text, "FY2025 FCF reference value ($2,835M) renders on the page")
    check(
        abs(hist["capital_expenditure"] - abs(hist["investing_cash_flow"])) > 1.0,
        "CapEx and CFI are numerically distinct in the underlying data (no CFI-as-CapEx substitution)",
    )

    # --- What-if sandbox: zero-delta reproduces exact scenario defaults ---
    whatif_text = page.locator("#whatif-results").inner_text()
    check(
        f"${base_terminal['revenue']:,.0f}".replace(",", ",")[:6] in whatif_text.replace(",", ","),
        "What-If sandbox at zero delta reproduces Python's FY2030 Base revenue",
    )
    lines = whatif_text.split("\n")
    whatif_revenue = money_to_float([l for l in lines if l.startswith("$") and "M" in l][0])
    check(abs(whatif_revenue - base_terminal["revenue"]) < 1.0, "What-If sandbox default revenue matches Python exactly")

    slider = page.locator("#whatif-controls input[type=range]").first
    slider.evaluate("(el) => { el.value = '2.0'; el.dispatchEvent(new Event('input', {bubbles: true})); }")
    page.wait_for_timeout(200)
    whatif_text_after = page.locator("#whatif-results").inner_text()
    check(whatif_text_after != whatif_text, "What-If sandbox recomputes when a slider moves (output changes)")

    page.click("#whatif-reset")
    page.wait_for_timeout(200)
    whatif_text_reset = page.locator("#whatif-results").inner_text()
    check(whatif_text_reset == whatif_text, "What-If sandbox 'Reset to scenario defaults' restores the exact original output")

    # --- No-double-counting proof reads OK ---
    proof_text = page.locator("#no-double-count-banner").inner_text()
    check("OK" in proof_text, "Capital allocation no-double-counting proof reads OK for the default scenario/year")

    # --- Milestone 9 correction: legacy KPI removed from headline; 4 corrected concepts present ---
    kpi_text_check = page.locator("#kpi-grid").inner_text().lower()
    check(
        "deployable capacity" not in kpi_text_check,
        "Legacy ambiguous capacity KPI is removed from the Snapshot headline cards",
    )
    cap_kpi_text = page.locator("#capacity-kpi-grid").inner_text()
    cap_kpi_text_lower = cap_kpi_text.lower()
    for label in ["Self-Funded Capacity Generated", "Debt-Funded Capacity", "Discretionary Deployment",
                  "Remaining Deployable Headroom"]:
        check(label.lower() in cap_kpi_text_lower, f"Corrected capacity concept displayed: {label!r}")

    base_terminal_cap = data["scenarios"]["base"]["capacity_taxonomy_by_year"][str(base_terminal["fiscal_year"])]
    cap_values_text = cap_kpi_text.replace(",", "")
    check(
        f"${round(base_terminal_cap['self_funded_gross_capacity']):,}".replace(",", "") in cap_values_text.replace(",", ""),
        "Self-Funded Capacity Generated KPI value matches Python (Base, FY2030)",
    )

    # No bare "Deployable Capacity" label anywhere without a qualifier (legacy/deprecated/corrected wording).
    full_page_text = page.locator("body").inner_text()
    bare_mentions = [
        line for line in full_page_text.split("\n")
        if "deployable capacity" in line.lower()
        and not any(q in line.lower() for q in ("legacy", "deprecated", "remaining", "cumulative"))
    ]
    check(
        len(bare_mentions) == 0,
        f"No bare 'deployable capacity' label lacking a legacy/deprecated/remaining qualifier (found {len(bare_mentions)})",
    )

    # --- Structural / accessibility checks ---
    check(page.locator("a.skip-link").count() == 1, "Skip-to-content link present")
    nav_links = page.locator(".site-nav a").count()
    check(nav_links == 10, f"10 navigation links present for the 10 required interface areas (found {nav_links})")
    check(page.title() != "", "Page has a non-empty <title>")

    # --- Responsive check: mobile viewport doesn't overflow horizontally ---
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(200)
    body_width = page.evaluate("document.body.scrollWidth")
    check(body_width <= 391, f"No horizontal overflow at 390px mobile width (body scrollWidth={body_width})")

    browser.close()

httpd.shutdown()

print()
if errors_found:
    print(f"VERIFICATION FAILED: {len(errors_found)} issue(s) found.")
    sys.exit(1)
else:
    print("ALL VERIFICATION CHECKS PASSED.")
