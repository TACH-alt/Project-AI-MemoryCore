---
name: save-memory
description: "MUST use when user says 'save', 'save memory', 'save progress', 'update memory', or when important information from the current conversation needs to be preserved to Legend's memory files. Triggers on any explicit persistence request, and proactively when a significant preference, decision, or context worth keeping emerges."
---

# Save Memory

## Activation

When this skill activates, output:

`💾 Saving memory...`

Then execute the protocol below.

## Context Guard

save-memory activates only in appropriate contexts.

| Context | Status |
|---------|--------|
| **User says "save", "save memory", "save progress", "update memory"** | ACTIVE — full protocol |
| **Significant preference or decision emerged this session** | ACTIVE — full protocol |
| **End of a meaningful working session** | ACTIVE — full protocol |
| **Casual conversation with no new persistent info** | DORMANT — do not activate |
| **Already saved this exact info this session** | DORMANT — skip redundant save |

## Protocol

### Step 1: Identify What to Save
- [ ] Scan current conversation for new, genuinely important information
- [ ] Categorize: preference (→ main-memory), decision (→ current-session), milestone (→ both)
- [ ] Flag items that would be lost without preservation

### Step 2: Update main/main-memory.md
- [ ] New communication preferences → `Legend Profile (User) > Communication Patterns`
- [ ] New focus areas or skills → `Legend Profile (User) > Work / Study Patterns`
- [ ] New motivators or things-to-avoid → `Legend Profile (User) > Personal Preferences`
- [ ] Relationship milestones → `Relationship Context > Interaction History` (with date)
- [ ] Never overwrite existing content blindly — append or refine

### Step 3: Update main/current-session.md
- [ ] Update `Active Context` with current topic / recent progress / next steps
- [ ] Add entries to `Session Achievements`
- [ ] Refresh `Session Recap` so a restart picks up cleanly
- [ ] Verify file line count stays under 500 (auto-reset if exceeded per session-format.md)

### Step 4: Confirm
- [ ] Display a brief summary of what was saved and to which file
- [ ] Confirm all writes succeeded
- [ ] Output: `✅ Memory saved. Ready to continue.`

## Mandatory Rules

1. **Only save genuinely important information** — not every conversational detail
2. **Preserve existing content** — append or update, never wipe without reason
3. **Always confirm** what was saved, in one short summary line per file touched
4. **Respect the 500-line session limit** — trigger session reset if this save would push it over

## Edge Cases

| Situation | Behavior |
|-----------|----------|
| **User says "save" but nothing new this session** | Confirm "Nothing new to save — session recap is current." Do not write. |
| **Memory files missing** | Report which file is missing; do not silently recreate. |
| **Conflict with existing info** | Ask user which version to keep before overwriting. |
| **Session over 500 lines** | Trigger RAM reset per session-format.md before saving, then save into fresh file. |

## Level History

- **Lv.1** — Base: Save conversation insights to memory files on command. (Origin: 2026-04-22, installed with Skill Plugin System Tier 1 feature.)
