@echo off
cd /d "%~dp0"
echo === HERMES WORKER E2E: TJean Kitchen Set (Shopee) === > hermes_run_output.txt
py -V >> hermes_run_output.txt 2>&1
echo --- JSON result --- >> hermes_run_output.txt
py scripts\hermes_make_video.py "https://shopee.com.my/TJean-Kitchen-Set-Wok-Pot-Non-stick-Cookware-Set-(7-Pcs)-PFAS-PTFE-PFOA-Free-Suitable-All-Stove-Frying-Pan-Wok-Soup-Pot-Saucepan-i.666152415.24208019232" 1>> hermes_run_output.txt 2>> hermes_run_stderr.txt
echo. >> hermes_run_output.txt
echo === EXITCODE %ERRORLEVEL% === >> hermes_run_output.txt
echo === DONE === >> hermes_run_output.txt
