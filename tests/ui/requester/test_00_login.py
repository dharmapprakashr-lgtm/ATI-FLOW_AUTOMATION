"""Requester device login — gate test.

  TC_LOGIN_REQ_001  Admin-provisioned requester device logs in -> lands on
                     its own dashboard.
  TC_LOGIN_REQ_002  Login is rejected with an invalid password.

Named to sort first in this folder (test_00_ < test_01_ < test_requester_),
so a broken requester login is caught immediately, before any other requester
test tries to open a page - same reasoning as tests/ui/test_login.py for admin.

``seeded_requester`` is what makes this the actual flow described by the
manual test plan: admin creates the requester device via Execution Source
Config first (session-scoped, idempotent - deletes and recreates the record),
*then* this test logs in as that device and lands on the requester side.
Unlike ``requester_page`` (used by every other requester test), this test
drives a fresh, un-authenticated context through the real LoginPage flow
instead of restoring saved session state, so a login regression fails here
with a clear assertion instead of surfacing as a confusing error deep inside
another test's fixture setup.
"""

import allure
import pytest

from config.environment import config
from pages.dashboards.requester_dashboard_page import RequesterHomePage
from pages.login.login_page import LoginPage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


def _fresh_page(browser):
    """Open a brand-new browser context with no stored state."""
    ctx = browser.new_context(ignore_https_errors=config.ignore_https_errors)
    page = ctx.new_page()
    return ctx, page, LoginPage(page)


@allure.feature("Dashboards")
@allure.story("Requester login")
class TestRequesterLogin:

    @allure.title("TC_LOGIN_REQ_001 — Admin-provisioned requester device logs in")
    def test_requester_device_login_with_valid_credentials(self, browser, seeded_requester):
        """
        ID     : TC_LOGIN_REQ_001
        Title  : Admin-provisioned requester device logs in and lands on its
                 own dashboard
        Reason : Gate test — every other requester test assumes login already
                 works. Device login uses the device's Name, not its Device
                 ID (confirmed live; Device ID always 401s regardless of
                 password), so this also guards against that mistake creeping
                 back into ``as_login()``.
        Steps  :
          1. Admin creates/refreshes the requester device (seeded_requester).
          2. Open a fresh, unauthenticated browser context.
          3. Log in with the device's Name and Password.
        Pass   : URL leaves 'login', and the requester dashboard's own
                 "Make New Request" control is visible.
        """
        name, password = seeded_requester.as_login()
        ctx, page, login = _fresh_page(browser)
        try:
            login.login(name, password)
            page.wait_for_timeout(2000)

            assert "login" not in page.url.lower(), (
                f"Requester device '{name}' did not authenticate — still at: {page.url}"
            )

            home = RequesterHomePage(page)
            assert home.make_new_request_btn.is_visible(timeout=5000), (
                f"Requester device '{name}' logged in but its dashboard "
                f"('Make New Request') never rendered."
            )
        finally:
            ctx.close()

    @allure.title("TC_LOGIN_REQ_002 — Requester login is rejected with an invalid password")
    def test_requester_device_login_rejected_with_invalid_credentials(self, browser, seeded_requester):
        """
        ID     : TC_LOGIN_REQ_002
        Title  : Requester device login is rejected with an invalid password
        Reason : Confirms the device's password is actually verified, not
                 just its Name.
        Pass   : URL still contains 'login'.
        Fail   : App accepts the wrong password and enters the dashboard.
        """
        name, _ = seeded_requester.as_login()
        ctx, page, login = _fresh_page(browser)
        try:
            login.login(name, "this_is_definitely_the_wrong_password_XYZ!")
            page.wait_for_timeout(2000)
            assert "login" in page.url.lower(), (
                f"Requester device '{name}' was accepted with a wrong "
                f"password — authentication is broken."
            )
        finally:
            ctx.close()
