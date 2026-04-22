---
name: echo-recall
description: "MUST use when user says 'do you remember', 'remember when', 'recall', or when past session context is needed to ground the current conversation in shared history."
---

# Echo Memory Recall

## Activation
When this skill activates, output:
`🔍 Recalling memory...`

## Protocol
1. **Keyword Extraction**: Identify 2-4 specific terms from the user's question.
2. **Search Loop**: 
   - Search `daily-diary/current/*.md`
   - Search `daily-diary/archived/*/*.md`
3. **Narrate**: 
   - If found: Use `daily-diary/recall-format.md` to compose a narrative response.
   - If not found: Ask the user for clarification.
4. **Link**: Connect the past insight to the current conversation goal.

## Mandatory Rules
1. **Evidence Only** — never fabricate memories. If it's not in the Memory Log, state so clearly.
2. **Chronological Order** — present multiple matches from oldest to newest.

## Level History
- **Lv.1** — Base: Keyword-based narrative search across Memory Logs. (Installed 2026-04-22)
