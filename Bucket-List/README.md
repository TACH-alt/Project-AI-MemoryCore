# 🪣 Bucket List

Personal bucket-list app for capturing and organising life goals across **Food**, **Place**, **Accommodation**, and **Things-to-Do** categories.

## Status

**Phase**: Planning & Research (no code yet)  
**Started**: 2026-05-22  
**Owner**: Legend  

## Goal

Quickly capture ideas, organise them by category, and gracefully move items through:

```
idea → planned → booked → done → archived
```

## Phased Approach

| Phase | Stack | Purpose |
|-------|-------|---------|
| MVP | Notion / Airtable | Quick validation, instant mobile sync |
| Iter-1 | Local-first Markdown (Obsidian-style) | Full data ownership, offline |
| Iter-2 | SQLite + Go + HTMX (or FastAPI + Svelte) | Custom UI, map integration |
| Iter-3 | PostgreSQL (Supabase/Turso) + Multi-user | Scalable social version |

## Quick Capture (Future)

Telegram bot receives a link → LLM extracts title + thumbnail → creates BucketItem with status `idea`.

## Project Structure

```
Bucket-List/
├── README.md              # This file
├── ARCHITECTURE.md        # System design & decisions
├── research/              # Market landscape, data models, UX patterns, pitfalls
├── docs/                  # Specs, plans, workflow diagrams
├── data/                  # Schema definitions, sample data, Notion templates
├── scripts/               # Automation, Telegram bot, migration tools
└── tests/                 # Test files when code phase begins
```

## Links

- Plan: `.hermes/plans/2024-05-22_165200-bucket-list-plan.md`
- Obsidian: `05-Projects/Bucket-List/`
