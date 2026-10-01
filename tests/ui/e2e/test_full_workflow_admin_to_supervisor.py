"""End-to-end: admin builds the chain, then every role authenticates against it.

This is deliberately the only e2e module. Cross-role tests are the slowest and
most brittle in the suite; they exist to catch integration breaks that the
isolated role suites cannot see, not to re-verify what those suites already
cover.

What the first test proves that the role suites do not: that one Processing
Area, its workflow, and the three device records bound to it are mutually
consistent and usable **in the same run** - a requester bound to a workflow
that was deleted, or a supervisor bound to a renamed area, fails here and
nowhere else.

The second test (added once the Dispatcher page object grew past a stub)
closes the loop the first one stops short of: it actually places a request as
the requester, dispatches that exact request, and confirms in **Fleet
Manager itself** (a separate app at 192.168.6.12 - see
pages/fleet_manager/manage_trips_page.py) that a real trip was created.
That is the only way to prove a dispatch had its real physical effect -
AtiFlow's own UI merely stops showing "Dispatch" on the row.

This module runs against its own isolated data: a `test_e2e` Processing Area,
the four `*_e2e` workflows and `requester_e2e` / `dispatcher_e2e` /
`supervisor_e2e` device records - all the `[e2e_*]` tables in
config/test_data.toml, NOT the shared `test_9707` / `requester_45` baseline
the role suites use. The root conftest.py defines `e2e_provisioned_baseline`
and the three `e2e_seeded_*` fixtures to build that world from scratch (delete and
recreate) every run, so `pytest tests/ui/e2e/` starts from a clean area and a
later `pytest -m requester` never finds its baseline deleted. Real Fleet
Manager values (station ids, fleet "test", AH_stage, the live SKU) are shared
verbatim - only names AtiFlow itself creates carry the `_e2e` suffix.

Both tests only ever mutate records/requests this run created itself. See
pages/dashboards/dispatcher_dashboard_page.py's module docstring for why that
page object still exposes no reusable "click Dispatch" method - the guarded
click lives inline in the second test below, next to the pre-flight checks
that justify it.
"""

import re
from datetime import datetime, timedelta

import allure
import pytest
from playwright.sync_api import expect

from config.data import TestData
from config.environment import config
from config.processing_area import e2e_workflow_spec, e2e_workflow_specs
from pages.admin.admin_navigation import AdminDashboardPage
from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage
from pages.dashboards.requester_dashboard_page import RequesterHomePage
from pages.dashboards.supervisor_dashboard_page import SupervisorHomePage
from pages.fleet_manager.manage_trips_page import FleetManagerPage

pytestmark = [pytest.mark.e2e]


def _resolve_station(station_type, station_value):
    """A workflow's pickup/drop is either a literal station id ("static") or
    an [e2e_station_mapping] label ("mapping") that must be resolved to the
    real Fleet Manager station id."""
    if station_type != "mapping":
        return station_value
    if station_value == TestData.e2e_station_mapping_name:
        return TestData.e2e_station_id
    if station_value == TestData.e2e_station_mapping_name_2:
        return TestData.e2e_station_id_2
    return station_value  # unresolved - surfaces as a clear FM mismatch


def _bound_stations():
    value = TestData.e2e_disp_bound_stations
    return list(value) if isinstance(value, (list, tuple)) else [value]


@allure.feature("End to end")
@allure.story("Admin to supervisor chain")
class TestFullWorkflowAdminToSupervisor:

    @allure.title("Admin-built workflow and devices are consistent across all three roles")
    def test_admin_setup_is_usable_by_every_role(
        self, admin_page, e2e_requester_page, e2e_dispatcher_page, e2e_supervisor_page
    ):
        workflow = e2e_workflow_spec()

        with allure.step("Admin: the workflow the requester binds to exists"):
            dashboard = AdminDashboardPage(admin_page)
            dashboard.navigate_to_existing_area(TestData.e2e_processing_area_name)
            dashboard.go_to_workflow()
            expect(
                admin_page.locator("tr").filter(has_text=workflow.name).first
            ).to_be_visible(timeout=10000)

        with allure.step("Admin: all three device records are present"):
            dashboard.navigate_to_execution_source_config()
            for tab, device in (
                (dashboard.click_requester_tab, TestData.e2e_req_device_name),
                (dashboard.click_dispatcher_tab, TestData.e2e_disp_device_name),
                (dashboard.click_supervisor_tab, TestData.e2e_sup_device_name),
            ):
                tab()
                dashboard.verify_device_created(device)

        with allure.step("Requester: authenticates and shows its bound configuration"):
            requester_home = RequesterHomePage(e2e_requester_page)
            assert "login" not in e2e_requester_page.url.lower(), (
                f"Requester bound to workflow '{workflow.name}' could not authenticate; "
                f"still at {e2e_requester_page.url}"
            )

            assert TestData.e2e_req_bound_machines in requester_home.bound_machine_text(), (
                f"Requester dashboard does not show bound machine "
                f"'{TestData.e2e_req_bound_machines}' - the device record admin just "
                f"created and the dashboard it renders are out of sync."
            )

            # The requester device is bound to several workflows (config
            # [[e2e_workflow]]) and the sidebar dropdown defaults to whichever
            # the app picks. Assert the shown value is *one of* the configured
            # names, not specifically the first one (see the "Workflow dropdown
            # has drifted" note in the project notes).
            shown_workflow = requester_home.bound_workflow_text()
            configured_names = [w.name for w in e2e_workflow_specs()] or [workflow.name]
            assert any(name in shown_workflow for name in configured_names), (
                f"Requester dashboard shows bound workflow {shown_workflow!r}, "
                f"which is none of the configured bound workflows "
                f"{configured_names} that admin created and bound in this run."
            )

            for tab in (
                requester_home.requested_tab, requester_home.in_progress_tab,
                requester_home.completed_tab, requester_home.cancelled_tab,
                requester_home.all_tab,
            ):
                assert tab.is_visible(timeout=5000)

        with allure.step("Dispatcher: authenticates against its bound station"):
            DispatcherHomePage(e2e_dispatcher_page)
            assert "login" not in e2e_dispatcher_page.url.lower(), (
                f"Dispatcher could not authenticate; still at {e2e_dispatcher_page.url}"
            )

        with allure.step("Supervisor: authenticates against its bound Processing Area"):
            SupervisorHomePage(e2e_supervisor_page)
            assert "login" not in e2e_supervisor_page.url.lower(), (
                f"Supervisor bound to '{TestData.e2e_sup_processing_areas}' could not "
                f"authenticate; still at {e2e_supervisor_page.url}"
            )

    @allure.title("A dispatched request creates a real trip in Fleet Manager")
    def test_request_flows_from_requester_through_dispatch_to_a_fleet_manager_trip(
        self, browser, e2e_requester_page, e2e_dispatcher_page
    ):
        """
        Admin build + per-role auth is already proven by the test above (and
        by this test's own fixture chain - e2e_requester_page/e2e_dispatcher_page
        both depend on seeded_requester/seeded_dispatcher, which create the
        device records via the admin UI). This test starts from there and
        goes all the way to Fleet Manager:

            requester raises a real request
              -> dispatcher dispatches THAT exact request
              -> Fleet Manager's Manage Trips grid shows a matching trip

        Safety: the dispatcher click only ever targets the request id this
        test raised moments earlier, after verifying the row's material and
        status. Fleet Manager is read-only throughout - it only searches
        Manage Trips, never cancels or edits a row.
        """
        req_home = RequesterHomePage(e2e_requester_page)
        sub_sku = TestData.req_request_sub_sku_code

        with allure.step("Resolve the requester's *current* bound workflow to real station ids"):
            current_workflow_name = req_home.bound_workflow_text()
            spec = next(
                (w for w in e2e_workflow_specs() if w.name == current_workflow_name), None
            )
            assert spec, (
                f"Sidebar shows workflow {current_workflow_name!r}, which is not one "
                f"of the workflows configured in config/test_data.toml [[e2e_workflow]] "
                f"- cannot resolve pickup/drop stations to check Fleet Manager against."
            )
            pickup_station = _resolve_station(spec.pickup_type, spec.pickup_station)
            drop_station = _resolve_station(spec.drop_type, spec.drop_station)
            allure.attach(f"{pickup_station} -> {drop_station}", "expected FM route")

        with allure.step(f"Requester raises a 1-unit request for {sub_sku}"):
            # Buffered a minute back to absorb clock skew between this
            # machine and the Fleet Manager server when comparing timestamps.
            submitted_at = datetime.now() - timedelta(minutes=1)
            req_home.open_make_new_request()
            req_home.select_sku(TestData.req_request_sku_code)
            if req_home.sub_sku_available_count(sub_sku) < 1:
                pytest.skip(
                    f"{sub_sku} shows 0 Available right now - no live stock to raise "
                    f"a request with, so there is nothing to dispatch."
                )
            req_home.add_sub_sku_item(sub_sku, count=1)
            req_home.click_next()
            assert e2e_requester_page.get_by_text(
                "Request Summary", exact=True
            ).first.is_visible(timeout=5000)
            req_home.click_confirm_and_wait(timeout=20000)

        with allure.step("Capture the new request's id from Request History"):
            req_home.click_home()
            e2e_requester_page.locator("tbody tr").first.wait_for(state="visible", timeout=15000)
            req_home.set_history_sort("Newest First")
            page1_text = " ".join(req_home.request_history_row_texts())
            nums = [int(n) for n in re.findall(r"Req-(\d+)", page1_text)]
            assert nums, "No Req-NNN rows in Request History after submitting"
            request_id = str(max(nums))
            allure.attach(request_id, "requester_request_id")

        disp_home = DispatcherHomePage(e2e_dispatcher_page)
        with allure.step(f"Dispatcher: locate request {request_id} in a bound station's Pending queue"):
            # A just-submitted request can take a couple of seconds to
            # propagate into the dispatcher's Pending queue after the
            # requester's confirm call returns - confirmed live 2026-09-08:
            # a single sweep of the bound stations right after submitting
            # missed a request that appeared on the very next sweep. Sweep
            # more than once before giving up, the same tolerance the
            # "leaves PENDING tab" step below already uses.
            station = None
            for sweep in range(3):
                for candidate in _bound_stations():
                    disp_home.select_station(candidate)
                    disp_home.select_tab("Pending")
                    disp_home.set_rows_per_page(50)
                    if int(request_id) in disp_home.row_ids():
                        station = candidate
                        break
                if station:
                    break
                e2e_dispatcher_page.wait_for_timeout(2000)
            assert station, (
                f"Request {request_id} raised by the requester never appeared in the "
                f"Pending queue of any bound station {_bound_stations()} after 3 "
                f"sweeps. Not dispatching anything."
            )

        with allure.step(f"Pre-flight checks on row {request_id} before dispatching"):
            assert disp_home.row_status(request_id) == "Awaiting Dispatch"
            assert sub_sku in disp_home.row_material(request_id), (
                f"Row {request_id} material {disp_home.row_material(request_id)!r} does "
                f"not contain the submitted sub-SKU {sub_sku!r} - refusing to dispatch "
                f"a row that isn't the one this test created."
            )
            assert disp_home.has_dispatch_action(request_id)

        with allure.step(f"Dispatch request {request_id} (tasks a real AMR)"):
            e2e_dispatcher_page.locator(f"#approvals-dispatch-decision-cell-{request_id}").click()
            e2e_dispatcher_page.wait_for_timeout(1500)
            # Confirmed live 2026-09-08: for a Manual-confirmation workflow,
            # dispatching opens an "Approve Request" dialog
            # (#approve-request-dialog-*) that PRE-SELECTS its one eligible
            # physical item/trolley itself ("Pre-selected by system", quota
            # already met) - "Confirm Approval" enables on its own once that
            # happens. Never touch the item checkboxes: every OTHER listed
            # item is visually disabled but not necessarily `disabled` at the
            # DOM level, so force-checking one raises "Clicking the checkbox
            # did not change its state" (the app silently blocks it) instead
            # of doing anything useful - the system has already picked the
            # only valid item for us. Not every dispatch shows this dialog (a
            # request can dispatch immediately when the system auto-assigns);
            # if it does appear but "Confirm Approval" never enables on its
            # own (no eligible physical stock/trolley at all right now - a
            # real inventory-state condition this suite cannot manufacture,
            # not a code defect), back out via "Cancel Request" and skip with
            # a clear reason - same pattern as the existing "0 Available"
            # stock skips.
            dialog = e2e_dispatcher_page.locator(".MuiDialog-container")
            if dialog.count() and dialog.is_visible():
                confirm_btn = e2e_dispatcher_page.locator("#approve-request-dialog-confirm-btn")

                confirmed = False
                for _ in range(8):
                    if confirm_btn.is_enabled():
                        confirm_btn.click()
                        confirmed = True
                        break
                    e2e_dispatcher_page.wait_for_timeout(1000)

                if not confirmed:
                    cancel_btn = e2e_dispatcher_page.locator("#approve-request-dialog-cancel-btn")
                    (
                        cancel_btn if cancel_btn.count()
                        else e2e_dispatcher_page.locator("#approve-request-dialog-close-icon-btn")
                    ).click()
                    e2e_dispatcher_page.wait_for_timeout(1000)
                    pytest.skip(
                        f"Approve Request dialog for {request_id} never let 'Confirm "
                        f"Approval' enable itself - no eligible physical item/trolley "
                        f"to complete a real dispatch with right now."
                    )

                # Its backdrop blocks every later click (same shape as Fleet
                # Manager's alert modal) until it is fully gone - wait for
                # that rather than a fixed sleep.
                try:
                    dialog.wait_for(state="hidden", timeout=8000)
                except Exception:
                    pass
                e2e_dispatcher_page.wait_for_timeout(800)

        with allure.step(f"Request {request_id} leaves the dispatcher's PENDING tab"):
            # Confirmed live 2026-08-28: the dispatch itself succeeds
            # immediately server-side, but the Pending grid can still show
            # the stale row for a couple of seconds after the click - so
            # this polls instead of checking once.
            left_pending = False
            for _ in range(8):
                disp_home.select_tab("Pending")
                disp_home.set_rows_per_page(50)
                if int(request_id) not in disp_home.row_ids():
                    left_pending = True
                    break
                e2e_dispatcher_page.wait_for_timeout(1500)
            assert left_pending, f"{request_id} is still in the PENDING tab after dispatching"

        fm_context = browser.new_context(ignore_https_errors=config.ignore_https_errors)
        try:
            fm = FleetManagerPage(fm_context.new_page())
            with allure.step(f"Fleet Manager: log in and switch to the '{TestData.staging_area_bound_fleet}' fleet"):
                fm.login()
                fm.select_fleet(TestData.staging_area_bound_fleet)

            with allure.step(f"Fleet Manager: Manage Trips shows {pickup_station} -> {drop_station}, booked just now"):
                fm.open_manage_trips()
                trip = fm.find_trip(pickup_station, drop_station, since=submitted_at)
                assert trip, (
                    f"No Fleet Manager trip {pickup_station} -> {drop_station} booked "
                    f"since {submitted_at:%H:%M:%S} was found in Manage Trips (fleet "
                    f"'{TestData.staging_area_bound_fleet}') after dispatching request "
                    f"{request_id}. The dispatch did not create a real trip."
                )
                allure.attach(str(trip), "fleet_manager_trip_row")
        finally:
            fm_context.close()
