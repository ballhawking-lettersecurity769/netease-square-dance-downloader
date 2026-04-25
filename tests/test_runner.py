import csv
from pathlib import Path
from unittest.mock import MagicMock

from src.downloader import DownloadOutcome
from src.manifest import ManifestStore
from src.runner import run_download_batch


def _write_candidates(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "idx", "track_id", "name", "artist",
            "album", "norm_key", "fee", "source_offset",
        ])
        w.writeheader()
        for r in rows:
            w.writerow(r)


def test_run_download_batch_happy(tmp_path):
    cand = tmp_path / "candidates.csv"
    _write_candidates(cand, [
        {"idx": 1, "track_id": 100, "name": "a", "artist": "x", "album": "",
         "norm_key": "a", "fee": 0, "source_offset": 0},
        {"idx": 2, "track_id": 200, "name": "b", "artist": "y", "album": "",
         "norm_key": "b", "fee": 0, "source_offset": 0},
    ])
    manifest = tmp_path / "manifest.csv"
    failed = tmp_path / "failed.csv"
    out = tmp_path / "downloads"

    def fake_download(candidate, **kwargs):
        f = out / f"{candidate['track_id']}.mp3"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b"x")
        return DownloadOutcome(
            status="ok", file_path=f, size_bytes=1, bitrate="standard",
        )

    run_download_batch(
        candidates_csv=cand, manifest_csv=manifest, failed_csv=failed,
        output_dir=out, cookies={}, level="standard",
        session=MagicMock(), url_fn=lambda *a, **kw: {"data": [{"url": "x"}]},
        download_fn=fake_download,
    )
    assert manifest.exists()
    lines = manifest.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3  # header + 2


def test_run_download_batch_skips_already_done(tmp_path):
    cand = tmp_path / "candidates.csv"
    _write_candidates(cand, [
        {"idx": 1, "track_id": 100, "name": "a", "artist": "", "album": "",
         "norm_key": "a", "fee": 0, "source_offset": 0},
    ])
    manifest = tmp_path / "manifest.csv"
    ManifestStore(manifest).append({
        "idx": 1, "track_id": 100, "name": "a", "artist": "",
        "file_path": "a.mp3", "size_bytes": 0, "bitrate": "",
        "downloaded_at": "",
    })
    failed = tmp_path / "failed.csv"
    calls = []

    def fake_download(candidate, **kwargs):
        calls.append(candidate["track_id"])
        return DownloadOutcome(status="ok")

    run_download_batch(
        candidates_csv=cand, manifest_csv=manifest, failed_csv=failed,
        output_dir=tmp_path / "out", cookies={}, level="standard",
        session=MagicMock(), url_fn=lambda *a, **kw: {},
        download_fn=fake_download,
    )
    assert calls == []


def test_run_download_batch_failures_logged(tmp_path):
    cand = tmp_path / "candidates.csv"
    _write_candidates(cand, [
        {"idx": 1, "track_id": 100, "name": "a", "artist": "", "album": "",
         "norm_key": "a", "fee": 1, "source_offset": 0},
    ])
    manifest = tmp_path / "manifest.csv"
    failed = tmp_path / "failed.csv"

    def fake_download(candidate, **kwargs):
        return DownloadOutcome(status="failed", reason="vip_required")

    run_download_batch(
        candidates_csv=cand, manifest_csv=manifest, failed_csv=failed,
        output_dir=tmp_path / "out", cookies={}, level="standard",
        session=MagicMock(), url_fn=lambda *a, **kw: {},
        download_fn=fake_download,
    )
    assert failed.exists()
    failed_lines = failed.read_text(encoding="utf-8").splitlines()
    assert len(failed_lines) == 2  # header + 1
    assert "vip_required" in failed_lines[1]


def test_run_download_batch_skips_previously_failed(tmp_path):
    cand = tmp_path / "candidates.csv"
    _write_candidates(cand, [
        {"idx": 1, "track_id": 100, "name": "a", "artist": "", "album": "",
         "norm_key": "a", "fee": 0, "source_offset": 0},
    ])
    manifest = tmp_path / "manifest.csv"
    failed = tmp_path / "failed.csv"
    # Pre-populate failed
    from src.manifest import FailureStore
    FailureStore(failed).append({
        "idx": 1, "track_id": 100, "name": "a", "artist": "",
        "reason": "vip_required", "http_code": 0, "tried_at": "",
    })
    calls = []

    def fake_download(candidate, **kwargs):
        calls.append(candidate["track_id"])
        return DownloadOutcome(status="ok")

    run_download_batch(
        candidates_csv=cand, manifest_csv=manifest, failed_csv=failed,
        output_dir=tmp_path / "out", cookies={}, level="standard",
        session=MagicMock(), url_fn=lambda *a, **kw: {},
        download_fn=fake_download,
    )
    assert calls == []  # skipped
