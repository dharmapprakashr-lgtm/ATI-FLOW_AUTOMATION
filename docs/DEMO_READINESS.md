# UI demo readiness — 2026-09-28

Run from the repository root with the configured QA application reachable:

```bash
# Rehearsal, with a PDF report
HEADLESS=True python3 -m pytest tests/ui -m smoke

# Visible browser for the demo
python3 -m pytest tests/ui -m smoke --headed
```

Use the `tests/ui` path: plain `pytest` also runs API contract tests, which have separate bearer-token configuration and known backend validation failures. The smoke marker currently selects 68 UI checks, rather than the older 14-test count elsewhere in the README. Reports are written to `reports/report_<timestamp>.pdf`.

## Causes corrected

- Machine API/UI tests previously read an expired token from disk and failed during setup with HTTP 401. They now use the current admin browser session token, in memory, against the same application. Standalone API tests retain their explicit token configuration.
- Forced clicks could miss the area dialog or requester wizard. Area creation, validation, navigation, and security tests now use a shared dialog helper with visible-state checks.
- The machine form now selects the point type before filling and checking the name, and submits with normal browser actionability checks.
- Success alerts such as “Logged In successfully” no longer count as errors. Visible errors are checked even when an earlier alert is hidden.
- Dispatcher All-tab pagination initially renders a partial total. Navigation now waits for the larger All-tab API response before inspecting pagination. The full-page scan chooses a supported page size instead of silently timing out on an unavailable option.

## Environment prerequisites and remaining issues

- The application currently reports **MES Connections: Connection issues detected**. The dedicated MES health test remains a failure; restoring the configured MES service is an application/environment task. The rendering test still verifies that an explicit status appears.
- Some scenarios legitimately skip when the configured device has only one bound machine/staging area, the dispatcher queue is empty, or all staging cells are locked. These conditions are reported by the existing tests.
- Session restoration currently falls back to UI login because the app stores authentication in sessionStorage. Its warning does not indicate a failed login.
- These tests create and delete QA records. Keep the configured QA server and required Fleet Manager/MES test data available; do not run overlapping suites that rebuild the shared baseline.

## Verification

- Machine validation and API/UI consistency: **7 passed**.
- Error-alert regression checks: **6 passed**.
- Area validation, navigation, and security after the dialog fix: **23 passed, 1 existing skip**.
- Full smoke rehearsal: in progress; see the generated PDF for the final outcome.
