"""Stage 2: per-song download with retry, jitter, and failure recording."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.sanitize import sanitize_filename


@dataclass
class DownloadOutcome:
    status: str  # "ok" | "failed" | "skipped"
    file_path: Path | None = None
    size_bytes: int = 0
    bitrate: str = ""
    reason: str = ""
    http_code: int = 0


def _build_filename(name: str, artist: str) -> str:
    base = f"{name} - {artist}" if artist else name
    return sanitize_filename(f"{base}.mp3")


def download_one(
    candidate: dict[str, Any],
    level: str,
    cookies: dict[str, str],
    output_dir: Path,
    session: requests.Session,
    url_fn: Callable[[int, str, dict[str, str]], dict[str, Any]],
) -> DownloadOutcome:
    """Single-song download. Raises on HTTP errors so tenacity can retry."""
    track_id = int(candidate["track_id"])
    name = candidate.get("name", "")
    artist = candidate.get("artist", "")

    info = url_fn(track_id, level, cookies)
    data_list = info.get("data") or [{}]
    data = data_list[0] if data_list else {}
    url = data.get("url")
    if not url:
        return DownloadOutcome(status="failed", reason="url_empty")

    filename = _build_filename(name, artist)
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / filename
    part = dest.with_suffix(dest.suffix + ".part")

    try:
        with session.get(url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            with part.open("wb") as f:
                for chunk in resp.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
        part.rename(dest)
    except Exception:
        if part.exists():
            try:
                part.unlink()
            except OSError:
                pass
        raise

    size = dest.stat().st_size
    return DownloadOutcome(
        status="ok",
        file_path=dest,
        size_bytes=size,
        bitrate=str(data.get("level") or level),
    )


_download_one_retry = retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    retry=retry_if_exception_type((requests.RequestException,)),
)(download_one)


def download_with_jitter(
    candidate: dict[str, Any],
    level: str,
    cookies: dict[str, str],
    output_dir: Path,
    session: requests.Session,
    url_fn: Callable[[int, str, dict[str, str]], dict[str, Any]],
    delay_min: float = 1.0,
    delay_max: float = 2.0,
) -> DownloadOutcome:
    """Pre-sleep + retry wrapper. Never raises; always returns an Outcome."""
    if delay_max > 0:
        time.sleep(random.uniform(delay_min, delay_max))
    try:
        return _download_one_retry(
            candidate=candidate, level=level, cookies=cookies,
            output_dir=output_dir, session=session, url_fn=url_fn,
        )
    except requests.RequestException as e:
        code = getattr(getattr(e, "response", None), "status_code", 0) or 0
        return DownloadOutcome(status="failed", reason="http_error", http_code=code)
    except Exception as e:  # noqa: BLE001
        return DownloadOutcome(status="failed", reason=f"error:{type(e).__name__}")
