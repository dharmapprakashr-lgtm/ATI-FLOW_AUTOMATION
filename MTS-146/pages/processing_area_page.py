"""
ProcessingAreaPage
-------------------
Handles creating a NEW processing area from the sidebar — intended to give
this automation suite its own dedicated area (own materials, containers,
staging area) instead of running against the shared "august" area.

SELECTOR STATUS:
- CONFIRMED (from the very first recording of this whole project, and
  re-confirmed via a full end-to-end recording on Aug 11): the
  "Create New Area" link/button in the sidebar, the Name/Description
  fields, and the SAVE button (exact text "SAVE").
- NOT YET RECORDED: how to add a Staging Area to a brand-new area
  EXPLICITLY. However: a full recording that created a new area, added
  ONE material with its "Staging Area" toggle switched ON, then went to
  the Staging Area tab — and a staging area card (id
  #staging-area-list-admin-card-top-row-0) was already there, with no
  separate "create staging area" step ever clicked. This strongly
  suggests staging areas are auto-provisioned based on material
  configuration (the "Staging Area" toggle when adding a material), not
  created directly. Not 100% certain — worth confirming explicitly if it
  matters later — but this is what own_test_area_setup.py relies on.
"""

from playwright.sync_api import Page, expect
from pages.base_page import BasePage


class ProcessingAreaPage(BasePage):
    CREATE_NEW_AREA_TEXT = "Create New Area"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)

    def open_create_area_modal(self):
        self.page.get_by_text(self.CREATE_NEW_AREA_TEXT).click()

    def fill_new_area(self, name: str, description: str = ""):
        self.page.get_by_role("textbox", name="Name").fill(name)
        if description:
            self.page.get_by_role("textbox", name="Description").fill(description)

    def save_new_area(self):
        """CONFIRMED (Aug 11, via full recording) — button text is exactly "SAVE"."""
        self.page.get_by_role("button", name="SAVE").click()

    def cancel_new_area(self):
        self.page.get_by_role("button", name="CANCEL").click()

    def create_area(self, name: str, description: str = ""):
        """Full flow — but see save_new_area()'s docstring caveat before trusting this end-to-end."""
        self.open_create_area_modal()
        self.fill_new_area(name, description)
        self.save_new_area()
