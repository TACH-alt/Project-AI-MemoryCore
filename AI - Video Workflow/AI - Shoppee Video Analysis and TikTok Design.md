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
