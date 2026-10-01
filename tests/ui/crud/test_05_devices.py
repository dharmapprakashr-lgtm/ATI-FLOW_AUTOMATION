"""Device edit and delete lifecycle for all three roles.

Each test creates its own throwaway device, edits it, then deletes it. The
original version edited the shared devices' passwords to "new_password_123",
which is now unsafe: the root ``conftest.py`` logs the role suites in with
``TestData.<role>_device_pass``, so mutating the shared record would break every
role login that ran afterwards.
"""

import allure
import pytest

from config.data import TestData
from utils.data_factory import unique_name

pytestmark = [pytest.mark.admin, pytest.mark.crud]


@allure.feature("Admin Console")
@allure.story("Execution Source Config: device lifecycle")
class TestDeviceLifecycle:

    @allure.title("Create, edit and delete a throwaway requester device")
    def test_requester_device_lifecycle(self, exec_config):
        name = unique_name(TestData.crud_requester_name_prefix)
        exec_config.click_requester_tab()

        with allure.step(f"Create '{name}'"):
            exec_config.add_requester_device(
                name,
                unique_name(TestData.crud_requester_id_prefix),
                TestData.crud_device_password,
                TestData.req_bound_machines,
                TestData.req_bound_workflows,
                TestData.req_staging_areas,
            )
            exec_config.verify_device_created(name)

        with allure.step("Edit its password"):
            exec_config.update_requester_device(
                name,
                new_password=TestData.crud_device_updated_password,
                new_machines=None,
                new_workflows=None,
                new_staging=None,
            )
            exec_config.verify_device_created(name)

        with allure.step(f"Delete '{name}'"):
            assert exec_config.delete_device_if_exists(name) is True

    @allure.title("Create, edit and delete a throwaway dispatcher device")
    def test_dispatcher_device_lifecycle(self, exec_config):
        name = unique_name(TestData.crud_dispatcher_name_prefix)
        exec_config.click_dispatcher_tab()

        with allure.step(f"Create '{name}'"):
            exec_config.add_dispatcher_device(
                name,
                unique_name(TestData.crud_dispatcher_id_prefix),
                TestData.crud_device_password,
                TestData.disp_bound_stations,
                TestData.disp_staging_areas,
            )
            exec_config.verify_device_created(name)

        with allure.step("Edit its password"):
            exec_config.update_dispatcher_device(
                name,
                new_password=TestData.crud_device_updated_password,
                new_stations=None,
                new_staging=None,
            )
            exec_config.verify_device_created(name)

        with allure.step(f"Delete '{name}'"):
            assert exec_config.delete_device_if_exists(name) is True

    @allure.title("Create, edit and delete a throwaway supervisor device")
    def test_supervisor_device_lifecycle(self, exec_config):
        name = unique_name(TestData.crud_supervisor_name_prefix)
        exec_config.click_supervisor_tab()

        with allure.step(f"Create '{name}'"):
            exec_config.add_supervisor_device(
                name,
                unique_name(TestData.crud_supervisor_id_prefix),
                TestData.crud_device_password,
                TestData.sup_staging_areas,
                TestData.sup_processing_areas,
            )
            exec_config.verify_device_created(name)

        with allure.step("Edit its password"):
            exec_config.update_supervisor_device(
                name,
                new_password=TestData.crud_device_updated_password,
                new_staging=None,
                new_processing=None,
            )
            exec_config.verify_device_created(name)

        with allure.step(f"Delete '{name}'"):
            assert exec_config.delete_device_if_exists(name) is True
