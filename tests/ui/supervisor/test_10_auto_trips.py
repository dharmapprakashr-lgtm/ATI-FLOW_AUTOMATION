"""Supervisor — Auto Trips screen (/auto-trips).

Not in the supplied TC-001..TC-045 list, but a real supervisor screen (one of
the three sidebar items), so it gets smoke coverage here. It is also where
in-transit movement is actually visible for this role (see test_04 TC-005).

Confirmed live 2026-09-07: a paginated table with columns Material Code, MHE,
Production Unit, Pickup Station, Staging Area - Drop Cell, Workflow, Status,
Retries, Created; Date and Status filters; a Refresh button + "Updated <time>".
Rows are live production trips — this file only reads.
"""

import allure
import pytest

from pages.dashboards.supervisor_dashboard_page import SupervisorHomePage

pytestmark = [pytest.mark.supervisor, pytest.mark.dashboards]

_EXPECTED_COLS = [
    "Material Code", "MHE", "Production Unit", "Pickup Station",
    "Staging Area - Drop Cell", "Workflow", "Status", "Retries", "Created",
]


@allure.feature("Dashboards")
@allure.story("Supervisor — Auto Trips")
class TestAutoTrips:

    @allure.title("TC_SUP_TRIPS_001 — Auto Trips table renders with its column contract")
    @pytest.mark.smoke
    def test_auto_trips_table_columns(self, supervisor_page):
        """
        ID     : TC_SUP_TRIPS_001
        Title  : Auto Trips renders the expected columns
        Reason : This is the supervisor's window on AMR movement; a broken
                 header row means they cannot read trip state.
        """
        home = SupervisorHomePage(supervisor_page)
        home.go_to_auto_trips()
        headers = home.trips_column_headers()
        assert headers == _EXPECTED_COLS, f"Auto Trips columns {headers} != {_EXPECTED_COLS}"

    @allure.title("TC_SUP_TRIPS_002 — Auto Trips has Refresh + Status/Date filters")
    def test_auto_trips_controls_present(self, supervisor_page):
        """
        ID     : TC_SUP_TRIPS_002
        Title  : Refresh control and Status / Date filters are present
        Reason : Without filters the supervisor cannot narrow 100+ live trips to
                 the ones that need attention.
        """
        home = SupervisorHomePage(supervisor_page)
        home.go_to_auto_trips()
        assert supervisor_page.get_by_role("button", name="Refresh").is_visible()
        body = supervisor_page.locator("body").inner_text()
        assert "Status" in body and "Date" in body, "Auto Trips filters missing."
