"""Shared live API client for run_mts*.py test suites.

Provides:
  - LiveAPIClient  — authenticated requests session against the real MTS API
  - get_client()   — convenience factory (reads from env or logs in)

All run_mts*.py files import from here so login logic lives in one place.
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import requests
import urllib3

# Suppress SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_ROOT = Path(__file__).resolve().parent.parent  # AtiFlowAutomation-main/

# ── Login endpoint (discovered from /openapi.json) ───────────────────────────
_LOGIN_CANDIDATES = [
    ("/mts/auth/device/login", "device"),   # ← primary (real endpoint)
    ("/auth/token",            "oauth2"),
    ("/api/auth/token",        "oauth2"),
    ("/auth/login",            "json"),
    ("/api/login",             "json"),
]


def _load_dotenv(path: Path) -> None:
    try:
        with open(path) as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass


def _ssl_ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _resolve_base_url() -> str:
    raw = (
        os.environ.get("MTS_BASE_URL", "").strip()
        or os.environ.get("BASE_URL", "").strip()
        or "http://192.168.6.32:8000"
    )
    if raw.endswith("/login"):
        raw = raw[: -len("/login")]
    return raw.rstrip("/")


def fetch_token(base_url: str, username: str, password: str) -> str:
    """POST to the login endpoint and return 'Bearer <token>'.  Raises on failure."""
    last_error = ""
    for suffix, style in _LOGIN_CANDIDATES:
        url = base_url + suffix
        try:
            if style == "device":
                body = json.dumps({"name": username, "device_password": password}).encode()
                ctype = "application/json"
            elif style == "oauth2":
                body = urllib.parse.urlencode({"username": username, "password": password}).encode()
                ctype = "application/x-www-form-urlencoded"
            else:
                body = json.dumps({"username": username, "password": password}).encode()
                ctype = "application/json"

            req = urllib.request.Request(
                url, data=body,
                headers={"Content-Type": ctype, "User-Agent": "AtiFLOW-Tester/2.0"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=8.0, context=_ssl_ctx()) as resp:
                data = json.loads(resp.read().decode())

            raw = (
                data.get("access_token") or data.get("token")
                or data.get("accessToken") or data.get("bearer_token") or ""
            ).strip()
            if raw:
                token = raw if raw.lower().startswith("bearer ") else f"Bearer {raw}"
                os.environ["MTS_TOKEN"] = token
                os.environ["API_BEARER_TOKEN"] = token
                return token
            last_error = f"{url}: no token in response (keys={list(data.keys())})"
        except urllib.error.HTTPError as e:
            last_error = f"{url}: HTTP {e.code}"
        except Exception as e:
            last_error = f"{url}: {type(e).__name__}: {e}"

    raise RuntimeError(
        f"Live API login failed.\nLast error: {last_error}\n"
        "Set MTS_TOKEN in .env to skip auto-login."
    )


class LiveAPIClient:
    """Thin wrapper around requests.Session pointed at the real MTS API.

    Usage::

        client = LiveAPIClient()          # auto-logins using .env credentials
        resp = client.get("/mts/processing-area/")
        resp = client.post("/mts/processing-area/", json={"processing_area_name": "Test"})

    The session automatically adds:
      - Authorization: Bearer <token>
      - Content-Type: application/json
      - SSL verification disabled (self-signed cert)
    """

    def __init__(self, token: str = "", base_url: str = ""):
        # Load .env
        _load_dotenv(_ROOT / ".env")

        self.base_url = base_url or _resolve_base_url()

        # Resolve token: env var → file → auto-login
        if not token:
            token = (
                os.environ.get("MTS_TOKEN", "").strip()
                or os.environ.get("API_BEARER_TOKEN", "").strip()
            )
        if not token:
            for p in [Path(__file__).parent / ".mts_token", _ROOT / ".mts_token"]:
                if p.is_file():
                    token = p.read_text().strip()
                    break
        if not token:
            username = os.environ.get("ADMIN_USERNAME", "admin").strip() or "admin"
            password = os.environ.get("ADMIN_PASSWORD", "admin123").strip() or "admin123"
            token = fetch_token(self.base_url, username, password)
            print(f"[LiveAPIClient] Logged in → {self.base_url}")

        self.token = token if token.lower().startswith("bearer ") else f"Bearer {token}"

        self._session = requests.Session()
        self._session.verify = False
        self._session.headers.update({
            "Authorization": self.token,
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        })

    # ── HTTP verbs ────────────────────────────────────────────────────────────

    def get(self, path: str, **kwargs) -> requests.Response:
        return self._session.get(self.base_url + path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self._session.post(self.base_url + path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self._session.put(self.base_url + path, **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        return self._session.patch(self.base_url + path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self._session.delete(self.base_url + path, **kwargs)

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        return self._session.request(method, self.base_url + path, **kwargs)

    # ── Health helpers ────────────────────────────────────────────────────────

    def health(self) -> dict:
        return self.get("/health").json()

    def ping(self) -> bool:
        try:
            return self.get("/health").status_code == 200
        except Exception:
            return False

    def close(self):
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


# ── Convenience factory ───────────────────────────────────────────────────────

_shared_client: LiveAPIClient | None = None


def get_client(force_new: bool = False) -> LiveAPIClient:
    """Return a module-level shared client (singleton per process).

    Use ``force_new=True`` to create a fresh client with a new login.
    """
    global _shared_client
    if _shared_client is None or force_new:
        _shared_client = LiveAPIClient()
    return _shared_client
