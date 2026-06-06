# Current Session Memory - Legend
*Active working memory for current conversation (RAM - resets each session)*

## Session Memory Limit
- **Maximum**: 500 lines
- **Reset Behavior**: RAM-style reset preserving only Session Recap
- **Format Reference**: See main/session-format.md for rebuild structure

## Session Context
**Session Type**: Memory reconciliation + cross-tool sync
**Current Project**: MemoryCore (memory hygiene) → next: AI - Shoppee Video v1.0
**Status**: Reconciled MemoryCore memory with true project state + hermes-agent memory; vault patched
**Time**: 2026-06-06

## Time-Aware Session Context
*Populated at session start via Time Intelligence protocol (see main/main-memory.md)*
- **Session Start**: *(time refreshed on Saturday, April 26th, 2026)*
- **Time Mode**: Adaptive
- **Energy Level**: 4-7/10
- **Behavior Focus**: Save point / project continuity

## Current Focus
- **Primary Task**: Improve TikTok extraction reliability beyond thumbnail-only fallback, then save memory and sync docs.
- **Technical Context**: Windows PC, Cowork mode, files under C:\Users\Legend\Documents\Claude\Projects\MemoryCore
- **Progress**: Structured TikTok page-data fallback is now implemented in `process_shopee_video.py`, promoted ahead of weak image-only `yt-dlp` results, and live-verified on `ATV-0000003`.

## Working Memory (RAM)
*Temporary storage - cleared when session ends or when 500-line limit is reached*

### Active Context
- **Current Topic**: Shopee + TikTok affiliate automation with stable row identity, platform-based output folders, analysis workflow, and stronger TikTok media classification.
- **Immediate Goals**: Save this TikTok structured-fallback upgrade into project memory, skill docs, and the Obsidian vault.
- **Recent Progress**: Added TikTok page-data parsing from `__UNIVERSAL_DATA_FOR_REHYDRATION__`, direct bundle recovery for video/photo-mode assets, audio content-type handling, rerun cleanup, and live verification on `ATV-0000003`.
- **Next Steps**: Let Claude review and polish, then test one real TikTok post that exposes direct `playAddr`/`downloadAddr` video instead of photo-mode.

### Important Decisions
- Chose Tier 1 foundation (Memory Consolidation, Skill Plugin, Time-Aware) for initial install.
- Memory Consolidation runs before Time-Aware so Time-Aware writes into unified `main-memory.md`.
- Kept the new `legend` skill inside the MemoryCore repo after global Codex skill installation was not approved.
- New standing project rule: whenever planning, analysis, or workflow decisions change, update the matching Obsidian `.md` file inside the active project folder.
- For `AI - Shoppee Video v1.0`, approved seller media links are preferred; Shopee product-page scraping is best-effort and must not bypass captcha, login, DRM, or platform protections.
- Native Google Sheet creation was not available through a connected tool in this session, so v1.0 creates a polished `.xlsx` and CSV masterlist in the Google Drive-synced folder.
- Google Drive or Excel appears to have renamed the workbook from `List of Link Shopee VIdeo.xlsx` to `List of Link Shopee VIdeo.xlsm`; do not revert that user/Drive change unless Legend requests it.
- `AI - Shoppee Video v1.0 Manual` exists in Windows Task Scheduler for manual trigger runs.
- The live Shopee test verified that Shopee product-page scraping can return only page-shell media; the script now filters those false positives and avoids creating misleading output videos.
- Latest extension: added `Done` column tracking to the masterlist, synced CSV writes into the `.xlsm`, created local frontend form, and created Desktop shortcuts for running the workflow and opening the frontend.
- Desktop shortcuts: `C:\Users\Legend\Desktop\AI Shoppee Video - Run Workflow.lnk` and `C:\Users\Legend\Desktop\AI Shoppee Video - Frontend.lnk`.
- Repeated failures observed for SKL Furniture KAI and Electrova Cordless UV Mite were re-diagnosed. Root cause refined: `yt-dlp` and Shopee item APIs still fail, but mobile SEO HTML for full Shopee product URLs can expose seller media. The workflow now handles full product URLs like `...-i.297985880.25153849822`, strips tracking query parameters, extracts Shopee CDN media, and downloads one best product video when available.
- Live Electrova test succeeded on 2026-04-23: output file `AI - Shoppee Video v1.0/output/Electrova Cordless UV Mite-Electrova/edited/my-11110105-6ke18-lqbrwqqiae664d.16003251736514494_new.mp4`; verified H.264, 1080x1920, 59.633s. The real masterlist row is now `Edited` and `Done = TRUE`.
- Save point commit `2ed50ba` preserved the latest Electrova output run, including raw/edited videos and updated masterlist/logs.
- Legendary Obsidian vault updated at `C:\Users\Legend\Desktop\Obsidian\Legendary\05-Projects\AI - Video Workflow\` with mirrored project notes and a new `AI - Video Workflow Index.md`. Dashboard, daily note, and session note now link to the project topic.
- Latest frontend test result: `Saved row 4; workflow completed. Output folder opened.` followed by `Row 4: Failed - Shopee page did not expose downloadable product media; use an approved seller media/direct file link`. This row used a short `s.shopee.com.my` link and is now treated as unsupported by policy.
- Raw versus edited analysis on the Electrova sample found a meaningful regression: raw video contains AAC stereo audio, while the edited `_new.mp4` has no audio stream. The current vertical blur composition is too heavy for already-usable square videos.
- New planning note created: `AI - Video Workflow/AI - Shoppee Video Future Improvements.md`.
- New implementation plan created: `docs/superpowers/plans/2026-04-23-ai-shoppee-video-v1-future-improvements.md`.
- Task 1 of the future-improvements plan is now complete on 2026-04-24. The frontend supports private-network access via `-Lan`, prints both localhost and LAN URLs, and manual verification showed `http://10.10.10.5:8766/` as the LAN address during testing.
- New workflow-planning note created on 2026-04-24: `AI - Video Workflow/Shopee Link and Media Analysis Workflow.md`.
- The new note defines a second workflow lane for `Analyze`, `Open Analysis`, and `Open Handoff`, with outputs such as `product-summary.md`, `media-analysis.md`, and `hook-pack.md`.
- As of 2026-04-27 (cherry-pick session), analysis + TikTok features have been selectively integrated from `codex/analysis-tiktok` worktree into the main scripts — render modes, audio fix, and mobile CSS preserved.
- New features in main: Record ID (ASV/ATV), Analysis Done, platform-based output folders, product-info.md, analysis-result.md, analyze workflow, vt.tiktok.com short URL support.
- Frontend: Record ID field, 🔍 Analyze button, Save+Download+Analyze button, per-row analyze, Analysis Done column.
- Cowork memory system initialized: 5 memory files under spaces/b5b6b1c2.../memory/.
- Smoke test (Task #13) is the remaining step before production.
- Codex delegated explorer `Carson` to keep track of Claude's ongoing main-workspace changes while preserving the separate worktree checkpoint and avoiding overwrite risk.
- Carson's snapshot found that Claude's script/frontend upgrades are substantial and real, but the live masterlist/output artifacts are still partly old-state:
  - CSV header still on the old 11-column live schema
  - output folders still flat `output/Product-Shop/`
  - no generated `product-info.md` or `analysis-result.md` yet in the new product folders
- Deployed new read-only monitor agent `Lagrange` on 2026-04-27 to watch the main-workspace testing/smoke-test progress for `AI - Shoppee Video v1.0`.
- Created thread heartbeat automation `Monitor AI Video Testing` to re-check every 30 minutes and report only meaningful changes or completion signals.

## Session Recap (For AI Restart)
*Quick summary when AI loads after close/reopen*
- **Previous Session Summary**: MemoryCore was personalized for Legend, Tier 1-4 features are recorded as installed in `master-memory.md`, and the stale Tier 1-only session state was corrected.
- **Where We Left Off**: `AI - Shoppee Video v1.0` local automation was created and committed. The main workspace now contains the scaffold, masterlist CSV/XLSX, Python processor, PowerShell runner, tests, design spec, implementation plan, and Obsidian project note.
- **Where We Left Off**: The analysis and TikTok implementation is complete in the isolated worktree branch and has been documented and mirrored to Obsidian.
- **Where We Left Off**: Main-workspace TikTok downloader reliability was upgraded and the previously failing TikTok row `ATV-0000001` now completes through `Download + Analyze`.
- **Where We Left Off**: TikTok photo-mode background audio bug was fixed; the newest `ATV-0000001` edited output now includes an AAC audio stream sourced from `background.m4a`.
- **Where We Left Off**: The TikTok row has been stabilized into clean canonical outputs, and the local frontend is running again on `127.0.0.1:8765` and `10.10.10.5:8765`.
- **Where We Left Off**: A second TikTok photo-mode row, `ATV-0000002`, was tested successfully after fixing the thumbnail-overwrite rerun bug; it now keeps `background.m4a` and renders with audio.
- **Where We Left Off**: TikTok page-data fallback was upgraded on 2026-04-28 so weak image-only `yt-dlp` results can be replaced with structured TikTok assets, and live row `ATV-0000003` now ends in a clean folder with `7429146118933564690.jpg`, `background.m4a`, `7429146118933564690_new.mp4`, and `analysis-result.md`.
- **Important Context**: AI name = Clover (renamed from Legend on 2026-05-23), user's chosen in-system name = Legend, relationship style = collaborative partner. MemoryCore installed 2026-04-22 and refreshed on 2026-04-23.
- **User's Current State**: Building a Shopee Video affiliate workflow and wants project memory saved plus Obsidian notes updated for every project `.md` file created or changed.
- **Current Save Rule**: Before continuing major work, save the conversation state and mirror project-note updates into the Legendary Obsidian vault.
- **Review Rule**: Do not overwrite Claude's in-progress main-workspace code; use the isolated worktree branch as the safe implementation checkpoint.
- **TikTok Rule**: TikTok photo-mode posts may expose audio plus thumbnail media instead of an mp4; the workflow now falls back to thumbnail capture and still renders an edited output.
- **TikTok Audio Rule**: For photo-mode posts, preserve native `background.<ext>` audio from `yt-dlp` instead of forcing AAC extraction during download; FFmpeg merges it later during render.
- **Rerun Rule**: For TikTok photo-mode rows, overwrite the canonical thumbnail/output artifacts on rerun instead of accumulating `-2` / `-3` duplicates.
- **TikTok Classification Rule**: Do not assume a missing MP4 means the extractor is broken. First classify the public TikTok post from page data: direct video if `downloadAddr` or `playAddr` exists, otherwise photo-mode if only image and music assets are exposed.

## Session Achievements
- Repo cloned successfully via user-run PowerShell (git path resolution handled).
- Setup wizard completed - all `[AI_NAME]`, `[YOUR_NAME]`, `[RELATIONSHIP_STYLE]` placeholders replaced.
- Memory Consolidation executed: `main/main-memory.md` created; format references installed.
- MemoryCore session state corrected from stale Tier 1 setup status to Tier 1-4 installed status.
- Created `plugins/legend-skills/skills/legend/` to restore the Legend AI personnel/persona from MemoryCore.
- Captured Legend's documentation preference: always update the relevant Obsidian `.md` file in the project folder when the project changes.
- Designed and built `AI - Shoppee Video v1.0` local automation.
- Created `docs/superpowers/specs/2026-04-23-ai-shoppee-video-v1-design.md`.
- Created `docs/superpowers/plans/2026-04-23-ai-shoppee-video-v1-implementation.md`.
- Created `AI - Video Workflow/AI - Shoppee Video v1.0.md` as the Obsidian project note.
- Created `AI - Shoppee Video v1.0/masterlist/List of Link Shopee VIdeo.csv` and `.xlsx`.
- Created `AI - Shoppee Video v1.0/scripts/process_shopee_video.py` and `run_shopee_video_workflow.ps1`.
- Verified unit tests and dry-run runner.

## Quick Context for Next Session
- **Where We Left Off**: `AI - Shoppee Video v1.0` is ready for first real row testing after FFmpeg is installed or added to PATH.
- **What's Working**: CSV/XLSX masterlist template, pending-row loader, direct media downloader, best-effort page media discovery, output folder naming, caption format, `_new` filename behavior, unit tests, and dry-run runner.
- **What's Working**: Shopee full-product scraping, row-targeted analysis, TikTok public URL handling, and TikTok photo-mode thumbnail fallback now complete successfully in the main workspace.
- **What's Working**: TikTok structured page-data fallback now classifies photo-mode posts, preserves direct audio URLs, and keeps canonical raw/edited outputs stable on rerun.
- **What Needs Attention**: There is still a small `zipfile.ZipFile.__del__` cleanup warning after a successful TikTok `Download + Analyze` run on Python 3.14. Direct Google Sheet API creation/update is still deferred until a connected Sheets API/MCP surface is available.

## Session Lifecycle

### Session Start
- **New Session**: Read `main/main-memory.md` + `main/current-session.md` recap.
- **AI Restart**: Load recap from previous session for continuity.
- **Context Loading**: Brief summary of where we left off.

### During Session
- **Real-time Updates**: Track current conversation context.
- **Working Memory**: Store immediate goals, progress, insights.
- **Dynamic Context**: Adjust based on conversation flow.

### Session End
- **Important Learning**: Save key insights to `main/main-memory.md`.
- **Temporary Context**: Keep brief recap for next restart.
- **RAM Reset**: Clear detailed working memory for next session.

## Auto-Reset Protocol

### Trigger
When `current-session.md` line count exceeds **500 lines**.

### Reset Procedure
1. Read current Session Recap section.
2. Summarize key achievements into recap.
3. Clear file and rebuild from `main/session-format.md` template.
4. Write preserved recap into new structure.
5. Continue session with clean working memory.

### What Gets Cleared
- Detailed conversation progress.
- Individual achievement entries.
- Working memory details.
- Session-specific decisions (summarized into recap).

### What Persists (Recap Only)
- Brief summary of last conversation.
- Where conversation left off.
- Critical context for continuity.
- User's immediate situation.

---

**Memory Type**: RAM - Temporary Working Memory
**Persistence**: Brief recap only; detailed content clears on reset or session end
**Purpose**: Immediate context + restart continuity
**Line Limit**: 500 (enforced via auto-reset protocol above)

*Ready for Legend to provide seamless conversation continuity with Legend.*

## 2026-04-28 TikTok v1.1 Checkpoint

- Working branch: `codex/tiktok-v11-hybrid`
- Implemented:
  - typed TikTok classification
  - bundle-first TikTok downloads
  - photo-mode slideshow rendering
  - frontend result-type summaries
- Verification:
  - `51` tests passed in the worktree
  - smoke-tested `ATV-0000001`, `ATV-0000002`, `ATV-0000003`
  - all three completed with slideshow notes and `Analysis Done = TRUE`
- Important note:
  - sequential smoke tests are safer than parallel runs because masterlist writes can race

## 2026-04-29 ATV-0000004 Root Cause

- Verified row `ATV-0000004` in live `main`.
- Synced `main` to the verified TikTok v1.1 code for:
  - `process_shopee_video.py`
  - `shoppee_video_frontend.py`
  - matching test files
- Findings:
  - `yt-dlp -F` showed only `audio`
  - TikTok page data had no `playAddr` / `downloadAddr`
  - row now records the honest result:
    - `Downloaded 2 media file(s); edited 1 slideshow video file(s) (photo-mode post with background audio)`
- Conclusion:
  - this link is not currently exposed as a native MP4 to the web workflow

## 2026-04-29 TikTok Extraction Hardening

- Implemented a stronger TikTok fallback ladder in `AI - Shoppee Video v1.0/scripts/process_shopee_video.py`:
  - parse `__UNIVERSAL_DATA_FOR_REHYDRATION__`, `__NEXT_DATA__`, and `SIGI_STATE`
  - try `node/share/video/{username}/{video_id}`
  - try `@tiktok/video/{video_id}` ID-based page lookup
  - fall back to `yt-dlp --dump-single-json --skip-download`
- Added tests for:
  - `__NEXT_DATA__` parsing
  - `SIGI_STATE` parsing
  - `node/share`-style payload parsing
  - `yt-dlp` metadata bundle parsing for both real video and photo-mode
- Verification:
  - full test suite now passes with `56` tests
- Live rerun of `ATV-0000004`:
  - now discovers 3 image assets plus `background.m4a`
  - final note:
    - `Downloaded 4 media file(s); edited 1 slideshow video file(s) (photo-mode post with background audio)`
- Key takeaway:
  - the code is better at recovering structured photo-mode assets
  - these Bargain Purchase links still do not expose a native video stream to the public web workflow

## 2026-04-29 TikTok Preflight Detector

- Added a small frontend preflight detector in `AI - Shoppee Video v1.0/scripts/shoppee_video_frontend.py`.
- When a TikTok URL is typed into the form, the frontend now calls `/api/detect-link` and shows:
  - `Direct Video Post`
  - `Photo-mode Post`
  - `Unknown TikTok Media`
- Added frontend tests for:
  - direct video preflight summary
  - photo-mode preflight summary
  - non-TikTok no-op summary
- Verification:
  - full suite now passes with `59` tests

## 2026-04-29 Confirmed TikTok Link Types

- `https://vt.tiktok.com/ZS9AatQFk/`
  - `Photo-mode Post`
  - 3 image assets + audio
  - no native video URL

- `https://vt.tiktok.com/ZS9AHsXP5/`
  - `Photo-mode Post`
  - 3 image assets + audio
  - no native video URL

- `https://vt.tiktok.com/ZS9AHnKE2/`
  - `Direct Video Post`
  - multiple native MP4 video URLs found
  - proves the direct-video branch is working on real moving-video posts

## 2026-06-04 (Night) — Clover Persona + Nightly Restart Automation

- **Workspace**: MemoryCore confirmed as main; operating as Clover persona (loaded master-memory + main-memory + current-session).
- **Built nightly restart**: Windows Task Scheduler task `Restart Claude Code Daily`, Daily 00:00, Interactive, per-user. Script `orchestration/scripts/restart-claude-code.ps1` kills ONLY the Claude Code CLI (`...\npm\node_modules\@anthropic-ai\claude-code\bin\claude.exe`) and PRESERVES the Claude Desktop app (`WindowsApps\Claude_*`), then relaunches a fresh window via Windows Terminal in the MemoryCore folder.
- **Continuity safeguard**: `orchestration/scripts/checkpoint-session.ps1` runs before the kill — commits dirty MemoryCore git, breadcrumbs `Legendary\00-System\auto-checkpoint-log.md` (vault not a git repo), appends to `SHARED-ACTIVITY-LOG.md`. Logs in `orchestration/logs/`.
- **Standing rule**: script is a mechanical backstop only — Clover authors the intelligent session save (memory + diary + Obsidian mirror) as each session ends.
- **Verified**: non-destructive test passed (kill target = CLI PID only; 7 desktop procs preserved; relaunch spawned+cleaned a fresh CLI). Auto-checkpoint commit `7ca120a`. Legend then chose option B = a true end-to-end restart now (this session's save authored first).
- **Where We Left Off (next session)**: reload via "Legend", confirm the fresh post-restart window came up clean, close any leftover empty terminal window, then resume AI - Shoppee Video v1.0 (TikTok extraction, last 59 tests green).

## 2026-06-06 — Memory Reconciliation + Hermes Sync

- **What this session did**: read the entire MemoryCore + AI - Shoppee Video project state, then reconciled stale memory against reality and against the hermes-agent's live memory.
- **User identity synced**: user's real name is **Harith** (handle "Legend"). Pulled work-style preferences from `C:\Users\Legend\.hermes\memories\USER.md` + `MEMORY.md` + `SOUL.md` into `main/main-memory.md` (action-first, architecture-first, pros/cons+risk before committing, route coding through OpenCode, manual updates over cron). Added Active Projects list (Shopee Video, SalaryCalculatorMY, GO-Ollama eGPU, Hermes automation, Bucket-List).
- **Project state corrected**: AI - Shoppee Video is at **Phases 1–6 / 92 tests** (not the "59 tests / TikTok fallback" state the old recap implies). Telegram bot, caption packs, hook overlays, cover images all shipped. Canonical status: `AI - Shoppee Video v1.0/CODE-REVIEW.md`.
- **tikwm v12 investigated**: branch `codex/tiktok-v12-tikwm-fallback` (commit `cfa939ab`) implemented + tested the tikwm.com fallback but was branched from the 2026-04-29 state and **never merged**; main's CODE-REVIEW still lists it as open gap G2. Next: re-port onto current main (don't merge stale branch).
- **Divergences flagged (need Harith's call)**: (1) hermes says "Claude Code NOT installed" but the nightly task drives the Claude Code CLI — hermes memory stale; (2) hermes vault path = `C:\Users\Legend\Documents\Obsidian Vault`, MemoryCore/orchestration vault = `C:\Users\Legend\Desktop\Obsidian\Legendary` — two vaults, confirm canonical.
- **Did NOT write to hermes memory** — `.hermes\memories\*.md.lock` files present (agent may hold locks); proposed hermes-side updates left for approval.
- **Where We Left Off (next session)**: decide whether to (a) re-port tikwm onto main, and/or (b) push the reconciled facts back into hermes memory + resolve the two divergences.
