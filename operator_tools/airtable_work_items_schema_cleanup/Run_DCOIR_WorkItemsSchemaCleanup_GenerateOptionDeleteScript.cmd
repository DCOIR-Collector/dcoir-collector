@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run_DCOIR_WorkItemsSchemaCleanup.ps1" -Mode generate-option-delete-script
