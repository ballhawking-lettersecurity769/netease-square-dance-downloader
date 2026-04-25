"""Append-only CSV stores for manifest and failures with resume support."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


MANIFEST_FIELDS = [
    "idx", "track_id", "name", "artist",
    "file_path", "size_bytes", "bitrate", "downloaded_at",
]

FAILED_FIELDS = [
    "idx", "track_id", "name", "artist",
    "reason", "http_code", "tried_at",
]


class _CsvStore:
    def __init__(self, path: Path, fields: list[str]):
        self.path = Path(path)
        self.fields = fields
        self._completed: set[int] = set()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    self._completed.add(int(row["track_id"]))
                except (KeyError, ValueError):
                    continue

    def append(self, row: dict[str, Any]) -> None:
        write_header = not self.path.exists() or self.path.stat().st_size == 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.fields)
            if write_header:
                writer.writeheader()
            writer.writerow({k: row.get(k, "") for k in self.fields})
            f.flush()
        try:
            self._completed.add(int(row["track_id"]))
        except (KeyError, ValueError):
            pass


class ManifestStore(_CsvStore):
    def __init__(self, path: Path):
        super().__init__(path, MANIFEST_FIELDS)

    def completed_ids(self) -> set[int]:
        return set(self._completed)

    def is_completed(self, track_id: int) -> bool:
        return int(track_id) in self._completed


class FailureStore(_CsvStore):
    def __init__(self, path: Path):
        super().__init__(path, FAILED_FIELDS)

    def failed_ids(self) -> set[int]:
        return set(self._completed)
