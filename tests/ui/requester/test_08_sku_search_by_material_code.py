"""Requester > Make New Request - Step 1, SKU search."""

import allure
import pytest

from config.data import TestData
from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@allure.title("Searching a material code returns the matching SKU")
def test_sku_search_by_material_code(requester_page):
    """Typing a material code into 'Search by material code...' returns a
    dropdown option for it; clicking that option loads its Sub-SKU rows.

    Uses config/test_data.toml's [requester_request_material] - a real, live
    SKU with physical WIP inventory (this suite's own throwaway [material]
    has none, see the requester_dashboard_page module docstring). Confirmed
    live 2026-08-26."""
    home = RequesterHomePage(requester_page)
    home.open_make_new_request()

    with allure.step("Search returns the SKU"):
        options = home.search_material(TestData.req_request_sku_code)
        assert any(TestData.req_request_sku_code in o for o in options), (
            f"Expected SKU '{TestData.req_request_sku_code}' in search results, got {options}"
        )

    with allure.step("Selecting it loads Sub-SKU rows below"):
        home.select_sku(TestData.req_request_sku_code)
        assert requester_page.get_by_text(TestData.req_request_sub_sku_code, exact=False).first.is_visible()
