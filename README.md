# ATIFlow Automation Test Suite

This repository contains the automated regression suite for ATIFlow. It uses
Python, pytest, and Playwright to verify browser workflows, HTTP API contracts,
legacy MTS model checks, and small unit-level helpers.

The root `README.md` is the central guide for the test suite. Folder-level test
README files have been removed so contributors have one place to read, update,
and maintain test instructions.

## Project Structure and Coverage

The suite is organized around the product areas that need to work together:

| Area | Location | Purpose |
| --- | --- | --- |
| Shared UI checks | `tests/ui/common/` | Login, version display, dashboards, access control, security, navigation, and non-functional checks. |
| Admin processing area | `tests/ui/admin/processing_area/` | Processing area setup, tabs, materials, machines, containers, station mappings, workflows, staging areas, settings, and notifications. |
| Admin execution source config | `tests/ui/admin/execution_source_config/` | Requester, dispatcher, supervisor, MES configuration, and validation flows. |
| CRUD lifecycle | `tests/ui/crud/` | Temporary entity create/read/update/delete checks and selected API/UI consistency checks. |
| Requester role | `tests/ui/requester/` | Requester dashboard, machine/workflow context, staging area search, SKU selection, item quantities, request summary, submit, and cancel flows. |
| Dispatcher role | `tests/ui/dispatcher/` | Dispatcher dashboard, station switching, sorting, search, tabs, request details, dispatch action, pagination, and notifications. |
| Supervisor role | `tests/ui/supervisor/` | Supervisor dashboard shell, processing area selector, staging area list/detail/manage flows, realtime refresh, notifications, auto trips, and access control. |
| End to end | `tests/ui/e2e/` | Cross-role workflow from admin setup through requester, dispatcher, supervisor, and Fleet Manager verification. |
| API contracts | `tests/api/` | Live processing area, machine, and material/station mapping contracts. See the API guide below for individual modules. |
| Legacy MTS model checks | `tests/api/test_mts_automation.py` | Central pytest adapter for model/mock MTS cases marked `api_model`. These are not proof of live API or UI behavior. |
| Unit checks | `tests/unit/` | Focused helper-level behavior. |

See `docs/TEST_COVERAGE.md` for the detailed case inventory and coverage notes.

Supporting files and folders:

| Location | Purpose |
| --- | --- |
| `config/` | Environment profiles, credentials, and test-data configuration. |
| `data/` | Reference CSV payloads and upload data. |
| `docs/` | Detailed coverage inventory and product notes. |
| `pages/` | Playwright page objects. |
| `utils/` | API helpers, waits, cleanup, logging, and reporting. |
| `reports/` | Generated PDF reports; ignored by git. |
| `conftest.py` | Shared fixtures, API authentication, ordering, cleanup, and reporting. |
| `pytest.ini` | Discovery rules, markers, cache, and default options. |
| `requirements.txt` | Python dependencies. |

## Setup

Create a virtual environment and install dependencies from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Create a local `.env` from `.env.example`, then update `config/test_data.toml`
for the target environment. Do not commit credentials, bearer tokens, or other
environment secrets.

Environment selection works as follows:

- `TEST_ENV` selects `config/environments/<env>.yaml`; the default is `qa`.
- Environment variables and `.env` values override YAML defaults.
- The staging profile requires a `BASE_URL` override.
- UI tests require configured admin and role credentials.
- Live API tests require the API base URL and a valid token.

For configuration details, read `config/README.md`.

## Running Tests

Run commands from the repository root unless noted otherwise.

```bash
# Check discovery without executing test bodies or generating a report
pytest --collect-only --no-pdf

# Run the complete suite
pytest

# Run all UI tests
pytest tests/ui

# Run shared UI checks
pytest tests/ui/common

# Run API-folder tests
pytest tests/api

# Run live API contracts only
pytest tests/api -m 'not api_model'

# Run legacy MTS model/mock checks only
pytest tests/api -m api_model

# Run individual UI suites
pytest tests/ui/admin/processing_area
pytest tests/ui/admin/execution_source_config
pytest tests/ui/crud
pytest tests/ui/requester
pytest tests/ui/dispatcher
pytest tests/ui/supervisor
pytest tests/ui/e2e

# Run browser tests headed and show skip/xfail reasons
pytest tests/ui --headed -rs

# Run against staging configuration
TEST_ENV=staging pytest tests/ui/admin/processing_area
```

Pytest intentionally has no fixed `testpaths` setting. Running `pytest` from a
subdirectory collects that subdirectory's tests. For example, running `pytest`
inside `tests/api/` collects the API suite.

## Markers

Markers are registered in `pytest.ini` and can be combined with `-m`:

| Marker | Meaning |
| --- | --- |
| `ui` | Browser UI tests. |
| `api` | HTTP API contract tests. |
| `api_model` | Legacy MTS model/mock harness checks. |
| `integration` | API and browser consistency checks. |
| `admin`, `requester`, `dispatcher`, `supervisor` | Role or area-specific tests. |
| `crud` | Create, read, update, and delete lifecycle checks. |
| `smoke`, `regression`, `e2e` | Suite selection by intent or release scope. |
| `auth`, `access_control`, `security`, `nfr`, `ui_nav` | Cross-cutting behavior checks. |
| `admin_pa`, `exec_config`, `settings`, `dashboards` | Feature-specific UI checks. |

Examples:

```bash
pytest -m smoke
pytest tests/ui -m 'admin and not crud'
pytest tests/api -m 'not api_model'
```

## Execution Order

Full UI runs are ordered by `SUITE_ORDER` in `conftest.py`. Numeric file prefixes
inside each suite still control local order. The high-level order is:

1. Login and application version checks.
2. Admin processing area setup.
3. Admin execution source configuration.
4. CRUD lifecycle checks.
5. Access control.
6. Requester, dispatcher, supervisor, and shared dashboard checks.
7. End-to-end workflow checks.
8. Security checks.
9. Non-functional checks.
10. UI navigation checks.

Keep this order in mind when adding tests. Several role suites depend on admin
records and device records created earlier in a full run.

## API Testing Guide

The API folder contains live HTTP contract tests against the configured ATIFlow
backend and legacy model/mock checks exposed through `test_mts_automation.py`.
Both are included in `pytest tests/api`.

### Live API Coverage

Endpoint paths are relative to `MTS_BASE_URL`. These tests create, update, and
delete records: use a test environment with permission for these operations.

| Test module in `tests/api/` | Endpoint family | Checks |
| --- | --- | --- |
| `test_processing_area_api.py` | `/mts/processing-area/` | List/fetch, creation, duplicate names, missing/empty fields, long and special names, updates, deletion, invalid IDs, and authentication. |
| `test_processing_area_machines_api.py` | `/mts/processing-area-machines/` | CRUD, required fields, duplicates, pagination, area filtering and deletion, production/consumption point types, name lookup, invalid updates, and authentication across operations. |
| `test_material_station_mapping_api.py` | `/mts/material-station-mapping/` | CRUD and upserts, required fields, area/material filtering, bulk create/update, deletion by mapping key, preservation of unrelated mappings, and authentication. |

Processing-area tests contain their own client. Machine tests use
`utils/machine_api.py` and the `machine_api` fixture in `conftest.py`. Mapping
tests use their own `MappingRun` helper and fixtures. These helpers track created
records for teardown; the machine helper also tracks unexpected successful
creates in negative tests.

### API Configuration and Authentication

After installing `requirements.txt`, add these settings to the root `.env`,
replacing the placeholders:

```dotenv
MTS_BASE_URL=http://your-test-api-host:8000
MTS_TOKEN=your-test-environment-token
```

Alternatively, omit the token and set `ADMIN_USERNAME` and `ADMIN_PASSWORD` for
automatic login. The three live API modules do not launch a browser.

| Setting | Behavior |
| --- | --- |
| `MTS_BASE_URL` | Preferred backend URL. Bootstrap falls back to `BASE_URL`, then `http://localhost:8000`. Set this explicitly; individual helpers have different defaults. Use the service root without an endpoint path. |
| `MTS_TOKEN` | Preferred token, either raw or prefixed with `Bearer `. |
| `API_BEARER_TOKEN` | Alternative when `MTS_TOKEN` is absent. |
| `MTS_TOKEN_FILE` | Optional token-file path. Bootstrap also checks `tests/api/.mts_token` and root `.mts_token`. |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | Credentials used when no token is found. Bootstrap tries `/mts/auth/device/login`, then alternate authentication endpoints. |
| `MSM_STATION_ID` | Initial mapping station ID; defaults to `pick3_gg`. |
| `MSM_UPDATED_STATION_ID` | Replacement mapping station ID; defaults to `pick4_gg`. |
| `config/test_data.toml` | Machine helper inputs, including temporary name prefixes, descriptions, and point types. |

Bootstrap loads `.env` without overriding shell variables. Token resolution is:
environment variables, token files, then automatic login. A supplied expired
token is not automatically refreshed. API setup can run during `--collect-only`
and model-only selection, so these commands may still attempt authentication.
Bootstrap currently prints a token prefix; redact authentication output before
sharing logs.

### Run Live API Tests

```bash
# All live contracts
pytest tests/api -m 'not api_model' -rs

# One endpoint family
pytest tests/api/test_processing_area_api.py
pytest tests/api/test_processing_area_machines_api.py
pytest tests/api/test_material_station_mapping_api.py

# One case
pytest tests/api/test_processing_area_api.py::test_pa_get_001_get_all_processing_areas

# Authentication cases
pytest tests/api -m 'not api_model' -k auth

# Inspect discovery without running test bodies
pytest tests/api --collect-only --no-pdf
```

Use the API folder with `-m 'not api_model'` for all live contracts. Some live
modules do not declare the `api` marker, so adding `-m api` can omit tests.

### Legacy MTS Coverage

These seven source modules are excluded from normal directory collection by
`collect_ignore` in `conftest.py`. Select their cases through the adapter using
the names below instead of targeting the source files directly.

| Source module in `tests/api/` | Selection name (`-k`) | Coverage |
| --- | --- | --- |
| `test_mes_integration_polling.py` | `mes_integration_polling` | Polling windows, scheduling, checkpoints, inventory processing, deduplication, and recovery using a local engine and MES HTTP probes/fallback. |
| `test_central_config_health.py` | `central_config_health` | Connection configuration, validation, health states, notifications, history, rollback, and material/container models. |
| `test_processing_staging_grid.py` | `processing_staging_grid` | Staging list/grid views and cell management using a local API and model. |
| `test_material_master_config.py` | `material_master_config` | Material configuration, validation, CRUD, and local API/model behavior. |
| `test_settings_rest_api.py` | `settings_rest_api` | Local REST endpoints for connections, configuration, health, and notifications. |
| `test_tablet_login_security.py` | `tablet_login_security` | Local login/session endpoints and tablet login UI-model checks. |
| `test_external_connections_setup.py` | `external_connections_setup` | Connection discovery, credentials, validation, persistence, lifecycle, and health behavior. |

```bash
# All legacy cases
pytest tests/api/test_mts_automation.py

# MES polling cases
pytest tests/api/test_mts_automation.py -k mes_integration_polling

# Another legacy suite
pytest tests/api/test_mts_automation.py -k settings_rest_api

# List case IDs, then select one
pytest tests/api/test_mts_automation.py --collect-only --no-pdf
pytest tests/api/test_mts_automation.py -k 'MTS-167-TC-01'
```

The adapter discovers `record(...)` cases without importing the runners and
reports each case independently with its suite, ID, title, execution mode, and
actual result. Each selected suite runs once in a child process with a
180-second timeout and a temporary working directory. Selecting one case still
executes its entire legacy runner internally. Temporary results and execution
logs are removed at teardown.

Staging-grid and material-master cases run with `use_playwright=False`. The MES
runner has hardcoded service URLs and can fall back to an embedded HTTP server
when the remote MES request fails. `MTS_BASE_URL` does not configure every legacy
URL. Passing `api_model` checks therefore does not establish that the deployed
backend, MES integration, or browser workflow works.

### API Results and Troubleshooting

| Symptom | What to check |
| --- | --- |
| Connection refused or timeout | Check `MTS_BASE_URL`, backend availability, and test-network access. |
| Login warning or missing-token error | Supply a valid token or check admin credentials and login endpoints. |
| Unexpected `401` or `403` | Check token expiry and account permissions. Authentication-negative cases intentionally expect rejection. |
| Mapping validation failure | Check station IDs, request data, and the deployed contract against the assertion output. |
| `XFAIL` | Read the reason with `-rs`. Some processing-area and mapping cases record known backend gaps; this is not a pass. |
| Cleanup failure | Inspect teardown output and the temporary records it identifies. API cleanup still runs with `CLEANUP_TEST_DATA=0`. |
| Legacy runner failure or timeout | Check the runner error, local server port availability, and MES connectivity where applicable. Scratch logs are temporary. |
| No cases from a legacy source module | Select its suite through `test_mts_automation.py` with `-k`. |

API results use the same combined PDF report as UI results. Add `--no-pdf` to
disable report generation. Avoid concurrent legacy runs because some embedded
servers use fixed ports.

## CRUD Suite Notes

`tests/ui/crud/` uses throwaway entities to verify lifecycle behavior without
editing shared role devices. It covers processing areas, material/container
records, machines, station mappings, devices, and selected machine API/UI
consistency. Some temporary names are fixed in `config/test_data.toml`, so do
not run multiple suites concurrently against the same environment.

## Reports

By default, pytest writes one combined PDF report:

```text
reports/report_<timestamp>.pdf
```

Use `--no-pdf` for collection checks, quick local debugging, or CI jobs that do
not need PDF output:

```bash
pytest tests/api --no-pdf
```

`REPORT_KEEP_RUNS` controls PDF retention and defaults to `20`. Set it to `0` to
keep all generated reports.

## Cleanup and Test Data

The root fixtures track and clean up records created by supported helpers:

- UI-created processing areas, role devices, and helper-created child records.
- API-created processing areas, machines, and mappings.
- Temporary directories used by the MTS adapter.

Cleanup failures are surfaced as warnings or test failures where appropriate.
Pre-existing records are not claimed by the cleanup helpers. Direct UI actions
outside supported helpers, changes to pre-existing records, and interrupted
processes may require manual cleanup.

For UI debugging, you can keep created UI data:

```bash
CLEANUP_TEST_DATA=0 pytest tests/ui/admin/processing_area
```

API fixture cleanup still runs even when UI cleanup is disabled.

## Development Guidelines

- Add new tests under the suite that matches the user workflow or API area.
- Use existing page objects, fixtures, data factories, and API helpers before
  creating new abstractions.
- Register new pytest markers in `pytest.ini`.
- Preserve numeric UI file prefixes when order matters.
- Update `docs/TEST_COVERAGE.md` when adding, removing, or materially changing
  test coverage.
- Avoid parallel runs against the same configured test records unless the data
  is explicitly isolated.
- Keep secrets in local environment files or secret stores, never in git.

## Useful Documentation

- `docs/TEST_COVERAGE.md` - detailed coverage matrix and current inventory.
- `config/README.md` - environment and test-data configuration.
- `docs/ATIFLOW_CONFIGURATION.md` - product configuration walkthrough.
- `docs/WIP_INVENTORY_TEST_CASES.md` - deferred WIP inventory scenarios.
- `docs/plan.md` - historical development context.

## Cache Notes

Pytest metadata is stored in `.cache/pytest/`.

Project imports and child Python processes route bytecode caches to
`.cache/pycache/`, which is gitignored. Python may still create a root
`__pycache__` while loading initial pytest configuration. To route interpreter
startup caches as well, run this once in the terminal from the repository root:

```bash
export PYTHONPYCACHEPREFIX="$PWD/.cache/pycache"
pytest
```
