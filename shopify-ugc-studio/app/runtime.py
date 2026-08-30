from __future__ import annotations

import os
import sys
from pathlib import Path

APP_FOLDER = "ShopifyUGCStudio"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[1]


def data_root() -> Path:
    override = os.environ.get("UGC_STUDIO_HOME", "").strip()
    if override:
        root = Path(override).expanduser().resolve()
    elif is_frozen() and os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
        root = base / APP_FOLDER
    else:
        root = resource_root()
    root.mkdir(parents=True, exist_ok=True)
    return root
