"""Dispatcher > Requests - Station dropdown selection.

Verified live 2026-08-28: picking a different bound station updates the
breadcrumb ("<station> > Requests"), the sidebar selector value, and reloads
the table with that station's requests only (each bound station has its own,
independent queue - auto2_gg had pending rows, auto1_gg showed the empty
state).
"""

import allure
import pytest

from config.data import TestData
from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]


@allure.title("Selecting another bound station re-scopes the breadcrumb and the queue")
def test_switching_station_updates_breadcrumb_and_list(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)
    default_station = TestData.disp_req_default_station
    alt_station = TestData.disp_req_alt_station

    with allure.step("Starts on the default bound station"):
        assert home.breadcrumb_station.inner_text().strip() == default_station
        before_rows = home.row_texts()

    with allure.step(f"Switch to {alt_station}"):
        home.select_station(alt_station)

    with allure.step("Breadcrumb and sidebar selector both move to the new station"):
        assert home.breadcrumb_station.inner_text().strip() == alt_station
        assert home.bound_station_text() == alt_station
        assert home.breadcrumb_text() == f"{alt_station} Requests"

    with allure.step("The table reloaded for the new station"):
        after_rows = home.row_texts()
        assert after_rows != before_rows or home.is_empty_state(), (
            "Row set did not change after switching stations - the list may "
            "not be scoped per station"
        )

    with allure.step("Switching back restores the default station's scope"):
        home.select_station(default_station)
        assert home.breadcrumb_station.inner_text().strip() == default_station
