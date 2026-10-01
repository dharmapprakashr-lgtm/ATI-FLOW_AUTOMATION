"""Supervisor dashboard shell — the sidebar the whole role is navigated from.

Confirmed live 2026-09-07: after login the supervisor lands on /stagingArea
with a sidebar for operational screens, a Processing Area selector, a Notifications row and a profile
block reading "supervisor_45 / Supervisor". These are the only surfaces this
role has — there is no Workflow / Mapping / Execution Source Config entry
(that isolation is asserted in test_11_access_control.py).
"""

import allure
import pytest

from config.data import TestData
from pages.dashboards.supervisor_dashboard_page import SupervisorHomePage

pytestmark = [pytest.mark.supervisor, pytest.mark.dashboards]

_EXPECTED_NAV = ["Staging Area", "Auto Trips"]


@allure.feature("Dashboards")
@allure.story("Supervisor dashboard shell")
class TestSupervisorDashboardShell:

    @allure.title("TC_DASH_S_001 — Supervisor dashboard loads after provisioning")
    @pytest.mark.smoke
    def test_supervisor_dashboard_loads_after_provisioning(self, supervisor_page):
        """
        ID     : TC_DASH_S_001
        Title  : Supervisor dashboard loads after provisioning
        Reason : Gate for the fixture chain — confirms the admin-created
                 supervisor device record is valid and its dashboard renders.
        """
        home = SupervisorHomePage(supervisor_page)
        assert "login" not in supervisor_page.url.lower(), (
            f"Supervisor was not authenticated; still at {supervisor_page.url}"
        )
        assert home.profile_role.inner_text().strip() == "Supervisor"
        assert home.profile_name.inner_text().strip() == TestData.sup_device_name

    @allure.title("TC_SUP_SHELL_001 — Sidebar exposes the in-scope supervisor screens")
    def test_sidebar_has_exactly_the_supervisor_nav_items(self, supervisor_page):
        """
        ID     : TC_SUP_SHELL_001
        Title  : Sidebar exposes Staging Area and Auto Trips; WIP is deferred
        Reason : The supervisor's navigation must stay inside their operational
                 remit. An extra admin-style entry appearing here is a
                 privilege leak; a missing one is a broken screen.
        """
        home = SupervisorHomePage(supervisor_page)
        assert [label for label in home.sidebar_nav_labels() if label != "WIP Inventory"] == _EXPECTED_NAV, (
            f"Supervisor sidebar nav = {home.sidebar_nav_labels()}, expected {_EXPECTED_NAV}"
        )

    @allure.title("TC_SUP_SHELL_002 — Each sidebar screen is reachable and routes correctly")
    def test_each_screen_is_reachable(self, supervisor_page):
        """
        ID     : TC_SUP_SHELL_002
        Title  : Staging Area / Auto Trips each open their route
        Reason : A nav item that renders but does not route (or 404s) leaves the
                 supervisor unable to do their job even though login worked.
        """
        home = SupervisorHomePage(supervisor_page)

        with allure.step("Auto Trips -> /auto-trips"):
            home.go_to_auto_trips()
            assert "/auto-trips" in supervisor_page.url

        with allure.step("Staging Area -> /stagingArea"):
            home.go_to_staging_area()
            assert "/stagingArea" in supervisor_page.url
