# Shopee Video — Progress Review & Improvement Plan

**Date:** 2026-06-06 · **Reviewer:** Clover (Claude) · **Scope:** Shopee path only (TikTok intentionally excluded) · **Code:** `scripts/process_shopee_video.py` (~2,500 lines)

---

## TL;DR

The Shopee pipeline is **usable and production-shaped**. Full test suite **ran green today: `92 passed in 2.94s`** (Python 3.14.4, pytest 9.0.3, exit 0 — live run, not from memory). The end-to-end Shopee flow works: link → scrape seller media → pick best video → render a captioned 1080×1920 MP4 with an AI hook overlay → write caption pack + cover image. The biggest real gap is a **single-row frontend button that ships a bare video** (no hook/caption/cover); everything else is hardening, not repair.

---

## 1. What the Shopee path does today

| Stage | Implementation | State |
|---|---|---|
| Link classification | `detect_platform` / `is_shopee_product_url` — handles `-i.<shop>.<item>` and `/product/<id>/<id>`; rejects `s.shopee.com.my` shortlinks | ✅ |
| Media discovery | `discover_media_urls` → mobile-SEO HTML fetch (`page_request_headers`) → `extract_media_urls_from_html` with Shopee CDN allowlist (`*.vod.susercontent.com`, `down-my.img...`) | ✅ |
| Noise filtering | `is_site_chrome_media_url` strips logos, sprites, placeholders, product-detail-page chrome | ✅ |
| Best-media pick | `select_media_urls_for_download` — one best video by `video_quality_score`, else top-5 images | ✅ (caveat §3) |
| Download | `download_url` streams to disk, infers extension from content-type | ✅ |
| Render | `build_ffmpeg_command` — `passthrough` (already-vertical 9:16), `light` (pad), `vertical-blur` (image/canvas); audio preserved via `-map 0:a?` | ✅ |
| Hook overlay | `generate_hook` (9Router LLM), spliced into the filter graph, cached in `Hook` column | ✅ |
| Caption pack | `write_captions_pack` → `captions.txt` (TikTok/Reels/Shorts/Shopee variants + hashtags) | ✅ |
| Cover image | `render_cover_image` → `cover.jpg` with hook | ✅ |
| Orchestration | `process_pending_rows` — per-row error isolation, incremental CSV writes, `product-info.md`, run log | ✅ |
| Bulk intake | paste many URLs, dedupe, auto-name from slug, reject shortlinks | ✅ |

**Verdict:** past "usable." This is a working daily-driver for Shopee, contingent on Shopee still exposing seller media in mobile SEO HTML (an external dependency, not a code defect).

---

## 2. Test results (live, today)

```
Python 3.14.4 · pytest 9.0.3
tests/test_process_shopee_video.py + tests/test_shoppee_video_frontend.py
92 passed in 2.94s   (exit 0)
```

Shopee-specific coverage is solid: product-URL query stripping, mobile headers, SEO-HTML media extraction, single-best-video selection, site-chrome filtering, render-mode selection, caption-pack JSON parsing/formatting, hook sanitisation, cover timing, masterlist column/Excel sync, and bulk intake. A reusable `run_shopee_tests.bat` was added at the project root (double-click to re-run; writes `test_output.txt`).

---

## 3. Code review — strengths & issues (Shopee)

### Strengths
- Clean, typed, docstringed; small single-purpose functions; good separation of concerns.
- Defensive orchestration: one row's failure never kills the batch; captions/cover are best-effort and never fail a row; incremental writes give live frontend progress.
- The `passthrough` mode correctly avoids re-blurring already-vertical sources — this fixed the earlier "over-processed + dropped audio" regression. Audio is mapped through.
- Sensible font fallback chain (`arial → segoeui → tahoma → verdana`).

### Issues / risks (ranked)
1. **G1 — single-row button ships a bare video (High, user-facing).** The frontend "Save + Download + Analyze" / `--download-and-analyze-record-id` path does **not** run the hook + caption + cover block that `process_pending_rows` does. The button you actually click produces a lower-quality output than a batch run. *(Already logged as G1 in `CODE-REVIEW.md`.)*
2. **`video_quality_score` is an ID heuristic, not resolution (Medium).** It picks the largest `.<digits>.mp4` token — that number is a Shopee file id, not a resolution. "Best video" can therefore pick a worse variant. Probe real dimensions (ffprobe) or parse an actual resolution marker before choosing.
3. **Single-video selection with no fallback (Medium).** `select_media_urls_for_download` returns exactly one video URL; if that download 404s/times out, the row fails even when other valid seller videos were discovered. Keep an ordered candidate list and try the next on failure (the image branch already keeps up to 5).
4. **Discovery breakage is silent and hard to debug (Medium).** When Shopee changes markup/WAF and 0 media are found, the row just reports "no media." There's no retry, no UA rotation, and no dump of the fetched HTML — so diagnosing a breakage means reproducing by hand. This is the Shopee analog of the TikTok fragility.
5. **LLM-dependent features degrade quietly (Low).** If 9Router is unreachable, hooks and captions are skipped (good — row still renders), but there's no per-batch visibility into how many rows shipped without a hook/caption.
6. **No preflight for ffmpeg/ffprobe (Low).** If ffmpeg isn't found, `render_video` returns `None` and the row silently becomes `Downloaded` instead of `Edited`. A one-time startup check would surface this immediately.

---

## 4. Recommended improvements (prioritised)

### 🔴 Now (~30–45 min) — the only real bug
- **Fix G1.** Refactor the single-row download+analyze path to call the same hook + caption + cover block as `process_pending_rows` (extract that block into one shared function and call it from both). This is the highest-value fix: it makes the button you use daily produce full-quality output.

### 🟡 Soon (each ≤1 hr) — Shopee reliability
- **Discovery diagnostics + resilience** (issue #4): 1 retry with a rotated User-Agent; when 0 media found, dump the fetched HTML to `raw/_debug_page.html` so breakage is debuggable in seconds.
- **Startup preflight** (issue #6): check ffmpeg/ffprobe/font once at launch; print a clear warning if missing.

> Descoped per Harith (2026-06-06): resolution-aware "best video" selection and multi-candidate video fallback (issues #2/#3) — not pursued.

### 🟢 Later — robustness & scale (from `CODE-REVIEW.md`)
- **State + `--resume`** (R1): crash-safe, idempotent batches keyed by URL hash → stage. Friendly to scheduled runs.
- **DLQ + daily digest** (R2): failed rows to `failed/<rid>/error.json`; a once-a-day summary with counts and top error class; auto-retry transient errors with backoff.
- **Batch-quality logging** (issue #5): per-run counts of hooks/captions generated vs skipped.

### Explicitly *not* worth doing (research-confirmed earlier)
Audio-muxing "trending" sounds, HeyGen avatars, per-second AI video, Canva/CapCut API handoff, and auto-upload to platforms — all rejected on cost or ToS grounds in the prior review. No change.

---

## 5. Suggested next action

Do **G1** first — it's small, it's the only true defect, and it directly raises the quality of every video you produce through the UI. I can implement it (route the single-row path through the shared render+enrich block) and re-run the suite to confirm still-green. Want me to proceed?

*Note: the tikwm TikTok fallback (branch `codex/tiktok-v12-tikwm-fallback`, gap G2) is deliberately out of scope here per your "ignore TikTok for now."*
