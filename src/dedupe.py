"""Title normalization and dedupe for square-dance songs."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any


_PAREN_RE = re.compile(r"[\(（\[【][^)）\]】]*[\)）\]】]")
_TAG_WORDS = [
    "dj版", "dj", "remix", "广场舞版", "广场舞", "伴奏",
    "live", "现场版", "抖音版", "完整版", "精选版",
    "ver", "version", "cover", "翻唱",
]
_PUNCT_RE = re.compile(r"[\s\-_·・、,，.。!！?？:：;；\'\"`~]")


def normalize_title(s: str) -> str:
    """Collapse incidental differences (case, brackets, version tags, punctuation)."""
    s = s.lower()
    s = _PAREN_RE.sub("", s)
    for tag in _TAG_WORDS:
        s = s.replace(tag, "")
    s = unicodedata.normalize("NFKC", s)
    s = _PUNCT_RE.sub("", s)
    return s.strip()


@dataclass
class Deduper:
    _seen: set[str] = field(default_factory=set)
    items: list[dict[str, Any]] = field(default_factory=list)

    def add(self, song: dict[str, Any]) -> bool:
        """First-wins dedupe. Returns True if the song was kept, False if dropped."""
        key = normalize_title(str(song.get("name", "")))
        if not key or key in self._seen:
            return False
        self._seen.add(key)
        enriched = dict(song)
        enriched["norm_key"] = key
        self.items.append(enriched)
        return True

    def __len__(self) -> int:
        return len(self.items)
