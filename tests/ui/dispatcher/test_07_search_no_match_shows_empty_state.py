"""Dispatcher > Requests - search box, no-match case.

Verified live 2026-08-28: a search string matching nothing shows a single
centred "No pending requests found." row - a clear empty state, not a blank
table, a spinner, or an error toast. Clearing the box brings the queue back.
"""

import allure
import pytest

from config.data import TestData
from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage
from utils.waits import is_error_visible

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]


@allure.title("A search with no matches shows the empty state, not an error or blank table")
def test_search_no_match_shows_empty_state(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)
    before = home.row_texts()

    with allure.step(f"Search for {TestData.disp_req_no_match!r}"):
        home.search(TestData.disp_req_no_match)

    with allure.step("Empty-state message is shown"):
        assert home.is_empty_state(), (
            f"Expected an empty-state row; tbody was: "
            f"{dispatcher_page.locator('tbody').inner_text()!r}"
        )
        assert TestData.disp_req_empty_state in dispatcher_page.locator("tbody").inner_text().lower()
        assert home.row_count() == 0
        assert not is_error_visible(dispatcher_page, timeout=1000), (
            "A no-match search should not raise an error toast"
        )

    with allure.step("Clearing the search restores the previous rows"):
        home.clear_search()
        assert home.row_texts() == before or not home.is_empty_state()
