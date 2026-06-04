---
date: {{DATE}}
time: {{TIME}}
type: handoff
from: Claude (Cowork)
to: Gemini-CLI
status: pending-pickup
tags: [handoff, session-transfer]
---

# 🔁 Session Handoff — Claude → Gemini

**Handoff Time:** {{DATE}} {{TIME}}
**Reason:** {{REASON}}
**Session:** [[01-Sessions/{{SESSION_FILE}}]]

---

## 🎯 What We Were Doing

{{CURRENT_TASK_DESCRIPTION}}

---

## ✅ What Claude Completed

{{COMPLETED_ITEMS}}

---

## 🔄 What Needs To Continue

{{REMAINING_TASKS}}

---

## 💬 Key Context Gemini Must Know

{{IMPORTANT_CONTEXT}}

---

## 📁 Relevant Files

{{RELEVANT_FILES}}

---

## 🤖 Instructions for Gemini

You are continuing a session started by Claude. Here is exactly what to do:

1. Read this entire handoff note carefully
2. Review any files listed under "Relevant Files"
3. Continue the tasks listed under "What Needs To Continue"
4. Save ALL your outputs to the Obsidian vault: `C:\Users\Legend\Desktop\Obsidian`
5. Log your progress in: `01-Sessions\{{SESSION_FILE}}`
6. Tag all your outputs with `gemini` and the current date

### Obsidian Save Command
```
scripts\ask-gemini.bat "your prompt" "output-title" "target-folder"
```

### When you finish each task
Update the session note: `01-Sessions\{{SESSION_FILE}}`
Add completed items to the `## ✅ Completed` section.

---

## 🔮 When Claude Returns

Claude will read this file and the session log to resume.
Gemini: When Claude returns, update this note's status to `completed` and
add a summary of what you accomplished.

---
*Handoff created by Claude Orchestrator | v1.0*
