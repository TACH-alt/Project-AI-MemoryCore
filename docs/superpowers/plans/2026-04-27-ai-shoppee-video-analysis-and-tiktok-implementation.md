# AI - Shoppee Video Analysis and TikTok Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add stable masterlist record IDs, analysis tracking, product-folder markdown output, manual and direct analysis actions, and public TikTok single-video download support to `AI - Shoppee Video v1.0`.

**Architecture:** Extend the existing `process_shopee_video.py` pipeline with platform detection, row identity, folder resolution, product-info markdown writing, analysis generation, and TikTok-aware media collection. Then wire the new capabilities into `shoppee_video_frontend.py` and the PowerShell runner using `Record ID` as the stable action target.

**Tech Stack:** Python, PowerShell, CSV/openpyxl workbook sync, FFmpeg, yt-dlp, unittest, local HTML frontend

---

## File Structure

### Existing files to modify

- `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
  - masterlist schema migration
  - record ID generation
  - platform detection
  - output folder resolution
  - product-info markdown writing
  - analysis generation
  - TikTok public-video collection support
  - CLI support for analysis-only and download-plus-analyze flows
- `AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py`
  - form/table updates for `Record ID` and `Analysis Done`
  - new `Analyze` and `Save + Download + Analyze` actions
  - action routing by `Record ID`
- `AI - Shoppee Video v1.0/scripts/run_shopee_video_workflow.ps1`
  - CLI passthrough for analysis modes / target record
- `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`
  - row schema, ID, folder, markdown, analysis, TikTok tests
- `AI - Shoppee Video v1.0/tests/test_shoppee_video_frontend.py`
  - frontend normalization and API helper tests

### New files to create

- `AI - Shoppee Video v1.0/tests/test_analysis_workflow.py`
  - focused end-to-end row workflow tests for analyze and download+analyze paths

---

### Task 1: Migrate The Masterlist Schema And Stable Record IDs

**Files:**
- Modify: `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
- Modify: `AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py`
- Modify: `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`
- Modify: `AI - Shoppee Video v1.0/tests/test_shoppee_video_frontend.py`

- [ ] **Step 1: Write the failing schema and ID tests**

Add tests to `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py` for the new masterlist order, default values, and backfill behavior:

```python
def test_ensure_masterlist_columns_adds_record_id_and_analysis_done(self):
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
        path = Path(tmp) / "master.csv"
        path.write_text(
            "Date,Product Link,Product Name,Shop Name,Source Type,Status,Done,Notes,Last Processed At,Output Folder,Output File\n"
            "2026-04-27,https://shopee.com.my/product/1/2,Kettle,Electrova,Auto,Pending,FALSE,,,,\n",
            encoding="utf-8-sig",
        )
        ensure_masterlist_columns(path)
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(rows[0]["Record ID"], "ASV-0000001")
        self.assertEqual(rows[0]["Analysis Done"], "FALSE")


def test_backfilled_ids_use_platform_specific_prefixes(self):
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
        path = Path(tmp) / "master.csv"
        path.write_text(
            "Date,Product Link,Product Name,Shop Name,Source Type,Status,Done,Analysis Done,Notes,Last Processed At,Output Folder,Output File\n"
            "2026-04-27,https://shopee.com.my/product/1/2,Kettle,Electrova,Auto,Pending,FALSE,FALSE,,,,\n"
            "2026-04-27,https://www.tiktok.com/@demo/video/1234567890,Steam Iron,Electrova,Auto,Pending,FALSE,FALSE,,,,\n",
            encoding="utf-8-sig",
        )
        ensure_masterlist_columns(path)
        rows = read_masterlist(path)
        self.assertEqual(rows[0]["Record ID"], "ASV-0000001")
        self.assertEqual(rows[1]["Record ID"], "ATV-0000001")
```

Add a frontend normalization test to `AI - Shoppee Video v1.0/tests/test_shoppee_video_frontend.py`:

```python
def test_normalize_frontend_row_defaults_record_and_analysis_fields(self):
    row = normalize_frontend_row({
        "Date": "2026-04-27",
        "Product Link": "https://shopee.com.my/product/1/2",
        "Product Name": "Kettle",
        "Shop Name": "Electrova",
    })
    self.assertEqual(row["Record ID"], "")
    self.assertEqual(row["Analysis Done"], "FALSE")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest .\AI - Shoppee Video v1.0\tests\test_process_shopee_video.py -v
python -m unittest .\AI - Shoppee Video v1.0\tests\test_shoppee_video_frontend.py -v
```

Expected:
- failures for missing `Record ID`
- failures for missing `Analysis Done`
- failures because platform-specific IDs do not exist yet

- [ ] **Step 3: Implement the schema migration and ID helpers**

Update `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`:

```python
REQUIRED_COLUMNS = [
    "Record ID",
    "Date",
    "Product Link",
    "Product Name",
    "Shop Name",
    "Source Type",
    "Status",
    "Done",
    "Analysis Done",
    "Notes",
    "Last Processed At",
    "Output Folder",
    "Output File",
]


def is_tiktok_video_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return host.endswith("tiktok.com") and "/video/" in parsed.path


def detect_platform(url: str) -> str:
    if is_shopee_url(url):
        return "Shopee"
    if is_tiktok_video_url(url):
        return "TikTok"
    return "Unknown"


def record_prefix_for_url(url: str) -> str:
    platform = detect_platform(url)
    if platform == "Shopee":
        return "ASV"
    if platform == "TikTok":
        return "ATV"
    return "ASV"


def next_record_id(rows: list[dict[str, str]], prefix: str) -> str:
    pattern = re.compile(rf"^{prefix}-(\d{{7}})$")
    highest = 0
    for row in rows:
        match = pattern.match((row.get("Record ID") or "").strip())
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}-{highest + 1:07d}"
```

Update record normalization in both scripts:

```python
def default_value_for_column(column: str) -> str:
    defaults = {
        "Record ID": "",
        "Source Type": "Auto",
        "Status": "Pending",
        "Done": "FALSE",
        "Analysis Done": "FALSE",
    }
    return defaults.get(column, "")
```

Backfill IDs during schema normalization:

```python
def backfill_record_identity(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    normalized_rows = [normalize_record(row) for row in rows]
    for row in normalized_rows:
        if not row["Record ID"] and row["Product Link"]:
            prefix = record_prefix_for_url(row["Product Link"])
            row["Record ID"] = next_record_id(normalized_rows, prefix)
    return normalized_rows
```

Wire this into `ensure_masterlist_columns()` and `read_masterlist()`, and update `shoppee_video_frontend.py` defaults:

```python
def default_row() -> dict[str, str]:
    return {
        "Record ID": "",
        "Date": "",
        "Product Link": "",
        "Product Name": "",
        "Shop Name": "",
        "Source Type": "Auto",
        "Status": "Pending",
        "Done": "FALSE",
        "Analysis Done": "FALSE",
        "Notes": "",
        "Last Processed At": "",
        "Output Folder": "",
        "Output File": "",
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m unittest .\AI - Shoppee Video v1.0\tests\test_process_shopee_video.py -v
python -m unittest .\AI - Shoppee Video v1.0\tests\test_shoppee_video_frontend.py -v
```

Expected:
- both suites pass
- old masterlist migration still works

- [ ] **Step 5: Commit**

```powershell
git add -- "AI - Shoppee Video v1.0/scripts/process_shopee_video.py" "AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py" "AI - Shoppee Video v1.0/tests/test_process_shopee_video.py" "AI - Shoppee Video v1.0/tests/test_shoppee_video_frontend.py"
git commit -m "feat: add record ids and analysis tracking"
```

---

### Task 2: Resolve Platform/Shop/Product Folders And Write product-info.md On Save

**Files:**
- Modify: `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
- Modify: `AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py`
- Modify: `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`

- [ ] **Step 1: Write the failing folder and markdown tests**

Add tests to `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`:

```python
def test_resolve_product_folder_groups_by_platform_shop_and_product(self):
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
        root = Path(tmp)
        folder = resolve_product_folder(
            root / "output",
            "Shopee",
            "Electrova",
            "Cordless Kettle",
        )
        self.assertEqual(
            folder,
            root / "output" / "Shopee" / "Electrova" / "Cordless Kettle",
        )


def test_resolve_shop_folder_reuses_first_saved_case_insensitive_name(self):
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
        root = Path(tmp) / "output" / "Shopee"
        (root / "Electrova").mkdir(parents=True)
        folder = resolve_shop_folder(root, "electrova")
        self.assertEqual(folder.name, "Electrova")


def test_write_product_info_creates_zero_media_summary_before_download(self):
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
        product_dir = Path(tmp) / "Shopee" / "Electrova" / "Kettle"
        row = {
            "Record ID": "ASV-0000001",
            "Date": "2026-04-27",
            "Product Link": "https://shopee.com.my/product/1/2",
            "Product Name": "Kettle",
            "Shop Name": "Electrova",
            "Source Type": "Auto",
            "Status": "Pending",
            "Done": "FALSE",
            "Analysis Done": "FALSE",
            "Notes": "",
            "Last Processed At": "",
            "Output Folder": "",
            "Output File": "",
        }
        write_product_info(product_dir, row, platform="Shopee")
        note = (product_dir / "product-info.md").read_text(encoding="utf-8")
        self.assertIn("Record ID: ASV-0000001", note)
        self.assertIn("Downloaded Video Count: 0", note)
        self.assertIn("Downloaded Image Count: 0", note)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest .\AI - Shoppee Video v1.0\tests\test_process_shopee_video.py -v
```

Expected:
- failures for missing folder resolver helpers
- failure for missing `product-info.md` generation

- [ ] **Step 3: Implement folder resolution and product-info markdown**

Add helpers to `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`:

```python
def safe_folder_name(value: str) -> str:
    return safe_filename(value)


def resolve_shop_folder(platform_root: Path, shop_name: str) -> Path:
    wanted = safe_folder_name(shop_name)
    platform_root.mkdir(parents=True, exist_ok=True)
    for child in platform_root.iterdir():
        if child.is_dir() and child.name.casefold() == wanted.casefold():
            return child
    return platform_root / wanted


def resolve_product_folder(output_root: Path, platform: str, shop_name: str, product_name: str) -> Path:
    platform_root = output_root / platform
    shop_folder = resolve_shop_folder(platform_root, shop_name)
    return shop_folder / safe_folder_name(product_name)


def count_media_files(directory: Path) -> tuple[int, int]:
    if not directory.exists():
        return (0, 0)
    videos = sum(1 for path in directory.iterdir() if path.suffix.lower() in VIDEO_EXTENSIONS)
    images = sum(1 for path in directory.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)
    return (videos, images)


def write_product_info(product_dir: Path, row: dict[str, str], platform: str) -> Path:
    raw_dir = product_dir / "raw"
    videos, images = count_media_files(raw_dir)
    body = "\n".join([
        f"# {row['Product Name']}",
        "",
        f"- Record ID: {row['Record ID']}",
        f"- Platform: {platform}",
        f"- Date: {row['Date']}",
        f"- Product Link: {row['Product Link']}",
        f"- Product Name: {row['Product Name']}",
        f"- Shop Name: {row['Shop Name']}",
        f"- Source Type: {row['Source Type']}",
        f"- Status: {row['Status']}",
        f"- Done: {row['Done']}",
        f"- Analysis Done: {row['Analysis Done']}",
        f"- Notes: {row['Notes']}",
        "",
        "## Media Summary",
        f"- Downloaded Video Count: {videos}",
        f"- Downloaded Image Count: {images}",
        f"- Output File: {row['Output File']}",
    ])
    product_dir.mkdir(parents=True, exist_ok=True)
    note_path = product_dir / "product-info.md"
    note_path.write_text(body + "\n", encoding="utf-8")
    return note_path
```

Update row save/upsert in `shoppee_video_frontend.py` so new rows are keyed by `Record ID` when present, then refresh product notes after save:

```python
def upsert_masterlist_row(masterlist_path: Path, payload: dict[str, str]) -> tuple[int, dict[str, str]]:
    ensure_masterlist_columns(masterlist_path)
    rows = read_masterlist(masterlist_path)
    row = normalize_frontend_row(payload)
    if not row["Record ID"]:
        row["Record ID"] = next_record_id(rows, record_prefix_for_url(row["Product Link"]))
    for index, existing in enumerate(rows):
        if row["Record ID"] and existing["Record ID"] == row["Record ID"]:
            merged = existing.copy()
            merged.update(row)
            rows[index] = merged
            write_masterlist(masterlist_path, rows)
            return index + 2, merged
    rows.append(row)
    write_masterlist(masterlist_path, rows)
    return len(rows) + 1, row
```

Then, after save:

```python
platform = detect_platform(saved_row["Product Link"])
product_dir = resolve_product_folder(project_root / "output", platform, saved_row["Shop Name"], saved_row["Product Name"])
saved_row["Output Folder"] = str(product_dir)
write_product_info(product_dir, saved_row, platform=platform)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m unittest .\AI - Shoppee Video v1.0\tests\test_process_shopee_video.py -v
python -m unittest .\AI - Shoppee Video v1.0\tests\test_shoppee_video_frontend.py -v
```

Expected:
- folder resolution tests pass
- `product-info.md` creation test passes

- [ ] **Step 5: Commit**

```powershell
git add -- "AI - Shoppee Video v1.0/scripts/process_shopee_video.py" "AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py" "AI - Shoppee Video v1.0/tests/test_process_shopee_video.py"
git commit -m "feat: add platform folders and product info notes"
```

---

### Task 3: Add Analysis Backend And analysis-result.md Generation

**Files:**
- Modify: `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
- Create: `AI - Shoppee Video v1.0/tests/test_analysis_workflow.py`

- [ ] **Step 1: Write the failing analysis tests**

Create `AI - Shoppee Video v1.0/tests/test_analysis_workflow.py`:

```python
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from process_shopee_video import analyze_row_record


class AnalysisWorkflowTests(unittest.TestCase):
    def test_analyze_row_fails_cleanly_when_no_media_exists(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            project_root = Path(tmp)
            row = {
                "Record ID": "ASV-0000001",
                "Product Link": "https://shopee.com.my/product/1/2",
                "Product Name": "Kettle",
                "Shop Name": "Electrova",
                "Source Type": "Auto",
                "Status": "Downloaded",
                "Done": "TRUE",
                "Analysis Done": "FALSE",
                "Notes": "",
                "Output Folder": str(project_root / "output" / "Shopee" / "Electrova" / "Kettle"),
                "Output File": "",
            }
            with self.assertRaisesRegex(RuntimeError, "No downloaded media found"):
                analyze_row_record(project_root, row)

    def test_analyze_row_writes_analysis_result_and_marks_done(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            project_root = Path(tmp)
            product_dir = project_root / "output" / "Shopee" / "Electrova" / "Kettle"
            raw_dir = product_dir / "raw"
            raw_dir.mkdir(parents=True)
            media = raw_dir / "demo.mp4"
            media.write_bytes(b"fake")
            row = {
                "Record ID": "ASV-0000001",
                "Date": "2026-04-27",
                "Product Link": "https://shopee.com.my/product/1/2",
                "Product Name": "Kettle",
                "Shop Name": "Electrova",
                "Source Type": "Auto",
                "Status": "Downloaded",
                "Done": "TRUE",
                "Analysis Done": "FALSE",
                "Notes": "",
                "Output Folder": str(product_dir),
                "Output File": "",
            }
            result_path = analyze_row_record(project_root, row)
            self.assertTrue(result_path.exists())
            self.assertEqual(row["Analysis Done"], "TRUE")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest .\AI - Shoppee Video v1.0\tests\test_analysis_workflow.py -v
```

Expected:
- import or attribute failures for missing analysis helpers

- [ ] **Step 3: Implement analysis helpers and CLI modes**

Add focused analysis helpers to `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`:

```python
def choose_analysis_media(product_dir: Path) -> Path | None:
    raw_dir = product_dir / "raw"
    if not raw_dir.exists():
        return None
    candidates = sorted(raw_dir.iterdir())
    videos = [path for path in candidates if path.suffix.lower() in VIDEO_EXTENSIONS]
    if videos:
        return videos[0]
    images = [path for path in candidates if path.suffix.lower() in IMAGE_EXTENSIONS]
    return images[0] if images else None


def media_summary_for_analysis(media_path: Path) -> dict[str, str]:
    return {
        "file": media_path.name,
        "duration": "unknown",
        "resolution": "unknown",
        "fps": "unknown",
        "audio": "unknown",
    }


def write_analysis_result(product_dir: Path, row: dict[str, str], platform: str, media_path: Path) -> Path:
    analysis_dir = product_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    summary = media_summary_for_analysis(media_path)
    body = "\n".join([
        f"# Analysis Result - {row['Product Name']}",
        "",
        f"- Record ID: {row['Record ID']}",
        f"- Platform: {platform}",
        f"- Product Name: {row['Product Name']}",
        f"- Shop Name: {row['Shop Name']}",
        f"- Product Link: {row['Product Link']}",
        f"- Source Type: {row['Source Type']}",
        f"- Analyzed Media: {summary['file']}",
        "",
        "## Technical Summary",
        f"- Duration: {summary['duration']}",
        f"- Resolution: {summary['resolution']}",
        f"- FPS: {summary['fps']}",
        f"- Audio Present: {summary['audio']}",
        "",
        "## Suggested Hooks",
        "- Hook 1",
        "- Hook 2",
        "- Hook 3",
        "",
        "## Suggested Angles",
        "- Problem-solving",
        "- Value-for-money",
        "- Review / worth-it",
        "",
        "## Suggested Clip Order",
        "- Open with strongest visual proof",
        "- Follow with product close-up",
        "- End with soft CTA",
        "",
        "## CTA Suggestions",
        "- Check orange bag",
        "- See latest price",
        "",
        "## CapCut Handoff",
        "- Trim pacing manually",
        "- Keep captions light and readable",
    ])
    path = analysis_dir / "analysis-result.md"
    path.write_text(body + "\n", encoding="utf-8")
    return path


def analyze_row_record(project_root: Path, row: dict[str, str]) -> Path:
    platform = detect_platform(row["Product Link"])
    product_dir = Path(row["Output Folder"]) if row.get("Output Folder") else resolve_product_folder(
        project_root / "output",
        platform,
        row["Shop Name"],
        row["Product Name"],
    )
    media_path = choose_analysis_media(product_dir)
    if media_path is None:
        raise RuntimeError(f"No downloaded media found for Record ID {row['Record ID']}. Run Download first.")
    result = write_analysis_result(product_dir, row, platform, media_path)
    row["Analysis Done"] = "TRUE"
    write_product_info(product_dir, row, platform=platform)
    return result
```

Extend CLI parsing:

```python
parser.add_argument("--analyze-record-id", default=None)
parser.add_argument("--download-and-analyze-record-id", default=None)
```

And in `main()` route those modes before the batch pending-row flow:

```python
if args.analyze_record_id:
    records = read_masterlist(masterlist)
    row = next(record for record in records if record["Record ID"] == args.analyze_record_id)
    analyze_row_record(project_root, row)
    write_masterlist(masterlist, records)
    return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m unittest .\AI - Shoppee Video v1.0\tests\test_analysis_workflow.py -v
python -m unittest .\AI - Shoppee Video v1.0\tests\test_process_shopee_video.py -v
```

Expected:
- analysis-only tests pass
- no regression in process tests

- [ ] **Step 5: Commit**

```powershell
git add -- "AI - Shoppee Video v1.0/scripts/process_shopee_video.py" "AI - Shoppee Video v1.0/tests/test_analysis_workflow.py" "AI - Shoppee Video v1.0/tests/test_process_shopee_video.py"
git commit -m "feat: add analysis result generation"
```

---

### Task 4: Wire The Frontend Analyze Actions And Record-ID Table Flow

**Files:**
- Modify: `AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py`
- Modify: `AI - Shoppee Video v1.0/scripts/run_shopee_video_workflow.ps1`
- Modify: `AI - Shoppee Video v1.0/tests/test_shoppee_video_frontend.py`

- [ ] **Step 1: Write the failing frontend tests**

Extend `AI - Shoppee Video v1.0/tests/test_shoppee_video_frontend.py`:

```python
def test_upsert_masterlist_row_updates_by_record_id_when_present(self):
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
        path = Path(tmp) / "master.csv"
        first_row, saved = upsert_masterlist_row(path, {
            "Record ID": "ASV-0000001",
            "Date": "2026-04-27",
            "Product Link": "https://shopee.com.my/product/1/2",
            "Product Name": "Kettle",
            "Shop Name": "Electrova",
        })
        second_row, updated = upsert_masterlist_row(path, {
            "Record ID": "ASV-0000001",
            "Date": "2026-04-27",
            "Product Link": "https://shopee.com.my/product/1/2",
            "Product Name": "Kettle Updated",
            "Shop Name": "Electrova",
        })
        self.assertEqual(first_row, 2)
        self.assertEqual(second_row, 2)
        self.assertEqual(updated["Product Name"], "Kettle Updated")
```

Add an argument passthrough test:

```python
def test_run_workflow_can_target_analysis_record_id(self):
    command = build_workflow_command(Path("project"), analyze_record_id="ASV-0000001")
    self.assertIn("--analyze-record-id", command)
    self.assertIn("ASV-0000001", command)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest .\AI - Shoppee Video v1.0\tests\test_shoppee_video_frontend.py -v
```

Expected:
- failures because frontend helpers do not support record-ID updates or analysis commands

- [ ] **Step 3: Implement frontend actions and runner passthrough**

Refactor workflow command construction in `shoppee_video_frontend.py`:

```python
def build_workflow_command(
    project_root: Path,
    analyze_record_id: str | None = None,
    download_and_analyze_record_id: str | None = None,
) -> list[str]:
    runner = project_root / "scripts" / "run_shopee_video_workflow.ps1"
    command = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(runner),
        "-OpenOutput",
    ]
    if analyze_record_id:
        command += ["-AnalyzeRecordId", analyze_record_id]
    if download_and_analyze_record_id:
        command += ["-DownloadAndAnalyzeRecordId", download_and_analyze_record_id]
    return command
```

Update `run_workflow()`:

```python
def run_workflow(project_root: Path, analyze_record_id: str | None = None, download_and_analyze_record_id: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        build_workflow_command(
            project_root,
            analyze_record_id=analyze_record_id,
            download_and_analyze_record_id=download_and_analyze_record_id,
        ),
        cwd=project_root.parent,
        capture_output=True,
        text=True,
        check=False,
    )
```

Add frontend routes inside `FrontendHandler.do_POST()`:

```python
if self.path == "/api/analyze":
    data = self.read_json()
    record_id = data.get("Record ID", "").strip()
    result = run_workflow(self.project_root, analyze_record_id=record_id)
    ...

if self.path == "/api/download-analyze":
    row_number, saved_row = upsert_masterlist_row(self.masterlist_path, self.read_json())
    result = run_workflow(self.project_root, download_and_analyze_record_id=saved_row["Record ID"])
    ...
```

Extend the HTML:

```html
<button class="btn-primary" id="anBtn" style="background:#7c3aed">Analyze</button>
<button class="btn-danger" id="dlaBtn">Save &amp; Download &amp; Analyze</button>
```

And the table:

```html
<th>Record ID</th>
<th>Analysis</th>
```

With row action wiring:

```javascript
const payload = getPayload();
await api("/api/analyze", payload);
await api("/api/download-analyze", payload);
```

Update the PowerShell runner `AI - Shoppee Video v1.0/scripts/run_shopee_video_workflow.ps1`:

```powershell
param(
    [switch]$DryRun,
    [switch]$Force,
    [switch]$OpenOutput,
    [string]$AnalyzeRecordId,
    [string]$DownloadAndAnalyzeRecordId
)

if ($AnalyzeRecordId) {
    $ArgsList += @("--analyze-record-id", $AnalyzeRecordId)
}

if ($DownloadAndAnalyzeRecordId) {
    $ArgsList += @("--download-and-analyze-record-id", $DownloadAndAnalyzeRecordId)
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m unittest .\AI - Shoppee Video v1.0\tests\test_shoppee_video_frontend.py -v
```

Expected:
- record-ID frontend tests pass
- analysis action command-building test passes

- [ ] **Step 5: Commit**

```powershell
git add -- "AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py" "AI - Shoppee Video v1.0/scripts/run_shopee_video_workflow.ps1" "AI - Shoppee Video v1.0/tests/test_shoppee_video_frontend.py"
git commit -m "feat: add analyze actions to frontend"
```

---

### Task 5: Add TikTok Public Video Collection Support

**Files:**
- Modify: `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
- Modify: `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`
- Modify: `AI - Shoppee Video v1.0/tests/test_analysis_workflow.py`

- [ ] **Step 1: Write the failing TikTok tests**

Add tests to `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`:

```python
def test_detect_platform_identifies_public_tiktok_video(self):
    self.assertEqual(
        detect_platform("https://www.tiktok.com/@shopdemo/video/7490123456789012345"),
        "TikTok",
    )


def test_record_prefix_for_public_tiktok_video(self):
    self.assertEqual(
        record_prefix_for_url("https://www.tiktok.com/@shopdemo/video/7490123456789012345"),
        "ATV",
    )


def test_invalid_tiktok_path_is_not_supported_video_url(self):
    self.assertFalse(is_tiktok_video_url("https://www.tiktok.com/@shopdemo"))
```

Add a workflow test in `AI - Shoppee Video v1.0/tests/test_analysis_workflow.py`:

```python
def test_download_and_analyze_tiktok_row_uses_tiktok_folder(self):
    row = {
        "Record ID": "ATV-0000001",
        "Product Link": "https://www.tiktok.com/@shopdemo/video/7490123456789012345",
        "Product Name": "Steam Iron",
        "Shop Name": "Electrova",
        "Source Type": "Auto",
        "Status": "Pending",
        "Done": "FALSE",
        "Analysis Done": "FALSE",
        "Notes": "",
        "Output Folder": "",
        "Output File": "",
    }
    folder = resolve_product_folder(Path("output"), "TikTok", row["Shop Name"], row["Product Name"])
    self.assertIn(str(Path("output") / "TikTok" / "Electrova"), str(folder))
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest .\AI - Shoppee Video v1.0\tests\test_process_shopee_video.py -v
python -m unittest .\AI - Shoppee Video v1.0\tests\test_analysis_workflow.py -v
```

Expected:
- failures for missing TikTok URL classifier support

- [ ] **Step 3: Implement TikTok public-video support in the existing collection flow**

Keep the integration shallow and reuse yt-dlp first:

```python
def is_tiktok_video_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return host.endswith("tiktok.com") and "/video/" in parsed.path


def collect_media(row: MasterRow, raw_dir: Path) -> list[Path]:
    link = row.product_link.strip()
    local_path = Path(link)
    if local_path.exists() and local_path.is_file():
        return [copy_local_media(local_path, raw_dir)]

    if is_direct_media_url(link):
        return [download_url(link, raw_dir, fallback_name=f"row-{row.row_number}")]

    if is_tiktok_video_url(link):
        return download_with_ytdlp(link, raw_dir)

    ytdlp_files = download_with_ytdlp(link, raw_dir)
    if ytdlp_files:
        return ytdlp_files

    media_urls = discover_media_urls(link)
    ...
```

Reject unsupported TikTok shapes with a clear message:

```python
def no_media_message(url: str) -> str:
    if is_shopee_url(url):
        return "Shopee page did not expose downloadable product media; use an approved seller media/direct file link"
    if "tiktok.com" in urlparse(url).netloc.lower() and not is_tiktok_video_url(url):
        return "TikTok link must be a public single video URL"
    return "No downloadable media found"
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m unittest .\AI - Shoppee Video v1.0\tests\test_process_shopee_video.py -v
python -m unittest .\AI - Shoppee Video v1.0\tests\test_analysis_workflow.py -v
```

Expected:
- TikTok unit tests pass
- no Shopee regressions

- [ ] **Step 5: Commit**

```powershell
git add -- "AI - Shoppee Video v1.0/scripts/process_shopee_video.py" "AI - Shoppee Video v1.0/tests/test_process_shopee_video.py" "AI - Shoppee Video v1.0/tests/test_analysis_workflow.py"
git commit -m "feat: add public tiktok video support"
```

---

### Task 6: Run Full Verification And Update Project Notes

**Files:**
- Modify: `AI - Video Workflow/AI - Shoppee Video v1.0.md`
- Modify: `AI - Video Workflow/Shopee Link and Media Analysis Workflow.md`
- Modify: `AI - Video Workflow/AI - Shoppee Video Analysis and TikTok Design.md`

- [ ] **Step 1: Add/update verification notes in project markdown**

Append the implementation result to the project notes with:

```markdown
## Analysis And TikTok Upgrade - 2026-04-27

- Added `Record ID` as first masterlist column.
- Added `Analysis Done` tracking.
- Added `product-info.md` creation on save.
- Added `Analyze` and `Save + Download + Analyze`.
- Added public TikTok single-video URL support.
- Changed output folder grouping to `output/<Platform>/<Shop Name>/<Product Name>/`.
```

- [ ] **Step 2: Run the full test suite**

Run:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v
```

Expected:
- all tests pass

- [ ] **Step 3: Run manual workflow verification**

Run dry-run first:

```powershell
powershell -ExecutionPolicy Bypass -File '.\AI - Shoppee Video v1.0\scripts\run_shopee_video_workflow.ps1' -DryRun
```

Then manually verify:

1. `Save` creates `product-info.md`
2. `Analyze` on a downloaded row creates `analysis-result.md`
3. `Save + Download + Analyze` runs end to end
4. public TikTok video URL saves under `output/TikTok/<Shop>/<Product>/`

- [ ] **Step 4: Commit**

```powershell
git add -- "AI - Video Workflow/AI - Shoppee Video v1.0.md" "AI - Video Workflow/Shopee Link and Media Analysis Workflow.md" "AI - Video Workflow/AI - Shoppee Video Analysis and TikTok Design.md"
git commit -m "docs: record analysis and tiktok implementation"
```

