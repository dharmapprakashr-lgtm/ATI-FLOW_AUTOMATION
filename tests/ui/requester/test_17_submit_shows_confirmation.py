"""Requester > Make New Request - Step 3, Confirmation screen.

Verified live 2026-08-26 (screenshot): clicking Confirm on the Request
Summary step transitions to a Confirmation screen that shows:

  - A teal checkmark icon (Step 3 stepper node turns active)
  - "Request confirmed!" heading
  - "AMR will be assigned shortly to fulfill your request" sub-text
  - A Summary section with a Materials sub-heading
  - One row per submitted item (code + "N unit" label)
  - A "Home" button that returns to the Request History landing page

This test submits a real request against the live Fleet Manager — that is
intentional and expected in the test environment.  Fleet Manager can receive
these requests and the Dispatcher role is responsible for acting on them.
The request is placed under the device's bound machine/workflow context
(consuption_machine_45 / anyStation_to_StagingArea) exactly as a human
requester would do it.

NOTE: the `run_context` cross-role fixture (for handing the request id to
the Dispatcher phase) is not used here yet — test_12 only validates the
Confirmation screen itself.  Cross-role linking belongs in tests/e2e/.
"""

import allure
import pytest

from config.data import TestData
from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@allure.title("Submitting the request shows the Step 3 Confirmation screen")
def test_submit_shows_confirmation(requester_page):
    """Clicking Confirm on Step 2 (Request Summary) advances to Step 3
    (Confirmation) and shows a success heading, AMR sub-text, a Summary
    section with the submitted material, and a Home button.

    Confirmed live 2026-08-26: the stepper at the top highlights the third
    node ("Confirmation"), the page body shows a teal check circle,
    "Request confirmed!" and "AMR will be assigned shortly to fulfill your
    request", followed by a Summary accordion with the requested items and
    a "Home" button to return to the Request History page.
    """
    home = RequesterHomePage(requester_page)
    sub_sku = TestData.req_request_sub_sku_code

    with allure.step("Navigate through wizard to Step 2 (Request Summary)"):
        home.open_make_new_request()
        home.select_sku(TestData.req_request_sku_code)
        home.add_sub_sku_item(sub_sku, count=1)
        home.click_next()
        assert requester_page.get_by_text(
            "Request Summary", exact=True
        ).first.is_visible(timeout=5000)

    with allure.step("Clicking Confirm transitions to Step 3 Confirmation"):
        home.click_confirm_and_wait(timeout=15000)

    with allure.step("Step 3 stepper node is active"):
        assert home.step_confirmation.first.is_visible(timeout=5000)

    with allure.step("Success heading and AMR sub-text are visible"):
        assert home.confirmation_heading.is_visible()
        assert home.confirmation_amr_text.is_visible()

    with allure.step("Summary section with Materials sub-heading is visible"):
        assert home.confirmation_summary_heading.is_visible()
        assert home.confirmation_materials_heading.is_visible()

    with allure.step("The submitted sub-SKU appears in the confirmation summary"):
        summary_row = home.confirmation_summary_row(sub_sku)
        row_text = summary_row.inner_text()
        assert sub_sku in row_text, (
            f"Expected sub-SKU '{sub_sku}' in confirmation summary row, got: {row_text!r}"
        )

    with allure.step("Home button is present and returns to Request History"):
        assert home.home_btn.is_visible()
        home.click_home()
        # After Home the app lands back on the Request History page
        requester_page.locator("tbody tr").first.wait_for(
            state="visible", timeout=10000
        )
