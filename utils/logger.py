"""Suite-wide logging.

pytest captures stdout per test and only shows it for failures, which is usually
what you want. Session-scoped fixtures are the exception: their output is
discarded unless ``-s`` is passed, which is how a silent teardown failure hides.
Use ``get_logger`` there so the message reaches the log capture instead.
"""

import logging
import os
import sys

_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
_FORMAT = "%(asctime)s  %(levelname)-7s  %(name)s  %(message)s"
_configured = False


def _configure_once():
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt="%H:%M:%S"))

    root = logging.getLogger("atiflow")
    root.setLevel(_LEVEL)
    root.addHandler(handler)
    root.propagate = False
    _configured = True


def get_logger(name):
    """Return a namespaced logger, e.g. ``get_logger(__name__)``."""
    _configure_once()
    return logging.getLogger(f"atiflow.{name}")
