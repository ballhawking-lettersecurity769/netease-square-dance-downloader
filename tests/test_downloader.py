from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from src.downloader import DownloadOutcome, download_one, download_with_jitter


def _mock_session_get(status_code=200, chunks=(b"mp3data",), raise_exc=None):
    session = MagicMock()
    resp = MagicMock()
    resp.status_code = status_code
    if raise_exc:
        resp.raise_for_status.side_effect = raise_exc
    else:
        resp.raise_for_status.return_value = None
    resp.iter_content = lambda chunk_size: iter(chunks)
    ctx = MagicMock()
    ctx.__enter__ = lambda self: resp
    ctx.__exit__ = lambda *a: None
    session.get.return_value = ctx
    return session


def test_download_success(tmp_path: Path):
    candidate = {"idx": 1, "track_id": 100, "name": "最炫民族风",
                 "artist": "凤凰传奇", "fee": 0}
    session = _mock_session_get(chunks=(b"mp3data",))

    outcome = download_one(
        candidate=candidate, level="standard",
        cookies={"MUSIC_U": "x"}, output_dir=tmp_path, session=session,
        url_fn=lambda sid, lvl, ck: {"data": [{"url": "https://x/y.mp3",
                                                 "size": 1024, "level": lvl}]},
    )
    assert outcome.status == "ok"
    assert outcome.file_path is not None
    assert outcome.file_path.exists()
    assert outcome.file_path.read_bytes() == b"mp3data"
    assert outcome.file_path.name == "最炫民族风 - 凤凰传奇.mp3"


def test_download_url_empty(tmp_path: Path):
    candidate = {"idx": 1, "track_id": 100, "name": "x", "artist": "", "fee": 1}
    outcome = download_one(
        candidate=candidate, level="standard", cookies={},
        output_dir=tmp_path, session=MagicMock(),
        url_fn=lambda sid, lvl, ck: {"data": [{"url": None}]},
    )
    assert outcome.status == "failed"
    assert outcome.reason == "url_empty"


def test_download_http_error_raises_for_retry(tmp_path: Path):
    candidate = {"idx": 1, "track_id": 100, "name": "x", "artist": "", "fee": 0}
    session = _mock_session_get(
        status_code=500,
        raise_exc=requests.HTTPError("500 boom"),
    )
    with pytest.raises(requests.HTTPError):
        download_one(
            candidate=candidate, level="standard", cookies={},
            output_dir=tmp_path, session=session,
            url_fn=lambda sid, lvl, ck: {"data": [{"url": "https://x/y.mp3"}]},
        )


def test_download_with_jitter_catches_http_error(tmp_path: Path):
    candidate = {"idx": 1, "track_id": 100, "name": "x", "artist": "", "fee": 0}

    def url_fn(sid, lvl, ck):
        return {"data": [{"url": "https://x/y.mp3"}]}

    session = _mock_session_get(
        status_code=500,
        raise_exc=requests.HTTPError("500 boom"),
    )
    outcome = download_with_jitter(
        candidate=candidate, level="standard", cookies={},
        output_dir=tmp_path, session=session, url_fn=url_fn,
        delay_min=0.0, delay_max=0.0,
    )
    assert outcome.status == "failed"
    assert outcome.reason == "http_error"


def test_download_partial_file_promoted(tmp_path: Path):
    candidate = {"idx": 1, "track_id": 100, "name": "x", "artist": "y", "fee": 0}
    session = _mock_session_get(chunks=(b"a", b"b", b"c"))
    outcome = download_one(
        candidate=candidate, level="standard", cookies={},
        output_dir=tmp_path, session=session,
        url_fn=lambda sid, lvl, ck: {"data": [{"url": "https://x/y.mp3"}]},
    )
    assert outcome.status == "ok"
    assert outcome.file_path.read_bytes() == b"abc"
    # No .part leftover
    assert not (tmp_path / "x - y.mp3.part").exists()
