@echo off
:: ============================================
::  SAVE-TO-OBSIDIAN.BAT
::  Saves a markdown file to the Obsidian vault
::
::  Usage: save-to-obsidian.bat "folder" "title" "content-file"
::  Example: save-to-obsidian.bat "04-Research" "ML-basics" "C:\temp\output.md"
:: ============================================

setlocal EnableDelayedExpansion

set VAULT=C:\Users\Legend\Desktop\Obsidian
set FOLDER=%~1
set TITLE=%~2
set CONTENT_FILE=%~3

if "%FOLDER%"=="" set FOLDER=02-Gemini-Outputs
if "%TITLE%"=="" (
    echo [ERROR] Please provide a title
    echo Usage: save-to-obsidian.bat "folder" "title" "content-file-path"
    exit /b 1
)

:: Date
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set TODAY=%%c-%%b-%%a
set TARGET_DIR=%VAULT%\%FOLDER%
set TARGET_FILE=%TARGET_DIR%\%TODAY%-%TITLE%.md

:: Create folder if needed
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

:: Write to vault
if not "%CONTENT_FILE%"=="" (
    if exist "%CONTENT_FILE%" (
        echo ---                      >  "%TARGET_FILE%"
        echo date: %TODAY%            >> "%TARGET_FILE%"
        echo title: %TITLE%           >> "%TARGET_FILE%"
        echo folder: %FOLDER%         >> "%TARGET_FILE%"
        echo tags: [saved, ai-output] >> "%TARGET_FILE%"
        echo ---                      >> "%TARGET_FILE%"
        echo.                         >> "%TARGET_FILE%"
        type "%CONTENT_FILE%"         >> "%TARGET_FILE%"
        echo [✅] Saved: %TARGET_FILE%
    ) else (
        echo [ERROR] Content file not found: %CONTENT_FILE%
        exit /b 1
    )
) else (
    echo [ERROR] No content file provided
    exit /b 1
)

:: Open in Obsidian
set OBS_PATH=%FOLDER%/%TODAY%-%TITLE%
start "" "C:\Program Files\Obsidian\Obsidian.exe" "obsidian://open?vault=Legendary&file=%OBS_PATH%"

endlocal
