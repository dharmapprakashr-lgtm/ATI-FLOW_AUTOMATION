"""Dispatcher device login — gate test.

  TC_LOGIN_DISP_001  Admin-provisioned dispatcher device logs in -> lands on
                     its own Requests screen.
  TC_LOGIN_DISP_002  Login is rejected with an invalid password.

Named to sort first in this folder (test_00_ < test_01_ < test_dispatcher_),
so a broken dispatcher login is caught immediately, before any other
dispatcher test tries to open a page - same reasoning as
tests/ui/requester/test_00_login.py.

``seeded_dispatcher`` is what makes this the actual flow described by the
manual test plan: admin creates the dispatcher device via Execution Source
Config first (session-scoped, idempotent - deletes and recreates the record),
*then* this test logs in as that device and lands on the dispatcher side.
Unlike ``dispatcher_page`` (used by every other dispatcher test), this test
drives a fresh, un-authenticated context through the real LoginPage flow
instead of restoring saved session state, so a login regression fails here
with a clear assertion instead of surfacing as a confusing error deep inside
another test's fixture setup.
"""

import allure
import pytest

from config.environment import config
from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage
from pages.login.login_page import LoginPage

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]


def _fresh_page(browser):
    """Open a brand-new browser context with no stored state."""
    ctx = browser.new_context(ignore_https_errors=config.ignore_https_errors)
    page = ctx.new_page()
    return ctx, page, LoginPage(page)


@allure.feature("Dashboards")
@allure.story("Dispatcher login")
class TestDispatcherLogin:

    @allure.title("TC_LOGIN_DISP_001 — Admin-provisioned dispatcher device logs in")
    def test_dispatcher_device_login_with_valid_credentials(self, browser, seeded_dispatcher):
        """
        ID     : TC_LOGIN_DISP_001
        Title  : Admin-provisioned dispatcher device logs in and lands on its
                 own Requests screen
        Reason : Gate test — every other dispatcher test assumes login already
                 works. Device login uses the device's Name, not its Device
                 ID (confirmed live; Device ID always 401s regardless of
                 password), so this also guards against that mistake creeping
                 back into ``as_login()``.
        Steps  :
          1. Admin creates/refreshes the dispatcher device (seeded_dispatcher).
          2. Open a fresh, unauthenticated browser context.
          3. Log in with the device's Name and Password.
        Pass   : URL leaves 'login', and the dispatcher's own bound-station
                 sidebar control is visible.
        """
        name, password = seeded_dispatcher.as_login()
        ctx, page, login = _fresh_page(browser)
        try:
            login.login(name, password)
            page.wait_for_timeout(2000)

            assert "login" not in page.url.lower(), (
                f"Dispatcher device '{name}' did not authenticate — still at: {page.url}"
            )

            home = DispatcherHomePage(page)
            assert home.bound_station_select.is_visible(timeout=8000), (
                f"Dispatcher device '{name}' logged in but its Requests screen "
                f"(bound-station sidebar control) never rendered."
            )
        finally:
            ctx.close()

    @allure.title("TC_LOGIN_DISP_002 — Dispatcher login is rejected with an invalid password")
    def test_dispatcher_device_login_rejected_with_invalid_credentials(self, browser, seeded_dispatcher):
        """
        ID     : TC_LOGIN_DISP_002
        Title  : Dispatcher device login is rejected with an invalid password
        Reason : Confirms the device's password is actually verified, not
                 just its Name.
        Pass   : URL still contains 'login'.
        Fail   : App accepts the wrong password and enters the dashboard.
        """
        name, _ = seeded_dispatcher.as_login()
        ctx, page, login = _fresh_page(browser)
        try:
            login.login(name, "this_is_definitely_the_wrong_password_XYZ!")
            page.wait_for_timeout(2000)
            assert "login" in page.url.lower(), (
                f"Dispatcher device '{name}' was accepted with a wrong "
                f"password — authentication is broken."
            )
        finally:
            ctx.close()
