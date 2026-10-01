"""Dispatcher device record. Binds to a station and a staging area."""

import allure
import pytest

from config.data import TestData

pytestmark = [pytest.mark.admin, pytest.mark.smoke]


@allure.feature("Admin Console")
@allure.story("Execution Source Config: dispatcher device")
class TestCreateDispatcherDevice:

    @allure.title("Create a dispatcher device bound to a station and staging area")
    def test_create_dispatcher_device(self, exec_config):
        exec_config.click_dispatcher_tab()

        exec_config.delete_device_if_exists(TestData.disp_device_name)
        exec_config.add_dispatcher_device(
            TestData.disp_device_name,
            TestData.disp_device_id,
            TestData.disp_device_pass,
            TestData.disp_bound_stations,
            TestData.disp_staging_areas,
        )
        exec_config.verify_device_created(TestData.disp_device_name)
