"""Requester device record.

Binds to the consumption machine and the workflow created in
``tests/admin/processing_area``, so it cannot pass on its own against an empty
environment.
"""

import allure
import pytest

from config.data import TestData

pytestmark = [pytest.mark.admin, pytest.mark.smoke]


@allure.feature("Admin Console")
@allure.story("Execution Source Config: requester device")
class TestCreateRequesterDevice:

    @allure.title("Create a requester device bound to the suite workflow and machine")
    def test_create_requester_device(self, exec_config):
        exec_config.click_requester_tab()

        exec_config.delete_device_if_exists(TestData.req_device_name)
        exec_config.add_requester_device(
            TestData.req_device_name,
            TestData.req_device_id,
            TestData.req_device_pass,
            TestData.req_bound_machines,
            TestData.req_bound_workflows,
            TestData.req_staging_areas,
        )
        exec_config.verify_device_created(TestData.req_device_name)
