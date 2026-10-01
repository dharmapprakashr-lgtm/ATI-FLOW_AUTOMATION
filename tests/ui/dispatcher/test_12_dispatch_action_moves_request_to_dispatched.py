"""Dispatcher > Requests - Dispatch action (Decision column).

SKIPPED BY DESIGN - not a scaffold waiting to be filled in.

Clicking "Dispatch" on a Pending row has a real, physical side effect: the
bound Fleet Manager (192.168.6.12) assigns and moves an actual AMR to service
that request. The Dispatcher's Pending queue on the live instance is real
production traffic - other requesters' in-flight material requests - not
anything this suite created. The project's standing rule (see
pages/dashboards/dispatcher_dashboard_page.py and the AtiFlow testing-approach
notes) is: never take an action with a production side effect on a record this
suite did not itself create.

This test can only run safely when it is handed the id of a request THIS test
run raised itself, via a cross-role `run_context` fixture chained from the
Requester phase - which lives in tests/ui/e2e/, not here. Until that exists,
the dispatch happy-path is exercised end-to-end there, not in the
dispatcher-only folder.

Implementation sketch (for the e2e version):
    request_id = run_context["requester_request_id"]
    row = dispatcher_page.locator(f"#approvals-request-grid-row-{request_id}")
    dispatcher_page.locator(f"#approvals-dispatch-decision-cell-{request_id}").click()
    # Status flips Awaiting Dispatch -> Dispatched
    # Row leaves the PENDING tab, appears under DISPATCHED after reload
    # Settings > Connection Check shows the route triggered through the FM
"""

import allure
import pytest

from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage

pytestmark = [pytest.mark.dispatcher]


@allure.title("Dispatch action moves a request to Dispatched (e2e-only - see module docstring)")
@pytest.mark.skip(
    reason="Clicking Dispatch moves a real AMR via the live Fleet Manager. It "
    "may only be run against a request this test run created itself, which "
    "requires the cross-role run_context fixture from tests/ui/e2e/. Not "
    "runnable from the dispatcher-only folder."
)
def test_dispatch_action_moves_request_to_dispatched(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)
    _ = home  # pragma: no cover - body never executes; see module docstring
