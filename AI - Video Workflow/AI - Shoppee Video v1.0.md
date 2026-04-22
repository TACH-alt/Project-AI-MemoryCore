# AI - Shoppee Video v1.0

**Project name:** AI - Shoppee Video v1.0  
**Date opened:** 2026-04-23  
**Status:** Implementation planning started  
**Owner:** Legend

## Purpose

Build a local-first automation system for Shopee Video affiliate work. Legend manually adds product rows from phone, Google Drive, or desktop. The automation reads the masterlist, downloads approved seller media or best-effort Shopee page media, organizes files by product and shop, creates 1080p vertical captioned videos, and saves edited files with `_new` appended to the filename.

## Current Decisions

- Use approved seller media links as the preferred source.
- Support Shopee product page links as best-effort fallback only.
- Use a Google Drive-synced project folder as the local operating area.
- Create a polished `.xlsx` masterlist template and a CSV masterlist that automation can read reliably.
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
Notes
Last Processed At
Output Folder
Output File
```

## Key Files

- `docs/superpowers/specs/2026-04-23-ai-shoppee-video-v1-design.md`
- `docs/superpowers/plans/2026-04-23-ai-shoppee-video-v1-implementation.md`
- `AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.csv`
- `AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.xlsx`
- `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
- `AI - Shoppee Video v1.0/scripts/run_shopee_video_workflow.ps1`

## Markdown Change Log

### 2026-04-23

- Created design spec: `docs/superpowers/specs/2026-04-23-ai-shoppee-video-v1-design.md`.
- Created implementation plan: `docs/superpowers/plans/2026-04-23-ai-shoppee-video-v1-implementation.md`.
- Created this Obsidian project note: `AI - Video Workflow/AI - Shoppee Video v1.0.md`.

## Next Actions

- Build the local project scaffold.
- Create the masterlist workbook and CSV.
- Implement the Python processor and PowerShell runner.
- Run unit tests and dry-run verification.
- Save session memory and daily diary updates after implementation.

