---
name: work-plan
description: "MUST use when user says 'copy plan', 'append plan', 'resume plan', or when beginning a multi-step task. Manages structured execution from Project Resources/project-plan.md."
---

# Work Plan Execution

## Activation
When this skill activates, output:
`💾 Copying plan to execution format...`

## Protocol
1. **Load Plan**: Read `Project Resources/project-plan.md` (or create from template if new).
2. **Execute Step**:
   - Focus on the first available `[ ]` task.
   - Perform the work surgically.
   - **Commit Chain**: If successful, run `commit` (via auto-commit skill) and mark as `[x]`.
3. **Save**: Update `Project Resources/project-plan.md` with progress.
4. **Context Reset Recovery**: Use `resume plan` to reload state after a session restart.

## Mandatory Rules
1. **One Task at a Time** — never work on multiple steps simultaneously.
2. **Auto-Commit Integration** — Every `[x]` MUST have a corresponding commit.
3. **Limit 1000 Lines** — Archive plan to `Project Resources/archived/` if exceeded.

## Level History
- **Lv.1** — Base: Plan-to-execution tracking with Commit Chain integration. (Installed 2026-04-22)
