"""Non-Functional Requirements — Part 9.

TC_NFR_001  Supported browsers and shopfloor viewports render correctly
TC_NFR_002  Keyboard operation and readability on shopfloor screens

These tests are intentionally lightweight probes: they do not re-execute
every functional test under each viewport, but they confirm that the admin
console is at least navigable and readable at the dimensions shop-floor
hardware uses.
"""

import allure
import pytest
from playwright.sync_api import expect

from config.environment import config
from pages.login.login_page import LoginPage
from utils.waits import wait_for_app_ready

pytestmark = [pytest.mark.nfr]


# ── Shop-floor viewport presets ───────────────────────────────────────────────

_SHOPFLOOR_VIEWPORTS = [
    # (label,           width,  height)
    ("Tablet landscape",  1280,   800),
    ("Tablet portrait",    768,  1024),
    ("10-inch panel",      1024,  600),
    ("FHD monitor",       1920,  1080),
    ("HD monitor",        1366,   768),
]


# =============================================================================
# Browser / viewport rendering
# =============================================================================

@allure.feature("Non-Functional")
@allure.story("Viewport rendering")
class TestViewportRendering:
    """TC_NFR_001"""

    @allure.title("TC_NFR_001 — Supported viewports render the admin console")
    def test_supported_browsers_and_shopfloor_viewports_render(self, browser):
        """
        ID     : TC_NFR_001
        Title  : Supported browsers and shopfloor viewport sizes render correctly
        Reason : AMR consoles vary from 10-inch touch panels to full-HD monitors.
                 A layout that breaks at 768 px wide blocks the operator from
                 seeing task queues or configuration settings.

        Pass criteria per viewport:
          • Page loads without JS errors captured via console event listener.
          • The operator sidebar (#operator-sidebar-nav) is present in the DOM.
          • No horizontal scrollbar (scrollWidth ≤ clientWidth + 5 px tolerance).
        """
        for label, width, height in _SHOPFLOOR_VIEWPORTS:
            with allure.step(f"Viewport: {label} ({width}×{height})"):
                ctx = browser.new_context(
                    viewport={"width": width, "height": height},
                    ignore_https_errors=config.ignore_https_errors,
                )
                page = ctx.new_page()
                js_errors = []
                page.on("pageerror", lambda exc: js_errors.append(str(exc)))

                try:
                    LoginPage(page).login(config.admin_user, config.admin_pass)
                    wait_for_app_ready(page, timeout=config.default_timeout)

                    assert "login" not in page.url.lower(), (
                        f"[{label}] Login failed — still at {page.url}"
                    )

                    # Sidebar must exist (may be collapsed on narrow widths)
                    sidebar = page.locator("#operator-sidebar-nav")
                    sidebar.wait_for(state="attached", timeout=10000)
                    assert sidebar.count() > 0, (
                        f"[{label}] #operator-sidebar-nav not found in DOM."
                    )

                    # Check for catastrophic horizontal overflow
                    overflow = page.evaluate(
                        "() => document.documentElement.scrollWidth > "
                        "document.documentElement.clientWidth + 5"
                    )
                    assert not overflow, (
                        f"[{label}] Page has horizontal overflow at {width}×{height}."
                    )

                    # No JS exceptions
                    assert not js_errors, (
                        f"[{label}] JavaScript errors: {'; '.join(js_errors[:3])}"
                    )

                finally:
                    ctx.close()


