"""Machine Name CRUD lifecycle test — Part 3c (CRUD).

Uses a dedicated throwaway record from [machine_name_crud] in test_data.toml —
never touches the shared baseline machines (production_machine_45 / consuption_machine_45).

TC_MCH_CRUD  Machine create → verify → delete lifecycle
"""

import allure
import pytest
from playwright.sync_api import expect

from config.processing_area import machine_crud_spec
from pages.admin.admin_navigation import AdminDashboardPage

pytestmark = [pytest.mark.admin, pytest.mark.admin_pa, pytest.mark.crud]


@allure.feature("Admin Console")
@allure.story("Processing Area: machine name CRUD lifecycle")
class TestMachineNameCrud:
    """TC_MCH_CRUD"""

    @allure.title("TC_MCH_CRUD — Machine create and delete lifecycle")
    def test_machine_create_and_delete(self, admin_page, processing_area, safe_step):
        """
        ID     : TC_MCH_CRUD
        Title  : Machine create → verify → delete lifecycle
        Reason : Confirms the full lifecycle works end-to-end using a dedicated
                 throwaway record from [machine_name_crud] in test_data.toml.
                 The shared baseline machines are never touched.
        """
        dashboard = AdminDashboardPage(admin_page)
        machine = machine_crud_spec()

        safe_step("Open Machine Names tab", processing_area.go_to_machine_names)

        def create():
            dashboard.delete_device_if_exists(machine.name)
            processing_area.add_machine_name(machine.name, machine.production_type)
        safe_step(f"Create machine '{machine.name}'", create)

        def verify_exists():
            expect(
                admin_page.locator("tr").filter(has_text=machine.name).first
            ).to_be_visible(timeout=5000)
        safe_step(f"Verify machine '{machine.name}' is present in the table", verify_exists)

        def delete_it():
            result = dashboard.delete_device_if_exists(machine.name)
            assert result, f"Expected to delete '{machine.name}' but it was not found."
            expect(
                admin_page.locator("tr").filter(has_text=machine.name).first
            ).not_to_be_visible(timeout=5000)
        safe_step(f"Delete machine '{machine.name}'", delete_it)

        safe_step.assert_no_failures()
