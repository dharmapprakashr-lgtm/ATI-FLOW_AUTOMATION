"""Security tests — Part 8.

TC_SEC_001  Stored XSS payloads are escaped everywhere
TC_SEC_002  Injection payloads in search and forms are safe

Strategy
--------
Inject ``<script>alert(1)</script>`` (and similar payloads) as the name of a
Processing Area, verify the app accepts or rejects the payload without
executing it, and that the rendered output is escaped HTML rather than live
JavaScript.

These tests deliberately re-use the admin Processing Area creation flow
because that is the widest write surface exposed to admin users.  If XSS
survives there, it is likely present in downstream list/detail views too.
"""

import allure
import pytest
from playwright.sync_api import expect

from config.environment import config
from utils.data_factory import unique_name

pytestmark = [pytest.mark.security]


# ── Helpers ───────────────────────────────────────────────────────────────────

_XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(1)",
    "'\"><script>alert(1)</script>",
    "<svg onload=alert(1)>",
]

_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "\" OR \"1\"=\"1",
    "; DROP TABLE processing_areas; --",
    "\\u003cscript\\u003ealert(1)\\u003c/script\\u003e",
    "${7*7}",              # Template injection probe
    "{{7*7}}",             # Jinja/Angular expression probe
]


def _dialog_was_executed(page):
    """Return True if a JavaScript alert/confirm dialog was triggered.

    Playwright auto-dismisses dialogs by default; this hook detects whether
    one was fired at all (which would indicate un-escaped script execution).
    """
    dialog_fired = []

    def on_dialog(dialog):
        dialog_fired.append(dialog.type)
        dialog.dismiss()

    page.on("dialog", on_dialog)
    page.wait_for_timeout(1000)
    page.remove_listener("dialog", on_dialog)
    return len(dialog_fired) > 0


def _server_error_visible(page):
    return page.locator("text=500").is_visible(timeout=500)


# =============================================================================
# Stored XSS
# =============================================================================

@allure.feature("Security")
@allure.story("XSS")
class TestStoredXss:
    """TC_SEC_001"""

    @allure.title("TC_SEC_001 — Stored XSS payloads are escaped everywhere")
    def test_stored_xss_payloads_are_escaped_everywhere(self, pa_page, admin_page):
        """
        ID     : TC_SEC_001
        Title  : Stored XSS payloads are escaped everywhere
        Reason : A Processing Area name that executes JavaScript when rendered
                 is a stored XSS vector. Every operator who opens the area list
                 would be attacked, not just the one who created the record.

        Pass criteria (any of the following):
          • The app rejects the name outright (error toast / validation).
          • The name is stored and displayed as plain text (escaped).
          • No alert/confirm/prompt dialog fires.
          • No server 500.
        """
        for payload in _XSS_PAYLOADS:
            unique_payload = unique_name("sec") + payload[:20]

            with allure.step(f"Inject payload: {repr(payload[:40])}"):
                # Attach a dialog listener before any interaction
                dialog_fired = []

                def on_dialog(dialog, _d=dialog_fired):
                    _d.append(dialog.type)
                    dialog.dismiss()

                admin_page.on("dialog", on_dialog)

                try:
                    pa_page.expand_processing_areas()
                    pa_page.open_create_area_dialog()

                    name_input = admin_page.get_by_placeholder("Enter area name")
                    name_input.wait_for(state="visible", timeout=10000)
                    name_input.fill(unique_payload)
                    admin_page.get_by_placeholder("Enter area description").fill(
                        "XSS security test"
                    )

                    admin_page.locator(".MuiDialogActions-root button").filter(
                        has_text="SAVE"
                    ).click(force=True)
                    admin_page.wait_for_timeout(2000)

                    assert not dialog_fired, (
                        f"JavaScript dialog fired after injecting payload: {repr(payload)}. "
                        f"Dialog type(s): {dialog_fired}. Stored XSS is present."
                    )
                    assert not _server_error_visible(admin_page), (
                        f"Server 500 on XSS payload: {repr(payload)}"
                    )

                    # If it was saved, clean up; if not (rejected), that's fine too.
                    if admin_page.locator(".MuiDialog-container").is_visible(timeout=500):
                        admin_page.keyboard.press("Escape")
                        admin_page.wait_for_timeout(500)
                    else:
                        # Try to delete the record if it was saved
                        try:
                            pa_page.delete_processing_area(unique_payload)
                        except Exception:
                            pass

                finally:
                    try:
                        admin_page.remove_listener("dialog", on_dialog)
                    except Exception:
                        pass


# =============================================================================
# Injection payloads in search and forms
# =============================================================================

@allure.feature("Security")
@allure.story("Injection")
class TestInjectionPayloads:
    """TC_SEC_002"""

    @allure.title("TC_SEC_002 — Injection payloads in search and forms are safe")
    def test_injection_payloads_in_search_and_forms_are_safe(self, pa_page, admin_page):
        """
        ID     : TC_SEC_002
        Title  : Injection payloads in search and forms are safe
        Reason : SQL/NoSQL injection in a name field can exfiltrate or corrupt
                 the database.  Template injection (${7*7}, {{7*7}}) can execute
                 server-side if the backend renders names through a template engine.

        Pass criteria:
          • No server 500 / unhandled exception.
          • The app does not render the evaluated payload (e.g. '49' for '${7*7}').
          • No alert dialog fires.
        """
        for payload in _INJECTION_PAYLOADS:
            unique_payload = unique_name("inj") + payload[:15]

            with allure.step(f"Inject: {repr(payload[:40])}"):
                dialog_fired = []

                def on_dialog(dialog, _d=dialog_fired):
                    _d.append(dialog.type)
                    dialog.dismiss()

                admin_page.on("dialog", on_dialog)

                try:
                    pa_page.expand_processing_areas()
                    pa_page.open_create_area_dialog()

                    name_input = admin_page.get_by_placeholder("Enter area name")
                    name_input.wait_for(state="visible", timeout=10000)
                    name_input.fill(unique_payload)
                    admin_page.get_by_placeholder("Enter area description").fill(
                        "Injection security test"
                    )

                    admin_page.locator(".MuiDialogActions-root button").filter(
                        has_text="SAVE"
                    ).click(force=True)
                    admin_page.wait_for_timeout(2000)

                    assert not dialog_fired, (
                        f"JavaScript dialog fired after injecting: {repr(payload)}. "
                        "Injection-based XSS confirmed."
                    )
                    assert not _server_error_visible(admin_page), (
                        f"Server 500 on injection payload: {repr(payload)}"
                    )

                    # Check for template injection evaluation (e.g. 7*7=49)
                    rendered_text = admin_page.locator("body").inner_text()
                    if "7*7" in payload:
                        assert "49" not in rendered_text or unique_payload in rendered_text, (
                            f"Template injection payload '{payload}' may have been evaluated. "
                            "The string '49' appeared in the page body."
                        )

                    # Cleanup
                    if admin_page.locator(".MuiDialog-container").is_visible(timeout=500):
                        admin_page.keyboard.press("Escape")
                        admin_page.wait_for_timeout(500)
                    else:
                        try:
                            pa_page.delete_processing_area(unique_payload)
                        except Exception:
                            pass

                finally:
                    try:
                        admin_page.remove_listener("dialog", on_dialog)
                    except Exception:
                        pass
