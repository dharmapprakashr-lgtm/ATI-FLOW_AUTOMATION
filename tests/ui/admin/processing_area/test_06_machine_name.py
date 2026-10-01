"""Machine Names tab: one production machine and one consumption machine.

Both are required downstream. Station mapping picks a machine for its Station ID
column, and the workflow wizard's consumption-unit dropdown is populated from
the consumption machine.
"""

import allure
import pytest

from config.processing_area import machine_specs
from pages.admin.admin_navigation import AdminDashboardPage

pytestmark = [pytest.mark.admin, pytest.mark.smoke]


@allure.feature("Admin Console")
@allure.story("Processing Area: machine names")
class TestMachineNames:

    @allure.title("Create the production and consumption machines")
    def test_create_machines(self, admin_page, processing_area, safe_step):
        admin_dashboard = AdminDashboardPage(admin_page)

        safe_step("Open the Machine Names tab", processing_area.go_to_machine_names)

        for machine in machine_specs():
            def create(m=machine):
                admin_dashboard.delete_device_if_exists(m.name)
                processing_area.add_machine_name(m.name, m.production_type)
            safe_step(f"Create machine '{machine.name}' ({machine.production_type})", create)

        safe_step.assert_no_failures()
