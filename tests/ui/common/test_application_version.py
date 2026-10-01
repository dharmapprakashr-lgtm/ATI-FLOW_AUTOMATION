"""Capture the displayed AtiFlow version for Allure and the PDF run report.

Runs after the common login checks and uses the admin session to read the
version on the Settings screen. Historical case ID TC_SET_002 is retained.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from config.environment import config


@allure.feature("Common UI")
@allure.story("Application version")
@pytest.mark.admin
@pytest.mark.smoke
@allure.title("TC_SET_002 — Capture the AtiFlow version displayed in the UI")
def test_capture_displayed_atiflow_version(admin_page, record_property):
    """Capture UI build identification; no deployment-version comparison is implied."""
    admin_page.goto(config.app_url + "/settings", wait_until="domcontentloaded")

    # Match an entire version label, not IP addresses, dates, or arbitrary
    # numbers embedded in connection-status text. Supports v2.0, 2.0.1,
    # AtiFlow v2.0.1 and Version: 2.0.1-rc.1+build.42.
    version_pattern = re.compile(
        r"^\s*(?:AtiFlow\s*[:\-]?\s*)?(?:Version\s*[:\-]?\s*)?"
        r"v?(\d+\.\d+(?:\.\d+)?(?:-[0-9A-Za-z.-]+)?"
        r"(?:\+[0-9A-Za-z.-]+)?)\s*$",
        re.IGNORECASE,
    )
    with allure.step("Read the visible AtiFlow version label"):
        version_label = admin_page.get_by_text(version_pattern).filter(visible=True).first
        expect(version_label).to_be_visible(timeout=10_000)
        displayed_text = version_label.inner_text().strip()
        match = version_pattern.fullmatch(displayed_text)
        assert match, f"Unrecognized AtiFlow version label: {displayed_text!r}"
        version = match.group(1)

    with allure.step(f"Record AtiFlow version: {version}"):
        record_property("atiflow_version", version)
        allure.attach(displayed_text, "AtiFlow version displayed in UI", allure.attachment_type.TEXT)
        allure.attach(
            version_label.screenshot(), "AtiFlow version label",
            allure.attachment_type.PNG,
        )
        print(f"AtiFlow UI version: {version}")

