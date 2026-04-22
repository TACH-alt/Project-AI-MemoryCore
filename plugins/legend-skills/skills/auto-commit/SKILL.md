---
name: auto-commit
description: "MUST use when user says 'commit', 'git commit', 'save changes', or when a development milestone is reached. Triggers a structured commit with session context."
---

# Auto-Commit

## Activation
When this skill activates, output:
`💾 Committing changes to history...`

## Protocol
1. **Analyze Changes**: Run `git status` and `git diff` to identify modified, added, or deleted files.
2. **Draft Message**: Compose a commit message following the structured format:
   - **Header**: `[type]([scope]): [short summary]` (Conventional Commits)
   - **Section 1**: `=== TECHNICAL CHANGES ===` - Bulleted list of file-level changes.
   - **Section 2**: `=== SESSION CONTEXT ===` - Project metadata, time spent, and reasoning.
3. **Execute Commit**:
   - `git add .`
   - `git commit -m "[drafted_message]"`
4. **Confirm**: Output the commit hash and a summary.

## Mandatory Rules
1. **Author**: Commit as `Legend`.
2. **Never Auto-Push**: Always ask the user before running `git push`.
3. **Sensitive Files**: Detect and skip `.env`, credentials, or API keys.

## Level History
- **Lv.1** — Base: Structured commit with session context. (Installed 2026-04-22)
