"""
ContainersPage
--------------
Covers TC_PA_017 - TC_PA_020.

SELECTOR STATUS (updated Aug 11 — full Add-to-Save recording):
- Confirmed: "Add New Container" button, Container Type dropdown (options
  "Trolley"/"Pallet"/"Bin"), Container Sub-type (textbox, placeholder
  "Enter sub-type"), Length/Width/Height/Hitch Length (id-based:
  #ctr-length, #ctr-width, #ctr-height, #ctr-hitch-length), QTY field
  (placeholder "01", NOT an id — earlier #ctr-qty guess was wrong), Save
  button (text "SAVE", all caps), Cancel button ("CANCEL").
- RESOLVED: the ambiguous "01" placeholder from an earlier recording is
  confirmed to be QTY, not Container ID. This modal has NO separate
  Container ID field at all — despite the ticket spec listing
  "Container ID *" as mandatory. This is a SPEC MISMATCH worth flagging
  to dev/product, same category as the Active/Inactive filter tabs issue.
- CONFIRMED BEHAVIORALLY (not via a specific error-text selector):
  clicking SAVE with all fields empty does NOT close the modal — it
  silently blocks. attempt_save_missing_mandatory_fields() checks this by
  asserting the modal (Sub-type field) is still visible after the click,
  rather than looking for a specific validation message element.
- STILL NOT CONFIRMED: table row selector (a recording clicked an empty
  action-column cell, not a usable row locator — row_count()/get_row()
  below fall back to the generic ARIA "row" role, which MUI DataGrid
  typically renders, but this is a reasonable guess, not confirmed),
  Search input interaction, Export CSV button interaction (both were
  skipped in the last recording despite being asked for).
"""

from playwright.sync_api import Page, expect
from pages.base_page import BasePage


class ContainersPage(BasePage):
    ADD_BTN_TEXT = "Add New Container"
    CONTAINER_TYPE_LABEL = "CONTAINER TYPE *"
    CONTAINER_TYPES = ["Trolley", "Pallet", "Bin"]
    SUBTYPE_PLACEHOLDER = "Enter sub-type"
    LENGTH_ID = "#ctr-length"
    WIDTH_ID = "#ctr-width"
    HEIGHT_ID = "#ctr-height"
    HITCH_LENGTH_ID = "#ctr-hitch-length"
    HITCH_LENGTH_LABEL = "HITCH LENGTH (in mm) *"
    QTY_PLACEHOLDER = "01"  # CONFIRMED — this is Qty, not Container ID

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)

    def open(self, processing_area: str):
        self.page.locator("#operator-sidebar-nav").get_by_text(processing_area, exact=True).click()
        self.page.get_by_role("tab", name="Containers").click()

    def row_count(self) -> int:
        """UNCONFIRMED — using generic ARIA row role as a reasonable guess for a MUI DataGrid table."""
        return self.page.get_by_role("row").count()

    def get_row(self, text: str):
        """UNCONFIRMED — same caveat as row_count()."""
        return self.page.get_by_role("row").filter(has_text=text)

    # ---------- Add Container modal ----------
    def open_add_modal(self):
        self.page.get_by_role("button", name=self.ADD_BTN_TEXT).click()

    def select_container_type(self, c_type: str):
        self.page.get_by_label("", exact=True).click()
        self.page.get_by_role("option", name=c_type).click()

    def fill_subtype(self, c_subtype: str):
        self.page.get_by_role("textbox", name=self.SUBTYPE_PLACEHOLDER).fill(c_subtype)

    def fill_dimensions(self, length: str = "", width: str = "",
                         height: str = "", hitch_length: str = ""):
        if length:
            self.page.locator(self.LENGTH_ID).fill(length)
        if width:
            self.page.locator(self.WIDTH_ID).fill(width)
        if height:
            self.page.locator(self.HEIGHT_ID).fill(height)
        if hitch_length:
            self.page.locator(self.HITCH_LENGTH_ID).fill(hitch_length)

    def fill_qty(self, qty: str):
        self.page.get_by_placeholder(self.QTY_PLACEHOLDER).fill(qty)

    def save(self):
        self.page.get_by_role("button", name="SAVE").click()

    def cancel_modal(self):
        self.page.get_by_role("button", name="CANCEL").click()

    def add_container(self, c_type: str, c_subtype: str,
                       length: str = "", width: str = "", height: str = "",
                       hitch_length: str = "", qty: str = ""):
        """CONFIRMED full flow (Aug 11) — Add through Save, no Container ID field exists."""
        self.open_add_modal()
        self.select_container_type(c_type)
        self.fill_subtype(c_subtype)
        self.fill_dimensions(length, width, height, hitch_length)
        if qty:
            self.fill_qty(qty)
        self.save()

    def attempt_save_missing_mandatory_fields(self):
        self.open_add_modal()
        self.save()

    def assert_validation_blocked(self):
        """
        Confirmed behaviorally: the modal stays open (Sub-type field still
        visible) when Save is clicked with empty required fields — no
        specific error-message selector confirmed yet.
        """
        expect(self.page.get_by_role("textbox", name=self.SUBTYPE_PLACEHOLDER)).to_be_visible()

    def export_csv(self):
        raise NotImplementedError("Export CSV button click was not captured in the last recording — needs a dedicated retry.")

    def search(self, term: str):
        raise NotImplementedError("Search input interaction was not captured in the last recording — needs a dedicated retry.")
