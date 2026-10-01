"""Processing Area edit and delete lifecycle.

Operates on a throwaway area with a generated name, never on the suite's
baseline area. The original version of this test edited and deleted
``TestData.processing_area_name`` directly, which only worked because the
destructive suite happened to run last. Now that role suites and e2e bind to
that area, a shared-entity delete here would break them - and would do it
order-dependently, which is the worst kind of flake to diagnose.
"""

import allure
import pytest
from playwright.sync_api import expect

from config.data import TestData
from utils.data_factory import unique_name

pytestmark = [pytest.mark.admin, pytest.mark.crud]


@allure.feature("Admin Console")
@allure.story("Processing Area: edit and delete lifecycle")
class TestProcessingAreaLifecycle:

    @allure.title("Create, rename and delete a throwaway Processing Area")
    def test_area_edit_and_delete(self, admin_page, pa_page):
        original_name = unique_name(TestData.crud_area_name_prefix)
        renamed = unique_name(TestData.crud_area_renamed_prefix)

        with allure.step(f"Create '{original_name}'"):
            pa_page.create_processing_area(original_name, TestData.crud_area_description)
            expect(admin_page.get_by_text(original_name, exact=True).first).to_be_visible(timeout=10000)

        with allure.step(f"Rename to '{renamed}'"):
            pa_page.edit_processing_area(original_name, renamed, TestData.crud_area_updated_description)
            expect(admin_page.get_by_text(renamed, exact=True).first).to_be_visible(timeout=10000)

        with allure.step(f"Delete '{renamed}'"):
            # delete_processing_area asserts the sidebar entry disappears.
            assert pa_page.delete_processing_area(renamed) is True, (
                f"'{renamed}' was not present to delete"
            )

    @allure.title("Deleting an absent Processing Area is a no-op")
    def test_delete_absent_area_is_noop(self, pa_page):
        assert pa_page.delete_processing_area(unique_name(TestData.crud_area_absent_prefix)) is False
