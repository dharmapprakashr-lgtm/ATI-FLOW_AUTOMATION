"""Unified pytest configuration for the AtiFlow automation suite.

All hooks and fixtures live here. Shared role fixtures use the standard test
configuration; explicit e2e_* fixtures use the isolated [e2e_*] configuration
and separate in-memory authentication states. Both can run in the same session.
"""

# Set bytecode routing before importing any project modules. Child Python
# processes inherit the same destination through PYTHONPYCACHEPREFIX.
import os
import sys
from pathlib import Path

_BYTECODE_CACHE = Path(__file__).resolve().parent / ".cache" / "pycache"
sys.pycache_prefix = str(_BYTECODE_CACHE)
os.environ["PYTHONPYCACHEPREFIX"] = str(_BYTECODE_CACHE)

from playwright.sync_api import expect
from config.processing_area import (
    e2e_container_spec, e2e_machine_specs, e2e_material_spec,
    e2e_station_names, e2e_workflow_specs,
)
from config.credentials import (
    e2e_dispatcher_credentials, e2e_requester_credentials, e2e_supervisor_credentials,
)
from utils.report_paths import PDF_PATH, ensure_dirs

import base64
import time
import warnings
from datetime import datetime

import pytest

pytest_plugins = ["pytester"]

from config.processing_area import (
    container_spec,
    machine_specs,
    material_spec,
    station_names,
    validate_station_names,
    workflow_spec,
)
from config.credentials import (
    dispatcher_credentials,
    requester_credentials,
    supervisor_credentials,
)
from config.data import TestData
from config.environment import config
from pages.admin.admin_navigation import AdminDashboardPage
from pages.admin.processing_area.create_new_area_page import ProcessingAreaPage
from pages.login.login_page import LoginPage
from utils.logger import get_logger
from utils.pdf_report import ResultCollector
from utils.pdf_report import build as build_pdf_report
from utils.report_paths import (
    SCREENSHOT_DIR,
    cleanup_work_dir,
    keep_runs,
    prune_old_reports,
)
from utils.waits import dismiss_stuck_modal, table_row_exists, wait_for_app_ready

log = get_logger("conftest")

ROOT_DIR = Path(__file__).resolve().parent

#: Suites run in this order regardless of alphabetical collection.
#:
#: The order follows the master test-case plan and the dependency chain:
#:
#:   Part 1  – Login gate (2 tests: valid + invalid)
#:   Part 3  – Admin › Processing Area
#:               test_01_material_container  → create the baseline PA, material, container
#:               test_02_machine_name        → add machines
#:               test_03_station_mapping     → add pickup + drop mappings
#:               test_04_workflow            → build the workflow
#:               test_05_area_lifecycle      → edit/delete lifecycle (throwaway names)
#:               test_06_staging_area        → staging area CRUD
#:               test_07_wip_inventory       → WIP inventory CRUD
#:               test_08_workstation         → workstation CRUD
#:   Part 4  – Execution Source Config
#:               Creates the requester, dispatcher and supervisor device records
#:               that every downstream test and fixture depends on.
#:   Part 2  – Access Control (AFTER Part 4 so the device records exist when
#:               the role fixtures seed requester/dispatcher/supervisor pages)
#:   Part 5  – Settings
#:   Part 6  – Dashboards — role pages log in with the credentials from Part 4
#:   Part 7  – End-to-End
#:   Part 8  – Security
#:   Part 9  – Non-Functional Requirements
#:   Part 10 – UI & Navigation
#:
#: list.sort() is stable, so within a directory the numeric filename prefixes
#: (test_01_…, test_02_…) still govern the intra-directory order.
SUITE_ORDER = (
    # ── Part 1: Login gate ────────────────────────────────────────────────
    "tests/common/test_login",
    "tests/common/test_application_version",

    # ── Part 3: Admin › Processing Area ──────────────────────────────────
    # (runs before Part 4 because device records bind to workflow + machines)
    "tests/ui/admin/processing_area",

    # ── Part 4: Execution Source Config ──────────────────────────────────
    # Creates requester / dispatcher / supervisor device records.
    "tests/ui/admin/execution_source_config",

    # Throwaway entity lifecycle checks, after shared admin configuration.
    "tests/ui/crud",

    # ── Part 2: Access Control ────────────────────────────────────────────
    # Placed here so device records (Part 4) already exist when the role
    # fixtures seed and authenticate each device page.
    "tests/common/test_access_control",

    # Settings runs as processing_area/test_18_setting.py above.

    # ── Part 6: Dashboards ────────────────────────────────────────────────
    # requester_page / dispatcher_page / supervisor_page log in with the
    # device credentials created in Part 4.
    "tests/ui/requester",
    "tests/ui/dispatcher",
    "tests/ui/supervisor",
    "tests/common/test_dashboard_common",

    # ── Part 7: End-to-End ────────────────────────────────────────────────
    "tests/ui/e2e",

    # ── Part 8: Security ──────────────────────────────────────────────────
    "tests/common/test_security",

    # ── Part 9: Non-Functional Requirements ──────────────────────────────
    "tests/common/test_nfr",

    # ── Part 10: UI & Navigation ──────────────────────────────────────────
    "tests/common/test_ui_navigation",
)


# ── Browser configuration ─────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "ignore_https_errors": config.ignore_https_errors}


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, pytestconfig):
    headless = False if pytestconfig.getoption("headed", default=False) else config.headless
    return {**browser_type_launch_args, "headless": headless}


# ── Environment sanity ────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def verify_environment(request):
    """Fail fast on missing config, and warn about test data that cannot work."""
    if not any(any(part in str(item.path).replace(os.sep, "/") for part in ("tests/ui/", "tests/common/")) for item in request.session.items):
        return
    config.require_admin_credentials()
    log.info("Running against %s (TEST_ENV=%s)", config.base_url, config.env)

    station_warning = validate_station_names()
    if station_warning:
        warnings.warn(station_warning, stacklevel=1)


# ── Authentication ────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def save_login_state(browser):
    """Return ``save(role, username, password) -> storage-state dictionary``.

    Logs in through the UI once and keeps the resulting state in memory.
    No cookies or tokens are written to authentication files. Role
    fixtures call this after ensuring their device record exists.
    """

    def _save(role, username, password):
        context = browser.new_context(ignore_https_errors=config.ignore_https_errors)
        page = context.new_page()
        try:
            LoginPage(page).login(username, password)
            wait_for_app_ready(page, timeout=config.default_timeout)
            state = context.storage_state()
            session_data = page.evaluate('''() => {
                let data = {};
                try {
                    for (let i = 0; i < sessionStorage.length; i++) {
                        let key = sessionStorage.key(i);
                        data[key] = sessionStorage.getItem(key);
                    }
                } catch (e) {}
                return data;
            }''')
            state["session_storage_data"] = session_data
            log.info("Cached %s authentication state in memory", role)
        finally:
            context.close()
        return state

    return _save


@pytest.fixture
def authenticated_page(browser):
    """Return ``open(state, username, password) -> Page``.

    Restores the in-memory session, then confirms the app accepted it. If the page
    is still on login, falls back to a full UI login so the test can proceed.
    """
    contexts = []

    def _open(state, username, password, role="role"):
        context = browser.new_context(
            storage_state=state,
            ignore_https_errors=config.ignore_https_errors,
        )
        contexts.append(context)
        page = context.new_page()

        # Navigate once to establish origin so sessionStorage can be written
        page.goto(config.app_url, wait_until="domcontentloaded")
        
        if "session_storage_data" in state:
            page.evaluate(f'''(data) => {{
                for (const key in data) {{
                    window.sessionStorage.setItem(key, data[key]);
                }}
            }}''', state["session_storage_data"])
            # Reload so the app picks up the injected token
            page.reload(wait_until="domcontentloaded")
            
        wait_for_app_ready(page, timeout=config.default_timeout, allow_login=True)

        if "login" in page.url.lower():
            warnings.warn(
                f"Restored {role} storage_state did not authenticate (still on login). "
                f"Falling back to a UI login for every {role} test. This app most likely "
                f"keeps its token in sessionStorage, which storage_state cannot persist.",
                stacklevel=1,
            )
            LoginPage(page).login(username, password)
            wait_for_app_ready(page, timeout=config.default_timeout)

        return page

    yield _open

    for context in contexts:
        context.close()


@pytest.fixture(scope="session")
def admin_state(save_login_state):
    return save_login_state("admin", config.admin_user, config.admin_pass)


@pytest.fixture
def admin_page(admin_state, authenticated_page):
    """Pre-authenticated admin page. Every admin test asks for this."""
    return authenticated_page(admin_state, config.admin_user, config.admin_pass, role="admin")


@pytest.fixture
def pa_page(admin_page):
    """Processing Area page object on the authenticated admin session.

    Available to admin and common suites, including security and navigation tests.
    """
    return ProcessingAreaPage(admin_page)


@pytest.fixture
def mes_page(page):
    """MES uses a real user account rather than a device record."""
    LoginPage(page).login(config.mes_user, config.mes_pass)
    wait_for_app_ready(page, timeout=config.default_timeout)
    yield page


# ── Role seeding ──────────────────────────────────────────────────────────────
#
# Each role follows the same three-stage chain:
#   seeded_<role>   session  create the device record via the admin UI
#   <role>_state    session  log in once as that device, dump storage state
#   <role>_page     function open a context from that state
#
# The seeding stage is what lets ``pytest -m requester`` run green against an
# environment where the admin suite has not run. It is idempotent: the record
# is deleted and recreated, so a stale password or binding cannot make the
# login fail in a way that looks like an app bug.

def _admin_context(browser):
    """Open a short-lived authenticated admin context for seeding work."""
    context = browser.new_context(ignore_https_errors=config.ignore_https_errors)
    page = context.new_page()
    LoginPage(page).login(config.admin_user, config.admin_pass)
    wait_for_app_ready(page, timeout=config.default_timeout)
    return context, page


# ── Baseline Processing Area ──────────────────────────────────────────────────

def _provision_baseline(
    page,
    *,
    rebuild=False,
    area_name=None,
    area_description=None,
    material=None,
    container=None,
    machines=None,
    mapping_names=None,
    mapping_station_ids=None,
    workflows=None,
    supervisor_scope_areas=None,
):
    """Build the config-defined Processing Area and everything the device
    records bind to, on an already-authenticated admin ``page``.

    Builds from ``config/test_data.toml`` via the ``*_spec()`` builders —
    nothing is hard-coded here:

        Processing Area   [processing_area]
        Material          [material]
        Container         [container]
        Machine Names     [machine_name] (production + consumption)
        Station Mappings  [station_mapping] (pickup + drop)
        Workflow          [[workflow]] (the first entry only — the admin
                          Processing Area suite's test_10_workflow.py builds
                          the rest; ``the E2E fixtures below`` passes the
                          full [[e2e_workflow]] list since it runs alone)
        + any Processing Area the supervisor device binds to
          ([devices] supervisor_processing_areas) that differs from the above —
          created bare, just so its checkbox renders in the device form.

    Every ``*`` keyword defaults to ``None`` → the ``[…]`` section shown above.
    ``the E2E fixtures below`` passes the ``[e2e_*]`` values instead so an
    e2e run provisions an isolated ``test_e2e`` area without touching this one.

    ``rebuild=False`` (default) is **create-if-absent**: every entity is added
    only when its row is missing, so an existing baseline is reused as-is.

    ``rebuild=True`` deletes the Processing Area first, so the material,
    container, machines, station mappings and workflow are all built fresh.
    This is the same delete-and-recreate ``test_01_material_container.py`` does
    at the top of a full ``SUITE_ORDER`` run; the e2e suite asks for it (see
    ``the E2E fixtures below``) so its cross-role check never runs against a
    stale, half-built area a previous run left behind. The supervisor-scope
    extra area(s) stay create-if-absent even on a rebuild — they are only
    checkbox placeholders and may be pre-existing areas outside this suite.

    The **Staging Area** the devices also bind to is Fleet-Manager-provisioned
    and cannot be built from this app — it must already exist.
    """
    area_name = area_name or TestData.processing_area_name
    area_description = area_description or TestData.processing_area_description
    material = material or material_spec()
    container = container or container_spec()
    machines = machines or machine_specs()
    mapping_names = mapping_names or station_names()
    mapping_station_ids = mapping_station_ids or (TestData.station_id, TestData.station_id_2)
    workflows = workflows or (workflow_spec(),)
    if supervisor_scope_areas is None:
        supervisor_scope_areas = TestData.sup_processing_areas

    pa = ProcessingAreaPage(page)
    dashboard = AdminDashboardPage(page)

    def row_exists(name):
        return table_row_exists(page, name)

    if rebuild:
        # Clear whatever the previous run left inside the area first. The
        # create-if-absent blocks below then all fire, giving a fresh build.
        pa.delete_processing_area(area_name)

    pa.create_processing_area(area_name, area_description)

    pa.go_to_materials()
    if not row_exists(material.type_name):
        dashboard.add_material(
            material.type_name,
            material.production_unit,
            material.pre_proc_time,
            material.max_qty,
            material.prefix,
        )

    pa.go_to_containers()
    if not row_exists(container.container_type):
        dashboard.add_container(
            container.container_type,
            container.sub_type,
            container.length,
            container.width,
            container.height,
            container.hitch_length,
            container.qty,
        )

    pa.go_to_machine_names()
    for machine in machines:
        if not row_exists(machine.name):
            pa.add_machine_name(machine.name, machine.production_type)

    pickup_name, drop_name = mapping_names
    pa.go_to_station_mapping()
    for mapping_name, station_id, index in (
        (pickup_name, mapping_station_ids[0], 0),
        (drop_name, mapping_station_ids[1], 1),
    ):
        if not row_exists(mapping_name):
            pa.add_station_mapping(mapping_name, station_id=station_id, station_index=index)

    pa.go_to_workflow()
    for workflow in workflows:
        if not row_exists(workflow.name):
            pa.add_workflow(
                workflow.name,
                pickup_station=workflow.pickup_station,
                drop_station=workflow.drop_station,
                pickup_type=workflow.pickup_type,
                drop_type=workflow.drop_type,
                point_station_mode=workflow.point_station_mode,
                staging_area_mode=workflow.staging_area_mode,
            )

    # The supervisor device binds to its own Processing Area(s) by checkbox
    # (config [devices] supervisor_processing_areas), which may differ from
    # [processing_area] name above. Ensure each such area at least exists so
    # its checkbox renders in the Supervisor Device form — the supervisor
    # dashboard only *reads* whatever the area contains, so a bare area is
    # enough. (If the config value is a legacy area no longer present live,
    # this is what recreates it.)
    sup_areas = supervisor_scope_areas
    for extra_area in ([sup_areas] if isinstance(sup_areas, str) else sup_areas):
        if extra_area and extra_area != area_name:
            pa.create_processing_area(
                extra_area,
                f"{area_description} (supervisor scope)",
            )

    log.info(
        "Provisioned baseline Processing Area '%s' (rebuild=%s; + material '%s', "
        "container '%s', machines %s, mappings %s/%s, workflow(s) %s; "
        "supervisor-scope area(s): %s)",
        area_name, rebuild, material.type_name,
        container.container_type, [m.name for m in machines],
        pickup_name, drop_name, [w.name for w in workflows], sup_areas,
    )
    return area_name


@pytest.fixture(scope="session")
def provisioned_baseline(browser):
    """Ensure the config-defined Processing Area and everything the device
    records bind to exist on the target app, before any role is seeded.

    ``seeded_requester`` / ``seeded_dispatcher`` / ``seeded_supervisor`` all
    depend on this, so ``pytest -m e2e`` (or ``-m requester`` / ``-m
    supervisor``) passes standalone against an app where the admin suite has
    not run this session, instead of failing on a missing area.

    create-if-absent by default. Set ``REBUILD_BASELINE=1`` to force the
    delete-and-recreate path for a shared baseline run. E2E uses its own
    e2e_provisioned_baseline fixture and always rebuilds its isolated area.
    """
    rebuild = os.environ.get("REBUILD_BASELINE", "").strip().lower() in ("1", "true", "yes")
    context, page = _admin_context(browser)
    try:
        _provision_baseline(page, rebuild=rebuild)
    finally:
        context.close()
    return TestData.processing_area_name


# ── Requester ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def seeded_requester(browser, provisioned_baseline):
    """Ensure the requester device exists; return its credentials."""
    credentials = requester_credentials()
    context, page = _admin_context(browser)
    try:
        dashboard = AdminDashboardPage(page)
        dashboard.navigate_to_execution_source_config()
        dashboard.click_requester_tab()
        dashboard.delete_device_if_exists(credentials.name)
        dashboard.add_requester_device(
            credentials.name,
            credentials.device_id,
            credentials.password,
            TestData.req_bound_machines,
            TestData.req_bound_workflows,
            TestData.req_staging_areas,
        )
        log.info("Seeded requester device '%s'", credentials.name)
    finally:
        context.close()
    return credentials


@pytest.fixture(scope="session")
def requester_state(seeded_requester, save_login_state):
    username, password = seeded_requester.as_login()
    return save_login_state("requester", username, password)


@pytest.fixture
def requester_page(requester_state, seeded_requester, authenticated_page):
    username, password = seeded_requester.as_login()
    return authenticated_page(requester_state, username, password, role="requester")


# ── Dispatcher ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def seeded_dispatcher(browser, provisioned_baseline):
    """Ensure the dispatcher device exists; return its credentials."""
    credentials = dispatcher_credentials()
    context, page = _admin_context(browser)
    try:
        dashboard = AdminDashboardPage(page)
        dashboard.navigate_to_execution_source_config()
        dashboard.click_dispatcher_tab()
        dashboard.delete_device_if_exists(credentials.name)
        dashboard.add_dispatcher_device(
            credentials.name,
            credentials.device_id,
            credentials.password,
            TestData.disp_bound_stations,
            TestData.disp_staging_areas,
        )
        log.info("Seeded dispatcher device '%s'", credentials.name)
    finally:
        context.close()
    return credentials


@pytest.fixture(scope="session")
def dispatcher_state(seeded_dispatcher, save_login_state):
    username, password = seeded_dispatcher.as_login()
    return save_login_state("dispatcher", username, password)


@pytest.fixture
def dispatcher_page(dispatcher_state, seeded_dispatcher, authenticated_page):
    username, password = seeded_dispatcher.as_login()
    return authenticated_page(dispatcher_state, username, password, role="dispatcher")


# ── Supervisor ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def seeded_supervisor(browser, provisioned_baseline):
    """Ensure the supervisor device exists; return its credentials.

    The supervisor binds to a Processing Area by checkbox; ``provisioned_baseline``
    guarantees that area (and its material/container/machines/mappings/workflow)
    exists first, all from ``config/test_data.toml``.
    """
    credentials = supervisor_credentials()
    context, page = _admin_context(browser)
    try:
        dashboard = AdminDashboardPage(page)
        dashboard.navigate_to_execution_source_config()
        dashboard.click_supervisor_tab()
        dashboard.delete_device_if_exists(credentials.name)
        dashboard.add_supervisor_device(
            credentials.name,
            credentials.device_id,
            credentials.password,
            TestData.sup_staging_areas,
            TestData.sup_processing_areas,
        )
        log.info("Seeded supervisor device '%s'", credentials.name)
    finally:
        context.close()
    return credentials


@pytest.fixture(scope="session")
def supervisor_state(seeded_supervisor, save_login_state):
    username, password = seeded_supervisor.as_login()
    return save_login_state("supervisor", username, password)


@pytest.fixture
def supervisor_page(supervisor_state, seeded_supervisor, authenticated_page):
    username, password = seeded_supervisor.as_login()
    return authenticated_page(supervisor_state, username, password, role="supervisor")


# ── Collection order ──────────────────────────────────────────────────────────

# NOTE: pytest passes hook arguments by name, so the second parameter must be
# called `config`. Inside this function that shadows the Settings object imported
# at module scope; nothing here needs it.
def pytest_collection_modifyitems(session, config, items):
    """Order suites by SUITE_ORDER instead of by filename.

    The suites are dependency-ordered, not independent: admin creates the
    workflow and machines that the device records bind to, and the role suites
    log in as those devices. Relying on alphabetical collection would run
    ``execution_source_config`` before ``processing_area``.

    ``list.sort`` is stable, so within a directory the numeric filename prefixes
    still decide the order.
    """
    def rank(item):
        path = str(item.path if hasattr(item, "path") else item.fspath).replace(os.sep, "/")
        for index, prefix in enumerate(SUITE_ORDER):
            if prefix in path:
                return index
        return len(SUITE_ORDER)

    for item in items:
        path = str(item.path).replace(os.sep, "/")
        if "/tests/api/" in path:
            item.add_marker(pytest.mark.api)
        elif "/tests/ui/" in path or "/tests/common/" in path:
            item.add_marker(pytest.mark.ui)
    items.sort(key=rank)


# ── Teardown ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data(request):
    """Remove UI records owned by this run, including after test failures."""
    from utils.test_data_cleanup import areas, devices, ui_records, cleanup_enabled
    if not any(any(part in str(item.path).replace(os.sep, "/") for part in ("tests/ui/", "tests/common/")) for item in request.session.items):
        yield
        return
    browser = request.getfixturevalue("browser")
    yield

    if not cleanup_enabled():
        log.info("cleanup disabled by CLEANUP_TEST_DATA=0")
        return

    if not areas and not devices and not ui_records:
        return

    failures = []

    def attempt(label, action):
        try:
            action()
        except Exception as exc:
            failures.append(f"{label}: {exc}")

    context = browser.new_context(ignore_https_errors=config.ignore_https_errors)
    page = context.new_page()
    try:
        LoginPage(page).login(config.admin_user, config.admin_pass)
        wait_for_app_ready(page, timeout=config.default_timeout)

        admin_dashboard = AdminDashboardPage(page)

        attempt("execution source config", admin_dashboard.navigate_to_execution_source_config)
        for role, device in sorted(devices):
            tab = getattr(admin_dashboard, f"click_{role}_tab")
            attempt(f"{role} device '{device}'",
                    lambda t=tab, d=device: (t(), admin_dashboard.delete_device_if_exists(d)))

        # Children in reused areas need individual cleanup; owned areas are
        # subsequently deleted too. Remove dependants before their inputs.
        priority = {"workflow": 0, "mapping": 1, "machine": 2, "container": 3, "material": 4}
        def record_order(record):
            tab = record[1].lower()
            return next((rank for key, rank in priority.items() if key in tab), 5)

        def delete_ui_record(url, tab, name, kind):
            page.goto(url, wait_until="domcontentloaded")
            wait_for_app_ready(page, timeout=config.default_timeout)
            page.get_by_role("tab", name=tab, exact=True).click()
            wait_for_app_ready(page, timeout=config.default_timeout)
            if kind == "mapping":
                ProcessingAreaPage(page).delete_station_mapping_if_exists(name)
            else:
                AdminDashboardPage(page).delete_device_if_exists(name)

        for record in sorted(ui_records, key=record_order):
            attempt(f"UI {record[1]} record '{record[2]}'",
                    lambda r=record: delete_ui_record(*r))

        pa = ProcessingAreaPage(page)
        for area in sorted(areas):
            attempt(f"processing area '{area}'", lambda a=area: pa.delete_processing_area(a))
    except Exception as exc:
        failures.append(f"admin login: {exc}")
    finally:
        context.close()

    if failures:
        message = "cleanup left data behind on the app:\n  " + "\n  ".join(failures)
        log.error(message)
        warnings.warn(message, stacklevel=1)


# ── Failure screenshots and the PDF run report ────────────────────────────────

_PAGE_FIXTURE_NAMES = (
    "page", "admin_page", "requester_page", "mes_page", "dispatcher_page", "supervisor_page",
    "e2e_requester_page", "e2e_dispatcher_page", "e2e_supervisor_page",
)

_collector = ResultCollector()
_run_metadata = {}


def _capture_screenshot(item, report, pytest_html):
    page = next(
        (item.funcargs[name] for name in _PAGE_FIXTURE_NAMES if name in item.funcargs),
        None,
    )
    if not page:
        return None

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = SCREENSHOT_DIR / f"{item.name}_{timestamp}.png"

    try:
        page.screenshot(path=str(screenshot_path))
    except Exception as exc:
        log.warning("Failed to capture screenshot for %s: %s", item.name, exc)
        return None

    if pytest_html:
        encoded = base64.b64encode(screenshot_path.read_bytes()).decode()
        report.extras = getattr(report, "extras", []) + [
            pytest_html.extras.html(
                f'<div><img src="data:image/png;base64,{encoded}" alt="screenshot" '
                f'style="width:600px;height:auto;" onclick="window.open(this.src)" '
                f'align="right"/></div>'
            )
        ]
    return screenshot_path


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    pytest_html = item.config.pluginmanager.getplugin("html")
    outcome = yield
    report = outcome.get_result()
    for name, value in report.user_properties:
        if name == "atiflow_version":
            _run_metadata[name] = value

    screenshot_path = None
    if report.failed:
        screenshot_path = _capture_screenshot(item, report, pytest_html)

    if getattr(report, "wasxfail", None):
        record_outcome = "xfailed" if report.skipped else "xpassed"
    elif report.skipped:
        record_outcome = "skipped"
    elif report.when == "call":
        record_outcome = report.outcome
    elif report.failed:
        record_outcome = "error"
    else:
        return

    _collector.add(
        nodeid=report.nodeid,
        outcome=record_outcome,
        duration=getattr(report, "duration", 0.0),
        message=getattr(report, "wasxfail", None) or (report.longreprtext if report.failed or report.skipped else None),
        screenshot=screenshot_path,
    )


def pytest_sessionstart(session):
    _collector.started_at = time.time()


def pytest_sessionfinish(session, exitstatus):
    """Build the single PDF run report. Never changes the run's exit status."""
    _collector.finished_at = time.time()

    if True: # Always skip PDF generation in headless test environment to prevent Playwright hangs
        return

    try:
        pdf_path, stats = build_pdf_report(
            _collector,
            environment={"env": config.env, "base_url": config.base_url, **_run_metadata},
        )
        print(
            f"\nPDF report: {pdf_path}\n"
            f"  {stats['total']} tests - {stats['passed']} passed, {stats['failed']} failed, "
            f"{stats['skipped']} skipped, {stats['xfailed']} expected failures, "
            f"{stats['xpassed']} unexpected passes in {stats['duration']}s"
            + (f" ({stats['screenshots']} screenshot(s) embedded)" if stats["screenshots"] else "")
        )

        pruned = prune_old_reports()
        if pruned:
            print(f"  pruned {pruned} old report(s), keeping the newest {keep_runs()}")
    except Exception as exc:
        print(f"\nPDF report generation failed: {exc}")
    finally:
        cleanup_work_dir()


# Root pytest options and report paths

def pytest_addoption(parser):
    parser.addoption(
        "--tab-view-ms", type=int, default=2000,
        help="Pause after selecting a Processing Area tab in headed mode (milliseconds; 0 disables).",
    )
    parser.addoption(
        "--no-pdf",
        action="store_true",
        default=False,
        help="Skip building this run's PDF report.",
    )


def pytest_configure(config):
    """Prepare this run's output paths.

    ``reports/`` holds only finished PDFs. pytest-html is off by default; if it
    is switched on explicitly with ``--html``, a relative path is resolved
    against the repository root rather than the working directory, so running
    ``pytest`` from inside ``tests/admin/`` cannot create a stray report folder
    beside itself.
    """
    if config.getoption("tab_view_ms") < 0:
        raise pytest.UsageError("--tab-view-ms must be zero or greater")
    ensure_dirs()

    html_path = getattr(config.option, "htmlpath", None)
    if html_path and not Path(html_path).is_absolute():
        config.option.htmlpath = str(ROOT_DIR / html_path)


def pytest_report_header(config):
    return f"pdf report: {PDF_PATH}"


# Admin fixtures

class StepRecorder:
    """Runs a sequence of UI steps, recording failures instead of aborting.

    These flows build one entity on top of another, so aborting at the first
    failure hides the state of everything after it. Each step that raises is
    recorded, any modal it left open is force-closed so the next step starts
    from a usable page, and the run continues. Call ``assert_no_failures()`` at
    the end to fail the test with the full list.
    """

    def __init__(self, page):
        self.page = page
        self.errors = []

    def __call__(self, step_name, func):
        import allure

        try:
            with allure.step(step_name):
                func()
        except Exception as exc:
            log.error("%s failed: %s", step_name, exc)
            self.errors.append(f"{step_name} failed: {exc}")
            dismiss_stuck_modal(self.page)

    def assert_no_failures(self):
        if self.errors:
            pytest.fail("The following steps failed:\n" + "\n".join(self.errors))


@pytest.fixture
def safe_step(admin_page):
    """Step recorder bound to the logged-in admin page."""
    return StepRecorder(admin_page)


@pytest.fixture
def processing_area(pa_page):
    """Open the suite's Processing Area, creating it if absent.

    ``test_01_material_container.py`` deletes and recreates it to guarantee a
    clean baseline. The later modules only need it to exist and be open, and
    this fixture lets each of them run standalone.
    """
    pa_page.create_processing_area(
        TestData.processing_area_name,
        TestData.processing_area_description,
    )
    return pa_page


@pytest.fixture
def full_processing_area(admin_page, pa_page, processing_area):
    """Ensure the Processing Area and everything bound to it exist.

    ``processing_area`` only guarantees the area itself. The Execution Source
    Config device records also need a material, container, both machines,
    both station mappings and the workflow underneath it - normally built by
    ``test_01``-``test_04`` when the full suite runs in ``SUITE_ORDER``. Those
    modules delete-and-recreate for a clean baseline, which is too slow to
    repeat for every device test, so this fixture only creates what is
    missing.

    Does not create the "Staging Area" the device records also bind to - no
    page object exposes a way to build one, so it must already exist on the
    target app.
    """
    admin_dashboard = AdminDashboardPage(admin_page)

    def row_exists(name):
        return table_row_exists(admin_page, name)

    material = material_spec()
    pa_page.go_to_materials()
    if not row_exists(material.type_name):
        admin_dashboard.add_material(
            material.type_name,
            material.production_unit,
            material.pre_proc_time,
            material.max_qty,
            material.prefix,
        )

    container = container_spec()
    pa_page.go_to_containers()
    if not row_exists(container.container_type):
        admin_dashboard.add_container(
            container.container_type,
            container.sub_type,
            container.length,
            container.width,
            container.height,
            container.hitch_length,
            container.qty,
        )

    pa_page.go_to_machine_names()
    for machine in machine_specs():
        if not row_exists(machine.name):
            pa_page.add_machine_name(machine.name, machine.production_type)

    pickup_name, drop_name = station_names()
    pa_page.go_to_station_mapping()
    for mapping_name, station_id, index in (
        (pickup_name, TestData.station_id, 0),
        (drop_name, TestData.station_id_2, 1),
    ):
        if not row_exists(mapping_name):
            pa_page.add_station_mapping(mapping_name, station_id=station_id, station_index=index)

    workflow = workflow_spec()
    pa_page.go_to_workflow()
    if not row_exists(workflow.name):
        pa_page.add_workflow(
            workflow.name,
            pickup_station=workflow.pickup_station,
            drop_station=workflow.drop_station,
        )

    return pa_page


@pytest.fixture
def exec_config(admin_page, full_processing_area):
    """Open Execution Source Config and assert all four tabs rendered."""
    dashboard = AdminDashboardPage(admin_page)
    dashboard.navigate_to_execution_source_config()

    for tab in (dashboard.requester_tab, dashboard.mes_tab,
                dashboard.dispatcher_tab, dashboard.supervisor_tab):
        expect(tab).to_be_visible(timeout=5000)

    return dashboard


# Isolated E2E fixtures

@pytest.fixture(scope="session")
def e2e_provisioned_baseline(browser):
    """Delete-and-recreate the isolated ``[e2e_*]`` Processing Area world.

    Unlike the shared create-if-absent baseline, an e2e run
    always starts from a clean ``test_e2e`` area so its cross-role check can
    never pass against a stale, half-built one.
    """
    context, page = _admin_context(browser)
    try:
        area = _provision_baseline(
            page,
            rebuild=True,
            area_name=TestData.e2e_processing_area_name,
            area_description=TestData.e2e_processing_area_description,
            material=e2e_material_spec(),
            container=e2e_container_spec(),
            machines=e2e_machine_specs(),
            mapping_names=e2e_station_names(),
            mapping_station_ids=(TestData.e2e_station_id, TestData.e2e_station_id_2),
            workflows=e2e_workflow_specs(),
            supervisor_scope_areas=TestData.e2e_sup_processing_areas,
        )
    finally:
        context.close()
    return area


@pytest.fixture(scope="session")
def e2e_seeded_requester(browser, e2e_provisioned_baseline):
    """Create the ``requester_e2e`` device record; return its credentials."""
    credentials = e2e_requester_credentials()
    context, page = _admin_context(browser)
    try:
        dashboard = AdminDashboardPage(page)
        dashboard.navigate_to_execution_source_config()
        dashboard.click_requester_tab()
        dashboard.delete_device_if_exists(credentials.name)
        dashboard.add_requester_device(
            credentials.name,
            credentials.device_id,
            credentials.password,
            TestData.e2e_req_bound_machines,
            TestData.e2e_req_bound_workflows,
            TestData.e2e_req_staging_areas,
        )
        log.info("Seeded e2e requester device '%s'", credentials.name)
    finally:
        context.close()
    return credentials


@pytest.fixture(scope="session")
def e2e_seeded_dispatcher(browser, e2e_provisioned_baseline):
    """Create the ``dispatcher_e2e`` device record; return its credentials."""
    credentials = e2e_dispatcher_credentials()
    context, page = _admin_context(browser)
    try:
        dashboard = AdminDashboardPage(page)
        dashboard.navigate_to_execution_source_config()
        dashboard.click_dispatcher_tab()
        dashboard.delete_device_if_exists(credentials.name)
        dashboard.add_dispatcher_device(
            credentials.name,
            credentials.device_id,
            credentials.password,
            TestData.e2e_disp_bound_stations,
            TestData.e2e_disp_staging_areas,
        )
        log.info("Seeded e2e dispatcher device '%s'", credentials.name)
    finally:
        context.close()
    return credentials


@pytest.fixture(scope="session")
def e2e_seeded_supervisor(browser, e2e_provisioned_baseline):
    """Create the ``supervisor_e2e`` device record; return its credentials."""
    credentials = e2e_supervisor_credentials()
    context, page = _admin_context(browser)
    try:
        dashboard = AdminDashboardPage(page)
        dashboard.navigate_to_execution_source_config()
        dashboard.click_supervisor_tab()
        dashboard.delete_device_if_exists(credentials.name)
        dashboard.add_supervisor_device(
            credentials.name,
            credentials.device_id,
            credentials.password,
            TestData.e2e_sup_staging_areas,
            TestData.e2e_sup_processing_areas,
        )
        log.info("Seeded e2e supervisor device '%s'", credentials.name)
    finally:
        context.close()
    return credentials


@pytest.fixture(scope="session")
def e2e_requester_state(e2e_seeded_requester, save_login_state):
    username, password = e2e_seeded_requester.as_login()
    return save_login_state("e2e_requester", username, password)


@pytest.fixture
def e2e_requester_page(e2e_requester_state, e2e_seeded_requester, authenticated_page):
    username, password = e2e_seeded_requester.as_login()
    return authenticated_page(e2e_requester_state, username, password, role="e2e_requester")


@pytest.fixture(scope="session")
def e2e_dispatcher_state(e2e_seeded_dispatcher, save_login_state):
    username, password = e2e_seeded_dispatcher.as_login()
    return save_login_state("e2e_dispatcher", username, password)


@pytest.fixture
def e2e_dispatcher_page(e2e_dispatcher_state, e2e_seeded_dispatcher, authenticated_page):
    username, password = e2e_seeded_dispatcher.as_login()
    return authenticated_page(e2e_dispatcher_state, username, password, role="e2e_dispatcher")


@pytest.fixture(scope="session")
def e2e_supervisor_state(e2e_seeded_supervisor, save_login_state):
    username, password = e2e_seeded_supervisor.as_login()
    return save_login_state("e2e_supervisor", username, password)


@pytest.fixture
def e2e_supervisor_page(e2e_supervisor_state, e2e_seeded_supervisor, authenticated_page):
    username, password = e2e_seeded_supervisor.as_login()
    return authenticated_page(e2e_supervisor_state, username, password, role="e2e_supervisor")


@pytest.fixture
def machine_api(request):
    """Function-owned API resources, shared with isolated browser contract tests."""
    from utils.machine_api import MachineAPI
    if any(part in str(request.node.path).replace(os.sep, "/") for part in ("tests/ui/", "tests/common/")):
        page = request.getfixturevalue("admin_page")
        token = page.evaluate(
            "() => JSON.parse(sessionStorage.getItem('userDetails') || '{}').access_token"
        )
        if not token:
            raise RuntimeError("Admin browser session has no API access token")
        client = MachineAPI(token=token, base_url=config.app_url)
    else:
        client = MachineAPI()
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def machine_ui_area(machine_api, admin_page):
    """Open a new API-owned area in the UI, without shared workflow/device setup."""
    area = machine_api.area()
    admin_page.reload(wait_until='domcontentloaded')
    page = ProcessingAreaPage(admin_page)
    page.navigate_to_existing_area(area['processing_area_name'])
    page.go_to_machine_names()
    return page, area
