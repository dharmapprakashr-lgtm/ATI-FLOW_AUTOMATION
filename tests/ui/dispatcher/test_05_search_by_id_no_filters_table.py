"""Dispatcher > Requests - search box vs. the "ID No." column.

The original scaffold assumed typing a Request ID (e.g. "312") filters the
table to that one request. Verified live 2026-08-28 that is NOT how the box
behaves: it matches the **Request Details / material-code** column only, and a
bare numeric ID search drops straight to the empty state ("No pending
requests found."). This test pins that real behaviour so a future regression
that *starts* matching IDs - or that breaks material-code search - is caught.

Search-by-material-code is covered positively in
test_06_search_by_material_code_filters_table.py.
"""

import allure
import pytest

from config.data import TestData
from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]


@allure.title("Search box does not match the ID No. column (matches material code only)")
def test_search_by_id_no_filters_table(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)

    ids = home.row_ids()
    if not ids:
        pytest.skip("No pending requests on the default station to search for.")

    target_id = str(ids[0])
    target_material = home.row_material(ids[0])

    with allure.step(f"Searching the bare ID {target_id!r} yields the empty state"):
        home.search(target_id)
        assert home.is_empty_state(), (
            f"Search for ID {target_id!r} returned rows - the search box now "
            f"matches the ID No. column, which it did not on 2026-08-28. "
            f"Update this test and dispatcher_dashboard_page if that is intended."
        )

    with allure.step("Searching that row's material code DOES surface the row"):
        home.search(target_material)
        assert not home.is_empty_state()
        assert target_material in " ".join(home.row_texts())

    home.clear_search()
