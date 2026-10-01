"""Dispatcher > Requests - Station dropdown (left sidebar).

Verified live 2026-08-28: the sidebar Station dropdown
(#operator-sidebar-dispatch-select) opens to exactly the stations bound to
this dispatcher device in Execution Source Config - config/test_data.toml
[devices] dispatcher_bound_stations - and nothing else. It is not a list of
every station in the system.
"""

import allure
import pytest

from config.data import TestData
from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]


def _bound_stations():
    """dispatcher_bound_stations, normalised to a list."""
    value = TestData.disp_bound_stations
    return list(value) if isinstance(value, (list, tuple)) else [value]


@allure.title("Station dropdown lists only this device's bound stations")
def test_station_dropdown_lists_bound_stations(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)
    expected = _bound_stations()

    with allure.step("Open the sidebar Station dropdown"):
        options = home.open_station_dropdown()
        home.close_dropdown()

    with allure.step(f"Options exactly match the {len(expected)} configured bound stations"):
        assert sorted(options) == sorted(expected), (
            f"Station dropdown options {sorted(options)} != configured bound "
            f"stations {sorted(expected)}"
        )
