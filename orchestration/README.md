# 🧠 AI Orchestration System — Legend's Stack

**Three-layer intelligence pipeline running on your PC.**

| Layer | Tool | Role |
|-------|------|------|
| 🎯 Orchestrator | Claude (Cowork) | Planning, routing, memory, quality control |
| ⚡ Worker | Gemini-CLI | Heavy generation, bulk tasks, long-form content |
| 📚 Knowledge Base | Obsidian (Legendary vault) | All outputs, sessions, research, decisions |

---

## How It Works

```
You → Claude (orchestrator)
          ↓
    Analyze task complexity
          ↓
    ┌─────┴──────┐
Claude handles  Gemini handles
(short/complex) (long/bulk/heavy)
    └─────┬──────┘
          ↓
    Result formatted
          ↓
    Saved to Obsidian
          ↓
    MemoryCore updated
```

## Quick Commands

| What you want | Run |
|--------------|-----|
| Ask Gemini something | `scripts\ask-gemini.bat "your prompt"` |
| Save content to vault | `scripts\save-to-obsidian.bat "folder" "title" "content"` |
| Create today's note | `scripts\daily-note.bat` |
| Handoff to Gemini | `scripts\handoff-to-gemini.bat` |
| Fix/install Gemini-CLI | `scripts\setup-gemini.bat` |

## Vault Location
`C:\Users\Legend\Desktop\Obsidian` (vault name: Legendary)

## MemoryCore Location
`C:\Users\Legend\Documents\Claude\Projects\MemoryCore`

---
*Built: 2026-04-23 | Architect: Claude Orchestrator*
