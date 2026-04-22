@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set LOG=%~dp0_probe-claude.log
echo === Claude CLI Probe === > "%LOG%"
echo Date: %DATE% %TIME% >> "%LOG%"
echo. >> "%LOG%"

echo --- PATH check (where claude) --- >> "%LOG%"
where claude >> "%LOG%" 2>>&1
where claude.cmd >> "%LOG%" 2>>&1
where claude.exe >> "%LOG%" 2>>&1
echo. >> "%LOG%"

echo --- Common install paths --- >> "%LOG%"
for %%P in (
  "%LOCALAPPDATA%\Programs\claude\claude.exe"
  "%LOCALAPPDATA%\Programs\claude\claude.cmd"
  "%LOCALAPPDATA%\Programs\claude-code\claude.exe"
  "%LOCALAPPDATA%\Programs\claude-code\claude.cmd"
  "%LOCALAPPDATA%\AnthropicClaude\claude.exe"
  "%APPDATA%\npm\claude.cmd"
  "%APPDATA%\npm\claude.ps1"
  "%APPDATA%\npm\claude"
  "%USERPROFILE%\.claude\bin\claude.exe"
  "%USERPROFILE%\.claude\bin\claude.cmd"
  "%USERPROFILE%\.claude\local\claude.exe"
  "%USERPROFILE%\.claude\local\claude"
  "%USERPROFILE%\.local\bin\claude.exe"
  "%USERPROFILE%\.local\bin\claude"
  "%ProgramFiles%\Claude\claude.exe"
  "%ProgramFiles%\Anthropic\Claude\claude.exe"
) do (
  if exist %%P (
    echo [FOUND] %%~P >> "%LOG%"
  ) else (
    echo [miss ] %%~P >> "%LOG%"
  )
)
echo. >> "%LOG%"

echo --- node/npm check --- >> "%LOG%"
where node >> "%LOG%" 2>>&1
where npm >> "%LOG%" 2>>&1
call npm root -g >> "%LOG%" 2>>&1
echo. >> "%LOG%"

echo --- npm global list (claude-code related) --- >> "%LOG%"
call npm list -g --depth=0 >> "%LOG%" 2>>&1
echo. >> "%LOG%"

echo --- Broader search: %USERPROFILE% --- >> "%LOG%"
dir /b /s "%USERPROFILE%\claude.exe" 2>nul >> "%LOG%"
dir /b /s "%USERPROFILE%\claude.cmd" 2>nul >> "%LOG%"
echo. >> "%LOG%"

echo --- Scan %LOCALAPPDATA%\Programs --- >> "%LOG%"
dir /b "%LOCALAPPDATA%\Programs" 2>>&1 >> "%LOG%"
echo. >> "%LOG%"

echo === Done === >> "%LOG%"
exit /b 0
