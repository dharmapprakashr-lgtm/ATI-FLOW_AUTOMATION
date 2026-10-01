"""Ownership ledger for UI records created by this Python test process."""
import os

areas = set()
devices = set()
ui_records = set()


def cleanup_enabled():
    return os.getenv("CLEANUP_TEST_DATA", "1").strip().lower() not in {"0", "false", "no"}


def track_area(name):
    areas.add(name)


def track_device(role, name):
    devices.add((role, name))


def track_area_rename(old_name, new_name):
    if old_name in areas:
        # Keep both names so teardown covers a partially completed rename.
        areas.add(new_name)


def track_ui_record(page, name, kind="row"):
    """Claim only an absent exact-name record before submitting its create form."""
    if not name:
        return
    locator = (page.get_by_role("columnheader", name=name, exact=True)
               if kind == "mapping" else
               page.locator("tr").filter(has=page.get_by_text(name, exact=True)))
    if locator.count():
        return
    tab = page.get_by_role("tab", selected=True)
    if tab.count() != 1:
        raise AssertionError("Cannot register UI cleanup: expected one active area tab")
    ui_records.add((page.url, tab.inner_text().strip(), name, kind))
