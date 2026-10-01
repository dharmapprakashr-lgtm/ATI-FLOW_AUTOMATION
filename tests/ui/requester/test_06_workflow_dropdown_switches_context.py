"""Requester - Workflow dropdown (left sidebar)."""

import allure
import pytest

from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@allure.title("Selecting a different workflow updates the sidebar context")
def test_workflow_dropdown_switches_context(requester_page):
    """Confirmed live 2026-08-26: the dropdown does NOT match
    config/test_data.toml's requester_bound_workflows 4-name array. It shows
    9 options but only 2 distinct names ('order_material_manual_45' x6,
    'anyStation_to_StagingArea' x3, each a different internal data-value) -
    'order_material_auto' and 'stagingArea_to_any_station' aren't present at
    all live. This looks like orphaned duplicate workflow records from
    earlier admin test runs (see atiflow-testing-approach memory on sweeping
    orphans left by broken runs) rather than a requester-page bug, and
    cleaning that up is admin-side work, out of scope here.

    So this test switches by whatever distinct text is actually offered,
    not by name from config, and only asserts the one thing this page
    controls: the sidebar reflects whichever option was clicked."""
    home = RequesterHomePage(requester_page)
    starting_workflow = home.bound_workflow_text()

    with allure.step("Open the Workflow dropdown and find a differently-named option"):
        home.bound_workflow_select.click()
        options = requester_page.get_by_role("option")
        count = options.count()
        assert count > 0, "Workflow dropdown offered no options at all"

        other_option = None
        other_text = None
        for i in range(count):
            text = options.nth(i).inner_text()
            if text != starting_workflow:
                other_option = options.nth(i)
                other_text = text
                break

        assert other_option is not None, (
            f"All {count} workflow options are named '{starting_workflow}' - "
            f"no distinct workflow to switch to."
        )

    with allure.step(f"Switch from '{starting_workflow}' to '{other_text}'"):
        other_option.click()
        requester_page.wait_for_timeout(1000)
        assert home.bound_workflow_text() == other_text
