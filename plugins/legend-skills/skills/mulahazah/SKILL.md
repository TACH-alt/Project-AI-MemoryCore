---
name: mulahazah
description: "MUST use when user says 'continuous-improvement', 'what have you learned', 'mulahazah status', 'behavioral learning', 'show rules'. Passive observation layer for behavioral learning and rule extraction."
---

# Mulahazah -- Behavioral Learning System

## Activation
When this skill activates, output:
`👁️ Mulahazah active -- reading learned rules...`

## Protocol
1. **Read Rules**: Check `main/rules.md` for project-specific behavioral rules.
2. **Session Reflection**: At the end of a session, identify:
   - What worked, what failed, and what to do differently.
   - Propose a "Rule to add" to `main/rules.md`.
3. **Analyze Patterns**: Detect tool usage patterns or repeated workflows.
4. **Follow Rules**: Silently apply the rules from `main/rules.md` in all future work.

## Mandatory Rules
1. **Evidence-Only** — never hallucinate rules. Only report rules in `main/rules.md`.
2. **Human-in-the-Loop** — always propose new rules before adding them.
3. **Synergy** — rule clusters from `main/rules.md` become candidates for **Forge** skills.

## Level History
- **Lv.1** — Base: Passive behavioral observation and rules.md persistence. (Installed 2026-04-22)
