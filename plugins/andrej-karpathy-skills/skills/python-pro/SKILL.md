---
name: python-pro
description: "Auto-triggers on '.py' file edits, 'python', 'script', 'refactor', or 'pip' commands. Enforces PEP 8 standards, idiomatic Pythonic patterns, and modern type safety."
---

# Python-Pro -- Idiomatic Python Engineering
*Beautiful is better than ugly. Explicit is better than implicit.*

## Activation
When this skill activates, output:
`🐍 Python-Pro active -- applying Pythonic standards...`

## Protocol
1. **Environment Check**: Detect Python version and dependencies (`requirements.txt` or `pyproject.toml`).
2. **Refine Logic**: Convert "C-style" loops to list comprehensions or generators; optimize `async/await`.
3. **Type Safety**: Enforce `typing` hints for all function signatures and complex variables.
4. **PEP 8 Compliance**: Match existing naming conventions (snake_case) and spacing.
5. **Quality Gate**: Suggest running `ruff` or `pytest` if supported by the environment.

## Mandatory Rules
1. **Idiomatic First** — Always prefer "The Pythonic Way" (e.g., `with` statements).
2. **No Magic Numbers** — Use named constants or enums.
3. **Docstrings Required** — Every class and function must have a clear description.

## Level History
- **Lv.1** — Base: Idiomatic refinement, type safety, and PEP 8 enforcement. (Installed 2026-04-22)
