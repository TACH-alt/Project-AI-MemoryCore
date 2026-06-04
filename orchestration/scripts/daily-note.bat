@echo off
:: ============================================
::  DAILY-NOTE.BAT
::  Creates or updates today's Obsidian daily note
::  Pulls context from MemoryCore current-session.md
:: ============================================

setlocal EnableDelayedExpansion

set VAULT=C:\Users\Legend\Desktop\Obsidian
set MEMORYCORE=C:\Users\Legend\Documents\Claude\Projects\MemoryCore
set DAILY_FOLDER=%VAULT%\03-Daily-Notes

:: Get today's date
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set TODAY=%%c-%%b-%%a
set NOTE=%DAILY_FOLDER%\%TODAY%.md

:: Create folder if needed
if not exist "%DAILY_FOLDER%" mkdir "%DAILY_FOLDER%"

echo.
echo [📅 DAILY NOTE] Date: %TODAY%
echo.

if exist "%NOTE%" (
    echo [INFO] Daily note already exists. Appending session entry...
    echo.
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set NOW=%%a:%%b
    echo.                                          >> "%NOTE%"
    echo ## Session Update — !NOW!                 >> "%NOTE%"
    echo.                                          >> "%NOTE%"
    echo - Session active                          >> "%NOTE%"
    echo - See [[01-Sessions\%TODAY%]] for details >> "%NOTE%"
    echo.                                          >> "%NOTE%"
    echo [✅] Updated: %NOTE%
) else (
    echo [CREATE] Building today's note...
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set NOW=%%a:%%b

    echo ---                                        >  "%NOTE%"
    echo date: %TODAY%                              >> "%NOTE%"
    echo type: daily-note                           >> "%NOTE%"
    echo tags: [daily, ai-session]                  >> "%NOTE%"
    echo ---                                        >> "%NOTE%"
    echo.                                           >> "%NOTE%"
    echo # 📅 Daily Note — %TODAY%                  >> "%NOTE%"
    echo.                                           >> "%NOTE%"
    echo ## 🎯 Today's Focus                        >> "%NOTE%"
    echo.                                           >> "%NOTE%"
    echo - [ ] _Add your goals here_                >> "%NOTE%"
    echo.                                           >> "%NOTE%"
    echo ## 🤖 AI Sessions                          >> "%NOTE%"
    echo.                                           >> "%NOTE%"
    echo - Session started: !NOW!                   >> "%NOTE%"
    echo - See [[01-Sessions\%TODAY%-001]]          >> "%NOTE%"
    echo.                                           >> "%NOTE%"
    echo ## ⚡ Gemini Tasks                          >> "%NOTE%"
    echo.                                           >> "%NOTE%"
    echo _Tasks delegated to Gemini today_          >> "%NOTE%"
    echo.                                           >> "%NOTE%"
    echo ## 📋 Decisions Made                       >> "%NOTE%"
    echo.                                           >> "%NOTE%"
    echo _Key decisions recorded_                   >> "%NOTE%"
    echo.                                           >> "%NOTE%"
    echo ## 📝 Notes                                >> "%NOTE%"
    echo.                                           >> "%NOTE%"
    echo _Free notes_                               >> "%NOTE%"
    echo.                                           >> "%NOTE%"

    echo [✅] Created: %NOTE%
)

echo.
echo Opening in Obsidian...
start "" "C:\Program Files\Obsidian\Obsidian.exe" "obsidian://open?vault=Legendary&file=03-Daily-Notes/%TODAY%"

endlocal
