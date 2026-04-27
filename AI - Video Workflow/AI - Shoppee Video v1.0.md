# AI - Shoppee Video v1.0

**Project name:** AI - Shoppee Video v1.0  
**Date opened:** 2026-04-23  
**Status:** Local v1.0 scaffold and runner implemented  
**Owner:** Legend

## Purpose

Build a local-first automation system for Shopee Video affiliate work. Legend manually adds product rows from phone, Google Drive, or desktop. The automation reads the masterlist, downloads approved seller media or best-effort Shopee page media, organizes files by product and shop, creates 1080p vertical captioned videos, and saves edited files with `_new` appended to the filename.

## Current Decisions

- Use approved seller media links as the preferred source.
- Support Shopee product page links as best-effort fallback only.
- Use a Google Drive-synced project folder as the local operating area.
- Create a polished Excel masterlist template and a CSV masterlist that automation can read reliably.
- Use FFmpeg for 1080p vertical rendering when installed.
- Do not bypass captcha, login, DRM, or platform protections.
- Keep this Obsidian note updated whenever project `.md` files are created or changed.

## Masterlist

Workbook and CSV name:

```text
List of Link Shopee VIdeo
```

Columns:

```text
Record ID
Date
Product Link
Product Name
Shop Name
Source Type
Status
Done
Analysis Done
Notes
Last Processed At
Output Folder
Output File
```

## Key Files

- `docs/superpowers/specs/2026-04-23-ai-shoppee-video-v1-design.md`
- `docs/superpowers/plans/2026-04-23-ai-shoppee-video-v1-implementation.md`
- `AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.csv`
- `AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.xlsm`
- `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
- `AI - Shoppee Video v1.0/scripts/run_shopee_video_workflow.ps1`

## Markdown Change Log

### 2026-04-23

- Created design spec: `docs/superpowers/specs/2026-04-23-ai-shoppee-video-v1-design.md`.
- Created implementation plan: `docs/superpowers/plans/2026-04-23-ai-shoppee-video-v1-implementation.md`.
- Created this Obsidian project note: `AI - Video Workflow/AI - Shoppee Video v1.0.md`.
- Created local project scaffold under `AI - Shoppee Video v1.0/`.
- Created masterlist files: `List of Link Shopee VIdeo.csv` and `List of Link Shopee VIdeo.xlsx`.
- Created processor script: `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`.
- Created manual runner: `AI - Shoppee Video v1.0/scripts/run_shopee_video_workflow.ps1`.
- Created unit tests: `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`.
- Updated session memory: `main/current-session.md`.
- Updated long-term interaction history: `main/main-memory.md`.
- Updated daily diary: `daily-diary/current/2026-04-23.md`.
- Updated implementation plan progress and verification checklist: `docs/superpowers/plans/2026-04-23-ai-shoppee-video-v1-implementation.md`.
- Saved new test-session memory request: `main/current-session.md`.
- Started live-test diary entry: `daily-diary/current/2026-04-23.md`.

## Live Test Session - 2026-04-23

### Test Input

```text
https://shopee.com.my/product/32632559/41452031782
```

### Current Workspace Observation

- Google Drive or Excel appears to have renamed `List of Link Shopee VIdeo.xlsx` to `List of Link Shopee VIdeo.xlsm`.
- The automation source remains `AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.csv`.
- The `.xlsm` file should be preserved unless Legend explicitly asks to convert it back.
- Added `Done` as a checkbox-style tracking column. The automation writes `TRUE` only when a row reaches `Downloaded` or `Edited`; failed and pending rows stay `FALSE`.
- The CSV remains the automation source, and the `.xlsm` masterlist is synced from the CSV whenever the workflow/frontend writes the CSV.

### Upgrade Results

- Installed FFmpeg Essentials Build 8.1 through WinGet.
- Installed/updated yt-dlp to version `2026.3.17` through Python pip.
- Updated the workflow script so it can find FFmpeg from the WinGet package folder even when the shell alias is not refreshed.
- Updated the workflow script so it can find yt-dlp from the Python user Scripts folder or fall back to `python -m yt_dlp`.
- Registered Windows Task Scheduler task `AI - Shoppee Video v1.0 Manual` for manual runs.
- Test-triggered the scheduled task successfully with `LastTaskResult = 0`.

### Live Test Result

Result for the Shopee product page:

```text
Failed - No downloadable media found
```

Root cause:

- `yt-dlp` reports the Shopee URL as unsupported.
- Shopee product page/API checks returned blocked or non-usable responses.
- The basic page fallback found Shopee app icon/splash assets, not product media.

Fixes made during testing:

- Changed the renderer from `-vf` to `-filter_complex` for the two-layer 1080p canvas.
- Filtered out favicon, icon, splash, logo, sprite, and placeholder assets so the workflow does not create misleading videos from Shopee page chrome.
- Cleared stale `Output File` values when a forced rerun fails after a previous successful/partial run.

Current conclusion:

- The workflow is working for control flow, status updates, dependency discovery, logging, and safe failure handling.
- Initial desktop Shopee scraping failed because Shopee served an app shell with no product media.
- Approved seller media/direct video links remain the most reliable input.
- Shopee product-page extraction is now supported when the mobile SEO HTML exposes product media.

## Shopee Product Page Extractor Fix - 2026-04-23

### Root Cause

- `yt-dlp` still reports Shopee product URLs as unsupported.
- Shopee API endpoints still return anti-crawler-style `403` responses.
- Desktop/browser-shell HTML for links with `extraParams` did not include product media.
- A mobile browser-style request to the clean product URL returned SEO/product HTML containing seller media URLs.

### Code Changes

- Added Shopee product URL recognition for both:
  - `https://shopee.com.my/product/<shopid>/<itemid>`
  - `https://shopee.com.my/<slug>-i.<shopid>.<itemid>`
- Added query stripping for Shopee product links before page scraping.
- Added mobile browser request headers for Shopee page discovery.
- Added Shopee CDN extraction for:
  - seller video URLs from `*.vod.susercontent.com`
  - seller image URLs from `down-my.img.susercontent.com/file/...`
- Filtered out Shopee page chrome assets from the mobile product page.
- Limited workflow download selection to one best video when product videos are available.

### Markdown Files Updated For This Fix

- `AI - Video Workflow/AI - Shoppee Video v1.0.md`
- `docs/superpowers/plans/2026-04-23-ai-shoppee-video-v1-implementation.md`
- `daily-diary/current/2026-04-23.md`
- `main/current-session.md`
- `main/main-memory.md`

### Legendary Obsidian Vault Mirror

Created/updated project notes in:

```text
C:\Users\Legend\Desktop\Obsidian\Legendary\05-Projects\AI - Video Workflow\
```

Vault files updated:

- `AI - Video Workflow Index.md`
- `AI - Shoppee Video v1.0.md`
- `CapCut Affiliate Video Workflow Plan.md`
- `Rekalab Affiliate Video Workflow Analysis.md`
- `Project Documentation Rules.md`
- `C:\Users\Legend\Desktop\Obsidian\Legendary\Dashboard.md`
- `C:\Users\Legend\Desktop\Obsidian\Legendary\03-Daily-Notes\2026-04-23.md`
- `C:\Users\Legend\Desktop\Obsidian\Legendary\01-Sessions\2026-04-23-001.md`

### Live Test Result

Test link:

```text
https://shopee.com.my/Electrova-Cordless-UV-Mite-Remover-Vacuum-Cleaner-VacLife-Series-i.297985880.25153849822?extraParams=%7B%22display_model_id%22%3A250102961680%7D
```

Result:

```text
Downloaded 1 media file(s); edited 1 video file(s)
```

Output:

```text
AI - Shoppee Video v1.0/output/Electrova Cordless UV Mite-Electrova/edited/my-11110105-6ke18-lqbrwqqiae664d.16003251736514494_new.mp4
```

Verified video:

```text
codec=h264
resolution=1080x1920
duration=59.633008s
size=7,225,434 bytes
```

Masterlist status:

```text
Status=Edited
Done=TRUE
```

## Local Frontend And Manual Shortcuts

### Frontend

Created a local browser frontend:

```text
AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py
```

Start script:

```text
AI - Shoppee Video v1.0/scripts/start_shoppee_video_frontend.ps1
```

Frontend behavior:

- Shows input fields matching the masterlist.
- Provides `Save` to update the CSV masterlist and sync the `.xlsm`.
- Provides `Download` to save the row, run the workflow, and open the output folder.
- Provides `Open Output Folder` for manual access to completed/raw video folders.

### Desktop Shortcuts

Created Desktop shortcuts:

```text
C:\Users\Legend\Desktop\AI Shoppee Video - Run Workflow.lnk
C:\Users\Legend\Desktop\AI Shoppee Video - Frontend.lnk
```

`AI Shoppee Video - Run Workflow.lnk` runs the automation and opens:

```text
AI - Shoppee Video v1.0/output/
```

`AI Shoppee Video - Frontend.lnk` starts the local browser frontend.

## Verification

- Unit tests pass with `python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v`.
- Manual runner dry-run passes with `powershell -ExecutionPolicy Bypass -File '.\AI - Shoppee Video v1.0\scripts\run_shopee_video_workflow.ps1' -DryRun`.
- FFmpeg is installed through WinGet and is discovered by the workflow.
- Live Electrova Shopee product-page test produced a captioned `_new.mp4` at 1080x1920.

## LAN Frontend Upgrade - 2026-04-24

Implemented:

- Added LAN-friendly frontend URL generation in `shoppee_video_frontend.py`.
- Added LAN IP detection for private-network use.
- Added `-Lan` switch to `start_shoppee_video_frontend.ps1`.
- Kept browser-open behavior pointed at localhost while still binding the server to all interfaces.

How to run:

```powershell
powershell -ExecutionPolicy Bypass -File '.\AI - Shoppee Video v1.0\scripts\start_shoppee_video_frontend.ps1' -Lan
```

Expected access:

```text
http://127.0.0.1:8765/
http://<your-lan-ip>:8765/
```

Manual verification result:

```text
AI - Shoppee Video v1.0 frontend:
  http://127.0.0.1:8766/
  http://10.10.10.5:8766/
```

Test coverage added:

- frontend default host remains `127.0.0.1`
- LAN binding builds both localhost and LAN URLs

Current note:

- This is private-network hosting only, not public internet publishing.
- Windows Firewall may still need local-network allow access on first run.

## Latest User Test - 2026-04-23

Frontend test result:

```text
Saved row 4; workflow completed. Output folder opened.
Row 4: Failed - Shopee page did not expose downloadable product media; use an approved seller media/direct file link
```

Interpretation:

- The tested row used a short `s.shopee.com.my` link.
- Short redirect links are now treated as unreliable input and should be ignored for future workflow work.
- Use full Shopee product URLs or direct approved media links only.

## Raw vs Edited Video Analysis - 2026-04-23

Analyzed files:

```text
raw:    AI - Shoppee Video v1.0/output/Electrova - Cordless UV Mite-Electrova/raw/my-11110105-6ke18-lqbrwqqiae664d.16003251736514494.mp4
edited: AI - Shoppee Video v1.0/output/Electrova - Cordless UV Mite-Electrova/edited/my-11110105-6ke18-lqbrwqqiae664d.16003251736514494_new.mp4
```

Measured properties:

```text
raw video:    720x720, 25 fps, video bitrate about 258 kb/s, audio AAC stereo present
edited video: 1080x1920, 30 fps, video bitrate about 966 kb/s, no audio stream present
```

Practical finding:

- The current edit path forces square source video into a blurred 9:16 canvas.
- The output is larger and technically higher bitrate, but not meaningfully sharper because the source itself is low-resolution square video.
- The current render drops the original audio completely.
- The caption treatment is too heavy for clips that are already visually usable.

Conclusion:

- Future editing should be lighter by default.
- If the downloaded raw video is already acceptable, preserve the source audio, avoid aggressive blur framing, and use a minimal caption overlay.
- Stronger editing should be optional, not the only render path.

## Next Actions

- Import/open the `.xlsx` masterlist in Google Sheets if a native Google Sheet is required.
- Continue using full Shopee product URLs or approved seller media links.
- Ignore short `s.shopee.com.my` links for future workflow work.
- Task 1 is complete: LAN/private-network frontend access.
- Next task candidate: lighter renderer with audio preservation.

## Planning Expansion - 2026-04-26

Project planning was extended with a second workflow lane:

```text
AI - Video Workflow/Shopee Link and Media Analysis Workflow.md
```

This new planning direction adds:

- shared-link analysis
- downloaded-media analysis
- multi-angle hook generation
- clip-order and timestamp suggestions
- CapCut/editor handoff artifacts

Current recommended first slice:

```text
Add an Analyze workflow that writes product-summary.md, media-analysis.md, and hook-pack.md into each product folder after successful download.
```

Current note:

- This save point records planning only.
- No new implementation work has been started in this documentation update.

## Analysis And TikTok Upgrade - 2026-04-27

Implemented in isolated worktree branch:

```text
codex/analysis-tiktok
```

What landed:

- Added stable `Record ID` handling with:
  - `ASV-0000001` for Shopee rows
  - `ATV-0000001` for TikTok rows
- Added `Analysis Done` tracking to the masterlist CSV and workbook sync path.
- Changed output folders to:

```text
output/
  Shopee|TikTok/
    <Shop Name>/
      <Product Name>/
```

- Added `product-info.md` creation/update on save.
- Added `analysis/analysis-result.md` creation on successful analysis.
- Added direct CLI and frontend support for:
  - `Analyze`
  - `Save + Download + Analyze`
- Updated the frontend to work from saved rows by `Record ID`, with row actions for:
  - `Load`
  - `Analyze`
  - `Open`
- Added public TikTok single-video URL support.
- Added clear rejection text for unsupported TikTok links:

```text
TikTok link must be a public single video URL
```

Verification:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v
```

Result:

```text
46 tests passed
```

## Monitoring Claude Updates - 2026-04-27

- After the Codex implementation checkpoint and Claude cherry-pick session, Codex delegated explorer agent `Carson` to read Claude's ongoing main-workspace updates without modifying files.
- The purpose of this monitoring step is to keep project memory aligned while preserving both:
  - Claude's active main-workspace progress
  - the isolated worktree fallback/checkpoint
- MemoryCore and Obsidian were refreshed again at this point so the current save includes both tracks.

### Carson Findings

- Claude's main-workspace code upgrades are substantial and coherent in:
  - `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
  - `AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py`
- Recent output folders and run logs confirm real recent workflow activity.
- The main workspace still shows partially old live artifacts:
  - CSV header still on the older live schema
  - output folders still flat `output/Product-Shop/`
  - no visible `product-info.md` / `analysis-result.md` generated yet in the new product folders
- Carson was closed after this snapshot was saved.

## Testing Monitor Deployment - 2026-04-27

- Codex deployed new read-only monitor agent `Lagrange` to watch Claude's ongoing testing in the main workspace.
- Monitoring focus:
  - smoke-test completion
  - live schema migration in the masterlist
  - transition from flat output folders to the new grouped model
  - creation of `product-info.md` and `analysis-result.md`
- Thread heartbeat automation also created so this thread keeps checking every 30 minutes without manual follow-up.

## TikTok Downloader Upgrade - 2026-04-27

- Investigated the failing TikTok row against SnapTik behavior and local `yt-dlp` output.
- Confirmed the root cause in the live environment:
  - `yt-dlp` could only see an `audio` format for the TikTok URL.
  - the machine was missing a supported impersonation backend for `yt-dlp`
  - the tested TikTok post is a photo-mode post, not a normal video post
- Installed compatible `curl_cffi` support for `yt-dlp`:
  - `curl_cffi==0.14.0`
- Upgraded `process_shopee_video.py` to:
  - canonicalize TikTok short links through TikTok `oEmbed`
  - force merged video output attempts first for real TikTok videos
  - clean up audio-only leftovers like `.m4a`
  - fall back to TikTok thumbnail capture when a post exposes only audio/cover media
  - normalize `.image` thumbnail artifacts into real image extensions like `.jpg`
- Result for live row `ATV-0000001`:
  - completed successfully through `Download + Analyze`
  - wrote `product-info.md`
  - wrote `analysis/analysis-result.md`
  - created edited output:
    - `output/TikTok/Bargain Purchase/Marble Dining Table/edited/7129084799339351323_new.mp4`
- Masterlist state after retest:
  - `Status = Edited`
  - `Done = TRUE`
  - `Analysis Done = TRUE`
- Verification after code changes:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v
```

Result:

```text
30 tests passed
```

- One small runtime warning still appeared after success:
  - a `zipfile.ZipFile.__del__` cleanup warning on Python 3.14
  - workflow result still completed successfully
