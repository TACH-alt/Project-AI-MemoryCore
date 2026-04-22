---
name: observation
description: "MUST use when user says 'survey project', 'scan project', 'investigate', 'deep dive', 'refine code', 'audit system', or when the AI needs to assess project health before planning. Follows tiered observation protocol."
---

# Observation System

## Activation
When this skill activates, output:
`👁️ Observation System...`

## Protocol
1. **Determine Depth**:
   - **Survey (Lv.1)**: Quick bird's-eye view (structure, stack, health).
   - **Investigate (Lv.2)**: Trace bugs or reveal hidden patterns in a specific area.
   - **Refine (Lv.2)**: Corrective review of changed code.
   - **Audit (Lv.3)**: Full system audit of connections and data flows.
2. **Execute Tier**: Follow the specific steps for the chosen depth (see `SKILL.md` in plugin folder).
3. **Escalate**: Suggest a deeper tier if findings warrant it.

## Mandatory Rules
1. **Dependency Scan First** — understand the actual tech stack before analyzing code.
2. **Permission to Fix** — Refine must always ask before applying any changes.
3. **Narrative Findings** — present findings as stories, not just raw data dumps.

## Level History
- **Lv.1** — Base: Four-tier tiered code awareness (Survey, Investigate, Refine, Audit). (Installed 2026-04-22)
