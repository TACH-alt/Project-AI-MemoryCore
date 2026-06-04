@echo off
title Legend's Orchestration Pipeline Test
color 0A
echo.
echo ==========================================
echo   LEGEND'S ORCHESTRATION PIPELINE TEST
echo   Claude (Orchestrator) + Gemini + ChatGPT
echo ==========================================
echo.

setlocal EnableDelayedExpansion

set VAULT=C:\Users\Legend\Desktop\Obsidian\Legendary
set SCRIPTS=C:\Users\Legend\Documents\Claude\Projects\MemoryCore\orchestration\scripts

:: Use PowerShell for reliable date formatting
for /f %%d in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set TODAY=%%d

echo [DATE] %TODAY%
echo.

:: ==========================================
:: STEP 1 — Check Gemini
:: ==========================================
echo [1/5] Checking Gemini-CLI...
where gemini >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Gemini not found in PATH
    set GEMINI_OK=0
) else (
    echo [OK] Gemini found.
    set GEMINI_OK=1
)

:: ==========================================
:: STEP 2 — Check ChatGPT (shell-gpt / codex)
:: ==========================================
echo [2/5] Checking ChatGPT workers...
where sgpt >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] shell-gpt (sgpt) found.
    set CHATGPT_OK=1
    set CHATGPT_CMD=sgpt
) else (
    where codex >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Codex CLI found.
        set CHATGPT_OK=1
        set CHATGPT_CMD=codex
    ) else (
        echo [WARN] No ChatGPT worker found. Run setup-chatgpt.bat
        set CHATGPT_OK=0
    )
)
echo.

:: ==========================================
:: STEP 3 — Test Gemini (if available)
:: ==========================================
if "%GEMINI_OK%"=="1" (
    echo [3/5] Sending test prompt to Gemini...
    set GEMINI_OUT=%TEMP%\gemini-test-%TODAY%.txt
    gemini -p "You are Worker-A (Gemini) in Legend's AI orchestration system. Claude is the orchestrator. Confirm in 2 sentences that you are online and ready to receive delegated tasks. Sign as 'Gemini Worker-A'." > "!GEMINI_OUT!" 2>&1
    if !errorlevel! equ 0 (
        echo [OK] Gemini responded successfully.
    ) else (
        echo [WARN] Gemini returned an error. You may need to authenticate first: run 'gemini' interactively.
        set GEMINI_OK=0
    )
) else (
    echo [3/5] Skipping Gemini test (not found).
)
echo.

:: ==========================================
:: STEP 4 — Save results to Obsidian
:: ==========================================
echo [4/5] Saving pipeline test results to Obsidian...

set OUTFILE=%VAULT%\02-Gemini-Outputs\pipeline-test-%TODAY%.md
if not exist "%VAULT%\02-Gemini-Outputs" mkdir "%VAULT%\02-Gemini-Outputs"

(
echo ---
echo date: %TODAY%
echo type: pipeline-test
echo tags: [test, pipeline, gemini, chatgpt]
echo ---
echo.
echo # Pipeline Test — %TODAY%
echo.
echo ^| Worker ^| Status ^|
echo ^|-----^|-------^|
if "%GEMINI_OK%"=="1" (
    echo ^| Gemini Worker-A ^| ✅ Online ^|
) else (
    echo ^| Gemini Worker-A ^| ⚠️ Needs auth ^|
)
if "%CHATGPT_OK%"=="1" (
    echo ^| ChatGPT Worker-B ^| ✅ Online ^|
) else (
    echo ^| ChatGPT Worker-B ^| ⚠️ Not installed ^|
)
echo ^| Claude Orchestrator ^| ✅ Active ^|
echo ^| Obsidian Vault ^| ✅ Connected ^|
echo.
echo ## Routing Architecture
echo.
echo ^^^`^^^`^^^`
echo Your Request
echo     ↓
echo Claude (Orchestrator)
echo     ↓           ↓
echo Gemini      ChatGPT/Codex
echo (Writing,   (Code, Logic,
echo  Research)   Debugging^)
echo     ↓           ↓
echo   Obsidian Legendary Vault
echo ^^^`^^^`^^^`
echo.
) > "%OUTFILE%"

if "%GEMINI_OK%"=="1" (
    echo. >> "%OUTFILE%"
    echo ## Gemini Worker-A Response >> "%OUTFILE%"
    echo. >> "%OUTFILE%"
    type "!GEMINI_OUT!" >> "%OUTFILE%"
)

echo [OK] Results saved: 02-Gemini-Outputs\pipeline-test-%TODAY%.md
echo.

:: ==========================================
:: STEP 5 — Open in Obsidian
:: ==========================================
echo [5/5] Opening results in Obsidian...
start "" "obsidian://open?vault=Legendary&file=02-Gemini-Outputs/pipeline-test-%TODAY%"

echo.
echo ==========================================
echo   TEST COMPLETE
echo ==========================================
echo.
echo   Gemini (Worker-A):     %GEMINI_OK% (1=online, 0=needs setup)
echo   ChatGPT (Worker-B):    %CHATGPT_OK% (1=online, 0=needs setup)
echo   Obsidian:              Saved
echo.
echo   Next step if workers show 0:
echo   - Gemini: type 'gemini' in terminal to authenticate
echo   - ChatGPT: run scripts\setup-chatgpt.bat
echo.
pause
endlocal
