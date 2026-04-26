# AI - Shoppee Video Analysis and TikTok Design

**Project**: AI - Shoppee Video v1.0  
**Date**: 2026-04-27  
**Status**: Design approved and spec written  

## Summary

This note tracks the approved design for the next upgrade phase:

- add stable `Record ID` values to the masterlist
- add `Analysis Done` tracking
- add manual `Analyze` support for existing downloaded folders
- add direct `Save + Download + Analyze`
- add `product-info.md` and `analysis-result.md` output files
- add public single TikTok video URL support
- change output folder structure to:

```text
output/
  Shopee|TikTok/
    <Shop Name>/
      <Product Name>/
```

## Spec File

Main spec:

```text
docs/superpowers/specs/2026-04-27-ai-shoppee-video-analysis-and-tiktok-design.md
```

## Key Approved Rules

- `Record ID` is the first masterlist column.
- Shopee IDs use `ASV-0000001` format.
- TikTok IDs use `ATV-0000001` format.
- `Analysis Done` is a checkbox-style tracker.
- Shop folders must match case-insensitively and reuse first-saved casing.
- `Analyze` works on existing downloaded media.
- `Save + Download + Analyze` runs analysis immediately after successful download.
- `product-info.md` must be refreshed from saved row data and media counts.
- `analysis-result.md` is the analysis completion artifact.

## Current State

- Design approved by user.
- Spec written.
- Implementation has not started yet in this note.
