---
name: interactive-story
description: "Auto-triggers when user says 'new adventure', 'start adventure', 'save adventure', 'resume adventure', 'VN mode'. Manages Visual Novel RPG adventures with choice-based storytelling and cinematic combat."
---

# Interactive Story System

## Activation
When this skill activates for a new adventure, pick an evocative portal line (e.g., `*a shimmering portal tears through reality*`) and begin setup.

## Protocol
1. **Setup**: Choose Play Mode (Duo/Solo), Power Level (OP/Balanced), and World Type (Fantasy, Steampunk, etc.).
2. **Character Creation**: Create hero (and companion if Duo) with named abilities.
3. **World Generation**: Create `adventures/[world-name]/` with settings and summary files.
4. **Cinematic Narration**: Use full light-novel-quality prose for every scene.
5. **Choice-Based**: Every scene ends with a choice box (3-4 actions + 1 dialogue).
6. **Combat**: Minimum 2 choreographic exchanges with named techniques and prose-based impact.
7. **Persistence**: Save progress to markdown files on "save adventure" and update session memory.

## Mandatory Rules
1. **Rich Prose** — write MORE, not less. Full sensory details.
2. **Choice Box Mandatory** — never leave the player without options.
3. **Evidence-Based Recall** — load summary and last 50 lines on resume.

## Level History
- **Lv.1** — Base: Visual Novel RPG engine with duo/solo modes, OP/balanced levels, and cinematic combat. (Installed 2026-04-22)
