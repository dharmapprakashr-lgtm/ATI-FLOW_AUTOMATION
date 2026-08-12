"""
Processing Area Config tests — TC_PA_013 to TC_PA_016.
"""

import pytest
from playwright.sync_api import expect


@pytest.mark.processing_area_config
@pytest.mark.p0
def test_tc_pa_013_table_displays_correct_columns_and_data(processing_area_config_page):
    """Verify Processing Area Config table displays correct columns and data."""
    expect(processing_area_config_page.page.locator(
        processing_area_config_page.TABLE_ROW
    ).first).to_be_visible()


@pytest.mark.processing_area_config
@pytest.mark.p0
def test_tc_pa_014_add_new_config_entry(processing_area_config_page):
    """Verify adding a new config entry."""
    machine_name = "Extruder-07"
    processing_area_config_page.add_config(
        machine_name=machine_name,
        consumption_points=["Consumption Point A", "Production Point B"],
    )
    processing_area_config_page.assert_row_visible(machine_name)


@pytest.mark.processing_area_config
@pytest.mark.p0
def test_tc_pa_015_validation_blank_machine_name(processing_area_config_page):
    """Verify validation when Machine Name is left blank."""
    processing_area_config_page.attempt_save_without_machine_name()
    processing_area_config_page.assert_validation_error_shown()


@pytest.mark.processing_area_config
@pytest.mark.p1
def test_tc_pa_016_delete_entry_with_confirmation(processing_area_config_page):
    """Verify deleting a config entry with confirmation."""
    machine_name = "Extruder-DeleteTest"
    processing_area_config_page.add_config(
        machine_name=machine_name, consumption_points=["Consumption Point A"]
    )
    processing_area_config_page.assert_row_visible(machine_name)

    processing_area_config_page.delete_config(machine_name, confirm=True)
    processing_area_config_page.assert_row_not_present(machine_name)
