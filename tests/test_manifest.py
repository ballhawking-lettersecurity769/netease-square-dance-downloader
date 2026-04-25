from pathlib import Path

from src.manifest import ManifestStore, FailureStore


class TestManifestStore:
    def test_empty_file(self, tmp_path: Path):
        m = ManifestStore(tmp_path / "manifest.csv")
        assert m.completed_ids() == set()

    def test_append_and_reload(self, tmp_path: Path):
        path = tmp_path / "manifest.csv"
        m = ManifestStore(path)
        m.append({
            "idx": 1, "track_id": 100, "name": "a", "artist": "x",
            "file_path": "a.mp3", "size_bytes": 1024,
            "bitrate": "standard", "downloaded_at": "2026-04-24T10:00:00",
        })
        m2 = ManifestStore(path)
        assert m2.completed_ids() == {100}

    def test_is_completed(self, tmp_path: Path):
        m = ManifestStore(tmp_path / "manifest.csv")
        m.append({"idx": 1, "track_id": 42, "name": "a", "artist": "",
                  "file_path": "a.mp3", "size_bytes": 0,
                  "bitrate": "", "downloaded_at": ""})
        assert m.is_completed(42)
        assert not m.is_completed(99)

    def test_multiple_rows(self, tmp_path: Path):
        path = tmp_path / "manifest.csv"
        m = ManifestStore(path)
        for i, tid in enumerate([10, 20, 30], start=1):
            m.append({"idx": i, "track_id": tid, "name": f"s{tid}",
                      "artist": "", "file_path": "", "size_bytes": 0,
                      "bitrate": "", "downloaded_at": ""})
        assert ManifestStore(path).completed_ids() == {10, 20, 30}


class TestFailureStore:
    def test_append_reason(self, tmp_path: Path):
        f = FailureStore(tmp_path / "failed.csv")
        f.append({"idx": 1, "track_id": 7, "name": "x", "artist": "",
                  "reason": "vip_required", "http_code": 0,
                  "tried_at": "2026-04-24T10:00:00"})
        assert f.failed_ids() == {7}

    def test_reload(self, tmp_path: Path):
        path = tmp_path / "failed.csv"
        FailureStore(path).append({"idx": 1, "track_id": 7, "name": "", "artist": "",
                                     "reason": "url_empty", "http_code": 0,
                                     "tried_at": ""})
        assert FailureStore(path).failed_ids() == {7}
