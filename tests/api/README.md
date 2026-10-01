# API test suite

Run all collected API-folder tests from this directory:

```bash
cd tests/api
pytest
```

Or from the repository root:

```bash
pytest tests/api
```

Pytest collects 310 cases: 128 existing cases and 182 cases from the seven
`run_mts*_automation_tests.py` scripts. The root configuration loads the project
settings and generates the usual consolidated PDF report.

Run only the legacy MTS cases:

```bash
pytest -m api_model
```

Exclude those model/mock checks:

```bash
pytest -m 'not api_model'
```

Check collection without running tests:

```bash
pytest --collect-only --no-pdf
```

The centralized `test_mts_automation.py` adapter discovers literal `record(...)`
case IDs without executing the scripts during collection. Each legacy suite runs
once in a separate process, preserving its original case order and shared state.
Each result appears as a separate pytest item, and recorded failures fail pytest.
Selecting one case still executes its underlying suite to establish that state.

The adapter uses pytest temporary directories for the legacy hardcoded output
and scratch paths. `execution.log` and `results.json` live there during execution; the temporary
directories are removed at module teardown. A crashed or timed-out runner fails its cases instead of reporting
success. Original standalone scripts remain usable as before.

These legacy checks are marked `api_model`: they exercise local models/mock
servers and some network probes. MTS-146 and MTS-147 explicitly use their model
mode in this API adapter; they do not attempt browser testing or silently fall
back from live UI failures. Passing these cases does not verify the live API/UI.
The existing live API tests retain their configured endpoints and credentials.

Operational server repair utilities are not part of this test suite.

API fixtures delete their owned processing areas, machines, and mappings even
when assertions fail. Cleanup failures are reported; pre-existing records and
PDF reports are preserved.
