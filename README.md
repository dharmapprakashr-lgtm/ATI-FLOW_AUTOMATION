# AtiFlow Automation

> **End-to-end, API, and CRUD test suite for AtiFlow v2.0** — a warehouse/factory material-flow management platform.  
> Built with **Python · Playwright · pytest · HTTPX/Requests**.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Directory Structure](#3-directory-structure)
4. [Prerequisites](#4-prerequisites)
5. [Installation](#5-installation)
6. [Configuration](#6-configuration)
   - [Environment Variables (.env)](#61-environment-variables-env)
   - [Test Data (test_data.toml)](#62-test-data-test_datatoml)
   - [Environment Profiles (YAML)](#63-environment-profiles-yaml)
7. [Running Tests](#7-running-tests)
   - [Run the Full Suite](#71-run-the-full-suite)
   - [Run by Role / Module](#72-run-by-role--module)
   - [Run by Marker](#73-run-by-marker)
   - [Run API Tests](#74-run-api-tests)
   - [Run with Visible Browser](#75-run-with-visible-browser)
8. [Test Suites In Detail](#8-test-suites-in-detail)
   - [Admin Suite](#81-admin-suite)
   - [Dispatcher Suite](#82-dispatcher-suite)
   - [Requester Suite](#83-requester-suite)
   - [Supervisor Suite](#84-supervisor-suite)
   - [Common / Cross-Role Suite](#85-common--cross-role-suite)
   - [CRUD Lifecycle Suite](#86-crud-lifecycle-suite)
   - [End-to-End (E2E) Suite](#87-end-to-end-e2e-suite)
   - [API Suite](#88-api-suite)
   - [Unit Tests](#89-unit-tests)
9. [pytest Markers Reference](#9-pytest-markers-reference)
10. [Page Object Model](#10-page-object-model)
11. [Utilities](#11-utilities)
12. [Reporting](#12-reporting)
13. [Data Files](#13-data-files)
14. [CI / GitHub Actions](#14-ci--github-actions)
15. [Contributing](#15-contributing)

---

## 1. Project Overview

**AtiFlow** is an industrial material-flow application used on factory floors. It connects three device-based roles — **Requester**, **Dispatcher**, and **Supervisor** — through an **Admin** portal and communicates with an external **Fleet Manager (FM)** and an **MES** (Manufacturing Execution System).

This repository provides a **full automation harness** that validates:

| Layer | What is tested |
|---|---|
| **UI (browser)** | Every role's dashboard, navigation, forms, search, pagination, notifications, and access-control guards |
| **API (HTTP)** | REST endpoints for processing areas, machines, materials, station mappings, tablet login security, MES polling, and settings |
| **CRUD lifecycle** | Create → Read → Update → Delete flows for all major admin entities |
| **End-to-end** | Full cross-role workflow: Admin sets up → Requester raises a request → Dispatcher dispatches → FM creates a trip → Supervisor monitors |
| **NFR / Security** | Page load performance, XSS injection guards, role-based access control |

---

## 2. Architecture

```
+------------------------------------------------------------------+
|                        Test Execution                            |
|  pytest + pytest-playwright  |  pytest + httpx/requests          |
|        (UI tests)            |        (API tests)                |
+---------------+--------------+--------------+--------------------+
                |                             |
        +-------+-------+           +---------+---------+
        |  Page Objects |           |  LiveAPIClient    |
        |  (pages/)     |           |  (utils/)         |
        +-------+-------+           +---------+---------+
                |                             |
        +-------+-----------------------------+---------+
        |              AtiFlow Application              |
        |         https://<BASE_URL>/login              |
        +--------------------+---------------------------+
                             |
              +--------------+--------------+
              |  Fleet Manager (FM)         |
              |  MES (Manufacturing Exec.)  |
              +-----------------------------+
```

**Key design decisions:**

- **Page Object Model (POM)** — every screen has a dedicated class in `pages/`. Tests never contain raw locators.
- **Central config** — `config/environment.py` (Settings) and `config/data.py` (TestData) are the single source of truth; tests read attributes, not env vars directly.
- **TOML-driven test data** — `config/test_data.toml` holds all names, IDs, and values. Changing a test value = editing one file, not touching test code.
- **PDF reports** — each run produces a single self-contained PDF in `reports/`, with screenshots of every failure embedded inline.

---

## 3. Directory Structure

```
AtiFlowAutomation/
├── config/                         # Configuration layer
│   ├── environment.py              # Settings dataclass — URLs, headless, timeouts
│   ├── data.py                     # TestData class — all test input values
│   ├── credentials.py              # Role credential helpers
│   ├── processing_area.py          # Processing area / machine / workflow builders
│   ├── test_data.toml              # <- Edit this to change any test value
│   └── environments/
│       ├── qa.yaml                 # QA environment defaults (non-secret)
│       └── staging.yaml            # Staging environment defaults
│
├── pages/                          # Page Object Model
│   ├── login/login_page.py
│   ├── admin/
│   │   ├── admin_navigation.py     # Admin shell + sidebar navigation
│   │   ├── processing_area/        # Materials, containers, machines, workflows
│   │   ├── execution_source_config/
│   │   └── settings/
│   ├── dashboards/
│   │   ├── requester_dashboard_page.py
│   │   ├── dispatcher_dashboard_page.py
│   │   └── supervisor_dashboard_page.py
│   ├── fleet_manager/
│   │   └── manage_trips_page.py
│   ├── containers_page.py
│   └── staging_area_page.py
│
├── tests/                          # All test files
│   ├── ui/
│   │   ├── admin/
│   │   │   ├── processing_area/    # 14 test modules (creation, materials, containers)
│   │   │   └── execution_source_config/  # 5 test modules (devices, validation)
│   │   ├── dispatcher/             # 17 test modules (login → pagination)
│   │   ├── requester/              # 19 test modules (login → cancel request)
│   │   ├── supervisor/             # 10 test modules (dashboard → auto-trips)
│   │   ├── common/                 # 7 cross-role modules (security, NFR, nav)
│   │   ├── crud/                   # 7 lifecycle modules
│   │   └── e2e/                    # Full cross-role workflow test
│   ├── api/                        # 11 API test modules
│   └── unit/                       # 1 unit test module
│
├── utils/
│   ├── live_api_client.py          # Authenticated HTTP session against MTS API
│   ├── machine_api.py              # Machine REST API helpers
│   ├── waits.py                    # Smart Playwright wait helpers
│   ├── pdf_report.py               # PDF report builder (ReportLab)
│   ├── report_paths.py             # Timestamped paths for reports/screenshots
│   ├── report_to_pdf.py            # HTML -> PDF conversion
│   ├── data_factory.py             # Dynamic test data generators
│   ├── test_data_cleanup.py        # Post-run teardown helpers
│   └── logger.py                   # Structured logger (get_logger)
│
├── data/
│   ├── container_bulk_upload.csv   # Sample bulk-upload payload for containers
│   └── material_bulk_upload.csv    # Sample bulk-upload payload for materials
│
├── docs/
│   ├── ATIFLOW_CONFIGURATION.md    # Full Admin -> FM configuration guide
│   ├── TEST_COVERAGE.md            # Detailed test coverage matrix
│   ├── WIP_INVENTORY_TEST_CASES.md # WIP inventory test case specs
│   └── plan.md                     # Test planning notes
│
├── conftest.py                     # All pytest hooks + shared fixtures
├── pytest.ini                      # pytest settings, markers, addopts
├── requirements.txt                # Python dependencies
├── .env.example                    # Template for secrets — copy to .env
└── .gitignore
```

---

## 4. Prerequisites

| Requirement | Minimum version |
|---|---|
| Python | 3.10+ |
| pip | 22+ |
| Playwright browsers | Chromium (installed via `playwright install`) |
| Network access | AtiFlow instance reachable at `BASE_URL` |

> **Python 3.11+** is recommended — it ships with `tomllib` in the stdlib, eliminating the `tomli` backport.

---

## 5. Installation

```bash
# 1. Clone the repository
git clone https://github.com/dharmapprakashr-lgtm/ATI-FLOW_AUTOMATION.git
cd ATI-FLOW_AUTOMATION

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright browser binaries
playwright install chromium

# 5. Set up your secrets
cp .env.example .env
# -> Edit .env with your real BASE_URL, ADMIN_USERNAME, ADMIN_PASSWORD
```

---

## 6. Configuration

### 6.1 Environment Variables (`.env`)

Copy `.env.example` to `.env` and fill in the values. **Never commit `.env`** — it is git-ignored.

```ini
# Required
BASE_URL=https://192.168.x.x/login   # Full URL including /login
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Optional
MES_USERNAME=mes_user
MES_PASSWORD=mes_pass
HEADLESS=True                         # false = watch the browser
TEST_ENV=qa                           # selects config/environments/<name>.yaml
DEFAULT_TIMEOUT=15000                 # Playwright default wait (ms)

# Only needed for the E2E suite (Fleet Manager cross-check)
FM_BASE_URL=https://192.168.x.x
FM_USERNAME=fm_user
FM_PASSWORD=fm_pass
```

**Resolution priority (highest wins):** Shell env → `.env` file → `config/environments/<env>.yaml` defaults.

---

### 6.2 Test Data (`config/test_data.toml`)

All names, IDs, passwords, SKU codes, and expected values used in tests come from `config/test_data.toml`. **To change a test value, edit only this file** — no test code changes needed.

Key TOML sections:

| Section | Purpose |
|---|---|
| `[processing_area]` | Name and description of the main test processing area |
| `[processing_area_crud]` | Names used in CRUD lifecycle tests |
| `[devices_crud]` | Device names and passwords for CRUD lifecycle |
| `[material]` / `[material_crud]` | Material type names and specs |
| `[container]` / `[container_crud]` | Container types and dimensions |
| `[machine_name]` / `[machine_name_crud]` | Machine name variants |
| `[station_mapping]` / `[station_mapping_crud]` | Station mapping names and IDs |
| `[[workflow]]` | Array of workflow specs (name, pickup/drop types and stations) |
| `[devices]` | Requester / Dispatcher / Supervisor device names, IDs, passwords |
| `[requester]` | Sample request name and priority |
| `[requester_request_material]` | Live WIP-inventory SKU codes for request wizard tests |
| `[dispatcher]` | Default dispatcher zone |
| `[supervisor]` | Report name |
| `[supervisor_dashboard]` | Staging grid size, legend states, column names |
| `[dispatcher_requests]` | Default and alternate stations for dispatcher tests |
| `[mes]` | MES machine name |
| `[e2e_*]` | Isolated names used exclusively by E2E tests |

---

### 6.3 Environment Profiles (YAML)

Non-secret, per-environment defaults live in `config/environments/`:

```
config/environments/
├── qa.yaml        # Points to QA instance — base_url, timeouts, headless
└── staging.yaml   # Points to staging instance
```

Select a profile with `TEST_ENV`:

```bash
TEST_ENV=staging pytest -m smoke
```

---

## 7. Running Tests

### 7.1 Run the Full Suite

```bash
pytest tests/
```

### 7.2 Run by Role / Module

```bash
# All UI tests
pytest tests/ui/

# Admin tests only
pytest tests/ui/admin/

# Specific admin module
pytest tests/ui/admin/processing_area/

# Dispatcher tests
pytest tests/ui/dispatcher/

# Requester tests
pytest tests/ui/requester/

# Supervisor tests
pytest tests/ui/supervisor/

# Common / cross-role tests
pytest tests/ui/common/

# CRUD lifecycle tests
pytest tests/ui/crud/

# End-to-end workflow
pytest tests/ui/e2e/

# API tests
pytest tests/api/
```

### 7.3 Run by Marker

```bash
pytest -m smoke              # Fast critical-path checks
pytest -m admin              # Admin console tests
pytest -m dispatcher         # Dispatcher role tests
pytest -m requester          # Requester role tests
pytest -m supervisor         # Supervisor role tests
pytest -m e2e                # Full cross-role workflow
pytest -m crud               # Create/Read/Update/Delete lifecycle
pytest -m api                # HTTP API contract tests
pytest -m auth               # Authentication and session tests
pytest -m security           # XSS and injection security tests
pytest -m nfr                # Non-functional requirement tests
pytest -m regression         # Full regression sweep
pytest -m "admin and smoke"  # Combine markers
```

### 7.4 Run API Tests

```bash
# The API suite reads BASE_URL / ADMIN_USERNAME / ADMIN_PASSWORD from .env
pytest tests/api/test_processing_area_api.py
pytest tests/api/test_material_station_mapping_api.py
pytest tests/api/test_settings_rest_api.py
```

> **Note:** Several large API test files are excluded from the default collection (`collect_ignore` in `conftest.py`). Pass them explicitly on the command line when needed.

### 7.5 Run with Visible Browser

```bash
HEADLESS=false pytest tests/ui/requester/
```

---

## 8. Test Suites In Detail

### 8.1 Admin Suite

`tests/ui/admin/` — **19 test modules**

**Processing Area** (`processing_area/`):

| Module | What it tests |
|---|---|
| `test_01_processing_area_creation` | Create a processing area via the Admin UI |
| `test_02_area_tabs_visibility` | All configuration tabs are present and visible |
| `test_05_material` | Add, edit, and validate material types |
| `test_06_machine_name` | Add machine names |
| `test_07_machine_name_validation` | Machine name field validation rules |
| `test_08_container` | Add, edit, and validate container types |
| `test_09_station_mapping` | Create station mappings |
| `test_10_station_mapping_validation` | Station mapping validation rules |
| `test_12_workflow` | Create and bind workflows |
| `test_14_area_validation` | Processing area form validation |
| `test_15_staging_area` | Staging area visibility and binding |
| `test_18_setting` | Admin settings panel |
| `test_19_notification` | Admin notification panel |

**Execution Source Config** (`execution_source_config/`):

| Module | What it tests |
|---|---|
| `test_create_requester` | Create a Requester device record |
| `test_create_dispatcher` | Create a Dispatcher device record |
| `test_create_supervisor` | Create a Supervisor device record |
| `test_mes_config` | MES device configuration |
| `test_exec_config_validation` | Execution Source Config form validation |

---

### 8.2 Dispatcher Suite

`tests/ui/dispatcher/` — **17 test modules** (numbered `test_00` to `test_16`)

| # | Test | Description |
|---|---|---|
| 00 | Login | Device login with Dispatcher credentials |
| 01 | Dashboard loads | Dashboard renders with the bound station |
| 02 | Station dropdown | Lists only the dispatcher's bound stations |
| 03 | Station switching | Switching station updates breadcrumb and request list |
| 04 | Sort dropdown | Toggles between Newest / Oldest order |
| 05 | Search by ID | Filters the request table by request ID |
| 06 | Search by material code | Filters the request table by material code |
| 07 | No-match search | Shows empty state when search has no results |
| 08 | Pending tab | Shows only "Awaiting Dispatch" requests |
| 09 | Dispatched tab | Shows only dispatched requests |
| 10 | All tab | Shows union of Pending + Dispatched |
| 11 | Row detail | Clicking a row expands the request details |
| 12 | Dispatch action | Dispatching a request moves it to the Dispatched tab |
| 13 | Manual confirmation | Manual confirmation mode is visible when configured |
| 14 | Pagination | Row count selector and page controls work correctly |
| 15 | Notification icon | Opens the notification panel |
| 16 | Notification scope | Notifications are scoped to this dispatcher's station |

---

### 8.3 Requester Suite

`tests/ui/requester/` — **19 test modules** (numbered `test_00` to `test_18`)

| # | Test | Description |
|---|---|---|
| 00 | Login | Device login with Requester credentials |
| 01 | Staging area cells | Staging area grid matches the requester's bound cells |
| 02 | Machine dropdown | Switching machine updates context |
| 03 | Request wizard | Wizard loads with correct machine and workflow |
| 04 | Staging area search | Filter and search in the staging area picker |
| 05 | Utilisation bar | Utilisation bar percentage is accurate |
| 06 | Workflow dropdown | Switching workflow updates context |
| 07 | Request history sort/filter | Sort and filter the request history table |
| 08 | SKU search | Search by material (SKU) code |
| 09 | Fleet filter | Fleet filter in staging area selector |
| 10 | Sub-SKU rows | Selecting a SKU loads its sub-SKU rows |
| 11 | Add / increment / decrement | Quantity controls work correctly |
| 12 | Max quantity guard | Quantity cannot exceed available stock |
| 13 | Zero-stock row | Zero-available rows are disabled |
| 14 | Next button | "Next" enables once a valid quantity is selected |
| 15 | Advance to summary | Request wizard advances to the summary step |
| 16 | Summary reflects selection | Summary page reflects all selections made |
| 17 | Submit confirmation | Submitting shows a confirmation screen |
| 18 | Cancel order | A requested order can be cancelled |

---

### 8.4 Supervisor Suite

`tests/ui/supervisor/` — **10 test modules**

| Module | Description |
|---|---|
| `test_00_login` | Device login with Supervisor credentials |
| `test_01_dashboard_shell` | Dashboard header, tabs, and layout |
| `test_02_processing_area_selector` | Switching processing area updates context |
| `test_03_staging_area_list` | Staging area list matches bound areas |
| `test_04_staging_area_detail` | Cell grid, legend states, and colour accuracy |
| `test_05_staging_area_manage` | Manage cell states (block, unblock, fill, clear) |
| `test_07_realtime_refresh` | Real-time data refresh behaviour |
| `test_09_notifications` | Notification panel, scoping, and badge count |
| `test_10_auto_trips` | Auto-trip list and state |
| `test_11_access_control` | Supervisor cannot access Admin or other role pages |

---

### 8.5 Common / Cross-Role Suite

`tests/ui/common/` — **7 test modules**

| Module | Description |
|---|---|
| `test_login` | Login page UI, error messages, session persistence |
| `test_access_control` | Role-based access control — each role blocked from others' pages |
| `test_security` | XSS injection attempts in all input fields |
| `test_dashboard_common` | Common dashboard elements present across all roles |
| `test_ui_navigation` | Navigation menus, breadcrumbs, and back-navigation |
| `test_application_version` | Application version is displayed |
| `test_nfr` | Non-functional requirements: page load time under threshold |

---

### 8.6 CRUD Lifecycle Suite

`tests/ui/crud/` — **7 test modules**

Full Create → Read → Update → Delete lifecycle validation for each entity:

| Module | Entity |
|---|---|
| `test_01_processing_area` | Processing Area |
| `test_02_material_container` | Material Type and Container Type |
| `test_03_machine` | Machine Name |
| `test_04_station_mapping` | Station Mapping |
| `test_05_devices` | Requester / Dispatcher / Supervisor devices |
| `test_machine_api_ui` | Machine via API + verify in UI |

---

### 8.7 End-to-End (E2E) Suite

`tests/ui/e2e/test_full_workflow_admin_to_supervisor.py`

The **full cross-role integration test**:

1. Admin creates a processing area with isolated E2E names
2. Admin configures materials, containers, machines, station mappings, and workflows
3. Admin creates Requester, Dispatcher, and Supervisor device records
4. Requester logs in and submits a material request
5. Dispatcher logs in and dispatches the request
6. Fleet Manager creates a trip (verified via FM login)
7. Supervisor monitors the staging area and sees the update

This suite uses isolated `[e2e_*]` TOML sections to avoid polluting data shared with the role-specific suites.

---

### 8.8 API Suite

`tests/api/` — **11 test modules**

| Module | What it covers |
|---|---|
| `test_processing_area_api` | CRUD operations on processing areas via REST |
| `test_processing_area_machines_api` | Machine endpoints on a processing area |
| `test_material_station_mapping_api` | Material and station-mapping REST endpoints |
| `test_material_master_config` | Material master configuration API |
| `test_settings_rest_api` | Settings REST endpoints |
| `test_central_config_health` | Central config health-check endpoints |
| `test_external_connections_setup` | External connection (FM / MES) setup endpoints |
| `test_processing_staging_grid` | Staging grid REST API |
| `test_mes_integration_polling` | MES polling behaviour |
| `test_tablet_login_security` | Tablet (device) login security — brute force, token expiry |
| `test_mts_automation` | MTS automation endpoints |

---

### 8.9 Unit Tests

`tests/unit/test_table_row_exists.py` — verifies the `table_row_exists` Playwright wait helper in isolation.

---

## 9. pytest Markers Reference

| Marker | Scope |
|---|---|
| `ui` | Browser UI tests |
| `api` | HTTP API contract tests |
| `api_model` | Legacy MTS model/mock API harness |
| `integration` | API + browser consistency checks |
| `admin` | Admin console tests |
| `admin_pa` | Admin processing area tests |
| `exec_config` | Execution source config tests |
| `requester` | Requester role tests |
| `dispatcher` | Dispatcher role tests |
| `supervisor` | Supervisor role tests |
| `dashboards` | Dashboard tests (all roles) |
| `e2e` | Full cross-role workflow |
| `crud` | Create/Read/Update/Delete lifecycle |
| `auth` | Authentication and session tests |
| `access_control` | Role-based access control |
| `security` | XSS and injection security |
| `nfr` | Non-functional requirements |
| `ui_nav` | UI navigation and form tests |
| `settings` | Settings module tests |
| `smoke` | Fast critical-path checks |
| `regression` | Full regression sweep |

Use `--strict-markers` (enabled by default in `pytest.ini`) to catch typos in marker names.

---

## 10. Page Object Model

All page interaction is encapsulated in `pages/`. Tests **never** contain raw locators.

```
pages/
├── login/
│   └── login_page.py               # LoginPage — enter credentials, click Sign In
├── admin/
│   ├── admin_navigation.py         # AdminDashboardPage — sidebar, breadcrumbs
│   ├── processing_area/
│   │   ├── create_new_area_page.py
│   │   ├── materials_page.py
│   │   ├── container_page.py
│   │   ├── machine_name_page.py
│   │   ├── station_mapping_page.py
│   │   ├── staging_area_page.py
│   │   └── workflow_page.py
│   ├── execution_source_config/
│   └── settings/
├── dashboards/
│   ├── requester_dashboard_page.py   # Make New Request wizard, history, staging area
│   ├── dispatcher_dashboard_page.py  # Requests table, dispatch action, notifications
│   └── supervisor_dashboard_page.py  # Staging area grid, cell management, auto-trips
├── fleet_manager/
│   └── manage_trips_page.py          # FM trip list verification
├── containers_page.py
└── staging_area_page.py
```

---

## 11. Utilities

| Module | Purpose |
|---|---|
| `utils/live_api_client.py` | `LiveAPIClient` — authenticated `requests.Session` against the MTS REST API. Auto-discovers the login endpoint from `/openapi.json`. |
| `utils/machine_api.py` | High-level helpers: create/delete machines, get processing areas |
| `utils/waits.py` | `wait_for_app_ready`, `table_row_exists`, `dismiss_stuck_modal` — smart Playwright waits with retry logic |
| `utils/pdf_report.py` | `ResultCollector` + `build()` — collects test outcomes and screenshots, renders a PDF report |
| `utils/report_paths.py` | Timestamped paths for `reports/`, screenshot dir, HTML summary |
| `utils/report_to_pdf.py` | Converts intermediate HTML summary to the final PDF |
| `utils/data_factory.py` | Generates unique time-stamped names/IDs for test isolation |
| `utils/test_data_cleanup.py` | Teardown helpers that remove test-created entities from the app |
| `utils/logger.py` | `get_logger(name)` — structured logging for conftest and page objects |

---

## 12. Reporting

After every `pytest` run a PDF report is written to `reports/`:

```
reports/
└── report_<YYYY-MM-DD_HH-MM-SS>/
    └── report_<timestamp>.pdf
```

The PDF contains:

1. **Header** — environment name, base URL, run start time, total duration
2. **Summary table** — total / passed / failed / skipped / errors / pass rate
3. **Full results** — every test with outcome and duration
4. **Failure details** — error message + inline screenshot for each failure

Screenshots of failures are embedded as base64 data URIs — the PDF is self-contained and can be attached to a Jira ticket as-is.

> `reports/` is git-ignored. Archive PDFs externally as needed.

---

## 13. Data Files

`data/` contains CSV templates for testing bulk-upload features:

| File | Purpose |
|---|---|
| `container_bulk_upload.csv` | Sample payload for the Admin > Container bulk-upload endpoint |
| `material_bulk_upload.csv` | Sample payload for the Admin > Material bulk-upload endpoint |

---

## 14. CI / GitHub Actions

The repository includes a `.github/` directory. A recommended workflow:

```yaml
name: AtiFlow Automation
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Install Playwright browsers
        run: playwright install chromium

      - name: Run smoke tests
        run: pytest tests/ui/ -m smoke
        env:
          BASE_URL: ${{ secrets.BASE_URL }}
          ADMIN_USERNAME: ${{ secrets.ADMIN_USERNAME }}
          ADMIN_PASSWORD: ${{ secrets.ADMIN_PASSWORD }}
          HEADLESS: "true"

      - name: Upload test report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-report
          path: reports/
```

Store `BASE_URL`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` as **GitHub Actions secrets** — never in the YAML file itself.

---

## 15. Contributing

1. **Fork** the repository and create a feature branch from `main`.
2. **Follow the Page Object pattern** — add new locators to the appropriate class in `pages/`, never inline them in a test.
3. **Add test data to `test_data.toml`** — do not hard-code values in test files.
4. **Tag your tests** with the appropriate markers defined in `pytest.ini`.
5. **Run the relevant suite locally** before opening a PR:
   ```bash
   pytest tests/ui/<your_module>/ -v
   ```
6. **Do not commit** `.env`, `reports/`, or `.cache/` — they are all git-ignored.
7. Open a **Pull Request** targeting `main` with a clear description of what was added or fixed.

---

## Quick Reference

```bash
# First-time setup
cp .env.example .env && nano .env
pip install -r requirements.txt && playwright install chromium

# Smoke test (fast, critical path)
pytest -m smoke -v

# Full UI suite
HEADLESS=true pytest tests/ui/

# Watch mode — see the browser live
HEADLESS=false pytest tests/ui/dispatcher/ -v

# Single API test module
pytest tests/api/test_processing_area_api.py -v

# Full E2E workflow
pytest tests/ui/e2e/ -v

# Against staging environment
TEST_ENV=staging pytest -m regression
```

---

*For a detailed step-by-step configuration walkthrough, see [`docs/ATIFLOW_CONFIGURATION.md`](docs/ATIFLOW_CONFIGURATION.md).*  
*For the full test coverage matrix, see [`docs/TEST_COVERAGE.md`](docs/TEST_COVERAGE.md).*
