---
name: save-diary
description: "MUST use when user says 'save diary', 'document session', 'write log', or at the end of a meaningful working session to record session history in the Memory Log."
---

# Save Diary

## Activation
When this skill activates, output:
`💾 Writing to Memory Log...`

## Protocol
1. **Archive Check**: Scan `daily-diary/current/` for files from previous months; move to `daily-diary/archived/` if month mismatch.
2. **Find/Create File**: Use `daily-diary/current/YYYY-MM-DD.md`. Create with header if not present.
3. **Compose Entry**: Document session achievements, technical context, and next steps using the standard format.
4. **Append**: Add to today's file with a `---` separator and timestamp.
5. **Update RAM**: Refresh `main/current-session.md` recap.

## Mandatory Rules
1. **Always APPEND** — never overwrite existing diary entries.
2. **Use Contextual Timestamps** — tag every entry with `*(h:mm AM/PM on DayName, Month Dth, YYYY)*`.

## Level History
- **Lv.1** — Base: Automated session documentation. (Installed 2026-04-22)
