# Rekalab Affiliate Video Workflow Analysis

**Project**: AI - Video Workflow  
**Date**: 2026-04-23  
**Use Case**: Shopee and TikTok affiliate product videos  
**Status**: Analysis complete; ready for workflow buildout

## Executive Summary

Rekalab is an all-in-one AI content platform aimed at beginner creators who want fast video, image, copywriting, and content idea generation from a simple prompt. For Shopee and TikTok affiliate work, the workflow is useful because it compresses product research, scripting, visuals, voice, and short-form video creation into one interface.

The same workflow can be recreated outside Rekalab using hosted tools, or partly/fully locally with open-source video generation and automation tools. The best practical path is to start with a hosted or hybrid workflow first, validate what products and hooks convert, then automate more of the workflow later.

## Rekalab Public Site Findings

From Rekalab's public website:

- Claims 60-second videos can be generated with one prompt.
- Claims videos can be ready in about 3 minutes.
- Offers four main content types:
  - AI video
  - Images
  - Copywriting
  - Content ideas
- Shows examples for affiliate/product content.
- Creator plan is listed at RM39/month with 1,600 credits/month.
- Business plan is listed at RM129/month with 7,600 credits/month and priority queue.
- Supports image uploads, motion scene-to-video, AI voice, gallery access, and premium features.

Source: [Rekalab](https://www.rekalab.com/)

## Likely Rekalab Workflow

Rekalab appears to package this general affiliate-content pipeline:

1. User enters a product topic, prompt, or image.
2. AI generates a content idea and short script.
3. AI creates or enhances visuals.
4. Image-to-video or scene-to-video generates motion.
5. AI voice creates narration.
6. Text overlays and captions are added.
7. Video exports in a short-form format suitable for TikTok, Shopee Video, Reels, or Shorts.

## Can This Be Done Without Rekalab?

Yes. The workflow is not unique to Rekalab. Rekalab is valuable because it packages the workflow in one beginner-friendly place, but the underlying steps can be recreated with other tools.

## Recommended Hosted Workflow

This is the recommended starting workflow because it is fast, practical, and does not require GPU setup.

### Tools

- ChatGPT or Codex for product analysis, hook writing, scripts, captions, and prompts.
- Pippit / CapCut Commerce Pro for product-link-to-video workflows, AI product visuals, avatars, voice, scheduling, and analytics.
- CapCut for manual polish, captions, templates, trending audio, and export.
- Runway or Kling for higher-quality image-to-video clips when needed.
- Google Sheets, Notion, or Obsidian for content tracking.

### Workflow

1. Collect product data:
   - Product name
   - Shopee/TikTok product link
   - Price
   - Discount or campaign
   - Main product images
   - Key benefits
   - Reviews and complaints

2. Generate content angle:
   - Problem-solution angle
   - Before-after angle
   - Demo angle
   - Curiosity angle
   - Budget/deal angle

3. Generate video package:
   - 3 hooks
   - 20-35 second script
   - Voiceover text
   - Scene plan
   - Text overlays
   - Caption
   - Hashtags
   - CTA

4. Generate or assemble video:
   - Use Pippit/Rekalab for fast generation.
   - Use Runway/Kling for product motion shots.
   - Use CapCut for final edit.

5. Publish and track:
   - Platform
   - Product link
   - Hook
   - Video version
   - Views
   - Clicks
   - Conversions
   - Commission

Sources:

- [Pippit AI](https://www.pippit.ai/)
- [Runway Gen-4 Video](https://help.runwayml.com/hc/en-us/articles/37327109429011-Creating-with-Gen-4-Video)
- [Runway Gen-4 Prompting Guide](https://help.runwayml.com/hc/en-us/articles/39789879462419-Gen-4-Video-Prompting-Guide)

## Possible Local Workflow

A local workflow is possible, but it is better as a later-stage setup after product-market validation.

### Local Stack

- Local LLM or ChatGPT/Codex for scripts.
- ComfyUI with Wan image-to-video workflow for motion generation.
- Local TTS for voiceover.
- FFmpeg for video assembly.
- Python scripts for batching product videos.
- CapCut or another editor for final manual polish if needed.

### Local Workflow

1. Save product images locally.
2. Generate script and scene plan.
3. Generate product hero images or improved product backgrounds.
4. Animate images using ComfyUI image-to-video.
5. Generate voiceover.
6. Assemble scenes, voice, subtitles, music, and overlays with FFmpeg.
7. Export vertical 9:16 videos.

Source: [ComfyUI Wan Image-to-Video Workflow](https://www.comfy.org/ko/workflows/image_to_video_wan/)

## Hosted vs Local Comparison

| Option | Best For | Pros | Cons |
|---|---|---|---|
| Rekalab | Fast beginner-friendly content | Simple, Malay-market friendly, all-in-one | Credit limits, less control, platform lock-in |
| Pippit / CapCut Commerce Pro | E-commerce and product-link videos | Product-link workflow, templates, AI voice, publishing | Still SaaS-based, licensing must be checked per asset |
| Runway / Kling | Higher-quality motion clips | Better cinematic image-to-video quality | More expensive per generated clip, needs editing workflow |
| Local ComfyUI / Wan | Scale and control | Private, customizable, low per-video cost after setup | Technical setup, GPU needs, slower iteration at first |

## Recommended Path For Legend

Use a three-stage approach:

1. **Validation Stage**
   - Use Rekalab or Pippit to create videos quickly.
   - Test 10-30 products.
   - Track which hooks, niches, and formats convert.

2. **Hybrid Stage**
   - Use Codex for scripts and content systems.
   - Use CapCut templates for repeatable editing.
   - Use Runway/Kling only for high-value product hero clips.
   - Keep tracking every video in a sheet or Obsidian.

3. **Automation Stage**
   - Build a local/semi-local generator.
   - Batch-create hooks, scripts, captions, and scene plans.
   - Use ComfyUI/Wan for video clips if hardware supports it.
   - Use FFmpeg to assemble repeatable formats.

## Affiliate Video Formula

Recommended structure for Shopee and TikTok affiliate videos:

```text
0-2s: Scroll-stopping hook
2-8s: Problem or pain point
8-18s: Product demo or visual proof
18-25s: Benefit or result
25-35s: Price, deal, and CTA
```

## Example Script Template

```text
Hook:
Barang ni nampak simple, tapi kalau rumah selalu bersepah, memang wajib tengok.

Problem:
Meja cepat penuh, barang kecil hilang, kabel pun selalu berserabut.

Demo:
Letak dekat tepi meja, semua remote, cable, charger terus ada tempat.

Benefit:
Meja nampak lebih kemas, senang ambil barang, tak payah cari merata.

CTA:
Saya letak link Shopee dekat sini. Kalau tengah promo, memang berbaloi grab sekarang.
```

## Compliance Notes

### TikTok

TikTok's branded content policy includes content where the creator receives commission through affiliate links or promotional codes. Affiliate content should be disclosed properly.

Source: [TikTok Branded Content Policy](https://www.tiktok.com/legal/page/global/bc-policy/en)

TikTok Shop affiliate creatives used in Shop Ads require affiliate authorization.

Sources:

- [About affiliate creatives for TikTok Shop Ads](https://ads.tiktok.com/help/article/affiliate-creative-videos-in-shop-ads?lang=en)
- [How to authorize affiliate videos for TikTok Shop Ads](https://ads.us.tiktok.com/help/article/how-to-authorize-affiliate-videos-for-shop-ads?lang=en)

### Shopee

Avoid:

- Misleading ads or creatives
- Copyrighted videos
- Bot or software-generated traffic
- Link dumping without content
- Clickbait unrelated to the product
- Impersonating Shopee official channels

Source: [Shopee affiliate restrictions listing](https://affi.io/m/shopee)

## Project Next Actions

- [ ] Pick 3 product niches to test.
- [ ] Choose the first 10 products.
- [ ] Create a repeatable video script template.
- [ ] Build an Obsidian tracker for product videos.
- [ ] Create the first product video package from one Shopee or TikTok product link.
- [ ] Test Rekalab vs Pippit vs CapCut workflow speed.
- [ ] Decide whether local ComfyUI/Wan setup is worth it after validation.

## Suggested Folder Structure

```text
AI - Video Workflow/
├── Rekalab Affiliate Video Workflow Analysis.md
├── Product Video Tracker.md
├── Prompt Library.md
├── Script Templates.md
├── Product Research/
├── Generated Scripts/
├── Video Prompts/
└── Exports/
```
