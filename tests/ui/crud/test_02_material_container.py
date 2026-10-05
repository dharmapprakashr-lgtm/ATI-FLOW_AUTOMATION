"""Material and Container CRUD lifecycle tests.

Uses dedicated throwaway records from [material_crud] and [container_crud]
in test_data.toml and never touches the shared baseline records.

TC_MAT_CRUD  Material create -> verify -> edit -> verify -> delete lifecycle
TC_CON_CRUD  Container create -> verify -> edit -> verify -> delete lifecycle
"""

import re

import allure
import pytest

from config.data import TestData
from pages.admin.admin_navigation import AdminDashboardPage

pytestmark = [pytest.mark.admin, pytest.mark.admin_pa, pytest.mark.crud]


def _submit_dialog(page, *labels):
    dialog = page.locator(".MuiDialog-container")
    pattern = re.compile(rf"^({'|'.join(re.escape(label) for label in labels)})$", re.I)
    named_button = dialog.get_by_role("button", name=pattern)
    if named_button.count():
        named_button.last.click(force=True)
    else:
        dialog.locator(".MuiDialogActions-root button").last.click(force=True)
    page.wait_for_timeout(2_000)


# =============================================================================
# Material CRUD
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Processing Area: material CRUD lifecycle")
class TestMaterialCrud:
    """TC_MAT_CRUD - create -> verify -> edit -> verify -> delete."""

    @allure.title("TC_MAT_CRUD - Material full CRUD lifecycle in one pass")
    def test_material_crud_lifecycle(self, admin_page, processing_area):
        """
        ID     : TC_MAT_CRUD
        Title  : Material create -> search -> edit -> delete lifecycle
        Reason : Validates every write path for materials in one session so a
                 regression in any step is caught without running the full suite.
        """
        dashboard = AdminDashboardPage(admin_page)
        crud_name = TestData.crud_material_name
        edited_name = TestData.crud_material_name_edited
        prefix = TestData.crud_material_prefix

        processing_area.go_to_materials()

        with allure.step(f"Create material '{crud_name}'"):
            dashboard.delete_device_if_exists(edited_name)
            dashboard.delete_device_if_exists(crud_name)
            dashboard.add_material(
                crud_name,
                TestData.crud_material_prod_unit,
                TestData.crud_material_pre_proc,
                TestData.crud_material_max_qty,
                prefix,
            )

        with allure.step(f"Verify '{crud_name}' appears in the table"):
            dashboard.verify_device_created(crud_name)

        with allure.step(f"Rename '{crud_name}' to '{edited_name}' via the edit icon"):
            search_input = dashboard._search_for(crud_name)
            row = dashboard._row_by_exact_name(crud_name)
            assert row.count() > 0, f"Material '{crud_name}' was not found for edit."
            row.first.locator("button").first.click(force=True)
            admin_page.wait_for_timeout(1_000)
            admin_page.locator("#mat-type-name").fill(edited_name)
            _submit_dialog(admin_page, "Add Material", "Update Material", "Save", "SAVE")
            dashboard._clear_search(search_input)

        with allure.step(f"Verify edited name '{edited_name}' is in the table"):
            dashboard.verify_device_created(edited_name)

        with allure.step(f"Delete '{edited_name}'"):
            deleted = dashboard.delete_device_if_exists(edited_name)
            assert deleted, f"Expected to delete '{edited_name}' but it was not found."

        with allure.step(f"Confirm '{edited_name}' is gone from the table"):
            search_input = dashboard._search_for(edited_name)
            count = dashboard._row_by_exact_name(edited_name).count()
            dashboard._clear_search(search_input)
            assert count == 0, f"Material '{edited_name}' still visible after deletion."


# =============================================================================
# Container CRUD
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Processing Area: container CRUD lifecycle")
class TestContainerCrud:
    """TC_CON_CRUD - create -> verify -> edit -> verify -> delete."""

    @allure.title("TC_CON_CRUD - Container full CRUD lifecycle in one pass")
    def test_container_crud_lifecycle(self, admin_page, processing_area):
        """
        ID     : TC_CON_CRUD
        Title  : Container create -> search -> edit -> delete lifecycle
        Reason : Validates every write path for containers in one session so a
                 regression in any step is caught without running the full suite.
        """
        dashboard = AdminDashboardPage(admin_page)
        crud_sub_type = TestData.crud_container_sub_type
        edited_sub_type = TestData.crud_container_sub_type_ed

        processing_area.go_to_containers()

        with allure.step(f"Create container sub-type '{crud_sub_type}'"):
            dashboard.delete_device_if_exists(edited_sub_type)
            dashboard.delete_device_if_exists(crud_sub_type)
            dashboard.add_container(
                TestData.crud_container_type,
                crud_sub_type,
                TestData.crud_container_length,
                TestData.crud_container_width,
                TestData.crud_container_height,
                TestData.crud_container_hitch_length,
                TestData.crud_container_qty,
            )

        with allure.step(f"Verify '{crud_sub_type}' appears in the Containers table"):
            dashboard.verify_device_created(crud_sub_type)

        with allure.step(f"Edit sub-type: '{crud_sub_type}' to '{edited_sub_type}'"):
            search_input = dashboard._search_for(crud_sub_type)
            row = dashboard._row_by_exact_name(crud_sub_type)
            assert row.count() > 0, f"Container '{crud_sub_type}' was not found for edit."
            row.first.locator("button").first.click(force=True)
            admin_page.wait_for_timeout(1_000)
            admin_page.locator("#ctr-sub-type").fill(edited_sub_type)
            _submit_dialog(admin_page, "SAVE", "Save", "Update Container", "Add Container")
            dashboard._clear_search(search_input)

        with allure.step(f"Verify edited sub-type '{edited_sub_type}' is in the table"):
            dashboard.verify_device_created(edited_sub_type)

        with allure.step(f"Delete '{edited_sub_type}'"):
            deleted = dashboard.delete_device_if_exists(edited_sub_type)
            assert deleted, f"Expected to delete container '{edited_sub_type}' but it was not found."

        with allure.step(f"Confirm '{edited_sub_type}' is gone from the table"):
            search_input = dashboard._search_for(edited_sub_type)
            count = dashboard._row_by_exact_name(edited_sub_type).count()
            dashboard._clear_search(search_input)
            assert count == 0, f"Container '{edited_sub_type}' still visible after deletion."
