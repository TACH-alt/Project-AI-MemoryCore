# Hermes Agent Utilization Plan

**Project**: AI - Video Workflow (and future projects)  
**Date**: 2026-05-01  
**Status**: Planned — not yet implemented  
**Decision Type**: Infrastructure and automation strategy

## Why This Note Exists

Legend has a Hermes AI agent running on Proxmox VM (10.10.10.2) with Claude Opus 4 via 9Router. This note documents how Hermes should be utilized across current and future projects as a background worker, automation server, research agent, dev server, and collaboration partner.

## Current Hermes State

| Aspect | Value |
|---|---|
| Host | Proxmox VM at `10.10.10.2` |
| OS | Linux (Debian/Ubuntu) |
| User | `legend` |
| AI Agent | Claude Code-style CLI agent |
| LLM Provider | 9Router (`http://127.0.0.1:20128/v1`) |
| Model | `cc/claude-opus-4-7` |
| Config | `/home/legend/.hermes/config.yaml` |
| Status | Running but idle — no services, no automation |

## Five Use Cases

### 1. Background Batch Processing

**Purpose**: Offload long-running compute tasks from Legend's Windows desktop.

**For AI Shoppee Video v1.0:**

- Process pending masterlist rows (download + render) while Legend works on other things
- Bulk TikTok/Shopee media downloads
- FFmpeg video rendering (Linux FFmpeg is often faster than Windows)
- LLM-powered caption/hook generation in batch

**For future projects:**

- Any CPU/GPU-intensive batch job
- Data processing pipelines
- Bulk API calls with rate limiting

**Requirements to implement:**

```text
- Install: FFmpeg, Python 3.12+, yt-dlp, pip packages (openpyxl, requests)
- Sync project scripts to Hermes (git clone or rsync)
- Shared masterlist access (network share, rsync, or git-based sync)
- Output folder accessible from Windows (SMB share or rsync back)
```

---

### 2. Scheduled Automation (Cron)

**Purpose**: Run recurring tasks without manual intervention.

**Planned cron jobs:**

| Schedule | Task | Project |
|---|---|---|
| Every 30 min | Check masterlist for new pending rows → auto-process | AI Shoppee Video |
| Daily 6:00 AM | Health check: 9Router, disk space, services | Infrastructure |
| Daily 8:00 AM | Pull latest project changes from git | All projects |
| On webhook | Process specific record ID triggered via Telegram | AI Shoppee Video |

**Requirements to implement:**

```text
- systemd timers or crontab entries
- Logging to /home/legend/logs/ with rotation
- Notification on failure (Telegram bot message)
- Lock files to prevent overlapping runs
```

---

### 3. Research & Analysis Agent

**Purpose**: Hermes researches topics, analyzes code, writes reports while Legend focuses elsewhere.

**Workflow:**

1. Legend SSHs into Hermes or sends a task via shared file
2. Hermes agent picks up the task and works autonomously
3. Results written to a shared location (e.g., `/home/legend/research/`)
4. Legend reviews results when ready

**Example tasks:**

- "Analyze this GitHub repo and write a summary of applicable techniques"
- "Research FFmpeg xfade transitions and write example commands"
- "Review this Python file for bugs and write a report"
- "Compare these 3 TikTok scraping libraries and recommend one"

**Requirements to implement:**

```text
- Task inbox: /home/legend/tasks/inbox/ (one .md file per task)
- Task output: /home/legend/tasks/done/ (results written here)
- Hermes watches inbox and processes tasks
- Simple protocol: filename = priority-timestamp-description.md
```

---

### 4. Development Server

**Purpose**: Host always-on services accessible from Legend's LAN.

**Planned services:**

| Service | Port | Purpose |
|---|---|---|
| Shoppee Video Frontend | `10.10.10.2:8766` | Web UI for masterlist management |
| Telegram Bot | (outbound only) | Always-on bot for mobile workflow |
| 9Router | `10.10.10.2:20128` | LLM proxy (already running) |
| OpenReel Video (future) | `10.10.10.2:3000` | Self-hosted video editor |
| Task Dashboard (future) | `10.10.10.2:8080` | View task queue and results |

**Requirements to implement:**

```text
- systemd service files for each service
- Reverse proxy (nginx/caddy) for clean URLs (optional)
- Firewall rules: allow LAN (10.10.10.0/24), block WAN
- Auto-restart on crash (systemd Restart=always)
```

---

### 5. Multi-Agent Collaboration (OpenCode ↔ Hermes)

**Purpose**: Two AI agents working in parallel — one researches while the other implements.

**Protocol design:**

```text
Shared location: /home/legend/collab/ (mounted as SMB or synced via rsync)

Structure:
  collab/
    tasks/
      pending/     ← OpenCode drops task files here
      in-progress/ ← Hermes moves tasks here while working
      done/        ← Hermes moves completed tasks here
    results/       ← Hermes writes output files here
    signals/       ← Simple coordination signals
```

**Task file format:**

```markdown
# Task: <short description>
Priority: high | medium | low
From: opencode
Requested: 2026-05-01T14:30:00

## Instructions
<detailed task description>

## Expected Output
<what should be returned>
```

**Result file format:**

```markdown
# Result: <task description>
Completed: 2026-05-01T15:00:00
Duration: 30 min

## Summary
<brief summary>

## Details
<full output>
```

**Alternative: Telegram-based coordination**

- Legend sends task to Telegram bot
- Hermes picks up via bot polling
- Results sent back as Telegram message or file

**Requirements to implement:**

```text
- SMB share from Hermes accessible on Windows (\\10.10.10.2\collab)
  OR rsync/syncthing between machines
- Hermes watcher script (inotifywait or polling loop)
- Task validation and error handling
- Timeout for stuck tasks
```

---

## Implementation Sequence (When Ready)

| Phase | Tasks | Enables |
|---|---|---|
| **Phase 1** | Install FFmpeg, Python, yt-dlp on Hermes; clone project; verify render works | Batch processing |
| **Phase 2** | Deploy Telegram bot as systemd service | Mobile workflow, notifications |
| **Phase 3** | Set up cron jobs for auto-processing | Scheduled automation |
| **Phase 4** | Deploy frontend on Hermes | LAN-accessible web UI |
| **Phase 5** | Set up shared task queue (SMB or file-based) | Multi-agent collaboration |
| **Phase 6** | Add research agent watcher | Autonomous research |

## Network Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    Home LAN (10.10.10.0/24)              │
│                                                         │
│  ┌──────────────┐         ┌──────────────────────────┐  │
│  │ Legend's PC   │         │ Hermes (Proxmox VM)      │  │
│  │ 10.10.10.5   │◄───────►│ 10.10.10.2               │  │
│  │              │  SSH/SMB │                          │  │
│  │ - OpenCode   │         │ - 9Router (:20128)       │  │
│  │ - Claude     │         │ - Hermes Agent           │  │
│  │ - VS Code    │         │ - Telegram Bot           │  │
│  │              │         │ - Frontend (:8766)       │  │
│  │              │         │ - FFmpeg + Python        │  │
│  │              │         │ - Cron jobs              │  │
│  └──────────────┘         └──────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Standing Decisions

- Hermes stays on LAN only — no public internet exposure
- All services use systemd for lifecycle management
- Logs go to `/home/legend/logs/` with daily rotation
- Hermes uses 9Router for LLM access (not direct API)
- Shared files use SMB or rsync (decide during Phase 5)
- Telegram bot is the primary mobile interface

## Obsidian Sync Requirement

This note should be mirrored into the Legendary vault topic folder:

```text
C:\Users\Legend\Desktop\Obsidian\Legendary\05-Projects\AI - Video Workflow\
```
