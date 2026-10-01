"""Processing Area creation — end-to-end in one pass.

TC_PA_001  Admin dashboard is visible after login
TC_PA_002  'Processing Areas' section expands in the sidebar
TC_PA_003  'Create New Area' button is clickable and opens the dialog
TC_PA_004  New Processing Area is saved and appears in the sidebar
TC_PA_005  Navigating to the area renders the full tab strip
"""

import allure
import pytest
from playwright.sync_api import expect

from config.data import TestData

pytestmark = [pytest.mark.admin, pytest.mark.smoke]


@allure.feature("Admin Console")
@allure.story("Processing Area: creation and verification")
class TestProcessingAreaCreation:
    """Single sequential test — one browser session, one navigation chain.

    Walks through the full creation flow:
      login → dashboard visible → expand sidebar → open dialog →
      fill form → save → confirm in sidebar → open area → tab strip visible.
    """

    @allure.title("TC_PA_001–005 — Create Processing Area and verify tab strip in one pass")
    def test_create_processing_area_full_flow(self, admin_page, pa_page):
        """
        ID     : TC_PA_001 – TC_PA_005
        Title  : Processing Area creation flow — dashboard → sidebar → create → tabs
        Reason : Validates the full creation journey in a single browser session.
                 Each Allure step maps to one TC so failures are easy to triage.
        """

        # ── TC_PA_001 — Admin dashboard is visible ────────────────────────────
        with allure.step("TC_PA_001 — Admin dashboard loads after login"):
            expect(
                admin_page.locator("#operator-sidebar-root"),
                "Admin sidebar should be visible — confirms dashboard loaded",
            ).to_be_visible(timeout=15_000)

        # ── TC_PA_002 — Expand 'Processing Areas' section ─────────────────────
        with allure.step("TC_PA_002 — Expand 'Processing Areas' in the sidebar"):
            pa_page.expand_processing_areas()
            expect(
                admin_page.get_by_text("Create New Area", exact=True).last,
                "'Create New Area' button must appear after expanding the section",
            ).to_be_visible(timeout=10_000)

        # ── TC_PA_003 — 'Create New Area' opens dialog ────────────────────────
        with allure.step("TC_PA_003 — Click 'Create New Area' and verify the dialog opens"):
            # If the area already exists navigate to it and skip creation
            existing = admin_page.get_by_text(
                TestData.processing_area_name, exact=True
            )
            if existing.count() > 0:
                allure.attach(
                    f"'{TestData.processing_area_name}' already exists — skipping creation.",
                    name="info",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                admin_page.get_by_text("Create New Area", exact=True).last.click(
                    force=True
                )
                name_input = admin_page.get_by_placeholder("Enter area name")
                expect(
                    name_input,
                    "Create-area dialog should open with the name input",
                ).to_be_visible(timeout=10_000)

                # ── TC_PA_004 — Fill the form and save ────────────────────────
                with allure.step(
                    f"TC_PA_004 — Fill name='{TestData.processing_area_name}' "
                    f"and description, then save"
                ):
                    name_input.fill(TestData.processing_area_name)
                    admin_page.get_by_placeholder("Enter area description").fill(
                        TestData.processing_area_description
                    )
                    admin_page.locator(".MuiDialogActions-root button").filter(
                        has_text="SAVE"
                    ).click(force=True)

                    # Confirm the area link appears in the sidebar after saving
                    saved_link = admin_page.locator(
                        "#operator-sidebar-root"
                    ).get_by_text(TestData.processing_area_name, exact=True)
                    expect(
                        saved_link.first,
                        f"'{TestData.processing_area_name}' must appear in the "
                        "sidebar after saving",
                    ).to_be_visible(timeout=15_000)

        # ── TC_PA_004 (verify) — area link in sidebar ─────────────────────────
        with allure.step(
            f"TC_PA_004 — Confirm '{TestData.processing_area_name}' is listed in the sidebar"
        ):
            area_link = admin_page.locator("#operator-sidebar-root").get_by_text(
                TestData.processing_area_name, exact=True
            )
            expect(area_link.first).to_be_visible(timeout=10_000)

        # ── TC_PA_005 — Navigate to area and verify tab strip ─────────────────
        with allure.step(
            f"TC_PA_005 — Click '{TestData.processing_area_name}' and verify the tab strip"
        ):
            pa_page.navigate_to_existing_area(TestData.processing_area_name)
            expect(
                admin_page.locator("[role='tablist']"),
                "Tab strip (tablist) must be visible after opening the Processing Area",
            ).to_be_visible(timeout=15_000)
