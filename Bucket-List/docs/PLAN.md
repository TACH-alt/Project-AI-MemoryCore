# Bucket List – Implementation Plan
*Created: 2026-05-22 | Status: Planning & Research (no code executed yet)*

---

## 1. Goal

Create a personal bucket-list app that lets you quickly capture ideas, organise them by **Food**, **Place**, **Accommodation**, **Things-to-Do**, and gracefully move items from `idea → planned → booked → done → archived` while supporting a lightweight, low-maintenance tech stack for a solo Malaysian developer.

---

## 2. Current Context & Assumptions

- Working on Windows 11 workstation (10.10.10.5) with MSYS bash.
- Hermes Agent, OpenCode & Gemini-CLI are available.
- No existing code for this project – starting from scratch.
- Preference for manual updates over cron-driven changes.
- Clear documentation (ARCHITECTURE.md) and bite-size, test-driven implementation.

---

## 3. Phased Approach

| Phase | Stack | Why |
|-------|-------|-----|
| **MVP** | Notion / Airtable (hosted) | Quick validation, instant mobile sync, no deployment headaches |
| **Iter-1** | Local-first Markdown (Obsidian-style) | Full data ownership, cheap, works offline |
| **Iter-2** | SQLite + Go + HTMX (or FastAPI + Svelte) | Custom UI, map integration, easy to add auth later |
| **Iter-3** | PostgreSQL (Supabase/Turso) + Multi-user | Scalable social version if you ever share lists |

**Recommendation:** Start with Notion for 3 months to settle on fields & workflow, then build the SQLite + Go version.

---

## 4. Research Summary

### 4.1 Market Landscape
Top bucket-list apps (2026) – features, pricing, platforms, UX highlights.
*(Full markdown in `research/market-landscape.md`)*

### 4.2 Data-Model Patterns
Common entities – BucketItem, Media, Location, Collaborators, Milestones.
Smart fields – `social_source_url`, `impact_score`, `privacy_level`.
*(Full markdown in `research/data-model.md`)*

### 4.3 Delightful UX Patterns
Multi-sensory celebrations, AR map overlays, zero-click "Log Visit", predictive UI.
*(Full markdown in `research/ux-patterns.md`)*

### 4.4 User Pitfalls
Discovery gap, ambition graveyard, subscription fatigue, productivity bloat, sync conflicts.
*(Full markdown in `research/pitfalls.md`)*

---

## 5. Detailed Data Schema (SQLite / JSONB)

### BucketItem

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| title | TEXT | Required |
| category | ENUM | food, place, accommodation, things_to_do |
| status | ENUM | idea, planned, booked, done, archived |
| priority | INT | 1-5 |
| geo_lat | FLOAT | Nullable |
| geo_lng | FLOAT | Nullable |
| budget_myr | DECIMAL | Nullable |
| tags | TEXT[] | Flexible tagging |
| source_url | TEXT | Where the idea came from |
| source_note | TEXT | Free-form context |
| created_at | TIMESTAMP | Auto |
| updated_at | TIMESTAMP | Auto |
| metadata | JSONB | Category-specific fields (see below) |

### Category-Specific Metadata (JSONB)

- **Food:** `cuisine_type`, `must_order_dish`, `halal_status`
- **Place:** `best_season`, `duration_days`
- **Accommodation:** `platform`, `booking_ref`
- **Things-to-Do:** `activity_type`, `gear_needed`

### Completion (optional subset)

| Field | Type |
|-------|------|
| completed_date | DATE |
| actual_cost_myr | DECIMAL |
| rating | INT (1-5) |
| reflection | TEXT |
| photos | TEXT[] |

---

## 6. Suggested Workflows

### 1. Quick Capture
Telegram bot receives a link → extracts title + thumbnail via LLM → creates BucketItem with `status=idea`.

### 2. Planning View
Map UI (Mapbox/Leaflet) filters by budget, radius, status → drag-and-drop to change status to `planned`.

### 3. Booking
Inline modal to add `booking_ref`, set dates → mark `booked`.

### 4. Completion
Log actual cost, rating, reflection, photos → mark `done` → celebration UX.

### 5. Archive
Manual or auto-archive after 30 days in `done` status.

---

## 7. Sprint Breakdown (MVP – Notion Phase)

### Sprint 1: Notion Setup
- [ ] Create Notion database with all BucketItem fields
- [ ] Create views: by Category, by Status, Map (if supported)
- [ ] Create template pages for each category
- [ ] Add sample data (5-10 items across categories)

### Sprint 2: Workflow Validation
- [ ] Test the idea → planned → booked → done flow
- [ ] Validate mobile experience (Notion app)
- [ ] Identify missing fields or awkward UX
- [ ] Document findings in `research/notion-mvp-findings.md`

### Sprint 3: Quick Capture Prototype
- [ ] Telegram bot scaffold (Python or Go)
- [ ] Bot receives link, creates Notion page via API
- [ ] Basic LLM extraction (title, category guess)
- [ ] Test with 10 real links

---

## 8. Success Criteria

- Can capture a new idea in < 30 seconds (via Telegram or Notion)
- Can view all items on a map filtered by budget
- Status transitions feel natural and require minimal clicks
- Data is fully exportable at any phase
- Works offline from Iter-1 onwards
