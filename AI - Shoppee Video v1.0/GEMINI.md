# AI - Shoppee Video v1.0 — Gemini CLI Context

> Read this file before touching any code in this project.

## Purpose

Local-first affiliate video automation. Reads a CSV masterlist of Shopee and TikTok product links, downloads seller media, renders 1080×1920 captioned MP4s with FFmpeg, and tracks everything in a CSV/XLSM masterlist.

## Tech Stack

- Python 3.14
- FFmpeg (WinGet install, auto-discovered by script)
- yt-dlp (pip install, also run as `python -m yt_dlp`)
- curl_cffi 0.14.0 (yt-dlp TikTok impersonation)
- Local HTTP frontend (no framework — stdlib only)
- unittest for tests

## Key Files

| File | Role |
|------|------|
| `scripts/process_shopee_video.py` | Core pipeline — download, render, analysis, masterlist write |
| `scripts/shoppee_video_frontend.py` | Local browser frontend on port 8765 |
| `scripts/start_shoppee_video_frontend.ps1` | PowerShell launcher; use `-Lan` for LAN binding |
| `masterlist/List of Link Shopee VIdeo.csv` | Live masterlist — automation source of truth |
| `masterlist/List of Link Shopee VIdeo.xlsm` | Excel mirror — synced from CSV on every write |
| `tests/test_process_shopee_video.py` | Unit + integration tests (42+ passing) |
| `tests/test_shoppee_video_frontend.py` | Frontend tests |
| `logs/run-log.csv` | Append-only run log |

## Masterlist Columns (13, in order)

`Record ID`, `Date`, `Product Link`, `Product Name`, `Shop Name`, `Source Type`, `Status`, `Done`, `Analysis Done`, `Notes`, `Last Processed At`, `Output Folder`, `Output File`

- Shopee rows: `ASV-0000001` prefix
- TikTok rows: `ATV-0000001` prefix
- IDs are auto-assigned and never change

## Output Folder Structure

```
output/
  Shopee/<Shop Name>/<Product Name>/
    product-info.md
    raw/
    edited/
    analysis/analysis-result.md
  TikTok/<Shop Name>/<Product Name>/
    (same layout)
```

## TikTok Post Types (v1.1 Hybrid)

TikTok posts are classified before downloading. **Do not assume `/video/` URLs are always video posts** — TikTok also uses that path for photo carousels.

| Type | Raw output | Edited output |
|------|-----------|---------------|
| `video` | `<id>.mp4` | `<id>_new.mp4` |
| `photo_mode` | `<id>.jpg` + `background.m4a` | `<id>_new.mp4` (slideshow) |

Download waterfall:
1. yt-dlp → real MP4 → done
2. yt-dlp returns images only → try `discover_tiktok_media_bundle()` (scrapes `itemStruct` JSON)
3. Bundle path → CDN-direct download of images + `music.playUrl` audio
4. Thumbnail fallback → `download_tiktok_photo_audio()` (yt-dlp bestaudio)
5. Nothing → `no_media_message()`

## Render Modes

`auto` (default), `light`, `vertical-blur` — passed via `--render-mode` CLI flag or frontend.

## CLI

```powershell
cd "C:\Users\Legend\Documents\Claude\Projects\MemoryCore"
# Process all pending rows
python "AI - Shoppee Video v1.0\scripts\process_shopee_video.py"
# Force rerun a specific record
python "AI - Shoppee Video v1.0\scripts\process_shopee_video.py" --force --download-and-analyze-record-id ATV-0000001
# Run tests
python -m unittest discover -s "AI - Shoppee Video v1.0\tests" -v
```

## Rules

- Never change the masterlist schema without updating `REQUIRED_COLUMNS`, `MasterRow`, `default_value_for_column`, and all 13 Excel column widths.
- Never bypass yt-dlp download restrictions or login-gated content.
- Always run tests before committing changes to the pipeline.
- Keep canonical raw filenames stable — reruns must overwrite, not accumulate duplicates.
- Preserve `background.*` audio through `cleanup_non_media_outputs`.

## Active Git Branches

- `main` — current working branch (all latest changes merged here)
- `codex/tiktok-v11-hybrid` — Codex worktree for v1.1 TikTok upgrade (merged to main via c0aab19)

## Not In Scope

- Private TikTok posts / login flows
- Shopee short links (`s.shopee.com.my`)
- Remotion editor (future lane, not implemented)
- CapCut project export (future)
