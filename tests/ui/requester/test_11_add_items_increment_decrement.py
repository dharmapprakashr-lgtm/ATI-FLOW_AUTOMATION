"""Requester > Make New Request - Step 1, quantity +/- controls."""

import allure
import pytest

from config.data import TestData
from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@allure.title("'+' and '-' increment and decrement a Sub-SKU's Add Items count")
def test_add_items_increment_decrement(requester_page):
    """On a Sub-SKU row with available stock, tapping '+' increments the Add
    Items counter; tapping '-' decrements it, never below 0.

    Confirmed live 2026-08-26 on DTE15A0666 (real stock). Ends by decrementing
    back to 0 so this suite doesn't leave a tentative reservation behind."""
    home = RequesterHomePage(requester_page)
    home.open_make_new_request()
    home.select_sku(TestData.req_request_sku_code)
    sub_sku = TestData.req_request_sub_sku_code

    try:
        with allure.step("'-' starts disabled at quantity 0"):
            assert home.sub_sku_quantity(sub_sku) == 0
            assert home.sub_sku_remove_button_disabled(sub_sku)

        with allure.step("'+' increments the counter and enables '-'"):
            home.add_sub_sku_item(sub_sku, count=1)
            assert home.sub_sku_quantity(sub_sku) == 1
            assert not home.sub_sku_remove_button_disabled(sub_sku)
            home.add_sub_sku_item(sub_sku, count=1)
            assert home.sub_sku_quantity(sub_sku) == 2

        with allure.step("'-' decrements the counter"):
            home.remove_sub_sku_item(sub_sku, count=1)
            assert home.sub_sku_quantity(sub_sku) == 1

        with allure.step("'-' disables again at 0, preventing it from going negative"):
            home.remove_sub_sku_item(sub_sku, count=1)
            assert home.sub_sku_quantity(sub_sku) == 0
            # The button is a real HTML `disabled` control here, not just
            # styled to look inactive - Playwright refuses to click a
            # disabled element, which is itself proof the floor holds.
            assert home.sub_sku_remove_button_disabled(sub_sku)
    finally:
        # Belt-and-braces cleanup in case an assertion above failed mid-way -
        # never leave a tentative reservation against real live stock.
        for _ in range(3):
            if home.sub_sku_quantity(sub_sku) == 0:
                break
            home.remove_sub_sku_item(sub_sku, count=1)
