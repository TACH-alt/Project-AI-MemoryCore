@echo off
title Setup ChatGPT/Codex Worker-B
color 0B
echo.
echo ==========================================
echo   SETUP: ChatGPT / Codex Worker-B
echo   Installs CLI tools to use ChatGPT
echo   as a worker in Legend's pipeline
echo ==========================================
echo.

:: ==========================================
:: OPTION A: shell-gpt (recommended — ChatGPT)
:: ==========================================
echo [Option A] Installing shell-gpt (ChatGPT via OpenAI API)...
echo   Command after install: sgpt "your prompt"
echo.
pip install shell-gpt --quiet 2>nul
where sgpt >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] shell-gpt installed successfully.
    echo.
    echo  You need an OpenAI API key. Get one at: https://platform.openai.com/api-keys
    echo  Then set it permanently:
    echo    setx OPENAI_API_KEY "sk-your-key-here"
    echo.
    set SGPT_OK=1
) else (
    echo [WARN] shell-gpt install may have failed. Try: pip install shell-gpt
    set SGPT_OK=0
)

echo.

:: ==========================================
:: OPTION B: OpenAI Codex CLI (code tasks)
:: ==========================================
echo [Option B] Installing OpenAI Codex CLI (code generation)...
echo   Command after install: codex "your prompt"
echo.
call npm install -g @openai/codex >nul 2>&1
where codex >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Codex CLI installed successfully.
    set CODEX_OK=1
) else (
    echo [WARN] Codex install may have failed. Try in Git Bash: npm install -g @openai/codex
    set CODEX_OK=0
)

echo.
echo ==========================================
echo   SETUP COMPLETE
echo ==========================================
echo.
echo   shell-gpt (ChatGPT):  %SGPT_OK% (1=installed)
echo   Codex CLI:            %CODEX_OK% (1=installed)
echo.
echo   IMPORTANT: Set your OpenAI API key before using:
echo   In PowerShell or cmd:
echo     setx OPENAI_API_KEY "sk-proj-your-key-here"
echo.
echo   Then test with:
echo     sgpt "Hello from Legend's orchestration system"
echo.
pause
