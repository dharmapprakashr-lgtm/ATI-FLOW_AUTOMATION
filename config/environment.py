"""Environment-driven configuration.

Resolution order, lowest priority first:

1. ``config/environments/<env>.yaml``  - non-secret, per-environment defaults
2. process environment / ``.env``      - secrets and local overrides

Select the environment with ``TEST_ENV`` (default ``qa``)::

    TEST_ENV=staging pytest -m admin

Secrets never live in the YAML files; only base URLs, timeouts and other
non-sensitive settings belong there.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"

load_dotenv(ROOT_DIR / ".env")


def _load_environment_file(env_name):
    """Return the parsed environment YAML, or {} when the file is absent."""
    env_file = CONFIG_DIR / "environments" / f"{env_name}.yaml"
    if not env_file.exists():
        return {}
    with open(env_file, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _env_flag(name, default):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class Settings:
    """Typed view of everything the suite needs to reach an environment."""

    env: str
    base_url: str
    headless: bool
    default_timeout: int
    ignore_https_errors: bool

    admin_user: str = field(repr=False, default="")
    admin_pass: str = field(repr=False, default="")
    mes_user: str = field(repr=False, default="")
    mes_pass: str = field(repr=False, default="")

    # Fleet Manager — separate app/login from AtiFlow itself. Used only by the
    # e2e chain that verifies a dispatched request actually created a trip
    # (tests/ui/e2e/test_full_workflow_admin_to_supervisor.py).
    fm_base_url: str = field(default="")
    fm_user: str = field(repr=False, default="")
    fm_pass: str = field(repr=False, default="")

    @classmethod
    def load(cls):
        env_name = os.environ.get("TEST_ENV", "qa")
        file_values = _load_environment_file(env_name)

        return cls(
            env=env_name,
            # BASE_URL from the environment wins so a developer can point at a
            # local instance without editing a checked-in file.
            base_url=os.environ.get("BASE_URL") or file_values.get("base_url", ""),
            headless=_env_flag("HEADLESS", file_values.get("headless", True)),
            default_timeout=int(os.environ.get("DEFAULT_TIMEOUT", file_values.get("default_timeout", 15000))),
            ignore_https_errors=_env_flag(
                "IGNORE_HTTPS_ERRORS", file_values.get("ignore_https_errors", True)
            ),
            admin_user=os.environ.get("ADMIN_USERNAME", ""),
            admin_pass=os.environ.get("ADMIN_PASSWORD", ""),
            mes_user=os.environ.get("MES_USERNAME", ""),
            mes_pass=os.environ.get("MES_PASSWORD", ""),
            fm_base_url=os.environ.get("FM_BASE_URL", ""),
            fm_user=os.environ.get("FM_USERNAME", ""),
            fm_pass=os.environ.get("FM_PASSWORD", ""),
        )

    @property
    def app_url(self):
        """Base URL without the /login suffix, for post-auth navigation."""
        return self.base_url.rsplit("/login", 1)[0].rstrip("/") or self.base_url

    def require_admin_credentials(self):
        """Fail loudly at setup rather than at a confusing login timeout."""
        missing = [
            name for name, value in (
                ("BASE_URL", self.base_url),
                ("ADMIN_USERNAME", self.admin_user),
                ("ADMIN_PASSWORD", self.admin_pass),
            ) if not value
        ]
        if missing:
            raise RuntimeError(
                f"Missing required configuration: {', '.join(missing)}. "
                f"Copy .env.example to .env and fill it in (TEST_ENV={self.env})."
            )


config = Settings.load()
