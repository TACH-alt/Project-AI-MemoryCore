# Architecture — Bucket List

## Design Principles

1. **Start simple, scale later** — Notion MVP validates workflow before writing code
2. **Data ownership** — All data exportable; no vendor lock-in
3. **Offline-first** — Works without internet (from Iter-1 onwards)
4. **Malaysian context** — Halal status, MYR budget, local categories
5. **Low maintenance** — Solo dev, no cron-driven updates unless necessary

## Data Model

### Core Entity: BucketItem

```
id              UUID
title           TEXT
category        ENUM (food | place | accommodation | things_to_do)
status          ENUM (idea | planned | booked | done | archived)
priority        INT (1-5)
geo_lat         FLOAT (nullable)
geo_lng         FLOAT (nullable)
budget_myr      DECIMAL (nullable)
tags            TEXT[] 
source_url      TEXT (nullable)
source_note     TEXT (nullable)
created_at      TIMESTAMP
updated_at      TIMESTAMP
metadata        JSONB (category-specific fields)
```

### Category-Specific Metadata (JSONB)

**Food:**
- `cuisine_type` — e.g. Japanese, Malay, Western
- `must_order_dish` — signature item
- `halal_status` — certified | muslim-owned | non-halal | unknown

**Place:**
- `best_season` — e.g. "March-May"
- `duration_days` — recommended trip length

**Accommodation:**
- `platform` — Airbnb | Booking.com | Agoda | direct
- `booking_ref` — reference number when booked

**Things-to-Do:**
- `activity_type` — adventure | cultural | wellness | learning
- `gear_needed` — equipment list

### Completion Record (subset)

```
completed_date  DATE
actual_cost_myr DECIMAL
rating          INT (1-5)
reflection      TEXT
photos          TEXT[]
```

## Status Flow

```
idea ──→ planned ──→ booked ──→ done ──→ archived
  │         │          │                    ↑
  │         │          └────────────────────┘ (skip done)
  │         └───────────────────────────────┘ (cancel/archive)
  └─────────────────────────────────────────┘ (discard)
```

## Workflows

### 1. Quick Capture (Telegram Bot)
- Receive link or text via Telegram
- LLM extracts: title, category guess, thumbnail
- Creates BucketItem with status=idea
- User confirms or edits via inline keyboard

### 2. Planning View (Map UI)
- Mapbox/Leaflet map with pins by category
- Filter by: budget range, radius, status, tags
- Drag-and-drop to change status to planned

### 3. Booking Flow
- Inline modal: add booking_ref, set dates
- Mark status=booked
- Optional: calendar integration

### 4. Completion
- Log actual cost, rating, reflection, photos
- Mark status=done
- Trigger celebration UX

## Tech Stack Decisions

### MVP (Current Phase)
- **Notion** database with views per category
- **Notion API** for future migration scripting
- Template pages for each category type

### Iter-2 (Target Build)
- **Go + HTMX** — lightweight, fast, single binary deploy
- **SQLite** — zero-ops database, JSONB for metadata
- **Leaflet** — open-source maps (no Mapbox billing)
- **Telegram Bot API** — quick capture integration

### Why Go + HTMX over FastAPI + Svelte
- Single binary deployment (no Node runtime needed)
- Lower memory footprint for personal use
- HTMX keeps frontend simple without SPA complexity
- Go's stdlib handles HTTP, JSON, SQLite well

## Security & Privacy

- All data local by default (SQLite file)
- No analytics or tracking
- Photos stored locally, not cloud
- Telegram bot token stored in env var, not code
- Future multi-user: row-level security via Supabase RLS
