# Project structure and maintenance

The repository is organized by responsibility. The `tests/` directory contains `api/`, `ui/`, and `common/`. Test paths, fixture names,
parameter IDs, and ordering are stable interfaces: external commands, CI jobs,
and reports can depend on them.

## Directory map

| Location | Responsibility |
| --- | --- |
| `config/` | Load environment settings, credentials, TOML test inputs, and typed specifications. |
| `data/` | Reference CSV payloads used by bulk-upload tests. |
| `pages/` | Browser page objects; keep selectors and reusable UI interactions here. |
| `tests/ui/` | Browser assertions grouped by admin, CRUD, requester, dispatcher, supervisor, and E2E. |
| `tests/common/` | Shared browser login, version, navigation, access, security, and dashboard checks. |
| `tests/api/` | Flat directory containing HTTP contract tests, MTS runners, and their pytest adapter. |
| `utils/` | Shared waits, data generation, cleanup tracking, API support, and reporting. |
| `docs/` | Coverage inventory, project structure, product configuration, and planning documents. |
| `reports/` | Generated reports; excluded from version control. |
| `.cache/pycache/` | Central Python bytecode destination. |
| `.cache/pytest/` | Pytest cache data such as last-failed test IDs. |
| `.github/` | CI workflow definitions. |

## Root files

- `conftest.py`: shared pytest fixtures, authentication, provisioning, ordering,
  cleanup, and report hooks. It remains at the root so both UI and API commands
  discover it consistently.
- `pytest.ini`: collection rules, markers, reporting options, and cache location.
- `requirements.txt`: dependencies; install into a virtual environment.
- `.env.example`: configuration template. `.env` and `.mts_token` are local secrets.
- `.editorconfig`: whitespace and encoding conventions; it does not reformat
  existing files automatically.
- `README.md`: setup, commands, and links to detailed documentation.

## Rules for adding or changing tests

1. Put shared cross-role browser checks in `tests/common/`; put feature-specific browser tests under the appropriate `tests/ui/` feature or role directory.
2. Put API tests directly in `tests/api/`; do not create a second API runner tree.
3. Name pytest modules `test_*.py` and test functions `test_*`.
   `run_mts*_automation_tests.py` files are consumed by `test_mts_automation.py`;
   they are not directly collected. Their `api_model` results describe local
   models/mock services rather than deployed product validation.
4. Preserve existing numeric UI prefixes and `SUITE_ORDER` in `conftest.py`.
   Do not reorder dependency-based tests solely to make numbering consecutive.
5. Register new markers in `pytest.ini`. Update coverage documentation when
   collected cases or behavior change.
6. Keep generated files out of source folders. Use pytest temporary directories
   for transient data and `reports/` for reports. Never commit credentials.

The `scripts/` and manual-runner folders were removed by request. All supported
suite commands use pytest. Existing page-object module paths are retained for
compatibility; unused-looking modules should not be removed without checking
imports and external usage.

## Verification commands

From the repository root:

```bash
export PYTHONPYCACHEPREFIX="$PWD/.cache/pycache"
pytest --collect-only --no-pdf
pytest tests/api/test_mts_automation.py --no-pdf
```

From `tests/api/`, `pytest --collect-only --no-pdf` must still collect the full
API-folder suite. Live UI/API execution requires the configured application and
credentials; collection and model passes are not substitutes for a live run.

## Documentation

- [Setup and commands](../README.md)
- [Configuration guide](../config/README.md)
- [Product configuration walkthrough](ATIFLOW_CONFIGURATION.md)
- [Test coverage](TEST_COVERAGE.md)
- [API execution modes](../tests/api/README.md)

The historical [development plan](plan.md) is retained as design context;
current source files and pytest collection determine the executable structure.

Shared tests retain the `ui` marker and use the same environment validation,
authentication, cleanup, and ordered collection hooks as role-specific UI tests.
Use `pytest tests/ui tests/common` to run all browser suites.
