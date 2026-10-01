"""Authentication tests — Part 1.

Two focused smoke tests:

  TC_AUTH_001  Admin logs in with valid credentials → lands inside the app.
  TC_AUTH_002  Login is rejected with an invalid password → stays on login page.

All other auth edge-cases (session expiry, injection, brute-force, etc.)
are deferred to the security suite (Part 8 / test_security.py) or an
extended nightly regression run, because they require extra infra
(idle-timeout config, rate-limiter bypass, second browser context).

These two tests run first in every suite so a broken login is caught
immediately, before any admin-only test even tries to open a page.
"""

import allure
import pytest

from config.environment import config
from pages.login.login_page import LoginPage
from utils.waits import wait_for_app_ready

#: Also carries `admin`: every admin test depends on this login working, and
#: `pytest -m admin` is the suite's documented "whole admin console" command
#: (see README). Without this marker these two gate tests are silently
#: skipped by that run despite being first in SUITE_ORDER.
pytestmark = [pytest.mark.auth, pytest.mark.smoke, pytest.mark.admin]


# ── helpers ───────────────────────────────────────────────────────────────────

def _fresh_page(browser):
    """Open a brand-new browser context with no stored state."""
    ctx = browser.new_context(ignore_https_errors=config.ignore_https_errors)
    page = ctx.new_page()
    return ctx, page, LoginPage(page)


def _is_on_login(page):
    return "login" in page.url.lower()


def _is_inside_app(page):
    return not _is_on_login(page)


# =============================================================================
# Part 1 — Authentication gate
# =============================================================================

@allure.feature("Authentication")
@allure.story("Login")
class TestLogin:

    @allure.title("TC_AUTH_001 — Admin logs in with valid credentials")
    def test_admin_login_with_valid_credentials(self, browser):
        """
        ID     : TC_AUTH_001
        Title  : Admin logs in with valid credentials
        Reason : Gate test — all subsequent admin tests depend on a working
                 login. A broken auth is caught here before anything else runs.
        Steps  :
          1. Open a fresh (unauthenticated) browser context.
          2. Navigate to the login page.
          3. Enter the admin username and password from .env.
          4. Submit and wait for the app shell to appear.
        Pass   : URL no longer contains 'login'.
        """
        ctx, page, login = _fresh_page(browser)
        try:
            login.login(config.admin_user, config.admin_pass)
            wait_for_app_ready(page, timeout=config.default_timeout)
            assert _is_inside_app(page), (
                f"Valid admin login did not enter the app — still at: {page.url}"
            )
        finally:
            ctx.close()

    @allure.title("TC_AUTH_002 — Login is rejected with an invalid password")
    def test_login_rejected_with_invalid_credentials(self, browser):
        """
        ID     : TC_AUTH_002
        Title  : Login rejected with invalid credentials
        Reason : Confirms the password is actually verified; without this check
                 any string would be accepted and authentication would be meaningless.
        Steps  :
          1. Open a fresh browser context.
          2. Enter the correct admin username but a wrong password.
          3. Submit.
        Pass   : URL still contains 'login' (redirect back / no redirect).
        Fail   : App accepts the wrong password and enters a protected route.
        """
        ctx, page, login = _fresh_page(browser)
        try:
            login.login(config.admin_user, "this_is_definitely_the_wrong_password_XYZ!")
            page.wait_for_timeout(2000)
            assert _is_on_login(page), (
                "App accepted an invalid password — authentication is broken."
            )
        finally:
            ctx.close()
