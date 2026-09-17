"""Automated verification of the web decision cockpit (recruiter-facing
UI-polish phase).

Serves deliverables/web_cockpit/ over a local HTTP server, loads it in a
real headless browser (Playwright + the pre-installed Chromium), and checks:
zero console/page errors; the Overview KPI row matches the Python model
exactly for all three scenarios; the corrected gross/net horizon-capacity
reconciliation renders correctly and matches Python; no bare/legacy capacity
KPI renders anywhere; the scenario selector keeps every rendered section in
sync (never mixes scenarios); the comparison-mode panel; the What-If Lab's
zero-delta parity and visual separation from published results; disclaimers;
download-card link integrity (referenced local files actually exist);
accessibility basics (skip link, landmarks, nav labeling, chart aria-labels);
and zero horizontal overflow at 6 required viewports (desktop through
mobile).

Usage: python3 scripts/verify_web_cockpit.py
"""
import http.server
import json
import re
import socketserver
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[1]
COCKPIT_DIR = REPO_ROOT / "deliverables" / "web_cockpit"
DATA_PATH = COCKPIT_DIR / "data" / "model_data.json"
CHROMIUM_PATH = "/opt/pw-browsers/chromium"
PORT = 8792

EXPECTED_NET_HORIZON = {"base": 9175.0, "upside": 7420.7, "downside": 6387.5}
VIEWPORTS = [
    ("1440x1000 desktop", 1440, 1000),
    ("1280x800 desktop", 1280, 800),
    ("1024x768 tablet-landscape", 1024, 768),
    ("768x1024 tablet-portrait", 768, 1024),
    ("390x844 mobile", 390, 844),
    ("360x800 mobile", 360, 800),
]

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
    socketserver.TCPServer.allow_reuse_address = True
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
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: console_errors.append(str(exc)))
    page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="networkidle")
    page.wait_for_timeout(500)

    check(len(console_errors) == 0, f"Zero console/page errors on load (found {len(console_errors)})")
    for e in console_errors[:10]:
        print("   ERROR:", e)

    # --- Positioning / disclaimers render ---
    check(page.title() == "Target Cash Flow & Investment Capacity Decision Cockpit", "Page <title> matches the required product title exactly")
    hero_text = page.locator(".hero").inner_text()
    check("Not affiliated with Target Corporation" in hero_text, "Hero disclaims Target affiliation")
    check("not investment advice or price targets" in hero_text.lower(), "Hero disclaims investment advice / price targets")
    check("SEC-filed history" in hero_text and "scenario planning" in hero_text and "capital allocation" in hero_text and "valuation" in hero_text, "Hero subtitle matches the required positioning line")
    footer_text = page.locator(".site-footer").inner_text()
    check("Not affiliated with Target Corporation" in footer_text, "Footer repeats the affiliation disclaimer")

    # --- Evidence badges: verified against the data file, not hardcoded guesses ---
    badges_text = page.locator("#header-badges").inner_text()
    check(f"{len(data['sources'])} SEC filings" in badges_text, "Evidence badge: SEC filing count matches data file")
    check(data["information_cutoff"] in badges_text, "Evidence badge: information cutoff matches data file")
    cap_v = data["validation"].get("capacity_taxonomy", {"total": 0, "PASS": 0})
    total_checks = data["validation"]["forecast"]["total"] + data["validation"]["valuation"]["total"] + cap_v["total"]
    total_pass = data["validation"]["forecast"]["PASS"] + data["validation"]["valuation"]["PASS"] + cap_v["PASS"]
    check(f"{total_pass}/{total_checks} PASS" in badges_text, "Evidence badge: validation total matches data file")
    check(f"{cap_v['total']} capacity-validation results" in badges_text, "Evidence badge: capacity-validation result count matches data file")

    # --- 30-second tour ---
    tour_text = page.locator("#tour").inner_text()
    check("What happened?" in tour_text and "What could happen?" in tour_text and "What can safely be deployed?" in tour_text, "30-second tour has the three required steps")

    # --- Overview KPI row: the exact required 6 cards, matching Python ---
    base_terminal = data["scenarios"]["base"]["years"][-1]
    base_hz = data["scenarios"]["base"]["capacity_horizon_summary"]
    base_cap_terminal = data["scenarios"]["base"]["capacity_taxonomy_by_year"][str(base_terminal["fiscal_year"])]
    kpi_grid = page.locator("#kpi-grid")
    kpi_text = kpi_grid.inner_text()
    kpi_text_lower = kpi_text.lower()  # CSS text-transform:uppercase changes inner_text() case
    for required_label in [
        "FY2030 Revenue", "FY2030 Free Cash Flow", "Net Horizon Deployable Capacity",
        "FY2030 Remaining Deployable Headroom", "Implied DCF Value/Share", "Validation Status",
    ]:
        check(required_label.lower() in kpi_text_lower, f"Overview KPI row includes required card: {required_label!r}")
    check(kpi_grid.locator(".kpi-card").count() == 6, f"Overview KPI row has exactly 6 cards (found {kpi_grid.locator('.kpi-card').count()})")
    check(f"${round(base_terminal['revenue']):,}".replace(",", "") in kpi_text.replace(",", ""), "KPI: FY2030 Revenue matches Python (Base)")
    check(f"${round(base_hz['net_horizon_deployable_capacity']):,}".replace(",", "") in kpi_text.replace(",", ""), "KPI: Net Horizon Deployable Capacity matches Python (Base)")
    check(f"${round(base_cap_terminal['remaining_deployable_headroom']):,}".replace(",", "") in kpi_text.replace(",", ""), "KPI: FY2030 Remaining Deployable Headroom matches Python (Base)")

    # Required exact values (independently, from the data file Python generated).
    for scenario, expected in EXPECTED_NET_HORIZON.items():
        hz = data["scenarios"][scenario]["capacity_horizon_summary"]
        check(abs(hz["net_horizon_deployable_capacity"] - expected) < 0.1, f"{scenario.capitalize()}: Net Horizon Deployable Capacity == ${expected}M exactly")
    expected_headroom = {"base": 6378.7, "upside": 2043.5, "downside": 6387.5}
    for scenario, expected in expected_headroom.items():
        yrs = data["scenarios"][scenario]["years"]
        term = yrs[-1]
        headroom = data["scenarios"][scenario]["capacity_taxonomy_by_year"][str(term["fiscal_year"])]["remaining_deployable_headroom"]
        check(abs(headroom - expected) < 0.5, f"{scenario.capitalize()}: FY2030 Remaining Deployable Headroom == ${expected}M (within rounding)")

    # Headroom-is-not-a-score explanation text.
    headroom_note = page.locator("#headroom-note").inner_text().lower()
    check("not a performance score" in headroom_note, "Headroom explanation text present (liquidity outcome, not a performance score)")

    # Never these as unlabeled/bare KPI card LABELS (checked as exact label text,
    # not loose substring, since "5-Year Net Horizon Deployable Capacity" is a
    # legitimate qualified label that happens to contain "deployable capacity").
    forbidden_bare_labels = {"deployable capacity", "cumulative deployable capacity", "gross debt proceeds", "gross horizon funding before reserve adjustments"}
    kpi_label_texts = [t.strip().lower() for t in kpi_grid.locator(".kpi-label").all_inner_texts()]
    bad_labels = [t for t in kpi_label_texts if t in forbidden_bare_labels]
    check(len(bad_labels) == 0, f"No forbidden bare legacy KPI label in the executive KPI row (found: {bad_labels})")

    # --- Comparison mode ---
    cmp_btn = page.locator("#comparison-toggle-btn")
    check(cmp_btn.get_attribute("aria-expanded") == "false", "Comparison panel starts collapsed")
    cmp_btn.click()
    page.wait_for_timeout(150)
    check(cmp_btn.get_attribute("aria-expanded") == "true", "Comparison toggle expands on click")
    cmp_text = page.locator("#table-comparison").inner_text()
    for label in ["Base", "Upside", "Downside"]:
        check(label in cmp_text, f"Comparison table includes {label} column")
    check(f"${round(EXPECTED_NET_HORIZON['upside']):,}".replace(",", "") in cmp_text.replace(",", ""), "Comparison table Upside net horizon capacity matches Python")
    cmp_btn.click()
    page.wait_for_timeout(150)

    # --- Scenario selector keeps every section in sync (never mixes scenarios) ---
    page.click('button[data-scenario="upside"]')
    page.wait_for_timeout(300)
    upside_terminal = data["scenarios"]["upside"]["years"][-1]
    upside_hz = data["scenarios"]["upside"]["capacity_horizon_summary"]
    kpi_text_upside = page.locator("#kpi-grid").inner_text()
    check(
        f"${round(upside_terminal['revenue']):,}".replace(",", "") in kpi_text_upside.replace(",", "")
        and f"${round(base_terminal['revenue']):,}".replace(",", "") not in kpi_text_upside.replace(",", ""),
        "Scenario selector -> Upside: KPI row updates to Upside's revenue, not Base's",
    )
    horizon_text_upside = page.locator("#table-capacity-horizon").inner_text()
    check(
        f"${round(upside_hz['net_horizon_deployable_capacity']):,}".replace(",", "") in horizon_text_upside.replace(",", ""),
        "Scenario selector -> Upside: horizon reconciliation table updates to Upside's net figure",
    )
    forecast_caption = page.locator("#table-forecast caption").inner_text().lower()
    check("upside" in forecast_caption, "Scenario selector -> Upside: forecast table caption updates to Upside")

    page.click('button[data-scenario="downside"]')
    page.wait_for_timeout(300)
    downside_terminal = data["scenarios"]["downside"]["years"][-1]
    kpi_text_downside = page.locator("#kpi-grid").inner_text()
    check(f"${round(downside_terminal['revenue']):,}".replace(",", "") in kpi_text_downside.replace(",", ""), "Scenario selector -> Downside: KPI row updates to Downside's revenue")

    page.click('button[data-scenario="base"]')
    page.wait_for_timeout(300)

    # --- Cash-flow definitions: CFO/CapEx/CFI/FCF distinct and correct ---
    defs_text = page.locator("#cash-definitions-grid").inner_text()
    hist = data["historical"]["2025"]
    check("$6,562M" in defs_text, "FY2025 CFO reference value ($6,562M) renders on the page")
    check("$3,727M" in defs_text, "FY2025 CapEx reference value ($3,727M) renders on the page")
    check("$3,649M" in defs_text or "-$3,649M" in defs_text or "$-3,649M" in defs_text, "FY2025 CFI reference value ($(3,649)M) renders on the page")
    check("$2,835M" in defs_text, "FY2025 FCF reference value ($2,835M) renders on the page")
    check(abs(hist["capital_expenditure"] - abs(hist["investing_cash_flow"])) > 1.0, "CapEx and CFI are numerically distinct in the underlying data")

    # --- Gross vs net horizon capacity: correct labeling and reconciliation ---
    horizon_text = page.locator("#table-capacity-horizon").inner_text()
    horizon_lower = horizon_text.lower()
    check("gross horizon funding" in horizon_lower and "not accessible capacity" in horizon_lower, "Horizon table labels the gross figure as NOT accessible capacity")
    check("net horizon deployable capacity" in horizon_lower and "decision kpi" in horizon_lower, "Horizon table labels the net figure as the decision KPI")
    check(f"${round(base_hz['gross_horizon_funding_before_reserve_adjustments']):,}".replace(",", "") in horizon_text.replace(",", ""), "Gross Horizon Funding value on the page matches Python (Base)")
    check(f"${round(base_hz['net_horizon_deployable_capacity']):,}".replace(",", "") in horizon_text.replace(",", ""), "Net Horizon Deployable Capacity value on the page matches Python (Base)")
    for scenario, expected_net in EXPECTED_NET_HORIZON.items():
        hz = data["scenarios"][scenario]["capacity_horizon_summary"]
        gross = hz["gross_horizon_funding_before_reserve_adjustments"]
        net = hz["net_horizon_deployable_capacity"]
        reserves = hz["ending_reserve_movement"] + hz["terminal_forward_debt_repayment_reserve"]
        check(abs(net - (gross - reserves)) < 0.1, f"{scenario.capitalize()}: Net = Gross - Ending Reserve Movement - Terminal Forward Reserve, exactly")
        check(abs(net - (hz["cumulative_discretionary_deployment"] + hz["terminal_remaining_headroom"])) < 0.1, f"{scenario.capitalize()}: Net also equals Cumulative Discretionary Deployment + Terminal Remaining Headroom (dual identity)")

    # Stock/flow/use/source/reserve badges present in the Investment Capacity section.
    capacity_section_text = page.locator("#capacity").inner_text()
    for badge in ["STOCK", "FLOW", "SOURCE", "USE", "RESERVE"]:
        check(badge in capacity_section_text, f"Investment Capacity section includes a {badge} badge")
    check("FY2031" in capacity_section_text, "Terminal forward reserve is identified as an FY2031 proxy, not a real obligation")

    # --- What-If Lab: visual separation, baseline vs output, zero-delta parity ---
    check("Illustrative What-If Lab" in page.locator("#whatif-h").inner_text(), "What-If section is titled 'Illustrative What-If Lab'")
    whatif_panel_text = page.locator("#whatif").inner_text()
    check("Browser-only exploratory recalculation" in whatif_panel_text, "What-If Lab carries the required 'browser-only' disclaimer")
    check("not published" in page.locator("#whatif-results").locator("xpath=..").inner_text().lower(), "What-If output is labeled 'not published'")

    baseline_text = page.locator("#whatif-baseline").inner_text()
    whatif_text = page.locator("#whatif-results").inner_text()
    check(baseline_text == whatif_text, "What-If Lab at zero delta exactly matches the published baseline (side by side)")
    check(f"${round(base_terminal['revenue']):,}".replace(",", "") in whatif_text.replace(",", ""), "What-If sandbox default revenue matches Python exactly")

    changed_indicator = page.locator("#whatif-changed-indicator").inner_text()
    check("No inputs changed" in changed_indicator, "What-If changed-input indicator reads 'no inputs changed' at baseline")

    slider = page.locator("#whatif-controls input[type=range]").first
    slider.evaluate("(el) => { el.value = '2.0'; el.dispatchEvent(new Event('input', {bubbles: true})); }")
    page.wait_for_timeout(200)
    whatif_text_after = page.locator("#whatif-results").inner_text()
    check(whatif_text_after != whatif_text, "What-If sandbox recomputes when a slider moves (output changes)")
    check(baseline_text != whatif_text_after, "What-If output diverges from the (unchanged) published baseline once a slider moves")
    changed_indicator_after = page.locator("#whatif-changed-indicator").inner_text()
    check("1 input changed" in changed_indicator_after, "What-If changed-input indicator updates when a slider moves")

    page.click("#whatif-reset")
    page.wait_for_timeout(200)
    whatif_text_reset = page.locator("#whatif-results").inner_text()
    check(whatif_text_reset == whatif_text, "What-If sandbox 'Reset to scenario defaults' restores the exact original output")

    # --- No-double-counting proof ---
    proof_text = page.locator("#no-double-count-banner").inner_text()
    check("OK" in proof_text, "Capital allocation no-double-counting proof reads OK for the default scenario/year")

    # --- Audit & methodology ---
    audit_checks_text = page.locator("#table-audit-checks").inner_text()
    check(str(cap_v["total"]) in audit_checks_text, "Audit table shows the capacity-validation result count matching Python")
    check("19 named checks" in audit_checks_text, "Audit table names the 19 capacity-taxonomy checks")
    check(f"{total_pass}" in audit_checks_text and f"{total_checks}" in audit_checks_text, "Audit table shows the grand total matching Python")

    # --- Downloads: cards present, hrefs well-formed, referenced local files exist ---
    download_cards = page.locator(".download-card")
    check(download_cards.count() == 5, f"Downloads section has 5 cards (found {download_cards.count()})")
    hrefs = download_cards.evaluate_all("els => els.map(e => e.getAttribute('href'))")
    titles = download_cards.locator("h3").all_inner_texts()
    check(not any(".pbix" in (h or "") for h in hrefs), "No .pbix file is claimed to exist anywhere in Downloads")
    check(any("powerbi_handoff_package.zip" in (h or "") for h in hrefs), "Power BI-ready handoff is offered as a versioned .zip, not a claimed folder download")
    for href in hrefs:
        parsed = urlparse(href)
        check(parsed.scheme in ("https", "http") and bool(parsed.netloc), f"Download href is a well-formed absolute URL: {href}")
    # Confirm every referenced repository file genuinely exists on disk (broken-link test).
    local_targets = {
        "Target_Cash_Flow_Investment_Capacity_Model.xlsx": REPO_ROOT / "deliverables" / "Target_Cash_Flow_Investment_Capacity_Model.xlsx",
        "powerbi_handoff_package.zip": REPO_ROOT / "deliverables" / "powerbi_handoff_package.zip",
        "01_executive_case_study.md": REPO_ROOT / "deliverables" / "portfolio_package" / "01_executive_case_study.md",
        "investment_capacity_correction_evidence.md": REPO_ROOT / "docs" / "investment_capacity_correction_evidence.md",
    }
    for fname, path_on_disk in local_targets.items():
        referenced = any(fname in (h or "") for h in hrefs)
        check(referenced and path_on_disk.is_file(), f"Download link for {fname} references a file that exists on disk ({path_on_disk})")

    # --- Accessibility basics ---
    check(page.locator("a.skip-link").count() == 1, "Skip-to-content link present")
    check(page.locator("a.skip-link").get_attribute("href") == "#main", "Skip link targets #main")
    nav_links = page.locator("#site-nav a").count()
    check(nav_links == 9, f"9 navigation links present for the 9 required IA sections (found {nav_links})")
    check(page.locator("nav[aria-label]").count() >= 1, "Navigation landmark has an aria-label")
    h1_count = page.locator("h1").count()
    check(h1_count == 1, f"Exactly one <h1> on the page (found {h1_count})")
    h2_count = page.locator("main h2").count()
    check(h2_count == 9, f"Exactly 9 <h2> section headings in <main> (found {h2_count})")
    imgs_without_label = page.locator('[role="img"]:not([aria-label])').count()
    check(imgs_without_label == 0, f"Every role=img chart has an aria-label (found {imgs_without_label} without one)")
    details_count = page.locator("details.evidence-panel").count()
    check(details_count >= 3, f"At least 3 expandable evidence/methodology panels present (found {details_count})")
    range_inputs_labeled = page.locator('input[type="range"]:not([aria-label])').count()
    check(range_inputs_labeled == 0, "Every What-If slider has an aria-label")

    # --- Scrollspy active-state nav ---
    page.evaluate("document.documentElement.style.scrollBehavior='auto'; document.getElementById('capacity').scrollIntoView();")
    page.wait_for_timeout(400)
    active_link = page.locator("#site-nav a.active")
    check(active_link.count() >= 1, "Nav shows an active-state link while scrolled into a section")
    if active_link.count() >= 1:
        check(active_link.first.get_attribute("data-section") == "capacity", "Nav active-state link matches the section actually in view")
    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(200)

    # --- No bare "deployable capacity" anywhere without a qualifier ---
    full_page_text = page.locator("body").inner_text()
    bare_mentions = [
        line for line in full_page_text.split("\n")
        if "deployable capacity" in line.lower()
        and not any(q in line.lower() for q in ("legacy", "deprecated", "remaining", "cumulative", "net horizon", "5-year net"))
    ]
    check(len(bare_mentions) == 0, f"No bare 'deployable capacity' label lacking a qualifier (found {len(bare_mentions)})")

    browser.close()

    # --- Responsive: zero horizontal overflow at all 6 required viewports ---
    browser = p.chromium.launch(executable_path=CHROMIUM_PATH)
    for name, w, h in VIEWPORTS:
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="networkidle")
        body_width = page.evaluate("document.body.scrollWidth")
        check(body_width <= w + 1, f"No horizontal overflow at {name} (body scrollWidth={body_width}, viewport={w})")
        page.close()
    browser.close()

    # --- Mobile: every #table-capacity-horizon VALUE cell is actually on
    # screen (inside the visible table wrapper), not just "body doesn't
    # overflow" -- a table can be scroll-contained and still hide its value
    # column off to the right within that container, which is exactly the
    # bug a prior release shipped (see docs/ui_ux_audit.md). This checks
    # each cell's own bounding box against the viewport, so a value sitting
    # outside the visible area is caught even when nothing overflows the
    # page as a whole.
    browser = p.chromium.launch(executable_path=CHROMIUM_PATH)
    for name, w, h in [("390x844 mobile", 390, 844), ("360x800 mobile", 360, 800)]:
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="networkidle")
        page.evaluate("document.documentElement.style.scrollBehavior='auto'; document.getElementById('table-capacity-horizon').scrollIntoView();")
        page.wait_for_timeout(200)

        wrapper_box = page.eval_on_selector("#table-capacity-horizon", "el => { const r = el.closest('.table-wrap').getBoundingClientRect(); return {left:r.left, right:r.right, top:r.top, bottom:r.bottom}; }")
        cell_boxes = page.eval_on_selector_all(
            "#table-capacity-horizon tbody td",
            "els => els.map(el => { const r = el.getBoundingClientRect(); return {text: el.textContent.trim(), left:r.left, right:r.right, width:r.width, height:r.height}; })",
        )
        check(len(cell_boxes) > 0, f"{name}: horizon table has value cells to check")
        offscreen = [
            c for c in cell_boxes
            if c["width"] <= 0 or c["height"] <= 0 or c["left"] < -1 or c["right"] > w + 1
        ]
        check(
            len(offscreen) == 0,
            f"{name}: every horizon-table cell (label AND value) is fully within the {w}px viewport, none clipped or off-screen "
            f"(found {len(offscreen)} problem cells: {[c['text'][:40] for c in offscreen]})",
        )
        # Specifically confirm the gross and net VALUE cells (not just labels) are visible, on screen, and match Python.
        value_cells = [c for c in cell_boxes if c["text"].startswith("$")]
        check(len(value_cells) >= 9, f"{name}: at least 9 dollar-value cells are visible in the horizon table (found {len(value_cells)})")
        base_hz = data["scenarios"]["base"]["capacity_horizon_summary"]
        gross_text = f"${round(base_hz['gross_horizon_funding_before_reserve_adjustments']):,}M"
        net_text = f"${round(base_hz['net_horizon_deployable_capacity']):,}M"
        value_texts = [c["text"] for c in value_cells]
        check(gross_text in value_texts, f"{name}: gross value ({gross_text}) is on screen as its own visible cell, matching Python")
        check(net_text in value_texts, f"{name}: net value ({net_text}) is on screen as its own visible cell, matching Python")
        page.close()
    browser.close()

httpd.shutdown()

print()
if errors_found:
    print(f"VERIFICATION FAILED: {len(errors_found)} issue(s) found.")
    sys.exit(1)
else:
    print("ALL VERIFICATION CHECKS PASSED.")
