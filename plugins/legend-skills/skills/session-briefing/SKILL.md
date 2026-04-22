---
name: session-briefing
description: "MUST use at the start of every session, before responding to the first message, or when user says 'brief', 'status', 'where were we'. Delivers a context brief from session-brief-core.md."
---

# Session Briefing

## Activation
When this skill activates, output:
`📋 Session Briefing...`

## Protocol
1. **Load Context**: Read `main/current-session.md` (Session Recap) and `main/session-brief-core.md`.
2. **Time Check**: Get current time via `Get-Date` (Windows) or `date` (macOS/Linux) for energy classification.
3. **Scan Dependencies**:
   - Check `main/reminders.md` for open tasks (if exists).
   - Check `projects/` for active/idle projects (if LRU installed).
4. **Deliver Brief**: Follow the template in `session-brief-core.md` to present:
   - Time period (Morning/Afternoon/Evening/Night)
   - Last session summary
   - Active focus & progress flags
   - Open reminders
   - Suggested work focus based on time.

## Mandatory Rules
1. **Be Concise** — the brief should be readable in 5 seconds.
2. **Proactive** — deliver automatically after a context reset/restart.
3. **Evidence-based** — only summarize what's in the files.

## Level History
- **Lv.1** — Base: Automated session-start context brief. (Installed 2026-04-22)
