"""Requester > Make New Request - Step 1, quantity ceiling."""

import allure
import pytest

from config.data import TestData
from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@allure.title("Quantity cannot be pushed past the 'X Available' figure")
def test_quantity_cannot_exceed_available(requester_page):
    """Confirmed live 2026-08-26: unlike the scaffold's original guess, '+'
    does NOT disable at the ceiling - it silently caps. Clicking '+' exactly
    'X Available' times brings the row to '0 Available' with quantity == X;
    a further '+' click is a no-op (quantity stays at X, still 0 Available).

    Reads the live Available figure at test start rather than hardcoding it,
    since it's real production stock and drifts. Always decrements back down
    to 0 afterwards - confirmed live that this fully restores the original
    Available count, so no tentative reservation is left behind."""
    home = RequesterHomePage(requester_page)
    home.open_make_new_request()
    home.select_sku(TestData.req_request_sku_code)
    sub_sku = TestData.req_request_sub_sku_code

    starting_available = home.sub_sku_available_count(sub_sku)
    assert starting_available > 0, (
        f"'{sub_sku}' shows 0 Available right now - ceiling test needs a "
        f"moment with real stock; re-run when live inventory allows it."
    )

    try:
        with allure.step(f"Add up to the ceiling ({starting_available})"):
            home.add_sub_sku_item(sub_sku, count=starting_available)
            assert home.sub_sku_quantity(sub_sku) == starting_available
            assert home.sub_sku_available_count(sub_sku) == 0

        with allure.step("One more '+' click does not push past the ceiling"):
            home.add_sub_sku_item(sub_sku, count=1)
            assert home.sub_sku_quantity(sub_sku) == starting_available
            assert home.sub_sku_available_count(sub_sku) == 0
    finally:
        with allure.step("Clean up: decrement back to 0, restoring live Available"):
            home.remove_sub_sku_item(sub_sku, count=starting_available)
            assert home.sub_sku_quantity(sub_sku) == 0
            assert home.sub_sku_available_count(sub_sku) == starting_available
