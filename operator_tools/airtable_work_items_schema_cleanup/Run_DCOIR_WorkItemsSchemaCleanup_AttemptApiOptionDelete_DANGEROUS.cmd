@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run_DCOIR_WorkItemsSchemaCleanup.ps1" -Mode attempt-api-option-delete -ConfirmOptionDelete DELETE_OPTIONS
