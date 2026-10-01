"""Requester > Staging Area - card matches config."""

import allure
import pytest

from config.data import TestData
from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@allure.title("Staging Area card shows the bound area with its real cell grid")
def test_staging_area_matches_bound_cells(requester_page):
    """Confirmed live 2026-08-26: the device's one bound staging area
    (AH_stage, config/test_data.toml [staging_area]) renders as a single
    card showing '1 x 4 cells' - the area's fixed grid size in Fleet
    Manager, not a live occupancy figure, so stable to assert on exactly."""
    home = RequesterHomePage(requester_page)
    home.open_staging_area()

    with allure.step("Exactly one card, for the bound staging area"):
        assert home.staging_area_card_count() == 1
        assert home.staging_area_card_title(0) == TestData.staging_area_name

    with allure.step("Cell grid size matches Fleet Manager's real 1 x 4 layout"):
        assert home.staging_area_card_subtitle(0) == "1 x 4 cells"
