# AI - Shoppee Video TikTok v1.1 Hybrid Design

**Project**: AI - Shoppee Video v1.0  
**Date**: 2026-04-28  
**Status**: Approved design spec  
**Scope**: Improve TikTok public-post handling by combining stronger extraction with better photo-mode output quality, while deferring Remotion into a separate future site.

## Goal

Upgrade the current TikTok workflow so it can:

- handle public TikTok post URLs more reliably
- distinguish true video posts from photo-mode posts
- download the right media set for each post type
- produce better photo-mode output than a one-image fallback
- surface clearer post-type and output-state information in the existing frontend

This is a hybrid upgrade:

- stronger TikTok extraction
- better photo-mode output quality
- no Remotion implementation yet inside this project

## Out of Scope

This design does not include:

- private TikTok posts
- login-required TikTok flows
- TikTok profile scraping
- TikTok playlist scraping
- signed TikTok web API / cookie machinery like `msToken`, `X-Bogus`, or `X-Gnarly`
- dependence on hosted relay services such as SSSTik or Tikwm for the core workflow
- a Remotion editor implementation in the current app
- CapCut project export
- hook-generation UI or prompt-based style editing UI

## Current Problem

The current system can already:

- normalize some TikTok links
- use `yt-dlp` as a first-pass downloader
- fall back to image-plus-audio behavior for some photo-mode posts
- render a final `_new.mp4`

But it still has important gaps:

- it does not treat all public TikTok post shapes explicitly
- it can accept weak image-only results too early
- photo-mode output is still too close to a single-image fallback
- the frontend does not clearly communicate what type of TikTok post was processed

## Supported Links

v1.1 should support only **public single-post TikTok links**:

- `https://www.tiktok.com/@user/video/<id>`
- `https://vt.tiktok.com/...`
- `https://vm.tiktok.com/...`
- explicit public TikTok `/photo/` post links if encountered

Not supported:

- profile pages
- playlists
- private posts
- bulk scraping

## Post Type Model

The TikTok extractor must classify each public post into one of these:

### `video`

A real downloadable or playable video stream is exposed.

Expected result:

- download real video media
- do not fall back to image conversion if a valid video stream exists

### `photo_mode`

Direct video is unavailable, but usable image assets and optionally background music are exposed.

Expected result:

- download all usable image assets when available
- download background audio when available
- render a slideshow-style affiliate output

### `unknown`

The post exists, but the extractor cannot confidently build a usable media bundle.

Expected result:

- fail clearly
- do not pretend the post was successfully downloaded

## Media Bundle Model

The extractor should return a structured TikTok media bundle before downloading files.

Proposed logical shape:

```text
platform: TikTok
post_type: video | photo_mode | unknown
canonical_url: ...
video_id: ...
video_urls: [...]
image_urls: [...]
audio_url: ...
caption_text: ...
author_name: ...
notes: ...
```

Rules:

- `video` bundles must prefer direct video URLs
- `photo_mode` bundles must prefer full image sets over a single fallback image
- `unknown` bundles must not be treated as successful media acquisition

## Extraction Flow

### Step 1: normalize URL

Every supported TikTok input must be normalized to a canonical public post URL when possible.

Example:

```text
https://www.tiktok.com/@bargainpurchasesofficial/video/7429146118933564690
```

### Step 2: fast path

Keep the existing fast path:

- try `yt-dlp` first
- if it returns a real video file, accept the result as `video`

But:

- if it returns only audio or image artifacts, do not stop there

### Step 3: structured inspection

Inspect TikTok page data, primarily:

```text
__UNIVERSAL_DATA_FOR_REHYDRATION__
```

Read the relevant post data and classify the post:

- if `downloadAddr` or `playAddr` is populated -> `video`
- if video is empty but image assets plus music exist -> `photo_mode`
- otherwise -> `unknown`

### Step 4: build download plan

For `video`:

- prefer direct downloadable video URL
- fallback to playable video URL if needed

For `photo_mode`:

- prefer the full photo set if TikTok exposes it
- otherwise keep one best fallback image
- keep background music/audio when available

### Step 5: download bundle

Only after classification should the downloader fetch the media.

## Download Targets

### Video posts

Expected raw target:

```text
raw/<video-id>.mp4
```

### Photo-mode posts

Expected raw targets:

```text
raw/<video-id>.jpg
raw/<video-id>-2.jpg
raw/<video-id>-3.jpg
...
raw/background.m4a
```

Rules:

- filenames must be stable and deterministic
- reruns must overwrite canonical outputs instead of accumulating junk files

## Photo-Mode Output

### Goal

Move beyond the current “one image turned into video” behavior whenever the post exposes multiple images.

### Output path

The final edited output remains:

```text
edited/<video-id>_new.mp4
```

Only one final edited MP4 per TikTok post.

### Slideshow behavior

For v1.1, keep the renderer conservative:

- use the available image sequence
- assign short fixed durations per image
- cap total runtime to something practical for affiliate content

Recommended defaults:

- 1 image: 6-8 seconds
- 2-4 images: about 2-3 seconds per image
- 5+ images: cap to about 10-15 seconds total unless later made configurable

### Visual treatment

For v1.1:

- keep the current vertical composition style
- allow hard cuts or very light fades
- avoid complex scene animation or editor-like motion logic

### Audio behavior

If `background.*` exists:

- include it in the final slideshow render
- trim to final duration

If background audio does not exist:

- still render the slideshow
- surface that absence in notes or analysis

### Caption behavior

Keep the existing master caption:

```text
Shop Name - Product Name
```

Do not add scene-by-scene caption logic in this phase.

## Frontend Changes

Keep the current button set:

- `Save`
- `Save + Download`
- `Analyze`
- `Save + Download + Analyze`
- `Open Output Folder`

### Required UI improvements

For TikTok rows, after processing the frontend should communicate the result type more clearly.

Recommended display labels:

- `Video Post`
- `Photo-mode Post`
- `Unknown TikTok Media`

These can appear in:

- status text
- row notes
- compact badges or summary text

### Media summary

When a row is loaded, the frontend should be able to show a compact summary when available:

```text
Raw images: N
Audio: Yes/No
Edited output: Yes/No
Analysis: Yes/No
```

### Masterlist schema

Do not add a new dedicated column for TikTok post type in v1.1.

Instead:

- keep `Status`
- keep `Analysis Done`
- record the richer post-type detail in `Notes`

Example:

```text
Downloaded 4 media file(s); edited 1 slideshow video file(s) (photo-mode post with background audio)
```

## Remotion Boundary

Remotion should remain a separate future site or tool.

The current app may later add a separate button such as:

```text
Open Remotion Editor
```

But v1.1 does not implement that site or rendering lane.

Reason:

- keep current scope focused on extraction and output quality
- avoid mixing two render systems before TikTok classification is solid

## Risks

### TikTok page structure changes

TikTok may change:

- hydration JSON structure
- field names
- image asset placement
- music field placement

Mitigation:

- keep classification logic modular
- keep explicit tests for `video`, `photo_mode`, and `unknown`
- fail clearly when structured classification becomes impossible

### Partial photo-mode bundles

Some posts may expose:

- a full image set
- only one best image plus audio
- audio without enough image data

Mitigation:

- support graded success
- prefer full image sets
- allow single-image fallback as a limited success path
- hard fail only when no usable media bundle exists

### Misclassification

If the system misclassifies a post:

- it may produce a slideshow when a real video existed
- or report failure when the post was actually photo-mode

Mitigation:

- prefer direct video fields first
- only use `photo_mode` when direct video is absent
- surface result type in notes/status

### Rerun duplication

The workflow has already shown rerun sensitivity.

Mitigation:

- canonical filenames
- raw-image cleanup before photo-mode redownload
- edited-output cleanup before photo-mode rerender
- regression tests for rerun behavior

## Test Plan

### Extraction tests

- normalize standard TikTok `/video/` URLs
- normalize short links
- support `/photo/` URL shape when encountered
- classify direct video posts from structured data
- classify photo-mode posts from structured data
- classify `unknown` correctly when no usable bundle exists

### Bundle tests

- video bundle chooses direct video targets correctly
- photo-mode bundle builds ordered image targets plus audio target
- extensionless audio URLs save as valid audio files
- returned bundle paths actually exist on disk

### Rerun tests

- photo-mode rerun does not accumulate junk duplicates
- rerun preserves canonical filenames
- stale edited outputs are replaced correctly

### Render tests

- single-image fallback still renders
- multi-image photo-mode bundle renders one final MP4
- background audio is preserved when available
- output filename remains `<video-id>_new.mp4`

### Frontend tests

- TikTok rows still save/download/analyze correctly
- notes/status reflect `Video Post` vs `Photo-mode Post`
- loaded rows can show a compact media summary
- Shopee flows remain unaffected

## Recommended v1.1 Implementation Order

### Phase 1: extractor foundation

1. expand TikTok URL support to include `/photo/`
2. strengthen typed classification model
3. build structured media bundle output

### Phase 2: download behavior

4. download true video posts correctly
5. download photo-mode bundles correctly
6. keep canonical raw filenames stable

### Phase 3: photo-mode rendering

7. render multi-image slideshow output
8. merge background audio
9. improve status and notes wording

### Phase 4: frontend clarity

10. show post-type/result-type feedback
11. show compact media summary
12. preserve current simple button flow

### Phase 5: verification

13. run full unit test suite
14. run live smoke tests:
    - one real TikTok video post
    - one photo-mode TikTok post
    - one rerun verification
15. update memory, project notes, and Obsidian mirror

## Recommendation

For v1.1, this is the right boundary:

- stronger TikTok extraction
- explicit post-type classification
- better photo-mode output
- clearer user feedback
- no Remotion implementation yet

This keeps the upgrade local-first, focused, and testable.
