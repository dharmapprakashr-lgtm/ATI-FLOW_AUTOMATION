"""Supervisor Auto Trips refresh checks.

WIP refresh coverage is deferred to docs/WIP_INVENTORY_TEST_CASES.md.
"""

import allure
import pytest

from pages.dashboards.supervisor_dashboard_page import SupervisorHomePage

pytestmark = [pytest.mark.supervisor, pytest.mark.dashboards]


@allure.feature("Dashboards")
@allure.story("Supervisor — data freshness")
class TestRealtimeRefresh:


    @allure.title("TC-041 — Auto Trips also uses the manual Refresh model")
    def test_auto_trips_manual_refresh_affordance(self, supervisor_page):
        """
        ID     : TC-041
        Title  : Auto Trips exposes the same manual Refresh + 'Updated' marker
        Reason : A supervisor watching trips needs a visible freshness signal.
        """
        home = SupervisorHomePage(supervisor_page)
        home.go_to_auto_trips()
        assert supervisor_page.get_by_role("button", name="Refresh").is_visible()
        assert supervisor_page.get_by_text("Updated", exact=False).first.is_visible()
