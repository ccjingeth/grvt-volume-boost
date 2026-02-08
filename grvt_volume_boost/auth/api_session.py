from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from grvt_volume_boost.runtime import ensure_tls_trust
from grvt_volume_boost.secure_files import ensure_private_dir, restrict_file
from grvt_volume_boost.settings import COOKIE_CACHE_FILE, EDGE_URL, ORIGIN, SESSION_DIR


@dataclass(frozen=True)
class ApiEnv:
    num: int
    api_key: str | None
    api_secret: str | None
    api_passphrase: str | None
    private_key: str | None
    gravity: str | None
    account_id: str | None
    chain_sub_account_id: str | None
    sub_account_id: str | None


def _env(name: str) -> str | None:
    val = os.getenv(name)
    if val is None:
        return None
    s = str(val).strip()
    return s or None


def _env_present(num: int) -> bool:
    keys = [
        f"GRVT_API_KEY_{num}",
        f"GRVT_API_SECRET_{num}",
        f"GRVT_API_PASSPHRASE_{num}",
        f"GRVT_PRIVATE_KEY_{num}",
        f"GRVT_GRAVITY_{num}",
        f"GRVT_ACCOUNT_ID_{num}",
        f"GRVT_CHAIN_SUB_ACCOUNT_ID_{num}",
        f"GRVT_SUB_ACCOUNT_ID_{num}",
    ]
    return any(_env(k) for k in keys)


def load_api_env(num: int) -> ApiEnv | None:
    if not _env_present(num):
        return None
    return ApiEnv(
        num=num,
        api_key=_env(f"GRVT_API_KEY_{num}"),
        api_secret=_env(f"GRVT_API_SECRET_{num}"),
        api_passphrase=_env(f"GRVT_API_PASSPHRASE_{num}"),
        private_key=_env(f"GRVT_PRIVATE_KEY_{num}"),
        gravity=_env(f"GRVT_GRAVITY_{num}"),
        account_id=_env(f"GRVT_ACCOUNT_ID_{num}"),
        chain_sub_account_id=_env(f"GRVT_CHAIN_SUB_ACCOUNT_ID_{num}"),
        sub_account_id=_env(f"GRVT_SUB_ACCOUNT_ID_{num}"),
    )


def _write_cookie_cache(gravity: str) -> None:
    cache = {
        "gravity": gravity,
        "timestamp": time.time(),
        "datetime": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    ensure_private_dir(COOKIE_CACHE_FILE.parent)
    with open(COOKIE_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
    restrict_file(COOKIE_CACHE_FILE)


def _gravity_cookie(gravity: str) -> dict:
    host = urlparse(ORIGIN).hostname or "grvt.io"
    domain = host if host.startswith(".") else f".{host}"
    return {
        "name": "gravity",
        "value": gravity,
        "domain": domain,
        "path": "/",
        "expires": -1,
        "httpOnly": True,
        "secure": True,
        "sameSite": "Lax",
    }


def _build_storage_state(local_storage: dict[str, str], gravity: str | None) -> dict:
    items = [{"name": k, "value": v} for k, v in local_storage.items()]
    state = {"cookies": [], "origins": [{"origin": ORIGIN, "localStorage": items}]}
    if gravity:
        state["cookies"].append(_gravity_cookie(gravity))
    return state


def _extract_ids_from_json(obj: Any) -> dict[str, str]:
    found: dict[str, str] = {}
    key_map = {
        "account_id": "account_id",
        "accountid": "account_id",
        "accountID": "account_id",
        "chain_sub_account_id": "chain_sub_account_id",
        "chainsubaccountid": "chain_sub_account_id",
        "sub_account_id": "sub_account_id",
        "subaccountid": "sub_account_id",
        "subaccount": "sub_account_id",
    }

    def _walk(v: Any) -> None:
        if isinstance(v, dict):
            for k, val in v.items():
                lk = str(k).strip()
                lk_norm = lk.lower().replace("-", "_")
                mapped = key_map.get(lk_norm) or key_map.get(lk)
                if mapped and val is not None:
                    s = str(val).strip()
                    if s:
                        found[mapped] = s
                _walk(val)
        elif isinstance(v, list):
            for item in v:
                _walk(item)

    _walk(obj)
    return found


def api_key_login(env: ApiEnv, *, timeout_sec: float = 30.0) -> tuple[str | None, dict[str, str], str | None]:
    ensure_tls_trust()
    session = requests.Session()

    login_url = _env("GRVT_API_LOGIN_URL") or f"{EDGE_URL}/auth/api_key/login"
    headers_base = {
        "Content-Type": "application/json",
        "Origin": ORIGIN,
        "Referer": f"{ORIGIN}/",
        "X-Api-Source": "WEB",
    }

    payloads = []
    if env.api_key and env.api_secret:
        payloads.append({"apiKey": env.api_key, "apiSecret": env.api_secret})
        payloads.append({"api_key": env.api_key, "api_secret": env.api_secret})
        payloads.append({"key": env.api_key, "secret": env.api_secret})
        if env.api_passphrase:
            payloads.append({"apiKey": env.api_key, "apiSecret": env.api_secret, "passphrase": env.api_passphrase})
            payloads.append({"api_key": env.api_key, "api_secret": env.api_secret, "passphrase": env.api_passphrase})

    header_sets = [
        {},
        {
            "X-Api-Key": env.api_key or "",
            "X-Api-Secret": env.api_secret or "",
        },
        {
            "x-api-key": env.api_key or "",
            "x-api-secret": env.api_secret or "",
        },
    ]
    if env.api_passphrase:
        for h in header_sets:
            h.setdefault("X-Api-Passphrase", env.api_passphrase)
            h.setdefault("x-api-passphrase", env.api_passphrase)

    last_err = None
    info: dict[str, str] = {}
    for headers in header_sets:
        for payload in payloads:
            try:
                r = session.post(login_url, json=payload, headers={**headers_base, **headers}, timeout=timeout_sec)
            except Exception as e:
                last_err = e
                continue

            gravity = session.cookies.get("gravity") or r.cookies.get("gravity")
            try:
                info = _extract_ids_from_json(r.json()) or info
            except Exception:
                pass

            if gravity:
                return gravity, info, None

            # If the response JSON contains a gravity token, accept it.
            try:
                data = r.json()
                for key in ("gravity", "cookie", "token"):
                    val = data.get(key) if isinstance(data, dict) else None
                    if val:
                        return str(val), info, None
            except Exception:
                pass

    if last_err:
        return None, info, f"{last_err}"
    return None, info, "API login failed (no gravity cookie returned)."


def _api_state_path(num: int) -> Path:
    return SESSION_DIR / f"grvt_browser_state_{num}.json"


def _make_grvt_ss_on_chain(private_key: str) -> str:
    payload = {"API": {"privateKey": private_key}}
    return json.dumps(payload, ensure_ascii=False)


def maybe_prepare_api_session(num: int) -> tuple[bool, str | None]:
    env = load_api_env(num)
    if not env:
        return False, None

    if not env.private_key:
        return True, "Missing GRVT_PRIVATE_KEY_{n} for API mode.".replace("{n}", str(num))

    if not env.api_key or not env.api_secret:
        if not env.gravity:
            return True, (
                f"Account {num}: API mode enabled but missing GRVT_API_KEY_{num}/GRVT_API_SECRET_{num} "
                f"and no GRVT_GRAVITY_{num} provided."
            )

    gravity = env.gravity
    info: dict[str, str] = {}
    if not gravity and env.api_key and env.api_secret:
        gravity, info, err = api_key_login(env)
        if not gravity:
            msg = err or "API login failed."
            return True, f"Account {num}: {msg} Set GRVT_GRAVITY_{num} manually if needed."

    account_id = env.account_id or info.get("account_id")
    chain_sub = env.chain_sub_account_id or info.get("chain_sub_account_id")
    sub_account_id = env.sub_account_id or info.get("sub_account_id")

    local_storage: dict[str, str] = {
        "grvt_ss_on_chain": _make_grvt_ss_on_chain(env.private_key),
    }
    if account_id:
        local_storage["grvt:account_id"] = str(account_id)
    if chain_sub:
        local_storage["grvt:chain_sub_account_id"] = str(chain_sub)
    if sub_account_id:
        local_storage["grvt:sub_account_id"] = str(sub_account_id)
    local_storage["grvt:auth_mode"] = "api"

    ensure_private_dir(SESSION_DIR)
    state_path = _api_state_path(num)
    state = _build_storage_state(local_storage, gravity)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    restrict_file(state_path)

    if gravity:
        try:
            _write_cookie_cache(gravity)
        except Exception:
            pass

    # If account IDs are still missing, let the caller surface a clear error.
    if not account_id or not chain_sub:
        return True, (
            f"Account {num}: API session created, but missing GRVT_ACCOUNT_ID_{num} or "
            f"GRVT_CHAIN_SUB_ACCOUNT_ID_{num}. Provide them in .env."
        )

    return True, None


def _infer_account_num(state_path: Path) -> int | None:
    m = re.search(r"grvt_browser_state_(\d+)\.json$", state_path.name)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def refresh_gravity_cookie_for_state(state_path: Path) -> str | None:
    """Refresh gravity cookie using API credentials if available for this account."""
    num = _infer_account_num(state_path)
    if not num:
        return None
    env = load_api_env(num)
    if not env or not env.api_key or not env.api_secret:
        return None
    gravity, info, err = api_key_login(env)
    if not gravity:
        return None
    try:
        _update_state_cookie(state_path, gravity)
    except Exception:
        pass
    try:
        _write_cookie_cache(gravity)
    except Exception:
        pass
    return gravity


def _update_state_cookie(state_path: Path, gravity: str) -> None:
    if not state_path.exists():
        return
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    if "cookies" not in state:
        return
    cookies = state.get("cookies", []) or []
    replaced = False
    for c in cookies:
        try:
            if c.get("name") == "gravity":
                c["value"] = gravity
                replaced = True
        except Exception:
            continue
    if not replaced:
        cookies.append(_gravity_cookie(gravity))
    state["cookies"] = cookies
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    restrict_file(state_path)
