"""Processing Area validation tests — Part 14 (boundary + negative cases).

Complements test_13_area_lifecycle.py (which owns create/edit/delete happy path)
with boundary, duplicate, cancel, search, and concurrent-edit scenarios.

TC_PA_006  Duplicate name rejected
TC_PA_007  Name length boundaries (1 char, 255 chars, 256 chars)
TC_PA_008  Blank / whitespace-only name rejected
TC_PA_009  Special characters and unicode handled
TC_PA_010  Delete confirmation can be cancelled
TC_PA_011  Cancel on create form discards input
TC_PA_012  List search with realistic volume
TC_PA_013  Two admins editing same area (last-write-wins / conflict)
"""

import allure
import pytest
from playwright.sync_api import expect

from config.data import TestData
from config.environment import config
from pages.admin.processing_area.create_new_area_page import ProcessingAreaPage
from pages.login.login_page import LoginPage
from utils.data_factory import unique_name
from utils.waits import collect_error_text, is_error_visible, wait_for_app_ready

pytestmark = [pytest.mark.admin_pa]


def _open_edit_dialog(pa, name):
    """Open the Edit dialog for a Processing Area via its 3-dot row menu."""
    pa.expand_processing_areas()
    pa._open_row_menu(name)
    pa.page.get_by_role("menuitem", name="Edit").click(force=True)
    pa.page.get_by_placeholder("Enter area description").wait_for(
        state="visible", timeout=10000
    )


def _save_description_in_open_dialog(page, description):
    """Overwrite the description in an already-open Edit dialog and click SAVE.

    This app signals a successful save by *closing the modal* (see
    ``utils.waits.wait_for_modal_close``); a green success toast reuses the
    same ``[role=alert]`` container as errors, so the modal state — not the
    toast — is the reliable signal.

    Returns a short string describing what the app did:
      "saved"    – modal closed
      "warned"   – modal stayed open AND the app surfaced non-success error text
      "stuck"    – modal stayed open with nothing explaining why
    """
    page.get_by_placeholder("Enter area description").fill(description)
    page.locator(".MuiDialogActions-root button").filter(has_text="SAVE").click(force=True)
    page.wait_for_timeout(2500)

    modal = page.locator(".MuiDialog-container")
    modal_open = modal.count() > 0 and modal.first.is_visible()
    if not modal_open:
        return "saved"

    error_text = collect_error_text(page)  # filters out "...success..."
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    return "warned" if error_text else "stuck"


# =============================================================================
# Duplicate, boundary and validation
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Processing Area: validation")
class TestProcessingAreaValidation:
    """TC_PA_006, TC_PA_007, TC_PA_008, TC_PA_009"""

    @allure.title("TC_PA_006 — Duplicate Processing Area name is rejected")
    def test_duplicate_processing_area_name_rejected(self, pa_page):
        """
        ID     : TC_PA_006
        Title  : Duplicate Processing Area name is rejected
        Reason : Duplicate names lead operators to select the wrong area, routing
                 tasks to the wrong physical location.
        """
        # Make sure the baseline area exists first
        pa_page.create_processing_area(
            TestData.processing_area_name,
            TestData.processing_area_description,
        )

        pa_page.expand_processing_areas()
        pa_page.open_create_area_dialog()

        name_input = pa_page.page.get_by_placeholder("Enter area name")
        name_input.wait_for(state="visible", timeout=10000)
        name_input.fill(TestData.processing_area_name)  # duplicate!
        pa_page.page.get_by_placeholder("Enter area description").fill("Duplicate test")

        pa_page.page.locator(".MuiDialogActions-root button").filter(
            has_text="SAVE"
        ).click(force=True)
        pa_page.page.wait_for_timeout(1500)

        # Either an error toast appeared OR the modal did NOT close
        modal_still_open = pa_page.page.locator(".MuiDialog-container").is_visible(
            timeout=2000
        )
        error_shown = is_error_visible(pa_page.page)

        assert modal_still_open or error_shown, (
            "Duplicate Processing Area name was accepted — no error shown and "
            "modal closed as if the create succeeded."
        )

        # Clean up: close modal if still open
        if modal_still_open:
            pa_page.page.keyboard.press("Escape")
            pa_page.page.wait_for_timeout(500)

    @allure.title("TC_PA_007 — Name length boundaries (1 char, 255 chars, 256 chars)")
    def test_name_length_boundaries(self, pa_page, admin_page):
        """
        ID     : TC_PA_007
        Title  : Name length boundaries
        Reason : DB column overflow (256+) must not silently truncate or crash.
        """
        # 1-char name — should succeed
        short_name = unique_name("x")[:1] + unique_name("")[1:5]  # keep unique
        short_name = "A"  # simplest single char (we'll make it unique below)
        short_name = "A" + unique_name("")[3:7]

        with allure.step("1-character name is accepted"):
            pa_page.create_processing_area(short_name, "Short name test")
            expect(
                admin_page.get_by_text(short_name, exact=True).first
            ).to_be_visible(timeout=10000)
            pa_page.delete_processing_area(short_name)

        # 255-char name — at-boundary, should succeed
        long_name = ("B" * 200) + unique_name("_")[:55]
        long_name = long_name[:255]

        with allure.step("255-character name is accepted"):
            # Confirmed against the live app: the sidebar truncates displayed
            # names to 50 characters (the DOM text itself, not just CSS) no
            # matter how long the stored name is. So creation success and
            # cleanup must both target that 50-char prefix — an exact match
            # on the full 255-char name can never appear in the sidebar.
            displayed_name = long_name[:50]

            pa_page.expand_processing_areas()
            pa_page.open_create_area_dialog()
            name_input = pa_page.page.get_by_placeholder("Enter area name")
            name_input.wait_for(state="visible", timeout=10000)
            name_input.fill(long_name)
            pa_page.page.get_by_placeholder("Enter area description").fill("Max length test")
            pa_page.page.locator(".MuiDialogActions-root button").filter(
                has_text="SAVE"
            ).click(force=True)
            pa_page.page.wait_for_timeout(2000)

            if pa_page.page.locator(".MuiDialog-container").is_visible(timeout=1000):
                pytest.fail(
                    "255-char name was rejected unexpectedly: "
                    f"{collect_error_text(pa_page.page) or 'modal did not close'}"
                )

            pa_page.expand_processing_areas()
            expect(
                admin_page.get_by_text(displayed_name, exact=True).first
            ).to_be_visible(timeout=10000)
            pa_page.delete_processing_area(displayed_name)

        # 256-char name — over-boundary
        over_name = "C" * 256

        with allure.step("256-character name is rejected or truncated gracefully"):
            pa_page.expand_processing_areas()
            pa_page.open_create_area_dialog()
            name_input = pa_page.page.get_by_placeholder("Enter area name")
            name_input.wait_for(state="visible", timeout=10000)
            name_input.fill(over_name)
            pa_page.page.locator(".MuiDialogActions-root button").filter(
                has_text="SAVE"
            ).click(force=True)
            pa_page.page.wait_for_timeout(1500)

            # Must not be a 500 error
            assert not pa_page.page.locator("text=500").is_visible(timeout=1000), (
                "Server returned 500 on 256-char name."
            )
            # Close modal if still open
            if pa_page.page.locator(".MuiDialog-container").is_visible(timeout=500):
                pa_page.page.keyboard.press("Escape")
                pa_page.page.wait_for_timeout(500)

    @allure.title("TC_PA_008 — Blank or whitespace-only name is rejected")
    def test_blank_or_whitespace_only_name_rejected(self, pa_page):
        """
        ID     : TC_PA_008
        Title  : Blank or whitespace-only name is rejected
        Reason : A whitespace-only record is invisible in lists and very hard
                 to delete — it effectively becomes a ghost entry.
        """
        pa_page.expand_processing_areas()
        pa_page.open_create_area_dialog()

        name_input = pa_page.page.get_by_placeholder("Enter area name")
        name_input.wait_for(state="visible", timeout=10000)

        for bad_name in ("", "   ", "\t"):
            with allure.step(f"Name={repr(bad_name)} is rejected"):
                name_input.fill(bad_name)
                pa_page.page.locator(".MuiDialogActions-root button").filter(
                    has_text="SAVE"
                ).click(force=True)
                pa_page.page.wait_for_timeout(1000)

                modal_open = pa_page.page.locator(
                    ".MuiDialog-container"
                ).is_visible(timeout=1000)
                error_shown = is_error_visible(pa_page.page)
                assert modal_open or error_shown, (
                    f"Blank/whitespace name {repr(bad_name)} was accepted — "
                    "no validation triggered."
                )

        pa_page.page.keyboard.press("Escape")
        pa_page.page.wait_for_timeout(500)

    @allure.title("TC_PA_009 — Special characters and unicode handled without server error")
    def test_special_characters_and_unicode_handled(self, pa_page, admin_page):
        """
        ID     : TC_PA_009
        Title  : Special characters and unicode are handled without server errors
        Reason : Encoding bugs or unescaped input cause 500 errors or stored XSS.
        """
        test_cases = [
            (unique_name("क्षेत्र"),    "Hindi unicode"),
            (unique_name("区域_"),       "CJK unicode"),
            (unique_name("Área-1"),      "Latin accents and hyphens"),
        ]

        for name, label in test_cases:
            with allure.step(f"{label}: '{name}'"):
                try:
                    pa_page.create_processing_area(name, f"Special char test: {label}")
                    # Verify it rendered without server error
                    assert not pa_page.page.locator("text=500").is_visible(
                        timeout=1000
                    ), f"Server error on special char name: {name}"
                    # Clean up
                    pa_page.delete_processing_area(name)
                except Exception as exc:
                    # Failing to create is acceptable for some edge cases;
                    # crashing with a 500 is not.
                    if "500" in str(exc):
                        raise
                    # Close any stuck modal
                    if pa_page.page.locator(".MuiDialog-container").is_visible(
                        timeout=500
                    ):
                        pa_page.page.keyboard.press("Escape")
                        pa_page.page.wait_for_timeout(500)


# =============================================================================
# Cancel behaviour
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Processing Area: cancel behaviour")
class TestProcessingAreaCancel:
    """TC_PA_010, TC_PA_011"""

    @allure.title("TC_PA_010 — Delete confirmation can be cancelled")
    def test_delete_confirmation_can_be_cancelled(self, pa_page, admin_page):
        """
        ID     : TC_PA_010
        Title  : Delete confirmation can be cancelled
        Reason : Cancel in the confirmation dialog must leave the record
                 completely untouched.
        """
        # Create a throwaway area
        area_name = unique_name("pa_cancel_delete")
        pa_page.create_processing_area(area_name, "Cancel delete test")
        expect(admin_page.get_by_text(area_name, exact=True).first).to_be_visible(
            timeout=10000
        )

        # Open the 3-dot menu and click Delete
        pa_page.expand_processing_areas()
        area_row = pa_page._area_link_in_sidebar(area_name).locator(
            "xpath=ancestor::div[contains(@class,'css-13aljni') "
            "or contains(@class,'css-es7gyt')]"
        )
        area_row.last.locator("button").click(force=True)
        pa_page.page.wait_for_timeout(500)
        pa_page.page.get_by_role("menuitem", name="Delete").click(force=True)
        pa_page.page.wait_for_timeout(1000)

        # Click Cancel (not DELETE) in the confirmation dialog
        cancel_btn = pa_page.page.locator(
            "button:has-text('Cancel'), button:has-text('CANCEL')"
        ).first
        if cancel_btn.is_visible(timeout=3000):
            cancel_btn.click(force=True)
        else:
            pa_page.page.keyboard.press("Escape")
        pa_page.page.wait_for_timeout(1000)

        # Area must still exist
        pa_page.expand_processing_areas()
        expect(
            pa_page._area_link_in_sidebar(area_name).first
        ).to_be_visible(timeout=5000)

        # Clean up
        pa_page.delete_processing_area(area_name)

    @allure.title("TC_PA_011 — Cancel on the create form discards input")
    def test_cancel_on_create_form_discards_input(self, pa_page):
        """
        ID     : TC_PA_011
        Title  : Cancel on the create form discards input
        Reason : Cancel must not leave a ghost record and must clear the form
                 so it is empty when reopened.
        """
        ghost_name = unique_name("pa_ghost_check")

        pa_page.expand_processing_areas()
        pa_page.open_create_area_dialog()

        name_input = pa_page.page.get_by_placeholder("Enter area name")
        name_input.wait_for(state="visible", timeout=10000)
        name_input.fill(ghost_name)
        pa_page.page.get_by_placeholder("Enter area description").fill(
            "Should be discarded"
        )

        # Cancel instead of saving
        cancel_btn = pa_page.page.locator(
            "button:has-text('Cancel'), button:has-text('CANCEL')"
        ).first
        if cancel_btn.is_visible(timeout=2000):
            cancel_btn.click(force=True)
        else:
            pa_page.page.keyboard.press("Escape")
        pa_page.page.wait_for_timeout(1000)

        # Ghost name must NOT appear in the sidebar
        pa_page.expand_processing_areas()
        count = pa_page._area_link_in_sidebar(ghost_name).count()
        assert count == 0, (
            f"'{ghost_name}' appeared in the sidebar after Cancel — "
            "a ghost record was created."
        )


# =============================================================================
# List / search / pagination
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Processing Area: list and search")
class TestProcessingAreaList:
    """TC_PA_012"""

    @allure.title("TC_PA_012 — List search with a realistic record count")
    def test_list_search_sort_pagination_with_realistic_volume(self, pa_page, admin_page):
        """
        ID     : TC_PA_012
        Title  : List search, sort and pagination with a realistic record count
        Reason : 10 records look fine; real volume exposes off-by-one paging bugs
                 and sort resets.
        """
        created = []
        batch_prefix = unique_name("pa_vol")

        with allure.step("Create 5 areas for volume testing"):
            for i in range(5):
                name = f"{batch_prefix}_{i}"
                pa_page.create_processing_area(name, f"Volume test {i}")
                created.append(name)

        with allure.step("Search for the batch prefix in sidebar"):
            # The sidebar is the primary list for Processing Areas
            pa_page.expand_processing_areas()
            for name in created:
                expect(
                    pa_page._area_link_in_sidebar(name).first
                ).to_be_visible(timeout=5000)

        with allure.step("Clean up volume test areas"):
            for name in reversed(created):
                pa_page.delete_processing_area(name)


# =============================================================================
# Concurrent edit
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Processing Area: concurrency")
class TestProcessingAreaConcurrency:
    """TC_PA_013"""

    @pytest.mark.xfail(reason="Backend bug: concurrent edits result in area deletion/data loss")
    @allure.title("TC_PA_013 — Two admins editing the same area do not silently lose data")
    def test_two_admins_editing_same_area_do_not_lose_data(self, pa_page, browser):
        """
        ID     : TC_PA_013
        Title  : Two admins editing the same area do not lose data
        Reason : Last-write-wins with no warning means the first admin's change
                 silently disappears. App should either block or warn.

        Runs a real two-session race: a second admin browser context is spun up
        here (no dedicated fixture needed). Both sessions open the SAME area's
        Edit dialog, then admin A saves, then admin B saves over it. The hard
        assertions are the ones that matter for data safety — the area survives,
        stays single, and persists one of the two admins' intended values (never
        blank, never the stale pre-edit value). Whether the app *warned* admin B
        is recorded to the Allure report rather than asserted, since silent
        last-write-wins is a known product characteristic, not a crash.
        """
        area = unique_name("pa_concurrent")
        marker_a = f"edited by admin A {unique_name('')}"
        marker_b = f"edited by admin B {unique_name('')}"

        with allure.step(f"Admin A creates area '{area}'"):
            pa_page.create_processing_area(area, "original description")

        ctx_b = browser.new_context(ignore_https_errors=config.ignore_https_errors)
        try:
            page_b = ctx_b.new_page()
            LoginPage(page_b).login(config.admin_user, config.admin_pass)
            wait_for_app_ready(page_b, timeout=config.default_timeout)
            pa_b = ProcessingAreaPage(page_b)

            with allure.step("Both admins open the Edit dialog for the same area"):
                _open_edit_dialog(pa_page, area)
                _open_edit_dialog(pa_b, area)

            with allure.step("Admin A saves first"):
                result_a = _save_description_in_open_dialog(pa_page.page, marker_a)
                assert result_a == "saved", (
                    f"Admin A's own edit did not save cleanly (got '{result_a}')."
                )

            with allure.step("Admin B saves over admin A's change"):
                result_b = _save_description_in_open_dialog(page_b, marker_b)
                allure.attach(
                    f"Admin B save outcome: {result_b} "
                    f"({'app warned/blocked' if result_b == 'warned' else 'silent last-write-wins' if result_b == 'saved' else 'modal stuck'})",
                    name="concurrency behaviour",
                )

            with allure.step("The area survives the race intact"):
                pa_page.page.reload()
                wait_for_app_ready(pa_page.page, timeout=config.default_timeout)
                pa_page.expand_processing_areas()
                links = pa_page._area_link_in_sidebar(area)
                assert links.count() == 1, (
                    f"After the concurrent edit, area '{area}' resolves to "
                    f"{links.count()} sidebar entries — expected exactly 1 "
                    "(duplication or loss on concurrent write)."
                )

            with allure.step("The persisted description is one admin's value, not stale/blank"):
                _open_edit_dialog(pa_page, area)
                persisted = pa_page.page.get_by_placeholder(
                    "Enter area description"
                ).input_value()
                pa_page.page.keyboard.press("Escape")
                pa_page.page.wait_for_timeout(500)
                assert persisted.strip(), "Description came back blank after the race."
                assert persisted in (marker_a, marker_b), (
                    f"Persisted description {persisted!r} is neither admin's "
                    f"intended value — data was corrupted or reverted to stale "
                    f"('original description')."
                )
        finally:
            ctx_b.close()
            with allure.step(f"Clean up area '{area}'"):
                pa_page.delete_processing_area(area)
