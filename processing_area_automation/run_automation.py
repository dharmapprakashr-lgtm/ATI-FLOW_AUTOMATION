"""
run_automation.py
------------------
Standalone Playwright test runner — no pytest, no fixtures, no markers.
Runs each test case as a plain Python function, catches failures, takes a
screenshot on failure, and writes a single self-contained HTML report at
the end.

Usage:
    python3 run_automation.py

Config via environment variables (same as before):
    BASE_URL, ADMIN_USER, ADMIN_PASS, PROC_AREA, HEADLESS
"""

import os
import random
import sys
import time
import traceback
from datetime import datetime
from html import escape

from playwright.sync_api import sync_playwright, expect

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pages.staging_area_page import StagingAreaPage
from pages.containers_page import ContainersPage

BASE_URL = os.getenv("BASE_URL", "https://192.168.6.32")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")
PROC_AREA = os.getenv("PROC_AREA", "august")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"

TEST_SA_NAME = "AH_stage"

REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
SCREENSHOT_DIR = os.path.join(REPORT_DIR, "screenshots")

results = []  # each: {id, name, status, duration, error, screenshot}


def login(page):
    page.set_default_timeout(10000)  # 10s instead of default 30s — fail fast during this debugging phase
    page.goto(f"{BASE_URL}/login")
    page.get_by_role("textbox", name="Username").fill(ADMIN_USER)
    page.get_by_role("textbox", name="Password").fill(ADMIN_PASS)
    page.get_by_role("button", name="Login").click()
    page.wait_for_load_state("networkidle")


def run_setup(step_name: str, page, fn):
    """
    Like run_case, but for setup steps (login, open()) that aren't
    individual test cases. Never lets an exception crash the whole run —
    records it, screenshots + prints the current URL for debugging, and
    returns False so the caller can skip dependent tests instead of dying.
    """
    print(f"[setup] {step_name} ... ", end="", flush=True)
    try:
        fn()
        print("OK")
        return True
    except Exception as e:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        screenshot_rel = f"screenshots/setup_{step_name.replace(' ', '_')}.png"
        screenshot_path = os.path.join(REPORT_DIR, screenshot_rel)
        try:
            page.screenshot(path=screenshot_path)
        except Exception:
            screenshot_rel = None
        current_url = None
        try:
            current_url = page.url
        except Exception:
            pass
        print(f"FAILED — {type(e).__name__}: {e}")
        print(f"  current URL at failure: {current_url}")
        if screenshot_rel:
            print(f"  screenshot: reports/{screenshot_rel}")
        results.append({
            "id": f"SETUP_{step_name.replace(' ', '_')}", "name": step_name,
            "status": "FAIL", "duration": 0,
            "error": f"{type(e).__name__}: {e} (url: {current_url})",
            "screenshot": screenshot_rel,
        })
        return False


def _cleanup_after_test(page):
    """
    Best-effort cleanup run after EVERY test (pass or fail): presses
    Escape to close any lingering dialog. Added after discovering
    TC_PA_006 left a "View Trolley Details" dialog open, which then
    blocked every subsequent test's navigation (30s timeout each,
    cascading). Silently ignored if it fails — this is a safety net,
    not something we want breaking the actual test result.
    """
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass


def run_case(tc_id: str, name: str, page, fn):
    """Runs one test case function, records result, screenshots on failure."""
    print(f"  {tc_id}: {name} ... ", end="", flush=True)
    start = time.time()
    try:
        fn()
        duration = time.time() - start
        results.append({
            "id": tc_id, "name": name, "status": "PASS",
            "duration": duration, "error": None, "screenshot": None,
        })
        print(f"PASS ({duration:.1f}s)")
    except Exception as e:
        duration = time.time() - start
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        screenshot_rel = f"screenshots/{tc_id}.png"
        screenshot_path = os.path.join(REPORT_DIR, screenshot_rel)
        try:
            page.screenshot(path=screenshot_path)
        except Exception:
            screenshot_rel = None
        results.append({
            "id": tc_id, "name": name, "status": "FAIL",
            "duration": duration, "error": f"{type(e).__name__}: {e}",
            "screenshot": screenshot_rel,
        })
        print(f"FAIL ({duration:.1f}s) — {type(e).__name__}: {e}")
    finally:
        _cleanup_after_test(page)


def run_skipped(tc_id: str, name: str, reason: str):
    """Records a case as skipped without running it — e.g. selector not confirmed yet."""
    print(f"  {tc_id}: {name} ... SKIP — {reason}")
    results.append({
        "id": tc_id, "name": name, "status": "SKIP",
        "duration": 0, "error": reason, "screenshot": None,
    })


# ---------------------------------------------------------------------
# Test case definitions — mirrors tests/test_staging_area.py and
# tests/test_containers.py, but as plain functions.
# ---------------------------------------------------------------------

def tc_pa_001(sap, page):
    card = sap.get_card(TEST_SA_NAME)
    expect(card).to_be_visible()


def tc_pa_004(sap, page):
    sap.open_grid(TEST_SA_NAME)
    expect(page.get_by_role("button", name="View")).to_be_visible()
    expect(page.get_by_role("button", name="Manage")).to_be_visible()


def tc_pa_006(sap, page):
    """
    Uses cell index 1 (pre-filled with real data — "Sidewall"/"DSW500").
    CORRECTED (Aug 11): clicking a filled cell in View mode actually opens
    a "View Trolley Details" dialog (read-only fields + a single CLOSE
    button, no Save/Cancel) — that IS the correct "read-only" behavior,
    just not what the original assertion checked for. Now explicitly
    checks for the CLOSE-only dialog and closes it via close_panel(),
    rather than the earlier (accidentally-passing) combobox check that
    left the dialog open and broke every test after it.
    """
    sap.open_grid(TEST_SA_NAME)
    sap.switch_to_view_mode()
    sap.click_cell(1)
    expect(page.get_by_role("button", name="Close")).to_be_visible()
    expect(page.get_by_role("button", name="Save")).not_to_be_visible()
    sap.close_panel()


def tc_pa_007(sap, page):
    """
    Uses cell index 1. FIXED (Aug 11): the dialog has 5 comboboxes, so a
    bare get_by_role("combobox") was ambiguous (strict-mode violation) —
    not a real failure, just an imprecise assertion. Now checks the
    specific Cell State select by its confirmed id.
    """
    sap.open_grid(TEST_SA_NAME)
    sap.switch_to_manage_mode()
    sap.click_cell(1)
    expect(page.locator(sap.CELL_STATE_SELECT_ID)).to_be_visible()
    sap.cancel()


def tc_pa_008(sap, page):
    """Uses cell index 2 — TC_PA_013 depends on this cell staying filled afterward."""
    sap.open_grid(TEST_SA_NAME)
    sap.switch_to_manage_mode()
    sap.click_cell(2)
    sap.fill_material(category="General", code="DTE18C0253", mhe_number="LT-47")
    sap.save()


def tc_pa_009(sap, page):
    """
    FIXED (Aug 11): was using cell index 3, which turned out to be the
    cell with a literal `disabled` HTML attribute (flagged during DevTools
    inspection earlier) — clicking a disabled element opens nothing, which
    is why this timed out waiting for a dialog that never appeared. Moved
    to cell index 0, confirmed interactive via TC_PA_010/011.
    """
    sap.open_grid(TEST_SA_NAME)
    sap.switch_to_manage_mode()
    sap.click_cell(0)
    trolley_visible = sap.trolley_option_visible()
    page.keyboard.press("Escape")  # close the fill-type dropdown
    sap.cancel()
    assert not trolley_visible, "Trolley option should not show for Yokohama Dahej"


def tc_pa_010(sap, page):
    """Uses cell index 0. TC_PA_011 depends on this running first (block, then unblock)."""
    sap.open_grid(TEST_SA_NAME)
    sap.switch_to_manage_mode()
    sap.click_cell(0)
    sap.set_cell_status(new_state="Blocked")
    sap.save()


def tc_pa_011(sap, page):
    """
    Uses cell index 0, same cell TC_PA_010 just blocked.
    NOTE: if this still fails after the ID-based selector fix, check
    whether a Blocked cell renders as a genuinely disabled/non-clickable
    element (one cell was observed with a literal `disabled` HTML
    attribute during DevTools inspection) — if so, click_cell(0) itself
    may not be opening the dialog at all, which would need a different
    interaction path to unblock (not yet discovered).
    """
    sap.open_grid(TEST_SA_NAME)
    sap.switch_to_manage_mode()
    sap.click_cell(0)
    sap.set_cell_status(new_state="Available")
    sap.save()


def tc_pa_013(sap, page):
    """
    CORRECTED (Aug 11): uses View mode + cell index 1, which already has
    real pre-existing data (Cell Location "Cell B1", SKU "Sidewall",
    Sub-SKU "DSW500", Qty "1") confirmed via screenshot. This decouples
    the test from TC_PA_008's fill/save succeeding first — it just reads
    existing state, which is more robust. Closes via the CLOSE button
    (this dialog only has Close, not Save/Cancel).
    """
    sap.open_grid(TEST_SA_NAME)
    sap.switch_to_view_mode()
    sap.click_cell(1)
    details = sap.view_cell_details()
    expect(details["cell_location"]).to_be_visible()
    expect(details["sku"]).to_be_visible()
    expect(details["sub_sku"]).to_be_visible()
    expect(details["quantity"]).to_be_visible()
    sap.close_details_dialog()


def tc_pa_018(cp, page):
    """CONFIRMED full flow now — Add through Save."""
    cp.add_container(
        c_type="Trolley", c_subtype="AutoTestSubtype",
        length="100", width="50", height="80", hitch_length="10", qty="2",
    )


def tc_pa_019(cp, page):
    """Confirmed behaviorally: Save with empty fields doesn't close the modal."""
    cp.attempt_save_missing_mandatory_fields()
    cp.assert_validation_blocked()
    cp.cancel_modal()


def tc_pa_018_by_type(cp, page, c_type: str):
    """
    Adds one container of the given type with randomized dimensions/qty.
    Used to confirm all three confirmed types (Trolley, Pallet, Bin) work
    through Save, not just Trolley — every earlier test only used Trolley.
    """
    cp.add_container(
        c_type=c_type,
        c_subtype=f"AutoType-{c_type}-{random.randint(1000, 9999)}",
        length=str(random.randint(50, 300)),
        width=str(random.randint(20, 150)),
        height=str(random.randint(50, 250)),
        hitch_length=str(random.randint(5, 50)),
        qty=str(random.randint(1, 20)),
    )


def tc_pa_018b(cp, page):
    cp.open_add_modal()
    cp.select_container_type("Trolley")
    cp.fill_subtype("Standard")
    cp.fill_dimensions(length="120", width="80", height="150", hitch_length="30")
    cp.cancel_modal()


# ---------------------------------------------------------------------
# HTML report generation
# ---------------------------------------------------------------------

def generate_html_report():
    os.makedirs(REPORT_DIR, exist_ok=True)
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")

    rows = []
    for r in results:
        status_class = {"PASS": "pass", "FAIL": "fail", "SKIP": "skip"}[r["status"]]
        error_html = escape(r["error"]) if r["error"] else ""
        screenshot_html = (
            f'<a href="{r["screenshot"]}" target="_blank">screenshot</a>'
            if r["screenshot"] else ""
        )
        rows.append(f"""
        <tr class="{status_class}">
            <td>{escape(r["id"])}</td>
            <td>{escape(r["name"])}</td>
            <td class="status">{r["status"]}</td>
            <td>{r["duration"]:.1f}s</td>
            <td class="error">{error_html}</td>
            <td>{screenshot_html}</td>
        </tr>""")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Processing Area Automation Report</title>
<style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #222; }}
    h1 {{ margin-bottom: 4px; }}
    .meta {{ color: #666; margin-bottom: 16px; }}
    .summary {{ display: flex; gap: 16px; margin-bottom: 20px; }}
    .summary div {{ padding: 10px 18px; border-radius: 6px; font-weight: bold; }}
    .summary .total {{ background: #eee; }}
    .summary .passed {{ background: #d4edda; color: #155724; }}
    .summary .failed {{ background: #f8d7da; color: #721c24; }}
    .summary .skipped {{ background: #fff3cd; color: #856404; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px 10px; text-align: left; font-size: 14px; }}
    th {{ background: #008080; color: white; }}
    tr.pass .status {{ color: #155724; font-weight: bold; }}
    tr.fail .status {{ color: #721c24; font-weight: bold; }}
    tr.fail {{ background: #fdecea; }}
    tr.skip .status {{ color: #856404; font-weight: bold; }}
    tr.skip {{ background: #fffaf0; }}
    .error {{ font-family: monospace; font-size: 12px; color: #721c24; max-width: 400px; }}
</style>
</head>
<body>
    <h1>Processing Area Automation Report</h1>
    <div class="meta">Run at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} — target: {escape(BASE_URL)}</div>
    <div class="summary">
        <div class="total">Total: {total}</div>
        <div class="passed">Passed: {passed}</div>
        <div class="failed">Failed: {failed}</div>
        <div class="skipped">Skipped: {skipped}</div>
    </div>
    <table>
        <tr>
            <th>Test Case ID</th><th>Name</th><th>Status</th>
            <th>Duration</th><th>Error</th><th>Screenshot</th>
        </tr>
        {"".join(rows)}
    </table>
</body>
</html>"""

    report_path = os.path.join(REPORT_DIR, "report.html")
    with open(report_path, "w") as f:
        f.write(html)
    return report_path


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=HEADLESS)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        try:
            _run_all(page)
        except Exception as e:
            # Last-resort catch: something unexpected outside any run_case/
            # run_setup wrapper. Record it so the report still gets written
            # instead of the script dying with a bare traceback.
            print(f"\nUNEXPECTED ERROR: {type(e).__name__}: {e}")
            traceback.print_exc()
            os.makedirs(SCREENSHOT_DIR, exist_ok=True)
            try:
                page.screenshot(path=os.path.join(SCREENSHOT_DIR, "unexpected_error.png"))
            except Exception:
                pass
            results.append({
                "id": "UNEXPECTED", "name": "Unhandled exception",
                "status": "FAIL", "duration": 0,
                "error": f"{type(e).__name__}: {e}",
                "screenshot": "screenshots/unexpected_error.png",
            })

        context.close()
        browser.close()

    report_path = generate_html_report()
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    print(f"\n{'='*50}")
    print(f"Total: {total}  Passed: {passed}  Failed: {failed}  Skipped: {skipped}")
    print(f"Report: file://{report_path}")
    print(f"{'='*50}")

    sys.exit(1 if failed > 0 else 0)


def _run_all(page):

    print("Logging in...")
    if not run_setup("login", page, lambda: login(page)):
        print("Login failed — cannot continue. Generating report with what we have.")
        report_path = generate_html_report()
        print(f"Report: file://{report_path}")
        sys.exit(1)

    print("\nStaging Area tests:")
    sap = StagingAreaPage(page, BASE_URL)
    staging_area_ready = run_setup(
        "open Staging Area", page, lambda: sap.open(PROC_AREA)
    )

    if staging_area_ready:
        run_case("TC_PA_001", "Card displays correct details", page, lambda: tc_pa_001(sap, page))
        run_skipped("TC_PA_002", "Active/Inactive border indicator", "spec mismatch — needs dev/product clarification")
        run_skipped("TC_PA_003", "Filter tabs scope correctly", "spec mismatch — no All/Active/Inactive filter found in build")
        run_case("TC_PA_004", "Card click navigates to grid view", page, lambda: tc_pa_004(sap, page))
        run_case("TC_PA_006", "View mode is read-only", page, lambda: tc_pa_006(sap, page))
        run_case("TC_PA_007", "Manage mode allows interaction", page, lambda: tc_pa_007(sap, page))
        run_case("TC_PA_008", "Fill Available cell with Material", page, lambda: tc_pa_008(sap, page))
        run_case("TC_PA_009", "Trolley option skipped for Yokohama Dahej", page, lambda: tc_pa_009(sap, page))
        run_case("TC_PA_010", "Block cell", page, lambda: tc_pa_010(sap, page))
        run_case("TC_PA_011", "Unblock cell", page, lambda: tc_pa_011(sap, page))
        run_case("TC_PA_013", "View filled cell details", page, lambda: tc_pa_013(sap, page))
    else:
        print("  Skipping all Staging Area test cases — setup failed above.")
        for tc_id, name in [
            ("TC_PA_001", "Card displays correct details"),
            ("TC_PA_004", "Card click navigates to grid view"),
            ("TC_PA_006", "View mode is read-only"),
            ("TC_PA_007", "Manage mode allows interaction"),
            ("TC_PA_008", "Fill Available cell with Material"),
            ("TC_PA_009", "Trolley option skipped for Yokohama Dahej"),
            ("TC_PA_010", "Block cell"),
            ("TC_PA_011", "Unblock cell"),
            ("TC_PA_013", "View filled cell details"),
        ]:
            run_skipped(tc_id, name, "blocked — Staging Area open() failed, see SETUP entry above")

    print("\nContainers tests:")
    cp = ContainersPage(page, BASE_URL)
    containers_ready = run_setup("open Containers", page, lambda: cp.open(PROC_AREA))

    run_skipped("TC_PA_017", "Table displays correct columns/data", "table row selector unconfirmed — using best-effort ARIA row role")
    if containers_ready:
        run_case("TC_PA_018", "Add new container (full save)", page, lambda: tc_pa_018(cp, page))
        run_case("TC_PA_018b", "Add Container modal opens with confirmed fields", page, lambda: tc_pa_018b(cp, page))
        run_case("TC_PA_019", "Validation on missing mandatory fields", page, lambda: tc_pa_019(cp, page))
        for c_type in ContainersPage.CONTAINER_TYPES:
            run_case(
                f"TC_PA_018_{c_type.upper()}",
                f"Add container — type {c_type} (randomized values)",
                page,
                lambda c_type=c_type: tc_pa_018_by_type(cp, page, c_type),
            )
    else:
        run_skipped("TC_PA_018", "Add new container (full save)", "blocked — Containers open() failed, see SETUP entry above")
        run_skipped("TC_PA_018b", "Add Container modal opens with confirmed fields", "blocked — Containers open() failed, see SETUP entry above")
        run_skipped("TC_PA_019", "Validation on missing mandatory fields", "blocked — Containers open() failed, see SETUP entry above")
        for c_type in ContainersPage.CONTAINER_TYPES:
            run_skipped(f"TC_PA_018_{c_type.upper()}", f"Add container — type {c_type}", "blocked — Containers open() failed, see SETUP entry above")
    run_skipped("TC_PA_020", "Export CSV", "export button interaction not yet captured in a recording")


if __name__ == "__main__":
    main()
