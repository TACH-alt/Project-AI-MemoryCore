@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set LOG=%~dp0_probe-plugin-cmds.log
set CLAUDE=C:\Users\Legend\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude-code\2.1.111\claude.exe

echo === Plugin Subcommand Probe === > "%LOG%"
echo. >> "%LOG%"

echo --- claude plugin marketplace --help --- >> "%LOG%"
call "%CLAUDE%" plugin marketplace --help >> "%LOG%" 2>>&1
echo. >> "%LOG%"

echo --- claude plugin install --help --- >> "%LOG%"
call "%CLAUDE%" plugin install --help >> "%LOG%" 2>>&1
echo. >> "%LOG%"

echo --- claude plugin validate plugins/legend-skills --- >> "%LOG%"
call "%CLAUDE%" plugin validate plugins/legend-skills >> "%LOG%" 2>>&1
echo. >> "%LOG%"

echo --- claude plugin marketplace list --- >> "%LOG%"
call "%CLAUDE%" plugin marketplace list >> "%LOG%" 2>>&1
echo. >> "%LOG%"

echo === Done === >> "%LOG%"
exit /b 0
