"""Wait conditions specific to this application's MUI front end.

Playwright auto-waits for actionability, so these cover only the cases it cannot
infer: transitions that this app signals through modal state and toast text
rather than through the element being acted on.
"""

ERROR_SELECTORS = ".Toastify__toast--error, .Mui-error"
DIALOG_SELECTOR = ".MuiDialog-container"

#: Superset of ERROR_SELECTORS: also catches inline MUI field errors and ARIA
#: alerts, for callers that need "is anything error-shaped on screen right
#: now" rather than the toast text a completed action left behind.
ANY_ERROR_SELECTORS = (
    ".Toastify__toast--error",
    ".MuiAlert-standardError",
    "[role='alert']",
    ".Mui-error",
)


def is_error_visible(page, timeout=1500):
    """True if any toast/snackbar/inline error is currently on screen.

    Check each match: a hidden earlier alert must not hide a visible error.
    Success notifications also use ARIA alerts and are not validation errors.
    """
    import re

    for selector in ANY_ERROR_SELECTORS:
        for element in page.locator(selector).all():
            if not element.is_visible(timeout=timeout):
                continue
            # ARIA alerts announce successes too (including the login toast).
            # Explicit error styles still take precedence over message wording.
            if selector == "[role='alert']":
                if re.search(r"\bsuccess(?:ful(?:ly)?)?\b", element.inner_text(), re.IGNORECASE):
                    continue
            return True
    return False


def collect_error_text(page):
    """Return the app's visible error text, or "" when there is none.

    Success toasts share the error containers in places, so anything containing
    "success" is filtered out.
    """
    messages = page.locator(ERROR_SELECTORS).all_text_contents()
    return " | ".join(
        text.strip() for text in messages
        if text.strip() and "success" not in text.lower()
    )


def wait_for_modal_close(page, action, timeout=5000):
    """Wait for the open dialog to close, which is how this app signals success.

    Raises AssertionError carrying the app's own error text, which is far more
    useful than a bare Playwright timeout.
    """
    try:
        page.locator(DIALOG_SELECTOR).wait_for(state="hidden", timeout=timeout)
    except Exception:
        raise AssertionError(f"{action} failed: {collect_error_text(page) or 'Modal did not close'}")


def dismiss_stuck_modal(page):
    """Best-effort close of whatever dialog a failed step left open.

    Tries Cancel, then the title-bar close icon, then a backdrop click, then
    Escape. Never raises - it runs on the failure path, where the useful error
    has already been recorded.
    """
    import re

    try:
        cancel_btn = page.locator(f"{DIALOG_SELECTOR} button").filter(
            has_text=re.compile(r"cancel", re.IGNORECASE)
        ).first
        if cancel_btn.is_visible(timeout=1000):
            cancel_btn.click(force=True)
            page.wait_for_timeout(500)
        else:
            close_btn = page.locator(".MuiDialogTitle-root button").first
            if close_btn.is_visible():
                close_btn.click(force=True)
                page.wait_for_timeout(500)

        page.mouse.click(10, 10)
        page.wait_for_timeout(500)
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
    except Exception:
        pass


def wait_for_app_ready(page, timeout=15000, allow_login=False):
    """Wait for the rendered app shell; polling does not prevent UI readiness.

    Restored sessions may redirect to login, which callers handle explicitly.
    A fresh login must render the authenticated shell to count as ready.
    """
    page.wait_for_load_state("domcontentloaded", timeout=timeout)
    selector = "#operator-sidebar-root:visible"
    if allow_login:
        selector += ", input[type='password']:visible"
    page.locator(selector).first.wait_for(state="visible", timeout=timeout)


def delete_row_by_name(page, name):
    """Find a table row containing ``name`` and delete it via its row menu.

    Shared by the generic Add/Edit/Delete tabs (Staging Area, WIP Inventory,
    Workstation) that don't have a dedicated page object yet - all three
    tables share this same "last button in the row opens delete, confirm via
    a DELETE button" shape. Returns False when no matching row exists.

    Matches on exact text, not substring: a plain ``has_text=name`` filter
    would also match e.g. "crud_pick" when looking for "pick" - this suite's
    own ``crud_<name>`` naming convention makes that collision realistic, and
    whichever row sorts first would then get deleted instead of the intended
    one (see AdminDashboardPage._row_by_exact_name for the same fix).
    """
    row = page.locator("tr").filter(has=page.get_by_text(name, exact=True))
    if row.count() == 0:
        return False
    row.first.locator("button").last.click(force=True)
    page.wait_for_timeout(500)
    confirm = page.get_by_role("button", name="DELETE")
    if confirm.is_visible(timeout=2000):
        confirm.click(force=True)
        page.wait_for_timeout(1500)
    return True


def table_row_exists(page, name, timeout=5000):
    """Allow asynchronously loaded rows to appear before seeding a record."""
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    row = page.locator("tr").filter(has=page.get_by_text(name, exact=True)).first
    try:
        row.wait_for(state="visible", timeout=timeout)
    except PlaywrightTimeoutError:
        return False
    return True
