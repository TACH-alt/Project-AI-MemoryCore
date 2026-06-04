# 🔧 Orchestration Protocol v1.0

## Roles & Responsibilities

### Claude (Orchestrator)
- Receives all user requests
- Decides routing: handle directly OR delegate to Gemini
- Curates and validates all Gemini output
- Saves everything to Obsidian
- Updates MemoryCore memory files
- Manages context and handoff when approaching token limits

### Gemini-CLI (Worker)
- Invoked for tasks requiring heavy token usage
- Long-form writing (>500 words)
- Bulk code generation
- Research expansion
- Data analysis and summarization
- Repetitive structured content

### Obsidian (Knowledge Base)
- Permanent record of ALL AI outputs
- Session logs with timestamps
- Searchable, linked knowledge graph
- Daily notes for continuity

---

## Routing Decision Matrix

| Task Type | Route To | Reason |
|-----------|----------|--------|
| Quick answer (<200 words) | Claude | Fast, no overhead |
| Complex reasoning | Claude | Nuanced judgment |
| Memory/context decisions | Claude | Knows your history |
| Long-form writing (>500w) | Gemini | Token efficiency |
| Bulk generation (lists, tables) | Gemini | Scale |
| Code review of large files | Gemini | Context window |
| Research summarization | Gemini | Length |
| Creative writing (long) | Gemini | Token efficiency |
| Simple code snippets | Claude | Speed |
| Strategic planning | Claude | Judgment + memory |

---

## Gemini-CLI Usage

### Basic call
```bash
gemini -p "Your prompt here"
```

### With model selection
```bash
gemini --model gemini-2.0-flash -p "Your prompt"
```

### Pipe to file (save output)
```bash
gemini -p "Write a detailed analysis of X" > output.md
```

### Non-interactive mode (for scripts)
```bash
echo "Your prompt" | gemini --no-interactive
```

---

## Obsidian Vault Structure

```
Legendary/
├── 📊 Dashboard.md              ← Start here every session
├── 00-System/
│   ├── orchestration-protocol.md
│   ├── gemini-setup.md
│   └── handoff-protocol.md
├── 01-Sessions/
│   └── YYYY-MM-DD-NNN.md       ← One per AI session
├── 02-Gemini-Outputs/
│   └── YYYY-MM-DD-[topic].md   ← Raw Gemini outputs
├── 03-Daily-Notes/
│   └── YYYY-MM-DD.md           ← Daily summary
├── 04-Research/
│   └── [topic].md
├── 05-Projects/
│   └── [project-name].md
└── 06-Decisions/
    └── YYYY-MM-DD-[decision].md
```

---

## Claude → Gemini Handoff Protocol

When Claude's context limit approaches (or user requests handoff):

### Step 1: Claude creates handoff file
File: `C:\Users\Legend\Desktop\Obsidian\01-Sessions\HANDOFF-[timestamp].md`

Contents:
- Full conversation summary
- Current task state
- What was completed
- What remains to do
- Exact next steps for Gemini
- Any context Gemini needs

### Step 2: Gemini reads and continues
```bash
gemini -p "Read C:\Users\Legend\Desktop\Obsidian\01-Sessions\HANDOFF-[timestamp].md and continue the session"
```

### Step 3: Gemini saves its work
Gemini outputs get saved to `02-Gemini-Outputs\`

### Step 4: Claude resumes (after refresh)
Claude reads the latest session file and continues seamlessly

---

## Gemini → Obsidian Save Protocol

Every Gemini output must be saved with this header:

```markdown
---
date: YYYY-MM-DD HH:MM
model: gemini-[version]
task: [brief task description]
prompted-by: [claude/user]
tags: [relevant tags]
---
```

---

## Session Continuity

1. Every session starts by reading:
   - `main/current-session.md` (MemoryCore)
   - Latest `01-Sessions/` file (Obsidian)
   - Today's `03-Daily-Notes/` file (Obsidian)

2. Every session ends by updating:
   - `main/current-session.md`
   - Today's daily note
   - Session log

---
*Protocol Version: 1.0 | Created: 2026-04-23*
