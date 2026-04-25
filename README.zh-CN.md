# netease-square-dance-downloader（网易云广场舞批量下载器）

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-45%20passed-brightgreen.svg)](#测试)

> [English](README.md) | **简体中文**

批量下载网易云广场舞歌曲到 U 盘的命令行工具，专为外置音响场景设计——一次性凑齐
500 首去重后的广场舞 MP3。

基于 [Suxiaoqinx/Netease_url](https://github.com/Suxiaoqinx/Netease_url) 的
只读能力，叠加 Playwright 扫码登录、绕过 vendor 缺失 `offset` 参数的翻页搜索、
基于标题规范化的智能去重、可断点续传的批量下载。

## 功能特性

- **扫码登录**：Playwright 弹出 Chromium，手机扫码即可，cookie 自动持久化为
  JSON 文件，无需手工从浏览器 DevTools 复制
- **智能去重**：`最炫民族风`、`最炫民族风 (DJ版)`、`最炫民族风【广场舞】`、
  `最炫民族风 Remix` 全部归一为同一首，先到先得
- **两阶段执行**：`search` 先产出 `candidates.csv` 供你审阅，确认后再 `download`
- **断点续传**：`manifest.csv` 记录已下载条目，重跑自动跳过
- **U 盘友好**：扁平输出 `<歌名> - <歌手>.mp3`，自动剥离 FAT32/exFAT 非法字符
- **可调速率限制**：1~2 秒随机抖动，tenacity 指数退避重试，支持 Ctrl+C 优雅退出
- **音质可选**：默认 128 kbps `standard`；有 VIP 可切到 `exhigh`（320 kbps）
  或 `lossless`（FLAC）

## 快速开始

```bash
# 前置条件：Python 3.11+、git
git clone https://github.com/Zhanglala103838/netease-square-dance-downloader.git
cd netease-square-dance-downloader

python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/playwright install chromium

# 拉取并固定 Netease_url 上游库
scripts/fetch_vendor.sh

cp .env.example .env  # 按需调整 OUTPUT_DIR / TARGET_COUNT / QUERY
```

## 使用方式

```bash
# 1. 扫码登录（浏览器弹出，用手机网易云 App 扫码）
.venv/bin/python -m src.cli login

# 2. Stage 1：翻页搜索 + 去重 → data/candidates.csv
.venv/bin/python -m src.cli search --target 500

# 3. Stage 2：下载（U 盘场景用 --output 指向挂载点）
.venv/bin/python -m src.cli download --output /Volumes/UDISK/广场舞

# 4. 补跑失败项（例如换到 VIP cookie 之后）
.venv/bin/python -m src.cli retry --output /Volumes/UDISK/广场舞
```

### 音质等级

默认 `standard`（128 kbps MP3），通过 `--level` 切换：

| Level      | 格式            | 账号要求       |
|------------|-----------------|---------------|
| `standard` | 128 kbps MP3    | 免费          |
| `exhigh`   | 320 kbps MP3    | 免费 / VIP    |
| `lossless` | FLAC 无损       | VIP（黑胶）   |
| `hires`    | 24-bit Hi-Res   | SVIP          |

## 产物

| 路径                            | 说明                                            |
|---------------------------------|------------------------------------------------|
| `data/cookies.json`             | Playwright 持久化的网易云会话 cookie            |
| `data/candidates.csv`           | Stage 1 去重结果（一行一条）                    |
| `data/manifest.csv`             | 已成功下载清单（断点续传依据）                  |
| `data/failed.csv`               | 失败清单，含 `reason` 字段                      |
| `downloads/`（或 `--output`）   | 扁平 MP3 输出目录                               |

## 架构

```
login (Playwright) ──→ cookies.json
                           │
                           ▼
search（直调 /api/search/get/web，支持 offset）
   │
   └─→ dedupe（title 规范化，先到先得）──→ candidates.csv
                                                 │
                                                 ▼
runner ── 逐首 ──→ downloader（vendor url_v1 + 重试）
   │                       │
   ├─→ manifest.csv（成功） │
   └─→ failed.csv（失败）   ▼
                        downloads/*.mp3
```

vendor 库的 `search_music(keywords, cookies, limit)` **不暴露 `offset`**，
所以本项目翻页搜索绕过 vendor，直接打网易云的旧版 `/api/search/get/web` 端点
（无需 weapi 加密）；而 `/song/url` 解析仍走 vendor 的 `url_v1`，复用其
weapi 加密实现。

## 测试

```bash
.venv/bin/pytest -v
```

45 个单元测试覆盖去重、文件名清洗、manifest 读写、翻页搜索、下载重试、
batch 编排、端到端冒烟。全部使用 mock，**不真实访问网易云**。

## 配置

`.env`（从 `.env.example` 复制）：

| Key                | 默认值                   | 说明                              |
|--------------------|--------------------------|----------------------------------|
| `COOKIES_PATH`     | `data/cookies.json`      |                                  |
| `CANDIDATES_PATH`  | `data/candidates.csv`    |                                  |
| `MANIFEST_PATH`    | `data/manifest.csv`      |                                  |
| `FAILED_PATH`      | `data/failed.csv`        |                                  |
| `OUTPUT_DIR`       | `downloads`              | 改为 U 盘挂载点即可               |
| `TARGET_COUNT`     | `500`                    |                                  |
| `MAX_PAGES`        | `100`                    | 翻页硬上限，避免无限循环          |
| `DELAY_MIN_SEC`    | `1.0`                    |                                  |
| `DELAY_MAX_SEC`    | `2.0`                    |                                  |
| `RETRY_MAX`        | `3`                      |                                  |
| `LEVEL`            | `standard`               | 见上方音质表                     |
| `QUERY`            | `广场舞`                 | 默认搜索关键词                   |

## 注意事项

- **VIP 专享曲目**在普通账号下 `/song/url` 返回空 url，会落到 `failed.csv`，
  `reason=url_empty`
- **风控**：连续高频请求会触发 IP 短时限流；默认 1~2 秒抖动跑 500 首是安全的
- **Cookie 过期**：Stage 2 返回 401 即重新跑 `login` 扫码
- **Ctrl+C**：优雅退出——完成当前曲、刷新 manifest、清理 `.part` 临时文件，
  退出码 130；下次直接重跑即可续传

## 许可

MIT，见 [LICENSE](LICENSE)。

## 致谢

- [Suxiaoqinx/Netease_url](https://github.com/Suxiaoqinx/Netease_url) — 本项目
  作为库引入它的 weapi 加密 / cookie 管理能力
- 社区维护的 [网易云音乐 API 文档](https://neteasecloudmusicapi.vercel.app/) —
  端点参考
