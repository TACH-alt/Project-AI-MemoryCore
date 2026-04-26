# Shopee Link and Media Analysis Workflow

**Project**: AI - Shoppee Video v1.0  
**Date**: 2026-04-24  
**Status**: Planning note for next improvement  
**Purpose**: Expand the current downloader/editor into a product-analysis and hook-generation workflow for affiliate content

## Why This Note Exists

Legend asked for the next improvement after the current Shopee downloader/frontend work:

1. analyze the link that is shared
2. analyze the downloaded video or image media
3. generate a second workflow for hooks, script ideas, clip order, and post-ready affiliate variations

This note folds in the useful ideas from `C:\Users\Legend\Downloads\faceless_affiliate_shopee_tiktok_workflow.md` and maps them onto the existing local web app.

## What The Imported Workflow Adds

The imported handoff note is strong in four areas that the current local app does not yet cover:

### 1. One Product Should Create Multiple Videos

Useful operating rule:

```text
Same footage + different hook + different script + different clip order = different post
```

This is a good fit for the current project because the app already downloads and organizes media by product folder. The missing layer is content analysis and variant generation.

### 2. Hooks And Angles Should Be Generated Per Product

The handoff note recommends generating multiple angles such as:

- problem-solving
- value-for-money
- review / worth-it
- premium look
- practical use
- family / lifestyle fit

This should become a structured output of the web app, not just a manual brainstorming step.

### 3. Clip-Level Suggestions Matter

The handoff note goes beyond generic scripts. It breaks seller video into:

- timestamp ranges
- best clips by angle
- recommended clip order
- ready-to-use on-screen text
- ready-to-use voiceover

That is the clearest missing bridge between the current downloader and a real affiliate production system.

### 4. CapCut Should Be Treated As A Handoff Target

The current local app can download and render, but the imported note assumes a more practical creator workflow:

- AI/system suggests hooks and scene order
- human does final trim, polish, voice, music, and timing in CapCut

That is a better fit than trying to fully automate every creative decision in FFmpeg.

## Recommended Product-Analysis Workflow

The next workflow should sit beside the current `Save` and `Download` path.

### Trigger

Allow analysis from either:

- a full Shopee product URL
- a direct approved media URL
- an already-downloaded raw file inside the product folder

### Stage 1: Product Summary

Build a structured product summary from the link and masterlist row:

- product name
- shop name
- source type
- product category guess
- main problem solved
- top visible features
- target buyer guess
- cautions to avoid overclaiming

Output artifact:

```text
output/<product-folder>/analysis/product-summary.json
output/<product-folder>/analysis/product-summary.md
```

### Stage 2: Media Analysis

Inspect the downloaded media and produce usable editing notes:

- duration
- resolution
- fps
- audio present or not
- scene/shot boundaries
- high-motion vs static sections
- visible text/OCR if practical
- candidate hero shots
- candidate proof shots
- candidate closing/CTA shots

Output artifact:

```text
output/<product-folder>/analysis/media-analysis.json
output/<product-folder>/analysis/media-analysis.md
```

### Stage 3: Hook Package Generation

Generate 3 to 5 affiliate content packages per product.

Each package should include:

- angle name
- hook
- 15-18 second voiceover
- on-screen text lines
- soft CTA
- short caption
- suggested clip order
- suggested timestamps when available

Output artifact:

```text
output/<product-folder>/analysis/hook-pack.json
output/<product-folder>/analysis/hook-pack.md
```

### Stage 4: Editor Handoff

Create a handoff bundle for manual finishing in CapCut or another editor.

Recommended contents:

- raw media path
- edited media path, if any
- product summary
- best 3 hook packages
- timestamp suggestions
- caption text
- voiceover text
- notes for music, trim, or CTA

Output artifact:

```text
output/<product-folder>/handoff/README.md
output/<product-folder>/handoff/handoff.json
```

## What Can Be Automated Reliably

These are realistic for the current local-first stack:

- extract product metadata from the saved row and best-effort Shopee page HTML
- inspect local media with `ffprobe`
- detect rough scene changes from video frames
- generate hook/script/caption variants from rules plus AI prompting
- save reusable markdown and JSON output per product
- expose the analysis results inside the web app

## What Should Stay Manual Or Review-Based

These should not be treated as fully automatic truth:

- exact product claims not visible in the listing or media
- final timestamp precision for every clip without human review
- final voice, music, hook style, and pacing choice
- compliance-sensitive statements such as stock status, exact price, or medical/performance claims

## Best UX For The Web App

The current frontend should gain an analysis lane, not just a download lane.

### Suggested Buttons

- `Save`
- `Download`
- `Analyze`
- `Open Analysis`
- `Open Handoff`

### Suggested Screen Sections

- masterlist input form
- product/media status table
- analysis summary panel
- hook package list
- handoff export section

### Suggested Per-Row Outputs

For each completed row, show:

- download status
- analysis status
- best hook title
- number of generated angle packages
- link to raw media
- link to analysis markdown
- link to handoff folder

## Recommended Implementation Order

This should be built in small slices.

### Phase 1: Product And Media Analysis

Add a post-download analysis step that writes:

- `product-summary.md`
- `media-analysis.md`

This gives immediate value and low risk.

### Phase 2: Hook Package Generator

Generate 3 to 5 structured affiliate angles from the row plus media-analysis output.

This is the first phase that turns the app from downloader into content assistant.

### Phase 3: Frontend Review Panel

Show the generated hooks, captions, and clip suggestions inside the web app with copy/open buttons.

### Phase 4: Editor Handoff Bundle

Create the CapCut-friendly handoff package with markdown, JSON, and reusable copy.

## Recommended First Slice

The next improvement should be:

```text
Add an Analyze workflow that runs after a successful download and writes product-summary.md, media-analysis.md, and hook-pack.md into each product folder.
```

Why this first:

- it does not interfere with Claude's current frontend/render work
- it creates reusable value even before deeper editor integration
- it gives a clean base for CapCut handoff later

## Relationship To Existing Project Notes

This planning note extends:

- `AI - Shoppee Video v1.0.md`
- `AI - Shoppee Video Future Improvements.md`
- `CapCut Affiliate Video Workflow Plan.md`

It does not replace the current downloader/editor workflow. It adds a second layer focused on affiliate content strategy and manual-finishing support.

## Save Point - 2026-04-26

This planning note was re-saved into MemoryCore and mirrored into the Legendary Obsidian vault on 2026-04-26 before any new implementation phase began.

Status at this save point:

- planning note complete
- no code implementation started yet for the analysis workflow
- next likely step is to convert this note into a concrete implementation plan
