@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run_DCOIR_WorkItemsSchemaCleanup.ps1" -Mode apply-options 
set "DCOIR_EXIT=%ERRORLEVEL%"
echo.
echo Exit code: %DCOIR_EXIT%
echo If the window above shows an error, copy the text or upload the log from your Downloads\DCOIR folder.
echo.
pause
exit /b %DCOIR_EXIT%
