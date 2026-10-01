"""Admin › Settings › Connections — the connection-status panel at ``/settings``.

Locators verified live against the running app on 2026-09-03.

Layout
------
Two tabs — **Connections** (default) and **General**. The Connections tab
renders two status cards:

    Fleet Manager   (badge "FM")  — status line, Host, Last synced,  Edit pencil
    MES Connections (badge "MES") — status line, AMR URL, BOM URL,    Edit pencils

Behaviour (this is what TC_SET_003 exercises)
--------------------------------------------
Each card **probes its connection when the panel mounts**: the status line
shows ``Checking connection...`` and then settles on a real result such as
``Connected`` or ``Connection issues detected``. The two cards settle
independently (FM ``Connected`` while MES reports issues), so the status is
the output of a live per-connection probe, not one shared hardcoded string.

The settled result is cached for the rest of the session, so the transient
``Checking connection...`` is only reliably visible on the first visit in a
fresh browser context. There is **no Refresh button** and **no ticking
timestamp** — ``Last synced`` is a static relative label. The only
user-driven re-mount of the panel is leaving the Connections tab and
returning to it (:meth:`remount_panel`).

The DOM is MUI + emotion-hash classes with essentially no stable ids, so
these locators are anchored on ``role="tab"`` and visible card text.
"""

import re

#: Transient status shown while a card is still probing.
CHECKING_RE = re.compile(r"checking connection", re.IGNORECASE)

#: Settled (terminal) status vocabulary a card can show once the probe returns.
RESOLVED_RE = re.compile(
    r"connection issues detected|disconnected|unreachable|not reachable|"
    r"offline|connected|online|reachable",
    re.IGNORECASE,
)

#: Placeholder / stub text that must never appear in place of a real status.
PLACEHOLDER_RE = re.compile(r"todo|tbd|placeholder|coming soon", re.IGNORECASE)

#: Nearest ancestor <div> that wraps a whole card (header status line + the
#: labelled detail rows). Anchored on a label that is unique to each card.
_CARD_ROOT = (
    "xpath=ancestor::div[.//p[normalize-space()='Host' "
    "or normalize-space()='AMR URL']][1]"
)


class ConnectionCheckPage:
    PATH = "/settings"

    def __init__(self, page):
        self.page = page
        self.connections_tab = page.get_by_role("tab", name="Connections")
        self.general_tab = page.get_by_role("tab", name="General")

    # ── tab navigation ───────────────────────────────────────────────────────
    def is_loaded(self):
        return self.connections_tab.is_visible() and self.card("Fleet Manager").is_visible()

    def show_connections(self):
        self.connections_tab.click()
        self.page.wait_for_timeout(300)

    def show_general(self):
        self.general_tab.click()
        self.page.wait_for_timeout(300)

    def remount_panel(self):
        """Re-mount the Connections panel the only way the UI allows — tab away
        and back. This is the page's de-facto "manual refresh"."""
        self.show_general()
        self.show_connections()

    # ── cards ────────────────────────────────────────────────────────────────
    def card(self, title):
        """The <div> wrapping a whole card, found from its title text."""
        return self.page.get_by_text(title, exact=True).first.locator(_CARD_ROOT)

    def card_text(self, title):
        return re.sub(r"\s+", " ", self.card(title).inner_text()).strip()

    def is_checking(self, title):
        return bool(CHECKING_RE.search(self.card_text(title)))

    def settled_status(self, title):
        """The card's terminal status string, or "" while it is still checking."""
        text = self.card_text(title)
        if CHECKING_RE.search(text):
            return ""
        match = RESOLVED_RE.search(text)
        return match.group(0) if match else ""

    def wait_until_settled(self, title, timeout=20000):
        """Poll until the card leaves ``Checking connection...``.

        Returns the settled status string, or "" if it never settled within
        *timeout* (a genuinely unreachable service can stay on
        ``Checking connection...`` indefinitely).
        """
        elapsed, step = 0, 500
        while elapsed < timeout:
            status = self.settled_status(title)
            if status:
                return status
            self.page.wait_for_timeout(step)
            elapsed += step
        return ""

    def field_value(self, label):
        """Value of a labelled detail row, e.g. ``field_value("Host")``.

        The labels (Host, Last synced, AMR URL, BOM URL) are unique across the
        two cards, so this does not need to be card-scoped.
        """
        label_node = self.page.get_by_text(label, exact=True).first
        return re.sub(
            r"\s+", " ",
            label_node.locator("xpath=following-sibling::*[1]").inner_text(),
        ).strip()
