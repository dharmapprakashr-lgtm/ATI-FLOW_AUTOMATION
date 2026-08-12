"""
MaterialsPage
--------------
Handles the "Add New Material" flow.

SELECTOR STATUS (CORRECTED Aug 11, via a clear screenshot of the actual
modal — this supersedes earlier guesses about field meaning):

Real labeled fields, top to bottom:
- MATERIAL TYPE NAME * — textbox, placeholder "e.g. SMD Class"
- PRODUCTION UNIT * — textbox, placeholder "e.g. Unit A"
- PROCESS NAME — greyed-out, pre-filled with the processing area's own
  name (e.g. "AutoTest_28968"), NOT user-editable. Not a field we fill.
- PRE-PROC TIME (in mins) * — the field previously called "field1"
  (placeholder "e.g. 15"). CORRECTED: this is Pre-Proc Time, NOT Prefix
  as earlier guessed.
- MAX QTY * — the field previously called "field2" (placeholder "e.g. 100").
- Staging Area — toggle switch.
- PREFIX ASSOCIATED * — the field previously mislabeled "SKU code"
  (placeholder "e.g. MAT-"). This is the actual Prefix field the earlier
  "Prefix already associated" error was complaining about.

THE REAL BUG (found via screenshot after a stuck run, then CONFIRMED FIXED
via a second recording + screenshot showing a registered "MAT-001" chip):
there are TWO separate "Add Material"-labeled controls —
  1. A small green "+" icon button immediately next to the PREFIX
     ASSOCIATED field — this REGISTERS that prefix value into the form,
     visually confirmed by a chip (e.g. "MAT-001 ✕") appearing below the
     input after clicking it. CONFIRMED selector: it's an icon-only
     button with NO visible text, matched via
     get_by_role("button").filter(has_text=re.compile(r"^$")) scoped to
     the open dialog.
  2. The actual dialog submit button at the bottom, ALSO labeled
     "Add Material" — the real save-the-whole-form action, click this
     AFTER the prefix chip is registered.
The earlier bug: code only ever clicked #2, skipping #1 — prefix was
typed but never registered, producing "Prefix Associated is required"
even though the field visibly had text. register_prefix() and
add_material() below are now fixed to click #1 before #2.
"""

from playwright.sync_api import Page, expect
from pages.base_page import BasePage


class MaterialsPage(BasePage):
    ADD_MATERIAL_BTN = "Add New Material"  # opens the modal
    SUBMIT_BTN_TEXT = "Add Material"       # submits it — DIFFERENT text, no "New"
    CLASS_NAME_PLACEHOLDER = "e.g. SMD Class"      # MATERIAL TYPE NAME *
    UNIT_PLACEHOLDER = "e.g. Unit A"                # PRODUCTION UNIT *
    PRE_PROC_TIME_PLACEHOLDER = "e.g. 15"           # PRE-PROC TIME (in mins) *
    MAX_QTY_PLACEHOLDER = "e.g. 100"                # MAX QTY *
    PREFIX_PLACEHOLDER = "e.g. MAT-"                # PREFIX ASSOCIATED *

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)

    def open_add_material_modal(self):
        self.page.get_by_role("button", name=self.ADD_MATERIAL_BTN).click()

    def fill_class_name(self, name: str):
        self.page.get_by_role("textbox", name=self.CLASS_NAME_PLACEHOLDER).fill(name)

    def fill_unit(self, unit: str):
        """
        CONFIRMED role: combobox, not textbox — verified in the very
        first recording of this flow. A later "screenshot-based
        correction" incorrectly changed this to textbox, which broke a
        real run. Reverted.
        """
        self.page.get_by_role("combobox", name=self.UNIT_PLACEHOLDER).fill(unit)

    def fill_pre_proc_time(self, minutes: str):
        self.page.get_by_placeholder(self.PRE_PROC_TIME_PLACEHOLDER).fill(minutes)

    def fill_max_qty(self, qty: str):
        self.page.get_by_placeholder(self.MAX_QTY_PLACEHOLDER).fill(qty)

    def enable_staging_area_toggle(self):
        self.page.get_by_role("switch", name="Staging Area").check()

    def fill_prefix(self, prefix: str):
        self.page.get_by_placeholder(self.PREFIX_PLACEHOLDER).fill(prefix)

    def register_prefix(self):
        """
        CONFIRMED (Aug 11, via recording + screenshot showing a resulting
        chip). The "+" button has no visible text — matched as the
        empty-text button within the open dialog.
        """
        import re
        self.page.get_by_role("dialog").get_by_role("button").filter(
            has_text=re.compile(r"^$")
        ).click()

    def submit(self):
        """
        FIXED: this button says "Add Material" (no "New"), NOT the same
        text as the opener button ("Add New Material") — confirmed via
        the original recording. Using the wrong shared constant here was
        the actual cause of the last failed run.
        """
        self.page.get_by_role("button", name=self.SUBMIT_BTN_TEXT).click()

    def add_material(self, class_name: str, unit: str = "",
                      pre_proc_time: str = "", max_qty: str = "",
                      enable_staging_area: bool = True, prefix: str = ""):
        """
        CONFIRMED full flow (Aug 11): fill prefix, click "+" to register
        it (producing a chip), fill remaining fields, then submit.
        """
        self.open_add_material_modal()
        self.fill_class_name(class_name)
        if unit:
            self.fill_unit(unit)
        if pre_proc_time:
            self.fill_pre_proc_time(pre_proc_time)
        if max_qty:
            self.fill_max_qty(max_qty)
        if enable_staging_area:
            self.enable_staging_area_toggle()
        if prefix:
            self.fill_prefix(prefix)
            self.register_prefix()
        self.submit()

        still_open = self.page.get_by_role(
            "textbox", name=self.CLASS_NAME_PLACEHOLDER
        ).is_visible()
        if still_open:
            raise RuntimeError(
                "Add Material modal did not close after submit — check "
                "the failure screenshot for the actual on-screen "
                "validation message."
            )
