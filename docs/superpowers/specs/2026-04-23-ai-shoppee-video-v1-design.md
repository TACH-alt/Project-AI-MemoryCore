# AI - Shoppee Video v1.0 Design

**Project name:** AI - Shoppee Video v1.0  
**Date:** 2026-04-23  
**Status:** Design approved for documentation  
**Primary user:** Legend  
**Purpose:** Automate collection, organization, and basic editing of approved Shopee affiliate product videos and images.

## Goal

Build a practical automation system for Shopee Video affiliate content. Legend will manually add product rows through a Google Sheet, usually from phone or Google Drive. When the automation is triggered manually or by schedule, it will download seller-approved media or best-effort media from a Shopee product page, organize the files by product and shop, upscale video output to 1080p, add a caption, and save the edited video with `_new` appended to the original video name.

## Masterlist

The masterlist should be a Google Sheet named after the project:

```text
AI - Shoppee Video v1.0
```

The first sheet tab should be:

```text
List of Link Shopee VIdeo
```

Required columns:

```text
Date
Product Link
Product Name
Shop Name
```

Recommended automation columns:

```text
Source Type
Status
Notes
Last Processed At
Output Folder
Output File
```

`Source Type` should allow values such as `Approved Media`, `Shopee Page`, or `Auto`. `Status` should allow values such as `Pending`, `Downloaded`, `Edited`, `Failed`, or `Skipped`.

## Operating Model

Legend adds rows manually in Google Sheet from Google Drive, phone, or desktop. The automation only processes rows that are new or marked `Pending`. It should not overwrite completed outputs unless the user manually resets a row status or runs a force option.

The automation supports two link types:

1. Approved seller media links, which are the preferred and most reliable source.
2. Shopee product page links, which are supported as a best-effort fallback because Shopee pages can be dynamic, protected, or blocked by login, captcha, or rate limits.

When a Shopee product page cannot be scraped reliably, the row should be marked `Failed` with a clear note instead of silently skipping it.

## Folder Structure

The local project folder should be:

```text
AI - Shoppee Video v1.0/
  masterlist/
  input/
    approved-media/
  output/
    Product Name-Shop Name/
      raw/
      edited/
  logs/
  scripts/
  docs/
```

Each processed product gets a folder named:

```text
Product Name-Shop Name
```

Invalid filename characters should be cleaned so Windows, Google Drive sync, and video tools can handle the folder names safely.

## Workflow

1. Read the masterlist from Google Sheet or from a synced local export.
2. Find rows with blank status or `Pending`.
3. Determine whether the `Product Link` is approved media, a direct file link, or a Shopee product page.
4. Download video or image media into the product folder under `raw`.
5. If the source is an image, either store it for later video creation or create a simple 1080p vertical video from the image.
6. Normalize output to 1080p vertical format where practical.
7. Add caption text in this format:

```text
Shop Name - Product Name
```

8. Save the edited video under `edited`.
9. Rename the edited video by appending `_new` before the extension.
10. Update logs and, where possible, update the sheet row with status, notes, output folder, output file, and last processed time.

## Video Output Rules

Default output target:

```text
Resolution: 1080x1920
Aspect ratio: 9:16 vertical
Format: MP4
Codec: H.264
Caption: Shop Name - Product Name
```

If the source video is landscape or square, the v1.0 behavior should be conservative: fit the video into a vertical canvas with padding or blurred background rather than cropping important product content without review.

Edited filenames should follow:

```text
original-name_new.mp4
```

If no original filename is available, use a safe generated name based on date, product name, and shop name.

## Triggering

The system should support both:

1. Manual trigger from a PowerShell script or desktop shortcut.
2. Scheduled trigger through Windows Task Scheduler or a Codex automation after the manual workflow is proven stable.

Manual trigger is the first implementation priority because it is easier to test and safer while the scraper behavior is being validated.

## Error Handling

The automation must log each row outcome. Failures should include the row number, product link, reason, and time. Common failure reasons include blocked Shopee page, no video found, download error, invalid link, missing product name, missing shop name, and FFmpeg processing error.

Failed rows should not block the whole batch. The system should continue processing the next pending row.

## Compliance And Safety

The system is designed for seller-approved affiliate media. The preferred input should always be approved seller media links or media that Legend has permission to reuse. Shopee page extraction should be treated as best-effort and should respect platform limitations.

The automation should not generate fake engagement, click traffic, or misleading product claims. It only prepares media files for manual review and posting.

## V1.0 Scope

Included:

- Google Sheet masterlist design.
- Local project folder structure.
- Manual row entry by Legend.
- Manual automation trigger.
- Pending-row processing.
- Download approved media links.
- Best-effort Shopee page media extraction.
- Product folder creation.
- 1080p vertical MP4 output.
- Caption overlay using `Shop Name - Product Name`.
- `_new` edited filename suffix.
- Run logs and row status updates where available.

Not included in v1.0:

- Automatic posting to Shopee Video.
- Automatic affiliate performance tracking.
- AI script generation.
- AI voiceover.
- Advanced template editing.
- Bypassing captcha, login, DRM, or platform protections.
- Fully reliable scraping from every Shopee page.

## Open Implementation Choices

The implementation plan should decide whether the first build reads directly from Google Sheets through an API or uses the locally synced Google Drive file. Direct Google Sheets access is cleaner for row updates, while local synced files are simpler if Drive is already syncing the project folder.

The first build should prefer reliability over full automation. A manual run button, clear logs, and simple folder output are more valuable than a complex scheduler before the media extraction behavior is tested.

