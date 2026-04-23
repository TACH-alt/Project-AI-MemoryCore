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
Date
Product Link
Product Name
Shop Name
Source Type
Status
Done
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
- The supplied Shopee product page does not expose downloadable approved seller media to this local scraper.
- For production use, add approved seller media/direct video links in `Product Link` whenever possible.

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

- Unit tests pass with `python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v` when run outside the sandbox.
- Manual runner dry-run passes with `powershell -ExecutionPolicy Bypass -File '.\AI - Shoppee Video v1.0\scripts\run_shopee_video_workflow.ps1' -DryRun`.
- FFmpeg is not currently on PATH, so edited `_new.mp4` rendering will require installing FFmpeg or adding it to PATH.

## Next Actions

- Copy or merge the worktree output back to the main workspace.
- Import/open the `.xlsx` masterlist in Google Sheets if a native Google Sheet is required.
- Install FFmpeg for video rendering.
- Add a real approved seller media link row and run a first live test.
