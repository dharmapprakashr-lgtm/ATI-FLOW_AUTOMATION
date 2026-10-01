"""Unique-name generation for entities created during a test run.

The suite's baseline entities come from ``config/test_data.toml`` and use fixed
names on purpose: the teardown in ``tests/conftest.py`` has to know what to
delete, and role suites bind to those exact names.

Use these helpers for anything created *inside* a test that does not need a
stable name. Fixed names are what currently prevents running the suite in
parallel - two workers creating "mohit_test_area22" collide.
"""

import os
import random
import string
from datetime import datetime

# Short per-process token so two workers (or two concurrent CI jobs) cannot
# generate the same name even within the same second.
_RUN_TOKEN = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))


def run_token():
    """Stable token for the lifetime of this process."""
    return _RUN_TOKEN


def unique_name(prefix, separator="_"):
    """Return ``<prefix>_<HHMMSS>_<token>``, safe for a UI name field."""
    stamp = datetime.now().strftime("%H%M%S")
    return f"{prefix}{separator}{stamp}{separator}{_RUN_TOKEN}"


def unique_username(role):
    """Return a unique login name for a role-scoped device account."""
    return unique_name(role)


def scoped_name(base):
    """Namespace a fixed name by CI job, leaving local runs untouched.

    Lets the same ``test_data.toml`` drive several CI jobs against one
    environment without collisions, while a developer running locally still
    sees the plain names from the file.
    """
    job = os.environ.get("CI_JOB_ID") or os.environ.get("GITHUB_RUN_ID")
    return f"{base}_{job}" if job else base
