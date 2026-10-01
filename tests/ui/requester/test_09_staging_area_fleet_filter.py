"""Requester > Staging Area - 'All Fleets' dropdown."""

import allure
import pytest

from config.data import TestData
from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@allure.title("'All Fleets' dropdown filters Staging Area cards by fleet")
def test_staging_area_fleet_filter(requester_page):
    """Switching to the staging area's own fleet (or 'All Fleets') keeps its
    card visible; switching to a different real fleet filters it out.

    Confirmed live 2026-08-26: 4 real fleets exist ("All Fleets", "test_01",
    "Isaac_sim_warehouse_v4", "test"); AH_stage belongs to "test" - see
    config/test_data.toml [staging_area] bound_fleet/other_fleet."""
    home = RequesterHomePage(requester_page)
    home.open_staging_area()
    assert home.staging_area_card_count() == 1

    with allure.step(f"Switching to a different fleet ('{TestData.staging_area_other_fleet}') filters the card out"):
        home.staging_area_select_fleet(TestData.staging_area_other_fleet)
        assert home.staging_area_card_count() == 0

    with allure.step(f"Switching to the bound fleet ('{TestData.staging_area_bound_fleet}') shows it again"):
        home.staging_area_select_fleet(TestData.staging_area_bound_fleet)
        assert home.staging_area_card_count() == 1
        assert home.staging_area_card_title(0) == TestData.staging_area_name

    with allure.step("'All Fleets' also shows it"):
        home.staging_area_select_fleet("All Fleets")
        assert home.staging_area_card_count() == 1
