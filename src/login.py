"""Playwright QR login → cookies.json."""
from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.netease_client import save_cookies_playwright


LOGIN_URL = "https://music.163.com/#/login"
TIMEOUT_SEC = 300
POLL_INTERVAL_SEC = 2


def run_qr_login(output: Path) -> Path:
    """Open Chromium, wait for QR scan, save cookies to `output`.

    Returns the path to the saved cookies JSON.
    Raises TimeoutError if login not detected within TIMEOUT_SEC.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.goto(LOGIN_URL)
        print(
            f"[i] 请在弹出的浏览器中用手机网易云 App 扫码登录 "
            f"(超时 {TIMEOUT_SEC // 60} 分钟)"
        )

        start = time.monotonic()
        logged_in = False
        while time.monotonic() - start < TIMEOUT_SEC:
            cookies = context.cookies()
            if any(c["name"] == "MUSIC_U" and c.get("value") for c in cookies):
                logged_in = True
                break
            time.sleep(POLL_INTERVAL_SEC)

        if not logged_in:
            browser.close()
            raise TimeoutError(
                f"{TIMEOUT_SEC // 60} 分钟内未检测到登录，放弃。"
            )

        cookies = context.cookies()
        save_cookies_playwright(Path(output), cookies)
        print(f"[✓] cookies saved to {output}")
        browser.close()
        return Path(output)
