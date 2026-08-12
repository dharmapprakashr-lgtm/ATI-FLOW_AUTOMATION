# Processing Area Sub-Tabs — Playwright Automation

UI automation framework for the "Processing Area Sub-Tabs: Staging Area, Area
Config & Containers" ticket. Built with Playwright (Python, sync API), with
both a standalone script (no pytest) and a pytest suite — Page Object Model
throughout.

## FIXED — root cause of the pytest run's 11 errors (Aug 11)

Every test errored the same way: `open()` tried clicking the "Staging
Area" tab but the page never left `/Execution_Source_Config`. The cause
was the sidebar navigation — `page.locator("div").filter(has_text=...)`,
copied straight from a codegen recording — which only worked in that
recording's specific page state (sidebar already expanded from prior
clicks), not on a fresh login.

**Fixed**: both `StagingAreaPage.open()` and `ContainersPage.open()` now
navigate directly to `{BASE_URL}/processing_area/{area}` (confirmed via
screenshot — the same URL is used across all tabs, since tab switching is
client-side) and then click the relevant tab. This should resolve all 11
setup errors from that run.

## Structure

```
processing_area_automation/
├── conftest.py                      # fixtures: browser/page setup, login, page objects
├── pytest.ini                       # markers + HTML report config
├── requirements.txt
├── .env.example
├── pages/
│   ├── base_page.py                 # shared helpers (click, fill, toast, confirm/cancel dialog)
│   ├── staging_area_page.py         # List View, Grid View, Cell Management
│   ├── processing_area_config_page.py
│   └── containers_page.py
├── tests/
│   ├── test_staging_area.py         # TC_PA_001 - TC_PA_012
│   ├── test_processing_area_config.py  # TC_PA_013 - TC_PA_016
│   └── test_containers.py           # TC_PA_017 - TC_PA_020
└── reports/                         # HTML report output (generated on run)
```

Each test file maps 1:1 to the Test Case IDs from the manual test case sheet,
referenced in the docstring of every test function.

## IMPORTANT — selector status (updated Aug 11, from codegen recording)

A `playwright codegen` recording confirmed real selectors for: login,
processing-area sidebar navigation, Staging Area / Containers tab switching,
staging area card → grid navigation, View/Manage toggle, and the cell status
combobox (Available/Reserved/Blocked appear to be set via ONE dropdown, not
separate buttons). These are wired into `pages/staging_area_page.py` and
`conftest.py` already.

**Still needs its own recording** (short, focused — one flow at a time is
easier than one long one):
1. List View filter tabs — All / Active / Inactive
2. Card Edit (pencil) icon and ⋮ overflow menu
3. Filling an Available cell with **Material** (SKU, Qty, MHE No.,
   Production Timestamp) — confirm whether this is separate fields or also
   folds into the status combobox flow
4. The **Trolley** fill option, and confirming it's hidden for the
   Yokohama Dahej project specifically
5. Processing Area Config tab — Add/Edit modal (Machine Name, Consumption
   Point dropdown + multi-add), delete + confirmation, search
6. Containers tab — Add New Container modal (all fields), Export CSV,
   Bulk Upload, search

**Known fragile selector:** the grid cell itself (`.css-11ihfi1` in
`staging_area_page.py`) is a CSS-in-JS hash class with no accessible
role/name — it works today but will break on the next frontend rebuild.
Worth asking the dev team for a `data-testid` or `aria-label` per cell
(e.g. `aria-label="cell-A1"`) — this is the highest-value fix for the
whole framework's long-term stability.

**How to record the remaining flows:**
```bash
playwright codegen --ignore-https-errors -o recorded_flow.py https://192.168.6.32
```
Click through just ONE flow (e.g. only the Material fill), close the
browser, and send over `recorded_flow.py`. Repeat per flow above — shorter
recordings are much easier to map back into the right page-object method.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

cp .env.example .env
# edit .env with real BASE_URL, credentials, and processing area name
```

## Running — two options

### Option A: Standalone script (no pytest, simplest, generates its own HTML report)

```bash
python3 run_automation.py
```

Runs against the shared "august" area — proven working (10/10 runnable
tests passing as of Aug 11).

### Option A2: Own dedicated test area (no pytest, isolated from shared data)

```bash
python3 run_automation_own_area.py
```

The SAME full test suite as Option A (TC_PA_001 through TC_PA_020, all
20 test cases from the ticket) — but creates its own dedicated processing
area first (random name, e.g. `AutoTest_53021`) instead of running
against the shared `august` area. Adds one material (diagnostic only,
doesn't block later steps), one container, then runs every confirmed
Staging Area and Container test against that new area. TC_PA_006/013 are
slightly adapted since a fresh grid starts empty — they fill a cell
first, then read it back, instead of relying on `august`'s pre-existing
data. Fully isolated — safe to run repeatedly, though it does NOT clean
up after itself (each run creates a new area; delete old ones manually
via the sidebar's ⋮ menu if that matters). Report written to
`reports/report_own_area.html`.

### Option B: pytest (more setup, better for CI / larger suites later)

```bash
pytest -m "staging_area or containers" -v
```

## Design notes

- **Page Object Model**: one class per screen/tab. Test files only call
  page-object methods and make assertions — no raw selectors inside test
  files. If the UI changes, update one page object, not every test.
- **Fixtures own setup**: `conftest.py` handles login and page-object
  instantiation so each test starts from a logged-in, correctly-navigated
  state.
- **Markers** (`p0`, `p1`, `staging_area`, `processing_area_config`,
  `containers`) let you run subsets — e.g. a fast P0-only smoke run in CI
  on every PR, full suite nightly.
- **Data cleanup**: tests that create data (e.g. `test_tc_pa_014`,
  `test_tc_pa_018`) currently don't tear down what they create. Add
  `yield`-based fixture teardown or an API-based cleanup step once the
  app exposes a delete/reset endpoint, so reruns stay idempotent.
- **Environment-specific test (TC_PA_009)**: the Yokohama Dahej / Trolley-skip
  test needs to run against an environment or tenant actually configured as
  Yokohama Dahej. Point `PROC_AREA` (or add a dedicated fixture) at that
  tenant when running this specific test.

## Extending

To add a new test case:
1. Add any new selectors needed to the relevant page object in `pages/`.
2. Add a method to the page object if the interaction is reusable.
3. Add the test function to the matching file in `tests/`, named
   `test_tc_pa_0XX_<short_description>` and referencing the Test Case ID
   in the docstring.
4. Tag it with the right `@pytest.mark` markers.
