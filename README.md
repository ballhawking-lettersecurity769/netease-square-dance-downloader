# netease-square-dance-downloader

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-45%20passed-brightgreen.svg)](#testing)

> **English** | [简体中文](README.zh-CN.md)

Batch downloader for Netease Cloud Music square-dance (广场舞) songs — designed
to fill a USB stick with 500 deduplicated tracks for an external speaker.

Built around the read-only side of [Suxiaoqinx/Netease_url](https://github.com/Suxiaoqinx/Netease_url),
with Playwright-based QR login, paginated keyword search that bypasses the
vendor's missing `offset` parameter, smart title-normalization dedupe, and
resumable batch downloads.

## Features

- **QR login** — Playwright opens Chromium, you scan with your phone, cookies
  persist to JSON. No need to copy cookies from DevTools.
- **Smart dedupe** — `最炫民族风`, `最炫民族风 (DJ版)`, `最炫民族风【广场舞】`,
  `最炫民族风 Remix` all collapse to one track. First-wins.
- **Two-stage execution** — `search` produces `candidates.csv` you can audit
  before `download` starts pulling MP3s.
- **Resumable** — `manifest.csv` tracks completed downloads; rerun to skip them.
- **USB-friendly** — flat output `<Title> - <Artist>.mp3` with FAT32/exFAT
  illegal characters stripped.
- **Tunable rate-limiting** — 1-2s jitter, tenacity exponential-backoff retries,
  graceful Ctrl+C exit.
- **Quality levels** — defaults to 128 kbps `standard`; if you have VIP, switch
  to `exhigh` (320 kbps) or `lossless` (FLAC).

## Quick Start

```bash
# Prerequisites: Python 3.11+, git
git clone https://github.com/Zhanglala103838/netease-square-dance-downloader.git
cd netease-square-dance-downloader

python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/playwright install chromium

# Pin and clone the upstream Netease_url library
scripts/fetch_vendor.sh

cp .env.example .env  # tweak OUTPUT_DIR / TARGET_COUNT / QUERY as desired
```

## Usage

```bash
# 1. QR login (browser opens, scan with the Netease Cloud Music mobile app)
.venv/bin/python -m src.cli login

# 2. Stage 1: paginated search + dedupe → data/candidates.csv
.venv/bin/python -m src.cli search --target 500

# 3. Stage 2: download (use --output to point at your USB mount)
.venv/bin/python -m src.cli download --output /Volumes/UDISK/SquareDance

# 4. Retry failed items (e.g. after upgrading to a VIP cookie)
.venv/bin/python -m src.cli retry --output /Volumes/UDISK/SquareDance
```

### Audio Quality

Default is `standard` (128 kbps MP3). Override with `--level`:

| Level      | Format          | Account Required |
|------------|-----------------|------------------|
| `standard` | 128 kbps MP3    | Free             |
| `exhigh`   | 320 kbps MP3    | Free / VIP       |
| `lossless` | FLAC            | VIP              |
| `hires`    | 24-bit Hi-Res   | SVIP             |

## Output

| Path                          | Description                                       |
|-------------------------------|---------------------------------------------------|
| `data/cookies.json`           | Playwright-saved Netease session cookies          |
| `data/candidates.csv`         | Stage 1 deduped results (one row per track)       |
| `data/manifest.csv`           | Successful downloads — read for resume support    |
| `data/failed.csv`             | Failed items with `reason` column                 |
| `downloads/` (or `--output`)  | Flat MP3 files                                    |

## Architecture

```
login (Playwright) ──→ cookies.json
                           │
                           ▼
search (legacy /api/search/get/web with offset)
   │
   └─→ dedupe (title normalization, first-wins) ──→ candidates.csv
                                                          │
                                                          ▼
runner ── per-track ──→ downloader (vendor url_v1 + retry)
   │                          │
   ├─→ manifest.csv (success) │
   └─→ failed.csv (error)     ▼
                           downloads/*.mp3
```

The vendor library exposes `search_music(keywords, cookies, limit)` but
**not `offset`**, so paginated search calls Netease's legacy
`/api/search/get/web` endpoint directly (no encryption needed). For
`/song/url` resolution we use the vendor's `url_v1`, which handles the
weapi encryption.

## Testing

```bash
.venv/bin/pytest -v
```

45 unit tests cover dedupe, filename sanitization, manifest I/O, paginated
search, downloader retries, runner orchestration, and an end-to-end smoke
test — all using mocks, no real network calls.

## Configuration

`.env` (copy from `.env.example`):

| Key                | Default                  | Notes                              |
|--------------------|--------------------------|------------------------------------|
| `COOKIES_PATH`     | `data/cookies.json`      |                                    |
| `CANDIDATES_PATH`  | `data/candidates.csv`    |                                    |
| `MANIFEST_PATH`    | `data/manifest.csv`      |                                    |
| `FAILED_PATH`      | `data/failed.csv`        |                                    |
| `OUTPUT_DIR`       | `downloads`              | Set to USB mount path              |
| `TARGET_COUNT`     | `500`                    |                                    |
| `MAX_PAGES`        | `100`                    | Hard ceiling for search pagination |
| `DELAY_MIN_SEC`    | `1.0`                    |                                    |
| `DELAY_MAX_SEC`    | `2.0`                    |                                    |
| `RETRY_MAX`        | `3`                      |                                    |
| `LEVEL`            | `standard`               | See quality table above            |
| `QUERY`            | `广场舞`                 | Default search keyword             |

## Caveats

- **VIP-exclusive tracks** without an authorized cookie return empty URLs;
  they're logged to `failed.csv` with `reason=url_empty`.
- **Anti-fraud throttling** kicks in if you hammer the API. Default jitter
  (1-2 s) keeps you safe for ~500 tracks; pushing concurrency higher invites
  IP-level cooldowns.
- **Cookie expiry** — Stage 2 returning 401 means run `login` again.
- **Ctrl+C** is graceful: it finishes the current track, flushes manifest,
  removes the `.part` file, and exits with code 130. Resume just by rerunning.

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

- [Suxiaoqinx/Netease_url](https://github.com/Suxiaoqinx/Netease_url) for the
  weapi encryption / cookie management used as a library here.
- The community-maintained [Netease Cloud Music API docs](https://neteasecloudmusicapi.vercel.app/)
  for endpoint references.
