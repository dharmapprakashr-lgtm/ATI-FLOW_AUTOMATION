"""Dispatcher > Requests screen - initial load.

Verified live 2026-08-28: on login the dispatcher device lands on
``/approval`` scoped to the first of its bound stations
(config/test_data.toml [dispatcher_requests] default_station). The breadcrumb
reads "<station> > Requests", the PENDING tab is active, and the table header
row (ID No., Request Details, Request Time, Status, Decision) is visible.
"""

import allure
import pytest

from config.data import TestData
from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]

EXPECTED_HEADERS = ["ID No.", "Request Details", "Request Time", "Status", "Decision"]


@allure.title("Dispatcher lands on the Requests screen scoped to its default bound station")
def test_dashboard_loads_with_bound_station(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)

    with allure.step("Requests screen is the landing page"):
        assert "/approval" in dispatcher_page.url, (
            f"Expected the dispatcher to land on /approval, got {dispatcher_page.url}"
        )
        assert home.breadcrumb_page.inner_text().strip() == "Requests"

    with allure.step("Breadcrumb is scoped to the default bound station"):
        station = home.breadcrumb_station.inner_text().strip()
        assert station == TestData.disp_req_default_station, (
            f"Breadcrumb station {station!r} != configured default "
            f"{TestData.disp_req_default_station!r}"
        )
        assert home.bound_station_text() == station, (
            "Sidebar station selector and breadcrumb disagree on the bound station"
        )
        assert home.breadcrumb_text() == f"{station} Requests"

    with allure.step("PENDING tab is the active tab on load"):
        assert home.active_tab() == "pending"

    with allure.step("Table header row shows all five columns"):
        headers = [
            h.strip()
            for h in dispatcher_page.locator("thead th").all_text_contents()
            if h.strip()
        ]
        assert headers == EXPECTED_HEADERS, f"Unexpected header row: {headers}"
