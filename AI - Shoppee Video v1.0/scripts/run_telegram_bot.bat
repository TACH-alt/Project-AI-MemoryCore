@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM Run the AI - Shoppee Video Telegram bot.
REM First-time setup:
REM   1. pip install "python-telegram-bot==21.*"
REM   2. Copy config\telegram.example.json to config\telegram.json
REM   3. Fill in bot_token (from @BotFather) and allowed_user_ids (from @userinfobot)
REM ─────────────────────────────────────────────────────────────────────────────

setlocal
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set CONFIG=%PROJECT_ROOT%\config\telegram.json

if not exist "%CONFIG%" (
    echo.
    echo  Config not found: %CONFIG%
    echo  Copy config\telegram.example.json to config\telegram.json and fill it in.
    echo.
    exit /b 1
)

python -c "import telegram" 1>nul 2>nul
if errorlevel 1 (
    echo.
    echo  Installing python-telegram-bot...
    pip install "python-telegram-bot==21.*" || exit /b 1
)

python "%SCRIPT_DIR%telegram_bot.py" --project-root "%PROJECT_ROOT%"
endlocal
