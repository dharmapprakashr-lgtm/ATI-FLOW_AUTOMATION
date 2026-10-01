# Configuration guide

Most changes belong in `.env`, an environment YAML file, or `test_data.toml`.
The Python modules read those values and prepare them for fixtures and tests.

```text
.env                          Login credentials and local environment overrides
config/
├── README.md                 Start here
├── environments/
│   ├── qa.yaml               QA defaults
│   └── staging.yaml          Staging defaults
├── test_data.toml            Names, bindings, and inputs used by tests
├── environment.py            Loads .env and the selected environment YAML
├── data.py                   Reads TOML into TestData attributes
├── processing_area.py        Groups test inputs into typed entity specifications
├── credentials.py            Builds shared and E2E device login credentials
└── __init__.py               Package description; no configuration loading
```

## Where to make changes

| Change | File |
|---|---|
| Admin, MES, or Fleet Manager login credentials | Root `.env` |
| Target environment | `TEST_ENV` in `.env` or the process environment |
| Environment URLs, timeouts, and browser defaults | `environments/<TEST_ENV>.yaml` |
| Local overrides such as `BASE_URL` or `HEADLESS` | Root `.env` |
| Processing areas, materials, machines, stations, workflows | `test_data.toml` |
| Device names, passwords, and bindings | `[devices]` / `[e2e_devices]` in `test_data.toml` |
| Isolated E2E inputs | `[e2e_*]` sections in `test_data.toml` |
| A new TOML field exposed to tests | `data.py` |
| How values are grouped for page-object calls | `processing_area.py` |
| Browser setup, authentication, seeding, and cleanup | Root `conftest.py` |

Environment resolution is YAML defaults, then `.env`, then existing process
environment variables. `TEST_ENV` defaults to `qa`. Existing process variables
are not overwritten by `.env`.

## How the pieces connect

```text
.env + environments/*.yaml → environment.py → config (Settings instance)
test_data.toml             → data.py        → TestData
                                              ├─ processing_area.py → entity specs
                                              └─ credentials.py     → device credentials

conftest.py uses these objects to prepare browsers and test data.
Tests use page objects to interact with AtiFlow and assert the results.
```

Use explicit imports so the source of each value is clear:

```python
from config.environment import config
from config.data import TestData
from config.processing_area import material_spec, workflow_specs
from config.credentials import requester_credentials
```

`data.py` is the Python reader; `test_data.toml` is the editable input file.
Device credentials must match the records that fixtures create, so they continue
to come from TOML. Admin, MES, and Fleet Manager credentials come from `.env`.
Authentication sessions stay in memory; no auth-state JSON files are required.

## Checking a configuration change

From the repository root:

```bash
python3 -m pytest --collect-only --no-pdf -q
```

This checks imports and collection without launching browsers or changing the
live application. Actual UI behavior still requires a test run.
