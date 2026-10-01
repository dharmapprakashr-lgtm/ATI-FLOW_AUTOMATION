"""Supervisor device login — gate test.

  TC_SUP_LOGIN_001  Admin-provisioned supervisor device logs in -> lands on
                    its own dashboard (/stagingArea).
  TC_SUP_LOGIN_002  Login is rejected with an invalid password.

Named to sort first in this folder (test_00_ < test_01_ ...), so a broken
supervisor login is caught immediately, before any other supervisor test
tries to open a page — same reasoning as tests/ui/requester/test_00_login.py
and tests/ui/dispatcher/test_00_login.py.

``seeded_supervisor`` makes this the actual flow from the manual test plan:
admin creates the supervisor device via Execution Source Config first
(session-scoped, idempotent — deletes and recreates the record, binding it to
its Processing Area by checkbox), *then* this test logs in as that device.
Unlike ``supervisor_page`` (used by every other supervisor test), this test
drives a fresh, un-authenticated context through the real LoginPage flow.
"""

import allure
import pytest

from config.environment import config
from pages.dashboards.supervisor_dashboard_page import SupervisorHomePage
from pages.login.login_page import LoginPage

pytestmark = [pytest.mark.supervisor, pytest.mark.smoke, pytest.mark.dashboards]


def _fresh_page(browser):
    """Open a brand-new browser context with no stored state."""
    ctx = browser.new_context(ignore_https_errors=config.ignore_https_errors)
    page = ctx.new_page()
    return ctx, page, LoginPage(page)


@allure.feature("Dashboards")
@allure.story("Supervisor login")
class TestSupervisorLogin:

    @allure.title("TC_SUP_LOGIN_001 — Admin-provisioned supervisor device logs in")
    def test_supervisor_device_login_with_valid_credentials(self, browser, seeded_supervisor):
        """
        ID     : TC_SUP_LOGIN_001
        Title  : Admin-provisioned supervisor device logs in and lands on its
                 own dashboard
        Reason : Gate test — every other supervisor test assumes login already
                 works. Device login uses the device's Name, not its Device ID
                 (confirmed live; Device ID always 401s regardless of password).
        Steps  :
          1. Admin creates/refreshes the supervisor device (seeded_supervisor).
          2. Open a fresh, unauthenticated browser context.
          3. Log in with the device's Name and Password.
        Pass   : URL leaves 'login' and lands on /stagingArea; the supervisor
                 sidebar's Processing Area selector is visible.
        """
        name, password = seeded_supervisor.as_login()
        ctx, page, login = _fresh_page(browser)
        try:
            login.login(name, password)
            page.wait_for_timeout(2500)

            assert "login" not in page.url.lower(), (
                f"Supervisor device '{name}' did not authenticate — still at: {page.url}"
            )
            assert "stagingarea" in page.url.lower(), (
                f"Supervisor device '{name}' authenticated but did not land on "
                f"/stagingArea — landed at: {page.url}"
            )

            home = SupervisorHomePage(page)
            assert home.pa_select.is_visible(timeout=8000), (
                f"Supervisor device '{name}' logged in but its dashboard "
                f"(Processing Area selector) never rendered."
            )
        finally:
            ctx.close()

    @allure.title("TC_SUP_LOGIN_002 — Supervisor login is rejected with an invalid password")
    def test_supervisor_device_login_rejected_with_invalid_credentials(self, browser, seeded_supervisor):
        """
        ID     : TC_SUP_LOGIN_002
        Title  : Supervisor device login is rejected with an invalid password
        Reason : Confirms the device's password is actually verified, not just
                 its Name.
        Pass   : URL still contains 'login'.
        """
        name, _ = seeded_supervisor.as_login()
        ctx, page, login = _fresh_page(browser)
        try:
            login.login(name, "this_is_definitely_the_wrong_password_XYZ!")
            page.wait_for_timeout(2000)
            assert "login" in page.url.lower(), (
                f"Supervisor device '{name}' was accepted with a wrong "
                f"password — authentication is broken."
            )
        finally:
            ctx.close()
