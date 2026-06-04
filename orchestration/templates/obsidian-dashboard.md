# 🧠 Legend's AI Command Center

> *Orchestrated by Claude · Powered by Gemini · Remembered in Obsidian*

---

## ⚡ Quick Actions

| Action | Command |
|--------|---------|
| Start new session | `scripts\new-session.bat` |
| Ask Gemini something | `scripts\ask-gemini.bat "prompt" "title" "folder"` |
| Create today's note | `scripts\daily-note.bat` |
| Handoff to Gemini | `scripts\handoff-to-gemini.bat` |
| Fix Gemini install | `scripts\setup-gemini.bat` |

> 📁 Scripts live at: `C:\Users\Legend\Documents\Claude\Projects\MemoryCore\orchestration\scripts\`

---

## 📅 Daily Notes
```dataview
LIST
FROM "03-Daily-Notes"
SORT file.name DESC
LIMIT 7
```

## 🤖 Recent Sessions
```dataview
LIST
FROM "01-Sessions"
SORT file.name DESC
LIMIT 5
```

## ⚡ Recent Gemini Outputs
```dataview
LIST
FROM "02-Gemini-Outputs"
SORT file.mtime DESC
LIMIT 5
```

---

## 🏗️ System Status

| Component | Status | Notes |
|-----------|--------|-------|
| Claude (Cowork) | 🟢 Active | Orchestrator |
| Gemini-CLI | ⚠️ Check | Run setup-gemini.bat if needed |
| Obsidian Vault | 🟢 Active | Legendary |
| MemoryCore | 🟢 Active | Legend persona |

---

## 🗂️ Vault Navigation

- 📁 [[01-Sessions/]] — AI session logs
- 📁 [[02-Gemini-Outputs/]] — All Gemini responses
- 📁 [[03-Daily-Notes/]] — Daily summaries
- 📁 [[04-Research/]] — Research outputs
- 📁 [[05-Projects/]] — Project tracking
- 📁 [[06-Decisions/]] — Decision log
- 📁 [[00-System/]] — Protocols & setup

---

## 🔁 How Routing Works

```
Your Request
    ↓
Claude analyzes
    ↓
Short/complex → Claude handles directly
Long/bulk     → Gemini handles, Claude curates
    ↓
Everything saved here to Obsidian
    ↓
MemoryCore updated for continuity
```

---

## 🆘 Claude Context Limit Protocol

If Claude says "approaching context limit":
1. Claude creates `01-Sessions/HANDOFF-[time].md`
2. Run: `scripts\handoff-to-gemini.bat`
3. Gemini reads handoff and continues
4. When Claude refreshes → reads latest session file and resumes

---
*Last updated: 2026-04-23 | System v1.0*
