"""Credentials for the three Execution Source Config device roles.

These dashboards do not have separate user accounts: a device authenticates
with its **Name** and **Password** as entered in Execution Source Config - not
its Device ID. The admin suite creates the records; the role suites log in with
them.

``RoleCredentials`` is what the per-role conftests hand to their login fixture,
so a role suite never reaches into ``TestData`` for a password directly.
"""

from dataclasses import dataclass, field

from config.data import TestData


@dataclass(frozen=True)
class RoleCredentials:
    role: str
    name: str
    password: str = field(repr=False)
    device_id: str = ""

    def as_login(self):
        """Return the (username, password) pair the login page expects."""
        return self.name, self.password


def requester_credentials():
    return RoleCredentials(
        role="requester",
        name=TestData.req_device_name,
        password=TestData.req_device_pass,
        device_id=TestData.req_device_id,
    )


def dispatcher_credentials():
    return RoleCredentials(
        role="dispatcher",
        name=TestData.disp_device_name,
        password=TestData.disp_device_pass,
        device_id=TestData.disp_device_id,
    )


def supervisor_credentials():
    return RoleCredentials(
        role="supervisor",
        name=TestData.sup_device_name,
        password=TestData.sup_device_pass,
        device_id=TestData.sup_device_id,
    )


ALL_ROLES = {
    "requester": requester_credentials,
    "dispatcher": dispatcher_credentials,
    "supervisor": supervisor_credentials,
}


# ── End-to-end suite — isolated `_e2e` device records ─────────────────────────
# Same three roles, read from TestData.e2e_* (the [e2e_devices] table). Used
# only by tests/ui/e2e/conftest.py.

def e2e_requester_credentials():
    return RoleCredentials(
        role="requester",
        name=TestData.e2e_req_device_name,
        password=TestData.e2e_req_device_pass,
        device_id=TestData.e2e_req_device_id,
    )


def e2e_dispatcher_credentials():
    return RoleCredentials(
        role="dispatcher",
        name=TestData.e2e_disp_device_name,
        password=TestData.e2e_disp_device_pass,
        device_id=TestData.e2e_disp_device_id,
    )


def e2e_supervisor_credentials():
    return RoleCredentials(
        role="supervisor",
        name=TestData.e2e_sup_device_name,
        password=TestData.e2e_sup_device_pass,
        device_id=TestData.e2e_sup_device_id,
    )
