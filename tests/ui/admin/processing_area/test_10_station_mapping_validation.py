"""Station Mapping validation tests — Part 10.

Complements test_09_station_mapping.py (happy-path create) with:

TC_STM_001v  Baseline mappings exist in the table (search by name from TOML)
TC_STM_002   Mapping referencing a deleted station or machine
TC_STM_003   Duplicate mapping is rejected
TC_STM_004   Incomplete mapping cannot be saved

CRUD lifecycle (create → delete) lives in test_11_station_mapping_crud.py.
"""

import allure
import pytest

from config.processing_area import station_names
from utils.data_factory import unique_name
from utils.waits import is_error_visible

pytestmark = [pytest.mark.admin_pa]


# =============================================================================
# Existence checks (search the records test_09 created)
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Processing Area: station mapping existence")
class TestStationMappingsExist:
    """TC_STM_001v"""

    @allure.title("TC_STM_001v — Baseline station mappings exist after creation")
    def test_baseline_mappings_exist(self, admin_page, processing_area):
        """
        ID     : TC_STM_001v
        Title  : Baseline pickup and drop station mappings are present
        Reason : Confirms test_03 actually persisted both records — the
                 workflow wizard's Mapping ID dropdown depends on them existing.

        Checks the exact Material Mapping column header, not a `<tr>`
        substring match - a real Station ID value (e.g. "pick2_gg") can
        contain a mapping name as a substring and produce a false positive
        (see the note on ProcessingAreaPage's Station Mapping CRUD section).
        """
        pickup_name, drop_name = station_names()
        processing_area.go_to_station_mapping()

        for name in (pickup_name, drop_name):
            with allure.step(f"Search for station mapping '{name}' in the table"):
                processing_area.verify_station_mapping_exists(name, timeout=8000)


@allure.feature("Admin Console")
@allure.story("Processing Area: station mapping validation")
class TestStationMappingValidation:
    """TC_STM_002, TC_STM_003, TC_STM_004"""

    @allure.title("TC_STM_002 — Mapping referencing a deleted station or machine")
    @pytest.mark.skip(
        reason='Not implemented: needs an isolated, explicitly linked machine/mapping fixture and a defined deletion contract. FM stations cannot be deleted through AtiFlow admin. Historical product behavior has not been reverified.',
    )
    def test_mapping_referencing_deleted_station_or_machine(self, processing_area):
        """
        ID     : TC_STM_002
        Title  : Mapping referencing a deleted station or machine
        Reason : Dangling reference causes task assignment to fail at runtime
                 rather than at config time — config time is far cheaper to fix.
        """

    @allure.title("TC_STM_003 — Duplicate station mapping is rejected")
    def test_duplicate_mapping_is_rejected(self, admin_page, processing_area, safe_step):
        """
        ID     : TC_STM_003
        Title  : Duplicate mapping is rejected
        Reason : Two mappings on the same Station ID make task routing
                 non-deterministic — the AMR could go to either station.
        """
        from config.data import TestData

        pickup_name, _ = station_names()

        safe_step("Open Station Mapping tab", processing_area.go_to_station_mapping)

        def ensure_baseline_exists():
            if processing_area._mapping_column_header(pickup_name).count() == 0:
                processing_area.add_station_mapping(
                    pickup_name,
                    station_id=TestData.station_id,
                    station_index=0,
                )
        safe_step(f"Ensure baseline mapping '{pickup_name}' exists", ensure_baseline_exists)

        def attempt_duplicate():
            # Try to create another mapping with the exact same name
            admin_page.locator("button").filter(has_text="Add").first.click(force=True)
            admin_page.wait_for_timeout(1000)

            name_input = admin_page.locator(
                ".MuiDialog-container input[role='combobox']"
            ).first
            name_input.click(force=True)
            name_input.fill(pickup_name)
            admin_page.wait_for_timeout(500)

            # Click the Add Row button to expose the table row
            add_row = admin_page.locator("button").filter(has_text="Add Row")
            if add_row.is_visible(timeout=2000):
                add_row.click(force=True)
                admin_page.wait_for_timeout(1000)

            # Try to save
            admin_page.locator(".MuiDialogActions-root button").last.click(force=True)
            admin_page.wait_for_timeout(1500)

            modal_open = admin_page.locator(
                ".MuiDialog-container"
            ).is_visible(timeout=1000)
            error_shown = is_error_visible(admin_page)

            if modal_open:
                admin_page.keyboard.press("Escape")
                admin_page.wait_for_timeout(500)

            assert modal_open or error_shown, (
                f"Duplicate mapping '{pickup_name}' was accepted — no error "
                "shown and modal closed as if create succeeded."
            )

        safe_step(f"Attempt duplicate mapping '{pickup_name}'", attempt_duplicate)
        safe_step.assert_no_failures()

    @allure.title("TC_STM_004 — Incomplete station mapping cannot be saved")
    def test_incomplete_mapping_cannot_be_saved(self, admin_page, processing_area):
        """
        ID     : TC_STM_004
        Title  : Incomplete mapping cannot be saved
        Reason : A half-filled mapping looks valid in the config UI but fails
                 silently with a null-pointer at task execution time.
        """
        processing_area.go_to_station_mapping()

        with allure.step("Open Add dialog with no name filled"):
            admin_page.locator("button").filter(has_text="Add").first.click(force=True)
            admin_page.wait_for_timeout(1000)

            # Attempt to save immediately without filling any field
            admin_page.locator(".MuiDialogActions-root button").last.click(force=True)
            admin_page.wait_for_timeout(1000)

            modal_open = admin_page.locator(
                ".MuiDialog-container"
            ).is_visible(timeout=1000)
            error_shown = is_error_visible(admin_page)

            # Must not silently save an empty mapping
            assert modal_open or error_shown, (
                "Empty station mapping was accepted — form submitted without "
                "any validation."
            )

            if modal_open:
                admin_page.keyboard.press("Escape")
                admin_page.wait_for_timeout(500)

        with allure.step("Open Add dialog with name but no row (no Material Type / Station ID)"):
            stub_name = unique_name("sm_incomplete")
            admin_page.locator("button").filter(has_text="Add").first.click(force=True)
            admin_page.wait_for_timeout(1000)

            name_input = admin_page.locator(
                ".MuiDialog-container input[role='combobox']"
            ).first
            name_input.click(force=True)
            name_input.fill(stub_name)
            admin_page.wait_for_timeout(500)
            # Deliberately do NOT click Add Row

            admin_page.locator(".MuiDialogActions-root button").last.click(force=True)
            admin_page.wait_for_timeout(1000)

            modal_open = admin_page.locator(
                ".MuiDialog-container"
            ).is_visible(timeout=1000)
            error_shown = is_error_visible(admin_page)

            assert modal_open or error_shown, (
                "Mapping with name but no row data was accepted — partial "
                "mapping should be rejected."
            )

            if modal_open:
                admin_page.keyboard.press("Escape")
                admin_page.wait_for_timeout(500)
