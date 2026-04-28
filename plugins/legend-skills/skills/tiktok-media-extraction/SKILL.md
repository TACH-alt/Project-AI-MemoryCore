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
3. If it returns only images or audio, fetch the TikTok page and inspect `__UNIVERSAL_DATA_FOR_REHYDRATION__`.
4. Classify the post:
   - `video`: non-empty `video.downloadAddr` or `video.playAddr`
   - `photo_mode`: no direct video URL, but image cover/origin assets and music URL exist
5. For photo-mode:
   - prefer `imagePost` assets if present
   - otherwise use one best fallback image asset, not duplicate cover variants
   - keep background audio separately and merge it during render

## Practical Checks

- `python -m yt_dlp -F "<url>"`:
  - real video posts normally show video formats
  - photo-mode posts often show only `audio`
- page-data fallback:
  - parse `webapp.video-detail -> itemInfo -> itemStruct`
  - check `video.downloadAddr`, `video.playAddr`, `video.originCover`, `video.zoomCover`, `music.playUrl`

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
