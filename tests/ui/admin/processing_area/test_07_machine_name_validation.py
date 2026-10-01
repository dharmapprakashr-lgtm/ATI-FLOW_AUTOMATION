"""Machine Name validation tests — Part 7.

Complements test_06_machine_name.py with:

TC_MCH_001v  Baseline machines exist in the table (search by name from TOML)
TC_MCH_002   Duplicate rejection within an isolated processing area

Cross-layer CRUD and isolation checks live in tests/ui/crud/test_machine_api_ui.py.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from config.processing_area import machine_specs

pytestmark = [pytest.mark.admin_pa]


# =============================================================================
# Existence checks (search the records test_06 created)
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Processing Area: machine existence")
class TestMachineNamesExist:
    """TC_MCH_001v"""

    @allure.title("TC_MCH_001v — Baseline machines exist after creation")
    def test_baseline_machines_exist(self, admin_page, processing_area):
        """
        ID     : TC_MCH_001v
        Title  : Baseline production and consumption machines are present
        Reason : Confirms test_02 actually persisted both records — station
                 mapping and the workflow wizard both depend on them existing.
        """
        processing_area.go_to_machine_names()

        for machine in machine_specs():
            with allure.step(f"Search for machine '{machine.name}' in the table"):
                expect(
                    admin_page.locator("tr").filter(has_text=machine.name).first
                ).to_be_visible(timeout=8000)


@allure.feature("Admin Console")
@allure.story("Processing Area: machine name validation")
class TestMachineNameValidation:
    """TC_MCH_002"""

    @allure.title("TC_MCH_002 — Duplicate name is rejected within one area")
    def test_machine_name_uniqueness_scope(self, admin_page, machine_ui_area, machine_api):
        area_page, area = machine_ui_area
        machine = machine_api.create(machine_api.payload(area['id']))
        admin_page.reload(wait_until="domcontentloaded")
        area_page.go_to_machine_names()
        expect(admin_page.get_by_role("cell", name=machine['machine_name'], exact=True)).to_be_visible()
        area_page.fill_machine_form(machine['machine_name'], "Production Type")
        name_input = admin_page.get_by_placeholder("e.g. Machine A")
        expect(name_input).to_have_value(machine['machine_name'])
        expect(admin_page.locator(".MuiDialog-container .MuiSelect-select").first).to_have_text("Production Type")
        admin_page.locator(".MuiDialogActions-root button").last.click()
        # Verify visible rejection and unchanged data. API tests separately reject server 500s.
        error = admin_page.locator(
            ".MuiFormHelperText-root, .Toastify__toast--error, .MuiAlert-message, [role='alert']"
        ).filter(has_text=re.compile(r"already|duplicate|exist|unique|failed|error", re.IGNORECASE)).first
        try:
            expect(error).to_be_visible(timeout=10000)
        except AssertionError as exc:
            raise AssertionError(
                "Duplicate rejection feedback missing. Dialog: "
                + admin_page.locator(".MuiDialog-container").inner_text()
            ) from exc
        expect(admin_page.locator(".MuiDialog-container")).to_be_visible()
        assert machine_api.by_area(area['id']) == [machine], "Duplicate changed stored records"
