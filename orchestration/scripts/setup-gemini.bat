@echo off
echo ============================================
echo  Gemini-CLI Setup Script
echo  Fixes PowerShell execution policy + installs
echo ============================================
echo.

:: Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Not running as Administrator.
    echo [!] Right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [1] Setting PowerShell execution policy...
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
if %errorLevel% == 0 (
    echo [OK] Execution policy set to RemoteSigned for current user
) else (
    echo [WARN] Could not set policy. Trying machine-level...
    powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine -Force"
)

echo.
echo [2] Checking Node.js...
node --version 2>nul
if %errorLevel% neq 0 (
    echo [ERROR] Node.js not found. Please install from https://nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js found

echo.
echo [3] Checking npm...
call npm --version 2>nul
if %errorLevel% neq 0 (
    echo [ERROR] npm not found. Reinstall Node.js
    pause
    exit /b 1
)
echo [OK] npm found

echo.
echo [4] Installing Gemini-CLI globally...
call npm install -g @google/gemini-cli
if %errorLevel% == 0 (
    echo [OK] Gemini-CLI installed successfully!
) else (
    echo [ERROR] Installation failed. Check internet connection.
    pause
    exit /b 1
)

echo.
echo [5] Verifying Gemini-CLI...
gemini --version 2>nul
if %errorLevel% == 0 (
    echo [OK] Gemini-CLI is ready!
) else (
    echo [WARN] gemini command not found in PATH. You may need to restart terminal.
)

echo.
echo [6] First-time auth (opens browser for Google login)...
echo Run this command in a new terminal: gemini auth
echo.

echo ============================================
echo  SETUP COMPLETE
echo  Next: Open a new terminal and run:
echo    gemini auth
echo  Then test with:
echo    gemini -p "Hello, say hi back"
echo ============================================
pause
