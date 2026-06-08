# Code Review Log — AI - Shoppee Video v1.0

This file is the canonical reference for code reviews on this project. Every audit, gap analysis, or
research-driven improvement plan gets appended here so we can track what was found, what was fixed,
and what remains open.

**How to use:** newest review at the top. Each review block has Status, Audit checklist, Open gaps,
Research findings (if any), and a recommended priority order. Once a gap closes, mark it ✅ inline
and leave it in place — don't delete history.

---

## Update — 2026-06-06 — G1 fix + error log + Desktop mirror

**By:** Clover (Claude) · **Tests:** 98/98 passing (live-run on Windows, Python 3.14.4 / pytest 9.0.3)

- ✅ **G1 fixed** — extracted shared `render_and_enrich_row()`; both batch and single-row `--download-and-analyze-record-id` paths now produce hook + caption pack + cover. Guard test `DownloadAndAnalyzeWiringTests`.
- ✅ **Categorized error log** — `logs/error-log.csv` (`timestamp, record_id, product_link, platform, category, message`). `classify_error()` buckets failures into `FILE_TOO_LARGE`, `NO_MEDIA`, `DOWNLOAD_FAILED`, `FETCH_FAILED`, `RENDER_FAILED`, `RENDER_SKIPPED`, `MISSING_FIELDS`, `UNKNOWN`. Wired into batch + single-row paths.
- ✅ **File-size guard** — `MAX_DOWNLOAD_BYTES = 500 MB`; `download_url` rejects oversized assets by declared `content-length` and by post-write size → logged as `FILE_TOO_LARGE`.
- ✅ **Desktop mirror** — finished media copied to `Desktop\Shopee Video Output\<Shop>\<Product>\{edited,raw}\` (best-effort, never fails a row). Toggle off with `--no-desktop-copy`.
- New tests: `ErrorLogAndDesktopTests` (classify, oversize guard, copy mirror, empty-copy, error-log append).
- ✅ **Hybrid media (download both types)** — `select_media_urls_for_download` now keeps the best video **and** product images (capped `MAX_SLIDESHOW_IMAGES = 8`). In render, each video renders on its own and all images are combined into **one** slideshow MP4 (`render_photo_mode_slideshow`, silent when no audio). TikTok photo-mode path unchanged. Tests `HybridRenderTests` + updated `select_media_urls_keeps_best_video_and_images`. Suite now **99/99**.

---

## Review #1 — 2026-05-06 — Post-Phase-4 Audit + Phase-5 Research

**Reviewer:** Claude Opus 4.7
**Trigger:** Phase 4A + 4B + 4D + 4E shipped earlier same day; user requested verification + improvement research before next phase
**State at review:** 92/92 tests passing, code at ~2500 lines in `scripts/process_shopee_video.py`

### Audit checklist (current state)

#### ✅ Phase 1 — Bulk URL intake
- ✅ CLI `--bulk-intake PATH|-` works (verified end-to-end)
- ✅ Frontend `/api/bulk-intake` + textarea UI present
- ✅ Shortlink `s.shopee.com.my` rejected with clear error
- ✅ Dedup against existing rows
- ✅ Auto-extracts product name from Shopee slug + TikTok video ID
- ✅ Optional `--bulk-fetch-remote` for page-title enrichment
- ✅ 5 tests in `BulkIntakeTests`

#### ✅ Phase 2 — Live batch progress
- ✅ Incremental CSV writes after every row (`sync_excel=False` mid-loop)
- ✅ Final xlsm sync at end of batch
- ✅ Frontend polls every 3 s during Run All Pending
- ✅ Failure rows trigger an incremental write the same way success rows do

#### ✅ Phase 3 — 9:16 passthrough render
- ✅ `passthrough` mode added to `RENDER_MODES`
- ✅ Auto-selected for vertical sources (height ≥720, ratio 0.50–0.62)
- ✅ Filter: `scale=1080:1920:flags=lanczos,setsar=1,drawtext=...` — no blur, no padding
- ✅ Audio preserved via `-map 0:a?`
- ✅ Frontend dropdown exposes the option

#### ✅ Phase 4A — Caption pack
- ✅ Direct 9Router calls (`gc/gemini-3-flash-preview` primary, `cc/claude-haiku-4-5-20251001` fallback on 401)
- ✅ Failure-isolated — never breaks the row
- ✅ Raw fallback when JSON parse fails (`# WARNING:` saved)
- ✅ `--skip-captions`, `--captions-model` CLI flags
- ✅ 10 tests

#### ✅ Phase 4B — Hook overlay
- ✅ `Hook` column added to `REQUIRED_COLUMNS`
- ✅ Cached so reruns don't re-call LLM
- ✅ Splices into all 3 video render modes + 1-image and multi-image slideshows
- ✅ Time-gated (0–1.5 s) with alpha fade-out
- ✅ Frontend shows 🪝 hook chip per row

#### ✅ Phase 4D — Cover image
- ✅ `cover_extract_time` handles short clips (`duration/2` for <2 s)
- ✅ FFmpeg `-ss` seek + `-frames:v 1` + drawtext at 80 pt center
- ✅ Skipped for photo-mode (intentional)
- ✅ `--skip-cover` flag
- ✅ 4 tests

#### ✅ Phase 4E — Telegram caption delivery
- ✅ Sends cover → MP4 → caption code-blocks per platform
- ✅ MarkdownV2 escaping correct (verified via tests)
- ✅ Lazy `python-telegram-bot` import (testable without dep)

#### ✅ Phase 6 — Telegram bot
- ✅ Whitelist by user ID
- ✅ `/start`, `/help`, `/status`, `/run`, plain-text URL intake
- ✅ Hook caption included in MP4 send
- ✅ Auto-installs `python-telegram-bot` via `run_telegram_bot.bat`

### Open gaps (severity-ranked)

| ID | Gap | Severity | Effort | Status |
|----|-----|----------|--------|--------|
| **G1** | `--download-and-analyze-record-id` mode (frontend "Save + Download + Analyze" button) does NOT generate hooks / captions / cover. Single-row workflow ships a bare video. | **High** — real button users click | ~30 min — refactor to share render block with `process_pending_rows` | ✅ **Fixed 2026-06-06** — extracted shared `render_and_enrich_row()`; both batch and single-row paths now route through it (hook + caption pack + cover). Regression test `DownloadAndAnalyzeWiringTests` added; suite 93/93 green. |
| **G2** | tikwm.com fallback for TikTok WAF blocks designed in `CODEX-PLAN-v1.2-tikwm-fallback.md` but never implemented. WAF flap → entire row fails. | Medium | ~2 hrs (plan exists) | ⬜ Open |
| **G3** | No end-to-end batch test running `process_pending_rows` from a temp masterlist with all phases enabled (mocked LLM + mocked FFmpeg). Orchestration regressions could slip through. | Medium | ~45 min | ⬜ Open |
| **G4** | No "🪝 Regenerate hook" button on the frontend; user must edit CSV cell manually to retry a bad hook. Same for `/regenerate <RID>` in the bot. | Low | ~20 min combined | ⬜ Open |
| **G5** | Caption section >4096 chars (Telegram per-message limit) would fail the send. Currently no chunking. | Low | ~10 min | ⬜ Open |
| **G6** | Frontend `📂 Open output file` only opens MP4 — no link for `captions.txt` / `cover.jpg`. | Low | ~10 min | ⬜ Open |
| **G7** | Bot `/status` doesn't surface Phase 4 health (captions generated / failed, hooks generated, etc.). | Low | ~15 min | ⬜ Open |
| **G8** | `scripts\ask-gemini.bat` is dead code in this pipeline (we hit 9Router directly). `GEMINI.md` may reference it stale. | Trivial | ~5 min — doc cleanup | ⬜ Open |

### Research findings (Phase-5+ improvement candidates)

Source: research agent run 2026-05-06 covering format conversion, trending audio, local Whisper, own-UGC alternatives, and reliability features.

#### Q1 — Conversion-lift formats for Malaysian/SEA TikTok Shop affiliate Shorts

Three patterns dominate top-performer 2025-26 benchmarks (top videos hit 5–8 % in-app checkout CR vs 1.92 % average):

1. **3-second hook with on-screen price/discount reveal at ~1 s.** 63 % of top videos surface the main message inside 3 s.
2. **Problem→Product→Result jump-cut (sub-2 s cuts).** Lo-fi UGC-style cuts drive +33 % consideration and +12 % purchase intent vs polished ads.
3. **Native CTA card at end (5:5 video-to-CTA ratio).** Static "Tap yellow basket" overlay at 0:08–0:15.

#### Q2 — Trending audio (Malaysia)

- **Discovery:** TikTok Creative Center Sounds (region=MY filter), Apify "TikTok Music Trend API", tokchart.com, ogohogo/tiktok-trending-data-api (free GitHub Actions scraper).
- **Verdict:** Real algo lift only fires when the sound is selected in-app at upload time. Muxing a sound into the file gives ambience but no algo bonus, and Reels actively penalises muxed audio. So **don't mux** — instead surface a `suggested_sound:` line in the Telegram caption block so Legend swaps the sound during upload.

#### Q3 — Local Whisper (May 2026, Windows CPU)

| Tool | 30 s clip | Word-level | Output |
|------|-----------|------------|--------|
| **faster-whisper (small.en, int8)** | ~7–10 s | ✅ via `word_timestamps=True` | srt/vtt/json |
| whisper.cpp | ~20–25 s | ✅ | srt/vtt/json |
| WhisperX | ~10–15 s | ✅ phoneme-aligned | srt/ass/json |

**Verdict:** **faster-whisper** with `model_size="small.en"`, `compute_type="int8"`, export `.ass` for FFmpeg `subtitles=` burn-in. Upgrade to WhisperX if word-pop alignment looks loose.

#### Q4 — Own-UGC alternative to HeyGen

- **Best combo:** Legend records 20 neutral 30 s base clips of own face once → **Wav2Lip** drives lip-sync from **ElevenLabs voice clone** of his own voice → product B-roll picture-in-picture.
- Marginal cost: ElevenLabs ~$22/mo Creator plan only.
- Wav2Lip = best lip-sync accuracy on existing footage; LivePortrait = best one-photo quality (alternative).

#### Q5 — Top reliability features

1. **State.json + `--resume` flag.** URL hash → stage (queued/rendered/captioned/delivered). Crash-safe, idempotent. Windows Task Scheduler friendly.
2. **DLQ + daily Telegram digest.** Failed rows → `failed/<rid>/error.json`; 9 pm summary with count + top error class. Auto-retry transient errors with exponential backoff first.
3. **A/B hook variant generation.** Gemini emits 3 hook variants → render all 3 → Telegram album with poll → feed winners back as few-shot examples to next batch.

Bonus: **Per-stage timing metrics → weekly Telegram digest** so the RM 2000/month math stays visible.

### Explicitly NOT worth doing (research-confirmed)

- ❌ Audio muxing of "trending" sounds — no algo lift, complicates upload
- ❌ HeyGen Avatar IV — $40/day kills the RM 2000/mo budget
- ❌ Runway / Veo / Kling per-second AI video — $0.05–0.50/sec, too expensive at 20/day
- ❌ Canva Connect API — template-fill only, not a real video editor
- ❌ CapCut API — no public API in 2026; unofficial libs violate ToS
- ❌ Auto-upload to TikTok / Shopee / Reels / Shorts — ToS-hostile

### Recommended priority order

#### 🔴 Right now (~30 min)
- Fix **G1** — the only "real bug." Single-row download-and-analyze should call the same hook+captions+cover block as `process_pending_rows`.

#### 🟡 Quick wins this week (each ≤1 hr)

| | Item | Source |
|---|------|--------|
| **W1** | Append `suggested_sound:` line to Telegram caption block (daily Creative Center MY scrape) | Q2 |
| **W2** | Price-reveal sticker at t=1 s (extend hook overlay) | Q1.1 |
| **W3** | G5 — chunk caption sections >4096 chars | Audit |
| **W4** | G4 + G6 + G7 — Regenerate hook button + Open captions/cover links + bot `/status` Phase 4 health (~30 min combined) | Audit |

#### 🟢 Phase 5 — Reliability session (~6 hrs)

| | Item | Source |
|---|------|--------|
| **R1** | State.json + `--resume` flag | Q5.1 |
| **R2** | DLQ + 9 pm Telegram daily digest with auto-retry on transient errors | Q5.1 |
| **R3** | Tikwm.com fallback (G2) | Audit + plan already written |

#### 🔵 Phase 6 — Performance (separate sessions)

| | Item | Source | Effort |
|---|------|--------|--------|
| **P1** | A/B hook variants → Telegram album poll → few-shot feedback loop | Q5.3 | ~3 hrs |
| **P2** | Phase 4C — word-level burned captions via faster-whisper + .ass | Q3 | ~3 hrs |
| **P3** | 3-cut jump-cut auto-editor (sub-2 s cuts in first 6 s) | Q1.2 | ~5 hrs |
| **P4** | 2 s CTA card appended to every video | Q1.3 | ~1 hr |
| **P5** | End-to-end batch test (G3) | Audit | ~45 min |

#### 🟣 Sub-project — Own UGC pipeline (multi-session, opt-in)

- Legend records 20 neutral 30 s base clips of own face once
- Wav2Lip + ElevenLabs voice clone of own voice
- Product B-roll picture-in-picture
- Per-row toggle on masterlist: `Mode = ugc | clip`
- Gemini writes the spoken script (different prompt than caption pack)
- Effort: 2–3 sessions for a clean v1

### References

- Plan files: `C:\Users\Legend\.claude\plans\phase-4-implementation.md`, `phase-4-ai-captions-and-video-polish.md`
- Tikwm fallback design: `CODEX-PLAN-v1.2-tikwm-fallback.md`
- Memory: `C:\Users\Legend\.claude\projects\C--Users-Legend-Project-AI-MemoryCore\memory\project_shopee_video.md`
- Obsidian: `Legendary\05-Projects\AI - Video Workflow\AI - Video Workflow Index.md`
- Session logs: `Legendary\01-Sessions\2026-05-05-001.md`, `2026-05-06-001.md`

### External research sources

- [Average Affiliate Link Conversion Rate on TikTok 2025 — Napolify](https://napolify.com/blogs/news/tiktok-affiliate-conversion-rate)
- [TikTok Ads Benchmarks for CTR, CR, CPM 2026 — Lebesgue](https://lebesgue.io/tiktok-ads/tiktok-ads-benchmarks-for-ctr-cr-and-cpm)
- [How to Increase TikTok CTR & TikTok Shop CTR 2026 — Awisee](https://awisee.com/blog/increase-tiktok-ctr/)
- [TikTok Music Trend API — Apify](https://apify.com/novi/tiktok-music-trend-api/api)
- [tokchart — daily TikTok trending sounds](https://tokchart.com/)
- [ogohogo/tiktok-trending-data-api — GitHub](https://github.com/ogohogo/tiktok-trending-data-api)
- [Choosing between Whisper variants — Modal](https://modal.com/blog/choosing-whisper-variants)
- [faster-whisper vs whisper.cpp benchmark — GitHub](https://github.com/ggml-org/whisper.cpp/issues/1127)
- [8 Best Open Source Lip-Sync Models 2026 — Pixazo](https://www.pixazo.ai/blog/best-open-source-lip-sync-models)
- [SadTalker vs Wav2Lip](https://sadtalkerai.com/sadtalker-vs-wav2lip/)
- [Dead Letter Queues: Developer Guide — swenotes](https://swenotes.com/2025/09/25/dead-letter-queues-dlq-the-complete-developer-friendly-guide/)

---

## Template — Future review

Copy this block when adding a new review. Numbering continues; latest stays at top.

```markdown
## Review #N — YYYY-MM-DD — Short title

**Reviewer:** ...
**Trigger:** ...
**State at review:** test count, recent shipped phases

### Audit checklist
...

### Open gaps
| ID | Gap | Severity | Effort | Status |
|----|-----|----------|--------|--------|

### Research findings (if any)
...

### Recommended priority order
...

### References
...
```
