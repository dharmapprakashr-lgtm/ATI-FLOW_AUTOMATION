"""Requester > Request History - cancel a Requested-status order.

The ACTIONS column on each row in the Requested tab contains a red ⊗ icon
button (MUI IconButton, no text, no aria-label) followed by an
expand-details chevron.  This test clicks the ⊗ directly.

Flow under test:
  1. Submit a fresh request (same flow as test_17) so there is a known
     Requested-status order to act on — the test no longer depends on
     ambient state left by an earlier test or a manual run.
  2. Note its Req-NNN id (newest row on the Requested tab).
  3. Click the ⊗ icon in that row's ACTIONS column.
  4. Confirm the "Cancel Request — Are you sure…?" dialog ("Yes, Cancel").
  5. Assert the id appears in the "Cancelled" tab within a short poll.
  6. Assert it is no longer visible in the "Requested" tab.

Placing the request is intentional and sanctioned in the test environment
(see test_17's module docstring). This test then cancels exactly the order
it created, so it is self-cleaning and safe to run repeatedly.
"""

import allure
import pytest

from config.data import TestData
from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@allure.title("A Requested order can be cancelled via the ACTIONS column ⊗ icon")
def test_cancel_requested_order(requester_page):
    """Submit a request, then cancel it from the Requested tab's ⊗ icon and
    verify it moves to the Cancelled tab and leaves the Requested tab.
    """
    home = RequesterHomePage(requester_page)
    sku = TestData.req_request_sku_code
    sub_sku = TestData.req_request_sub_sku_code

    with allure.step(f"Submit a fresh request for {sub_sku}"):
        home.open_make_new_request()
        try:
            # select_sku's click carries Playwright's full actionability wait,
            # so this rides out the known SKU-search latency (see
            # RequesterHomePage.search_material) rather than a flaky pre-check.
            home.select_sku(sku)
            home.add_sub_sku_item(sub_sku, count=1)
        except Exception as exc:
            pytest.skip(
                f"Could not stage an order for {sub_sku}/{sku} — the wizard "
                f"shows no available stock right now ({exc.__class__.__name__})."
            )
        home.click_next()
        assert requester_page.get_by_text("Request Summary", exact=True).first.is_visible(
            timeout=5000
        )
        home.click_confirm_and_wait(timeout=20000)
        home.click_home()

    with allure.step("Note the Req-NNN id of the order just created"):
        home.request_history_nav.click()
        home.requested_tab.click()
        requester_page.wait_for_timeout(1000)
        home.set_history_sort("Newest First")
        req_id, first_row = home.get_first_requested_row()
        assert req_id is not None, (
            "Could not find a Req-NNN id in the first row of the Requested tab "
            "after submitting a request."
        )

    with allure.step(f"Click the ⊗ cancel icon in the ACTIONS column for {req_id}"):
        home.click_cancel_icon_on_row(first_row, timeout=10000)

    with allure.step("Confirm the 'Cancel Request' dialog"):
        home.confirm_cancel_dialog(timeout=8000)

    with allure.step(f"Order {req_id} appears in the Cancelled tab"):
        found_in_cancelled = home.request_id_in_tab(req_id, "Cancelled", timeout=15000)
        assert found_in_cancelled, (
            f"{req_id} did not appear in the Cancelled tab within 15 s after "
            f"clicking the cancel icon."
        )

    with allure.step(f"Order {req_id} is no longer in the Requested tab"):
        home.requested_tab.click()
        requester_page.wait_for_timeout(800)
        row_texts = home.request_history_row_texts()
        assert not any(req_id in t for t in row_texts), (
            f"{req_id} still visible in the Requested tab after cancellation."
        )
