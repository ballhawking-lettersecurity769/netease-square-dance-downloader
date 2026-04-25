"""Stage 1: paginated keyword search with incremental dedupe."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Callable

import requests

from src.dedupe import Deduper


SEARCH_URL = "https://music.163.com/api/search/get/web"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Referer": "https://music.163.com/",
    "Origin": "https://music.163.com",
}


CANDIDATE_FIELDS = [
    "idx", "track_id", "name", "artist", "album",
    "norm_key", "fee", "source_offset",
]


def search_page(
    session: requests.Session,
    query: str,
    offset: int,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Call Netease legacy search API. Returns normalized rows."""
    data = {"s": query, "type": 1, "limit": limit, "offset": offset}
    resp = session.post(SEARCH_URL, data=data, headers=DEFAULT_HEADERS, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    songs = (payload.get("result") or {}).get("songs") or []
    rows: list[dict[str, Any]] = []
    for s in songs:
        artists = s.get("artists") or []
        artist_name = "/".join(a.get("name", "") for a in artists if a.get("name"))
        rows.append({
            "track_id": int(s.get("id", 0)),
            "name": s.get("name", ""),
            "artist": artist_name,
            "album": (s.get("album") or {}).get("name", ""),
            "fee": int(s.get("fee", 0)),
        })
    return rows


class SearchRunner:
    def __init__(
        self,
        session: requests.Session,
        query: str,
        target: int,
        max_pages: int,
        page_size: int = 30,
        page_fn: Callable[..., list[dict[str, Any]]] = search_page,
    ):
        self.session = session
        self.query = query
        self.target = target
        self.max_pages = max_pages
        self.page_size = page_size
        self.page_fn = page_fn

    def run(self, out_csv: Path) -> list[dict[str, Any]]:
        deduper = Deduper()
        for page in range(self.max_pages):
            offset = page * self.page_size
            rows = self.page_fn(
                self.session, self.query,
                offset=offset, limit=self.page_size,
            )
            if not rows:
                break
            for row in rows:
                if deduper.add(row):
                    deduper.items[-1]["source_offset"] = offset
                if len(deduper) >= self.target:
                    break
            if len(deduper) >= self.target:
                break

        out_csv.parent.mkdir(parents=True, exist_ok=True)
        with out_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CANDIDATE_FIELDS)
            writer.writeheader()
            for idx, item in enumerate(deduper.items, start=1):
                writer.writerow({
                    "idx": idx,
                    "track_id": item["track_id"],
                    "name": item["name"],
                    "artist": item["artist"],
                    "album": item.get("album", ""),
                    "norm_key": item["norm_key"],
                    "fee": item.get("fee", 0),
                    "source_offset": item.get("source_offset", 0),
                })
        return deduper.items
