"""Requester > Make New Request - Step 1, Sub-SKU rows."""

import allure
import pytest

from config.data import TestData
from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]

#: Confirmed live 2026-08-26: DGT15A0666-01's 7 sub-SKU components (DILS0019,
#: 0870DNW58, 0840DNW58, DBA0701A0A, DCH100, DTE15A0666, DSW0684). This is the
#: SKU's fixed BOM composition, not a live stock figure, so unlike "Available"
#: quantities it isn't expected to drift run to run.
EXPECTED_SUB_SKU_ROW_COUNT = 7


@allure.title("Selecting a SKU populates the Sub-SKU column with rows")
def test_selecting_sku_loads_sub_sku_rows(requester_page):
    """Selecting a SKU populates the Sub-SKU column with one row per
    component, each showing a description and an 'X Available' quantity."""
    home = RequesterHomePage(requester_page)
    home.open_make_new_request()
    home.select_sku(TestData.req_request_sku_code)

    with allure.step("Expected number of Sub-SKU rows rendered"):
        assert home.sub_sku_row_count() == EXPECTED_SUB_SKU_ROW_COUNT

    with allure.step("The known sub-SKU row shows its description and Available text"):
        row_text = home.sub_sku_row_text(TestData.req_request_sub_sku_code)
        assert TestData.req_request_sub_sku_description in row_text
        assert "Available" in row_text
