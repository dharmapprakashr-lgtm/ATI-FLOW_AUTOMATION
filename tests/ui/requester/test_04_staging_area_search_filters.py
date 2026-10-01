"""Requester > Staging Area - search box."""

import allure
import pytest

from config.data import TestData
from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@allure.title("Search box filters the Staging Area card grid")
def test_staging_area_search_filters(requester_page):
    """Confirmed live 2026-08-26: typing a matching name keeps the card
    visible, a non-matching term filters it out entirely (0 cards, not just
    visually dimmed), and clearing the box restores it. Only one staging
    area (AH_stage) is bound to this device, so this proves the search
    actually filters rather than being a no-op decoration."""
    home = RequesterHomePage(requester_page)
    home.open_staging_area()
    assert home.staging_area_card_count() == 1

    with allure.step("Matching search keeps the card"):
        home.staging_area_search(TestData.staging_area_name)
        assert home.staging_area_card_count() == 1
        assert home.staging_area_card_title(0) == TestData.staging_area_name

    with allure.step("Non-matching search filters it out"):
        home.staging_area_search("zzz_definitely_no_match_zzz")
        assert home.staging_area_card_count() == 0

    with allure.step("Clearing the search restores the card"):
        home.staging_area_search("")
        assert home.staging_area_card_count() == 1
