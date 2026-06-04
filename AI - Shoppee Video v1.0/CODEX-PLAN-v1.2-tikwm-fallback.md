# Codex Implementation Plan: v1.2 — tikwm.com Fallback + Extraction Hardening

**Branch:** `codex/tiktok-v12-tikwm-fallback`  
**Base branch:** `main`  
**Target file:** `scripts/process_shopee_video.py`  
**Plan author:** Legend (via Claude)  
**Date:** 2026-04-30  
**Complexity:** Medium — additive only, no existing logic removed

---

## Objective

Strengthen the TikTok media extraction waterfall by adding `tikwm.com` as a **dedicated fallback API step** between the existing page-scrape and yt-dlp paths. When TikTok's WAF blocks the page HTML fetch (returning a bot-challenge page with no `itemStruct`), tikwm's API can still return `downloadAddr`, `imagePost`, and `music.playUrl` for the same video ID.

This change makes the pipeline resilient to WAF flaps without changing any working code path.

---

## Context for Codex

### Current extraction waterfall in `discover_tiktok_media_bundle(url)` (line ~827)

```
1. fetch_tiktok_html → extract_tiktok_media_bundle_from_html
2. build_tiktok_node_share_url → fetch_tiktok_json → build_tiktok_media_bundle
3. build_tiktok_id_lookup_url → fetch_tiktok_html (ID-based lookup)
4. discover_tiktok_media_bundle_from_ytdlp (yt-dlp --dump-single-json)
5. return last HTML parse result or None
```

### What tikwm is

`tikwm.com` exposes a free, no-auth JSON API:

```
GET https://www.tikwm.com/api/?url=<tiktok_url>
```

Response shape (success):
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "id": "7429642666880568594",
    "play": "https://...cdn.../play.mp4",
    "wmplay": "https://...cdn.../wmplay.mp4",
    "hdplay": "https://...cdn.../hdplay.mp4",
    "cover": "https://...cdn.../cover.jpg",
    "origin_cover": "https://...cdn.../origin_cover.jpg",
    "images": ["https://...cdn.../img1.jpg", "..."],
    "music": "https://...cdn.../music.mp3",
    "title": "...",
    "author": { "unique_id": "..." }
  }
}
```

- `code: 0` = success; anything else = failure / blocked
- `play` = watermark video URL  
- `hdplay` = HD watermark-free video URL (prefer this)  
- `images` = non-empty array for photo-mode carousels  
- `music` = background audio URL (always present if content exists)

### Mapping tikwm response → our bundle format

Our internal bundle dict shape (from `build_tiktok_media_bundle`):

```python
{
    "url": <canonical tiktok url>,
    "kind": "video" | "photo_mode" | "unknown",
    "post_type": "video" | "photo_mode" | "unknown",  # alias
    "video_urls": [<str>, ...],      # non-empty for video posts
    "image_urls": [<str>, ...],      # non-empty for photo_mode
    "audio_url": <str> | None,
    "video_id": <str>,
}
```

---

## Changes Required

### Change 1 — Add `fetch_tikwm_bundle(url)` function

**Location:** After `discover_tiktok_media_bundle_from_ytdlp` (around line 821) and before `discover_tiktok_media_bundle` (line 827).

**Function signature:**
```python
def fetch_tikwm_bundle(url: str) -> dict[str, object] | None:
```

**Implementation:**

```python
def fetch_tikwm_bundle(url: str) -> dict[str, object] | None:
    """Attempt to get TikTok media bundle from tikwm.com public API.

    tikwm.com exposes a free no-auth API that returns video/image CDN URLs.
    Returns a bundle dict compatible with download_tiktok_bundle(), or None on
    any failure (network error, non-zero code, missing data).

    API docs: https://www.tikwm.com/
    """
    import json as _json

    api_url = f"https://www.tikwm.com/api/?url={url}"
    try:
        with request_url(api_url) as response:
            raw = response.read()
    except Exception:
        return None

    try:
        payload = _json.loads(raw)
    except Exception:
        return None

    if not isinstance(payload, dict):
        return None
    if int(payload.get("code", -1)) != 0:
        return None

    data = payload.get("data")
    if not isinstance(data, dict):
        return None

    video_id = str(data.get("id") or "").strip()

    # Prefer hdplay (watermark-free HD) > play (watermarked) > wmplay
    video_url = (
        str(data.get("hdplay") or "").strip()
        or str(data.get("play") or "").strip()
        or str(data.get("wmplay") or "").strip()
    )

    images_raw = data.get("images") or []
    image_urls = [str(u).strip() for u in images_raw if str(u).strip()]

    audio_url = str(data.get("music") or "").strip() or None

    # Classify post type
    if image_urls:
        kind = "photo_mode"
    elif video_url:
        kind = "video"
    else:
        return None  # No usable media — don't return an empty bundle

    return {
        "url": url,
        "kind": kind,
        "post_type": kind,
        "video_urls": [video_url] if video_url and kind == "video" else [],
        "image_urls": image_urls,
        "audio_url": audio_url,
        "video_id": video_id,
    }
```

**Notes for Codex:**
- Use `request_url` (already imported, handles timeouts + headers) not `urllib.request.urlopen` directly
- `import json as _json` inside the function avoids adding a module-level import (json is stdlib, already available but this keeps the change contained)
- Do NOT use `requests` library — it is not a project dependency
- The function must be completely self-contained — no new module-level imports required

---

### Change 2 — Insert tikwm step into `discover_tiktok_media_bundle`

**Location:** `discover_tiktok_media_bundle` function (line ~827). Insert the tikwm call as **step 3b** — after the node/share URL attempt and before the ID-based page lookup.

**Current waterfall (annotated):**

```python
def discover_tiktok_media_bundle(url: str) -> dict[str, object] | None:
    canonical_url = canonicalize_tiktok_url(url)
    cookie_jar = CookieJar()

    # Step 1: page HTML scrape
    body = fetch_tiktok_html(canonical_url, cookie_jar)
    if body:
        bundle = extract_tiktok_media_bundle_from_html(canonical_url, body)
        if bundle and bundle.get("kind") != "unknown":
            return bundle

    # Step 2: node/share API
    node_share_url = build_tiktok_node_share_url(canonical_url)
    if node_share_url:
        payload = fetch_tiktok_json(node_share_url, cookie_jar)
        bundle = build_tiktok_media_bundle(payload or {}, canonical_url) if payload else None
        if bundle and bundle.get("kind") != "unknown":
            return bundle

    # ← INSERT tikwm step HERE (step 3b)

    # Step 3: ID-based page lookup
    id_lookup_url = build_tiktok_id_lookup_url(canonical_url)
    if id_lookup_url and id_lookup_url != canonical_url:
        fallback_body = fetch_tiktok_html(id_lookup_url, cookie_jar)
        if fallback_body:
            bundle = extract_tiktok_media_bundle_from_html(canonical_url, fallback_body)
            if bundle:
                return bundle

    # Step 4: yt-dlp metadata dump
    ytdlp_bundle = discover_tiktok_media_bundle_from_ytdlp(canonical_url)
    if ytdlp_bundle:
        return ytdlp_bundle

    if body:
        return extract_tiktok_media_bundle_from_html(canonical_url, body)
    return None
```

**Exact insertion — add these lines after the node/share block and before the ID-lookup block:**

```python
    # Step 3b: tikwm.com public API fallback
    tikwm_bundle = fetch_tikwm_bundle(canonical_url)
    if tikwm_bundle and tikwm_bundle.get("kind") != "unknown":
        return tikwm_bundle
```

**Result — updated waterfall:**

```
1. page HTML → itemStruct
2. node/share → itemStruct  
3. tikwm.com API → bundle  ← NEW
4. ID-based page lookup
5. yt-dlp --dump-single-json
6. return last HTML parse or None
```

---

### Change 3 — Add `TIKWM_API_TIMEOUT` constant (optional but recommended)

If `request_url` accepts a timeout parameter, pass `timeout=10` (seconds) to the tikwm call. If `request_url` does not accept a timeout, skip this — do NOT modify `request_url` or add a new timeout mechanism.

Check the signature of `request_url` first:
```python
# Look for: def request_url(url, ...) in process_shopee_video.py
```

If it accepts `timeout`:
```python
with request_url(api_url, timeout=10) as response:
```

If it does not accept `timeout`, leave the call as-is:
```python
with request_url(api_url) as response:
```

---

## Verification Steps

After implementing, Codex must verify the following before committing:

### Step 1 — Syntax check
```bash
python -m py_compile scripts/process_shopee_video.py && echo "OK"
```

### Step 2 — Unit test `fetch_tikwm_bundle` logic (offline)

Add a test in `tests/` or run inline:

```python
# Simulate a successful tikwm photo_mode response
fake_photo = {
    "code": 0,
    "msg": "success",
    "data": {
        "id": "7429642666880568594",
        "play": "",
        "hdplay": "",
        "images": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
        "music": "https://example.com/bg.mp3",
    }
}
# Expected: kind="photo_mode", image_urls has 2 items, audio_url set

fake_video = {
    "code": 0,
    "data": {
        "id": "9999",
        "hdplay": "https://example.com/video.mp4",
        "images": [],
        "music": "https://example.com/bg.mp3",
    }
}
# Expected: kind="video", video_urls=["https://example.com/video.mp4"]

fake_fail = {"code": -1, "msg": "error"}
# Expected: returns None

fake_empty = {"code": 0, "data": {"id": "x", "play": "", "hdplay": "", "images": [], "music": ""}}
# Expected: returns None (no usable media)
```

### Step 3 — Live smoke test (one URL)

Test with the confirmed photo-mode URL:
```
https://www.tiktok.com/@bargainpurchasesofficial/video/7429642666880568594
```

Expected: `fetch_tikwm_bundle` returns a bundle with `kind="photo_mode"` and `image_urls` non-empty.

```bash
python -c "
from scripts.process_shopee_video import fetch_tikwm_bundle
b = fetch_tikwm_bundle('https://www.tiktok.com/@bargainpurchasesofficial/video/7429642666880568594')
print('kind:', b.get('kind') if b else 'NONE')
print('images:', len(b.get('image_urls', [])) if b else 0)
print('audio:', bool(b.get('audio_url')) if b else False)
"
```

### Step 4 — Full pipeline smoke test (optional)

Run the existing smoke test on a photo-mode URL via the frontend or CLI and confirm the waterfall logs show tikwm being attempted before yt-dlp.

---

## Commit Format

```
feat: add tikwm.com API fallback to TikTok media bundle discovery

- New fetch_tikwm_bundle() function queries tikwm.com public API
- Inserted as step 3b in discover_tiktok_media_bundle() waterfall
- Sits between node/share attempt and ID-based page lookup
- Handles both video and photo_mode post types
- Returns None on any network or parse failure (safe fallback)
- No new dependencies: uses existing request_url() helper
```

---

## Out of Scope for This Change

Do NOT implement in this Codex run:

- User-Agent or cookie rotation (separate task)
- Exponential backoff / retry logic
- FastAPI endpoint or cloud deployment
- Any changes to `download_tiktok_bundle`, `find_background_audio`, or render logic
- Changes to frontend (`shoppee_video_frontend.py`)
- Changes to test infrastructure beyond the new function unit tests

---

## Reference

- tikwm API base: `https://www.tikwm.com/api/?url=<tiktok_url>`
- SnapTik analysis doc: `docs/SnapTik-Analysis.md`
- Current waterfall: `discover_tiktok_media_bundle` (~line 827)
- Bundle consumer: `download_tiktok_bundle` (~line 1136)
- Waterfall entry point: `download_with_ytdlp` (~line 985)

---

*Plan: Claude for Legend · Execute: ChatGPT Codex · Branch: codex/tiktok-v12-tikwm-fallback*
