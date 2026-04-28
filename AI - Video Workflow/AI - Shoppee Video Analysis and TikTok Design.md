# AI - Shoppee Video Analysis and TikTok Design

**Project**: AI - Shoppee Video v1.0  
**Date**: 2026-04-27  
**Status**: Implemented in isolated worktree branch `codex/analysis-tiktok`  

## Summary

This note tracks the approved design for the next upgrade phase:

- add stable `Record ID` values to the masterlist
- add `Analysis Done` tracking
- add manual `Analyze` support for existing downloaded folders
- add direct `Save + Download + Analyze`
- add `product-info.md` and `analysis-result.md` output files
- add public single TikTok video URL support
- change output folder structure to:

```text
output/
  Shopee|TikTok/
    <Shop Name>/
      <Product Name>/
```

## Spec File

Main spec:

```text
docs/superpowers/specs/2026-04-27-ai-shoppee-video-analysis-and-tiktok-design.md
```

Implementation plan:

```text
docs/superpowers/plans/2026-04-27-ai-shoppee-video-analysis-and-tiktok-implementation.md
```

## Key Approved Rules

- `Record ID` is the first masterlist column.
- Shopee IDs use `ASV-0000001` format.
- TikTok IDs use `ATV-0000001` format.
- `Analysis Done` is a checkbox-style tracker.
- Shop folders must match case-insensitively and reuse first-saved casing.
- `Analyze` works on existing downloaded media.
- `Save + Download + Analyze` runs analysis immediately after successful download.
- `product-info.md` must be refreshed from saved row data and media counts.
- `analysis-result.md` is the analysis completion artifact.

## Implementation Result - 2026-04-27

- Added `Record ID` as the first masterlist column with platform-specific prefixes:
  - Shopee: `ASV-0000001`
  - TikTok: `ATV-0000001`
- Added `Analysis Done` tracking to the CSV and workbook sync path.
- Changed product output grouping to:

```text
output/
  Shopee|TikTok/
    <Shop Name>/
      <Product Name>/
```

- Added `product-info.md` creation and refresh on save.
- Added `analysis-result.md` creation for successful analysis runs.
- Added CLI support for:
  - `--analyze-record-id`
  - `--download-and-analyze-record-id`
- Updated the frontend so rows can be targeted by `Record ID`, including:
  - visible `Record ID` field
  - row `Load`
  - row `Analyze`
  - row `Open`
  - selected-row `Analyze`
  - `Save + Download + Analyze`
- Added public TikTok single-video URL support in the existing downloader path.
- Added a clear failure message for unsupported TikTok shapes:
  - `TikTok link must be a public single video URL`

## Verification

Verified in the isolated worktree:

```text
C:\Users\Legend\Documents\Claude\Projects\MemoryCore\.worktrees\codex-analysis-tiktok
```

Command:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v
```

Result:

```text
46 tests passed
```

## Current State

- Design approved by user.
- Spec written.
- Implementation plan written.
- Core implementation completed in the isolated worktree branch.
- Main workspace remains untouched for Claude's in-progress changes.

## Monitoring Note - 2026-04-27

- Claude's ongoing main-workspace updates are being tracked separately from the isolated worktree implementation checkpoint.
- Codex delegated explorer agent `Carson` to read and summarize Claude's current main-workspace changes without editing them.
- This keeps the project memory aligned across:
  - isolated worktree implementation state
  - newer main-branch cherry-pick state
  - Obsidian mirror notes

## Carson Snapshot - 2026-04-27

- Carson completed the read and was closed after reporting.
- Current main-workspace nuance:
  - Claude's script/frontend upgrades are real and substantial.
  - Recent output folders and logs show actual runs.
  - The live workspace is still only partially migrated to the new model:
    - masterlist header still reflects the older live schema
    - output folders still appear in older flat `output/Product-Shop/` form
    - `product-info.md` and `analysis-result.md` do not yet appear in those new main-workspace product folders
- This means the code path is ahead of the currently exercised artifact trail in the main workspace.

## Testing Monitor - 2026-04-27

- Deployed read-only monitor agent `Lagrange` to watch the main-workspace testing/smoke-test progress.
- Agent scope:
  - new schema exercise in live masterlist files
  - output folder migration evidence
  - generated `product-info.md`
  - generated `analysis-result.md`
  - any meaningful smoke-test completion signals
- Supporting thread heartbeat automation created:
  - `Monitor AI Video Testing`
  - active every 30 minutes

## TikTok Research Outcome - 2026-04-27

- SnapTik-style research confirmed that successful TikTok capture is typically handled server-side, with URL normalization and download relays.
- For this local workflow, the practical fix path was:
  - resolve TikTok short links to canonical long-form URLs
  - improve `yt-dlp` video extraction attempts
  - add a local fallback for TikTok photo-mode posts
- The tested live TikTok row turned out to be a photo-mode post:
  - webpage exposed empty `playAddr` / `downloadAddr`
  - `yt-dlp` only surfaced an audio track plus thumbnails
- The workflow was upgraded to treat this as usable media instead of a dead-end failure:
  - thumbnail capture is downloaded
  - `.image` artifacts are normalized to image extensions
  - the image can still flow into the existing caption/render/analyze pipeline
- This means TikTok support is now broader than “mp4 only”:
  - real video posts still try direct video download
  - photo-mode posts can still produce a usable edited output from image media
## TikTok Structured Fallback Result - 2026-04-28

- Upgraded the main-workspace TikTok path beyond plain `yt-dlp` fallback.
- Added structured parsing of TikTok page hydration data from `__UNIVERSAL_DATA_FOR_REHYDRATION__`.
- New extraction rule:
  - if `yt-dlp` returns a real video, keep it
  - if TikTok returns image-only media, promote the structured page bundle before accepting the low-fidelity thumbnail path
- Structured bundle support now covers:
  - direct video URLs when `downloadAddr` or `playAddr` is exposed
  - one best photo-mode image asset when direct video is absent
  - direct music/audio URL recovery
- Fixed a real regression during this upgrade:
  - a rename helper could delete an already-correct TikTok image output and leave only a dead path in memory
- Tightened rerun hygiene too:
  - clear stale raw image assets before redownloading photo-mode bundles
  - clear stale edited outputs before rerendering photo-mode rows

### Verified Main-Workspace Result

Revalidated live row:

```text
ATV-0000003
```

Final clean output:

```text
output/TikTok/Bargain Purchase/Massage Gaming Chair/
  raw/7429146118933564690.jpg
  raw/background.m4a
  edited/7429146118933564690_new.mp4
  analysis/analysis-result.md
```

Verification:

```text
42 tests passed
```

## TikTok v1.1 Hybrid Design - 2026-04-28

- Approved the next TikTok upgrade as a hybrid v1.1:
  - stronger public-post extraction
  - explicit `video` vs `photo_mode` vs `unknown` classification
  - better multi-image photo-mode output
  - clearer frontend feedback
- Decided that Remotion should stay out of this phase and be handled as a separate future website/editor with its own button later.

### New Spec

```text
docs/superpowers/specs/2026-04-28-ai-shoppee-video-tiktok-v11-hybrid-design.md
```

### Implementation Plan

```text
docs/superpowers/plans/2026-04-28-ai-shoppee-video-tiktok-v11-hybrid-implementation.md
```

### Main v1.1 decisions

- support public TikTok `/video/`, short-link, and `/photo/` post shapes
- keep local-first architecture
- avoid relay services as the core workflow
- avoid deep signature/cookie API machinery for now
- upgrade photo-mode output from weak one-image fallback toward real multi-image slideshow behavior
- keep `Status` and `Analysis Done` simple, and put richer TikTok result type detail into `Notes`
