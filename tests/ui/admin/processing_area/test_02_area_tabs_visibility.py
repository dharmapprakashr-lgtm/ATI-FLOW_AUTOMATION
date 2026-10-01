"""Processing Area tab visibility tests — Part 3.

Runs after test_01_processing_area_creation.py (PA exists + tab strip visible).
Navigates to each tab in a single pass and asserts every sub-tab defined by
the application is present, enabled, and selectable.

Tabs verified (matches the UI tab strip from left to right):
  TC_PA_TAB_001  Materials
  TC_PA_TAB_002  Containers
  TC_PA_TAB_003  Workflow
  TC_PA_TAB_004  WIP Inventory
  TC_PA_TAB_005  Staging Area
  TC_PA_TAB_006  Station Mapping
  TC_PA_TAB_007  Machine Names
"""

import allure
import pytest
from playwright.sync_api import expect

from config.data import TestData

pytestmark = [pytest.mark.admin, pytest.mark.smoke]

# All tabs in left-to-right order as they appear in the UI tab strip
EXPECTED_TABS = [
    ("TC_PA_TAB_001", "Materials"),
    ("TC_PA_TAB_002", "Containers"),
    ("TC_PA_TAB_003", "Workflow"),
    ("TC_PA_TAB_004", "WIP Inventory"),
    ("TC_PA_TAB_005", "Staging Area"),
    ("TC_PA_TAB_006", "Station Mapping"),
    ("TC_PA_TAB_007", "Machine Names"),
]


@allure.feature("Admin Console")
@allure.story("Processing Area: tab visibility")
class TestProcessingAreaTabsVisible:
    """TC_PA_TAB_001 – TC_PA_TAB_007

    A single test navigates to every Processing Area tab in sequence inside
    one browser session. Each tab is verified to be visible, enabled, and
    becomes selected after clicking.
    """

    # ── helpers ───────────────────────────────────────────────────────────────

    @pytest.fixture(autouse=True)
    def _navigate_to_area(self, pa_page, browser_type_launch_args, pytestconfig):
        """Navigate to the baseline Processing Area before the test runs."""
        pa_page.navigate_to_existing_area(TestData.processing_area_name)
        self._tab_view_ms = (
            0 if browser_type_launch_args.get("headless", True)
            else pytestconfig.getoption("tab_view_ms")
        )

    def _open_tab(self, page, name):
        """Click a tab and assert it is visible, enabled, and selected."""
        with allure.step(f"Open and verify the '{name}' tab"):
            tab = page.get_by_role("tab", name=name, exact=True)
            tab.scroll_into_view_if_needed()
            expect(tab).to_be_visible(timeout=8_000)
            expect(tab).to_be_enabled()
            expect(tab).not_to_have_attribute("aria-disabled", "true")
            tab.click()
            expect(tab).to_have_attribute("aria-selected", "true", timeout=8_000)
            if self._tab_view_ms:
                page.wait_for_timeout(self._tab_view_ms)

    # ── single combined test ──────────────────────────────────────────────────

    @allure.title("TC_PA_TAB_001–007 — All tabs are visible and navigable in one pass")
    def test_all_tabs_visible_in_one_pass(self, admin_page):
        """
        ID     : TC_PA_TAB_001 – TC_PA_TAB_007
        Title  : All seven Processing Area tabs can be selected in sequence
        Reason : Opens the Processing Area once and walks through every tab
                 left-to-right. Faster than individual tests (single login /
                 navigation) while still pinpointing which tab failed via the
                 Allure step report.

        Expected tab order (left → right):
          Materials · Containers · Workflow · WIP Inventory ·
          Staging Area · Station Mapping · Machine Names
        """
        for tc_id, tab_name in EXPECTED_TABS:
            with allure.step(f"{tc_id} — '{tab_name}' tab"):
                self._open_tab(admin_page, tab_name)
