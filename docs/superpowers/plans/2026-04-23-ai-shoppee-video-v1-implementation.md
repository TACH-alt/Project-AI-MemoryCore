# AI - Shoppee Video v1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local first-pass automation for Shopee affiliate video intake, media download, 1080p captioned output, and project documentation.

**Architecture:** The system uses a Google Drive-synced project folder as the operational boundary. A spreadsheet/CSV masterlist is the human-editable input, Python handles row processing and media download, FFmpeg handles video rendering when installed, and Obsidian-friendly Markdown notes preserve project memory. Direct Google Sheets API updates are deferred until credentials or a connected Sheets MCP surface are available.

**Tech Stack:** Windows PowerShell, Python 3.14 standard library, optional `yt-dlp`, optional FFmpeg, Google Drive sync, `.xlsx`/`.csv` masterlist, Markdown notes.

---

## File Structure

- Create: `AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.csv`
- Create: `AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.xlsx`
- Create: `AI - Shoppee Video v1.0/input/approved-media/.gitkeep`
- Create: `AI - Shoppee Video v1.0/output/.gitkeep`
- Create: `AI - Shoppee Video v1.0/logs/run-log.csv`
- Create: `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
- Create: `AI - Shoppee Video v1.0/scripts/run_shopee_video_workflow.ps1`
- Create: `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`
- Create: `AI - Video Workflow/AI - Shoppee Video v1.0.md`
- Modify: `main/current-session.md`
- Modify: `daily-diary/current/2026-04-23.md`

## Implementation Notes

- The first runnable version reads CSV because it is stable with Python standard library and easy to sync through Google Drive.
- The `.xlsx` workbook is created as the polished masterlist template for Google Sheets import/opening.
- The script treats approved direct media links as first-class input.
- Shopee product pages are best-effort only: try `yt-dlp` when installed, then HTML media discovery. If neither works, log a clear failure.
- FFmpeg is required for edited video output. Without FFmpeg, the script still downloads raw media and logs that editing is blocked by the missing dependency.

### Task 1: Create Project Scaffold

**Files:**
- Create: `AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.csv`
- Create: `AI - Shoppee Video v1.0/input/approved-media/.gitkeep`
- Create: `AI - Shoppee Video v1.0/output/.gitkeep`
- Create: `AI - Shoppee Video v1.0/logs/run-log.csv`

- [x] **Step 1: Create folders**

Run:

```powershell
New-Item -ItemType Directory -Force -Path '.\AI - Shoppee Video v1.0\masterlist', '.\AI - Shoppee Video v1.0\input\approved-media', '.\AI - Shoppee Video v1.0\output', '.\AI - Shoppee Video v1.0\logs', '.\AI - Shoppee Video v1.0\scripts', '.\AI - Shoppee Video v1.0\tests'
```

Expected: directories exist.

- [x] **Step 2: Create CSV masterlist**

Write `AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.csv` with:

```csv
Date,Product Link,Product Name,Shop Name,Source Type,Status,Notes,Last Processed At,Output Folder,Output File
,,,,Auto,Pending,,,,
```

- [x] **Step 3: Create run log**

Write `AI - Shoppee Video v1.0/logs/run-log.csv` with:

```csv
timestamp,row_number,product_link,product_name,shop_name,status,message,output_file
```

- [x] **Step 4: Commit scaffold**

Run:

```powershell
git add -- 'AI - Shoppee Video v1.0'
git commit -m "feat: scaffold shoppee video workflow"
```

Expected: commit succeeds.

### Task 2: Add Masterlist Workbook

**Files:**
- Create: `AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.xlsx`

- [x] **Step 1: Build workbook**

Create a workbook with one sheet named `List of Link Shopee VIdeo`. Headers:

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

Use dropdown values:

```text
Source Type: Auto, Approved Media, Shopee Page
Status: Pending, Downloaded, Edited, Failed, Skipped
```

- [x] **Step 2: Verify workbook**

Inspect the header row and first editable row. Expected: headers match exactly and the first editable row has `Source Type = Auto`, `Status = Pending`.

- [x] **Step 3: Commit workbook**

Run:

```powershell
git add -- 'AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.xlsx'
git commit -m "feat: add shoppee video masterlist workbook"
```

Expected: commit succeeds.

### Task 3: Write Unit Tests For Core Helpers

**Files:**
- Create: `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`

- [x] **Step 1: Write failing tests**

Test these functions before implementation:

```python
from pathlib import Path
import csv
import tempfile
import unittest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from process_shopee_video import (
    build_caption,
    build_product_folder_name,
    derive_output_name,
    is_direct_media_url,
    safe_filename,
    load_rows,
)


class HelperTests(unittest.TestCase):
    def test_safe_filename_removes_windows_forbidden_characters(self):
        self.assertEqual(safe_filename('A/B:C*D?E"F<G>H|I'), "A-B-C-D-E-F-G-H-I")

    def test_product_folder_uses_product_dash_shop(self):
        self.assertEqual(build_product_folder_name("Mini Fan", "Cool Shop"), "Mini Fan-Cool Shop")

    def test_caption_uses_shop_dash_product(self):
        self.assertEqual(build_caption("Mini Fan", "Cool Shop"), "Cool Shop - Mini Fan")

    def test_output_name_appends_new_before_extension(self):
        self.assertEqual(derive_output_name(Path("demo.mp4")), "demo_new.mp4")

    def test_direct_media_detection(self):
        self.assertTrue(is_direct_media_url("https://example.com/video.mp4?download=1"))
        self.assertTrue(is_direct_media_url("https://example.com/image.jpeg"))
        self.assertFalse(is_direct_media_url("https://shopee.com.my/product/123"))

    def test_load_rows_reads_pending_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "master.csv"
            with path.open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "Date", "Product Link", "Product Name", "Shop Name",
                    "Source Type", "Status", "Notes", "Last Processed At",
                    "Output Folder", "Output File",
                ])
                writer.writeheader()
                writer.writerow({
                    "Date": "2026-04-23",
                    "Product Link": "https://example.com/video.mp4",
                    "Product Name": "Mini Fan",
                    "Shop Name": "Cool Shop",
                    "Source Type": "Approved Media",
                    "Status": "Pending",
                })
            rows = load_rows(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].row_number, 2)
            self.assertEqual(rows[0].product_name, "Mini Fan")


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v
```

Expected: FAIL with module or function import errors.

### Task 4: Implement Core Automation Script

**Files:**
- Create: `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`

- [x] **Step 1: Implement helper functions and CLI**

Implement:

```python
safe_filename(value: str) -> str
build_product_folder_name(product_name: str, shop_name: str) -> str
build_caption(product_name: str, shop_name: str) -> str
derive_output_name(raw_path: Path) -> str
is_direct_media_url(url: str) -> bool
load_rows(masterlist_path: Path) -> list[MasterRow]
process_pending_rows(config: WorkflowConfig) -> int
```

The CLI accepts:

```text
--masterlist
--project-root
--force
--dry-run
```

- [x] **Step 2: Run helper tests**

Run:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v
```

Expected: PASS.

- [x] **Step 3: Commit script and tests**

Run:

```powershell
git add -- 'AI - Shoppee Video v1.0/scripts/process_shopee_video.py' 'AI - Shoppee Video v1.0/tests/test_process_shopee_video.py'
git commit -m "feat: add shoppee video processing script"
```

Expected: commit succeeds.

### Task 5: Add PowerShell Runner

**Files:**
- Create: `AI - Shoppee Video v1.0/scripts/run_shopee_video_workflow.ps1`

- [x] **Step 1: Create runner**

The runner sets `$ProjectRoot`, points to `masterlist/List of Link Shopee VIdeo.csv`, checks Python, then runs:

```powershell
python "$ProjectRoot\scripts\process_shopee_video.py" --project-root "$ProjectRoot" --masterlist "$ProjectRoot\masterlist\List of Link Shopee VIdeo.csv"
```

- [x] **Step 2: Smoke test dry run**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File '.\AI - Shoppee Video v1.0\scripts\run_shopee_video_workflow.ps1' -DryRun
```

Expected: exits successfully and reports zero pending usable rows or dry-run actions.

- [x] **Step 3: Commit runner**

Run:

```powershell
git add -- 'AI - Shoppee Video v1.0/scripts/run_shopee_video_workflow.ps1'
git commit -m "feat: add shoppee video workflow runner"
```

Expected: commit succeeds.

### Task 6: Update Obsidian Project Note

**Files:**
- Create or modify: `AI - Video Workflow/AI - Shoppee Video v1.0.md`

- [x] **Step 1: Add project note**

Include:

```markdown
# AI - Shoppee Video v1.0

## Purpose
Local-first automation for Shopee Video affiliate media intake, download, 1080p caption rendering, and organized output.

## Current Status
- Design spec created.
- Implementation plan created.
- Local scaffold and scripts created.

## Key Files
- `docs/superpowers/specs/2026-04-23-ai-shoppee-video-v1-design.md`
- `docs/superpowers/plans/2026-04-23-ai-shoppee-video-v1-implementation.md`
- `AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.xlsx`
- `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
- `AI - Shoppee Video v1.0/scripts/run_shopee_video_workflow.ps1`

## Operating Notes
- Use approved seller media links whenever possible.
- Shopee product page scraping is best-effort only.
- FFmpeg is required for edited `_new.mp4` output.
```

- [x] **Step 2: Commit note**

Run:

```powershell
git add -- 'AI - Video Workflow/AI - Shoppee Video v1.0.md'
git commit -m "docs: add shoppee video project note"
```

Expected: commit succeeds.

### Task 7: Save Memory And Diary

**Files:**
- Modify: `main/current-session.md`
- Modify: `daily-diary/current/2026-04-23.md`

- [x] **Step 1: Update current session memory**

Record that `AI - Shoppee Video v1.0` moved from design into implementation planning and local scaffold build, and that Legend asked for every project `.md` update to be mirrored into Obsidian notes.

- [x] **Step 2: Update daily diary**

Add a concise entry for the project decision, generated spec, generated plan, and implementation status.

- [x] **Step 3: Commit memory updates**

Run:

```powershell
git add -- 'main/current-session.md' 'daily-diary/current/2026-04-23.md'
git commit -m "docs: save shoppee video workflow memory"
```

Expected: commit succeeds.

## Verification Checklist

- [x] Unit tests pass with `python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v`.
- [x] Dry run succeeds with `powershell -ExecutionPolicy Bypass -File '.\AI - Shoppee Video v1.0\scripts\run_shopee_video_workflow.ps1' -DryRun`.
- [x] Masterlist CSV and workbook contain the required columns.
- [x] Obsidian note links to every project `.md` created or updated in this work.
- [x] Memory files mention the new documentation rule and current project status.
- [x] Shopee full product URL extractor is tested for query cleanup, mobile page headers, Shopee CDN media extraction, and one-best-video selection.
- [x] Live Electrova product URL test produced a captioned `1080x1920` `_new.mp4` and updated the masterlist row to `Edited` / `Done = TRUE`.

## Follow-Up Fix - Shopee Product URL Extraction

**Date:** 2026-04-23

Root cause refinement:

- Desktop Shopee HTML and Shopee item APIs can fail or omit product media.
- Mobile browser-style Shopee product HTML can expose seller media URLs in SEO/product data.

Implemented:

- Shopee product URL parser for `/product/<shopid>/<itemid>` and slug `-i.<shopid>.<itemid>` links.
- Query stripping for Shopee product URLs before scraping.
- Mobile browser request headers for Shopee page discovery.
- Shopee CDN extraction for `*.vod.susercontent.com` MP4 files and `down-my.img.susercontent.com/file/...` images.
- Shopee UI asset filtering.
- One-best-video selection to avoid duplicate renders from multiple quality variants.

Verified output:

```text
AI - Shoppee Video v1.0/output/Electrova Cordless UV Mite-Electrova/edited/my-11110105-6ke18-lqbrwqqiae664d.16003251736514494_new.mp4
```

