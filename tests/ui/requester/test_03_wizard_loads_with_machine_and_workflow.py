"""Requester > Make New Request - initial load."""

import allure
import pytest

from config.data import TestData
from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@allure.title("Make New Request wizard loads in its empty Step 1 state")
def test_wizard_loads_with_machine_and_workflow(requester_page):
    """Confirmed live 2026-08-26: opening the wizard shows the bound machine
    in the breadcrumb, the 3-step progress bar (Request Material active),
    an empty SKU search box, and Next disabled with "Please add items to
    proceed" - before any SKU is searched."""
    home = RequesterHomePage(requester_page)
    home.open_make_new_request()

    with allure.step("Breadcrumb shows the bound machine and 'Make New Request'"):
        assert requester_page.get_by_text(TestData.machine_name_cons, exact=True).first.is_visible()
        assert requester_page.get_by_text("Make New Request", exact=True).first.is_visible()

    with allure.step("All three wizard steps are present"):
        assert home.step_request_material.first.is_visible()
        assert home.step_request_summary.first.is_visible()
        assert home.step_confirmation.first.is_visible()

    with allure.step("SKU search is empty and Next is disabled"):
        assert home.sku_search_input.input_value() == ""
        assert not home.next_btn.is_enabled()
        assert home.empty_items_message.is_visible()
