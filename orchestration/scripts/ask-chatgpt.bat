@echo off
:: ============================================
::  ASK-CHATGPT.BAT — Orchestration Worker Call
::  Usage: ask-chatgpt.bat "your prompt" [output-title] [obsidian-folder]
:: ============================================

setlocal EnableDelayedExpansion

set PROMPT=%~1
set TITLE=%~2
set FOLDER=%~3

if "%PROMPT%"=="" (
    echo [ERROR] No prompt provided.
    exit /b 1
)

if "%TITLE%"=="" set TITLE=chatgpt-output
if "%FOLDER%"=="" set FOLDER=02-Gemini-Outputs

python "C:\Users\Legend\Documents\Claude\Projects\MemoryCore\orchestration\scripts\ask-worker.py" --agent Codex --prompt "%PROMPT%" --title "%TITLE%" --folder "%FOLDER%"

endlocal
