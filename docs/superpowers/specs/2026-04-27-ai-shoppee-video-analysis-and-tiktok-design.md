# AI - Shoppee Video Analysis and TikTok Support Design

**Project**: AI - Shoppee Video v1.0  
**Date**: 2026-04-27  
**Status**: Approved design spec  
**Scope**: Add analysis workflow support, stable record IDs, revised output folder structure, and public TikTok video URL support

## Goal

Extend the existing Shopee affiliate workflow so the app can:

- assign stable IDs to every masterlist row
- support a manual `Analyze` action on already-downloaded product folders
- support a direct `Save + Download + Analyze` action
- write markdown documentation files into each product folder
- support public single TikTok video URLs as a new download source

This design keeps the current local-first workflow and builds the new features into the existing frontend, backend, and masterlist instead of creating a second tool.

## Out of Scope

This design does not include:

- private TikTok videos
- TikTok profile or playlist scraping
- login-required flows
- deep TikTok metadata extraction beyond what is needed for download and analysis
- public internet hosting
- full CapCut project import/export integration

## Current System Summary

The current system already supports:

- CSV and workbook masterlist sync
- Shopee and direct media download flow
- local frontend for saving rows and triggering downloads
- FFmpeg render pipeline
- output folders with raw and edited media

The current system does not yet support:

- stable row identity independent of `Product Link`
- analysis-only workflow
- download-and-analyze workflow
- analysis-tracking in masterlist
- TikTok public video URL support
- product-folder markdown summaries

## Masterlist Design

### Required Columns

The masterlist should be revised to this order:

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

### Record ID

`Record ID` must be the first column.

Format:

- Shopee rows: `ASV-0000001`
- TikTok rows: `ATV-0000001`

Rules:

- generated automatically when a new row is first saved
- never changes after creation
- existing rows are backfilled once
- used as the stable identity for row actions in frontend and backend

Platform-specific numbering should be independent:

- first Shopee row -> `ASV-0000001`
- second Shopee row -> `ASV-0000002`
- first TikTok row -> `ATV-0000001`

### Analysis Done

`Analysis Done` is a checkbox-style tracker.

Rules:

- default value: `FALSE`
- set to `TRUE` only when analysis markdown is successfully written
- stays `FALSE` if download happened without analysis
- stays `FALSE` if analysis fails

### Backfill Rules

When the revised masterlist is loaded:

- missing `Record ID` values must be generated and written back
- missing `Analysis Done` values must default to `FALSE`
- CSV and workbook sync must continue working
- old rows must keep their original business data

## Platform Detection

Platform must be inferred from the saved link.

Rules:

- Shopee URL -> platform `Shopee`
- public single TikTok video URL -> platform `TikTok`

Platform decides:

- `Record ID` prefix
- output folder top-level directory
- download strategy

## Output Folder Structure

The output folder structure should change to:

```text
output/
  Shopee/
    <Shop Name>/
      <Product Name>/
  TikTok/
    <Shop Name>/
      <Product Name>/
```

### Shop Folder Rules

Shop grouping must be case-insensitive.

If a matching shop already exists under the same platform:

- reuse the first-saved shop folder name
- do not create a second folder only because casing changed

Example:

```text
output/
  Shopee/
    Electrova/
      Kettle/
      Steam Iron/
```

If the user first saved `Electrova` and later typed `electrova`, the system must keep `Electrova`.

### Product Folder Rules

Product folder names:

- are created under the resolved platform/shop path
- use user-entered `Product Name`
- must be sanitized for Windows-safe naming

`Record ID` remains the row identity in the data model, but it is not used as the visible folder prefix.

## Product Folder Contents

Each product folder becomes a small workflow record:

```text
output/
  Shopee|TikTok/
    <Shop Name>/
      <Product Name>/
        product-info.md
        raw/
        edited/
        analysis/
          analysis-result.md
```

## Save Workflow

### Save

On successful `Save`, the backend must:

1. ensure the row has a `Record ID`
2. resolve platform from the link
3. resolve the shop folder case-insensitively
4. create the product folder if needed
5. create or update `product-info.md`
6. save the row back to the masterlist

### product-info.md

Path:

```text
output/<Platform>/<Shop Name>/<Product Name>/product-info.md
```

Content must include:

- Record ID
- Date
- Product Link
- Product Name
- Shop Name
- Platform
- Source Type
- Status
- Done
- Analysis Done
- Notes

And a media summary:

- downloaded video count
- downloaded image count
- latest known output file summary

Rules:

- if no download exists yet, media counts must be `0`
- later download and analysis actions should refresh this same file

## Download Workflow

### Save + Download

The current download flow remains valid, but it must operate on the new row identity and folder model.

On successful download:

- raw media must be written into the product folder `raw/`
- edited outputs must be written into `edited/`
- `product-info.md` must be refreshed with the latest media counts

### Public TikTok Video URL Support

Support only:

- public single TikTok video URLs

Do not support:

- private videos
- profile pages
- playlists
- login-only content
- unrelated TikTok scraping

TikTok public video download should be integrated into the existing media collection pipeline, not implemented as a separate tool.

## Analyze Workflow

### Manual Analyze

The app must support an `Analyze` action for already-downloaded rows.

Flow:

1. user selects or loads a row from the masterlist
2. frontend sends the row `Record ID`
3. backend finds that exact row by `Record ID`
4. backend resolves the product folder
5. backend finds the best available media to analyze
6. backend writes analysis markdown
7. backend updates `Analysis Done = TRUE`
8. backend refreshes `product-info.md`

If no downloaded media exists:

- analysis must fail clearly
- `Analysis Done` must remain `FALSE`

Error message:

```text
No downloaded media found for Record ID ASV-0000001. Run Download first.
```

### Download + Analyze

The app must support a direct `Save + Download + Analyze` action.

Flow:

1. save row
2. ensure `Record ID`
3. run download flow
4. if media exists, immediately run analysis
5. write analysis markdown
6. update `Analysis Done = TRUE`
7. refresh `product-info.md`

If download fails:

- analysis must not run
- `Analysis Done` stays `FALSE`

If download succeeds but analysis fails:

- keep downloaded media and any edited outputs
- keep `Done` based on actual download/edit result
- keep `Analysis Done = FALSE`

## Analysis Result File

Path:

```text
output/<Platform>/<Shop Name>/<Product Name>/analysis/analysis-result.md
```

This file is the completion artifact for analysis.

Content should include:

- Record ID
- Platform
- Product Name
- Shop Name
- Product Link
- Source Type
- analyzed media file path/name
- technical media summary
  - duration
  - resolution
  - fps
  - audio present or not
- suggested hooks
- suggested angles
- suggested clip order or scene sequence
- CTA suggestions
- CapCut/manual handoff note

Rules:

- do not claim facts that are not visible in media or present in saved row data
- if exact timestamps cannot be derived confidently, use scene-order or clip-sequence suggestions instead of fake precision

## Frontend Design

### Main Actions

The frontend should support:

- `Save`
- `Save + Download`
- `Analyze`
- `Save + Download + Analyze`
- `Open Output Folder`

### Row Identity

Frontend row actions must use `Record ID`, not `Product Link`, as the true row identity.

This applies to:

- `Load`
- `Analyze`
- retry/download actions
- combined actions

### Table Display

The table should expose:

- `Record ID`
- `Status`
- `Done`
- `Analysis Done`

Recommended behavior:

- `Analyze` should be available as a row action
- `Save + Download + Analyze` should be a main form button

## Backend Design

Recommended backend units:

- `save_row(record)`
- `download_row(record_id)`
- `analyze_row(record_id)`
- `download_and_analyze_row(record_id)`

Supporting responsibilities:

- detect platform from link
- generate backfilled and new IDs
- resolve platform/shop/product folder path
- find best analyzable media
- write `product-info.md`
- write `analysis-result.md`
- update masterlist flags

## Logging and Failure Behavior

### Save

If row save succeeds but markdown update fails:

- report the error clearly
- do not silently lose row data

### Analyze

If analysis fails:

- do not remove downloaded media
- do not clear successful download state
- keep `Analysis Done = FALSE`
- write useful error context into notes or run log

### Download + Analyze

If download fails:

- analysis does not run

If analysis fails after a successful download:

- preserve the successful download and outputs
- preserve `Done`
- keep `Analysis Done = FALSE`

## Testing Requirements

### Masterlist

- adds `Record ID` as first column
- adds `Analysis Done`
- backfills old rows safely
- preserves workbook sync

### ID Generation

- Shopee rows generate `ASV-0000001` style IDs
- TikTok rows generate `ATV-0000001` style IDs
- numbering is stable and separated by platform

### Folder Resolution

- Shopee rows go to `output/Shopee/...`
- TikTok rows go to `output/TikTok/...`
- shop matching is case-insensitive
- first-saved shop casing is reused

### Save Flow

- `Save` creates or updates `product-info.md`
- zero media counts are shown before download
- row updates preserve the same `Record ID`

### Analyze Flow

- analyze fails cleanly if no media exists
- analyze writes `analysis-result.md`
- analyze sets `Analysis Done = TRUE` on success

### Download + Analyze Flow

- download runs before analysis
- failed download does not mark analysis complete
- analysis failure does not destroy successful download state

### Frontend

- actions target `Record ID`
- `Analyze` route works on existing rows
- `Save + Download + Analyze` route works end to end
- table shows `Analysis Done`

### TikTok Support

- public TikTok single-video URL is accepted
- non-supported TikTok URL shapes fail clearly

## Implementation Order

Recommended build order:

1. masterlist migration for `Record ID` and `Analysis Done`
2. platform detection and output-folder resolver
3. `product-info.md` generation on save
4. analysis backend and `analysis-result.md`
5. frontend `Analyze` and `Save + Download + Analyze`
6. TikTok public video URL support
7. full test pass and manual verification

## Rationale

This design moves the system from:

```text
save -> download -> edit
```

to:

```text
save -> document -> download -> analyze -> handoff
```

while preserving the existing local-first workflow and keeping the new features consistent across Shopee and TikTok inputs.
