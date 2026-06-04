# 🔍 Echo — Memory Recall Protocol
*Installed: 2026-04-24 | Level: Lv.1 Keyword Search + Narrative*

---

## Trigger Phrases

Activate Echo when the user says any of these:

| Pattern | Example |
|---------|---------|
| "do you remember" | "Do you remember when we fixed the audio bug?" |
| "remember when" | "Remember when we built the frontend?" |
| "recall" | "Can you recall our FFmpeg discussion?" |
| "that time when" | "That time when we set up the scheduler..." |
| "what happened with" | "What happened with the Electrova test?" |
| "when did we" | "When did we install yt-dlp?" |
| "have we done" | "Have we done anything with Shopee short links?" |
| "check our history" | "Check our history on the masterlist setup" |
| "check history" | "Check history for the LAN frontend" |

---

## Protocol (3-Level System)

### Lv.1 — Search & Narrate
1. Extract 2–4 specific keywords from the user's question
   - Remove: the, a, when, did, we, do, you, remember, recall, etc.
   - Keep: proper nouns, technical terms, action verbs, product names
2. Search `daily-diary/current/*.md` for keyword matches (case-insensitive)
3. If not found → search `daily-diary/archived/*/*.md`
4. If found → compose narrative using `daily-diary/recall-format.md`
5. If not found → fall through to Lv.3

### Lv.2 — Uncertainty Guard
- When uncertain about any past context, ALWAYS search diary before speaking
- Never assume or fabricate past events
- If you are not certain something happened, search first

### Lv.3 — Ask User Fallback
- When search yields no results, ask:
  > "I don't see a record of [topic] in my diary. Can you tell me more about what you're remembering?"

---

## Mandatory Rules

1. **Evidence only** — never fabricate memories; if it is not in a diary entry, state that clearly
2. **Search before speaking** — always read diary files before making claims about past sessions
3. **Chronological order** — present multiple matches oldest to newest
4. **Natural narrative** — use `daily-diary/recall-format.md`; never dump raw file content
5. **Always continue** — after recall, flow naturally back into the current conversation

---

## Search Paths (in order)

1. `daily-diary/current/*.md` — most recent sessions
2. `daily-diary/archived/*/*.md` — older archived months
3. Fallback: ask user directly

---

## Recall Commands

```
echo [topic]         → Search diary for past sessions about [topic]
recall [topic]       → Same as echo
check history        → Search diary for context relevant to current conversation
do you remember...   → Auto-triggers search
```

---

## Format Reference

Output format: `daily-diary/recall-format.md`

---

*Echo Memory Recall | Protocol v1.0 | Installed: 2026-04-24*
*Search before speaking — narrate from evidence — ask when uncertain*
