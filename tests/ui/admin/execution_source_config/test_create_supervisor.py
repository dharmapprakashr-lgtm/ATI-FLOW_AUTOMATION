"""Supervisor device record. Binds to the suite's Processing Area."""

import allure
import pytest

from config.data import TestData

pytestmark = [pytest.mark.admin, pytest.mark.smoke]


@allure.feature("Admin Console")
@allure.story("Execution Source Config: supervisor device")
class TestCreateSupervisorDevice:

    @allure.title("Create a supervisor device bound to the suite Processing Area")
    def test_create_supervisor_device(self, exec_config):
        exec_config.click_supervisor_tab()

        exec_config.delete_device_if_exists(TestData.sup_device_name)
        exec_config.add_supervisor_device(
            TestData.sup_device_name,
            TestData.sup_device_id,
            TestData.sup_device_pass,
            TestData.sup_staging_areas,
            TestData.sup_processing_areas,
        )
        exec_config.verify_device_created(TestData.sup_device_name)
