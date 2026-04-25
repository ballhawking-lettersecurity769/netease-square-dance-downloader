"""End-to-end smoke with mocked network layer."""
import csv
from pathlib import Path
from unittest.mock import MagicMock

from src.downloader import DownloadOutcome
from src.runner import run_download_batch
from src.search import SearchRunner


def test_pipeline_smoke(tmp_path: Path):
    # Stage 1: search + dedupe
    def fake_page(session, query, offset, limit):
        if offset >= 60:
            return []
        return [
            {"track_id": offset + 1, "name": "最炫民族风", "artist": "A",
             "album": "", "fee": 0},
            {"track_id": offset + 2, "name": f"歌曲{offset}", "artist": "B",
             "album": "", "fee": 0},
            {"track_id": offset + 3, "name": "最炫民族风 (DJ版)", "artist": "C",
             "album": "", "fee": 0},
        ]

    cand_csv = tmp_path / "candidates.csv"
    SearchRunner(
        session=MagicMock(), query="广场舞", target=5,
        max_pages=10, page_size=3, page_fn=fake_page,
    ).run(cand_csv)
    rows = list(csv.DictReader(cand_csv.open(encoding="utf-8")))
    assert len(rows) >= 3
    # dedupe: "最炫民族风" kept once
    norm_keys = [r["norm_key"] for r in rows]
    assert len(norm_keys) == len(set(norm_keys))

    # Stage 2: download
    manifest = tmp_path / "manifest.csv"
    failed = tmp_path / "failed.csv"
    out = tmp_path / "out"

    def fake_dl(candidate, **kwargs):
        f = out / f"{candidate['track_id']}.mp3"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b"x")
        return DownloadOutcome(
            status="ok", file_path=f, size_bytes=1, bitrate="standard",
        )

    run_download_batch(
        candidates_csv=cand_csv, manifest_csv=manifest, failed_csv=failed,
        output_dir=out, cookies={}, level="standard",
        session=MagicMock(), url_fn=lambda *a, **kw: {"data": [{"url": "x"}]},
        download_fn=fake_dl,
    )
    manifest_rows = list(csv.DictReader(manifest.open(encoding="utf-8")))
    assert len(manifest_rows) == len(rows)

    # Stage 3: resume — running again should be a no-op
    run_download_batch(
        candidates_csv=cand_csv, manifest_csv=manifest, failed_csv=failed,
        output_dir=out, cookies={}, level="standard",
        session=MagicMock(), url_fn=lambda *a, **kw: {"data": [{"url": "x"}]},
        download_fn=lambda candidate, **kw: (_ for _ in ()).throw(
            AssertionError("should not be called on resume")
        ),
    )
