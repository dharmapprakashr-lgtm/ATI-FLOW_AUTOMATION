"""
run_automation_own_area.py
----------------------------
The FULL Processing Area Sub-Tabs test suite (same test cases as
run_automation.py / the original ticket), but run against a BRAND NEW,
dedicated processing area created by this script itself — not the shared
"august" area. Fully isolated, safe to re-run repeatedly.

Usage:
    python3 run_automation_own_area.py

What this does, in order:
    1. Creates a new area (name: AutoTest_XXXXX, random each run)
    2. Attempts to add one material (diagnostic only — does NOT block
       later steps if it fails; the staging area and containers have been
       confirmed to work independently of material creation)
    3. Adds one container
    4. Opens the area's Staging Area tab and grid (via card index — a
       fresh area's staging area has no name we know ahead of time)
    5. Runs the full set of confirmed cell-level tests (TC_PA_001, 004,
       006, 007, 008, 009, 010, 011, 013) — reordered/adapted from the
       'august' version since a fresh grid starts EMPTY (no pre-existing
       filled cell to read), so TC_PA_006/013 now fill a cell first, then
       read it back, instead of relying on real leftover data.
    6. Runs the full set of confirmed Container tests (TC_PA_018, 018b,
       019, and all three container types) via the same ContainersPage
       already proven in run_automation.py.
    7. Same skips as the 'august' suite: TC_PA_002/003 (spec mismatch —
       applies regardless of which area), TC_PA_017 (table row selector
       unconfirmed), TC_PA_020 (Export CSV not yet recorded).

Does NOT clean up after itself — each run creates a new area.

Config via environment variables:
    BASE_URL, ADMIN_USER, ADMIN_PASS, HEADLESS
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
from pages.processing_area_page import ProcessingAreaPage
from pages.materials_page import MaterialsPage
from pages.staging_area_page import StagingAreaPage
from pages.containers_page import ContainersPage

BASE_URL = os.getenv("BASE_URL", "https://192.168.6.32")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"

AREA_NAME = f"AutoTest_{random.randint(10000, 99999)}"

REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
SCREENSHOT_DIR = os.path.join(REPORT_DIR, "screenshots")

results = []


def login(page):
    page.set_default_timeout(10000)
    page.goto(f"{BASE_URL}/login")
    page.get_by_role("textbox", name="Username").fill(ADMIN_USER)
    page.get_by_role("textbox", name="Password").fill(ADMIN_PASS)
    page.get_by_role("button", name="Login").click()
    page.wait_for_load_state("networkidle")


def _cleanup_after_test(page):
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass


def run_case(tc_id, name, page, fn):
    print(f"  {tc_id}: {name} ... ", end="", flush=True)
    start = time.time()
    try:
        fn()
        duration = time.time() - start
        results.append({"id": tc_id, "name": name, "status": "PASS", "duration": duration, "error": None, "screenshot": None})
        print(f"PASS ({duration:.1f}s)")
    except Exception as e:
        duration = time.time() - start
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        screenshot_rel = f"screenshots/own_area_{tc_id}.png"
        try:
            page.screenshot(path=os.path.join(REPORT_DIR, screenshot_rel))
        except Exception:
            screenshot_rel = None
        results.append({"id": tc_id, "name": name, "status": "FAIL", "duration": duration, "error": f"{type(e).__name__}: {e}", "screenshot": screenshot_rel})
        print(f"FAIL ({duration:.1f}s) — {type(e).__name__}: {e}")
    finally:
        _cleanup_after_test(page)


def run_skipped(tc_id, name, reason):
    print(f"  {tc_id}: {name} ... SKIP — {reason}")
    results.append({"id": tc_id, "name": name, "status": "SKIP", "duration": 0, "error": reason, "screenshot": None})


def run_setup(step_name, page, fn):
    print(f"[setup] {step_name} ... ", end="", flush=True)
    try:
        fn()
        print("OK")
        return True
    except Exception as e:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        screenshot_rel = f"screenshots/own_area_setup_{step_name.replace(' ', '_')}.png"
        try:
            page.screenshot(path=os.path.join(REPORT_DIR, screenshot_rel))
        except Exception:
            screenshot_rel = None
        print(f"FAILED — {type(e).__name__}: {e}")
        try:
            print(f"  current URL: {page.url}")
        except Exception:
            pass
        results.append({"id": f"SETUP_{step_name.replace(' ', '_')}", "name": step_name, "status": "FAIL", "duration": 0, "error": f"{type(e).__name__}: {e}", "screenshot": screenshot_rel})
        return False


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
        screenshot_html = f'<a href="{r["screenshot"]}" target="_blank">screenshot</a>' if r["screenshot"] else ""
        rows.append(f"""
        <tr class="{status_class}">
            <td>{escape(r["id"])}</td><td>{escape(r["name"])}</td>
            <td class="status">{r["status"]}</td><td>{r["duration"]:.1f}s</td>
            <td class="error">{error_html}</td><td>{screenshot_html}</td>
        </tr>""")
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
    <title>Own Test Area — Full Suite Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 24px; color: #222; }}
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
    </style></head><body>
    <h1>Own Test Area — Full Suite Report</h1>
    <div class="meta">Run at REPLACED_TIME — area: REPLACED_AREA — target: REPLACED_URL</div>
    <div class="summary">
        <div class="total">Total: REPLACED_TOTAL</div>
        <div class="passed">Passed: REPLACED_PASSED</div>
        <div class="failed">Failed: REPLACED_FAILED</div>
        <div class="skipped">Skipped: REPLACED_SKIPPED</div>
    </div>
    <table><tr><th>ID</th><th>Name</th><th>Status</th><th>Duration</th><th>Error</th><th>Screenshot</th></tr>
    REPLACED_ROWS</table></body></html>"""

    total_v = total
    passed_v = passed
    failed_v = failed
    skipped_v = skipped
    html = html.replace("REPLACED_TIME", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    html = html.replace("REPLACED_AREA", escape(AREA_NAME))
    html = html.replace("REPLACED_URL", escape(BASE_URL))
    html = html.replace("REPLACED_TOTAL", str(total_v))
    html = html.replace("REPLACED_PASSED", str(passed_v))
    html = html.replace("REPLACED_FAILED", str(failed_v))
    html = html.replace("REPLACED_SKIPPED", str(skipped_v))
    html = html.replace("REPLACED_ROWS", "".join(rows))

    report_path = os.path.join(REPORT_DIR, "report_own_area.html")
    with open(report_path, "w") as f:
        f.write(html)
    return report_path


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=HEADLESS)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        try:
            _run_all(page)
        except Exception as e:
            print(f"\nUNEXPECTED ERROR: {type(e).__name__}: {e}")
            traceback.print_exc()

        context.close()
        browser.close()

    report_path = generate_html_report()
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    print(f"\n{'='*50}")
    print(f"Area created: {AREA_NAME}")
    print(f"Total: {total}  Passed: {passed}  Failed: {failed}  Skipped: {skipped}")
    print(f"Report: file://{report_path}")
    print(f"{'='*50}")
    sys.exit(1 if failed > 0 else 0)


def _run_all(page):
    print("Logging in...")
    if not run_setup("login", page, lambda: login(page)):
        return

    print(f"\nCreating dedicated test area: {AREA_NAME}")
    pap = ProcessingAreaPage(page, BASE_URL)
    if not run_setup("create area", page, lambda: pap.create_area(AREA_NAME, "Created by automation")):
        return

    print("\nAdding one material (diagnostic only, does not block later steps)...")
    mp = MaterialsPage(page, BASE_URL)
    run_setup("add material", page, lambda: mp.add_material(
        class_name=f"AutoMat_{random.randint(100, 999)}",
        unit="A",
        pre_proc_time="1",
        max_qty="10",
        enable_staging_area=True,
        prefix=f"MAT-{random.randint(100, 999)}",
    ))
    # If the material modal is still open (failed), press Escape so it
    # doesn't block the container/staging steps below.
    page.keyboard.press("Escape")

    print("\nAdding one container...")
    cp = ContainersPage(page, BASE_URL)
    containers_ready = run_setup("open Containers", page, lambda: cp.open(AREA_NAME))

    def do_container_tests():
        run_case("TC_PA_018", "Add new container (full save)", page, lambda: cp.add_container(
            c_type="Trolley", c_subtype="OwnAreaSetup",
            length="100", width="50", height="80", hitch_length="10", qty="1",
        ))

        def tc_018b():
            cp.open_add_modal()
            cp.select_container_type("Trolley")
            cp.fill_subtype("Standard")
            cp.fill_dimensions(length="120", width="80", height="150", hitch_length="30")
            cp.cancel_modal()

        run_case("TC_PA_018b", "Add Container modal opens with confirmed fields", page, tc_018b)

        def tc_019():
            cp.attempt_save_missing_mandatory_fields()
            cp.assert_validation_blocked()
            cp.cancel_modal()

        run_case("TC_PA_019", "Validation on missing mandatory fields", page, tc_019)

        for c_type in ContainersPage.CONTAINER_TYPES:
            def make_type_test(c_type=c_type):
                def _test():
                    cp.add_container(
                        c_type=c_type,
                        c_subtype=f"AutoType-{c_type}-{random.randint(1000, 9999)}",
                        length=str(random.randint(50, 300)),
                        width=str(random.randint(20, 150)),
                        height=str(random.randint(50, 250)),
                        hitch_length=str(random.randint(5, 50)),
                        qty=str(random.randint(1, 20)),
                    )
                return _test
            run_case(f"TC_PA_018_{c_type.upper()}", f"Add container — type {c_type} (randomized values)", page, make_type_test())

    if containers_ready:
        do_container_tests()
    else:
        for tc_id, name in [
            ("TC_PA_018", "Add new container (full save)"),
            ("TC_PA_018b", "Add Container modal opens with confirmed fields"),
            ("TC_PA_019", "Validation on missing mandatory fields"),
            ("TC_PA_018_TROLLEY", "Add container — type Trolley"),
            ("TC_PA_018_PALLET", "Add container — type Pallet"),
            ("TC_PA_018_BIN", "Add container — type Bin"),
        ]:
            run_skipped(tc_id, name, "blocked — Containers open() failed, see SETUP entry above")

    run_skipped("TC_PA_017", "Table displays correct columns/data", "table row selector unconfirmed")
    run_skipped("TC_PA_020", "Export CSV", "export button interaction not yet captured in a recording")

    print("\nOpening auto-provisioned staging area...")
    sap = StagingAreaPage(page, BASE_URL)

    def open_staging_tab():
        page.locator("#operator-sidebar-nav").get_by_text(AREA_NAME, exact=True).click()
        page.get_by_role("tab", name="Staging Area").click()

    staging_ready = run_setup("open Staging Area tab", page, open_staging_tab)
    if not staging_ready:
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
            run_skipped(tc_id, name, "blocked — Staging Area tab failed, see SETUP entry above")
        run_skipped("TC_PA_002", "Active/Inactive border indicator", "spec mismatch — needs dev/product clarification")
        run_skipped("TC_PA_003", "Filter tabs scope correctly", "spec mismatch — no All/Active/Inactive filter found in build")
        return

    def tc_001():
        expect(sap.get_card_by_index(0)).to_be_visible()

    run_case("TC_PA_001", "Card displays correct details", page, tc_001)

    run_skipped("TC_PA_002", "Active/Inactive border indicator", "spec mismatch — needs dev/product clarification")
    run_skipped("TC_PA_003", "Filter tabs scope correctly", "spec mismatch — no All/Active/Inactive filter found in build")

    def tc_004():
        sap.open_grid_by_index(0)
        expect(page.get_by_role("button", name="View")).to_be_visible()
        expect(page.get_by_role("button", name="Manage")).to_be_visible()

    run_case("TC_PA_004", "Card click navigates to grid view", page, tc_004)

    def tc_006():
        """
        Adapted: fresh grid has no pre-existing filled cell, so fill
        cell 0 first, THEN switch to View mode and confirm the read-only
        dialog. Also sets up the data TC_PA_013 reads back later.
        """
        sap.switch_to_manage_mode()
        sap.click_cell(0)
        sap.fill_material(category="General", code="DTE18C0253", mhe_number="LT-47")
        sap.save()
        sap.switch_to_view_mode()
        sap.click_cell(0)
        expect(page.get_by_role("button", name="Close")).to_be_visible()
        expect(page.get_by_role("button", name="Save")).not_to_be_visible()
        sap.close_panel()

    run_case("TC_PA_006", "View mode is read-only (fills cell 0 first)", page, tc_006)

    def tc_007():
        sap.switch_to_manage_mode()
        sap.click_cell(1)
        expect(page.locator(sap.CELL_STATE_SELECT_ID)).to_be_visible()
        sap.cancel()

    run_case("TC_PA_007", "Manage mode allows interaction", page, tc_007)

    def tc_008():
        sap.click_cell(2)
        sap.fill_material(category="General", code="DTE18C0253", mhe_number="LT-47")
        sap.save()

    run_case("TC_PA_008", "Fill Available cell with Material", page, tc_008)

    def tc_009():
        sap.click_cell(1)
        trolley_visible = sap.trolley_option_visible()
        page.keyboard.press("Escape")
        sap.cancel()
        assert not trolley_visible, "Trolley option should not show for Yokohama Dahej"

    run_case("TC_PA_009", "Trolley option skipped for Yokohama Dahej", page, tc_009)

    def tc_010():
        """
        Uses cell index 1, NOT 3 — cell index 3 is the same disabled cell
        discovered in the 'august' grid (it never opens the Manage
        dialog). Index 1 is already proven interactive by TC_PA_007/009
        earlier in this same run.
        """
        sap.click_cell(1)
        sap.set_cell_status(new_state="Blocked")
        sap.save()

    run_case("TC_PA_010", "Block cell", page, tc_010)

    def tc_011():
        sap.click_cell(1)
        sap.set_cell_status(new_state="Available")
        sap.save()

    run_case("TC_PA_011", "Unblock cell", page, tc_011)

    def tc_013():
        sap.switch_to_view_mode()
        sap.click_cell(0)
        details = sap.view_cell_details()
        expect(details["cell_location"]).to_be_visible()
        expect(details["sku"]).to_be_visible()
        expect(details["sub_sku"]).to_be_visible()
        expect(details["quantity"]).to_be_visible()
        sap.close_details_dialog()

    run_case("TC_PA_013", "View filled cell details", page, tc_013)


if __name__ == "__main__":
    main()
