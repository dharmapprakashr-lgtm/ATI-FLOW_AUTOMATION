> Historical design plan: paths and proposed helpers below may no longer exist.
> See [current structure](../README.md#project-structure) for the active layout.

This archived plan describes an earlier proposed pytest + Playwright structure
for the ATIFlow automation suite. It is kept for background only; the active
repository layout and run commands are documented in the root README.

## Design Principles

- Tests should interact through Page Objects instead of calling Playwright
  directly from test bodies.
- Setup should use APIs where available. UI setup is acceptable when no API
  exists, but should be isolated in fixtures and reused across tests.
- Roles should remain first-class test dimensions so suites can be selected with
  markers such as `admin`, `requester`, `dispatcher`, and `supervisor`.
- Authentication state should be reused per role to avoid repeated login flows.
- Configuration and secrets should come from environment-specific settings, not
  hardcoded values.

## Proposed Historical Structure

```text
automation-suite/
├── pages/                              # (your existing layer, unchanged)
│   ├── __init__.py
│   ├── base_page.py
│   ├── login/
│   │   └── login_page.py
│   ├── admin/
│   │   ├── admin_navigation.py
│   │   ├── processing_area/
│   │   │   ├── processing_area_list_page.py
│   │   │   └── create_new_area_page.py
│   │   ├── execution_source_config/
│   │   │   ├── requester_device_page.py
│   │   │   ├── mes_page.py
│   │   │   ├── dispatcher_page.py
│   │   │   └── supervisor_device_page.py
│   │   └── settings/
│   │       └── connection_checking_page.py
│   └── dashboards/
│       ├── requester_dashboard_page.py
│       ├── dispatcher_dashboard_page.py
│       └── supervisor_dashboard_page.py
│
├── tests/                              # mirrors pages/, one test module per page-object concern
│   ├── conftest.py                     # top-level fixtures: browser, base_url, per-role auth
│   ├── admin/
│   │   ├── conftest.py                 # admin-only fixtures (e.g. logged-in admin page)
│   │   ├── processing_area/
│   │   │   ├── test_material_container.py
│   │   │   ├── test_machine_name.py
│   │   │   ├── test_station_mapping.py
│   │   │   └── test_workflow.py
│   │   ├── execution_source_config/
│   │   │   ├── test_create_requester.py
│   │   │   ├── test_create_dispatcher.py
│   │   │   ├── test_create_supervisor.py
│   │   │   └── test_mes_config.py
│   │   └── settings/
│   │       └── test_connection_checking.py
│   ├── requester/
│   │   ├── conftest.py                 # depends on admin fixtures to seed a requester account
│   │   └── test_requester_dashboard.py
│   ├── dispatcher/
│   │   ├── conftest.py
│   │   └── test_dispatcher_dashboard.py
│   ├── supervisor/
│   │   ├── conftest.py
│   │   └── test_supervisor_dashboard.py
│   └── e2e/                            # cross-role workflows, run last / nightly
│       └── test_full_workflow_admin_to_supervisor.py
│
├── config/
│   ├── __init__.py
│   ├── environment.py                     # reads env vars, exposes typed config object
│   └── environments/
│       ├── qa.yaml
│       └── staging.yaml
│
├── fixtures/
│   ├── __init__.py
│   ├── auth_states/                    # storage_state JSON dumps, gitignored, regenerated per run
│   └── test_data/
│       ├── processing_area_data.py
│       └── role_credentials_template.py
│
├── utils/
│   ├── __init__.py
│   ├── api_client.py                   # optional: create/delete test entities via API instead of UI
│   ├── data_factory.py                 # faker-based unique names (avoid collisions in parallel runs)
│   ├── logger.py
│   └── waits.py                        # custom wait conditions beyond base_page defaults
│
├── reports/                            # allure-results / html reports, gitignored
├── .github/workflows/
│   └── e2e.yml                         # CI matrix by role marker
├── pytest.ini                          # markers, test paths, default options
├── requirements.txt
└── README.md
```

## Key Mechanism: Auth Reuse Across Roles

The original proposal used Playwright `storage_state` files so each role could
log in once and share that authenticated state across the suite:

```python
# tests/conftest.py
import pytest
from playwright.sync_api import sync_playwright
from config.environment import config
from pages.login.login_page import LoginPage

@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.headless)
        yield browser
        browser.close()

def _login_and_save_state(browser, role: str, username: str, password: str, state_path: str):
    context = browser.new_context(base_url=config.base_url)
    page = context.new_page()
    LoginPage(page).login(username, password)
    context.storage_state(path=state_path)
    context.close()

@pytest.fixture(scope="session")
def admin_state(browser, tmp_path_factory):
    path = str(tmp_path_factory.mktemp("auth") / "admin.json")
    _login_and_save_state(browser, "admin", config.admin_user, config.admin_pass, path)
    return path

@pytest.fixture
def admin_page(browser, admin_state):
    context = browser.new_context(storage_state=admin_state, base_url=config.base_url)
    page = context.new_page()
    yield page
    context.close()
```

Each admin test could request `admin_page` and receive a pre-authenticated page
without repeating the login flow.

## Role Credential Setup

The requester, dispatcher, and supervisor suites were intended to seed their own
role account through the admin layer once per session:

```python
# tests/requester/conftest.py
import pytest
from utils.data_factory import unique_username
from pages.admin.execution_source_config.requester_device_page import RequesterDevicePage

@pytest.fixture(scope="session")
def requester_credentials(admin_page):
    username, password = unique_username("requester"), "AutoTest@123"
    RequesterDevicePage(admin_page).create_requester(username, password)
    return username, password

@pytest.fixture(scope="session")
def requester_state(browser, requester_credentials, tmp_path_factory):
    username, password = requester_credentials
    path = str(tmp_path_factory.mktemp("auth") / "requester.json")
    _login_and_save_state(browser, "requester", username, password, path)  # import from top conftest
    return path

@pytest.fixture
def requester_page(browser, requester_state):
    context = browser.new_context(storage_state=requester_state)
    page = context.new_page()
    yield page
    context.close()
```

This encodes the manual flow as reusable fixtures: admin creates the account
once, then the role-specific suite logs in with that account and exercises its
dashboard.

## Markers for Role-Based Execution

```ini
# pytest.ini
[pytest]
markers =
    admin: admin console tests
    requester: requester role tests
    dispatcher: dispatcher role tests
    supervisor: supervisor role tests
    smoke: fast critical-path checks
    e2e: full cross-role workflow tests
```

Tag each test file's tests accordingly, for example
`pytestmark = pytest.mark.admin`, so CI can select focused suites such as
`-m "admin and smoke"` and reserve cross-role E2E flows for slower jobs.

## Phased Rollout

1. Finish the admin coverage first: processing area tabs, execution source
   configuration, and settings.
2. Add requester, dispatcher, and supervisor suites with their own page objects
   and role-seeding fixtures.
3. Keep E2E tests focused on one or two complete cross-role workflows, because
   they are slower and more sensitive to environment state.

When setup APIs exist, prefer them for creating processing areas and role
accounts. Keep UI interactions for the behavior under test. If setup APIs are
not available, session-scoped UI fixtures are the fallback.
