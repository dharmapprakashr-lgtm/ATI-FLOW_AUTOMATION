"""Requester > Make New Request - Step 1 to Step 2 transition."""

import allure
import pytest

from config.data import TestData
from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@allure.title("Next advances from Request Material to Request Summary")
def test_advance_to_request_summary_step(requester_page):
    """Confirmed live 2026-08-26: with a valid Step 1 selection, tapping Next
    leaves the SKU search screen and shows the Request Summary heading, plus
    a Back control to return to Step 1 and a Confirm control to submit.

    Does not click Confirm - that would place a real request against the
    live Fleet Manager (see atiflow-testing-approach memory)."""
    home = RequesterHomePage(requester_page)
    home.open_make_new_request()
    home.select_sku(TestData.req_request_sku_code)
    home.add_sub_sku_item(TestData.req_request_sub_sku_code, count=1)

    with allure.step("Next advances to Request Summary"):
        home.click_next()
        assert home.step_request_summary.first.is_visible(timeout=5000)
        assert requester_page.get_by_text("Request Summary", exact=True).first.is_visible()

    with allure.step("Step 2 offers Back (to Step 1) and Confirm (to submit)"):
        assert home.back_btn.is_visible()
        assert home.confirm_btn.is_visible()

    with allure.step("Back returns to Step 1 with the selection intact"):
        home.click_back()
        assert home.step_request_material.first.is_visible(timeout=5000)
        assert home.sub_sku_quantity(TestData.req_request_sub_sku_code) == 1

    with allure.step("Clean up"):
        home.remove_sub_sku_item(TestData.req_request_sub_sku_code, count=1)
