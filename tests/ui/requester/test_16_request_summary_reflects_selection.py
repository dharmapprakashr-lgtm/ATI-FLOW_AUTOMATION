"""Requester > Make New Request - Step 2, Request Summary."""

import allure
import pytest

from config.data import TestData
from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@allure.title("Request Summary reflects exactly what was added in Step 1")
def test_request_summary_reflects_selection(requester_page):
    """Confirmed live 2026-08-26: Step 2 shows a "Request Summary" heading,
    a "1. Material" / "Quantity" column header row, and one row per added
    Sub-SKU with its code, description, and exact quantity - matching what
    was set in Step 1, before confirmation.

    Does not click Confirm - that would place a real request against the
    live Fleet Manager (see atiflow-testing-approach memory)."""
    home = RequesterHomePage(requester_page)
    home.open_make_new_request()
    home.select_sku(TestData.req_request_sku_code)
    sub_sku = TestData.req_request_sub_sku_code
    home.add_sub_sku_item(sub_sku, count=2)

    home.click_next()
    assert requester_page.get_by_text("Request Summary", exact=True).first.is_visible(timeout=5000)

    with allure.step("Column headers are present"):
        assert requester_page.get_by_text("1. Material", exact=True).is_visible()
        assert requester_page.get_by_text("Quantity", exact=True).is_visible()

    with allure.step("The added Sub-SKU appears with its description and exact quantity"):
        row_text = home.summary_row(sub_sku).inner_text()
        assert sub_sku in row_text
        assert TestData.req_request_sub_sku_description in row_text
        assert "Units" in row_text
        assert home.summary_quantity(sub_sku) == 2

    with allure.step("Clean up: back to Step 1 and remove the added items"):
        home.click_back()
        home.remove_sub_sku_item(sub_sku, count=2)
