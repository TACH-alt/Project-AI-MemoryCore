---
name: tiktok-media-extraction
description: Use when a TikTok affiliate workflow needs to tell apart true video posts from photo-mode posts, recover the best available media from public TikTok URLs, or debug why a downloader only returns audio, thumbnails, or inconsistent rerun artifacts.
---

# TikTok Media Extraction

## Overview

Public TikTok post URLs do not all behave like normal MP4 videos. Some are true video posts, some are photo-mode posts, and some expose only partial assets to standard download tools.

The rule: classify the post type first, then choose the extraction path that matches the evidence.

## When to Use

- `yt-dlp -F` only shows `audio`
- a TikTok URL "works" but produces an image-to-video output
- reruns create duplicate thumbnails or stale outputs
- you need to verify whether the problem is the site, the tool, or the workflow

Do not use this for private TikTok posts, login-gated content, or bypass work.

## Extraction Order

1. Try `yt-dlp` first for the public post URL.
2. If it returns a real video file, keep that path.
3. If it returns only images or audio, fetch the TikTok page and inspect structured payloads in this order:
   - `__UNIVERSAL_DATA_FOR_REHYDRATION__`
   - `__NEXT_DATA__`
   - `SIGI_STATE`
4. If page HTML is blocked or incomplete, try web fallbacks before giving up:
   - `https://www.tiktok.com/node/share/video/{username}/{video_id}`
   - `https://www.tiktok.com/@tiktok/video/{video_id}` as an ID-based page lookup
   - `yt-dlp --dump-single-json --skip-download` as a metadata fallback
5. Classify the post:
   - `video`: non-empty `video.downloadAddr` or `video.playAddr`
   - `photo_mode`: no direct video URL, but image cover/origin assets and music URL exist
6. For photo-mode:
   - prefer `imagePost` assets if present
   - otherwise keep the best ordered image assets available from thumbnails/covers
   - keep background audio separately and merge it during render

## Practical Checks

- `python -m yt_dlp -F "<url>"`:
  - real video posts normally show video formats
  - photo-mode posts often show only `audio`
- page-data fallback:
  - parse `webapp.video-detail -> itemInfo -> itemStruct`
  - check `video.downloadAddr`, `video.playAddr`, `video.originCover`, `video.zoomCover`, `music.playUrl`
- node/share fallback:
  - expect `statusCode == 0`
  - parse `itemInfo.itemStruct`
- `yt-dlp --dump-single-json` fallback:
  - if `formats` include any entry with `vcodec != none`, prefer those video URLs
  - if `formats` are audio-only but `thumbnails` exist, treat as `photo_mode`

## Rerun Discipline

- Keep canonical filenames stable:
  - first image: `<video_id>.jpg`
  - next images: `<video_id>-2.jpg`, `<video_id>-3.jpg`
  - audio: `background.<ext>`
- Before a photo-mode rerun:
  - remove stale raw image files
  - clear stale edited MP4s
- Verify that any returned media paths still exist on disk after rename logic

## Verification

- Confirm the raw folder contains the expected image and `background.*`
- Confirm the edited MP4 exists
- Confirm audio with:

```powershell
ffprobe -v quiet -show_streams -select_streams a <output.mp4>
```

- If the page itself exposes no video URLs, do not describe the result as a failed video extraction. It is a photo-mode post.

## v1.1 Upgrade Notes

- Public TikTok handling now treats `/video/` and `/photo/` as first-class post shapes.
- Prefer a typed bundle:
  - `post_type = video`
  - `post_type = photo_mode`
  - `post_type = unknown`
- Photo-mode outputs should be described honestly:
  - ordered image assets
  - optional `background.*` audio
  - one slideshow MP4 output
- For live verification, avoid running multiple TikTok smoke tests in parallel against the same masterlist because CSV/XLSM writes can race.

## Critical: `/video/` URLs Are Not Always Video Posts

Do NOT classify a TikTok post as a true video post based on the URL path alone.

TikTok uses `/video/<id>` in the URL for both real video posts and photo-mode carousel posts. Confirmed live examples where `/video/` URLs were photo-mode:

- `https://vt.tiktok.com/ZS9hjGD43/` → resolves to `/video/7129084799339351323` → photo-mode
- `https://www.tiktok.com/@bargainpurchasesofficial/video/7429642666880568594` → photo-mode

Always classify by inspecting `itemStruct` from `__UNIVERSAL_DATA_FOR_REHYDRATION__`:

- If `video.downloadAddr` or `video.playAddr` is non-empty → `video`
- If both are empty but image assets or `music.playUrl` exist → `photo_mode`
- Otherwise → `unknown`

`yt-dlp -F` showing only an `audio` format is a strong signal the post is photo-mode, but confirm via page data before concluding.

## WAF and Reality Check

TikTok’s web app can return a WAF "Please wait..." challenge page instead of usable metadata. When that happens:

- plain HTML scraping may return no `itemStruct`
- `node/share/video/...` can return `403 Forbidden`
- browser impersonation alone may still fail

This does **not** automatically mean the extractor is broken. Use the fallback ladder:

1. page JSON
2. `node/share`
3. ID-based page lookup
4. `yt-dlp --dump-single-json`

If all of those still expose only audio plus image assets, the post is behaving like `photo_mode` for the public web workflow.

## Native Video vs Assembled MP4

Keep this distinction sharp:

- **Native video extraction**: TikTok exposes a real CDN video URL (`playAddr`, `downloadAddr`, or a video `format` URL).
- **Assembled slideshow MP4**: the workflow downloads image assets plus audio, then renders its own MP4.

Sites like SaveTik, SnapTik, or AhaTok may return an `.mp4` for the same TikTok link, but that can still be an assembled slideshow on their backend rather than proof that TikTok exposed a native MP4 stream.

## Audio Extension Handling

TikTok background music URLs often have no file extension. The content-type must be inspected to choose the correct save extension (e.g. `audio/mp4` → `.m4a`). The workflow saves as `background.<ext>` and `find_background_audio()` accepts any extension in `AUDIO_EXTENSIONS = {".aac", ".m4a", ".mp3", ".opus", ".ogg", ".wav", ".webm"}`.
