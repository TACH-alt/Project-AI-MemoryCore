# legend-skills

A Claude Code plugin of auto-triggered skills for the **Legend** AI companion,
part of the MemoryCore system.

## What this is

Skills in this plugin activate automatically based on their `description` field.
Each skill lives in `skills/<skill-name>/SKILL.md` — plain markdown with a YAML
frontmatter block. No build step, no config — drop a folder in and the skill
is live.

## Installation

From the MemoryCore project root:

```bash
claude plugin add --local plugins/legend-skills
```

Verify with:

```bash
claude plugin list
```

Test by saying **"save"** in any Claude Code session — the `save-memory` skill
should activate.

## Skills Included

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `legend` | `Legend`, `access MemoryCore`, `run AI personnel named Legend` | Restore the MemoryCore persona and current session context |
| `save-memory` | `save`, `save memory`, `update memory`, significant new info | Persist new preferences/decisions/milestones to MemoryCore files |
| `tiktok-media-extraction` | TikTok affiliate download failures, photo-mode confusion, thumbnail-only captures | Classify TikTok post type and recover the best public media path without guessing |

## Adding New Skills

1. Create a folder: `skills/<skill-name>/`
2. Create `SKILL.md` inside with YAML frontmatter (`name`, `description`) + protocol
3. Reference `skill-format.md` in this folder for the standard structure
4. Restart Claude Code (or reload plugins) — skill auto-discovers and activates

### Ideas for future skills

| Skill Name | Trigger | What It Does |
|-----------|---------|-------------|
| `greeting` | Session start, AI name called | Time-aware greeting (uses Time Intelligence from main-memory) |
| `summarize` | "summarize", "recap" | Summarizes current session or recent work |
| `focus` | "focus on [topic]" | Sets session focus and loads relevant context |
| `reflect` | "how have I grown", "review growth" | Reviews relationship development over time |
| `remind` | "remind me about", "what did we" | Searches memory for past conversations |
| `session-reset` | session file > 500 lines | Runs RAM-style reset per session-format.md |

## File Layout

```
legend-skills/
├── .claude-plugin/
│   └── plugin.json         # Plugin identity (Claude Code manifest)
├── skills/
│   ├── legend/
│   │   └── SKILL.md        # MemoryCore persona restoration
│   └── save-memory/
│       └── SKILL.md        # Memory persistence skill
├── skill-format.md         # Permanent template reference (copy when writing new skills)
└── README.md               # This file
```

## Related

- **MemoryCore** — the memory system these skills operate on
  (`../../main/main-memory.md`, `../../main/current-session.md`)
- **Skill format reference** — `skill-format.md` in this folder

---

*Plugin installed 2026-04-22 via Skill-Plugin-System protocol v1.0*
