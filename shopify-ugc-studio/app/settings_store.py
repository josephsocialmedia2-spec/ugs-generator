from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULTS = {
    "shopify_shop": "",
    "shopify_access_token": "",
    "avatar_name": "F1 Avatar",
    "avatar_voice_mode": "local",
}


def load_settings(base: Path) -> dict:
    path = base / "settings.json"
    data = dict(DEFAULTS)
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                for key in DEFAULTS:
                    if key in payload:
                        data[key] = str(payload.get(key) or "")
        except Exception:
            pass
    if os.environ.get("SHOPIFY_SHOP"):
        data["shopify_shop"] = os.environ["SHOPIFY_SHOP"]
    if os.environ.get("SHOPIFY_ACCESS_TOKEN"):
        data["shopify_access_token"] = os.environ["SHOPIFY_ACCESS_TOKEN"]
    return data


def save_settings(base: Path, updates: dict) -> dict:
    current = load_settings(base)
    for key in DEFAULTS:
        if key in updates:
            value = updates.get(key)
            if value is None:
                continue
            current[key] = str(value).strip()
    path = base / "settings.json"
    persistent = {key: current.get(key, "") for key in DEFAULTS}
    path.write_text(json.dumps(persistent, ensure_ascii=False, indent=2), encoding="utf-8")
    return current


def public_settings(settings: dict) -> dict:
    return {
        "shopify_shop": settings.get("shopify_shop", ""),
        "shopify_configured": bool(settings.get("shopify_shop") and settings.get("shopify_access_token")),
        "shopify_token_masked": _mask(settings.get("shopify_access_token", "")),
        "avatar_name": settings.get("avatar_name", "F1 Avatar"),
        "avatar_voice_mode": settings.get("avatar_voice_mode", "local"),
    }


def _mask(value: str) -> str:
    value = str(value or "")
    if not value:
        return ""
    if len(value) <= 8:
        return "••••••••"
    return value[:4] + "••••••••" + value[-4:]
