"""Requester > Staging Area - utilisation display."""

import re

import allure
import pytest

from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@allure.title("Utilisation bar's fill accurately reflects its own 'X/Y' label")
def test_staging_area_utilisation_bar_accurate(requester_page):
    """AH_stage is a shared staging area with real, live occupancy that
    changes independently of this suite (see atiflow-testing-approach
    memory) - so this can't assert a fixed 'X/4 Utilised cells' figure.

    Instead it cross-checks the card's two independent renderings of the
    same number: the 'X/Y Utilised cells' text label, and the MUI
    LinearProgress bar's own aria-valuenow (0-100). If the card is telling
    the truth, valuenow must equal round(X/Y * 100) - confirmed live
    2026-08-26 (0/4 -> aria-valuenow="0")."""
    home = RequesterHomePage(requester_page)
    home.open_staging_area()

    label = home.staging_area_utilised_text(0)
    match = re.match(r"(\d+)/(\d+) Utilised cells", label)
    assert match, f"Unexpected utilisation label format: {label!r}"
    occupied, total = int(match.group(1)), int(match.group(2))

    with allure.step(f"Label '{label}' is internally sane"):
        assert total > 0
        assert 0 <= occupied <= total

    with allure.step("Progress bar's own percentage matches the label's fraction"):
        expected_pct = round(occupied / total * 100)
        assert home.staging_area_progress_value(0) == expected_pct
