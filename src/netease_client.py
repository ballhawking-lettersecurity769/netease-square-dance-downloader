"""Thin wrappers around vendor Netease_url + cookie IO."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


VENDOR_PATH = Path(__file__).resolve().parent.parent / "vendor" / "netease_url"
if str(VENDOR_PATH) not in sys.path:
    sys.path.insert(0, str(VENDOR_PATH))


def load_cookies_dict(path: Path) -> dict[str, str]:
    """Load Playwright-format cookies.json into a dict suitable for vendor funcs."""
    p = Path(path)
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {c["name"]: c["value"] for c in data if "name" in c and "value" in c}


def save_cookies_playwright(path: Path, cookies: list[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(cookies, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def vendor_url_v1(song_id: int, level: str, cookies: dict[str, str]) -> dict[str, Any]:
    from music_api import url_v1  # type: ignore[import-not-found]
    return url_v1(song_id, level, cookies)


def vendor_name_v1(song_id: int) -> dict[str, Any]:
    from music_api import name_v1  # type: ignore[import-not-found]
    return name_v1(song_id)
