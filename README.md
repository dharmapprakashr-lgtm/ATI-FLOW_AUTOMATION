# ATIFlow Automation

Python, pytest, and Playwright automation for ATIFlow UI workflows, HTTP API
contracts, and legacy MTS model checks.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Configure `.env` using `.env.example`, then update `config/test_data.toml` for
the target environment. Keep credentials and bearer tokens out of version control.
See [configuration](config/README.md) for details.

`TEST_ENV` selects `config/environments/<env>.yaml` (default `qa`). Environment
variables and `.env` override YAML defaults. The staging profile needs a
`BASE_URL` override. UI tests require admin/role configuration; live API tests
require the API URL and a valid token.

## Run tests

```bash
pytest --collect-only --no-pdf           # discovery without execution
pytest                                 # complete suite
pytest tests/ui tests/common           # all browser suites
pytest tests/common                    # shared browser checks
pytest tests/api                       # HTTP contracts and MTS models
pytest tests/api -m 'not api_model'      # HTTP contracts only
pytest tests/api -m api_model           # legacy model/mock checks
pytest tests/ui/admin/processing_area  # processing-area administration
pytest tests/ui/requester
pytest tests/ui/dispatcher
pytest tests/ui/supervisor
pytest tests/ui --headed -rs
```

You can also run `pytest` directly inside `tests/api/`. The current inventory is
483 cases: 147 role/feature UI, 26 common, and 310 API-folder cases (128 HTTP contracts + 182 model checks). Collection counts are not pass counts. Legacy model passes
are not evidence that deployed API/UI behavior works.

UI test ordering is defined by `SUITE_ORDER` in `conftest.py`. Preserve numeric
file ordering and shared setup dependencies. Avoid simultaneous runs against the
same configured test records. E2E tests can submit requests and interact with
Fleet Manager.

## Project structure

```text
config/                    Environment, credentials, and test-data configuration
data/                      Reference CSV bulk-upload payloads
pages/                     Browser page objects
  admin/                   Processing-area and execution-source administration
  dashboards/              Requester, dispatcher, and supervisor pages
  fleet_manager/           Fleet Manager trip verification
  login/                   Authentication pages
tests/
  common/                  Shared login, navigation, access, and security checks
  api/                     HTTP tests, MTS scripts, and centralized pytest adapter
  ui/
    admin/                 Processing-area and execution-source suites
    crud/                  Throwaway entity lifecycle and API/UI consistency
    requester/             Requester workflows
    dispatcher/            Dispatcher dashboard and tasks
    supervisor/            Supervisor dashboard
    e2e/                   Cross-role flows and Fleet Manager verification
utils/                     Waits, API helpers, ownership tracking, and reporting
docs/                      Coverage, architecture, and product documentation
.cache/                    Generated Python and pytest caches (gitignored)
reports/                   Generated run reports (gitignored)
conftest.py                Shared pytest fixtures, ordering, cleanup, and reporting
pytest.ini                 Discovery patterns and markers
requirements.txt           Runtime/test dependencies
```

Settings and notifications remain in the processing-area suite as `test_18` and
`test_19` to preserve the existing setup order. 

## Reports and cleanup

Pytest writes one combined `reports/report_<timestamp>.pdf` per run. Use
`--no-pdf` to disable it. `REPORT_KEEP_RUNS` defaults to 20; set `0` to retain all
reports.

Automatic teardown removes tracked test-created UI records and API fixture
records. MTS temporary model directories are removed after their module runs.
Existing records are not claimed by create-if-missing helpers. Direct UI actions
outside those helpers, changes to pre-existing records, and force-killed runs
may need manual cleanup. Cleanup failures are surfaced.

`CLEANUP_TEST_DATA=0 pytest ...` disables session UI cleanup for debugging; API
fixture cleanup still runs. See the coverage document for precise boundaries.

## Documentation and tools

- [Project layout and maintenance](docs/PROJECT_STRUCTURE.md)
- [Detailed test coverage](docs/TEST_COVERAGE.md)
- [Environment and data configuration](config/README.md)
- [API suite usage](tests/api/README.md)
- [CRUD suite](tests/ui/crud/README.md)
- [Product configuration walkthrough](docs/ATIFLOW_CONFIGURATION.md)
- [Demo readiness](docs/DEMO_READINESS.md)
- [WIP inventory scenarios](docs/WIP_INVENTORY_TEST_CASES.md)
- [Historical development plan](docs/plan.md)

The historical plan is design context; the collected tests and coverage
inventory describe the current executable suite.

## Generated caches

Pytest metadata is stored in `.cache/pytest/`.

Pytest routes project imports and child Python processes to `.cache/pycache/`,
which is gitignored. Python may create a root `__pycache__` while loading pytest's
initial configuration before this setting takes effect. To route caches from
interpreter startup as well (including standalone Python commands), set this
once in your terminal from the repository root:

```bash
export PYTHONPYCACHEPREFIX="$PWD/.cache/pycache"
pytest
```

The export remains active for that terminal, including runs from `tests/api/`.
It belongs in the shell environment; placing it only in `.env` is too late for
Python startup imports.
# AtiFlowAutomation
