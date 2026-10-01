"""Workflow tab: create all workflows defined in [[workflow]] in test_data.toml.

Each workflow specifies its own pickup_type/drop_type ("mapping" or "static")
so the wizard correctly handles both Mapping-based and Static station modes.
"""

import allure
import pytest

from config.processing_area import workflow_specs
from pages.admin.admin_navigation import AdminDashboardPage

pytestmark = [pytest.mark.admin, pytest.mark.smoke]


@allure.feature("Admin Console")
@allure.story("Processing Area: workflow")
class TestWorkflow:

    @allure.title("Create all workflows with their pickup/drop station types")
    def test_create_workflow(self, admin_page, processing_area, safe_step):
        admin_dashboard = AdminDashboardPage(admin_page)

        safe_step("Open the Workflow tab", processing_area.go_to_workflow)

        for workflow in workflow_specs():
            def create_one(wf=workflow):
                admin_dashboard.delete_device_if_exists(wf.name)
                processing_area.add_workflow(
                    wf.name,
                    pickup_station=wf.pickup_station,
                    drop_station=wf.drop_station,
                    pickup_type=wf.pickup_type,
                    drop_type=wf.drop_type,
                    point_station_mode=wf.point_station_mode,
                    staging_area_mode=wf.staging_area_mode,
                )
            safe_step(f"Create workflow '{workflow.name}'", create_one)

        safe_step.assert_no_failures()
