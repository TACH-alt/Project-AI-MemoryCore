@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set LOG=%~dp0_register-plugin.log
set CLAUDE=C:\Users\Legend\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude-code\2.1.111\claude.exe

echo === Plugin Registration === > "%LOG%"
echo Date: %DATE% %TIME% >> "%LOG%"
echo CLAUDE exe: %CLAUDE% >> "%LOG%"
echo CWD: %CD% >> "%LOG%"
echo. >> "%LOG%"

if not exist "%CLAUDE%" (
  echo [FAIL] Claude exe not found at path >> "%LOG%"
  goto :END
)
echo [OK] Claude exe exists >> "%LOG%"
echo. >> "%LOG%"

echo --- claude --version --- >> "%LOG%"
call "%CLAUDE%" --version >> "%LOG%" 2>>&1
echo. >> "%LOG%"

echo --- claude --help (first lines) --- >> "%LOG%"
call "%CLAUDE%" --help >> "%LOG%" 2>>&1
echo. >> "%LOG%"

echo --- claude plugin --help --- >> "%LOG%"
call "%CLAUDE%" plugin --help >> "%LOG%" 2>>&1
echo. >> "%LOG%"

echo --- Verify plugins\legend-skills exists --- >> "%LOG%"
if exist "plugins\legend-skills" (
  echo [OK] plugins\legend-skills directory found >> "%LOG%"
  dir /b "plugins\legend-skills" >> "%LOG%" 2>>&1
) else (
  echo [FAIL] plugins\legend-skills not found >> "%LOG%"
)
echo. >> "%LOG%"

echo --- Run: claude plugin add --local plugins/legend-skills --- >> "%LOG%"
call "%CLAUDE%" plugin add --local plugins/legend-skills >> "%LOG%" 2>>&1
set RC=%ERRORLEVEL%
echo exit code: %RC% >> "%LOG%"
echo. >> "%LOG%"

echo --- Run: claude plugin list --- >> "%LOG%"
call "%CLAUDE%" plugin list >> "%LOG%" 2>>&1
echo exit code: %ERRORLEVEL% >> "%LOG%"

:END
echo. >> "%LOG%"
echo === Done === >> "%LOG%"
exit /b 0
