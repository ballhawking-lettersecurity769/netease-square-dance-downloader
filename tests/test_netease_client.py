import json
from pathlib import Path

from src.netease_client import load_cookies_dict, save_cookies_playwright


def test_load_cookies_dict(tmp_path: Path):
    p = tmp_path / "cookies.json"
    p.write_text(json.dumps([
        {"name": "MUSIC_U", "value": "abc", "domain": ".music.163.com"},
        {"name": "__csrf", "value": "xyz", "domain": ".music.163.com"},
    ]), encoding="utf-8")
    d = load_cookies_dict(p)
    assert d == {"MUSIC_U": "abc", "__csrf": "xyz"}


def test_load_cookies_dict_missing_file(tmp_path: Path):
    d = load_cookies_dict(tmp_path / "nope.json")
    assert d == {}


def test_save_cookies_playwright(tmp_path: Path):
    p = tmp_path / "cookies.json"
    save_cookies_playwright(p, [
        {"name": "A", "value": "1", "domain": ".music.163.com", "path": "/",
         "expires": 0, "httpOnly": False, "secure": True, "sameSite": "Lax"},
    ])
    loaded = json.loads(p.read_text(encoding="utf-8"))
    assert loaded[0]["name"] == "A"
    assert loaded[0]["value"] == "1"


def test_save_cookies_playwright_creates_parent(tmp_path: Path):
    p = tmp_path / "nested" / "dir" / "cookies.json"
    save_cookies_playwright(p, [{"name": "A", "value": "1"}])
    assert p.exists()
