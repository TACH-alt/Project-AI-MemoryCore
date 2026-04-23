# AI - Shoppee Video v1.x Future Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add private-network frontend access, improve the video render pipeline so it preserves quality and audio, and create a clean handoff path into CapCut or another editor.

**Architecture:** Keep the current local-first workflow, but separate three concerns: frontend serving, render modes, and editor export/handoff. The current all-in-one render path should become a configurable pipeline with a light default mode and an optional heavier vertical composition mode.

**Tech Stack:** Python, PowerShell, FFmpeg/ffprobe, CSV/XLSM sync, local HTML frontend, optional CapCut-compatible export folder structure.

---

## Scope And Constraints

### In Scope

- Serve the frontend inside the home/private network.
- Preserve source audio when editing videos.
- Add lighter edit modes so already-good raw videos are not over-processed.
- Add export/handoff files so Legend can continue work in CapCut or another editor.

### Not In Scope

- Public internet hosting with home-network exposure by default.
- Any bypass of Shopee login, anti-bot, DRM, or restricted media protections.
- A direct supported CapCut project API integration unless a documented import path is found later.

### File Map

- Modify: `AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py`
- Modify: `AI - Shoppee Video v1.0/scripts/start_shoppee_video_frontend.ps1`
- Modify: `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
- Modify: `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`
- Modify: `AI - Shoppee Video v1.0/tests/test_shoppee_video_frontend.py`
- Create: `AI - Shoppee Video v1.0/output/<product-folder>/handoff/README.txt`
- Create: `AI - Shoppee Video v1.0/output/<product-folder>/handoff/project.json`
- Create: `AI - Video Workflow/AI - Shoppee Video Future Improvements.md`

---

### Task 1: Private-Network Frontend Access

**Files:**
- Modify: `AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py`
- Modify: `AI - Shoppee Video v1.0/scripts/start_shoppee_video_frontend.ps1`
- Test: `AI - Shoppee Video v1.0/tests/test_shoppee_video_frontend.py`

- [x] **Step 1: Write the failing test**

```python
def test_default_frontend_host_is_localhost():
    args = parse_args([])
    assert args.host == "127.0.0.1"


def test_build_access_urls_for_lan_binding_includes_localhost_and_lan():
    assert build_access_urls("0.0.0.0", 8765, "192.168.0.10") == [
        "http://127.0.0.1:8765/",
        "http://192.168.0.10:8765/",
    ]
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -p 'test_shoppee_video_frontend.py' -v`

Expected: FAIL because `build_access_urls` does not exist yet.

- [x] **Step 3: Write minimal implementation**

```python
def build_access_urls(host: str, port: int, local_ip: str | None = None) -> list[str]:
    if host == "0.0.0.0":
        urls = [f"http://127.0.0.1:{port}/"]
        if local_ip and local_ip != "127.0.0.1":
            urls.append(f"http://{local_ip}:{port}/")
        return urls
    return [f"http://{host}:{port}/"]
```

```powershell
param(
    [int]$Port = 8765,
    [switch]$Lan
)

$Args = @($Frontend, "--project-root", $ProjectRoot, "--port", $Port)
if ($Lan) {
    $Args += @("--host", "0.0.0.0")
}

& $Python.Source @Args
```

- [x] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -p 'test_shoppee_video_frontend.py' -v`

Expected: PASS.

- [x] **Step 5: Manual verification**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File '.\AI - Shoppee Video v1.0\scripts\start_shoppee_video_frontend.ps1' -Lan
```

Expected:

- Console prints `http://127.0.0.1:8765/`
- Console also prints a home-network URL such as `http://192.168.x.x:8765/`
- Phone or another device on the same Wi-Fi can open that LAN URL

Actual verification:

```text
AI - Shoppee Video v1.0 frontend:
  http://127.0.0.1:8766/
  http://10.10.10.5:8766/
```

- [x] **Step 6: Commit**

```bash
git add "AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py" "AI - Shoppee Video v1.0/scripts/start_shoppee_video_frontend.ps1" "AI - Shoppee Video v1.0/tests/test_shoppee_video_frontend.py"
git commit -m "feat: allow shopee frontend on private network"
```

---

### Task 2: Lighter Video Editing With Audio Preservation

**Files:**
- Modify: `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
- Test: `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_build_ffmpeg_command_preserves_audio_for_video_inputs():
    command = build_ffmpeg_command("ffmpeg", Path("raw.mp4"), Path("edited.mp4"), "Shop - Product", mode="light")
    assert "-map" in command
    assert "0:a?" in command
    assert "-c:a" in command


def test_render_mode_defaults_to_light_for_videos():
    row = {"Source Type": "Auto", "Notes": "", "Product Link": "https://example.com/video.mp4"}
    assert choose_render_mode(row, Path("raw.mp4")) == "light"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -p 'test_process_shopee_video.py' -v`

Expected: FAIL because render modes and audio mapping do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
def choose_render_mode(record: dict[str, str], raw_path: Path) -> str:
    if raw_path.suffix.lower() in IMAGE_EXTENSIONS:
        return "vertical-blur"
    return "light"
```

```python
if mode == "light":
    filter_graph = (
        "[0:v]scale=1080:1080:force_original_aspect_ratio=decrease,"
        "pad=1080:1080:(ow-iw)/2:(oh-ih)/2:white,"
        "drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='{text}':"
        "x=(w-text_w)/2:y=h-110:fontsize=42:fontcolor=white:"
        "box=1:boxcolor=black@0.45:boxborderw=18[v]"
    )
    audio_args = ["-map", "0:a?", "-c:a", "aac", "-b:a", "128k"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -p 'test_process_shopee_video.py' -v`

Expected: PASS.

- [ ] **Step 5: Manual verification**

Run:

```powershell
python '.\AI - Shoppee Video v1.0\scripts\process_shopee_video.py' --project-root '.\AI - Shoppee Video v1.0' --force
```

Expected:

- Edited output keeps audio when source video has audio
- Caption is smaller and less intrusive
- Square source is not over-blurred into a full-height frame unless explicitly requested

- [ ] **Step 6: Commit**

```bash
git add "AI - Shoppee Video v1.0/scripts/process_shopee_video.py" "AI - Shoppee Video v1.0/tests/test_process_shopee_video.py"
git commit -m "feat: add lighter render mode and preserve audio"
```

---

### Task 3: Editor Handoff For CapCut Or Another Video Editor

**Files:**
- Modify: `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`
- Create: `AI - Shoppee Video v1.0/output/<product-folder>/handoff/README.txt`
- Create: `AI - Shoppee Video v1.0/output/<product-folder>/handoff/project.json`
- Test: `AI - Shoppee Video v1.0/tests/test_process_shopee_video.py`

- [ ] **Step 1: Write the failing test**

```python
def test_create_editor_handoff_writes_manifest():
    create_editor_handoff(
        product_folder=Path("output/Product-Shop"),
        raw_files=[Path("raw/demo.mp4")],
        edited_files=[Path("edited/demo_new.mp4")],
        caption="Shop - Product",
    )
    assert (Path("output/Product-Shop/handoff/project.json")).exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -p 'test_process_shopee_video.py' -v`

Expected: FAIL because the handoff manifest does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
payload = {
    "product_folder": str(product_folder),
    "raw_files": [str(path) for path in raw_files],
    "edited_files": [str(path) for path in edited_files],
    "caption": caption,
    "recommended_editor": "CapCut",
    "suggested_actions": [
        "trim",
        "replace caption style",
        "add hook voiceover",
        "add music",
    ],
}
```

```text
README.txt

Open the raw or edited clip in CapCut.
Recommended next edits:
1. Trim intro and ending
2. Replace caption style if needed
3. Add hook voiceover or music
4. Export final platform version
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s '.\AI - Shoppee Video v1.0\tests' -p 'test_process_shopee_video.py' -v`

Expected: PASS.

- [ ] **Step 5: Manual verification**

Expected:

- Every processed product folder contains a `handoff` subfolder
- `project.json` contains the raw path, edited path, and caption text
- Legend can open the folder and import the raw or edited clip into CapCut manually

- [ ] **Step 6: Commit**

```bash
git add "AI - Shoppee Video v1.0/scripts/process_shopee_video.py" "AI - Shoppee Video v1.0/tests/test_process_shopee_video.py"
git commit -m "feat: add editor handoff export"
```

---

### Task 4: Project Documentation And Obsidian Sync

**Files:**
- Create: `AI - Video Workflow/AI - Shoppee Video Future Improvements.md`
- Modify: `AI - Video Workflow/AI - Shoppee Video v1.0.md`

- [ ] **Step 1: Write the documentation**

Include:

- What can be done now:
  - private-network hosting
  - lighter edit mode
  - audio preservation
  - editor handoff
- What cannot be guaranteed:
  - short Shopee redirects
  - direct CapCut API project injection
  - public hosting by default

- [ ] **Step 2: Save and mirror to Obsidian**

Expected:

- `AI - Video Workflow/AI - Shoppee Video Future Improvements.md` exists
- mirrored into `C:\Users\Legend\Desktop\Obsidian\Legendary\05-Projects\AI - Video Workflow\`

- [ ] **Step 3: Commit**

```bash
git add "AI - Video Workflow/AI - Shoppee Video Future Improvements.md" "AI - Video Workflow/AI - Shoppee Video v1.0.md"
git commit -m "docs: add shopee video future improvements plan"
```

---

## Self-Review

### Spec Coverage

- Home/private-network access: covered by Task 1.
- Better editing/upscale decisions: covered by Task 2.
- CapCut or editor customization path: covered by Task 3.
- Documentation and Obsidian sync: covered by Task 4.

### Placeholder Scan

- No `TBD`, `TODO`, or unspecified file paths remain.
- Commands and target files are explicit.

### Type Consistency

- Planned helper names are consistent across tasks:
  - `lan_access_url`
  - `choose_render_mode`
  - `create_editor_handoff`

Plan complete and saved to `docs/superpowers/plans/2026-04-23-ai-shoppee-video-v1-future-improvements.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
