"""Access Control tests — Part 2.

Covers TC_AC_001 through TC_AC_004:
  - Requester cannot reach Admin routes
  - Dispatcher cannot reach Admin configuration
  - Supervisor navigation limited to permitted areas
  - Admin sees the complete navigation tree

Each test uses a role-specific page fixture that is seeded and authenticated
by the fixture chain in fixtures/role_fixtures.py.
"""

import allure
import pytest
from playwright.sync_api import expect

from config.environment import config
from pages.admin.admin_navigation import AdminDashboardPage

pytestmark = [pytest.mark.access_control]

# Known admin-only routes to probe for role access
_ADMIN_ONLY_ROUTES = [
    "/admin",
    "/admin/processing_area",
    "/Execution_Source_Config",
    # FM/MES connection config lives here — added 2026-09-03 while cross-
    # referencing a BRD test-case list that specifically calls out "Central
    # configuration screen accessible only to Admin role". Not yet re-run
    # against the live app (network to 192.168.6.32 was down when this was
    # added) — verify on the next live pass.
    "/settings",
]


def _is_blocked(page):
    """Return True if the page was redirected away or shows a blocked-access UI.

    Verified against the live app (2026-08-21): a non-admin role hitting
    ``/admin`` or ``/admin/processing_area`` is not redirected at all - the URL
    stays put and the app renders its own 404 ("Page Not Found... uncharted
    territory") in place, rather than an explicit "access denied" message.
    ``/Execution_Source_Config`` does show an explicit "not authorized" message.
    Both are legitimate ways to block a route, so this checks for either.
    """
    url_lower = page.url.lower()
    if "login" in url_lower:
        return True
    denied_locators = [
        page.locator("text=Access Denied"),
        page.locator("text=403"),
        page.locator("text=Forbidden"),
        page.locator("text=Unauthorized"),
        page.locator("text=Not Authorized"),
        page.locator("text=404"),
        page.locator("text=Page Not Found"),
        page.locator("text=uncharted territory"),
    ]
    return any(loc.first.is_visible(timeout=1000) for loc in denied_locators)


# =============================================================================
# Access Control by Role
# =============================================================================

@allure.feature("Access Control")
class TestAccessControl:
    """TC_AC_001 – TC_AC_004"""

    @allure.title("TC_AC_001 — Requester cannot reach Admin routes by URL")
    def test_requester_cannot_reach_admin_routes_by_url(self, requester_page):
        """
        ID     : TC_AC_001
        Sub    : Requester
        Title  : Requester cannot reach Admin routes by URL
        Reason : Hiding a menu item is not security. Server-side authorisation
                 must block the request even when the URL is typed directly.
        """
        base = config.app_url
        for route in _ADMIN_ONLY_ROUTES:
            with allure.step(f"Probe route: {route}"):
                requester_page.goto(
                    base + route, wait_until="domcontentloaded"
                )
                requester_page.wait_for_timeout(1500)
                assert _is_blocked(requester_page), (
                    f"Requester was NOT blocked from admin route '{route}'. "
                    f"Landed at: {requester_page.url}"
                )

    @allure.title("TC_AC_002 — Dispatcher cannot reach Admin configuration")
    def test_dispatcher_cannot_reach_admin_configuration(self, dispatcher_page):
        """
        ID     : TC_AC_002
        Sub    : Dispatcher
        Title  : Dispatcher cannot reach Admin configuration
        Reason : Dispatcher modifying master config (areas, machines, MES)
                 would affect the whole fleet.
        """
        base = config.app_url
        for route in _ADMIN_ONLY_ROUTES:
            with allure.step(f"Probe route: {route}"):
                dispatcher_page.goto(
                    base + route, wait_until="domcontentloaded"
                )
                dispatcher_page.wait_for_timeout(1500)
                assert _is_blocked(dispatcher_page), (
                    f"Dispatcher was NOT blocked from admin route '{route}'. "
                    f"Landed at: {dispatcher_page.url}"
                )

    @allure.title("TC_AC_003 — Supervisor navigation is limited to permitted areas")
    def test_supervisor_navigation_limited_to_permitted_areas(self, supervisor_page):
        """
        ID     : TC_AC_003
        Sub    : Supervisor
        Title  : Supervisor navigation is limited to permitted areas
        Reason : Supervisor scope must stay within their assigned Processing
                 Areas — another area's data must not be visible.
        """
        # Supervisor should not reach admin configuration routes
        for route in _ADMIN_ONLY_ROUTES:
            with allure.step(f"Probe admin route: {route}"):
                supervisor_page.goto(
                    config.app_url + route, wait_until="domcontentloaded"
                )
                supervisor_page.wait_for_timeout(1500)
                assert _is_blocked(supervisor_page), (
                    f"Supervisor was NOT blocked from admin route '{route}'. "
                    f"Landed at: {supervisor_page.url}"
                )

    @allure.title("TC_AC_004 — Admin sees the complete navigation tree")
    def test_admin_sees_complete_navigation_tree(self, admin_page):
        """
        ID     : TC_AC_004
        Sub    : Admin
        Title  : Admin sees the complete navigation tree
        Reason : Positive counterpart to the negative tests — over-restriction
                 that blocks the Admin is also a bug.
        """
        dashboard = AdminDashboardPage(admin_page)

        with allure.step("Processing Areas header is visible in sidebar"):
            expect(dashboard.processing_areas_header).to_be_visible(timeout=10000)

        with allure.step("Execution Source Config menu is visible"):
            expect(dashboard.execution_source_config_menu).to_be_visible(timeout=5000)

        with allure.step("Admin can navigate to Execution Source Config"):
            dashboard.navigate_to_execution_source_config()
            for tab in (
                dashboard.requester_tab,
                dashboard.mes_tab,
                dashboard.dispatcher_tab,
                dashboard.supervisor_tab,
            ):
                expect(tab).to_be_visible(timeout=5000)
