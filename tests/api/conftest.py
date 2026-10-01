"""API test suite configuration — auto-login and environment bootstrap.

Uses pytest_configure() which runs BEFORE any test module is imported,
so module-level variables like:

    TOKEN = os.getenv("MTS_TOKEN") or ""

in test_processing_area_api.py correctly pick up the injected token.

Login endpoint discovered from the live OpenAPI spec:
  POST /mts/auth/device/login
  Body: {"name": "<ADMIN_USERNAME>", "device_password": "<ADMIN_PASSWORD>"}
  Response: {"access_token": "...", "token_type": "bearer", ...}
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parent.parent.parent  # AtiFlowAutomation-main/

# Primary endpoint — discovered from OpenAPI spec on 192.168.6.32:8000.
# Fallbacks cover alternate deployment patterns.
_LOGIN_ENDPOINTS = [
    # (url_suffix,  payload_builder,  style)
    ("/mts/auth/device/login",   "device_json"),   # ← real endpoint
    ("/auth/token",              "oauth2_form"),
    ("/api/auth/token",          "oauth2_form"),
    ("/mts/auth/token",          "oauth2_form"),
    ("/auth/login",              "user_json"),
    ("/api/login",               "user_json"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_dotenv(path: Path) -> None:
    """Minimal .env reader — writes KEY=VALUE into os.environ without
    overwriting variables that are already set in the shell."""
    try:
        with open(path) as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                os.environ.setdefault(key, val)
    except FileNotFoundError:
        pass


def _ssl_ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _resolve_base_url() -> str:
    """MTS API base URL — no trailing slash, no /login suffix."""
    raw = (
        os.environ.get("MTS_BASE_URL", "").strip()
        or os.environ.get("BASE_URL", "").strip()
        or "http://localhost:8000"
    )
    if raw.endswith("/login"):
        raw = raw[: -len("/login")]
    return raw.rstrip("/")


def _make_payload(style: str, username: str, password: str) -> tuple[bytes, str]:
    """Return (body_bytes, content_type) for the given login style."""
    if style == "device_json":
        # POST /mts/auth/device/login  {"name": "...", "device_password": "..."}
        body = json.dumps({"name": username, "device_password": password}).encode()
        return body, "application/json"
    if style == "oauth2_form":
        body = urllib.parse.urlencode(
            {"username": username, "password": password}
        ).encode()
        return body, "application/x-www-form-urlencoded"
    # user_json fallback
    body = json.dumps({"username": username, "password": password}).encode()
    return body, "application/json"


def _fetch_token(base_url: str, username: str, password: str) -> str:
    """Try every login endpoint in _LOGIN_ENDPOINTS and return the first
    'Bearer <token>' string that succeeds.  Raises RuntimeError otherwise."""
    last_error = "no endpoints tried"

    for suffix, style in _LOGIN_ENDPOINTS:
        url = base_url + suffix
        body, ctype = _make_payload(style, username, password)
        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": ctype, "User-Agent": "AtiFLOW-Tester/2.0"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=8.0, context=_ssl_ctx()) as resp:
                data = json.loads(resp.read().decode())

            raw_token: str = (
                data.get("access_token")
                or data.get("token")
                or data.get("accessToken")
                or data.get("bearer_token")
                or ""
            ).strip()

            if raw_token:
                token = (
                    raw_token
                    if raw_token.lower().startswith("bearer ")
                    else f"Bearer {raw_token}"
                )
                print(f"\n[API conftest] Login OK via {url} (role={data.get('role','?')})")
                return token

            last_error = (
                f"{url}: response OK but no token field "
                f"(keys: {list(data.keys())})"
            )

        except urllib.error.HTTPError as exc:
            last_error = f"{url}: HTTP {exc.code} {exc.reason}"
        except Exception as exc:  # noqa: BLE001
            last_error = f"{url}: {type(exc).__name__}: {exc}"

    raise RuntimeError(
        "[API conftest] Login failed — tried all endpoints.\n"
        f"Last error : {last_error}\n"
        f"Base URL   : {base_url}\n"
        f"Username   : {username}\n"
        "Fix: set MTS_TOKEN in .env to skip auto-login, or check ADMIN_USERNAME / "
        "ADMIN_PASSWORD / MTS_BASE_URL."
    )


# ---------------------------------------------------------------------------
# pytest_configure — runs before ANY test module is imported
# ---------------------------------------------------------------------------

def pytest_configure(config):  # noqa: ANN001
    """Bootstrap environment variables for the API test suite.

    Called by pytest *before* it imports any test file, so module-level
    statements like::

        TOKEN = os.getenv("MTS_TOKEN") or ""

    in test_processing_area_api.py already see the injected value.

    Resolution order for the bearer token (first non-empty wins):
      1. MTS_TOKEN already in the shell
      2. API_BEARER_TOKEN already in the shell
      3. File at MTS_TOKEN_FILE env var path
      4. .mts_token file next to this conftest  (tests/api/.mts_token)
      5. .mts_token file in the project root
      6. Auto-login: POST /mts/auth/device/login with ADMIN credentials
    """
    # ── 1. Load .env (never overwrites existing shell vars) ─────────────────
    _load_dotenv(_ROOT / ".env")

    # ── 2. Publish MTS_BASE_URL ──────────────────────────────────────────────
    base_url = _resolve_base_url()
    os.environ.setdefault("MTS_BASE_URL", base_url)

    # ── 3. Short-circuit if token already present ────────────────────────────
    existing = (
        os.environ.get("MTS_TOKEN", "").strip()
        or os.environ.get("API_BEARER_TOKEN", "").strip()
    )

    if not existing:
        # Check token-file paths
        candidates: list[Path] = []
        if tf := os.environ.get("MTS_TOKEN_FILE", "").strip():
            candidates.append(Path(tf))
        candidates += [
            Path(__file__).parent / ".mts_token",
            _ROOT / ".mts_token",
        ]
        for p in candidates:
            if p.is_file():
                existing = p.read_text().strip()
                if existing:
                    print(f"\n[API conftest] Token loaded from {p}")
                    break

    if existing:
        token = (
            existing
            if existing.lower().startswith("bearer ")
            else f"Bearer {existing}"
        )
        _publish(token)
        return

    # ── 4. Auto-login ────────────────────────────────────────────────────────
    username = os.environ.get("ADMIN_USERNAME", "").strip() or "admin"
    password = os.environ.get("ADMIN_PASSWORD", "").strip() or "admin123"

    try:
        token = _fetch_token(base_url, username, password)
        _publish(token)
    except RuntimeError as exc:
        # Print a clear warning but don't abort collection — individual tests
        # will show their own "MTS_TOKEN required" errors.
        print(f"\n[API conftest] WARNING: {exc}")


def _publish(token: str) -> None:
    """Write the bearer token to every env var the test files check."""
    os.environ["MTS_TOKEN"] = token
    os.environ["API_BEARER_TOKEN"] = token
    print(
        f"[API conftest] MTS_BASE_URL  = {os.environ.get('MTS_BASE_URL')}\n"
        f"[API conftest] MTS_TOKEN     = {token[:55]}..."
    )
