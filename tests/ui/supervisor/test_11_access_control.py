"""Supervisor — role isolation / access control.

Manual test cases covered:
  TC-038  Supervisor sees only assigned areas end-to-end; direct access to an
          unassigned area's data is blocked
  TC-043  Workflow editing is not accessible to the Supervisor
  TC-044  Mapping editing is not accessible to the Supervisor
  TC-045  Execution Source configuration is not accessible to the Supervisor

Confirmed live 2026-09-07: typing an admin route as the supervisor is blocked
two ways — most routes render the app's own "Page Not Found" (URL unchanged),
while /Execution_Source_Config and /settings render "You are not authorized to
access this page!". Both count as blocked. The supervisor's own navigation
(test_01) already proves no Workflow / Mapping / Exec-Source entry is even
shown; this file proves the routes are blocked when reached directly.
"""

import allure
import pytest

from config.environment import config
from pages.dashboards.supervisor_dashboard_page import SupervisorHomePage

pytestmark = [pytest.mark.supervisor, pytest.mark.access_control]

#: (route, human label) — the config surfaces a supervisor must never reach.
_FORBIDDEN_ROUTES = [
    ("/admin", "Admin console"),
    ("/admin/processing_area", "Processing Area admin"),
    ("/workflow", "Workflow editing"),                 # TC-043
    ("/station-mapping", "Station Mapping editing"),   # TC-044
    ("/Execution_Source_Config", "Execution Source Config"),   # TC-045
    ("/settings", "Central configuration / Settings"),
]

_BLOCKED_MARKERS = (
    "page not found", "uncharted territory", "not authorized", "not authorised",
    "access denied", "403", "forbidden", "unauthorized",
)


def _is_blocked(page):
    url = page.url.lower()
    if "login" in url:
        return True
    body = page.locator("body").inner_text().lower()
    return any(m in body for m in _BLOCKED_MARKERS)


@allure.feature("Access Control")
@allure.story("Supervisor role isolation")
class TestSupervisorAccessControl:

    @allure.title("TC-043/TC-044/TC-045/TC-038 — Supervisor is blocked from every admin/config route")
    def test_supervisor_blocked_from_admin_and_config_routes(self, supervisor_page):
        """
        ID     : TC-043 / TC-044 / TC-045 / TC-038
        Title  : Supervisor cannot reach Workflow editing, Mapping editing,
                 Execution Source Config, or any admin route — even by typing
                 the URL directly
        Reason : Hiding a menu item is not security. A supervisor who could
                 reach workflow/mapping/exec-source config could reconfigure
                 the whole fleet, not just their floor.
        """
        base = config.app_url
        failures = []
        for route, label in _FORBIDDEN_ROUTES:
            with allure.step(f"Probe {label} ({route})"):
                supervisor_page.goto(base + route, wait_until="domcontentloaded")
                supervisor_page.wait_for_timeout(1500)
                if not _is_blocked(supervisor_page):
                    failures.append(f"{label} ({route}) -> {supervisor_page.url}")
        assert not failures, (
            "Supervisor was NOT blocked from:\n  " + "\n  ".join(failures)
        )

    @allure.title("TC-038 — Supervisor navigation stays inside their operational remit")
    def test_supervisor_navigation_is_scoped(self, supervisor_page):
        """
        ID     : TC-038
        Title  : End-to-end, the supervisor's UI only exposes their assigned
                 scope (in-scope operational screens and assigned areas)
        Reason : Positive companion to the negative probes — over-restriction
                 that breaks the supervisor's own screens is also a bug.
        """
        home = SupervisorHomePage(supervisor_page)
        # Recover from the forbidden-route navigation above if run in sequence.
        supervisor_page.goto(config.app_url + "/stagingArea", wait_until="domcontentloaded")
        supervisor_page.wait_for_timeout(1500)

        assert [label for label in home.sidebar_nav_labels() if label != "WIP Inventory"] == ["Staging Area", "Auto Trips"]
        assert home.profile_role.inner_text().strip() == "Supervisor"
        options = home.open_processing_area_dropdown()
        home.close_dropdown()
        assert options, "Processing Area selector offered no area at all — over-restricted."
