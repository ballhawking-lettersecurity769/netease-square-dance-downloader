"""Filename sanitization for U-disk (FAT32/exFAT) compatibility."""
from __future__ import annotations

import re

_ILLEGAL = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_WS = re.compile(r"\s+")


def sanitize_filename(name: str, max_len: int = 200) -> str:
    if "." in name:
        stem, _, ext = name.rpartition(".")
    else:
        stem, ext = name, ""
    stem = _ILLEGAL.sub("", stem)
    stem = _WS.sub(" ", stem).strip(" .")
    if not stem:
        stem = "_"
    ext = _ILLEGAL.sub("", ext).strip(" .")
    if ext:
        max_stem = max_len - len(ext) - 1
        if len(stem) > max_stem:
            stem = stem[:max_stem]
        return f"{stem}.{ext}"
    return stem[:max_len]
