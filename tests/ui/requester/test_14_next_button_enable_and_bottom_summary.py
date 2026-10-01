"""Requester > Make New Request - Step 1, Next button + footer summary."""

import allure
import pytest

from config.data import TestData
from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@allure.title("Adding an item swaps the footer message and enables Next")
def test_next_button_enable_and_bottom_summary(requester_page):
    """Confirmed live 2026-08-26: once any Sub-SKU quantity > 0, the 'Please
    add items to proceed' message is replaced with 'N Units of <code> added'
    and Next becomes enabled. Removing the item again reverts both."""
    home = RequesterHomePage(requester_page)
    home.open_make_new_request()
    home.select_sku(TestData.req_request_sku_code)
    sub_sku = TestData.req_request_sub_sku_code

    try:
        with allure.step("Before adding anything: empty message, Next disabled"):
            assert home.empty_items_message.is_visible()
            assert not home.next_btn.is_enabled()

        with allure.step("After adding one item: summary message, Next enabled"):
            home.add_sub_sku_item(sub_sku, count=1)
            assert f"1 Units of {sub_sku} added" in home.footer_summary_text()
            assert home.next_btn.is_enabled()
    finally:
        home.remove_sub_sku_item(sub_sku, count=1)
