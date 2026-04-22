---
name: post-mortem
description: "MUST use when a failure signal is detected (deployment failure, broken tests, wasted time, architecture reversal, security incident, data loss) or when user says 'post-mortem', 'what went wrong', 'let's review that'. Follows post-mortem-core.md."
---

# Post-Mortem

## Activation
When this skill activates, output:
`🔥 Post-Mortem...`

## Protocol
1. **Detect Failure**: Identify failure signals like deployment failures, broken tests, or architecture reversals.
2. **Log Entry**: 
   - Ask the user if it's worth a post-mortem.
   - If yes: follow the template in `main/post-mortem-core.md`.
   - Record what went wrong, why, and what to do differently.
3. **Persist**: Append the entry to `main/post-mortems.md`.
4. **Reference**: Check the log when starting work in the same domain.

## Mandatory Rules
1. **No Blame** — focus on technical or process failures, not people.
2. **Actionable** — every entry must include at least one concrete prevention action.
3. **Append-Only** — never delete or overwrite past post-mortems.

## Level History
- **Lv.1** — Base: Failure learning log with auto-detection. (Installed 2026-04-22)
