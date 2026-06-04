@echo off
title Setup: Gemini MCP Tool
color 0B
echo.
echo ==========================================
echo   SETUP: Gemini MCP Tool
echo   https://github.com/jamubc/gemini-mcp-tool
echo   Connects Gemini directly to Claude via MCP
echo ==========================================
echo.

setlocal EnableDelayedExpansion

set INSTALL_DIR=C:\Users\Legend\Documents\Claude\Projects\gemini-mcp-tool
set CONFIG_DIR=C:\Users\Legend\AppData\Roaming\Claude
set CONFIG_FILE=%CONFIG_DIR%\claude_desktop_config.json

:: ==========================================
:: STEP 1 — Clone the repo
:: ==========================================
echo [1/4] Cloning gemini-mcp-tool...

if exist "%INSTALL_DIR%" (
    echo [INFO] Repo already exists at %INSTALL_DIR%
    echo [INFO] Pulling latest changes...
    cd /d "%INSTALL_DIR%"
    git pull
) else (
    git clone https://github.com/jamubc/gemini-mcp-tool "%INSTALL_DIR%"
    if %errorlevel% neq 0 (
        echo [ERROR] Git clone failed. Is Git installed and do you have internet?
        pause
        exit /b 1
    )
)
echo [OK] Repo ready at: %INSTALL_DIR%
echo.

:: ==========================================
:: STEP 2 — Install dependencies
:: ==========================================
echo [2/4] Installing Node.js dependencies...
cd /d "%INSTALL_DIR%"
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] npm install failed.
    echo Try running this script from Git Bash instead.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.
echo.

:: ==========================================
:: STEP 3 — Check/create Claude config
:: ==========================================
echo [3/4] Configuring MCP in Claude Desktop...

if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"

:: Check if config file exists
if not exist "%CONFIG_FILE%" (
    echo [INFO] Creating new claude_desktop_config.json...
    (
        echo {
        echo   "mcpServers": {
        echo     "gemini-mcp-tool": {
        echo       "command": "node",
        echo       "args": ["%INSTALL_DIR:\=\\%\\index.js"],
        echo       "env": {
        echo         "GEMINI_API_KEY": "YOUR_GEMINI_API_KEY_HERE"
        echo       }
        echo     }
        echo   }
        echo }
    ) > "%CONFIG_FILE%"
    echo [OK] Config created.
) else (
    echo [INFO] claude_desktop_config.json already exists.
    echo [INFO] You need to manually add the gemini-mcp-tool entry.
    echo [INFO] See: %CONFIG_DIR%\claude_desktop_config.json
    echo [INFO] The entry to add is shown below and saved to gemini-mcp-config-snippet.json
)

:: Always save the snippet for reference
set SNIPPET=%INSTALL_DIR%\gemini-mcp-config-snippet.json
(
    echo.
    echo   ADD THIS TO YOUR claude_desktop_config.json under "mcpServers":
    echo.
    echo   "gemini-mcp-tool": {
    echo     "command": "node",
    echo     "args": ["%INSTALL_DIR:\=\\%\\index.js"],
    echo     "env": {
    echo       "GEMINI_API_KEY": "YOUR_GEMINI_API_KEY_HERE"
    echo     }
    echo   }
    echo.
) > "%SNIPPET%"
type "%SNIPPET%"

echo.

:: ==========================================
:: STEP 4 — Instructions
:: ==========================================
echo [4/4] Next steps:
echo.
echo   1. Get your Gemini API key:
echo      https://aistudio.google.com/apikey
echo.
echo   2. Set the API key permanently:
echo      setx GEMINI_API_KEY "your-key-here"
echo.
echo   3. Edit Claude config if it already existed:
echo      %CONFIG_FILE%
echo.
echo   4. Restart Claude (Cowork) completely.
echo.
echo   5. Gemini will appear as an MCP tool in Claude.
echo      Claude can then call it directly — no batch scripts needed!
echo.
echo ==========================================
echo   SETUP COMPLETE
echo   Repo: %INSTALL_DIR%
echo   Config: %CONFIG_FILE%
echo ==========================================
echo.

:: Open the config file for editing
echo Opening Claude config for review...
notepad "%CONFIG_FILE%"

pause
endlocal
