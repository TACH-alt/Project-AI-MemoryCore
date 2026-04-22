@echo off
cd /d "%~dp0"
del /f /q "_probe-claude.bat" 2>nul
del /f /q "_probe-claude.log" 2>nul
del /f /q "_register-plugin.bat" 2>nul
del /f /q "_register-plugin.log" 2>nul
del /f /q "_probe-plugin-cmds.bat" 2>nul
del /f /q "_probe-plugin-cmds.log" 2>nul
del /f /q "_cleanup-temps.bat" 2>nul
exit /b 0
