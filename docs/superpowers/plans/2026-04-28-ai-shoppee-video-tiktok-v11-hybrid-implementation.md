# AI - Shoppee Video TikTok v1.1 Hybrid Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade TikTok handling in `AI - Shoppee Video v1.0` so public TikTok posts are classified as true video vs photo-mode, downloaded through a typed media-bundle flow, rendered into better photo-mode slideshow outputs, and surfaced more clearly in the frontend.

**Architecture:** Keep the current Python orchestration and FFmpeg renderer. Extend `process_shopee_video.py` with a typed TikTok extraction model and a bundle-first download flow, then upgrade the photo-mode render lane and add lightweight frontend clarity without changing the masterlist schema again.

**Tech Stack:** Python 3.14, existing `yt_dlp` path, `urllib`, FFmpeg/FFprobe, CSV/XLSM sync, local Python frontend in `shoppee_video_frontend.py`, `unittest`.

---

## File Structure

### Existing files to modify

- `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
  - Own TikTok URL normalization, typed extraction, bundle download, photo-mode render behavior, row notes/status wording, and analysis metadata updates.
- `AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py`
  - Own lightweight UI visibility for TikTok result type and media summary after rows are loaded or processed.
- `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`
  - Own extraction, bundle, rerun, and render behavior tests.
- `AI - Shoppee Video v1.0/tests/test_shoppee_video_frontend.py`
  - Own frontend summary/status behavior tests.
- `AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.csv`
  - Use only as a live smoke-test artifact, not for schema changes.
- `AI - Video Workflow/AI - Shoppee Video v1.0.md`
  - Document implementation result and verification.
- `AI - Video Workflow/AI - Shoppee Video Analysis and TikTok Design.md`
  - Add implementation result for v1.1 when complete.
- `daily-diary/current/2026-04-28.md`
  - Save implementation checkpoint.
- `main/current-session.md`
  - Save current state checkpoint.
- `main/main-memory.md`
  - Save milestone memory.

### No new code files required

This plan deliberately keeps the implementation inside the existing TikTok/renderer/frontend modules to avoid unnecessary subsystem churn.

---

### Task 1: Expand TikTok URL support and typed post classification

**Files:**
- Modify: `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
- Test: `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`

- [ ] **Step 1: Write failing tests for TikTok `/photo/` support and explicit post typing**

Add tests near the existing TikTok helpers:

```python
    def test_tiktok_url_detector_accepts_public_photo_posts(self):
        self.assertTrue(
            is_tiktok_video_url("https://www.tiktok.com/@shopdemo/photo/7490123456789012345")
        )

    def test_tiktok_post_type_uses_video_when_direct_stream_exists(self):
        body = """
        <script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">
        {"__DEFAULT_SCOPE__":{"webapp.video-detail":{"itemInfo":{"itemStruct":{
            "id":"7490123456789012345",
            "video":{"playAddr":"https://cdn.example.com/play.mp4","downloadAddr":"https://cdn.example.com/download.mp4"},
            "music":{"playUrl":"https://cdn.example.com/music.m4a"}
        }}}}}
        </script>
        """
        bundle = extract_tiktok_media_bundle_from_html(
            "https://www.tiktok.com/@shopdemo/video/7490123456789012345",
            body,
        )
        self.assertEqual(bundle["post_type"], "video")

    def test_tiktok_post_type_uses_photo_mode_when_only_images_exist(self):
        body = """
        <script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">
        {"__DEFAULT_SCOPE__":{"webapp.video-detail":{"itemInfo":{"itemStruct":{
            "id":"7490123456789012345",
            "video":{"playAddr":"","downloadAddr":"","originCover":"https://cdn.example.com/origin.image"},
            "music":{"playUrl":"https://cdn.example.com/music.m4a"}
        }}}}}
        </script>
        """
        bundle = extract_tiktok_media_bundle_from_html(
            "https://www.tiktok.com/@shopdemo/photo/7490123456789012345",
            body,
        )
        self.assertEqual(bundle["post_type"], "photo_mode")

    def test_tiktok_post_type_is_unknown_when_no_media_bundle_exists(self):
        body = """
        <script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">
        {"__DEFAULT_SCOPE__":{"webapp.video-detail":{"itemInfo":{"itemStruct":{
            "id":"7490123456789012345",
            "video":{"playAddr":"","downloadAddr":""},
            "music":{"playUrl":""}
        }}}}}
        </script>
        """
        bundle = extract_tiktok_media_bundle_from_html(
            "https://www.tiktok.com/@shopdemo/video/7490123456789012345",
            body,
        )
        self.assertEqual(bundle["post_type"], "unknown")
```

- [ ] **Step 2: Run tests to verify they fail for the right reasons**

Run:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -p 'test_process_shopee_video.py' -v
```

Expected:

- `/photo/` detection test fails
- bundle tests fail because `post_type` is missing or still uses old `kind` semantics

- [ ] **Step 3: Implement typed TikTok URL and bundle classification**

Update `process_shopee_video.py` so TikTok public single-post detection accepts `/photo/` and the structured extractor returns `post_type`.

Implementation shape:

```python
def is_tiktok_video_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if not host.endswith("tiktok.com"):
        return False
    if host in {"vt.tiktok.com", "vm.tiktok.com"}:
        return True
    path = parsed.path
    return "/video/" in path or "/photo/" in path


def tiktok_post_id_from_url(url: str) -> str | None:
    match = re.search(r"/(?:video|photo)/(\d+)", urlparse(url).path)
    return match.group(1) if match else None


def extract_tiktok_media_bundle_from_html(page_url: str, body: str) -> dict[str, object] | None:
    ...
    post_type = "unknown"
    if video_urls:
        post_type = "video"
    elif image_urls:
        post_type = "photo_mode"
    return {
        "platform": "TikTok",
        "post_type": post_type,
        "canonical_url": page_url,
        "video_id": video_id,
        "video_urls": video_urls,
        "image_urls": image_urls,
        "audio_url": audio_url,
        "caption_text": caption_text,
        "author_name": author_name,
        "notes": notes,
    }
```

- [ ] **Step 4: Run tests to verify the extractor passes**

Run:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -p 'test_process_shopee_video.py' -v
```

Expected:

- new TikTok typing tests pass
- no previously green TikTok helper test regresses

- [ ] **Step 5: Commit**

```bash
git add "AI - Shoppee Video v1.0/scripts/process_shopee_video.py" "AI - Shoppee Video v1.0/tests/test_process_shopee_video.py"
git commit -m "feat: classify tiktok posts by media type"
```

---

### Task 2: Build bundle-first TikTok download flow

**Files:**
- Modify: `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
- Test: `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`

- [ ] **Step 1: Write failing tests for bundle-first download behavior**

Add tests for:

```python
    def test_download_tiktok_bundle_prefers_direct_video_target(self):
        bundle = {
            "platform": "TikTok",
            "post_type": "video",
            "video_id": "7490123456789012345",
            "video_urls": ["https://cdn.example.com/video.mp4"],
            "image_urls": [],
            "audio_url": "",
        }
        ...
        self.assertEqual([path.name for path in media], ["7490123456789012345.mp4"])

    def test_download_tiktok_bundle_keeps_multiple_photo_assets_in_order(self):
        bundle = {
            "platform": "TikTok",
            "post_type": "photo_mode",
            "video_id": "7490123456789012345",
            "video_urls": [],
            "image_urls": [
                "https://cdn.example.com/one.jpeg",
                "https://cdn.example.com/two.jpeg",
                "https://cdn.example.com/three.jpeg",
            ],
            "audio_url": "https://cdn.example.com/music.m4a",
        }
        ...
        self.assertEqual(
            [path.name for path in media],
            ["7490123456789012345.jpg", "7490123456789012345-2.jpg", "7490123456789012345-3.jpg"],
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -p 'test_process_shopee_video.py' -v
```

Expected:

- direct-video bundle target naming fails
- multi-image ordering/count test fails if only one fallback image is retained

- [ ] **Step 3: Implement bundle-first TikTok download**

Refactor `download_with_ytdlp()` and `download_tiktok_bundle()` so:

- direct video bundle wins immediately
- image-only `yt-dlp` results trigger structured bundle promotion
- multi-image photo-mode bundles are preserved when available

Implementation shape:

```python
def download_tiktok_bundle(bundle: dict[str, object], raw_dir: Path) -> list[Path]:
    post_type = str(bundle.get("post_type", "")).strip().lower()
    video_id = str(bundle.get("video_id", "")).strip() or "tiktok"

    if post_type == "video":
        for media_url in bundle.get("video_urls", []) or []:
            target = download_url(str(media_url), raw_dir, fallback_name=video_id)
            if target.suffix.lower() in VIDEO_EXTENSIONS:
                desired = raw_dir / f"{video_id}{target.suffix.lower()}"
                if target != desired:
                    desired.unlink(missing_ok=True)
                    target.rename(desired)
                    target = desired
                return [target]
        return []

    if post_type == "photo_mode":
        image_urls = list(bundle.get("image_urls", []) or [])
        media_files = []
        for index, media_url in enumerate(image_urls, start=1):
            fallback_name = video_id if index == 1 else f"{video_id}-{index}"
            target = download_url(str(media_url), raw_dir, fallback_name=fallback_name)
            if target.suffix.lower() == ".image":
                target = normalize_downloaded_image_artifact(target)
            desired = raw_dir / safe_filename(f"{fallback_name}{target.suffix.lower()}")
            if target != desired:
                desired.unlink(missing_ok=True)
                target.rename(desired)
                target = desired
            if target.suffix.lower() in IMAGE_EXTENSIONS:
                media_files.append(target)
        ...
        return media_files
```

- [ ] **Step 4: Run tests to verify bundle download passes**

Run:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -p 'test_process_shopee_video.py' -v
```

Expected:

- new direct-video and multi-image bundle tests pass
- earlier audio-extension and rerun tests stay green

- [ ] **Step 5: Commit**

```bash
git add "AI - Shoppee Video v1.0/scripts/process_shopee_video.py" "AI - Shoppee Video v1.0/tests/test_process_shopee_video.py"
git commit -m "feat: add bundle-first tiktok downloads"
```

---

### Task 3: Upgrade photo-mode rendering from one-image fallback to slideshow render

**Files:**
- Modify: `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
- Test: `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`

- [ ] **Step 1: Write failing tests for photo-mode slideshow grouping**

Add tests covering grouping and message wording:

```python
    def test_group_photo_mode_sequence_collects_ordered_images(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            raw_dir = Path(tmp) / "raw"
            raw_dir.mkdir()
            for name in ["7490.jpg", "7490-2.jpg", "7490-3.jpg"]:
                (raw_dir / name).write_bytes(b"img")
            files = group_photo_mode_images(raw_dir / "7490.jpg", raw_dir)
            self.assertEqual([path.name for path in files], ["7490.jpg", "7490-2.jpg", "7490-3.jpg"])

    def test_photo_mode_status_message_mentions_slideshow(self):
        message = build_photo_mode_status_message(image_count=3, edited_count=1, has_audio=True)
        self.assertEqual(
            message,
            "Downloaded 4 media file(s); edited 1 slideshow video file(s) (photo-mode post with background audio)",
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -p 'test_process_shopee_video.py' -v
```

Expected:

- grouping helper is undefined
- status-message helper is undefined

- [ ] **Step 3: Implement grouped photo-mode rendering with a single final MP4**

Keep FFmpeg and the current render lane, but add a dedicated slideshow path.

Implementation shape:

```python
def group_photo_mode_images(seed_image: Path, raw_dir: Path) -> list[Path]:
    stem = seed_image.stem.split("-")[0]
    ordered = []
    for candidate in sorted(raw_dir.iterdir()):
        if not candidate.is_file() or candidate.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if candidate.stem == stem or candidate.stem.startswith(f"{stem}-"):
            ordered.append(candidate)
    return ordered or [seed_image]


def build_photo_mode_status_message(image_count: int, edited_count: int, has_audio: bool) -> str:
    raw_count = image_count + (1 if has_audio else 0)
    note = " (photo-mode post with background audio)" if has_audio else " (photo-mode post)"
    return f"Downloaded {raw_count} media file(s); edited {edited_count} slideshow video file(s){note}"
```

Then update the row-processing path so:

- grouped photo-mode images render into one `edited/<video-id>_new.mp4`
- ordinary video files still render one-to-one

Keep the first implementation simple:

- hard cuts or very light fades
- fixed short per-image duration
- total duration constrained by image count and optional audio

- [ ] **Step 4: Run tests and a live smoke test**

Run unit tests:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v
```

Then run a live photo-mode row:

```powershell
python '.\AI - Shoppee Video v1.0\scripts\process_shopee_video.py' --project-root '.\AI - Shoppee Video v1.0' --masterlist '.\AI - Shoppee Video v1.0\masterlist\List of Link Shopee VIdeo.csv' --download-and-analyze-record-id ATV-0000003
```

Expected:

- tests pass
- one final edited MP4 for the row
- notes mention `slideshow video file(s)`

- [ ] **Step 5: Commit**

```bash
git add "AI - Shoppee Video v1.0/scripts/process_shopee_video.py" "AI - Shoppee Video v1.0/tests/test_process_shopee_video.py" "AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.csv"
git commit -m "feat: render tiktok photo mode as slideshow"
```

---

### Task 4: Add frontend result-type and media-summary visibility

**Files:**
- Modify: `AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py`
- Test: `AI - Shoppee Video v1.0/tests/test_shoppee_video_frontend.py`

- [ ] **Step 1: Write failing frontend tests for TikTok result summary**

Add tests like:

```python
    def test_frontend_row_summary_detects_photo_mode_from_notes(self):
        row = {
            "Record ID": "ATV-0000003",
            "Product Link": "https://vt.tiktok.com/ZS9ST61G4/",
            "Notes": "Downloaded 4 media file(s); edited 1 slideshow video file(s) (photo-mode post with background audio)",
            "Output Folder": r"C:\\demo\\output\\TikTok\\Bargain Purchase\\Massage Gaming Chair",
        }
        summary = build_frontend_media_summary(row)
        self.assertEqual(summary["post_type"], "Photo-mode Post")

    def test_frontend_row_summary_detects_video_post_from_notes(self):
        row = {
            "Record ID": "ATV-0000004",
            "Product Link": "https://www.tiktok.com/@shopdemo/video/7490123456789012345",
            "Notes": "Downloaded 1 media file(s); edited 1 video file(s) (video post)",
            "Output Folder": r"C:\\demo\\output\\TikTok\\ShopDemo\\Chair",
        }
        summary = build_frontend_media_summary(row)
        self.assertEqual(summary["post_type"], "Video Post")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -p 'test_shoppee_video_frontend.py' -v
```

Expected:

- summary helper is undefined

- [ ] **Step 3: Implement lightweight summary helpers and UI wiring**

Add a helper in `shoppee_video_frontend.py`:

```python
def build_frontend_media_summary(row: dict[str, str]) -> dict[str, str]:
    notes = (row.get("Notes", "") or "").lower()
    if "photo-mode post" in notes:
        post_type = "Photo-mode Post"
    elif "video post" in notes:
        post_type = "Video Post"
    elif "tiktok" in (row.get("Product Link", "") or "").lower():
        post_type = "Unknown TikTok Media"
    else:
        post_type = ""
    return {
        "post_type": post_type,
        "analysis_done": row.get("Analysis Done", "FALSE"),
        "output_file": row.get("Output File", ""),
    }
```

Then use that helper to:

- enrich the JSON returned for rows
- show a compact loaded-row summary block in the page
- display `Video Post` / `Photo-mode Post` when available

Keep the UI minimal. Do not add new buttons.

- [ ] **Step 4: Run tests and verify frontend still starts**

Run:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -p 'test_shoppee_video_frontend.py' -v
python '.\AI - Shoppee Video v1.0\scripts\shoppee_video_frontend.py' --host 127.0.0.1 --port 8767
```

Expected:

- frontend tests pass
- frontend starts without tracebacks on a spare port

- [ ] **Step 5: Commit**

```bash
git add "AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py" "AI - Shoppee Video v1.0/tests/test_shoppee_video_frontend.py"
git commit -m "feat: show tiktok result type in frontend"
```

---

### Task 5: Run final verification and update documentation

**Files:**
- Modify: `AI - Video Workflow/AI - Shoppee Video v1.0.md`
- Modify: `AI - Video Workflow/AI - Shoppee Video Analysis and TikTok Design.md`
- Modify: `daily-diary/current/2026-04-28.md`
- Modify: `main/current-session.md`
- Modify: `main/main-memory.md`
- Optional artifact updates: `AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.csv`, product output folder files

- [ ] **Step 1: Run the full verification suite**

Run:

```powershell
python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -v
```

Expected:

- entire test suite passes

- [ ] **Step 2: Run live smoke tests for three TikTok cases**

Run:

```powershell
python '.\AI - Shoppee Video v1.0\scripts\process_shopee_video.py' --project-root '.\AI - Shoppee Video v1.0' --masterlist '.\AI - Shoppee Video v1.0\masterlist\List of Link Shopee VIdeo.csv' --download-and-analyze-record-id ATV-0000001
python '.\AI - Shoppee Video v1.0\scripts\process_shopee_video.py' --project-root '.\AI - Shoppee Video v1.0' --masterlist '.\AI - Shoppee Video v1.0\masterlist\List of Link Shopee VIdeo.csv' --download-and-analyze-record-id ATV-0000002
python '.\AI - Shoppee Video v1.0\scripts\process_shopee_video.py' --project-root '.\AI - Shoppee Video v1.0' --masterlist '.\AI - Shoppee Video v1.0\masterlist\List of Link Shopee VIdeo.csv' --download-and-analyze-record-id ATV-0000003
```

Expected:

- no hard failures
- notes clearly distinguish slideshow/photo-mode behavior
- output folders end in one canonical edited MP4 per row

- [ ] **Step 3: Update project notes and memory**

Update the docs with:

- what changed in TikTok extraction
- whether `/photo/` support was exercised
- how slideshow output behaves
- final test count and smoke-test results

Minimum sections to add:

```markdown
## TikTok v1.1 Implementation Result - 2026-04-28

- Added typed TikTok post classification
- Added bundle-first download flow
- Upgraded photo-mode rendering to slideshow output
- Added frontend result-type visibility
- Verified with full tests and live smoke runs
```

- [ ] **Step 4: Mirror the updated markdown files into Obsidian**

Copy:

```powershell
Copy-Item 'AI - Video Workflow\AI - Shoppee Video v1.0.md' 'C:\Users\Legend\Desktop\Obsidian\Legendary\05-Projects\AI - Video Workflow\AI - Shoppee Video v1.0.md' -Force
Copy-Item 'AI - Video Workflow\AI - Shoppee Video Analysis and TikTok Design.md' 'C:\Users\Legend\Desktop\Obsidian\Legendary\05-Projects\AI - Video Workflow\AI - Shoppee Video Analysis and TikTok Design.md' -Force
Copy-Item 'daily-diary\current\2026-04-28.md' 'C:\Users\Legend\Desktop\Obsidian\Legendary\03-Daily-Notes\2026-04-28.md' -Force
Copy-Item 'main\current-session.md' 'C:\Users\Legend\Desktop\Obsidian\Legendary\01-Sessions\2026-04-28-001.md' -Force
```

- [ ] **Step 5: Commit final implementation state**

```bash
git add "AI - Shoppee Video v1.0" "AI - Video Workflow/AI - Shoppee Video v1.0.md" "AI - Video Workflow/AI - Shoppee Video Analysis and TikTok Design.md" "daily-diary/current/2026-04-28.md" "main/current-session.md" "main/main-memory.md"
git commit -m "feat: complete tiktok v1.1 hybrid workflow"
```

---

## Self-Review

### Spec coverage

- Supported TikTok link types: covered in Task 1
- Typed `video` / `photo_mode` / `unknown` model: covered in Task 1
- Bundle-first download flow: covered in Task 2
- Better photo-mode output: covered in Task 3
- Frontend clarity: covered in Task 4
- Verification and docs sync: covered in Task 5

### Placeholder scan

- No `TBD`, `TODO`, or “implement later” placeholders left in the tasks
- All code-changing steps include code snippets or concrete implementation shapes
- All test steps include runnable commands and expected results

### Type consistency

- Uses `post_type` consistently instead of mixing `kind` and `post_type`
- Uses `tiktok_post_id_from_url()` consistently for `/video/` and `/photo/`
- Keeps canonical output naming aligned with the spec
