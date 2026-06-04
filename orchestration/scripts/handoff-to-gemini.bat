@echo off
:: ============================================
::  HANDOFF-TO-GEMINI.BAT
::  Transfers Claude session to Gemini when
::  Claude approaches context/token limits.
::
::  Usage: handoff-to-gemini.bat [handoff-note-path]
::  The handoff note is created by Claude before
::  calling this script.
:: ============================================

setlocal EnableDelayedExpansion

set VAULT=C:\Users\Legend\Desktop\Obsidian
set SESSION_FOLDER=%VAULT%\01-Sessions
set HANDOFF_NOTE=%~1

echo.
echo ╔══════════════════════════════════════════╗
echo ║     CLAUDE → GEMINI HANDOFF INITIATED   ║
echo ╚══════════════════════════════════════════╝
echo.

if "%HANDOFF_NOTE%"=="" (
    :: Find the most recent HANDOFF file
    for /f "delims=" %%f in ('dir /b /o-d "%SESSION_FOLDER%\HANDOFF-*.md" 2^>nul') do (
        set HANDOFF_NOTE=%SESSION_FOLDER%\%%f
        goto :found
    )
    echo [ERROR] No handoff note found in %SESSION_FOLDER%
    echo Claude should create a HANDOFF-[timestamp].md file first.
    exit /b 1
)

:found
echo [📋] Reading handoff note: %HANDOFF_NOTE%
echo.
type "%HANDOFF_NOTE%"
echo.
echo ──────────────────────────────────────────
echo.

:: Build Gemini prompt from handoff note
set GEMINI_PROMPT=You are taking over a session from Claude. Read the following handoff note carefully and continue exactly where Claude left off. Save all your work to the Obsidian vault at C:\Users\Legend\Desktop\Obsidian. Here is the handoff note:

echo [🤖 GEMINI] Loading session and continuing...
echo.

gemini -p "%GEMINI_PROMPT%" --context-file "%HANDOFF_NOTE%"

if %errorLevel% neq 0 (
    echo.
    echo [FALLBACK] Trying alternative Gemini invocation...
    echo.
    :: Alternative: open Gemini interactive with the file as context
    start "" cmd /k "echo Gemini Takeover Session && echo. && echo Read this handoff file: %HANDOFF_NOTE% && echo. && gemini"
)

echo.
echo [✅] Gemini session initiated.
echo     Check %SESSION_FOLDER% for outputs.
echo.
endlocal
