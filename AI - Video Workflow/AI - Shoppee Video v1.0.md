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

## TikTok Structured Fallback Upgrade - 2026-04-28

### What Changed

- Added a structured TikTok page-data fallback on top of the existing `yt-dlp` path.
- The workflow now parses TikTok's `__UNIVERSAL_DATA_FOR_REHYDRATION__` payload to classify a public post as:
  - direct video post
  - photo-mode post
- Added direct bundle recovery for TikTok page assets:
  - direct video URL when TikTok exposes one
  - best photo-mode image asset
  - background audio URL from TikTok page data
- Extended content-type handling so TikTok music URLs without file extensions still save as audio files such as `.m4a`.
- Tightened photo-mode reruns:
  - clean raw image artifacts before replacing them
  - clean stale edited mp4 outputs before rerender
  - keep canonical naming stable for reruns

### Root Cause Learned

- Some public TikTok links that look like "videos" are actually photo-mode posts.
- `yt-dlp -F` can show only an `audio` stream for those posts even when the web page still contains usable image and music assets.
- Our earlier fallback was too shallow:
  - it accepted low-fidelity JPG output from `yt-dlp`
  - it did not always promote better page-derived assets
  - a rename helper could delete a correctly named image and leave a dead path behind

### Live Verification

Smoke-tested and rerun successfully for:

```text
ATV-0000003
https://vt.tiktok.com/ZS9ST61G4/
```

Observed bundle classification:

```text
kind=photo_mode
video_urls=[]
image_urls=[best photo asset]
audio_url=<TikTok music CDN URL>
```

Final product folder state:

```text
AI - Shoppee Video v1.0/output/TikTok/Bargain Purchase/Massage Gaming Chair/
  product-info.md
  raw/
    7429146118933564690.jpg
    background.m4a
  edited/
    7429146118933564690_new.mp4
  analysis/
    analysis-result.md
```

Audio verification:

```text
ffprobe confirmed AAC audio stream in 7429146118933564690_new.mp4
```

### Code + Test Result

- Added structured TikTok bundle parsing and recovery in:
  - `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
- Added new regression tests covering:
  - TikTok page-data parsing
  - audio content-type mapping
  - bundle download file survival
  - structured fallback replacing low-fidelity TikTok JPG results

Verification command:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v
```

Result:

```text
42 tests passed
```

### Skill Update

Created a reusable local skill:

```text
plugins/legend-skills/skills/tiktok-media-extraction/SKILL.md
```

Purpose:

- classify TikTok public posts before assuming a download failure
- distinguish direct video versus photo-mode
- preserve stable rerun artifacts and audio verification discipline

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

## TikTok Audio Fix - 2026-04-27

- Picked up after Claude hit the limit while enhancing TikTok photo-mode audio.
- Verified the root cause:
  - `yt-dlp -F https://vt.tiktok.com/ZS9hjGD43/` exposed only one `audio` format
  - `download_tiktok_photo_audio()` was asking `yt-dlp` to extract/convert to `background.aac`
  - `yt-dlp` downloaded the track but failed post-processing because its internal `ffmpeg` / `ffprobe` lookup could not find those tools on PATH
  - the usable file left behind was `background.m4a`, which the workflow then ignored and cleaned up
- Fixed in code by:
  - introducing `AUDIO_EXTENSIONS`
  - preserving `background.<ext>` audio files during cleanup
  - downloading TikTok photo-mode audio as native `bestaudio` instead of forcing AAC extraction
  - teaching the renderer to detect any `background.*` supported audio file, not only `background.aac`
- Verification:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v
```

Result:

```text
33 tests passed
```

- Live retest:
  - reran `ATV-0000001` with `--download-and-analyze-record-id`
  - raw folder now includes:
    - `background.m4a`
  - newest edited output:
    - `7129084799339351323-3_new.mp4`
  - `ffprobe` confirmed the rendered file now has an AAC audio stream

## Running State - 2026-04-27

- Tightened rerun behavior for TikTok photo-mode rows:
  - thumbnail normalization now replaces the canonical image file instead of generating `-2` / `-3` artifacts
  - edited output rendering now replaces the canonical `_new.mp4` instead of creating duplicate suffixed renders
  - `yt-dlp` thumbnail and background-audio commands now use `--force-overwrites`
- Cleaned old duplicate TikTok artifacts from:
  - `output/TikTok/Bargain Purchase/Marble Dining Table/raw/`
  - `output/TikTok/Bargain Purchase/Marble Dining Table/edited/`
- Final steady-state after rerun:
  - raw:
    - `7129084799339351323.jpg`
    - `background.m4a`
  - edited:
    - `7129084799339351323_new.mp4`
- `product-info.md` media summary now reflects the cleaned state:
  - `Images downloaded = 1`
- Frontend is live again and reachable at:
  - `http://127.0.0.1:8765/`
  - `http://10.10.10.5:8765/`
- Fresh verification:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v
python '.\AI - Shoppee Video v1.0\scripts\process_shopee_video.py' --project-root '.\AI - Shoppee Video v1.0' --masterlist '.\AI - Shoppee Video v1.0\masterlist\List of Link Shopee VIdeo.csv' --download-and-analyze-record-id ATV-0000001
```

Results:

```text
35 tests passed
Download + Analyze complete for ATV-0000001.
```

## TikTok Retest - 2026-04-28

- Tested new TikTok link:

```text
https://www.tiktok.com/@bargainpurchasesofficial/video/7430739715701099783?is_from_webapp=1&sender_device=pc
```

- Added row:
  - `ATV-0000002`
  - Product Name: `Nordic Premium Chair`
  - Shop Name: `Bargain Purchase`
- Initial `Save + Download + Analyze` completed and created the right folder/artifacts, but the first readback exposed a rerun bug:
  - the row state eventually wrote correctly
  - output folder and analysis files existed
  - however the photo-mode rerun path skipped `background.m4a`, so the first retest rendered a silent MP4
- Root cause:
  - on rerun, the TikTok cover JPG was overwritten in place
  - `download_tiktok_thumbnail_with_ytdlp()` only looked for newly created files
  - because the existing JPG path was reused, the workflow treated the thumbnail step as empty and skipped the background-audio follow-up
- Fix:
  - added `tiktok_video_id_from_url()`
  - taught `download_tiktok_thumbnail_with_ytdlp()` to reuse an overwritten canonical image path when the thumbnail already exists
- Fresh verification:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v
python '.\AI - Shoppee Video v1.0\scripts\process_shopee_video.py' --project-root '.\AI - Shoppee Video v1.0' --masterlist '.\AI - Shoppee Video v1.0\masterlist\List of Link Shopee VIdeo.csv' --download-and-analyze-record-id ATV-0000002
```

Results:

```text
37 tests passed
Download + Analyze complete for ATV-0000002.
```

- Final verified state for `ATV-0000002`:
  - raw:
    - `7430739715701099783.jpg`
    - `background.m4a`
  - edited:
    - `7430739715701099783_new.mp4`
  - `ffprobe` confirmed an AAC audio stream exists in the final MP4

## TikTok v1.1 Implementation Result - 2026-04-28

- Implemented in isolated branch/worktree:
  - branch: `codex/tiktok-v11-hybrid`
  - worktree: `.worktrees/codex-tiktok-v11-hybrid`
- Added typed TikTok post classification:
  - accepts public `/video/`, `/photo/`, `vt.tiktok.com`, and `vm.tiktok.com`
  - returns `post_type` alongside the older `kind` field for compatibility
- Added bundle-first TikTok downloads:
  - direct video bundles now normalize to `<video_id>.mp4`
  - photo-mode bundles preserve ordered image assets and background audio
- Upgraded photo-mode rendering:
  - groups ordered images by TikTok post id
  - renders one canonical slideshow MP4
  - keeps background audio when available
  - writes clearer notes such as:
    - `Downloaded 2 media file(s); edited 1 slideshow video file(s) (photo-mode post with background audio)`
- Added frontend result-type visibility:
  - rows now derive `Video Post`, `Photo-mode Post`, or `Unknown TikTok Media`
  - result type is surfaced in the table from backend summary data

### Verification

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v
```

Result:

```text
51 tests passed
```

### Live Smoke Tests

```powershell
python '.\AI - Shoppee Video v1.0\scripts\process_shopee_video.py' --project-root '.\AI - Shoppee Video v1.0' --masterlist '.\AI - Shoppee Video v1.0\masterlist\List of Link Shopee VIdeo.csv' --download-and-analyze-record-id ATV-0000001
python '.\AI - Shoppee Video v1.0\scripts\process_shopee_video.py' --project-root '.\AI - Shoppee Video v1.0' --masterlist '.\AI - Shoppee Video v1.0\masterlist\List of Link Shopee VIdeo.csv' --download-and-analyze-record-id ATV-0000002
python '.\AI - Shoppee Video v1.0\scripts\process_shopee_video.py' --project-root '.\AI - Shoppee Video v1.0' --masterlist '.\AI - Shoppee Video v1.0\masterlist\List of Link Shopee VIdeo.csv' --download-and-analyze-record-id ATV-0000003
```

Result:

```text
All three rows completed successfully.
ATV-0000001, ATV-0000002, and ATV-0000003 now end as slideshow outputs with background audio and Analysis Done = TRUE.
```

### Known Minor Issue

- Python 3.14 still prints the harmless `ZipFile.__del__` cleanup traceback after successful TikTok runs.
- This did not block download, render, analysis, or masterlist updates.

## ATV-0000004 Verification - 2026-04-29

- Synced the live `main` app to the verified TikTok v1.1 code from `codex/tiktok-v11-hybrid`:
  - `scripts/process_shopee_video.py`
  - `scripts/shoppee_video_frontend.py`
  - `tests/test_process_shopee_video.py`
  - `tests/test_shoppee_video_frontend.py`
- Fresh verification after sync:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v
python -m yt_dlp -F "https://www.tiktok.com/@bargainpurchasesofficial/video/7429642666880568594"
python '.\AI - Shoppee Video v1.0\scripts\process_shopee_video.py' --project-root '.\AI - Shoppee Video v1.0' --masterlist '.\AI - Shoppee Video v1.0\masterlist\List of Link Shopee VIdeo.csv' --download-and-analyze-record-id ATV-0000004
```

Results:

```text
51 tests passed
yt-dlp listed only one `audio` format for ATV-0000004
download + analyze completed successfully
```

- Page-data inspection for `ATV-0000004` confirmed:
  - `video.downloadAddr = ""`
  - `video.playAddr = ""`
  - no `imagePost` array in the hydration payload
  - one cover image URL plus background music URL
- Conclusion:
  - `ATV-0000004` is currently exposed to the web workflow as a photo-mode / cover-image post, not a native MP4 video stream
  - the workflow is now behaving honestly by recording:
    - `Downloaded 2 media file(s); edited 1 slideshow video file(s) (photo-mode post with background audio)`
