# AI - Shoppee Video Future Improvements

**Project**: AI - Shoppee Video v1.0  
**Date**: 2026-04-23  
**Status**: Planning phase  
**Decision Type**: Future improvements roadmap

## Why This Note Exists

Legend asked for a future-improvement outline after testing the frontend workflow and seeing another short-link failure plus weak edited-video quality.

This note summarizes what can be improved, what should be avoided, and how the next phase should be implemented.

## New Standing Decisions

- Ignore short `s.shopee.com.my` links for future workflow work.
- Use full Shopee product URLs or direct approved media links only.
- Keep the automation local-first.
- Shift the default video treatment toward lighter editing.

## Latest Findings

### Short Link Failure

Latest frontend test result:

```text
Saved row 4; workflow completed. Output folder opened.
Row 4: Failed - Shopee page did not expose downloadable product media; use an approved seller media/direct file link
```

Interpretation:

- The failure came from a short redirect link, not a full Shopee product URL.
- Redirect links are unreliable for the current scraper path.

### Raw vs Edited Video Quality

Measured comparison on the Electrova sample:

```text
raw:    720x720, 25 fps, AAC stereo audio present
edited: 1080x1920, 30 fps, no audio stream present
```

Visual comparison:

- Raw video is already usable product footage.
- Current edit adds a heavy vertical composition and blur treatment.
- Output is larger but not truly sharper.
- The current render removes the original audio, which is a quality regression.

## Future Improvement Areas

## 1. Private-Network Frontend Access

### Status

- Completed on 2026-04-24.

### What Can Be Done

- Bind the local frontend to `0.0.0.0` instead of only `127.0.0.1`.
- Show the home-network URL in the console, for example `http://192.168.x.x:8765/`.
- Keep access limited to devices on the same home Wi-Fi or LAN.

### What Should Not Be Assumed

- This does not make the app safely public on the internet.
- Windows Firewall may still need a local-network allow rule.
- Port forwarding should not be enabled by default.

### How It Should Be Done

- Add a `-Lan` switch in `start_shoppee_video_frontend.ps1`.
- Add a matching `--host 0.0.0.0` option in `shoppee_video_frontend.py`.
- Print both localhost and LAN URLs.

### What Was Implemented

- `shoppee_video_frontend.py` now prints both localhost and LAN URLs when bound to `0.0.0.0`.
- `start_shoppee_video_frontend.ps1` now accepts `-Lan`.
- Manual verification showed:

```text
http://127.0.0.1:8766/
http://10.10.10.5:8766/
```

## 2. Better Video Editing Strategy

### What Can Be Done

- Preserve source audio in edited video outputs.
- Add a lighter default mode for already-good raw videos.
- Keep stronger vertical blur composition only as an optional mode.
- Decide edit mode based on source shape and quality instead of forcing one style.

### What Should Not Be Assumed

- Upscaling alone cannot create real detail from a low-bitrate square source.
- Bigger resolution does not automatically mean better quality.
- Not every product video needs a full remake.

### How It Should Be Done

- Add a render-mode selector:
  - `light` for usable raw product videos
  - `vertical-blur` for cases that really need a 9:16 canvas
  - `image-video` for still-image sources
- Preserve audio with `-map 0:a?` and AAC output.
- Make caption size smaller and less intrusive.

## 3. CapCut Or Editor Handoff

### What Can Be Done

- Export clean handoff files for CapCut or another editor.
- Save raw file, edited file, caption text, and suggested next actions in a `handoff` folder.
- Let Legend continue trimming, caption styling, music, voiceover, and hooks manually in a real editor.

### What Cannot Be Guaranteed Right Now

- A proper direct CapCut project API integration is not available in this workflow.
- We should not promise one-click import into a native CapCut project unless a documented import path is verified.

### How It Should Be Done

- Create `output/<product-folder>/handoff/project.json`
- Create `output/<product-folder>/handoff/README.txt`
- Include:
  - raw file path
  - edited file path
  - caption text
  - recommended next edits

## Recommended Sequence

1. Fix the video pipeline first: preserve audio and make editing lighter.
2. Add editor handoff so Legend can finish stronger videos in CapCut.

## Main Implementation Plan

Detailed implementation plan saved here:

```text
docs/superpowers/plans/2026-04-23-ai-shoppee-video-v1-future-improvements.md
```

## Obsidian Sync Requirement

This note should be mirrored into the Legendary vault topic folder:

```text
C:\Users\Legend\Desktop\Obsidian\Legendary\05-Projects\AI - Video Workflow\
```
