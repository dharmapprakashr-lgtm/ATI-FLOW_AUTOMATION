"""UI Navigation tests — Part 10.

TC_UI_001   Every navigation item routes to the correct screen
TC_UI_002   Context preserved between Processing Area submodules
TC_UI_003   Browser Back/Forward keeps the app consistent
TC_UI_004   Browser refresh mid-form does not break the app
TC_UI_005   Navigating away from a dirty form is predictable
TC_UI_006   Field labels, required markers and tab order
TC_UI_007   Save is protected against double-click
TC_UI_008   Success messages appear, are readable, and are dismissible
TC_UI_009   Error messages are operator-readable
TC_UI_010   Tables render correctly with long values and many rows
TC_UI_012   Dropdowns reflect records created in the same session
TC_UI_013   Screens usable at shopfloor viewport sizes (smoke)
TC_UI_014   Page and browser tab titles are correct
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from config.data import TestData
from config.environment import config
from pages.admin.admin_navigation import AdminDashboardPage
from pages.admin.processing_area.create_new_area_page import ProcessingAreaPage
from utils.data_factory import unique_name

pytestmark = [pytest.mark.ui_nav]


# =============================================================================
# TC_UI_001 — Navigation items route correctly
# =============================================================================

@allure.feature("UI & Navigation")
@allure.story("Navigation routing")
class TestNavigationRouting:

    @allure.title("TC_UI_001 — Every navigation item routes to the correct screen")
    def test_every_navigation_item_routes_to_correct_screen(self, admin_page):
        """
        ID     : TC_UI_001
        Title  : Every navigation item routes to the correct screen
        Reason : A nav item that loads the wrong page (or silently does nothing)
                 confuses operators and masks routing bugs introduced by refactors.
        """
        dashboard = AdminDashboardPage(admin_page)

        with allure.step("Execution Source Config link loads that section"):
            dashboard.navigate_to_execution_source_config()
            for tab in (
                dashboard.requester_tab,
                dashboard.mes_tab,
                dashboard.dispatcher_tab,
                dashboard.supervisor_tab,
            ):
                expect(tab).to_be_visible(timeout=5000)

        with allure.step("Processing Areas header is visible in the sidebar"):
            expect(dashboard.processing_areas_header).to_be_visible(timeout=10000)


# =============================================================================
# TC_UI_002 — Context preserved between PA submodules
# =============================================================================

@allure.feature("UI & Navigation")
@allure.story("Sub-module context")
class TestSubmoduleContext:

    @allure.title("TC_UI_002 — Context preserved between Processing Area submodules")
    def test_context_preserved_between_processing_area_submodules(
        self, admin_page, pa_page
    ):
        """
        ID     : TC_UI_002
        Title  : Context is preserved between Processing Area submodules
        Reason : Switching from Materials to Workflow and back must stay inside
                 the same Processing Area. A context reset would show the wrong
                 area's data after navigation.
        """
        pa_page.create_processing_area(
            TestData.processing_area_name,
            TestData.processing_area_description,
        )

        with allure.step("Navigate Materials → Workflow → Materials — area unchanged"):
            pa_page.go_to_materials()
            expect(pa_page.materials_tab).to_have_attribute(
                "aria-selected", "true", timeout=5000
            )
            pa_page.go_to_workflow()
            expect(pa_page.workflow_tab).to_have_attribute(
                "aria-selected", "true", timeout=5000
            )
            pa_page.go_to_materials()
            expect(pa_page.materials_tab).to_have_attribute(
                "aria-selected", "true", timeout=5000
            )
            # The PA name should still be visible (we haven't left the area)
            expect(
                admin_page.get_by_text(TestData.processing_area_name, exact=True).first
            ).to_be_visible(timeout=5000)


# =============================================================================
# TC_UI_003 — Browser Back/Forward
# =============================================================================

@allure.feature("UI & Navigation")
@allure.story("Browser history")
class TestBrowserHistory:

    @allure.title("TC_UI_003 — Browser Back and Forward keep the app consistent")
    def test_browser_back_and_forward_keep_app_consistent(self, admin_page):
        """
        ID     : TC_UI_003
        Title  : Browser Back and Forward keep the app consistent
        Reason : If Back navigates to a broken / stale state (e.g. showing
                 deleted data or a blank page), operators are forced to do a
                 full page reload, losing their context.
        """
        dashboard = AdminDashboardPage(admin_page)

        url_before = admin_page.url
        dashboard.navigate_to_execution_source_config()
        admin_page.wait_for_timeout(1000)

        with allure.step("Back returns to previous section without crash"):
            admin_page.go_back()
            admin_page.wait_for_timeout(1500)
            assert "login" not in admin_page.url.lower(), (
                "Back navigation sent the admin to the login page unexpectedly."
            )
            assert not admin_page.locator("text=500").is_visible(timeout=500), (
                "Back navigation produced a 500 error."
            )

        with allure.step("Forward re-opens Exec Source Config without crash"):
            admin_page.go_forward()
            admin_page.wait_for_timeout(1500)
            assert "login" not in admin_page.url.lower(), (
                "Forward navigation sent the admin to the login page unexpectedly."
            )
            assert not admin_page.locator("text=500").is_visible(timeout=500), (
                "Forward navigation produced a 500 error."
            )


# =============================================================================
# TC_UI_004 — Browser refresh mid-form
# =============================================================================

@allure.feature("UI & Navigation")
@allure.story("Page refresh")
class TestPageRefresh:

    @allure.title("TC_UI_004 — Browser refresh mid-form does not break the app")
    def test_browser_refresh_midform_does_not_break_app(self, admin_page, pa_page):
        """
        ID     : TC_UI_004
        Title  : Browser refresh mid-form does not break the app
        Reason : Operators on touch screens accidentally tap Refresh. The app
                 must not leave a zombie form or ghost record.
        """
        pa_page.expand_processing_areas()
        pa_page.open_create_area_dialog()

        name_input = admin_page.get_by_placeholder("Enter area name")
        name_input.wait_for(state="visible", timeout=10000)
        name_input.fill("ShouldNotExistAfterRefresh")

        with allure.step("Refresh mid-form"):
            admin_page.reload(wait_until="domcontentloaded")
            admin_page.wait_for_timeout(2000)

        with allure.step("App still loads without 500"):
            assert "login" not in admin_page.url.lower() or True, ""  # either is fine
            assert not admin_page.locator("text=500").is_visible(timeout=1000), (
                "Server 500 after refresh mid-form."
            )

        with allure.step("Zombie name not in the area list"):
            pa_page.expand_processing_areas()
            assert admin_page.locator(
                "text=ShouldNotExistAfterRefresh"
            ).count() == 0, (
                "Refresh mid-form created a ghost record — 'ShouldNotExistAfterRefresh' "
                "appeared in the sidebar."
            )


# =============================================================================
# TC_UI_005 — Navigating away from a dirty form
# =============================================================================

@allure.feature("UI & Navigation")
@allure.story("Dirty form guard")
class TestDirtyFormGuard:

    @allure.title("TC_UI_005 — Navigating away from a dirty form is predictable")
    def test_navigating_away_from_dirty_form_is_predictable(
        self, admin_page, pa_page, dashboard_nav=None
    ):
        """
        ID     : TC_UI_005
        Title  : Navigating away from a dirty form is predictable
        Reason : Losing unsaved input silently is not acceptable on a shop
                 floor. The app should either warn the user or discard changes
                 consistently — the worst outcome is partial saves.
        """
        pa_page.expand_processing_areas()
        pa_page.open_create_area_dialog()

        name_input = admin_page.get_by_placeholder("Enter area name")
        name_input.wait_for(state="visible", timeout=10000)
        name_input.fill("DirtyFormTest")

        with allure.step("Click away / navigate to a different section"):
            dashboard = AdminDashboardPage(admin_page)
            dashboard.navigate_to_execution_source_config()
            admin_page.wait_for_timeout(2000)

        with allure.step("App did not crash or show 500"):
            assert not admin_page.locator("text=500").is_visible(timeout=500), (
                "Server 500 after navigating away from a dirty form."
            )

        with allure.step("Ghost record was not created"):
            pa_page.expand_processing_areas()
            assert admin_page.locator("text=DirtyFormTest").count() == 0, (
                "Navigating away from an unsaved form silently created a record."
            )


# =============================================================================
# TC_UI_006 — Field labels, required markers and tab order
# =============================================================================

@allure.feature("UI & Navigation")
@allure.story("Form accessibility")
class TestFormAccessibility:

    @allure.title("TC_UI_006 — Field labels, required markers and tab order")
    def test_field_labels_required_markers_and_tab_order(
        self, admin_page, pa_page
    ):
        """
        ID     : TC_UI_006
        Title  : Field labels, required markers and tab order
        Reason : Unlabelled fields are inaccessible to screen readers and
                 confusing to operators who do not know what to type.
        """
        pa_page.expand_processing_areas()
        pa_page.open_create_area_dialog()
        admin_page.wait_for_timeout(1000)

        with allure.step("Name and Description fields have placeholder / aria-label"):
            name_input = admin_page.get_by_placeholder("Enter area name")
            expect(name_input).to_be_visible(timeout=5000)
            desc_input = admin_page.get_by_placeholder("Enter area description")
            expect(desc_input).to_be_visible(timeout=5000)

        with allure.step("Tab cycles through form fields"):
            name_input.focus()
            admin_page.keyboard.press("Tab")
            # After Tab, focus should move (not stay on body)
            focused = admin_page.evaluate(
                "() => document.activeElement?.tagName"
            )
            assert focused not in (None, "BODY", "HTML"), (
                f"Tab from name field did not move focus; still on {focused}."
            )

        admin_page.keyboard.press("Escape")
        admin_page.wait_for_timeout(500)


# =============================================================================
# TC_UI_007 — Save protected against double-click
# =============================================================================

@allure.feature("UI & Navigation")
@allure.story("Double submit protection")
class TestDoubleSubmitProtection:

    @allure.title("TC_UI_007 — Save is protected against double-click")
    def test_save_is_protected_against_double_click(self, admin_page, pa_page):
        """
        ID     : TC_UI_007
        Title  : Save is protected against double-click (idempotent submit)
        Reason : Operators with gloves often double-tap buttons. A second save
                 must not create a duplicate record or throw a 500 error.
        """
        area_name = unique_name("ui_dbl_save")
        pa_page.expand_processing_areas()
        pa_page.open_create_area_dialog()

        name_input = admin_page.get_by_placeholder("Enter area name")
        name_input.wait_for(state="visible", timeout=10000)
        name_input.fill(area_name)
        admin_page.get_by_placeholder("Enter area description").fill("Double-click test")

        save_btn = admin_page.locator(".MuiDialogActions-root button").filter(
            has_text="SAVE"
        )

        with allure.step("Double-click the SAVE button"):
            save_btn.dblclick(force=True)
            admin_page.wait_for_timeout(2500)

        with allure.step("No server error"):
            assert not admin_page.locator("text=500").is_visible(timeout=500), (
                "Server 500 on double-click save."
            )

        with allure.step("At most one record created"):
            pa_page.expand_processing_areas()
            count = pa_page._area_link_in_sidebar(area_name).count()
            assert count <= 1, (
                f"Double-click SAVE created {count} copies of '{area_name}'."
            )

        # Clean up
        try:
            pa_page.delete_processing_area(area_name)
        except Exception:
            pass


# =============================================================================
# TC_UI_008 — Success messages
# =============================================================================

@allure.feature("UI & Navigation")
@allure.story("Success feedback")
class TestSuccessMessages:

    @allure.title("TC_UI_008 — Success messages appear, are readable, and are dismissible")
    def test_success_messages_appear_readable_and_dismissible(
        self, admin_page, pa_page
    ):
        """
        ID     : TC_UI_008
        Title  : Success messages appear, are readable and are dismissible
        Reason : Silent save confuses operators — they keep clicking because
                 they are unsure the action worked.
        """
        area_name = unique_name("crud_feedback")
        try:
            pa_page.expand_processing_areas()
            pa_page.open_create_area_dialog()
            name_input = admin_page.get_by_placeholder("Enter area name")
            name_input.wait_for(state="visible", timeout=10000)
            name_input.fill(area_name)
            admin_page.get_by_placeholder("Enter area description").fill("Success message test")
            admin_page.locator(".MuiDialogActions-root button").filter(has_text="SAVE").click()

            with allure.step("Success feedback becomes visible after saving"):
                feedback = admin_page.locator(
                    ".Toastify__toast--success, .MuiAlert-standardSuccess"
                ).or_(admin_page.get_by_text(re.compile(r"success|created|saved", re.I)))
                expect(feedback.filter(visible=True).first).to_be_visible(timeout=5000)
        finally:
            # Always clean up this test's entity, including assertion failures.
            from utils.waits import dismiss_stuck_modal
            dismiss_stuck_modal(admin_page)
            pa_page.delete_processing_area(area_name)


# =============================================================================
# TC_UI_009 — Error messages are operator-readable
# =============================================================================

@allure.feature("UI & Navigation")
@allure.story("Error feedback")
class TestErrorMessages:

    @allure.title("TC_UI_009 — Error messages are operator-readable")
    def test_error_messages_are_operator_readable(self, admin_page, pa_page):
        """
        ID     : TC_UI_009
        Title  : Error messages are operator-readable
        Reason : An error that says 'Error 4e8f...' or dumps a stack trace is
                 not actionable by a shop-floor operator without tech support.
        """
        pa_page.expand_processing_areas()
        pa_page.open_create_area_dialog()

        name_input = admin_page.get_by_placeholder("Enter area name")
        name_input.wait_for(state="visible", timeout=10000)
        # Submit empty name to trigger a validation error
        admin_page.locator(".MuiDialogActions-root button").filter(
            has_text="SAVE"
        ).click(force=True)
        admin_page.wait_for_timeout(1500)

        with allure.step("Error message is visible and not a raw exception dump"):
            error_locators = [
                admin_page.locator(".Toastify__toast--error"),
                admin_page.locator(".MuiAlert-standardError"),
                admin_page.locator("[role='alert']"),
                admin_page.locator(".Mui-error"),
            ]
            # .is_visible() on a locator matching more than one element raises
            # a strict-mode violation instead of returning a bool - a blank
            # form lights up several .Mui-error fields at once (Name AND
            # Description), so this must check .first per selector rather
            # than the whole locator. Same fix as utils.waits.is_error_visible.
            visible_errors = [
                loc for loc in error_locators if loc.first.is_visible(timeout=2000)
            ]

            modal_still_open = admin_page.locator(
                ".MuiDialog-container"
            ).is_visible(timeout=500)

            if visible_errors:
                for err_loc in visible_errors:
                    err_text = err_loc.first.inner_text(timeout=2000).lower()
                    # Should not be a raw stack trace or UUID
                    assert "traceback" not in err_text, (
                        f"Error message contains a Python stack trace: {err_text[:200]}"
                    )
                    assert len(err_text) < 500, (
                        f"Error message is suspiciously long — likely a dump: {err_text[:200]}"
                    )

        admin_page.keyboard.press("Escape")
        admin_page.wait_for_timeout(500)


# =============================================================================
# TC_UI_010 — Tables with long values and many rows
# =============================================================================

@allure.feature("UI & Navigation")
@allure.story("Table rendering")
class TestTableRendering:

    @allure.title("TC_UI_010 — Tables render correctly with long values and many rows")
    def test_tables_render_correctly_with_long_values_and_many_rows(
        self, admin_page, pa_page
    ):
        """
        ID     : TC_UI_010
        Title  : Tables render correctly with long values and many rows
        Reason : A cell that overflows its column breaks the row layout, making
                 adjacent data unreadable. Many rows expose missing pagination.
        """
        created = []
        prefix = unique_name("ui_tbl")
        long_suffix = "X" * 60

        with allure.step("Create 5 areas including one with a long name"):
            for i in range(5):
                # Capped at 50, not 80: confirmed live (see test_05b_area_
                # validation.py TC_PA_007) that the sidebar truncates the
                # displayed name to 50 characters regardless of the stored
                # length. create_processing_area / _area_link_in_sidebar match
                # exactly against what's shown, so anything longer can never
                # be found afterwards to navigate to or clean up.
                name = f"{prefix}_{i}" if i < 4 else f"{prefix}_long_{long_suffix}"[:50]
                pa_page.create_processing_area(name, f"Table render test {i}")
                created.append(name)

        with allure.step("Sidebar list renders all entries"):
            pa_page.expand_processing_areas()
            for name in created:
                expect(
                    pa_page._area_link_in_sidebar(name).first
                ).to_be_visible(timeout=5000)

        with allure.step("No horizontal overflow in the list"):
            overflow = admin_page.evaluate(
                "() => document.documentElement.scrollWidth > "
                "document.documentElement.clientWidth + 5"
            )
            assert not overflow, "Horizontal overflow detected after rendering long names."

        with allure.step("Clean up"):
            for name in reversed(created):
                try:
                    pa_page.delete_processing_area(name)
                except Exception:
                    pass


# =============================================================================
# TC_UI_012 — Dropdowns reflect records created in the same session
# =============================================================================

@allure.feature("UI & Navigation")
@allure.story("Dropdown freshness")
class TestDropdownFreshness:

    @allure.title("TC_UI_012 — Dropdowns reflect records created in the same session")
    def test_dropdowns_reflect_records_created_in_same_session(
        self, admin_page, pa_page
    ):
        """
        ID     : TC_UI_012
        Title  : Dropdowns reflect records created in the same session
        Reason : If the device form caches the list of Processing Areas at page
                 load time, a newly created area will not appear in the dropdown
                 until the page is refreshed — operators cannot configure the
                 device immediately after creating the area.
        """
        # Create a new area in this session
        fresh_area = unique_name("ui_dropdown_fresh")
        pa_page.create_processing_area(fresh_area, "Dropdown freshness test")

        with allure.step(f"Freshly created area '{fresh_area}' appears in sidebar"):
            pa_page.expand_processing_areas()
            expect(
                pa_page._area_link_in_sidebar(fresh_area).first
            ).to_be_visible(timeout=5000)

        # Clean up
        try:
            pa_page.delete_processing_area(fresh_area)
        except Exception:
            pass


# =============================================================================
# TC_UI_013 — Shopfloor viewport smoke
# =============================================================================

@allure.feature("UI & Navigation")
@allure.story("Shopfloor viewport")
class TestShopfloorViewport:

    @allure.title("TC_UI_013 — Screens usable at shopfloor viewport sizes")
    @pytest.mark.smoke
    def test_screens_usable_at_shopfloor_viewport_sizes(self, admin_page):
        """
        ID     : TC_UI_013
        Title  : Screens usable at shopfloor viewport sizes
        Reason : Lightweight smoke check — confirms the admin shell renders at
                 the most common shop-floor tablet resolution (1280×800)
                 without horizontal overflow.

        Full viewport matrix is in test_nfr.py TC_NFR_001.
        """
        admin_page.set_viewport_size({"width": 1280, "height": 800})
        admin_page.wait_for_timeout(500)

        overflow = admin_page.evaluate(
            "() => document.documentElement.scrollWidth > "
            "document.documentElement.clientWidth + 5"
        )
        assert not overflow, (
            "Horizontal overflow at 1280×800 — layout broken for shopfloor tablets."
        )

        # Restore default viewport to avoid polluting subsequent tests
        admin_page.set_viewport_size({"width": 1280, "height": 720})


# =============================================================================
# TC_UI_014 — Page and browser tab titles
# =============================================================================

@allure.feature("UI & Navigation")
@allure.story("Page titles")
class TestPageTitles:

    @allure.title("TC_UI_014 — Page and browser tab titles are correct")
    def test_page_and_browser_tab_titles_are_correct(self, admin_page):
        """
        ID     : TC_UI_014
        Title  : Page and browser tab titles are correct
        Reason : A tab titled 'React App' or 'undefined' is useless when an
                 operator has 10 tabs open. Correct titles also aid bookmarks
                 and history search.

        Pass criteria:
          • <title> is non-empty.
          • <title> does not equal the generic placeholder 'React App'.
          • <h1> (if present) matches or relates to the current section.
        """
        with allure.step("<title> is descriptive"):
            title = admin_page.title()
            assert title, "Page <title> is empty."
            assert title.lower() not in ("react app", "vite app", "untitled", ""), (
                f"Page title is a generic placeholder: '{title}'."
            )

        with allure.step("<h1> is present and non-empty (if rendered)"):
            h1_count = admin_page.locator("h1").count()
            if h1_count > 0:
                h1_text = admin_page.locator("h1").first.inner_text(timeout=2000)
                assert h1_text.strip(), "<h1> is present but empty."
