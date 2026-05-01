@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run_DCOIR_WorkItemsSchemaCleanup.ps1" -Mode generate-option-delete-script 
set "DCOIR_EXIT=%ERRORLEVEL%"
echo.
echo Exit code: %DCOIR_EXIT%
echo Upload the newest log/report from the tool output folder if there is an error.
echo.
pause
exit /b %DCOIR_EXIT%
