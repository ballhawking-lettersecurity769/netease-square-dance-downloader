"""Stage 2 orchestration: iterate candidates, download, record outcomes."""
from __future__ import annotations

import csv
import signal
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
)

from src.downloader import DownloadOutcome, download_with_jitter
from src.manifest import FailureStore, ManifestStore


_STOP = {"flag": False}


def _install_sigint() -> None:
    def _handler(signum, frame):  # noqa: ARG001
        _STOP["flag"] = True
        print("\n[!] Ctrl+C received, finishing current item then exiting...")

    try:
        signal.signal(signal.SIGINT, _handler)
    except (ValueError, OSError):
        # Running in a non-main thread (e.g., pytest subprocess); skip.
        pass


def run_download_batch(
    *,
    candidates_csv: Path,
    manifest_csv: Path,
    failed_csv: Path,
    output_dir: Path,
    cookies: dict[str, str],
    level: str,
    session,
    url_fn: Callable[..., dict[str, Any]],
    download_fn: Callable[..., DownloadOutcome] = download_with_jitter,
    delay_min: float = 1.0,
    delay_max: float = 2.0,
) -> None:
    _install_sigint()
    _STOP["flag"] = False  # reset between runs

    manifest = ManifestStore(manifest_csv)
    failures = FailureStore(failed_csv)
    completed = manifest.completed_ids()
    already_failed = failures.failed_ids()

    with Path(candidates_csv).open("r", encoding="utf-8", newline="") as f:
        all_rows = list(csv.DictReader(f))

    rows_to_do = [
        r for r in all_rows
        if int(r["track_id"]) not in completed
        and int(r["track_id"]) not in already_failed
    ]

    if not rows_to_do:
        print("[i] nothing to do — all candidates already processed")
        return

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("downloading", total=len(rows_to_do))
        for row in rows_to_do:
            if _STOP["flag"]:
                break
            candidate = {
                "idx": int(row["idx"]),
                "track_id": int(row["track_id"]),
                "name": row["name"],
                "artist": row["artist"],
                "fee": int(row.get("fee") or 0),
            }
            outcome = download_fn(
                candidate=candidate, level=level, cookies=cookies,
                output_dir=output_dir, session=session, url_fn=url_fn,
                delay_min=delay_min, delay_max=delay_max,
            )
            now = datetime.now().isoformat(timespec="seconds")
            if outcome.status == "ok":
                manifest.append({
                    "idx": candidate["idx"],
                    "track_id": candidate["track_id"],
                    "name": candidate["name"],
                    "artist": candidate["artist"],
                    "file_path": str(outcome.file_path or ""),
                    "size_bytes": outcome.size_bytes,
                    "bitrate": outcome.bitrate,
                    "downloaded_at": now,
                })
            else:
                failures.append({
                    "idx": candidate["idx"],
                    "track_id": candidate["track_id"],
                    "name": candidate["name"],
                    "artist": candidate["artist"],
                    "reason": outcome.reason or "unknown",
                    "http_code": outcome.http_code,
                    "tried_at": now,
                })
            progress.update(task, advance=1)
