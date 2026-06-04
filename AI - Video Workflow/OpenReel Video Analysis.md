# OpenReel Video Analysis

**Project**: AI - Video Workflow  
**Date**: 2026-05-01  
**Status**: Research complete  
**Decision Type**: Technology evaluation — learnable techniques for FFmpeg pipeline

## Why This Note Exists

Legend asked to evaluate OpenReel Video (github.com/Augani/openreel-video) as a potential source of learnable techniques for the AI Shoppee Video v1.0 render pipeline.

## What OpenReel Is

OpenReel Video is an open-source, browser-based video editor (MIT license) positioned as a CapCut alternative — 100% client-side, no uploads, no watermarks.

- **Tech stack**: React 18, TypeScript, WebCodecs, WebGPU, Web Audio API, THREE.js, Zustand
- **Size**: ~130k lines of code (66k frontend, 59k core engine)
- **Status**: Beta (v0.1.0, Feb 2026)
- **Stars**: 899 | Forks: 172

## Features Relevant to Our FFmpeg Pipeline

### Video Processing

| OpenReel Feature | Our Current State | Applicable? |
|---|---|---|
| Multi-track timeline | Single-track FFmpeg render | Concept for future multi-clip assembly |
| Transitions (crossfade, wipe, slide) | Hard cuts only | Yes — FFmpeg `xfade` filter |
| Speed control (0.25x–4x with pitch preservation) | Not implemented | Yes — `atempo` + `setpts` |
| Crop & transform (position, scale, rotation) | Basic vertical-blur composition | Yes — better composition logic |
| Blend modes | Not implemented | Useful for overlay text/watermarks |
| Video effects (brightness, contrast, blur, sharpen, chroma key) | Not implemented | FFmpeg has equivalents |

### Audio

| OpenReel Feature | Our Current State | Applicable? |
|---|---|---|
| Audio preservation | Already implemented correctly | Confirmed working (`-map 0:a?`) |
| Volume & panning with fade in/out | Not implemented | Yes — FFmpeg `afade`, `volume` |
| Audio ducking (auto-reduce music when dialog plays) | Not implemented | Useful for voiceover videos |
| Noise reduction (3-pass: tonal, broadband, rumble) | Not implemented | FFmpeg `anlmdn`, `highpass`, `lowpass` |
| Beat detection | Not implemented | Useful for clip-sync editing |
| Multi-track mixing | Not implemented | FFmpeg `amix` filter |

### Text & Graphics

| OpenReel Feature | Our Current State | Applicable? |
|---|---|---|
| 20+ text animations (typewriter, fade, slide, bounce) | Static caption only | Yes — FFmpeg `drawtext` with expressions |
| Karaoke-style subtitles (word-by-word highlight) | Not implemented | High-value for TikTok engagement |
| Shape tools (rectangle, arrow, star) | Not implemented | FFmpeg overlay + generated PNGs |
| SRT subtitle import | Not implemented | FFmpeg `subtitles` filter |

### Export

| OpenReel Feature | Our Current State | Applicable? |
|---|---|---|
| H.264/H.265 MP4 | We use H.264 | Already aligned |
| Quality presets (4K, 1080p, 720p) | Fixed 1080×1920 | Could add preset selector |
| Custom bitrate/framerate | Hardcoded 30fps | Could make configurable |
| Audio export (MP3, WAV, AAC) | AAC only | Could add options |

### Architecture Patterns

| Pattern | What We Can Learn |
|---|---|
| Action-based editing (every edit is undoable) | Good pattern for future frontend undo/redo |
| Engine separation (video, audio, graphics independent) | Our processor is monolithic — could modularize |
| Progressive enhancement (WebGPU → Canvas2D fallback) | Good pattern for render-mode selector |
| Auto-save with IndexedDB | Could add to our frontend form state |

## Key Finding: Audio Is Already Fixed

After reviewing `build_ffmpeg_command()` in `process_shopee_video.py`, the audio preservation logic is **already correctly implemented**:

- Video sources: `-map 0:a?` (optional audio mapping — won't fail if no audio stream)
- Photo-mode with background audio: `-map 1:a` (maps from second input)
- Photo-mode without audio: no audio mapping

The earlier "audio loss" bug noted in the Future Improvements doc has been resolved. The `?` suffix on the audio stream specifier makes it gracefully optional.

## Key Finding: Render Modes Already Exist

The render pipeline already supports multiple modes:

- `auto` — picks `passthrough` for already-vertical 9:16 sources, else `light`
- `passthrough` — scale to 1080×1920 with lanczos, caption only (no blur/padding)
- `light` — scale-to-fit with black padding, small caption
- `vertical-blur` — blurred background canvas composition, larger caption

These were implemented after the Future Improvements doc was written.

## What OpenReel Does NOT Help With

| Gap | Reason |
|---|---|
| Media downloading | OpenReel is an editor, not a downloader |
| Product analysis / AI hooks | No AI content generation |
| Affiliate workflow automation | No e-commerce integration |
| TikTok/Shopee platform integration | No platform APIs |
| Batch processing | Single-project editor only |

## Strategic Verdict

| Aspect | Decision |
|---|---|
| Replace our FFmpeg pipeline? | **No** — OpenReel is browser-based, we need server/local batch processing |
| Use as "editor handoff" target? | **Maybe** — could replace CapCut for manual polish step |
| Learn techniques from? | **Yes** — transitions, text animations, audio ducking |
| Fork/integrate directly? | **No** — different architecture (React SPA vs Python batch) |
| Self-host for manual editing? | **Possible** — could deploy locally as Phase 4 Editor Handoff |

## Recommended Next Improvements (Priority Order)

### 1. Crossfade Transitions for Photo-Mode Slideshows

Currently `render_photo_mode_slideshow` uses hard `concat` between images. Adding crossfade:

```bash
# FFmpeg xfade between two segments
[v0][v1]xfade=transition=fade:duration=0.5:offset=2.5[vt01];
[vt01][v2]xfade=transition=fade:duration=0.5:offset=5.0[vt02]
```

### 2. Karaoke-Style Captions

For TikTok-style word-by-word highlight captions using ASS subtitles:

```ass
Dialogue: 0,0:00:00.00,0:00:01.50,Default,,0,0,0,,{\k30}Best {\k25}product {\k35}ever!
```

Then render with FFmpeg `ass` filter instead of `drawtext`.

### 3. Audio Ducking for Future Voiceover

When voiceover generation is added:

```bash
ffmpeg -i background.m4a -i voiceover.mp3 \
  -filter_complex "[0:a]sidechaincompress=threshold=0.02:ratio=6[ducked]; [ducked][1:a]amix=inputs=2" \
  output.mp4
```

### 4. Self-Host OpenReel as Editor Handoff

Instead of depending on CapCut for manual polish:
- Deploy OpenReel locally (npm install + serve)
- Use as the "Phase 4 Editor Handoff" target
- Advantage: no account required, no watermarks, runs offline

## Obsidian Sync Requirement

This note should be mirrored into the Legendary vault topic folder:

```text
C:\Users\Legend\Desktop\Obsidian\Legendary\05-Projects\AI - Video Workflow\
```
