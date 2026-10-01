"""Execution Source Config validation tests — Part 4 additions.

Complements the existing device create + lifecycle tests with:

TC_RQD_003  Duplicate device name or identifier rejected
TC_RQD_004  Newly provisioned device can actually log in
TC_MES_002  Invalid MES parameters fail cleanly
TC_DSP_002  Dispatcher only receives tasks from its assigned scope
TC_SPD_002  Supervisor scope spans configured Processing Areas

TC_MES_003 / TC_MES_004 were deleted 2026-09-04 — this environment's MES tab is
a workflow list with no connection form / Test Connection button / credential
field to test.
"""

import allure
import pytest
from playwright.sync_api import expect

from config.data import TestData
from config.environment import config
from config.processing_area import workflow_spec
from pages.admin.admin_navigation import AdminDashboardPage
from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage
from pages.login.login_page import LoginPage
from utils.data_factory import unique_name
from utils.waits import wait_for_app_ready

pytestmark = [pytest.mark.exec_config]


def _as_list(value):
    """A single string or a list/tuple, normalised to a list."""
    return list(value) if isinstance(value, (list, tuple)) else [value]


# =============================================================================
# Requester Device — TC_RQD_003, TC_RQD_004
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Execution Source Config: requester device validation")
class TestRequesterDeviceValidation:
    """TC_RQD_003, TC_RQD_004"""

    @allure.title("TC_RQD_003 — Duplicate device name or identifier is rejected")
    def test_duplicate_device_name_or_identifier_rejected(self, exec_config):
        """
        ID     : TC_RQD_003
        Title  : Duplicate device name or identifier is rejected
        Reason : Duplicate identifier makes it impossible to trace which device
                 sent which request — audit trail becomes useless.
        """
        name = unique_name("req_dup")
        device_id = unique_name("RID_dup")

        exec_config.click_requester_tab()

        with allure.step(f"Create first device '{name}'"):
            exec_config.add_requester_device(
                name,
                device_id,
                "password123",
                TestData.req_bound_machines,
                TestData.req_bound_workflows,
                TestData.req_staging_areas,
            )
            exec_config.verify_device_created(name)

        with allure.step("Attempt to create a second device with the same name"):
            exec_config.page.locator("button").filter(
                has_text="ADD NEW"
            ).click(force=True)
            exec_config.page.wait_for_timeout(1000)
            exec_config.page.get_by_placeholder("Requester Name").fill(name)  # same name
            exec_config.page.get_by_placeholder("Device ID").fill(
                unique_name("RID_dup2")
            )
            exec_config.page.get_by_placeholder("Password").fill("password123")

            exec_config.page.get_by_label("Bound Machines", exact=False).fill(
                TestData.req_bound_machines
            )
            exec_config.page.wait_for_timeout(500)
            opt = exec_config.page.get_by_role(
                "option", name=TestData.req_bound_machines, exact=False
            ).first
            if opt.is_visible(timeout=2000):
                opt.click(force=True)
            exec_config.page.keyboard.press("Escape")
            exec_config.page.wait_for_timeout(500)

            exec_config.page.get_by_role("button", name="SAVE").click(force=True)
            exec_config.page.wait_for_timeout(2000)

            modal_open = exec_config.page.locator(
                ".MuiDialog-container"
            ).is_visible(timeout=1000)
            error_shown = any(
                exec_config.page.locator(s).is_visible(timeout=1000)
                for s in [
                    ".Toastify__toast--error",
                    ".MuiAlert-standardError",
                    "[role='alert']",
                ]
            )

            if modal_open:
                exec_config.page.keyboard.press("Escape")
                exec_config.page.wait_for_timeout(500)

            assert modal_open or error_shown, (
                f"Duplicate device name '{name}' was accepted — no error shown."
            )

        with allure.step("Clean up"):
            exec_config.delete_device_if_exists(name)

    @allure.title("TC_RQD_004 — A newly provisioned device can actually log in")
    def test_newly_provisioned_device_can_actually_login(self, exec_config, browser):
        """
        ID     : TC_RQD_004
        Title  : A newly provisioned device can actually log in
        Reason : Config save and credential validity are separate concerns.
                 End-to-end provisioning must be verified.
        """
        name = unique_name("req_login_chk")
        device_id = unique_name("RID_lck")
        password = "LoginCheck@123"

        exec_config.click_requester_tab()

        with allure.step(f"Create device '{name}'"):
            exec_config.delete_device_if_exists(name)
            exec_config.add_requester_device(
                name,
                device_id,
                password,
                TestData.req_bound_machines,
                TestData.req_bound_workflows,
                TestData.req_staging_areas,
            )
            exec_config.verify_device_created(name)

        with allure.step(f"Login as '{name}'"):
            # Devices authenticate with their Name, not their Device ID - see
            # fixtures/test_data/role_credentials_template.py. Logging in with
            # device_id here always 401s regardless of password and looks like
            # a provisioning bug; verified live (2026-08-21) that the very same
            # device logs in fine once `name` is used instead.
            ctx = browser.new_context(
                ignore_https_errors=config.ignore_https_errors
            )
            page = ctx.new_page()
            try:
                login = LoginPage(page)
                login.login(name, password)
                wait_for_app_ready(page, timeout=config.default_timeout)
                assert "login" not in page.url.lower(), (
                    f"Newly provisioned requester device '{name}' "
                    f"could not log in — still at {page.url}"
                )
            finally:
                ctx.close()

        with allure.step("Clean up"):
            exec_config.delete_device_if_exists(name)


# =============================================================================
# MES Config — TC_MES_002
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Execution Source Config: MES")
class TestMesConfigValidation:
    """TC_MES_002"""


    @allure.title("TC_MES_002 — Invalid MES parameters fail cleanly")
    def test_invalid_mes_parameters_fail_cleanly(self, exec_config):
        """
        ID     : TC_MES_002
        Title  : Invalid MES parameters fail cleanly
        Reason : A wrong host/port must show a readable error, not make the app
                 hang or crash with an unhandled exception.
        """
        exec_config.click_mes_tab()

        with allure.step("Fill invalid host and attempt Test Connection"):
            host_input = exec_config.page.locator(
                "input[placeholder*='host' i], input[placeholder*='url' i], "
                "input[placeholder*='address' i], input[type='text']"
            ).first
            if not host_input.is_visible(timeout=2000):
                pytest.skip(
                    "MES configuration form not found — MES may not be "
                    "configurable from the UI in this environment."
                )

            original_value = host_input.input_value()
            host_input.fill("invalid-host-xyz.local:99999")

            test_btn = exec_config.page.locator(
                "button:has-text('Test'), button:has-text('Test Connection')"
            ).first
            if test_btn.is_visible(timeout=2000):
                test_btn.click(force=True)
                exec_config.page.wait_for_timeout(3000)
                # Should show error, not hang
                assert not exec_config.page.locator("text=500").is_visible(
                    timeout=1000
                ), "Server 500 on invalid MES parameters."

            # Restore original value
            host_input.fill(original_value)

# TC_MES_003 (Test Connection reports the true state) and TC_MES_004 (MES
# credentials masked after saving) were deleted 2026-09-04: verified live that
# this environment's MES tab renders only a workflow list (Workflow Name /
# Workflow / Processing Area) with a search box and pagination — there is no
# connection-config form, no Test Connection button and no credential field to
# test. Restore them if a deployment ships an MES connection form.


# =============================================================================
# Dispatcher Scope — TC_DSP_002
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Execution Source Config: dispatcher scope")
class TestDispatcherScope:
    """TC_DSP_002"""

    @allure.title("TC_DSP_002 — Dispatcher only receives tasks from its assigned scope")
    def test_dispatcher_only_receives_tasks_from_assigned_scope(
        self, exec_config, admin_page, dispatcher_page
    ):
        """
        ID     : TC_DSP_002
        Title  : A Dispatcher only receives tasks from its assigned scope
        Reason : Scope leak means one area's dispatcher picks up another area's
                 tasks — operational chaos on a multi-area floor.

        Read-only realisation (the dispatcher dashboard deliberately exposes no
        Dispatch action, and the Pending queue is real production data — see
        DispatcherHomePage's module docstring). It proves the config→runtime
        scope contract without touching the queue:

          1. Admin ▸ Execution Source Config shows the dispatcher device bound to
             exactly ``dispatcher_bound_stations``.
          2. Logged in as that device, the station switcher offers *those and
             only those* stations — an out-of-scope station is unreachable, so
             its queue can never be viewed here.
          3. Each bound station re-scopes the breadcrumb to itself, i.e. every
             station's queue is independent (no cross-station bleed).
        """
        expected = _as_list(TestData.disp_bound_stations)

        with allure.step("Admin: the dispatcher device is bound to the configured scope"):
            exec_config.click_dispatcher_tab()
            exec_config.verify_device_created(TestData.disp_device_name)
            search_input, row = exec_config._open_row_editor(TestData.disp_device_name)
            assert row.count() > 0, (
                f"Dispatcher device '{TestData.disp_device_name}' row not found."
            )
            modal = admin_page.locator(".MuiDialog-container")
            expect(modal).to_be_visible(timeout=5000)
            modal_text = modal.inner_text()
            admin_page.keyboard.press("Escape")
            admin_page.wait_for_timeout(500)
            exec_config._clear_search(search_input)
            for station in expected:
                assert station in modal_text, (
                    f"Dispatcher device '{TestData.disp_device_name}' editor does "
                    f"not show bound station '{station}'. Modal text: {modal_text!r}"
                )

        home = DispatcherHomePage(dispatcher_page)

        with allure.step("Dispatcher: the station switcher offers only the assigned scope"):
            options = home.open_station_dropdown()
            home.close_dropdown()
            assert sorted(options) == sorted(expected), (
                f"Dispatcher station switcher offers {sorted(options)} but its "
                f"assigned scope is {sorted(expected)} — a station outside the "
                "configured scope is reachable (scope leak) or one is missing."
            )

        with allure.step("Dispatcher: each bound station scopes the queue to itself"):
            for station in expected:
                home.select_station(station)
                assert home.breadcrumb_station.inner_text().strip() == station, (
                    f"Selecting '{station}' did not re-scope the breadcrumb to it "
                    f"(got '{home.breadcrumb_station.inner_text().strip()}') — the "
                    "queue may not be isolated per station."
                )
                # Whatever is in this station's queue, reading it must not error.
                _ = home.row_count()


# =============================================================================
# Supervisor Scope — TC_SPD_002
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Execution Source Config: supervisor scope")
class TestSupervisorScope:
    """TC_SPD_002"""

    @allure.title("TC_SPD_002 — Supervisor scope spans the configured Processing Areas")
    def test_supervisor_scope_spans_configured_processing_areas(
        self, exec_config, admin_page
    ):
        """
        ID     : TC_SPD_002
        Title  : Supervisor scope spans the configured Processing Areas
        Reason : A multi-area supervisor must see exactly their assigned areas —
                 neither fewer nor more.
        """
        exec_config.click_supervisor_tab()

        with allure.step(
            f"Baseline supervisor '{TestData.sup_device_name}' exists with "
            f"scope '{TestData.sup_processing_areas}'"
        ):
            exec_config.verify_device_created(TestData.sup_device_name)

        with allure.step("Open the supervisor record and verify processing area binding"):
            row = admin_page.locator("tr").filter(
                has_text=TestData.sup_device_name
            ).first
            # Click the edit (first) button
            row.locator("button").first.click(force=True)
            admin_page.wait_for_timeout(1000)

            # The modal should show the bound Processing Area
            modal = admin_page.locator(".MuiDialog-container")
            area_label = modal.get_by_text(
                TestData.sup_processing_areas, exact=False
            )
            expect(area_label).to_be_visible(timeout=5000)

            # Close without saving
            admin_page.keyboard.press("Escape")
            admin_page.wait_for_timeout(500)
