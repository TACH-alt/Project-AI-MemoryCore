---
name: image-prompt
description: "Auto-triggers when user asks for a Midjourney or NijiJourney image prompt, when creating visual art prompts, or when user says 'midjourney prompt', 'niji prompt', 'create prompt', 'image prompt'. Generates optimized prompts with composition-aware framing."
---

# Image Prompt System

## Activation
When this skill activates, output:
`🎨 Generating image prompt...`

## Protocol
1. **Parse Request**: Identify the subject, mood, setting, and style.
2. **Detect Mode**: 
   - **Character Mode**: Use the character profile from main-memory.md (if exists).
   - **Freeform Mode**: For landscapes, objects, or non-character scenes.
3. **Select Composition**: Choose a shot type (Extreme Wide, Close-Up, POV, etc.) and place it FIRST in the prompt.
4. **Build Prompt**: Assemble using the weight-based order: `[SHOT] → [SUBJECT] → [DETAILS] → [SETTING] → [ACTION] → [MOOD] → [QUALITY] → [MODEL FLAG]`.
5. **Safety Check**: Ensure the prompt is moderator-safe and artistic.
6. **Present**: Output the complete prompt in a code block with the appropriate flag (`--niji 7` or `--v 7`).

## Mandatory Rules
1. **Composition-First** — every prompt MUST have a shot type framing.
2. **Weight-Aware** — place the most important tokens at the beginning.
3. **Consistent Style** — follow the user's preferred style preset (Anime, Realistic, etc.).

## Level History
- **Lv.1** — Base: Composition-aware MJ/Niji prompt generation with character/freeform modes. (Installed 2026-04-22)
