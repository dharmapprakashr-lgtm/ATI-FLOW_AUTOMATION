"""Material and Container CRUD lifecycle tests — Part 3b (CRUD).

Uses dedicated throwaway records from [material_crud] and [container_crud]
in test_data.toml — never touches the shared baseline records.

TC_MAT_CRUD  Material create → verify → delete lifecycle
TC_CON_CRUD  Container create → verify → delete lifecycle
"""

import allure
import pytest
from playwright.sync_api import expect

from config.data import TestData
from pages.admin.admin_navigation import AdminDashboardPage

pytestmark = [pytest.mark.admin, pytest.mark.admin_pa, pytest.mark.crud]


# =============================================================================
# Material CRUD
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Processing Area: material CRUD lifecycle")
class TestMaterialCrud:
    """TC_MAT_CRUD"""

    @allure.title("TC_MAT_CRUD — Material create and delete lifecycle")
    def test_material_create_and_delete(self, admin_page, processing_area, safe_step):
        """
        ID     : TC_MAT_CRUD
        Title  : Material create → verify → delete lifecycle
        Reason : Confirms the full lifecycle works end-to-end using a dedicated
                 throwaway record from [material_crud] in test_data.toml.
                 The shared baseline material (testing_material_45) is never touched.
        """
        dashboard = AdminDashboardPage(admin_page)
        name        = TestData.crud_material_name
        prod_unit   = TestData.crud_material_prod_unit
        pre_proc    = TestData.crud_material_pre_proc
        max_qty     = TestData.crud_material_max_qty
        prefix      = TestData.crud_material_prefix

        safe_step("Open Materials tab", processing_area.go_to_materials)

        def create():
            dashboard.delete_device_if_exists(name)
            dashboard.add_material(name, prod_unit, pre_proc, max_qty, prefix)
            expect(
                admin_page.locator("tr").filter(has_text=name).first
            ).to_be_visible(timeout=5000)
        safe_step(f"Create material '{name}'", create)

        def verify_exists():
            expect(
                admin_page.locator("tr").filter(has_text=name).first
            ).to_be_visible(timeout=5000)
        safe_step(f"Verify material '{name}' is present in the table", verify_exists)

        def delete_it():
            result = dashboard.delete_device_if_exists(name)
            assert result, f"Expected to delete '{name}' but it was not found."
            expect(
                admin_page.locator("tr").filter(has_text=name).first
            ).not_to_be_visible(timeout=5000)
        safe_step(f"Delete material '{name}'", delete_it)

        safe_step.assert_no_failures()


# =============================================================================
# Container CRUD
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Processing Area: container CRUD lifecycle")
class TestContainerCrud:
    """TC_CON_CRUD"""

    @allure.title("TC_CON_CRUD — Container create and delete lifecycle")
    def test_container_create_and_delete(self, admin_page, processing_area, safe_step):
        """
        ID     : TC_CON_CRUD
        Title  : Container create → verify → delete lifecycle
        Reason : Confirms the full lifecycle works end-to-end using a dedicated
                 throwaway record from [container_crud] in test_data.toml.
                 The shared baseline container (mini trolly) is never touched.
        """
        dashboard   = AdminDashboardPage(admin_page)
        ctr_type    = TestData.crud_container_type
        sub_type    = TestData.crud_container_sub_type
        length      = TestData.crud_container_length
        width       = TestData.crud_container_width
        height      = TestData.crud_container_height
        hitch       = TestData.crud_container_hitch_length
        qty         = TestData.crud_container_qty

        safe_step("Open Containers tab", processing_area.go_to_containers)

        def create():
            dashboard.delete_device_if_exists(sub_type)
            dashboard.add_container(ctr_type, sub_type, length, width, height, hitch, qty)
            expect(
                admin_page.locator("tr").filter(has_text=sub_type).first
            ).to_be_visible(timeout=5000)
        safe_step(f"Create container '{sub_type}'", create)

        def verify_exists():
            expect(
                admin_page.locator("tr").filter(has_text=sub_type).first
            ).to_be_visible(timeout=5000)
        safe_step(f"Verify container '{sub_type}' is present in the table", verify_exists)

        def delete_it():
            result = dashboard.delete_device_if_exists(sub_type)
            assert result, f"Expected to delete '{sub_type}' but it was not found."
            expect(
                admin_page.locator("tr").filter(has_text=sub_type).first
            ).not_to_be_visible(timeout=5000)
        safe_step(f"Delete container '{sub_type}'", delete_it)

        safe_step.assert_no_failures()
