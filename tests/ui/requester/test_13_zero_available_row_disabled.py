"""Requester > Make New Request - Step 1, zero-stock row."""

import allure
import pytest

from config.data import TestData
from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@allure.title("A '0 Available' Sub-SKU row keeps its '+' control disabled")
def test_zero_available_row_disabled(requester_page):
    """Confirmed live 2026-08-26: under DGT15A0666-01, sub-SKU DILS0019 shows
    '0 Available' and its '+' button is a real disabled HTML control -
    cannot be added to the request."""
    home = RequesterHomePage(requester_page)
    home.open_make_new_request()
    home.select_sku(TestData.req_request_sku_code)
    zero_stock_sub_sku = TestData.req_request_zero_stock_sub_sku

    with allure.step(f"'{zero_stock_sub_sku}' shows 0 Available"):
        assert home.sub_sku_available_count(zero_stock_sub_sku) == 0

    with allure.step("'+' is disabled on that row"):
        assert home.sub_sku_add_button_disabled(zero_stock_sub_sku)

    with allure.step("Quantity stays 0 - no items can be added"):
        assert home.sub_sku_quantity(zero_stock_sub_sku) == 0
