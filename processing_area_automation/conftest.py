"""
Shared pytest fixtures.

Environment variables (set in .env or CI):
  BASE_URL   - e.g. https://mts-staging.atimotors.com
  ADMIN_USER - admin login username
  ADMIN_PASS - admin login password
  PROC_AREA  - processing area name/slug to run tests against, e.g. "ROTR"
"""

import os
import pytest
from playwright.sync_api import sync_playwright

from pages.staging_area_page import StagingAreaPage
from pages.processing_area_config_page import ProcessingAreaConfigPage
from pages.containers_page import ContainersPage


BASE_URL = os.getenv("BASE_URL", "https://192.168.6.32")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")
PROC_AREA = os.getenv("PROC_AREA", "august")

HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance):
    browser = playwright_instance.chromium.launch(headless=HEADLESS, slow_mo=0)
    yield browser
    browser.close()


@pytest.fixture
def page(browser):
    # ignore_https_errors: the app serves a self-signed/untrusted cert
    # (Chrome shows "Not secure" on 192.168.6.32) — Playwright blocks on
    # this by default without this flag.
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        ignore_https_errors=True,
    )
    page = context.new_page()
    _login(page)
    yield page
    context.close()


def _login(page):
    """
    Logs in as Admin. Confirmed via playwright codegen recording.
    """
    page.goto(f"{BASE_URL}/login")
    page.get_by_role("textbox", name="Username").fill(ADMIN_USER)
    page.get_by_role("textbox", name="Password").fill(ADMIN_PASS)
    page.get_by_role("button", name="Login").click()
    page.wait_for_load_state("networkidle")


@pytest.fixture
def staging_area_page(page):
    sap = StagingAreaPage(page, BASE_URL)
    sap.open(PROC_AREA)
    return sap


@pytest.fixture
def processing_area_config_page(page):
    pacp = ProcessingAreaConfigPage(page, BASE_URL)
    pacp.open(PROC_AREA)
    return pacp


@pytest.fixture
def containers_page(page):
    cp = ContainersPage(page, BASE_URL)
    cp.open(PROC_AREA)
    return cp
