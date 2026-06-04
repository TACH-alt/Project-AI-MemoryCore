@echo off
:: ============================================
::  NEW-SESSION.BAT
::  Creates a new AI session log in Obsidian
::  Run at the start of each work session
:: ============================================

setlocal EnableDelayedExpansion

set VAULT=C:\Users\Legend\Desktop\Obsidian
set SESSION_FOLDER=%VAULT%\01-Sessions

:: Date and time
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set TODAY=%%c-%%b-%%a
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set NOW=%%a:%%b

:: Find session number for today
set COUNTER=001
for /f %%n in ('dir /b "%SESSION_FOLDER%\%TODAY%-*.md" 2^>nul ^| find /c /v ""') do (
    set /a NUM=%%n+1
    if !NUM! LSS 10 set COUNTER=00!NUM!
    if !NUM! GEQ 10 set COUNTER=0!NUM!
    if !NUM! GEQ 100 set COUNTER=!NUM!
)

set SESSION_FILE=%SESSION_FOLDER%\%TODAY%-%COUNTER%.md

:: Create folder if needed
if not exist "%SESSION_FOLDER%" mkdir "%SESSION_FOLDER%"

echo.
echo [🚀 NEW SESSION] %TODAY% — Session %COUNTER%
echo.

:: Create session note
echo ---                                        >  "%SESSION_FILE%"
echo date: %TODAY%                              >> "%SESSION_FILE%"
echo session: %COUNTER%                         >> "%SESSION_FILE%"
echo started: %NOW%                             >> "%SESSION_FILE%"
echo type: ai-session                           >> "%SESSION_FILE%"
echo tags: [session, claude, active]            >> "%SESSION_FILE%"
echo ---                                        >> "%SESSION_FILE%"
echo.                                           >> "%SESSION_FILE%"
echo # 🤖 AI Session — %TODAY% #%COUNTER%       >> "%SESSION_FILE%"
echo.                                           >> "%SESSION_FILE%"
echo **Started:** %NOW%                         >> "%SESSION_FILE%"
echo **Status:** 🟢 Active                      >> "%SESSION_FILE%"
echo **AI:** Claude (Orchestrator)              >> "%SESSION_FILE%"
echo.                                           >> "%SESSION_FILE%"
echo ## 🎯 Session Goals                        >> "%SESSION_FILE%"
echo.                                           >> "%SESSION_FILE%"
echo _Define goals at start of session_         >> "%SESSION_FILE%"
echo.                                           >> "%SESSION_FILE%"
echo ## 💬 Conversation Log                     >> "%SESSION_FILE%"
echo.                                           >> "%SESSION_FILE%"
echo _Key exchanges, decisions, outputs_        >> "%SESSION_FILE%"
echo.                                           >> "%SESSION_FILE%"
echo ## ⚡ Gemini Tasks                          >> "%SESSION_FILE%"
echo.                                           >> "%SESSION_FILE%"
echo _Tasks routed to Gemini this session_      >> "%SESSION_FILE%"
echo.                                           >> "%SESSION_FILE%"
echo ## ✅ Completed                             >> "%SESSION_FILE%"
echo.                                           >> "%SESSION_FILE%"
echo _What was accomplished_                    >> "%SESSION_FILE%"
echo.                                           >> "%SESSION_FILE%"
echo ## 🔗 Related Notes                        >> "%SESSION_FILE%"
echo.                                           >> "%SESSION_FILE%"
echo - [[03-Daily-Notes/%TODAY%]]               >> "%SESSION_FILE%"
echo.                                           >> "%SESSION_FILE%"

echo [✅] Session created: %SESSION_FILE%
echo.

:: Open in Obsidian
start "" "C:\Program Files\Obsidian\Obsidian.exe" "obsidian://open?vault=Legendary&file=01-Sessions/%TODAY%-%COUNTER%"

endlocal
