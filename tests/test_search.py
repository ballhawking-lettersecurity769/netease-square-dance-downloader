from unittest.mock import MagicMock

from src.search import SearchRunner, search_page


def test_search_page_parses_response():
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {
            "songs": [
                {"id": 1, "name": "最炫民族风",
                 "artists": [{"name": "凤凰传奇"}],
                 "album": {"name": "album"}, "fee": 0},
                {"id": 2, "name": "小苹果",
                 "artists": [{"name": "筷子兄弟"}],
                 "album": {"name": "album"}, "fee": 1},
            ]
        }
    }
    mock_session.post.return_value = mock_resp
    songs = search_page(mock_session, "广场舞", offset=0, limit=30)
    assert len(songs) == 2
    assert songs[0]["track_id"] == 1
    assert songs[0]["artist"] == "凤凰传奇"
    assert songs[1]["fee"] == 1


def test_search_page_empty_results():
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"result": {"songs": []}}
    mock_session.post.return_value = mock_resp
    assert search_page(mock_session, "xxx", 0, 30) == []


def test_search_runner_dedupes_and_stops_at_target(tmp_path):
    calls = []

    def fake_page(session, query, offset, limit):
        calls.append(offset)
        base = offset
        return [
            {"track_id": base + 0, "name": "最炫民族风", "artist": "A",
             "album": "", "fee": 0},
            {"track_id": base + 1, "name": "最炫民族风 (DJ版)", "artist": "B",
             "album": "", "fee": 0},
            {"track_id": base + 2, "name": f"歌曲{base}", "artist": "X",
             "album": "", "fee": 0},
        ]

    runner = SearchRunner(
        session=MagicMock(),
        query="广场舞",
        target=5,
        max_pages=50,
        page_size=3,
        page_fn=fake_page,
    )
    out_csv = tmp_path / "candidates.csv"
    items = runner.run(out_csv)
    assert len(items) == 5
    assert out_csv.exists()
    lines = out_csv.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 6  # header + 5


def test_search_runner_stops_at_empty_page(tmp_path):
    def fake_page(session, query, offset, limit):
        return [] if offset >= 3 else [
            {"track_id": offset, "name": f"s{offset}", "artist": "",
             "album": "", "fee": 0},
        ]
    runner = SearchRunner(
        session=MagicMock(), query="x", target=500,
        max_pages=10, page_size=1, page_fn=fake_page,
    )
    items = runner.run(tmp_path / "c.csv")
    assert len(items) == 3
