"""Typer CLI: login | search | download | retry."""
from __future__ import annotations

import csv
import os
from pathlib import Path

import requests
import typer
from dotenv import load_dotenv

from src.login import run_qr_login
from src.netease_client import load_cookies_dict, vendor_url_v1
from src.runner import run_download_batch
from src.search import CANDIDATE_FIELDS, SearchRunner


app = typer.Typer(
    help="广场舞 500 首批量下载器",
    no_args_is_help=True,
    add_completion=False,
)
load_dotenv()


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _session(cookies: dict[str, str] | None = None) -> requests.Session:
    s = requests.Session()
    if cookies:
        s.cookies.update(cookies)
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
    })
    return s


@app.command()
def login(
    output: Path = typer.Option(
        Path(_env("COOKIES_PATH", "data/cookies.json")),
        help="Path to save cookies JSON",
    ),
):
    """Playwright 扫码登录，cookie 持久化到 JSON。"""
    run_qr_login(output)


@app.command()
def search(
    query: str = typer.Option(_env("QUERY", "广场舞")),
    target: int = typer.Option(int(_env("TARGET_COUNT", "500"))),
    max_pages: int = typer.Option(int(_env("MAX_PAGES", "100"))),
    cookies_path: Path = typer.Option(
        Path(_env("COOKIES_PATH", "data/cookies.json"))
    ),
    out: Path = typer.Option(
        Path(_env("CANDIDATES_PATH", "data/candidates.csv"))
    ),
):
    """Stage 1: 翻页搜索 + 去重 → candidates.csv"""
    cookies = load_cookies_dict(cookies_path)
    if not cookies:
        typer.echo(
            "[!] 未找到 cookie，将匿名搜索（结果数量可能受限）。"
            "建议先运行 `music163 login`。"
        )
    session = _session(cookies)
    runner = SearchRunner(
        session=session,
        query=query,
        target=target,
        max_pages=max_pages,
        page_size=30,
    )
    items = runner.run(out)
    typer.echo(f"[✓] 去重后产出 {len(items)} 条候选 → {out}")


@app.command()
def download(
    candidates_csv: Path = typer.Option(
        Path(_env("CANDIDATES_PATH", "data/candidates.csv"))
    ),
    manifest_csv: Path = typer.Option(
        Path(_env("MANIFEST_PATH", "data/manifest.csv"))
    ),
    failed_csv: Path = typer.Option(
        Path(_env("FAILED_PATH", "data/failed.csv"))
    ),
    output: Path = typer.Option(Path(_env("OUTPUT_DIR", "downloads"))),
    cookies_path: Path = typer.Option(
        Path(_env("COOKIES_PATH", "data/cookies.json"))
    ),
    level: str = typer.Option(
        _env("LEVEL", "standard"),
        help="Audio quality: standard / exhigh / lossless / hires (VIP only)",
    ),
    delay_min: float = typer.Option(float(_env("DELAY_MIN_SEC", "1.0"))),
    delay_max: float = typer.Option(float(_env("DELAY_MAX_SEC", "2.0"))),
):
    """Stage 2: 按 candidates.csv 下载。"""
    cookies = load_cookies_dict(cookies_path)
    if not cookies:
        typer.echo(
            "[✗] 未找到 cookie。请先运行 `music163 login`。"
        )
        raise typer.Exit(code=2)
    session = _session(cookies)
    run_download_batch(
        candidates_csv=candidates_csv,
        manifest_csv=manifest_csv,
        failed_csv=failed_csv,
        output_dir=output,
        cookies=cookies,
        level=level,
        session=session,
        url_fn=vendor_url_v1,
        delay_min=delay_min,
        delay_max=delay_max,
    )
    typer.echo(
        f"[✓] 完成。已下载清单: {manifest_csv}；失败清单: {failed_csv}"
    )


@app.command()
def retry(
    failed_csv: Path = typer.Option(
        Path(_env("FAILED_PATH", "data/failed.csv"))
    ),
    manifest_csv: Path = typer.Option(
        Path(_env("MANIFEST_PATH", "data/manifest.csv"))
    ),
    output: Path = typer.Option(Path(_env("OUTPUT_DIR", "downloads"))),
    cookies_path: Path = typer.Option(
        Path(_env("COOKIES_PATH", "data/cookies.json"))
    ),
    level: str = typer.Option(_env("LEVEL", "standard")),
    delay_min: float = typer.Option(float(_env("DELAY_MIN_SEC", "1.0"))),
    delay_max: float = typer.Option(float(_env("DELAY_MAX_SEC", "2.0"))),
):
    """补跑：把 failed.csv 当候选重跑（切换到 VIP cookie 后再跑即可）。"""
    if not failed_csv.exists():
        typer.echo(f"[✗] {failed_csv} 不存在，无失败项可补跑。")
        raise typer.Exit(code=1)
    tmp_cand = failed_csv.parent / "retry_candidates.csv"
    with failed_csv.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        typer.echo("[i] failed.csv 为空，无需补跑。")
        raise typer.Exit(code=0)
    with tmp_cand.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CANDIDATE_FIELDS)
        w.writeheader()
        for i, r in enumerate(rows, start=1):
            w.writerow({
                "idx": i, "track_id": r["track_id"],
                "name": r["name"], "artist": r["artist"],
                "album": "", "norm_key": "",
                "fee": 0, "source_offset": 0,
            })
    # 清空 failed.csv 让本轮重新记录
    failed_csv.unlink(missing_ok=True)

    cookies = load_cookies_dict(cookies_path)
    if not cookies:
        typer.echo("[✗] 未找到 cookie。请先运行 `music163 login`。")
        raise typer.Exit(code=2)
    session = _session(cookies)
    run_download_batch(
        candidates_csv=tmp_cand,
        manifest_csv=manifest_csv,
        failed_csv=failed_csv,
        output_dir=output,
        cookies=cookies,
        level=level,
        session=session,
        url_fn=vendor_url_v1,
        delay_min=delay_min,
        delay_max=delay_max,
    )
    tmp_cand.unlink(missing_ok=True)
    typer.echo("[✓] 补跑完成。")


if __name__ == "__main__":
    app()
