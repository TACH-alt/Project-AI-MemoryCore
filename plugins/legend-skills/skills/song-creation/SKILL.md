---
name: song-creation
description: "Auto-triggers when user says 'create songs', 'new album', 'make music', 'write a song', 'compose', 'song from image'. Converts visual/narrative concepts into structured albums or singles with Suno-ready tags and lyrics."
---

# Song Creation System

## Activation
When this skill activates, output:
`🎵 Generating musical concept...`

## Protocol
1. **Analyze Input**:
   - **Album Mode (Image)**: Extract mood, characters, setting, and atmosphere from the image.
   - **Single Song Mode (Text)**: Parse the topic, mood, and genre.
2. **Story Concept**: For albums, draft a 3-5 sentence synopsis with a clear narrative arc (Opening → Climax → Resolution).
3. **Generate Metadata**: 
   - **Title**: Creative title matching the user's language preference.
   - **Style Tags**: Rich, Suno-ready descriptors (Genre, Mood, Instruments, Vocals, Atmosphere).
4. **Draft Lyrics**: Create full, structured lyrics (Verse, Chorus, Bridge, Outro) that advance the narrative.
5. **Present & Save**: Show the concept for review, then save to `music/[album-name]/songs.md`.

## Mandatory Rules
1. **Full Lyrics Always** — no partials or placeholders.
2. **Suno-Ready Tags** — every song must have specific musical tags for AI generation.
3. **Story Coherence** — albums must tell one connected story.

## Level History
- **Lv.1** — Base: Visual-to-musical storytelling with album/single modes and Suno-ready tags. (Installed 2026-04-22)
