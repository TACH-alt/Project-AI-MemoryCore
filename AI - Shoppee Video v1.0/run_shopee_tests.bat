@echo off
cd /d "%~dp0"
echo === ENV === > test_output.txt 2>&1
py -V >> test_output.txt 2>&1
py -m pytest --version >> test_output.txt 2>&1
echo === PYTEST RUN === >> test_output.txt 2>&1
py -m pytest -q tests\test_process_shopee_video.py tests\test_shoppee_video_frontend.py >> test_output.txt 2>&1
echo === EXITCODE %ERRORLEVEL% === >> test_output.txt 2>&1
echo === DONE === >> test_output.txt 2>&1
