"""MES tab.

No MES record is created: unlike the three device roles, MES authenticates with
a real user account (MES_USERNAME / MES_PASSWORD) rather than a record managed
here. This module covers what the tab itself exposes.
"""

import allure
import pytest
from playwright.sync_api import expect

from config.data import TestData

pytestmark = [pytest.mark.admin]


@allure.feature("Admin Console")
@allure.story("Execution Source Config: MES")
class TestMesConfig:

    @allure.title("All four Execution Source Config tabs render with the expected labels")
    def test_all_tabs_present(self, exec_config):
        # exec_config already asserts visibility; this pins the labels against
        # the list in test_data.toml so a renamed tab is caught here.
        for label in TestData.exec_config_tabs:
            expect(exec_config.page.get_by_text(label, exact=True).first).to_be_visible(timeout=5000)

    @allure.title("MES tab activates when selected")
    def test_mes_tab_activates(self, exec_config):
        exec_config.click_mes_tab()
        expect(exec_config.mes_tab).to_have_attribute("aria-selected", "true", timeout=5000)
