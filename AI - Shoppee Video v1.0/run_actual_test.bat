@echo off
cd /d "%~dp0"
echo === ACTUAL E2E RUN: ASV-0000008 (Electrova Cordless UV Mite, Shopee) === > run_output.txt 2>&1
py -V >> run_output.txt 2>&1
echo --- output --- >> run_output.txt 2>&1
py scripts\process_shopee_video.py --download-and-analyze-record-id ASV-0000008 >> run_output.txt 2>&1
echo === EXITCODE %ERRORLEVEL% === >> run_output.txt
echo === DONE === >> run_output.txt
