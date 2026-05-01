@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run_DCOIR_WorkItemsSchemaCleanup.ps1" -Mode attempt-field-delete -DeletePrefixedFields -ConfirmFieldDelete DELETE_FIELDS
